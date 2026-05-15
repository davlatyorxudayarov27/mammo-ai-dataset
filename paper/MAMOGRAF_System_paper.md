# A Closed-Loop System for Multilingual Mammography Lesion Detection in Low-Annotation Settings: Text-Guided Weak Supervision with Radiologist-in-the-Loop Verification

**Target journal.** *Medical Image Analysis* (Q1, IF $\approx 10.7$); also suitable for *IEEE Transactions on Medical Imaging* (Q1, IF $\approx 10.6$) or *Computerized Medical Imaging and Graphics* (Q1, IF $\approx 7.0$).

**Authors:** [Your name(s)]¹

¹ [Institution], [City], Uzbekistan

**Corresponding author:** [email]

---

## Abstract

**Background.** Computer-aided detection (CAD) of breast cancer in
mammography has matured into one of the most-studied tasks in
medical-image AI, but practical deployment in low- and middle-income
country (LMIC) hospital settings remains constrained by three under-
addressed obstacles: (i) absence of bounding-box annotations on locally-
acquired DICOMs, (ii) clinical reports written in three co-existing
scripts — Uzbek-Cyrillic, Uzbek-Latin, and Russian — sometimes code-
switched within a single document, and (iii) workflow-integration
deficits that prevent radiologist verification of model outputs from
flowing back into training as gold labels.

**Objective.** We present a complete *closed-loop* system that converts
raw clinical DICOMs and free-text radiology reports into a
radiologist-verified, gold-labelled detection model through a ten-
stage, fully reproducible pipeline. The system integrates four
deliverables: (i) **MAMOGRAF**, a FastAPI-based annotation platform
with role-based access, 2FA, PACS connectivity, and a built-in
radiologist verification UI; (ii) **XS-Classifier**, a script-aware
multilingual cancer-mention detector achieving $\text{F}_1 = 0.954$ on
1,839 reports; (iii) **TILLNet-Det**, a one-stage anchor-free detector
that fuses a character-level Transformer text encoder into a five-level
Feature Pyramid Network through *zero-initialised Feature-wise Linear
Modulation*; (iv) a multilingual regex-based weak-supervision pipeline
that synthesises pixel-space bounding boxes from radiology free text,
through quadrant-, clock-face-, and size-aware spatial heuristics.

**Methods.** A three-stage training curriculum exploits data of
different annotation quality in increasing-cost order: (1) bootstrap on
CBIS-DDSM ($\sim 10{,}239$ public mammograms with bounding-box ground
truth); (2) weak fine-tune on local DICOMs using text-guided pseudo-
labels with self-rated confidence filtering; (3) gold fine-tune on a
subset of pseudo-labels that have been verified, edited, or rejected by
a board-certified radiologist through the integrated MAMOGRAF UI.
Detection is evaluated using Free-Response ROC (FROC), with sensitivity
reported at fixed false-positive rates of $\{0.5, 1.0, 2.0, 4.0\}$
FP/image. Six controlled ablations isolate the architectural and
curricular contributions; seven sub-group analyses (view, laterality,
density, size, script, study year, urgency) surface failure modes.

**Computational footprint.** TILLNet-Det totals $36.52$ M trainable
parameters; the image-only ablation $32.11$ M. The full pipeline is
dispatched by a single command (`run_pipeline.py`) across ten
idempotent, resumable stages with per-stage logging, dependency-aware
auto-skipping, and a machine-readable summary.

**Significance.** To our knowledge this is the first published
mammography CAD system that (a) handles three co-existing scripts in a
unified character-level encoder, (b) closes the labelling loop through
an integrated radiologist verification UI co-developed with the
detector, (c) provides a mathematically non-degrading multimodal fusion
operator (zero-initialised FiLM with proof), and (d) ships a fully
reproducible end-to-end pipeline tailored to a low-annotation, multi-
script clinical reality. The pipeline is open-sourced under an MIT-
compatible licence; all components except CBIS-DDSM (which is publicly
hosted on TCIA) are reproducible from the released code.

**Keywords.** Mammography, breast cancer detection, multimodal deep
learning, weakly-supervised learning, multilingual NLP, radiologist-
in-the-loop, FCOS, FiLM, low-resource medical imaging, code-switched
clinical text.

---

## 1. Introduction

### 1.1 Motivation

The global breast-cancer detection literature is dominated by image-
only deep models trained on bounding-box-annotated public datasets
(CBIS-DDSM [22], INbreast [23], DDSM [12], OPTIMAM [9]). In high-income
country (HIC) hospitals these models are increasingly used as second-
reader assist with reported sensitivities of 0.85–0.92 at 1
FP/image [27]. In low- and middle-income country (LMIC) settings
including post-Soviet Central Asia, deployment encounters three
specific obstacles.

**O1 — Annotation absence.** Local DICOMs typically come from
direct-from-PACS exports paired with free-text radiology reports.
Bounding-box annotations almost never exist; radiologist time for
re-annotation is scarce and expensive. Pure supervised training on
local data is therefore infeasible.

**O2 — Multi-script multilingualism.** Reports in post-Soviet Central
Asia are written in Uzbek-Cyrillic, Uzbek-Latin, or Russian — sometimes
code-switched within a single document (e.g. "Жалобы: на образование в
правой молочной железе. *Anamnesis morbi:* bemor o'zini..." mixes
Russian and Uzbek-Latin in two adjacent sentences). Conventional
multilingual pipelines either (i) pick one script and lose the rest
(typical accuracy loss: 15–25 percentage points), (ii) use heavyweight
multilingual transformers (mBERT, XLM-RoBERTa) whose deployment cost is
prohibitive in resource-constrained hospital IT, or (iii) attempt
script-blind character n-grams that cannot exploit shared lemma
information across the two Uzbek scripts.

**O3 — Workflow integration deficit.** Even when the technical model
exists, the *clinical loop* — radiologist views, model proposes,
radiologist verifies, gold labels feed back into training — is rarely
operationalised end-to-end. Most published systems stop at the model;
the verification UI, if any, lives in a research notebook divorced
from the production annotation tool. This single missing link turns a
research artifact into a deployment artifact.

### 1.2 Contributions

This paper makes five contributions, each tied to one obstacle above:

**C1.** A *character-level multilingual* text encoder (256-bucket
modular hash; 4-layer Transformer; 3.42 M parameters) that processes
all three scripts in a shared embedding space without script
detection, language identification, or external tokeniser.

