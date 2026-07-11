"""A/B test — A1 funksiyasi (avtomatik AI inference upload paytida).

Eski xulq (AUTO_INFER_ON_UPLOAD=0) va yangi xulqni (AUTO_INFER_ON_UPLOAD=1)
bitta haqiqiy DICOM bilan solishtiradi.

Ishlatish:
    .venv\\Scripts\\python -m scripts.test_auto_infer
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import time
import uuid
from pathlib import Path

# Bash/console UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Proyekt yo'lini qo'shish
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# DICOM faylini topish
CANDIDATES = [
    ROOT / "app" / "uploads" / "9b2443dd03704b37ba851a3b9160ad9d.dcm",
    ROOT / "app" / "uploads" / "b88d122ad4f8452cbad37f3994e392ad.dcm",
    ROOT / "app" / "uploads" / "bf3ffbe47af6417db27aee352c78b4bb.dcm",
]
SRC = next((p for p in CANDIDATES if p.exists()), None)
if SRC is None:
    print("Test DICOM topilmadi"); sys.exit(1)


def run_one(mode: str, call_auto: bool) -> dict:
    """Bitta upload-like oqimni simulyatsiya qiladi va natijani qaytaradi."""
    from app import main as M
    import pydicom

    print(f"\n=== Rejim: {mode} ===")
    print(f"  call_auto = {call_auto}")

    file_id = "test_" + mode + "_" + uuid.uuid4().hex[:8]
    out = M.UPLOAD_DIR / f"{file_id}.dcm"
    shutil.copy(SRC, out)

    ds = pydicom.dcmread(str(out), stop_before_pixels=True, force=True)
    rows = int(getattr(ds, "Rows", 0) or 0)
    cols = int(getattr(ds, "Columns", 0) or 0)

    result = {
        "mode": mode,
        "file_id": file_id,
        "annotation_count": 0,
        "ai_inference": None,
        "duration_s": 0.0,
        "annot_file_exists": False,
    }

    t0 = time.time()
    if call_auto and rows and cols:
        ai_info = M._auto_infer_uploaded(file_id, out, rows, cols)
        result["ai_inference"] = ai_info
        result["annotation_count"] = ai_info.get("detections", 0) if ai_info.get("ran") else 0
    result["duration_s"] = round(time.time() - t0, 2)

    # Annotation fayl yaratildimi?
    annot_path = M.ANNOT_DIR / f"upload__{file_id}.json"
    result["annot_file_exists"] = annot_path.exists()
    if annot_path.exists():
        data = json.loads(annot_path.read_text(encoding="utf-8"))
        result["annotations"] = data.get("annotations", [])
    else:
        result["annotations"] = []

    # Tozalash
    out.unlink(missing_ok=True)
    if annot_path.exists():
        annot_path.unlink()

    return result


def main():
    print("A/B TEST — Avtomatik AI inference upload paytida (A1)")
    print(f"Test fayl: {SRC.name}  ({SRC.stat().st_size/1e6:.1f} MB)")

    # Eski xulq: helper umuman chaqirilmaydi
    old = run_one("OLD", call_auto=False)

    # Yangi xulq: helper to'g'ridan-to'g'ri chaqiriladi
    new = run_one("NEW", call_auto=True)

    # Solishtirish
    print("\n" + "=" * 60)
    print("SOLISHTIRISH")
    print("=" * 60)
    rows = [
        ("Annotation yaratildimi (annot fayl)?", old["annot_file_exists"], new["annot_file_exists"]),
        ("Detections soni", old["annotation_count"], new["annotation_count"]),
        ("Davomiyligi (sek)", old["duration_s"], new["duration_s"]),
        ("AI inference info", old["ai_inference"], new["ai_inference"]),
    ]
    print(f"  {'Korsatkich':<40} {'ESKI':<25} {'YANGI':<25}")
    print(f"  {'-' * 40} {'-' * 25} {'-' * 25}")
    for label, ov, nv in rows:
        print(f"  {label:<40} {str(ov):<25} {str(nv):<25}")

    print("\n=== YANGI rejim: yaratilgan annotation'lar (zone bilan) ===")
    for i, a in enumerate(new["annotations"][:10]):
        z = a.get('zone', '-')
        zone_icon = {'auto_accept': '🟢', 'review': '🟡', 'suspect': '🔴'}.get(z, '⚪')
        print(f"  [{i}] {zone_icon} zone={z:11} conf={a.get('confidence'):.3f} status={a.get('status'):12} label={a.get('label')!r}")
    if len(new["annotations"]) > 10:
        print(f"  ... yana {len(new['annotations']) - 10} ta")

    # A2: 3-zonali klassifikatsiya integratsiyasi
    from app import main as M
    print("\n=== A2 — Klassifikatsiya funksiyasi sinovi ===")
    for c in [0.95, 0.85, 0.70, 0.40, 0.30, 0.20, 0.15]:
        z, s = M._classify_confidence_zone(c)
        zone_icon = {'auto_accept': '🟢', 'review': '🟡', 'suspect': '🔴', 'drop': '⚫'}.get(z, '⚪')
        print(f"  conf={c:.2f}  ->  {zone_icon} zone={z:12}  status={s!r}")
    print(f"\n  Chegaralar: accept≥{M.AUTO_INFER_ACCEPT_THR}  review≥{M.AUTO_INFER_REVIEW_THR}  suspect≥{M.AUTO_INFER_SUSPECT_THR}")

    if new.get("ai_inference") and new["ai_inference"].get("zones"):
        print(f"\n  Zonalar bo'yicha taqsimot (haqiqiy fayl): {new['ai_inference']['zones']}")

    # Xulosa
    print("\n=== XULOSA ===")
    if not new["ai_inference"]:
        print("  XATO: YANGI rejimda AI ishlamadi")
        sys.exit(1)
    if new["ai_inference"].get("error"):
        print(f"  YANGI rejimda xato: {new['ai_inference']['error']}")
        sys.exit(1)
    print(f"  ESKI rejim: annotation yaratilmadi ({old['annotation_count']} ta)")
    print(f"  YANGI rejim: {new['annotation_count']} ta pseudo-bbox avto-yaratildi")
    print(f"  Qo'shimcha vaqt: {new['duration_s']:.1f}s")
    print(f"  Model: {new['ai_inference'].get('model')}")
    print("  OK")


if __name__ == "__main__":
    main()
