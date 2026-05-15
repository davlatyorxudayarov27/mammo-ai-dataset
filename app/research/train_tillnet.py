"""TILLNet-Det training script.

End-to-end trainer for the multimodal mammography detector defined in
`app.models_arch.tillnet_det`. Implements:

    - FCOS-style dense target assignment (per-level regress ranges + center sampling)
    - Composite loss:  focal_cls + GIoU_reg + BCE_centerness
    - Paired (image, text) dataloader: PNG + YOLO .txt + clinical text
    - AdamW + cosine LR schedule + linear warmup
    - Periodic FROC validation (best checkpoint by sensitivity@1FP/image)

The script reuses the FROC math from `app.research.train_detector` so the
metric numbers are directly comparable to the YOLOv8 stage-1 baseline.

Usage:
    python -m app.research.train_tillnet \\
        --data    /path/to/yolo_cbis/dataset.yaml \\
        --texts   /path/to/texts.csv         # columns: filename,text
        --epochs  60 \\
        --imgsz   1024 \\
        --batch   2 \\
        --device  0 \\
        --out     runs/tillnet
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
import warnings
from dataclasses import dataclass
from pathlib import Path

warnings.filterwarnings("ignore")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from PIL import Image

from app.models_arch.tillnet_det import (
    TILLNetDet, TILLNetConfig, encode_text, TEXT_MAX_LEN,
)
from app.research.train_detector import (
    _PredHit, _match_image, compute_froc, sensitivity_at_fp, plot_froc,
)


# Standard FCOS regress ranges (in original-image pixels) per pyramid level.
# Locations whose maximum (l,t,r,b) falls in the level's range are "responsible"
# for that GT, which gives the network a natural multi-scale specialisation.
REGRESS_RANGES = (
    (-1, 64),     # P3 stride 8     small lesions ≤ 64 px
    (64, 128),    # P4 stride 16
    (128, 256),   # P5 stride 32
    (256, 512),   # P6 stride 64
    (512, 10_000) # P7 stride 128   large masses
)


# ---------------------------------------------------------------------------
# 1. Dataset — paired (image, YOLO labels, text)
# ---------------------------------------------------------------------------


def _read_yolo_label(path: Path, img_size: int) -> tuple[np.ndarray, np.ndarray]:
    """Returns (boxes Nx4 xyxy in pixels, labels N int64)."""
    boxes, labels = [], []
    if path.exists():
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
            if x1 > x0 and y1 > y0:
                boxes.append([x0, y0, x1, y1])
                labels.append(cls)
    return (np.asarray(boxes, dtype=np.float32).reshape(-1, 4),
            np.asarray(labels, dtype=np.int64))


class MammoDetTextDataset(Dataset):
    """One sample = (image tensor, GT boxes, GT labels, text token ids)."""

    def __init__(
        self,
        images_dir: Path,
        labels_dir: Path,
        texts_lookup: dict[str, str],
        target_size: int,
        augment: bool = False,
    ):
        self.images_dir = Path(images_dir)
        self.labels_dir = Path(labels_dir)
        self.target_size = target_size
        self.augment = augment
        self.texts_lookup = texts_lookup
        self.files = sorted(p for p in self.images_dir.iterdir()
                            if p.suffix.lower() in (".png", ".jpg", ".jpeg"))
        if not self.files:
            raise RuntimeError(f"no images under {images_dir}")

    def __len__(self) -> int:
        return len(self.files)

    def __getitem__(self, idx: int):
        img_path = self.files[idx]
        # PIL grayscale, scale to target_size if mismatched (preprocess.py already
        # produces target-size PNGs, but this guards against mixed runs).
        img = Image.open(img_path).convert("L")
        if img.size != (self.target_size, self.target_size):
            img = img.resize((self.target_size, self.target_size), Image.BILINEAR)
        arr = np.asarray(img, dtype=np.float32) / 255.0

        if self.augment:
            # Mammography-conservative: slight intensity jitter only.
            arr = arr * float(np.random.uniform(0.9, 1.1))
            arr = np.clip(arr + float(np.random.uniform(-0.05, 0.05)), 0.0, 1.0)

        img_t = torch.from_numpy(arr)[None]                     # (1, H, W)

        lbl_path = self.labels_dir / (img_path.stem + ".txt")
        boxes, labels = _read_yolo_label(lbl_path, self.target_size)
        boxes_t = torch.from_numpy(boxes)
        labels_t = torch.from_numpy(labels)

        text = self.texts_lookup.get(img_path.name, "")
        text_ids = encode_text(text)

        return {
            "image": img_t,
            "boxes": boxes_t,            # (N, 4)
            "labels": labels_t,          # (N,)
            "text_ids": text_ids,        # (L,)
            "image_id": img_path.stem,
        }


def collate_fn(batch: list[dict]) -> dict:
    return {
        "images":   torch.stack([b["image"] for b in batch], dim=0),
        "text_ids": torch.stack([b["text_ids"] for b in batch], dim=0),
        "boxes":    [b["boxes"] for b in batch],
        "labels":   [b["labels"] for b in batch],
        "image_ids": [b["image_id"] for b in batch],
    }


# ---------------------------------------------------------------------------
# 2. FCOS target assignment
# ---------------------------------------------------------------------------


def _grid_locations(H: int, W: int, stride: int, device) -> torch.Tensor:
    """Return (H*W, 2) tensor of (x, y) pixel locations at feature-pixel centers."""
    ys = torch.arange(H, device=device, dtype=torch.float32)
    xs = torch.arange(W, device=device, dtype=torch.float32)
    yy, xx = torch.meshgrid(ys, xs, indexing="ij")
    cx = (xx.reshape(-1) + 0.5) * stride
    cy = (yy.reshape(-1) + 0.5) * stride
    return torch.stack([cx, cy], dim=-1)        # (HW, 2)


def _assign_targets_one_image(
    gt_boxes: torch.Tensor,             # (G, 4) xyxy
    gt_labels: torch.Tensor,            # (G,)
    locations_per_level: list[torch.Tensor],   # each (HW_l, 2)
    strides: tuple[int, ...],
    regress_ranges: tuple[tuple[float, float], ...],
    num_classes: int,
    center_sample_radius: float = 1.5,
):
    """For one image, return cls_target / reg_target / ctr_target per level."""
    device = locations_per_level[0].device
    cls_t_levels: list[torch.Tensor] = []
    reg_t_levels: list[torch.Tensor] = []
    ctr_t_levels: list[torch.Tensor] = []

    G = int(gt_boxes.shape[0])
    if G == 0:
        # All-background masks
        for loc in locations_per_level:
            N = loc.shape[0]
            cls_t_levels.append(torch.full((N,), -1, dtype=torch.long, device=device))
            reg_t_levels.append(torch.zeros((N, 4), device=device))
            ctr_t_levels.append(torch.zeros((N,), device=device))
        return cls_t_levels, reg_t_levels, ctr_t_levels

    gt_areas = (gt_boxes[:, 2] - gt_boxes[:, 0]) * (gt_boxes[:, 3] - gt_boxes[:, 1])     # (G,)
    gt_cx = (gt_boxes[:, 0] + gt_boxes[:, 2]) * 0.5
    gt_cy = (gt_boxes[:, 1] + gt_boxes[:, 3]) * 0.5

    for level, loc in enumerate(locations_per_level):
        N = loc.shape[0]
        stride = strides[level]
        lo, hi = regress_ranges[level]
        x = loc[:, 0:1]                                                 # (N, 1)
        y = loc[:, 1:2]
        l = x - gt_boxes[:, 0]                                          # (N, G)
        t = y - gt_boxes[:, 1]
        r = gt_boxes[:, 2] - x
        b = gt_boxes[:, 3] - y
        ltrb = torch.stack([l, t, r, b], dim=-1)                        # (N, G, 4)

        inside_box = ltrb.min(dim=-1).values > 0                        # (N, G)

        # Center sampling: location must also be within radius * stride of GT center
        radius = center_sample_radius * stride
        cs_x0 = torch.clamp_min(gt_cx - radius, gt_boxes[:, 0])
        cs_y0 = torch.clamp_min(gt_cy - radius, gt_boxes[:, 1])
        cs_x1 = torch.clamp_max(gt_cx + radius, gt_boxes[:, 2])
        cs_y1 = torch.clamp_max(gt_cy + radius, gt_boxes[:, 3])
        cs_inside = (x >= cs_x0) & (x <= cs_x1) & (y >= cs_y0) & (y <= cs_y1)

        max_ltrb = ltrb.max(dim=-1).values                              # (N, G)
        in_range = (max_ltrb >= lo) & (max_ltrb < hi)                   # (N, G)

        valid = inside_box & cs_inside & in_range                       # (N, G)

        # Among valid GTs, pick the one with smallest area (FCOS heuristic).
        BIG = 1e10
        areas_exp = gt_areas[None, :].expand(N, G).clone()
        areas_exp[~valid] = BIG
        min_area, gt_idx = areas_exp.min(dim=1)                         # (N,) each
        is_pos = min_area < BIG

        cls_t = torch.full((N,), -1, dtype=torch.long, device=device)   # -1 = ignore/background
        cls_t[is_pos] = gt_labels[gt_idx[is_pos]]

        chosen_ltrb = ltrb[torch.arange(N, device=device), gt_idx]      # (N, 4)
        reg_t = chosen_ltrb / stride                                    # normalised by stride
        reg_t[~is_pos] = 0.0

        # Centerness target — only meaningful for positive locations
        if is_pos.any():
            l_, t_, r_, b_ = chosen_ltrb[is_pos].unbind(dim=-1)
            ctr_full = torch.zeros((N,), device=device)
            ctr = ((torch.minimum(l_, r_) / torch.maximum(l_, r_)) *
                   (torch.minimum(t_, b_) / torch.maximum(t_, b_))).clamp_min(0).sqrt()
            ctr_full[is_pos] = ctr
            ctr_t = ctr_full
        else:
            ctr_t = torch.zeros((N,), device=device)

        cls_t_levels.append(cls_t)
        reg_t_levels.append(reg_t)
        ctr_t_levels.append(ctr_t)

    return cls_t_levels, reg_t_levels, ctr_t_levels


# ---------------------------------------------------------------------------
# 3. Loss functions
# ---------------------------------------------------------------------------


def _sigmoid_focal_loss(
    logits: torch.Tensor, targets: torch.Tensor,
    alpha: float = 0.25, gamma: float = 2.0,
) -> torch.Tensor:
    """Multi-class focal loss on per-class binary outputs (FCOS / RetinaNet style).

    logits  : (M, K)
    targets : (M, K) one-hot (positives only)
    """
    p = logits.sigmoid()
    ce = F.binary_cross_entropy_with_logits(logits, targets, reduction="none")
    pt = p * targets + (1 - p) * (1 - targets)
    alpha_t = alpha * targets + (1 - alpha) * (1 - targets)
    loss = alpha_t * (1 - pt).pow(gamma) * ce
    return loss.sum()


def _giou_loss(pred_ltrb: torch.Tensor, target_ltrb: torch.Tensor) -> torch.Tensor:
    """Generalized IoU loss between two sets of (l, t, r, b) regressions.

    All values are in stride units; computed without converting to xyxy because
    GIoU on l/t/r/b distances is mathematically equivalent.
    """
    pl, pt, pr, pb = pred_ltrb.unbind(dim=-1)
    tl, tt, tr, tb = target_ltrb.unbind(dim=-1)

    pred_area = (pl + pr) * (pt + pb)
    target_area = (tl + tr) * (tt + tb)

    inter_w = torch.minimum(pl, tl) + torch.minimum(pr, tr)
    inter_h = torch.minimum(pt, tt) + torch.minimum(pb, tb)
    inter = inter_w.clamp_min(0) * inter_h.clamp_min(0)

    union = pred_area + target_area - inter + 1e-6
    iou = inter / union

    enclose_w = torch.maximum(pl, tl) + torch.maximum(pr, tr)
    enclose_h = torch.maximum(pt, tt) + torch.maximum(pb, tb)
    enclose = enclose_w.clamp_min(0) * enclose_h.clamp_min(0) + 1e-6
    giou = iou - (enclose - union) / enclose

    return (1 - giou).sum()


def fcos_loss(
    out: dict,
    gt_boxes: list[torch.Tensor],
    gt_labels: list[torch.Tensor],
    image_size: int,
    num_classes: int,
    cls_weight: float = 1.0,
    reg_weight: float = 1.0,
    ctr_weight: float = 1.0,
) -> dict:
    """Compute FCOS-style composite loss over a batch."""
    cls_outs = out["cls_logits"]                # list of (B, K, H, W)
    reg_outs = out["reg_dist"]                  # list of (B, 4, H, W)
    ctr_outs = out["centerness"]                # list of (B, 1, H, W)
    strides = out["fpn_strides"]
    device = cls_outs[0].device
    B = cls_outs[0].shape[0]

    # Precompute per-level location grids (shared across the batch).
    locations_per_level = [
        _grid_locations(c.shape[-2], c.shape[-1], strides[i], device)
        for i, c in enumerate(cls_outs)
    ]

    # Assign targets per image, then concatenate across images per level.
    cls_t_all = [[] for _ in cls_outs]
    reg_t_all = [[] for _ in cls_outs]
    ctr_t_all = [[] for _ in cls_outs]
    for b in range(B):
        c_lvls, r_lvls, k_lvls = _assign_targets_one_image(
            gt_boxes[b].to(device), gt_labels[b].to(device),
            locations_per_level, strides, REGRESS_RANGES, num_classes,
        )
        for i in range(len(cls_outs)):
            cls_t_all[i].append(c_lvls[i])
            reg_t_all[i].append(r_lvls[i])
            ctr_t_all[i].append(k_lvls[i])

    total_cls = total_reg = total_ctr = torch.zeros((), device=device)
    n_pos_total = 0
    for i in range(len(cls_outs)):
        cls_logits = cls_outs[i].permute(0, 2, 3, 1).reshape(-1, num_classes)
        reg_pred = reg_outs[i].permute(0, 2, 3, 1).reshape(-1, 4)
        ctr_pred = ctr_outs[i].permute(0, 2, 3, 1).reshape(-1)

        cls_t = torch.cat(cls_t_all[i])
        reg_t = torch.cat(reg_t_all[i])
        ctr_t = torch.cat(ctr_t_all[i])

        # Build one-hot targets for focal loss (positives only contribute).
        valid = cls_t >= 0
        cls_one_hot = torch.zeros_like(cls_logits)
        if valid.any():
            cls_one_hot[valid, cls_t[valid]] = 1.0
        total_cls = total_cls + _sigmoid_focal_loss(cls_logits, cls_one_hot)

        if valid.any():
            total_reg = total_reg + _giou_loss(reg_pred[valid], reg_t[valid])
            total_ctr = total_ctr + F.binary_cross_entropy_with_logits(
                ctr_pred[valid], ctr_t[valid], reduction="sum",
            )
            n_pos_total += int(valid.sum())

    n_pos = max(n_pos_total, 1)
    loss_cls = total_cls / n_pos
    loss_reg = total_reg / n_pos
    loss_ctr = total_ctr / n_pos
    loss = cls_weight * loss_cls + reg_weight * loss_reg + ctr_weight * loss_ctr
    return {
        "loss": loss,
        "loss_cls": loss_cls.detach(),
        "loss_reg": loss_reg.detach(),
        "loss_ctr": loss_ctr.detach(),
        "n_pos": n_pos,
    }


# ---------------------------------------------------------------------------
# 4. NMS + FROC eval (using TILLNet's predict() then matching to GT)
# ---------------------------------------------------------------------------


def _nms(boxes: torch.Tensor, scores: torch.Tensor, iou_thr: float = 0.5) -> torch.Tensor:
    """Class-agnostic NMS. Returns indices to keep, sorted by score."""
    if boxes.numel() == 0:
        return torch.zeros((0,), dtype=torch.long, device=boxes.device)
    order = scores.argsort(descending=True)
    keep = []
    while order.numel() > 0:
        i = order[0].item()
        keep.append(i)
        if order.numel() == 1:
            break
        rest = order[1:]
        xx0 = torch.maximum(boxes[i, 0], boxes[rest, 0])
        yy0 = torch.maximum(boxes[i, 1], boxes[rest, 1])
        xx1 = torch.minimum(boxes[i, 2], boxes[rest, 2])
        yy1 = torch.minimum(boxes[i, 3], boxes[rest, 3])
        iw = (xx1 - xx0).clamp_min(0)
        ih = (yy1 - yy0).clamp_min(0)
        inter = iw * ih
        a_i = (boxes[i, 2] - boxes[i, 0]) * (boxes[i, 3] - boxes[i, 1])
        a_r = (boxes[rest, 2] - boxes[rest, 0]) * (boxes[rest, 3] - boxes[rest, 1])
        iou = inter / (a_i + a_r - inter + 1e-6)
        order = rest[iou <= iou_thr]
    return torch.tensor(keep, dtype=torch.long, device=boxes.device)


@torch.no_grad()
def evaluate_froc_tillnet(
    model: TILLNetDet,
    loader: DataLoader,
    device,
    iou_thr_match: float = 0.3,
    nms_iou: float = 0.5,
    score_min: float = 0.01,
) -> dict:
    """Run model over loader and compute FROC + sensitivity@FP-rates."""
    model.eval()
    per_image: list[tuple[list[_PredHit], int]] = []
    n_images = 0
    for batch in loader:
        images = batch["images"].to(device)
        text_ids = batch["text_ids"].to(device)
        preds = model.predict(images, text_ids,
                              score_threshold=score_min, max_per_image=300)
        for i, p in enumerate(preds):
            n_images += 1
            keep = _nms(p["boxes"], p["scores"], iou_thr=nms_iou)
            boxes = p["boxes"][keep].cpu().numpy()
            scores = p["scores"][keep].cpu().numpy()
            preds_list = [
                (float(s), float(b[0]), float(b[1]), float(b[2]), float(b[3]))
                for s, b in zip(scores, boxes)
            ]
            gt_boxes = batch["boxes"][i].cpu().numpy()
            gt_labels = batch["labels"][i].cpu().numpy()
            gts = [(int(c), float(x0), float(y0), float(x1), float(y1))
                   for (x0, y0, x1, y1), c in zip(gt_boxes, gt_labels)]
            per_image.append(_match_image(preds_list, gts, iou_thr_match))

    curve = compute_froc(per_image, n_images=n_images)
    fp_targets = [0.5, 1.0, 2.0, 4.0]
    return {
        "n_images": n_images,
        "iou_threshold": iou_thr_match,
        "n_total_gt": sum(n for _, n in per_image),
        "sens_at_fp": {f"{t:g}": sensitivity_at_fp(curve, t) for t in fp_targets},
        "froc_curve": [{"score": p.score, "sensitivity": p.sensitivity,
                        "fp_per_image": p.fp_per_image} for p in curve],
    }


# ---------------------------------------------------------------------------
# 5. LR schedule (warmup + cosine)
# ---------------------------------------------------------------------------


def _make_scheduler(optimizer, total_steps: int, warmup_steps: int):
    def lr_lambda(step: int) -> float:
        if step < warmup_steps:
            return step / max(1, warmup_steps)
        prog = (step - warmup_steps) / max(1, total_steps - warmup_steps)
        return 0.5 * (1 + math.cos(math.pi * prog))
    return torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda)


# ---------------------------------------------------------------------------
# 6. CLI
# ---------------------------------------------------------------------------


def _load_texts(path: Path | None) -> dict[str, str]:
    if path is None:
        return {}
    p = Path(path)
    if not p.exists():
        return {}
    out: dict[str, str] = {}
    if p.suffix.lower() == ".jsonl":
        for line in p.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            fn = r.get("filename") or r.get("image") or r.get("file")
            if fn:
                out[Path(fn).name] = r.get("text", "") or ""
    else:
        import csv as _csv
        with p.open("r", encoding="utf-8", newline="") as f:
            for r in _csv.DictReader(f):
                fn = r.get("filename") or r.get("image") or r.get("file")
                if fn:
                    out[Path(fn).name] = r.get("text", "") or ""
    return out


def _resolve_split_dirs(data_yaml: Path):
    import yaml as _yaml
    cfg = _yaml.safe_load(data_yaml.read_text(encoding="utf-8"))
    root = Path(cfg.get("path", data_yaml.parent)).resolve()

    def split_dirs(name: str):
        rel = cfg.get(name, f"images/{name}")
        img = (root / rel).resolve()
        lbl = Path(str(img).replace("/images/", "/labels/").replace("\\images\\", "\\labels\\"))
        return img, lbl

    return cfg, root, split_dirs


def main():
    ap = argparse.ArgumentParser(description="TILLNet-Det multimodal detector trainer")
    ap.add_argument("--data", required=True)
    ap.add_argument("--texts", default=None,
                    help="CSV or JSONL with 'filename,text' columns (filename = image basename)")
    ap.add_argument("--epochs", type=int, default=60)
    ap.add_argument("--imgsz", type=int, default=1024)
    ap.add_argument("--batch", type=int, default=2)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--weight-decay", type=float, default=5e-4)
    ap.add_argument("--warmup-epochs", type=float, default=2.0)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--out", default="runs/tillnet")
    ap.add_argument("--no-text", action="store_true",
                    help="Image-only ablation (drops text branch entirely)")
    ap.add_argument("--no-pretrained", action="store_true",
                    help="Train backbone from scratch")
    ap.add_argument("--clip-grad", type=float, default=10.0)
    ap.add_argument("--eval-every", type=int, default=2,
                    help="Run FROC validation every N epochs")
    ap.add_argument("--num-classes", type=int, default=2,
                    help="Must match dataset.yaml's nc")
    ap.add_argument("--resume", default=None,
                    help="Path to .pt checkpoint to resume training")
    args = ap.parse_args()

    data_yaml = Path(args.data).resolve()
    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    device = torch.device(args.device)

    cfg, root, split_dirs = _resolve_split_dirs(data_yaml)
    nc = int(cfg.get("nc", args.num_classes))
    if nc != args.num_classes:
        print(f"[warn] dataset.yaml nc={nc} differs from --num-classes={args.num_classes}; using {nc}")
    args.num_classes = nc

    train_img, train_lbl = split_dirs("train")
    val_img, val_lbl = split_dirs("val")
    texts = _load_texts(Path(args.texts) if args.texts else None)
    print(f"[data] train={train_img}  val={val_img}  texts={len(texts)} entries")

    train_ds = MammoDetTextDataset(train_img, train_lbl, texts, args.imgsz, augment=True)
    val_ds = MammoDetTextDataset(val_img, val_lbl, texts, args.imgsz, augment=False)
    train_loader = DataLoader(train_ds, batch_size=args.batch, shuffle=True,
                              num_workers=args.workers, collate_fn=collate_fn, drop_last=True)
    val_loader = DataLoader(val_ds, batch_size=max(1, args.batch),
                            shuffle=False, num_workers=args.workers, collate_fn=collate_fn)

    cfg_m = TILLNetConfig(
        num_classes=args.num_classes,
        pretrained_backbone=not args.no_pretrained,
        use_text=not args.no_text,
    )
    model = TILLNetDet(cfg_m).to(device)

    start_epoch = 0
    best_sens_at_1 = 0.0
    if args.resume:
        ckpt = torch.load(args.resume, map_location=device)
        model.load_state_dict(ckpt["model"])
        start_epoch = ckpt.get("epoch", 0) + 1
        best_sens_at_1 = ckpt.get("best_sens_at_1", 0.0)
        print(f"[resume] from epoch {start_epoch}, best sens@1FP = {best_sens_at_1:.4f}")

    optim = torch.optim.AdamW(
        model.parameters(), lr=args.lr, weight_decay=args.weight_decay,
        betas=(0.9, 0.999),
    )
    steps_per_epoch = max(1, len(train_loader))
    total_steps = steps_per_epoch * args.epochs
    warmup_steps = int(steps_per_epoch * args.warmup_epochs)
    scheduler = _make_scheduler(optim, total_steps, warmup_steps)

    print(f"[model] params = {sum(p.numel() for p in model.parameters() if p.requires_grad)/1e6:.2f}M  "
          f"text_branch={cfg_m.use_text}  pretrained_backbone={cfg_m.pretrained_backbone}")
    print(f"[train] epochs={args.epochs}  batch={args.batch}  imgsz={args.imgsz}  "
          f"lr={args.lr}  steps/epoch={steps_per_epoch}  device={device}")

    history = []
    for epoch in range(start_epoch, args.epochs):
        model.train()
        ep_t0 = time.time()
        running = {"loss": 0.0, "cls": 0.0, "reg": 0.0, "ctr": 0.0}
        n_batches = 0
        for batch in train_loader:
            images = batch["images"].to(device, non_blocking=True)
            text_ids = batch["text_ids"].to(device, non_blocking=True)
            out = model(images, text_ids if cfg_m.use_text else None)
            losses = fcos_loss(
                out, batch["boxes"], batch["labels"],
                image_size=args.imgsz, num_classes=args.num_classes,
            )
            loss = losses["loss"]
            optim.zero_grad(set_to_none=True)
            loss.backward()
            if args.clip_grad > 0:
                nn.utils.clip_grad_norm_(model.parameters(), args.clip_grad)
            optim.step()
            scheduler.step()
            running["loss"] += float(loss.detach())
            running["cls"] += float(losses["loss_cls"])
            running["reg"] += float(losses["loss_reg"])
            running["ctr"] += float(losses["loss_ctr"])
            n_batches += 1

        avg = {k: v / max(1, n_batches) for k, v in running.items()}
        ep_dt = time.time() - ep_t0
        print(f"[ep {epoch+1:3d}/{args.epochs}] "
              f"loss={avg['loss']:.4f} cls={avg['cls']:.4f} "
              f"reg={avg['reg']:.4f} ctr={avg['ctr']:.4f}  "
              f"({ep_dt:.1f}s, lr={scheduler.get_last_lr()[0]:.2e})")

        do_eval = ((epoch + 1) % args.eval_every == 0) or (epoch + 1 == args.epochs)
        if do_eval and len(val_ds) > 0:
            summary = evaluate_froc_tillnet(model, val_loader, device)
            sens1 = summary["sens_at_fp"].get("1", 0.0)
            print(f"           val FROC: sens@1FP={sens1:.4f}  "
                  f"sens@2FP={summary['sens_at_fp'].get('2',0.0):.4f}  "
                  f"({summary['n_images']} imgs, {summary['n_total_gt']} GTs)")
            history.append({"epoch": epoch + 1, "train": avg, "val": summary})
            (out_dir / "history.jsonl").write_text(
                "\n".join(json.dumps(h, ensure_ascii=False) for h in history),
                encoding="utf-8",
            )
            if sens1 > best_sens_at_1:
                best_sens_at_1 = sens1
                torch.save({
                    "model": model.state_dict(),
                    "epoch": epoch,
                    "best_sens_at_1": best_sens_at_1,
                    "config": cfg_m.__dict__,
                }, out_dir / "best.pt")
                plot_froc(summary, out_dir / "best_froc.png")
                print(f"           [save] new best  best.pt  sens@1FP={best_sens_at_1:.4f}")

        # Always keep the most recent weights for resume.
        torch.save({
            "model": model.state_dict(),
            "epoch": epoch,
            "best_sens_at_1": best_sens_at_1,
            "config": cfg_m.__dict__,
        }, out_dir / "last.pt")

    print(f"\n[done] best sens@1FP = {best_sens_at_1:.4f}")
    print(f"[saved] {out_dir / 'best.pt'}")
    print(f"[saved] {out_dir / 'history.jsonl'}")


if __name__ == "__main__":
    main()
