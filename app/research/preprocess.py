"""Mammography DICOM preprocessing pipeline.

Implements the 9-step pipeline used in the breast lesion detection project:

    1. Modality LUT     (RescaleSlope / RescaleIntercept)
    2. VOI LUT          (WindowCenter / WindowWidth → 8-bit)
    3. Photometric inv. (MONOCHROME1 → MONOCHROME2)
    4. Breast segment.  (Otsu + largest connected component)
    5. Crop             (tight bbox around breast)
    6. Pectoral removal (MLO views: Hough line + triangle mask)
    7. CLAHE            (clipLimit=2.0, tileGrid=8×8)
    8. Letterbox resize (1024×1024, square pad)
    9. Save PNG + manifest entry (view, laterality, breast_bbox, spacing)

Usage (CLI):
    python -m app.research.preprocess --input <dicom_root> --output <png_root>

Programmatic:
    from app.research.preprocess import preprocess_mammogram
    img8, meta = preprocess_mammogram(Path("study/file.dcm"), target_size=1024)
"""
from __future__ import annotations

import argparse
import json
import sys
import warnings
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

warnings.filterwarnings("ignore")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np
import pydicom
from PIL import Image
from pydicom.uid import ImplicitVRLittleEndian

try:
    from pydicom.pixels.processing import apply_modality_lut, apply_voi_lut
except ImportError:
    from pydicom.pixel_data_handlers.util import apply_modality_lut, apply_voi_lut

import cv2
from scipy import ndimage as ndi


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------


@dataclass
class PreprocessMeta:
    """Metadata describing a preprocessed mammogram."""
    src_path: str
    out_path: str
    patient_id: str
    study_uid: str
    series_uid: str
    sop_uid: str
    laterality: str          # "L" / "R" / ""
    view: str                # "CC" / "MLO" / ""
    photometric: str         # "MONOCHROME1" / "MONOCHROME2"
    rows_orig: int
    cols_orig: int
    pixel_spacing: tuple[float, float] | None  # (row, col) mm
    breast_bbox: tuple[int, int, int, int]     # (x0, y0, x1, y1) in original coords
    pectoral_removed: bool
    target_size: int
    flipped_to_left: bool    # True if R-laterality was horizontally flipped


# ---------------------------------------------------------------------------
# DICOM helpers (mirror app.dicom_utils style)
# ---------------------------------------------------------------------------


def _ensure_transfer_syntax(ds: pydicom.Dataset) -> None:
    fm = getattr(ds, "file_meta", None)
    if fm is None or not getattr(fm, "TransferSyntaxUID", None):
        meta = pydicom.dataset.FileMetaDataset()
        meta.TransferSyntaxUID = ImplicitVRLittleEndian
        ds.file_meta = meta


def _read_dicom(path: Path) -> pydicom.Dataset:
    ds = pydicom.dcmread(str(path), force=True)
    _ensure_transfer_syntax(ds)
    return ds


def _get_pixel_spacing(ds: pydicom.Dataset) -> Optional[tuple[float, float]]:
    for attr in ("PixelSpacing", "ImagerPixelSpacing"):
        v = getattr(ds, attr, None)
        if v is None:
            continue
        try:
            row, col = float(v[0]), float(v[1])
            return (row, col)
        except Exception:
            continue
    return None


def _str_attr(ds: pydicom.Dataset, key: str) -> str:
    v = getattr(ds, key, "")
    return str(v) if v is not None else ""


# ---------------------------------------------------------------------------
# Step 1+2: Modality + VOI LUT → float32 in [0, 1]
# ---------------------------------------------------------------------------


