# Claude tomonidan bajarilgan ishlar jurnali (aiscan.airi.uz / MAMOGRAF)

> Loyiha serverga ko'chirilgandan (deploy) keyin Claude bajargan barcha o'zgarishlar.
> Maqsad: shu o'zgarishlarni **lokal kompyuterdagi loyihaga** ham qo'shish.

Server: `aiscan.airi.uz` — FastAPI + Docker. Kod ishlaydigan nusxa `mamograf-prod_app_db`
volume ichida (`/app/app`). Manba kod: `~/plan_project_new/app/`.

---

## 1-sessiya — 2026-06-03 (3-iyun)

### 1.1. Yangi kod deploy qilindi (annotatsiyalar saqlanib)
- Backup olindi → `rsync` (db.sqlite3, .jwt_secret, uploads, annotations, models **chetlab**) → konteyner restart.
- Natija: belgilashlar **407 ta**, bemorlar **1570 ta** — hech narsa o'chmadi.

### 1.2. 3 ta yetishmayotgan AI model qo'shildi
- Serverda 2 ta model bor edi, lokalda 5 ta. Yetishmagan 3 tasi `app_models` volume'ga qo'shildi:
  `yolo9_e.pt`, `yolo11_x.pt`, `yolo10_x.pt`.
- Kod modellarni dinamik (`glob("*.pt")`) o'qigani uchun restart shart bo'lmadi.

### 1.3. 🐞 KOD TUZATISH — Annotatsiya metka ro'yxati to'liq ko'rinmasligi
**Muammo:** O'ng paneldagi metka (mass, calcification, …) ro'yxati kesilib, faqat skrol bilan chiqardi.
**Sabab:** `.ms-panel` `position: absolute` edi, ota-konteyner `.rpane { overflow: auto }` uni kesardi.
**Yechim:**
- `static/style.css` — `.ms-panel` → `position: fixed` (top/left endi JS belgilaydi).
- `static/app.js` — `positionPanel()` funksiyasi qo'shildi (tugma yoniga aniq joylashtiradi, ekranga sig'masa yuqoriga ochiladi) + skrol qilinganda ro'yxat yopiladi (capture rejimi).

**O'zgargan fayllar:** `app/static/style.css`, `app/static/app.js`

---

## 2-sessiya — 2026-06-14 (14-iyun)

### 2.1. Yangi kod deploy qilindi (13-iyun versiyasi)
- Backup → `rsync` (data chetlab) → restart. `annotation_history` 556 → 556, o'chmadi.

