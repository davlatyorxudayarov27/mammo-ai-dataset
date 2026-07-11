# -*- coding: utf-8 -*-
"""boolfs_api.py — Model Studio uchun "Xamdamov: bulcha belgilar" bo'limi backend'i.

Bulcha dasturlash usuli (R.X. Xamdamov, 2017: (3.2.2), (3.4.5), (3.6.2)-(3.6.4))
bilan informativ belgilar tanlanadi va ROI'lar minimal masofa qoidasi bo'yicha
tasniflanadi; natija YOLO detektori bilan ansambl qilinadi.

Foydalanuvchi UI'dan dataset + YOLO modelini tanlab, turli konfiguratsiyalarni
sinab ko'radi. Har sinov (run) fon-thread'da bajariladi va natijalar
app/boolfs_runs/<run_id>/ ga saqlanadi.

Marshrutlar main.py'da `include_router(boolfs_api.router)` bilan ulanadi.
"""
from __future__ import annotations

import json
import threading
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from . import auth as auth_mod

BASE_DIR = Path(__file__).resolve().parent          # /app/app
RUNS_DIR = BASE_DIR / "boolfs_runs"
RUNS_DIR.mkdir(exist_ok=True)
RUNS_JSON = RUNS_DIR / "runs.json"

router = APIRouter(prefix="/api/boolfs", tags=["boolfs"])

_RUNS: dict[str, dict] = {}
_LOCK = threading.Lock()
_WORKERS: dict[str, threading.Thread] = {}
_STOP: dict[str, threading.Event] = {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_runs() -> None:
    global _RUNS
    if RUNS_JSON.exists():
        try:
            _RUNS = json.loads(RUNS_JSON.read_text())
        except Exception:
            _RUNS = {}
    # restartdan keyin "running" qolib ketganlarni belgilaymiz
    for r in _RUNS.values():
        if r.get("status") == "running":
            r["status"] = "interrupted"
            r["message"] = "Server qayta ishga tushdi — run uzildi"


def _save_runs() -> None:
    with _LOCK:
        try:
            RUNS_JSON.write_text(json.dumps(_RUNS, indent=1))
        except Exception:
            pass


_load_runs()


def _update(run_id: str, **fields) -> None:
    with _LOCK:
        _RUNS.setdefault(run_id, {}).update(fields)
        _RUNS[run_id]["updated_at"] = _now()
    _save_runs()


def _log(run_id: str, msg: str) -> None:
    r = _RUNS.get(run_id, {})
    logs = r.get("log", [])
    logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] {msg}")
    _update(run_id, log=logs[-200:], message=msg)


# --------------------------------------------------------------------------- #
# Konfiguratsiya                                                              #
# --------------------------------------------------------------------------- #
class BoolfsRunBody(BaseModel):
    data_yaml: str
    weights: str = ""              # YOLO .pt (ansambl uchun; bo'sh bo'lsa ansamblsiz)
    alpha: float = 0.5             # YOLO skorining ulushi
    conf: float = 0.05             # detektsiya ishonch chegarasi
    iou: float = 0.3               # GT bilan moslash chegarasi
    votes_mode: str = "global"     # 'global' | 'pairwise' (kriteriy rejimi)
    cv_folds: int = 5
    split: str = "val"             # baholash bo'linmasi
    n_star: int = 0                # 0 = P(n') bo'yicha avtomatik tanlash
    note: str = ""                 # foydalanuvchi izohi (sinovlarni farqlash uchun)


