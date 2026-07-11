# -*- coding: utf-8 -*-
"""exp33_k_sweep.py — ko'chirilgan belgi to'plami tasodifiydan yaxshiroqmi? k bo'yicha.

exp32 da taqqoslash faqat CV tanlagan k (3–5) da qilingan edi — bu juda kichik va
shovqinli. Bu skript butun k ∈ {3,5,8,13,21,28,34} oralig'ida uch egri chizadi:

  own(k)   maqsad bazaning O'Z ranjirlashidan olingan top-k   (yuqori chegara)
  src(k)   manba bazaning ranjirlashidan olingan top-k        (sinov)
  rand(k)  tasodifiy k ta belgi, 200 marta, o'rtacha ± s.d.   (nol gipoteza)

Barcha uch holatda normallashtirish va sentroidlar MAQSAD bazaning o'quv qismida
o'rnatiladi — ya'ni faqat BELGILAR TANLOVI ko'chiriladi, kalibrovka emas.

`src` ning tasodifiy taqsimotdagi empirik persentili keltiriladi (normal yaqinlashuv emas).

Chiqish: runs/exp_external_cbis/k_sweep.json
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

import metrics_lib as ML
from boolfs import classifier as clf_mod
from boolfs import criterion, selector
from boolfs.features import FEATURE_NAMES, N_FEATURES, Normalizer

OUT = Path("runs/exp_external_cbis")
CACHE = OUT / "cache_harm"
K_LIST = [3, 5, 8, 13, 21, 28, 34]
N_RAND = 200
SEED = 42
SHAPE_IDX = [i for i, f in enumerate(FEATURE_NAMES) if f.startswith("shape_")]
KEEP_NOSHAPE = [i for i in range(N_FEATURES) if i not in SHAPE_IDX]

RUNGS = [("V0_raw", "V0_raw", list(range(N_FEATURES))),
         ("V2_scale", "V2_scale", list(range(N_FEATURES))),
         ("V3_noshape", "V2_scale", KEEP_NOSHAPE)]


def log(m):
    print(f"[ksweep] {m}", flush=True)


def feats(src, split, var):
    d = np.load(CACHE / f"{src}_{split}_{var}.npz")
    return d["X"], d["y"]


def rank_order(X, y, cols):
    Xn = Normalizer().fit(X[:, cols]).transform(X[:, cols])
    a, w = criterion.global_abc(Xn, y)
    o, _ = selector.rank_features(a, w)
    return [int(j) for j in o]


def eval_subset(Xn, ytr, Xten, yte, keep, ncols):
    lam = np.zeros(ncols, dtype=int)
    lam[np.asarray(keep)] = 1
    clf = clf_mod.MinDistClassifier().fit(Xn, ytr, lam)
    s = clf.scores(Xten)
    S = np.zeros((len(yte), 2))
    for i, c in enumerate(clf.classes_):
        S[:, int(c)] = s[:, i]
    r = ML.summary(yte, S, 2)
    return r["balanced_accuracy"], r["auc_macro"]


def direction(name, Xs, ys, Xt, yt, Xte, yte, cols):
    o_src = rank_order(Xs, ys, cols)
    o_own = rank_order(Xt, yt, cols)
    norm = Normalizer().fit(Xt[:, cols])
    Xn, Xten = norm.transform(Xt[:, cols]), norm.transform(Xte[:, cols])
    nc = len(cols)
    rng = np.random.default_rng(SEED)

    rows = []
    for k in K_LIST:
        if k > nc:
            break
        ob, oa = eval_subset(Xn, yt, Xten, yte, o_own[:k], nc)
        sb, sa = eval_subset(Xn, yt, Xten, yte, o_src[:k], nc)
        rb, ra = [], []
        for _ in range(N_RAND):
            sub = rng.choice(nc, size=k, replace=False)
            b, a = eval_subset(Xn, yt, Xten, yte, sub, nc)
            rb.append(b); ra.append(a)
        rb, ra = np.array(rb), np.array(ra)
        # empirik persentil (yarim-tenglikni hisobga olib)
        pb = float((np.sum(rb < sb) + 0.5 * np.sum(rb == sb)) / N_RAND)
        pa = float((np.sum(ra < sa) + 0.5 * np.sum(ra == sa)) / N_RAND)
        rows.append({
            "k": k, "overlap": len(set(o_src[:k]) & set(o_own[:k])) / k,
            "own_bacc": ob, "src_bacc": sb,
            "rand_bacc_mean": float(rb.mean()), "rand_bacc_sd": float(rb.std()),
            "rand_bacc_lo": float(np.percentile(rb, 2.5)),
            "rand_bacc_hi": float(np.percentile(rb, 97.5)),
            "src_pctile_bacc": pb,
            "own_auc": oa, "src_auc": sa,
            "rand_auc_mean": float(ra.mean()), "rand_auc_sd": float(ra.std()),
            "src_pctile_auc": pa,
        })
        log(f"{name} k={k:2d}: overlap={rows[-1]['overlap']:.2f} | "
            f"own={ob:.3f} src={sb:.3f} rand={rb.mean():.3f}±{rb.std():.3f} "
            f"(src pctile {pb:.2f}) | AUC own={oa:.3f} src={sa:.3f} rand={ra.mean():.3f} "
            f"(pctile {pa:.2f})")
    return rows


def main():
    R = {"k_list": K_LIST, "n_rand": N_RAND, "rungs": {}}
    for name, var, cols in RUNGS:
        Xo, yo = feats("ours", "train", var)
        Xov, yov = feats("ours", "val", var)
        Xc, yc = feats("cbis", "train", var)
        Xct, yct = feats("cbis", "test", var)
        R["rungs"][name] = {
            "n_features": len(cols),
            "ours_to_cbis": direction(f"{name} O→C", Xo, yo, Xc, yc, Xct, yct, cols),
            "cbis_to_ours": direction(f"{name} C→O", Xc, yc, Xo, yo, Xov, yov, cols),
        }
    (OUT / "k_sweep.json").write_text(json.dumps(R, indent=1, default=float))
    log(f"saqlandi: {OUT}/k_sweep.json")


if __name__ == "__main__":
    main()
