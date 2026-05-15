from __future__ import annotations

import io
from pathlib import Path
from typing import Optional

import numpy as np
import pydicom
from PIL import Image, ImageDraw


def _polygon_mask(rows: int, cols: int, points_norm: list[list[float]]) -> np.ndarray:
    img = Image.new("L", (cols, rows), 0)
    if len(points_norm) >= 3:
        pts = [(int(round(p[0] * cols)), int(round(p[1] * rows))) for p in points_norm]
        ImageDraw.Draw(img).polygon(pts, fill=1)
    return np.array(img, dtype=np.uint8)


def _bbox_mask(rows: int, cols: int, bbox: list[float]) -> np.ndarray:
    img = Image.new("L", (cols, rows), 0)
    if len(bbox) == 4:
        x0 = int(round(bbox[0] * cols))
        y0 = int(round(bbox[1] * rows))
        x1 = int(round((bbox[0] + bbox[2]) * cols))
        y1 = int(round((bbox[1] + bbox[3]) * rows))
        ImageDraw.Draw(img).rectangle([x0, y0, x1, y1], fill=1)
    return np.array(img, dtype=np.uint8)


def annotations_to_seg(
    src_path: Path,
    annotations: list[dict],
    rows: Optional[int] = None,
    cols: Optional[int] = None,
    series_description: str = "MAMOGRAF annotations SEG",
) -> bytes:
    try:
        import highdicom as hd
    except ImportError as e:
        raise RuntimeError("highdicom kerak: pip install highdicom") from e

    src = pydicom.dcmread(str(src_path), force=True)
    if not getattr(src, "file_meta", None) or not getattr(src.file_meta, "TransferSyntaxUID", None):
        from pydicom.uid import ImplicitVRLittleEndian
        meta = pydicom.dataset.FileMetaDataset()
        meta.TransferSyntaxUID = ImplicitVRLittleEndian
        src.file_meta = meta

    if rows is None or cols is None:
        rows = int(getattr(src, "Rows", 0) or 0)
        cols = int(getattr(src, "Columns", 0) or 0)
    if not rows or not cols:
        raise RuntimeError("source DICOM rows/cols topilmadi")

    by_label: dict[str, list[dict]] = {}
    for a in annotations:
        if a.get("status") == "rejected":
            continue
        lbl = a.get("label") or "finding"
        by_label.setdefault(lbl, []).append(a)
    if not by_label:
        raise RuntimeError("eksport qilinadigan annotation yo'q")

    has_for_uid = bool(src.get("FrameOfReferenceUID"))
    multi_segment = has_for_uid and len(by_label) > 1

    segment_descriptions = []
    masks_per_segment = []
    for seg_num, (label, anns) in enumerate(sorted(by_label.items()), start=1):
        combined = np.zeros((rows, cols), dtype=np.uint8)
        for a in anns:
            if a.get("type") == "polygon" and a.get("points"):
                combined |= _polygon_mask(rows, cols, a["points"])
            else:
                combined |= _bbox_mask(rows, cols, a.get("bbox") or [0, 0, 0, 0])
        if combined.sum() == 0:
            continue
        masks_per_segment.append((label, combined.astype(bool)))

    if not masks_per_segment:
        raise RuntimeError("hech qanday segment yaratilmadi")

    if not multi_segment:
        merged = np.zeros((rows, cols), dtype=bool)
        labels_used = []
        for label, m in masks_per_segment:
            merged |= m
            labels_used.append(label)
        masks_per_segment = [(", ".join(labels_used[:5]), merged)]

    for seg_num, (label, _) in enumerate(masks_per_segment, start=1):
        seg_desc = hd.seg.SegmentDescription(
            segment_number=seg_num,
            segment_label=label,
            segmented_property_category=hd.sr.CodedConcept(
                "49755003", "SCT", "Morphologically Abnormal Structure"
            ),
            segmented_property_type=hd.sr.CodedConcept(
                "108369006", "SCT", "Neoplasm"
            ),
            algorithm_type=hd.seg.SegmentAlgorithmTypeValues.MANUAL,
            algorithm_identification=hd.AlgorithmIdentificationSequence(
                name="MAMOGRAF",
                version="1.0",
                family=hd.sr.CodedConcept("113076", "DCM", "Segmentation"),
            ),
            tracking_uid=hd.UID(),
            tracking_id=label,
        )
        segment_descriptions.append(seg_desc)

    if multi_segment:
        pixel_array = np.stack([m for _, m in masks_per_segment], axis=-1).astype(np.uint8)
    else:
        pixel_array = masks_per_segment[0][1]

    seg = hd.seg.Segmentation(
        source_images=[src],
        pixel_array=pixel_array,
        segmentation_type=hd.seg.SegmentationTypeValues.BINARY,
        segment_descriptions=segment_descriptions,
        series_instance_uid=hd.UID(),
        series_number=9998,
        sop_instance_uid=hd.UID(),
        instance_number=1,
        manufacturer="MAMOGRAF",
        manufacturer_model_name="MAMOGRAF DICOM Viewer",
        software_versions="1.0",
        device_serial_number="0",
        series_description=series_description,
    )

    buf = io.BytesIO()
    seg.save_as(buf, write_like_original=False)
    return buf.getvalue()
