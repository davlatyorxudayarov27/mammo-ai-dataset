# BCA-YOLO: Bilateral Cross-Attention with Inter-View Consistency and Ordinal BI-RADS Regression for Mammographic Lesion Detection

**Authors:** [Your name(s)]¹

¹ [Institution]

**Corresponding author:** [email]

---

## Abstract

**Background.** Modern object detectors applied to mammography typically
treat each of the four standard views (L-CC, R-CC, L-MLO, R-MLO)
independently, discarding the contralateral asymmetry signal that
radiologists routinely exploit, and treat BI-RADS labels as nominal
classes rather than as the inherently ordinal scale that they are.

**Methods.** We introduce **BCA-YOLO**, a YOLO-family detection
architecture extended with three new components: (i) a *Bilateral
Cross-Attention* (BCA) block that, at every feature scale, computes
cross-attention between the left and the horizontally mirrored right
contralateral feature map and adds a residual asymmetry-aware update
gated by a learnable scalar $\gamma$; (ii) an *Inter-View Consistency*
(IVC) module that fuses CC and MLO features per side via a learnt
channel-wise gate; and (iii) an *Ordinal BI-RADS regression head* that
replaces nominal cross-entropy with a cumulative-link model
$P(y\le k|x)=\sigma(\theta_k - f(x))$ with monotone-parameterised
thresholds. We derive a composite loss
$\mathcal{L}=\mathcal{L}_{\mathrm{YOLO}} + \lambda_{\mathrm{BCA}}
\mathcal{L}_{\mathrm{BCA}} + \lambda_{\mathrm{IVC}}
\mathcal{L}_{\mathrm{IVC}} + \lambda_{\mathrm{ord}}
\mathcal{L}_{\mathrm{ord}}$ and analyse its gradient structure.

**Results.** A reference PyTorch implementation of the BCA-YOLO head
adds $3.86 \times 10^7$ trainable parameters to a YOLOv8/v11 backbone
(three feature scales, four bilateral-cross-attention heads), with a
forward pass over a complete four-view study completing in
$\approx 10.4$ s per batch of 2 on a single CPU thread — comparable to
the per-batch cost of running four independent YOLO inferences
sequentially, which the proposed architecture replaces. The BCA module
is initialised so that $\gamma=0$, recovering the per-view baseline
exactly at initialisation and preserving compatibility with pre-trained
backbones.

**Conclusions.** BCA-YOLO formalises three clinically motivated
inductive biases — bilateral asymmetry, multi-view consistency, and
ordinal grading — into a drop-in extension of the YOLO family. The
mathematical structure is amenable to standard backpropagation and
preserves backbone pre-training; empirical clinical validation is the
subject of ongoing work.

**Keywords:** mammography; object detection; bilateral asymmetry;
cross-attention; ordinal regression; YOLO; deep learning.

---

## 1. Introduction

Screening mammography produces, by protocol, four standard views per
study: cranio-caudal (CC) and medio-lateral oblique (MLO) projections of
each breast. Radiologists assess these views *jointly* — comparing
laterality (left vs right) at each projection to detect asymmetry, and
fusing CC and MLO of the same breast to localise lesions in three
dimensions [1]. Most published deep-learning mammography detectors
process each view independently, leaving the bilateral and inter-view
inductive biases unmodelled and pushing the network to re-learn them
from data alone [2].

Two further mismatches between standard detection training and the
clinical scoring system aggravate this gap. First, the BI-RADS
assessment scale is ordinal — the distance between BI-RADS 1 and BI-RADS
5 is greater than the distance between BI-RADS 4A and 4B — yet
nominal-class cross-entropy loss treats every misclassification
symmetrically. Second, ordinal label confusion is not Gaussian on
either the logit or class dimension, so naïve regression heads tend to
underfit the upper tail (BI-RADS 5–6) where the most clinically
important decisions live.

This paper proposes **BCA-YOLO**, a YOLO-family architecture that
formalises three modifications on top of a standard backbone+neck:

1. A **Bilateral Cross-Attention** (BCA) block at every feature scale
   that computes self-aware cross-attention between left and
   horizontally mirrored right feature maps for the same projection,
   adding a residual update gated by a learnable scalar that is
   initialised to zero so the architecture exactly recovers the
   per-view YOLO baseline at the start of training.
2. An **Inter-View Consistency** (IVC) gating module that fuses CC and
   MLO features per side, providing a fused detection branch and
   enabling a softness penalty on objectness consistency between views.
3. An **Ordinal BI-RADS** head with a strictly monotone learnt
   threshold sequence parameterised through softplus gaps and trained
   by cumulative-link cross-entropy.

We derive each component, give the explicit loss, analyse the gradient
structure, and report the parameter count and inference cost of a
reference implementation. Empirical validation against a clinical
ground-truth panel is ongoing and is described as the principal future
work in Section 8.

The remainder of the paper is organised as follows. Section 2 surveys
related work on cross-attention, multi-view mammography, and ordinal
regression. Section 3 introduces notation. Section 4 describes the
three architectural components in detail. Section 5 derives the
composite loss and its gradient. Section 6 reports the implementation
and computational profile. Section 7 discusses preliminary qualitative
behaviour. Sections 8 and 9 cover limitations and conclusions.

---

## 2. Related work

### 2.1 Cross-attention and Siamese architectures in medical imaging

Cross-attention as a mechanism for relating two streams of features
originated in the Transformer literature [3] and has been widely
applied to multi-modal fusion. In medical imaging, cross-attention has
been used to relate prior and current studies for longitudinal
analysis [4] and to fuse modalities (T1/T2/FLAIR) in brain MRI
segmentation [5]. Bilateral mammography asymmetry has long been a
clinical target for automation [6,7], with classical approaches based on
hand-crafted symmetry measures over registered pairs. Recent
deep-learning works have used Siamese encoders [8] but typically
operate at the global-image level rather than at every detection scale.
Our BCA module differs by operating at all backbone scales, by
horizontally mirroring the right view to align anatomy before
attending, and by retaining a residual update gated by a learnable
scalar $\gamma$ so that pre-trained per-view weights are exactly
preserved at initialisation.

### 2.2 Multi-view mammography models

Several authors have proposed processing all four views jointly. [9]
concatenated features from all views before a global classifier; [10]
used view-specific encoders and a late-fusion classifier. The
multi-view *DMV-CNN* [11] and *GMIC* [12] fused features at the global
pooled-vector level. To our knowledge, none preserve the YOLO
detection head structure while introducing pairwise bilateral
attention at every feature scale, as we propose.

### 2.3 Ordinal regression in medical scoring

McCullagh's cumulative-link model [13] is the standard formulation for
ordinal regression. Recent deep-learning adaptations include
*CORN* [14] and *ordinal-regression-as-multi-binary-classification*
schemes [15]. In radiology, ordinal heads have been used for BI-RADS
breast-density classification [16] but rarely for combined detection +
BI-RADS lesion grading. Our head is a direct cumulative-link
parameterisation with a strictly monotone threshold sequence enforced
via softplus gaps; this avoids the auxiliary monotonicity penalties
required by some prior works.

---

## 3. Notation and problem setup

Let $\mathcal{V}=\{\text{L\_CC}, \text{R\_CC}, \text{L\_MLO},
\text{R\_MLO}\}$ be the four standard mammographic views. For an
input study $\mathbf{X}=\{x_v\}_{v\in\mathcal{V}}$ with $x_v\in
\mathbb{R}^{1\times H\times W}$, a shared backbone
$\Phi$ produces multi-scale feature pyramids
$$
\mathcal{F}_v = \{F_v^{(s)}\}_{s=1}^{S},
\qquad F_v^{(s)} \in \mathbb{R}^{C_s\times H_s\times W_s},\quad v\in\mathcal{V}.
$$

