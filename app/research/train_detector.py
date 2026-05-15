"""Stage-1 YOLOv8/v11 detector training on CBIS-DDSM (or any YOLO-format
mammography dataset).

Tuned for mammography:

    - fliplr=0.0     images are pre-standardised to LEFT laterality
    - flipud=0.0     up/down flip changes anatomy
    - scale=0.1      conservative; lesion size is diagnostically meaningful
    - degrees=5      small rotations only
    - mosaic=0.3     low mosaic — multi-breast composites are unrealistic
    - mixup=0.0      blending two mammograms invents non-existent lesions
    - hsv_*=0.0      mammograms are grayscale; HSV jitter is meaningless
    - copy_paste=0.0 same reason as mosaic
    - close_mosaic   disables mosaic for the last N epochs

Beyond stock Ultralytics metrics (mAP@0.5, mAP@0.5:0.95) the script computes
**FROC** (Free-Response ROC) and **sensitivity at fixed FP/image** rates,
which are the standard mammography lesion-detection benchmarks.

Usage:
    python -m app.research.train_detector \\
        --data   /path/to/yolo_cbis/dataset.yaml \\
        --model  yolov8m.pt \\
        --epochs 100 \\
        --imgsz  1024 \\
        --batch  8 \\
        --project runs/cbis_stage1
"""
from __future__ import annotations

import argparse
import json
import sys
import warnings
from dataclasses import dataclass, asdict
from pathlib import Path

warnings.filterwarnings("ignore")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np


# ---------------------------------------------------------------------------
# Mammography-specific train hyper-parameters
# ---------------------------------------------------------------------------


MAMMO_HYPS = dict(
    # Augmentation
    hsv_h=0.0, hsv_s=0.0, hsv_v=0.05,
    degrees=5.0,
    translate=0.05,
    scale=0.10,
    shear=0.0,
    perspective=0.0,
    flipud=0.0,
    fliplr=0.0,
    mosaic=0.3,
    mixup=0.0,
    copy_paste=0.0,
    erasing=0.0,
    close_mosaic=10,
    # Optimization (sane defaults — Ultralytics auto-tunes lr0 anyway)
    optimizer="AdamW",
    lr0=1e-3,
    lrf=0.01,
    momentum=0.937,
    weight_decay=5e-4,
    warmup_epochs=3.0,
    cos_lr=True,
    # Detection-specific
    box=7.5, cls=0.5, dfl=1.5,
    label_smoothing=0.0,
)


# ---------------------------------------------------------------------------
# YOLO label I/O
# ---------------------------------------------------------------------------


def _read_yolo_label(path: Path, img_size: int) -> list[tuple[int, float, float, float, float]]:
    """Return list of (cls, x0, y0, x1, y1) in pixel coords."""
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.strip().split()
        if len(parts) != 5:
            continue
        cls = int(parts[0])
        cx, cy, w, h = (float(x) for x in parts[1:])
        x0 = (cx - w / 2) * img_size
        y0 = (cy - h / 2) * img_size
        x1 = (cx + w / 2) * img_size
        y1 = (cy + h / 2) * img_size
        out.append((cls, x0, y0, x1, y1))
    return out


# ---------------------------------------------------------------------------
# IoU + bbox matching for FROC
# ---------------------------------------------------------------------------


def _iou(a: tuple, b: tuple) -> float:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    ix0 = max(ax0, bx0); iy0 = max(ay0, by0)
    ix1 = min(ax1, bx1); iy1 = min(ay1, by1)
    iw = max(0.0, ix1 - ix0); ih = max(0.0, iy1 - iy0)
    inter = iw * ih
    area_a = max(0.0, ax1 - ax0) * max(0.0, ay1 - ay0)
    area_b = max(0.0, bx1 - bx0) * max(0.0, by1 - by0)
    union = area_a + area_b - inter
    if union <= 0:
        return 0.0
    return inter / union


@dataclass
class _PredHit:
    score: float
    is_tp: bool          # matched a GT


def _match_image(
    preds: list[tuple[float, float, float, float, float]],   # (score, x0, y0, x1, y1)
    gts: list[tuple[int, float, float, float, float]],
    iou_thr: float,
) -> tuple[list[_PredHit], int]:
    """Greedy match preds to GTs by descending score. Returns (hits, n_gt)."""
    n_gt = len(gts)
    used = [False] * n_gt
    hits: list[_PredHit] = []
    preds_sorted = sorted(preds, key=lambda p: -p[0])
    for score, *box in preds_sorted:
        best_iou = 0.0
        best_idx = -1
        for j, g in enumerate(gts):
            if used[j]:
                continue
            i = _iou(tuple(box), tuple(g[1:]))
            if i > best_iou:
                best_iou = i
                best_idx = j
        if best_idx >= 0 and best_iou >= iou_thr:
            used[best_idx] = True
            hits.append(_PredHit(score=score, is_tp=True))
        else:
            hits.append(_PredHit(score=score, is_tp=False))
    return hits, n_gt


