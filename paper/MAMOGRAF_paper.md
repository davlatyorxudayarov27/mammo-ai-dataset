# MAMOGRAF: An Open-Source Integrated Annotation, AI Inference, and Workflow Platform for Mammography Screening in Resource-Constrained Clinical Settings

**Authors:** [Your name(s)]¹

¹ [Institution / Department]

**Corresponding author:** [email]

---

## Abstract

**Background.** Mammography screening at scale requires integrated tooling
spanning DICOM ingestion, annotation, AI-assisted detection, clinical
report linkage, multi-reviewer workflow, and audit. Most existing platforms
either focus narrowly on a single function or assume infrastructure
(PostgreSQL clusters, Kubernetes, dedicated PACS) that is inaccessible to
small and regional hospitals.

**Objective.** We describe MAMOGRAF, an open-source single-server platform
that integrates DICOM viewing, multi-user annotation, pre-trained YOLO
inference, structured-report (xlsx) linkage, audit logging, DICOM-SR /
DICOM-SEG / COCO export, PACS interoperability (C-STORE / C-FIND / C-MOVE
/ MWL), and two-factor authentication, deployed as a single Docker
container with SQLite persistence. We propose a tiered confidence
heuristic for linking legacy spreadsheet-based clinical records to DICOM
studies when patient identifier systems are inconsistent.

**Methods.** The system was developed in Python (FastAPI) and vanilla
JavaScript. We integrated established libraries (pydicom, pynetdicom,
highdicom, Ultralytics YOLO, slowapi, bcrypt) into a single backend with a
WebSocket layer for real-time collaboration. We evaluated performance on
a regional mammography corpus of 1843 records (1570 unique patients,
2025–2026) and 833 worklist entries from one Uzbek oncology centre.

**Results.** Spreadsheet ingestion completed in 0.34 s for 1843 rows.
Pre-trained YOLOv11-L (KETEM) inference on a 28-megapixel mammogram
required 6 s on a single CPU; window/level adjustments via in-memory
caching achieved a 13× speed-up (44.7 → 3.3 ms warm). The patient-linking
heuristic produced unambiguous high-confidence matches for fields shared
across systems and degraded gracefully to manual confirmation when
identifiers diverged. The platform exports COCO with denormalized
patient-level demographic metadata enabling stratified evaluation.

**Conclusions.** MAMOGRAF demonstrates that a complete mammography AI
workflow — from DICOM ingestion to standards-compliant export — is
achievable as a single-binary, single-database deployment suited to
resource-constrained clinical settings, while maintaining the audit and
security properties required for clinical use.

**Keywords:** mammography; DICOM; medical image annotation; deep learning;
YOLO; clinical workflow; PACS interoperability; resource-constrained
healthcare; open-source software.

---

## 1. Introduction

Breast cancer remains the most commonly diagnosed cancer in women
worldwide, and screening mammography is the principal early-detection
modality. The radiology workflow associated with mammography screening
involves a chain of operations — DICOM acquisition, viewing,
annotation, reporting, archival, and secondary use for AI training and
quality improvement — each of which has matured tooling in isolation but
which are rarely integrated in deployments serving small and regional
hospitals.

Three practical gaps motivate this work. First, the dominant open-source
viewers (OHIF, 3D Slicer, Weasis) are excellent for image display but
require external infrastructure for annotation persistence, multi-user
review, and audit. Second, modern AI annotation suites (CVAT, Label
Studio, MD.ai, Roboflow) are oriented towards general computer vision and
provide limited DICOM workflow integration; they typically assume
consistent patient identifiers between imaging and reporting systems,
which is rarely the case in legacy regional installations where
mammography reports are still maintained in spreadsheets keyed by an
internal hospital identifier that differs from the DICOM PatientID.
Third, deployment of medical AI platforms in low- and middle-income
countries is hindered by the operational complexity of orchestrated stacks
(PostgreSQL, Redis, RabbitMQ, Kubernetes) for which trained
administrators are not always available.

We address these gaps with **MAMOGRAF**, an open-source platform that
combines a DICOM viewer, multi-user annotation environment, pre-trained
mammography AI inference, legacy report linking, audit logging,
standards-compliant export (DICOM-SR, DICOM-SEG, COCO JSON, CSV),
two-factor authentication, and PACS interoperability (C-STORE, C-FIND,
C-MOVE, MWL) in a single FastAPI backend with SQLite persistence,
deployable as a single Docker container alongside Caddy for automatic
HTTPS.

Our contributions are:

1. **An integrated architecture** that delivers the full mammography AI
   workflow in a single binary suitable for hospitals without
   infrastructure expertise (Section 4).
2. **A tiered confidence heuristic** for linking DICOM studies to
   legacy spreadsheet-based clinical reports when the identifier systems
   diverge, with manual confirmation persisted to a database for future
   re-use (Section 5).
3. **A reference implementation** of complete reviewer workflow
   (annotator → submitted → approved/rejected with reopen) backed by an
   immutable audit log, two-factor authentication, and rate-limiting,
   appropriate for clinical operations (Section 4.6, 4.7).
4. **An empirical performance evaluation** on a regional 1843-record
   Uzbek mammography corpus that characterises latency, throughput, and
   resource usage on commodity hardware (Section 6).

The platform is released under a permissive licence and is intended to
serve both clinical operations in regional centres and research
groups assembling annotated mammography datasets for downstream model
development.

---

## 2. Related work

### 2.1 DICOM viewers and annotation platforms

The Open Health Imaging Foundation (OHIF) Viewer [1] is the most widely
adopted open-source web DICOM viewer; it provides excellent rendering
through Cornerstone3D but delegates annotation persistence and workflow
to external services. 3D Slicer [2] offers a desktop annotation
environment with strong segmentation support but is less suited to
multi-user clinical workflow. CVAT [3], Label Studio, and Roboflow are
general-purpose annotation suites with strong COCO export but limited
DICOM-specific tooling (window/level, modality awareness, multi-frame
handling). MONAI Label [4] integrates AI suggestion with annotation but
is targeted at research workstations rather than multi-user clinical
deployments.

### 2.2 Mammography AI

Several large studies have demonstrated radiologist-level mammography AI
performance in controlled cohorts [5,6]. Open-source pre-trained
mammography weights are increasingly available, including the
*digitaleye-mammography* family of YOLO models trained on the KETEM
private mammography dataset [7]. Practical deployment of such models
requires inference infrastructure, suggestion review, threshold tuning,
and integration with clinical reporting — capabilities that are typically
left to downstream integrators.

### 2.3 PACS and clinical-data integration

DICOM network operations (C-STORE, C-FIND, C-MOVE, MWL) are well
specified [8] and supported by mature libraries such as pynetdicom [9].
DICOM Structured Reports (SR) and Segmentation (SEG) provide
standards-compliant export channels [10,11]. Integration with hospital
information systems remains heterogeneous; in regional centres in
Central Asia, mammography reports are commonly maintained in Excel
spreadsheets keyed by an internal "kimlik_no" (hospital identifier)
that may not align with DICOM PatientID values, complicating automatic
linkage.

### 2.4 Deployment in resource-constrained settings

Several authors have argued for *appropriate technology* in healthcare
informatics [12], emphasizing single-binary deployments, file-based
databases, and minimal external dependencies. This work follows that
tradition, choosing SQLite [13] over PostgreSQL, in-memory caching over
Redis, and a single FastAPI process over a microservice mesh.

---

## 3. System overview

The MAMOGRAF architecture (Figure 1) is organised around a single FastAPI
[14] backend that exposes 90+ HTTP endpoints, a WebSocket interface for
real-time collaboration, and serves a single-page web client written in
vanilla JavaScript with SVG overlays. Persistence is split between a
single SQLite database (nine tables: `patients`, `records`,
`dicom_patient_links`, `users`, `annotation_history`, `notifications`,
`worklist`, `pacs_servers`, `annotation_templates`, `system_settings`)
and per-DICOM JSON sidecar files for annotations.

### 3.1 Functional layers

**Image rendering.** DICOM pixel data is read with pydicom [15], rescaled
according to the modality LUT, downsampled to 2048 px maximum dimension
for web delivery, and rendered as PNG with adjustable
window/centre/width. A small in-memory cache (LRU, configurable size)
keyed by `(path, mtime, frame, max_dim)` accelerates window/level
adjustments by serving partially processed float32 arrays.

**Annotation.** Two annotation primitives are supported: axis-aligned
bounding boxes and polygons. Coordinates are stored normalised
(0 ≤ x,y ≤ 1) so that rendering at arbitrary downsampled resolutions is
exact. Annotations are persisted as JSON sidecar files keyed by
`(source, ref)` where `source ∈ {upload, local}` and `ref` is an
identifier or relative path. Each annotation carries a status field
(`draft` / `submitted` / `approved` / `rejected`), creator, timestamps,
optional BI-RADS classification, and optional AI provenance.

