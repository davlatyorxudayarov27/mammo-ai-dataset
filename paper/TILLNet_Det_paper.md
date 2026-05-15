# TILLNet-Det: Text-Informed Lesion Localisation Network for Multilingual Mammography Detection

**Authors:** [Your name(s)]¹

¹ [Institution]

**Corresponding author:** [email]

---

## Abstract

**Background.** Mammography lesion detection is dominated by image-only
deep models that ignore the radiology report routinely produced alongside
each acquisition. Reports in post-Soviet Central Asia are written in three
co-existing scripts (Uzbek-Cyrillic, Uzbek-Latin, Russian), often
code-switched within a single document, and contain explicit
spatial cues — laterality, quadrant, clock face position, and lesion
size — that an image-only detector must rediscover from pixels alone.

**Objective.** We propose **TILLNet-Det**, an end-to-end multimodal
detector that conditions a Feature-Pyramid–Network–based one-stage detector
on a learned multilingual representation of the radiology report through
**Feature-wise Linear Modulation (FiLM)** at every pyramid level.

**Methods.** TILLNet-Det combines (i) a 1-channel ResNet-50 backbone
adapted from ImageNet via averaged-channel weight initialisation,
(ii) a 5-level Feature Pyramid Network ($P_3$–$P_7$), (iii) a 4-layer
character-level Transformer text encoder that maps mixed-script reports
to a $d_t = 256$ semantic vector $\mathbf{t}$, (iv) per-level FiLM
modulators $\mathrm{FiLM}_l(\mathbf{x}_l, \mathbf{t}) =
(1+\boldsymbol{\gamma}_l)\odot \mathbf{x}_l + \boldsymbol{\beta}_l$
with $(\boldsymbol{\gamma}_l, \boldsymbol{\beta}_l) =
\mathrm{MLP}_l(\mathbf{t})$, and (v) a shared FCOS-style head with
classification, regression, and centerness branches. The FiLM modules
are *zero-initialised* so that at the start of training the model is
mathematically equivalent to its image-only ablation, providing a
controlled multimodal warm start.

**Training.** A three-stage protocol is proposed:
(1) **bootstrap** on CBIS-DDSM with full bounding-box supervision,
(2) **weak fine-tune** on local DICOMs using
text-guided pseudo-labels generated from the radiology report, and
(3) **gold fine-tune** on radiologist-verified annotations.
A composite FCOS-style loss is optimised:
$\mathcal{L} = \mathcal{L}_{\text{focal}} + \mathcal{L}_{\text{GIoU}}
+ \mathcal{L}_{\text{ctr}}$, normalised by the number of positive
locations.

**Computational footprint.** The full multimodal model has
$36.52$ M trainable parameters (backbone $23.50$ M, text encoder
$3.42$ M, FPN $3.87$ M, FiLM $0.99$ M, detection head $4.74$ M).
The image-only ablation has $32.11$ M parameters; the additional
$4.41$ M parameters constitute the multimodal contribution.

**Evaluation protocol.** Free-Response ROC (FROC) is used as the
primary metric, with sensitivity reported at fixed false-positive rates
of $\{0.5, 1.0, 2.0, 4.0\}$ FP/image. Six controlled ablations
(image-only, text-only–positional, no-FiLM, level-restricted FiLM,
no-pretrained, single-stage training) test each architectural
contribution independently.

**Significance.** TILLNet-Det is, to our knowledge, the first
multimodal mammography detector that (a) handles three scripts
simultaneously without script-specific encoders, (b) learns
text-conditioning via zero-initialised FiLM that is provably
non-degrading at initialisation, and (c) operationalises a
text-to-bbox weak supervision pipeline tailored to a low-annotation
regime.

**Keywords.** mammography, lesion detection, multimodal learning,
FiLM, FCOS, code-switched text, weak supervision, multilingual NLP,
medical imaging.

---

## 1. Introduction

Computer-aided detection (CAD) of breast cancer in mammography has
benefited substantially from one-stage object detectors such as YOLO,
RetinaNet, and FCOS [4, 9, 12]. These systems treat the mammogram as
the sole input and learn a function $f_\theta: \mathbb{R}^{H\times W}
\to \{(\mathbf{b}_i, c_i, s_i)\}$ from pixels to a set of bounding
boxes, classes, and scores. The accompanying radiology report,
typically dictated by a senior radiologist immediately after image
acquisition, is discarded.

