# MAMOGRAF DICOM Viewer — Foydalanuvchi qo'llanmasi

To'liq mammografiya annotatsiya platformasi: DICOM ko'rish, annotatsiya
qilish, AI tahlil, hisobot, audit, PACS integratsiyasi, ko'p foydalanuvchili
ish jarayoni.

---

## 1. Boshlash

### 1.1 Birinchi marta ishga tushirish

```cmd
run.bat
```

Birinchi safar `.venv/` virtualenv yaratiladi va paketlar o'rnatiladi (~5
daqiqa). Keyingi safar darhol server ishga tushadi.

### 1.2 Birinchi admin yarating

```cmd
.venv\Scripts\python.exe -m app.manage_users create admin --role admin
```

Parol so'raladi.

### 1.3 Brauzerda oching

```
http://127.0.0.1:8000
```

Login modal ko'rinadi → admin uchun yaratgan parolingizni kiriting.

### 1.4 3 ta rol

| Rol | Vakolatlar |
|---|---|
| **admin** | Hammasini bajaradi: foydalanuvchilarni boshqarish, sozlamalar, audit eksport, status'larni majburlash |
| **reviewer** | Annotatsiyalarni approve/reject qiladi, statistikani ko'radi, PACS sozlamalari |
| **annotator** | O'z annotatsiyalarini chizadi, submit qiladi, AI takliflarini qabul qiladi |

---

## 2. Asosiy interfeys

```
┌──────────────────────── HEADER ────────────────────────┐
│ ☰  MAMOGRAF   tayyor   🔔  📜📊🏥👥🔒  user (role)  ⎋  │
├─────────┬───────────────────────────┬──────────────────┤
│         │       TOOLBAR             │                  │
│ CHAP    │                           │  O'NG PANEL      │
│ PANEL   │                           │                  │
│ (4 tab) │     DICOM RASMI           │  (3 tab)         │
│         │                           │                  │
│         │                           │                  │
│         ├───────────────────────────┤                  │
│         │       W/L SLAYDERLAR      │                  │
└─────────┴───────────────────────────┴──────────────────┘
```

### 2.1 Header (yuqorigi panel)

