# -*- coding: utf-8 -*-
"""Radiomika asosidagi benign / malignant (xavfsiz / xavfli) klassifikatori.

Kirish: bitta ROI (massa) radiomika belgilari (radiomics.extract natijasi) +
ixtiyoriy BI-RADS. Chiqish: P(malignant) — xavfli o'simta ehtimoli.

DIQQAT (klinik xavfsizlik): bu QAROR QO'LLAB-QUVVATLASH vositasi, tashxis emas.
Yorliqlar (benign/malignant) PATOLOGIYA (biopsiya) bilan tasdiqlangan bo'lishi
shart — shundagina BI-RADS'ni belgi sifatida qo'shish to'g'ri ("leakage" yo'q).
Yakuniy qarorni radiolog qabul qiladi.

O'qitish offline (scripts/train_radiomics_clf.py) amalga oshiriladi; veb faqat
inference (predict_one) va holatni (model_info) qaytaradi.
"""
from __future__ import annotations

import datetime as _dt
from pathlib import Path
from typing import Optional

import numpy as np

MODEL_PATH = Path(__file__).resolve().parent / "models" / "radiomics_clf.joblib"

# BI-RADS kategoriyasi -> tartibli (ordinal) son. Yetishmasa NaN (imputer to'ldiradi).
BIRADS_ORD = {
    "0": 0, "1": 1, "2": 2, "3": 3,
    "4": 4, "4A": 4, "4B": 5, "4C": 6, "5": 7, "6": 8,
}
_BIRADS_FEATURE = "clinical.birads"


# ----------------------------- belgilar -----------------------------

def flatten_features(feat: dict) -> tuple[list[str], list[float]]:
    """radiomics.extract() ning ichma-ich dict'ini tartiblangan (nomlar, qiymatlar)
    ga aylantiradi. Tartib deterministik (guruh nomi, keyin belgi nomi bo'yicha)."""
    names: list[str] = []
    vals: list[float] = []
    for group in sorted(feat):
        d = feat[group]
        if not isinstance(d, dict):
            continue
        for k in sorted(d):
            v = d[k]
            names.append(f"{group}.{k}")
            try:
                fv = float(v)
            except (TypeError, ValueError):
                fv = np.nan
            vals.append(fv if np.isfinite(fv) else np.nan)
    return names, vals


def birads_ordinal(bi_rads: Optional[str]) -> float:
    if bi_rads is None:
        return np.nan
    return float(BIRADS_ORD.get(str(bi_rads).strip().upper(), np.nan))


def build_feature_row(feat: dict, bi_rads: Optional[str], use_birads: bool) -> tuple[list[str], list[float]]:
    """Bitta ROI uchun (nomlar, qiymatlar) — ixtiyoriy BI-RADS belgisi bilan."""
    names, vals = flatten_features(feat)
    if use_birads:
        names.append(_BIRADS_FEATURE)
        vals.append(birads_ordinal(bi_rads))
    return names, vals


# ----------------------------- o'qitish -----------------------------

def _make_pipeline(model_type: str):
    from sklearn.pipeline import Pipeline
    from sklearn.impute import SimpleImputer
    from sklearn.preprocessing import StandardScaler

    if model_type == "rf":
        from sklearn.ensemble import RandomForestClassifier
        clf = RandomForestClassifier(
            n_estimators=400, class_weight="balanced", random_state=42, n_jobs=-1)
    elif model_type == "gb":
        from sklearn.ensemble import GradientBoostingClassifier
        clf = GradientBoostingClassifier(random_state=42)
    else:  # "logreg" — kichik ma'lumotda mustahkam, kalibrlangan ehtimol
        from sklearn.linear_model import LogisticRegression
        clf = LogisticRegression(max_iter=4000, class_weight="balanced", C=1.0)
    return Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
        ("clf", clf),
    ])


