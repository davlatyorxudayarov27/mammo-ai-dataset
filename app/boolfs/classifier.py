"""classifier.py — minimal masofa klassifikatori (kitob 3.6.2-3.6.4).

Har sinf p uchun etalon x̄ᵖ (train o'rtacha vektori) va ichki tarqoqlik
S(X_p) hisoblanadi. Yangi obyekt x uchun ((3.6.2)-(3.6.3)):

    ρ_p(x) = Σ_j λ_j·(x_j − x̄ᵖ_j)² / S(X_p)
    sinf(x) = argmin_p ρ_p(x)

Bu yerda S(X_p) — sinf a'zolarining etalondan o'rtacha kvadrat chetlanishi
(tanlangan λ belgilar bo'yicha): S(X_p) = (1/k_p)·Σ_l Σ_j λ_j (x_plj − x̄ᵖ_j)².
k_p = 1 yoki S = 0 chekka holatida boshqa sinflar S'ining medianasi olinadi
(masofa masshtabi buzilmasin).

Ishonchlilik o'lchovi ((3.6.4)): P = to'g'ri tanilganlar / jami.
CV sxemasi: k_p < 5 sinflar leave-one-out, qolganlar stratified 5-fold.
Ensemble uchun softmax score: s_p = exp(−ρ_p) / Σ_q exp(−ρ_q).
"""
from __future__ import annotations

import numpy as np

_EPS = 1e-12
_SMALL_CLASS = 5      # k_p < 5 -> leave-one-out (masalan architectural_distortion)


class MinDistClassifier:
    """Minimal masofa qoidasi (3.6.3) — etalonlar + sinf ichki tarqoqlik."""

    def __init__(self):
        self.classes_: np.ndarray | None = None
        self.centroids_: np.ndarray | None = None   # (m, n)
        self.scatters_: np.ndarray | None = None    # (m,)
        self.lam_: np.ndarray | None = None         # (n,) {0,1}

    def fit(self, X: np.ndarray, y: np.ndarray, lam: np.ndarray) -> "MinDistClassifier":
        X = np.asarray(X, dtype=np.float64)
        y = np.asarray(y)
        self.lam_ = np.asarray(lam, dtype=np.float64)
        self.classes_ = np.unique(y)
        cents, scats = [], []
        for c in self.classes_:
            Xc = X[y == c]
            mu = Xc.mean(axis=0)
            cents.append(mu)
            if Xc.shape[0] > 1:
                d2 = ((Xc - mu) ** 2 * self.lam_).sum(axis=1)
                scats.append(float(d2.mean()))
            else:
                scats.append(np.nan)                 # keyin mediana bilan to'ldiriladi
        scats = np.asarray(scats, dtype=np.float64)
        good = scats[np.isfinite(scats) & (scats > _EPS)]
        fallback = float(np.median(good)) if good.size else 1.0
        scats[~np.isfinite(scats) | (scats <= _EPS)] = fallback
        self.centroids_ = np.asarray(cents)
        self.scatters_ = scats
        return self

    def rho(self, X: np.ndarray) -> np.ndarray:
        """ρ_p(x) matritsasi (N, m) — (3.6.2)."""
        X = np.atleast_2d(np.asarray(X, dtype=np.float64))
        diff2 = (X[:, None, :] - self.centroids_[None, :, :]) ** 2   # (N, m, n)
        d = (diff2 * self.lam_[None, None, :]).sum(axis=2)           # (N, m)
        return d / self.scatters_[None, :]

    def predict(self, X: np.ndarray) -> np.ndarray:
        """(3.6.3): sinf(x) = argmin_p ρ_p(x)."""
        return self.classes_[np.argmin(self.rho(X), axis=1)]

    def scores(self, X: np.ndarray) -> np.ndarray:
        """Softmax score s_p = exp(−ρ_p)/Σ exp(−ρ_q) — ensemble uchun (N, m)."""
        r = self.rho(X)
        r = r - r.min(axis=1, keepdims=True)         # sonli barqarorlik
        e = np.exp(-r)
        return e / e.sum(axis=1, keepdims=True)

    def to_dict(self) -> dict:
        return {"classes": self.classes_.tolist(),
                "centroids": self.centroids_.tolist(),
                "scatters": self.scatters_.tolist(),
                "lam": self.lam_.tolist()}

    @classmethod
    def from_dict(cls, d: dict) -> "MinDistClassifier":
        m = cls()
        m.classes_ = np.asarray(d["classes"])
        m.centroids_ = np.asarray(d["centroids"], dtype=np.float64)
        m.scatters_ = np.asarray(d["scatters"], dtype=np.float64)
        m.lam_ = np.asarray(d["lam"], dtype=np.float64)
        return m


def p_criterion(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """(3.6.4): P = to'g'ri tanilganlar / jami."""
    y_true = np.asarray(y_true)
    return float((y_true == np.asarray(y_pred)).mean()) if y_true.size else 0.0


def _make_folds(y: np.ndarray, n_folds: int = 5, seed: int = 42) -> list[np.ndarray]:
    """Aralash CV bo'linishi: kichik sinflar (k_p < 5) — LOO (har namunasi
    alohida fold'da), qolganlar — stratified n-fold."""
    rng = np.random.default_rng(seed)
    y = np.asarray(y)
    fold_of = np.full(y.shape[0], -1, dtype=np.int64)
    next_loo = n_folds
    for c in np.unique(y):
        idx = np.where(y == c)[0]
        if idx.size < _SMALL_CLASS:
            for i in idx:                       # LOO — har biri o'z fold'i
                fold_of[i] = next_loo
                next_loo += 1
        else:
            perm = rng.permutation(idx)
            for pos, i in enumerate(perm):      # stratified: sinf ichida aylanma
                fold_of[i] = pos % n_folds
    return [np.where(fold_of == f)[0] for f in range(next_loo)
            if (fold_of == f).any()]


def cv_predictions(X: np.ndarray, y: np.ndarray, lam: np.ndarray,
                   n_folds: int = 5, seed: int = 42) -> np.ndarray:
    """Har namunaga CV-bashorat (o'zi qatnashmagan modeldan)."""
    X = np.asarray(X, dtype=np.float64)
    y = np.asarray(y)
    pred = np.empty_like(y)
    for test_idx in _make_folds(y, n_folds=n_folds, seed=seed):
        train_mask = np.ones(y.shape[0], dtype=bool)
        train_mask[test_idx] = False
        clf = MinDistClassifier().fit(X[train_mask], y[train_mask], lam)
        pred[test_idx] = clf.predict(X[test_idx])
    return pred


def cv_P(X: np.ndarray, y: np.ndarray, lam: np.ndarray,
         n_folds: int = 5, seed: int = 42) -> float:
    """P(λ) — CV bo'yicha (3.6.4) ishonchlilik."""
    return p_criterion(y, cv_predictions(X, y, lam, n_folds=n_folds, seed=seed))