def _run_boolfs(run_id: str, cfg: dict) -> None:
    """Fon-thread: fit → evaluate → (ensemble) → report."""
    import sys
    # boolfs paketi app_db volume'i ichida (/app/app/boolfs) — faqat shu yo'l saqlanadi
    for _p in (str(BASE_DIR), str(BASE_DIR.parent)):
        if _p not in sys.path:
            sys.path.insert(0, _p)
    out_dir = RUNS_DIR / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    stop = _STOP[run_id]
    try:
        import numpy as np
        from boolfs import classifier as clf_mod
        from boolfs import criterion, selector
        from boolfs.features import (FEATURE_NAMES, N_FEATURES, Normalizer,
                                     extract_split)
        from boolfs.pipeline import load_data_cfg, split_dirs

        _update(run_id, status="running", started_at=_now())
        _log(run_id, "dataset o'qilmoqda...")
        dcfg = load_data_cfg(cfg["data_yaml"])
        names = dcfg["names"]

        # ---------------- FIT ----------------
        img_dir, lbl_dir = split_dirs(dcfg, "train")
        _log(run_id, f"train belgilar ajratilmoqda: {img_dir.name}")
        X, y, _ = extract_split(img_dir, lbl_dir, log=lambda m: _log(run_id, m.strip()))
        if stop.is_set():
            raise RuntimeError("foydalanuvchi to'xtatdi")
        if len(y) < 10:
            raise RuntimeError(f"ROI juda kam ({len(y)}) — dataset labellarini tekshiring")
        counts = {names[c]: int((y == c).sum()) for c in np.unique(y)}
        _log(run_id, f"{len(y)} ROI · sinflar: {counts}")

        norm = Normalizer().fit(X)
        Xn = norm.transform(X)
        a, w = criterion.global_abc(Xn, y)
        order, r = selector.rank_features(a, w)
        sel_table = selector.selection_table(a, w, order, FEATURE_NAMES)
        _log(run_id, "ranjirlangan qator: "
             + ", ".join(t["feature"] for t in sel_table[:3]) + " ...")

        # P(n') egri chizig'i
        _log(run_id, f"P(n') hisoblanmoqda ({N_FEATURES} nuqta, {cfg['cv_folds']}-fold CV)...")
        P_curve = []
        for k in range(1, N_FEATURES + 1):
            if stop.is_set():
                raise RuntimeError("foydalanuvchi to'xtatdi")
            lam = selector.prefix_mask(order, k, N_FEATURES)
            P_curve.append(clf_mod.cv_P(Xn, y, lam, n_folds=int(cfg["cv_folds"])))
            if k % 8 == 0:
                _update(run_id, progress=round(k / N_FEATURES * 60))
        P_curve = np.asarray(P_curve)

        n_star = int(cfg.get("n_star") or 0) or int(np.argmax(P_curve)) + 1
        n_star = max(1, min(n_star, N_FEATURES))
        lam_star = selector.prefix_mask(order, n_star, N_FEATURES)
        _log(run_id, f"n* = {n_star}, P(n*) = {P_curve[n_star - 1]:.4f}")

        final = clf_mod.MinDistClassifier().fit(Xn, y, lam_star)
        pair_phi = criterion.pairwise_phi_matrix(Xn, y, lam_star)

        model = {"feature_names": FEATURE_NAMES, "normalizer": norm.to_dict(),
                 "order": [int(i) for i in order], "n_star": n_star,
                 "lambda": [int(v) for v in lam_star],
                 "selected_features": [FEATURE_NAMES[int(j)] for j in order[:n_star]],
                 "classifier": final.to_dict(), "class_names": names}
        (out_dir / "model.json").write_text(json.dumps(model, indent=1))
        artifacts = {
            "class_counts": counts, "n_roi_train": int(len(y)),
            "selection_table": sel_table,
            "phi_curve": [float(t["phi_prefix"]) for t in sel_table],
            "P_curve": [float(v) for v in P_curve],
            "n_star": n_star, "P_star": float(P_curve[n_star - 1]),
            "P_full": float(P_curve[-1]),
            "pairwise_phi": pair_phi.tolist(),
            "pairwise_phi_classes": [names[int(c)] for c in np.unique(y)],
        }
        (out_dir / "artifacts.json").write_text(json.dumps(artifacts, indent=1))
        _update(run_id, progress=65, artifacts=artifacts["n_star"])

        # ---------------- EVALUATE ----------------
        if stop.is_set():
            raise RuntimeError("foydalanuvchi to'xtatdi")
        img_dir, lbl_dir = split_dirs(dcfg, cfg["split"])
        _log(run_id, f"{cfg['split']} bo'yicha baholash...")
        Xv, yv, _ = extract_split(img_dir, lbl_dir, log=lambda m: None)
        yp = final.predict(norm.transform(Xv))
        P_val = clf_mod.p_criterion(yv, yp)
        m_cls = len(names)
        cm = np.zeros((m_cls, m_cls), dtype=int)
        for t, p in zip(yv, yp):
            cm[int(t), int(p)] += 1
        ev = {"split": cfg["split"], "P": float(P_val), "n_roi": int(len(yv)),
              "confusion": cm.tolist(), "class_names": names,
              "per_class": _per_class(cm, names)}
        (out_dir / "eval.json").write_text(json.dumps(ev, indent=1))
        _log(run_id, f"boolfs (yakka) P = {P_val:.4f}")
        _update(run_id, progress=80, P_star=artifacts["P_star"], P_val=float(P_val))

        # ---------------- ENSEMBLE ----------------
        ens = None
        if cfg.get("weights"):
            if stop.is_set():
                raise RuntimeError("foydalanuvchi to'xtatdi")
            _log(run_id, f"YOLO ansambl: {Path(cfg['weights']).name}")
            ens = _ensemble(run_id, cfg, dcfg, norm, final, names, stop)
            (out_dir / "ensemble.json").write_text(json.dumps(ens, indent=1))
            _log(run_id, f"YOLO P={ens['alpha_results']['1.0']:.4f} → "
                         f"ansambl P={ens['alpha_results'][str(ens['best_alpha'])]:.4f}")

        # ---------------- REPORT (grafiklar) ----------------
        _update(run_id, progress=92)
        _log(run_id, "grafiklar chizilmoqda...")
        try:
            from boolfs import report as rep
            rep.build(out_dir)
        except Exception as e:  # noqa: BLE001
            _log(run_id, f"hisobot xatosi (natijalar saqlandi): {e}")

        _update(run_id, status="done", progress=100, finished_at=_now(),
                message="Tugadi",
                summary={"n_star": n_star, "P_cv": artifacts["P_star"],
                         "P_val": float(P_val), "n_roi": int(len(y)),
                         "P_yolo": (ens["alpha_results"]["1.0"] if ens else None),
                         "P_ens": (ens["alpha_results"][str(ens["best_alpha"])] if ens else None),
                         "best_alpha": (ens["best_alpha"] if ens else None)})
    except Exception as e:  # noqa: BLE001
        status = "stopped" if stop.is_set() else "failed"
        _log(run_id, f"{'to‘xtatildi' if stop.is_set() else 'XATO'}: {e}")
        _update(run_id, status=status, finished_at=_now(),
                error=str(e)[:400], traceback=traceback.format_exc()[-1500:])


