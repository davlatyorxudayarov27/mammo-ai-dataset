# MAMOGRAF — AI-yordamli mammografiya tahlili tizimi

Mammografiya rasmlarini avtomatik tahlil qilish, lezyonlarni topish va klinik
hisobotlarni klassifikatsiya qilish uchun mo'ljallangan tadqiqot va prototip
loyihasi. Web-ilova (FastAPI) + tadqiqot moduli + ilmiy maqolalar.

> ⚠️ **Eslatma:** bu repozitoriya **faqat manba kodi va ilmiy hujjatlar**ni
> o'z ichiga oladi. Hech qanday bemor rasmi (DICOM), bemor ma'lumotlari yoki
> trening og'irliklari (model weights) bu yerda saqlanmaydi —
> [`.gitignore`](.gitignore) ga qarang.

## Komponentlar

- **Web-ilova** (`app/`) — FastAPI backend + statik UI. DICOM viewer,
  annotation, AI taklif, hisobot, PACS integratsiyasi, foydalanuvchi
  boshqaruvi (JWT + TOTP).
- **Modellar — arxitektura** (`app/models_arch/`):
  - **BCA-YOLO** — Bilateral Cross-Attention YOLO mammografiya lezyon
    detektsiyasi uchun (chap/o'ng asimmetriya hisobga olinadi)
  - **TILLNet-Det** — matn shartlangan (radiologiya hisobotidan) lezyon
    lokalizatsiyasi tarmoq (FiLM + FCOS)
  - **XS-Classifier** — Cross-Script TF-IDF + Logistic Regression:
    o'zbek (kirill+lotin) va rus tilidagi hisobotlarni rak/rak emas
    sifatida klassifikatsiya qilish
- **Trening / tadqiqot** (`app/research/`) — pipeline, dataset
  tayyorlash, statistik testlar, soxta-yorliqlash (pseudo-labels), train
  skriptlari.
- **Ilmiy maqolalar** (`paper/`) — har bir model va tizim bo'yicha 5 ta
  maqola (MD + PDF).
- **Dissertatsiya** (`dissertation/`) — to'liq dissertatsiya manbalari.

## O'rnatish va ishga tushirish

```bash
python -m venv .venv
.venv\Scripts\activate     # Windows
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
# yoki:
run.bat
```

Brauzerda: `http://127.0.0.1:8000`

Docker:
```bash
docker compose up --build
```

Foydalanuvchi va tadqiqotchi qo'llanmalari uchun loyiha root'idagi MD
fayllar:
- `FOYDALANUVCHI_QOLLANMA.md`
- `TADQIQOTCHI_QOLLANMA.md`

## Modellar — og'irliklarni qayerdan olish

Trening og'irliklari (`.pt`) bu repo'ga kiritilmagan. Tizim ulardan
keyin foydalanish uchun:

1. `app/models/digitaleye_yolo11_l.pt` — sizning trening YOLOv11-L
2. `app/models/yolov8n.pt` — Ultralytics rasmiy YOLOv8-Nano

Bularning ikkalasi ham `app/models/` papkasiga qo'lda joylashtiriladi.
Distribution kanali (HuggingFace Hub / Git LFS) keyin qo'shiladi.

## Litsenziya va foydalanish

Bu loyiha — tadqiqot maqsadida. Klinik foydalanish uchun rasmiy sertifikat
va validatsiya talab qilinadi. Maqolalardagi natijalar maxsus dataset
va trening shartlarida olingan; o'z datasetingizda farq qilishi mumkin.

## Etika

Loyiha bemor ma'lumotlarini hech qachon klinika tarmog'idan tashqariga
chiqarmaslik tamoyili bilan qurilgan. Maqolalarda yozilgan:
*"All multilingual text is processed locally; no data leaves the
institution; no cloud LLM is called."*
