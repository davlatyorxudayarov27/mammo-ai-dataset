from __future__ import annotations

import io
from datetime import datetime
from pathlib import Path
from typing import Optional

import pydicom
from pydicom.dataset import Dataset, FileDataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian, generate_uid


COMPREHENSIVE_SR_CLASS_UID = "1.2.840.10008.5.1.4.1.1.88.33"
DCM_CODING_SCHEME = "DCM"


def _coded_concept(code: str, scheme: str, meaning: str) -> Dataset:
    ds = Dataset()
    ds.CodeValue = code
    ds.CodingSchemeDesignator = scheme
    ds.CodeMeaning = meaning
    return ds


def _text_item(label: str, text: str) -> Dataset:
    item = Dataset()
    item.RelationshipType = "CONTAINS"
    item.ValueType = "TEXT"
    item.ConceptNameCodeSequence = [_coded_concept("121071", DCM_CODING_SCHEME, label)]
    item.TextValue = text
    return item


def _num_item(label: str, value: float, unit_code: str = "1") -> Dataset:
    item = Dataset()
    item.RelationshipType = "CONTAINS"
    item.ValueType = "NUM"
    item.ConceptNameCodeSequence = [_coded_concept("121070", DCM_CODING_SCHEME, label)]
    measured = Dataset()
    measured.NumericValue = str(value)
    units = Dataset()
    units.CodeValue = unit_code
    units.CodingSchemeDesignator = "UCUM"
    units.CodeMeaning = unit_code
    measured.MeasurementUnitsCodeSequence = [units]
    item.MeasuredValueSequence = [measured]
    return item


def _container_item(label: str, children: list[Dataset]) -> Dataset:
    c = Dataset()
    c.RelationshipType = "CONTAINS"
    c.ValueType = "CONTAINER"
    c.ContinuityOfContent = "SEPARATE"
    c.ConceptNameCodeSequence = [_coded_concept("121111", DCM_CODING_SCHEME, label)]
    c.ContentSequence = children
    return c


def report_to_sr(
    src_path: Path,
    report_text: str,
    findings: Optional[dict] = None,
    author: Optional[str] = None,
    verified: bool = False,
) -> bytes:
    """Tayyor mammografiya hisobotini (narrativ matn + strukturaviy topilmalar)
    DICOM Comprehensive SR sifatida quradi. Bemor/study metadata manba DICOM'dan
    meros qilib olinadi."""
    src = pydicom.dcmread(str(src_path), stop_before_pixels=True, force=True)

    now = datetime.now()
    sr_date = now.strftime("%Y%m%d")
    sr_time = now.strftime("%H%M%S")

    meta = FileMetaDataset()
    meta.MediaStorageSOPClassUID = COMPREHENSIVE_SR_CLASS_UID
    meta.MediaStorageSOPInstanceUID = generate_uid()
    meta.TransferSyntaxUID = ExplicitVRLittleEndian
    meta.ImplementationClassUID = generate_uid()
    meta.ImplementationVersionName = "MAMOGRAF_SR"

    sr = FileDataset(None, {}, file_meta=meta, preamble=b"\0" * 128)
    sr.SOPClassUID = meta.MediaStorageSOPClassUID
    sr.SOPInstanceUID = meta.MediaStorageSOPInstanceUID
    sr.Modality = "SR"
    sr.SeriesInstanceUID = generate_uid()
    sr.StudyInstanceUID = src.get("StudyInstanceUID", generate_uid())
    sr.SeriesNumber = 9998
    sr.InstanceNumber = 1
    sr.SeriesDescription = "MAMOGRAF report"

    for tag in (
        "PatientName", "PatientID", "PatientBirthDate", "PatientSex",
        "StudyDate", "StudyTime", "AccessionNumber", "ReferringPhysicianName",
    ):
        if tag in src:
            try:
                sr[tag] = src[tag]
            except Exception:
                pass

    sr.ContentDate = sr_date
    sr.ContentTime = sr_time
    sr.InstanceCreationDate = sr_date
    sr.InstanceCreationTime = sr_time
    sr.SpecificCharacterSet = "ISO_IR 192"

    if author:
        author_ds = Dataset()
        author_ds.PersonName = author
        sr.AuthorObserverSequence = [author_ds]

    sr.CompletionFlag = "COMPLETE"
    sr.VerificationFlag = "VERIFIED" if verified else "UNVERIFIED"
    sr.PreliminaryFlag = "FINAL"

    sr.ValueType = "CONTAINER"
    sr.ContinuityOfContent = "SEPARATE"
    sr.ConceptNameCodeSequence = [
        _coded_concept("11528-7", "LN", "Radiology Report")
    ]

    children: list[Dataset] = [_text_item("Report", report_text or "")]

    findings = findings or {}
    overall = findings.get("overall_birads")
    if overall:
        children.append(_text_item("Assessment", f"BI-RADS {overall}"))
    rec = findings.get("recommendation")
    if rec:
        children.append(_text_item("Recommendation", rec))

    lesion_items: list[Dataset] = []
    for i, l in enumerate(findings.get("lesions", []) or [], start=1):
        parts = [f"#{i} {l.get('type', '')}".strip()]
        if l.get("laterality"):
            parts.append(f"laterallik: {l['laterality']}")
        if l.get("view"):
            parts.append(f"proeksiya: {l['view']}")
        if l.get("quadrant"):
            parts.append(f"lokalizatsiya: {l['quadrant']}")
        if l.get("size_mm"):
            parts.append(f"o'lcham: ~{float(l['size_mm']):.0f} mm")
        if l.get("margin"):
            parts.append(f"chegara: {l['margin']}")
        if l.get("birads"):
            parts.append(f"BI-RADS: {l['birads']}")
        lesion_items.append(_text_item("Finding", "\n".join(parts)))
    if lesion_items:
        children.append(_container_item("Findings", lesion_items))

    sr.ContentSequence = children

    buf = io.BytesIO()
    sr.is_little_endian = True
    sr.is_implicit_VR = False
    sr.save_as(buf, write_like_original=False)
    return buf.getvalue()


