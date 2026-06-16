"""A3 sinovi — Uncertainty heatmap (modellar kelishmaslik xaritasi).

Bir nechta YOLO modelini bir DICOM ustida ishga tushirib, noaniqlik xaritasini
yaratadi va hisobot beradi (jami detection'lar, har modeldagi, heatmap statistikasi).

Ishlatish:
    .venv\\Scripts\\python -m scripts.test_uncertainty
"""
from __future__ import annotations

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import main as M
from app import inference as inf
from app.dicom_utils import render_frame_png

# Test fayllar
CAND = [
    ROOT / "app" / "uploads" / "9b2443dd03704b37ba851a3b9160ad9d.dcm",
    ROOT / "app" / "uploads" / "b88d122ad4f8452cbad37f3994e392ad.dcm",
]
SRC = next((p for p in CAND if p.exists()), None)
if SRC is None:
    print("Test DICOM topilmadi"); sys.exit(1)


def main():
    print("A3 SINOVI — Uncertainty heatmap")
    print(f"Test fayl: {SRC.name}\n")

    # 1. PNG render
    print("1. DICOM -> PNG render (max 2048)...")
    png_bytes = render_frame_png(SRC, frame=0, max_dim=2048)
    print(f"   PNG hajmi: {len(png_bytes)/1024:.0f} KB")

    # 2. Mavjud modellar (kamida 2 ta kerak)
    models = inf.list_models()
    print(f"\n2. Mavjud modellar: {len(models)} ta")
    for m in models:
        print(f"   - {m['name']}")
    if len(models) < 2:
        print("XATO: kamida 2 ta model kerak"); sys.exit(1)

    # 3. Har model uchun inference
    print(f"\n3. Har model uchun inference (conf=0.20)...")
    per_model_dets = []
    image_size_wh = None
    import time
    for m in models[:4]:  # birinchi 4 tasini ishlatamiz (CPU vaqtni tejash)
        t0 = time.time()
        try:
            res = inf.infer_png(png_bytes, model_name=m["name"], conf=0.20, iou=0.5, imgsz=1024)
            dets = res.get("detections", []) or []
            dt = time.time() - t0
            print(f"   {m['name']:<32} -> {len(dets)} det  ({dt:.1f}s)")
            for d in dets[:3]:
                print(f"      conf={d['confidence']:.3f}  label={d['label']!r}  bbox={[round(x, 3) for x in d['bbox']]}")
            per_model_dets.append(dets)
            if image_size_wh is None and res.get("image_size"):
                image_size_wh = tuple(res["image_size"])
        except Exception as e:
            print(f"   {m['name']:<32} -> XATO: {e}")

    if len(per_model_dets) < 2:
        print("XATO: 2 ta model ham ishlamadi"); sys.exit(1)
    print(f"   Image size (WxH): {image_size_wh}")

    # 4. Heatmap hisoblash
    print(f"\n4. Uncertainty xaritasini hisoblash...")
    heat, info = M._compute_uncertainty_map(per_model_dets, image_size_wh)
    print(f"   heat shape: {heat.shape}")
    print(f"   n_models: {info['n_models']}")
    print(f"   max_heat: {info['max_heat']:.4f}")
    print(f"   nonzero_pct: {info['nonzero_pct']:.2f}% (heat > 0.01)")

    # 5. PNG'ga render
    print(f"\n5. PNG xaritasini render qilish...")
    out_png = M._render_uncertainty_png(heat)
    print(f"   PNG hajmi: {len(out_png)/1024:.0f} KB")

    out_path = ROOT / "uncertainty_heatmap_test.png"
    out_path.write_bytes(out_png)
    print(f"   Saqlandi: {out_path}")

    # 6. Tahlil
    print(f"\n=== XULOSA ===")
    if info['nonzero_pct'] > 0.5:
        print(f"   ✓ Modellar kelishmagan zonalar topildi ({info['nonzero_pct']:.2f}% maydonda)")
        print(f"   ✓ Eng yuqori noaniqlik: {info['max_heat']:.3f}")
    else:
        print(f"   ⚠ Heatmap deyarli bo'sh ({info['nonzero_pct']:.2f}%) — modellar yaxshi kelishadi YOKI bitta-yarim model ishladi")

    # Per-model detection count
    print(f"\n   Modellar bo'yicha topilgan lezyon soni:")
    for m, dets in zip(models[:len(per_model_dets)], per_model_dets):
        print(f"     {m['name']:<32} = {len(dets)}")
    print("\n   OK")


if __name__ == "__main__":
    main()