def _to_normalized_float(ds: pydicom.Dataset) -> tuple[np.ndarray, str]:
    """Apply Modality LUT, then VOI LUT, return float32 in [0,1] and photometric."""
    if "PixelData" not in ds:
        raise ValueError("DICOM has no pixel data")

    raw = ds.pixel_array
    if raw.ndim == 3 and raw.shape[0] > 1 and raw.shape[-1] not in (3, 4):
        raw = raw[0]
    if raw.ndim == 3 and raw.shape[-1] in (3, 4):
        raw = raw[..., 0]

    try:
        raw = apply_modality_lut(raw, ds)
    except Exception:
        pass

    try:
        windowed = apply_voi_lut(raw.astype(np.float32), ds, prefer_lut=True)
    except Exception:
        wc = getattr(ds, "WindowCenter", None)
        ww = getattr(ds, "WindowWidth", None)
        if isinstance(wc, pydicom.multival.MultiValue):
            wc = wc[0]
        if isinstance(ww, pydicom.multival.MultiValue):
            ww = ww[0]
        try:
            wc = float(wc); ww = float(ww)
        except Exception:
            wc, ww = None, None
        if wc is None or ww is None or ww <= 0:
            lo, hi = float(np.min(raw)), float(np.max(raw))
            wc = (lo + hi) / 2.0
            ww = max(hi - lo, 1.0)
        lo = wc - ww / 2.0
        hi = wc + ww / 2.0
        windowed = np.clip(raw.astype(np.float32), lo, hi)

    arr = windowed.astype(np.float32)
    lo, hi = float(np.min(arr)), float(np.max(arr))
    if hi <= lo:
        hi = lo + 1.0
    norm = (arr - lo) / (hi - lo)
    return norm, str(getattr(ds, "PhotometricInterpretation", "MONOCHROME2"))


# ---------------------------------------------------------------------------
# Step 4: Breast segmentation (Otsu + largest connected component)
# ---------------------------------------------------------------------------


def _segment_breast(img01: np.ndarray) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    """Return (binary_mask, bbox=(x0,y0,x1,y1)) for the breast region."""
    u8 = (img01 * 255).astype(np.uint8)
    blur = cv2.GaussianBlur(u8, (5, 5), 0)
    _, mask = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    labels, n = ndi.label(mask > 0)
    if n == 0:
        h, w = img01.shape
        return np.ones_like(img01, dtype=np.uint8), (0, 0, w, h)
    sizes = ndi.sum(mask > 0, labels, index=range(1, n + 1))
    biggest = int(np.argmax(sizes)) + 1
    breast = (labels == biggest).astype(np.uint8)

    breast = ndi.binary_fill_holes(breast).astype(np.uint8)
    ys, xs = np.where(breast > 0)
    if ys.size == 0:
        h, w = img01.shape
        return breast, (0, 0, w, h)
    x0, x1 = int(xs.min()), int(xs.max()) + 1
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    return breast, (x0, y0, x1, y1)


# ---------------------------------------------------------------------------
# Step 6: Pectoral muscle removal (MLO views only)
# ---------------------------------------------------------------------------


def _remove_pectoral(img01: np.ndarray, side: str) -> tuple[np.ndarray, bool]:
    """Erase the pectoral muscle triangle on MLO views.

    Strategy: the pectoral muscle is the brightest triangular region in the
    upper-left (left-laterality) or upper-right (right-laterality) corner.
    We Hough-detect the dominant straight edge and zero out the triangle
    above it, but only if its slope is plausible (avoids false positives on
    CC views or heterogeneously dense breasts).
    """
    h, w = img01.shape
    side = (side or "L").upper()

    crop_w = max(int(w * 0.45), 32)
    crop_h = max(int(h * 0.55), 32)
    if side == "L":
        roi = (img01[:crop_h, :crop_w] * 255).astype(np.uint8)
        x_off, y_off = 0, 0
    else:
        roi = (img01[:crop_h, w - crop_w:] * 255).astype(np.uint8)
        x_off, y_off = w - crop_w, 0

    edges = cv2.Canny(roi, 30, 100)
    lines = cv2.HoughLines(edges, 1, np.pi / 180, threshold=int(min(crop_h, crop_w) * 0.4))
    if lines is None:
        return img01, False

    best = None
    for rho, theta in lines[:, 0]:
        deg = np.degrees(theta)
        if side == "L":
            ok = 100.0 < deg < 170.0
        else:
            ok = 10.0 < deg < 80.0
        if ok:
            best = (rho, theta)
            break
    if best is None:
        return img01, False

    rho, theta = best
    a, b = np.cos(theta), np.sin(theta)
    if abs(b) < 1e-6:
        return img01, False

    out = img01.copy()
    yy, xx = np.indices(roi.shape)
    line_y = (rho - a * xx) / b
    if side == "L":
        keep = yy >= line_y
    else:
        keep = yy >= line_y
    erase = ~keep
    sub = out[y_off:y_off + crop_h, x_off:x_off + crop_w]
    sub[erase] = 0.0
    out[y_off:y_off + crop_h, x_off:x_off + crop_w] = sub
    return out, True


