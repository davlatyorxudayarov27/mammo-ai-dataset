from __future__ import annotations

import csv
import io
import json
import os
import re
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import pydicom
from fastapi import Depends, FastAPI, File, HTTPException, Query, Request, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from . import annotations as annot_store
from . import auth as auth_mod
from . import db as db_mod
from . import deidentify as deid
from . import dicom_seg as dseg
from . import dicom_sr as dsr
from . import inference as inf
from . import pacs as pacs_mod
from . import ws as ws_mod
from .dicom_utils import (
    NoPixelDataError, extract_sr_content, quick_summary,
    read_metadata, render_frame_png,
)

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
ANNOT_DIR = BASE_DIR / "annotations"
ANNOT_DIR.mkdir(exist_ok=True)
STATIC_DIR = BASE_DIR / "static"

# Avtomatik anonimlashtirish: upload paytida DICOM PHI tag'lari tozalanadi.
# AUTO_DEIDENTIFY=0 yoki "false" o'rnatilsa — o'chiriladi (sukut: yoqilgan).
AUTO_DEIDENTIFY = os.environ.get("AUTO_DEIDENTIFY", "1").strip().lower() not in (
    "0", "false", "no", "off", ""
)

DEFAULT_LABELS = [
    {"name": "mass", "color": "#ff5050"},
    {"name": "calcification", "color": "#ffb000"},
    {"name": "asymmetry", "color": "#00c4ff"},
    {"name": "architectural_distortion", "color": "#a070ff"},
    {"name": "skin_thickening", "color": "#28d97f"},
    {"name": "nipple_retraction", "color": "#ff80b4"},
    {"name": "lymph_node", "color": "#ffe44d"},
    {"name": "other", "color": "#9aa3b2"},
]
BIRADS_VALUES = ["0", "1", "2", "3", "4A", "4B", "4C", "5", "6"]
LABELS_CONFIG = BASE_DIR / "labels.json"


def load_labels_config() -> tuple[list[dict], list[str]]:
    if LABELS_CONFIG.exists():
        try:
            data = json.loads(LABELS_CONFIG.read_text(encoding="utf-8"))
            labels = data.get("labels") or DEFAULT_LABELS
            birads = data.get("birads") or BIRADS_VALUES
            return labels, birads
        except Exception:
            pass
    return DEFAULT_LABELS, BIRADS_VALUES

LOCAL_ROOT_ENV = os.environ.get("LOCAL_DICOM_ROOT", "").strip()
LOCAL_ROOT: Optional[Path] = Path(LOCAL_ROOT_ENV).resolve() if LOCAL_ROOT_ENV else None

@asynccontextmanager
async def lifespan(_app: FastAPI):
    db_mod.init_db()
    yield


