"""Explore real labels in the SQLite DB to design the classification task."""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.db import get_conn

CANCER_PATTERNS = [
    r"\bC\s*50\b", r"С\s*50",
    r"\bsarat[oa]n", r"\bсарат[оа]н",
    r"\bрак\b", r"\braka?\b",
    r"саратон", r"saraton",
    r"karsinom", r"карцином",
    r"malign", r"малигн",
    r"\bM\s*8500/3\b",
]
CANCER_RE = re.compile("|".join(CANCER_PATTERNS), re.IGNORECASE | re.UNICODE)


def detect_cancer(text: str) -> bool:
    if not text:
        return False
    return bool(CANCER_RE.search(text))


def script_ratio(text: str) -> dict:
    """Cyrillic vs Latin character ratio."""
    if not text:
        return {"cyrillic": 0, "latin": 0, "other": 0}
    cyr = sum(1 for c in text if "Ѐ" <= c <= "ӿ")
    lat = sum(1 for c in text if c.isalpha() and ord(c) < 128)
    other = sum(1 for c in text if c.isalpha()) - cyr - lat
    total = max(1, cyr + lat + other)
    return {"cyrillic": cyr / total, "latin": lat / total, "other": other / total}


def main():
    with get_conn() as c:
        rows = c.execute("""
            SELECT id, diagnosis, complaints, history, clinical_findings,
                   recommendations, report
            FROM records
        """).fetchall()
    rows = [dict(r) for r in rows]
    print(f"Total records: {len(rows)}")

    has_dx = [r for r in rows if r.get("diagnosis")]
    print(f"Records with non-null diagnosis: {len(has_dx)}")
    cancer_rows = [r for r in rows if detect_cancer(r.get("diagnosis") or "")]
    print(f"Records with cancer in diagnosis: {len(cancer_rows)} ({len(cancer_rows)/len(rows)*100:.1f}%)")

    input_rows = [r for r in rows
                  if (r.get("complaints") or r.get("history") or r.get("clinical_findings"))]
    print(f"Records with at least one input field: {len(input_rows)}")

    usable = []
    for r in rows:
        inp = " ".join(filter(None, [
            r.get("complaints") or "", r.get("history") or "",
            r.get("clinical_findings") or "",
        ]))
        if not inp.strip():
            continue
        dx = r.get("diagnosis") or ""
        rep = r.get("report") or ""
        is_cancer = detect_cancer(dx) or detect_cancer(rep)
        usable.append({"id": r["id"], "text": inp, "dx": dx, "is_cancer": is_cancer})

    print(f"\nUsable for ML (has input text): {len(usable)}")
    n_pos = sum(1 for r in usable if r["is_cancer"])
    print(f"  positive (cancer): {n_pos} ({n_pos/len(usable)*100:.1f}%)")
    print(f"  negative: {len(usable)-n_pos} ({(len(usable)-n_pos)/len(usable)*100:.1f}%)")

    # Script distribution
    print("\nScript distribution (first 200 usable):")
    cyr_pure = lat_pure = mixed = 0
    for r in usable[:200]:
        sr = script_ratio(r["text"])
        if sr["cyrillic"] > 0.7:
            cyr_pure += 1
        elif sr["latin"] > 0.7:
            lat_pure += 1
        else:
            mixed += 1
    print(f"  Cyrillic-dominant: {cyr_pure}")
    print(f"  Latin-dominant:    {lat_pure}")
    print(f"  Mixed/other:       {mixed}")

    # Sample positives and negatives
    print("\nSample POSITIVE (cancer):")
    for r in [r for r in usable if r["is_cancer"]][:2]:
        print(f"  id={r['id']}  text[:200]={r['text'][:200]!r}")
        print(f"            dx={r['dx'][:100]!r}")
    print("\nSample NEGATIVE:")
    for r in [r for r in usable if not r["is_cancer"]][:2]:
        print(f"  id={r['id']}  text[:200]={r['text'][:200]!r}")
        print(f"            dx={r['dx'][:80]!r}")


if __name__ == "__main__":
    main()