| Element | Vazifa |
|---|---|
| **☰** (chap) | Telefonda — chap panelni ochadi/yopadi |
| **MAMOGRAF** | Loyiha nomi |
| **tayyor** | Status xabarlari (yuklash, AI ishlamoqda, xatolar) |
| **📋** (o'ng) | Telefonda — o'ng panelni ochadi/yopadi |
| **🔔** | Bildirishnomalar (qizil dot — o'qilmagan) |
| **📜** | Audit timeline (admin/reviewer) |
| **📊** | Statistika (admin/reviewer) |
| **🏥** | PACS serverlar (admin/reviewer) |
| **🗂** | Annotatsiyalangan DICOM'lar overview |
| **👥** | Foydalanuvchilarni boshqarish (admin) |
| **🔒/🔓** | 2FA sozlash (yopiq/ochiq) |
| **user (role)** | Joriy foydalanuvchi |
| **⎋** | Chiqish |

### 2.2 Chap panel — 4 ta tab

| Tab | Mazmuni |
|---|---|
| **Yuklangan** | Web orqali yuklangan DICOM'lar (drag & drop yoki tugmadan) |
| **Lokal** | Server diskidagi DICOM'lar (`LOCAL_DICOM_ROOT` env) |
| **🔗 Bog'langan** | xlsx bemorga bog'langan DICOM'lar (qidiruv bilan) |
| **📋 Mening ishim** | Status filter bilan annotatsiyalarning ro'yxati |
| **📥 Worklist** | DICOM ish navbati (CSV import yoki MWL'dan) |

Har bir DICOM yonida:
- 🟢 yashil pill — annotatsiyalar soni
- ☑ checkbox — multi-tanlash (AI batch uchun)

### 2.3 Toolbar (markaz, yuqori)

```
[Fit] [1:1] [Invert] [W/L reset] | [Select] [BBox] [Poly] [label v] [BI-RADS v]
| [AI model v] [🤖 AI tahlil] [≥25%] [✓ Qabul] [✕] | Frame [—] | 100%
| saqlandi | [⤓ Eksport] [🛡 De-ID] [📄 SR] [🖼 SEG] [📤 PACS] [📑 Tpl] [💾 Tpl]
```

| Tugma | Vazifa |
|---|---|
| **Fit** | Rasmni ekranga moslash (Hotkey: F) |
| **1:1** | 100% zoom (Hotkey: 0) |
| **Invert** | Ranglarni o'zgartirish (Hotkey: I) |
| **W/L reset** | Window/Level standart qiymatga qaytaradi |
| **▶ Select** | Tanlash rejimi (Hotkey: V) |
| **▭ BBox** | To'rtburchak chizish rejimi (Hotkey: B) |
| **⬢ Poly** | Polygon chizish rejimi (Hotkey: P) |
| **label** | Yangi annotatsiya uchun label tanlash (mass / calcification / ...) |
| **BI-RADS** | BI-RADS klassifikatsiyasi (1, 2, 3, 4A, 4B, 4C, 5, 6) |
| **AI model** | YOLO modelini tanlash |
| **🤖 AI tahlil** | Joriy DICOM'da AI ni yugurtirish |
| **≥25%** | AI confidence threshold (slayder, 10-95%) |
| **✓ Qabul** | Barcha ko'rinadigan AI takliflarini annotatsiyaga aylantirish |
| **✕** | AI takliflarini tozalash |
| **Frame** | Multi-frame DICOM'da frame'ni tanlash |
| **100%** | Joriy zoom darajasi |
| **saqlandi** | Auto-save indikatori |
| **⤓ Eksport** | Barcha annotatsiyalarni COCO JSON sifatida tushirish |
| **🛡 De-ID** | DICOM'ni anonimlashtirib yuklab olish |
| **📄 SR** | Annotatsiyalarni DICOM-SR (matn) sifatida |
| **🖼 SEG** | Annotatsiyalarni DICOM-SEG (pixel mask) sifatida |
| **📤 PACS** | DICOM'ni PACS serverga yuborish |
| **📑 Tpl** | Saqlangan template'larni qo'llash |
| **💾 Tpl** | Joriy annotatsiyalarni template sifatida saqlash |

### 2.4 O'ng panel — 3 ta tab

| Tab | Mazmuni |
|---|---|
| **Metadata** | DICOM tags (PatientName, ID, DOB, manufacturer, va h.k.) |
| **Annotatsiyalar [N]** | Annotatsiyalar ro'yxati + status + transition tugmalar |
| **Hisobot [N]** | xlsx'dan kelgan klinik hisobot (mos kelgan bemor) |

### 2.5 Pastki panel (Window/Level)

| Slayder | Vazifa |
|---|---|
| **WC** | Window Center (rasmning markaz qoramligi) |
| **WW** | Window Width (kontrast diapazoni) |

Tipik mammografiya uchun:
- WC ~30000, WW ~50000 (umumiy ko'rinish)
- WC ~40000, WW ~10000 (yumshoq to'qima detali)

---

## 3. Klaviatura yorliqlari

| Tugma | Vazifa |
|---|---|
| **V** | Tanlash rejimi |
| **B** | BBox chizish |
| **P** | Polygon chizish |
| **F** | Fit (ekranga moslash) |
| **0** | 1:1 zoom |
| **+ / =** | Zoom in |
| **- / _** | Zoom out |
| **I** | Invert (ranglarni teskari) |
| **J / ↓** | Keyingi annotatsiyaga o'tish |
| **K / ↑** | Oldingi annotatsiyaga |
| **← / →** | Frame oldingi/keyingi (multi-frame) |
| **S** | Submit (own draft) |
| **Y** | Approve (reviewer) |
| **N** | Reject + sabab (reviewer) |
| **R** | Recall (status'ni draft'ga qaytarish) |
| **Delete** | Tanlangan annotatsiyani o'chirish |
| **Enter** (poly) | Polygon yopish (≥3 nuqta kerak) |
| **Esc** | Tanlovni bekor / polygon chizishni bekor |
| **Ctrl + C** | Annotatsiya nusxasini olish |
| **Ctrl + V** | Annotatsiya qo'yish (boshqa DICOM'da ham) |
| **?** | Klaviatura yordami (alert oynasi) |

---

## 4. DICOM ochish va ko'rish

### 4.1 Yuklash usullari

**A) Drag & drop**: DICOM faylini chap panel'ning yuqori qismiga torting.

**B) "Fayl tanlash"**: bir nechta `.dcm` faylni tanlash.

**C) "Papka tanlash"**: butun papkani yuklash (rekursiv).

**D) Lokal**: server diskidagi `LOCAL_DICOM_ROOT` ostidagi fayllar (yuklamasdan).

