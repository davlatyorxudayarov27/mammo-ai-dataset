from __future__ import annotations

import argparse
import csv
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .db import get_conn, init_db


def _parse_date(s: Optional[str]) -> Optional[str]:
    if not s:
        return None
    s = s.strip()
    if not s:
        return None
    for fmt in ("%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def _parse_bool(s: Optional[str]) -> bool:
    if not s:
        return False
    return s.strip().upper() in ("TRUE", "1", "YES", "Y")


def import_worklist(path: Path, reset: bool = False) -> dict:
    init_db()
    if reset:
        with get_conn() as c:
            c.execute("DELETE FROM worklist")
            c.commit()

    t0 = time.perf_counter()
    inserted = 0
    skipped = 0
    now = datetime.now(timezone.utc).isoformat()

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows_to_insert = []
        for r_idx, row in enumerate(reader, start=2):
            pid = (row.get("ID") or "").strip()
            if not pid:
                skipped += 1
                continue
            rows_to_insert.append((
                pid,
                (row.get("Name(DICOM)") or "").strip() or None,
                (row.get("Sex") or "").strip() or None,
                _parse_date(row.get("DOB")),
                _parse_date(row.get("Study Date")),
                (row.get("Modality") or "").strip() or None,
                int(_parse_bool(row.get("File"))),
                int(_parse_bool(row.get("Report"))),
                (row.get("Report Status") or "").strip() or None,
                None,
                "normal",
                "pending",
                None,
                now,
                r_idx,
            ))

    with get_conn() as c:
        c.executemany(
            "INSERT OR REPLACE INTO worklist "
            "(patient_id, patient_name, sex, dob, study_date, modality, "
            "has_file, has_report, report_status, assigned_to, priority, "
            "status, notes, imported_at, source_row) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            rows_to_insert,
        )
        inserted = len(rows_to_insert)
        c.commit()

    return {
        "path": str(path),
        "inserted_or_replaced": inserted,
        "skipped_no_id": skipped,
        "elapsed_s": round(time.perf_counter() - t0, 2),
    }


def main():
    ap = argparse.ArgumentParser(description="Import Worklist CSV into worklist table")
    default_path = Path(__file__).resolve().parent.parent / ".." / "dicomfiles" / "Worklist_20260220_1236_test23.csv"
    ap.add_argument("path", nargs="?", default=str(default_path),
                    help="path to worklist CSV (default looks in dicomfiles/)")
    ap.add_argument("--reset", action="store_true",
                    help="drop existing worklist rows before import")
    args = ap.parse_args()
    p = Path(args.path)
    if not p.exists():
        print(f"not found: {p}", file=sys.stderr)
        sys.exit(1)
    result = import_worklist(p, reset=args.reset)
    width = max(len(k) for k in result)
    for k, v in result.items():
        print(f"  {k.ljust(width)} : {v}")


if __name__ == "__main__":
    main()