def _client_key(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        try:
            payload = auth_mod.decode_token(auth.split(" ", 1)[1])
            return f"user:{payload.get('sub','?')}"
        except HTTPException:
            pass
    return f"ip:{get_remote_address(request)}"


limiter = Limiter(key_func=_client_key)

app = FastAPI(title="MAMOGRAF DICOM Viewer", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

_ALLOWED_ORIGINS = [
    o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "").split(",") if o.strip()
]
if _ALLOWED_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

_CSP = (
    "default-src 'self'; "
    "img-src 'self' data: blob:; "
    "style-src 'self' 'unsafe-inline'; "
    "script-src 'self'; "
    "connect-src 'self' ws: wss:; "
    "object-src 'none'; "
    "base-uri 'self'; "
    "frame-ancestors 'none';"
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "interest-cohort=()"
    response.headers["Content-Security-Policy"] = _CSP
    return response


def _resolve_local(rel: str) -> Path:
    if LOCAL_ROOT is None:
        raise HTTPException(404, "local browsing disabled (set LOCAL_DICOM_ROOT)")
    p = (LOCAL_ROOT / rel).resolve()
    try:
        p.relative_to(LOCAL_ROOT)
    except ValueError:
        raise HTTPException(400, "invalid path")
    if not p.exists() or not p.is_file():
        raise HTTPException(404, "file not found")
    return p


def _looks_like_dicom(p: Path) -> bool:
    suf = p.suffix.lower()
    if suf in (".dcm", ".dicom"):
        return True
    if suf == "":
        try:
            with p.open("rb") as f:
                f.seek(128)
                return f.read(4) == b"DICM"
        except OSError:
            return False
    return False


@app.get("/api/config")
def config():
    return {
        "local_browsing": LOCAL_ROOT is not None,
        "local_root": str(LOCAL_ROOT) if LOCAL_ROOT else None,
        "auth_required": auth_mod.has_any_user(),
    }


class LoginBody(BaseModel):
    username: str
    password: str
    totp_code: Optional[str] = None


@app.post("/api/auth/login")
@limiter.limit("10/minute")
def auth_login(request: Request, body: LoginBody):
    user = auth_mod.get_user_by_username(body.username)
    if not user or not user.get("is_active"):
        raise HTTPException(401, "invalid credentials")
    if not auth_mod.verify_password(body.password, user["password_hash"]):
        raise HTTPException(401, "invalid credentials")
    if user.get("totp_enrolled"):
        if not body.totp_code:
            raise HTTPException(
                status_code=401,
                detail={"error": "totp_required", "message": "TOTP kodi kerak"},
            )
        if not auth_mod.verify_totp(user.get("totp_secret"), body.totp_code):
            raise HTTPException(401, "invalid TOTP code")
    auth_mod.update_last_login(user["id"])
    token, exp = auth_mod.issue_token(user)
    pub = auth_mod.public_user(user)
    pub["totp_setup_required"] = auth_mod.needs_totp_setup(user)
    return {
        "token": token,
        "expires_at": exp,
        "user": pub,
    }


@app.get("/api/settings")
def get_settings(_user: dict = Depends(auth_mod.require_user)):
    return {
        "totp_required_roles": auth_mod.totp_required_roles(),
    }


class SettingsBody(BaseModel):
    totp_required_roles: Optional[list[str]] = None


@app.patch("/api/settings")
def update_settings(
    body: SettingsBody,
    user: dict = Depends(auth_mod.require_role("admin")),
):
    if body.totp_required_roles is not None:
        valid = {r for r in body.totp_required_roles if r in auth_mod.ROLES}
        auth_mod.set_setting(
            "totp_required_roles", ",".join(sorted(valid)), updated_by=user.get("sub")
        )
    return {"ok": True, "totp_required_roles": auth_mod.totp_required_roles()}


@app.post("/api/auth/totp/setup")
def auth_totp_setup(user: dict = Depends(auth_mod.require_user)):
    row = auth_mod.get_user_by_username(user["sub"])
    if not row:
        raise HTTPException(404, "user not found")
    if row.get("totp_enrolled"):
        raise HTTPException(409, "TOTP allaqachon yoqilgan")
    secret = auth_mod.generate_totp_secret()
    auth_mod.set_totp_secret(user["sub"], secret, enrolled=False)
    uri = auth_mod.totp_provisioning_uri(user["sub"], secret)
    qr = auth_mod.totp_qr_data_uri(uri)
    return {"secret": secret, "uri": uri, "qr_png_data_url": qr}


class TotpVerifyBody(BaseModel):
    code: str


@app.post("/api/auth/totp/verify")
def auth_totp_verify(
    body: TotpVerifyBody,
    user: dict = Depends(auth_mod.require_user),
):
    row = auth_mod.get_user_by_username(user["sub"])
    if not row or not row.get("totp_secret"):
        raise HTTPException(400, "TOTP setup qilinmagan")
    if not auth_mod.verify_totp(row.get("totp_secret"), body.code):
        raise HTTPException(401, "kod noto'g'ri")
    auth_mod.set_totp_secret(user["sub"], row.get("totp_secret"), enrolled=True)
    return {"ok": True, "totp_enrolled": True}


class TotpDisableBody(BaseModel):
    password: str


@app.post("/api/auth/totp/disable")
def auth_totp_disable(
    body: TotpDisableBody,
    user: dict = Depends(auth_mod.require_user),
):
    row = auth_mod.get_user_by_username(user["sub"])
    if not row:
        raise HTTPException(404, "user not found")
    if not auth_mod.verify_password(body.password, row["password_hash"]):
        raise HTTPException(401, "parol noto'g'ri")
    auth_mod.set_totp_secret(user["sub"], None, enrolled=False)
    return {"ok": True}


@app.get("/api/auth/me")
def auth_me(user: dict = Depends(auth_mod.require_user)):
    row = auth_mod.get_user_by_username(user["sub"])
    if not row:
        raise HTTPException(401, "user not found")
    pub = auth_mod.public_user(row)
    pub["totp_setup_required"] = auth_mod.needs_totp_setup(row)
    return pub


class PasswordChangeBody(BaseModel):
    current_password: str
    new_password: str


@app.post("/api/auth/change-password")
def auth_change_password(
    body: PasswordChangeBody,
    user: dict = Depends(auth_mod.require_user),
):
    row = auth_mod.get_user_by_username(user["sub"])
    if not row or not auth_mod.verify_password(body.current_password, row["password_hash"]):
        raise HTTPException(401, "current password incorrect")
    if len(body.new_password) < 4:
        raise HTTPException(400, "new password too short")
    auth_mod.update_password(user["sub"], body.new_password)
    return {"ok": True}


@app.get("/api/auth/users")
def auth_users(_admin: dict = Depends(auth_mod.require_role("admin"))):
    return {"users": auth_mod.list_users()}


class CreateUserBody(BaseModel):
    username: str
    password: str
    role: str
    display_name: Optional[str] = None
    email: Optional[str] = None


@app.post("/api/auth/users")
def admin_create_user(
    body: CreateUserBody,
    _admin: dict = Depends(auth_mod.require_role("admin")),
):
    if body.role not in auth_mod.ROLES:
        raise HTTPException(400, f"role must be one of {auth_mod.ROLES}")
    if not body.username or not body.username.strip():
        raise HTTPException(400, "username required")
    if len(body.password) < 4:
        raise HTTPException(400, "password too short (min 4)")
    if auth_mod.get_user_by_username(body.username):
        raise HTTPException(409, "username already exists")
    user = auth_mod.create_user(
        username=body.username.strip(),
        password=body.password,
        role=body.role,
        display_name=body.display_name,
        email=body.email,
    )
    return {"ok": True, "user": auth_mod.public_user(user)}


class UpdateUserBody(BaseModel):
    role: Optional[str] = None
    display_name: Optional[str] = None
    email: Optional[str] = None
    is_active: Optional[bool] = None


@app.patch("/api/auth/users/{username}")
def admin_update_user(
    username: str,
    body: UpdateUserBody,
    admin: dict = Depends(auth_mod.require_role("admin")),
):
    user = auth_mod.get_user_by_username(username)
    if not user:
        raise HTTPException(404, "user not found")
    fields = []
    params: list = []
    if body.role is not None:
        if body.role not in auth_mod.ROLES:
            raise HTTPException(400, "invalid role")
        if username == admin.get("sub") and body.role != "admin":
            raise HTTPException(400, "cannot demote yourself")
        fields.append("role = ?"); params.append(body.role)
    if body.display_name is not None:
        fields.append("display_name = ?"); params.append(body.display_name)
    if body.email is not None:
        fields.append("email = ?"); params.append(body.email)
    if body.is_active is not None:
        if username == admin.get("sub") and not body.is_active:
            raise HTTPException(400, "cannot deactivate yourself")
        fields.append("is_active = ?"); params.append(1 if body.is_active else 0)
    if not fields:
        return {"ok": True, "user": auth_mod.public_user(user), "no_changes": True}
    params.append(username)
    with db_mod.get_conn() as c:
        c.execute(f"UPDATE users SET {', '.join(fields)} WHERE username = ?", params)
        c.commit()
    refreshed = auth_mod.get_user_by_username(username)
    return {"ok": True, "user": auth_mod.public_user(refreshed)}


class AdminResetPasswordBody(BaseModel):
    new_password: str


@app.post("/api/auth/users/{username}/reset-password")
def admin_reset_password(
    username: str,
    body: AdminResetPasswordBody,
    _admin: dict = Depends(auth_mod.require_role("admin")),
):
    if not auth_mod.get_user_by_username(username):
        raise HTTPException(404, "user not found")
    if len(body.new_password) < 4:
        raise HTTPException(400, "password too short (min 4)")
    auth_mod.update_password(username, body.new_password)
    return {"ok": True}


@app.delete("/api/auth/users/{username}")
def admin_delete_user(
    username: str,
    admin: dict = Depends(auth_mod.require_role("admin")),
):
    if username == admin.get("sub"):
        raise HTTPException(400, "cannot delete yourself")
    if not auth_mod.get_user_by_username(username):
        raise HTTPException(404, "user not found")
    with db_mod.get_conn() as c:
        c.execute("DELETE FROM users WHERE username = ?", (username,))
        c.commit()
    return {"ok": True}


_UPLOAD_CHUNK = 1024 * 1024  # 1 MB


@app.post("/api/upload")
async def upload(
    files: list[UploadFile] = File(...),
    _user: dict = Depends(auth_mod.require_user),
):
    saved = []
    for f in files:
        file_id = uuid.uuid4().hex
        out = UPLOAD_DIR / f"{file_id}.dcm"
        with out.open("wb") as fout:
            while True:
                chunk = await f.read(_UPLOAD_CHUNK)
                if not chunk:
                    break
                fout.write(chunk)
        try:
            ds = pydicom.dcmread(out, stop_before_pixels=True, force=True)
        except Exception as e:
            out.unlink(missing_ok=True)
            raise HTTPException(status_code=400, detail=f"{f.filename}: not a valid DICOM ({e})")

        # Avtomatik anonimlashtirish: PHI tag'lari tozalanadi va fayl qayta yoziladi.
        # Box/annotation va export PHI-siz fayl ustida bajariladi.
        deidentified_now = False
        if AUTO_DEIDENTIFY:
            try:
                deid.anonymize_in_place(out)
                ds = pydicom.dcmread(out, stop_before_pixels=True, force=True)
                deidentified_now = True
            except Exception as e:
                out.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=500,
                    detail=f"{f.filename}: anonymization failed ({e})",
                )

        rows = int(getattr(ds, "Rows", 0) or 0)
        cols = int(getattr(ds, "Columns", 0) or 0)
        info = {
            "id": file_id,
            "patient": str(getattr(ds, "PatientName", "")),
            "patient_id": str(getattr(ds, "PatientID", "")),
            "modality": str(getattr(ds, "Modality", "")),
            "study_date": str(getattr(ds, "StudyDate", "")),
            "view": str(getattr(ds, "ViewPosition", "")),
            "laterality": str(getattr(ds, "ImageLaterality", "")),
            "rows": rows,
            "cols": cols,
            "frames": int(getattr(ds, "NumberOfFrames", 1) or 1) if rows and cols else 0,
            "has_pixels": bool(rows and cols),
            "annotation_count": 0,
            "original_name": f.filename,
            "deidentified": deidentified_now,
        }
        saved.append(info)
    return {"files": saved}


@app.get("/api/files")
def list_files():
    items = []
    for p in sorted(UPLOAD_DIR.glob("*.dcm")):
        info = quick_summary(p)
        if "error" in info:
            continue
        info["id"] = p.stem
        info["annotation_count"] = annot_store.count(ANNOT_DIR, "upload", p.stem)
        items.append(info)
    return {"files": items}


@app.get("/api/files/{file_id}/metadata")
def metadata(file_id: str):
    p = UPLOAD_DIR / f"{file_id}.dcm"
    if not p.exists():
        raise HTTPException(404)
    return read_metadata(p)


@app.get("/api/files/{file_id}/image")
def image(
    file_id: str,
    frame: int = 0,
    wc: Optional[float] = Query(default=None),
    ww: Optional[float] = Query(default=None),
    invert: bool = False,
    max_dim: int = 2048,
):
    p = UPLOAD_DIR / f"{file_id}.dcm"
    if not p.exists():
        raise HTTPException(404)
    try:
        png_bytes = render_frame_png(p, frame=frame, wc=wc, ww=ww, invert=invert, max_dim=max_dim)
    except NoPixelDataError as e:
        raise HTTPException(
            status_code=422,
            detail={"error": "no_pixels", "modality": e.modality, "sop_class": e.sop_class},
        )
    except Exception as e:
        raise HTTPException(500, f"render failed: {e}")
    return StreamingResponse(io.BytesIO(png_bytes), media_type="image/png")


@app.delete("/api/files/{file_id}")
def delete_file(file_id: str, _user: dict = Depends(auth_mod.require_user)):
    p = UPLOAD_DIR / f"{file_id}.dcm"
    if p.exists():
        p.unlink()
    return {"ok": True}


@app.get("/api/local/list")
def local_list(subdir: str = "", limit: int = 1000):
    if LOCAL_ROOT is None:
        return {"enabled": False, "dirs": [], "files": []}
    target = (LOCAL_ROOT / subdir).resolve()
    try:
        target.relative_to(LOCAL_ROOT)
    except ValueError:
        raise HTTPException(400, "invalid path")
    if not target.exists() or not target.is_dir():
        raise HTTPException(404, "directory not found")

    dirs, files = [], []
    try:
        entries = sorted(target.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
    except PermissionError:
        raise HTTPException(403, "permission denied")

    for p in entries[:limit]:
        rel = p.relative_to(LOCAL_ROOT).as_posix()
        if p.is_dir():
            dirs.append({"name": p.name, "path": rel})
        elif _looks_like_dicom(p):
            try:
                size = p.stat().st_size
            except OSError:
                size = 0
            files.append({
                "name": p.name,
                "path": rel,
                "size": size,
                "annotation_count": annot_store.count(ANNOT_DIR, "local", rel),
            })

    parent = ""
    if subdir:
        parent_path = Path(subdir).parent.as_posix()
        parent = "" if parent_path == "." else parent_path

    return {
        "enabled": True,
        "root": str(LOCAL_ROOT),
        "subdir": subdir,
        "parent": parent,
        "dirs": dirs,
        "files": files,
    }


@app.get("/api/local/metadata")
def local_metadata(path: str):
    p = _resolve_local(path)
    return read_metadata(p)


@app.get("/api/files/{file_id}/sr-content")
def upload_sr_content(file_id: str):
    p = UPLOAD_DIR / f"{file_id}.dcm"
    if not p.exists():
        raise HTTPException(404, "upload not found")
    try:
        return extract_sr_content(p)
    except Exception as e:
        raise HTTPException(500, f"SR parse failed: {e}")


@app.get("/api/local/sr-content")
def local_sr_content(path: str):
    p = _resolve_local(path)
    try:
        return extract_sr_content(p)
    except Exception as e:
        raise HTTPException(500, f"SR parse failed: {e}")


@app.get("/api/local/summary")
def local_summary(path: str):
    p = _resolve_local(path)
    return quick_summary(p)


@app.get("/api/local/image")
def local_image(
    path: str,
    frame: int = 0,
    wc: Optional[float] = Query(default=None),
    ww: Optional[float] = Query(default=None),
    invert: bool = False,
    max_dim: int = 2048,
):
    p = _resolve_local(path)
    try:
        png_bytes = render_frame_png(p, frame=frame, wc=wc, ww=ww, invert=invert, max_dim=max_dim)
    except NoPixelDataError as e:
        raise HTTPException(
            status_code=422,
            detail={"error": "no_pixels", "modality": e.modality, "sop_class": e.sop_class},
        )
    except Exception as e:
        raise HTTPException(500, f"render failed: {e}")
    return StreamingResponse(io.BytesIO(png_bytes), media_type="image/png")


@app.get("/api/labels")
def labels():
    lbls, brs = load_labels_config()
    return {"labels": lbls, "birads": brs}


class AnnotationsBody(BaseModel):
    source: str
    ref: str
    annotations: list[dict] = []
    rows: Optional[int] = None
    cols: Optional[int] = None


def _validate_source(source: str) -> None:
    if source not in ("upload", "local"):
        raise HTTPException(400, "invalid source")


def _validate_ref(source: str, ref: str) -> None:
    if not ref:
        raise HTTPException(400, "missing ref")
    if source == "upload":
        if not ref.replace("-", "").replace("_", "").isalnum():
            raise HTTPException(400, "invalid upload id")
        if not (UPLOAD_DIR / f"{ref}.dcm").exists():
            raise HTTPException(404, "upload not found")
    else:
        _resolve_local(ref)


@app.get("/api/annotations")
def get_annotations(source: str, ref: str):
    _validate_source(source)
    _validate_ref(source, ref)
    return annot_store.load(ANNOT_DIR, source, ref)


_HISTORY_IGNORE_FIELDS = {"updated_at", "updated_by"}


def _annotation_state_eq(a: dict, b: dict) -> bool:
    def normalize(d: dict) -> dict:
        return {k: v for k, v in d.items() if k not in _HISTORY_IGNORE_FIELDS}
    return normalize(a) == normalize(b)


def _notify(
    recipients: list[str],
    kind: str,
    title: str,
    body: str = "",
    link_source: Optional[str] = None,
    link_ref: Optional[str] = None,
    link_annotation_id: Optional[str] = None,
    actor: Optional[str] = None,
) -> None:
    if not recipients:
        return
    now = datetime.now(timezone.utc).isoformat()
    with db_mod.get_conn() as c:
        for r in recipients:
            c.execute(
                "INSERT INTO notifications "
                "(recipient, ts, kind, title, body, link_source, link_ref, link_annotation_id, actor) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (r, now, kind, title, body, link_source, link_ref, link_annotation_id, actor),
            )
        c.commit()


def _reviewer_recipients(exclude: Optional[str] = None) -> list[str]:
    with db_mod.get_conn() as c:
        rows = c.execute(
            "SELECT username FROM users "
            "WHERE role IN ('reviewer', 'admin') AND is_active = 1"
        ).fetchall()
    return [r[0] for r in rows if r[0] != exclude]


_ANNOT_CHANGE_TS = 0.0
_CACHE: dict[str, tuple[float, object]] = {}
_CACHE_TTL = 30.0


def _bump_annot_ts() -> None:
    import time
    global _ANNOT_CHANGE_TS
    _ANNOT_CHANGE_TS = time.time()


def _cache_get(key: str):
    import time
    entry = _CACHE.get(key)
    if not entry:
        return None
    ts, value = entry
    if ts < _ANNOT_CHANGE_TS:
        return None
    if time.time() - ts > _CACHE_TTL:
        return None
    return value


def _cache_set(key: str, value: object) -> None:
    import time
    _CACHE[key] = (time.time(), value)


def _record_history(source: str, ref: str, rows: list[dict]) -> None:
    if not rows:
        return
    with db_mod.get_conn() as c:
        for row in rows:
            c.execute(
                "INSERT INTO annotation_history "
                "(source, ref, annotation_id, action, username, ts, prev_snapshot, new_snapshot) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    source, ref,
                    row["annotation_id"],
                    row["action"],
                    row["username"],
                    row["ts"],
                    json.dumps(row["prev"], ensure_ascii=False) if row.get("prev") else None,
                    json.dumps(row["new"], ensure_ascii=False) if row.get("new") else None,
                ),
            )
        c.commit()


@app.put("/api/annotations")
async def put_annotations(
    body: AnnotationsBody,
    user: dict = Depends(auth_mod.require_user),
):
    _validate_source(body.source)
    _validate_ref(body.source, body.ref)
    now = datetime.now(timezone.utc).isoformat()
    username = user.get("sub") or ""
    role = user.get("role") or ""

    old_data = annot_store.load(ANNOT_DIR, body.source, body.ref)
    old_by_id = {a.get("id"): a for a in old_data.get("annotations", []) if a.get("id")}
    new_by_id = {a.get("id"): a for a in body.annotations if a.get("id")}

    history_rows: list[dict] = []

    for aid, new_a in new_by_id.items():
        old_a = old_by_id.get(aid)
        if old_a is None:
            new_a.setdefault("created_by", username)
            new_a.setdefault("created_at", now)
            new_a["updated_by"] = username
            new_a["updated_at"] = now
            new_a.setdefault("status", "draft")
            history_rows.append({
                "annotation_id": aid, "action": "create",
                "username": username, "ts": now,
                "prev": None, "new": new_a,
            })
        else:
            new_a["created_by"] = old_a.get("created_by") or username
            new_a["created_at"] = old_a.get("created_at") or now
            new_a["status"] = old_a.get("status", "draft")
            if "reviewed_by" in old_a:
                new_a["reviewed_by"] = old_a["reviewed_by"]
            if "reviewed_at" in old_a:
                new_a["reviewed_at"] = old_a["reviewed_at"]
            if "review_note" in old_a:
                new_a["review_note"] = old_a["review_note"]

            if role == "annotator":
                if old_a.get("created_by") and old_a.get("created_by") != username:
                    if not _annotation_state_eq(old_a, new_a):
                        raise HTTPException(403, f"annotator cannot edit annotation owned by {old_a.get('created_by')}")
                if old_a.get("status") in ("approved",):
                    if not _annotation_state_eq(old_a, new_a):
                        raise HTTPException(403, "approved annotation is locked; reviewer must reopen it first")

            if not _annotation_state_eq(old_a, new_a):
                new_a["updated_by"] = username
                new_a["updated_at"] = now
                history_rows.append({
                    "annotation_id": aid, "action": "update",
                    "username": username, "ts": now,
                    "prev": old_a, "new": new_a,
                })
            else:
                new_a["updated_by"] = old_a.get("updated_by") or username
                new_a["updated_at"] = old_a.get("updated_at") or now

    for aid, old_a in old_by_id.items():
        if aid in new_by_id:
            continue
        if role == "annotator":
            if old_a.get("created_by") and old_a.get("created_by") != username:
                raise HTTPException(403, f"annotator cannot delete annotation owned by {old_a.get('created_by')}")
            if old_a.get("status") in ("approved",):
                raise HTTPException(403, "approved annotation cannot be deleted by annotator")
        history_rows.append({
            "annotation_id": aid, "action": "delete",
            "username": username, "ts": now,
            "prev": old_a, "new": None,
        })

    annot_store.save(ANNOT_DIR, body.source, body.ref, body.model_dump())
    _record_history(body.source, body.ref, history_rows)
    _bump_annot_ts()
    if history_rows:
        try:
            await ws_mod.rooms.broadcast(body.source, body.ref, {
                "type": "annotations_changed",
                "by": username,
                "changes": len(history_rows),
            })
        except Exception:
            pass
    return {
        "ok": True,
        "count": len(body.annotations),
        "history_rows_added": len(history_rows),
    }


VALID_STATUSES = ("draft", "submitted", "approved", "rejected")


class StatusChangeBody(BaseModel):
    source: str
    ref: str
    annotation_id: str
    status: str
    note: Optional[str] = None


@app.post("/api/annotations/status")
async def patch_annotation_status(
    body: StatusChangeBody,
    user: dict = Depends(auth_mod.require_user),
):
    if body.status not in VALID_STATUSES:
        raise HTTPException(400, f"invalid status (allowed: {VALID_STATUSES})")
    _validate_source(body.source)
    _validate_ref(body.source, body.ref)

    data = annot_store.load(ANNOT_DIR, body.source, body.ref)
    ann = next((a for a in data.get("annotations", []) if a.get("id") == body.annotation_id), None)
    if not ann:
        raise HTTPException(404, "annotation not found")

    old_status = ann.get("status", "draft")
    new_status = body.status
    role = user.get("role")
    username = user.get("sub")
    is_owner = ann.get("created_by") == username

    annotator_allowed = {("draft", "submitted"), ("submitted", "draft")}
    if role == "annotator":
        if not is_owner:
            raise HTTPException(403, "annotator can only change own annotations")
        if (old_status, new_status) not in annotator_allowed:
            raise HTTPException(403, "annotator transitions limited to draft↔submitted on own work")

    now = datetime.now(timezone.utc).isoformat()
    ann["status"] = new_status
    ann["updated_by"] = username
    ann["updated_at"] = now
    if new_status in ("approved", "rejected"):
        ann["reviewed_by"] = username
        ann["reviewed_at"] = now
        if body.note:
            ann["review_note"] = body.note
    elif new_status == "draft" and old_status in ("approved", "rejected"):
        ann.pop("reviewed_by", None)
        ann.pop("reviewed_at", None)
        ann.pop("review_note", None)

    annot_store.save(ANNOT_DIR, body.source, body.ref, data)
    _record_history(body.source, body.ref, [{
        "annotation_id": body.annotation_id, "action": "status",
        "username": username, "ts": now,
        "prev": {"status": old_status},
        "new": {"status": new_status, "note": body.note},
    }])
    _bump_annot_ts()

    label = ann.get("label") or "annotation"
    if new_status == "submitted":
        recipients = _reviewer_recipients(exclude=username)
        _notify(
            recipients,
            kind="submitted",
            title=f"{username} '{label}' annotatsiyasini ko'rib chiqishga yubordi",
            body=f"DICOM: {body.ref}",
            link_source=body.source, link_ref=body.ref,
            link_annotation_id=body.annotation_id,
            actor=username,
        )
    elif new_status in ("approved", "rejected"):
        owner = ann.get("created_by")
        if owner and owner != username:
            verb = "tasdiqladi" if new_status == "approved" else "rad etdi"
            _notify(
                [owner],
                kind=new_status,
                title=f"{username} sizning '{label}' annotatsiyangizni {verb}",
                body=body.note or "",
                link_source=body.source, link_ref=body.ref,
                link_annotation_id=body.annotation_id,
                actor=username,
            )

    try:
        await ws_mod.rooms.broadcast(body.source, body.ref, {
            "type": "status_changed",
            "by": username,
            "annotation_id": body.annotation_id,
            "status": new_status,
        })
    except Exception:
        pass

    return {"ok": True, "status": new_status, "previous": old_status, "snapshot": ann}


@app.get("/api/notifications")
def get_notifications(
    unread_only: bool = False,
    limit: int = 50,
    user: dict = Depends(auth_mod.require_user),
):
    sql = "SELECT * FROM notifications WHERE recipient IN (?, '*')"
    params: list = [user["sub"]]
    if unread_only:
        sql += " AND read_at IS NULL"
    sql += " ORDER BY ts DESC LIMIT ?"
    params.append(limit)
    with db_mod.get_conn() as c:
        rows = [dict(r) for r in c.execute(sql, params).fetchall()]
        unread = c.execute(
            "SELECT COUNT(*) FROM notifications "
            "WHERE recipient IN (?, '*') AND read_at IS NULL",
            (user["sub"],),
        ).fetchone()[0]
    return {"notifications": rows, "unread_count": unread}


class MarkReadBody(BaseModel):
    ids: Optional[list[int]] = None
    all: bool = False


@app.post("/api/notifications/mark-read")
def mark_notifications_read(
    body: MarkReadBody,
    user: dict = Depends(auth_mod.require_user),
):
    now = datetime.now(timezone.utc).isoformat()
    with db_mod.get_conn() as c:
        if body.all:
            c.execute(
                "UPDATE notifications SET read_at = ? "
                "WHERE recipient IN (?, '*') AND read_at IS NULL",
                (now, user["sub"]),
            )
        elif body.ids:
            placeholders = ",".join("?" * len(body.ids))
            c.execute(
                f"UPDATE notifications SET read_at = ? "
                f"WHERE id IN ({placeholders}) AND recipient IN (?, '*')",
                [now, *body.ids, user["sub"]],
            )
        c.commit()
    return {"ok": True}


@app.get("/api/annotations/list")
def list_annotations(
    status: Optional[str] = None,
    created_by: Optional[str] = None,
    own: bool = False,
    limit: int = 500,
    user: dict = Depends(auth_mod.require_user),
):
    if own and not created_by:
        created_by = user["sub"]

    links: dict[tuple, dict] = {}
    with db_mod.get_conn() as c:
        for r in c.execute(
            "SELECT l.source, l.ref, p.patient_id, p.first_name, p.last_name, "
            "p.sex, p.birth_date "
            "FROM dicom_patient_links l "
            "JOIN patients p ON p.patient_id = l.patient_id"
        ).fetchall():
            d = dict(r)
            links[(d.pop("source"), d.pop("ref"))] = d

    items: list[dict] = []
    for entry in annot_store.iter_all(ANNOT_DIR):
        src = entry.get("source")
        ref = entry.get("ref")
        if not src or not ref:
            continue
        for a in entry.get("annotations", []):
            ann_status = a.get("status", "draft")
            if status and ann_status != status:
                continue
            if created_by and a.get("created_by") != created_by:
                continue
            items.append({
                "source": src,
                "ref": ref,
                "annotation_id": a.get("id"),
                "type": a.get("type", "bbox"),
                "label": a.get("label"),
                "bi_rads": a.get("bi_rads"),
                "status": ann_status,
                "created_by": a.get("created_by"),
                "updated_by": a.get("updated_by"),
                "reviewed_by": a.get("reviewed_by"),
                "review_note": a.get("review_note"),
                "created_at": a.get("created_at"),
                "updated_at": a.get("updated_at"),
                "patient": links.get((src, ref)),
            })

    items.sort(key=lambda x: (x.get("updated_at") or "", x.get("created_at") or ""), reverse=True)
    return {"items": items[:limit], "count": min(len(items), limit), "total": len(items)}


@app.get("/api/audit/timeline")
def audit_timeline(
    since: Optional[str] = None,
    username: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = 200,
    _user: dict = Depends(auth_mod.require_role("admin", "reviewer")),
):
    sql = "SELECT * FROM annotation_history WHERE 1=1"
    params: list = []
    if since:
        sql += " AND ts >= ?"
        params.append(since)
    if username:
        sql += " AND username = ?"
        params.append(username)
    if action:
        sql += " AND action = ?"
        params.append(action)
    sql += " ORDER BY ts DESC, id DESC LIMIT ?"
    params.append(limit)
    with db_mod.get_conn() as c:
        rows = [dict(r) for r in c.execute(sql, params).fetchall()]
    for r in rows:
        for k in ("prev_snapshot", "new_snapshot"):
            v = r.get(k)
            if v:
                try:
                    r[k] = json.loads(v)
                except Exception:
                    pass
    return {"events": rows, "count": len(rows)}


@app.get("/api/annotations/history")
def get_annotation_history(
    source: str,
    ref: str,
    annotation_id: Optional[str] = None,
    limit: int = 200,
):
    _validate_source(source)
    _validate_ref(source, ref)
    sql = "SELECT * FROM annotation_history WHERE source = ? AND ref = ?"
    params: list = [source, ref]
    if annotation_id:
        sql += " AND annotation_id = ?"
        params.append(annotation_id)
    sql += " ORDER BY ts DESC, id DESC LIMIT ?"
    params.append(limit)

    with db_mod.get_conn() as c:
        rows = [dict(r) for r in c.execute(sql, params).fetchall()]
    for r in rows:
        for k in ("prev_snapshot", "new_snapshot"):
            v = r.get(k)
            if v:
                try:
                    r[k] = json.loads(v)
                except Exception:
                    pass
    return {"history": rows, "count": len(rows)}


def _polygon_area(pts: list[tuple[float, float]]) -> float:
    n = len(pts)
    if n < 3:
        return 0.0
    s = 0.0
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        s += x1 * y2 - x2 * y1
    return s / 2.0


def _resolve_dims(source: str, ref: str, stored_rows, stored_cols):
    if stored_rows and stored_cols:
        return int(stored_rows), int(stored_cols)
    try:
        if source == "upload":
            p = UPLOAD_DIR / f"{ref}.dcm"
        else:
            p = (LOCAL_ROOT / ref).resolve() if LOCAL_ROOT else None
        if p and p.exists():
            s = quick_summary(p)
            return int(s.get("rows") or 0), int(s.get("cols") or 0)
    except Exception:
        pass
    return 0, 0


def _build_coco():
    labels_cfg, _ = load_labels_config()
    seen_labels: list[str] = [l["name"] for l in labels_cfg]

    links: dict[tuple, dict] = {}
    with db_mod.get_conn() as c:
        for row in c.execute(
            "SELECT l.source, l.ref, l.confidence, l.confirmed_at, "
            "p.patient_id, p.first_name, p.last_name, p.sex, p.birth_date "
            "FROM dicom_patient_links l "
            "JOIN patients p ON p.patient_id = l.patient_id"
        ).fetchall():
            d = dict(row)
            src = d.pop("source"); ref = d.pop("ref")
            links[(src, ref)] = d

    images = []
    annotations_out = []
    image_ix: dict[tuple, int] = {}
    label_ix: dict[str, int] = {name: i + 1 for i, name in enumerate(seen_labels)}
    next_image_id = 1
    next_ann_id = 1

    for entry in annot_store.iter_all(ANNOT_DIR):
        source = entry.get("source")
        ref = entry.get("ref")
        if not source or not ref:
            continue
        rows, cols = _resolve_dims(source, ref, entry.get("rows"), entry.get("cols"))
        key = (source, ref)
        if key not in image_ix:
            image_ix[key] = next_image_id
            img_entry = {
                "id": next_image_id,
                "file_name": ref,
                "source": source,
                "width": cols or 0,
                "height": rows or 0,
            }
            if key in links:
                img_entry["patient"] = links[key]
            images.append(img_entry)
            next_image_id += 1
        img_id = image_ix[key]
        link_for_image = links.get(key)
        for a in entry.get("annotations", []):
            label = a.get("label") or "other"
            if label not in label_ix:
                label_ix[label] = len(label_ix) + 1
            cat_id = label_ix[label]
            bbox = a.get("bbox") or [0, 0, 0, 0]
            if len(bbox) != 4:
                continue
            x_n, y_n, w_n, h_n = bbox
            if rows and cols:
                x = x_n * cols
                y = y_n * rows
                w = w_n * cols
                h = h_n * rows
            else:
                x, y, w, h = x_n, y_n, w_n, h_n

            ann_type = a.get("type") or "bbox"
            ann_out = {
                "id": next_ann_id,
                "image_id": img_id,
                "category_id": cat_id,
                "type": ann_type,
                "bbox": [round(x, 2), round(y, 2), round(w, 2), round(h, 2)],
                "bbox_normalized": [x_n, y_n, w_n, h_n],
                "iscrowd": 0,
                "bi_rads": a.get("bi_rads") or "",
                "note": a.get("note") or "",
                "frame": a.get("frame") or 0,
                "status": a.get("status") or "draft",
                "created_by": a.get("created_by") or "",
                "reviewed_by": a.get("reviewed_by") or "",
            }
            if link_for_image and link_for_image.get("patient_id"):
                ann_out["patient_id"] = link_for_image["patient_id"]

            if ann_type == "polygon" and a.get("points"):
                pts = a["points"]
                if rows and cols:
                    flat_px: list[float] = []
                    for px, py in pts:
                        flat_px.append(round(px * cols, 2))
                        flat_px.append(round(py * rows, 2))
                    ann_out["segmentation"] = [flat_px]
                    pts_px = [(px * cols, py * rows) for px, py in pts]
                    ann_out["area"] = round(abs(_polygon_area(pts_px)), 2)
                else:
                    flat_n: list[float] = []
                    for px, py in pts:
                        flat_n.append(px)
                        flat_n.append(py)
                    ann_out["segmentation_normalized"] = [flat_n]
                    ann_out["area"] = round(w * h, 2)
                ann_out["points_count"] = len(pts)
            else:
                ann_out["area"] = round(w * h, 2)

            annotations_out.append(ann_out)
            next_ann_id += 1

    categories = [{"id": v, "name": k} for k, v in sorted(label_ix.items(), key=lambda kv: kv[1])]
    return {
        "info": {
            "description": "MAMOGRAF DICOM Viewer annotations export",
            "date_created": datetime.now(timezone.utc).isoformat(),
            "version": "1",
        },
        "categories": categories,
        "images": images,
        "annotations": annotations_out,
    }


@app.get("/api/worklist")
def list_worklist(
    assigned_to: Optional[str] = None,
    status: Optional[str] = None,
    own: bool = False,
    limit: int = 500,
    user: dict = Depends(auth_mod.require_user),
):
    if own:
        assigned_to = user["sub"]
    where = []
    params: list = []
    if assigned_to:
        where.append("w.assigned_to = ?")
        params.append(assigned_to)
    if status:
        where.append("w.status = ?")
        params.append(status)

    sql = (
        "SELECT w.*, p.first_name, p.last_name, "
        "(SELECT COUNT(*) FROM records r WHERE r.patient_id = w.patient_id) AS record_count "
        "FROM worklist w "
        "LEFT JOIN patients p ON p.patient_id = w.patient_id"
    )
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY w.priority DESC, w.study_date DESC, w.id LIMIT ?"
    params.append(limit)

    with db_mod.get_conn() as c:
        rows = [dict(r) for r in c.execute(sql, params).fetchall()]
    return {"items": rows, "count": len(rows)}


class WorklistUpdateBody(BaseModel):
    assigned_to: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


@app.patch("/api/worklist/{wl_id}")
def update_worklist(
    wl_id: int,
    body: WorklistUpdateBody,
    user: dict = Depends(auth_mod.require_user),
):
    role = user.get("role")
    fields = []
    params: list = []
    if body.assigned_to is not None:
        if role not in ("admin", "reviewer"):
            raise HTTPException(403, "only admin/reviewer can assign")
        fields.append("assigned_to = ?")
        params.append(body.assigned_to or None)
    if body.priority is not None:
        if body.priority not in ("low", "normal", "high", "urgent"):
            raise HTTPException(400, "invalid priority")
        fields.append("priority = ?")
        params.append(body.priority)
    if body.status is not None:
        if body.status not in ("pending", "in_progress", "done", "skipped"):
            raise HTTPException(400, "invalid status")
        fields.append("status = ?")
        params.append(body.status)
    if body.notes is not None:
        fields.append("notes = ?")
        params.append(body.notes)
    if not fields:
        raise HTTPException(400, "nothing to update")
    params.append(wl_id)
    with db_mod.get_conn() as c:
        cur = c.execute(f"UPDATE worklist SET {', '.join(fields)} WHERE id = ?", params)
        c.commit()
        if cur.rowcount == 0:
            raise HTTPException(404, "not found")
        row = c.execute("SELECT * FROM worklist WHERE id = ?", (wl_id,)).fetchone()

    if body.assigned_to and role in ("admin", "reviewer"):
        _notify(
            [body.assigned_to],
            kind="assigned",
            title=f"Yangi worklist topshirig'i: {row['patient_name'] or row['patient_id']}",
            body=f"Sana: {row['study_date']} · Modality: {row['modality']}",
            actor=user.get("sub"),
        )
    return {"ok": True, "item": dict(row)}


@app.get("/api/pacs/servers")
def pacs_list_servers(_user: dict = Depends(auth_mod.require_user)):
    with db_mod.get_conn() as c:
        rows = [dict(r) for r in c.execute("SELECT * FROM pacs_servers ORDER BY name").fetchall()]
    return {"servers": rows}


class PacsServerBody(BaseModel):
    name: str
    host: str
    port: int
    aet: str
    calling_aet: Optional[str] = "MAMOGRAF_SCU"
    notes: Optional[str] = None


@app.post("/api/pacs/servers")
def pacs_add_server(
    body: PacsServerBody,
    user: dict = Depends(auth_mod.require_role("admin", "reviewer")),
):
    if not body.name.strip() or not body.host.strip() or not body.aet.strip():
        raise HTTPException(400, "name, host, aet required")
    if not (1 <= body.port <= 65535):
        raise HTTPException(400, "invalid port")
    now = datetime.now(timezone.utc).isoformat()
    with db_mod.get_conn() as c:
        try:
            c.execute(
                "INSERT INTO pacs_servers (name, host, port, aet, calling_aet, notes, added_by, added_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (body.name.strip(), body.host.strip(), body.port,
                 body.aet.strip(), (body.calling_aet or "MAMOGRAF_SCU").strip(),
                 body.notes, user.get("sub"), now),
            )
            c.commit()
            new_id = c.execute("SELECT last_insert_rowid()").fetchone()[0]
            row = c.execute("SELECT * FROM pacs_servers WHERE id=?", (new_id,)).fetchone()
        except Exception as e:
            raise HTTPException(409, f"insert failed: {e}")
    return {"ok": True, "server": dict(row)}


