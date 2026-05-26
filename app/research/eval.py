"""Detection-benchmark evaluation for MAMOGRAF.

Reports per-configuration AP@0.5, AP@[0.5:0.95], and FROC (sensitivity at
0.25, 0.5, 1.0, 2.0, 4.0 false positives / image) with bootstrap 95% CIs.
Supports four configurations driven from a single dataset:

  * each individual YOLO model (`--models a.pt b.pt …`)
  * the WBF ensemble of those models (`--ensemble`)
  * the same with test-time augmentation (`--tta`)

Dataset layout follows the standard Ultralytics YOLO format::

    data.yaml          # `path:`, `val:` (or `test:`), `names: {0: …, 1: …}`
    images/<split>/*.[png|jpg]
    labels/<split>/*.txt   # one row per box: "<cls> cx cy w h" (normalised)

Usage:
    python -m app.research.eval --data path/to/data.yaml \\
        --models app/models/yolo9_e.pt app/models/yolo11_x.pt \\
        --ensemble --tta --bootstrap 1000 \\
        --out paper/results.json --md-out paper/results_tables.md

Outputs a JSON file with raw metrics + bootstrap CIs and a Markdown file with
Tables 3 / FROC ready to paste into the manuscript.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Optional

import numpy as np
from PIL import Image

try:
    import yaml
except ImportError:
    sys.exit("PyYAML is required: pip install pyyaml")

# Reuse the WBF + TTA implementation from the platform.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from app.inference import infer_png, weighted_boxes_fusion  # noqa: E402


# --------------------------------------------------------------------------- #
# Dataset helpers                                                             #
# --------------------------------------------------------------------------- #
def load_dataset(yaml_path: Path, split: str | None) -> tuple[list[Path], dict[int, str]]:
    cfg = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    root = Path(cfg.get("path", yaml_path.parent)).expanduser()
    if not root.is_absolute():
        root = (yaml_path.parent / root).resolve()
    chosen = split or ("test" if "test" in cfg else "val")
    images_dir = cfg.get(chosen)
    if images_dir is None:
        raise SystemExit(f"split '{chosen}' not present in {yaml_path}")
    images_dir = root / images_dir
    images = sorted(p for p in images_dir.rglob("*") if p.suffix.lower() in {".png", ".jpg", ".jpeg"})
    if not images:
        raise SystemExit(f"no images found under {images_dir}")
    names_raw = cfg.get("names", {})
    if isinstance(names_raw, list):
        names = {i: n for i, n in enumerate(names_raw)}
    else:
        names = {int(k): v for k, v in names_raw.items()}
    return images, names


def label_path_for(img: Path) -> Path:
    return Path(str(img).replace("/images/", "/labels/").replace("\\images\\", "\\labels\\")).with_suffix(".txt")


def read_yolo_labels(p: Path) -> list[tuple[int, float, float, float, float]]:
    """Each line: <cls> <cx> <cy> <w> <h> (normalised); returns (cls, x1, y1, x2, y2)."""
    out = []
    if not p.exists():
        return out
    for line in p.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) != 5:
            continue
        c, cx, cy, w, h = parts
        cx, cy, w, h = float(cx), float(cy), float(w), float(h)
        out.append((int(c), cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2))
    return out


# --------------------------------------------------------------------------- #
# Inference                                                                   #
# --------------------------------------------------------------------------- #
def detect_one(image_path: Path, models: list[str], ensemble: bool, tta: bool,
                conf: float, iou: float, imgsz: int, names_inv: dict[str, int]
                ) -> list[tuple[int, float, float, float, float, float]]:
    """Return detections as (cls, x1, y1, x2, y2, score), normalised."""
    png = image_path.read_bytes()
    per_model: list[list[dict]] = []
    for m in models:
        r = infer_png(png, m, conf=conf, iou=iou, imgsz=imgsz, tta=tta)
        per_model.append(r["detections"])
    dets_dicts = (weighted_boxes_fusion(per_model, iou_thr=0.55, num_sources=len(models))
                  if ensemble else per_model[0])
    out = []
    for d in dets_dicts:
        cls = names_inv.get(str(d.get("label")), d.get("class_id", -1))
        if cls is None or cls < 0:
            continue
        x, y, w, h = d["bbox"]
        out.append((int(cls), x, y, x + w, y + h, float(d["confidence"])))
    return out


# --------------------------------------------------------------------------- #
# Metrics                                                                     #
# --------------------------------------------------------------------------- #
def iou_xyxy(a, b):
    ix1, iy1 = max(a[0], b[0]), max(a[1], b[1])
    ix2, iy2 = min(a[2], b[2]), min(a[3], b[3])
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    inter = iw * ih
    if inter <= 0:
        return 0.0
    area_a = max(0.0, a[2] - a[0]) * max(0.0, a[3] - a[1])
    area_b = max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])
    return inter / (area_a + area_b - inter + 1e-12)


def match_image(preds, gts, iou_thr: float):
    """Greedy IoU matching; returns list of (score, tp_flag) and #FP, plus per-image TP count."""
    preds_sorted = sorted(preds, key=lambda p: -p[5])
    used = [False] * len(gts)
    out: list[tuple[float, int]] = []
    tp = 0
    fp = 0
    for cls, x1, y1, x2, y2, s in preds_sorted:
        best_i, best_iou = -1, iou_thr
        for i, g in enumerate(gts):
            if used[i] or g[0] != cls:
                continue
            iou = iou_xyxy((x1, y1, x2, y2), g[1:5])
            if iou > best_iou:
                best_iou, best_i = iou, i
        if best_i >= 0:
            used[best_i] = True
            out.append((s, 1))
            tp += 1
        else:
            out.append((s, 0))
            fp += 1
    fn = sum(1 for u in used if not u)
    return out, tp, fp, fn