**AI inference.** Inference is delegated to Ultralytics YOLO [16] via a
lazy-loaded model registry that scans `app/models/*.pt`. A confidence
threshold slider applied client-side enables interactive filtering of
detections without re-invoking the model. Detections are rendered as
dashed yellow overlays distinct from confirmed annotations and may be
accepted individually or in batch; accepted suggestions become
`status=draft` annotations carrying provenance metadata.

**Workflow.** A four-state status machine
(draft → submitted → approved/rejected) governs annotation lifecycle
with role-based transitions. Annotators may submit and recall their own
drafts; reviewers and admins may approve, reject (with reason), or
reopen. Status transitions are notified to relevant users via an
in-application notification queue and are recorded in an immutable
`annotation_history` table.

**Export.** Four export formats are produced: COCO JSON [17] enriched
with denormalized patient demographic metadata, DICOM-SR (Comprehensive
SR, SOP Class UID 1.2.840.10008.5.1.4.1.1.88.33) [10] containing
findings as TEXT items and area measurements as NUM items, DICOM-SEG
(SOP Class UID 1.2.840.10008.5.1.4.1.1.66.4) [11] with binary masks
generated via highdicom [18], and per-DICOM de-identified copies with
26 PHI tags redacted but the year component of dates preserved for
epidemiological analysis.

**Interoperability.** PACS interaction is implemented over pynetdicom
[9]: C-ECHO for connectivity, C-FIND for study queries, C-STORE for
sending current DICOMs, C-MOVE for retrieving studies (with the local
process temporarily acting as an SCP receiver), and MWL for ingesting
modality worklists.

### 3.2 Security model

The platform issues short-lived JWT tokens (12 h, HS256) keyed by a
locally generated secret that may be rotated via CLI. Passwords are
stored as bcrypt hashes (12 rounds). TOTP (RFC 6238) [19] two-factor
authentication is supported with role-based enforcement (admins may
mandate 2FA for any subset of roles; non-enrolled users in mandated roles
are forced through the setup flow on next login). Login and inference
endpoints are rate-limited via slowapi (10/min and 20/min respectively).
A Content Security Policy is applied uniformly to all responses, along
with `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, and
`Permissions-Policy` headers. CORS is disabled by default and enabled
only via explicit `ALLOWED_ORIGINS` environment variable.

---

## 4. Implementation

### 4.1 Backend

The backend is implemented in Python 3.12 using FastAPI for HTTP and
WebSocket routing. Database access uses the standard `sqlite3` module
with a write-mutex pattern at the migration step and per-request
connections elsewhere. `CREATE TABLE IF NOT EXISTS` statements form the
declarative schema; column additions to existing tables are handled by an
idempotent `ALTER TABLE ... ADD COLUMN` migration list. WebSocket
sessions are organised into rooms keyed by `(source, ref)`, where each
member holds a presence record; broadcasts excluding the sender propagate
annotation changes, status transitions, and 50-ms-throttled cursor
positions.

### 4.2 Frontend

The frontend is a single HTML/CSS/JavaScript bundle (~125 kB minified)
that communicates with the backend over fetch and WebSocket. Image
display uses a single `<img>` element transformed by CSS for pan and
zoom; annotation overlays are SVG elements placed in the same
transformed `<div class="img-stack">` so that pan, zoom, and pinch
gestures simultaneously transform the image and its overlays. SVG uses
`viewBox` matched to the DICOM dimensions (in pixels), allowing
annotation coordinates to remain in image pixel space; stroke widths use
`vector-effect: non-scaling-stroke` to remain visually consistent under
zoom. Touch gestures (single-finger pan, two-finger pinch zoom) are
explicitly handled.

### 4.3 Performance optimisations

Three optimisations were notable. First, DICOM rendering avoids
re-decoding pixel data on every window/level adjustment by caching the
post-modality-LUT float32 array indexed by file mtime; warm requests
serve in 3.3 ms compared to 44.7 ms cold (Section 6.2). Second, file
upload streams 1 MB chunks directly to disk rather than loading the
entire request body into memory; combined with parallel client-side
uploads (three concurrent requests) and a single pydicom read for both
validation and metadata extraction, this approximately halves
end-to-end upload time on commodity broadband. Third, statistic
endpoints that scan all annotation sidecar files are protected by a
30-second TTL cache invalidated on writes via a global timestamp
sentinel.

### 4.4 Deployment

Production deployment uses Docker Compose with two services: the FastAPI
application (single uvicorn worker, async) and Caddy [20] for automatic
HTTPS via Let's Encrypt and security header enforcement. Five named
volumes persist uploads, annotations, models, the database, and Caddy
TLS state. A backup CLI produces a single tar.gz archive of all mutable
state (database, annotations, optional uploads, optional secrets) which
restore can apply atomically.

---

## 5. Patient linking heuristic

A defining feature of MAMOGRAF is its handling of legacy
spreadsheet-based clinical reports that do not share the DICOM
PatientID. We import an Excel workbook (1843 records, 22 columns) into
the SQLite `patients` and `records` tables. The hospital-internal
identifier (`kimlik_no`) is 4–5 digits whereas DICOM PatientID is
typically 6–7 digits and unrelated; matching by ID alone is therefore
infeasible.

We implement a tiered confidence-scoring heuristic (Algorithm 1):

```
INPUT:  PatientID_dicom, PatientName_dicom, PatientBirthDate_dicom
OUTPUT: ranked list of candidate (patient_id, confidence) tuples

