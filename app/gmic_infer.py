"""GMIC (NYU) benign/malignant tashxis — bir-rasmli inference.

GMIC kodi `app/gmic/src/` ga vendor qilingan (AGPLv3, manba: github.com/nyukat/GMIC).
Model bizning ma'lumotda MIL fine-tune qilingan (faqat head'lar, backbone muzlatilgan).
Backbone NYU Hologic'da o'qitilgan — boshqa apparat uchun bu QORALAMA, klinik emas.

Oqim: DICOM -> 16-bit PNG -> crop (fon olib tashlash) -> optimal markaz ->
process -> GMIC forward -> P(benign), P(malignant) [+ ixtiyoriy saliency].
"""
from __future__ import annotations

import os
import sys
import tempfile
import threading
from pathlib import Path

import numpy as np

# Vendored GMIC `src` paketi import qilinishi uchun app/gmic ni yo'lga qo'shamiz
_GMIC_ROOT = str(Path(__file__).resolve().parent / "gmic")
if _GMIC_ROOT not in sys.path:
    sys.path.insert(0, _GMIC_ROOT)

MODELS_DIR = Path(__file__).resolve().parent / "models"
# Fine-tune qilingan og'irlik (head'lar qayta sozlangan, backbone = GMIC model-1)
WEIGHT_PATH = MODELS_DIR / "gmic" / "gmic_bm_finetuned.pt"

GMIC_PARAMS = {
    "device_type": "cpu", "gpu_number": 0,
    "max_crop_noise": (100, 100), "max_crop_size_noise": 100,
    "cam_size": (46, 30), "K": 6, "crop_shape": (256, 256),
    "post_processing_dim": 256, "num_classes": 2, "use_v1_global": False,
}

_model = None
_lock = threading.Lock()


def available() -> bool:
    return WEIGHT_PATH.exists()


def _get_model():
    global _model
    if _model is not None:
        return _model
    with _lock:
        if _model is not None:
            return _model
        import torch
        from src.modeling import gmic as gmic_mod
        from src.constants import PERCENT_T_DICT
        params = dict(GMIC_PARAMS)
        params["percent_t"] = PERCENT_T_DICT["1"]  # fine-tune model-1 backbone'da edi
        m = gmic_mod.GMIC(params)
        sd = torch.load(str(WEIGHT_PATH), map_location="cpu")
        m.load_state_dict(sd, strict=False)
        m.eval()
        _model = m
        return _model


