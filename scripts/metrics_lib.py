# -*- coding: utf-8 -*-
"""metrics_lib.py — tasniflash metrikalarining to'liq to'plami + bootstrap ishonch oraliqlari.

Ko'p sinfli (m = 8) holat uchun har bir sinf "bir-hammaga qarshi" (one-vs-rest) ko'rinishida
qaraladi; makro va vaznli o'rtachalar hisoblanadi.

    Sezgirlik (sensitivity, recall, TPR) = TP / (TP + FN)
    O'ziga xoslik (specificity, TNR)     = TN / (TN + FP)
    Aniqlik (precision, PPV)             = TP / (TP + FP)
    F1                                   = 2·PPV·TPR / (PPV + TPR)
    Muvozanatli aniqlik (balanced acc)   = makro sezgirlik
    Umumiy aniqlik (accuracy)            = to'g'ri tanilganlar / jami
    MCC, Cohen κ, ROC-AUC (OvR makro/vaznli)
"""
from __future__ import annotations

import numpy as np
from sklearn.metrics import (cohen_kappa_score, matthews_corrcoef,
                             roc_auc_score, roc_curve)

_EPS = 1e-12


def confusion(y_true, y_pred, m):
    M = np.zeros((m, m), dtype=np.int64)
    for t, p in zip(y_true, y_pred):
        M[int(t), int(p)] += 1
    return M


def per_class(y_true, y_pred, m):
    """Har sinf uchun TP/FP/FN/TN va hosila metrikalar."""
    M = confusion(y_true, y_pred, m)
    tot = M.sum()
    out = []
    for c in range(m):
        tp = int(M[c, c])
        fn = int(M[c].sum()) - tp
        fp = int(M[:, c].sum()) - tp
        tn = int(tot - tp - fn - fp)
        sup = tp + fn
        sens = tp / (tp + fn) if tp + fn else np.nan          # sezgirlik
        spec = tn / (tn + fp) if tn + fp else np.nan          # o'ziga xoslik
        prec = tp / (tp + fp) if tp + fp else np.nan          # aniqlik (PPV)
        npv = tn / (tn + fn) if tn + fn else np.nan
        f1 = (2 * prec * sens / (prec + sens)
              if prec == prec and sens == sens and (prec + sens) > 0 else np.nan)
        out.append({"class_idx": c, "support": sup, "tp": tp, "fp": fp, "fn": fn, "tn": tn,
                    "sensitivity": sens, "specificity": spec, "precision": prec,
                    "npv": npv, "f1": f1})
    return out, M


def _nanmean(vals, weights=None):
    v = np.asarray(vals, dtype=float)
    ok = np.isfinite(v)
    if not ok.any():
        return float("nan")
    if weights is None:
        return float(v[ok].mean())
    w = np.asarray(weights, dtype=float)[ok]
    return float((v[ok] * w).sum() / max(w.sum(), _EPS))


def auc_ovr(y_true, scores, m):
    """One-vs-rest ROC-AUC: makro va vaznli. Faqat mavjud sinflar bo'yicha."""
    present = [c for c in range(m) if (y_true == c).sum() > 0 and (y_true != c).sum() > 0]
    if not present:
        return float("nan"), float("nan"), {}
    per = {}
    for c in present:
        try:
            per[c] = float(roc_auc_score((y_true == c).astype(int), scores[:, c]))
        except ValueError:
            per[c] = float("nan")
    sup = [int((y_true == c).sum()) for c in present]
    macro = _nanmean([per[c] for c in present])
    weighted = _nanmean([per[c] for c in present], weights=sup)
    return macro, weighted, per


