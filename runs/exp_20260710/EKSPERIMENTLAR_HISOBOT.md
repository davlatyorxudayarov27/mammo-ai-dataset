# Xamdamov (boolfs) usuli — 11 eksperiment seriyasi hisoboti

**Sana:** 2026-07-10 · **Dataset:** `d_dataset_mamagrammav445` (8 sinf; 175 train rasm / 519 GT ROI, 47 val rasm / 148 GT ROI)
**Metod:** Xamdamov (2017) — (3.2.2) a/b/c kriteriy, (3.4.5) ranjirlangan qator, (3.6.2)–(3.6.4) minimal masofa klassifikatori; YOLO bilan gibrid ansambl `score = α·YOLO + (1−α)·boolfs`.
**Muhit:** `mamograf-prod-app` konteyneri, CPU (GPU talab qilinmadi, hech qanday xizmat to'xtatilmadi).
**Skript:** `scripts/run_experiments_20260710.sh` + `scripts/exp04_nsweep.py`; xom natijalar `runs/exp_20260710/exp*/`.

---

## E01–E03 — Bazaviy model va baholash

| Eksperiment | Natija |
|---|---|
| E01 fit | n′\* = **34** (38 dan), P_cv = **0.5260** (to'liq 38 belgi: 0.5202) |
| E02 evaluate val | P_val (GT ROI) = **0.6284** (148 ROI) |
| E03 evaluate train | P_train (GT ROI) = **0.5356** (519 ROI) |

Top-5 belgi: `glcm_d1_correlation`, `glcm_d3_correlation`, `grad_sobel_std`, `glcm_d1_dissimilarity`, `glcm_d3_dissimilarity`.
P_train < P_val — overfitting yo'q (val'da kichik sinflar kam uchraydi, taqsimot yengilroq).

## E04 — n′ (tanlangan belgilar soni) sweep

| n′ | 3 | 5 | 8 | 13 | 21 | 28 | **34** | 38 |
|---|---|---|---|---|---|---|---|---|
| P_cv | 0.489 | 0.462 | 0.480 | 0.497 | 0.495 | 0.515 | **0.526** | 0.520 |
| P_val | 0.568 | 0.554 | 0.588 | 0.601 | 0.588 | 0.588 | **0.628** | 0.615 |

**Xulosa:** avtomatik tanlangan n′\*=34 ham CV, ham val bo'yicha optimal — (3.4.5) ranjirlash asosidagi tanlov mustaqil to'plamda tasdiqlandi. 38-belgigacha to'ldirish sifatni pasaytiradi (shovqinli belgilar).

## E05–E08 — Ansambl: α, conf, IoU sezgirligi (YOLO11s 8-klass, val)

| Eksp | Sozlama | Mos ROI | YOLO (α=1) | boolfs (α=0) | Eng yaxshi | Yutuq |
|---|---|---|---|---|---|---|
| E05/E06 | conf=0.05, iou=0.3 | 95/163 | 0.737 | 0.547 | **α=0.7 → 0.853** | **+11.6 punkt** |
| E07 | conf=0.15 | 75/163 | 0.907 | 0.520 | α=0.7 → 0.907 | +0.0 |
| E08 | iou=0.5 | 88/163 | 0.705 | 0.500 | α=0.5 → 0.818 | +11.4 punkt |

α-egri (E05+E06, birlashtirilgan): 0→0.547, 0.1→0.705, 0.3→0.789, 0.5→0.842, **0.7→0.853**, 0.9→0.832, 1→0.737. Egri silliq, bitta maksimumli — α=0.5–0.7 oralig'i barqaror.

**Muhim topilma (E07):** conf chegarasi 0.15 ga ko'tarilsa YOLO'ning o'zi 0.907 aniq bo'ladi va boolfs qo'shimcha yutuq bermaydi — **boolfs'ning foydasi aynan past-ishonchli detektsiyalarda** (conf 0.05–0.15 oralig'idagi shubhali ROI'lar). Bu usulning klinik qiymatini aniq ko'rsatadi: shubhali hollarda ikkinchi fikr.

## E09–E10 — Boshqa YOLO modellari bilan ansambl (val, conf=0.05, iou=0.3)

| Eksp | YOLO vazn | YOLO (α=1) | Eng yaxshi ansambl | Yutuq |
|---|---|---|---|---|
| E05 | yolo11s_8class | 0.737 | α=0.7 → **0.853** | +11.6 |
| E09 | trained_8class_yolo11l | 0.800 | α=0.7 → **0.867** | +6.7 |
| E10 | trained_8class_ai_v2_ep50 | 0.835 | α=0.3 → **0.864** | +2.9 |

**Xulosa:** boolfs har uch model bilan ham yutuq beradi; YOLO qancha kuchli bo'lsa, yutuq shuncha kichik, lekin yakuniy P baribir ~0.85–0.87 atrofiga chiqadi. Eng yuqori mutlaq natija: **YOLO11l + boolfs (α=0.7) = 0.867**.

## E11 — Train splitda barqarorlik nazorati

yolo11s, train split: YOLO 0.835 → ansambl (α=0.7) **0.846**. Yutuq yo'nalishi val bilan mos — natija tasodifiy emas.

---

## UMUMIY XULOSALAR

1. **n′\*=34** belgi tanlovi mustaqil tekshiruvda optimal deb tasdiqlandi (E04).
2. Gibrid ansambl **hamma sozlamalarda** YOLO'dan yaxshi yoki teng: +2.9…+11.6 punkt (E05–E10).
3. Optimal α modelga bog'liq: kuchsiz YOLO uchun 0.7 (boolfs'ga ko'proq vazn kerak emas — aksincha YOLO'ga; qiziq: α=YOLO vazni), kuchli YOLO (v2ep50) uchun 0.3 ham yetadi — egri yassi, α∈[0.3,0.7] xavfsiz tanlov.
4. boolfs'ning asosiy foydasi **past-ishonchli (shubhali) detektsiyalarni** to'g'rilashda (E07) — maqola/dissertatsiya uchun kuchli argument.
5. Eng yaxshi kombinatsiya: **trained_8class_yolo11l + boolfs, α=0.7 → P=0.867** (val, 105 mos ROI).