def ap_from_pr(scored: list[tuple[float, int]], n_gt: int) -> float:
    """Average precision via the all-point interpolation (COCO style)."""
    if n_gt == 0:
        return 0.0 if not scored else float("nan")
    scored = sorted(scored, key=lambda x: -x[0])
    tp_cum, fp_cum = 0, 0
    pr = []
    for s, tp_flag in scored:
        tp_cum += tp_flag
        fp_cum += 1 - tp_flag
        recall = tp_cum / n_gt
        precision = tp_cum / (tp_cum + fp_cum)
        pr.append((recall, precision))
    if not pr:
        return 0.0
    rec = np.array([0.0] + [p[0] for p in pr] + [1.0])
    prec = np.array([0.0] + [p[1] for p in pr] + [0.0])
    for i in range(len(prec) - 2, -1, -1):
        prec[i] = max(prec[i], prec[i + 1])
    idx = np.where(rec[1:] != rec[:-1])[0]
    return float(np.sum((rec[idx + 1] - rec[idx]) * prec[idx + 1]))


def map_at_iou(per_image_dets, per_image_gts, iou_thr: float) -> float:
    """Mean AP across classes at a single IoU threshold."""
    by_cls_scored: dict[int, list[tuple[float, int]]] = defaultdict(list)
    by_cls_gt: dict[int, int] = defaultdict(int)
    for preds, gts in zip(per_image_dets, per_image_gts):
        for g in gts:
            by_cls_gt[g[0]] += 1
        # match per class
        for cls in set([p[0] for p in preds] + [g[0] for g in gts]):
            preds_c = [p for p in preds if p[0] == cls]
            gts_c = [g for g in gts if g[0] == cls]
            scored, _, _, _ = match_image(preds_c, gts_c, iou_thr)
            by_cls_scored[cls].extend(scored)
    if not by_cls_gt:
        return float("nan")
    aps = [ap_from_pr(by_cls_scored[c], by_cls_gt[c]) for c in by_cls_gt]
    return float(np.mean(aps))


def coco_ap(per_image_dets, per_image_gts) -> float:
    return float(np.mean([map_at_iou(per_image_dets, per_image_gts, t)
                          for t in np.arange(0.5, 1.0, 0.05)]))


def froc(per_image_dets, per_image_gts, fppi_points=(0.25, 0.5, 1.0, 2.0, 4.0),
         iou_thr: float = 0.5) -> dict[float, float]:
    """Sensitivity at fixed FP-per-image operating points (single-class proxy)."""
    pairs: list[tuple[float, int, int]] = []  # (score, tp, n_images_contribution=1)
    n_gt = 0
    n_img = max(1, len(per_image_dets))
    for preds, gts in zip(per_image_dets, per_image_gts):
        n_gt += len(gts)
        scored, _tp, _fp, _fn = match_image(preds, gts, iou_thr)
        for s, tp in scored:
            pairs.append((s, tp, 1))
    if n_gt == 0:
        return {f: float("nan") for f in fppi_points}
    pairs.sort(key=lambda x: -x[0])
    tp_cum, fp_cum = 0, 0
    curve = []  # (fppi, sensitivity)
    for s, tp, _ in pairs:
        tp_cum += tp
        fp_cum += 1 - tp
        curve.append((fp_cum / n_img, tp_cum / n_gt))
    out: dict[float, float] = {}
    for target in fppi_points:
        best = 0.0
        for fppi, sens in curve:
            if fppi <= target and sens > best:
                best = sens
        out[target] = float(best)
    return out


def bootstrap_ci(per_image_dets, per_image_gts, metric_fn, n: int = 1000,
                 seed: int = 0) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    m = len(per_image_dets)
    vals = []
    for _ in range(n):
        idx = rng.integers(0, m, size=m)
        v = metric_fn([per_image_dets[i] for i in idx], [per_image_gts[i] for i in idx])
        if np.isfinite(v):
            vals.append(v)
    if not vals:
        return float("nan"), float("nan")
    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


