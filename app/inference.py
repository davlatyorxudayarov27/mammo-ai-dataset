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
    tta: bool = False,
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
        augment=tta,          # test-time augmentation (multi-scale + flips)
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
        "params": {"conf": conf, "iou": iou, "imgsz": imgsz, "tta": tta},
    }


# --------------------------------------------------------------------------- #
# Classification (image-level diagnosis, e.g. benign / malignant)             #
# Klassifikatsiya modellari fayl nomi `_cls.pt` bilan tugaydi — shu konvensiya #
# bo'yicha detection modellaridan ajratiladi (detection dropdown'ga tushmaydi).#
# --------------------------------------------------------------------------- #
def is_cls_model(name: str) -> bool:
    return str(name).lower().endswith("_cls.pt")


def list_detection_models() -> list[dict]:
    return [m for m in list_models() if not is_cls_model(m["name"])]


def list_cls_models() -> list[dict]:
    return [m for m in list_models() if is_cls_model(m["name"])]


def classify_png(png_bytes: bytes, model_name: str, imgsz: int = 384) -> dict:
    """Bitta rasm uchun klassifikatsiya — har klass ehtimoli bilan."""
    ok, err = is_available()
    if not ok:
        raise RuntimeError(err)
    model = get_model(model_name)
    img = Image.open(io.BytesIO(png_bytes))
    if img.mode != "RGB":
        img = img.convert("RGB")
    results = model.predict(source=img, imgsz=imgsz, verbose=False)
    if not results:
        raise RuntimeError("natija yo'q")
    r = results[0]
    probs = getattr(r, "probs", None)
    if probs is None:
        raise RuntimeError("bu model klassifikatsiya emas (probs topilmadi)")
    names = r.names if hasattr(r, "names") else getattr(model, "names", {})

    def _nm(i):
        return str(names.get(int(i), int(i))) if isinstance(names, dict) else str(int(i))

    data = probs.data.cpu().numpy().tolist()
    top1 = int(probs.top1)
    return {
        "model": model_name,
        "top1_label": _nm(top1),
        "top1_conf": float(probs.top1conf),
        "probs": {_nm(i): float(p) for i, p in enumerate(data)},
        "device": device_info().get("device", "cpu"),
    }


# --------------------------------------------------------------------------- #
# Weighted Boxes Fusion + ensemble                                            #
# --------------------------------------------------------------------------- #
def _iou_xyxy(a, b) -> float:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    inter = iw * ih
    if inter <= 0:
        return 0.0
    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    return inter / (area_a + area_b - inter + 1e-9)


def weighted_boxes_fusion(per_source_dets: list[list[dict]], iou_thr: float = 0.55,
                          num_sources: Optional[int] = None) -> list[dict]:
    """Fuse detections from several sources (models or TTA passes).

    Each detection is ``{label, class_id, confidence, bbox=[x,y,w,h], ...}``
    in normalised coords. Boxes of the same label that overlap (IoU > thr) are
    merged into one box whose coordinates are score-weighted averages and whose
    score reflects cross-source agreement (canonical WBF).
    """
    if num_sources is None:
        num_sources = len(per_source_dets)
    num_sources = max(1, num_sources)

    # Flatten to xyxy with label key.
    items = []
    for dets in per_source_dets:
        for d in dets:
            x, y, w, h = d["bbox"]
            items.append({
                "label": d.get("label"),
                "class_id": d.get("class_id"),
                "score": float(d.get("confidence", 0.0)),
                "box": [x, y, x + w, y + h],
            })
    items.sort(key=lambda it: it["score"], reverse=True)

    clusters: list[dict] = []  # each: {label, boxes:[...], scores:[...], fused:[xyxy]}
    for it in items:
        placed = False
        for cl in clusters:
            if cl["label"] == it["label"] and _iou_xyxy(cl["fused"], it["box"]) > iou_thr:
                cl["boxes"].append(it["box"])
                cl["scores"].append(it["score"])
                cl["class_id"] = it["class_id"]
                w = sum(cl["scores"])
                cl["fused"] = [
                    sum(b[i] * s for b, s in zip(cl["boxes"], cl["scores"])) / w
                    for i in range(4)
                ]
                placed = True
                break
        if not placed:
            clusters.append({
                "label": it["label"], "class_id": it["class_id"],
                "boxes": [it["box"]], "scores": [it["score"]], "fused": list(it["box"]),
            })

    out = []
    for cl in clusters:
        n = len(cl["scores"])
        # WBF score: mean confidence rescaled by agreement across sources.
        score = (sum(cl["scores"]) / n) * min(1.0, n / num_sources)
        x1, y1, x2, y2 = cl["fused"]
        out.append({
            "label": cl["label"],
            "class_id": cl["class_id"],
            "confidence": float(score),
            "bbox": [x1, y1, max(0.0, x2 - x1), max(0.0, y2 - y1)],
            "n_models": n,
        })
    out.sort(key=lambda d: d["confidence"], reverse=True)
    return out


def infer_ensemble(
    png_bytes: bytes,
    model_names: list[str],
    conf: float = 0.25,
    iou: float = 0.5,
    imgsz: int = 1024,
    tta: bool = False,
    wbf_iou: float = 0.55,
) -> dict:
    """Run several models and fuse their detections with Weighted Boxes Fusion."""
    ok, err = is_available()
    if not ok:
        raise RuntimeError(err)

    per_model: list[list[dict]] = []
    used: list[str] = []
    img_w = img_h = 0
    for name in model_names:
        try:
            r = infer_png(png_bytes, name, conf=conf, iou=iou, imgsz=imgsz, tta=tta)
        except FileNotFoundError:
            continue
        used.append(name)
        img_w, img_h = r["image_size"]
        per_model.append(r["detections"])
    if not used:
        raise FileNotFoundError("no usable models for ensemble")

    fused = weighted_boxes_fusion(per_model, iou_thr=wbf_iou, num_sources=len(used))
    return {
        "model": "ensemble:" + ",".join(used),
        "ensemble_models": used,
        "image_size": [img_w, img_h],
        "device": device_info().get("device", "cpu"),
        "detections": fused,
        "params": {"conf": conf, "iou": iou, "imgsz": imgsz, "tta": tta, "wbf_iou": wbf_iou},
    }
