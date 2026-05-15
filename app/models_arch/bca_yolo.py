"""
BCA-YOLO: Bilateral Cross-Attention YOLO for Mammographic Lesion Detection.

Reference implementation accompanying the methods paper.

Architecture overview
---------------------
Input:  Four co-registered mammographic views per study,
        x_v ∈ R^{1×H×W}, v ∈ {L_CC, R_CC, L_MLO, R_MLO}.

Components:
  1. Shared YOLO backbone Φ produces multi-scale features F_v.
  2. Bilateral Cross-Attention (BCA) at scale s pairs (L_p, R_p) for
     each projection p ∈ {CC, MLO} and produces asymmetry-aware features.
  3. Inter-View Consistency (IVC) module fuses {CC, MLO} for each side.
  4. Detection heads (per-view + fused-side auxiliary).
  5. Ordinal BI-RADS regression head with cumulative link.

This module focuses on the BCA + IVC + ordinal head — the YOLO backbone
and detection heads are intentionally factored out so any Ultralytics
backbone can be swapped in.
"""
from __future__ import annotations

from dataclasses import dataclass

import torch
import torch.nn as nn
import torch.nn.functional as F


# ---------------------------------------------------------------------------
# 1. Bilateral Cross-Attention (BCA)
# ---------------------------------------------------------------------------


class BilateralCrossAttention(nn.Module):
    r"""Cross-attention between left/right contralateral feature maps.

    Given F_L, F_R ∈ R^{B×C×H×W} for the same projection p, this module
    horizontally mirrors F_R (so that anatomical regions are aligned) and
    computes:

        Q_L = W_q F_L
        K_R = W_k mirror(F_R)
        V_R = W_v mirror(F_R)
        A_LR = softmax(Q_L K_R^T / sqrt(d_k))
        F'_L = F_L + γ · A_LR V_R

    Symmetrically, F'_R is updated using F_L. The learnable γ initialises
    to a small value so the module starts as identity (which preserves
    pre-trained backbone behaviour) and learns to attend to asymmetric
    regions only when this reduces the loss.
    """

    def __init__(self, channels: int, num_heads: int = 4, dropout: float = 0.0):
        super().__init__()
        if channels % num_heads != 0:
            raise ValueError("channels must be divisible by num_heads")
        self.channels = channels
        self.num_heads = num_heads
        self.head_dim = channels // num_heads
        self.scale = self.head_dim ** -0.5

        self.qkv_l = nn.Conv2d(channels, channels * 3, kernel_size=1, bias=False)
        self.qkv_r = nn.Conv2d(channels, channels * 3, kernel_size=1, bias=False)
        self.proj_l = nn.Conv2d(channels, channels, kernel_size=1)
        self.proj_r = nn.Conv2d(channels, channels, kernel_size=1)
        self.gamma = nn.Parameter(torch.zeros(1))
        self.drop = nn.Dropout(dropout)

    @staticmethod
    def mirror(x: torch.Tensor) -> torch.Tensor:
        return torch.flip(x, dims=[-1])

    def _attend(self, qkv_a: torch.Tensor, qkv_b_mirrored: torch.Tensor):
        B, C3, H, W = qkv_a.shape
        C = C3 // 3
        qkv_a = qkv_a.view(B, 3, self.num_heads, self.head_dim, H * W)
        qkv_b = qkv_b_mirrored.view(B, 3, self.num_heads, self.head_dim, H * W)
        Q = qkv_a[:, 0]
        K = qkv_b[:, 1]
        V = qkv_b[:, 2]
        attn = torch.einsum("bhdn,bhdm->bhnm", Q, K) * self.scale
        attn = attn.softmax(dim=-1)
        attn = self.drop(attn)
        out = torch.einsum("bhnm,bhdm->bhdn", attn, V)
        out = out.reshape(B, C, H, W)
        return out, attn

    def forward(self, F_L: torch.Tensor, F_R: torch.Tensor):
        F_R_m = self.mirror(F_R)
        qkv_l = self.qkv_l(F_L)
        qkv_r_m = self.qkv_r(F_R_m)

        out_l, attn_lr = self._attend(qkv_l, qkv_r_m)
        out_l = self.proj_l(out_l)

        F_L_m = self.mirror(F_L)
        qkv_l_m = self.qkv_l(F_L_m)
        out_r, attn_rl = self._attend(qkv_r_m, qkv_l_m)
        out_r = self.mirror(self.proj_r(out_r))

        Fp_L = F_L + self.gamma * out_l
        Fp_R = F_R + self.gamma * out_r
        return Fp_L, Fp_R, {"attn_lr": attn_lr, "attn_rl": attn_rl}