# ---------------------------------------------------------------------------
# Step 7: CLAHE
# ---------------------------------------------------------------------------


def _apply_clahe(img01: np.ndarray, clip: float = 2.0, tile: int = 8) -> np.ndarray:
    u8 = (np.clip(img01, 0, 1) * 255).astype(np.uint8)
    clahe = cv2.createCLAHE(clipLimit=clip, tileGridSize=(tile, tile))
    out = clahe.apply(u8)
    return out.astype(np.float32) / 255.0


# ---------------------------------------------------------------------------
# Step 8: Letterbox resize to a square
# ---------------------------------------------------------------------------


def _letterbox(img01: np.ndarray, size: int = 1024, pad: float = 0.0) -> np.ndarray:
    h, w = img01.shape
    if h == 0 or w == 0:
        return np.full((size, size), pad, dtype=np.float32)
    scale = min(size / w, size / h)
    new_w = max(1, int(round(w * scale)))
    new_h = max(1, int(round(h * scale)))
    resized = cv2.resize(img01, (new_w, new_h), interpolation=cv2.INTER_AREA)
    canvas = np.full((size, size), pad, dtype=np.float32)
    y0 = (size - new_h) // 2
    x0 = (size - new_w) // 2
    canvas[y0:y0 + new_h, x0:x0 + new_w] = resized
    return canvas


# ---------------------------------------------------------------------------
# Top-level pipeline
# ---------------------------------------------------------------------------


def preprocess_mammogram(
    dcm_path: Path,
    target_size: int = 1024,
    standardize_to_left: bool = True,
    do_pectoral: bool = True,
    do_clahe: bool = True,
) -> tuple[np.ndarray, PreprocessMeta]:
    """Run the full 9-step preprocessing pipeline on one DICOM file.

    Returns:
        img8 : uint8 HxW image of size target_size×target_size
        meta : PreprocessMeta describing provenance
    """
    dcm_path = Path(dcm_path)
    ds = _read_dicom(dcm_path)

    laterality = _str_attr(ds, "ImageLaterality").upper()
    view = _str_attr(ds, "ViewPosition").upper()
    rows_orig = int(getattr(ds, "Rows", 0) or 0)
    cols_orig = int(getattr(ds, "Columns", 0) or 0)
    spacing = _get_pixel_spacing(ds)

    # 1+2. Modality LUT + VOI LUT
    img, photometric = _to_normalized_float(ds)

    # 3. Photometric inversion
    if photometric == "MONOCHROME1":
        img = 1.0 - img

    # 4+5. Breast segmentation + crop
    mask, bbox = _segment_breast(img)
    x0, y0, x1, y1 = bbox
    img_crop = img[y0:y1, x0:x1] * mask[y0:y1, x0:x1]

    # Standardize laterality so all breasts face the same direction (left).
    flipped = False
    if standardize_to_left and laterality == "R":
        img_crop = np.fliplr(img_crop)
        flipped = True
    side_for_pectoral = "L" if (laterality != "R" or flipped) else "R"

    # 6. Pectoral muscle removal (MLO only)
    pectoral_removed = False
    if do_pectoral and "MLO" in view:
        img_crop, pectoral_removed = _remove_pectoral(img_crop, side_for_pectoral)

    # 7. CLAHE
    if do_clahe:
        img_crop = _apply_clahe(img_crop, clip=2.0, tile=8)

    # 8. Letterbox to square
    canvas = _letterbox(img_crop, size=target_size, pad=0.0)
    img8 = (np.clip(canvas, 0, 1) * 255).astype(np.uint8)

    meta = PreprocessMeta(
        src_path=str(dcm_path),
        out_path="",
        patient_id=_str_attr(ds, "PatientID"),
        study_uid=_str_attr(ds, "StudyInstanceUID"),
        series_uid=_str_attr(ds, "SeriesInstanceUID"),
        sop_uid=_str_attr(ds, "SOPInstanceUID"),
        laterality=laterality,
        view=view,
        photometric=photometric,
        rows_orig=rows_orig,
        cols_orig=cols_orig,
        pixel_spacing=spacing,
        breast_bbox=(int(x0), int(y0), int(x1), int(y1)),
        pectoral_removed=pectoral_removed,
        target_size=target_size,
        flipped_to_left=flipped,
    )
    return img8, meta


