"""IBSI-inspired 2D radiomics feature extraction (self-contained).

Extracts quantitative features from a region of interest (ROI) drawn on a
single DICOM frame. Six feature families are computed:

  * first-order (intensity statistics)
  * shape (2D morphology)
  * GLCM   — gray-level co-occurrence matrix (texture)
  * GLRLM  — gray-level run-length matrix
  * GLSZM  — gray-level size-zone matrix
  * NGTDM  — neighbouring gray-tone difference matrix

The implementation depends only on numpy / scipy / scikit-image (no
PyRadiomics), so it installs cleanly on modern Python. Intensities inside the
ROI are discretised to a fixed number of bins for the texture matrices.

Note: research/quantitative use. Values are reproducible but this module is
not a certified IBSI reference implementation.
"""
from __future__ import annotations

import math
from typing import Optional

import numpy as np
from scipy import ndimage
from skimage.draw import polygon as sk_polygon
from skimage.measure import label as sk_label
from skimage.measure import regionprops

EPS = 1e-9


# --------------------------------------------------------------------------- #
# ROI mask                                                                    #
# --------------------------------------------------------------------------- #
def roi_mask_from_annotation(ann: dict, rows: int, cols: int) -> np.ndarray:
    """Build a boolean ROI mask (rows×cols) from a bbox or polygon annotation.

    Coordinates in annotations are normalised (0..1).
    """
    mask = np.zeros((rows, cols), dtype=bool)
    if ann.get("type") == "polygon" and ann.get("points"):
        ys = np.array([min(max(p[1], 0.0), 1.0) * (rows - 1) for p in ann["points"]])
        xs = np.array([min(max(p[0], 0.0), 1.0) * (cols - 1) for p in ann["points"]])
        rr, cc = sk_polygon(ys, xs, shape=(rows, cols))
        mask[rr, cc] = True
    else:
        bbox = ann.get("bbox")
        if not bbox or len(bbox) != 4:
            return mask
        x, y, w, h = bbox
        x0 = int(round(max(0.0, x) * cols))
        y0 = int(round(max(0.0, y) * rows))
        x1 = int(round(min(1.0, x + w) * cols))
        y1 = int(round(min(1.0, y + h) * rows))
        x1 = max(x1, x0 + 1)
        y1 = max(y1, y0 + 1)
        mask[y0:min(y1, rows), x0:min(x1, cols)] = True
    return mask


def _discretise(values: np.ndarray, bins: int) -> tuple[np.ndarray, float, float]:
    mn = float(values.min())
    mx = float(values.max())
    if mx <= mn:
        return np.ones_like(values, dtype=int), mn, mx
    lvl = np.floor((values - mn) / (mx - mn) * (bins - 1)).astype(int) + 1
    lvl = np.clip(lvl, 1, bins)
    return lvl, mn, mx


# --------------------------------------------------------------------------- #
# First-order                                                                 #
# --------------------------------------------------------------------------- #
def _first_order(vals: np.ndarray, bins: int, voxel_area: float) -> dict:
    n = vals.size
    mean = float(vals.mean())
    var = float(vals.var())
    std = math.sqrt(var)
    diffs = vals - mean
    m3 = float((diffs ** 3).mean())
    m4 = float((diffs ** 4).mean())
    skew = m3 / (std ** 3 + EPS)
    kurt = m4 / (var ** 2 + EPS)
    p10, p25, p50, p75, p90 = (float(np.percentile(vals, q)) for q in (10, 25, 50, 75, 90))
    rng = float(vals.max() - vals.min())
    mad = float(np.abs(diffs).mean())
    robust = vals[(vals >= p10) & (vals <= p90)]
    rmad = float(np.abs(robust - robust.mean()).mean()) if robust.size else 0.0
    energy = float((vals ** 2).sum())
    rms = math.sqrt(float((vals ** 2).mean()))

    disc, _, _ = _discretise(vals, bins)
    counts = np.bincount(disc, minlength=bins + 1)[1:]
    p = counts / max(counts.sum(), 1)
    nz = p[p > 0]
    entropy = float(-(nz * np.log2(nz)).sum())
    uniformity = float((p ** 2).sum())

    return {
        "voxel_count": float(n),
        "mean": mean,
        "median": p50,
        "minimum": float(vals.min()),
        "maximum": float(vals.max()),
        "range": rng,
        "variance": var,
        "std_dev": std,
        "skewness": skew,
        "kurtosis": kurt,
        "p10": p10,
        "p90": p90,
        "interquartile_range": p75 - p25,
        "mean_abs_deviation": mad,
        "robust_mean_abs_deviation": rmad,
        "energy": energy,
        "total_energy": energy * voxel_area,
        "rms": rms,
        "entropy": entropy,
        "uniformity": uniformity,
    }