# ---------------------------------------------------------------------------
# 2. Inter-View Consistency (IVC) fusion
# ---------------------------------------------------------------------------


class InterViewConsistency(nn.Module):
    r"""Channel-wise gated fusion of CC and MLO views for the same side.

    F_fused = σ(W_g [F_CC ; F_MLO]) ⊙ F_CC + (1 - σ(...)) ⊙ F_MLO

    The learnable gate σ(·) ∈ (0, 1) is a per-channel sigmoid produced by a
    1×1 convolution over the concatenated features. The fused feature is
    used by an auxiliary detection head; the per-view heads also receive
    a consistency penalty during training.
    """

    def __init__(self, channels: int):
        super().__init__()
        self.gate = nn.Conv2d(channels * 2, channels, kernel_size=1)

    def forward(self, F_cc: torch.Tensor, F_mlo: torch.Tensor):
        if F_cc.shape != F_mlo.shape:
            F_mlo = F.interpolate(F_mlo, size=F_cc.shape[-2:], mode="bilinear",
                                   align_corners=False)
        cat = torch.cat([F_cc, F_mlo], dim=1)
        g = torch.sigmoid(self.gate(cat))
        return g * F_cc + (1.0 - g) * F_mlo


# ---------------------------------------------------------------------------
# 3. Ordinal BI-RADS regression head (cumulative link)
# ---------------------------------------------------------------------------


class OrdinalBIRADSHead(nn.Module):
    r"""Cumulative-link ordinal regression for BI-RADS 0-6.

    Standard cross-entropy treats BI-RADS 1↔2 the same as 1↔5; for an
    ordinal label this loses information.  Following McCullagh (1980) we
    model:

        P(y ≤ k | x) = σ(θ_k - f(x)),   k = 0, 1, ..., K-1
        P(y = k | x) = P(y ≤ k | x) - P(y ≤ k-1 | x)

    The thresholds θ_0 < θ_1 < ... < θ_{K-1} are learnt as a strictly
    increasing sequence by parameterising successive gaps as
        θ_0 = α_0,  θ_k = θ_{k-1} + softplus(α_k).
    """

    def __init__(self, in_features: int, num_classes: int = 7):
        super().__init__()
        self.num_classes = num_classes
        self.f = nn.Linear(in_features, 1)
        self.alpha = nn.Parameter(torch.zeros(num_classes - 1))

    def thresholds(self) -> torch.Tensor:
        gaps = F.softplus(self.alpha[1:])
        theta = torch.cat([self.alpha[:1], self.alpha[:1] + torch.cumsum(gaps, 0)])
        return theta

    def forward(self, h: torch.Tensor) -> torch.Tensor:
        score = self.f(h).squeeze(-1)
        theta = self.thresholds()
        cdf = torch.sigmoid(theta.unsqueeze(0) - score.unsqueeze(-1))
        zeros = torch.zeros_like(cdf[..., :1])
        ones = torch.ones_like(cdf[..., :1])
        cdf = torch.cat([zeros, cdf, ones], dim=-1)
        pmf = cdf[..., 1:] - cdf[..., :-1]
        pmf = pmf.clamp(min=1e-8)
        return pmf


# ---------------------------------------------------------------------------
# 4. Loss functions
# ---------------------------------------------------------------------------


def bca_attention_loss(
    attn_lr: torch.Tensor,
    bbox_target_l: torch.Tensor,
    eps: float = 1e-6,
) -> torch.Tensor:
    r"""Encourage attention from L to mirrored-R to peak at lesion locations.

    L_bca = - mean over lesion pixels p of log( pooled_attn(p) + eps )

    `bbox_target_l` is a binary map (B, 1, H, W) marking lesion pixels in
    the left view; `attn_lr` is (B, num_heads, N, N) where N = H*W.  We
    average over heads and reduce to a (B, H, W) attention-on-self map.
    """
    B, Hh, N, _ = attn_lr.shape
    attn_avg = attn_lr.mean(dim=1)
    attn_diag = attn_avg.diagonal(dim1=-2, dim2=-1)
    H = bbox_target_l.shape[-2]
    W = bbox_target_l.shape[-1]
    attn_map = attn_diag.view(B, H, W)
    target = bbox_target_l.squeeze(1).clamp(0, 1)
    masked = -(target * torch.log(attn_map + eps)).sum(dim=(1, 2))
    norm = target.sum(dim=(1, 2)).clamp(min=1.0)
    return (masked / norm).mean()


