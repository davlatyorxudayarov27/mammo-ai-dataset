"""
PACS DICOM SCU CLI: C-STORE (yuborish), C-FIND (qidirish), C-MOVE (olish).

Foydalanish:
    pip install pynetdicom

    # PACS'ga DICOM yuborish
    python -m app.pacs send --host 192.168.1.10 --port 4242 --aet ORTHANC \\
        path/to/file1.dcm path/to/file2.dcm

    # Bemor bo'yicha qidirish (C-FIND)
    python -m app.pacs query --host 192.168.1.10 --port 4242 --aet ORTHANC \\
        --patient-id 12345 --modality MG

    # Study'ni olish (C-MOVE — server bizga uzatadi)
    python -m app.pacs fetch --host 192.168.1.10 --port 4242 --aet ORTHANC \\
        --study-uid 1.2.3.4.5 --dest ./fetched/
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional


def _import_pynet():
    try:
        from pydicom.dataset import Dataset
        from pynetdicom import AE, evt, StoragePresentationContexts, debug_logger, Verification
        from pynetdicom.sop_class import (
            PatientRootQueryRetrieveInformationModelFind,
            PatientRootQueryRetrieveInformationModelMove,
            StudyRootQueryRetrieveInformationModelFind,
            StudyRootQueryRetrieveInformationModelMove,
            Verification as VerificationSOP,
        )
        return {
            "Dataset": Dataset, "AE": AE, "evt": evt,
            "StoragePresentationContexts": StoragePresentationContexts,
            "debug_logger": debug_logger,
            "Verification": VerificationSOP,
            "PatientFind": PatientRootQueryRetrieveInformationModelFind,
            "PatientMove": PatientRootQueryRetrieveInformationModelMove,
            "StudyFind": StudyRootQueryRetrieveInformationModelFind,
            "StudyMove": StudyRootQueryRetrieveInformationModelMove,
        }
    except ImportError as e:
        raise RuntimeError("pynetdicom kerak: pip install pynetdicom") from e


def echo(host: str, port: int, aet: str,
         calling_aet: str = "MAMOGRAF_SCU", timeout: int = 10) -> dict:
    pn = _import_pynet()
    ae = pn["AE"](ae_title=calling_aet)
    ae.add_requested_context(pn["Verification"])
    ae.acse_timeout = timeout
    ae.dimse_timeout = timeout
    assoc = ae.associate(host, port, ae_title=aet)
    if not assoc.is_established:
        raise RuntimeError(f"associate failed: {host}:{port} ({aet})")
    try:
        status = assoc.send_c_echo()
        ok = status is not None and status.Status == 0x0000
        return {"ok": ok, "status": status.Status if status else None}
    finally:
        assoc.release()


def store(host: str, port: int, aet: str, files: list[Path],
          calling_aet: str = "MAMOGRAF_SCU", timeout: int = 60) -> dict:
    pn = _import_pynet()
    import pydicom

    ae = pn["AE"](ae_title=calling_aet)
    for ctx in pn["StoragePresentationContexts"]:
        ae.add_requested_context(ctx.abstract_syntax)
    ae.acse_timeout = timeout
    ae.dimse_timeout = timeout

    sent = 0
    failed = 0
    print(f"[pacs] connecting to {host}:{port} (AET {aet})...")
    assoc = ae.associate(host, port, ae_title=aet)
    if not assoc.is_established:
        raise RuntimeError(f"associate failed: {host}:{port} ({aet})")
    try:
        for path in files:
            try:
                ds = pydicom.dcmread(str(path), force=True)
                status = assoc.send_c_store(ds)
                if status and status.Status == 0x0000:
                    sent += 1
                    print(f"  ✓ {path.name}")
                else:
                    failed += 1
                    code = status.Status if status else "no-status"
                    print(f"  ✗ {path.name}  status=0x{code:04X}" if isinstance(code, int) else f"  ✗ {path.name}  {code}")
            except Exception as e:
                failed += 1
                print(f"  ✗ {path.name}: {e}")
    finally:
        assoc.release()
    return {"sent": sent, "failed": failed}


def query(host: str, port: int, aet: str,
          patient_id: str = "", patient_name: str = "",
          modality: str = "", study_date: str = "",
          calling_aet: str = "MAMOGRAF_SCU", timeout: int = 30) -> list[dict]:
    pn = _import_pynet()
    Dataset = pn["Dataset"]
    ae = pn["AE"](ae_title=calling_aet)
    ae.add_requested_context(pn["StudyFind"])
    ae.acse_timeout = timeout
    ae.dimse_timeout = timeout

    ds = Dataset()
    ds.QueryRetrieveLevel = "STUDY"
    ds.PatientID = patient_id
    ds.PatientName = patient_name
    ds.PatientBirthDate = ""
    ds.PatientSex = ""
    ds.StudyInstanceUID = ""
    ds.StudyDate = study_date
    ds.StudyDescription = ""
    ds.AccessionNumber = ""
    ds.ModalitiesInStudy = modality

    print(f"[pacs] C-FIND on {host}:{port}...")
    assoc = ae.associate(host, port, ae_title=aet)
    if not assoc.is_established:
        raise RuntimeError(f"associate failed: {host}:{port} ({aet})")
    results = []
    try:
        for status, identifier in assoc.send_c_find(ds, pn["StudyFind"]):
            if status and status.Status in (0xFF00, 0xFF01) and identifier:
                results.append({
                    "patient_id": str(getattr(identifier, "PatientID", "") or ""),
                    "patient_name": str(getattr(identifier, "PatientName", "") or "").replace("^", " "),
                    "study_uid": str(getattr(identifier, "StudyInstanceUID", "") or ""),
                    "study_date": str(getattr(identifier, "StudyDate", "") or ""),
                    "modalities": str(getattr(identifier, "ModalitiesInStudy", "") or ""),
                    "description": str(getattr(identifier, "StudyDescription", "") or ""),
                    "accession": str(getattr(identifier, "AccessionNumber", "") or ""),
                })
    finally:
        assoc.release()
    return results


def fetch(host: str, port: int, aet: str, study_uid: str, dest: Path,
          calling_aet: str = "MAMOGRAF_SCU", scp_port: int = 11112,
          timeout: int = 120) -> dict:
    pn = _import_pynet()
    Dataset = pn["Dataset"]
    evt = pn["evt"]
    dest.mkdir(parents=True, exist_ok=True)
    received: list[str] = []

    def handle_store(event):
        ds = event.dataset
        ds.file_meta = event.file_meta
        sop = getattr(ds, "SOPInstanceUID", "instance")
        out = dest / f"{sop}.dcm"
        try:
            ds.save_as(str(out), write_like_original=False)
            received.append(out.name)
            print(f"  ← {out.name}")
        except Exception as e:
            print(f"  save xato: {e}")
            return 0xC001
        return 0x0000

    ae = pn["AE"](ae_title=calling_aet)
    ae.add_requested_context(pn["StudyMove"])
    for ctx in pn["StoragePresentationContexts"]:
        ae.add_supported_context(ctx.abstract_syntax)
    ae.acse_timeout = timeout
    ae.dimse_timeout = timeout

    handlers = [(evt.EVT_C_STORE, handle_store)]
    print(f"[pacs] starting local SCP on port {scp_port}...")
    scp = ae.start_server(("0.0.0.0", scp_port), block=False, evt_handlers=handlers,
                          ae_title=calling_aet)
    try:
        ds = Dataset()
        ds.QueryRetrieveLevel = "STUDY"
        ds.StudyInstanceUID = study_uid
        print(f"[pacs] C-MOVE study={study_uid} -> {calling_aet} ...")
        assoc = ae.associate(host, port, ae_title=aet)
        if not assoc.is_established:
            raise RuntimeError(f"associate failed: {host}:{port}")
        try:
            for status, identifier in assoc.send_c_move(ds, calling_aet, pn["StudyMove"]):
                if status and status.Status not in (0xFF00, 0x0000):
                    print(f"  status=0x{status.Status:04X}")
        finally:
            assoc.release()
    finally:
        scp.shutdown()
    return {"received": received, "count": len(received), "dest": str(dest)}


def _parse_files(args) -> list[Path]:
    out: list[Path] = []
    for f in args.files:
        p = Path(f)
        if not p.exists():
            print(f"fayl topilmadi: {p}", file=sys.stderr); sys.exit(1)
        if p.is_dir():
            out.extend(sorted(p.rglob("*.dcm")))
        else:
            out.append(p)
    return out


def main():
    ap = argparse.ArgumentParser(description="PACS DICOM SCU CLI")
    sub = ap.add_subparsers(dest="cmd", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--host", required=True)
    common.add_argument("--port", required=True, type=int)
    common.add_argument("--aet", required=True, help="PACS server AE title")
    common.add_argument("--calling", default="MAMOGRAF_SCU")
    common.add_argument("--timeout", type=int, default=60)

    s = sub.add_parser("send", parents=[common], help="DICOM faylni PACS'ga yuborish (C-STORE)")
    s.add_argument("files", nargs="+", help="fayl yoki papka yo'llari")
    s.set_defaults(func=lambda a: print(store(a.host, a.port, a.aet, _parse_files(a),
                                              a.calling, a.timeout)))

    q = sub.add_parser("query", parents=[common], help="qidirish (C-FIND)")
    q.add_argument("--patient-id", default="")
    q.add_argument("--patient-name", default="")
    q.add_argument("--modality", default="")
    q.add_argument("--study-date", default="")
    def _q(a):
        results = query(a.host, a.port, a.aet,
                        a.patient_id, a.patient_name,
                        a.modality, a.study_date,
                        a.calling, a.timeout)
        print(f"[pacs] {len(results)} ta study topildi")
        for r in results[:30]:
            print(f"  {r['patient_id']:<10} {r['patient_name']:<25} {r['study_date']:<10} {r['modalities']:<10} {r['study_uid']}")
        if len(results) > 30:
            print(f"  ... va yana {len(results)-30}")
    q.set_defaults(func=_q)

    f = sub.add_parser("fetch", parents=[common], help="study yoki study'larni olish (C-MOVE)")
    f.add_argument("--study-uid", required=True)
    f.add_argument("--dest", required=True)
    f.add_argument("--scp-port", type=int, default=11112)
    f.set_defaults(func=lambda a: print(fetch(a.host, a.port, a.aet, a.study_uid,
                                              Path(a.dest), a.calling, a.scp_port, a.timeout)))

    args = ap.parse_args()
    try:
        args.func(args)
    except RuntimeError as e:
        print(f"[xato] {e}", file=sys.stderr); sys.exit(1)


if __name__ == "__main__":
    main()