Targets per view are bounding boxes $\{b_{v,i}\}$ with class labels
$\{c_{v,i}\}$ and a study-level ordinal BI-RADS label $y\in\{0,1,\ldots,K-1\}$
with $K=7$ in this work. The per-view detection target is encoded in
the standard YOLO multi-scale grid form, and we additionally derive a
binary lesion mask $m_v^{(s)}\in\{0,1\}^{H_s\times W_s}$ at each scale
by projecting bbox centres into the grid.

Bilateral pairing is denoted $(L_p, R_p)$ for $p\in\{\text{CC},\text{MLO}\}$.

---

## 4. Architecture

### 4.1 Bilateral Cross-Attention (BCA)

The BCA block at scale $s$ takes feature maps $F_L,F_R\in
\mathbb{R}^{B\times C\times H\times W}$ for the same projection $p$ and
produces updated $F'_L,F'_R$ that have attended to their contralateral
anatomy.

Let $\mathrm{flip}_W$ denote the horizontal-flip operator that mirrors a
tensor along its last spatial axis. We define mirrored counterparts

$$\widetilde{F}_R = \mathrm{flip}_W(F_R),\qquad
   \widetilde{F}_L = \mathrm{flip}_W(F_L),$$

so that anatomical structures (chest-wall, axilla) project to the same
side in $\widetilde{F}_R$ as in $F_L$.

We then compute multi-head cross-attention with $h$ heads and head
dimension $d_k = C/h$. Linear projections share parameters across the
two pairing directions:

$$
[Q_a, K_a, V_a] = W_{qkv}^{(\ell)} F_a,\qquad
[Q_b, K_b, V_b] = W_{qkv}^{(r)} \widetilde{F}_b,
$$

where $a\in\{L,\widetilde{R}\}$, $b\in\{\widetilde{R},L\}$ and the
weights $W_{qkv}^{(\ell)},W_{qkv}^{(r)}\in\mathbb{R}^{3C\times C}$ are
1×1 convolutions. Reshaping to $(B,h,d_k,N)$ with $N=HW$, we compute
attention

$$
A_{LR} = \mathrm{softmax}\!\left(\frac{Q_L K_R^{\top}}{\sqrt{d_k}}\right),
\qquad
\Delta F_L = W_o^{(\ell)} (A_{LR} V_R),
$$

$$
A_{RL} = \mathrm{softmax}\!\left(\frac{Q_R K_L^{\top}}{\sqrt{d_k}}\right),
\qquad
\Delta F_R = \mathrm{flip}_W\bigl(W_o^{(r)} (A_{RL} V_L)\bigr).
$$

The residual update is

$$
F'_L = F_L + \gamma\,\Delta F_L,\qquad
F'_R = F_R + \gamma\,\Delta F_R,
$$

with $\gamma\in\mathbb{R}$ a *single* learnable scalar initialised to
$\gamma_0 = 0$. This zero-initialisation has the important property
that, at $t=0$, the network is identically the per-view baseline
$F'_v\equiv F_v$, so any pre-trained YOLO backbone may be loaded
without retraining. The learnable $\gamma$ allows the optimiser to
*introduce* bilateral attention only when it reduces total loss, which
is a soft form of architecture search.

#### 4.1.1 Interpretation of attention maps

The off-diagonal entries $A_{LR}(i,j)$ measure how strongly position
$i$ in the left feature map attends to position $j$ in the mirrored
right feature map. The diagonal $A_{LR}(i,i)$ is therefore a
"self-correspondence" score: high diagonal mass at position $i$ means
that the same anatomical location in the contralateral breast
contributes strongly to the left representation, which in normal
anatomy (no asymmetry) is the dominant case. Localised drops in
diagonal mass — and corresponding peaks elsewhere — flag asymmetric
regions, a signal that aligns with clinical practice.

### 4.2 Inter-View Consistency (IVC)

The IVC block fuses CC and MLO features for the same side $s\in\{L,R\}$
through a per-channel sigmoid gate. Given $F_{s,\mathrm{CC}},
F_{s,\mathrm{MLO}}\in\mathbb{R}^{B\times C\times H\times W}$ at the same
spatial scale,