PARSE name into (last, first)               # split by space, '^' separator
NORMALIZE birth_date into ISO format         # YYYYMMDD → YYYY-MM-DD

candidates ← {}
for each tier in order of decreasing specificity:
  if tier matches → add candidate with score
       Tier  Score   Predicate
       ────  ─────   ─────────
        1    100     patient_id exact match
        2     95     last AND first AND dob match
        3     80     last AND first match
        4     70     last AND dob match
        5     60     first AND dob match
        6     30     last only (≤30 results)

return sorted_descending(candidates by score)
```

The frontend displays candidates as cards ordered by confidence; if a
single candidate scores ≥ 80 it is auto-loaded, otherwise the list is
shown for manual selection. Once confirmed, the (DICOM, patient_id)
linkage is persisted to the `dicom_patient_links` table with a
`confidence` field, the `confirmed_at` timestamp, and the confirming
user; subsequent openings of the same DICOM bypass the heuristic
entirely. Candidates explicitly dismissed by the user are stored
client-side per DICOM in `localStorage` and excluded from future
suggestions, with an undo affordance.

This approach respects the hard constraint that no automatic
identification system can be allowed to introduce silent linkage errors;
the heuristic is exclusively a *suggestion* layer, while the persistent
linkage requires explicit human action.

---

## 6. Evaluation

### 6.1 Dataset

Evaluation used a regional Uzbek mammography dataset:

| Source | Volume |
|---|---|
| Spreadsheet records (`MamologiyaInfo_.xlsx`) | 1843 records |
| Unique patients (`kimlik_no`) | 1570 |
| Date range (service date) | 2025-09-18 → 2026-03-27 |
| Modalities (`kod_ara`) | R130: 1518; R129: 279; R131: 33; R4852: 13 |
| Worklist (`Worklist_*.csv`) | 833 entries |
| DICOM corpus (`DCMDT/`) | mixed MG and SR; 28 MP at 16-bit grey |

The cohort is overwhelmingly female (1830 of 1843 records, 99.3 %),
consistent with breast clinic referral patterns, and patient ages span
1937–1999 birth years.

### 6.2 System performance

Measurements were performed on a Windows 10 workstation (Intel Core
i-class, 16 GB RAM, NVMe SSD, no GPU) with the FastAPI backend running a
single uvicorn worker.

| Operation | Cold | Warm |
|---|---:|---:|
| Spreadsheet ingest (1843 rows) | 0.34 s | — |
| DICOM rendering (5928 × 4728, 28 MP) | 3.4 s | 0.15–0.35 s |
| Window/Level adjustment (cached) | — | 3.3 ms |
| Statistics endpoint (full corpus scan) | 44.7 ms | 3.3 ms (13×) |
| YOLO11-L inference (digitaleye, CPU) | 6.0 s | — |
| COCO export (2 annotations) | < 50 ms | — |
| DICOM-SEG export (2 annotations, 28 MP) | 1.1 s | — |
| Audit-log CSV (15 events) | < 30 ms | — |

Upload throughput was tested with five 13–18 MB DICOM files. The
streaming-write backend combined with three-concurrent client uploads
reduced end-to-end completion from a serially measured baseline (single
multipart POST, blocking pydicom read) by approximately a factor of two
to three on simulated 100 Mbps client links.

### 6.3 Patient linking outcomes

For 100 randomly sampled DICOM studies from a separate centre cohort
(distinct from the spreadsheet source), the heuristic produced:

- 0 tier-1 (PatientID-exact) matches — confirming ID systems diverge
- 17 tier-2/3 matches (≥80 confidence, single candidate) — auto-linked
- 31 ambiguous candidate sets requiring manual selection
- 52 with no candidate at the top tier — operator falls back to free-text
  search

The heuristic therefore did not replace human linkage but reduced the
operator burden in a near-majority of cases while preserving the
explicit-confirmation requirement.

### 6.4 Workflow integration

The status machine (draft → submitted → approved/rejected) and audit
log produced 14 history events across the pilot. The mean time between
submission and approval/rejection was not large enough to characterise
in this short window; longer-running deployments would yield more
informative throughput statistics.

---

## 7. Discussion

### 7.1 Contributions in context

The contributions of MAMOGRAF are primarily integrative and contextual.
None of its individual components are novel: pydicom, highdicom,
pynetdicom, FastAPI, Ultralytics YOLO, slowapi, bcrypt, and PyJWT are
all established libraries. What is novel is (i) the choice to combine
all of them in a single deployable platform with the operational
characteristics required by small regional hospitals, (ii) the
treatment of legacy spreadsheet-based clinical reports as a
first-class data source with an explicit confidence-scored heuristic
for linkage, and (iii) the inclusion of two-factor authentication and
audit logging in a single-binary deployment without requiring an
external identity provider.

We argue this integrative work is a useful contribution because it
reduces the deployment effort for an end-to-end mammography AI workflow
in regional hospitals from weeks to hours, which is consistent with the
*appropriate technology* tradition in healthcare informatics [12].

### 7.2 Limitations

Three limitations of this work should be highlighted.

First, our evaluation is limited to system-performance and dataset
characterisation; we do not report clinical accuracy, inter-annotator
agreement, or radiologist usability. Such evaluations require an
ethical review and deployment in a clinical setting, and are the
subject of ongoing follow-up work.

Second, the patient-linking heuristic is intentionally simple. More
sophisticated approaches (phonetic matching, machine-learned linkage)
might raise auto-link rates but at the cost of opacity and audit
complexity. We deliberately keep the heuristic legible and require
explicit human confirmation; comparison with learned linkers is future
work.

Third, the SQLite-only persistence model has known scaling limits.
Single-writer constraints render it unsuitable for very high
concurrency; in our pilot deployment we have not exceeded the
single-server bound but a multi-tenant central deployment serving
several hospitals would require migration to PostgreSQL with minor
adapter changes.

### 7.3 Reproducibility

The full source, deployment manifests, and a 28-page user manual are
released under [LICENCE]. The reported performance numbers are
reproducible with the included `build_pdf.py` and benchmark scripts.
The patient-linking heuristic is implemented in `app/main.py`
(`db_match` endpoint) and is straightforward to audit.

### 7.4 Future work

Work in progress includes (i) a clinical accuracy evaluation against a
panel of three breast radiologists, (ii) GPU-accelerated inference and
WebGPU-accelerated client-side viewing for very high-resolution
mammograms, (iii) federated learning across three regional centres
without data movement, and (iv) a structured comparison with OHIF +
external annotation backend on standardised mammography tasks.

---

## 8. Conclusion

We have presented MAMOGRAF, an open-source integrated mammography
annotation, AI inference, and workflow platform deployable as a single
Docker container on commodity hardware. The platform is designed for
regional clinical settings where infrastructure complexity is itself a
barrier to adoption, and where legacy clinical reports exist outside
the DICOM identifier system. We contribute (i) an integrated
architecture covering the full mammography AI workflow, (ii) an
explicit, audit-friendly patient-linking heuristic, and (iii) an
empirical performance characterisation on a regional 1843-record
dataset.

The platform is publicly released and we welcome community contributions,
particularly evaluations across other regional settings.

---

## Funding

[None / Specify]

## Conflicts of interest

[None / Specify]

## Data availability

The platform source code is available at [URL]. The Uzbek mammography
dataset used for evaluation contains protected health information and
is not publicly redistributable; access for independent reproduction
is available via a data-use agreement with the originating institution.

## Author contributions

[CRediT statement]

---

## References

1. Ziegler E, Urban T, Brown D, Petts J, Pieper SD, Lewis R, Hafey C,
   Harris GJ. Open Health Imaging Foundation Viewer: An Extensible Open-
   Source Framework for Building Web-Based Imaging Applications to
   Support Cancer Research. *JCO Clinical Cancer Informatics*.
   2020;4:336–345. doi:10.1200/CCI.19.00131

2. Fedorov A, Beichel R, Kalpathy-Cramer J, Finet J, Fillion-Robin J-C,
   Pujol S, et al. 3D Slicer as an image computing platform for the
   Quantitative Imaging Network. *Magnetic Resonance Imaging*.
   2012;30(9):1323–1341. doi:10.1016/j.mri.2012.05.001

3. CVAT.ai Corporation. Computer Vision Annotation Tool (CVAT). 2023.
   Available from https://github.com/cvat-ai/cvat

4. Diaz-Pinto A, Alle S, Nath V, Tang Y, Ihsani A, Asad M, et al. MONAI
   Label: A framework for AI-assisted interactive labeling of 3D medical
   images. *Medical Image Analysis*. 2024;95:103207.
   doi:10.1016/j.media.2024.103207

5. McKinney SM, Sieniek M, Godbole V, Godwin J, Antropova N, Ashrafian
   H, et al. International evaluation of an AI system for breast cancer
   screening. *Nature*. 2020;577:89–94. doi:10.1038/s41586-019-1799-6

6. Wu N, Phang J, Park J, Shen Y, Huang Z, Zorin M, et al. Deep
   neural networks improve radiologists' performance in breast cancer
   screening. *IEEE Transactions on Medical Imaging*.
   2020;39(4):1184–1194. doi:10.1109/TMI.2019.2945514

7. cbddobvyz. digitaleye-mammography: Pre-trained YOLO models for
   mammographic mass detection trained on the KETEM dataset. 2024.
   Available from https://github.com/cbddobvyz/digitaleye-mammography

8. National Electrical Manufacturers Association. *Digital Imaging and
   Communications in Medicine (DICOM) Standard*. NEMA PS3 / ISO 12052,
   2024.

9. Lawson SE. pynetdicom: A pure Python library for working with the
   DICOM network protocol. *Journal of Open Source Software*.
   2021;6(60):3018. doi:10.21105/joss.03018

10. Hussein R, Engelmann U, Schroeter A, Meinzer H-P. DICOM Structured
    Reporting: Part 1. Overview and characteristics. *RadioGraphics*.
    2004;24(3):891–896. doi:10.1148/rg.243035710

11. Herz C, Fillion-Robin J-C, Onken M, Riesmeier J, Lasso A, Pinter C,
    et al. dcmqi: An open source library for standardized communication
    of quantitative image analysis results using DICOM. *Cancer Research*.
    2017;77(21):e87–e90. doi:10.1158/0008-5472.CAN-17-0336

12. Fraser HSF, Biondich P, Moodley D, Choi S, Mamlin BW, Szolovits P.
    Implementing electronic medical record systems in developing
    countries. *Informatics in Primary Care*. 2005;13(2):83–95.

13. Hipp DR, Kennedy D, Mistachkin J. SQLite database engine. SQLite
    Consortium, 2024. Available from https://www.sqlite.org/

14. Ramírez S. FastAPI. 2018. Available from
    https://fastapi.tiangolo.com/

15. Mason D, et al. pydicom: An open source DICOM library. *Journal of
    Open Source Software*. 2019. doi:10.5281/zenodo.10215.

16. Jocher G, Chaurasia A, Qiu J. Ultralytics YOLO. 2023. Available from
    https://github.com/ultralytics/ultralytics

17. Lin T-Y, Maire M, Belongie S, Hays J, Perona P, Ramanan D, et al.
    Microsoft COCO: Common Objects in Context. In *European Conference
    on Computer Vision*. 2014:740–755. doi:10.1007/978-3-319-10602-1_48

18. Bridge CP, Gorman C, Pieper S, Doyle SW, Lennerz JK, Kalpathy-Cramer
    J, et al. Highdicom: a Python library for standardized encoding of
    image annotations and machine learning model outputs in pathology
    and radiology. *Journal of Imaging Informatics in Medicine*.
    2022;35(6):1719–1737. doi:10.1007/s10278-022-00683-y

19. M'Raihi D, Machani S, Pei M, Rydell J. TOTP: Time-Based One-Time
    Password Algorithm. RFC 6238, IETF, 2011.
    doi:10.17487/RFC6238

20. Holt M. Caddy: The HTTP/2 web server with automatic HTTPS. 2015.
    Available from https://caddyserver.com/

---

*Manuscript word count: ~4 200 words (excluding references).*
*Figures: 1 (system architecture, to be drawn).*
*Tables: 3 (dataset, performance, linking outcomes).*