# --------------------------------------------------------------------------- #
# Per-configuration evaluator                                                 #
# --------------------------------------------------------------------------- #
def evaluate_config(name: str, images: list[Path], names: dict[int, str],
                    models: list[str], ensemble: bool, tta: bool,
                    conf: float, iou: float, imgsz: int,
                    bootstrap: int) -> dict:
    names_inv = {v: k for k, v in names.items()}
    per_image_dets, per_image_gts = [], []
    t0 = time.time()
    for i, img in enumerate(images, 1):
        dets = detect_one(img, models, ensemble, tta, conf, iou, imgsz, names_inv)
        per_image_dets.append(dets)
        per_image_gts.append(read_yolo_labels(label_path_for(img)))
        if i % 25 == 0 or i == len(images):
            print(f"  {name}: {i}/{len(images)}  elapsed {time.time() - t0:.1f}s", flush=True)

    ap50 = map_at_iou(per_image_dets, per_image_gts, 0.5)
    ap5095 = coco_ap(per_image_dets, per_image_gts)
    froc_pts = froc(per_image_dets, per_image_gts)
    res = {
        "config": name, "n_images": len(images),
        "AP@0.5": ap50, "AP@[0.5:0.95]": ap5095, "FROC": froc_pts,
        "wall_time_s": time.time() - t0,
    }
    if bootstrap > 0:
        ci_lo, ci_hi = bootstrap_ci(per_image_dets, per_image_gts,
                                      lambda d, g: map_at_iou(d, g, 0.5),
                                      n=bootstrap)
        res["AP@0.5_ci95"] = [ci_lo, ci_hi]
    return res


# --------------------------------------------------------------------------- #
# Markdown table emitter                                                      #
# --------------------------------------------------------------------------- #
def write_markdown(results: list[dict], path: Path) -> None:
    fppi = (0.25, 0.5, 1.0, 2.0, 4.0)
    lines = ["# Detection benchmark", ""]
    lines.append("| Configuration | n | AP@0.5 (95% CI) | AP@[0.5:0.95] | "
                 + " | ".join(f"FROC@{f}" for f in fppi) + " |")
    lines.append("|" + "|".join(["---"] * (4 + len(fppi))) + "|")
    for r in results:
        ci = r.get("AP@0.5_ci95")
        ci_s = f" ({ci[0]:.3f}–{ci[1]:.3f})" if ci else ""
        froc_s = " | ".join(f"{r['FROC'][f]:.3f}" for f in fppi)
        lines.append(f"| {r['config']} | {r['n_images']} | "
                     f"{r['AP@0.5']:.3f}{ci_s} | {r['AP@[0.5:0.95]']:.3f} | {froc_s} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------- #
# CLI                                                                         #
# --------------------------------------------------------------------------- #
def main() -> None:
    ap = argparse.ArgumentParser(description="Detection benchmark (AP / FROC) for MAMOGRAF.")
    ap.add_argument("--data", required=True, help="Ultralytics data.yaml")
    ap.add_argument("--split", default=None, help="'test' (default if present) or 'val'")
    ap.add_argument("--models", nargs="+", required=True,
                    help="paths or filenames inside app/models/")
    ap.add_argument("--ensemble", action="store_true",
                    help="also evaluate the WBF ensemble of all --models")
    ap.add_argument("--tta", action="store_true",
                    help="also evaluate the TTA variant of each configuration")
    ap.add_argument("--conf", type=float, default=0.05)
    ap.add_argument("--iou", type=float, default=0.5)
    ap.add_argument("--imgsz", type=int, default=1024)
    ap.add_argument("--bootstrap", type=int, default=1000,
                    help="bootstrap iterations for AP@0.5 CI (0 to disable)")
    ap.add_argument("--out", default="paper/results.json")
    ap.add_argument("--md-out", default="paper/results_tables.md")
    args = ap.parse_args()

    images, names = load_dataset(Path(args.data), args.split)
    print(f"dataset: {len(images)} images, {len(names)} classes: {list(names.values())}")

    configs: list[tuple[str, list[str], bool, bool]] = []
    for m in args.models:
        stem = Path(m).stem
        configs.append((f"{stem} (single)", [m], False, False))
        if args.tta:
            configs.append((f"{stem} + TTA", [m], False, True))
    if args.ensemble and len(args.models) >= 2:
        configs.append((f"WBF ensemble x{len(args.models)}", args.models, True, False))
        if args.tta:
            configs.append((f"WBF ensemble x{len(args.models)} + TTA",
                            args.models, True, True))

    results = []
    for cfg_name, mlist, ens, tta in configs:
        print(f"\n>>> {cfg_name}")
        r = evaluate_config(cfg_name, images, names, mlist, ens, tta,
                             args.conf, args.iou, args.imgsz, args.bootstrap)
        results.append(r)
        print(f"    AP@0.5={r['AP@0.5']:.3f}  AP@[0.5:0.95]={r['AP@[0.5:0.95]']:.3f}  "
              f"FROC@1FP={r['FROC'][1.0]:.3f}")

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps({"results": results, "models": args.models,
                                            "classes": names}, indent=2), encoding="utf-8")
    Path(args.md_out).parent.mkdir(parents=True, exist_ok=True)
    write_markdown(results, Path(args.md_out))
    print(f"\nWrote {args.out} and {args.md_out}")


if __name__ == "__main__":
    main()