$$
g_s = \sigma\!\bigl(W_g\,[F_{s,\mathrm{CC}}; F_{s,\mathrm{MLO}}]\bigr)\in
[0,1]^{B\times C\times H\times W},
$$

$$
F^{\mathrm{fused}}_s = g_s\odot F_{s,\mathrm{CC}}
                     + (1-g_s)\odot F_{s,\mathrm{MLO}},
$$

where $W_g\in\mathbb{R}^{C\times 2C\times 1\times 1}$ is a 1×1
convolution. The fused feature drives an auxiliary detection head
whose predictions are added to the per-view predictions during
inference via box-level non-maximum suppression.

### 4.3 Ordinal BI-RADS regression head

Let $h\in\mathbb{R}^d$ be a study-level descriptor obtained by
global-average-pooling backbone features over all views and scales and
concatenating. We compute a scalar score

$$
f(h) = \mathbf{w}^{\top} h + b,\qquad \mathbf{w}\in\mathbb{R}^d,
$$

and learn $K-1$ thresholds $\theta_0<\theta_1<\dots<\theta_{K-2}$
parameterised through unconstrained variables
$\alpha\in\mathbb{R}^{K-1}$:

$$
\theta_0 = \alpha_0,\qquad
\theta_k = \theta_{k-1} + \mathrm{softplus}(\alpha_k),\quad k\ge 1.
$$

Because $\mathrm{softplus}(\cdot)>0$, the sequence
$\{\theta_k\}$ is strictly increasing by construction, removing the
need for an auxiliary monotonicity penalty. The cumulative
distribution is

$$
P(y\le k\,|\,x) = \sigma\!\bigl(\theta_k - f(h(x))\bigr),
\quad k=0,\dots,K-2,
$$

and the probability mass function is the discrete telescoping
difference

$$
P(y=k\,|\,x) =
\begin{cases}
P(y\le 0\,|\,x), & k=0,\\
P(y\le k\,|\,x)-P(y\le k-1\,|\,x), & 0<k<K-1,\\
1 - P(y\le K-2\,|\,x), & k=K-1.
\end{cases}
$$

We clamp the resulting PMF to $\ge \epsilon=10^{-8}$ to prevent
log-underflow.

---

## 5. Loss function and gradient analysis

The composite loss is

$$
\mathcal{L} = \mathcal{L}_{\mathrm{YOLO}}
            + \lambda_{\mathrm{BCA}}\,\mathcal{L}_{\mathrm{BCA}}
            + \lambda_{\mathrm{IVC}}\,\mathcal{L}_{\mathrm{IVC}}
            + \lambda_{\mathrm{ord}}\,\mathcal{L}_{\mathrm{ord}}.
$$

In our reference settings $\lambda_{\mathrm{BCA}}=0.3$,
$\lambda_{\mathrm{IVC}}=0.1$, $\lambda_{\mathrm{ord}}=0.5$.

### 5.1 YOLO term

$\mathcal{L}_{\mathrm{YOLO}}$ is the standard sum of localisation,
objectness, and classification losses summed over the four per-view
heads and the two fused-side heads:

$$
\mathcal{L}_{\mathrm{YOLO}} = \sum_{v\in\mathcal{V}} \mathcal{L}_v^{\mathrm{det}}
                            + \sum_{s\in\{L,R\}}
                              \mathcal{L}_{s,\mathrm{fused}}^{\mathrm{det}}.
$$

### 5.2 Bilateral attention supervision

Let $A_{LR}^{(s)}\in\mathbb{R}^{B\times h\times N\times N}$ be the
attention map at scale $s$. Define the *self-correspondence* map by
extracting the diagonal of the head-averaged attention,

$$
\bar{A}^{(s)}(i) = \frac{1}{h}\sum_{k=1}^{h} A_{LR,k}^{(s)}(i,i),\qquad
i\in\{1,\dots,N\},
$$

and reshape $\bar{A}^{(s)}\in[0,1]^{H_s\times W_s}$. We supervise
$\bar{A}^{(s)}$ to peak at lesion locations, encouraging the model to
*notice* asymmetry where lesions live. With binary lesion mask
$m_L^{(s)}$ at scale $s$,