def _per_class(cm, names: list[str]) -> list[dict]:
    out = []
    for c in range(cm.shape[0]):
        tp = int(cm[c, c])
        fn = int(cm[c].sum()) - tp
        fp = int(cm[:, c].sum()) - tp
        out.append({"class": names[c], "support": tp + fn,
                    "precision": round(tp / (tp + fp), 4) if tp + fp else 0.0,
                    "recall": round(tp / (tp + fn), 4) if tp + fn else 0.0})
    return out


def _ensemble(run_id: str, cfg: dict, dcfg: dict, norm, clf, names: list[str],
              stop: threading.Event) -> dict:
    import numpy as np
    from ultralytics import YOLO
    from boolfs import classifier as clf_mod
    from boolfs.features import crop_roi, extract_features, load_gray, yolo_line_to_xyxy
    from boolfs.pipeline import _iou, split_dirs

    m = len(names)
    yolo = YOLO(cfg["weights"])
    img_dir, lbl_dir = split_dirs(dcfg, cfg["split"])
    img_files = sorted(p for p in img_dir.glob("*")
                       if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".bmp"))
    matched = []
    n_pred = n_gt = 0
    for i, ip in enumerate(img_files):
        if stop.is_set():
            raise RuntimeError("foydalanuvchi to'xtatdi")
        img = load_gray(ip)
        H, W = img.shape
        gts = []
        lp = lbl_dir / (ip.stem + ".txt")
        if lp.exists():
            for line in lp.read_text().strip().splitlines():
                pr = yolo_line_to_xyxy(line, W, H)
                if pr:
                    gts.append(pr)
        n_gt += len(gts)
        res = yolo.predict(str(ip), conf=float(cfg["conf"]), verbose=False)[0]
        boxes = res.boxes
        if boxes is None or len(boxes) == 0:
            continue
        order = np.argsort(-boxes.conf.cpu().numpy())
        used = set()
        for bi in order:
            n_pred += 1
            bxy = boxes.xyxy.cpu().numpy()[bi]
            bcls = int(boxes.cls.cpu().numpy()[bi])
            bconf = float(boxes.conf.cpu().numpy()[bi])
            best_iou, best_g = 0.0, -1
            for gi, (gc, gxy) in enumerate(gts):
                if gi in used:
                    continue
                v = _iou(bxy, gxy)
                if v > best_iou:
                    best_iou, best_g = v, gi
            if best_iou < float(cfg["iou"]) or best_g < 0:
                continue
            used.add(best_g)
            patch = crop_roi(img, tuple(bxy))
            if patch is None:
                continue
            f = norm.transform(extract_features(patch).reshape(1, -1))
            s_small = clf.scores(f)[0]
            s = np.zeros(m)
            for k, c in enumerate(clf.classes_):
                s[int(c)] = s_small[k]
            matched.append((int(gts[best_g][0]), bcls, bconf, s))
        if (i + 1) % 10 == 0:
            _update(run_id, progress=80 + round((i + 1) / len(img_files) * 10))

    if not matched:
        raise RuntimeError("GT bilan mos kelgan detektsiya topilmadi "
                           "(conf/IoU chegarasini pasaytiring)")

    y_true = np.array([t for t, _, _, _ in matched])
    yolo_vec = np.zeros((len(matched), m))
    for i, (_, c, cf, _) in enumerate(matched):
        yolo_vec[i, :] = (1.0 - cf) / (m - 1)
        yolo_vec[i, c] = cf
    bool_vec = np.stack([s for _, _, _, s in matched])

    alphas = sorted({0.0, 0.3, 0.5, 0.7, 1.0} | {round(float(cfg["alpha"]), 2)})
    results = {}
    for al in alphas:
        comb = al * yolo_vec + (1.0 - al) * bool_vec
        results[al] = clf_mod.p_criterion(y_true, comb.argmax(axis=1))
    inner = [al for al in alphas if 0.0 < al < 1.0]
    best_alpha = max(inner, key=lambda al: results[al]) if inner else float(cfg["alpha"])

    yolo_pred = yolo_vec.argmax(axis=1)
    ens_pred = (best_alpha * yolo_vec + (1 - best_alpha) * bool_vec).argmax(axis=1)

    def _cm(pred):
        cm = np.zeros((m, m), dtype=int)
        for t, p in zip(y_true, pred):
            cm[int(t), int(p)] += 1
        return cm

    cm_y, cm_e = _cm(yolo_pred), _cm(ens_pred)
    return {"split": cfg["split"], "iou_thr": float(cfg["iou"]), "conf_thr": float(cfg["conf"]),
            "n_matched": len(matched), "n_pred": n_pred, "n_gt": n_gt,
            "weights": Path(cfg["weights"]).name,
            "alpha_results": {str(k): float(v) for k, v in results.items()},
            "best_alpha": best_alpha,
            "confusion_yolo": cm_y.tolist(), "confusion_ensemble": cm_e.tolist(),
            "per_class_yolo": _per_class(cm_y, names),
            "per_class_ensemble": _per_class(cm_e, names),
            "class_names": names}


