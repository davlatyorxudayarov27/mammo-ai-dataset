"""criterion.py — Xamdamov (3.2.2) kriteriy kattaliklari va Ф(λ) funksional.

Sinflar juftligi (p, q) va j-belgi uchun (kitobdagi (3.2.2)):

    a_j = Σ_{l=1..k_p} Σ_{t=1..k_q} (x_plj − x_qtj)²     — sinflararo tarqoqlik
    b_j = Σ_{l=1..k_p} Σ_{t=1..k_p} (x_plj − x_ptj)²     — p-sinf ichida
    c_j = Σ_{l=1..k_q} Σ_{t=1..k_q} (x_qlj − x_qtj)²     — q-sinf ichida

Vektorlashtirilgan hisob (ikki karra siklsiz, O(k)):
    Σ_l Σ_t (u_l − v_t)² = k_v·Σu² + k_u·Σv² − 2·(Σu)(Σv)
    Σ_l Σ_t (u_l − u_t)² = 2·k·Σu² − 2·(Σu)²

Funksional (kitobdagi Ф₁):
    Ф(λ) = Σ_j a_j·λ_j / Σ_j (b_j + c_j)·λ_j  → max,  λ_j ∈ {0,1}

Ko'p sinf (m=8) rejimlari:
    pairwise — har (p,q) juftlik alohida;
    global   — a_j = Σ_{p<q} a_j^{(pq)},  (b+c)_j = Σ_p (sinf ichidagi yig'indi).
"""
from __future__ import annotations

import numpy as np

_EPS = 1e-12


def pair_abc(Xp: np.ndarray, Xq: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(p, q) sinf juftligi uchun a_j, b_j, c_j vektorlari ((3.2.2), vektorlashgan).

    Xp: (k_p, n), Xq: (k_q, n). Qaytadi: a, b, c — har biri (n,).
    """
    Xp = np.asarray(Xp, dtype=np.float64)
    Xq = np.asarray(Xq, dtype=np.float64)
    kp, kq = Xp.shape[0], Xq.shape[0]
    sp, sq = Xp.sum(axis=0), Xq.sum(axis=0)
    sp2, sq2 = (Xp ** 2).sum(axis=0), (Xq ** 2).sum(axis=0)
    a = kq * sp2 + kp * sq2 - 2.0 * sp * sq
    b = 2.0 * kp * sp2 - 2.0 * sp ** 2
    c = 2.0 * kq * sq2 - 2.0 * sq ** 2
    return a, b, c


def intra_scatter(Xp: np.ndarray) -> np.ndarray:
    """Bitta sinf ichki tarqoqligi Σ_l Σ_t (x_l − x_t)² (b_j ko'rinishida), (n,)."""
    Xp = np.asarray(Xp, dtype=np.float64)
    kp = Xp.shape[0]
    s, s2 = Xp.sum(axis=0), (Xp ** 2).sum(axis=0)
    return 2.0 * kp * s2 - 2.0 * s ** 2


def global_abc(X: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """'global' rejim: a_j = Σ_{p<q} a_j^{(pq)};  w_j = (b+c)_j = Σ_p intra_p.

    Qaytadi: (a, w) — har biri (n,).
    """
    classes = np.unique(y)
    groups = {c: X[y == c] for c in classes}
    n = X.shape[1]
    a = np.zeros(n)
    for i, p in enumerate(classes):
        for q in classes[i + 1:]:
            apq, _, _ = pair_abc(groups[p], groups[q])
            a += apq
    w = np.zeros(n)
    for p in classes:
        w += intra_scatter(groups[p])
    return a, w


def phi(a: np.ndarray, w: np.ndarray, lam: np.ndarray) -> float:
    """Ф(λ) = Σ a_j λ_j / Σ w_j λ_j  (kitobdagi Ф₁). lam — {0,1} maska."""
    lam = np.asarray(lam, dtype=np.float64)
    num = float((a * lam).sum())
    den = float((w * lam).sum())
    return num / max(den, _EPS)


def pairwise_phi_matrix(X: np.ndarray, y: np.ndarray, lam: np.ndarray,
                        classes: np.ndarray | None = None) -> np.ndarray:
    """Sinf juftliklari ajraluvchanlik matritsasi (m x m, simmetrik):
    har (p,q) uchun tanlangan λ belgilar bo'yicha pairwise Ф^{(pq)}(λ).
    Diagonal — 0. Kichik Ф — sinflar belgi fazosida yomon ajraladi."""
    if classes is None:
        classes = np.unique(y)
    m = len(classes)
    M = np.zeros((m, m))
    groups = {c: X[y == c] for c in classes}
    for i in range(m):
        for j in range(i + 1, m):
            a, b, c = pair_abc(groups[classes[i]], groups[classes[j]])
            M[i, j] = M[j, i] = phi(a, b + c, lam)
    return M
