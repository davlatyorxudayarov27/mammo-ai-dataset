from __future__ import annotations

import io
import threading
from collections import OrderedDict
from pathlib import Path
from typing import Optional

import numpy as np
import pydicom
from PIL import Image
from pydicom.uid import ImplicitVRLittleEndian


_PIXEL_CACHE: "OrderedDict[tuple, tuple]" = OrderedDict()
_PIXEL_CACHE_LOCK = threading.Lock()
_PIXEL_CACHE_MAX = 4


def _cache_get(key):
    with _PIXEL_CACHE_LOCK:
        v = _PIXEL_CACHE.get(key)
        if v is not None:
            _PIXEL_CACHE.move_to_end(key)
        return v


def _cache_put(key, value):
    with _PIXEL_CACHE_LOCK:
        _PIXEL_CACHE[key] = value
        _PIXEL_CACHE.move_to_end(key)
        while len(_PIXEL_CACHE) > _PIXEL_CACHE_MAX:
            _PIXEL_CACHE.popitem(last=False)

try:
    from pydicom.pixels.processing import apply_modality_lut
except ImportError:
    from pydicom.pixel_data_handlers.util import apply_modality_lut


def _ensure_transfer_syntax(ds: pydicom.Dataset) -> None:
    fm = getattr(ds, "file_meta", None)
    if fm is None or not getattr(fm, "TransferSyntaxUID", None):
        meta = pydicom.dataset.FileMetaDataset()
        meta.TransferSyntaxUID = ImplicitVRLittleEndian
        ds.file_meta = meta


def get_frame_count(ds: pydicom.Dataset) -> int:
    n = getattr(ds, "NumberOfFrames", 1) or 1
    try:
        return int(n)
    except (TypeError, ValueError):
        return 1


def _to_float(v) -> Optional[float]:
    if v is None:
        return None
    if isinstance(v, pydicom.multival.MultiValue):
        if len(v) == 0:
            return None
        v = v[0]
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def default_window(ds: pydicom.Dataset) -> tuple[Optional[float], Optional[float]]:
    return _to_float(getattr(ds, "WindowCenter", None)), _to_float(getattr(ds, "WindowWidth", None))


def _select_frame(arr: np.ndarray, frame: int, frames: int) -> np.ndarray:
    if frames > 1 and arr.ndim >= 3 and arr.shape[0] == frames:
        return arr[frame]
    return arr


class NoPixelDataError(ValueError):
    def __init__(self, modality: str = "", sop_class: str = ""):
        super().__init__(f"DICOM has no pixel data (modality={modality})")
        self.modality = modality
        self.sop_class = sop_class


def render_frame_png(
    path: Path,
    frame: int = 0,
    wc: Optional[float] = None,
    ww: Optional[float] = None,
    invert: bool = False,
    max_dim: int = 2048,
) -> bytes:
    try:
        mtime = path.stat().st_mtime_ns
    except OSError:
        mtime = 0
    cache_key = (str(path), mtime, frame, int(max_dim or 0))
    cached = _cache_get(cache_key)
    if cached is not None:
        arr, photometric, default_wc, default_ww, is_color = cached
    else:
        ds = pydicom.dcmread(str(path), force=True)
        _ensure_transfer_syntax(ds)
        if "PixelData" not in ds:
            raise NoPixelDataError(
                modality=str(getattr(ds, "Modality", "") or ""),
                sop_class=str(getattr(ds, "SOPClassUID", "") or ""),
            )
        raw = ds.pixel_array
        frames = get_frame_count(ds)
        raw = _select_frame(raw, frame, frames)
        try:
            raw = apply_modality_lut(raw, ds)
        except Exception:
            pass
        is_color = raw.ndim == 3 and raw.shape[-1] in (3, 4)

        if not is_color:
            arr = np.asarray(raw, dtype=np.float32)
            if max_dim and (arr.shape[0] > max_dim or arr.shape[1] > max_dim):
                pil = Image.fromarray(arr, mode="F")
                pil.thumbnail((max_dim, max_dim), Image.BILINEAR)
                arr = np.asarray(pil, dtype=np.float32)
        else:
            arr = np.asarray(raw, dtype=np.uint8)
            if max_dim and (arr.shape[0] > max_dim or arr.shape[1] > max_dim):
                mode = "RGB" if arr.shape[-1] == 3 else "RGBA"
                pil = Image.fromarray(arr, mode=mode)
                pil.thumbnail((max_dim, max_dim), Image.LANCZOS)
                arr = np.asarray(pil, dtype=np.uint8)

        photometric = str(getattr(ds, "PhotometricInterpretation", "MONOCHROME2"))
        default_wc, default_ww = default_window(ds)
        _cache_put(cache_key, (arr, photometric, default_wc, default_ww, is_color))

    if is_color:
        out = np.clip(arr, 0, 255).astype(np.uint8)
    else:
        if wc is None:
            wc = default_wc
        if ww is None:
            ww = default_ww
        if wc is None or ww is None or ww <= 0:
            lo = float(np.min(arr))
            hi = float(np.max(arr))
            if hi <= lo:
                hi = lo + 1.0
            wc = (lo + hi) / 2.0
            ww = hi - lo

        lo = wc - ww / 2.0
        hi = wc + ww / 2.0
        out = np.clip(arr, lo, hi)
        out = ((out - lo) / (hi - lo) * 255.0).astype(np.uint8)

        if photometric == "MONOCHROME1":
            out = 255 - out
        if invert:
            out = 255 - out

    if out.ndim == 2:
        img = Image.fromarray(out, mode="L")
    elif out.ndim == 3 and out.shape[-1] == 3:
        img = Image.fromarray(out, mode="RGB")
    elif out.ndim == 3 and out.shape[-1] == 4:
        img = Image.fromarray(out, mode="RGBA")
    else:
        img = Image.fromarray(out)

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=False, compress_level=1)
    return buf.getvalue()


