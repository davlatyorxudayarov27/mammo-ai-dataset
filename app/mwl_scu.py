"""
Modality Worklist (MWL) SCU CLI.

Real DICOM modality worklist serveridan ish ro'yxatini olib, lokal `worklist`
jadvaliga import qiladi (CSV import o'rniga).

Foydalanish:
    pip install pynetdicom
    python -m app.mwl_scu --host 192.168.1.100 --port 4242 \\
        --aet ORTHANC --calling MAMOGRAF_SCU --modality MG \\
        --date today

Quvvatlanadigan filtrlar:
    --modality MG | CT | MR | ...
    --date today | YYYYMMDD | YYYYMMDD-YYYYMMDD
    --patient-id <ID>
    --station-aet <SCHEDULED_STATION_AE>

`pynetdicom` o'rnatilmagan bo'lsa CLI ishlamaydi (lazy import). Production'da
uni alohida o'rnatish tavsiya etiladi (qariyb 30MB, CI'da kerak emas).
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from typing import Optional

from .db import get_conn, init_db


def _parse_date_arg(s: str) -> str:
    s = s.strip().lower()
    if not s or s == "any":
        return ""
    if s == "today":
        return datetime.now().strftime("%Y%m%d")
    if "-" in s and len(s.replace("-", "")) == 16:
        return s
    if len(s) == 8 and s.isdigit():
        return s
    return s


def query(
    host: str,
    port: int,
    aet: str,
    calling_aet: str = "MAMOGRAF_SCU",
    modality: str = "",
    study_date: str = "",
    patient_id: str = "",
    station_aet: str = "",
    timeout: int = 30,
) -> list[dict]:
    try:
        from pydicom.dataset import Dataset
        from pynetdicom import AE
        from pynetdicom.sop_class import ModalityWorklistInformationFind
    except ImportError as e:
        raise RuntimeError(
            "pynetdicom installed kerak: pip install pynetdicom"
        ) from e

    ae = AE(ae_title=calling_aet)
    ae.add_requested_context(ModalityWorklistInformationFind)
    ae.acse_timeout = timeout
    ae.dimse_timeout = timeout

    ds = Dataset()
    ds.PatientName = ""
    ds.PatientID = patient_id or ""
    ds.PatientBirthDate = ""
    ds.PatientSex = ""
    ds.AccessionNumber = ""
    ds.RequestedProcedureID = ""

    sps = Dataset()
    sps.Modality = modality or ""
    sps.ScheduledStationAETitle = station_aet or ""
    sps.ScheduledProcedureStepStartDate = study_date or ""
    sps.ScheduledProcedureStepStartTime = ""
    sps.ScheduledProcedureStepDescription = ""
    sps.ScheduledPerformingPhysicianName = ""
    ds.ScheduledProcedureStepSequence = [sps]

    print(f"[mwl] connecting to {host}:{port} (AET {aet})...")
    assoc = ae.associate(host, port, ae_title=aet)
    if not assoc.is_established:
        raise RuntimeError(f"failed to associate with {host}:{port} ({aet})")

    found: list[dict] = []
    try:
        responses = assoc.send_c_find(ds, ModalityWorklistInformationFind)
        for status, identifier in responses:
            if status is None:
                continue
            if status.Status in (0xFF00, 0xFF01) and identifier:
                rec = _identifier_to_record(identifier)
                if rec:
                    found.append(rec)
    finally:
        assoc.release()

    return found


def _identifier_to_record(identifier) -> Optional[dict]:
    pid = str(getattr(identifier, "PatientID", "") or "").strip()
    if not pid:
        return None
    name = str(getattr(identifier, "PatientName", "") or "").replace("^", " ").strip()
    sex = str(getattr(identifier, "PatientSex", "") or "").strip()
    dob = _format_dicom_date(getattr(identifier, "PatientBirthDate", ""))

    sps_seq = getattr(identifier, "ScheduledProcedureStepSequence", None)
    modality = ""
    study_date = ""
    if sps_seq:
        sps = sps_seq[0]
        modality = str(getattr(sps, "Modality", "") or "").strip()
        study_date = _format_dicom_date(
            getattr(sps, "ScheduledProcedureStepStartDate", "")
        )

    return {
        "patient_id": pid,
        "patient_name": name or None,
        "sex": sex or None,
        "dob": dob,
        "study_date": study_date,
        "modality": modality or None,
        "has_file": 0,
        "has_report": 0,
        "report_status": None,
    }


def _format_dicom_date(value) -> Optional[str]:
    s = str(value or "").strip()
    if len(s) == 8 and s.isdigit():
        return f"{s[:4]}-{s[4:6]}-{s[6:8]}"
    return s or None


def import_into_worklist(rows: list[dict]) -> int:
    init_db()
    if not rows:
        return 0
    now = datetime.now(timezone.utc).isoformat()
    inserted = 0
    with get_conn() as c:
        for r in rows:
            cur = c.execute(
                "SELECT id FROM worklist WHERE patient_id=? AND study_date=? AND modality=?",
                (r["patient_id"], r["study_date"], r["modality"]),
            ).fetchone()
            if cur:
                c.execute(
                    "UPDATE worklist SET patient_name=?, sex=?, dob=?, "
                    "has_file=?, has_report=?, report_status=?, imported_at=? "
                    "WHERE id=?",
                    (r["patient_name"], r["sex"], r["dob"],
                     r["has_file"], r["has_report"], r["report_status"],
                     now, cur[0]),
                )
            else:
                c.execute(
                    "INSERT INTO worklist "
                    "(patient_id, patient_name, sex, dob, study_date, modality, "
                    "has_file, has_report, report_status, priority, status, imported_at) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (r["patient_id"], r["patient_name"], r["sex"], r["dob"],
                     r["study_date"], r["modality"],
                     r["has_file"], r["has_report"], r["report_status"],
                     "normal", "pending", now),
                )
                inserted += 1
        c.commit()
    return inserted


def main():
    ap = argparse.ArgumentParser(description="MWL SCU - DICOM worklist'ni server'dan olib import qilish")
    ap.add_argument("--host", required=True, help="MWL server host/IP")
    ap.add_argument("--port", required=True, type=int, help="MWL server portu")
    ap.add_argument("--aet", required=True, help="MWL server AE Title (called)")
    ap.add_argument("--calling", default="MAMOGRAF_SCU", help="bizning AE Title (calling)")
    ap.add_argument("--modality", default="", help="masalan, MG / CT / MR")
    ap.add_argument("--date", default="", help="today | YYYYMMDD | YYYYMMDD-YYYYMMDD")
    ap.add_argument("--patient-id", default="", help="aniq bemor ID")
    ap.add_argument("--station-aet", default="", help="ScheduledStationAETitle")
    ap.add_argument("--dry-run", action="store_true", help="DB ga yozmaydi, faqat ko'rsatadi")
    ap.add_argument("--timeout", type=int, default=30)
    args = ap.parse_args()

    try:
        rows = query(
            host=args.host,
            port=args.port,
            aet=args.aet,
            calling_aet=args.calling,
            modality=args.modality,
            study_date=_parse_date_arg(args.date),
            patient_id=args.patient_id,
            station_aet=args.station_aet,
            timeout=args.timeout,
        )
    except Exception as e:
        print(f"[xato] {e}", file=sys.stderr)
        sys.exit(1)

    print(f"[mwl] {len(rows)} ta yozuv topildi")
    for r in rows[:10]:
        print(f"  {r['patient_id']:<12} {r['patient_name']:<25} {r['modality']:<5} {r['study_date']}")
    if len(rows) > 10:
        print(f"  ... va yana {len(rows) - 10} ta")

    if args.dry_run:
        print("[dry-run] DB ga yozilmadi")
        return

    inserted = import_into_worklist(rows)
    print(f"[mwl] worklist jadvaliga {inserted} ta yangi yozuv qo'shildi (qolgan {len(rows) - inserted} ta yangilandi)")


if __name__ == "__main__":
    main()