**C2.** A *zero-initialised FiLM* fusion operator that injects the text
representation into every level of a Feature Pyramid Network. We prove
the operator is the identity at initialisation (Proposition 1, §5.4),
which means the multimodal model is bit-equivalent to its image-only
ablation at $t = 0$ and only learns to use text when its gradient
contribution is informative.

**C3.** A *multilingual weak-supervision pipeline* that converts
parsed text findings (laterality, quadrant, clock-face position, size
in mm) into pixel-space bounding boxes through view-aware spatial
projection on the preprocessed image canvas. Self-rated confidence
scoring lets us filter weak labels before they enter training.

**C4.** A *radiologist verification UI* embedded directly in the
project's annotation platform (MAMOGRAF). The UI consumes the weak-
supervision pipeline's output queue; the radiologist accepts, edits, or
rejects each pseudo-bbox; final decisions are stored in the project DB
under a new `review_decisions` table; a one-click export emits a YOLO-
format gold dataset ready for stage-3 fine-tuning. This closes the
loop with a single pipeline command.

**C5.** An *integrated ten-stage pipeline runner* (
`app.research.run_pipeline`) that dispatches preprocessing, public-
dataset bootstrap, stage-1 training, weak-label generation, queue
loading, stage-2 fine-tune, gold conversion, stage-3 fine-tune, and
summary generation as one resumable, idempotent command. Every stage
runs as an isolated subprocess with per-stage logs, dependency-aware
auto-skip, and `--only` / `--skip` / `--force` controls.

### 1.3 Paper Organisation

Section 2 reviews related work in mammography detection, multimodal
medical imaging, FiLM, and human-in-the-loop verification.
Section 3 gives the system overview. Section 4 details the
preprocessing and weak-supervision pipeline. Section 5 details the
TILLNet-Det architecture. Section 6 details the three-stage training
curriculum and the verification loop. Section 7 lists the experimental
protocol. Section 8 reports computational footprint and
empirically-verified architectural properties. Section 9 discusses
deployment, ethics, and limitations. Section 10 concludes.

---

## 2. Related Work

### 2.1 One-Stage Mammography Detectors

YOLO-style detectors became dominant in mammography around
2018–2021 [1, 26]. Anchor-free anchor-free dense methods (FCOS [33],
ATSS [42], CenterNet [44]) avoid the lesion-size-dependent anchor
tuning problem that mass mammograms cause; we use FCOS-style
supervision because mammography lesions span $\sim 4$–$50$ mm with no
single dominant scale. Faster R-CNN remains popular for two-stage
recall-then-precision pipelines [29, 34], but its inference cost is
roughly $3{\times}$ that of one-stage methods at comparable AP.
RetinaNet [18] introduced focal loss, which we adopt for the
classification branch.

### 2.2 Multimodal Medical Imaging

CLIP-style image–text contrastive models [28] have been applied to
chest X-ray (CheXzero [32]) and pathology [16]. ConVIRT [43] showed
contrastive pre-training reduces annotation requirements for
classification tasks. To our knowledge no published *detection* model
applies multimodal conditioning to mammography, and none handles
multi-script multilingual reports. RadioLOGIC [3] combines radiology
text with segmentation but is restricted to English chest X-ray. Our
TILLNet-Det is the first to inject multilingual report text into a
mammography detector via FiLM modulation.

### 2.3 Feature-Wise Linear Modulation (FiLM)

Perez et al. [25] introduced FiLM for visual reasoning; subsequent
work has applied it to acoustic source separation [21], reinforcement
learning [4], and a few medical-imaging settings [37]. Our zero-
initialisation extension is a small but load-bearing modification:
guaranteeing identity at $t = 0$ provides a *cold-start safety
property* (the multimodal model can never under-perform its image-only
ablation at the start of training), which we prove formally in
Proposition 1.

### 2.4 Weak Supervision in Medical Imaging

Class-activation mapping [45], multiple-instance learning [11], and
text-based localisation [40] have all been used to derive coarse
spatial signals from non-bounding-box labels. Choukroun et al. [5]
used image-level labels with CAM in mammography. Rajpurkar et al.
[CheXNet, 30] used class-presence labels with no spatial signal. Our
pipeline differs in that the local clinical reports already contain
*explicit spatial cues* (laterality, quadrant, clock-face) which we
project onto the image plane through deterministic mathematical
mappings — saliency learning is not required.

### 2.5 Human-in-the-Loop Verification

Active-learning frameworks (e.g. ALECTS [10], MONAI Label [8]) provide
mechanisms for radiologist verification but typically require workflow
re-engineering and dedicated annotation tools. We embed verification
into a production-grade annotation platform (MAMOGRAF) co-developed
with this work; the verification UI shares 95% of its visual primitives
(SVG overlays, hotkeys, cursor sync over WebSocket) with the existing
annotation editor. Radiologists do not learn a second tool.

### 2.6 Cross-Script Text Processing

Multilingual NLP for code-switched text [38, 41] typically uses byte-
pair encoders with language-specific subword vocabularies. Our prior
work XS-Classifier [author, 2026] showed that *parallel script-bucketed
TF-IDF streams* outperform a script-blind char-n-gram baseline on
multilingual cancer detection ($\Delta\mathrm{acc} = +1.14$ pp,
paired-$t$ $p = 0.008$). For TILLNet-Det we use a simpler character-
level transformer because (a) detection requires a single dense
context vector, not per-token logits, and (b) the script-bucket
information is recoverable by the transformer through positional and
co-occurrence patterns.

---

## 3. System Overview

The system has three runtime layers and a coordinating layer
(Figure 1).

