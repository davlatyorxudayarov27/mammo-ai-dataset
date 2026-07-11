"""features.py — ROI (bounding box patch) dan belgi ajratish.

Har bir ROI uchun 38 ta belgi (faqat numpy/scipy/skimage):
  1. Intensivlik statistikasi (8): mean, std, median, skewness, kurtosis,
     entropy (64-bin gistogramma), p10, p90.
  2. GLCM tekstura (12): distances=[1,3] x {contrast, dissimilarity,
     homogeneity, energy, correlation, ASM}, 4 burchak bo'yicha o'rtacha.
  3. LBP (10): P=8, R=1, 'uniform' — 10-binli normalangan gistogramma.
  4. Shakl (6, Otsu maskasidan): area_ratio, eccentricity, solidity,
     extent, kompaktlik (perimeter/sqrt(area)), bbox aspect ratio.
  5. Gradient (2): Sobel magnitude mean va std.

ROI manbai: '--source gt' (YOLO label fayllari) yoki '--source pred'
(YOLO detektsiyalari — pipeline.ensemble ichida).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy import stats as sstats
from skimage import color, filters, io, measure
from skimage.feature import graycomatrix, graycoprops, local_binary_pattern

# --------------------------------------------------------------- nomlar --- #
_INT_NAMES = ["int_mean", "int_std", "int_median", "int_skew", "int_kurtosis",
              "int_entropy", "int_p10", "int_p90"]
_GLCM_PROPS = ["contrast", "dissimilarity", "homogeneity", "energy",
               "correlation", "ASM"]
_GLCM_NAMES = [f"glcm_d{d}_{p}" for d in (1, 3) for p in _GLCM_PROPS]
_LBP_NAMES = [f"lbp_u{i}" for i in range(10)]
_SHAPE_NAMES = ["shape_area_ratio", "shape_eccentricity", "shape_solidity",
                "shape_extent", "shape_compactness", "shape_aspect"]
_GRAD_NAMES = ["grad_sobel_mean", "grad_sobel_std"]

FEATURE_NAMES: list[str] = _INT_NAMES + _GLCM_NAMES + _LBP_NAMES + _SHAPE_NAMES + _GRAD_NAMES
N_FEATURES = len(FEATURE_NAMES)          # 38

_GLCM_LEVELS = 64
_HIST_BINS = 64


# ------------------------------------------------------------ yordamchi --- #
def load_gray(path: str | Path) -> np.ndarray:
    """Rasmni o'qib, 8-bit (uint8) grayscale'ga keltiradi."""
    img = io.imread(str(path))
    if img.ndim == 3:
        img = color.rgb2gray(img[..., :3])           # 0..1 float
        img = (img * 255.0)
    img = img.astype(np.float64)
    mn, mx = float(img.min()), float(img.max())
    if mx > mn:
        img = (img - mn) / (mx - mn) * 255.0
    else:
        img = np.zeros_like(img)
    return img.astype(np.uint8)


def crop_roi(img: np.ndarray, box_xyxy: tuple[float, float, float, float],
             min_side: int = 8) -> np.ndarray | None:
    """Bbox (piksel, x1..y2) bo'yicha patch kesadi; juda kichigini None qaytaradi."""
    H, W = img.shape[:2]
    x1, y1, x2, y2 = box_xyxy
    x1, y1 = max(0, int(np.floor(x1))), max(0, int(np.floor(y1)))
    x2, y2 = min(W, int(np.ceil(x2))), min(H, int(np.ceil(y2)))
    if x2 - x1 < min_side or y2 - y1 < min_side:
        return None
    return img[y1:y2, x1:x2]


def yolo_line_to_xyxy(line: str, W: int, H: int) -> tuple[int, tuple] | None:
    """YOLO label qatori 'cls cx cy w h' (normalangan) -> (cls, xyxy piksel)."""
    parts = line.split()
    if len(parts) < 5:
        return None
    c = int(float(parts[0]))
    cx, cy, w, h = (float(v) for v in parts[1:5])
    x1, y1 = (cx - w / 2) * W, (cy - h / 2) * H
    x2, y2 = (cx + w / 2) * W, (cy + h / 2) * H
    return c, (x1, y1, x2, y2)


# ------------------------------------------------------- belgi hisoblash --- #
def _intensity_feats(p: np.ndarray) -> list[float]:
    v = p.astype(np.float64).ravel()
    hist, _ = np.histogram(v, bins=_HIST_BINS, range=(0, 255))
    q = hist / max(1, hist.sum())
    q = q[q > 0]
    entropy = float(-(q * np.log2(q)).sum())
    std = float(v.std())
    # bir xil qiymatli patch'da skew/kurtosis aniqlanmagan — 0 deb olamiz
    skew = float(sstats.skew(v)) if std > 1e-9 else 0.0
    kurt = float(sstats.kurtosis(v)) if std > 1e-9 else 0.0
    return [float(v.mean()), std, float(np.median(v)), skew, kurt,
            entropy, float(np.percentile(v, 10)), float(np.percentile(v, 90))]


