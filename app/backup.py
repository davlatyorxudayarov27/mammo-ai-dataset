"""
Backup / restore CLI.

Yaratish:
    python -m app.backup create
    python -m app.backup create my_backup.tar.gz
    python -m app.backup create --include-uploads --include-secret

Tiklash:
    python -m app.backup restore backup_2026-05-06.tar.gz
    python -m app.backup restore backup.tar.gz --force

Ro'yxat:
    python -m app.backup list
"""
from __future__ import annotations

import argparse
import shutil
import sys
import tarfile
import tempfile
from datetime import datetime
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
BACKUP_ROOT_NAME = "mamograf_backup"


def _items(include_uploads: bool, include_secret: bool) -> list[tuple[Path, str]]:
    items: list[tuple[Path, str]] = []
    db = APP_DIR / "db.sqlite3"
    if db.exists():
        items.append((db, "db.sqlite3"))
    annot_dir = APP_DIR / "annotations"
    if annot_dir.exists():
        for p in annot_dir.glob("*.json"):
            items.append((p, f"annotations/{p.name}"))
    labels = APP_DIR / "labels.json"
    if labels.exists():
        items.append((labels, "labels.json"))
    if include_uploads:
        uploads = APP_DIR / "uploads"
        if uploads.exists():
            for p in uploads.glob("*.dcm"):
                items.append((p, f"uploads/{p.name}"))
    if include_secret:
        secret = APP_DIR / ".jwt_secret"
        if secret.exists():
            items.append((secret, ".jwt_secret"))
    return items


def cmd_list(args):
    items = _items(args.include_uploads, args.include_secret)
    if not items:
        print("(bo'sh — backup qilinadigan fayl yo'q)")
        return
    total = 0
    for src, _arc in items:
        try:
            sz = src.stat().st_size
        except OSError:
            sz = 0
        total += sz
        print(f"  {sz:>12,d}  {_arc}")
    print(f"\nJami: {total:,} bayt ({total / 1024 / 1024:.1f} MB), {len(items)} fayl")


def cmd_create(args):
    items = _items(args.include_uploads, args.include_secret)
    if not items:
        print("hech narsa backup qilinmaydi", file=sys.stderr)
        sys.exit(1)
    out_path = Path(args.output) if args.output else Path.cwd() / (
        f"{BACKUP_ROOT_NAME}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.tar.gz"
    )
    with tarfile.open(out_path, "w:gz") as tar:
        for src, arc in items:
            tar.add(str(src), arcname=f"{BACKUP_ROOT_NAME}/{arc}")
    sz = out_path.stat().st_size
    print(f"yaratildi: {out_path}")
    print(f"  fayllar: {len(items)}")
    print(f"  hajm:    {sz:,} bayt ({sz / 1024 / 1024:.2f} MB)")


def cmd_restore(args):
    src = Path(args.input)
    if not src.exists():
        print(f"fayl topilmadi: {src}", file=sys.stderr)
        sys.exit(1)
    if not args.force:
        existing = []
        for cand in (APP_DIR / "db.sqlite3", APP_DIR / "annotations", APP_DIR / "uploads"):
            if cand.exists():
                existing.append(str(cand.relative_to(APP_DIR.parent)))
        if existing:
            print("Ogohlantirish: quyidagilar mavjud:")
            for x in existing:
                print(f"  {x}")
            ans = input("Davom etamizmi? Mavjud fayllar yangilanadi (yes/no): ")
            if ans.strip().lower() not in ("yes", "y", "ha"):
                print("bekor qilindi")
                return

    with tempfile.TemporaryDirectory() as tmp_str:
        tmp = Path(tmp_str)
        with tarfile.open(src, "r:gz") as tar:
            for m in tar.getmembers():
                if not m.name.startswith(f"{BACKUP_ROOT_NAME}/"):
                    print(f"  shubhali entry o'tkazib yuborildi: {m.name}", file=sys.stderr)
                    continue
                if ".." in Path(m.name).parts:
                    continue
                tar.extract(m, path=tmp)

        root = tmp / BACKUP_ROOT_NAME
        if not root.exists():
            print("backup tuzilmasi noto'g'ri (root yo'q)", file=sys.stderr)
            sys.exit(1)

        moved = 0
        for src_p in root.rglob("*"):
            if not src_p.is_file():
                continue
            rel = src_p.relative_to(root)
            dst = APP_DIR / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_p, dst)
            moved += 1
        print(f"qayta tiklandi: {moved} fayl → {APP_DIR}")


def main():
    ap = argparse.ArgumentParser(description="MAMOGRAF backup/restore CLI")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("list", help="backup tarkibini ko'rsatish (yaratmasdan)")
    p.add_argument("--include-uploads", action="store_true")
    p.add_argument("--include-secret", action="store_true")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("create", help="backup tar.gz yaratish")
    p.add_argument("output", nargs="?", help="(ixtiyoriy) chiquvchi fayl yo'li")
    p.add_argument("--include-uploads", action="store_true",
                   help="yuklangan DICOM'larni ham qo'shish (katta hajm)")
    p.add_argument("--include-secret", action="store_true",
                   help=".jwt_secret faylini ham qo'shish (xavf — ehtiyotkorlik)")
    p.set_defaults(func=cmd_create)

    p = sub.add_parser("restore", help="tar.gz dan tiklash")
    p.add_argument("input", help="backup tar.gz fayl yo'li")
    p.add_argument("--force", action="store_true",
                   help="tasdiqlashsiz tiklash (mavjud fayllarni yangilaydi)")
    p.set_defaults(func=cmd_restore)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