# --------------------------------------------------------------------------- #
# Shape (2D)                                                                  #
# --------------------------------------------------------------------------- #
def _rp(prop, *names):
    """Read a regionprops attribute, tolerating skimage's renamed properties."""
    for n in names:
        try:
            return float(getattr(prop, n))
        except Exception:
            continue
    return 0.0


def _shape(mask: np.ndarray, spacing: tuple[float, float]) -> dict:
    sy, sx = spacing
    lab = mask.astype(int)
    props = regionprops(lab)
    if not props:
        return {}
    p = max(props, key=lambda r: r.area)
    area_px = float(p.area)
    perim_px = float(p.perimeter) if p.perimeter else 0.0
    mean_sp = (sy + sx) / 2.0
    circularity = (4 * math.pi * area_px) / (perim_px ** 2) if perim_px > 0 else 0.0
    feret = _rp(p, "feret_diameter_max") * mean_sp
    major = _rp(p, "axis_major_length", "major_axis_length")
    minor = _rp(p, "axis_minor_length", "minor_axis_length")
    eqdiam = _rp(p, "equivalent_diameter_area", "equivalent_diameter")
    return {
        "pixel_area": area_px,
        "physical_area_mm2": area_px * sy * sx,
        "perimeter_px": perim_px,
        "physical_perimeter_mm": perim_px * mean_sp,
        "circularity": float(circularity),
        "equivalent_diameter_mm": eqdiam * mean_sp,
        "major_axis_length_mm": major * mean_sp,
        "minor_axis_length_mm": minor * mean_sp,
        "elongation": float(minor / (major + EPS)),
        "eccentricity": float(p.eccentricity),
        "orientation_rad": float(p.orientation),
        "extent": float(p.extent),
        "solidity": float(p.solidity),
        "max_feret_mm": feret,
    }


# --------------------------------------------------------------------------- #
# GLCM                                                                        #
# --------------------------------------------------------------------------- #
_GLCM_DIRS = [(0, 1), (-1, 1), (-1, 0), (-1, -1)]


def _glcm(disc: np.ndarray, ng: int) -> dict:
    P = np.zeros((ng, ng), dtype=np.float64)
    H, W = disc.shape
    for dy, dx in _GLCM_DIRS:
        ys0, ys1 = max(0, -dy), H - max(0, dy)
        xs0, xs1 = max(0, -dx), W - max(0, dx)
        A = disc[ys0:ys1, xs0:xs1]
        B = disc[ys0 + dy:ys1 + dy, xs0 + dx:xs1 + dx]
        valid = (A > 0) & (B > 0)
        ai = A[valid] - 1
        bi = B[valid] - 1
        np.add.at(P, (ai, bi), 1)
        np.add.at(P, (bi, ai), 1)  # symmetric
    total = P.sum()
    if total <= 0:
        return {k: 0.0 for k in ("contrast", "dissimilarity", "homogeneity",
                                   "asm", "energy", "entropy", "correlation")}
    P /= total
    idx = np.arange(1, ng + 1)
    I, J = np.meshgrid(idx, idx, indexing="ij")
    diff = I - J
    contrast = float((P * diff ** 2).sum())
    dissim = float((P * np.abs(diff)).sum())
    homog = float((P / (1.0 + diff ** 2)).sum())
    asm = float((P ** 2).sum())
    nz = P[P > 0]
    entropy = float(-(nz * np.log2(nz)).sum())
    mu_i = float((P * I).sum())
    mu_j = float((P * J).sum())
    sig_i = math.sqrt(float((P * (I - mu_i) ** 2).sum()))
    sig_j = math.sqrt(float((P * (J - mu_j) ** 2).sum()))
    corr = float((P * (I - mu_i) * (J - mu_j)).sum() / (sig_i * sig_j)) if sig_i > 0 and sig_j > 0 else 0.0
    return {
        "contrast": contrast,
        "dissimilarity": dissim,
        "homogeneity": homog,
        "asm": asm,
        "energy": math.sqrt(asm),
        "entropy": entropy,
        "correlation": corr,
    }