def load_frame_array(path: Path, frame: int = 0) -> tuple[np.ndarray, Optional[tuple[float, float]]]:
    """Return the modality-LUT-applied 2D pixel array (float32, full resolution)
    for one frame plus pixel spacing ``(row_mm, col_mm)`` if present.

    Unlike :func:`render_frame_png`, this performs no windowing and no
    downsampling, so the array aligns 1:1 with Rows×Columns — required for
    radiomics ROI extraction.
    """
    ds = pydicom.dcmread(str(path), force=True)
    _ensure_transfer_syntax(ds)
    if "PixelData" not in ds:
        raise NoPixelDataError(
            modality=str(getattr(ds, "Modality", "") or ""),
            sop_class=str(getattr(ds, "SOPClassUID", "") or ""),
        )
    raw = ds.pixel_array
    frames = get_frame_count(ds)
    raw = _select_frame(raw, frame, frames)
    try:
        raw = apply_modality_lut(raw, ds)
    except Exception:
        pass
    if raw.ndim == 3 and raw.shape[-1] in (3, 4):
        # Color → luminance so radiomics works on a single channel.
        raw = raw[..., :3].astype(np.float32)
        raw = 0.299 * raw[..., 0] + 0.587 * raw[..., 1] + 0.114 * raw[..., 2]
    arr = np.asarray(raw, dtype=np.float32)

    spacing: Optional[tuple[float, float]] = None
    ps = getattr(ds, "PixelSpacing", None) or getattr(ds, "ImagerPixelSpacing", None)
    if ps is not None:
        try:
            spacing = (float(ps[0]), float(ps[1]))
        except (TypeError, ValueError, IndexError):
            spacing = None
    return arr, spacing


_META_KEYS = [
    "PatientName", "PatientID", "PatientSex", "PatientBirthDate", "PatientAge",
    "StudyDate", "StudyTime", "StudyDescription", "StudyInstanceUID",
    "SeriesDescription", "SeriesNumber", "SeriesInstanceUID",
    "Modality", "Manufacturer", "ManufacturerModelName",
    "BodyPartExamined", "ViewPosition", "ImageLaterality",
    "Rows", "Columns", "BitsAllocated", "BitsStored", "PixelRepresentation",
    "PhotometricInterpretation",
    "WindowCenter", "WindowWidth",
    "RescaleSlope", "RescaleIntercept",
    "NumberOfFrames",
    "PixelSpacing", "ImagerPixelSpacing",
    "InstitutionName",
    "AcquisitionDate", "AcquisitionTime",
    "KVP", "ExposureTime", "XRayTubeCurrent",
    "CompressionForce", "BodyPartThickness",
    "TransferSyntaxUID",
]