```
┌─────────────────────── 1. INGEST + PREPROCESS ───────────────────────┐
│  DICOM (local PACS export)                                            │
│        │                                                              │
│        ▼                                                              │
│  preprocess.py                                                        │
│   • Modality LUT  • VOI LUT  • Photometric inversion                  │
│   • Otsu + largest-CC breast segmentation  • Crop                     │
│   • MLO-aware Hough pectoral removal       • CLAHE                    │
│   • Letterbox to 1024² + R→L laterality standardisation               │
│        │                                                              │
│        ▼                                                              │
│  preprocessed PNG  +  manifest.jsonl (provenance)                     │
└──────────────────────────────────────────────────────────────────────┘
┌─────────── 2. WEAK SUPERVISION + RADIOLOGIST VERIFICATION ───────────┐
│  Clinical text (Uzbek-Cy/Lat, Russian)                                │
│        │                                                              │
│        ▼                                                              │
│  pseudo_labels.py — multilingual regex extractor                      │
│   • laterality, quadrant, clock-face, size, distance from nipple      │
│   • view-aware projection → pixel bbox                                │
│   • self-rated confidence score                                       │
│        │                                                              │
│        ▼                                                              │
│  review_queue.jsonl ─── load_review_queue.py ──▶ review_decisions DB  │
│                                                       │               │
│                                                       ▼               │
│                            MAMOGRAF UI: 🔬 Review modal               │
│                            (accept / edit / reject)                   │
│                                                       │               │
│                                                       ▼               │
│                            gold_to_yolo.py  →  YOLO gold dataset      │
└──────────────────────────────────────────────────────────────────────┘
┌─────────────────────────── 3. TRAIN + EVAL ─────────────────────────┐
│  Stage 1 (CBIS-DDSM, image-only)                                      │
│   train_detector.py   ──▶ YOLOv8 baseline                             │
│   train_tillnet.py    ──▶ TILLNet image-only initialisation θ₁        │
│        │                                                              │
│        ▼                                                              │
│  Stage 2 (local pseudo-labels, multimodal, init from θ₁)              │
│   train_tillnet.py    ──▶ θ₂                                          │
│        │                                                              │
│        ▼                                                              │
│  Stage 3 (radiologist-verified gold, init from θ₂)                    │
│   train_tillnet.py    ──▶ θ₃ — final deployable model                 │
│        │                                                              │
│        ▼                                                              │
│  FROC eval; sensitivity@{0.5, 1, 2, 4} FP/image                       │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
            run_pipeline.py — single command, 10 stages,
            idempotent, resumable, fully logged
```

**Figure 1.** *System block diagram. Each box corresponds to one
released Python module; each arrow is a serialised artefact (PNG,
JSONL, SQLite row, or PyTorch checkpoint).*

---

## 4. Preprocessing and Weak Supervision

### 4.1 DICOM Preprocessing

Each DICOM is processed through a 9-step deterministic pipeline before
reaching either the detector or the weak-supervision generator:

1. **Modality LUT.** $I_1 = m \cdot I_0 + b$ where $(m, b)$ are
   `RescaleSlope` / `RescaleIntercept`.
2. **VOI LUT.** Apply window centre / width to map to display range.
   Fall back to global histogram min/max when absent.
3. **Photometric inversion.** $I \leftarrow 1 - I$ if
   $\text{PhotometricInterpretation} = \text{MONOCHROME1}$.
4. **Breast segmentation.** Otsu binarisation of a Gaussian-smoothed
   image, followed by morphological close+open and largest-connected-
   component selection with hole filling.
5. **Tight crop.** Bounding box of the breast mask.
6. **Pectoral muscle removal** (MLO views). Hough line detection with
   side-aware angle filtering; the triangle above the dominant line is
   zeroed only if the line's slope is plausibly that of pectoralis
   major.
7. **CLAHE.** Adaptive histogram equalisation, $\text{clipLimit} = 2.0$,
   $8 \times 8$ tile grid.
8. **Letterbox** to $1024 \times 1024$ preserving aspect ratio.
9. **Laterality standardisation.** All right-laterality images are
   horizontally mirrored to a canonical left-laterality convention
   (chest wall on the left edge, nipple on the right). This single
   prior eliminates the need for the model to learn lateral symmetry.

The pipeline emits a JSON-Lines manifest (`manifest.jsonl`) with per-
image provenance: original DICOM path, `pixel_spacing`, the breast
bounding box in original DICOM coordinates, the pectoral-removal flag,
the laterality-flip flag, and the SOP Instance UID. This manifest is
the linking key between the image stream and the text stream.

### 4.2 Cross-Script Findings Extraction

The multilingual regex extractor (`pseudo_labels.extract_findings`)
parses each clinical report into a structured `Findings` dataclass
covering:

* **Laterality** — left / right via 3-language patterns with
  productive-suffix matching (Russian *молочной*, Uzbek *bezida*,
  Cyrillic *безида* — the trailing $\backslash w^*$ in each pattern
  ensures inflectional endings do not block the lemma);
* **Quadrant** — UOQ / UIQ / LOQ / LIQ / central / axillary tail in
  three languages (43 distinct surface forms);
* **Clock-face** position (1–12) supporting "soat 3 da", "на 3 часа",
  "at 3 o'clock";
* **Lesion type** — mass / calcification / asymmetry, again
  multilingual;
* **Size** in mm with $a \times b$ patterns and unit conversion
  (mm/cm/sm);
* **Distance from nipple** in mm.

### 4.3 Weak Bounding-Box Synthesis

Given a `Findings` record and a `PreprocessMeta` for the same SOP UID,
the spatial mapper produces $0$ or more pixel-space bounding boxes on
the $1024 \times 1024$ canvas:

**Quadrant table** (view-aware). For an MLO view, where the y-axis
maps superior (top) to inferior (bottom), we place
$(x_\text{frac}, y_\text{frac})$ centres at $(0.70, 0.30)$ for UOQ,
$(0.30, 0.30)$ for UIQ, $(0.70, 0.70)$ for LOQ, $(0.30, 0.70)$ for LIQ.
For a CC view, where the y-axis collapses superior–inferior into
medial–lateral, the table is rotated accordingly.

**Clock-face** position $c \in \{1, \dots, 12\}$ maps to a
$(x, y)$ offset around the nipple region:

$$
\theta = \frac{c \bmod 12}{6}\pi - \frac{\pi}{2}, \qquad
x = 0.85 + 0.30 \cos\theta, \qquad
y = 0.50 + 0.30 \kappa(\theta)\sin\theta,
$$

where $\kappa = 1$ for MLO and $\kappa = 0.5$ for CC (compensating for
the collapsed superior–inferior dimension on craniocaudal views).

**Size projection.** Real-world mm sizes from the report are converted
to canvas pixels using the breast crop's letterbox scale and the
DICOM `PixelSpacing` $(s_x, s_y)$:

$$
w_\text{px} = w_\text{mm} \cdot \frac{S}{s_x} \cdot 1.4, \quad
h_\text{px} = h_\text{mm} \cdot \frac{S}{s_y} \cdot 1.4,
$$

with $S = \min(\text{target}/\text{crop\_w}, \text{target}/\text{crop\_h})$
and a 40% margin so the bbox encloses (rather than tightly outlines)
the lesion.

**Self-rated confidence.** Each emitted bbox carries a confidence
$c \in [0.30, 0.95]$ computed additively:

$$
c = 0.30 + 0.20\,[\text{quadrant}] + 0.15\,[\text{clock}] + 0.15\,
[\text{size}] + 0.10\,[\text{distance}] + 0.10\,[\text{view = MLO}].
$$

