# -*- coding: utf-8 -*-
"""exp31_harmonise.py — bazalararo taqqoslashda oldindan qayta ishlash konvensiyasining roli.

MUAMMO. exp30 da CBIS bilan bizning baza orasida belgi ranjirlashi deyarli teskari
chiqdi (ρ = −0,11; top-8 kesishuvi 0). Ammo bu ikki oqim bir xil emas edi:

  • intensivlik: CBIS yamoqlari yuklashda HAR BIR YAMOQ bo'yicha min-max qilingan,
    bizning ROI'lar esa butun mammogramma bo'yicha normallashtirilgan tasvirdan kesilgan;
  • masshtab: bizning ROI 1280 px kenglikdagi rasmdan, CBIS — to'liq o'lchamli plyonka
    skanidan; GLCM d ∈ {1,3} ikki bazada turli fizik masofani o'lchaydi;
  • kesish konvensiyasi: CBIS kesimlari lezyon atrofida tor, bizning GT ramkalar kengroq —
    shakl belgilari (`shape_*`) bevosita shunga bog'liq.

Shuning uchun "belgilar ko'chmaydi" degan xulosa chiqarishdan oldin oldindan qayta ishlashni
bosqichma-bosqich moslashtirib, har bir bosqichda kelishuv qanday o'zgarishini o'lchaymiz.

ZINAPOYA (har bosqich oldingisiga qo'shiladi):
  V0  raw            — hech narsa qilinmaydi (exp30 dagi holat)
  V1  +intensity     — har bir ROI min-max bilan [0,255] ga keltiriladi (IKKALA bazada)
  V2  +scale         — har bir ROI 128×128 ga keltiriladi (GLCM masofasi nisbiy bo'ladi)
  V3  −shape         — V2 dan shakl belgilari olib tashlanadi (kesish konvensiyasiga sezgir)

Chiqish: runs/exp_external_cbis/harmonise.json
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
from PIL import Image

import metrics_lib as ML
from boolfs import classifier as clf_mod
from boolfs import criterion, selector
from boolfs.features import (FEATURE_NAMES, N_FEATURES, Normalizer,
                             crop_roi, extract_features, load_gray,
                             yolo_line_to_xyxy)

DATA = Path("/app/app/training_data/d_ai_8class_1280")
CBIS = Path("datasets/cbis_ddsm_roi")
OUT = Path("runs/exp_external_cbis")
CACHE = OUT / "cache_harm"

CLASSES = ["calcification", "mass"]
OUR_IDX = {"calcification": 4, "mass": 6}          # d_ai_8class_1280 sinf indekslari
RESIZE = (128, 128)
N_BOOT = 1000
N_STAB = 200
SEED = 42
N_LIST = [3, 5, 8, 13, 21, 28, 34, 36]

SHAPE_IDX = [i for i, f in enumerate(FEATURE_NAMES) if f.startswith("shape_")]
KEEP_NOSHAPE = [i for i in range(N_FEATURES) if i not in SHAPE_IDX]


def log(m):
    print(f"[harm] {m}", flush=True)


# ───────────────────── yamoq transformatsiyalari ───────────────────── #

def t_minmax(p):
    p = p.astype(np.float64)
    lo, hi = p.min(), p.max()
    if hi <= lo:
        return np.zeros_like(p, dtype=np.uint8)
    return ((p - lo) / (hi - lo) * 255.0).astype(np.uint8)


def t_resize(p):
    return np.asarray(Image.fromarray(p).resize(RESIZE, Image.BILINEAR))


VARIANTS = {
    "V0_raw": lambda p: p,
    "V1_intensity": t_minmax,
    "V2_scale": lambda p: t_resize(t_minmax(p)),
}


# ─────────────────────────── belgilar ──────────────────────────────── #

def our_patches(split):
    """Katta bazadagi {calcification, mass} ROI yamoqlari."""
    img_dir, lab_dir = DATA / "images" / split, DATA / "labels" / split
    want = set(OUR_IDX.values())
    for ip in sorted(img_dir.glob("*")):
        lp = lab_dir / (ip.stem + ".txt")
        if not lp.exists():
            continue
        txt = lp.read_text().strip()
        if not txt:
            continue
        if not any(int(l.split()[0]) in want for l in txt.splitlines() if l.strip()):
            continue
        img = load_gray(ip)
        H, W = img.shape
        for line in txt.splitlines():
            r = yolo_line_to_xyxy(line, W, H)
            if not r:
                continue
            c, xyxy = r
            if c not in want:
                continue
            patch = crop_roi(img, xyxy)
            if patch is None or min(patch.shape) < 8:
                continue
            yield patch, (0 if c == OUR_IDX["calcification"] else 1)


def cbis_patches(split):
    for ci, cls in enumerate(CLASSES):
        for p in sorted((CBIS / split / cls).glob("*.png")):
            img = load_gray(p)
            if img is None or min(img.shape) < 8:
                continue
            yield img, ci


def feats(source, split, variant):
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / f"{source}_{split}_{variant}.npz"
    if f.exists():
        d = np.load(f)
        return d["X"], d["y"]
    fn = VARIANTS[variant]
    gen = our_patches(split) if source == "ours" else cbis_patches(split)
    X, y, t0 = [], [], time.time()
    for patch, lab in gen:
        X.append(extract_features(fn(patch)))
        y.append(lab)
    X, y = np.stack(X), np.asarray(y)
    np.savez_compressed(f, X=X, y=y)
    log(f"{source}/{split}/{variant}: {len(y)} ROI ({time.time() - t0:.0f}s)")
    return X, y


# ─────────────────────────── tahlil ────────────────────────────────── #

def ranking(X, y, cols):
    Xn = Normalizer().fit(X[:, cols]).transform(X[:, cols])
    a, w = criterion.global_abc(Xn, y)
    order, _ = selector.rank_features(a, w)
    return [FEATURE_NAMES[cols[int(j)]] for j in order]


def spearman(o1, o2):
    r1 = {f: i + 1 for i, f in enumerate(o1)}
    r2 = {f: i + 1 for i, f in enumerate(o2)}
    n = len(o1)
    d2 = sum((r1[f] - r2[f]) ** 2 for f in o1)
    return 1 - 6 * d2 / (n * (n * n - 1))


def agree(o1, o2, k):
    return len(set(o1[:k]) & set(o2[:k])) / k


def bacc(y, yp):
    return float(np.mean([((yp == c) & (y == c)).sum() / max((y == c).sum(), 1) for c in (0, 1)]))


def transfer(Xtr, ytr, Xte, yte, cols):
    """Manba bazada fit (normallashtirish ham), maqsad bazada baholash."""
    norm = Normalizer().fit(Xtr[:, cols])
    Xn, Xten = norm.transform(Xtr[:, cols]), norm.transform(Xte[:, cols])
    a, w = criterion.global_abc(Xn, ytr)
    order, _ = selector.rank_features(a, w)
    best, bv = None, -1.0
    for n in N_LIST:
        if n > len(cols):
            break
        lam = selector.prefix_mask(order, n, len(cols))
        v = bacc(ytr, clf_mod.cv_predictions(Xn, ytr, lam))
        if v > bv:
            bv, best = v, n
    lam = selector.prefix_mask(order, best, len(cols))
    clf = clf_mod.MinDistClassifier().fit(Xn, ytr, lam)
    s = clf.scores(Xten)
    S = np.zeros((len(yte), 2))
    for k, c in enumerate(clf.classes_):
        S[:, int(c)] = s[:, k]
    r = ML.summary(yte, S, 2)
    return {"n_star": best, "cv_bacc": bv, "accuracy": r["accuracy"],
            "balanced_accuracy": r["balanced_accuracy"], "auc": r["auc_macro"],
            "mcc": r["mcc"]}


def kuncheva(subs, k, N):
    exp = k * k / N
    if abs(k - exp) < 1e-9:
        return float("nan")
    v = [(len(subs[i] & subs[j]) - exp) / (k - exp)
         for i in range(len(subs)) for j in range(i + 1, len(subs))]
    return float(np.mean(v)) if v else float("nan")


def stability(X, y, cols, n_rep=N_STAB):
    rng = np.random.default_rng(SEED)
    Xn = Normalizer().fit(X[:, cols]).transform(X[:, cols])
    n, orders = len(y), []
    for _ in range(n_rep):
        i = rng.integers(0, n, n)
        if len(np.unique(y[i])) < 2:
            continue
        a, w = criterion.global_abc(Xn[i], y[i])
        o, _ = selector.rank_features(a, w)
        orders.append([int(x) for x in o])
    return {str(k): kuncheva([set(o[:k]) for o in orders], k, len(cols))
            for k in N_LIST if k <= len(cols)}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    R = {"classes": CLASSES, "resize": list(RESIZE), "n_boot": N_BOOT,
         "shape_features": [FEATURE_NAMES[i] for i in SHAPE_IDX], "rungs": {}}

    cache = {}
    for v in VARIANTS:
        for src in ("ours", "cbis"):
            for sp in (("train", "val") if src == "ours" else ("train", "test")):
                cache[(src, sp, v)] = feats(src, sp, v)

    rungs = [("V0_raw", "V0_raw", list(range(N_FEATURES))),
             ("V1_intensity", "V1_intensity", list(range(N_FEATURES))),
             ("V2_scale", "V2_scale", list(range(N_FEATURES))),
             ("V3_noshape", "V2_scale", KEEP_NOSHAPE)]

    for name, var, cols in rungs:
        Xo, yo = cache[("ours", "train", var)]
        Xov, yov = cache[("ours", "val", var)]
        Xc, yc = cache[("cbis", "train", var)]
        Xct, yct = cache[("cbis", "test", var)]

        o_ours = ranking(Xo, yo, cols)
        o_cbis = ranking(Xc, yc, cols)
        R["rungs"][name] = {
            "n_features": len(cols),
            "order_ours": o_ours[:8], "order_cbis": o_cbis[:8],
            "spearman": spearman(o_ours, o_cbis),
            "agreement": {str(k): agree(o_ours, o_cbis, k) for k in (3, 5, 8, 13)},
            "stability_ours": stability(Xo, yo, cols),
            "stability_cbis": stability(Xc, yc, cols),
            "in_ours": transfer(Xo, yo, Xov, yov, cols),
            "in_cbis": transfer(Xc, yc, Xct, yct, cols),
            "ours_to_cbis": transfer(Xo, yo, Xct, yct, cols),
            "cbis_to_ours": transfer(Xc, yc, Xov, yov, cols),
        }
        r = R["rungs"][name]
        log(f"{name}: rho={r['spearman']:+.3f} top3={r['agreement']['3']:.3f} "
            f"top5={r['agreement']['5']:.3f} top8={r['agreement']['8']:.3f} | "
            f"in-ours bacc={r['in_ours']['balanced_accuracy']:.3f} "
            f"in-cbis bacc={r['in_cbis']['balanced_accuracy']:.3f} "
            f"o→c bacc={r['ours_to_cbis']['balanced_accuracy']:.3f} "
            f"AUC={r['ours_to_cbis']['auc']:.3f}")
        log(f"   ours top-5: {o_ours[:5]}")
        log(f"   cbis top-5: {o_cbis[:5]}")

    (OUT / "harmonise.json").write_text(json.dumps(R, indent=1, default=float))
    log(f"saqlandi: {OUT}/harmonise.json")


if __name__ == "__main__":
    main()