### 4.2 Ko'rishni boshqarish

| Harakat | Qanday |
|---|---|
| **Pan** | Sichqoncha bilan rasmni sudrang (Select rejimida) |
| **Zoom** | Mouse wheel yoki **+ / -** klaviatura |
| **Pinch zoom** | Telefon/planshet — ikki barmoq |
| **W/L** | Pastki slayderlar yoki raqamlarga klik |
| **Frame** | Multi-frame uchun `←/→` yoki Frame slayder |

---

## 5. Annotatsiya jarayoni

### 5.1 BBox (to'rtburchak) chizish

1. Toolbar'dan label va BI-RADS tanlang (mas: `mass`, `4B`)
2. **B** bosing (yoki `▭ BBox`) → kursor crosshair
3. Rasmda sichqoncha bilan to'rtburchak sudrab chizing
4. Auto-save (1-2 soniya kechikishi bilan)

### 5.2 Polygon chizish

1. **P** bosing (`⬢ Poly`)
2. Rasmda **bosib** har bir nuqta qo'shing
3. **Dblclick** yoki **Enter** — polygon yopiladi
4. **Esc** — bekor qilish

### 5.3 Annotatsiyani tahrirlash

1. **V** bosing (`▶ Select`)
2. Annotatsiyani tanlang (sichqoncha bilan bosish):
   - **BBox**: 8 ta tutqich (4 burchak + 4 chet) — sudrash bilan o'lchamini o'zgartiring
   - **Polygon**: oq nuqtalar (vertex) — sudrash bilan ko'chirish; **right-click** — vertex o'chirish; yashil nuqta (chet o'rtasi) — yangi vertex qo'shish
3. Ann'ni o'rtasidan sudrab to'liq ko'chirish
4. **Delete** — o'chirish

### 5.4 Status flow (reviewer workflow)

```
   ┌─────────┐   submit   ┌───────────┐   approve   ┌──────────┐
   │  draft  │ ─────────> │ submitted │ ──────────> │ approved │
   └────┬────┘    (S)     └─────┬─────┘     (Y)     └─────┬────┘
        ▲ recall (R)            │ recall (R)              │
        └───────────────────────┤                  reopen │
                                │                         │
                                │ reject (N)              │
                                ▼ + sabab                 │
                          ┌───────────┐                   │
                          │ rejected  │                   │
                          └─────┬─────┘                   │
                                │ reopen                  │
                                └─────────────────────────┘
```

| Rol | draft → submitted | submitted → approved/rejected | own edit | others' edit |
|---|:---:|:---:|:---:|:---:|
| annotator | own only | ✗ | ✓ (draft) | ✗ |
| reviewer | ✓ | ✓ | ✓ | ✓ |
| admin | ✓ | ✓ | ✓ | ✓ |

Approved annotatsiya — annotator uchun read-only. Reviewer/admin reopen orqali draft'ga qaytaradi.

### 5.5 O'ng panelda annotatsiyalar

Har bir annotatsiya:
- **Label dropdown** — rangli ramka bilan
- **BI-RADS dropdown**
- **Status pill** — kulrang (draft) / sariq (submitted) / yashil (approved) / qizil (rejected)
- **Audit**: kim yaratdi · oxirgi tahrirlash · reviewer
- **Status tugmalari**: ▲ Submit / ✓ Approve / ✗ Reject / 🔓 Reopen / ▼ Recall
- **📜 Tarix** — har bir o'zgarish jurnali
- **✕** — o'chirish

---

## 6. Hisobot tab (xlsx integratsiyasi)

DICOM ochilganda — `Hisobot` tab avtomatik:

1. **PatientID + Name + DOB** orqali xlsx'dagi bemorga match qiladi
2. **Avtomatik ishonch ≥80%** bo'lsa — yozuvlarni darhol yuklaydi
3. **Bir nechta nomzod** bo'lsa — kart bilan tanlash uchun ko'rsatadi
4. **Topilmasa** — qo'lda qidirish maydoni

**Bog'lash (manual):** "🔗 Bog'lash" tugmasi — DICOM'ni shu bemorga doimiy bog'laydi. Keyingi safar avto-yuklanadi.

**Bog'langan banner**: yashil "🔗 Bog'langan · 85% · 2026-05-06". `🔓 Aloqani uzish` mavjud.

Yozuvlar accordion ko'rinishida (sana bo'yicha):
- Mammografiya hisoboti
- Shikoyatlari, Anamnesis morbi
- Klinik ko'rinish, Tashxis, Tavsiyalar
- va h.k. (12 ta klinik bo'lim)

---

## 7. AI tahlil

### 7.1 Bitta DICOM uchun

1. AI model dropdown'dan `.pt` faylni tanlang (masalan `digitaleye_yolo11_l.pt`)
2. **🤖 AI tahlil** bosing → 5-10 soniya kuting (CPU)
3. Sariq punktir bbox'lar paydo bo'ladi (`🤖 mass 87%`)
4. Slayder bilan threshold filtrlang (≥25% → ≥50% → ...)
5. Variantlar:
   - Bitta taklifni bosing → confirm bilan annotatsiyaga aylanadi
   - **✓ Hammasini qabul** — barcha ko'rinadigan takliflarni qabul qilish
   - **✕** — barchasini tozalash

### 7.2 Batch (bir nechta DICOM)

1. Chap panelda DICOM'lar yonida ☑ checkbox'larni belgilang
2. Yuqorida **🤖 AI batch** tugmasi yonadi
3. Bosing → confirm → max 50 DICOM'da AI yuguradi
4. Natijalar **avtomatik draft annotatsiya** sifatida saqlanadi
5. Reviewer keyinchalik approve/reject qiladi

### 7.3 Modellar

`app/models/*.pt` papkasiga qo'ying. Tavsiya:
- **digitaleye_yolo11_l.pt** (49MB) — KETEM mammografiya datasetida o'qitilgan
- Yoki o'zingiz tayyorlagan YOLO modeli (Ultralytics-compatible)

GPU bilan ishlatish uchun → [GPU.md](GPU.md) (10-20x tezroq).

---

## 8. Templates (qayta ishlatiladigan annotatsiyalar)

### 8.1 Saqlash

1. DICOM'da bir nechta tipik annotatsiya chizing (masalan, "BIRADS-4 standart joylar")
2. **💾 Tpl** bosing
3. Nom + tavsif kiriting
4. "Hammaga ko'rinsinmi?" — Yes (shared) yoki No (private)

### 8.2 Qo'llash

1. Yangi DICOM'ni oching
2. **📑 Template** dropdown'dan tanlang
3. Annotatsiyalar joriy frame'ga qo'shiladi (`note += "[tpl: nom]"`)
4. Avtomatik saqlanadi

### 8.3 Clipboard (vaqtinchalik)

- **Ctrl+C** — tanlangan / joriy frame'dagi barcha annotatsiyalarni clipboard'ga
- **Ctrl+V** — boshqa DICOM'da ham qo'yish
- localStorage'da saqlanadi (tab/brauzer reload — saqlanadi)

---

## 9. PACS integratsiyasi

### 9.1 Server qo'shish

1. **🏥 PACS** modal
2. Pastki formada: Nom + Host + Port + AET → "+ Qo'shish"
3. **🩺 Echo** — server bilan aloqa testi (C-ECHO)

### 9.2 Bemor qidirish (C-FIND)

1. Server tanlang
2. Patient ID / Name / Modality / Study Date kiriting
3. **🔍 Qidirish** → studies ro'yxati
4. Har bir natija yonida **→ Worklist** — worklist'ga qo'shish

### 9.3 DICOM yuborish (C-STORE)

DICOM ochiq bo'lganda:
1. Toolbar'dan **📤 PACS** tugmasi
2. Server tanlang (bir nechta bo'lsa)
3. Confirm → DICOM PACS'ga yuboriladi

### 9.4 DICOM olish (C-MOVE)

CLI orqali:
```cmd
.venv\Scripts\python.exe -m app.pacs fetch \
  --host 192.168.1.10 --port 4242 --aet ORTHANC \
  --study-uid 1.2.3.4 --dest ./fetched/
```

Yoki HTTP API: `POST /api/pacs/servers/{id}/fetch` body: `{"study_uid": "..."}`.

---

## 10. Eksport formatlari

| Format | Tugma | Mazmuni |
|---|---|---|
| **COCO JSON** | ⤓ Eksport | Barcha annotatsiyalar (bbox + segmentation), bemor demografiyasi, audit fields |
| **DICOM-SR** | 📄 SR | Standart Structured Report — matnli annotatsiyalar (PACS-friendly) |
| **DICOM-SEG** | 🖼 SEG | Pixel-mask DICOM (segmentation) |
| **De-ID DICOM** | 🛡 De-ID | Anonimlashtirilgan asl DICOM (PHI tozalangan) |

### 10.1 De-identification

DICOM ochilganda **🛡 De-ID** bossangiz:
1. PHI maydonlari ro'yxati (PatientName, ID, DOB, ReferringPhysician, va h.k.)
2. **⤓ Anonimlashtirilgan DICOM yuklab olish**
3. Tozalanadi: ism, ID → ANON; sana → 19000101; institution; physician
4. Saqlanadi: yil komponenti (StudyDate 20260408 → 20260101)
5. Pixel data o'zgarmaydi

---

## 11. Notifications (🔔)

Avto-tetiklayotgan hodisalar:

| Hodisa | Kim oladi |
|---|---|
| Annotator submit qiladi | Barcha reviewer + admin |
| Reviewer approves | Annotation egasi |
| Reviewer rejects + sabab | Annotation egasi |
| Worklist tayinlash | Tayinlangan user |

Bell tugmasini bossangiz dropdown ochiladi:
- O'qilmaganlari ko'k chiziq bilan ajratilgan
- Click → mark-read + tegishli DICOM ochiladi
- "Hammasini o'qildi qilish"

---

## 12. Admin paneli (👥)

### 12.1 Foydalanuvchilar

| Action | Vazifa |
|---|---|
| Role dropdown | admin/reviewer/annotator (live save) |
| Disable/Enable | Faollikni o'zgartirish |
| 🔑 Reset | Parolni o'zgartirish |
| 🗑 | O'chirish (faqat boshqa user'larni) |

### 12.2 Yangi user yaratish

Pastki forma: username + password + role + (display name + email opsional) → "+ Yaratish".

### 12.3 TOTP majburiy rollar

3 ta checkbox: admin / reviewer / annotator. Belgilangan rollar uchun keyingi login'da 2FA setup majburiy.

### 12.4 ⤓ Audit log CSV

Barcha `annotation_history` yozuvlarini CSV sifatida (UTF-8 BOM bilan, Excel'da to'g'ri ochiladi). Compliance/audit uchun.

---

## 13. Statistika (📊)

Admin/reviewer uchun:

- 8 ta umumiy ko'rsatkich (users, patients, annotations, AI-originated, va h.k.)
- Review davomiyligi: median, p90, mean (sekund)
- Bar chart'lar: status, top label'lar, top yaratuvchilar, worklist statuslar, audit action'lar
- Oxirgi 30 kun audit faolligi sparkline

---

## 14. Audit timeline (📜)

Admin/reviewer uchun:
- Sana bo'yicha guruhlangan barcha hodisalar
- Filter: username + action turi
- Status transition'larida `prev → new` + sabab

---

## 15. Annotated DICOMs overview (🗂)

Kart-ko'rinish:
- Bemor ismi + DOB + ID
- Annotatsiyalar soni + status pill'lar (draft/submitted/...)
- Label distribution
- Click → DICOM ochiladi

Filter: status + "faqat meniki".

---

## 16. 2FA (Two-Factor Authentication)

### 16.1 Yoqish

1. Header'da **🔓** (yoki **🔒**) tugmasi
2. QR kodni Google Authenticator / Authy / 1Password'da skanerlang
3. App'dan 6-raqamli kodni kiriting
4. **✓ Yoqish** — ishga tushadi

### 16.2 Login

Username + parol + (agar enrolled bo'lsa) **6-raqamli TOTP kod**.

### 16.3 O'chirish

🔒 modal → parol kiriting → "2FA ni o'chirish".

### 16.4 Majburiy enforcement

Admin **👥** modalda "TOTP majburiy rollar"'ni belgilasa, shu rolla kirgan userlar setup'gacha boshqa narsa qila olmaydi.

---

## 17. Worklist (📥)

Ish navbati — DICOM tartibida ko'rib chiqish kerak bo'lganlar.

### 17.1 Import

CSV orqali:
```cmd
.venv\Scripts\python.exe -m app.import_worklist worklist.csv --reset
```

DICOM MWL serverdan:
```cmd
pip install pynetdicom
.venv\Scripts\python.exe -m app.mwl_scu --host 192.168.1.10 --port 4242 \
  --aet ORTHANC --modality MG --date today
```

PACS query natijalaridan: `→ Worklist` tugmasi (PACS modal'dan).

### 17.2 Boshqarish

- **Filter**: status + "faqat meniki"
- **Right-click** (admin/reviewer) → assign / priority / status o'zgartirish
- **Click** → bemor overview modal

---

## 18. WebSocket — real-time hamkorlik

DICOM ochilganda:
- Boshqa user'lar real-time'da ko'rinadi (yashil **● user1, user2** pill toolbar'da)
- Boshqa user kursori — rangli doira + ism rasmda
- Annotatsiya qo'shilsa/o'zgarsa — barcha ko'ruvchilarda avto-yangilanadi

---

## 19. CLI komandalari to'plami

```cmd
:: Foydalanuvchilar
.venv\Scripts\python.exe -m app.manage_users list
.venv\Scripts\python.exe -m app.manage_users create alice --role annotator
.venv\Scripts\python.exe -m app.manage_users passwd alice
.venv\Scripts\python.exe -m app.manage_users rotate-secret

:: xlsx import
.venv\Scripts\python.exe -m app.import_xlsx --reset

:: Worklist import (CSV)
.venv\Scripts\python.exe -m app.import_worklist --reset

:: Worklist import (DICOM MWL)
.venv\Scripts\python.exe -m app.mwl_scu --host ... --port ... --aet ...

:: PACS
.venv\Scripts\python.exe -m app.pacs send --host ... file.dcm
.venv\Scripts\python.exe -m app.pacs query --host ... --patient-id 12345
.venv\Scripts\python.exe -m app.pacs fetch --host ... --study-uid 1.2.3 --dest ./out/

:: Backup
.venv\Scripts\python.exe -m app.backup list
.venv\Scripts\python.exe -m app.backup create [output.tar.gz]
.venv\Scripts\python.exe -m app.backup restore backup.tar.gz [--force]
```

---

## 20. Mobile (telefon/planshet)

Layout 768px'da o'zgaradi:
- Sidebar va meta-pane yashirinadi (toggle: ☰ va 📋)
- Pinch-to-zoom (ikki barmoq)
- Tugmalar 32px+ (touch-friendly)

---

## 21. Tipik ish jarayonlari

### Annotator (radiolog stajori)

1. Login
2. **📥 Worklist** → o'ziga tayinlangan ishlar
3. DICOM ochiladi → annotatsiyalar chizadi
4. **S** (Submit) bosadi
5. Reviewer reject qilsa **🔔** kelinadi → tuzatadi → qayta submit

### Reviewer (katta radiolog)

1. Login
2. **🔔** dan submit notification → DICOM ochadi
3. Annotatsiyani ko'rib chiqib **Y** (Approve) yoki **N** (Reject + sabab)
4. **🗂 Overview** dan keyingi DICOM tanlaydi
5. Statistikani **📊** dan ko'radi

### Admin

1. **👥** dan yangi user yaratadi
2. **🏥 PACS** sozlaydi
3. **📜 Audit timeline** dan jamoa faoliyatini kuzatadi
4. **⤓ Audit log CSV** — compliance hisobotlari uchun
5. **TOTP majburiy** rollar belgilaydi
6. Backup: `python -m app.backup create` haftalik

---

## 22. Tez-tez beriladigan savollar

**S: Brauzerda qora ekran ko'rinmoqda, login modal yo'q.**
J: `Ctrl+F5` bilan hard refresh qiling. Kesh muammosi bo'lishi mumkin.

**S: AI tahlil ishlamayapti.**
J: 1) `app/models/*.pt` faylini qo'ying. 2) `requirements.txt`'da `ultralytics` o'rnatilgan bo'lishi kerak.

**S: PACS ga ulanishda 503/502 xato.**
J: PACS server ishga tushganmi? `app.pacs --help` orqali testlang.

**S: DICOM-SEG eksport "FrameOfReferenceUID yo'q" deydi.**
J: Mammografiya'da bu normal. Avto-fallback bilan barcha label'lar bitta segmentga birlashtiriladi.

**S: 2FA QR kodini skanerlay olmadim.**
J: Secret string'ni qo'lda kiriting (Authenticator app'da "Manual entry").

**S: Worklist'ga qanday qo'shaman?**
J: CSV import yoki PACS C-FIND natijalaridan `→ Worklist` tugmasi.

**S: Server qaerga uploads va annotations saqlaydi?**
J: `app/uploads/` (DICOM), `app/annotations/` (JSON), `app/db.sqlite3` (DB).

**S: Sessiya qancha vaqt davom etadi?**
J: JWT token 12 soat amal qiladi. Keyin qayta kirish kerak.

**S: Production'ga qanday joylashtiraman?**
J: [DEPLOY.md](DEPLOY.md) — Docker Compose + Caddy bilan HTTPS.

---

## 23. Texnik ma'lumotlar

| | |
|---|---|
| Backend | FastAPI (Python 3.12) |
| DB | SQLite (`app/db.sqlite3`) |
| Frontend | Vanilla JS + SVG |
| Auth | JWT (HS256, 12h TTL) + bcrypt |
| 2FA | TOTP (RFC 6238, 6 raqam) |
| AI | YOLO via Ultralytics |
| WebSocket | FastAPI native, room-based |
| Eksport | COCO, DICOM-SR, DICOM-SEG (highdicom) |
| DICOM tarmoq | pynetdicom (C-STORE/FIND/MOVE/MWL) |
| Rate limit | slowapi (login 10/min, AI 20/min) |

---

## 24. Yordam

- **?** klaviatura → tezkor hotkey ro'yxati
- Loyiha hujjatlari:
  - [GPU.md](GPU.md) — CUDA setup
  - [DEPLOY.md](DEPLOY.md) — Docker production
- Server log: `uvicorn` chiqishida xatolar
- Brauzer xatolari: F12 → Console
