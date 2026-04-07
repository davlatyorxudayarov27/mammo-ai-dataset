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

```id="qv8a2s"
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

Metadata file:

```id="s3j2lx"
mapping_clean.xlsx
```

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

## 🚀 Usage

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

This dataset is provided for **non-commercial research use only**.

---

## 👨‍💻 Author

Developed as part of the **AI Scan project** in the field of medical AI and radiological image analysis.

---

## 📬 Contact

For collaboration, research, or dataset access inquiries, please contact the repository owner.
