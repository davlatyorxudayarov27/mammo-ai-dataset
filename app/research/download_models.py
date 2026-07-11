"""Download base YOLO architectures as FINE-TUNING bases for mammography training.

IMPORTANT — read this first
===========================
These are COCO-pretrained *general-purpose* detectors. Running them directly on
mammograms will NOT detect masses / calcifications — they detect everyday
objects. They are only useful as **starting weights** that you fine-tune on your
own annotated mammography dataset.

The honest path to "excellent results":
  1. Annotate cases in MAMOGRAF (you already can).
  2. Export a YOLO dataset:  GET /api/export?format=yolo   (the ⤓ YOLO button).
  3. Fine-tune one or more of these architectures on that dataset
     (see app/research/train_detector.py).
  4. Drop the trained *.pt files into app/models/ — they appear in the AI dropdown.
  5. Turn on TTA and select "🧬 Ensemble (WBF)" to combine them.

Bigger architecture ≈ higher ceiling but slower + needs more data:
  n (nano) < s (small) < m (medium) < l (large) < x (extra-large)

Usage
-----
    python -m app.research.download_models                # default recommended set
    python -m app.research.download_models yolo11x yolov8l
    python -m app.research.download_models --dest app/research/pretrained
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Recommended training bases (downloaded by Ultralytics on first use).
RECOMMENDED = ["yolo11s", "yolo11m", "yolo11l", "yolo11x", "yolov8m"]

DEFAULT_DEST = Path(__file__).resolve().parent / "pretrained"


def download(names: list[str], dest: Path) -> list[Path]:
    try:
        from ultralytics import YOLO
    except ImportError:
        sys.exit("ultralytics is not installed. Run: pip install ultralytics")

    dest.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []
    for name in names:
        weight = name if name.endswith(".pt") else f"{name}.pt"
        print(f"→ fetching {weight} …")
        # Constructing YOLO(weight) downloads the COCO-pretrained checkpoint.
        model = YOLO(weight)
        ckpt = Path(model.ckpt_path) if getattr(model, "ckpt_path", None) else Path(weight)
        target = dest / ckpt.name
        if ckpt.exists() and ckpt.resolve() != target.resolve():
            target.write_bytes(ckpt.read_bytes())
        print(f"  saved base weights → {target}")
        saved.append(target)
    return saved


def main() -> None:
    ap = argparse.ArgumentParser(description="Download YOLO training bases (NOT ready detectors).")
    ap.add_argument("models", nargs="*", default=RECOMMENDED,
                    help=f"architectures to fetch (default: {' '.join(RECOMMENDED)})")
    ap.add_argument("--dest", default=str(DEFAULT_DEST),
                    help="destination folder for training bases")
    args = ap.parse_args()

    names = args.models or RECOMMENDED
    dest = Path(args.dest)
    saved = download(names, dest)

    print("\nDone. Downloaded training bases:")
    for p in saved:
        print(f"  {p}")
    print(
        "\nNEXT: fine-tune on your exported YOLO dataset, e.g.\n"
        "  yolo detect train model={base}.pt data=path/to/data.yaml imgsz=1024 epochs=100\n"
        "Then copy the resulting best.pt into app/models/ (rename meaningfully, e.g.\n"
        "mammo_yolo11m_v1.pt). It will show up in the AI model dropdown automatically.\n"
        "Do NOT put these raw COCO bases into app/models/ — they do not detect findings."
    )


if __name__ == "__main__":
    main()