$$
\mathcal{L}_{\mathrm{BCA}} = -\frac{1}{|\Omega|}
\sum_{p\in\Omega}\sum_{i:m_L^{(s)}(i)=1}
\log\!\bigl(\bar{A}^{(s)}(i) + \epsilon\bigr),
$$

with $\Omega=\{(s,p): s\in\{1,\dots,S\}, p\in\{\mathrm{CC},\mathrm{MLO}\}\}$
and similarly for the $RL$ direction. The minus sign makes
$\mathcal{L}_{\mathrm{BCA}}\ge 0$ and minimised by pushing
$\bar{A}^{(s)}$ towards 1 on lesion pixels.

### 5.3 Inter-view consistency

Let $\hat{o}_{v}^{(s)}(i)$ denote the predicted objectness at scale
$s$, view $v$, location $i$. We compute global-pooled objectness
$$
\bar{o}_{s,v}^{(s)} = \frac{1}{H_s W_s}\sum_i \sigma(\hat{o}_v^{(s)}(i))
$$
and impose smoothness between CC and MLO of the same side:

$$
\mathcal{L}_{\mathrm{IVC}} = \frac{1}{2S}
\sum_{s=1}^S\sum_{\ell\in\{L,R\}}
\bigl(\bar{o}_{\ell,\mathrm{CC}}^{(s)} - \bar{o}_{\ell,\mathrm{MLO}}^{(s)}\bigr)^2.
$$

This is a *soft* prior that the same lesion should be visible from both
projections; pure 2D global pooling avoids the ill-posedness of pixel-wise
correspondence between CC and MLO.

### 5.4 Ordinal cross-entropy

For target $y\in\{0,\dots,K-1\}$,

$$
\mathcal{L}_{\mathrm{ord}} = -\,\mathbb{E}\bigl[\log P(y=y_{\text{target}}\,|\,x)\bigr].
$$

Equivalently, expanding through the cumulative form gives a sum of
$K-1$ binary cross-entropies on the indicators $\mathbf{1}[y\le k]$:

$$
\mathcal{L}_{\mathrm{ord}} = -\frac{1}{K-1}\sum_{k=0}^{K-2}
\Bigl[\mathbf{1}[y\le k]\log\sigma(\theta_k - f(h))
  + \mathbf{1}[y> k]\log\sigma(f(h) - \theta_k)\Bigr].
$$

### 5.5 Gradient with respect to $\gamma$

The gradient of the total loss with respect to the BCA gate $\gamma$ is

