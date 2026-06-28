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
