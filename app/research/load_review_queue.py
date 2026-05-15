"""Load a `review_queue.jsonl` (produced by app.research.pseudo_labels) into
the project SQLite DB so radiologists can verify the pseudo-bboxes through
the MAMOGRAF UI.

Each JSONL line becomes one row in `review_decisions` with status='pending'.
Re-running with the same source-queue is idempotent — existing rows
(matched by `(sop_uid, source_queue)`) are skipped, not duplicated.

Usage:
    python -m app.research.load_review_queue \\
        --queue       runs/full/local_pseudo/review_queue.jsonl \\
        --preproc-out runs/full/local_preprocessed
"""
from __future__ import annotations

import argparse
import json
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path

warnings.filterwarnings("ignore")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import sqlite3

# Touch the project's init_db so the table exists if this is the first call.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from app.db import get_conn, init_db


def _read_jsonl(path: Path):
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            continue


def _resolve_dicom_path(sop_uid: str, manifest_path: Path | None) -> str | None:
    """Look up the source DICOM path from the preprocess manifest by sop_uid."""
    if manifest_path is None or not manifest_path.exists():
        return None
    for d in _read_jsonl(manifest_path):
        if d.get("sop_uid") == sop_uid:
            return d.get("src_path")
    return None


def main():
    ap = argparse.ArgumentParser(description="Ingest review_queue.jsonl into review_decisions")
    ap.add_argument("--queue", required=True, help="Path to review_queue.jsonl")
    ap.add_argument("--preproc-out", default=None,
                    help="Path to preprocessing output dir (used to resolve PNG + DICOM paths)")
    ap.add_argument("--source-tag", default=None,
                    help="Identifier for this queue (default: queue file basename)")
    args = ap.parse_args()

    queue_path = Path(args.queue).resolve()
    if not queue_path.exists():
        raise SystemExit(f"queue file not found: {queue_path}")

    preproc_out = Path(args.preproc_out).resolve() if args.preproc_out else None
    manifest_path = (preproc_out / "manifest.jsonl") if preproc_out else None
    source_tag = args.source_tag or queue_path.name

    init_db()
    now = datetime.now(timezone.utc).isoformat()
    n_inserted = n_skipped = n_failed = 0

    with get_conn() as c:
        for entry in _read_jsonl(queue_path):
            sop_uid = entry.get("sop_uid") or ""
            if not sop_uid:
                n_failed += 1
                continue

            png_rel = entry.get("image") or ""
            png_abs = ""
            if preproc_out and png_rel:
                cand = (preproc_out / png_rel).resolve()
                if cand.exists():
                    png_abs = str(cand)

            dicom_path = _resolve_dicom_path(sop_uid, manifest_path) or ""

            try:
                c.execute(
                    "INSERT INTO review_decisions ("
                    "  sop_uid, dicom_path, preprocessed_png_path, view, laterality,"
                    "  findings_json, pseudo_bboxes_json, status, imported_at, source_queue"
                    ") VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)",
                    (
                        sop_uid,
                        dicom_path,
                        png_abs,
                        entry.get("view", "") or "",
                        entry.get("laterality", "") or "",
                        json.dumps(entry.get("findings") or {}, ensure_ascii=False),
                        json.dumps(entry.get("bboxes") or [], ensure_ascii=False),
                        now,
                        source_tag,
                    ),
                )
                n_inserted += 1
            except sqlite3.IntegrityError:
                n_skipped += 1
        c.commit()

    print(f"[done] inserted={n_inserted}  skipped(existing)={n_skipped}  failed={n_failed}")
    print(f"[source_queue] = {source_tag!r}")
    print(f"[next] open MAMOGRAF UI → 🔬 Review modal to verify each item")


if __name__ == "__main__":
    main()