def _dicom_to_png16(dcm_path, out_png):
    import pydicom
    from PIL import Image
    ds = pydicom.dcmread(str(dcm_path), force=True)
    arr = ds.pixel_array
    if arr.ndim == 3:
        arr = arr[arr.shape[0] // 2]
    slope = float(getattr(ds, "RescaleSlope", 1) or 1)
    inter = float(getattr(ds, "RescaleIntercept", 0) or 0)
    arr = arr.astype(np.float32) * slope + inter
    if str(getattr(ds, "PhotometricInterpretation", "")) == "MONOCHROME1":
        arr = arr.max() - arr
    arr = arr - arr.min()
    if arr.max() > 0:
        arr = arr / arr.max() * 65535.0
    Image.fromarray(arr.astype(np.uint16)).save(str(out_png))


def view_from_dicom(dcm_path):
    """DICOM'dan GMIC view nomi: 'L-CC' / 'R-CC' / 'L-MLO' / 'R-MLO'."""
    import pydicom
    ds = pydicom.dcmread(str(dcm_path), stop_before_pixels=True, force=True)
    lat = (str(getattr(ds, "ImageLaterality", "") or getattr(ds, "Laterality", "")).upper() + " ")[0]
    vp = str(getattr(ds, "ViewPosition", "")).upper()
    if vp not in ("CC", "MLO"):
        vp = "CC"
    return f"{lat}-{vp}" if lat in ("L", "R") else None


def _saliency_overlay_b64(orig, fc, sal_mal, view, md):
    """Malignant saliency'ni original DICOM koordinatasiga qaytarib, RGBA PNG (base64).

    process_image noise'siz (RandomState(0), max_crop_noise=(0,0)) — deterministik,
    shuning uchun crop oynasini aniq qayta hisoblab, saliency'ni teskari map qilamiz.
    """
    import base64
    import io as _io
    import cv2
    from PIL import Image
    from src.data_loading import augmentations as aug
    from src.constants import VIEWS, INPUT_SIZE_DICT

    INP = INPUT_SIZE_DICT[view]                       # (2944, 1920)
    ch, cw = fc.shape
    joint = np.expand_dims(fc, 2)
    padded, borders = aug.sample_crop_best_center(
        joint.copy(), INP, np.random.RandomState(0),
        np.array((0, 0)), 0, md["best_center"], view)
    ph, pw = padded.shape[0], padded.shape[1]
    pad_y_top = int((INP[0] - ch) / 2) if (VIEWS.is_cc(view) and ch < INP[0]) else 0
    t, b, l, r = [int(v) for v in borders]
    sal_full = cv2.resize(sal_mal, (r - l, b - t), interpolation=cv2.INTER_CUBIC)
    canvas = np.zeros((ph, pw), np.float32)
    canvas[t:b, l:r] = sal_full
    fcmap = canvas[pad_y_top:pad_y_top + ch, 0:cw]    # flipped-cropped fazo
    if VIEWS.is_right(view):
        fcmap = np.fliplr(fcmap)                       # unflip -> cropped fazo
    wl = md["window_location"]
    r0, r1, c0, c1 = int(wl[0]), int(wl[1]), int(wl[2]), int(wl[3])
    omap = np.zeros(orig.shape, np.float32)
    omap[r0:r1, c0:c1] = fcmap                         # original fazo
    mx = float(omap.max())
    if mx <= 0:
        return None
    omap = np.clip(omap / mx, 0, 1)
    # downscale (overlay PNG kichik bo'lsin)
    H, W = omap.shape
    s = 1024.0 / max(H, W)
    small = cv2.resize(omap, (max(1, int(W * s)), max(1, int(H * s))))
    heat = (small * 255).astype(np.uint8)
    rgb = cv2.applyColorMap(heat, cv2.COLORMAP_JET)[:, :, ::-1]  # BGR->RGB
    alpha = (small * 200).astype(np.uint8)            # past saliency = shaffof
    rgba = np.dstack([rgb, alpha])
    buf = _io.BytesIO()
    Image.fromarray(rgba, "RGBA").save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def predict_dicom(dcm_path, want_saliency=True) -> dict:
    """Bitta DICOM uchun benign/malignant ehtimoli (+ ixtiyoriy saliency overlay)."""
    if not available():
        raise RuntimeError("GMIC og'irligi topilmadi: models/gmic/gmic_bm_finetuned.pt")
    import torch
    from src.data_loading import loading
    from src.cropping.crop_single import crop_single_mammogram
    from src.optimal_centers.get_optimal_center_single import get_optimal_center_single
    from src.utilities import pickling

    view = view_from_dicom(dcm_path)
    if not view:
        raise ValueError("ImageLaterality/ViewPosition aniqlanmadi — GMIC view kerak")

    tmp = tempfile.mkdtemp(prefix="gmic_")
    try:
        png = os.path.join(tmp, "i.png")
        crop = os.path.join(tmp, "c.png")
        meta = os.path.join(tmp, "m.pkl")
        _dicom_to_png16(dcm_path, png)
        crop_single_mammogram(png, "NO", view, crop, meta, 100, 50)
        get_optimal_center_single(crop, meta)
        md = pickling.unpickle_from_file(meta)
        orig = loading.read_image_png(png).astype(np.float32)      # original (H0,W0)
        cropped = loading.read_image_png(crop).astype(np.float32)
        fc = loading.flip_image(cropped, view, md["horizontal_flip"])
        proc = loading.process_image(fc.copy(), view, md["best_center"])
        x = torch.from_numpy(np.expand_dims(np.expand_dims(proc, 0), 0).copy()).float()
        model = _get_model()
        with torch.no_grad():
            out = model(x).cpu().numpy()
            sal_mal = model.saliency_map.cpu().numpy()[0, 1]  # malignant saliency (h,w)
        # MIL fine-tune faqat malignant chiqishini supervise qildi; xom benign
        # bosh ma'lumotsiz (~0.5). malignant — asosiy skor, benign = 1 - malignant.
        malignant = float(out[0, 1])
        benign = round(1.0 - malignant, 4)
        result = {
            "view": view,
            "benign": benign,
            "malignant": round(malignant, 4),
            "label": "malignant" if malignant >= 0.5 else "benign",
            "model": "gmic_bm_finetuned",
        }
        if want_saliency:
            try:
                result["saliency_png"] = _saliency_overlay_b64(
                    orig, fc, sal_mal, view, md)
            except Exception:
                result["saliency_png"] = None
        return result
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)
