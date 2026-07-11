"""Training dataset tayyorlash sinovi."""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import main as M
from app.main import TrainingPrepareBody, training_prepare


# Maqsad: vaqtinchalik papka
dest = Path(tempfile.gettempdir()) / "mamograf_test_yolo"
if dest.exists():
    shutil.rmtree(dest)

# Mavjud annotation'lar uchun ma'lumot ko'rish
ann_files = list(M.ANNOT_DIR.glob("upload__*.json"))
print(f"Annotation fayllari: {len(ann_files)}")
for ap in ann_files[:5]:
    try:
        data = json.loads(ap.read_text(encoding="utf-8"))
        ans = data.get("annotations") or []
        labels = {a.get("label") for a in ans if a.get("label")}
        print(f"  - {ap.name}: {len(ans)} annotation, labels={sorted(labels)}")
    except Exception as e:
        print(f"  - {ap.name}: xato {e}")

print(f"\nMaqsad: {dest}\n")

# Run with sensible defaults
body = TrainingPrepareBody(
    destination=str(dest),
    target_size=1024,
    val_frac=0.15,
    include_ai=True,   # haqiqiy ma'lumotda qo'lda annotation kam, AI'sini qabul qilamiz
    image_format="png",
    seed=42,
    zip_after=False,
)

res = training_prepare(body, _user={"sub": "admin"})

print("=== Natija ===")
for k, v in res.items():
    if k not in ("classes",):
        print(f"  {k}: {v}")
print(f"  klasslar: {res['classes']}")

# Tasdiqlash
data_yaml = Path(res["data_yaml"])
assert data_yaml.exists(), "data.yaml mavjud emas"
print(f"\n=== data.yaml ===")
print(data_yaml.read_text(encoding="utf-8"))

train_imgs = list((dest / "images" / "train").glob("*"))
val_imgs = list((dest / "images" / "val").glob("*"))
train_lbls = list((dest / "labels" / "train").glob("*"))
val_lbls = list((dest / "labels" / "val").glob("*"))

print(f"=== Fayllar ===")
print(f"  train/images: {len(train_imgs)}")
print(f"  train/labels: {len(train_lbls)}")
print(f"  val/images: {len(val_imgs)}")
print(f"  val/labels: {len(val_lbls)}")

# Bir label faylini ko'rib chiqamiz
if train_lbls:
    sample = train_lbls[0]
    print(f"\n=== Namuna label fayli ({sample.name}) ===")
    print(sample.read_text(encoding="utf-8")[:500])

assert (res["train_imgs"] + res["val_imgs"]) >= 1, "Kamida 1 ta tasvir bo'lishi kerak"
assert (dest / "README_TRAIN.md").exists(), "README yo'q"

# Tozalash
shutil.rmtree(dest, ignore_errors=True)
print("\n✓ Test o'tdi")