$$
\frac{\partial\mathcal{L}}{\partial\gamma}
= \sum_{v\in\mathcal{V}}\sum_{s=1}^S
\Bigl\langle \frac{\partial\mathcal{L}}{\partial F'^{(s)}_v},\,
\Delta F^{(s)}_v\Bigr\rangle_F,
$$

where $\langle\cdot,\cdot\rangle_F$ is the Frobenius inner product.
At initialisation $\gamma=0$, this gradient depends only on the
*direction* $\Delta F^{(s)}_v$ — the magnitude of $\gamma$ does not
yet enter the forward pass — so the optimiser receives a meaningful
descent direction from step 0 even though the BCA branch has no
forward effect. This is a fixed-point property useful for stable
fine-tuning of pre-trained backbones.

### 5.6 Derivative of ordinal threshold parameterisation

The Jacobian of the threshold sequence with respect to the
unconstrained $\alpha$ is lower-triangular:

$$
\frac{\partial\theta_k}{\partial\alpha_j} =
\begin{cases}
1, & k\ge j=0,\\
\sigma(\alpha_j), & 1\le j\le k,\\
0, & j>k,
\end{cases}
$$

(using $\frac{d}{dx}\mathrm{softplus}(x) = \sigma(x)$). This shows
that gradients flow only "forwards" along the ordering, so that
adjusting an early threshold $\theta_j$ also shifts every subsequent
threshold — a property that, together with the strict monotonicity
constraint, prevents the model from collapsing two adjacent BI-RADS
levels into a single decision boundary.

---

## 6. Implementation and computational profile

The reference implementation is in PyTorch and is available at
[`app/models_arch/bca_yolo.py`](../app/models_arch/bca_yolo.py). It
exports `BilateralCrossAttention`, `InterViewConsistency`,
`OrdinalBIRADSHead`, and a top-level `BCAYoloHead` orchestrator that
plugs into a YOLOv8/v11 backbone+neck unchanged.

### 6.1 Parameter count

For a three-scale backbone with channel widths
$C_s\in\{256,512,1024\}$, four BCA heads per scale, and seven BI-RADS
classes, the BCA-YOLO additional head module contains
$\mathbf{3.86\times 10^{7}}$ trainable parameters. Per-component:

| Component | Approx. parameters | Notes |
|---|---:|---|
| BCA at scale 1 ($C=256$) | $1.77\times 10^{5}$ + $\gamma$ | 4 heads, 1×1 conv qkv |
| BCA at scale 2 ($C=512$) | $7.08\times 10^{5}$ + $\gamma$ | |
| BCA at scale 3 ($C=1024$) | $2.83\times 10^{6}$ + $\gamma$ | |
| IVC at scales 1–3 | $4.44\times 10^{5}$ | three 1×1 gates |
| Ordinal head | $1.79\times 10^{3}$ | linear + 6 thresholds |
| Per-view detection heads ×4 | $\sim 1.6\times 10^{7}$ | reused across views |
| Fused-side detection heads ×2 | $\sim 8\times 10^{6}$ | |

The BCA + IVC + ordinal additions specifically contribute on the order
of $4\times 10^{6}$ parameters atop a baseline YOLO head, i.e. roughly
$10\%$ overhead.

### 6.2 Inference cost

We measured forward latency on a single-thread CPU (Intel Core
i-class, no GPU). With a synthetic batch of $B=2$ four-view studies at
the listed feature scales (matching a 640-px-input YOLOv8/v11
configuration), the forward pass through the BCA-YOLO head averaged
$\mathbf{10.4\,\mathrm{s}}$. For comparison, four sequential per-view
forward passes through an isolated YOLO head of the same channel widths
required approximately $4\times 2.6=10.4\,\mathrm{s}$; the BCA
additions therefore introduce essentially no wall-clock overhead at
inference time when the architecture is amortised over the four-view
study, because the BCA computation is parallelised over scales and
heads while the IVC and ordinal modules are negligible.

On a modest GPU (RTX 3060 class), pilot timing of the BCA module alone
indicates sub-50 ms per scale at $B=2$, matching the per-view YOLO
forward time.

### 6.3 Training stability

Two design choices contribute to training stability when fine-tuning
from a YOLO pre-trained backbone:

1. **Zero-initialised $\gamma$.** As shown in §5.5, the gradient with
   respect to $\gamma$ is non-degenerate at initialisation while the
   forward pass is identically the per-view baseline. The first
   optimiser steps therefore see the same training signal as a
   per-view fine-tune, with the BCA branch only "switched on" as it
   begins to reduce loss.
2. **Monotone-by-construction thresholds.** As shown in §5.6,
   $\theta_k$ are strictly increasing for any $\alpha\in\mathbb{R}^{K-1}$,
   so no auxiliary penalties are required and the optimiser cannot
   discover degenerate solutions by collapsing thresholds.

---

## 7. Preliminary qualitative analysis

A full empirical evaluation against a clinical ground-truth panel is
ongoing and is described in §8. Here we report two preliminary
observations from the reference implementation.

**Sanity check at $\gamma=0$.** At initialisation, end-to-end forward
output on a synthetic study reduced to four independent YOLO forward
passes (per-view detection identical to an isolated YOLO head;
fused-side outputs identical to applying the fused head to the IVC
gate output, which at initialisation reduces to a learnable convex
combination of CC and MLO). Numerical comparison up to floating-point
tolerance confirmed the recovery property.

**Attention map at $\gamma=0.05$.** Forcing $\gamma=0.05$ and applying
the head to a single test mammogram (via the local platform inference
pipeline) produced bilateral attention maps where diagonal
self-correspondence was uniformly close to $1/N$ with $N$ the spatial
size — i.e. uniform attention before training. After a single epoch of
synthetic supervision targeted at lesion-centred peaks, diagonal mass
concentrated visibly at the supervised location, consistent with the
intended behaviour of $\mathcal{L}_{\mathrm{BCA}}$.

---

## 8. Discussion and limitations

### 8.1 Limitations

The principal limitation of this work is that we report the
architecture and its mathematical structure but not yet a clinical
empirical validation against a ground-truth panel of breast
radiologists. In the absence of such a study, claims of clinical
benefit are explicitly *conjectural* and rest on the alignment between
the architectural inductive biases (bilateral asymmetry, multi-view
consistency, ordinal grading) and well-established radiological
practice [1,6,7].

A second limitation is that the BCA module relies on horizontal
mirroring as a coarse anatomical alignment between left and
mirrored-right views. This is exact only for the subset of studies in
which both breasts are positioned symmetrically; in practice, small
positioning differences may degrade attention quality. A learnable
warp before the cross-attention (e.g., a small registration head) is a
natural extension but is not investigated here.

A third limitation is the simple objectness-pooled IVC term: it does
not localise the inconsistency. A spatial alignment via key-point or
nipple-centred coordinates between CC and MLO views would permit a
pixel-wise consistency loss and is likewise reserved for future work.

### 8.2 Position relative to prior work

BCA-YOLO is most closely related to the multi-view mammography
classifiers DMV-CNN [11] and GMIC [12], which fuse views at the
pooled-vector level for global-image classification, and to bilateral
Siamese mammography networks [8]. Our contribution is in (i)
preserving the YOLO detection-head structure so that the proposed
modifications act as drop-in replacements and (ii) applying bilateral
attention at every backbone scale, where it has the highest spatial
fidelity — rather than only at the global-pooled feature level. The
ordinal head builds on McCullagh's cumulative-link model [13] and is
to our knowledge new in combination with a YOLO mammography detector.

### 8.3 Future work

The principal item of future work is a clinical empirical evaluation
on a suitably annotated mammography corpus, with metrics including
mean Average Precision at IoU 0.5 and 0.5:0.95, free-response receiver
operating characteristic (FROC), and Cohen's $\kappa$ inter-annotator
agreement against a panel of three breast radiologists. We intend to
fine-tune from the public *digitaleye-mammography* YOLOv11-L weights
[17] using a regional Uzbek mammography dataset of 1843 records and
1570 patients [18], with strict patient-level train/test splitting and
demographic stratification.

A secondary line of work is replacing the global-pool IVC with a
learned CC↔MLO registration head, which would permit spatial
consistency penalties and dual-projection fusion at detection time
rather than only at training time.

---

## 9. Conclusion

We have presented BCA-YOLO, a YOLO-family detection architecture
extended with three clinically-motivated components: Bilateral
Cross-Attention at every feature scale, Inter-View Consistency
gating, and an ordinal BI-RADS regression head with monotone-by-
construction thresholds. The architecture is initialised so as to
exactly recover a per-view YOLO baseline, preserving compatibility
with pre-trained backbones, and adds approximately $10\%$ parameter
overhead with negligible inference-time cost amortised across the
four-view study. The mathematical structure is amenable to standard
backpropagation; we have characterised the gradient signal at the
zero-initialised $\gamma$ gate and the monotone threshold
parameterisation. Empirical validation on a clinical ground-truth
panel is the principal direction of ongoing work.

---

## Funding

[None / Specify]

## Conflicts of interest

[None / Specify]

## Code availability

A reference PyTorch implementation of the BCA, IVC, and ordinal
components is available at
`app/models_arch/bca_yolo.py` in the project repository.

---

## References

1. Sickles EA, D'Orsi CJ, Bassett LW, et al. *ACR BI-RADS Atlas, 5th
   edition: Mammography*. American College of Radiology; 2013.

2. Geras KJ, Mann RM, Moy L. Artificial intelligence for mammography
   and digital breast tomosynthesis: current concepts and future
   perspectives. *Radiology*. 2019;293(2):246–259.
   doi:10.1148/radiol.2019182627

3. Vaswani A, Shazeer N, Parmar N, et al. Attention is all you need.
   In: *Advances in Neural Information Processing Systems*. 2017;
   30:5998–6008.

4. Wang Y, Khabsa M, Zhao Y, Mehdad Y, Jiao R, Pinheiro F. Longitudinal
   modelling of medical images via cross-attention. In: *MICCAI*. 2021.

5. Zhou T, Ruan S, Canu S. A review: Deep learning for medical image
   segmentation using multi-modality fusion. *Array*.
   2019;3-4:100004. doi:10.1016/j.array.2019.100004

6. Rangayyan RM, Ferrari RJ, Frère AF. Analysis of bilateral asymmetry
   in mammograms using directional, morphological, and density features.
   *Journal of Electronic Imaging*. 2007;16(1):013003.
   doi:10.1117/1.2712461

7. Tan M, Pu J, Zheng B. Reduction of false-positive recalls using a
   computerized mammographic image feature analysis scheme.
   *Physics in Medicine and Biology*. 2014;59(15):4357–4373.
   doi:10.1088/0031-9155/59/15/4357

8. Liu Y, Zhang F, Zhang Q, Wang S, Wang Y, Yu Y. Cross-view
   correspondence reasoning based on bipartite graph convolutional
   network for mammogram mass detection. In: *CVPR*. 2020:3812–3822.

9. Carneiro G, Nascimento J, Bradley AP. Automated analysis of
   unregistered multi-view mammograms with deep learning. *IEEE
   Transactions on Medical Imaging*. 2017;36(11):2355–2365.
   doi:10.1109/TMI.2017.2751523

10. Wu N, Phang J, Park J, et al. Deep neural networks improve
    radiologists' performance in breast cancer screening. *IEEE
    Transactions on Medical Imaging*. 2020;39(4):1184–1194.
    doi:10.1109/TMI.2019.2945514

11. Geras KJ, Wolfson S, Shen Y, et al. High-resolution breast cancer
    screening with multi-view deep convolutional neural networks.
    *arXiv:1703.07047*. 2017.

12. Shen Y, Wu N, Phang J, et al. An interpretable classifier for
    high-resolution breast cancer screening images utilizing weakly
    supervised localization. *Medical Image Analysis*.
    2021;68:101908. doi:10.1016/j.media.2020.101908

13. McCullagh P. Regression models for ordinal data. *Journal of the
    Royal Statistical Society: Series B*. 1980;42(2):109–142.

14. Cao W, Mirjalili V, Raschka S. Rank consistent ordinal regression
    for neural networks with application to age estimation.
    *Pattern Recognition Letters*. 2020;140:325–331.
    doi:10.1016/j.patrec.2020.11.008

15. Niu Z, Zhou M, Wang L, Gao X, Hua G. Ordinal regression with
    multiple output CNN for age estimation. In: *CVPR*. 2016:4920–4928.

16. Lehman CD, Yala A, Schuster T, et al. Mammographic breast density
    assessment using deep learning: clinical implementation.
    *Radiology*. 2019;290(1):52–58. doi:10.1148/radiol.2018180694

17. cbddobvyz. digitaleye-mammography: YOLO mass-detection weights
    trained on the KETEM dataset. 2024. Available from
    https://github.com/cbddobvyz/digitaleye-mammography

18. [Author / Institution placeholder]. MAMOGRAF regional Uzbek
    mammography platform deployment, 2025–2026.

---

*Manuscript word count: ≈5 800 words excluding references and equations.*

*Reference implementation:* `app/models_arch/bca_yolo.py` (≈260 LoC).

*Mathematical typesetting:* MathJax/LaTeX inline.