# --------------------------------------------------------------------------- #
# Marshrutlar                                                                 #
# --------------------------------------------------------------------------- #
@router.post("/run")
def boolfs_run(body: BoolfsRunBody, _user: dict = Depends(auth_mod.require_user)):
    if not Path(body.data_yaml).exists():
        raise HTTPException(400, f"data.yaml topilmadi: {body.data_yaml}")
    if body.weights and not Path(body.weights).exists():
        raise HTTPException(400, f"model fayli topilmadi: {body.weights}")
    if any(r.get("status") == "running" for r in _RUNS.values()):
        raise HTTPException(409, "Boshqa boolfs sinovi ishlayapti — avval uni to'xtating")
    run_id = "bf" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:4]
    cfg = body.model_dump()
    _update(run_id, run_id=run_id, status="queued", params=cfg, created_at=_now(),
            progress=0, log=[])
    _STOP[run_id] = threading.Event()
    t = threading.Thread(target=_run_boolfs, args=(run_id, cfg), daemon=True)
    _WORKERS[run_id] = t
    t.start()
    return {"run_id": run_id, "status": "running"}


@router.post("/stop/{run_id}")
def boolfs_stop(run_id: str, _user: dict = Depends(auth_mod.require_user)):
    if run_id not in _RUNS:
        raise HTTPException(404, "Run topilmadi")
    ev = _STOP.get(run_id)
    if not ev or not (_WORKERS.get(run_id) and _WORKERS[run_id].is_alive()):
        raise HTTPException(400, "Bu run ishlamayapti")
    ev.set()
    _update(run_id, message="To'xtatish so'raldi (joriy bosqich tugagach)")
    return {"ok": True}