def annotations_to_sr(
    src_path: Path,
    annotations: list[dict],
    rows: Optional[int] = None,
    cols: Optional[int] = None,
    author: Optional[str] = None,
) -> bytes:
    src = pydicom.dcmread(str(src_path), stop_before_pixels=True, force=True)

    now = datetime.now()
    sr_date = now.strftime("%Y%m%d")
    sr_time = now.strftime("%H%M%S")

    meta = FileMetaDataset()
    meta.MediaStorageSOPClassUID = COMPREHENSIVE_SR_CLASS_UID
    meta.MediaStorageSOPInstanceUID = generate_uid()
    meta.TransferSyntaxUID = ExplicitVRLittleEndian
    meta.ImplementationClassUID = generate_uid()
    meta.ImplementationVersionName = "MAMOGRAF_SR"

    sr = FileDataset(None, {}, file_meta=meta, preamble=b"\0" * 128)
    sr.SOPClassUID = meta.MediaStorageSOPClassUID
    sr.SOPInstanceUID = meta.MediaStorageSOPInstanceUID
    sr.Modality = "SR"
    sr.SeriesInstanceUID = generate_uid()
    sr.StudyInstanceUID = src.get("StudyInstanceUID", generate_uid())
    sr.SeriesNumber = 9999
    sr.InstanceNumber = 1
    sr.SeriesDescription = "MAMOGRAF annotations"

    for tag in (
        "PatientName", "PatientID", "PatientBirthDate", "PatientSex",
        "StudyDate", "StudyTime", "AccessionNumber", "ReferringPhysicianName",
    ):
        if tag in src:
            try:
                sr[tag] = src[tag]
            except Exception:
                pass

    sr.ContentDate = sr_date
    sr.ContentTime = sr_time
    sr.InstanceCreationDate = sr_date
    sr.InstanceCreationTime = sr_time
    sr.SpecificCharacterSet = "ISO_IR 192"

    if author:
        author_ds = Dataset()
        author_ds.PersonName = author
        sr.AuthorObserverSequence = [author_ds]

    sr.CompletionFlag = "COMPLETE"
    sr.VerificationFlag = "UNVERIFIED"
    sr.PreliminaryFlag = "FINAL"

    sr.ValueType = "CONTAINER"
    sr.ContinuityOfContent = "SEPARATE"
    sr.ConceptNameCodeSequence = [
        _coded_concept("11528-7", "LN", "Radiology Report")
    ]

    findings_children: list[Dataset] = []
    measurements_children: list[Dataset] = []

    for i, a in enumerate(annotations, start=1):
        if a.get("status") not in (None, "approved", "submitted"):
            pass
        label = a.get("label") or "finding"
        bi_rads = a.get("bi_rads") or ""
        ann_type = a.get("type") or "bbox"
        bbox = a.get("bbox") or [0, 0, 0, 0]

        if rows and cols and len(bbox) == 4:
            x_px = round(bbox[0] * cols, 1)
            y_px = round(bbox[1] * rows, 1)
            w_px = round(bbox[2] * cols, 1)
            h_px = round(bbox[3] * rows, 1)
            geom_str = f"{ann_type} pixel x={x_px} y={y_px} w={w_px} h={h_px}"
        else:
            geom_str = (
                f"{ann_type} normalized x={bbox[0]:.4f} y={bbox[1]:.4f} "
                f"w={bbox[2]:.4f} h={bbox[3]:.4f}"
            )
        if ann_type == "polygon" and a.get("points"):
            geom_str += f" · {len(a['points'])} nuqta"

        text_lines = [
            f"#{i}  {label}",
            f"  status: {a.get('status', 'draft')}",
            f"  geometry: {geom_str}",
        ]
        if bi_rads:
            text_lines.insert(1, f"  BI-RADS: {bi_rads}")
        if a.get("created_by"):
            text_lines.append(f"  yaratdi: {a.get('created_by')}")
        if a.get("ai_source"):
            text_lines.append("  AI batch (izoh): AI batch tomonidan yaratilgan")
        if a.get("reviewed_by"):
            text_lines.append(f"  ko'rib chiqdi: {a.get('reviewed_by')}")
        if a.get("review_note"):
            text_lines.append(f"  reviewer izohi: {a.get('review_note')}")
        if a.get("note"):
            text_lines.append(f"  izoh: {a.get('note')}")

        findings_children.append(_text_item("Finding", "\n".join(text_lines)))

        if rows and cols and len(bbox) == 4:
            measurements_children.append(
                _num_item(f"#{i} {label} area px²",
                          round(bbox[2] * cols * bbox[3] * rows, 1))
            )

    summary = _text_item(
        "Summary",
        f"MAMOGRAF DICOM Viewer · {len(annotations)} annotation eksport qilindi · "
        f"{sr_date}",
    )

    sr.ContentSequence = [summary, _container_item("Findings", findings_children)]
    if measurements_children:
        sr.ContentSequence.append(
            _container_item("Measurements", measurements_children)
        )

    buf = io.BytesIO()
    sr.is_little_endian = True
    sr.is_implicit_VR = False
    sr.save_as(buf, write_like_original=False)
    return buf.getvalue()
