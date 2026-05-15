\newpage

# ILOVALAR

## 1-ilova. MAMOGRAF dasturiy majmuasi screenshot'lari

**1.1-rasm. Login (kirish) ekrani.** JWT autentifikatsiyasi va opsional TOTP 2FA bilan kirish jarayoni.

![](docs/screenshots/01_login.png)

**1.2-rasm. Asosiy ekran (DICOM yuklashga tayyor).** Toolbar ro'yxati, real-time WebSocket holat indikatori, mobile-responsive UI.

![](docs/screenshots/02_empty_ui.png)

**1.3-rasm. DICOM viewer (mammografiya tasviri).** SVG-asoslangan annotatsiya editor, hotkeys bilan boshqaruv, real-time cursor sync.

![](docs/screenshots/03_dicom_viewer.png)

**1.4-rasm. Annotatsiyalar paneli.** Bbox va polygon tip annotatsiyalar, status workflow (draft → submitted → approved/rejected), audit history.

![](docs/screenshots/05_annotations_tab.png)

**1.5-rasm. Hisobot (klinik yozuv) integratsiyasi.** Tiered confidence patient ID matching (100/95/80/70/60/30), DICOM ↔ klinik yozuv bog'lanishi.

![](docs/screenshots/06_report_tab.png)

**1.6-rasm. Statistika dashboard'i.** Real-time counters: jami DICOM, annotatsiyalashgan, status taqsimoti, har bir radiolog bo'yicha statistika.

![](docs/screenshots/07_stats_modal.png)

**1.7-rasm. Audit timeline.** Har bir annotatsiya o'zgartirishining to'liq tarixi: kim, qachon, qaysi ma'lumotlarni o'zgartirgan.

![](docs/screenshots/08_audit_modal.png)

**1.8-rasm. Annotatsiyalashgan DICOM'lar overview.** Card view, filtering (status, reviewer, sana oralig'i), bulk eksport.

![](docs/screenshots/09_overview_modal.png)

**1.9-rasm. PACS server boshqaruvi.** C-ECHO, C-FIND, C-STORE, C-MOVE protokollari uchun PACS server CRUD.

![](docs/screenshots/10_pacs_modal.png)

**1.10-rasm. Foydalanuvchi boshqaruvi (admin).** RBAC roli boshqaruvi (admin/reviewer/annotator), TOTP majburiy rollari, bulk audit log eksporti.

![](docs/screenshots/11_admin_modal.png)

**1.11-rasm. TOTP 2FA setup.** QR kod orqali Google Authenticator yoki o'xshash ilovalarda TOTP'ni faollashtirish.

![](docs/screenshots/12_totp_modal.png)

**1.12-rasm. Worklist.** DICOM Modality Worklist (MWL) integratsiyasi, kelayotgan tashxis ishlari.

![](docs/screenshots/13_worklist.png)

**1.13-rasm. Mening ishim (radiolog dashboard).** Status filter, faqat o'zining ishlari, status counter'lar, real-time yangilanish.

![](docs/screenshots/14_dashboard.png)

\newpage

## 2-ilova. Tadqiqotchi qo'llanmasidagi screenshot'lar

**2.1-rasm. DICOM faylini ochish.** Drag-and-drop interface, chunked upload (1 MB blocks), progress bar.

![](docs/researcher_screenshots/01_dicom_open.png)

**2.2-rasm. DICOM metadata.** To'liq DICOM tag ekrani, PII (Personally Identifiable Information) farqlash.

![](docs/researcher_screenshots/02_metadata.png)

**2.3-rasm. Hisobot bilan DICOM bog'lash.** Tiered patient ID matching algoritmi, manual confirmation bilan candidate ranking.

![](docs/researcher_screenshots/03_hisobot_match.png)

**2.4-rasm. AI bashoratlari.** YOLO-asoslangan detection natijalari, confidence threshold sliderlar.

![](docs/researcher_screenshots/04_ai_suggestions.png)

**2.5-rasm. Pastroq threshold bilan ko'proq bashoratlar.** Confidence threshold'ni pasaytirish orqali ko'proq potentsial lezyonlarni ko'rish.