# --------------------------------------------------------------------------- #
# GLRLM                                                                       #
# --------------------------------------------------------------------------- #
def _iter_lines(disc: np.ndarray):
    H, W = disc.shape
    for r in range(H):                       # horizontal
        yield disc[r, :]
    for c in range(W):                       # vertical
        yield disc[:, c]
    for off in range(-H + 1, W):             # main diagonal
        yield np.diagonal(disc, offset=off)
    flipped = disc[:, ::-1]
    for off in range(-H + 1, W):             # anti-diagonal
        yield np.diagonal(flipped, offset=off)


def _glrlm(disc: np.ndarray, ng: int, np_voxels: int) -> dict:
    max_len = max(disc.shape)
    R = np.zeros((ng, max_len), dtype=np.float64)
    for line in _iter_lines(disc):
        if line.size == 0:
            continue
        prev = line[0]
        run = 1
        for v in line[1:]:
            if v == prev and v > 0:
                run += 1
            else:
                if prev > 0:
                    R[prev - 1, run - 1] += 1
                prev = v
                run = 1
        if prev > 0:
            R[prev - 1, run - 1] += 1

    nr = R.sum()
    if nr <= 0:
        return {k: 0.0 for k in ("short_run_emphasis", "long_run_emphasis",
                                   "gray_level_nonuniformity", "run_length_nonuniformity",
                                   "run_percentage", "low_gray_level_run_emphasis",
                                   "high_gray_level_run_emphasis")}
    g = np.arange(1, ng + 1)[:, None]
    r = np.arange(1, max_len + 1)[None, :]
    sre = float((R / r ** 2).sum() / nr)
    lre = float((R * r ** 2).sum() / nr)
    gln = float((R.sum(axis=1) ** 2).sum() / nr)
    rln = float((R.sum(axis=0) ** 2).sum() / nr)
    rp = float(nr / max(np_voxels, 1))
    lglre = float((R / g ** 2).sum() / nr)
    hglre = float((R * g ** 2).sum() / nr)
    return {
        "short_run_emphasis": sre,
        "long_run_emphasis": lre,
        "gray_level_nonuniformity": gln,
        "run_length_nonuniformity": rln,
        "run_percentage": rp,
        "low_gray_level_run_emphasis": lglre,
        "high_gray_level_run_emphasis": hglre,
    }


# --------------------------------------------------------------------------- #
# GLSZM                                                                       #
# --------------------------------------------------------------------------- #
def _glszm(disc: np.ndarray, ng: int, np_voxels: int) -> dict:
    zones: dict[tuple[int, int], int] = {}
    max_size = 1
    struct = np.ones((3, 3), dtype=int)  # 8-connectivity
    for gl in range(1, ng + 1):
        bw = disc == gl
        if not bw.any():
            continue
        lab, n = ndimage.label(bw, structure=struct)
        if n == 0:
            continue
        sizes = np.bincount(lab.ravel())[1:]
        for s in sizes:
            s = int(s)
            zones[(gl, s)] = zones.get((gl, s), 0) + 1
            max_size = max(max_size, s)

    nz = sum(zones.values())
    if nz <= 0:
        return {k: 0.0 for k in ("small_area_emphasis", "large_area_emphasis",
                                   "gray_level_nonuniformity", "zone_size_nonuniformity",
                                   "zone_percentage", "low_gray_level_zone_emphasis",
                                   "high_gray_level_zone_emphasis")}
    Z = np.zeros((ng, max_size), dtype=np.float64)
    for (gl, s), c in zones.items():
        Z[gl - 1, s - 1] += c
    g = np.arange(1, ng + 1)[:, None]
    s = np.arange(1, max_size + 1)[None, :]
    return {
        "small_area_emphasis": float((Z / s ** 2).sum() / nz),
        "large_area_emphasis": float((Z * s ** 2).sum() / nz),
        "gray_level_nonuniformity": float((Z.sum(axis=1) ** 2).sum() / nz),
        "zone_size_nonuniformity": float((Z.sum(axis=0) ** 2).sum() / nz),
        "zone_percentage": float(nz / max(np_voxels, 1)),
        "low_gray_level_zone_emphasis": float((Z / g ** 2).sum() / nz),
        "high_gray_level_zone_emphasis": float((Z * g ** 2).sum() / nz),
    }