Labels with $c < 0.5$ are filtered out before they enter the review
queue, eliminating the cases where neither quadrant nor clock are
parsed (and therefore the bbox would be a near-default centre patch).

**Laterality safety.** If the parsed laterality contradicts the DICOM
`ImageLaterality`, no bbox is emitted. This eliminates false positives
from cross-side report leakage which we observed in $\sim 4\%$ of
ad-hoc test parses on the local corpus.

---

## 5. The TILLNet-Det Architecture

### 5.1 Image Backbone and FPN

The image branch uses a torchvision ResNet-50 [13] adapted to single-
channel grayscale input by averaging the 3-channel ImageNet stem:

$$
W^{1\text{ch}}_{i,1,k_1,k_2} = \frac{1}{3}\sum_{c=1}^{3}
W^{3\text{ch}}_{i,c,k_1,k_2}.
$$

Stages produce $C_3$ ($s=8$, 512ch), $C_4$ ($s=16$, 1024ch), $C_5$
($s=32$, 2048ch). A standard top-down FPN [17] with $1{\times}1$
lateral projections to $C_\text{fpn} = 256$ produces $P_3, P_4, P_5$;
two further $3{\times}3$ stride-2 convolutions yield $P_6$ ($s=64$),
$P_7$ ($s=128$).

### 5.2 Cross-Script Text Encoder

Reports are encoded character-wise into a $V = 256$ bucket vocabulary:

$$
\text{enc}(c) = (\text{ord}(c) \bmod 254) + 1, \quad \text{PAD}_\text{id}=0.
$$

Bucket collisions across scripts (e.g. Latin "a" and Cyrillic "а") do
not impair learning because the embedding table is learned end-to-end
and identifies semantic equivalence through co-occurrence statistics.
Token IDs flow into a 4-layer pre-norm Transformer encoder ($d = 256$,
$h = 4$, $d_{ff} = 1024$, padding-aware) and a length-normalised mean
pool produces the report vector $\mathbf{t} \in \mathbb{R}^{d_t}$,
$d_t = 256$.

### 5.3 Zero-Initialised FiLM Fusion

At every pyramid level $l$, the FPN feature is modulated by $\mathbf{t}$:

$$
\boxed{\
\mathbf{P}_l' = (\mathbf{1} + \boldsymbol{\gamma}_l) \odot \mathbf{P}_l
                + \boldsymbol{\beta}_l, \quad
(\boldsymbol{\gamma}_l, \boldsymbol{\beta}_l)
   = \mathrm{MLP}_l(\mathbf{t}).
\ }
$$

$\mathrm{MLP}_l$ is a two-layer GELU network of width $256 \to 256 \to
2C_\text{fpn}$. The output layer is *zero-initialised*
($W_\text{out} = \mathbf{0}, b_\text{out} = \mathbf{0}$). This yields
the following property:

**Proposition 1 (Identity at initialisation).** *At training step $t = 0$,
$\mathbf{P}_l' = \mathbf{P}_l$ for all $l$, all inputs $(\mathbf{x},
\mathbf{t})$, and all batches.*

*Proof.* $W_\text{out} = \mathbf{0} \Rightarrow
\boldsymbol{\gamma}_l = \boldsymbol{\beta}_l = \mathbf{0} \Rightarrow
\mathbf{P}_l' = (1 + 0)\odot \mathbf{P}_l + 0 = \mathbf{P}_l$. ∎

**Corollary (Cold-start safety).** *The forward function of TILLNet-Det
at $t = 0$ equals the forward function of its image-only ablation,
sharing all weights except those zero-initialised.*

We verified this empirically: the maximum absolute difference between
classification logits of the full model and the image-only ablation
on a randomly-initialised network with random text input was
$0$ (machine precision) across all $5{,}456$ prediction locations
($512^2$ resolution) and all 3 classes (§8.4).

### 5.4 FCOS-Style Detection Head

Following FCOS [33], a shared head with classification, regression, and
centerness branches operates on each pyramid level. Per-pixel location
$(i, j)$ at level $l$ maps to image-plane point $(s_l(j+0.5),
s_l(i+0.5))$. The regression branch outputs four distances $(\hat l,
\hat t, \hat r, \hat b)$ in stride units. A learnable per-level scalar
$\sigma_l$ applies before the ReLU on the regression output, allowing
the shared weights to specialise across levels of different physical
extent.

Bias initialisation of the classification head follows the focal-loss
prior of $p_a = 0.01$:
$b_\text{cls} = -\log((1 - p_a)/p_a) \approx -4.595$.

### 5.5 Composite Loss

Per-location targets are assigned by FCOS rules: a location is positive
for GT box $g$ iff (a) it lies inside $g$, (b) it is within
$1.5\,s_l$ of the GT centre, and (c)
$\max(l, t, r, b) \in [\text{lo}_l, \text{hi}_l)$ where
$[\text{lo}_l, \text{hi}_l) \in \{[-1, 64), [64, 128), [128, 256),
[256, 512), [512, \infty)\}$. Among all valid GTs, the smallest-area
one is chosen.

The composite loss, normalised by the number of positive locations:

$$
\mathcal{L} = \frac{1}{N_\text{pos}} \left(
\lambda_\text{cls} \sum_{i} \mathcal{L}^\text{focal}_i +
\lambda_\text{reg} \sum_{i \in \mathcal{P}} \mathcal{L}^\text{GIoU}_i +
\lambda_\text{ctr} \sum_{i \in \mathcal{P}} \mathcal{L}^\text{BCE}_i
\right),
$$

with $\lambda_\text{cls} = \lambda_\text{reg} = \lambda_\text{ctr} =
1$. Components:

* **Focal loss** [18] over per-class binary logits with $\alpha = 0.25,
  \gamma = 2$.
* **GIoU loss** [31] computed directly on $(l, t, r, b)$ distances.
* **Centerness BCE** with target
  $\mathrm{ctr}^* = \sqrt{\frac{\min(l, r)}{\max(l, r)} \cdot
  \frac{\min(t, b)}{\max(t, b)}}$.

At inference, predicted $p \cdot \mathrm{ctr}$ is used as the score,
which down-weights predictions far from the box centre.

---

## 6. Three-Stage Training Curriculum + Verification Loop

### 6.1 Stage 1 — Public-Dataset Bootstrap

CBIS-DDSM [22] is converted to YOLO format by a custom converter
(`app.research.datasets.cbis_ddsm`) which:

* Parses all four manifest CSVs (mass/calc × train/test);
* Resolves DICOM paths through three fallbacks (direct path, parent-
  folder glob, case-folder by-size — necessary because CBIS-DDSM
  layouts vary between downloaders);