![](docs/researcher_screenshots/05_threshold_low.png)

**2.6-rasm. Bashoratlarni qabul qilgandan so'ng.** Accept-ed bashorat → annotation status workflow'ga kiritiladi.

![](docs/researcher_screenshots/06_after_accept.png)

**2.7-rasm. Annotatsiyalar tab.** Per-annotation status, tarixi, bbox/polygon ma'lumotlari.

![](docs/researcher_screenshots/07_annotations_tab.png)

**2.8-rasm. Polygon annotation.** Erkin shaklli polygon, dynamic vertex add/remove, masking eksport.

![](docs/researcher_screenshots/08_polygon.png)

**2.9-rasm. Eksport tugmalari.** COCO, DICOM-SR, DICOM-SEG, de-identifikatsiyalashgan ZIP eksport.

![](docs/researcher_screenshots/09_export_buttons.png)

**2.10-rasm. Statistika.** Jami DICOM, annotatsiyalashgan, status taqsimoti, vaqt bo'yicha tahlil.

![](docs/researcher_screenshots/10_stats.png)

**2.11-rasm. PHI (Personal Health Information) tahlili va de-identifikatsiya.** Avtomatik PHI aniqlash, audit log bilan eksport.

![](docs/researcher_screenshots/11_deid_phi.png)

**2.12-rasm. Tadqiqotchi dashboard.** Status filter (draft/submitted/approved/rejected), sana oralig'i, batch operatsiyalar.

![](docs/researcher_screenshots/12_dashboard.png)

\newpage

## 3-ilova. XS-Classifier tajriba natijalari grafiklari

**3.1-rasm. Sinflar muvozanatlik diagrammasi.** Saraton mavjud (n=345, 18.8%) va saraton emas (n=1494, 81.2%) sinflarining nisbatii. Stratified k-fold splitting bu nisbat har foldda saqlangan.

![](paper/figures/class_balance.png)

**3.2-rasm. Skript taqsimoti.** 1839 ta klinik yozuvning kirill-dominant (n=894, 48.6%), lotin-dominant (n=941, 51.2%), va mixed (n=4, 0.2%) podgruppalari bo'yicha taqsimoti.

![](paper/figures/script_distribution.png)

**3.3-rasm. ROC egri chiziqlari.** XS-Classifier (AUROC=0.9931), Char $n$-gram (AUROC=0.9929), Word-only (AUROC=0.9919), Word+Char hybrid (AUROC=0.9929) modellari uchun ROC egri chiziqlari.

![](paper/figures/roc_curves.png)

**3.4-rasm. Precision–Recall egri chiziqlari.** XS-Classifier (AUPRC=0.9676) va boshqa baseline modellar uchun PR egri chiziqlari.

![](paper/figures/pr_curves.png)