def ivc_consistency_loss(
    obj_cc: torch.Tensor,
    obj_mlo: torch.Tensor,
) -> torch.Tensor:
    r"""Smoothness penalty between objectness on CC and MLO views.

    L_ivc = || pool(obj_cc) - pool(obj_mlo) ||_2^2

    Both maps are global-average-pooled per detection scale to remove
    spatial misalignment that a learnable loss should not need to handle.
    """
    p_cc = obj_cc.mean(dim=(-2, -1))
    p_mlo = obj_mlo.mean(dim=(-2, -1))
    return F.mse_loss(p_cc, p_mlo)


def ordinal_birads_loss(
    pmf: torch.Tensor,
    target: torch.Tensor,
) -> torch.Tensor:
    r"""Cumulative-link ordinal cross-entropy.

    L_ord = - mean log p(y_target | x)
          + λ_mono * Σ_k max(0, p_{k} - p_{k+1}) on tail
    """
    nll = -torch.log(pmf.gather(-1, target.long().unsqueeze(-1)).squeeze(-1)
                     .clamp(min=1e-8))
    return nll.mean()


# ---------------------------------------------------------------------------
# 5. Top-level orchestrator (skeleton)
# ---------------------------------------------------------------------------


@dataclass
class BCAYOLOConfig:
    backbone_channels: tuple[int, int, int] = (256, 512, 1024)
    num_classes: int = 4
    num_birads: int = 7
    bca_heads: int = 4
    lambda_bca: float = 0.3
    lambda_ivc: float = 0.1
    lambda_ord: float = 0.5


class BCAYoloHead(nn.Module):
    """Container module wiring BCA + IVC at three feature scales.

    The actual YOLO detection / box-regression layers are intentionally
    abstracted to `_make_det_head` so any Ultralytics-style head can be
    plugged in (this preserves training compatibility with the broader
    YOLOv8/v11 ecosystem).
    """

    def __init__(self, cfg: BCAYOLOConfig | None = None):
        super().__init__()
        cfg = cfg or BCAYOLOConfig()
        self.cfg = cfg
        self.bca = nn.ModuleList(
            [BilateralCrossAttention(c, num_heads=cfg.bca_heads)
             for c in cfg.backbone_channels]
        )
        self.ivc = nn.ModuleList(
            [InterViewConsistency(c) for c in cfg.backbone_channels]
        )
        self.det_per_view = nn.ModuleList(
            [self._make_det_head(c, cfg.num_classes) for c in cfg.backbone_channels]
        )
        self.det_fused = nn.ModuleList(
            [self._make_det_head(c, cfg.num_classes) for c in cfg.backbone_channels]
        )
        self.gap = nn.AdaptiveAvgPool2d(1)
        self.birads = OrdinalBIRADSHead(
            in_features=sum(cfg.backbone_channels), num_classes=cfg.num_birads,
        )

    def _make_det_head(self, channels: int, num_classes: int) -> nn.Module:
        return nn.Sequential(
            nn.Conv2d(channels, channels, kernel_size=3, padding=1),
            nn.SiLU(),
            nn.Conv2d(channels, num_classes + 5, kernel_size=1),
        )

    def forward(
        self,
        feats: dict[str, list[torch.Tensor]],
    ) -> dict:
        """feats: {view_name: [F_s1, F_s2, F_s3]} where view_name is one of
        L_CC, R_CC, L_MLO, R_MLO. Each tensor (B, C_s, H_s, W_s).
        """
        keys = ["L_CC", "R_CC", "L_MLO", "R_MLO"]
        for k in keys:
            assert k in feats, f"missing view {k}"

        per_view_dets: dict[str, list[torch.Tensor]] = {k: [] for k in keys}
        fused_dets: dict[str, list[torch.Tensor]] = {"L": [], "R": []}
        attn_maps: list[dict] = []

        for s, (bca_s, ivc_s, det_pv, det_f) in enumerate(
            zip(self.bca, self.ivc, self.det_per_view, self.det_fused)
        ):
            FL_cc, FR_cc, attn_cc = bca_s(feats["L_CC"][s], feats["R_CC"][s])
            FL_mlo, FR_mlo, attn_mlo = bca_s(feats["L_MLO"][s], feats["R_MLO"][s])
            attn_maps.append({"CC": attn_cc, "MLO": attn_mlo})

            for k, F_v in zip(["L_CC", "R_CC", "L_MLO", "R_MLO"],
                              [FL_cc, FR_cc, FL_mlo, FR_mlo]):
                per_view_dets[k].append(det_pv(F_v))

            FL_fused = ivc_s(FL_cc, FL_mlo)
            FR_fused = ivc_s(FR_cc, FR_mlo)
            fused_dets["L"].append(det_f(FL_fused))
            fused_dets["R"].append(det_f(FR_fused))

        h = []
        for s in range(len(self.cfg.backbone_channels)):
            for k in keys:
                h.append(self.gap(feats[k][s]).flatten(1))
        h = torch.cat(h, dim=-1)
        h = h.view(h.size(0), 4, -1).mean(dim=1)
        birads_pmf = self.birads(h)

        return {
            "per_view": per_view_dets,
            "fused": fused_dets,
            "birads": birads_pmf,
            "attn": attn_maps,
        }


