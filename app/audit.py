"""Foydalanuvchi harakatlari auditi va 'Savatcha' (o'chirilganni qayta tiklash).

- audit_log: kim, qachon, qaysi amalni bajardi (middleware avtomatik yozadi).
- trash: o'chirilgan obyektlar snapshot ko'rinishida saqlanadi va qayta tiklanishi mumkin.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from . import db as db_mod


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# --------------------------------------------------------------------------- #
#  Audit log
# --------------------------------------------------------------------------- #
def log_action(
    username: str | None,
    role: str | None,
    action: str | None,
    method: str | None = None,
    path: str | None = None,
    status: int | None = None,
    ip: str | None = None,
    detail=None,
) -> None:
    """Bitta harakatni audit_log'ga yozadi. Hech qachon istisno ko'tarmaydi
    (loglash so'rovni buzmasligi kerak)."""
    try:
        if detail is not None and not isinstance(detail, str):
            detail = json.dumps(detail, ensure_ascii=False, default=str)
        with db_mod.get_conn() as c:
            c.execute(
                "INSERT INTO audit_log (ts, username, role, action, method, path, status, ip, detail) "
                "VALUES (?,?,?,?,?,?,?,?,?)",
                (_now(), username, role, action, method, path, status, ip, detail),
            )
            c.commit()
    except Exception:
        pass


def list_audit(
    username: str | None = None,
    action: str | None = None,
    since: str | None = None,
    until: str | None = None,
    q: str | None = None,
    limit: int = 200,
    offset: int = 0,
) -> dict:
    where = []
    args: list = []
    if username:
        where.append("username = ?"); args.append(username)
    if action:
        where.append("action LIKE ?"); args.append(action + "%")
    if since:
        where.append("ts >= ?"); args.append(since)
    if until:
        where.append("ts <= ?"); args.append(until)
    if q:
        where.append("(path LIKE ? OR detail LIKE ? OR action LIKE ?)")
        args += [f"%{q}%", f"%{q}%", f"%{q}%"]
    clause = (" WHERE " + " AND ".join(where)) if where else ""
    limit = max(1, min(2000, int(limit)))
    with db_mod.get_conn() as c:
        total = c.execute(f"SELECT COUNT(*) FROM audit_log{clause}", args).fetchone()[0]
        rows = c.execute(
            f"SELECT * FROM audit_log{clause} ORDER BY id DESC LIMIT ? OFFSET ?",
            args + [limit, max(0, int(offset))],
        ).fetchall()
    return {"total": total, "items": [dict(r) for r in rows]}


def audit_users() -> list[str]:
    with db_mod.get_conn() as c:
        rows = c.execute(
            "SELECT DISTINCT username FROM audit_log WHERE username IS NOT NULL ORDER BY username"
        ).fetchall()
    return [r[0] for r in rows]


# --------------------------------------------------------------------------- #
#  Savatcha (trash)
# --------------------------------------------------------------------------- #
def trash_put(
    resource_type: str,
    resource_id: str,
    snapshot: dict,
    label: str | None = None,
    blob_path: str | None = None,
    deleted_by: str | None = None,
) -> int:
    """O'chirilgan obyektni savatchaga qo'yadi. snapshot — qayta tiklash uchun
    yetarli ma'lumot (DB qatori yoki fayl metasi). Trash id qaytaradi."""
    payload = json.dumps(snapshot, ensure_ascii=False, default=str)
    with db_mod.get_conn() as c:
        cur = c.execute(
            "INSERT INTO trash (ts, deleted_by, resource_type, resource_id, label, snapshot, blob_path) "
            "VALUES (?,?,?,?,?,?,?)",
            (_now(), deleted_by, resource_type, str(resource_id), label, payload, blob_path),
        )
        c.commit()
        return int(cur.lastrowid)


def trash_db_row(table: str, row: dict, resource_type: str, resource_id,
                 label: str | None = None, deleted_by: str | None = None) -> int:
    """DB qatorini savatchaga (re-insert uchun) saqlash qulayligi."""
    return trash_put(
        resource_type, resource_id,
        {"kind": "db_row", "table": table, "row": dict(row)},
        label=label, deleted_by=deleted_by,
    )


def list_trash(include_restored: bool = False, resource_type: str | None = None,
               limit: int = 300) -> list[dict]:
    where = []
    args: list = []
    if not include_restored:
        where.append("restored_at IS NULL")
    if resource_type:
        where.append("resource_type = ?"); args.append(resource_type)
    clause = (" WHERE " + " AND ".join(where)) if where else ""
    with db_mod.get_conn() as c:
        rows = c.execute(
            f"SELECT id, ts, deleted_by, resource_type, resource_id, label, blob_path, "
            f"restored_at, restored_by FROM trash{clause} ORDER BY id DESC LIMIT ?",
            args + [max(1, min(1000, int(limit)))],
        ).fetchall()
    return [dict(r) for r in rows]


def get_trash(trash_id: int) -> dict | None:
    with db_mod.get_conn() as c:
        row = c.execute("SELECT * FROM trash WHERE id = ?", (trash_id,)).fetchone()
    return dict(row) if row else None


def restore(trash_id: int, by: str | None = None) -> tuple[bool, str]:
    """Savatchadagi obyektni qayta tiklaydi. (ok, xabar) qaytaradi."""
    item = get_trash(trash_id)
    if not item:
        return False, "Savatchada topilmadi"
    if item.get("restored_at"):
        return False, "Allaqachon tiklangan"
    try:
        snap = json.loads(item["snapshot"])
    except Exception:
        return False, "Snapshot buzilgan"

    kind = snap.get("kind")
    if kind == "db_row":
        ok, msg = _restore_db_row(snap)
    elif kind == "file":
        ok, msg = _restore_file(snap, item.get("blob_path"))
    else:
        return False, f"Noma'lum tur: {kind}"

    if ok:
        with db_mod.get_conn() as c:
            c.execute(
                "UPDATE trash SET restored_at = ?, restored_by = ? WHERE id = ?",
                (_now(), by, trash_id),
            )
            c.commit()
    return ok, msg


def _restore_db_row(snap: dict) -> tuple[bool, str]:
    table = snap.get("table")
    row = snap.get("row") or {}
    if not table or not row:
        return False, "Qator ma'lumoti yo'q"
    try:
        with db_mod.get_conn() as c:
            # Hozir mavjud ustunlar bilan cheklaymiz (sxema o'zgargan bo'lsa ham ishlaydi)
            cols_info = c.execute(f"PRAGMA table_info({table})").fetchall()
            valid = {r[1] for r in cols_info}
            use_cols = [k for k in row.keys() if k in valid]
            if not use_cols:
                return False, "Mos ustun topilmadi"
            placeholders = ",".join("?" for _ in use_cols)
            collist = ",".join(use_cols)
            c.execute(
                f"INSERT INTO {table} ({collist}) VALUES ({placeholders})",
                [row[k] for k in use_cols],
            )
            c.commit()
        return True, f"{table} qatori tiklandi"
    except Exception as e:  # noqa: BLE001
        return False, f"DB tiklashda xato: {e}"


def _restore_file(snap: dict, blob_path: str | None) -> tuple[bool, str]:
    orig = snap.get("orig_path")
    if not orig:
        return False, "Asl yo'l yo'q"
    if not blob_path or not os.path.exists(blob_path):
        return False, "Savatcha fayli topilmadi (allaqachon tozalangan)"
    if os.path.exists(orig):
        return False, "Asl joyda fayl allaqachon mavjud"
    try:
        os.makedirs(os.path.dirname(orig), exist_ok=True)
        os.replace(blob_path, orig)
        return True, "Fayl tiklandi"
    except Exception as e:  # noqa: BLE001
        return False, f"Fayl tiklashda xato: {e}"


def purge(trash_id: int) -> tuple[bool, str]:
    """Savatchadagi obyektni butunlay o'chiradi (blob ham)."""
    item = get_trash(trash_id)
    if not item:
        return False, "Topilmadi"
    bp = item.get("blob_path")
    if bp and os.path.exists(bp):
        try:
            if os.path.isdir(bp):
                import shutil
                shutil.rmtree(bp, ignore_errors=True)
            else:
                os.remove(bp)
        except Exception:
            pass
    with db_mod.get_conn() as c:
        c.execute("DELETE FROM trash WHERE id = ?", (trash_id,))
        c.commit()
    return True, "Butunlay o'chirildi"