**3.5-rasm. XS-Classifier confusion matrix.** 5-fold CV jami: TP=341, FN=4, FP=29, TN=1465. False positive nisbati 6 (boshqa baseline'larda 19+22+22).

![](paper/figures/cm_xs_classifier_proposed.png)

**3.6-rasm. Char n-gram baseline confusion matrix.**

![](paper/figures/cm_char_n_gram_tf_idf_script_blind.png)

**3.7-rasm. Word-only baseline confusion matrix.**

![](paper/figures/cm_word_only_tf_idf_latin_blind.png)

**3.8-rasm. Word+Char hybrid baseline confusion matrix.**

![](paper/figures/cm_word_char_hybrid_single_stream.png)

\newpage

## 4-ilova. Joriy etish dalolatnomalari

[*Quyidagi joriy etish dalolatnomalari mualliflik tomonidan to'ldiriladi va dissertatsiyaning yakuniy versiyasiga qo'shiladi:*]

**4.1.** [Tibbiyot muassasasi 1] — joriy etish dalolatnomasi № [hujjat raqami], [yil-kun-oy].

**4.2.** [Tibbiyot muassasasi 2] — joriy etish dalolatnomasi № [hujjat raqami], [yil-kun-oy].

**4.3.** [Tibbiyot muassasasi 3] — joriy etish dalolatnomasi № [hujjat raqami], [yil-kun-oy].

**4.4.** O'zbekiston Respublikasi Sog'liqni Saqlash Vazirligi — ma'lumotnoma № [hujjat raqami], [yil-kun-oy].

**4.5.** [Viloyat sog'liqni saqlash boshqarmasi] — ma'lumotnoma № [hujjat raqami], [yil-kun-oy].

**4.6.** [Viloyat hokimligi] — ma'lumotnoma № [hujjat raqami], [yil-kun-oy].

\newpage

## 5-ilova. EHM uchun yaratilgan dasturiy vositalarga guvohnomalar

Mualliflik tomonidan tibbiy tasvirlarni qayta ishlash sohasida quyidagi elektron hisoblash mashinalari uchun yaratilgan dasturlarga O'zbekiston Respublikasi Adliya vazirligida rasmiy guvohnomalar olingan:

### 5.1. EHM № DGU 36888

**Dastur nomi:** *«Tibbiy tasvirlarni fraktal raqamli qayta ishlash»*

**Talabnoma kelib tushgan sana:** 03.04.2024

**Talabnoma raqami:** DGU 202403718

**Huquq egasi(lari):** TURAQULOV SHOXRUX XUDAYAROVICH; SOXIBOVA XOLIDA DAVRON QIZI

**Dastur muallifi(lari):** SOXIBOVA XOLIDA DAVRON QIZI; TURAQULOV SHOXRUX XUDAYAROVICH

**O'zbekiston Respublikasining Dasturiy mahsulotlar davlat reyestrida ro'yxatga olingan sana:** 27.04.2024

**Mazkur dissertatsiya bilan bog'liqligi:** ushbu dastur tibbiy tasvirlarga dastlabki ishlov berish, fraktal o'lchov asosida tasvir teksturasi tahlili va multi-resolution dekompozitsiya algoritmlari ustida ishlab chiqilgan. Mazkur dissertatsiyada bayon etilgan mammografiya tasvirlariga dastlabki ishlov berish quvuri (1.2-§) ushbu dasturning natijalaridan foydalanadi.

\

### 5.2. EHM № DGU 45451

**Dastur nomi:** *«MRT tasvirlarini bipolyar noravshan to'plamlar orqali qayta ishlab chuqur o'qitish modellari yordamida tasniflash dasturi»*

**Talabnoma kelib tushgan sana:** 03.12.2024

**Talabnoma raqami:** DT 202413400

**Huquq egasi(lari):** ISKANDAROVA SAYYORA NURMAMATOVNA; TURAQULOV SHOXRUX XUDAYAROVICH

**Dastur muallifi(lari):** ISKANDAROVA SAYYORA NURMAMATOVNA; TURAQULOV SHOXRUX XUDAYAROVICH

**O'zbekiston Respublikasining Dasturiy mahsulotlar davlat reyestrida ro'yxatga olingan sana:** 12.12.2024

**Mazkur dissertatsiya bilan bog'liqligi:** ushbu dastur tibbiy tasvirlarni bipolyar noravshan (fuzzy) to'plamlar va chuqur o'qitish (deep learning) modellari yordamida tasniflashga bag'ishlangan. Mazkur dissertatsiyada bayon etilgan TILLNet-Det multimodal arxitekturasining (3-bob) klassifikatsion qismi va weak supervision pipeline'i (3.6-§) noravshan to'plamlar nazariyasidan tushunchalardan foydalanadi.

\

### 5.3. MAMOGRAF dasturiy majmuasi (jarayonda)

Mazkur dissertatsiya doirasida ishlab chiqilgan **MAMOGRAF dasturiy majmuasi** — multilingual klinik matnlar va mammografiya tasvirlari uchun multimodal sun'iy intellekt tashxis tizimi — uchun EHM guvohnomasi olish bo'yicha jarayon davom etmoqda.

**Dastur nomi (taklif):** *«Multilingual klinik matnlar va mammografiya tasvirlari uchun multimodal sun'iy intellekt tashxis tizimi (MAMOGRAF)»*

**Komponentlar:**

– XS-Classifier: kod-aralash o'zbek-kirill, o'zbek-lotin va rus tillaridagi mammografiya klinik matnlarini tasniflash moduli;

– TILLNet-Det: matn va tasvirni multimodal tarzda birlashtiruvchi neyron tarmoq detektor;

– Radiolog verifikatsiya UI: pseudo-bbox annotatsiyalarini accept/edit/reject orqali gold labelsga aylantirish moduli;

– 10-bosqichli to'liq tadqiqot quvuri (run\_pipeline.py).

**Hajmi:** $\sim 23\,000$ qator Python kod + $\sim 4\,400$ qator JavaScript kod.

\

[*Eslatma: yuqoridagi dasturiy guvohnomalar nusxalari (DGU 36888 va DGU 45451) ushbu dissertatsiya ilovasiga ilova qilinadi. MAMOGRAF dasturiy majmuasi uchun EHM guvohnomasi nashr etilgandan keyin yangilangan ilovaga kiritiladi.*]

\newpage

## 6-ilova. Konferensiya va seminarlarda chiqishlar ro'yxati

[*Mualliflik tomonidan to'ldiriladi:*]

**6.1.** [Konferensiya nomi 1], [yil], [shahar, mamlakat] — ma'ruza: "[ma'ruza nomi]".

**6.2.** [Konferensiya nomi 2], [yil], [shahar, mamlakat] — ma'ruza: "[ma'ruza nomi]".

**6.3.** [Respublika anjumani 1], [yil], [shahar] — ma'ruza: "[ma'ruza nomi]".

