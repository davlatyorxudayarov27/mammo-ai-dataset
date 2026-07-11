"""pipeline.py — end-to-end: dataset → belgi ajratish → tanlash → baholash → hisobot.

CLI:
    python -m boolfs.pipeline fit      --data <data.yaml> --source gt --out runs/boolfs/
    python -m boolfs.pipeline evaluate --data <data.yaml> --model runs/boolfs/model.json
    python -m boolfs.pipeline ensemble --data <data.yaml> --model runs/boolfs/model.json \
                                       --pred <yolo_weights.pt> --alpha 0.5

fit: belgilar → a_j/(b_j+c_j) → (3.4.5) ranjirlash → P(n') bo'yicha n'* → model.json
evaluate: val to'plamda confusion matrix, per-class precision/recall, P (3.6.4)
ensemble: yakuniy score = α·YOLO + (1−α)·s_p; α ∈ {0.3, 0.5, 0.7} taqqoslanadi
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import yaml

from . import classifier as clf_mod
from . import criterion, report, selector
from .features import FEATURE_NAMES, N_FEATURES, Normalizer, extract_features, \
    crop_roi, extract_split, load_gray


def log(msg: str) -> None:
    print(f"[boolfs] {msg}", flush=True)


# ------------------------------------------------------------ data.yaml --- #
def load_data_cfg(data_yaml: str | Path) -> dict:
    """data.yaml o'qish. 'path' lokalda mavjud bo'lmasa (masalan GPU serverdan
    ko'chirilgan dataset), yaml fayl joylashgan papka olinadi."""
    dp = Path(data_yaml)
    cfg = yaml.safe_load(dp.read_text())
    root = Path(cfg.get("path", "."))
    if not root.exists():
        root = dp.parent
    names = cfg.get("names", {})
    if isinstance(names, dict):
        names = [names[k] for k in sorted(names)]
    return {"root": root, "train": cfg.get("train", "images/train"),
            "val": cfg.get("val", "images/val"), "names": list(names)}


def split_dirs(cfg: dict, split: str) -> tuple[Path, Path]:
    img = cfg["root"] / cfg[split]
    lbl = Path(str(img).replace("/images/", "/labels/").replace("\\images\\", "\\labels\\"))
    if not img.exists():
        raise SystemExit(f"[boolfs] XATO: rasm papkasi topilmadi: {img}")
    if not lbl.exists():
        raise SystemExit(f"[boolfs] XATO: label papkasi topilmadi: {lbl}")
    return img, lbl


# ------------------------------------------------------------------ fit --- #
def cmd_fit(args) -> None:
    cfg = load_data_cfg(args.data)
    names = cfg["names"]
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if args.source != "gt":
        raise SystemExit("[boolfs] fit faqat --source gt bilan (train GT labellar kerak)")

    log(f"dataset: {cfg['root']} · sinflar: {names}")
    img_dir, lbl_dir = split_dirs(cfg, "train")
    log(f"train belgilar ajratilmoqda: {img_dir}")
    X, y, meta = extract_split(img_dir, lbl_dir, log=log)
    log(f"train ROI: {len(y)} ta, belgilar: {X.shape[1]}")
    counts = {names[c]: int((y == c).sum()) for c in np.unique(y)}
    log(f"sinf taqsimoti: {counts}")

    norm = Normalizer().fit(X)
    Xn = norm.transform(X)

    # (3.2.2) global rejim + (3.4.5) ranjirlash
    a, w = criterion.global_abc(Xn, y)
    order, r = selector.rank_features(a, w)
    sel_table = selector.selection_table(a, w, order, FEATURE_NAMES)
    log("ranjirlangan qator (top-5): "
        + ", ".join(f"{t['feature']}({t['r_j']:.3g})" for t in sel_table[:5]))

    # P(n') egri chizig'i — n'* ni klassifikatsiya sifati bo'yicha tanlaymiz
    log("P(n') hisoblanmoqda (aralash CV: 5-fold + kichik sinflar LOO)...")
    P_curve = []
    for n_sel in range(1, N_FEATURES + 1):
        lam = selector.prefix_mask(order, n_sel, N_FEATURES)
        P_curve.append(clf_mod.cv_P(Xn, y, lam))
    P_curve = np.asarray(P_curve)
    n_star = int(np.argmax(P_curve)) + 1          # teng bo'lsa — kichigi
    lam_star = selector.prefix_mask(order, n_star, N_FEATURES)
    log(f"n'* = {n_star}, P(n'*) = {P_curve[n_star - 1]:.4f} "
        f"(to'liq n=38: P = {P_curve[-1]:.4f})")

    final = clf_mod.MinDistClassifier().fit(Xn, y, lam_star)
    pair_phi = criterion.pairwise_phi_matrix(Xn, y, lam_star)

    model = {
        "feature_names": FEATURE_NAMES,
        "normalizer": norm.to_dict(),
        "order": [int(i) for i in order],
        "ranking_r": [None if not np.isfinite(v) else float(v) for v in r],
        "n_star": n_star,
        "lambda": [int(v) for v in lam_star],
        "selected_features": [FEATURE_NAMES[int(j)] for j in order[:n_star]],
        "classifier": final.to_dict(),
        "class_names": names,
    }
    (out / "model.json").write_text(json.dumps(model, indent=1))

    artifacts = {
        "class_counts": counts,
        "n_roi_train": int(len(y)),
        "selection_table": sel_table,
        "phi_curve": [float(t["phi_prefix"]) for t in sel_table],
        "P_curve": [float(v) for v in P_curve],
        "n_star": n_star,
        "P_star": float(P_curve[n_star - 1]),
        "pairwise_phi": pair_phi.tolist(),
        "pairwise_phi_classes": [names[int(c)] for c in np.unique(y)],
    }
    (out / "artifacts.json").write_text(json.dumps(artifacts, indent=1))
    log(f"model.json va artifacts.json saqlandi: {out}")


# ------------------------------------------------------------- evaluate --- #
def _load_model(path: str | Path) -> tuple[dict, Normalizer, "clf_mod.MinDistClassifier"]:
    d = json.loads(Path(path).read_text())
    return d, Normalizer.from_dict(d["normalizer"]), clf_mod.MinDistClassifier.from_dict(d["classifier"])


def _confusion(y_true, y_pred, m: int) -> np.ndarray:
    M = np.zeros((m, m), dtype=np.int64)
    for t, p in zip(y_true, y_pred):
        M[int(t), int(p)] += 1
    return M


def _per_class(M: np.ndarray, names: list[str]) -> list[dict]:
    out = []
    for c in range(M.shape[0]):
        tp = int(M[c, c])
        fn = int(M[c].sum()) - tp
        fp = int(M[:, c].sum()) - tp
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        out.append({"class": names[c], "support": tp + fn,
                    "precision": round(prec, 4), "recall": round(rec, 4)})
    return out


def cmd_evaluate(args) -> None:
    cfg = load_data_cfg(args.data)
    names = cfg["names"]
    model_path = Path(args.model)
    out = model_path.parent
    model, norm, clf = _load_model(model_path)

    img_dir, lbl_dir = split_dirs(cfg, args.split)
    log(f"{args.split} belgilar ajratilmoqda: {img_dir}")
    X, y, meta = extract_split(img_dir, lbl_dir, log=log)
    log(f"{args.split} ROI: {len(y)} ta")
    y_pred = clf.predict(norm.transform(X))
    P = clf_mod.p_criterion(y, y_pred)
    M = _confusion(y, y_pred, len(names))
    log(f"P ({args.split}, GT ROI) = {P:.4f}")

    ev = {"split": args.split, "P": float(P), "n_roi": int(len(y)),
          "confusion": M.tolist(), "class_names": names,
          "per_class": _per_class(M, names)}
    (out / "eval.json").write_text(json.dumps(ev, indent=1))
    log(f"eval.json saqlandi: {out}")
    report.build(out)
    log(f"hisobot yangilandi: {out / 'report.md'}")


# ------------------------------------------------------------- ensemble --- #
def _iou(b1, b2) -> float:
    ax1, ay1, ax2, ay2 = b1
    bx1, by1, bx2, by2 = b2
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    inter = iw * ih
    ua = (ax2 - ax1) * (ay2 - ay1) + (bx2 - bx1) * (by2 - by1) - inter
    return inter / ua if ua > 0 else 0.0


def cmd_ensemble(args) -> None:
    cfg = load_data_cfg(args.data)
    names = cfg["names"]
    m = len(names)
    model_path = Path(args.model)
    out = model_path.parent
    model, norm, clf = _load_model(model_path)

    pred_path = Path(args.pred)
    if pred_path.suffix != ".pt":
        raise SystemExit("[boolfs] --pred YOLO vazn fayli (.pt) bo'lishi kerak")
    from ultralytics import YOLO
    log(f"YOLO yuklanmoqda: {pred_path}")
    yolo = YOLO(str(pred_path))

    img_dir, lbl_dir = split_dirs(cfg, args.split)
    img_files = sorted(p for p in img_dir.glob("*")
                       if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".bmp"))
    log(f"{len(img_files)} ta {args.split} rasmga YOLO inference (--source pred)...")

    matched = []      # (y_true, yolo_cls, yolo_conf, boolfs_scores_vector)
    n_pred_total = n_gt_total = 0
    from .features import yolo_line_to_xyxy
    for ip in img_files:
        img = load_gray(ip)
        H, W = img.shape
        gts = []
        lp = lbl_dir / (ip.stem + ".txt")
        if lp.exists():
            for line in lp.read_text().strip().splitlines():
                parsed = yolo_line_to_xyxy(line, W, H)
                if parsed:
                    gts.append(parsed)
        n_gt_total += len(gts)
        res = yolo.predict(str(ip), conf=args.conf, verbose=False)[0]
        boxes = res.boxes
        if boxes is None or len(boxes) == 0:
            continue
        order = np.argsort(-boxes.conf.cpu().numpy())
        used_gt = set()
        for bi in order:
            n_pred_total += 1
            bxy = boxes.xyxy.cpu().numpy()[bi]
            bcls = int(boxes.cls.cpu().numpy()[bi])
            bconf = float(boxes.conf.cpu().numpy()[bi])
            # eng mos GT (IoU>=0.3, greedy)
            best_iou, best_g = 0.0, -1
            for gi, (gc, gxy) in enumerate(gts):
                if gi in used_gt:
                    continue
                i = _iou(bxy, gxy)
                if i > best_iou:
                    best_iou, best_g = i, gi
            if best_iou < args.iou or best_g < 0:
                continue
            used_gt.add(best_g)
            patch = crop_roi(img, tuple(bxy))
            if patch is None:
                continue
            f = norm.transform(extract_features(patch).reshape(1, -1))
            s_small = clf.scores(f)[0]                       # klassifikator sinflari bo'yicha
            s = np.zeros(m)
            for k, c in enumerate(clf.classes_):
                s[int(c)] = s_small[k]
            matched.append((int(gts[best_g][0]), bcls, bconf, s))

    if not matched:
        raise SystemExit("[boolfs] GT bilan mos kelgan detektsiya topilmadi")
    log(f"mos kelgan detektsiyalar: {len(matched)} / pred={n_pred_total}, GT={n_gt_total}")

    y_true = np.array([t for t, _, _, _ in matched])
    yolo_vec = np.zeros((len(matched), m))
    for i, (_, c, cf, _) in enumerate(matched):
        yolo_vec[i, :] = (1.0 - cf) / (m - 1)                # qolgan sinflarga tekis
        yolo_vec[i, c] = cf
    bool_vec = np.stack([s for _, _, _, s in matched])

    alphas = sorted({0.0, 0.3, 0.5, 0.7, 1.0} | {float(args.alpha)})
    results = {}
    for al in alphas:
        comb = al * yolo_vec + (1.0 - al) * bool_vec
        acc = clf_mod.p_criterion(y_true, comb.argmax(axis=1))
        results[al] = acc
        log(f"  alpha={al:.1f}: P = {acc:.4f}"
            + ("  (faqat YOLO)" if al == 1.0 else "  (faqat boolfs)" if al == 0.0 else ""))
    best_alpha = max((al for al in alphas if 0.0 < al < 1.0), key=lambda al: results[al])

    yolo_pred = yolo_vec.argmax(axis=1)
    ens_pred = (best_alpha * yolo_vec + (1 - best_alpha) * bool_vec).argmax(axis=1)
    ens = {
        "split": args.split, "iou_thr": args.iou, "conf_thr": args.conf,
        "n_matched": len(matched), "n_pred": n_pred_total, "n_gt": n_gt_total,
        "weights": str(pred_path.name),
        "alpha_results": {str(k): float(v) for k, v in results.items()},
        "best_alpha": best_alpha,
        "confusion_yolo": _confusion(y_true, yolo_pred, m).tolist(),
        "confusion_ensemble": _confusion(y_true, ens_pred, m).tolist(),
        "per_class_yolo": _per_class(_confusion(y_true, yolo_pred, m), names),
        "per_class_ensemble": _per_class(_confusion(y_true, ens_pred, m), names),
        "class_names": names,
    }
    (out / "ensemble.json").write_text(json.dumps(ens, indent=1))
    log(f"ensemble.json saqlandi (best alpha={best_alpha}, "
        f"YOLO P={results[1.0]:.4f} -> ensemble P={results[best_alpha]:.4f})")
    report.build(out)
    log(f"hisobot yangilandi: {out / 'report.md'}")


# ------------------------------------------------------------------ CLI --- #
def main() -> None:
    ap = argparse.ArgumentParser(prog="boolfs.pipeline",
                                 description="Bulcha belgi tanlash pipeline (Xamdamov, 2017)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("fit", help="belgilar → tanlash → model.json")
    p.add_argument("--data", required=True)
    p.add_argument("--source", default="gt", choices=["gt", "pred"])
    p.add_argument("--out", default="runs/boolfs/")
    p.set_defaults(fn=cmd_fit)

    p = sub.add_parser("evaluate", help="val GT ROI bo'yicha baholash")
    p.add_argument("--data", required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--split", default="val", choices=["train", "val"])
    p.set_defaults(fn=cmd_evaluate)

    p = sub.add_parser("ensemble", help="YOLO + boolfs ensemble")
    p.add_argument("--data", required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--pred", required=True, help="YOLO vazn fayli (.pt)")
    p.add_argument("--alpha", type=float, default=0.5)
    p.add_argument("--split", default="val", choices=["train", "val"])
    p.add_argument("--conf", type=float, default=0.05)
    p.add_argument("--iou", type=float, default=0.3)
    p.set_defaults(fn=cmd_ensemble)

    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
