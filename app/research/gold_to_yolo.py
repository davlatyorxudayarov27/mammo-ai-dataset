"""Convert radiologist-verified gold labels (review_decisions table) into a
Ultralytics-compatible YOLO dataset, ready for the TILLNet-Det Stage-3
fine-tune.

Source of truth is the project SQLite DB: rows with `status IN ('accepted',
'edited')` are exported. For each row:

    1. The preprocessed PNG (as referenced by `preprocessed_png_path`) is
       symlinked / copied into <out>/images/<split>/<base>.png.
    2. `final_bboxes_json` (pixel coords on the preprocessed canvas, same
       coordinate system as `pseudo_labels.py` produced) is converted to
       YOLO format and written to <out>/labels/<split>/<base>.txt.
    3. A patient-level train/val split is computed from the SOP UID prefix
       (study UID prefix) so two views of the same study cannot leak across
       splits.

The resulting `dataset.yaml` is plug-compatible with both
`app.research.train_detector` (YOLOv8) and `app.research.train_tillnet`.

Usage:
    python -m app.research.gold_to_yolo \\
        --out /path/to/yolo_gold \\
        --target-size 1024 \\
        --val-frac 0.15 \\
        --include accepted,edited

Or pass a pre-exported JSONL bundle (from the /api/research/review/export
endpoint) instead of reading the DB directly:

    python -m app.research.gold_to_yolo \\
        --jsonl gold_labels_2026-05-07.jsonl \\
        --out /path/to/yolo_gold
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import shutil
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.db import get_conn, init_db


# Default 3-class layout matches pseudo_labels.DEFAULT_CLASS_MAP.
CLASS_NAMES = ["mass", "calcification", "asymmetry"]


# ---------------------------------------------------------------------------
# Sources: DB rows or pre-exported JSONL
# ---------------------------------------------------------------------------


def _rows_from_db(include: list[str]):
    init_db()
    placeholders = ",".join("?" * len(include))
    with get_conn() as c:
        return [dict(r) for r in c.execute(
            f"SELECT sop_uid, dicom_path, preprocessed_png_path, view, laterality, "
            f"       final_bboxes_json, status, reviewer "
            f"FROM review_decisions WHERE status IN ({placeholders})",
            include,
        ).fetchall()]


def _rows_from_jsonl(path: Path):
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        rows.append({
            "sop_uid": d.get("sop_uid", ""),
            "dicom_path": d.get("dicom_path", ""),
            "preprocessed_png_path": d.get("preprocessed_png", ""),
            "view": d.get("view", ""),
            "laterality": d.get("laterality", ""),
            "final_bboxes_json": json.dumps(d.get("bboxes", [])),
            "status": d.get("status", ""),
            "reviewer": d.get("reviewer", ""),
        })
    return rows


# ---------------------------------------------------------------------------
# YOLO label writer (final_bboxes are pixel coords on a target_size canvas)
# ---------------------------------------------------------------------------


def _bbox_to_yolo(bbox: dict, target_size: int) -> str | None:
    try:
        x0 = float(bbox["x0"]); y0 = float(bbox["y0"])
        x1 = float(bbox["x1"]); y1 = float(bbox["y1"])
        cls = int(bbox.get("cls", 0))
    except (KeyError, TypeError, ValueError):
        return None
    if x1 <= x0 or y1 <= y0:
        return None
    cx = (x0 + x1) / 2.0 / target_size
    cy = (y0 + y1) / 2.0 / target_size
    w = (x1 - x0) / target_size
    h = (y1 - y0) / target_size
    cx = max(0.0, min(1.0, cx)); cy = max(0.0, min(1.0, cy))
    w  = max(0.0, min(1.0, w));  h  = max(0.0, min(1.0, h))
    if w <= 0 or h <= 0:
        return None
    return f"{cls} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}"


def _write_label(path: Path, bboxes: list[dict], target_size: int) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with path.open("w", encoding="utf-8") as f:
        for b in bboxes:
            line = _bbox_to_yolo(b, target_size)
            if line:
                f.write(line + "\n"); n += 1
    return n


# ---------------------------------------------------------------------------
# Patient-level split — keys on the SOP UID's study root so two views of the
# same study stay together.
# ---------------------------------------------------------------------------


def _study_key(sop_uid: str) -> str:
    """Use the SOP UID without its final dotted segment (instance suffix) as
    a study-level grouping key. If nothing parses, fall back to the full UID.
    """
    if not sop_uid:
        return ""
    parts = sop_uid.rsplit(".", 1)
    return parts[0] if len(parts) == 2 else sop_uid


def _assign_split(study_keys: list[str], val_frac: float, seed: int) -> dict[str, str]:
    rng = random.Random(seed)
    keys = sorted(set(study_keys))
    rng.shuffle(keys)
    n_val = max(1, int(round(len(keys) * val_frac))) if keys else 0
    val_set = set(keys[:n_val])
    return {k: ("val" if k in val_set else "train") for k in keys}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def _safe_basename(row: dict) -> str:
    """Stable, filesystem-safe filename derived from SOP UID (full UIDs can
    exceed Windows path limits, so we hash long ones)."""
    sop = row.get("sop_uid") or ""
    if not sop:
        return hashlib.sha1((row.get("preprocessed_png_path") or "").encode()).hexdigest()[:16]
    safe = sop.replace(".", "_")
    if len(safe) <= 80:
        return safe
    return safe[:40] + "_" + hashlib.sha1(sop.encode()).hexdigest()[:16]


def main():
    ap = argparse.ArgumentParser(description="Gold-label → YOLO dataset converter")
    ap.add_argument("--out", required=True, help="Destination YOLO dataset folder")
    ap.add_argument("--include", default="accepted,edited",
                    help="Comma-separated review statuses to include")
    ap.add_argument("--target-size", type=int, default=1024,
                    help="Image size assumed for bbox normalisation (must match preprocess)")
    ap.add_argument("--val-frac", type=float, default=0.15)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--copy", action="store_true",
                    help="Copy PNGs (default: try symlink, fall back to copy on Windows)")
    ap.add_argument("--single-class", action="store_true",
                    help="Collapse all classes into one 'lesion' class")
    ap.add_argument("--jsonl", default=None,
                    help="Pre-exported JSONL (from /api/research/review/export); skips DB read")
    args = ap.parse_args()

    out_root = Path(args.out).resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    include = [s.strip() for s in args.include.split(",") if s.strip()]
    if args.jsonl:
        rows = _rows_from_jsonl(Path(args.jsonl))
        print(f"[load] {len(rows)} rows from {args.jsonl}")
    else:
        rows = _rows_from_db(include)
        print(f"[load] {len(rows)} rows from DB (status in {include})")

    if not rows:
        raise SystemExit("no gold-label rows found — did the radiologist review anything?")

    # Plan train/val split first.
    study_keys = [_study_key(r["sop_uid"]) for r in rows]
    split_map = _assign_split(study_keys, args.val_frac, args.seed)

    n_ok = n_skip_no_png = n_skip_no_bbox = n_train = n_val = 0
    for r in rows:
        png_src = (r.get("preprocessed_png_path") or "").strip()
        if not png_src or not Path(png_src).exists():
            n_skip_no_png += 1
            continue
        try:
            bboxes = json.loads(r.get("final_bboxes_json") or "[]")
        except json.JSONDecodeError:
            bboxes = []
        if not bboxes:
            n_skip_no_bbox += 1
            continue

        if args.single_class:
            for b in bboxes:
                b["cls"] = 0

        split = split_map.get(_study_key(r["sop_uid"]), "train")
        base = _safe_basename(r)
        img_dst = out_root / "images" / split / f"{base}.png"
        lbl_dst = out_root / "labels" / split / f"{base}.txt"
        img_dst.parent.mkdir(parents=True, exist_ok=True)

        # Try symlink first (fast, no duplication); fall back to copy.
        if not img_dst.exists():
            try:
                if args.copy:
                    raise OSError("copy mode forced")
                img_dst.symlink_to(Path(png_src).resolve())
            except (OSError, NotImplementedError):
                shutil.copy2(png_src, img_dst)

        n_written = _write_label(lbl_dst, bboxes, args.target_size)
        if n_written == 0:
            n_skip_no_bbox += 1
            img_dst.unlink(missing_ok=True)
            continue
        n_ok += 1
        if split == "train":
            n_train += 1
        else:
            n_val += 1

    names = ["lesion"] if args.single_class else CLASS_NAMES
    yaml_path = out_root / "dataset.yaml"
    yaml_path.write_text(
        f"# Auto-generated by app.research.gold_to_yolo\n"
        f"# Source: review_decisions table (statuses={include})\n"
        f"path: {out_root.as_posix()}\n"
        f"train: images/train\n"
        f"val: images/val\n"
        f"test: images/val\n"
        f"nc: {len(names)}\n"
        f"names: {names}\n",
        encoding="utf-8",
    )

    print(f"\n[done] wrote {n_ok} samples  (train={n_train}, val={n_val})")
    if n_skip_no_png:
        print(f"  skipped {n_skip_no_png} — preprocessed PNG missing")
    if n_skip_no_bbox:
        print(f"  skipped {n_skip_no_bbox} — no usable bboxes after conversion")
    print(f"  dataset.yaml → {yaml_path}")


if __name__ == "__main__":
    main()