\newpage

## 7-ilova. Asosiy dasturiy modullar ro'yxati

MAMOGRAF dasturiy majmuasining asosiy Python modullari:

| Fayl | Hajmi (LOC) | Vazifasi |
|------|-------------|----------|
| `app/main.py` | $\sim 2600$ | FastAPI backend, 90+ REST endpoint |
| `app/db.py` | $\sim 200$ | SQLite ma'lumotlar bazasi sxemasi |
| `app/auth.py` | $\sim 250$ | JWT, bcrypt, TOTP autentifikatsiyasi |
| `app/dicom_utils.py` | $\sim 320$ | DICOM rendering, kesh, SR parser |
| `app/annotations.py` | $\sim 80$ | Annotatsiya CRUD (JSON sidecar) |
| `app/pacs.py` | $\sim 400$ | PACS protokollari (C-STORE, etc.) |
| `app/inference.py` | $\sim 200$ | YOLO inference wrapper |
| `app/ws.py` | $\sim 150$ | WebSocket room manager |
| `app/deidentify.py` | $\sim 180$ | DICOM PHI removal |
| `app/dicom_sr.py` | $\sim 150$ | DICOM SR eksport |
| `app/dicom_seg.py` | $\sim 200$ | DICOM SEG eksport |
| `app/coco_to_yolo.py` | $\sim 120$ | COCO ↔ YOLO format konvertor |
| `app/import_xlsx.py` | $\sim 150$ | Klinik yozuvlarni Excel'dan import |
| `app/import_worklist.py` | $\sim 80$ | DICOM MWL import |
| `app/manage_users.py` | $\sim 100$ | CLI foydalanuvchi boshqaruvi |
| `app/backup.py` | $\sim 80$ | DB + sidecar backup |
| `app/mwl_scu.py` | $\sim 100$ | MWL SCU client |
| `app/research/preprocess.py` | $\sim 250$ | DICOM 9-bosqichli preprocessing |
| `app/research/datasets/cbis_ddsm.py` | $\sim 300$ | CBIS-DDSM → YOLO konvertor |
| `app/research/train_classifier.py` | $\sim 200$ | XS-Classifier 5-fold CV trening |
| `app/research/stat_test.py` | $\sim 80$ | Paired t-test, Wilcoxon |
| `app/research/train_detector.py` | $\sim 250$ | YOLOv8 baseline + FROC |
| `app/research/pseudo_labels.py` | $\sim 350$ | Multilingual weak supervision |
| `app/research/load_review_queue.py` | $\sim 100$ | Review queue loader |
| `app/research/train_tillnet.py` | $\sim 400$ | TILLNet-Det trener (FCOS loss) |
| `app/research/gold_to_yolo.py` | $\sim 200$ | Gold labels → YOLO konvertor |
| `app/research/run_pipeline.py` | $\sim 350$ | 10-bosqichli orkestrator |
| `app/models_arch/xs_classifier.py` | $\sim 200$ | XS-Classifier sklearn pipeline |
| `app/models_arch/tillnet_det.py` | $\sim 370$ | TILLNet-Det PyTorch arxitektura |
| `app/models_arch/bca_yolo.py` | $\sim 370$ | BCA-YOLO arxitektura (ekstra) |
| **Jami Python LOC** | **$\sim 23\,000$** | |
| `app/static/app.js` | $\sim 4400$ | Vanilla JS frontend SPA |
| `app/static/index.html` | $\sim 300$ | Statik HTML scaffold |
| `app/static/style.css` | $\sim 400$ | Mobile-responsive CSS |
| **Jami JS LOC** | **$\sim 4\,400$** | |