# ---------------------------------------------------------------------------
# FROC curve
# ---------------------------------------------------------------------------


@dataclass
class FrocPoint:
    score: float
    sensitivity: float
    fp_per_image: float


def compute_froc(
    per_image: list[tuple[list[_PredHit], int]],
    n_images: int,
) -> list[FrocPoint]:
    """Sweep score threshold; return one (sens, fp/img) per unique score."""
    all_hits: list[_PredHit] = []
    total_gt = 0
    for hits, n_gt in per_image:
        all_hits.extend(hits)
        total_gt += n_gt
    if total_gt == 0 or n_images == 0:
        return []

    all_hits.sort(key=lambda h: -h.score)
    tp = fp = 0
    pts: list[FrocPoint] = []
    last_score = None
    for h in all_hits:
        if h.is_tp:
            tp += 1
        else:
            fp += 1
        if last_score is None or h.score < last_score - 1e-9:
            pts.append(FrocPoint(
                score=float(h.score),
                sensitivity=tp / total_gt,
                fp_per_image=fp / n_images,
            ))
            last_score = h.score
    return pts


def sensitivity_at_fp(curve: list[FrocPoint], fp_target: float) -> float:
    """Highest sensitivity achievable at fp_per_image ≤ fp_target."""
    best = 0.0
    for p in curve:
        if p.fp_per_image <= fp_target and p.sensitivity > best:
            best = p.sensitivity
    return best


# ---------------------------------------------------------------------------
# Run YOLO inference on the test split and collect preds + GTs
# ---------------------------------------------------------------------------


def evaluate_froc(
    weights: Path,
    data_yaml: Path,
    split: str,
    imgsz: int,
    conf_min: float = 0.001,
    iou_thr: float = 0.3,
    device: str | None = None,
) -> dict:
    """Run weights over `split` images and compute FROC."""
    from ultralytics import YOLO  # local import — only needed for eval
    import yaml as _yaml

    cfg = _yaml.safe_load(data_yaml.read_text(encoding="utf-8"))
    root = Path(cfg.get("path", data_yaml.parent)).resolve()
    img_dir = root / cfg.get(split, f"images/{split}")
    if not img_dir.exists():
        raise FileNotFoundError(f"split dir not found: {img_dir}")
    label_dir = Path(str(img_dir).replace("/images/", "/labels/").replace("\\images\\", "\\labels\\"))

    images = sorted(p for p in img_dir.iterdir() if p.suffix.lower() in (".png", ".jpg", ".jpeg"))
    if not images:
        raise RuntimeError(f"no images under {img_dir}")

    model = YOLO(str(weights))

    per_image: list[tuple[list[_PredHit], int]] = []
    for batch_start in range(0, len(images), 32):
        batch = images[batch_start:batch_start + 32]
        results = model.predict(
            source=[str(p) for p in batch],
            imgsz=imgsz,
            conf=conf_min,
            iou=0.5,
            device=device,
            verbose=False,
            save=False,
        )
        for img_path, res in zip(batch, results):
            preds: list[tuple[float, float, float, float, float]] = []
            if res.boxes is not None and len(res.boxes) > 0:
                xyxy = res.boxes.xyxy.cpu().numpy()
                conf = res.boxes.conf.cpu().numpy()
                for (x0, y0, x1, y1), s in zip(xyxy, conf):
                    preds.append((float(s), float(x0), float(y0), float(x1), float(y1)))
            gt_path = label_dir / (img_path.stem + ".txt")
            gts = _read_yolo_label(gt_path, imgsz)
            per_image.append(_match_image(preds, gts, iou_thr))

    curve = compute_froc(per_image, n_images=len(images))
    fp_targets = [0.5, 1.0, 2.0, 4.0]
    summary = {
        "n_images": len(images),
        "iou_threshold": iou_thr,
        "n_total_gt": sum(n for _, n in per_image),
        "sens_at_fp": {f"{t:g}": sensitivity_at_fp(curve, t) for t in fp_targets},
        "froc_curve": [asdict(p) for p in curve],
    }
    return summary