def total_loss(
    out: dict,
    targets: dict,
    cfg: BCAYOLOConfig,
    yolo_loss_fn,
) -> dict[str, torch.Tensor]:
    L_yolo = sum(
        yolo_loss_fn(out["per_view"][k], targets["per_view"][k])
        for k in out["per_view"]
    )

    L_bca = torch.zeros((), device=L_yolo.device)
    for s_idx, attn_s in enumerate(out["attn"]):
        for proj in ("CC", "MLO"):
            attn = attn_s[proj]
            target_l = targets["bbox_mask"][f"L_{proj}"][s_idx]
            L_bca = L_bca + bca_attention_loss(attn["attn_lr"], target_l)
            target_r = targets["bbox_mask"][f"R_{proj}"][s_idx]
            L_bca = L_bca + bca_attention_loss(attn["attn_rl"], target_r)
    L_bca = L_bca / (2 * 2 * len(out["attn"]))

    L_ivc = torch.zeros((), device=L_yolo.device)
    for s_idx in range(len(out["per_view"]["L_CC"])):
        for side in ("L", "R"):
            cc = out["per_view"][f"{side}_CC"][s_idx][:, 4:5]
            mlo = out["per_view"][f"{side}_MLO"][s_idx][:, 4:5]
            L_ivc = L_ivc + ivc_consistency_loss(cc, mlo)
    L_ivc = L_ivc / (2 * len(out["per_view"]["L_CC"]))

    L_ord = ordinal_birads_loss(out["birads"], targets["birads"])

    L_total = L_yolo + cfg.lambda_bca * L_bca + cfg.lambda_ivc * L_ivc + cfg.lambda_ord * L_ord
    return {
        "total": L_total, "yolo": L_yolo,
        "bca": L_bca, "ivc": L_ivc, "ord": L_ord,
    }


def parameter_count(module: nn.Module) -> int:
    return sum(p.numel() for p in module.parameters() if p.requires_grad)


if __name__ == "__main__":
    import time
    cfg = BCAYOLOConfig()
    head = BCAYoloHead(cfg)
    print(f"BCA-YOLO head parameters: {parameter_count(head):,}")

    B, scales = 2, [(256, 80, 80), (512, 40, 40), (1024, 20, 20)]
    feats = {
        v: [torch.randn(B, c, h, w) for (c, h, w) in scales]
        for v in ["L_CC", "R_CC", "L_MLO", "R_MLO"]
    }
    head.eval()
    with torch.no_grad():
        t0 = time.perf_counter()
        for _ in range(5):
            out = head(feats)
        elapsed = (time.perf_counter() - t0) / 5
    print(f"forward latency (CPU, B={B}): {elapsed*1000:.1f} ms")
    print(f"per_view scales: {[d.shape for d in out['per_view']['L_CC']]}")
    print(f"fused scales:    {[d.shape for d in out['fused']['L']]}")
    print(f"birads pmf:      {out['birads'].shape}, sum={out['birads'].sum(-1)}")
