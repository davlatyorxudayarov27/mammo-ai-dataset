#!/usr/bin/env bash
# MAMOGRAF — serverni XAVFSIZ yangilash (annotatsiyalarni saqlagan holda).
#
# Annotatsiyalar, db, uploads, models — Docker NAMED VOLUME'larda saqlanadi
# (docker-compose.prod.yml). Bu skript ularga TEGMAYDI: faqat kodni yangilab,
# image'ni qayta quradi. 'docker compose down -v' HECH QACHON ishlatilmaydi.
# Qo'shimcha xavfsizlik: avval annotatsiya va db'ning backup'ini oladi.
#
# Ishlatish (serverda, loyiha papkasida):
#   bash deploy_update.sh
set -euo pipefail
cd "$(dirname "$0")"

BRANCH="${1:-feature/multilabel-radiomics-ensemble}"
COMPOSE="docker compose -f docker-compose.prod.yml"
STAMP="$(date +%F_%H%M%S)"
BK="backups"
mkdir -p "$BK"

echo "==[1/4] BACKUP (annotatsiyalar + db) — xavfsizlik uchun =="
for vol in app_annotations app_db app_uploads; do
  full="mamograf-prod_$vol"
  if docker volume inspect "$full" >/dev/null 2>&1; then
    docker run --rm -v "$full":/data:ro -v "$PWD/$BK":/backup alpine \
      tar czf "/backup/${vol}_$STAMP.tar.gz" -C /data . 2>/dev/null \
      && echo "   OK -> $BK/${vol}_$STAMP.tar.gz"
  else
    echo "   (!) '$full' volume topilmadi — ehtimol birinchi deploy."
  fi
done

echo "==[2/4] KOD yangilanmoqda ($BRANCH) =="
git fetch origin --prune
git reset --hard "origin/$BRANCH"
echo "   HEAD: $(git log --oneline -1)"

echo "==[3/4] Docker rebuild (volume'lar SAQLANADI; 'down -v' ISHLATILMAYDI) =="
$COMPOSE up -d --build

echo "==[4/4] HOLAT =="
$COMPOSE ps
echo
echo "Tekshirish:  curl -s http://localhost:8081/api/files | head -c 200 ; echo"
echo "Brauzerda:   Ctrl+F5"
echo "TUGADI. Backuplar: $PWD/$BK/"
