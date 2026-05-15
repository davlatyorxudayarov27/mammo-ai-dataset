# AI Scan: Mammography AI Dataset (De-identified)

## 📌 Description

This repository contains a structured and anonymized mammography dataset developed as part of the **AI Scan project**.

**AI Scan** is an artificial intelligence–based system designed for the **early detection and diagnosis of breast tumors (benign and malignant)** using medical imaging and radiomics approaches.

The dataset is prepared for:

* Breast cancer detection
* BI-RADS classification
* Radiomics-based analysis
* Deep learning model training (CNN, hybrid models)

All data has been **fully de-identified** to ensure patient privacy.

---

## 🧠 About AI Scan Project

**AI Scan** focuses on:

* Early detection of breast cancer
* Integration of AI into clinical workflows (PACS-compatible)
* Development of radiomics + deep learning models
* Improving diagnostic accuracy and reducing analysis time

The dataset in this repository serves as a **core training and validation resource** for the AI Scan system.

---

## 🗂 Dataset Structure

```
encrypted_dataset_grouped/
│
├── GROUP_000001/
│   ├── IMG_001.cdcm
│   ├── IMG_002.cdcm
│
├── GROUP_000002/
│   ├── IMG_001.cdcm
│   ├── IMG_002.cdcm
│
...
```

Each `GROUP_XXXXX` represents a **single study (patient case)**.

---

## 📊 Metadata

Metadata file: `mapping_clean.xlsx`

Main fields:

| Column                | Description                 |
| --------------------- | --------------------------- |
| study_id / group_code | Anonymized study identifier |
| image_code            | Image ID                    |
| image_index           | Image order                 |
| view_position         | CC, MLO, etc.               |
| body_part             | Breast                      |
| manufacturer          | Device manufacturer         |
| model                 | Device model                |
| presentation_type     | Image format/type           |
| status                | Processing status           |

---

## 🔐 Data Privacy & De-identification

The dataset has been processed according to strict privacy requirements:

* ❌ Patient names (F.I.O.) removed
* ❌ Dates removed or anonymized
* ❌ IDs and personal identifiers removed
* ❌ Clinical free-text cleaned or excluded

Only anonymized identifiers such as `GROUP_XXXXX` are used.

### Automatic anonymization on upload

The web application automatically removes PHI tags from every uploaded
DICOM file **before** it becomes available for boxing/annotation or
export. Subsequent steps (annotation, AI inference, export) all operate
on the de-identified copy — original PHI never enters the workflow.

What gets removed/replaced:

* `PatientName` → `ANONYMOUS^PATIENT`
* `PatientID` → `ANON`
* `ReferringPhysicianName`, `OperatorsName`, `InstitutionName`,
  `StationName`, `AccessionNumber`, etc. → cleared
* `StudyDate`/`AcquisitionDate` → year preserved, month/day set to `0101`
* `PatientIdentityRemoved` tag set to `YES`
* Pixel data, image dimensions, and `Modality` are **preserved** (needed
  for AI/research)

Configuration: set `AUTO_DEIDENTIFY=0` to disable (env var). Default: on.

Re-anonymize existing files (CLI):

```bash
python -m app.deidentify app/uploads
# or inside Docker:
docker compose exec app python -m app.deidentify /app/app/uploads
```

---

## ⚙️ Preprocessing Pipeline

The dataset was prepared using the following steps:

* DICOM metadata anonymization
* File renaming and grouping by study
* Removal of personal identifiers from text
* Hash-based ID generation
* Filtering invalid or incomplete records
* Cleaning of unnecessary folders

---

## 💻 AI Scan — Source Code

In addition to the dataset, this repository also contains the **AI Scan web application** source code (FastAPI backend + DICOM viewer UI + research/training scripts + model architectures).

Key folders:

* `app/` — FastAPI web application (DICOM viewer, annotations, AI suggestions, PACS, JWT+TOTP auth)
* `app/models_arch/` — model architectures (no weights):
  * **BCA-YOLO** — Bilateral Cross-Attention YOLO for mammographic lesion detection
  * **TILLNet-Det** — text-informed FiLM-modulated FCOS detector
  * **XS-Classifier** — cross-script TF-IDF + Logistic Regression for multilingual (Uzbek-Cyrillic / Uzbek-Latin / Russian) report classification
* `app/research/` — training pipelines, pseudo-labels, preprocessing, statistical tests
* `app/static/` — web UI (HTML/JS/CSS)

Install & run:

```bash
python -m venv .venv
.venv\Scripts\activate     # Windows
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Or via Docker: `docker compose up --build`

> Trained model weights (`*.pt`) and patient data (DICOMs, annotations, SQLite DB) are **not** included in this repository — see `.gitignore`.

---

## 🚀 Dataset Usage

Typical workflow:

1. Load metadata (`mapping_clean.xlsx`)
2. Map `group_code` → folder
3. Load DICOM images
4. Apply preprocessing (normalization, augmentation)
5. Train AI model (CNN / Radiomics + DL)

---

## 🧠 AI Applications

This dataset supports:

* Breast cancer classification (benign vs malignant)
* BI-RADS prediction
* Lesion detection
* Radiomics feature extraction
* Hybrid AI models (CNN + radiomics)

---

## ⚠️ Important Notes

* Dataset is for **research purposes only**
* Not intended for direct clinical use
* Requires validation before deployment
* Must comply with ethical and regulatory standards

---

## 🛠 Requirements

Recommended tools:

* Python 3.9+
* pandas
* pydicom
* numpy
* torch / tensorflow
* scikit-learn

---

## 📜 License

This dataset and source code are provided for **non-commercial research use only**.

---

## 👨‍💻 Author

Developed as part of the **AI Scan project** in the field of medical AI and radiological image analysis.

---

## 📬 Contact

For collaboration, research, or dataset access inquiries, please contact the repository owner.