def plot_froc(summary: dict, out_path: Path) -> None:
    """Save a FROC plot PNG (skips silently if matplotlib is missing)."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return
    curve = summary.get("froc_curve") or []
    if not curve:
        return
    fp = [p["fp_per_image"] for p in curve]
    se = [p["sensitivity"] for p in curve]
    fig, ax = plt.subplots(figsize=(5.5, 4.5))
    ax.plot(fp, se, "-", linewidth=2.0, color="#1f77b4")
    for t, val in summary["sens_at_fp"].items():
        ax.axvline(float(t), color="#888", linestyle=":", linewidth=0.8)
        ax.text(float(t), 0.02, f" {val:.2f}@{t}", fontsize=8, color="#444")
    ax.set_xlabel("False positives per image")
    ax.set_ylabel("Sensitivity (recall)")
    ax.set_title(f"FROC — IoU≥{summary.get('iou_threshold',0.3):.1f}, "
                 f"n={summary.get('n_images',0)}")
    ax.set_xscale("symlog", linthresh=0.5)
    ax.set_xlim(0, max(8.0, max(fp) if fp else 8.0))
    ax.set_ylim(0, 1.02)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    ap = argparse.ArgumentParser(description="Stage-1 YOLO mammography detector")
    ap.add_argument("--data", required=True, help="Path to dataset.yaml")
    ap.add_argument("--model", default="yolov8m.pt",
                    help="Pretrained weights or .yaml architecture spec")
    ap.add_argument("--epochs", type=int, default=100)
    ap.add_argument("--imgsz", type=int, default=1024)
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--device", default=None,
                    help="GPU id ('0'), 'cpu', or None for auto")
    ap.add_argument("--project", default="runs/detect", help="Output dir for runs")
    ap.add_argument("--name", default="cbis_stage1")
    ap.add_argument("--patience", type=int, default=20)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--resume", action="store_true",
                    help="Resume the last run with --name")
    ap.add_argument("--no-train", action="store_true",
                    help="Skip training; only run FROC eval on existing weights")
    ap.add_argument("--weights", default=None,
                    help="When --no-train, path to weights .pt; else uses best.pt of the run")
    ap.add_argument("--eval-split", default="test",
                    help="Which split to FROC-evaluate (default: test)")
    ap.add_argument("--iou-thr", type=float, default=0.3,
                    help="IoU threshold for hit detection in FROC (mammo standard 0.2–0.5)")
    args = ap.parse_args()

    data_yaml = Path(args.data).resolve()
    if not data_yaml.exists():
        raise SystemExit(f"dataset.yaml not found: {data_yaml}")

    project_dir = Path(args.project).resolve()
    project_dir.mkdir(parents=True, exist_ok=True)

    if not args.no_train:
        from ultralytics import YOLO
        print(f"[train] model={args.model} imgsz={args.imgsz} batch={args.batch} "
              f"epochs={args.epochs} device={args.device or 'auto'}")
        model = YOLO(args.model)
        results = model.train(
            data=str(data_yaml),
            epochs=args.epochs,
            imgsz=args.imgsz,
            batch=args.batch,
            device=args.device,
            workers=args.workers,
            project=str(project_dir),
            name=args.name,
            patience=args.patience,
            resume=args.resume,
            exist_ok=True,
            **MAMMO_HYPS,
        )
        run_dir = Path(results.save_dir) if hasattr(results, "save_dir") else (project_dir / args.name)
        weights = run_dir / "weights" / "best.pt"
    else:
        run_dir = project_dir / args.name
        weights = Path(args.weights) if args.weights else (run_dir / "weights" / "best.pt")

    if not weights.exists():
        raise SystemExit(f"best.pt not found at {weights}")

    print(f"\n[eval] FROC on split='{args.eval_split}', IoU≥{args.iou_thr}")
    summary = evaluate_froc(
        weights=weights,
        data_yaml=data_yaml,
        split=args.eval_split,
        imgsz=args.imgsz,
        iou_thr=args.iou_thr,
        device=args.device,
    )

    print(f"  n_images = {summary['n_images']}, n_gt = {summary['n_total_gt']}")
    for fp_t, sens in summary["sens_at_fp"].items():
        print(f"  sens @ {fp_t:>4} FP/img : {sens:.4f}")

    out_dir = Path(run_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "froc_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8",
    )
    plot_froc(summary, out_dir / "froc.png")
    print(f"\n[saved] {out_dir / 'froc_summary.json'}")
    print(f"[saved] {out_dir / 'froc.png'}")


if __name__ == "__main__":
    main()