def summary(y_true, scores, m, class_names=None, with_auc=True):
    """Bitta bashorat to'plami uchun barcha metrikalar. with_auc=False → tezroq (bootstrap)."""
    y_true = np.asarray(y_true)
    y_pred = scores.argmax(axis=1)
    pc, M = per_class(y_true, y_pred, m)
    present = [d for d in pc if d["support"] > 0]
    sup = [d["support"] for d in present]

    acc = float((y_true == y_pred).mean())
    sens_macro = _nanmean([d["sensitivity"] for d in present])
    spec_macro = _nanmean([d["specificity"] for d in present])
    prec_macro = _nanmean([d["precision"] for d in present])
    f1_macro = _nanmean([d["f1"] for d in present])
    sens_w = _nanmean([d["sensitivity"] for d in present], weights=sup)
    prec_w = _nanmean([d["precision"] for d in present], weights=sup)
    f1_w = _nanmean([d["f1"] for d in present], weights=sup)
    if with_auc:
        auc_m, auc_w, auc_per = auc_ovr(y_true, scores, m)
    else:
        auc_m = auc_w = float("nan")
        auc_per = {}

    res = {
        "n": int(len(y_true)),
        "accuracy": acc,
        "balanced_accuracy": sens_macro,          # = makro sezgirlik
        "sensitivity_macro": sens_macro,
        "specificity_macro": spec_macro,
        "precision_macro": prec_macro,
        "f1_macro": f1_macro,
        "sensitivity_weighted": sens_w,
        "precision_weighted": prec_w,
        "f1_weighted": f1_w,
        "auc_macro": auc_m,
        "auc_weighted": auc_w,
        "mcc": float(matthews_corrcoef(y_true, y_pred)),
        "kappa": float(cohen_kappa_score(y_true, y_pred)),
        "confusion": M.tolist(),
        "per_class": pc,
        "auc_per_class": {str(k): v for k, v in auc_per.items()},
    }
    if class_names:
        for d in res["per_class"]:
            d["class"] = class_names[d["class_idx"]]
    return res


# ------------------------------------------------------------ bootstrap --- #
_METRIC_KEYS = ("accuracy", "balanced_accuracy", "sensitivity_macro", "specificity_macro",
                "precision_macro", "f1_macro", "auc_macro", "mcc", "kappa")


def bootstrap_ci(y_true, scores, m, n_boot=2000, seed=42, keys=_METRIC_KEYS):
    """Stratifikatsiyalanmagan bootstrap (obyektlar bo'yicha qayta tanlash), 95% CI."""
    rng = np.random.default_rng(seed)
    y_true = np.asarray(y_true)
    n = len(y_true)
    acc = {k: [] for k in keys}
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        yt, sc = y_true[idx], scores[idx]
        if len(np.unique(yt)) < 2:
            continue
        s = summary(yt, sc, m, with_auc=("auc_macro" in keys))
        for k in keys:
            v = s[k]
            if v == v:          # NaN emas
                acc[k].append(v)
    out = {}
    for k in keys:
        a = np.asarray(acc[k], dtype=float)
        if a.size == 0:
            out[k] = {"lo": float("nan"), "hi": float("nan")}
        else:
            out[k] = {"lo": float(np.percentile(a, 2.5)),
                      "hi": float(np.percentile(a, 97.5))}
    return out


def bootstrap_delta(y_true, scores_a, scores_b, m, key="accuracy", n_boot=2000, seed=42):
    """B − A farqi uchun bootstrap CI va p-qiymat (juftlashgan, bir xil indekslar)."""
    rng = np.random.default_rng(seed)
    y_true = np.asarray(y_true)
    n = len(y_true)
    d = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        yt = y_true[idx]
        if len(np.unique(yt)) < 2:
            continue
        wa = key.startswith("auc")
        a = summary(yt, scores_a[idx], m, with_auc=wa)[key]
        b = summary(yt, scores_b[idx], m, with_auc=wa)[key]
        if a == a and b == b:
            d.append(b - a)
    d = np.asarray(d)
    if d.size == 0:
        return {"delta": float("nan"), "lo": float("nan"), "hi": float("nan"), "p": float("nan")}
    obs = (summary(y_true, scores_b, m)[key] - summary(y_true, scores_a, m)[key])
    # ikki tomonlama bootstrap p: nol farq gipotezasini rad etish ulushi
    p = 2.0 * min((d <= 0).mean(), (d >= 0).mean())
    return {"delta": float(obs), "lo": float(np.percentile(d, 2.5)),
            "hi": float(np.percentile(d, 97.5)), "p": float(min(1.0, p))}


def roc_macro(y_true, scores, m, grid=None):
    """Makro-o'rtacha ROC egri chizig'i (umumiy FPR setkasida interpolatsiya)."""
    y_true = np.asarray(y_true)
    grid = np.linspace(0, 1, 101) if grid is None else grid
    tprs = []
    for c in range(m):
        pos = (y_true == c).sum()
        if pos == 0 or pos == len(y_true):
            continue
        fpr, tpr, _ = roc_curve((y_true == c).astype(int), scores[:, c])
        tprs.append(np.interp(grid, fpr, tpr))
    if not tprs:
        return grid, np.full_like(grid, np.nan)
    return grid, np.mean(tprs, axis=0)
