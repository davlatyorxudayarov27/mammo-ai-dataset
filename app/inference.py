from __future__ import annotations

import io
import threading
from pathlib import Path
from typing import Optional

from PIL import Image

MODELS_DIR = Path(__file__).resolve().parent / "models"
MODELS_DIR.mkdir(exist_ok=True)

_model_cache: dict[str, object] = {}
_cache_lock = threading.Lock()


def is_available() -> tuple[bool, str]:
    try:
        import ultralytics  # noqa: F401
    except ImportError as e:
        return False, f"ultralytics not installed: {e}"
    return True, ""


def device_info() -> dict:
    try:
        import torch
        cuda_ok = bool(torch.cuda.is_available())
        return {
            "torch": torch.__version__,
            "cuda_available": cuda_ok,
            "device": "cuda:0" if cuda_ok else "cpu",
            "device_name": torch.cuda.get_device_name(0) if cuda_ok else "CPU",
        }
    except ImportError:
        return {"torch": None, "cuda_available": False, "device": "cpu", "device_name": "CPU"}


def list_models() -> list[dict]:
    out = []
    for p in sorted(MODELS_DIR.glob("*.pt")):
        try:
            size = p.stat().st_size
        except OSError:
            size = 0
        out.append({"name": p.name, "stem": p.stem, "size_bytes": size})
    return out


def _resolve_model_path(name: str) -> Path:
    safe = Path(name).name
    if not safe.endswith(".pt"):
        safe += ".pt"
    p = MODELS_DIR / safe
    if not p.exists() or not p.is_file():
        raise FileNotFoundError(f"model weights not found: {safe}")
    return p


def get_model(name: str):
    p = _resolve_model_path(name)
    key = str(p)
    with _cache_lock:
        cached = _model_cache.get(key)
        if cached is not None:
            return cached
        from ultralytics import YOLO
        model = YOLO(str(p))
        _model_cache[key] = model
        return model


def infer_png(
    png_bytes: bytes,
    model_name: str,
    conf: float = 0.25,
    iou: float = 0.5,
    imgsz: int = 1024,
) -> dict:
    ok, err = is_available()
    if not ok:
        raise RuntimeError(err)

    model = get_model(model_name)

    img = Image.open(io.BytesIO(png_bytes))
    if img.mode == "L":
        img = img.convert("RGB")
    elif img.mode != "RGB":
        img = img.convert("RGB")

    img_w, img_h = img.size

    results = model.predict(
        source=img,
        conf=conf,
        iou=iou,
        imgsz=imgsz,
        verbose=False,
    )

    detections = []
    if results:
        r = results[0]
        names = r.names if hasattr(r, "names") else getattr(model, "names", {})
        boxes = getattr(r, "boxes", None)
        if boxes is not None and len(boxes) > 0:
            xyxy = boxes.xyxy.cpu().numpy()
            confs = boxes.conf.cpu().numpy()
            clss = boxes.cls.cpu().numpy().astype(int)
            for (x1, y1, x2, y2), c, k in zip(xyxy, confs, clss):
                w = max(0.0, float(x2 - x1))
                h = max(0.0, float(y2 - y1))
                detections.append({
                    "label": str(names.get(int(k), int(k))) if isinstance(names, dict) else str(int(k)),
                    "class_id": int(k),
                    "confidence": float(c),
                    "bbox": [
                        float(x1) / img_w,
                        float(y1) / img_h,
                        w / img_w,
                        h / img_h,
                    ],
                    "bbox_pixels": [float(x1), float(y1), w, h],
                })

    return {
        "model": model_name,
        "image_size": [img_w, img_h],
        "device": device_info().get("device", "cpu"),
        "detections": detections,
        "params": {"conf": conf, "iou": iou, "imgsz": imgsz},
    }
