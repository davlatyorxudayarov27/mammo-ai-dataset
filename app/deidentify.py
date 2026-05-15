from __future__ import annotations

import io
from datetime import datetime
from pathlib import Path

import pydicom
from pydicom.uid import ImplicitVRLittleEndian


PHI_TAGS: dict[str, str] = {
    "PatientName": "ANONYMOUS^PATIENT",
    "PatientID": "ANON",
    "PatientBirthDate": "19000101",
    "PatientSex": None,
    "PatientAge": None,
    "PatientAddress": "",
    "PatientTelephoneNumbers": "",
    "PatientMotherBirthName": "",
    "OtherPatientIDs": "",
    "OtherPatientNames": "",
    "EthnicGroup": "",
    "ReferringPhysicianName": "",
    "ReferringPhysicianAddress": "",
    "ReferringPhysicianTelephoneNumbers": "",
    "PerformingPhysicianName": "",
    "OperatorsName": "",
    "PhysiciansOfRecord": "",
    "RequestingPhysician": "",
    "InstitutionName": "",
    "InstitutionAddress": "",
    "InstitutionalDepartmentName": "",
    "StationName": "",
    "DeviceSerialNumber": "",
    "AccessionNumber": "",
    "StudyID": "",
    "FillerOrderNumberImagingServiceRequest": "",
    "PlacerOrderNumberImagingServiceRequest": "",
}

DATE_TAGS_KEEP_YEAR = (
    "StudyDate", "SeriesDate", "AcquisitionDate", "ContentDate",
)


def detect_phi(path: Path) -> dict:
    ds = pydicom.dcmread(str(path), stop_before_pixels=True, force=True)
    found = []
    for tag in PHI_TAGS:
        if tag in ds:
            v = ds.get(tag)
            try:
                s = str(v)
            except Exception:
                s = repr(v)
            found.append({"tag": tag, "value": s[:80]})
    for tag in DATE_TAGS_KEEP_YEAR:
        if tag in ds:
            try:
                s = str(ds.get(tag))
            except Exception:
                s = ""
            found.append({"tag": tag, "value": s, "preserves_year": True})
    return {"file": str(path), "phi_tags_found": found, "count": len(found)}


def anonymize_to_bytes(path: Path) -> bytes:
    ds = pydicom.dcmread(str(path), force=True)
    if not getattr(ds, "file_meta", None) or not getattr(ds.file_meta, "TransferSyntaxUID", None):
        meta = pydicom.dataset.FileMetaDataset()
        meta.TransferSyntaxUID = ImplicitVRLittleEndian
        ds.file_meta = meta

    for tag, replacement in PHI_TAGS.items():
        if tag in ds:
            if replacement is None:
                del ds[tag]
            else:
                try:
                    ds.data_element(tag).value = replacement
                except Exception:
                    pass

    for tag in DATE_TAGS_KEEP_YEAR:
        if tag in ds:
            try:
                cur = str(ds.data_element(tag).value)
                if len(cur) >= 4 and cur[:4].isdigit():
                    ds.data_element(tag).value = cur[:4] + "0101"
            except Exception:
                pass

    if "PatientIdentityRemoved" in ds:
        ds.PatientIdentityRemoved = "YES"
    else:
        try:
            ds.add_new(0x00120062, "CS", "YES")
        except Exception:
            pass
    try:
        ds.add_new(0x00120063, "LO", f"MAMOGRAF de-id {datetime.now().strftime('%Y-%m-%d')}")
    except Exception:
        pass

    buf = io.BytesIO()
    ds.save_as(buf, write_like_original=False)
    return buf.getvalue()
