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


def anonymize_in_place(path: Path) -> None:
    """Anonimlashtirish + faylga qayta yozish (upload paytida)."""
    data = anonymize_to_bytes(path)
    path.write_bytes(data)


def is_deidentified(path: Path) -> bool:
    """Fayl allaqachon anonimlashtirilganmi (`PatientIdentityRemoved=YES` belgisi)."""
    try:
        ds = pydicom.dcmread(str(path), stop_before_pixels=True, force=True)
    except Exception:
        return False
    val = getattr(ds, "PatientIdentityRemoved", None)
    return str(val).upper() == "YES" if val is not None else False


def _cli():
    """`python -m app.deidentify <dir>` — papkadagi barcha `.dcm` fayllarni
    anonimlashtirish (faqat hali anonim emaslarni). Mavjud (eski) yuklar uchun."""
    import argparse, sys
    ap = argparse.ArgumentParser(description="Deidentify all DICOM files in a directory.")
    ap.add_argument("path", help="Papka yo'li (mas. app/uploads)")
    ap.add_argument("--force", action="store_true", help="Anonim deb belgilanganlarni ham qayta tozalash")
    args = ap.parse_args()

    root = Path(args.path)
    if not root.is_dir():
        print(f"[xato] papka topilmadi: {root}", file=sys.stderr)
        sys.exit(2)

    total = ok = skipped = failed = 0
    for p in sorted(root.glob("*.dcm")):
        total += 1
        try:
            if not args.force and is_deidentified(p):
                skipped += 1
                continue
            anonymize_in_place(p)
            ok += 1
            print(f"  ✓ {p.name}")
        except Exception as e:
            failed += 1
            print(f"  ✗ {p.name}: {e}", file=sys.stderr)

    print(f"\nJami: {total} | tozalandi: {ok} | o'tkazib yuborildi: {skipped} | xato: {failed}")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    _cli()