@app.delete("/api/pacs/servers/{srv_id}")
def pacs_delete_server(srv_id: int, _admin: dict = Depends(auth_mod.require_role("admin"))):
    with db_mod.get_conn() as c:
        cur = c.execute("DELETE FROM pacs_servers WHERE id=?", (srv_id,))
        c.commit()
        if cur.rowcount == 0:
            raise HTTPException(404, "not found")
    return {"ok": True}


def _get_pacs_server(srv_id: int) -> dict:
    with db_mod.get_conn() as c:
        row = c.execute("SELECT * FROM pacs_servers WHERE id=?", (srv_id,)).fetchone()
        if not row:
            raise HTTPException(404, "server not found")
    return dict(row)


@app.post("/api/pacs/servers/{srv_id}/echo")
def pacs_server_echo(
    srv_id: int,
    _user: dict = Depends(auth_mod.require_role("admin", "reviewer")),
):
    s = _get_pacs_server(srv_id)
    try:
        return pacs_mod.echo(s["host"], s["port"], s["aet"], s["calling_aet"])
    except RuntimeError as e:
        raise HTTPException(503, str(e))
    except Exception as e:
        raise HTTPException(502, f"echo failed: {e}")


class PacsQueryBody(BaseModel):
    patient_id: Optional[str] = ""
    patient_name: Optional[str] = ""
    modality: Optional[str] = ""
    study_date: Optional[str] = ""