@router.get("/runs")
def boolfs_runs(_user: dict = Depends(auth_mod.require_user)):
    items = []
    for rid, r in sorted(_RUNS.items(), key=lambda kv: kv[0], reverse=True)[:60]:
        alive = bool(_WORKERS.get(rid) and _WORKERS[rid].is_alive())
        items.append({"run_id": rid, "status": r.get("status"), "progress": r.get("progress", 0),
                      "created_at": r.get("created_at"), "note": (r.get("params") or {}).get("note", ""),
                      "weights": Path((r.get("params") or {}).get("weights", "") or "—").name,
                      "summary": r.get("summary"), "running": alive})
    return {"runs": items}


@router.get("/status/{run_id}")
def boolfs_status(run_id: str, _user: dict = Depends(auth_mod.require_user)):
    r = _RUNS.get(run_id)
    if not r:
        raise HTTPException(404, "Run topilmadi")
    out = dict(r)
    out["running"] = bool(_WORKERS.get(run_id) and _WORKERS[run_id].is_alive())
    out.pop("traceback", None)
    return out


@router.get("/result/{run_id}")
def boolfs_result(run_id: str, _user: dict = Depends(auth_mod.require_user)):
    d = RUNS_DIR / run_id
    if not d.is_dir():
        raise HTTPException(404, "Natija topilmadi")
    out = {"run_id": run_id, "params": (_RUNS.get(run_id) or {}).get("params", {})}
    for f in ("artifacts", "eval", "ensemble", "model"):
        p = d / f"{f}.json"
        if p.exists():
            try:
                out[f] = json.loads(p.read_text())
            except Exception:
                pass
    out["figures"] = [p.name for p in sorted(d.glob("*.png"))]
    return out


@router.get("/figure/{run_id}/{name}")
def boolfs_figure(run_id: str, name: str, _user: dict = Depends(auth_mod.require_user)):
    # yo'l traversalidan himoya
    if "/" in name or "\\" in name or ".." in name or not name.endswith(".png"):
        raise HTTPException(400, "Noto'g'ri fayl nomi")
    p = RUNS_DIR / run_id / name
    if not p.is_file():
        raise HTTPException(404, "Rasm topilmadi")
    return FileResponse(str(p), media_type="image/png")


@router.get("/report/{run_id}")
def boolfs_report(run_id: str, _user: dict = Depends(auth_mod.require_user)):
    p = RUNS_DIR / run_id / "report.md"
    if not p.is_file():
        raise HTTPException(404, "Hisobot topilmadi")
    return FileResponse(str(p), media_type="text/markdown",
                        filename=f"boolfs_{run_id}_report.md")
