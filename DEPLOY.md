# Production Deployment

Docker Compose + Caddy (avtomatik HTTPS) + uchta volume (uploads, annotations,
models, DB).

---

## 1. Talablar

- Linux server (Ubuntu 22.04+ tavsiyada) yoki Windows + WSL2 + Docker Desktop
- Docker Engine 24+ va docker compose plugin
- Domain — `mammo.example.uz` kabi (server IP'siga A-record sozlangan)
- 80 va 443 portlar ochiq (Let's Encrypt cert avtomatik so'raydi)
- ≥ 4 GB RAM, ≥ 20 GB disk (DICOM yuklash uchun ko'proq)
- (ixtiyoriy) NVIDIA GPU + nvidia-container-toolkit — bu holda
  [GPU.md](GPU.md)'dagi torchni `Dockerfile`'ga moslang

---

## 2. Yo'lga tushirish

```bash
git clone <repo> /opt/mamograf
cd /opt/mamograf

# Domain va dicom storage path'ni belgilang
cat > .env <<EOF
DOMAIN=mammo.example.uz
JWT_SECRET=$(openssl rand -base64 48)
LOCAL_DICOM_HOST_PATH=/srv/dicom_data
# Avtomatik DICOM anonimlashtirish (PHI tag'lari upload paytida tozalanadi).
# Default 1. PHI saqlangan asl fayl bilan ishlash kerak bo'lsa — 0 ga o'rnating.
AUTO_DEIDENTIFY=1
EOF

# Docker compose ishga tushirish
docker compose up -d --build

# Birinchi admin yarating
docker compose exec app python -m app.manage_users create admin --role admin
```

`https://mammo.example.uz` ochiladi (Caddy 30-60 soniyada Let's Encrypt
sertifikatini oladi).

---

## 3. Ma'lumotlar volume'lari

| Volume | Joylashuv | Ichida |
|---|---|---|
| `app_uploads` | `/app/app/uploads` | UI orqali yuklangan DICOM'lar |
| `app_annotations` | `/app/app/annotations` | per-DICOM JSON sidecar'lar |
| `app_models` | `/app/app/models` | YOLO `.pt` modellari |
| `app_db` | `/app/app/` | `db.sqlite3`, `.jwt_secret` |
| `caddy_data` | `/data` | TLS sertifikatlar, access log |

`LOCAL_DICOM_HOST_PATH` host'dagi mavjud DICOM kolleksiyasini read-only
montaj qiladi (yangi yuklash kerak emas).

---

## 4. Backup

Eng muhim joylar:

```bash
docker run --rm -v mamograf_app_db:/data -v $PWD:/backup alpine \
  tar czf /backup/db_$(date +%F).tar.gz -C /data .

docker run --rm -v mamograf_app_annotations:/data -v $PWD:/backup alpine \
  tar czf /backup/annotations_$(date +%F).tar.gz -C /data .
```

`models/` ni odatda backup qilmaymiz — qayta yuklab olinadi.

`uploads/` muhimligi loyihaga bog'liq.

---

## 5. Yangilash

```bash
cd /opt/mamograf
git pull
docker compose up -d --build
```

Schema avto-migratsiya: `app/db.py`'dagi `CREATE TABLE IF NOT EXISTS`'lar
yangi jadvallarni yaratadi. Mavjud jadvallarga `ALTER TABLE` kerak bo'lsa
qo'lda migratsiya yozish kerak.

---

## 6. Foydalanuvchilarni boshqarish

UI orqali (admin login) yoki CLI:

```bash
docker compose exec app python -m app.manage_users list
docker compose exec app python -m app.manage_users create alice --role annotator
docker compose exec app python -m app.manage_users passwd alice
```

---

## 7. xlsx import

```bash
docker cp MamologiyaInfo_.xlsx mamograf-app:/tmp/
docker compose exec app python -m app.import_xlsx /tmp/MamologiyaInfo_.xlsx --reset
```

---

## 8. Worklist import

```bash
docker cp Worklist.csv mamograf-app:/tmp/
docker compose exec app python -m app.import_worklist /tmp/Worklist.csv --reset
```

---

## 9. Logs

```bash
docker compose logs -f app
docker compose logs -f caddy
tail -f $(docker volume inspect -f '{{.Mountpoint}}' mamograf_caddy_data)/access.log
```

---

## 10. Xavfsizlik checklist

- [ ] `JWT_SECRET` — `openssl rand -base64 48` orqali yaratilgan
- [ ] Default `admin/admin123` parolni o'zgartirilgan (👥 panel orqali)
- [ ] `LOCAL_DICOM_HOST_PATH` read-only (`:ro` flag)
- [ ] Server firewall faqat 80/443 ochiq (SSH 22 cheklangan)
- [ ] Backup avtomatlashtirilgan (cron yoki systemd timer)
- [ ] Docker images muntazam yangilanadi (`docker compose pull` haftalik)
- [ ] HTTPS sertifikat Caddy tomonidan avtomatik yangilanmoqda (logs orqali tekshiring)

---

## 11. Troubleshooting

| Muammo | Yechim |
|---|---|
| `cert obtain failed` | DNS A-record tekshiring; 80 portga tashqaridan kirib bo'ladimi? |
| `502 Bad Gateway` | `docker compose logs app` — Python xato bormi? |
| WebSocket uzilib qoladi | `Caddyfile`'da `@ws` route tartibi yuqorida bo'lsin |
| DB locked | bir vaqtda 1 ta SQLite writer; restart `docker compose restart app` |
| Upload limiti kichik | Caddy `request_body { max_size 200MB }` directive qo'shing |

---

## 12. Single-node alternativa (Caddy'siz)

Faqat ichki tarmoqda foydalansangiz va HTTPS kerak bo'lmasa:

```yaml
services:
  app:
    build: .
    ports: ["8000:8000"]
    environment:
      - LOCAL_DICOM_ROOT=/data/dicom
    volumes:
      - ./uploads:/app/app/uploads
      - ./annotations:/app/app/annotations
      - ./models:/app/app/models
      - ./db_root:/app/app
      - /srv/dicom_data:/data/dicom:ro
```

`http://server-ip:8000` orqali kiring.