\newpage

## 8-ilova. Asosiy hyperparametrlar to'plami

### XS-Classifier hyperparametrlari

```python
@dataclass
class XSConfig:
    word_min_df: int = 2
    word_max_df: float = 0.95
    word_ngram: tuple = (1, 2)
    char_min_df: int = 2
    char_max_df: float = 0.95
    char_ngram: tuple = (3, 5)
    sublinear_tf: bool = True
    C: float = 1.0
    class_weight: str = "balanced"
    max_iter: int = 2000
    solver: str = "liblinear"
```

### TILLNet-Det hyperparametrlari

```python
@dataclass
class TILLNetConfig:
    num_classes: int = 3
    text_dim: int = 256
    fpn_dim: int = 256
    pretrained_backbone: bool = True
    in_chans: int = 1
    use_text: bool = True
```

### Mammografiya-konservativ augmentatsiya hyperparametrlari (Stage 1)

```python
MAMMO_HYPS = dict(
    hsv_h=0.0, hsv_s=0.0, hsv_v=0.05,
    degrees=5.0,
    translate=0.05,
    scale=0.10,
    shear=0.0,
    perspective=0.0,
    flipud=0.0,
    fliplr=0.0,            # R→L standartlashtirilgan
    mosaic=0.3,
    mixup=0.0,
    copy_paste=0.0,
    erasing=0.0,
    close_mosaic=10,
    optimizer="AdamW",
    lr0=1e-4,
    lrf=0.01,
    momentum=0.937,
    weight_decay=5e-4,
    warmup_epochs=2.0,
    cos_lr=True,
    box=7.5, cls=0.5, dfl=1.5,
    label_smoothing=0.0,
)
```

### TILLNet-Det FCOS regress ranges

```python
REGRESS_RANGES = (
    (-1, 64),     # P3 stride 8     small lesions ≤ 64 px
    (64, 128),    # P4 stride 16
    (128, 256),   # P5 stride 32
    (256, 512),   # P6 stride 64
    (512, 10_000) # P7 stride 128   large masses
)
```

### Pipeline runner argumentlari

```bash
python -m app.research.run_pipeline \
    --out-root         runs/full_pipeline_v1 \
    --local-dicoms     /data/MAMOGRAF/uploads \
    --cbis-root        /data/CBIS-DDSM \
    --texts-csv        /data/MAMOGRAF/reports.csv \
    --db               app/db.sqlite3 \
    --imgsz            1024 \
    --batch            8 \
    --epochs-stage1    100 \
    --epochs-stage2    30 \
    --gpu              0 \
    --yolo-model       yolov8m.pt \
    --workers          4 \
    --min-pseudo-conf  0.5 \
    --skip             ""    `# blacklist` \
    --only             ""    `# whitelist` \
    --force            ""    `# override idempotency`
```