### 2.2. ✨ YANGI FUNKSIYA — AI batch belgisi
**Talab:** AI batch yaratgan yozuvda "Yaratdi:" qismida AI ekani izoh shaklida ko'rinsin.
**Muammo:** AI batch (`/api/inference/batch`, auto_save) `created_by` ni odam username qilib qo'yardi → "Yaratdi: aziz" deb ko'rinardi.
**Yechim:** `ai_source` maydoni asos qilindi. Format: **`Yaratdi: aziz · 🤖 AI batch (izoh)`** — panel + ro'yxat + eksportda.
- `app/main.py` — `/api/annotations/list` (dashboard ro'yxati) javobiga `ai_source` qo'shildi.
- `app/static/app.js` — panel va ro'yxatda `🤖 AI batch` belgisi chiziladi.
- `app/exporters.py` — eksportga AI batch izohi.
- `app/dicom_sr.py` — DICOM SR eksportiga AI batch izohi.

**O'zgargan fayllar:** `app/main.py`, `app/static/app.js`, `app/exporters.py`, `app/dicom_sr.py`

### 2.3. ✨ YANGI FUNKSIYA — Fayl/papkada annotatsiya soni belgisi va rang
**Talab:** Annotatsiyasi bor fayl/papka boshqa rangda bo'lsin yoki annotatsiya soni belgisi ko'rsatilsin.
**Holat:** Fayllarda (upload + local) `anno-pill` belgisi allaqachon bor edi; **papkalarda** yo'q edi.
**Yechim:**
- `app/main.py` — `/api/local/list` endi papkalar uchun ichidagi annotatsiyalarni **rekursiv** hisoblaydi (`source`+`ref` bo'yicha yig'adi).
- `app/static/app.js` — `loadLocalDir` papkalarga `annoCount` beradi; `renderFileList` annotatsiyali elementga `has-anno` klassi qo'yadi.
- `app/static/style.css` — `has-anno` → nom **yashil** rangda + son belgisi (pill).

**O'zgargan fayllar:** `app/main.py`, `app/static/app.js`, `app/static/style.css`

### 2.4. 🗂 DATA AMALI — ALL_dicom papka tuzilmasini soddalashtirish (flatten)
> Bu faqat **serverdagi DICOM fayllarda** bajarilgan amal, kodga tegmaydi. Lokalga ko'chirishga shart emas.

- Avval: `ALL_dicom/<guruh>/<nomer>/<studyUID>/<seriesUID>/*.dcm`
- Keyin: `ALL_dicom/<guruh>/<nomer>/*.dcm`
- 7531 `.dcm` ko'chirildi, 9118 bo'sh shifrlangan papka o'chirildi, 0 yo'qotish. Rollback manifesti: `~/all_dicom_flatten_manifest.tsv`.

### 2.5. ✨ YANGI FUNKSIYA — "Keraksiz papkalarni tozalash" tugmasi
**Talab:** Yangi fayllar yuklangach, yuqoridagi flatten amalini avtomatik bajaradigan tugma.
**Yechim:**
- `app/main.py` — yangi flatten endpoint (chuqurdagi UID papkalarini tozalaydi).
- `app/static/index.html` — lokal brauzerga (chap panel, "Lokal" tab) tugma qo'shildi.
- `app/static/app.js` — tugma ishlovchisi.

**⚠️ Eslatma:** Serverda tugma deploy qilingan, **lekin hozircha faol emas** — chunki konteynerda
`/data/dicom` `:ro` (read-only) ulangan (`docker-compose.prod.yml:25`). Tugma ishlashi uchun mount
`:rw` ga o'zgartirilib, konteyner qayta yaratilishi kerak (foydalanuvchi hozircha rad etdi).
**Lokal kompyuterda bu cheklov bo'lmasligi mumkin** — agar lokalda mount read-write bo'lsa, tugma ishlaydi.

**O'zgargan fayllar:** `app/main.py`, `app/static/index.html`, `app/static/app.js`

---

## XULOSA — Lokalga ko'chirish uchun kerakli fayllar

Barcha o'zgarishlar **6 ta faylda** jamlangan. Eng to'liq, yangilangan nusxa: `~/plan_project_new/app/`

| Fayl | 3-iyun | 14-iyun |
|------|:------:|:-------:|
| `app/main.py` | | ✅ AI batch, papka soni, flatten endpoint |
| `app/static/app.js` | ✅ metka ro'yxati | ✅ AI batch, papka rang, tugma |
| `app/static/style.css` | ✅ ms-panel fix | ✅ has-anno yashil rang |
| `app/static/index.html` | | ✅ tozalash tugmasi |
| `app/exporters.py` | | ✅ AI batch izoh |
| `app/dicom_sr.py` | | ✅ AI batch izoh |

### Lokalga qanday qo'llash kerak
1. WinSCP bilan serverga ulaning (SFTP, host `10.10.0.75`, login `ai`).
2. `/home/ai/plan_project_new/app/` papkasidan yuqoridagi **6 ta faylni** lokal loyihangizning
   mos joyiga (`D:\Project_MAMOGRAF\plan_project\app\...`) yuklab oling (ustiga yozing).
3. Lokalda ilovani qayta ishga tushiring (`run.bat` yoki Docker restart).

> ⚠️ Agar lokal kodingizni shu fayllarda **qo'lda** o'zgartirgan bo'lsangiz, ustiga yozishdan oldin
> nusxa oling — aks holda o'sha o'zgarishlar yo'qoladi.

---
---

# DAVOMI — 14-iyundan keyingi sessiyalar (2026-07-10 da yozildi)

> Quyidagi bo'limlar 2026-07-10 kuni git tarixi, xotira yozuvlari va prod volume tahlili
> asosida jamlab yozildi.

---

## 3-sessiya — 2026-06-18 (18-iyun)

### 3.1. 🐞 Asboblarni to'liq tekshiruv — 4 ta xato tuzatildi
- Ruler / Angle / Smart-click o'lchov asboblari ishlamasligi tuzatildi.
- `renderAnnoList`/handles, avtomatik W/L (window/level), HEAD-probe, SEG eksport xatolari.
- Commitlar: `afc9f65`, `c1d109e`.

### 3.2. ✨ To'liq YOLO eksport
- `/api/export?format=yolo` endi **to'liq, o'qitishga tayyor dataset** beradi (rasm + label + data.yaml).
- Commit: `27ff63c`.

### 3.3. 🔧 scripts/pull_from_aiscan.py
- Serverdan annotatsiya + DICOM'larni lokal kompyuterga ko'chirish skripti. Commit: `2313133`.

### 3.4. 📄 Loyiha hujjatlari
- Ma'lumotnoma + taqdimot qo'shildi (`docs/`). Commit: `241f7c4`.

---

## 4-sessiya — 2026-06-21..22 (21-22 iyun)

### 4.1. ✨ Radiomika benign/malignant klassifikatori
- `scripts/train_radiomics_clf.py` + UI'da "🔬 Xavf tahlili" tugmasi; `requirements`ga scikit-learn.
- Commitlar: `79aaff8`, `58f0375`.

### 4.2. 🎨 UI ixchamlashtirish
- Ortiqcha tugmalar menyuga yig'ildi, ishlash sohasi kengaytirildi. Commit: `7e976e3`.

### 4.3. 🚀 CI/CD
- GitHub push'da serverga avtomatik deploy (self-hosted runner + Docker). `CICD_SETUP.md`. Commit: `51af638`.

### 4.4. 📋 Instrumentlar tekshiruvi
- `INSTRUMENTLAR_TEKSHIRUVI_21-iyun.md` — barcha asboblar ro'yxat bilan tekshirildi.

---

## 5-sessiya — 2026-06-26..28 (26-28 iyun)

### 5.1. ✨ Masofaviy GPU'da o'qitish (training)
- Training endi GPU serverda (10.10.0.72, RTX 3090) bajariladi: `mamograf-train.service` (:8077).
- Ilova `REMOTE_TRAIN_URL` + `app/remote_train.py` orqali proksi qiladi; `X-Train-Token` autentifikatsiya.
- Commit: `cac319e`.

### 5.2. ✨ Ollama "Hisobot" (lokal LLM)
- Annotatsiya asosida bemor hisobotini lokal LLM yozadi: Ollama (10.10.0.72, qwen2.5:7b), `OLLAMA_HOST` env.
- ⚠️ `report_findings.py` va `train_worker.py` prod volume'da yetishmayotgan edi — qo'shildi.

### 5.3. 🔒 Brute-force himoyasi
- Login lockout: 8 xato / 15 daqiqa + parol siyosati.
- Eslatma: X-Forwarded-For spoof qilinishi mumkin (`forwarded-allow-ips *`), IP-limit yolg'iz yetarli emas.

### 5.4. ✨ Landing sahifa
- Ilova `/app` marshrutiga ko'chdi, `/` — tanishtiruv (landing) sahifa. Test moslandi (`812364c`).

### 5.5. 🔧 Boshqa
- `scripts/test_full_app.py` — butun ilova tugmalarini avtomatik tekshiruv (`881c8ed`).
- `deploy_update.sh` — annotatsiyalarni saqlab xavfsiz yangilash (`939f21b`).
- Fix: train.html vertikal skrol (`c136d84`); dataset tayyorlash lokal annotatsiyalarni ham oladi (`b776812`).

---

## 6-sessiya — 2026-06-29 (29-iyun)

### 6.1. ✨ GPU'ga dataset oldindan yuklash
- Dataset prepare-vaqtida GPU serverga yuklanadi (`/datasets` + `dataset_name`) → train tugmasi bosilganda darhol boshlanadi. Commit: `094853c`.

### 6.2. 📄 PhD dissertatsiya generatori
- `scripts/make_dissertatsiya_phd.py` — docx generator (muallif Turaqulov, rahbar Xamdamov).
- Build **faqat konteynerda** (host'da pip yo'q). Zaxira: `MAMOGRAF_PhD_dissertatsiya_BACKUP_20260629.docx`.

### 6.3. 📄 Annotatsiya-yig'ish maqolasi
- `scripts/make_maqola_annotatsiya.py` — avtomatlashtirilgan annotatsiya yig'ish maqolasi (54 formula),
  dissertatsiyaga bob sifatida ulangan. 2 yangi model: YOLO11-Small mAP@50 0.43, YOLO9-compact 0.32.

---

## 7-sessiya — 2026-07-02 (2-iyul)

### 7.1. ✨ GMIC "Tashxis" paneli (benign/malignant)
- NYU GMIC modeli vendor qilindi: `app/gmic/` + `/api/inference/classify` marshrut.
- Out-of-box AUC 0.5 (domain shift) → MIL fine-tune bilan **AUC 0.725**.

### 7.2. 🔒 Audit log + Savatcha (soft-delete)
- Har bir harakat middleware orqali `audit_log` jadvaliga yoziladi.
- 7 ta delete endpoint endi soft-delete: `trash` jadvali, fayllar `_trash/` papkaga.
- Admin panelda "📋 Audit log" + "🗑 Savatcha" tablari. nan→None tuzatish.
- Commit: `20ee2d9`.

### 7.3. 🔧 Dockerfile.prod
- CPU-only torch + `.dockerignore` — yengil, barqaror image. Commit: `70c0f41`.

---

## 8-sessiya — 2026-07-03..09 (iyul boshi) ⚠️ QISMAN COMMIT QILINMAGAN

### 8.1. 🔒 Xavfsizlik auditi (5 loyiha bo'yicha, mamograf qismi)
- **CRITICAL tuzatildi:** PHI (bemor ma'lumoti) `/api` marshrutlariga auth-guard (`_guard_ok`) +
  HttpOnly cookie-auth (`auth_login`/`auth_logout` yangilandi).
- Eksport yo'lini tekshirish: `_validate_export_dest` (path traversal himoyasi).
- Sirlar 0600 fayllarda. **Bu tuzatishlar hozircha FAQAT prod volume'da!** (pastdagi 8.7 ga qarang)

### 8.2. ✨ BOOLFS — bulcha belgilar usuli (Xamdamov 2017)
- Bulcha (Boolean) belgi tanlash + minimal-masofa klassifikator — YOLO ustiga 2-bosqich.
- YOLO ensemble sinf-aniqligi **0.737 → 0.853**.
- Paket: `app/boolfs/` (7 modul: features, selector, criterion, classifier, pipeline, report) + `app/boolfs_api.py` + `app/static/boolfs.js`.
- Train UI: `train.html`da binafsha `bf-*` blok (Model Studio ichida).
- ⚠️ Bu kod **faqat prod volume'da edi** — 2026-07-10 da dev repo'ga qaytarib nusxalandi.
- Hisobot: konteynerda `app/boolfs_runs/`.

### 8.3. 📄 BOOLFS maqolalari
- 2 ta maqola docx (nazariy + amaliy), `scripts/make_maqola_boolfs.py`; raqamlar JSON'dan avtomatik.

### 8.4. ✨ 8-klassli detektor
- `d_dataset_mamagrammav445` — 8-klass (BIRADS juftlik, skin/nipple yo'q).
- GPU'ga to'g'ridan `X-Train-Token` bilan job yuborildi. YOLO11l mAP 0.417 (kichik datasetda small'dan o'zmadi).

### 8.5. ✨ Training natijalarini baholash (COMMIT QILINMAGAN, dev'da)
- `POST/GET /api/training/eval/{run_id}` — o'qitilgan modelni val-rasmlar ustida baholash (`main.py` +153 qator).
- `train.js` (+207): natija xulosasi kartalari (mAP50, mAP50-95, precision, recall, F1), parametrlar ko'rinishi.
- `train.html` (+54), `index.html` (+16), `app.js` (+5).
- Bu o'zgarishlar prod'ga deploy qilingan (train.js/index.html prod bilan bir xil).

### 8.6. ✨ Avtomatik annotatsiya (COMMIT QILINMAGAN)
- `scripts/auto_annotate.py` + `app/static/auto_annotate.html` (2026-07-08) — avtomatlashtirilgan annotatsiya yig'ish.
- `scripts/auto_backup.sh` — kunlik zaxira (cron 02:00): db + annotatsiya + labels, yakshanba to'liq (uploads bilan).

### 8.7. ⚠️⚠️ MUHIM: DEV va PROD KOD AJRALIB KETGAN (2026-07-10 holati)
Prod volume'dagi kod va `~/plan_project_new` dev nusxasi **ikki tomonlama** farq qiladi:

| Qayerda | Nima bor (ikkinchisida YO'Q) |
|---------|------------------------------|
| **Faqat PROD** | Xavfsizlik tuzatishlari (`_guard_ok`, cookie-auth, logout, `_validate_export_dest`), `boolfs_api` ulanishi, `/server` va `/iqttalim` reverse-proxy marshrutlari, train.html'dagi bf-* blok |
| **Faqat DEV** | AI annotatsiya rangi (`ai:*` → och yashil), admin nav (`_adminNav`), training eval (8.5) — oxirgisi prodga deploy qilingan |

**Xavf:** `deploy_update.sh` / rsync dev→volume yo'nalishida ishlaydi — ehtiyotsiz deploy
prod'dagi xavfsizlik tuzatishlarini O'CHIRIB yuboradi!
**Chora (2026-07-10):** prod kodning to'liq snapshoti olindi →
`backups/prod_code_snapshot_20260710.tar.gz` (276K, kod fayllari: *.py, static, boolfs, gmic/src, scripts).
**✅ MERGE BAJARILDI (2026-07-10):** prod'dagi barcha noyob o'zgarishlar dev'ga qaytarildi:
- `main.py`, `train.html` — prod versiyasi olindi (dev'dagi hamma narsa + xavfsizlik + bf-blok ichida bor edi);
- `app.js` — dev (yangiroq: study hanging 4-view, GMIC diag, admin nav) + prod'dan cookie-logout 2 qatori;
- prod-only sahifalar nusxalandi: `ai_report.html`, `preprocessing_lab.html`, `auto_annotate_status.html`.
- ⚠️ Yagona hal qilinmagan farq: `auto_annotate.html` dev va prod'da ikki xil variant (ikkalasi 08-iyul);
  dev'niki saqlandi, prod'niki snapshot arxivida turibdi.
Endi dev → prod deploy xavfsiz (dev to'liq superset).

---

## YANGILANGAN XULOSA (2026-07-10)

- Git'dagi oxirgi commit: `70c0f41` (2026-07-02). 8-sessiya ishlari hali commit qilinmagan.
- Eng to'liq **UI/train** kod: dev (`~/plan_project_new/app/`); eng to'liq **xavfsizlik/boolfs** kod: prod volume.
- Prod kod snapshoti: `backups/prod_code_snapshot_20260710.tar.gz`.
- Kunlik ma'lumot zaxirasi: `backups/auto/` (cron 02:00, `scripts/auto_backup.sh`).

---

## 9-sessiya — 2026-07-10 (10-iyul, davomi)

### 9.1. 🧪 Xamdamov (boolfs) usuli — 11 eksperiment seriyasi
- Joy: `~/mamograf_yangilash_21-iyun`, konteynerda CPU'da (GPU kerak bo'lmadi, xizmatlar to'xtatilmadi).
- Skriptlar: `scripts/run_experiments_20260710.sh`, `scripts/exp04_nsweep.py`; natijalar `runs/exp_20260710/`.
- Asosiy natijalar (val, GT bilan mos ROI'larda sinf-aniqlik P):
  - n′ sweep: avtomatik n′*=34 ham CV (0.526), ham val (0.628) bo'yicha optimal deb TASDIQLANDI;
  - yolo11s: 0.737 → ansambl α=0.7 **0.853** (+11.6 punkt);
  - yolo11l: 0.800 → **0.867** (+6.7) — eng yuqori mutlaq natija;
  - v2_ep50: 0.835 → **0.864** (+2.9, α=0.3);
  - iou=0.5 da ham +11.4; train splitda ham +1.1 (yo'nalish mos);
  - MUHIM TOPILMA: conf=0.15 da YOLO o'zi 0.907 — boolfs foydasi aynan PAST-ISHONCHLI
    detektsiyalarda (shubhali ROI'larga "ikkinchi fikr") — maqola uchun kuchli argument.
- To'liq hisobot: `runs/exp_20260710/EKSPERIMENTLAR_HISOBOT.md`.

### 9.2. 📄 Eksperiment natijalari bo'yicha maqola — 3 tilda, OMML formulalar
- Fayllar: `MAMOGRAF_Maqola_2026_Ansambl_{UZ,RU,EN}.docx` (~1600-1900 so'z, har birida
  13 tenglama, 5 jadval, 2 grafik).
- **Formulalar Word native OMML** (`m:oMath`) — oldingi maqolalardagidek matplotlib PNG rasm EMAS.
  Word/MathType'da to'g'ridan tahrirlanadi. Tekshirildi: pandoc docx→latex OMML'ni to'liq to'g'ri
  o'qidi (∑ limitlari, kasrlar, x̄ aksent, argmin/argmax ostki limitlari).
- Skriptlar: `scripts/omml.py` (OMML quruvchi), `scripts/maqola_formulalar.py` (13 formula),
  `scripts/make_maqola_exp2026.py` (3 tilli matn + grafiklar + docx).
- Barcha sonlar `runs/exp_20260710/*/`.json dan avtomatik o'qiladi (qo'lda kiritilmagan).
- Build: `docker run --rm -v $PWD:/work -w /work mamograf-prod-app sh -c "pip install -q python-docx && python scripts/make_maqola_exp2026.py"`

### 9.3. 📘 Dissertatsiyaga yangi bob qo'shildi (bulcha ansambl)
- **"II bob (davomi). Bulcha dasturlash asosida informativ belgilarni tanlash va
  interpretatsiyalanadigan gibrid ansambl"** — bob2 dan keyin joylashtirildi, mundarijaga ham.
- 7 ta paragraf (2.8-§ … 2.14-§), 13 tenglama ((2.15)–(2.27)), 5 jadval (2.5–2.9),
  2 rasm (2.5–2.6), bob xulosalari (5 band).
- Formulalar **Word native OMML** (dissertatsiyaning qolgan qismi hali LaTeX→PNG).
- Modul: `scripts/dissertatsiya_bob_boolfs.py`; u `make_maqola_exp2026.py` dan sonlarni,
  `maqola_formulalar.py` dan tenglamalarni oladi (dublikat matn yo'q).
- `scripts/make_dissertatsiya_phd.py` ga: `img_path()` yordamchisi + `@section bob2a_boolfs` + mundarija.
- Ma'lumot: `runs/exp_20260710/` va `doc_assets_exp2026/` mamograf_yangilash_21-iyun'dan ko'chirildi.
- Zaxira: `backups/MAMOGRAF_PhD_dissertatsiya_BEFORE_boolfs_20260710.docx`.
- Hajm: 14 676 so'z, 11 jadval, 102 rasm.

> ⚠️ **Aniqlangan eski nuqson (tuzatilmagan):** dissertatsiya matnida 80 ta xom LaTeX bo'lagi
> ko'rinib turibdi (`$\mathrm{softplus}$`, `$f_{deep}$`, `$F_v^{(s)}$` …) — `para()` satr ichidagi
> matematikani render qilmaydi. Bu yangi bobga taalluqli emas (unda 0 ta). Tuzatish uchun satr ichi
> matematikani OMML'ga o'tkazish kerak.

### 9.4. 🔬 Maqola natijalari qayta hisoblandi — to'liq metrika + halol protokol
**Muammo:** maqolada faqat P (aniqlik) bor edi, sezgirlik/o'ziga xoslik/AUC yo'q; grafiklarda
noaniqlik ko'rsatilmagan; α ansambl vazni **val to'plamda** tanlanardi (optimistik siljish).

**Qilingan ishlar:**
- `scripts/exp12_dump_predictions.py` — 8 konfiguratsiya (val+train) uchun XOM bashoratlar
  (y_true, yolo_vec, bool_vec, conf) `.npz` ga saqlanadi → metrikani YOLO'siz qayta hisoblash mumkin.
- `scripts/metrics_lib.py` — aniqlik, muvozanatli aniqlik (= makro sezgirlik), o'ziga xoslik,
  precision, F1, ROC-AUC (OvR makro/vaznli), MCC, Cohen κ + bootstrap CI va juftlashgan Δ testi.
- `scripts/exp13_metrics.py` — **α* endi FAQAT train'da tanlanadi**, val — yakuniy baholash;
  har metrika 95% CI (1000× bootstrap), Δ uchun p-qiymat.
- `scripts/exp14_nsweep_ci.py` — n′ sweep; fold-std o'rniga **pooled CV + bootstrap CI**
  (LOO fold'lari 1 namunali → fold aniqligi 0/1, std ≈0,37 sun'iy).
- `scripts/maqola_figures.py` — 5 ta grafik: n′ CI tasmali, α (train tanlov / val baholash),
  makro ROC, sinf kesimida sezgirlik, chalkashlik matritsasi.

**Natijalar o'zgardi (halol protokolda):**
- YOLO11l: aniqlik 0,800 → 0,810 (p = 0,868, AHAMIYATSIZ) — avvalgi "0,867" α ni val'da
  tanlashdan kelib chiqqan siljish edi. Ammo makro sezgirlik 0,575 → 0,709 (p = 0,032) va
  makro AUC 0,801 → 0,892.
- YOLO11s: hamma mezon sezilarli — aniqlik 0,737 → 0,853 (p < 0,001), AUC 0,729 → 0,852,
  κ 0,616 → 0,773.
- YOLO11l-v2: faqat AUC sezilarli (0,759 → 0,793).
- boolfs yolg'iz (GT ROI): aniqlik 0,628, AUC 0,889 → tartiblashda kuchli, qarorda zaif.
- Yutuq kam uchraydigan sinflarda: kalsifikatsiya 0,84 → 0,97; assimetriya 0,25 → 0,75;
  limfa tuguni 0,96 → 0,80 (almashuv).

**Maqolaning yangi markaziy da'vosi:** nomutanosib bazada aniqlik yolg'iz mezon sifatida
yaroqsiz; ansambl foydasi sezgirlik va AUC da. Sarlavha ham shunga moslandi.
Maqola 3 tilda qayta qurildi (13 OMML tenglama, 6 jadval, 5 rasm, ~2400-2850 so'z).
Dissertatsiya "II bob (davomi)" ham to'liq yangilandi (2.5-2.10-jadval, 2.5-2.9-rasm).

### 9.5. 🔧 Dissertatsiyadagi 80 ta xom LaTeX bo'lagi tuzatildi
**Muammo (9.3 da qayd etilgan edi):** matn ichida `$\mathrm{softplus}$`, `$f_{deep}$`,
`$F_v^{(s)} \in \mathbb{R}^{C_s \times H_s \times W_s}$` kabi bo'laklar xom LaTeX ko'rinishida
ko'rinib turardi — `para()` satr-ichi matematikani render qilmasdi.

**Yechim:** `scripts/omml_inline.py` — satr-ichi LaTeX → Word native OMML konvertori
(yunon harflari, _ va ^ indekslar, {guruh}, \text/\mathrm/\texttt/\mathbf, \mathbb{R}→ℝ,
\bar{x}→x̄, \times \dots \in \leq \geq, \{ \} qavslar; harf kursiv, son/operator tik).
`para()`, `lead()`, `bullets()` endi `emit_rich()` orqali ishlaydi (`**qalin**` ham saqlanadi).

**Natija:** xom `$...$` bo'laklar 80 → **0**; OMML tenglamalar 13 → **93** (13 display + 80 inline).
Matnda birorta teskari chiziq qolmadi. Tekshiruv: pandoc docx→latex to'g'ri o'qidi
(`F_{v}^{(s)} \in \mathbb{R}^{...}`, `y \leq k`, `(C_1,C_2,C_3)=(256,512,512)`).
Zaxira: `backups/MAMOGRAF_PhD_dissertatsiya_BEFORE_inline_math_20260710.docx`.

---

## Sessiya 10 — Katta datasetda boolfs + ikkita yangi maqola (2026-07-10)

### Vazifa
`d_ai_8class_1280` datasetida (foydalanuvchi `d_aa_8clas_1280` deb yozgan, real nom boshqacha)
Xamdamov usulini sinash va ansambl mavzusida **2 ta maqola × 3 til** yozish.

### Eksperimentlar (`/home/ai/mamograf_yangilash_21-iyun/`)
| Skript | Nima qiladi |
|---|---|
| `gpu_detect.py` | GPU'da (10.10.0.72) YOLO inferens; faqat xom detektsiyalar npz'ga (GPU'da skimage yo'q) |
| `exp20_boolfs_big.py` | boolfs fit; belgi keshi; n′ sweep + pooled CV + bootstrap CI |
| `exp21_match_big.py` | IoU≥0.3 greedy moslashtirish; har ROI uchun boolfs bahosi; `leaked` bayrog'i |
| `exp22_metrics_big.py` | α* train'da; leakage'siz val'da to'liq metrika + juftlashgan Δ + p |
| `exp23_stability_multi.py` | Kuncheva + Jaccard + o'rtacha o'rin, n′∈[3..36], IKKALA bazada |
| `figures_big.py` | 9 rasm × 3 til → `doc_assets_big/{uz,ru,en}/` |

**Dataset:** 4573 train / 798 val rasm → 13 968 / 2 359 GT ROI. Sinflar nomutanosib
(limfa tuguni 9483 … arxitektura buzilishi 13).

### Asosiy natijalar
- **boolfs (katta baza):** n′* = 36, val acc 0,596, bacc 0,638 [0,606; 0,762], makro AUC 0,947, MCC 0,490.
- **Barqarorlik ikki qatlamli** (1-maqolaning ilmiy hissasi):
  - baza ICHIDA yuqori: Kuncheva ≥ 0,830 barcha n′ da (katta baza), n′=5 da 1,000;
  - bazalar ORASIDA reyting boshi ko'chadi: Spirmen ρ = 0,937, ammo **top-3 kelishuvi 0,333**.
    Kichik bazada 1-o'rin `glcm_d1_correlation`, kattada `grad_sobel_std` (1,0 ± 0,0).
  - Jaccard n′=36 da 0,995 — tuzatilmagan o'lchov aldaydi (36/38 tanlansa har qanday
    ikki to'plam ustma-ust tushadi). **Faqat Kuncheva'ga tayanish kerak.**
- **MA'LUMOT SIZISHI topildi:** yangi val'ning 24 ta rasmi eski (445) bazaning train'ida.
  `yolo11s_8class` va `trained_8class_yolo11l` ularni ko'rgan. Sizgan detektsiyalar: 66 / 70 / 67.
  Barcha detektorlar bir xil **tozalangan** to'plamda baholandi.
- **Ansambl (toza detektor `trained_8class_ai_v2_ep50`, α*=0,55, n=2088):**
  | | YOLO | Ansambl | Δ | p |
  |---|---|---|---|---|
  | Aniqlik | 0,923 | 0,915 | −0,8 f.p. | 0,074 (ahamiyatsiz) |
  | Muvozanatli aniqlik | 0,640 | **0,692** | +5,2 f.p. | **0,036** |
  | Makro ROC-AUC | 0,897 | **0,976** | +7,9 f.p. | **<0,001** |
  - Foyda kam ta'minlangan sinflarda: BIRADS 1–2 sezgirlik 0,667→0,833; assimetriya 0,429→0,571;
    kalsifikatsiya 0,954→0,995. Limfa tuguni 0,932→0,910 (almashuv).
- **Sizishga uchragan detektorlarda ansambl aniqlikni AHAMIYATLI pasaytiradi** (p<0,001).
  Sizish `α*` ni ham buzadi: 0,30 / 0,35 (sizgan) vs 0,55 (toza). «Ansambl har doim foyda beradi»
  degan qarash rad etildi.

### Maqolalar (6 .docx, `/home/ai/mamograf_yangilash_21-iyun/`)
1. `MAMOGRAF_Maqola_2026_M1_Barqarorlik_{UZ,RU,EN}.docx` — nazariy-metodologik
   (belgi tanlash barqarorligi, ko'lam effekti). 15 raqamli tenglama, 5 jadval, 4 rasm.
2. `MAMOGRAF_Maqola_2026_M2_Ansambl_{UZ,RU,EN}.docx` — amaliy
   (gibrid ansambl, sizish nazorati, klinik talqin). 18 raqamli tenglama, 6 jadval, 5 rasm.

**Barcha formulalar Word-native OMML (MathType-mos), rasm emas.** Har bir .docx'da
124–157 ta `m:oMath` tugun; xom LaTeX qoldiq = 0; OMML sxema tekshiruvi 1032 tugunda 0 xato.

### Yangi modullar
- `scripts/omml.py` — `rad()`, `absv()` qo'shildi
- `scripts/maqola_formulalar_ext.py` — Kuncheva, Jaccard, o'rtacha o'rin, kelishuv, α*,
  BAcc, Spec, MCC, κ, AUC-OvR, bootstrap CI, juftlashgan Δ, IoU, leakage ta'rifi
- `scripts/maqola_kit.py` — umumiy .docx qurish (sarlavha/jadval/rasm ham inline OMML qabul qiladi)
- `scripts/m1_body_i18n.py`, `scripts/m2_body_i18n.py` — RU/EN professional tarjima

### Tuzoqlar
- `python-docx` **konteynerda yo'q**; host'da bor: `PYTHONPATH=/home/ai/.local/lib/python3.12/site-packages`.
  Yangi image qurib bo'lmaydi (pip SSL sertifikat xatosi).
- `numpy`/`matplotlib` esa faqat konteynerda → rasmlar `mamograf-prod-app` ichida, .docx host'da quriladi.
- OMML'da `sub(run(""), ...)` va bo'sh `nary` tanasi Word'da **bo'sh quti** bo'lib ko'rinadi —
  tekshirish uchun `m:e` bo'shligini sanash kerak.

### Sessiya 10-a — maqolalardagi tekshirilmagan da'volarni yopish (avtonom tik)

Yozilgan matnda **real hisob bilan qoplanmagan uchta da'vo** topildi va yopildi.

1. **`P` mezoni noto'g'ri ta'riflangan edi.** Men uni «to'g'ri sinf bilan eng yaqin raqib
   orasidagi masofa zaxirasi» deb yozgan edim. `boolfs/classifier.py:cv_P` ga qarasak,
   `P = (1/N) Σ I[class(xᵢ)=yᵢ]` — ya'ni **oddiy aniqlikning aynan o'zi**. Matn tuzatildi;
   real qiymatlar: boolfs 0,603 / YOLO 0,923 / ansambl 0,915. Bu maqolaning tezisini
   kuchaytiradi (P bo'yicha ansambl «yomonroq», holbuki bacc ahamiyatli oshgan).
2. **Chalkashlik matritsasi noto'g'ri o'qilgan edi.** «Asosiy chalkashlik o'sma↔limfa tuguni»
   deb yozilgandi. Haqiqiy eng katta katak: limfa tuguni → BIRADS 1–2 = **62** (keyin →o'sma 42,
   →kalsifikatsiya 27). Aynan 62 yolg'on musbat BIRADS 1–2 precision'ini 0,074 ga tushiradi.
3. **«IoU sezuvchanlik tekshiruvi o'tkazildi» — o'tkazilmagan edi.** Endi haqiqatan o'tkazildi:
   `scripts/exp24_iou_sensitivity.py` butun oqimni (moslashtirish → α* train'da → tozalangan
   val'da baholash) IoU ∈ {0,3; 0,5; 0,7} × 3 detektor uchun qaytadan bajardi.
   IoU=0,3 qiymatlari asosiy tahlil bilan aynan mos tushdi (mustaqil implementatsiya nazorati).

**IoU sezuvchanligining natijasi da'voni RAD ETDI va maqolani yaxshiladi:**

| Detektor | IoU | Δaniqlik | Δmuv.aniqlik | ΔAUC |
|---|---|---|---|---|
| YOLO11l-v2 (toza) | 0,3 | −0,8 (p=,074) | **+5,2 (p=,036)** | **+7,9 (p<,001)** |
| YOLO11l-v2 (toza) | 0,5 | −0,9 (p=,072) | **+5,4 (p=,042)** | **+7,6 (p<,001)** |
| YOLO11l-v2 (toza) | 0,7 | −2,6 (p<,001) | −0,8 (p=,648) | **+11,0 (p<,001)** |
| YOLO11l | 0,7 | −0,8 (p=,184) | +9,1 (p=,014) | +18,0 |
| YOLO11s | 0,7 | −3,6 (p<,001) | +25,9 (p<,001) | +9,3 |

- **ROC-AUC foydasi 9/9 holatda ijobiy va ahamiyatli** (+6,9 … +18,6 f.p.) — chegaradan
  mustaqil yagona xulosa.
- **Muvozanatli aniqlikdagi foyda ROI qiyinligiga bog'liq**: toza detektorda IoU=0,7 da
  yo'qoladi (mos ROI 2088→1828, faqat oson/aniq ramkalar qoladi, yakka detektorning o'z bacc'i
  0,640→0,693 ko'tariladi). Sizgan detektorlarda esa aksincha — chegara qat'iylashgani sari
  ansambl foydasi o'sadi.
- Xulosa: **ansamblning asosiy qiymati tartiblash sifatida (AUC), aniq qaror qoidasida emas.**

M2 maqolasiga **4.6-bo'lim + 7-jadval** qo'shildi (uch tilda), `d4` cheklovlar bandi va
xulosaning 6-bandi qayta yozildi. Yakuniy holat: M2 — 7 jadval, 5 rasm, ~3150–3750 so'z,
159–161 OMML tugun. Oltala hujjatda xom LaTeX 0, OMML sxema xatosi 0, bo'sh tenglama qutisi 0.