@app.post("/api/pacs/servers/{srv_id}/query")
def pacs_server_query(
    srv_id: int,
    body: PacsQueryBody,
    _user: dict = Depends(auth_mod.require_role("admin", "reviewer")),
):
    s = _get_pacs_server(srv_id)
    try:
        results = pacs_mod.query(
            s["host"], s["port"], s["aet"],
            patient_id=body.patient_id or "",
            patient_name=body.patient_name or "",
            modality=body.modality or "",
            study_date=body.study_date or "",
            calling_aet=s["calling_aet"],
        )
    except RuntimeError as e:
        raise HTTPException(503, str(e))
    except Exception as e:
        raise HTTPException(502, f"query failed: {e}")
    return {"results": results, "count": len(results)}


class PacsToWorklistBody(BaseModel):
    patient_id: str
    patient_name: Optional[str] = None
    sex: Optional[str] = None
    dob: Optional[str] = None
    study_date: Optional[str] = None
    modality: Optional[str] = None


class PacsStoreBody(BaseModel):
    items: list[dict]


@app.post("/api/pacs/servers/{srv_id}/store")
def pacs_server_store(
    srv_id: int,
    body: PacsStoreBody,
    _user: dict = Depends(auth_mod.require_role("admin", "reviewer")),
):
    s = _get_pacs_server(srv_id)
    paths: list[Path] = []
    for it in body.items:
        src = it.get("source")
        ref = it.get("ref")
        if src not in ("upload", "local") or not ref:
            continue
        try:
            paths.append(_resolve_dicom_path(src, ref))
        except HTTPException:
            continue
    if not paths:
        raise HTTPException(400, "no valid items to send")
    try:
        result = pacs_mod.store(s["host"], s["port"], s["aet"], paths,
                                calling_aet=s["calling_aet"])
    except RuntimeError as e:
        raise HTTPException(503, str(e))
    except Exception as e:
        raise HTTPException(502, f"store failed: {e}")
    return {"ok": True, **result, "total": len(paths)}


