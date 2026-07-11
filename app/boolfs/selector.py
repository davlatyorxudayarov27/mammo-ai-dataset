"""selector.py — umumlashgan tengsizliklar (ranjirlangan qator) usuli (kitob 3.4).

1. Belgilar r_j = a_j / (b_j + c_j) nisbati bo'yicha KAMAYISH tartibida
   ranjirlanadi — kitobdagi (3.4.5) qator.
2. (3.4.4) tengsizliklar zanjiri: ranjirlangan qator prefikslarida
   Ф(1) ≥ Ф(2) ≥ ... ≥ Ф(n) — har n' uchun to'plam sifatida dastlabki n'
   element olinadi; Ф(n') qiymatlari prefiks-yig'indilar bilan O(n) da
   hisoblanadi. (Qat'iy |S|=n' bo'yicha mutlaq optimallik emas — usulning
   asosi shu zanjir; yakuniy tanlov baribir P(n') bo'yicha.)
3. Yakuniy n'* Ф bo'yicha emas, klassifikatsiya sifati bo'yicha tanlanadi:
   P(n'*) = max_{n'} P(n')  (kitob 3.6.4 prinsipi) — classifier.cv_P bilan.
"""
from __future__ import annotations

import numpy as np

_EPS = 1e-12


def rank_features(a: np.ndarray, w: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """(3.4.5): r_j = a_j / w_j bo'yicha kamayish tartibi.

    w_j = 0 chekka holatlari: a_j > 0 bo'lsa belgi sinflarni "ideal" ajratadi
    (r = +inf, qator boshiga), a_j = 0 bo'lsa belgi ma'lumotsiz (r = 0, oxiriga).
    Qaytadi: (order — indekslar, r — nisbatlar asl tartibda).
    """
    a = np.asarray(a, dtype=np.float64)
    w = np.asarray(w, dtype=np.float64)
    r = np.where(w > _EPS, a / np.maximum(w, _EPS),
                 np.where(a > _EPS, np.inf, 0.0))
    order = np.argsort(-r, kind="stable")
    return order, r


def phi_prefix_curve(a: np.ndarray, w: np.ndarray,
                     order: np.ndarray) -> np.ndarray:
    """Ф(n') qiymatlari, n' = 1..n — ranjirlangan qator prefikslari bo'yicha
    ((3.4.4) zanjirga mos, prefiks-yig'indilar bilan)."""
    ca = np.cumsum(a[order])
    cw = np.cumsum(w[order])
    return ca / np.maximum(cw, _EPS)


def prefix_mask(order: np.ndarray, n_sel: int, n_total: int) -> np.ndarray:
    """Ranjirlangan qatorning dastlabki n_sel belgisi uchun λ maskasi ({0,1})."""
    lam = np.zeros(n_total, dtype=np.float64)
    lam[order[:n_sel]] = 1.0
    return lam


def selection_table(a: np.ndarray, w: np.ndarray, order: np.ndarray,
                    names: list[str]) -> list[dict]:
    """Har bir n' uchun (tanlangan belgilar, Ф) jadvali (4-band, 3-punkt)."""
    phis = phi_prefix_curve(a, w, order)
    r = np.where(w > _EPS, a / np.maximum(w, _EPS), 0.0)
    rows = []
    for i, j in enumerate(order):
        rows.append({
            "n": i + 1,
            "feature": names[int(j)],
            "r_j": float(r[int(j)]) if np.isfinite(r[int(j)]) else None,
            "phi_prefix": float(phis[i]),
        })
    return rows
