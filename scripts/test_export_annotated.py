"""Export annotated test — annotation bor fayllarni boshqa papkaga ko'chirish."""
from __future__ import annotations

import json
import sys
import shutil
import tempfile
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import main as M
from app.main import ExportAnnotatedBody, export_annotated


# 1. Test DICOM mavjudligi va annotation tayyorlash
CAND = [p for p in M.UPLOAD_DIR.glob("*.dcm")][:2]
if len(CAND) < 1:
    print("Hech qanday upload yo'q"); sys.exit(0)

# Bir fayl uchun annotation yaratamiz (test uchun)
test_file = CAND[0]
test_id = test_file.stem
ann_path = M.ANNOT_DIR / f"upload__{test_id}.json"
ann_existing = ann_path.exists()
if not ann_existing:
    payload = {
        "source": "upload", "ref": test_id, "rows": 5928, "cols": 4728,
        "annotations": [{
            "id": "test1", "type": "bbox", "label": "mass",
            "bbox": [0.5, 0.5, 0.1, 0.1], "frame": 0,
            "created_by": "admin", "status": "submitted",
            "created_at": "2026-06-13T00:00:00Z",
        }],
    }
    ann_path.write_text(json.dumps(payload), encoding="utf-8")
    print(f"Test annotation yaratildi: {ann_path.name}")

# 2. Vaqtinchalik destination
dest = Path(tempfile.gettempdir()) / "mamograf_test_export"
if dest.exists():
    shutil.rmtree(dest)
print(f"Test maqsad: {dest}\n")


# 3. Test 1: require_annotations=True, flat
print("=== TEST 1: require_annotations=True, flat ===")
body = ExportAnnotatedBody(
    destination=str(dest),
    source_kind="upload",
    require_annotations=True,
    organize_by="flat",
    include_annotation_json=True,
)
res = export_annotated(body, _user={"sub": "admin"})
print(f"  copied: {res['copied_count']}, skipped: {res['skipped_count']}, no_ann: {res['no_annotations_count']}")
for c in res["copied"][:3]:
    print(f"  - {c['id']} -> {c['annotations']} ann, json={c['annotation_json']}")
assert res["copied_count"] >= 1, "Kamida 1 ta fayl ko'chirilishi kerak"
assert dest.is_dir(), "Maqsad papka mavjud bo'lishi kerak"
copied_files = list(dest.glob("*.dcm"))
assert len(copied_files) >= 1, "Maqsad papkada .dcm bo'lishi kerak"
copied_jsons = list(dest.glob("*.json"))
assert len(copied_jsons) >= 1, "Annotation JSON ham ko'chirilishi kerak"
print(f"  ✓ Test 1: {len(copied_files)} .dcm + {len(copied_jsons)} .json mavjud\n")

# 4. Test 2: organize_by="by_status"
shutil.rmtree(dest); dest.mkdir()
print("=== TEST 2: organize_by=by_status ===")
body.organize_by = "by_status"
body.overwrite = True
res = export_annotated(body, _user={"sub": "admin"})
print(f"  copied: {res['copied_count']}")
subdirs = [p for p in dest.iterdir() if p.is_dir()]
print(f"  subdirs: {[s.name for s in subdirs]}")
assert any(s.name == "submitted" for s in subdirs), "submitted/ papkasi bo'lishi kerak"
print(f"  ✓ Test 2: status bo'yicha papka yaratildi\n")

# 5. Test 3: Xavfsizlik — taqiqlangan papka
print("=== TEST 3: taqiqlangan papka rad etiladi ===")
try:
    body_bad = ExportAnnotatedBody(destination=r"C:\Windows\test", source_kind="upload")
    res = export_annotated(body_bad, _user={"sub": "admin"})
    print("  ✗ Xato: taqiqlangan papka qabul qilindi!")
    sys.exit(1)
except Exception as e:
    msg = str(e)
    if "taqiqlangan" in msg.lower() or "400" in msg:
        print(f"  ✓ Taqiqlangan papka rad etildi: {msg[:60]}")
    else:
        raise

# Tozalash
if not ann_existing:
    ann_path.unlink(missing_ok=True)
shutil.rmtree(dest, ignore_errors=True)
print("\nBARCHA TESTLAR O'TDI ✓")