class PacsFetchBody(BaseModel):
    study_uid: str
    scp_port: Optional[int] = None


_PACS_FETCH_DIR = UPLOAD_DIR


@app.post("/api/pacs/servers/{srv_id}/fetch")
def pacs_server_fetch(
    srv_id: int,
    body: PacsFetchBody,
    _user: dict = Depends(auth_mod.require_role("admin", "reviewer")),
):
    s = _get_pacs_server(srv_id)
    if not body.study_uid.strip():
        raise HTTPException(400, "study_uid kerak")
    scp_port = body.scp_port or int(os.environ.get("PACS_SCP_PORT", "11112"))
    dest = _PACS_FETCH_DIR / "_pacs_inbox"
    dest.mkdir(parents=True, exist_ok=True)
    try:
        result = pacs_mod.fetch(
            s["host"], s["port"], s["aet"],
            study_uid=body.study_uid.strip(),
            dest=dest,
            calling_aet=s["calling_aet"],
            scp_port=scp_port,
        )
    except RuntimeError as e:
        raise HTTPException(503, str(e))
    except Exception as e:
        raise HTTPException(502, f"fetch failed: {e}")

    moved: list[dict] = []
    for fname in result.get("received", []):
        src_p = dest / fname
        if not src_p.exists():
            continue
        new_id = uuid.uuid4().hex
        out_path = UPLOAD_DIR / f"{new_id}.dcm"
        try:
            src_p.rename(out_path)
        except OSError:
            try:
                out_path.write_bytes(src_p.read_bytes())
                src_p.unlink(missing_ok=True)
            except Exception:
                continue
        try:
            ds = pydicom.dcmread(out_path, stop_before_pixels=True, force=True)
            moved.append({
                "id": new_id,
                "original": fname,
                "patient": str(getattr(ds, "PatientName", "")),
                "patient_id": str(getattr(ds, "PatientID", "")),
            })
        except Exception:
            moved.append({"id": new_id, "original": fname})

    return {"ok": True, "received": len(moved), "uploads": moved}


@app.post("/api/pacs/to-worklist")
def pacs_to_worklist(
    body: PacsToWorklistBody,
    _user: dict = Depends(auth_mod.require_role("admin", "reviewer")),
):
    now = datetime.now(timezone.utc).isoformat()
    with db_mod.get_conn() as c:
        c.execute(
            "INSERT OR IGNORE INTO worklist "
            "(patient_id, patient_name, sex, dob, study_date, modality, "
            "priority, status, imported_at) VALUES (?,?,?,?,?,?,?,?,?)",
            (body.patient_id, body.patient_name, body.sex, body.dob,
             body.study_date, body.modality, "normal", "pending", now),
        )
        c.commit()
    return {"ok": True}


@app.delete("/api/worklist/{wl_id}")
def delete_worklist(wl_id: int, _admin: dict = Depends(auth_mod.require_role("admin"))):
    with db_mod.get_conn() as c:
        cur = c.execute("DELETE FROM worklist WHERE id = ?", (wl_id,))
        c.commit()
        if cur.rowcount == 0:
            raise HTTPException(404, "not found")
    return {"ok": True}


def _resolve_dicom_path(source: str, ref: str) -> Path:
    if source == "upload":
        p = UPLOAD_DIR / f"{ref}.dcm"
        if not p.exists():
            raise HTTPException(404, "upload not found")
        return p
    if source == "local":
        return _resolve_local(ref)
    raise HTTPException(400, "invalid source")


@app.get("/api/deidentify/detect")
def deid_detect(source: str, ref: str, _user: dict = Depends(auth_mod.require_user)):
    _validate_source(source)
    _validate_ref(source, ref)
    path = _resolve_dicom_path(source, ref)
    try:
        return deid.detect_phi(path)
    except Exception as e:
        raise HTTPException(500, f"detect failed: {e}")


@app.get("/api/export/dicom-seg")
def export_dicom_seg(
    source: str,
    ref: str,
    _user: dict = Depends(auth_mod.require_user),
):
    _validate_source(source)
    _validate_ref(source, ref)
    src_path = _resolve_dicom_path(source, ref)
    data = annot_store.load(ANNOT_DIR, source, ref)
    annotations = data.get("annotations", []) or []
    if not annotations:
        raise HTTPException(404, "no annotations to export")
    rows = data.get("rows")
    cols = data.get("cols")
    try:
        body = dseg.annotations_to_seg(src_path, annotations, rows=rows, cols=cols)
    except RuntimeError as e:
        raise HTTPException(503, str(e))
    except Exception as e:
        raise HTTPException(500, f"SEG build failed: {e}")
    base = Path(ref).stem or "annotations"
    fname = f"{base}_seg.dcm"
    return StreamingResponse(
        io.BytesIO(body),
        media_type="application/dicom",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )


@app.get("/api/export/dicom-sr")
def export_dicom_sr(
    source: str,
    ref: str,
    user: dict = Depends(auth_mod.require_user),
):
    _validate_source(source)
    _validate_ref(source, ref)
    src_path = _resolve_dicom_path(source, ref)
    data = annot_store.load(ANNOT_DIR, source, ref)
    annotations = data.get("annotations", []) or []
    if not annotations:
        raise HTTPException(404, "no annotations to export")
    rows = data.get("rows")
    cols = data.get("cols")
    try:
        body = dsr.annotations_to_sr(
            src_path, annotations,
            rows=rows, cols=cols,
            author=user.get("sub"),
        )
    except Exception as e:
        raise HTTPException(500, f"SR build failed: {e}")
    base = Path(ref).stem or "annotations"
    fname = f"{base}_sr.dcm"
    return StreamingResponse(
        io.BytesIO(body),
        media_type="application/dicom",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )


@app.get("/api/deidentify/download")
def deid_download(source: str, ref: str, _user: dict = Depends(auth_mod.require_user)):
    _validate_source(source)
    _validate_ref(source, ref)
    path = _resolve_dicom_path(source, ref)
    try:
        body = deid.anonymize_to_bytes(path)
    except Exception as e:
        raise HTTPException(500, f"anonymize failed: {e}")
    base = Path(ref).stem or "anonymous"
    fname = f"{base}_anon.dcm"
    return StreamingResponse(
        io.BytesIO(body),
        media_type="application/dicom",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )


@app.get("/api/stats/overview")
def stats_overview(_admin: dict = Depends(auth_mod.require_role("admin", "reviewer"))):
    cached = _cache_get("stats")
    if cached is not None:
        return cached
    out: dict = {}
    with db_mod.get_conn() as c:
        out["users_total"] = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        out["users_active"] = c.execute(
            "SELECT COUNT(*) FROM users WHERE is_active = 1"
        ).fetchone()[0]
        out["patients_total"] = c.execute("SELECT COUNT(*) FROM patients").fetchone()[0]
        out["records_total"] = c.execute("SELECT COUNT(*) FROM records").fetchone()[0]
        out["dicom_links_total"] = c.execute(
            "SELECT COUNT(*) FROM dicom_patient_links"
        ).fetchone()[0]
        out["history_events"] = c.execute(
            "SELECT COUNT(*) FROM annotation_history"
        ).fetchone()[0]
        out["worklist_total"] = c.execute(
            "SELECT COUNT(*) FROM worklist"
        ).fetchone()[0]

        out["worklist_by_status"] = [
            dict(r) for r in c.execute(
                "SELECT status, COUNT(*) AS n FROM worklist GROUP BY status"
            ).fetchall()
        ]

        out["history_by_action"] = [
            dict(r) for r in c.execute(
                "SELECT action, COUNT(*) AS n FROM annotation_history GROUP BY action ORDER BY n DESC"
            ).fetchall()
        ]

        out["history_per_user"] = [
            dict(r) for r in c.execute(
                "SELECT username, COUNT(*) AS n FROM annotation_history "
                "WHERE username IS NOT NULL GROUP BY username ORDER BY n DESC LIMIT 20"
            ).fetchall()
        ]

        out["history_last_30_days"] = [
            dict(r) for r in c.execute(
                "SELECT substr(ts, 1, 10) AS day, COUNT(*) AS n "
                "FROM annotation_history "
                "WHERE ts >= date('now', '-30 days') "
                "GROUP BY day ORDER BY day"
            ).fetchall()
        ]

    annotation_counts: dict[str, int] = {}
    status_counts: dict[str, int] = {}
    label_counts: dict[str, int] = {}
    ai_origin = 0
    total_anns = 0
    review_durations: list[float] = []

    for entry in annot_store.iter_all(ANNOT_DIR):
        for a in entry.get("annotations", []):
            total_anns += 1
            cb = a.get("created_by") or "?"
            annotation_counts[cb] = annotation_counts.get(cb, 0) + 1
            st = a.get("status", "draft")
            status_counts[st] = status_counts.get(st, 0) + 1
            lbl = a.get("label") or "—"
            label_counts[lbl] = label_counts.get(lbl, 0) + 1
            if a.get("ai_source"):
                ai_origin += 1
            if a.get("created_at") and a.get("reviewed_at"):
                try:
                    t1 = datetime.fromisoformat(a["created_at"].replace("Z", "+00:00"))
                    t2 = datetime.fromisoformat(a["reviewed_at"].replace("Z", "+00:00"))
                    review_durations.append((t2 - t1).total_seconds())
                except Exception:
                    pass

    out["annotations_total"] = total_anns
    out["annotations_by_creator"] = sorted(
        [{"user": k, "n": v} for k, v in annotation_counts.items()],
        key=lambda x: -x["n"],
    )[:20]
    out["annotations_by_status"] = [
        {"status": k, "n": v} for k, v in sorted(status_counts.items())
    ]
    out["annotations_by_label"] = sorted(
        [{"label": k, "n": v} for k, v in label_counts.items()],
        key=lambda x: -x["n"],
    )[:20]
    out["ai_originated_annotations"] = ai_origin
    if review_durations:
        review_durations.sort()
        out["review_seconds"] = {
            "count": len(review_durations),
            "median": round(review_durations[len(review_durations) // 2], 1),
            "p90": round(review_durations[int(len(review_durations) * 0.9)], 1),
            "mean": round(sum(review_durations) / len(review_durations), 1),
        }
    else:
        out["review_seconds"] = None

    _cache_set("stats", out)
    return out


@app.get("/api/annotations/history.csv")
def export_history_csv(
    source: Optional[str] = None,
    ref: Optional[str] = None,
    _user: dict = Depends(auth_mod.require_role("admin", "reviewer")),
):
    sql = "SELECT * FROM annotation_history WHERE 1=1"
    params: list = []
    if source:
        sql += " AND source = ?"
        params.append(source)
    if ref:
        sql += " AND ref = ?"
        params.append(ref)
    sql += " ORDER BY ts DESC, id DESC"

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "ts", "username", "action", "source", "ref", "annotation_id",
        "prev_status", "new_status", "prev_label", "new_label",
        "prev_bi_rads", "new_bi_rads", "note",
    ])

    def _val(d, key):
        if isinstance(d, dict):
            v = d.get(key)
            return v if v is not None else ""
        return ""

    with db_mod.get_conn() as c:
        for row in c.execute(sql, params).fetchall():
            d = dict(row)
            try:
                prev = json.loads(d["prev_snapshot"]) if d.get("prev_snapshot") else {}
            except Exception:
                prev = {}
            try:
                new = json.loads(d["new_snapshot"]) if d.get("new_snapshot") else {}
            except Exception:
                new = {}
            writer.writerow([
                d.get("ts") or "",
                d.get("username") or "",
                d.get("action") or "",
                d.get("source") or "",
                d.get("ref") or "",
                d.get("annotation_id") or "",
                _val(prev, "status"),
                _val(new, "status"),
                _val(prev, "label"),
                _val(new, "label"),
                _val(prev, "bi_rads"),
                _val(new, "bi_rads"),
                _val(new, "note") or _val(new, "review_note"),
            ])

    body = ("﻿" + buf.getvalue()).encode("utf-8")
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = f"audit_log_{stamp}.csv"
    return StreamingResponse(
        io.BytesIO(body),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )


@app.get("/api/export")
def export(format: str = "coco"):
    fmt = format.lower()
    if fmt != "coco":
        raise HTTPException(400, "only format=coco is supported")
    coco = _build_coco()
    body = json.dumps(coco, ensure_ascii=False, indent=2).encode("utf-8")
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = f"annotations_coco_{stamp}.json"
    return StreamingResponse(
        io.BytesIO(body),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )


@app.get("/api/db/stats")
def db_stats():
    with db_mod.get_conn() as c:
        patients = c.execute("SELECT COUNT(*) FROM patients").fetchone()[0]
        records = c.execute("SELECT COUNT(*) FROM records").fetchone()[0]
        date_min = c.execute("SELECT MIN(service_date) FROM records").fetchone()[0]
        date_max = c.execute("SELECT MAX(service_date) FROM records").fetchone()[0]
        by_code = c.execute(
            "SELECT exam_code, COUNT(*) AS n FROM records "
            "WHERE exam_code IS NOT NULL GROUP BY exam_code ORDER BY n DESC"
        ).fetchall()
    return {
        "patients": patients,
        "records": records,
        "service_date_min": date_min,
        "service_date_max": date_max,
        "by_exam_code": [dict(r) for r in by_code],
    }


@app.get("/api/db/search")
def db_search(q: str = "", limit: int = 50):
    q = (q or "").strip()
    if not q:
        return {"results": []}
    pat = f"%{q}%"
    with db_mod.get_conn() as c:
        rows = c.execute(
            "SELECT p.patient_id, p.first_name, p.last_name, p.sex, p.birth_date, "
            "       (SELECT COUNT(*) FROM records r WHERE r.patient_id=p.patient_id) AS record_count, "
            "       (SELECT MAX(service_date) FROM records r WHERE r.patient_id=p.patient_id) AS last_visit "
            "FROM patients p "
            "WHERE p.patient_id LIKE ? OR p.first_name LIKE ? OR p.last_name LIKE ? "
            "ORDER BY p.last_name, p.first_name LIMIT ?",
            (pat, pat, pat, limit),
        ).fetchall()
    return {"results": [dict(r) for r in rows]}


@app.get("/api/db/patient/{patient_id}")
def db_patient(patient_id: str):
    with db_mod.get_conn() as c:
        p = c.execute(
            "SELECT * FROM patients WHERE patient_id = ?", (patient_id,)
        ).fetchone()
        if not p:
            raise HTTPException(404, "patient not found")
        recs = c.execute(
            "SELECT * FROM records WHERE patient_id = ? "
            "ORDER BY service_date DESC, source_row DESC",
            (patient_id,),
        ).fetchall()
    return {"patient": dict(p), "records": [dict(r) for r in recs]}


@app.get("/api/templates")
def list_templates(user: dict = Depends(auth_mod.require_user)):
    with db_mod.get_conn() as c:
        rows = c.execute(
            "SELECT * FROM annotation_templates "
            "WHERE is_shared = 1 OR created_by = ? "
            "ORDER BY created_at DESC",
            (user["sub"],),
        ).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        try:
            payload = json.loads(d.get("payload") or "[]")
        except Exception:
            payload = []
        d["annotation_count"] = len(payload)
        d.pop("payload", None)
        out.append(d)
    return {"templates": out, "count": len(out)}


@app.get("/api/templates/{tpl_id}")
def get_template(tpl_id: int, user: dict = Depends(auth_mod.require_user)):
    with db_mod.get_conn() as c:
        row = c.execute(
            "SELECT * FROM annotation_templates WHERE id = ?", (tpl_id,)
        ).fetchone()
        if not row:
            raise HTTPException(404, "template not found")
    d = dict(row)
    if not d.get("is_shared") and d.get("created_by") != user["sub"]:
        raise HTTPException(403, "private template")
    try:
        d["payload"] = json.loads(d.get("payload") or "[]")
    except Exception:
        d["payload"] = []
    return d


class TemplateBody(BaseModel):
    name: str
    description: Optional[str] = None
    payload: list[dict]
    is_shared: bool = True


@app.post("/api/templates")
def create_template(
    body: TemplateBody,
    user: dict = Depends(auth_mod.require_user),
):
    name = (body.name or "").strip()
    if not name:
        raise HTTPException(400, "name required")
    if not body.payload:
        raise HTTPException(400, "payload empty")

    cleaned = []
    for a in body.payload:
        c = dict(a)
        for k in ("id", "created_by", "created_at", "updated_by", "updated_at",
                  "reviewed_by", "reviewed_at", "review_note", "status"):
            c.pop(k, None)
        cleaned.append(c)

    now = datetime.now(timezone.utc).isoformat()
    with db_mod.get_conn() as c:
        try:
            c.execute(
                "INSERT INTO annotation_templates "
                "(name, description, payload, created_by, created_at, is_shared) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (name, body.description, json.dumps(cleaned, ensure_ascii=False),
                 user["sub"], now, 1 if body.is_shared else 0),
            )
            c.commit()
            new_id = c.execute("SELECT last_insert_rowid()").fetchone()[0]
        except Exception as e:
            raise HTTPException(409, f"insert failed: {e}")
    return {"ok": True, "id": new_id, "name": name, "annotation_count": len(cleaned)}


@app.delete("/api/templates/{tpl_id}")
def delete_template(
    tpl_id: int,
    user: dict = Depends(auth_mod.require_user),
):
    with db_mod.get_conn() as c:
        row = c.execute(
            "SELECT created_by FROM annotation_templates WHERE id = ?", (tpl_id,)
        ).fetchone()
        if not row:
            raise HTTPException(404, "template not found")
        is_admin = user.get("role") == "admin"
        if not is_admin and row[0] != user["sub"]:
            raise HTTPException(403, "can only delete own templates")
        c.execute("DELETE FROM annotation_templates WHERE id = ?", (tpl_id,))
        c.commit()
    return {"ok": True}


@app.get("/api/annotations/overview")
def annotations_overview(
    status: Optional[str] = None,
    created_by: Optional[str] = None,
    own: bool = False,
    limit: int = 200,
    user: dict = Depends(auth_mod.require_user),
):
    if own and not created_by:
        created_by = user["sub"]

    links: dict[tuple, dict] = {}
    with db_mod.get_conn() as c:
        for r in c.execute(
            "SELECT l.source, l.ref, p.patient_id, p.first_name, p.last_name, "
            "p.sex, p.birth_date "
            "FROM dicom_patient_links l "
            "JOIN patients p ON p.patient_id = l.patient_id"
        ).fetchall():
            d = dict(r)
            links[(d.pop("source"), d.pop("ref"))] = d

    grouped: dict[tuple, dict] = {}
    for entry in annot_store.iter_all(ANNOT_DIR):
        src = entry.get("source")
        ref = entry.get("ref")
        if not src or not ref:
            continue
        anns = entry.get("annotations") or []
        if status:
            anns = [a for a in anns if a.get("status", "draft") == status]
        if created_by:
            anns = [a for a in anns if a.get("created_by") == created_by]
        if not anns:
            continue

        key = (src, ref)
        statuses: dict[str, int] = {}
        labels: dict[str, int] = {}
        creators: set = set()
        latest = ""
        for a in anns:
            s = a.get("status", "draft")
            statuses[s] = statuses.get(s, 0) + 1
            lb = a.get("label") or "—"
            labels[lb] = labels.get(lb, 0) + 1
            if a.get("created_by"):
                creators.add(a["created_by"])
            t = a.get("updated_at") or a.get("created_at") or ""
            if t > latest:
                latest = t

        grouped[key] = {
            "source": src,
            "ref": ref,
            "annotation_count": len(anns),
            "by_status": statuses,
            "by_label": labels,
            "creators": sorted(creators),
            "latest_ts": latest,
            "patient": links.get(key),
        }

    items = sorted(grouped.values(), key=lambda x: x.get("latest_ts") or "", reverse=True)
    return {"items": items[:limit], "count": min(len(items), limit), "total": len(items)}