def _glcm_feats(p: np.ndarray) -> list[float]:
    q = (p.astype(np.float64) / 256.0 * _GLCM_LEVELS).astype(np.uint8)
    q = np.clip(q, 0, _GLCM_LEVELS - 1)
    glcm = graycomatrix(q, distances=[1, 3],
                        angles=[0, np.pi / 4, np.pi / 2, 3 * np.pi / 4],
                        levels=_GLCM_LEVELS, symmetric=True, normed=True)
    out = []
    for di in range(2):
        for prop in _GLCM_PROPS:
            vals = graycoprops(glcm, prop)[di, :]     # 4 burchak
            out.append(float(np.nanmean(vals)))
    return out


def _lbp_feats(p: np.ndarray) -> list[float]:
    lbp = local_binary_pattern(p, P=8, R=1, method="uniform")   # qiymatlar 0..9
    hist, _ = np.histogram(lbp, bins=10, range=(0, 10))
    hist = hist / max(1, hist.sum())
    return [float(x) for x in hist]


def _shape_feats(p: np.ndarray) -> list[float]:
    H, W = p.shape
    aspect = W / H
    try:
        thr = filters.threshold_otsu(p)
    except ValueError:                                 # bir xil qiymatli patch
        return [0.0, 0.0, 0.0, 0.0, 0.0, aspect]
    mask = p > thr
    if not mask.any():
        return [0.0, 0.0, 0.0, 0.0, 0.0, aspect]
    lab = measure.label(mask)
    regions = measure.regionprops(lab)
    reg = max(regions, key=lambda r: r.area)           # eng katta komponent
    area = float(reg.area)
    compact = float(reg.perimeter / np.sqrt(area)) if area > 0 else 0.0
    solidity = float(reg.solidity) if reg.solidity is not None else 0.0
    return [area / (H * W), float(reg.eccentricity), solidity,
            float(reg.extent), compact, aspect]


def _grad_feats(p: np.ndarray) -> list[float]:
    g = filters.sobel(p.astype(np.float64) / 255.0)
    return [float(g.mean()), float(g.std())]


def extract_features(patch: np.ndarray) -> np.ndarray:
    """Bitta ROI patch (uint8 grayscale) -> 38 o'lchamli belgi vektori."""
    f = (_intensity_feats(patch) + _glcm_feats(patch) + _lbp_feats(patch)
         + _shape_feats(patch) + _grad_feats(patch))
    v = np.asarray(f, dtype=np.float64)
    return np.nan_to_num(v, nan=0.0, posinf=0.0, neginf=0.0)


# ------------------------------------------------------ dataset bo'ylab --- #
def extract_split(images_dir: Path, labels_dir: Path,
                  log=print) -> tuple[np.ndarray, np.ndarray, list[dict]]:
    """GT labellardan ('--source gt'): barcha ROI belgilari.
    Qaytadi: X (N x 38), y (N,), meta (rasm/box ma'lumoti)."""
    X, y, meta = [], [], []
    img_files = sorted(images_dir.glob("*"))
    for i, ip in enumerate(img_files):
        if ip.suffix.lower() not in (".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"):
            continue
        lp = labels_dir / (ip.stem + ".txt")
        if not lp.exists():
            continue
        img = load_gray(ip)
        H, W = img.shape
        for line in lp.read_text().strip().splitlines():
            parsed = yolo_line_to_xyxy(line, W, H)
            if not parsed:
                continue
            c, xyxy = parsed
            patch = crop_roi(img, xyxy)
            if patch is None:
                continue
            X.append(extract_features(patch))
            y.append(c)
            meta.append({"image": ip.name, "box": [round(v, 1) for v in xyxy], "cls": c})
        if (i + 1) % 50 == 0:
            log(f"  ... {i + 1}/{len(img_files)} rasm, {len(y)} ROI")
    return (np.asarray(X, dtype=np.float64).reshape(len(y), N_FEATURES),
            np.asarray(y, dtype=np.int64), meta)


class Normalizer:
    """Z-score normalizatsiya — train bo'yicha mean/std saqlanadi ((2-band talabi),
    inference'da qayta ishlatiladi."""

    def __init__(self, mean=None, std=None):
        self.mean = None if mean is None else np.asarray(mean, dtype=np.float64)
        self.std = None if std is None else np.asarray(std, dtype=np.float64)

    def fit(self, X: np.ndarray) -> "Normalizer":
        self.mean = X.mean(axis=0)
        self.std = X.std(axis=0)
        self.std[self.std < 1e-12] = 1.0     # konstanta belgi — bo'linmasin
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        return (X - self.mean) / self.std

    def to_dict(self) -> dict:
        return {"mean": self.mean.tolist(), "std": self.std.tolist()}

    @classmethod
    def from_dict(cls, d: dict) -> "Normalizer":
        return cls(mean=d["mean"], std=d["std"])