def train(feature_names: list[str], rows: list[list[float]], y: list[int],
          use_birads: bool = True, model_type: str = "logreg") -> tuple[object, dict]:
    """Pipeline'ni o'qitadi va (pipeline, metrikalar) qaytaradi.

    rows — har bir namuna uchun feature_names tartibidagi qiymatlar.
    y     — 0=benign, 1=malignant.
    """
    from sklearn.metrics import roc_auc_score, accuracy_score
    from sklearn.model_selection import StratifiedKFold, cross_val_predict

    X = np.asarray(rows, dtype=float)
    y = np.asarray(y, dtype=int)
    n = int(len(y))
    pos = int((y == 1).sum())
    neg = int((y == 0).sum())
    if n < 4 or pos < 1 or neg < 1:
        raise ValueError(
            f"o'qitishga yetarli emas: jami={n}, malignant={pos}, benign={neg} "
            "(har sinfdan kamida 1 ta, jami >=4 kerak)")

    metrics: dict = {
        "n": n, "malignant": pos, "benign": neg,
        "model_type": model_type, "use_birads": use_birads,
        "n_features": int(X.shape[1]),
    }

    # Cross-validation AUC (har sinfda >=2 namuna bo'lsa)
    k = min(5, pos, neg)
    if k >= 2:
        cv = StratifiedKFold(n_splits=k, shuffle=True, random_state=42)
        try:
            proba = cross_val_predict(
                _make_pipeline(model_type), X, y, cv=cv, method="predict_proba")[:, 1]
            metrics["cv_auc"] = round(float(roc_auc_score(y, proba)), 4)
            metrics["cv_acc"] = round(float(accuracy_score(y, (proba >= 0.5).astype(int))), 4)
            metrics["cv_folds"] = int(k)
        except Exception as e:  # noqa: BLE001
            metrics["cv_note"] = f"CV o'tkazilmadi: {e}"
    else:
        metrics["cv_note"] = "CV uchun har sinfda kamida 2 namuna kerak"

    pipe = _make_pipeline(model_type)
    pipe.fit(X, y)
    return pipe, metrics


def save_model(pipeline, feature_names: list[str], use_birads: bool,
               metrics: dict, model_type: str) -> None:
    import joblib
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    bundle = {
        "pipeline": pipeline,
        "feature_names": list(feature_names),
        "use_birads": bool(use_birads),
        "model_type": model_type,
        "metrics": metrics,
        "trained_at": _dt.datetime.now().isoformat(timespec="seconds"),
        "version": 1,
    }
    joblib.dump(bundle, MODEL_PATH)


# ----------------------------- inference -----------------------------

_CACHE: dict = {"mtime": None, "bundle": None}


def _load_bundle():
    if not MODEL_PATH.exists():
        return None
    mtime = MODEL_PATH.stat().st_mtime_ns
    if _CACHE["bundle"] is not None and _CACHE["mtime"] == mtime:
        return _CACHE["bundle"]
    import joblib
    bundle = joblib.load(MODEL_PATH)
    _CACHE["mtime"] = mtime
    _CACHE["bundle"] = bundle
    return bundle


def is_trained() -> bool:
    return MODEL_PATH.exists()


def model_info() -> dict:
    bundle = _load_bundle()
    if bundle is None:
        return {"trained": False}
    return {
        "trained": True,
        "trained_at": bundle.get("trained_at"),
        "model_type": bundle.get("model_type"),
        "use_birads": bundle.get("use_birads"),
        "metrics": bundle.get("metrics", {}),
        "n_features": len(bundle.get("feature_names", [])),
    }


def predict_one(feat: dict, bi_rads: Optional[str] = None) -> dict:
    """Bitta ROI uchun bashorat. Model o'qitilmagan bo'lsa RuntimeError."""
    bundle = _load_bundle()
    if bundle is None:
        raise RuntimeError("klassifikator hali o'qitilmagan")

    names, vals = build_feature_row(feat, bi_rads, bundle["use_birads"])
    by_name = dict(zip(names, vals))
    # O'qitishdagi aynan shu tartib/belgilar bo'yicha qatorni tuzamiz
    row = [by_name.get(n, np.nan) for n in bundle["feature_names"]]

    pipe = bundle["pipeline"]
    proba = pipe.predict_proba([row])[0]
    classes = list(getattr(pipe, "classes_", [0, 1]))
    p_mal = float(proba[classes.index(1)]) if 1 in classes else float(proba[-1])
    p_ben = 1.0 - p_mal

    label = "malignant" if p_mal >= 0.5 else "benign"
    conf = max(p_mal, p_ben)
    return {
        "p_malignant": round(p_mal, 4),
        "p_benign": round(p_ben, 4),
        "label": label,
        "label_uz": "xavfli (malignant)" if label == "malignant" else "xavfsiz (benign)",
        "confidence": round(conf, 4),
        "used_birads": bool(bundle["use_birads"]),
        "model_type": bundle.get("model_type"),
        "cv_auc": bundle.get("metrics", {}).get("cv_auc"),
    }
