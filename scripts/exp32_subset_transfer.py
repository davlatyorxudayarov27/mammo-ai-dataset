# -*- coding: utf-8 -*-
"""exp32_subset_transfer.py — reyting ko'chadimi yoki faqat kalibrovka buziladimi?

exp31 da manba bazadan ranjirlash + normallashtirish + sentroidlar birga ko'chirilgan edi;
natija tasodif darajasida chiqdi. Bu ikki xil sababdan bo'lishi mumkin:

  (a) tanlangan BELGILAR maqsad bazada informativ emas, yoki
  (b) belgilar informativ, lekin KALIBROVKA (z-normallashtirish + sentroidlar) ko'chmaydi.

Ajratish uchun bu skript faqat **belgilar to'plamini** ko'chiradi va tasniflagichni
maqsad bazaning o'quv qismida qaytadan o'qitadi. Uch qiyoslama:

  own    — maqsad baza o'z ranjirlashidan olingan top-n′ to'plam  (yuqori chegara)
  src    — manba bazaning ranjirlashidan olingan top-n′ to'plam   (sinov)
  rand   — bir xil quvvatdagi tasodifiy to'plam, R marta          (pastki chegara)

Agar src ≈ own bo'lsa: belgilar ko'chadi, faqat kalibrovka buziladi; ranjirlashning
o'zi noyob emas (masala yomon aniqlangan).
Agar src ≈ rand bo'lsa: manba reytingi maqsad domenda hech qanday ma'lumot bermaydi.

Chiqish: runs/exp_external_cbis/subset_transfer.json
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
N_RAND = 200
N_BOOT = 1000
SEED = 42
N_LIST = [3, 5, 8, 13, 21, 28, 34, 36]
SHAPE_IDX = [i for i, f in enumerate(FEATURE_NAMES) if f.startswith("shape_")]
KEEP_NOSHAPE = [i for i in range(N_FEATURES) if i not in SHAPE_IDX]

RUNGS = [("V0_raw", "V0_raw", list(range(N_FEATURES))),
         ("V1_intensity", "V1_intensity", list(range(N_FEATURES))),
         ("V2_scale", "V2_scale", list(range(N_FEATURES))),
         ("V3_noshape", "V2_scale", KEEP_NOSHAPE)]


def log(m):
    print(f"[subset] {m}", flush=True)


def feats(src, split, var):
    d = np.load(CACHE / f"{src}_{split}_{var}.npz")
    return d["X"], d["y"]


def bacc(y, yp):
    return float(np.mean([((yp == c) & (y == c)).sum() / max((y == c).sum(), 1)
                          for c in (0, 1)]))


def rank_order(X, y, cols):
    Xn = Normalizer().fit(X[:, cols]).transform(X[:, cols])
    a, w = criterion.global_abc(Xn, y)
    o, _ = selector.rank_features(a, w)
    return [int(j) for j in o]                      # cols ichidagi lokal indekslar


def pick_nstar(X, y, cols, order):
    Xn = Normalizer().fit(X[:, cols]).transform(X[:, cols])
    best, bv = None, -1.0
    for n in N_LIST:
        if n > len(cols):
            break
        lam = selector.prefix_mask(np.asarray(order), n, len(cols))
        v = bacc(y, clf_mod.cv_predictions(Xn, y, lam))
        if v > bv:
            bv, best = v, n
    return best, bv


def eval_subset(Xtr, ytr, Xte, yte, cols, keep_local):
    """keep_local — cols ichidagi lokal indekslar. Klassifikator MAQSAD bazada o'qitiladi."""
    norm = Normalizer().fit(Xtr[:, cols])
    Xn, Xten = norm.transform(Xtr[:, cols]), norm.transform(Xte[:, cols])
    lam = np.zeros(len(cols), dtype=int)
    lam[np.asarray(keep_local)] = 1
    clf = clf_mod.MinDistClassifier().fit(Xn, ytr, lam)
    s = clf.scores(Xten)
    S = np.zeros((len(yte), 2))
    for k, c in enumerate(clf.classes_):
        S[:, int(c)] = s[:, k]
    r = ML.summary(yte, S, 2)
    return {"accuracy": r["accuracy"], "balanced_accuracy": r["balanced_accuracy"],
            "auc": r["auc_macro"], "mcc": r["mcc"]}