@app.get("/api/db/patient/{patient_id}/overview")
def db_patient_overview(patient_id: str):
    with db_mod.get_conn() as c:
        p = c.execute(
            "SELECT * FROM patients WHERE patient_id = ?", (patient_id,)
        ).fetchone()
        if not p:
            raise HTTPException(404, "patient not found")
        records = [dict(r) for r in c.execute(
            "SELECT * FROM records WHERE patient_id = ? "
            "ORDER BY service_date DESC, source_row DESC", (patient_id,),
        ).fetchall()]
        worklist = [dict(r) for r in c.execute(
            "SELECT * FROM worklist WHERE patient_id = ? "
            "ORDER BY study_date DESC", (patient_id,),
        ).fetchall()]
        links = [dict(r) for r in c.execute(
            "SELECT source, ref, confidence, confirmed_at FROM dicom_patient_links "
            "WHERE patient_id = ? ORDER BY confirmed_at DESC", (patient_id,),
        ).fetchall()]

    dicoms = []
    for link in links:
        ann_count = annot_store.count(ANNOT_DIR, link["source"], link["ref"])
        ann_data = annot_store.load(ANNOT_DIR, link["source"], link["ref"])
        statuses: dict[str, int] = {}
        for a in ann_data.get("annotations", []):
            s = a.get("status", "draft")
            statuses[s] = statuses.get(s, 0) + 1
        dicoms.append({
            "source": link["source"],
            "ref": link["ref"],
            "confidence": link["confidence"],
            "confirmed_at": link["confirmed_at"],
            "annotation_count": ann_count,
            "annotation_statuses": statuses,
        })

    timeline: list[dict] = []
    for r in records:
        if r.get("service_date"):
            timeline.append({
                "kind": "record",
                "ts": r["service_date"],
                "exam_code": r.get("exam_code"),
                "exam_name": r.get("exam_name"),
                "diagnosis": r.get("diagnosis"),
                "record_id": r["id"],
            })
    for w in worklist:
        if w.get("study_date"):
            timeline.append({
                "kind": "worklist",
                "ts": w["study_date"],
                "modality": w.get("modality"),
                "status": w.get("status"),
                "assigned_to": w.get("assigned_to"),
                "wl_id": w["id"],
            })
    for d in dicoms:
        ts = (d.get("confirmed_at") or "")[:10]
        timeline.append({
            "kind": "dicom",
            "ts": ts,
            "source": d["source"],
            "ref": d["ref"],
            "annotation_count": d["annotation_count"],
            "annotation_statuses": d["annotation_statuses"],
        })
    timeline.sort(key=lambda x: x.get("ts") or "", reverse=True)

    return {
        "patient": dict(p),
        "records": records,
        "worklist": worklist,
        "dicoms": dicoms,
        "timeline": timeline,
    }


@app.get("/api/db/record/{record_id}")
def db_record(record_id: int):
    with db_mod.get_conn() as c:
        r = c.execute("SELECT * FROM records WHERE id = ?", (record_id,)).fetchone()
        if not r:
            raise HTTPException(404, "record not found")
    return dict(r)


class LinkBody(BaseModel):
    source: str
    ref: str
    patient_id: str
    confidence: Optional[int] = None
    note: Optional[str] = None


@app.get("/api/db/link")
def db_get_link(source: str, ref: str):
    _validate_source(source)
    _validate_ref(source, ref)
    with db_mod.get_conn() as c:
        row = c.execute(
            "SELECT * FROM dicom_patient_links WHERE source = ? AND ref = ?",
            (source, ref),
        ).fetchone()
        if not row:
            return {"linked": False}
        link = dict(row)
        patient = c.execute(
            "SELECT * FROM patients WHERE patient_id = ?", (link["patient_id"],)
        ).fetchone()
        record_count = c.execute(
            "SELECT COUNT(*) FROM records WHERE patient_id = ?",
            (link["patient_id"],),
        ).fetchone()[0]
    return {
        "linked": True,
        "link": link,
        "patient": dict(patient) if patient else None,
        "record_count": record_count,
    }


@app.put("/api/db/link")
def db_set_link(body: LinkBody, _user: dict = Depends(auth_mod.require_user)):
    _validate_source(body.source)
    _validate_ref(body.source, body.ref)
    with db_mod.get_conn() as c:
        if not c.execute(
            "SELECT 1 FROM patients WHERE patient_id = ?", (body.patient_id,)
        ).fetchone():
            raise HTTPException(404, "patient not found")
        now = datetime.now(timezone.utc).isoformat()
        c.execute(
            "INSERT OR REPLACE INTO dicom_patient_links "
            "(source, ref, patient_id, confidence, note, confirmed_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (body.source, body.ref, body.patient_id,
             body.confidence, body.note, now),
        )
        c.commit()
    return {"ok": True, "confirmed_at": now}


@app.get("/api/db/links")
def db_list_links(
    q: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = 200,
):
    where = []
    params: list = []
    if source:
        if source not in ("upload", "local"):
            raise HTTPException(400, "invalid source")
        where.append("l.source = ?")
        params.append(source)
    if q:
        q = q.strip()
        if q:
            pat = f"%{q}%"
            where.append(
                "(p.first_name LIKE ? OR p.last_name LIKE ? OR p.patient_id LIKE ? OR l.ref LIKE ?)"
            )
            params.extend([pat, pat, pat, pat])

    sql = (
        "SELECT l.source, l.ref, l.confidence, l.confirmed_at, "
        "p.patient_id, p.first_name, p.last_name, p.sex, p.birth_date, "
        "(SELECT COUNT(*) FROM records r WHERE r.patient_id = l.patient_id) AS record_count, "
        "(SELECT MAX(r.service_date) FROM records r WHERE r.patient_id = l.patient_id) AS last_visit "
        "FROM dicom_patient_links l "
        "JOIN patients p ON p.patient_id = l.patient_id"
    )
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY l.confirmed_at DESC LIMIT ?"
    params.append(limit)

    with db_mod.get_conn() as c:
        rows = [dict(r) for r in c.execute(sql, params).fetchall()]

    for r in rows:
        r["annotation_count"] = annot_store.count(ANNOT_DIR, r["source"], r["ref"])

    return {"links": rows, "count": len(rows)}


@app.delete("/api/db/link")
def db_delete_link(source: str, ref: str, _user: dict = Depends(auth_mod.require_user)):
    _validate_source(source)
    if not ref:
        raise HTTPException(400, "missing ref")
    with db_mod.get_conn() as c:
        c.execute(
            "DELETE FROM dicom_patient_links WHERE source = ? AND ref = ?",
            (source, ref),
        )
        c.commit()
    return {"ok": True}


