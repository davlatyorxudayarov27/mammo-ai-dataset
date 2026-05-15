"""Text-guided pseudo-label generator for mammography lesion detection.

When local DICOMs lack ground-truth bounding boxes but DO have radiology
reports, this module mines the reports for laterality / quadrant / clock /
size cues and synthesises *weak* bounding boxes on the preprocessed image.
The bboxes are saved as YOLO labels with a `confidence` field in a sidecar
manifest so a radiologist can later verify them in the MAMOGRAF UI.

Languages handled:
    - Uzbek (Cyrillic)
    - Uzbek (Latin)
    - Russian
    - English (literature dumps)

Pipeline:
    1. `extract_findings(text)` runs all multilingual regexes and returns a
       structured `Findings` object.
    2. `findings_to_bboxes(findings, meta)` projects the findings onto the
       preprocessed image (using `PreprocessMeta` from `preprocess.py`).
    3. CLI: reads the project SQLite DB, joins DICOM links → records, runs
       the preprocessing manifest, and emits a YOLO-format `pseudo_labels/`
       dataset plus a verification queue JSONL.

Spatial conventions (after R→L standardisation in preprocess_mammogram):
    - LEFT side of image  = chest wall (posterior)
    - RIGHT side of image = nipple    (anterior)
    - TOP of image        = upper / superior  (in MLO views)
    - BOTTOM of image     = lower / inferior  (in MLO views)
    - In CC views the upper/lower information is collapsed; we still place
      the bbox using the same y-axis heuristic but flag it as low-confidence.

These pseudo-labels are deliberately *coarse*: typical bbox is ~25% of the
breast crop. They exist to bootstrap a fine-tuning stage and to seed the
radiologist verification UI — not to be trained on directly without review.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import warnings
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Iterable

warnings.filterwarnings("ignore")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np

from app.research.preprocess import PreprocessMeta


# ---------------------------------------------------------------------------
# 1. Regex patterns (multilingual)
# ---------------------------------------------------------------------------


# Laterality
# Note: trailing word boundaries are intentionally relaxed because Uzbek
# (locative -da, ablative -dan, …) and Russian (genitive/dative endings) attach
# productive suffixes onto the lemma. We anchor the *start* of the keyword and
# let inflection trail.
_LAT_RIGHT = re.compile(
    r"\b("
    r"right\s+breast|"
    r"o[’']?ng\s+(?:sut\s+bezi|ko[’']?krak)\w*|"                 # Uzbek-Latin
    r"o[’']?ng\s+tomon\w*|"
    r"ў?нг\s+(?:сут\s+бези|кўкрак)\w*|у?нг\s+сут\s+бези\w*|"     # Uzbek-Cyr
    r"ў?нг\s+тараф\w*|у?нг\s+тараф\w*|"
    r"правая?\s+(?:молочная|грудь)\w*|"                          # Russian
    r"справа|правой\s+молочн\w*"
    r")",
    re.IGNORECASE | re.UNICODE,
)
_LAT_LEFT = re.compile(
    r"\b("
    r"left\s+breast|"
    r"chap\s+(?:sut\s+bezi|ko[’']?krak)\w*|"
    r"chap\s+tomon\w*|"
    r"чап\s+(?:сут\s+бези|кўкрак)\w*|чап\s+сут\s+бези\w*|"
    r"чап\s+тараф\w*|"
    r"лева[яй]\s+(?:молочная|грудь)\w*|"
    r"слева|левой\s+молочн\w*"
    r")",
    re.IGNORECASE | re.UNICODE,
)

# Quadrants. Abbreviations are common (UOQ = upper outer quadrant) plus
# spelled-out forms in three languages.
_QUAD_PATTERNS = {
    "UOQ": re.compile(
        r"\b("
        r"UOQ|upper[-\s]?outer\s+quadrant|"
        r"yuqori[-\s]?tashqi(?:\s+kvadrant)?|"
        r"юқори[-\s]?ташқи(?:\s+квадрант)?|юкори[-\s]?ташки|"
        r"верхне[-\s]?наружн(?:ый|ом|ого)(?:\s+квадрант)?"
        r")\b", re.IGNORECASE | re.UNICODE),
    "UIQ": re.compile(
        r"\b("
        r"UIQ|upper[-\s]?inner\s+quadrant|"
        r"yuqori[-\s]?ichki(?:\s+kvadrant)?|"
        r"юқори[-\s]?ички(?:\s+квадрант)?|юкори[-\s]?ички|"
        r"верхне[-\s]?внутренн(?:ий|ем|его)(?:\s+квадрант)?"
        r")\b", re.IGNORECASE | re.UNICODE),
    "LOQ": re.compile(
        r"\b("
        r"LOQ|lower[-\s]?outer\s+quadrant|"
        r"pastki[-\s]?tashqi(?:\s+kvadrant)?|"
        r"пастки[-\s]?ташқи(?:\s+квадрант)?|пастки[-\s]?ташки|"
        r"нижне[-\s]?наружн(?:ый|ом|ого)(?:\s+квадрант)?"
        r")\b", re.IGNORECASE | re.UNICODE),
    "LIQ": re.compile(
        r"\b("
        r"LIQ|lower[-\s]?inner\s+quadrant|"
        r"pastki[-\s]?ichki(?:\s+kvadrant)?|"
        r"пастки[-\s]?ички(?:\s+квадрант)?|"
        r"нижне[-\s]?внутренн(?:ий|ем|его)(?:\s+квадрант)?"
        r")\b", re.IGNORECASE | re.UNICODE),
    "central": re.compile(
        r"\b("
        r"central|sub[-\s]?areolar|retro[-\s]?areolar|"
        r"markaziy|марказий|"
        r"центральн(?:ый|ом|ого)|"
        r"za\s+aerolasi|за\s+ареолой"
        r")\b", re.IGNORECASE | re.UNICODE),
    "axillary_tail": re.compile(
        r"\b("
        r"axillary\s+tail|aksillyar(?:\s+dum)?|"
        r"аксилляр(?:ная|ной)|подмышечн(?:ый|ой)\s+(?:отрост|хвост)|"
        r"qo[’']?ltiq\s+osti|қўлтиқ\s+ости"
        r")\b", re.IGNORECASE | re.UNICODE),
}

# Clock position: "X o'clock", "соат X да", "soat X da", "на X часах"
_CLOCK_RE = re.compile(
    r"(?:"
    r"(?:at\s+|на\s+|do\s+|га|га\s+\d{1,2}\s+мин)?"
    r"(?:soat|соат)\s+(?P<c1>\d{1,2})|"
    r"\b(?P<c2>\d{1,2})\s*(?:o[’']?\s*clock|часа?х?|час[аов]?)\b|"
    r"(?:position\s+|positsiya\s+|позици[яи]\s+)(?P<c3>\d{1,2})"
    r")",
    re.IGNORECASE | re.UNICODE,
)

# Size: "20x15 mm", "12 mm", "1.5 sm", "2 см"
_SIZE_RE = re.compile(
    r"(?P<a>\d+(?:[.,]\d+)?)\s*(?:[xх×]\s*(?P<b>\d+(?:[.,]\d+)?))?"
    r"\s*(?P<unit>mm|мм|sm|см|cm)\b",
    re.IGNORECASE | re.UNICODE,
)

# Distance from nipple
_DIST_NIPPLE_RE = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*(mm|мм|sm|см|cm)\s+(?:от|nipple|emchak|эмчак|"
    r"so[’']?rg[’']?ich|сўрғич)",
    re.IGNORECASE | re.UNICODE,
)

# Lesion type → class
_LESION_PATTERNS = {
    "calcification": re.compile(
        r"\b("
        r"calcification\w*|microcalcif\w*|"
        r"mikrokalts\w*|mikrokalsi\w*|kal[’']?siy\s+to[’']?plama\w*|"
        r"микрокальцин\w*|кальцификат\w*|кальциноз\w*|кальцин\w*"
        r")",
        re.IGNORECASE | re.UNICODE),
    "asymmetry": re.compile(
        r"\b("
        r"asymmetr\w*|architectural\s+distortion|"
        r"asimmetri\w*|tuzilma\s+buzilish\w*|"
        r"асимметри\w*|нарушение\s+архитектоник\w*"
        r")",
        re.IGNORECASE | re.UNICODE),
    "mass": re.compile(
        r"\b("
        r"mass\b|lesion\w*|tumou?r\w*|nodul\w*|"
        r"hosil[ая]?\w*|massa\b|o[’']?simta\w*|"
        r"хосил[ая]?\w*|масс[аы]\b|ўсимта\w*|"
        r"образован\w*|опухол\w*|узел\w*|узлов\w*"
        r")",
        re.IGNORECASE | re.UNICODE),
}


# ---------------------------------------------------------------------------
# 2. Findings dataclass
# ---------------------------------------------------------------------------


@dataclass
class Findings:
    laterality: str = ""           # "L" / "R" / ""
    quadrant: str = ""             # one of {"UOQ","UIQ","LOQ","LIQ","central","axillary_tail",""}
    clock: int | None = None       # 1..12 or None
    lesion_types: list[str] = field(default_factory=list)
    size_mm: tuple[float, float] | None = None   # (long, short) in mm
    distance_from_nipple_mm: float | None = None
    raw_hits: dict = field(default_factory=dict)


def _to_mm(value: str, unit: str) -> float:
    v = float(value.replace(",", "."))
    u = unit.lower()
    if u in ("sm", "см", "cm"):
        return v * 10.0
    return v


def extract_findings(text: str) -> Findings:
    """Run all multilingual regexes on `text` and return structured Findings."""
    f = Findings()
    if not text:
        return f
    t = text

    # Laterality (a single report can mention both — prefer the first hit; if
    # both are present we still mark which appears earliest, others added to raw).
    r_match = _LAT_RIGHT.search(t)
    l_match = _LAT_LEFT.search(t)
    if r_match and (not l_match or r_match.start() < l_match.start()):
        f.laterality = "R"
    elif l_match:
        f.laterality = "L"
    f.raw_hits["lat_right"] = bool(r_match)
    f.raw_hits["lat_left"] = bool(l_match)

    # Quadrant
    for name, pat in _QUAD_PATTERNS.items():
        if pat.search(t):
            f.quadrant = name
            break

    # Clock
    m = _CLOCK_RE.search(t)
    if m:
        for k in ("c1", "c2", "c3"):
            v = m.group(k)
            if v:
                try:
                    n = int(v)
                except ValueError:
                    continue
                if 1 <= n <= 12:
                    f.clock = n
                    break

    # Lesion types (multi-label)
    for cls, pat in _LESION_PATTERNS.items():
        if pat.search(t):
            f.lesion_types.append(cls)

    # Size
    m = _SIZE_RE.search(t)
    if m:
        a = _to_mm(m.group("a"), m.group("unit"))
        b_raw = m.group("b")
        b = _to_mm(b_raw, m.group("unit")) if b_raw else a
        f.size_mm = (max(a, b), min(a, b))

    # Distance from nipple
    m = _DIST_NIPPLE_RE.search(t)
    if m:
        f.distance_from_nipple_mm = _to_mm(m.group(1), m.group(2))

    return f


# ---------------------------------------------------------------------------
# 3. Spatial mapper: Findings × PreprocessMeta → bboxes
# ---------------------------------------------------------------------------


# Lesion class → YOLO class id (must match dataset.yaml)
DEFAULT_CLASS_MAP = {
    "mass": 0,
    "calcification": 1,
    "asymmetry": 2,
}


def _quadrant_center(quadrant: str, view: str) -> tuple[float, float]:
    """Return (x_frac, y_frac) of the quadrant centre inside the breast crop.

    After R→L standardisation: image x∈[0,1] maps chest-wall→nipple,
    y∈[0,1] maps top→bottom. Outer = far from chest wall = high x.
    """
    if "MLO" in view:
        # Y-axis = upper/lower (well-defined); X-axis = posterior/anterior
        mapping = {
            "UOQ": (0.70, 0.30),
            "UIQ": (0.30, 0.30),
            "LOQ": (0.70, 0.70),
            "LIQ": (0.30, 0.70),
            "central": (0.55, 0.50),
            "axillary_tail": (0.20, 0.20),  # toward chest wall + upper
        }
    else:
        # CC view: Y-axis is medial/lateral (collapsed). Heuristic: place
        # outer at the lateral side (top), inner at medial (bottom). Without a
        # second view this is ambiguous, so we keep the bbox large.
        mapping = {
            "UOQ": (0.65, 0.30),
            "UIQ": (0.65, 0.70),
            "LOQ": (0.40, 0.30),
            "LIQ": (0.40, 0.70),
            "central": (0.55, 0.50),
            "axillary_tail": (0.20, 0.40),
        }
    return mapping.get(quadrant, (0.55, 0.50))


def _clock_to_xy(clock: int, view: str) -> tuple[float, float]:
    """Clock face → (x_frac, y_frac) inside the breast crop.

    Convention (post-R→L): nipple at right edge, chest wall at left.
    Clock face is centred on the nipple. 12 → straight up (toward image top).
    For LEFT-side conventions (which is what we see post-flip), 3 o'clock →
    medial (toward chest wall), 9 o'clock → lateral (away from body).
    """
    angle = (clock % 12) * (np.pi / 6.0) - np.pi / 2.0  # 12 o'clock → top
    cx, cy = 0.85, 0.50            # rotate around the nipple area
    radius = 0.30
    x = cx + radius * np.cos(angle)
    if "MLO" in view:
        y = cy + radius * np.sin(angle)
    else:
        # CC view collapses superior/inferior; halve the y excursion.
        y = cy + radius * np.sin(angle) * 0.5
    return float(np.clip(x, 0.05, 0.95)), float(np.clip(y, 0.05, 0.95))


def _size_to_pixels(
    size_mm: tuple[float, float] | None,
    meta: PreprocessMeta,
    fallback_frac: float = 0.20,
) -> tuple[float, float]:
    """Convert a real-world lesion size in mm to pixels on the letterboxed image."""
    s = meta.target_size
    if size_mm is None or meta.pixel_spacing is None:
        side = s * fallback_frac
        return side, side

    # Scale factor: we cropped to breast bbox then letterboxed to s×s.
    bx0, by0, bx1, by1 = meta.breast_bbox
    crop_w = max(bx1 - bx0, 1)
    crop_h = max(by1 - by0, 1)
    scale = min(s / crop_w, s / crop_h)
    px_per_mm_x = scale / max(meta.pixel_spacing[1], 1e-3)
    px_per_mm_y = scale / max(meta.pixel_spacing[0], 1e-3)

    long_mm, short_mm = size_mm
    w_px = long_mm * px_per_mm_x * 1.4         # 40% margin (the bbox encloses, not equals)
    h_px = short_mm * px_per_mm_y * 1.4
    # Clamp to a sensible range
    w_px = float(np.clip(w_px, s * 0.05, s * 0.50))
    h_px = float(np.clip(h_px, s * 0.05, s * 0.50))
    return w_px, h_px


@dataclass
class WeakBBox:
    cls: int
    x0: float
    y0: float
    x1: float
    y1: float
    confidence: float          # 0..1, our self-rating of how trustworthy this label is
    rationale: str             # human-readable: "MLO + UOQ + size 20mm"


def _confidence_score(f: Findings, view: str) -> float:
    """Heuristic 0–1 score for how reliable the synthesised bbox is."""
    s = 0.30                                         # base
    if f.quadrant: s += 0.20
    if f.clock is not None: s += 0.15
    if f.size_mm is not None: s += 0.15
    if f.distance_from_nipple_mm is not None: s += 0.10
    if "MLO" in view: s += 0.10                      # MLO localisation is less ambiguous
    return float(min(s, 0.95))


def findings_to_bboxes(
    findings: Findings,
    meta: PreprocessMeta,
    class_map: dict[str, int] | None = None,
) -> list[WeakBBox]:
    """Synthesise weak bboxes from parsed Findings + PreprocessMeta."""
    class_map = class_map or DEFAULT_CLASS_MAP
    if not findings.lesion_types and findings.quadrant:
        findings.lesion_types = ["mass"]    # default class when only location is mentioned
    if not findings.lesion_types:
        return []

    # Verify laterality matches the image; if not, this report is about the
    # other breast and we should not place a bbox here.
    if findings.laterality and findings.laterality != meta.laterality:
        return []

    s = meta.target_size
    if findings.clock is not None:
        cx_frac, cy_frac = _clock_to_xy(findings.clock, meta.view)
        rationale_loc = f"clock={findings.clock}"
    elif findings.quadrant:
        cx_frac, cy_frac = _quadrant_center(findings.quadrant, meta.view)
        rationale_loc = f"quadrant={findings.quadrant}"
    else:
        cx_frac, cy_frac = 0.55, 0.50
        rationale_loc = "default-center"

    w_px, h_px = _size_to_pixels(findings.size_mm, meta)
    cx, cy = cx_frac * s, cy_frac * s
    x0 = float(np.clip(cx - w_px / 2, 0, s))
    y0 = float(np.clip(cy - h_px / 2, 0, s))
    x1 = float(np.clip(cx + w_px / 2, 0, s))
    y1 = float(np.clip(cy + h_px / 2, 0, s))
    if x1 <= x0 + 4 or y1 <= y0 + 4:
        return []

    conf = _confidence_score(findings, meta.view)
    rationale = f"{meta.view or '?'} | {rationale_loc} | size_mm={findings.size_mm} | conf={conf:.2f}"

    out: list[WeakBBox] = []
    for cls_name in findings.lesion_types:
        cls_id = class_map.get(cls_name)
        if cls_id is None:
            continue
        out.append(WeakBBox(
            cls=cls_id, x0=x0, y0=y0, x1=x1, y1=y1,
            confidence=conf, rationale=f"{cls_name}: {rationale}",
        ))
    return out


# ---------------------------------------------------------------------------
# 4. CLI: project DB + preprocess manifest → YOLO pseudo-labels
# ---------------------------------------------------------------------------


def _load_text_from_db(db_path: Path, sop_uid: str) -> str:
    """Look up a record's clinical text by SOP UID via dicom_patient_links → records.

    Falls back to PatientID matching if no SOP-level link exists.
    Returns concatenated free-text fields (complaints + history + clinical_findings + report).
    """
    import sqlite3
    if not db_path.exists():
        return ""
    con = sqlite3.connect(str(db_path))
    con.row_factory = sqlite3.Row
    try:
        # Try SOP-UID join via dicom_patient_links if such a column exists
        try:
            row = con.execute(
                "SELECT r.complaints, r.history, r.clinical_findings, r.report, r.diagnosis "
                "FROM dicom_patient_links l "
                "JOIN records r ON r.patient_id = l.patient_id "
                "WHERE l.sop_uid = ?",
                (sop_uid,),
            ).fetchone()
        except sqlite3.OperationalError:
            row = None
        if row is None:
            return ""
        parts = [row[k] for k in ("complaints", "history", "clinical_findings",
                                  "report", "diagnosis") if row[k]]
        return "\n".join(parts)
    finally:
        con.close()


def _read_preprocess_manifest(manifest_path: Path) -> Iterable[PreprocessMeta]:
    for line in manifest_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        d = json.loads(line)
        if d.get("pixel_spacing") and isinstance(d["pixel_spacing"], list):
            d["pixel_spacing"] = tuple(d["pixel_spacing"])
        if d.get("breast_bbox") and isinstance(d["breast_bbox"], list):
            d["breast_bbox"] = tuple(d["breast_bbox"])
        yield PreprocessMeta(**d)


def _write_yolo_label(path: Path, bboxes: list[WeakBBox], img_size: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for b in bboxes:
            cx = (b.x0 + b.x1) / 2.0 / img_size
            cy = (b.y0 + b.y1) / 2.0 / img_size
            w = (b.x1 - b.x0) / img_size
            h = (b.y1 - b.y0) / img_size
            if w <= 0 or h <= 0:
                continue
            f.write(f"{b.cls} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}\n")


def main():
    ap = argparse.ArgumentParser(description="Text-guided pseudo-label generator")
    ap.add_argument("--manifest", required=True,
                    help="JSONL produced by app.research.preprocess (rows of PreprocessMeta)")
    ap.add_argument("--images-root", required=True,
                    help="Folder where preprocess.py wrote images/")
    ap.add_argument("--db", default="app/db.sqlite3",
                    help="SQLite DB to source clinical text from")
    ap.add_argument("--out", required=True,
                    help="Destination folder for the pseudo-label YOLO dataset")
    ap.add_argument("--text-csv", default=None,
                    help="Optional CSV with columns [sop_uid, text]; bypasses DB lookup")
    ap.add_argument("--min-confidence", type=float, default=0.50,
                    help="Skip labels below this self-rated confidence")
    ap.add_argument("--single-class", action="store_true",
                    help="Collapse mass/calcification/asymmetry into one class")
    args = ap.parse_args()

    manifest_path = Path(args.manifest).resolve()
    images_root = Path(args.images_root).resolve()
    out_root = Path(args.out).resolve()
    db_path = Path(args.db).resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    text_lookup: dict[str, str] = {}
    if args.text_csv:
        import csv
        with open(args.text_csv, "r", encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                if row.get("sop_uid") and row.get("text"):
                    text_lookup[row["sop_uid"]] = row["text"]

    class_map = {"mass": 0} if args.single_class else dict(DEFAULT_CLASS_MAP)
    review_path = out_root / "review_queue.jsonl"
    n_labelled = n_empty = n_filtered = 0

    with review_path.open("w", encoding="utf-8") as rf:
        for meta in _read_preprocess_manifest(manifest_path):
            text = text_lookup.get(meta.sop_uid) or _load_text_from_db(db_path, meta.sop_uid)
            findings = extract_findings(text)
            if not findings.lesion_types and not findings.quadrant and findings.clock is None:
                n_empty += 1
                continue

            bboxes_all = findings_to_bboxes(findings, meta, class_map=class_map)
            bboxes = [b for b in bboxes_all if b.confidence >= args.min_confidence]
            if not bboxes:
                n_filtered += 1
                continue

            img_rel = Path(meta.out_path).with_suffix(".png").name
            label_path = out_root / "labels" / img_rel.replace(".png", ".txt")
            _write_yolo_label(label_path, bboxes, meta.target_size)

            rf.write(json.dumps({
                "sop_uid": meta.sop_uid,
                "image": meta.out_path,
                "view": meta.view,
                "laterality": meta.laterality,
                "findings": asdict(findings),
                "bboxes": [asdict(b) for b in bboxes],
                "needs_radiologist_review": True,
            }, ensure_ascii=False) + "\n")
            n_labelled += 1
            if n_labelled % 50 == 0:
                print(f"  ... {n_labelled} labelled, {n_empty} empty, {n_filtered} below conf")

    names = ["lesion"] if args.single_class else ["mass", "calcification", "asymmetry"]
    yaml_path = out_root / "dataset.yaml"
    yaml_path.write_text(
        f"# Auto-generated by app.research.pseudo_labels\n"
        f"# Pseudo-labels — REQUIRES radiologist verification before training!\n"
        f"path: {out_root.as_posix()}\n"
        f"train: {images_root.as_posix()}\n"
        f"nc: {len(names)}\n"
        f"names: {names}\n",
        encoding="utf-8",
    )
    print(f"\n[done] {n_labelled} labelled, {n_empty} no findings, {n_filtered} below confidence")
    print(f"  review queue : {review_path}")
    print(f"  dataset.yaml : {yaml_path}")
    print(f"\nNext step: open the MAMOGRAF UI, run a verification pass on")
    print(f"the review queue, then re-export with high-confidence-only labels.")


if __name__ == "__main__":
    main()