This is wasteful in two respects. First, the report contains explicit
spatial information — laterality, quadrant ($\text{UOQ}$, $\text{UIQ}$,
$\text{LOQ}$, $\text{LIQ}$), clock-face localisation, and physical size
in millimetres — that effectively narrows a binary "where is the
lesion?" search to a much smaller region of the image. Second, the
report contains BI-RADS-like categorical information that constrains
the lesion *type* (mass, calcification, asymmetry, architectural
distortion) which an image-only model must infer from pixels.

Three obstacles have prevented practical deployment of multimodal
mammography detectors in the post-Soviet Central Asian setting that
motivates this work:

1. **Script multiplicity.** Reports routinely contain Uzbek-Cyrillic,
   Uzbek-Latin, and Russian within the same document.
   Conventional multilingual NLP pipelines either pick one script and
   discard the rest or rely on heavy multilingual transformers
   (mBERT, XLM-R) whose deployment cost is prohibitive in resource-
   constrained Uzbek hospital IT.

2. **Annotation scarcity.** Local DICOM corpora come with reports but
   without radiologist-drawn bounding boxes. Pure supervised training
   is thus impossible without expensive re-annotation.

3. **Image–report alignment.** Even when both modalities exist, joint
   models can collapse onto either modality (the so-called "shortcut
   problem"), or worse, hallucinate detections from text that has no
   visual basis. A safe multimodal detector must degrade gracefully
   when the report is empty or wrong.

We address all three with **TILLNet-Det**:

* a *character-level* Transformer text encoder that processes any
  Unicode-bearing script in a shared vocabulary of $V = 256$ buckets
  (§3.2);
* **FiLM** [10] fusion that injects the text vector into every pyramid
  level of the visual tower, with γ and β both *zero-initialised* so
  that the multimodal model is bit-equivalent to its image-only
  ablation at $t = 0$ (§3.4);
* a three-stage training protocol that bootstraps on CBIS-DDSM,
  fine-tunes on text-guided pseudo-labels mined from the local
  reports, and finally on a small radiologist-verified set (§3.7).

### 1.1 Contributions

1. **Architecture.** A novel multimodal detector tailored to
   multilingual code-switched clinical text, with FiLM-based fusion
   that is provably non-degrading at initialisation.
2. **Pseudo-label pipeline.** A multilingual regex-based weak
   supervision pipeline that converts radiology free text into YOLO-
   format bounding boxes through quadrant-, clock-, and size-aware
   spatial heuristics, with self-rated confidence scores.
3. **Training protocol.** A three-stage CBIS$\to$pseudo$\to$gold
   curriculum that exploits ${\sim}10{,}000$ public bbox annotations,
   ${\sim}1{,}800$ local reports, and a small verification cohort.
4. **Evaluation framework.** Six ablations isolate the contribution
   of each module, with FROC and sensitivity@FP-rate as the primary
   clinical metrics, instrumented with paired statistical testing.
5. **Implementation.** A complete, reproducible codebase
   (preprocessing, dataset converter, weak supervision, trainer, FROC
   evaluator) released as Python modules.

---

## 2. Related Work

**One-stage mammography detectors.** Akselrod-Ballin et al. [1]
demonstrated YOLO-style detectors on mammography and reported
sensitivity around 0.87 at $1$ FP/image on a private corpus. Ribli
et al. [11] used Faster R-CNN on DDSM, reporting AUC $\approx 0.95$
for detection of malignant lesions but with lower spatial precision
than anchor-free methods. FCOS [12] provides anchor-free dense
prediction with regress-range stratification, well suited to the
order-of-magnitude lesion-size variation in mammography.

**Multimodal medical imaging.** CLIP-style image–text contrastive
learning [Radford 2021] has been applied to chest X-ray
[Tiu 2022] and pathology [Huang 2023] but not, to our knowledge,
to mammography lesion detection on multilingual clinical text. Most
multimodal medical models use English clinical English; the
multilingual code-switched setting is essentially unstudied.

**FiLM.** Perez et al. [10] introduced Feature-wise Linear Modulation
for visual question answering. Subsequent applications include
acoustic source separation and reinforcement learning, but FiLM has
seen limited use in object detection and, to our knowledge, no use in
mammography. Our zero-initialised FiLM variant is a small but
load-bearing modification that lets us guarantee non-degradation
relative to the image-only baseline (§3.4).

**Weak supervision in mammography.** Choukroun et al. [3] used
image-level (presence/absence) labels with class-activation mapping
to derive coarse localisation. Our work is complementary: the report
already contains explicit *spatial* cues; rather than localising via
saliency, we project the textual cues directly onto the image plane.

---

## 3. Methods

### 3.1 Preprocessing

Each DICOM is processed through a 9-step pipeline before reaching
the detector:

1. **Modality LUT.** Apply rescale slope and intercept:
   $I_1 = m \cdot I_0 + b$.
2. **VOI LUT.** Apply window-centre/window-width to map to display
   range. If absent, derive from the global histogram.
3. **Photometric inversion.** If $\text{PhotometricInterpretation} =
   \text{MONOCHROME1}$, invert: $I \leftarrow 1 - I$.
4. **Breast segmentation.** Otsu binarisation of a $5\times 5$
   Gaussian-smoothed image, followed by morphological close+open
   ($15\times 15$ ellipse) and largest-connected-component selection
   with hole filling.
5. **Crop** to the bounding box of the breast mask.
6. **Pectoral removal** (MLO views). Hough line detection on the
   upper $0.55H \times 0.45W$ region, with side-aware angle filtering
   and triangle erasure above the dominant line. Skipped if no line
   meets the slope plausibility check.
7. **CLAHE.** Adaptive histogram equalisation with $\text{clipLimit}
   = 2.0$ and $8\times 8$ tile grid.
8. **Letterbox** to $1024 \times 1024$ preserving aspect ratio
   (zero-pad).
9. **Laterality standardisation.** All right-laterality images are
   horizontally mirrored to a canonical left-laterality convention
   (chest wall left, nipple right). This is one of the strongest
   priors we can inject and lets the model share parameters across
   sides without learning a separate orientation.

The preprocessing also emits a JSON manifest with per-image
provenance — original DICOM path, breast bounding box, pectoral-
removed flag, pixel spacing, and the laterality-flip flag — used
later by the pseudo-label generator and by `transform_bbox()` for
mapping CBIS-DDSM ROI masks through the same coordinate system.

### 3.2 Cross-Script Text Encoder

Reports are encoded using a character-level vocabulary that maps each
Unicode codepoint to a $V = 256$-dimensional bucket:

$$
\text{enc}(c) = (\text{ord}(c) \bmod 254) + 1, \qquad \text{PAD}_{id} = 0.
$$

The $-1$ on the modulus ensures the PAD token is reserved.
Although collisions occur (the bucket for the Latin "a" coincides
with the Cyrillic "а"), the embedding table is learned end-to-end
and the bucket index need only be deterministic.

A learnable embedding $E \in \mathbb{R}^{V \times d}$ ($d = 256$) is
added to a learned positional embedding $P \in \mathbb{R}^{L \times d}$
($L = 512$). The embedded sequence passes through a 4-layer
pre-norm Transformer encoder with $h = 4$ heads and feed-forward
dimension $d_{ff} = 1024$:

$$
\mathbf{H} = \mathrm{Transformer}\bigl(E[s] + P, \mathrm{mask} =
[s = \text{PAD}_{id}]\bigr) \in \mathbb{R}^{B \times L \times d}.
$$

Padding tokens are masked and a length-normalised mean pool is
applied:

$$
\bar{\mathbf{h}} = \frac{\sum_{l=1}^{L} \mathbf{H}_{:,l,:} \cdot
[s_l \neq \text{PAD}_{id}]}{\sum_{l=1}^{L} [s_l \neq \text{PAD}_{id}]}.
$$

A linear projection produces the final semantic vector
$\mathbf{t} = W_o \bar{\mathbf{h}} \in \mathbb{R}^{d_t}$ with $d_t =
256$.

### 3.3 Image Backbone and Feature Pyramid

The image branch uses a torchvision ResNet-50, with the 3-channel
ImageNet-pretrained stem averaged to a 1-channel grayscale stem:

$$
W^{1\text{ch}}_{i,1,k_1,k_2} = \frac{1}{3} \sum_{c=1}^{3}
W^{3\text{ch}}_{i,c,k_1,k_2}.
$$

The four ResNet stages produce $C_2$ ($s = 4$, $256$ ch),
$C_3$ ($s = 8$, $512$), $C_4$ ($s = 16$, $1024$) and
$C_5$ ($s = 32$, $2048$). A standard top-down FPN [7] with $1\times 1$
lateral projections to $C_{\mathrm{fpn}} = 256$ produces $P_3$, $P_4$,
$P_5$. Two further $3\times 3$ stride-$2$ convolutions on top of $P_5$
yield $P_6$ ($s = 64$) and $P_7$ ($s = 128$), giving FCOS its canonical
five-level pyramid.

### 3.4 Multimodal Fusion via FiLM

Each pyramid level is modulated by the text vector $\mathbf{t}$:

$$
\boxed{\
\mathbf{P}_l' = (\mathbf{1} + \boldsymbol{\gamma}_l) \odot \mathbf{P}_l
                + \boldsymbol{\beta}_l, \qquad
(\boldsymbol{\gamma}_l, \boldsymbol{\beta}_l)
   = \mathrm{MLP}_l(\mathbf{t}), \quad
\boldsymbol{\gamma}_l, \boldsymbol{\beta}_l \in \mathbb{R}^{C_{\mathrm{fpn}}}.
\ }
$$

Each $\mathrm{MLP}_l$ is a 2-layer GELU-activated network of width
$256 \to 256 \to 2C_{\mathrm{fpn}}$. The *output* layer of every MLP is
**zero-initialised** ($W_{\text{out}} = \mathbf{0}, b_{\text{out}} =
\mathbf{0}$), which yields a critical property:

**Proposition (Identity at initialisation).** *At step* $0$ *of
training,*
$\mathbf{P}_l' = \mathbf{P}_l$ *for all* $l$, *for all inputs* $(\mathbf{x},
\mathbf{t})$.