# ---------------------------------------------------------------------------
# BBox transform (map original DICOM coords → preprocessed image coords)
# ---------------------------------------------------------------------------


def transform_bbox(
    bbox_orig: tuple[int, int, int, int],
    meta: PreprocessMeta,
) -> tuple[float, float, float, float] | None:
    """Map a bbox from original DICOM coordinates to preprocessed image coords.

    Mirrors the geometric transforms in preprocess_mammogram: crop → flip → letterbox.
    Returns (x0, y0, x1, y1) in pixels of the preprocessed canvas, or None if the
    bbox falls outside the breast crop.
    """
    bx0, by0, bx1, by1 = meta.breast_bbox
    crop_w = max(bx1 - bx0, 1)
    crop_h = max(by1 - by0, 1)

    x0, y0, x1, y1 = bbox_orig
    # 1. Translate into breast-crop frame
    x0 -= bx0; x1 -= bx0
    y0 -= by0; y1 -= by0
    # 2. Clip to crop
    x0 = max(0, min(x0, crop_w)); x1 = max(0, min(x1, crop_w))
    y0 = max(0, min(y0, crop_h)); y1 = max(0, min(y1, crop_h))
    if x1 <= x0 or y1 <= y0:
        return None
    # 3. Horizontal flip (R → L)
    if meta.flipped_to_left:
        x0, x1 = crop_w - x1, crop_w - x0
    # 4. Letterbox scale + pad
    s = meta.target_size
    scale = min(s / crop_w, s / crop_h)
    new_w = crop_w * scale
    new_h = crop_h * scale
    pad_x = (s - new_w) / 2.0
    pad_y = (s - new_h) / 2.0
    return (
        x0 * scale + pad_x,
        y0 * scale + pad_y,
        x1 * scale + pad_x,
        y1 * scale + pad_y,
    )


# ---------------------------------------------------------------------------
# Batch CLI
# ---------------------------------------------------------------------------


def _iter_dicoms(root: Path):
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in (".dcm", ".dicom", ""):
            yield p


def _save_png(img8: np.ndarray, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(img8, mode="L").save(out_path, format="PNG", optimize=False, compress_level=3)


def main():
    ap = argparse.ArgumentParser(description="Mammography DICOM preprocessing")
    ap.add_argument("--input", required=True, help="Folder of DICOM files (recursive)")
    ap.add_argument("--output", required=True, help="Folder to write PNGs")
    ap.add_argument("--size", type=int, default=1024, help="Target square size (default 1024)")
    ap.add_argument("--no-pectoral", action="store_true")
    ap.add_argument("--no-clahe", action="store_true")
    ap.add_argument("--no-flip", action="store_true",
                    help="Disable R→L laterality standardization")
    ap.add_argument("--manifest", default="manifest.jsonl",
                    help="Manifest filename inside output folder (default manifest.jsonl)")
    args = ap.parse_args()

    in_root = Path(args.input).resolve()
    out_root = Path(args.output).resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    if not in_root.exists():
        raise SystemExit(f"input folder not found: {in_root}")

    manifest_path = out_root / args.manifest
    n_ok = n_fail = 0

    with manifest_path.open("w", encoding="utf-8") as mf:
        for dcm in _iter_dicoms(in_root):
            try:
                img8, meta = preprocess_mammogram(
                    dcm,
                    target_size=args.size,
                    standardize_to_left=not args.no_flip,
                    do_pectoral=not args.no_pectoral,
                    do_clahe=not args.no_clahe,
                )
            except Exception as e:
                n_fail += 1
                print(f"[skip] {dcm.name}: {e}")
                continue

            rel = dcm.relative_to(in_root).with_suffix(".png")
            out_path = out_root / "images" / rel
            _save_png(img8, out_path)
            meta.out_path = str(out_path.relative_to(out_root)).replace("\\", "/")
            mf.write(json.dumps(asdict(meta), ensure_ascii=False) + "\n")
            n_ok += 1
            if n_ok % 25 == 0:
                print(f"  ... {n_ok} ok, {n_fail} failed")

    print(f"\n[done] {n_ok} preprocessed, {n_fail} failed")
    print(f"[manifest] {manifest_path}")


if __name__ == "__main__":
    main()