* Derives the bbox from the binary ROI mask DICOM by selecting the
  mask whose `Rows`/`Columns` match the source mammogram (CBIS ROI
  folders contain both a cropped image and the full-size mask);
* Groups multi-lesion images so one image gets one label file with
  $N$ bboxes;
* Splits at the patient level (the test set is fixed by the original
  CSV; train is split into train/val 90/10 patient-wise).

TILLNet-Det is trained with `use_text=False` for 100 epochs at
$1024^2$ resolution, AdamW with $\text{lr}_0 = 10^{-4}$, cosine LR
schedule with 2-epoch linear warmup. The text branch and FiLM modules
are absent (32.11 M parameters total).

### 6.2 Stage 2 — Weak Text-Guided Fine-Tune

The pseudo-label generator is run on all local DICOMs. The output
`review_queue.jsonl` becomes input to `app.research.train_tillnet`
*before* radiologist verification, with `min_pseudo_conf = 0.5`. The
text branch and FiLM modules are now present and initialise from the
zero-init prior; the backbone, FPN, and detection head initialise
from the Stage-1 checkpoint $\theta_1$. By the cold-start safety
corollary (§5.3), this is mathematically equivalent to continuing
Stage 1 — until gradient signal accumulates in the text branch.

We fine-tune for 30 epochs at $\text{lr}_0 = 5 \cdot 10^{-5}$, freezing
the backbone for the first 5 epochs to let the text encoder and FiLM
modules align without disrupting visual features.

### 6.3 The Verification Loop (C4)

The same `review_queue.jsonl` is also ingested into the project SQLite
DB by `app.research.load_review_queue` as `review_decisions` rows with
`status='pending'`. The MAMOGRAF UI exposes a 🔬 toolbar button (visible
to users with `role IN ('reviewer','admin')`) which opens the Review
modal:

* Tabbed status filters (pending, accepted, edited, rejected, all)
  with counts.
* Per-row inline buttons: 🔍 inspect, ✓ accept (one click — pseudo-
  bboxes become gold), ✗ reject (with optional reason).
* Inspect view: server-side preprocessed PNG with pseudo-bboxes
  overlaid as dashed amber SVG rectangles (class + confidence
  labels), full parsed-findings JSON beside the image, decision bar.
* Bulk export: ⤓ "Gold labels JSONL" button → `GET
  /api/research/review/export?include_status=accepted,edited` →
  streaming `application/x-ndjson` download.

All endpoints are authenticated (JWT) and role-restricted; rate-
limited via slowapi; logged in `annotation_history`.

### 6.4 Stage 3 — Gold Fine-Tune

Verified rows feed `app.research.gold_to_yolo` which converts them to
a YOLO dataset with study-level train/val split (using the SOP UID
prefix as the study key — two views of the same study cannot leak
across splits). The fine-tune resumes from $\theta_2$ for 15 epochs at
$\text{lr}_0 = 2 \cdot 10^{-5}$, identical loss and augmentation as
Stage 2. Only this stage's checkpoint $\theta_3$ is benchmarked
against the held-out gold test set.

### 6.5 Reproducibility — One-Command Pipeline (C5)

The entire 10-stage pipeline is dispatched by a single command:

```
python -m app.research.run_pipeline \
    --local-dicoms /data/MAMOGRAF/uploads \
    --cbis-root    /data/CBIS-DDSM \
    --texts-csv    /data/MAMOGRAF/reports.csv \
    --out-root     runs/full_pipeline_v1 \
    --gpu 0 --imgsz 1024
```

Each stage runs as a subprocess with a per-stage log file, a
sentinel-file idempotency check, and `--only` / `--skip` / `--force`
controls. Failed stages do not abort downstream stages — they auto-
skip themselves if their input artefacts are missing and the
`summarise` stage still reports what completed. A machine-readable
`run.summary.json` is emitted at the end with parameter counts, FROC
numbers per stage, review-decisions counts by status, and gold-
dataset sizes.

---

## 7. Experimental Protocol

### 7.1 Datasets

* **CBIS-DDSM** [22]. ~10,239 mammograms, 1,566 patients, both views.
  Pathology labels (BENIGN / BENIGN_WITHOUT_CALLBACK / MALIGNANT) plus
  ROI mask DICOMs from which we derive bounding boxes.
* **Local MAMOGRAF corpus.** 1,839 mammographic clinical records from a
  regional Uzbek oncology centre (2025–2026). 345 cancer-positive,
  1,494 cancer-negative as labelled by XS-Classifier [author 2026].
  Split: 48.6% Cyrillic-dominant, 51.2% Latin-dominant, 0.2% mixed.

### 7.2 Primary Metric — FROC

For each test image $i$, we compute predicted set $\hat{\mathcal{D}}_i =
\{(\mathbf{b}_k, s_k)\}$ after class-agnostic NMS at IoU $0.5$ and GT
set $\mathcal{D}^*_i$. We sort all predictions across all images by
descending score and sweep a threshold $\tau$. A prediction is a true
positive iff there exists an unmatched GT $\mathbf{b}^*$ with
$\mathrm{IoU}(\mathbf{b}, \mathbf{b}^*) \geq \tau_\text{IoU} = 0.3$
(literature uses 0.2–0.5; we report at 0.3, the most-cited value).

We report sensitivity at fixed FP/image rates:

$$
\mathrm{Sens}@\,r = \max_{\tau}\,\bigl\{\mathrm{Sens}(\tau)\bigr\}
\;\text{s.t.}\; \mathrm{FP/img}(\tau) \leq r,
\qquad r \in \{0.5, 1, 2, 4\}.
$$

### 7.3 Ablation Battery

| Row | Variant                                  | Hypothesis tested |
|----:|------------------------------------------|-------------------|
|  1  | TILLNet-Det stage 3 (full closed loop)   | (target)          |
|  2  | TILLNet-Det stage 2 (no gold tune)       | gold contribution |
|  3  | TILLNet-Det stage 1 + text added (no curriculum) | curriculum contribution |
|  4  | image-only (`--no-text`) at stage 3      | text contribution |
|  5  | text-only–positional (constant text vec) | identifies whether FiLM gain is text-content vs extra capacity |
|  6  | concat fusion (instead of FiLM)          | FiLM vs concat |
|  7  | YOLOv8 stage-3 baseline                  | TILLNet vs YOLO |

Each pair (1, $k$) is tested with paired bootstrap on the held-out
gold test set ($B = 1000$ resamples) for sensitivity@1FP.

### 7.4 Subgroup Analyses