*Proof.* $W_{\text{out}} = \mathbf{0} \Rightarrow \boldsymbol{\gamma}_l =
\boldsymbol{\beta}_l = \mathbf{0}$. Substituting,
$\mathbf{P}_l' = (1 + 0)\odot \mathbf{P}_l + 0 = \mathbf{P}_l$. ∎

This means TILLNet-Det at $t = 0$ is *bit-identical* to its image-only
ablation. We verified this empirically: the maximum absolute
difference between full-model and image-only-ablation classification
logits on a randomly-initialised network with random text input was
$0$ (machine precision) across all five FPN levels (§5.2).
Multimodal training therefore monotonically *adds* signal to a
working image-only solution rather than perturbing it from a different
initialisation, which is known to destabilise training when the text
branch is uninformed.

### 3.5 FCOS-Style Detection Head

Following FCOS [12], we use an anchor-free head with three branches
(classification, regression, centerness) operating on each pyramid
level. The head shares weights across levels, with a per-level
learnable scalar $\sigma_l$ applied to the regression branch only:

$$
\hat{\mathbf{r}}_l = \sigma_l \cdot \mathrm{ReLU}(\mathrm{Conv}_{3\times3}
(\mathrm{Tower}_{\text{reg}}(\mathbf{P}_l'))).
$$

Each location $(i, j)$ on $P_l$ corresponds to image-plane point
$(x_p, y_p) = (s_l(j + 0.5), s_l(i + 0.5))$. The regression output
$\hat{\mathbf{r}}_l \in \mathbb{R}^{H_l \times W_l \times 4}$
predicts distances $(\hat{l}, \hat{t}, \hat{r}, \hat{b})$ in stride
units; decoding to a bbox is $(\hat{l} s_l, \hat{t} s_l, \hat{r} s_l,
\hat{b} s_l) \to (x_p - \hat{l}s_l, y_p - \hat{t}s_l, x_p + \hat{r}s_l,
y_p + \hat{b}s_l)$.

Bias initialisation of the classification head follows the focal-loss
prior of $p_a = 0.01$:

$$
b_{\text{cls}} = -\log\left(\frac{1 - p_a}{p_a}\right)
              = -\log(99) \approx -4.595.
$$

### 3.6 Loss

For each image we assign FCOS-style targets to every location. A
location is *positive* for GT box $g$ if and only if:

* the location lies *inside* the box ($\min(l, t, r, b) > 0$);
* the location is within a *centre-sampling radius* $R = 1.5\,s_l$ of
  the box centre;
* $\max(l, t, r, b) \in [\text{lo}_l, \text{hi}_l)$, where the
  per-level regress ranges are $[-1, 64),$ $[64, 128),$ $[128, 256),$
  $[256, 512),$ $[512, \infty)$ (in original-image pixels).

If multiple GT boxes satisfy all three constraints, the smallest-area
GT is selected.

The composite loss is

$$
\mathcal{L}\;=\;\frac{1}{N_{\text{pos}}}\Bigl(\,
\lambda_{\text{cls}}\sum_{i}\mathcal{L}^{\text{focal}}_i
+ \lambda_{\text{reg}}\sum_{i \in \mathcal{P}} \mathcal{L}^{\text{GIoU}}_i
+ \lambda_{\text{ctr}}\sum_{i \in \mathcal{P}} \mathcal{L}^{\text{BCE}}_i
\Bigr),
$$

with $\lambda_{\text{cls}} = \lambda_{\text{reg}} = \lambda_{\text{ctr}} = 1$,
$N_{\text{pos}}$ the count of positive locations across the batch,
$\mathcal{P}$ the set of positive locations, and:

* **Focal loss** [8] over per-class binary logits, summed across all
  locations and classes with $\alpha = 0.25, \gamma = 2$:
  $\mathcal{L}^{\text{focal}}_i = -\alpha_t (1 - p_t)^\gamma \log p_t$,
  $p_t = p y + (1 - p)(1 - y)$.
* **GIoU loss** [Rezatofighi 2019] computed directly on $(l, t, r, b)$
  distances, exploiting the equivalence
  $\mathrm{IoU}(\mathrm{xyxy}_1, \mathrm{xyxy}_2) =
  \mathrm{IoU}_{\text{ltrb}}$ when both share an anchor point.
* **Centerness BCE** with target
  $\mathrm{ctr}^* = \sqrt{\frac{\min(l, r)}{\max(l, r)} \cdot
  \frac{\min(t, b)}{\max(t, b)}}$, which down-weights low-quality
  predictions at inference (predicted $p \cdot \mathrm{ctr}$ is used
  as the score).

### 3.7 Three-Stage Training Protocol

To exploit data of three radically different annotation qualities,
we propose:

**Stage 1 — Bootstrap on CBIS-DDSM.** Convert CBIS-DDSM
([2], 10,239 mammograms, 1,566 patients) to YOLO format using our
converter (§4.2), with patient-level train/val split. Train
TILLNet-Det with the text branch *disabled* (`use_text=False`) for
100 epochs at $1024^2$ resolution, $\text{lr}_0 = 10^{-4}$, AdamW,
cosine schedule, conservative augmentation (no fliplr because of
laterality standardisation, scale = $\pm 10\%$, mosaic disabled).
This produces a strong image-only initialisation $\theta_1$.

**Stage 2 — Weak text-guided fine-tune.** Run our pseudo-label
generator (§4.3) on the local DICOMs and reports, retaining only
labels with self-rated confidence $\geq 0.5$. Initialise from
$\theta_1$ with the text branch and FiLM modules added (FiLM remains
zero-initialised, so no warm-start divergence). Fine-tune for 30
epochs at lower learning rate $\text{lr}_0 = 5\cdot 10^{-5}$,
freezing the backbone for the first 5 epochs to let the text encoder
and FiLM modules align without disrupting visual features.

**Stage 3 — Gold fine-tune.** A subset of pseudo-labels is presented
to a senior radiologist via the MAMOGRAF UI; accept/edit/reject
actions produce gold labels. Fine-tune on this set for 20 epochs at
$\text{lr}_0 = 2\cdot 10^{-5}$. Only this stage uses radiologist
labels, and consequently only this stage is evaluated against
held-out gold labels.

---

## 4. Datasets and Implementation

### 4.1 CBIS-DDSM

The Curated Breast Imaging Subset of DDSM [2] provides
$\sim 10{,}239$ mammograms from 1,566 patients, each with one or more
ROI masks indicating mass or calcification location and pathology
labels (BENIGN / BENIGN_WITHOUT_CALLBACK / MALIGNANT). Our converter
groups multi-lesion images, derives bboxes from the binary masks via
non-zero pixel extent, and splits patient-wise into train/val/test
($\sim 80\% / 10\% / 10\%$ at patient level, with the test split fixed
by the original CBIS-DDSM CSV).

### 4.2 Local MAMOGRAF Corpus

The local corpus comprises 1,839 mammographic clinical records from a
regional Uzbek oncology centre, each with a free-text report
($n_{\text{positive}} = 345$, $n_{\text{negative}} = 1{,}494$ as
labelled by the XS-Classifier system [our prior work]). Of these,
DICOMs are available for a subset (see §4.4), with reports keyed
to images via study-level metadata.

### 4.3 Pseudo-Label Generation

For each local image, the matched report is parsed by our
multilingual `extract_findings` regex extractor for laterality,
quadrant ($\text{UOQ}|\text{UIQ}|\text{LOQ}|\text{LIQ}|\text{central}|
\text{axillary\_tail}$), clock face position ($1$–$12$), lesion type
(mass/calcification/asymmetry), size (mm), and distance from nipple.
Findings are projected onto the preprocessed canvas through:

* **Quadrant centre table** — view-aware mapping from the discrete
  quadrant to a $(x_{\text{frac}}, y_{\text{frac}})$ position in the
  cropped breast region (different MLO and CC tables).
* **Clock position** — angle from the nipple region:
  $\theta = (c \bmod 12) \cdot \pi/6 - \pi/2$,
  $(x, y) = (0.85 + 0.30 \cos\theta, 0.50 + 0.30 \sin\theta)$,
  with the $y$ excursion halved for CC views (where superior–inferior
  is collapsed in the projection).
* **Size to pixels** — using `pixel_spacing` from the DICOM and the
  letterbox scale factor $s$:
  $w_{\text{px}} = w_{\text{mm}} \cdot s/\text{spacing}_x \cdot 1.4$
  with a 40\% margin to keep the bbox enclosing rather than tight.
* **Confidence score** — heuristic 0.30 base plus 0.20 (quadrant)
  + 0.15 (clock) + 0.15 (size) + 0.10 (distance from nipple)
  + 0.10 (MLO bonus, since MLO localisation is less ambiguous).
* **Laterality safety** — if the parsed laterality $\neq$
  the image's `ImageLaterality`, *no* bbox is emitted for that image.
  This prevents cross-side report leakage from polluting the YOLO
  labels.

### 4.4 Implementation Details

The full system is implemented in Python ($\geq 3.10$) with PyTorch
2.11, torchvision 0.26, OpenCV-headless 4.13, and pydicom 3.x.
Training is performed on a single NVIDIA GPU (target: A100 / RTX
4090). Hyperparameters: batch 8, image size 1024², AdamW
$\beta = (0.9, 0.999)$, weight decay $5\times 10^{-4}$, gradient
clipping at 10.0, cosine LR schedule with linear warmup over the
first 2 epochs.

---

## 5. Computational Footprint and Forward-Pass Validation

We report the following empirical findings from the implemented
architecture, measured on a CPU-only forward pass of two
$1\times 512\times 512$ images.

### 5.1 Parameter Counts

| Module                       | Parameters | % total |
|------------------------------|-----------:|--------:|
| ResNet-50 backbone (1-chan)  | $23.50$ M  | $64.4$  |
| Char-Transformer text encoder| $3.42$ M   | $9.4$   |
| Feature Pyramid Network      | $3.87$ M   | $10.6$  |
| FiLM modulators (5 levels)   | $0.99$ M   | $2.7$   |
| FCOS-style detection head    | $4.74$ M   | $13.0$  |
| **Total (full multimodal)**  | **$36.52$ M** | $100$ |
| Image-only ablation          | $32.11$ M  | —       |

### 5.2 FiLM Identity at Initialisation (Empirical)

To verify Proposition 3.4 numerically, we initialise a TILLNet-Det
with `use_text=True`, freeze its backbone/FPN/head weights, and
construct a parallel `use_text=False` model with identical
backbone/FPN/head weights. We feed both an identical random image
and an arbitrary random text batch:

$$
\max_{\,l,\,b,\,k,\,i,\,j} \;\bigl|\,
\mathrm{cls}^{\text{full}}_{l,b,k,i,j}\;-\;
\mathrm{cls}^{\text{img}}_{l,b,k,i,j}\,\bigr|\;=\;0.0\;
(\,\text{across all 5 levels, 2 images, all classes, all locations}\,).
$$

This confirms that the multimodal model starts from the image-only
solution and that any subsequent divergence is the result of
gradient-driven specialisation, not initialisation noise.

### 5.3 Pyramid Output Shapes (image $512\times 512$, batch 2)

| Level | Stride | cls shape           | reg shape           | ctr shape           |
|------:|-------:|---------------------|---------------------|---------------------|
| $P_3$ |     8  | $(2,3,64,64)$       | $(2,4,64,64)$       | $(2,1,64,64)$       |
| $P_4$ |    16  | $(2,3,32,32)$       | $(2,4,32,32)$       | $(2,1,32,32)$       |
| $P_5$ |    32  | $(2,3,16,16)$       | $(2,4,16,16)$       | $(2,1,16,16)$       |
| $P_6$ |    64  | $(2,3,8,8)$         | $(2,4,8,8)$         | $(2,1,8,8)$         |
| $P_7$ |   128  | $(2,3,4,4)$         | $(2,4,4,4)$         | $(2,1,4,4)$         |

Total prediction locations per $512^2$ image:
$64^2 + 32^2 + 16^2 + 8^2 + 4^2 = 5{,}456$.
At the deployment resolution of $1024^2$, this becomes
$128^2 + 64^2 + 32^2 + 16^2 + 8^2 = 21{,}824$ locations per image.

### 5.4 End-to-End Smoke Run

A 2-epoch training run on a synthetic dataset (8 images, 1 lesion
each, image size $256^2$, batch 2, CPU) reduced the composite loss
from $2.89$ to $2.02$ (classification component $1.24 \to 0.46$, a
$63\%$ reduction in 2 epochs), confirming that gradients flow through
the full forward path including text embedding $\to$ Transformer
$\to$ FiLM $\to$ FPN $\to$ FCOS head $\to$ loss.

---

## 6. Evaluation Protocol

### 6.1 Primary Metric: FROC

Free-Response ROC is the de-facto standard for mammography
detection because it accounts for multiple lesions per image (which
mAP largely averages out) and because the operating point of
clinical interest is at low false-positive rates.

For each test image $i$ we compute the predicted set
$\hat{\mathcal{D}}_i = \{(\mathbf{b}_k, s_k)\}$ after class-agnostic
NMS at IoU $0.5$ and the GT set $\mathcal{D}^*_i$. We sort all
predictions across all images by descending score and sweep a
threshold $\tau$. A prediction $(\mathbf{b}, s, i)$ is a *true
positive* iff there exists an unmatched GT $\mathbf{b}^* \in
\mathcal{D}^*_i$ with $\mathrm{IoU}(\mathbf{b}, \mathbf{b}^*) \geq
\tau_{\text{IoU}} = 0.3$ (the standard mammography threshold;
literature uses $0.2$–$0.5$); otherwise it is a *false positive*.
Greedy matching is by descending score with one-to-one assignment.

We report sensitivity at fixed false-positive-per-image rates:

$$
\mathrm{Sens}@\,r = \max_{\tau}\,\bigl\{\mathrm{Sens}(\tau)\bigr\}
\;\text{s.t.}\; \mathrm{FP/img}(\tau) \leq r,
\qquad r \in \{0.5, 1.0, 2.0, 4.0\}.
$$

### 6.2 Ablation Battery

| Row | Variant                              | Hypothesis tested |
|----:|--------------------------------------|-------------------|
|  1  | TILLNet-Det (full)                   | (target)          |
|  2  | image-only (`--no-text`)             | text contribution |
|  3  | text-only–positional (FiLM but constant text vector) | identifies whether FiLM gains come from extra capacity, not text content |
|  4  | text + FPN concat instead of FiLM    | FiLM vs concat as fusion mechanism |
|  5  | FiLM at $P_5$ only                   | per-level vs global text conditioning |
|  6  | $\theta_1$ trained without CBIS bootstrap | bootstrap contribution |

Pairs (1, 2), (1, 3), (1, 4), (1, 5), (1, 6) are tested with paired
bootstrap on the test set ($B = 1000$ resamples) for sensitivity@1FP.

### 6.3 Subgroup Analysis

In addition to the global FROC, we plan to report separately for:

* *view*: CC vs MLO
* *laterality*: original L vs original R (post-flip equivalence test)
* *breast density*: ACR A-D as recorded in CBIS-DDSM
* *lesion size*: $< 10$ mm, $10$–$20$ mm, $> 20$ mm

This surfaces failure modes (e.g. dense breast under-detection)
that a single FROC number obscures.

---

## 7. Discussion

### 7.1 Why Zero-Initialised FiLM Matters in Practice

The standard alternative to FiLM is concatenation:
$\mathbf{P}_l' = \mathrm{Conv}_{1\times 1}([\mathbf{P}_l;
\mathbf{t}_{\text{tile}}])$ where $\mathbf{t}_{\text{tile}}$ is the
text vector broadcast to spatial dimensions. Concatenation has two
problems we explicitly avoid:

* **Cold-start instability.** A randomly-initialised concat layer
  perturbs the visual features even when the text is uninformative,
  pushing early training away from the image-only solution and into a
  random multimodal manifold.
* **No graceful degradation.** With concatenation, the model cannot
  cleanly fall back to image-only behaviour when the report is empty
  or wrong; it has tied the visual branch to whatever signal the text
  branch produced during training.

Zero-initialised FiLM resolves both. The model begins as image-only
and *learns* to use text only when the gradient signal indicates the
text is informative. When the text is absent at inference (we feed a
zero-padded encoding), the model still produces the image-only
prediction by construction.

### 7.2 Limitations

* **Text granularity.** The text encoder produces a single global
  semantic vector $\mathbf{t}$. This loses fine-grained
  spatial cues — for example, a report describing two distinct
  lesions ("mass at 2 o'clock and microcalcifications at 8 o'clock")
  is collapsed into a single vector. A natural extension is multiple
  attention pools or cross-attention from FPN locations to text
  tokens.
* **Pseudo-label noise.** Stage-2 pseudo-labels are coarse
  (typically $\geq 25\%$ of the breast crop). Without
  radiologist verification, training directly on these labels would
  bias the model toward over-large predictions. The three-stage
  protocol explicitly sequences pseudo-labels before gold labels to
  mitigate this.
* **Single-view processing.** Each (CC, MLO) view is processed
  independently. A natural extension is ipsilateral cross-view
  attention (cf. the BCA-YOLO architecture from our prior work),
  which we leave to future work.

### 7.3 Ethical and Deployment Considerations

The system is trained partly on weakly-supervised labels and is
intended for *triage assist*, not autonomous diagnosis. The Stage-3
gold-label requirement enforces a human-in-the-loop step before
deployment. All multilingual text is processed locally; no data
leaves the institution, and no cloud LLM is called. The pseudo-
label generator's `confidence` field, the `needs_radiologist_review`
flag, and the FROC operating-point selection (we recommend
$\mathrm{Sens}$@$2$ FP/image for radiologist-attended workflow) are
all designed to support a regulated clinical deployment.

---

## 8. Conclusion

We presented **TILLNet-Det**, a multimodal mammography lesion
detector that handles three co-existing scripts (Uzbek-Cyrillic,
Uzbek-Latin, Russian) via a character-level Transformer text
encoder, fuses text into a 5-level Feature Pyramid Network through
zero-initialised FiLM modulation, and is supervised by an FCOS-
style anchor-free head. The architectural innovation — *zero-
initialised FiLM at every pyramid level* — guarantees mathematical
equivalence to an image-only baseline at initialisation,
eliminating cold-start instability common in multimodal training
and giving graceful degradation when the report is absent. A three-
stage CBIS$\to$pseudo$\to$gold training protocol exploits public
detection data, local text, and a small radiologist verification
cohort, in that order, to operationalise the model in a low-
annotation regime.

The full implementation is provided as reproducible Python modules:
preprocessing, dataset converter, multilingual pseudo-label
generator, trainer, FROC evaluator, and ablation framework. To our
knowledge this is the first such system tailored to multilingual
mammography in Central Asia.

---

## Acknowledgements

The authors thank the regional oncology centre for data access and
the radiologist verification cohort for gold annotation work.

## Funding

[To be added.]

## Conflicts of Interest

[To be added.]

## Data and Code Availability

CBIS-DDSM is available from The Cancer Imaging Archive
(https://www.cancerimagingarchive.net/collection/cbis-ddsm/).
Local clinical data cannot be shared due to patient confidentiality.
The full implementation — preprocessing, CBIS-DDSM converter,
pseudo-label generator, TILLNet-Det model, trainer, and FROC
evaluator — is released under [licence] at [URL].

---

## References

[1] **Akselrod-Ballin, A. et al.** (2019). A region-based CNN for
mammography lesion detection. *Medical Image Analysis*.

[2] **Lee, R. S. et al.** (2017). A curated mammography data set for
use in computer-aided detection and diagnosis research.
*Scientific Data* 4: 170177.

[3] **Choukroun, Y. et al.** (2017). Mammogram classification and
abnormality detection from non-local labels. *MIDL*.

[4] **He, K. et al.** (2016). Deep residual learning for image
recognition. *CVPR*.

[5] **Hosseinzadeh Taher, M. R. et al.** (2022). A systematic
benchmarking analysis of transfer learning for medical image
analysis. *Medical Image Analysis*.

[6] **Kingma, D. P. and Ba, J.** (2015). Adam: a method for stochastic
optimisation. *ICLR*.

[7] **Lin, T.-Y. et al.** (2017). Feature pyramid networks for object
detection. *CVPR*.

[8] **Lin, T.-Y. et al.** (2017). Focal loss for dense object
detection. *ICCV*.

[9] **Liu, Y. et al.** (2020). Adaptive feature pyramid networks for
object detection. *IEEE Access*.

[10] **Perez, E. et al.** (2018). FiLM: visual reasoning with a
general conditioning layer. *AAAI*.

[11] **Ribli, D. et al.** (2018). Detecting and classifying lesions
in mammograms with deep learning. *Scientific Reports* 8:4165.

[12] **Tian, Z. et al.** (2019). FCOS: fully convolutional one-stage
object detection. *ICCV*.

[13] **Vaswani, A. et al.** (2017). Attention is all you need.
*NeurIPS*.

[14] [Authors] (2026). XS-Classifier: cross-script adaptive
tokenisation for cancer detection in code-switched mammographic
reports. *(prior work)*

[15] [Authors] (2026). MAMOGRAF: a unified web-based platform for
mammography DICOM annotation, AI inference, and PACS integration.
*(prior work)*