def _parse_dicom_name(name: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    if not name:
        return (None, None)
    s = str(name).replace("^", " ").strip()
    parts = re.split(r"\s+", s)
    parts = [p for p in parts if p]
    if not parts:
        return (None, None)
    if len(parts) == 1:
        return (parts[0].upper(), None)
    return (parts[0].upper(), " ".join(parts[1:]).upper())


def _norm_dicom_dob(dob: Optional[str]) -> Optional[str]:
    if not dob:
        return None
    s = str(dob).strip()
    if re.match(r"^\d{8}$", s):
        return f"{s[:4]}-{s[4:6]}-{s[6:8]}"
    m = re.match(r"^(\d{4}-\d{2}-\d{2})", s)
    if m:
        return m.group(1)
    return None


@app.get("/api/db/match")
def db_match(
    patient_id: Optional[str] = None,
    name: Optional[str] = None,
    birth_date: Optional[str] = None,
    limit: int = 10,
):
    last, first = _parse_dicom_name(name)
    dob = _norm_dicom_dob(birth_date)

    candidates: dict[str, dict] = {}

    def add(row, score: int, reason: str):
        pid = row["patient_id"]
        cur = candidates.get(pid)
        if cur is None:
            candidates[pid] = {
                "patient": dict(row),
                "score": score,
                "reasons": [reason],
            }
            return
        if reason not in cur["reasons"]:
            cur["reasons"].append(reason)
        if score > cur["score"]:
            cur["score"] = score

    with db_mod.get_conn() as c:
        if patient_id:
            row = c.execute(
                "SELECT * FROM patients WHERE patient_id = ?", (patient_id,)
            ).fetchone()
            if row:
                add(row, 100, "patient_id exact")

        if last and first and dob:
            for row in c.execute(
                "SELECT * FROM patients WHERE last_name = ? AND first_name = ? AND birth_date = ?",
                (last, first, dob),
            ).fetchall():
                add(row, 95, "last+first+dob")

        if last and first:
            for row in c.execute(
                "SELECT * FROM patients WHERE last_name = ? AND first_name = ?",
                (last, first),
            ).fetchall():
                add(row, 80, "last+first")

        if last and dob:
            for row in c.execute(
                "SELECT * FROM patients WHERE last_name = ? AND birth_date = ?",
                (last, dob),
            ).fetchall():
                add(row, 70, "last+dob")

        if first and dob:
            for row in c.execute(
                "SELECT * FROM patients WHERE first_name = ? AND birth_date = ?",
                (first, dob),
            ).fetchall():
                add(row, 60, "first+dob")

        if last:
            for row in c.execute(
                "SELECT * FROM patients WHERE last_name = ? LIMIT 30", (last,)
            ).fetchall():
                add(row, 30, "last only")

        ranked = sorted(candidates.values(), key=lambda v: -v["score"])[:limit]

        for cand in ranked:
            pid = cand["patient"]["patient_id"]
            cand["record_count"] = c.execute(
                "SELECT COUNT(*) FROM records WHERE patient_id = ?", (pid,)
            ).fetchone()[0]
            cand["last_visit"] = c.execute(
                "SELECT MAX(service_date) FROM records WHERE patient_id = ?", (pid,)
            ).fetchone()[0]

    return {
        "input": {
            "patient_id": patient_id,
            "name": name,
            "birth_date": birth_date,
            "parsed": {"last_name": last, "first_name": first, "dob": dob},
        },
        "candidates": ranked,
    }


@app.get("/api/inference/status")
def inference_status():
    ok, err = inf.is_available()
    info = inf.device_info()
    info["available"] = ok
    info["error"] = err if not ok else None
    info["models_dir"] = str(inf.MODELS_DIR)
    info["models"] = inf.list_models()
    return info


@app.get("/api/inference/models")
def inference_models():
    return {"models": inf.list_models(), "models_dir": str(inf.MODELS_DIR)}


class InferenceBody(BaseModel):
    source: str
    ref: str
    model: str
    frame: int = 0
    conf: float = 0.25
    iou: float = 0.5
    imgsz: int = 1024
    wc: Optional[float] = None
    ww: Optional[float] = None


class BatchInferenceBody(BaseModel):
    items: list[dict]
    model: str
    conf: float = 0.25
    iou: float = 0.5
    imgsz: int = 1024
    auto_save: bool = False


@app.post("/api/inference/batch")
@limiter.limit("5/minute")
async def inference_batch(
    request: Request,
    body: BatchInferenceBody,
    user: dict = Depends(auth_mod.require_user),
):
    if not body.items:
        raise HTTPException(400, "items empty")
    if len(body.items) > 50:
        raise HTTPException(400, "too many items (max 50 per batch)")

    results = []
    username = user.get("sub") or ""
    now = datetime.now(timezone.utc).isoformat()

    for it in body.items:
        src = it.get("source")
        ref = it.get("ref")
        if src not in ("upload", "local") or not ref:
            results.append({"source": src, "ref": ref, "ok": False, "error": "invalid item"})
            continue
        try:
            path = _resolve_dicom_path(src, ref)
            png_bytes = render_frame_png(path, frame=0, max_dim=2048)
            inf_res = inf.infer_png(
                png_bytes, model_name=body.model,
                conf=body.conf, iou=body.iou, imgsz=body.imgsz,
            )
        except Exception as e:
            results.append({"source": src, "ref": ref, "ok": False, "error": str(e)})
            continue

        if body.auto_save and inf_res.get("detections"):
            existing = annot_store.load(ANNOT_DIR, src, ref)
            new_anns = list(existing.get("annotations") or [])
            for d in inf_res["detections"]:
                lbl = d.get("label") or "mass"
                new_anns.append({
                    "id": uuid.uuid4().hex,
                    "type": "bbox",
                    "label": lbl,
                    "bi_rads": "",
                    "frame": 0,
                    "bbox": d["bbox"],
                    "note": f"AI: {lbl} {d['confidence']*100:.1f}%",
                    "ai_source": {
                        "label": lbl,
                        "confidence": d["confidence"],
                        "class_id": d.get("class_id"),
                    },
                    "status": "draft",
                    "created_by": username,
                    "created_at": now,
                    "updated_by": username,
                    "updated_at": now,
                })
            annot_store.save(ANNOT_DIR, src, ref, {
                "source": src, "ref": ref,
                "rows": existing.get("rows"), "cols": existing.get("cols"),
                "annotations": new_anns,
            })
        results.append({
            "source": src, "ref": ref, "ok": True,
            "detections": len(inf_res.get("detections", [])),
            "saved": body.auto_save,
        })
    return {"ok": True, "results": results, "count": len(results)}


@app.post("/api/inference/run")
@limiter.limit("20/minute")
def inference_run(request: Request, body: InferenceBody, _user: dict = Depends(auth_mod.require_user)):
    _validate_source(body.source)
    _validate_ref(body.source, body.ref)

    if body.source == "upload":
        path = UPLOAD_DIR / f"{body.ref}.dcm"
    else:
        path = _resolve_local(body.ref)

    try:
        png_bytes = render_frame_png(
            path, frame=body.frame, wc=body.wc, ww=body.ww, max_dim=2048
        )
    except Exception as e:
        raise HTTPException(500, f"render failed: {e}")

    try:
        result = inf.infer_png(
            png_bytes,
            model_name=body.model,
            conf=body.conf,
            iou=body.iou,
            imgsz=body.imgsz,
        )
    except FileNotFoundError as e:
        raise HTTPException(404, str(e))
    except RuntimeError as e:
        raise HTTPException(503, str(e))
    except Exception as e:
        raise HTTPException(500, f"inference failed: {e}")
    return result


@app.websocket("/ws/dicom")
async def ws_dicom(websocket: WebSocket, source: str, ref: str, token: str = ""):
    if not token:
        await websocket.close(code=1008)
        return
    try:
        payload = auth_mod.decode_token(token)
    except HTTPException:
        await websocket.close(code=1008)
        return

    if source not in ("upload", "local") or not ref:
        await websocket.close(code=1008)
        return

    username = payload.get("sub", "?")
    await websocket.accept()
    await ws_mod.rooms.join(source, ref, websocket, username)
    try:
        while True:
            data = await websocket.receive_json()
            kind = data.get("type")
            if kind == "ping":
                await websocket.send_json({"type": "pong"})
            elif kind == "cursor":
                await ws_mod.rooms.broadcast(source, ref, {
                    "type": "cursor",
                    "user": username,
                    "x": data.get("x"),
                    "y": data.get("y"),
                }, exclude_ws=websocket)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        await ws_mod.rooms.leave(source, ref, websocket, username)


# ---------------------------------------------------------------------------
# Research / radiologist verification (review_decisions table)
# ---------------------------------------------------------------------------


class ReviewDecideBody(BaseModel):
    status: str                      # "accepted" | "edited" | "rejected"
    final_bboxes: list[dict] | None = None    # YOLO-ready bboxes the radiologist confirmed
    comments: str | None = None


def _row_to_review_dict(row, include_pseudo: bool = False, include_final: bool = False) -> dict:
    out = {
        "id": row["id"],
        "sop_uid": row["sop_uid"],
        "view": row["view"] or "",
        "laterality": row["laterality"] or "",
        "status": row["status"],
        "reviewer": row["reviewer"] or "",
        "decided_at": row["decided_at"] or "",
        "imported_at": row["imported_at"],
        "source_queue": row["source_queue"] or "",
        "comments": row["comments"] or "",
        "n_pseudo": 0,
        "n_final": 0,
        "has_preview": bool(row["preprocessed_png_path"]) and Path(row["preprocessed_png_path"]).exists(),
    }
    try:
        pseudo = json.loads(row["pseudo_bboxes_json"] or "[]")
        out["n_pseudo"] = len(pseudo)
        if include_pseudo:
            out["pseudo_bboxes"] = pseudo
            out["findings"] = json.loads(row["findings_json"] or "{}")
    except Exception:
        pass
    if row["final_bboxes_json"]:
        try:
            final = json.loads(row["final_bboxes_json"])
            out["n_final"] = len(final)
            if include_final:
                out["final_bboxes"] = final
        except Exception:
            pass
    return out


@app.get("/api/research/review/queue")
def research_review_queue(
    status: str = Query("pending", pattern=r"^(pending|accepted|edited|rejected|all)$"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    _user: dict = Depends(auth_mod.require_role("admin", "reviewer")),
):
    sql = "SELECT * FROM review_decisions"
    params: list = []
    if status != "all":
        sql += " WHERE status = ?"
        params.append(status)
    sql += " ORDER BY (status = 'pending') DESC, imported_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    with db_mod.get_conn() as c:
        rows = c.execute(sql, params).fetchall()
        counts = c.execute(
            "SELECT status, COUNT(*) AS n FROM review_decisions GROUP BY status"
        ).fetchall()
    return {
        "items": [_row_to_review_dict(r) for r in rows],
        "counts": {r["status"]: r["n"] for r in counts},
        "limit": limit,
        "offset": offset,
    }


@app.get("/api/research/review/export")
def research_review_export(
    include_status: str = Query("accepted,edited", description="Comma-separated statuses to export"),
    _user: dict = Depends(auth_mod.require_role("admin", "reviewer")),
):
    """Emit a JSONL bundle of gold-label review_decisions ready to be turned
    into a YOLO dataset by `app.research.coco_to_yolo` or piped into
    `app.research.train_tillnet --texts <reports>`.
    """
    statuses = [s.strip() for s in include_status.split(",") if s.strip()]
    if not statuses:
        raise HTTPException(status_code=400, detail="no statuses requested")
    placeholders = ",".join("?" * len(statuses))
    with db_mod.get_conn() as c:
        rows = c.execute(
            f"SELECT * FROM review_decisions WHERE status IN ({placeholders}) "
            f"ORDER BY decided_at",
            statuses,
        ).fetchall()

    def _stream():
        for r in rows:
            try:
                final = json.loads(r["final_bboxes_json"] or "[]")
            except Exception:
                final = []
            yield json.dumps({
                "sop_uid": r["sop_uid"],
                "dicom_path": r["dicom_path"] or "",
                "preprocessed_png": r["preprocessed_png_path"] or "",
                "view": r["view"] or "",
                "laterality": r["laterality"] or "",
                "status": r["status"],
                "reviewer": r["reviewer"] or "",
                "decided_at": r["decided_at"] or "",
                "bboxes": final,
            }, ensure_ascii=False) + "\n"

    return StreamingResponse(
        _stream(),
        media_type="application/x-ndjson",
        headers={"Content-Disposition": 'attachment; filename="gold_labels.jsonl"'},
    )


@app.get("/api/research/review/{review_id}")
def research_review_get(
    review_id: int,
    _user: dict = Depends(auth_mod.require_role("admin", "reviewer")),
):
    with db_mod.get_conn() as c:
        row = c.execute(
            "SELECT * FROM review_decisions WHERE id = ?", (review_id,)
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="review item not found")
    return _row_to_review_dict(row, include_pseudo=True, include_final=True)


@app.get("/api/research/review/{review_id}/preview")
def research_review_preview(
    review_id: int,
    _user: dict = Depends(auth_mod.require_role("admin", "reviewer")),
):
    with db_mod.get_conn() as c:
        row = c.execute(
            "SELECT preprocessed_png_path FROM review_decisions WHERE id = ?", (review_id,)
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="review item not found")
    p = (row["preprocessed_png_path"] or "").strip()
    if not p:
        raise HTTPException(status_code=404, detail="no preview available")
    f = Path(p)
    if not f.exists() or not f.is_file():
        raise HTTPException(status_code=404, detail="preview file missing")
    return FileResponse(str(f), media_type="image/png")


@app.post("/api/research/review/{review_id}/decide")
def research_review_decide(
    review_id: int,
    body: ReviewDecideBody,
    user: dict = Depends(auth_mod.require_role("admin", "reviewer")),
):
    if body.status not in ("accepted", "edited", "rejected"):
        raise HTTPException(status_code=400, detail="invalid status")
    final = body.final_bboxes or []
    if body.status == "rejected":
        final = []                                         # ignore any sent boxes on reject
    final_json = json.dumps(final, ensure_ascii=False)
    now = datetime.now(timezone.utc).isoformat()
    reviewer = user.get("sub") or ""
    with db_mod.get_conn() as c:
        cur = c.execute(
            "UPDATE review_decisions "
            "SET status = ?, final_bboxes_json = ?, reviewer = ?, decided_at = ?, comments = ? "
            "WHERE id = ?",
            (body.status, final_json, reviewer, now, body.comments or "", review_id),
        )
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="review item not found")
        c.commit()
    return {"id": review_id, "status": body.status, "n_final": len(final), "decided_at": now}


app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