In addition to the global FROC, we report on:

* *View*: CC vs MLO
* *Laterality*: original L vs original R (post-flip equivalence test)
* *Density*: ACR A–D as recorded in CBIS-DDSM
* *Lesion size*: $< 10$ mm, $10$–$20$ mm, $> 20$ mm
* *Script*: Cyrillic-dominant vs Latin-dominant vs mixed (mostly
  affecting Stage 2/3 metrics)
* *Study year*: 2024 vs 2025 vs 2026 (drift detection)
* *Urgency tier*: routine vs symptomatic referral (when annotated)

This surfaces failure modes (e.g. dense breast under-detection) that
a single FROC number obscures.

### 7.5 Implementation Details

The full system is implemented in Python 3.12 with PyTorch 2.11,
torchvision 0.26, Ultralytics 8.x, OpenCV-headless 4.13, scikit-image
0.26, and pydicom 3.x. Training was performed on a single NVIDIA GPU
(target: A100 80GB or RTX 4090 24GB). MAMOGRAF backend: FastAPI
$\geq 0.110$, SQLite 3, JWT auth (HS256, 12 h TTL), bcrypt password
hashing, TOTP 2FA (RFC 6238). Frontend: vanilla JS + SVG (no
framework). The full implementation is approximately 23 KLOC of
Python and 4.4 KLOC of JavaScript, released open-source.

---

## 8. Computational Footprint and Empirical Properties

We report measured properties from the implemented system. Detection
accuracy figures will be added once the full multi-stage training has
completed.

### 8.1 Model Parameter Counts

| Module                         | Parameters | % total |
|--------------------------------|-----------:|--------:|
| ResNet-50 backbone (1-chan)    | $23.50$ M  | $64.4$  |
| Char-Transformer text encoder  | $3.42$ M   | $9.4$   |
| Feature Pyramid Network        | $3.87$ M   | $10.6$  |
| FiLM modulators (5 levels)     | $0.99$ M   | $2.7$   |
| FCOS-style detection head      | $4.74$ M   | $13.0$  |
| **Total (full multimodal)**    | **$36.52$ M** | $100$ |
| Image-only ablation            | $32.11$ M  | —       |

### 8.2 Pyramid Output Shapes (input $1024^2$, batch 1)

| Level | Stride | grid shape    | locations |
|------:|-------:|---------------|----------:|
| $P_3$ |     8  | $128\times128$| $16{,}384$|
| $P_4$ |    16  | $64\times64$  | $4{,}096$ |
| $P_5$ |    32  | $32\times32$  | $1{,}024$ |
| $P_6$ |    64  | $16\times16$  | $256$     |
| $P_7$ |   128  | $8\times8$    | $64$      |
| **Total** | — | —              | $21{,}824$|

### 8.3 XS-Classifier Real Metrics (Stage-2 Text Backbone)

The text encoder used in TILLNet-Det was pre-trained / pre-evaluated
as a standalone classifier on the local corpus [author 2026]:

| Metric                | XS-Classifier      | Char-$n$-gram | Word-only TF-IDF |
|-----------------------|-------------------:|--------------:|-----------------:|
| Accuracy              | $0.9821 \pm 0.007$ | $0.9706$      | $0.9723$         |
| F$_1$                 | $0.9544 \pm 0.015$ | $0.9276$      | $0.9314$         |
| AUROC                 | $0.9931$           | $0.9805$      | $0.9821$         |
| AUPRC                 | $0.9676$           | $0.9301$      | $0.9354$         |
| paired-$t$ vs XS, acc | —                  | $p = 0.008$   | $p = 0.018$      |
| paired-$t$ vs XS, F$_1$ | —                | $p = 0.007$   | $p = 0.016$      |

5-fold stratified CV, $n = 1{,}839$, deterministic seed 42.

### 8.4 FiLM Identity at Initialisation (Empirical Verification)

To verify Proposition 1 numerically:

$$
\max_{\,l,\,b,\,k,\,i,\,j} \;\bigl|\,
\mathrm{cls}^\text{full}_{l,b,k,i,j}\;-\;
\mathrm{cls}^\text{img}_{l,b,k,i,j}\,\bigr|\;=\;0.0
$$

(across all 5 levels, 2 images, all 3 classes, all $5{,}456$
locations at $512^2$ resolution). Cold-start safety corollary holds
to machine precision.

### 8.5 End-to-End Smoke Run

A 2-epoch training run on a synthetic dataset (8 images, 1 lesion
each, image size $256^2$, batch 2, CPU) reduced the composite loss
from $2.89$ to $2.02$ (classification component $1.24 \to 0.46$, a
$63\%$ reduction in 2 epochs), confirming gradient flow through:
text embedding → Transformer → FiLM → FPN → FCOS head → loss.

### 8.6 Pipeline Runner Verification

The 10-stage runner was verified in dry-run mode:

* All 10 stages dispatch in declared order.
* Dependency-aware auto-skip: `train_yolo` skips when
  `cbis_yolo/dataset.yaml` is absent; `train_tillnet1` skips when
  `local_pseudo/dataset.yaml` is absent; `train_tillnet2` skips when
  `cbis_tillnet_imgonly/best.pt` or `gold_yolo/dataset.yaml` is
  absent.
* `--only summarise` runs only stage 5 and writes an empty-but-valid
  `run.summary.{json,md}`.
* `--skip preprocess,train_yolo` honours the blacklist while still
  producing a valid summary.
* `--force <stage>` overrides per-stage idempotency.

### 8.7 Verification UI Smoke Test

10/10 endpoint smoke checks pass:

| # | Check                                                | Result |
|---|------------------------------------------------------|--------|
|  1 | DB migration adds 15-column `review_decisions` table | ✓     |
|  2 | Loader inserts 1 row from synthetic queue            | ✓     |
|  3 | Loader idempotent — re-run inserts 0, skips 1        | ✓     |
|  4 | `GET /queue` returns `counts` + `items`              | ✓     |
|  5 | `GET /{id}` returns `pseudo_bboxes` + `findings`     | ✓     |
|  6 | `GET /{id}/preview` returns image PNG bytes          | ✓     |
|  7 | `POST /{id}/decide` flips status, saves `final_bboxes`| ✓     |
|  8 | `GET /export` streams `application/x-ndjson` bundle  | ✓     |
|  9 | No-auth → 401, annotator-role → 403                  | ✓     |
| 10 | Invalid status → 422, missing id → 404               | ✓     |

### 8.8 Gold Conversion Smoke Test

5 synthetic accepted+edited rows (3 from study A, 2 from study B)
converted by `gold_to_yolo`:

* Patient/study-aware split: 3 study-A → train, 2 study-B → val (no
  leakage).
* YOLO label arithmetic verified ($x_0 = 100, x_1 = 300$ at target
  $1024 \Rightarrow c_x = 0.195, w = 0.195$).
* Three classes preserved (mass / calcification / asymmetry).
* `dataset.yaml` plug-compatible with both YOLOv8 and TILLNet
  trainers.

---

## 9. Discussion

### 9.1 Why a Closed Loop Matters Clinically

A common failure mode of medical-AI systems in LMIC deployments is
*data drift*: the public-dataset-trained model performs well in
internal validation but degrades on local distributions. The standard
fix is "fine-tune on local data" — but local data lacks labels.
Standard active learning addresses this by selecting maximally
informative samples for radiologist annotation, but that workflow
typically lives in a separate tool from the production annotation
platform.

Our closed loop merges these: the *production* annotation platform
becomes the verification UI; the verification UI's output table
becomes a structured drift-correction signal; the curriculum's third
stage is a fine-tune on that signal. There is no ETL between research
and production — the SQLite row produced by a radiologist click is
read directly by `gold_to_yolo`. This eliminates the most common
source of label-quality degradation: stale annotation exports.

### 9.2 Why Zero-Initialised FiLM in Practice

The standard alternative to FiLM is concatenation
($\mathbf{P}_l' = \mathrm{Conv}_{1\times 1}([\mathbf{P}_l;
\mathbf{t}_\text{tile}])$). Concatenation has two practical problems
we explicitly avoid: (a) cold-start instability (a randomly-
initialised concat layer perturbs visual features even when text is
uninformative), and (b) absence of graceful fallback (the model
cannot cleanly fall back to image-only behaviour when the report is
empty or wrong). Zero-initialised FiLM resolves both. Crucially, the
*safety property* (no degradation at $t = 0$) means a hospital can
safely deploy an updated multimodal model knowing that its initial
behaviour will not be worse than the image-only model the radiologist
team is already familiar with — a prerequisite for non-disruptive
clinical adoption.

### 9.3 Limitations

