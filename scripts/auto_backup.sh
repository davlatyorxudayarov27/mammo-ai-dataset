#!/usr/bin/env bash
# AI Scan (mamograf) avtomatik zaxira.
#   Kunlik  : db.sqlite3 + annotatsiyalar + labels (~11 MB) — 14 kun saqlanadi
#   Yakshanba: yuqoridagilar + uploads (DICOM) — 8 nusxa saqlanadi
# Rasmiy app.backup CLI ishlatiladi (restore ham shu bilan). WAL checkpoint oldindan.
# Cron: har kuni 02:00.  Restore: pastdagi izohga qarang.

CONTAINER="mamograf-app"
BK_DIR="/home/ai/plan_project_new/backups/auto"
LOG="$BK_DIR/backup.log"
KEEP_LIGHT=14
KEEP_FULL=8
mkdir -p "$BK_DIR"

log(){ echo "[$(date '+%F %T')] $*" | tee -a "$LOG" >/dev/null; }

# Yakshanba (7) -> to'liq (uploads bilan), aks holda yengil
if [ "$(date +%u)" = "7" ]; then
  KIND="full"; EXTRA="--include-uploads"; KEEP="$KEEP_FULL"
else
  KIND="light"; EXTRA=""; KEEP="$KEEP_LIGHT"
fi

TS="$(date +%Y%m%d_%H%M%S)"
OUT="mamograf_${KIND}_${TS}.tar.gz"
TMP="/tmp/${OUT}"

log "boshlandi ($KIND)"

# Konteyner ishlayaptimi?
if ! docker ps --format '{{.Names}}' | grep -qx "$CONTAINER"; then
  log "XATO: $CONTAINER ishlamayapti — zaxira o'tkazib yuborildi"
  exit 1
fi

# 1) WAL checkpoint — db.sqlite3 ni eng so'nggi holatga keltirish
docker exec "$CONTAINER" python3 -c \
  "import sqlite3;c=sqlite3.connect('/app/app/db.sqlite3');c.execute('PRAGMA wal_checkpoint(TRUNCATE)');c.close()" \
  2>>"$LOG" || log "ogohlantirish: WAL checkpoint muvaffaqiyatsiz (davom etamiz)"

# 2) Zaxira yaratish (konteyner ichida /tmp ga)
if ! docker exec -w /app "$CONTAINER" python -m app.backup create "$TMP" $EXTRA >>"$LOG" 2>&1; then
  log "XATO: backup create muvaffaqiyatsiz"
  exit 2
fi

# 3) Hostga ko'chirib olish
if ! docker cp "${CONTAINER}:${TMP}" "${BK_DIR}/${OUT}" 2>>"$LOG"; then
  log "XATO: docker cp muvaffaqiyatsiz"
  exit 3
fi
docker exec "$CONTAINER" rm -f "$TMP" 2>/dev/null

# Yaxlitlik tekshiruvi (tar buzuq emasmi)
if ! tar tzf "${BK_DIR}/${OUT}" >/dev/null 2>&1; then
  log "XATO: yaratilgan arxiv buzuq — o'chirilmoqda"
  rm -f "${BK_DIR}/${OUT}"
  exit 4
fi

SZ="$(du -h "${BK_DIR}/${OUT}" | cut -f1)"
log "tayyor: ${OUT} (${SZ})"

# 4) Retention — eski nusxalarni tozalash (turi bo'yicha alohida)
OLD="$(ls -1t "${BK_DIR}"/mamograf_${KIND}_*.tar.gz 2>/dev/null | tail -n +$((KEEP+1)))"
if [ -n "$OLD" ]; then
  echo "$OLD" | while IFS= read -r f; do
    rm -f "$f" && log "o'chirildi (eski): $(basename "$f")"
  done
fi

log "yakunlandi ($KIND — oxirgi $KEEP nusxa saqlanadi)"

# ---------------------------------------------------------------------------
# TIKLASH (restore):
#   1) docker cp backups/auto/<fayl>.tar.gz mamograf-app:/tmp/r.tar.gz
#   2) docker exec -w /app mamograf-app python -m app.backup restore /tmp/r.tar.gz --force
#   3) docker restart mamograf-app
# ---------------------------------------------------------------------------
