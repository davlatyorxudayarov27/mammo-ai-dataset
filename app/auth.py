from __future__ import annotations

import os
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import bcrypt
import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from . import db as db_mod

ROLES = ("admin", "reviewer", "annotator")
TOKEN_TTL = timedelta(hours=12)
ALGORITHM = "HS256"

_SECRET_FILE = Path(__file__).resolve().parent / ".jwt_secret"


def _load_secret() -> str:
    env = os.environ.get("JWT_SECRET", "").strip()
    if env:
        return env
    if _SECRET_FILE.exists():
        return _SECRET_FILE.read_text(encoding="utf-8").strip()
    s = secrets.token_urlsafe(48)
    _SECRET_FILE.write_text(s, encoding="utf-8")
    return s


_SECRET = _load_secret()
_bearer = HTTPBearer(auto_error=False)


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def issue_token(user: dict) -> tuple[str, str]:
    now = datetime.now(timezone.utc)
    exp = now + TOKEN_TTL
    payload = {
        "sub": user["username"],
        "uid": user["id"],
        "role": user["role"],
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    return jwt.encode(payload, _SECRET, algorithm=ALGORITHM), exp.isoformat()


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, _SECRET, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "invalid token")


def get_user_by_username(username: str) -> Optional[dict]:
    with db_mod.get_conn() as c:
        row = c.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
    return dict(row) if row else None


def create_user(
    username: str,
    password: str,
    role: str,
    display_name: Optional[str] = None,
    email: Optional[str] = None,
) -> dict:
    if role not in ROLES:
        raise ValueError(f"role must be one of {ROLES}")
    now = datetime.now(timezone.utc).isoformat()
    with db_mod.get_conn() as c:
        c.execute(
            "INSERT INTO users (username, password_hash, role, display_name, email, is_active, created_at) "
            "VALUES (?, ?, ?, ?, ?, 1, ?)",
            (username, hash_password(password), role, display_name, email, now),
        )
        c.commit()
        row = c.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    return dict(row)


def update_password(username: str, new_password: str) -> bool:
    with db_mod.get_conn() as c:
        cur = c.execute(
            "UPDATE users SET password_hash = ? WHERE username = ?",
            (hash_password(new_password), username),
        )
        c.commit()
    return cur.rowcount > 0


def update_last_login(user_id: int) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with db_mod.get_conn() as c:
        c.execute("UPDATE users SET last_login_at = ? WHERE id = ?", (now, user_id))
        c.commit()


def public_user(row: dict) -> dict:
    return {
        "id": row["id"],
        "username": row["username"],
        "role": row["role"],
        "display_name": row.get("display_name"),
        "email": row.get("email"),
        "is_active": bool(row.get("is_active", 1)),
        "last_login_at": row.get("last_login_at"),
        "created_at": row.get("created_at"),
        "totp_enrolled": bool(row.get("totp_enrolled", 0)),
    }


def generate_totp_secret() -> str:
    import pyotp
    return pyotp.random_base32()


def totp_provisioning_uri(username: str, secret: str, issuer: str = "MAMOGRAF") -> str:
    import pyotp
    return pyotp.totp.TOTP(secret).provisioning_uri(name=username, issuer_name=issuer)


def totp_qr_data_uri(provisioning_uri: str) -> str:
    import io
    import base64
    import qrcode
    img = qrcode.make(provisioning_uri)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def verify_totp(secret: str, code: str) -> bool:
    if not secret or not code:
        return False
    import pyotp
    try:
        return pyotp.TOTP(secret).verify(code.strip(), valid_window=1)
    except Exception:
        return False


def set_totp_secret(username: str, secret: Optional[str], enrolled: bool) -> None:
    with db_mod.get_conn() as c:
        c.execute(
            "UPDATE users SET totp_secret = ?, totp_enrolled = ? WHERE username = ?",
            (secret, 1 if enrolled else 0, username),
        )
        c.commit()


def get_setting(key: str, default: str = "") -> str:
    with db_mod.get_conn() as c:
        row = c.execute(
            "SELECT value FROM system_settings WHERE key = ?", (key,)
        ).fetchone()
    return row[0] if row else default


def set_setting(key: str, value: str, updated_by: Optional[str] = None) -> None:
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    with db_mod.get_conn() as c:
        c.execute(
            "INSERT INTO system_settings (key, value, updated_by, updated_at) "
            "VALUES (?, ?, ?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value, "
            "updated_by=excluded.updated_by, updated_at=excluded.updated_at",
            (key, value, updated_by, now),
        )
        c.commit()


def totp_required_roles() -> list[str]:
    raw = get_setting("totp_required_roles", "")
    return [r.strip() for r in raw.split(",") if r.strip()]


def needs_totp_setup(user_row: dict) -> bool:
    if user_row.get("totp_enrolled"):
        return False
    return user_row.get("role") in totp_required_roles()


def has_any_user() -> bool:
    with db_mod.get_conn() as c:
        return c.execute("SELECT COUNT(*) FROM users").fetchone()[0] > 0


def list_users() -> list[dict]:
    with db_mod.get_conn() as c:
        rows = c.execute(
            "SELECT * FROM users ORDER BY username"
        ).fetchall()
    return [public_user(dict(r)) for r in rows]


async def current_user_optional(
    request: Request,
    creds: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> Optional[dict]:
    if creds is None:
        return None
    payload = decode_token(creds.credentials)
    return payload


async def require_user(
    user: Optional[dict] = Depends(current_user_optional),
) -> dict:
    if user is None:
        raise HTTPException(401, "authentication required")
    return user


def require_role(*roles: str):
    async def _dep(user: dict = Depends(require_user)) -> dict:
        if user.get("role") not in roles:
            raise HTTPException(403, f"role required: {', '.join(roles)}")
        return user
    return _dep
