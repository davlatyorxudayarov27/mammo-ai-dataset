"""
COCO JSON eksport faylini YOLO formatga aylantiradi.

MAMOGRAF Viewer tomonidan eksport qilingan `annotations_coco_*.json`
fayldan YOLO format'da `labels/*.txt` va `images/` strukturasini yaratadi.

YOLO bbox format (har qator bitta bbox):
    <class_id> <x_center> <y_center> <width> <height>

Hammasi normalized [0..1].

Foydalanish:
    python -m app.coco_to_yolo annotations_coco.json --out yolo_dataset/
    python -m app.coco_to_yolo annotations_coco.json --out dataset/ --copy-images
    python -m app.coco_to_yolo annotations_coco.json --out dataset/ --train-val 0.8
"""
from __future__ import annotations

import argparse
import json
import random
import shutil
import sys
from pathlib import Path


def convert(
    coco_path: Path,
    out_dir: Path,
    copy_images: bool = False,
    upload_dir: Path | None = None,
    local_root: Path | None = None,
    train_val: float = 0.0,
    seed: int = 42,
) -> dict:
    if not coco_path.exists():
        raise FileNotFoundError(coco_path)
    data = json.loads(coco_path.read_text(encoding="utf-8"))

    images = {img["id"]: img for img in data.get("images", [])}
    cats = {c["id"]: c["name"] for c in data.get("categories", [])}
    sorted_cat_ids = sorted(cats.keys())
    cat_id_to_yolo = {cid: i for i, cid in enumerate(sorted_cat_ids)}

    out_dir.mkdir(parents=True, exist_ok=True)
    labels_dir = out_dir / "labels"
    images_dir = out_dir / "images"
    labels_dir.mkdir(exist_ok=True)
    if copy_images:
        images_dir.mkdir(exist_ok=True)

    by_image: dict[int, list[dict]] = {}
    for ann in data.get("annotations", []):
        by_image.setdefault(ann["image_id"], []).append(ann)

    written_labels = 0
    skipped_no_dim = 0
    copied_images = 0

    image_stems: list[str] = []
    for img_id, img in images.items():
        stem = Path(img["file_name"]).stem or f"img_{img_id}"
        image_stems.append(stem)
        anns = by_image.get(img_id, [])
        rows = []
        w = img.get("width") or 0
        h = img.get("height") or 0
        if not w or not h:
            skipped_no_dim += 1
            continue
        for ann in anns:
            yc = cat_id_to_yolo.get(ann["category_id"])
            if yc is None:
                continue
            bn = ann.get("bbox_normalized")
            if bn and len(bn) == 4:
                x_n, y_n, w_n, h_n = bn
            else:
                x_px, y_px, w_px, h_px = ann.get("bbox", [0, 0, 0, 0])
                x_n = x_px / w
                y_n = y_px / h
                w_n = w_px / w
                h_n = h_px / h
            xc = x_n + w_n / 2
            yc_norm = y_n + h_n / 2
            rows.append(f"{yc} {xc:.6f} {yc_norm:.6f} {w_n:.6f} {h_n:.6f}")
        (labels_dir / f"{stem}.txt").write_text("\n".join(rows), encoding="utf-8")
        written_labels += 1

        if copy_images:
            src_path = None
            ref = img["file_name"]
            if img.get("source") == "upload" and upload_dir:
                cand = upload_dir / f"{ref}.dcm"
                if cand.exists():
                    src_path = cand
            elif img.get("source") == "local" and local_root:
                cand = local_root / ref
                if cand.exists():
                    src_path = cand
            if src_path:
                shutil.copy2(src_path, images_dir / f"{stem}.dcm")
                copied_images += 1

    classes_file = out_dir / "classes.txt"
    classes_file.write_text(
        "\n".join(cats[cid] for cid in sorted_cat_ids), encoding="utf-8"
    )

    yaml_path = out_dir / "data.yaml"
    train_path = "images/train" if train_val else "images"
    val_path = "images/val" if train_val else "images"
    yaml_text = (
        f"# YOLO dataset config (avtomatik yaratilgan)\n"
        f"path: {out_dir.resolve().as_posix()}\n"
        f"train: {train_path}\n"
        f"val: {val_path}\n"
        f"names:\n"
    )
    for i, cid in enumerate(sorted_cat_ids):
        yaml_text += f"  {i}: {cats[cid]}\n"
    yaml_path.write_text(yaml_text, encoding="utf-8")

    split_info = {}
    if train_val and 0 < train_val < 1:
        random.Random(seed).shuffle(image_stems)
        cut = int(len(image_stems) * train_val)
        train_stems = image_stems[:cut]
        val_stems = image_stems[cut:]
        split_info = {"train": len(train_stems), "val": len(val_stems)}
        for split, stems in [("train", train_stems), ("val", val_stems)]:
            split_lbl = labels_dir.parent / "labels" / split
            split_img = images_dir.parent / "images" / split
            split_lbl.mkdir(parents=True, exist_ok=True)
            split_img.mkdir(parents=True, exist_ok=True)
            for stem in stems:
                lbl_src = labels_dir / f"{stem}.txt"
                if lbl_src.exists():
                    shutil.move(str(lbl_src), str(split_lbl / f"{stem}.txt"))
                if copy_images:
                    img_src = images_dir / f"{stem}.dcm"
                    if img_src.exists():
                        shutil.move(str(img_src), str(split_img / f"{stem}.dcm"))

    return {
        "out_dir": str(out_dir.resolve()),
        "yaml": str(yaml_path),
        "classes": list(cats[cid] for cid in sorted_cat_ids),
        "labels_written": written_labels,
        "images_copied": copied_images,
        "skipped_no_dim": skipped_no_dim,
        "split": split_info,
    }


def main():
    ap = argparse.ArgumentParser(description="MAMOGRAF COCO eksportni YOLO formatga aylantirish")
    ap.add_argument("coco_json", help="annotations_coco_YYYYMMDD_HHMMSS.json")
    ap.add_argument("--out", default="yolo_dataset", help="chiquvchi papka")
    ap.add_argument("--copy-images", action="store_true",
                    help="DICOM fayllarni dataset papkasiga ko'chirish")
    ap.add_argument("--upload-dir", default="app/uploads", help="upload manbai")
    ap.add_argument("--local-root", default="",
                    help="LOCAL_DICOM_ROOT (lokal manbalar uchun)")
    ap.add_argument("--train-val", type=float, default=0.0,
                    help="train/val split nisbati (e.g. 0.8 = 80/20)")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    coco = Path(args.coco_json)
    if not coco.exists():
        print(f"fayl topilmadi: {coco}", file=sys.stderr)
        sys.exit(1)

    res = convert(
        coco,
        Path(args.out),
        copy_images=args.copy_images,
        upload_dir=Path(args.upload_dir) if args.upload_dir else None,
        local_root=Path(args.local_root) if args.local_root else None,
        train_val=args.train_val,
        seed=args.seed,
    )
    width = max(len(k) for k in res)
    for k, v in res.items():
        print(f"  {k.ljust(width)} : {v}")


if __name__ == "__main__":
    main()