def rand_baseline(Xtr, ytr, Xte, yte, cols, k, n_rep=N_RAND, seed=SEED):
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(n_rep):
        sub = rng.choice(len(cols), size=k, replace=False)
        vals.append(eval_subset(Xtr, ytr, Xte, yte, cols, sub))
    out = {}
    for key in ("balanced_accuracy", "auc"):
        a = np.array([v[key] for v in vals])
        out[key] = {"mean": float(a.mean()), "sd": float(a.std()),
                    "lo": float(np.percentile(a, 2.5)), "hi": float(np.percentile(a, 97.5))}
    return out


def pctile(value, arr_stats):
    """src natijasi tasodifiy taqsimotning qaysi persentilida (taxminiy, normal yaqinlashuv)."""
    mu, sd = arr_stats["mean"], arr_stats["sd"]
    if sd < 1e-9:
        return float("nan")
    from math import erf, sqrt
    z = (value - mu) / sd
    return float(0.5 * (1 + erf(z / sqrt(2))))


def direction(name, Xs, ys, Xt_tr, yt_tr, Xt_te, yt_te, cols):
    """manba (s) reytingi → maqsad (t) bazada qayta o'qitish."""
    o_src = rank_order(Xs, ys, cols)
    o_own = rank_order(Xt_tr, yt_tr, cols)
    n_src, _ = pick_nstar(Xs, ys, cols, o_src)
    n_own, _ = pick_nstar(Xt_tr, yt_tr, cols, o_own)
    k = n_own                                   # bir xil quvvatda qiyoslash

    own = eval_subset(Xt_tr, yt_tr, Xt_te, yt_te, cols, o_own[:k])
    src = eval_subset(Xt_tr, yt_tr, Xt_te, yt_te, cols, o_src[:k])
    rnd = rand_baseline(Xt_tr, yt_tr, Xt_te, yt_te, cols, k)
    overlap = len(set(o_src[:k]) & set(o_own[:k])) / k

    res = {"k": k, "n_star_src": n_src, "n_star_own": n_own, "overlap_at_k": overlap,
           "own": own, "src": src, "random": rnd,
           "src_pctile_bacc": pctile(src["balanced_accuracy"], rnd["balanced_accuracy"]),
           "src_pctile_auc": pctile(src["auc"], rnd["auc"])}
    log(f"{name}: k={k} overlap={overlap:.2f} | own bacc={own['balanced_accuracy']:.3f} "
        f"src bacc={src['balanced_accuracy']:.3f} "
        f"rand bacc={rnd['balanced_accuracy']['mean']:.3f}±{rnd['balanced_accuracy']['sd']:.3f} "
        f"(src persentil {res['src_pctile_bacc']:.2f}) | "
        f"own AUC={own['auc']:.3f} src AUC={src['auc']:.3f} "
        f"rand AUC={rnd['auc']['mean']:.3f}")
    return res


def main():
    R = {"n_rand": N_RAND, "rungs": {}}
    for name, var, cols in RUNGS:
        Xo, yo = feats("ours", "train", var)
        Xov, yov = feats("ours", "val", var)
        Xc, yc = feats("cbis", "train", var)
        Xct, yct = feats("cbis", "test", var)
        R["rungs"][name] = {
            "n_features": len(cols),
            "ours_to_cbis": direction(f"{name} bizniki→CBIS", Xo, yo, Xc, yc, Xct, yct, cols),
            "cbis_to_ours": direction(f"{name} CBIS→bizniki", Xc, yc, Xo, yo, Xov, yov, cols),
        }
    (OUT / "subset_transfer.json").write_text(json.dumps(R, indent=1, default=float))
    log(f"saqlandi: {OUT}/subset_transfer.json")


if __name__ == "__main__":
    main()