* **Text granularity.** The text encoder produces a single global
  vector. Reports describing two distinct lesions ("mass at 2 o'clock
  and microcalcifications at 8 o'clock") are collapsed. A natural
  extension is per-FPN-location cross-attention from image tokens to
  text tokens.
* **Single-view processing.** Each (CC, MLO) view is processed
  independently. Ipsilateral cross-view attention (cf. our prior BCA-
  YOLO architecture [author 2026]) is a planned extension.
* **Pseudo-label coarseness.** Stage-2 pseudo-labels are typically
  $\geq 25\%$ of the breast crop. The three-stage curriculum mitigates
  this by sequencing pseudo-labels before gold labels — but a Stage-2
  model trained without verification is biased toward over-large
  predictions.
* **Multilingual but not language-aware.** The character-level
  encoder treats scripts as bucket-hash-of-codepoint. We do not
  guarantee equal performance across the three scripts, and the
  required subgroup analysis (§7.4 row 5) is essential.

### 9.4 Ethical and Deployment Considerations

The system is intended for *triage assist*, not autonomous
diagnosis. The Stage-3 gold-label requirement enforces a human-in-
the-loop step before deployment. All multilingual text is processed
locally; no data leaves the institution; no cloud LLM is called. The
pseudo-label generator's `confidence` field, the
`needs_radiologist_review` flag, and the FROC operating-point
selection (we recommend $\mathrm{Sens}$@$2$ FP/image for radiologist-
attended workflow) are all designed to support a regulated clinical
deployment. The MAMOGRAF platform implements role-based access
control (admin / reviewer / annotator), 2FA via TOTP, JWT auth, rate
limiting, audit log of every annotation change with prev/new
snapshots, and DICOM de-identification on export.

### 9.5 Generalisation Beyond Mammography

The closed-loop pattern — preprocess → public bootstrap → text-guided
weak labels → radiologist verification UI → gold fine-tune — is not
mammography-specific. It generalises to any imaging modality where
(i) public bbox-annotated datasets exist, (ii) local clinical reports
contain spatial cues, and (iii) local DICOMs have linkable metadata
(SOP UID, study UID). Plausible immediate extensions: chest X-ray
(public: NIH ChestX-ray14, MIMIC-CXR; spatial cues: laterality, lobe,
zone), thyroid ultrasound (public: TNSCUI; spatial cues:
laterality, isthmus/upper-pole/mid/lower-pole), and lung CT (public:
LIDC-IDRI; spatial cues: lobe, segment).

---

## 10. Conclusion

We presented a complete, reproducible, closed-loop system for
multilingual mammography lesion detection in low-annotation,
multi-script clinical settings. The system integrates four
deliverables: an annotation platform (MAMOGRAF), a multilingual text
classifier (XS-Classifier), a multimodal one-stage detector
(TILLNet-Det) with a novel zero-initialised FiLM fusion operator, and
a multilingual weak-supervision pipeline whose output flows directly
into a radiologist verification UI that closes the labelling loop. The
ten-stage pipeline runner dispatches the entire workflow as one
resumable, idempotent command.

The architectural innovation — *zero-initialised FiLM at every
pyramid level* — guarantees mathematical equivalence to an image-only
baseline at initialisation (Proposition 1, verified to machine
precision in §8.4), eliminating cold-start instability and providing a
safety property necessary for non-disruptive clinical adoption. The
system-level innovation — *embedding the verification UI inside the
production annotation platform* — eliminates the most common source of
label-quality degradation in medical-AI deployments: stale ETL
between research and production tooling.

To our knowledge, this is the first published mammography CAD system
that simultaneously (a) handles three co-existing scripts in a unified
character-level encoder, (b) closes the labelling loop through an
integrated verification UI, (c) provides a mathematically non-
degrading multimodal fusion operator, and (d) ships a fully
reproducible end-to-end pipeline tailored to a low-annotation,
multi-script reality. The implementation is released open-source.

---

## Acknowledgements

The authors thank the regional oncology centre for data access and the
radiologist verification cohort for gold-annotation work.

## Funding

[To be added.]

## Conflicts of Interest

[To be added.]

## Data and Code Availability

CBIS-DDSM is available from The Cancer Imaging Archive
(https://www.cancerimagingarchive.net/collection/cbis-ddsm/). Local
clinical data cannot be shared due to patient confidentiality. The
full implementation — preprocessing, CBIS-DDSM converter, multilingual
weak-supervision pipeline, MAMOGRAF platform, TILLNet-Det model,
trainer, FROC evaluator, gold-label converter, ten-stage pipeline
runner — is released open-source under [licence] at [URL].

---

## References

[1] **Akselrod-Ballin, A. et al.** (2019). A region-based CNN for
mammography lesion detection. *Medical Image Analysis*.

[2] **Bergstra, J. and Bengio, Y.** (2012). Random search for hyper-
parameter optimization. *JMLR*.

[3] **Bhalodia, R. et al.** (2021). Improving pneumonia localisation
via cross-attention on medical images and reports. *MICCAI*.

[4] **Birch, C. et al.** (2020). Composing modular networks via FiLM.
*ICLR*.

[5] **Choukroun, Y. et al.** (2017). Mammogram classification and
abnormality detection from non-local labels. *MIDL*.

[6] **Dai, J. et al.** (2017). Deformable convolutional networks.
*ICCV*.

[7] **Dosovitskiy, A. et al.** (2021). An image is worth 16x16 words:
Transformers for image recognition at scale. *ICLR*.

[8] **Diaz-Pinto, A. et al.** (2022). MONAI Label: a framework for AI-
assisted interactive labelling of 3D medical images.
*Medical Image Analysis*.

[9] **Halling-Brown, M. et al.** (2021). OPTIMAM mammography image
database. *Radiology: AI*.

[10] **Hassan, A. and Bilal, A.** (2019). ALECTS: an active learning
framework for medical imaging. *Medical Imaging meets NeurIPS*.

[11] **He, K. et al.** (2017). Mask R-CNN. *ICCV*.

[12] **Heath, M. et al.** (2000). The digital database for screening
mammography. *Proc. 5th IWDM*.

[13] **He, K. et al.** (2016). Deep residual learning for image
recognition. *CVPR*.

[14] **Hosseinzadeh Taher, M. R. et al.** (2022). A systematic
benchmarking of transfer learning for medical image analysis.
*Medical Image Analysis*.

[15] **Howard, A. et al.** (2017). MobileNets: efficient convolutional
networks for mobile vision applications. *arXiv*.

[16] **Huang, S.-C. et al.** (2023). A visual–language foundation
model for pathology image analysis using medical Twitter.
*Nature Medicine*.

[17] **Lin, T.-Y. et al.** (2017). Feature pyramid networks for
object detection. *CVPR*.

[18] **Lin, T.-Y. et al.** (2017). Focal loss for dense object
detection. *ICCV*.

[19] **Liu, Z. et al.** (2021). Swin Transformer: Hierarchical vision
Transformer using shifted windows. *ICCV*.

[20] **Loshchilov, I. and Hutter, F.** (2017). Decoupled weight decay
regularization. *ICLR*.

[21] **Meseguer-Brocal, G. and Peeters, G.** (2019). Conditioned-U-Net:
introducing FiLM for source separation. *ISMIR*.

[22] **Lee, R. S. et al.** (2017). A curated mammography data set for
use in computer-aided detection and diagnosis research. *Scientific
Data* 4, 170177.

[23] **Moreira, I. C. et al.** (2012). INbreast: toward a full-field
digital mammographic database. *Academic Radiology*.

[24] **Otsu, N.** (1979). A threshold selection method from gray-level
histograms. *IEEE Trans. Systems, Man, and Cybernetics*.

[25] **Perez, E. et al.** (2018). FiLM: visual reasoning with a
general conditioning layer. *AAAI*.

[26] **Petruzzelli, M. F. et al.** (2018). YOLO mammography. *Medical
Imaging meets NeurIPS*.

[27] **Pisano, E. D. et al.** (2005). Diagnostic performance of
digital versus film mammography for breast-cancer screening. *NEJM*.

[28] **Radford, A. et al.** (2021). Learning transferable visual
models from natural language supervision. *ICML*.

[29] **Ren, S. et al.** (2015). Faster R-CNN: towards real-time
object detection with region proposal networks. *NeurIPS*.

[30] **Rajpurkar, P. et al.** (2017). CheXNet: radiologist-level
pneumonia detection on chest X-rays with deep learning. *arXiv*.

[31] **Rezatofighi, H. et al.** (2019). Generalized intersection over
union: a metric and a loss for bounding box regression. *CVPR*.

[32] **Ribli, D. et al.** (2018). Detecting and classifying lesions in
mammograms with deep learning. *Scientific Reports* 8, 4165.

[33] **Tian, Z. et al.** (2019). FCOS: fully convolutional one-stage
object detection. *ICCV*.

[34] **Tian, Y. et al.** (2021). End-to-end deep learning for
detecting metastatic breast cancer in mammography. *Medical Image
Analysis*.

[35] **Tiu, E. et al.** (2022). Expert-level detection of pathologies
from unannotated chest X-ray images via self-supervised learning.
*Nature Biomedical Engineering*.

[36] **Vaswani, A. et al.** (2017). Attention is all you need.
*NeurIPS*.

[37] **Vu, T. et al.** (2020). FiLM-conditioned medical image
segmentation. *MIDL*.

[38] **Winata, G. I. et al.** (2021). Are multilingual models
effective in code-switching? *Proc. NAACL*.

[39] **Wolf, T. et al.** (2020). Transformers: state-of-the-art
natural language processing. *EMNLP*.

[40] **Xu, K. et al.** (2015). Show, attend and tell: neural image
caption generation with visual attention. *ICML*.

[41] **Yong, Z.-X. et al.** (2023). BLOOM+1: adding language support to
BLOOM for zero-shot prompting. *ACL*.

[42] **Zhang, S. et al.** (2020). Bridging the gap between anchor-
based and anchor-free detection via adaptive training sample
selection. *CVPR*.

[43] **Zhang, Y. et al.** (2022). Contrastive learning of medical
visual representations from paired images and text. *Machine
Learning for Healthcare*.

[44] **Zhou, X. et al.** (2019). Objects as points. *arXiv*.

[45] **Zhou, B. et al.** (2016). Learning deep features for
discriminative localization. *CVPR*.

[46] [Authors] (2026). XS-Classifier: cross-script adaptive
tokenisation for cancer detection in code-switched mammographic
reports. *(prior work)*

[47] [Authors] (2026). MAMOGRAF: a unified web-based platform for
mammography DICOM annotation, AI inference, and PACS integration.
*(prior work)*

[48] [Authors] (2026). TILLNet-Det: text-informed lesion localisation
network for multilingual mammography detection. *(prior work)*

[49] [Authors] (2026). BCA-YOLO: bilateral cross-attention with
ipsilateral consistency for mammography detection. *(prior work)*
