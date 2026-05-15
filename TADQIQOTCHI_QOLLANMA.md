# Tibbiy AI tadqiqotchi uchun qo'llanma

**MAMOGRAF DICOM Viewer** — mammografiya AI modellari uchun annotatsiya
qilingan dataset yaratish, o'rgatish va baholash bo'yicha to'liq amaliy
qo'llanma.

> Bu hujjat **AI tadqiqotchisi** uchun mo'ljallangan. Klinik foydalanuvchilar
> uchun: [FOYDALANUVCHI_QOLLANMA.md](FOYDALANUVCHI_QOLLANMA.md).

---

## 1. Maqsad va workflow umumiy ko'rinishi

### 1.1 Tadqiqotchi nima qiladi

Sizning maqsadingiz — mammografiyada lesion (mass, calcification, asymmetry)
detection va klassifikatsiya qiladigan **YOLO modelini o'rgatish**. Buning
uchun kerak:

1. **Annotatsiyalangan dataset** — har bir DICOM uchun bbox + class label
2. **Train/val split** — modelning generalization'ini baholash uchun
3. **Standart format** — Ultralytics YOLO yoki Detectron2 / MMDet o'qiy
   oladigan
4. **Bemor demografi** — bias tahlili uchun (yosh, jins, BI-RADS taqsimot)
5. **Audit trail** — kim qachon nima belgilagan (reproducibility uchun)

### 1.2 To'liq pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. DICOM yig'ish     │ Local disk yoki PACS C-FIND/MOVE          │
│                       │                                            │
│ 2. xlsx integratsiya  │ Bemor demografi (sex, DOB, hisobotlar)    │
│                       │                                            │
│ 3. AI bootstrap        │ digitaleye_yolo11_l (pre-trained) bilan   │
│                       │ taklif olish — boshlang'ich annotatsiya   │
│                       │                                            │
│ 4. Manual annotate     │ Annotator approve/reject + tuzatish        │
│                       │                                            │
│ 5. Reviewer approve    │ Senior radiolog tasdiqlaydi (gold std.)    │
│                       │                                            │
│ 6. COCO eksport        │ /api/export?format=coco                    │
│                       │                                            │
│ 7. COCO → YOLO         │ python -m app.coco_to_yolo ...            │
│                       │                                            │
│ 8. Train               │ yolo train data=data.yaml ...              │
│                       │                                            │
│ 9. Baholash            │ mAP, precision, recall, confusion matrix   │
│                       │                                            │
│ 10. Production         │ best.pt → app/models/ → live inference     │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 Mintaqaviy muhim mulohazalar

- **PHI**: training datasetlar de-identifikatsiya qilinishi kerak (🛡 De-ID)
- **Class balance**: BI-RADS 1-2 (norma) odatda BI-RADS 4-5 (suspicious) dan
  10x ko'p. Sampling/oversampling kerak.
- **Multi-view**: bitta ko'krak uchun CC + MLO (4 ta tasvir per studi). YOLO
  bitta tasvirni tanlay oladi yoki barchasini.
- **Reviewer agreement**: kappa coefficient hisoblash uchun bir nechta
  reviewer tomonidan annotatsiyalangan namunalar zarur.

---

## 2. Dataset tayyorlash

### 2.1 DICOM yig'ish

#### A) Lokal disk

`run.bat` orqali ishga tushirilganda `LOCAL_DICOM_ROOT` env o'rnatiladi
(default: `d:\Project_MAMOGRAF\dicomfiles`). Chap panelda **Lokal** tab
ostida ko'rinadi.

#### B) PACS dan import

```cmd
:: Studiyalarni qidirish
.venv\Scripts\python.exe -m app.pacs query \
  --host 192.168.1.10 --port 4242 --aet ORTHANC \
  --modality MG --study-date 20260101-20260601

:: Aniq study'ni olish
.venv\Scripts\python.exe -m app.pacs fetch \
  --host 192.168.1.10 --port 4242 --aet ORTHANC \
  --study-uid 1.2.3.4.5 --dest ./fetched/

:: Yoki HTTP API orqali (UI'dan): 🏥 PACS modal
```

#### C) MWL navbat

```cmd
.venv\Scripts\python.exe -m app.mwl_scu \
  --host 192.168.1.10 --port 4242 --aet ORTHANC \
  --modality MG --date today
```

### 2.2 xlsx bilan bog'lash

Klinik hisobotlar (1843 yozuv, 1570 bemor) avval import qilinadi:

```cmd
.venv\Scripts\python.exe -m app.import_xlsx --reset
```

DICOM ochilganda **Hisobot** tab avtomatik:

1. PatientID + Name + DOB orqali xlsx'ga match qiladi
2. Confidence ≥ 80% bo'lsa avto-bog'laydi
3. Aks holda candidate ro'yxatdan tanlash

**Tadqiqot uchun foyda**: bemor demografisi (sex, DOB, BI-RADS tashxis)
COCO eksportda image-level metadata sifatida saqlanadi → bias tahlili,
strata bo'yicha train/val split.

### 2.3 AI bootstrap (digitaleye_yolo11_l)

Boshlang'ich annotatsiya uchun pre-trained mammografiya modelini ishlatamiz:

1. `app/models/digitaleye_yolo11_l.pt` (49MB, KETEM datasetida o'qitilgan)
2. Toolbar: **AI model dropdown** → tanlash
3. **🤖 AI tahlil** bosish → 6-12 sekund kutib turing (CPU)
4. Sariq punktir bbox'lar paydo bo'ladi: `🤖 BIRADS45 13.4%`

#### Threshold sozlash

UI slayderi 10-95% oralig'ida. Tipik strategiya:

| Foydalanish | Threshold | Sabab |
|---|---|---|
| **Yangi DICOM'ga ko'rgazma** | 25-30% | Kam falsy positive, yuqori recall |
| **Tasdiqlangan dataset** | 50-60% | Balans |
| **Strict gold standard** | 75%+ | Faqat ishonchlilari |

**✓ Hammasini qabul** tugmasi — barcha ko'rinadigan takliflarni bir
clickda annotatsiyaga aylantiradi.

### 2.4 Batch AI inference

50 ta DICOM uchun bir vaqtda:

1. Chap panelda DICOM'lar yonida ☑ checkbox
2. **🤖 AI batch** tugmasi (yuqori chap)
3. Confirm → barcha tanlangan DICOM'lar uchun AI yuguradi
4. Natijalar avtomatik **draft** annotatsiya sifatida saqlanadi

```
Batch tugadi:
✓ 47/50 muvaffaqiyat
83 ta detection saqlandi
```

Keyin manual revizyon va approve / reject.

### 2.5 Manual tuzatish

AI takliflari ko'pincha to'g'ri, lekin chegaralar noto'g'ri yoki
soxta-pozitiv bo'ladi:

| Holat | Harakat |
|---|---|
| AI bbox to'g'ri joyda, lekin kichik | Resize handle bilan kengaytirish |
| AI lesion'ni topmagan | **B** (BBox) bilan qo'lda chizish |
| AI noto'g'ri joyga ishora | Delete bosish |
| Aniq kontur kerak (BRCA tadqiqot) | **P** (Polygon) — vertex-by-vertex chizish |

### 2.6 Reviewer approval (gold standard yaratish)

Trening datasetida faqat **approved** annotatsiyalar bo'lishi tavsiya
etiladi:

1. **annotator** chizadi → S (Submit)
2. **reviewer** Y (Approve) yoki N (Reject + sabab)
3. Approved annotatsiyalar locked — annotator tahrirlay olmaydi
4. Audit log saqlanadi (kim qachon tasdiqladi)

Rad etilgan annotatsiyalar reviewer izohi bilan annotator'ga qaytadi
(dataset to'g'ri kalibrlash uchun).

---

## 3. Eksport formatlari

### 3.1 COCO JSON (asosiy training format)

Toolbar **⤓ Eksport** → `annotations_coco_YYYYMMDD_HHMMSS.json` yuklab
olinadi.

#### Tarkibi

```json
{
  "info": {
    "description": "MAMOGRAF DICOM Viewer annotations export",
    "date_created": "2026-05-07T...",
    "version": "1"
  },
  "categories": [
    {"id": 1, "name": "mass"},
    {"id": 2, "name": "calcification"},
    {"id": 3, "name": "asymmetry"}
  ],
  "images": [
    {
      "id": 1,
      "file_name": "DCMDT/D0000000.dcm",
      "source": "local",
      "width": 4728,
      "height": 5928,
      "patient": {
        "patient_id": "14173",
        "first_name": "GULBAXOR",
        "last_name": "MAMASHUKUROVA",
        "sex": "A",
        "birth_date": "1976-04-15",
        "confidence": 85
      }
    }
  ],
  "annotations": [
    {
      "id": 1,
      "image_id": 1,
      "category_id": 1,
      "type": "bbox",
      "bbox": [472.8, 1185.6, 236.4, 355.68],
      "bbox_normalized": [0.1, 0.2, 0.05, 0.06],
      "area": 84082.75,
      "iscrowd": 0,
      "bi_rads": "4A",
      "note": "AI: BIRADS45 13.4%",
      "frame": 0,
      "status": "approved",
      "created_by": "radiolog",
      "reviewed_by": "admin",
      "patient_id": "14173"
    }
  ]
}
```

#### Tadqiqot uchun foydali maydonlar

| Maydon | Foyda |
|---|---|
| `bbox_normalized` | Format konvertatsiyalarsiz YOLO'ga to'g'ri |
| `patient.sex`, `birth_date` | Strata bo'yicha split (yosh, jins) |
| `bi_rads` | Multi-class learning (regression yoki ordinal) |
| `status` | Faqat `approved` bilan filtrlash uchun |
| `created_by`, `reviewed_by` | Inter-annotator agreement (kappa) |
| `note` (`AI: ...`) | AI-bootstrapped vs manual ratiosi |

### 3.2 DICOM-SR (klinik standart)

Toolbar **📄 SR** — har DICOM uchun alohida `*_sr.dcm` fayl.

- LOINC `11528-7` (Radiology Report) standartiga mos
- PACS'ga to'g'ridan-to'g'ri yuklab integratsiyalash mumkin
- Hospital systemlari (Epic, Cerner) o'qiy oladi
- Audit-friendly (immutable DICOM)

**Foyda**: tadqiqotni klinik validation uchun ishlatish — natijalarni
mahalliy hospital PACS'ga qayta yuborib, real radiologlar bilan
solishtirish.

### 3.3 DICOM-SEG (pixel-level segmentation)

Toolbar **🖼 SEG** — pixel maska bilan DICOM.

- SOP Class `1.2.840.10008.5.1.4.1.1.66.4` (Segmentation)
- BINARY mask (har polygon to'ldirilib raster qilingan)
- highdicom validatsiyasidan o'tgan
- Mammografiya source FoR (Frame of Reference) UID'siz bo'lganda — barcha
  label'lar bitta segment'ga birlashtiriladi (auto-fallback)

**Foyda**: U-Net/Mask R-CNN segmentation modellari uchun. Ayniqsa BRCA
tadqiqotlarida kontur shaklini o'rganish.

### 3.4 De-identification

Eksportdan oldin DICOM'larni anonimlashtirish kerak — public dataset yoki
multi-center sharing uchun.

Toolbar **🛡 De-ID** modal:

1. 26+ PHI tag aniqlanadi (PatientName, ID, DOB, ReferringPhysician, ...)
2. **⤓ Anonimlashtirilgan DICOM yuklab olish** bosilganda:
   - Ism/ID/manzil → `ANON`
   - StudyDate `20260408` → `20260101` (yili saqlanadi epi tahlil uchun)
   - `PatientIdentityRemoved=YES` tag qo'shiladi
   - Pixel data o'zgarmaydi

---

## 4. COCO → YOLO konvertatsiya

Loyihada `app/coco_to_yolo.py` skript mavjud.

### 4.1 Asosiy ishlatish

```cmd
.venv\Scripts\python.exe -m app.coco_to_yolo annotations_coco.json --out yolo_dataset/
```

Yaratiladi:

```
yolo_dataset/
  data.yaml         # Ultralytics YOLO config
  classes.txt       # class nomlari ro'yxati
  labels/
    DCMDT_D0000000.txt   # YOLO format bbox'lar
    ...
```

### 4.2 Train/val split bilan

```cmd
.venv\Scripts\python.exe -m app.coco_to_yolo annotations_coco.json \
  --out yolo_dataset/ --train-val 0.8 --seed 42
```

Natija:

```
yolo_dataset/
  labels/train/  (80%)
  labels/val/    (20%)
  images/train/
  images/val/
  data.yaml
```

### 4.3 DICOM rasmlari bilan

```cmd
.venv\Scripts\python.exe -m app.coco_to_yolo annotations_coco.json \
  --out yolo_dataset/ \
  --copy-images \
  --upload-dir app/uploads \
  --local-root d:\Project_MAMOGRAF\dicomfiles \
  --train-val 0.8
```

### 4.4 YOLO label format

```
# yolo_dataset/labels/DCMDT_D0000000.txt
0 0.125 0.230 0.050 0.060
1 0.575 0.420 0.180 0.220
```

`<class_id> <x_center_norm> <y_center_norm> <width_norm> <height_norm>`

### 4.5 data.yaml namunasi

```yaml
path: D:/Project_MAMOGRAF/plan_project/yolo_dataset
train: images/train
val: images/val
names:
  0: mass
  1: calcification
  2: asymmetry
  3: architectural_distortion
```

---

## 5. YOLO modelni o'rgatish

### 5.1 Ultralytics o'rnatish

```cmd
pip install ultralytics
```

GPU uchun: [GPU.md](GPU.md) bo'yicha CUDA torch'ni o'rnating.

### 5.2 DICOM → PNG preprocessing

YOLO DICOM'ni o'qiy olmaydi — PNG ga aylantirish kerak. Loyihadagi
`render_frame_png` funksiyasini ishlatamiz:

```python
# preprocess.py
from pathlib import Path
from app.dicom_utils import render_frame_png

for dcm in Path("yolo_dataset/images/train").rglob("*.dcm"):
    png_bytes = render_frame_png(dcm, max_dim=1024)
    out = dcm.with_suffix(".png")
    out.write_bytes(png_bytes)
    dcm.unlink()  # ixtiyoriy: DICOM'ni saqlash
```

Yoki to'liq pipeline'ni `app/coco_to_yolo.py` skript'iga `--render-png`
flag bilan kengaytirsa bo'ladi.

### 5.3 Train komandasi

```cmd
yolo train ^
  data=yolo_dataset/data.yaml ^
  model=yolov8m.pt ^
  imgsz=1024 ^
  epochs=100 ^
  batch=16 ^
  patience=20 ^
  device=0 ^
  project=runs/mammo ^
  name=v1
```

Yoki Python orqali:

```python
from ultralytics import YOLO

model = YOLO("yolov8m.pt")  # boshlang'ich og'irlik
results = model.train(
    data="yolo_dataset/data.yaml",
    imgsz=1024,
    epochs=100,
    batch=16,
    patience=20,
    device=0,
    project="runs/mammo",
    name="v1",
    plots=True,
)
```

### 5.4 Mammografiya uchun tavsiya etilgan parametrlar

| Parametr | Qiymat | Sabab |
|---|---|---|
| `imgsz` | 1024 | Mass odatda kichik (≥100×100 px), 640 yetarli emas |
| `batch` | 8-16 | 1024 imgsz bilan VRAM cheklovi |
| `epochs` | 100-300 | Mass detection sekin konvergensiya |
| `lr0` | 0.001 | Pre-trained'dan boshlanganda kichik LR |
| `cos_lr` | True | Keyingi epochlarda fine-tune |
| `patience` | 20-30 | Erta to'xtatish |
| `mosaic` | 0.5 | Mammografiya'da kontekst muhim, mosaic kamroq |
| `degrees` | 5 | Cheklangan rotation (medical anatomy) |
| `flipud` | 0 | Vertikal flip ishlatmaslik (chap/o'ng aniqlik) |
| `fliplr` | 0.5 | Gorizontal flip — chap/o'ng ko'krak |
| `hsv_v` | 0.1 | Yorug'lik o'zgarishi (W/L variation) |

### 5.5 Custom backbone (optional)

KETEM (digitaleye) yoki o'zingizning oldindan o'rgatilgan og'irligingizdan
boshlang:

```python
model = YOLO("app/models/digitaleye_yolo11_l.pt")
results = model.train(
    data="yolo_dataset/data.yaml",
    epochs=50,  # fine-tune kamroq epoch yetarli
    lr0=0.0001,  # o'rgatilgan og'irlikni saqlash uchun juda kichik LR
    freeze=10,   # birinchi 10 layerni muzlatish
)
```

---

## 6. Natijalarni baholash

Train tugagandan so'ng `runs/mammo/v1/` papkasida quyidagilar yaratiladi:

```
runs/mammo/v1/
  weights/
    best.pt        # eng yaxshi val mAP bilan
    last.pt        # oxirgi epoch
  results.png      # train/val loss + metrics chizmasi
  confusion_matrix.png
  PR_curve.png
  F1_curve.png
  val_batch0_labels.jpg   # haqiqiy bbox'lar
  val_batch0_pred.jpg     # bashoratlar
  results.csv      # epoch-by-epoch metrics
```

### 6.1 Asosiy metrikalar

| Metrik | Tavsif | Maqbul qiymat |
|---|---|---|
| **mAP@0.5** | mean Average Precision IoU=0.5 da | ≥0.65 |
| **mAP@0.5:0.95** | COCO standart (qattiqroq) | ≥0.40 |
| **Precision** | Topganlardan necha foiz to'g'ri | ≥0.70 |
| **Recall** | Borgenlardan necha foiz topildi | ≥0.75 |
| **F1** | Precision/Recall garmonik o'rta | ≥0.72 |

Mammografiya **recall** tahlili **precision**'dan muhim — har bir mass'ni
o'tkazib yuborish hayotga ta'sir qiladi.

### 6.2 Validatsiya komandasi

```cmd
yolo val data=yolo_dataset/data.yaml model=runs/mammo/v1/weights/best.pt imgsz=1024
```

Chiqishda metrikalar:

```
                 Class     Images  Instances      Box(P          R      mAP50  mAP50-95)
                   all        50         87       0.76       0.81       0.78       0.45
                  mass        50         52       0.82       0.85       0.82       0.51
         calcification        50         28       0.71       0.79       0.75       0.42
             asymmetry        50          7       0.65       0.71       0.68       0.31
```

### 6.3 Confusion matrix tahlili

`confusion_matrix.png`'da diagonal element — to'g'ri klassifikatsiya. Off-
diagonal — chalkashishlar:

- **mass ↔ asymmetry** — eng tez-tez chalkashish
- **calcification → background** — kichik elementlar yo'qotilishi (imgsz
  oshirish)

### 6.4 Real DICOM'da test

```python
from ultralytics import YOLO
from app.dicom_utils import render_frame_png

model = YOLO("runs/mammo/v1/weights/best.pt")
png = render_frame_png(Path("test.dcm"), max_dim=1024)
results = model.predict(png, imgsz=1024, conf=0.25)
for r in results:
    for box, cls, conf in zip(r.boxes.xyxy, r.boxes.cls, r.boxes.conf):
        print(f"{model.names[int(cls)]} {conf:.2f} bbox={box.tolist()}")
```

---

## 7. Production'ga olib chiqish

### 7.1 Modelni MAMOGRAF Viewer'ga ulash

```cmd
copy runs\mammo\v1\weights\best.pt app\models\custom_v1.pt
:: server qayta ishga tushiriladi
```

UI'da AI model dropdown'da **`custom_v1.pt`** ko'rinadi. Annotatorlar uni
tanlab AI tahlilda ishlatishi mumkin.

### 7.2 A/B testing

Ikki modelni parallel ishlatish:

1. `digitaleye_yolo11_l.pt` (baseline)
2. `custom_v1.pt` (sizning fine-tuned)

Annotator har bir DICOM'da ikkalasidan ham natijalarni ko'rib, qaysi
yaxshi ekanligini belgilaydi. Audit log orqali ishonchli baholash.

### 7.3 Continual learning loop

```
Real DICOM kelishi → AI infer (custom_v1) → annotator tuzatadi
                          ↑                          ↓
                          │                  approve qilingan
                          │                  yangi annotatsiyalar
                          │                          ↓
                          └─── re-train custom_v2 ←──┘
```

Har 1-3 oyda:
1. Yangi approved annotatsiyalarni eksport
2. Avvalgi train datasetga qo'shish
3. `custom_v1.pt`'dan fine-tune (kam epoch, kichik LR)
4. Validatsiya — metrikalar yaxshilanganmi?
5. `custom_v2.pt` deploy

### 7.4 Quality monitoring

📊 Statistika modal orqali:

- **AI suggestion accept rate** — AI tomonidan chiqarilgan bbox'larning
  necha foizi annotator tomonidan saqlanadi
- **Reviewer agreement** — annotator chizgan vs reviewer approve qilgan
- **Average review time** — tezroq inference ⇒ tezroq review

---

## 8. Bias va etika tahlili

### 8.1 Demographic stratification

COCO eksportda har bir image'da `patient.sex`, `birth_date` mavjud.
Strata bo'yicha mAP hisoblash:

```python
import json
from collections import defaultdict

coco = json.load(open("annotations_coco.json"))
by_age = defaultdict(list)

for img in coco["images"]:
    if not img.get("patient"): continue
    dob = img["patient"].get("birth_date")
    if dob:
        year = int(dob[:4])
        age = 2026 - year
        bucket = "<40" if age < 40 else "40-60" if age < 60 else ">60"
        by_age[bucket].append(img["id"])

# har strata uchun alohida YOLO val
```

### 8.2 Inter-annotator agreement

```python
# Cohen's kappa hisoblash
from sklearn.metrics import cohen_kappa_score

# COCO'dan: annotator A va B chizgan bbox'lar
# IoU > 0.5 bo'lsa "agree" deb hisoblash
kappa = cohen_kappa_score(labels_a, labels_b)
print(f"Cohen kappa: {kappa:.3f}")  # > 0.6 yaxshi
```

### 8.3 Kalibrlash (calibration)

Model `confidence=0.85` desa, haqiqatan 85% to'g'rimi?

Reliability diagram chizish:
```python
from sklearn.calibration import calibration_curve
prob_true, prob_pred = calibration_curve(y_true, y_pred_conf, n_bins=10)
# diagonal — perfect calibration
```

---

## 9. Yakuniy checklist

Tadqiqot publishing'ga tayyor bo'lish uchun:

- [ ] Dataset de-identifikatsiyalangan (🛡 De-ID barcha DICOM'lar uchun)
- [ ] Train/val/test split — random emas, **bemor-darajada** (data leakage
      yo'q)
- [ ] Class balance hisobotlangan (BI-RADS distribution table)
- [ ] Reviewer approval — kamida 80% annotatsiyalar `approved` status
- [ ] Inter-annotator kappa ≥ 0.6 (IRB tadqiqotlari uchun)
- [ ] Model card — limitations, bias, intended use
- [ ] Audit log eksport (CSV) — reproducibility
- [ ] COCO JSON `info` maydonida tadqiqot meta (institution, IRB number)
- [ ] Test set hech qachon training paytida ko'rilmagan

---

## 10. Tipik tadqiqot stseneriya'lari

### 10.1 BRCA tadqiqot (genetik moyillik)

- Polygon tool ishlatish (aniq mass shakli)
- DICOM-SEG eksport
- Mask R-CNN modeliga o'tkazish
- Shape descriptors (compactness, eccentricity) hisoblash

### 10.2 Multi-vendor robustlik

- Bir nechta DICOM manbai (FUJIFILM, Siemens, GE)
- Vendor-stratified mAP
- Domain adaptation tadqiqoti

### 10.3 Federated learning

- 3 ta hospital ma'lumotlarini birlashtirmasdan o'rgatish
- Har bir hospital o'z `app/models/local_v1.pt`'ni yaratadi
- Markaziy server faqat gradientlarni jamlaydi (FedAvg)

### 10.4 Active learning

- Mass detection uchun confidence past bo'lgan DICOM'larni avval annotate
  qilish
- 📋 Mening ishim tab → "draft" filter → AI noaniq bo'lgan namunalar
- Annotation effort'ni 30-50% kamaytirish

---

## 11. CLI komandalari to'plami (tadqiqotchi uchun)

```cmd
:: Dataset eksport
curl -H "Authorization: Bearer $TOKEN" ^
  http://127.0.0.1:8000/api/export?format=coco -o dataset.json

:: COCO → YOLO
.venv\Scripts\python.exe -m app.coco_to_yolo dataset.json ^
  --out yolo_data/ --train-val 0.8 --copy-images

:: Audit jurnali
curl -H "Authorization: Bearer $TOKEN" ^
  http://127.0.0.1:8000/api/annotations/history.csv -o audit.csv

:: Statistik dump
curl -H "Authorization: Bearer $TOKEN" ^
  http://127.0.0.1:8000/api/stats/overview > stats.json

:: Train
yolo train data=yolo_data/data.yaml model=yolov8m.pt imgsz=1024 epochs=100

:: Validation
yolo val data=yolo_data/data.yaml model=runs/mammo/v1/weights/best.pt

:: Predict
yolo predict model=best.pt source=test/img.png imgsz=1024 conf=0.25 save=True
```

---

## 12. Yordam

- **Dataset format**: [COCO spec](https://cocodataset.org/#format-data)
- **Ultralytics docs**: https://docs.ultralytics.com/
- **DICOM-SR**: DICOM PS3.16 standart, TID 1500 templates
- **DICOM-SEG**: highdicom hujjatlari + DICOM PS3.3 C.8.20
- Loyihaga aloqador: [GPU.md](GPU.md), [DEPLOY.md](DEPLOY.md), va asosiy
  [FOYDALANUVCHI_QOLLANMA.md](FOYDALANUVCHI_QOLLANMA.md)