# --------------------------------------------------------------------------- #
# NGTDM                                                                       #
# --------------------------------------------------------------------------- #
def _ngtdm(disc: np.ndarray, mask: np.ndarray, ng: int) -> dict:
    kernel = np.ones((3, 3), dtype=np.float64)
    kernel[1, 1] = 0.0
    m = mask.astype(np.float64)
    vals = disc.astype(np.float64) * m
    neigh_sum = ndimage.convolve(vals, kernel, mode="constant", cval=0.0)
    neigh_cnt = ndimage.convolve(m, kernel, mode="constant", cval=0.0)
    valid = mask & (neigh_cnt > 0)
    avg = np.zeros_like(vals)
    avg[valid] = neigh_sum[valid] / neigh_cnt[valid]

    s = np.zeros(ng + 1)
    nvec = np.zeros(ng + 1)
    gi = disc[valid]
    diff = np.abs(gi - avg[valid])
    np.add.at(s, gi, diff)
    np.add.at(nvec, gi, 1.0)
    nv = nvec.sum()
    if nv <= 0:
        return {k: 0.0 for k in ("coarseness", "contrast", "busyness",
                                   "complexity", "strength")}
    p = nvec / nv
    present = np.where(nvec > 0)[0]
    ngp = present.size

    coarseness = 1.0 / (float((p * s).sum()) + EPS)

    contrast = 0.0
    busy_den = 0.0
    complexity = 0.0
    strength = 0.0
    for i in present:
        for j in present:
            contrast += p[i] * p[j] * (i - j) ** 2
            busy_den += abs(i * p[i] - j * p[j])
            denom = p[i] + p[j]
            if denom > 0:
                complexity += abs(i - j) * (p[i] * s[i] + p[j] * s[j]) / denom
            strength += (p[i] + p[j]) * (i - j) ** 2
    contrast = (contrast / (ngp * (ngp - 1) + EPS)) * (float(s.sum()) / nv)
    busyness = float((p * s).sum()) / (busy_den + EPS)
    complexity = complexity / nv
    strength = strength / (float(s.sum()) + EPS)
    return {
        "coarseness": float(coarseness),
        "contrast": float(contrast),
        "busyness": float(busyness),
        "complexity": float(complexity),
        "strength": float(strength),
    }


# --------------------------------------------------------------------------- #
# Public API                                                                  #
# --------------------------------------------------------------------------- #
def extract(image: np.ndarray, mask: np.ndarray,
            spacing: Optional[tuple[float, float]] = None,
            bins: int = 32) -> dict:
    """Compute all feature families for one ROI.

    Returns ``{"shape": {...}, "first_order": {...}, "glcm": {...},
    "glrlm": {...}, "glszm": {...}, "ngtdm": {...}}``.
    """
    if image.shape != mask.shape:
        raise ValueError(f"image {image.shape} and mask {mask.shape} shape mismatch")
    if not mask.any():
        raise ValueError("empty ROI mask")
    sp = spacing if spacing else (1.0, 1.0)

    ys, xs = np.where(mask)
    y0, y1 = ys.min(), ys.max() + 1
    x0, x1 = xs.min(), xs.max() + 1
    sub_img = image[y0:y1, x0:x1]
    sub_mask = mask[y0:y1, x0:x1]
    roi_vals = sub_img[sub_mask].astype(np.float64)

    disc_vals, _, _ = _discretise(roi_vals, bins)
    disc = np.zeros(sub_img.shape, dtype=int)
    disc[sub_mask] = disc_vals
    np_voxels = int(sub_mask.sum())

    return {
        "shape": _shape(mask, sp),
        "first_order": _first_order(roi_vals, bins, sp[0] * sp[1]),
        "glcm": _glcm(disc, bins),
        "glrlm": _glrlm(disc, bins, np_voxels),
        "glszm": _glszm(disc, bins, np_voxels),
        "ngtdm": _ngtdm(disc, sub_mask, bins),
    }


def feature_count(result: dict) -> int:
    return sum(len(v) for v in result.values())