def read_metadata(path: Path) -> dict:
    ds = pydicom.dcmread(str(path), stop_before_pixels=True, force=True)
    out: dict = {}
    for k in _META_KEYS:
        v = getattr(ds, k, None)
        if v is None:
            continue
        try:
            if isinstance(v, (int, float)):
                out[k] = v
            else:
                out[k] = str(v)
        except Exception:
            out[k] = repr(v)

    ts = getattr(getattr(ds, "file_meta", None), "TransferSyntaxUID", None)
    if ts is not None:
        out["TransferSyntaxUID"] = str(ts)

    return out


def extract_sr_content(path: Path) -> dict:
    ds = pydicom.dcmread(str(path), force=True)
    _ensure_transfer_syntax(ds)

    def _concept_name(item) -> str:
        try:
            seq = getattr(item, "ConceptNameCodeSequence", None)
            if seq and len(seq):
                return str(getattr(seq[0], "CodeMeaning", "") or "")
        except Exception:
            pass
        return ""

    def _walk(item, depth: int = 0) -> list[dict]:
        out: list[dict] = []
        vt = str(getattr(item, "ValueType", "") or "")
        name = _concept_name(item)
        node: dict = {"depth": depth, "type": vt, "name": name}
        if vt == "TEXT":
            node["text"] = str(getattr(item, "TextValue", "") or "")
        elif vt == "NUM":
            try:
                mv = item.MeasuredValueSequence[0]
                val = str(getattr(mv, "NumericValue", ""))
                unit = ""
                u_seq = getattr(mv, "MeasurementUnitsCodeSequence", None)
                if u_seq and len(u_seq):
                    unit = str(getattr(u_seq[0], "CodeMeaning", "") or "")
                node["value"] = f"{val} {unit}".strip()
            except Exception:
                node["value"] = ""
        elif vt == "CODE":
            try:
                cs = item.ConceptCodeSequence[0]
                node["value"] = str(getattr(cs, "CodeMeaning", "") or "")
            except Exception:
                node["value"] = ""
        elif vt == "DATE":
            node["value"] = str(getattr(item, "Date", "") or "")
        elif vt == "PNAME":
            node["value"] = str(getattr(item, "PersonName", "") or "")
        out.append(node)

        children = getattr(item, "ContentSequence", None)
        if children:
            for ch in children:
                out.extend(_walk(ch, depth + 1))
        return out

    items: list[dict] = []
    root_name = _concept_name(ds)
    items.append({"depth": 0, "type": "ROOT", "name": root_name or "Structured Report"})
    for child in getattr(ds, "ContentSequence", []) or []:
        items.extend(_walk(child, 1))

    return {
        "modality": str(getattr(ds, "Modality", "") or ""),
        "sop_class": str(getattr(ds, "SOPClassUID", "") or ""),
        "completion_flag": str(getattr(ds, "CompletionFlag", "") or ""),
        "verification_flag": str(getattr(ds, "VerificationFlag", "") or ""),
        "patient_name": str(getattr(ds, "PatientName", "") or ""),
        "patient_id": str(getattr(ds, "PatientID", "") or ""),
        "content_date": str(getattr(ds, "ContentDate", "") or ""),
        "items": items,
    }


def quick_summary(path: Path) -> dict:
    try:
        ds = pydicom.dcmread(str(path), stop_before_pixels=True, force=True)
    except Exception as e:
        return {"error": str(e)}
    rows = int(getattr(ds, "Rows", 0) or 0)
    cols = int(getattr(ds, "Columns", 0) or 0)
    has_pixels = bool(rows and cols) and (
        "PixelData" in ds or "Rows" in ds
    )
    pir = getattr(ds, "PatientIdentityRemoved", None)
    return {
        "patient": str(getattr(ds, "PatientName", "")),
        "patient_id": str(getattr(ds, "PatientID", "")),
        "modality": str(getattr(ds, "Modality", "")),
        "study_date": str(getattr(ds, "StudyDate", "")),
        "view": str(getattr(ds, "ViewPosition", "")),
        "laterality": str(getattr(ds, "ImageLaterality", "")),
        "rows": rows,
        "cols": cols,
        "frames": get_frame_count(ds) if has_pixels else 0,
        "has_pixels": has_pixels,
        "deidentified": (str(pir).upper() == "YES") if pir is not None else False,
    }
