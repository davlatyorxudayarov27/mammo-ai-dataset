from __future__ import annotations

import csv
import io
import json
import os
import re
import subprocess
import sys
import threading
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import pydicom
from fastapi import BackgroundTasks, Depends, FastAPI, File, HTTPException, Query, Request, UploadFile, WebSocket, WebSocketDisconnect
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
from . import exporters as exporters
from . import radiomics as radiomics_mod
from . import inference as inf
from . import pacs as pacs_mod
from . import ws as ws_mod
from .dicom_utils import (
    NoPixelDataError, auto_window, extract_sr_content, load_frame_array, quick_summary,
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

# (A1) Avtomatik AI inference upload paytida — radiolog ekranga kelganda
# pseudo-bbox'lar allaqachon tayyor. Sukut bo'yicha O'CHIQ (opt-in):
# AUTO_INFER_ON_UPLOAD=1 ko'rsatilganda yoqiladi.
AUTO_INFER_ON_UPLOAD = os.environ.get("AUTO_INFER_ON_UPLOAD", "0").strip().lower() in (
    "1", "true", "yes", "on"
)
AUTO_INFER_MODEL = os.environ.get("AUTO_INFER_MODEL", "").strip()
AUTO_INFER_IOU = float(os.environ.get("AUTO_INFER_IOU", "0.5") or "0.5")
AUTO_INFER_IMGSZ = int(os.environ.get("AUTO_INFER_IMGSZ", "1024") or "1024")

# (A2) Ishonch 3-zona klassifikatsiyasi: yashil (avto-qabul) / sariq (ko'rib chiqish) / qizil (shubhali).
# Default chegaralar:
#   conf ≥ 0.85         → auto_accept (yashil, status=ai_accepted)
#   0.40 ≤ conf < 0.85  → review      (sariq, status=ai_review)
#   0.20 ≤ conf < 0.40  → suspect     (qizil pulsatsiya, status=ai_suspect)
#   conf < 0.20         → tashlanadi (saqlanmaydi)
AUTO_INFER_ACCEPT_THR = float(os.environ.get("AUTO_INFER_ACCEPT_THR", "0.85") or "0.85")
AUTO_INFER_REVIEW_THR = float(os.environ.get("AUTO_INFER_REVIEW_THR", "0.40") or "0.40")
AUTO_INFER_SUSPECT_THR = float(os.environ.get("AUTO_INFER_SUSPECT_THR", "0.20") or "0.20")
# Inference uchun YOLO conf chegarasi — eng past zona chegarasi (suspect_thr)
AUTO_INFER_CONF = AUTO_INFER_SUSPECT_THR


def _classify_confidence_zone(conf: float) -> tuple[str, str]:
    """Conf qiymatidan (zone_name, status) qaytaradi.
    Agar conf < suspect_thr bo'lsa, ('drop', '') qaytariladi — tashlanadi."""
    if conf >= AUTO_INFER_ACCEPT_THR:
        return ("auto_accept", "ai_accepted")
    if conf >= AUTO_INFER_REVIEW_THR:
        return ("review", "ai_review")
    if conf >= AUTO_INFER_SUSPECT_THR:
        return ("suspect", "ai_suspect")
    return ("drop", "")


def _auto_infer_uploaded(file_id: str, dicom_path: Path, rows: int, cols: int) -> dict:
    """Yuklangan DICOM uchun AI inference + pseudo-annotation saqlash.
    Hech qachon istisno qaytarmaydi — upload muvaffaqiyatsiz bo'lmasligi uchun."""
    info: dict = {"ran": False, "detections": 0, "model": None, "error": None}
    if not (rows and cols):
        info["error"] = "no pixels"
        return info
    try:
        models = inf.list_models()
        if not models:
            info["error"] = "no models available"
            return info
        model_name = AUTO_INFER_MODEL or models[0]["name"]
        try:
            png_bytes = render_frame_png(dicom_path, frame=0, max_dim=2048)
        except Exception as e:
            info["error"] = f"render failed: {e}"
            return info
        try:
            res = inf.infer_png(
                png_bytes, model_name=model_name,
                conf=AUTO_INFER_CONF, iou=AUTO_INFER_IOU,
                imgsz=AUTO_INFER_IMGSZ, tta=False,
            )
        except Exception as e:
            info["error"] = f"inference failed: {e}"
            info["model"] = model_name
            return info
        detections = res.get("detections", []) or []
        now = datetime.now(timezone.utc).isoformat()
        anns = []
        zone_counts = {"auto_accept": 0, "review": 0, "suspect": 0, "drop": 0}
        for d in detections:
            conf = float(d.get("confidence", 0.0))
            zone, status = _classify_confidence_zone(conf)
            zone_counts[zone] = zone_counts.get(zone, 0) + 1
            if zone == "drop":
                continue
            anns.append({
                "id": "ai" + uuid.uuid4().hex[:11],
                "type": "bbox",
                "label": d.get("label", "?"),
                "bi_rads": "",
                "note": f"AI: conf={conf:.2f} ({zone})",
                "frame": 0,
                "bbox": d.get("bbox", [0, 0, 0, 0]),
                "confidence": conf,
                "zone": zone,
                "created_at": now,
                "updated_at": now,
                "created_by": f"ai:{model_name}",
                "status": status,
            })
        if anns:
            payload = {
                "rows": rows,
                "cols": cols,
                "annotations": anns,
            }
            annot_store.save(ANNOT_DIR, "upload", file_id, payload)
        info.update({
            "ran": True,
            "detections": len(detections),
            "kept": len(anns),
            "zones": zone_counts,
            "model": model_name,
            "thresholds": {
                "accept": AUTO_INFER_ACCEPT_THR,
                "review": AUTO_INFER_REVIEW_THR,
                "suspect": AUTO_INFER_SUSPECT_THR,
            },
        })
        return info
    except Exception as e:
        info["error"] = f"{type(e).__name__}: {e}"
        return info

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
    background_tasks: BackgroundTasks,
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

        # (A1) Avtomatik AI inference — endi BACKGROUND task (upload bloklanmaydi).
        # Foydalanuvchi DICOM'ni darhol ko'radi; bbox'lar 10-20 sek ichida paydo bo'ladi.
        if AUTO_INFER_ON_UPLOAD and rows and cols:
            background_tasks.add_task(_auto_infer_uploaded, file_id, out, rows, cols)
            info["ai_inference"] = {"queued": True, "model": AUTO_INFER_MODEL or "default"}
            info["annotation_count"] = 0  # hali fonda hisoblanmoqda

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


# --------------------------------------------------------------------------- #
# Annotation bo'lgan fayllarni boshqa papkaga eksport (copy)                     #
# --------------------------------------------------------------------------- #
class ExportAnnotatedBody(BaseModel):
    destination: str                          # mutlaq yo'l
    source_kind: str = "upload"                # "upload" | "local" | "both"
    require_annotations: bool = True           # eng kamida 1 ta annotation kerakmi
    require_human: bool = False                # AI emas, qo'lda yaratilganlar
    statuses: Optional[list[str]] = None       # status filtri
    include_annotation_json: bool = True       # JSON sidecar ham
    organize_by: str = "flat"                  # "flat" | "by_patient" | "by_status"
    overwrite: bool = False


def _filter_annotations(anns: list[dict], body: ExportAnnotatedBody) -> bool:
    """Berilgan annotation ro'yxati filtrlardan o'tadimi."""
    if not anns:
        return not body.require_annotations
    if body.require_human:
        if not any(not str(a.get("created_by", "")).startswith("ai:") for a in anns):
            return False
    if body.statuses:
        if not any(a.get("status") in body.statuses for a in anns):
            return False
    return True


@app.post("/api/export/annotated")
def export_annotated(
    body: ExportAnnotatedBody,
    _user: dict = Depends(auth_mod.require_user),
):
    """Annotation bor (yoki belgilangan status'dagi) fayllarni boshqa papkaga ko'chiradi.
    Asl fayllar joyida qoladi (copy). Annotation JSON sidecar ixtiyoriy."""
    import shutil

    dest_str = (body.destination or "").strip()
    if not dest_str:
        raise HTTPException(400, "destination yo'l bo'sh")
    dest = Path(dest_str)
    # Xavfsizlik: sistem papkalariga yozishga ruxsat bermaymiz
    forbidden_starts = [r"C:\Windows", r"C:\Program Files", "/etc", "/usr", "/bin", "/sbin", "/sys", "/proc"]
    if any(str(dest).lower().startswith(x.lower()) for x in forbidden_starts):
        raise HTTPException(400, f"Bu papkaga yozish taqiqlangan: {dest}")
    try:
        dest.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        raise HTTPException(400, f"Papka yaratib bo'lmadi: {e}")
    if not dest.is_dir():
        raise HTTPException(400, "destination papka emas")

    copied: list[dict] = []
    skipped: list[dict] = []
    no_anns: list[str] = []

    def process(file_id: str, dcm_path: Path, source: str):
        ann_path = annot_store._annot_path(ANNOT_DIR, source, file_id)
        anns: list[dict] = []
        if ann_path.exists():
            try:
                data = json.loads(ann_path.read_text(encoding="utf-8"))
                anns = data.get("annotations") or []
            except Exception:
                anns = []
        if not _filter_annotations(anns, body):
            if body.require_annotations:
                no_anns.append(file_id)
            return

        # Maqsad katalogni aniqlash
        target_dir = dest
        if body.organize_by == "by_patient":
            try:
                ds = pydicom.dcmread(str(dcm_path), stop_before_pixels=True, force=True)
                pid = str(getattr(ds, "PatientID", "") or "").strip() or "ANON"
                pid = re.sub(r"[^A-Za-z0-9_-]+", "_", pid)
                target_dir = dest / pid
            except Exception:
                target_dir = dest / "UNKNOWN"
        elif body.organize_by == "by_status":
            # Birinchi annotationning statusiga ko'ra
            st = (anns[0].get("status") if anns else None) or "no_status"
            st = re.sub(r"[^A-Za-z0-9_-]+", "_", str(st))
            target_dir = dest / st
        target_dir.mkdir(parents=True, exist_ok=True)

        target = target_dir / f"{file_id}.dcm"
        if target.exists() and not body.overwrite:
            skipped.append({"id": file_id, "reason": "exists"})
            return
        try:
            shutil.copy2(dcm_path, target)
        except Exception as e:
            skipped.append({"id": file_id, "reason": f"copy_failed: {e}"})
            return
        ann_copied = False
        if body.include_annotation_json and ann_path.exists():
            try:
                shutil.copy2(ann_path, target_dir / ann_path.name)
                ann_copied = True
            except Exception:
                pass
        copied.append({
            "id": file_id, "target": str(target),
            "annotations": len(anns), "annotation_json": ann_copied,
        })

    # Upload'lar
    if body.source_kind in ("upload", "both"):
        for dcm in sorted(UPLOAD_DIR.glob("*.dcm")):
            process(dcm.stem, dcm, "upload")

    # Local DICOM'lar — annotation papkasiga "local__" prefix bilan
    if body.source_kind in ("local", "both"):
        for ann_path in sorted(ANNOT_DIR.glob("local__*.json")):
            file_id = ann_path.stem.replace("local__", "", 1)
            # Lokal yo'lni qayta tiklab bo'lmaydi (annotatsiya nomida hash) —
            # bu rejim faqat upload uchun ishonchli; lokal uchun keyin yaxshilanadi.
            no_anns.append(f"local:{file_id} (lokal eksport hozircha qo'llab-quvvatlanmaydi)")

    return {
        "destination": str(dest),
        "copied_count": len(copied),
        "skipped_count": len(skipped),
        "no_annotations_count": len(no_anns),
        "copied": copied[:200],
        "skipped": skipped[:50],
    }


# --------------------------------------------------------------------------- #
# Training dataset tayyorlash — YOLO formati (Ultralytics)                     #
# --------------------------------------------------------------------------- #
# Training run holatlarini xotirada saqlash (process'lar ro'yxati)
TRAINING_RUNS: dict = {}  # run_id -> {status, log_path, started_at, finished_at, dest_path, last_metrics}

def _training_log_path(run_id: str) -> Path:
    d = BASE_DIR / "training_runs"
    d.mkdir(exist_ok=True)
    return d / f"{run_id}.log"


# Ishlab turgan training subprocess'lar: run_id -> subprocess.Popen
TRAIN_PROCS: dict = {}


def _kill_proc_tree(pid: int) -> None:
    """Jarayon va uning bolalarini majburan to'xtatish (Windows: taskkill /T)."""
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(pid), "/T", "/F"],
            capture_output=True, text=True,
        )
    else:
        import signal as _sig
        try:
            os.killpg(os.getpgid(pid), _sig.SIGTERM)
        except Exception:
            try:
                os.kill(pid, _sig.SIGTERM)
            except Exception:
                pass


def _monitor_training(run_id: str, proc: "subprocess.Popen", logf) -> None:
    """Subprocess tugashini kutadi va status.json'dan yakuniy holatni o'qiydi."""
    rc = proc.wait()
    try:
        logf.close()
    except Exception:
        pass
    state = TRAINING_RUNS.get(run_id, {})
    project_dir = Path(state.get("project_dir") or (BASE_DIR / "training_runs" / run_id))
    final: dict = {}
    status_json = project_dir / "status.json"
    if status_json.exists():
        try:
            final = json.loads(status_json.read_text(encoding="utf-8"))
        except Exception:
            final = {}
    for k in ("status", "best_pt", "model_deployed", "last_metrics", "error", "error_warning"):
        if k in final:
            state[k] = final[k]
    if state.get("_stop_requested"):
        state["status"] = "stopped"
    elif "status" not in final or final.get("status") == "running":
        # status.json yo'q yoki yarim — jarayon kutilmaganda tugagan
        state["status"] = "failed" if rc != 0 else "done"
    state["return_code"] = rc
    state["finished_at"] = datetime.now(timezone.utc).isoformat()
    state.pop("_stop_requested", None)
    TRAINING_RUNS[run_id] = state
    TRAIN_PROCS.pop(run_id, None)


def _launch_training(run_id: str, params: dict) -> None:
    """Training'ni alohida subprocess sifatida ishga tushiradi (Stop mumkin bo'lishi uchun)."""
    project_dir = BASE_DIR / "training_runs" / run_id
    project_dir.mkdir(parents=True, exist_ok=True)
    log_path = _training_log_path(run_id)

    worker_params = dict(params)
    worker_params["run_id"] = run_id
    worker_params["project_dir"] = str(project_dir)
    worker_params["models_dir"] = str(inf.MODELS_DIR)
    params_path = project_dir / "params.json"
    params_path.write_text(json.dumps(worker_params, ensure_ascii=False), encoding="utf-8")

    logf = open(log_path, "w", encoding="utf-8", buffering=1)
    creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
    proc = subprocess.Popen(
        [sys.executable, "-m", "app.train_worker", str(params_path)],
        cwd=str(BASE_DIR.parent),
        stdout=logf,
        stderr=subprocess.STDOUT,
        creationflags=creationflags,
    )
    TRAIN_PROCS[run_id] = proc
    state = TRAINING_RUNS.get(run_id, {})
    state.update({
        "status": "running",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "log_path": str(log_path),
        "pid": proc.pid,
        "project_dir": str(project_dir),
        "params": params,
    })
    TRAINING_RUNS[run_id] = state
    threading.Thread(target=_monitor_training, args=(run_id, proc, logf), daemon=True).start()


class TrainingRunBody(BaseModel):
    data_yaml: str
    base_model: str = "yolo11n.pt"
    epochs: int = 50
    imgsz: int = 1024
    batch: int = 8
    deploy_after: bool = True
    # Kengaytirilgan parametrlar (ixtiyoriy)
    optimizer: str = "auto"          # SGD | Adam | AdamW | auto
    lr0: float = 0.01                # Boshlang'ich LR
    lrf: float = 0.01                # Yakuniy LR (lr0 * lrf)
    momentum: float = 0.937
    weight_decay: float = 0.0005
    warmup_epochs: float = 3.0
    patience: int = 50               # Early stopping
    seed: int = 0
    cos_lr: bool = False              # Cosine LR scheduler
    pretrained: bool = True           # False = scratch'dan
    resume: Optional[str] = None      # Run ID dan davom ettirish
    # Augmentation
    hsv_h: float = 0.015
    hsv_s: float = 0.7
    hsv_v: float = 0.4
    fliplr: float = 0.5
    flipud: float = 0.0
    scale: float = 0.5
    mosaic: float = 1.0
    mixup: float = 0.0
    # Boshqalar
    workers: int = 4
    cache: str = "False"              # "False" | "ram" | "disk"
    device: str = ""                  # "" auto, "cpu", "0", "0,1"
    project_name: Optional[str] = None  # foydalanuvchi bergan nom


@app.post("/api/training/run")
def training_run(
    body: TrainingRunBody,
    _user: dict = Depends(auth_mod.require_user),
):
    """YOLO o'qitishni alohida subprocess'da boshlaydi. Run ID qaytaradi."""
    if not Path(body.data_yaml).exists():
        raise HTTPException(400, f"data.yaml topilmadi: {body.data_yaml}")
    run_id = "tr" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:6]
    TRAINING_RUNS[run_id] = {"status": "queued", "queued_at": datetime.now(timezone.utc).isoformat(), "params": body.model_dump()}
    _launch_training(run_id, body.model_dump())
    return {"run_id": run_id, "status": "running"}


@app.post("/api/training/stop/{run_id}")
def training_stop(run_id: str, _user: dict = Depends(auth_mod.require_user)):
    """Ishlab turgan training subprocess'ni to'xtatadi. last.pt saqlanib qoladi
    (keyinroq Resume bilan davom ettirsa bo'ladi)."""
    state = TRAINING_RUNS.get(run_id)
    if not state:
        raise HTTPException(404, f"Run topilmadi: {run_id}")
    proc = TRAIN_PROCS.get(run_id)
    if proc is None or proc.poll() is not None:
        raise HTTPException(409, "Run hozir ishlamayapti (allaqachon tugagan)")
    state["_stop_requested"] = True
    _kill_proc_tree(proc.pid)
    return {"run_id": run_id, "status": "stopping"}


# Mavjud datasetlarni topish (data.yaml'lar)
@app.get("/api/training/datasets")
def training_datasets(_user: dict = Depends(auth_mod.require_user)):
    """Mavjud data.yaml fayllarni qidiradi (foydalanuvchi tanlashi uchun)."""
    candidates: list[dict] = []
    search_roots = []
    # Loyiha papkasi ostida
    search_roots.append(BASE_DIR.parent)
    # Lokal disklar
    for d in ("D:/datasets", "C:/datasets", "/datasets", "/srv/datasets"):
        if Path(d).is_dir():
            search_roots.append(Path(d))
    seen = set()
    for root in search_roots:
        if not root.is_dir():
            continue
        try:
            for yml in list(root.glob("**/data.yaml"))[:200]:
                if str(yml) in seen:
                    continue
                seen.add(str(yml))
                try:
                    size = yml.stat().st_size
                    parent = yml.parent
                    train_n = len(list((parent / "images/train").glob("*"))) if (parent / "images/train").is_dir() else 0
                    val_n = len(list((parent / "images/val").glob("*"))) if (parent / "images/val").is_dir() else 0
                except Exception:
                    train_n = val_n = size = 0
                candidates.append({
                    "yaml": str(yml),
                    "dir": str(yml.parent),
                    "train_count": train_n,
                    "val_count": val_n,
                    "size_bytes": size,
                })
        except Exception:
            continue
    candidates.sort(key=lambda x: -(x["train_count"] + x["val_count"]))
    return {"datasets": candidates[:50]}


# Mavjud base model fayllarini ro'yxati (foydalanuvchi tanlashi uchun)
@app.get("/api/training/base_models")
def training_base_models(_user: dict = Depends(auth_mod.require_user)):
    """Ultralytics tomonidan tanish base modellar + lokal trained_*'lar."""
    suggested = [
        {"name": "yolo11n.pt", "label": "YOLO11 Nano — eng yengil", "size_hint_mb": 5},
        {"name": "yolo11s.pt", "label": "YOLO11 Small", "size_hint_mb": 20},
        {"name": "yolo11m.pt", "label": "YOLO11 Medium", "size_hint_mb": 40},
        {"name": "yolo11l.pt", "label": "YOLO11 Large", "size_hint_mb": 50},
        {"name": "yolo11x.pt", "label": "YOLO11 Extra — eng kuchli", "size_hint_mb": 120},
        {"name": "yolov10n.pt", "label": "YOLOv10 Nano", "size_hint_mb": 5},
        {"name": "yolov10x.pt", "label": "YOLOv10 Extra", "size_hint_mb": 64},
        {"name": "yolov9c.pt", "label": "YOLOv9 Compact", "size_hint_mb": 50},
        {"name": "yolov9e.pt", "label": "YOLOv9 Extra", "size_hint_mb": 110},
        {"name": "yolov8n.pt", "label": "YOLOv8 Nano (klassik)", "size_hint_mb": 6},
        {"name": "yolov8x.pt", "label": "YOLOv8 Extra", "size_hint_mb": 130},
    ]
    # Lokal modellar — fine-tune uchun
    local_pts = []
    for m in inf.list_models():
        local_pts.append({
            "name": m["name"],
            "label": f"Lokal: {m['name']} ({m['size_bytes']/1e6:.1f} MB)",
            "is_local": True,
            "path": str(inf.MODELS_DIR / m["name"]),
        })
    return {"suggested": suggested, "local": local_pts}


@app.get("/api/training/status/{run_id}")
def training_status(run_id: str, tail: int = 200, _user: dict = Depends(auth_mod.require_user)):
    state = dict(TRAINING_RUNS.get(run_id) or {})
    if not state:
        raise HTTPException(404, f"Run topilmadi: {run_id}")
    state.pop("_stop_requested", None)
    proc = TRAIN_PROCS.get(run_id)
    state["is_alive"] = bool(proc and proc.poll() is None)
    # Ishlab turgan run uchun live oxirgi metrikalarni results.csv'dan o'qib qo'shamiz
    if state.get("status") == "running":
        live = _read_results_csv(Path(state.get("project_dir") or (BASE_DIR / "training_runs" / run_id)))
        if live:
            state["last_metrics"] = live[-1]
            state["epochs_done"] = len(live)
    log_lines: list[str] = []
    log_path = state.get("log_path")
    if log_path and Path(log_path).exists():
        try:
            content = Path(log_path).read_text(encoding="utf-8", errors="replace")
            log_lines = content.splitlines()[-max(20, min(2000, tail)):]
        except Exception:
            pass
    return {"run_id": run_id, **state, "log_tail": log_lines}


@app.get("/api/training/runs")
def training_list_runs(_user: dict = Depends(auth_mod.require_user)):
    return {"runs": [{"run_id": k, **v} for k, v in sorted(TRAINING_RUNS.items(), reverse=True)]}


def _read_results_csv(project_dir: Path) -> list[dict]:
    """Ultralytics results.csv'ni per-epoch qatorlar (dict) ro'yxatiga aylantiradi.
    Raqamli qiymatlar float'ga o'giriladi — grafiklar uchun."""
    csv_path = next(iter(project_dir.rglob("results.csv")), None)
    if not csv_path or not csv_path.exists():
        return []
    rows: list[dict] = []
    try:
        lines = csv_path.read_text(encoding="utf-8").splitlines()
        if len(lines) < 2:
            return []
        headers = [h.strip() for h in lines[0].split(",")]
        for ln in lines[1:]:
            vals = [v.strip() for v in ln.split(",")]
            if len(vals) != len(headers):
                continue
            row: dict = {}
            for h, v in zip(headers, vals):
                try:
                    row[h] = float(v)
                except ValueError:
                    row[h] = v
            rows.append(row)
    except Exception:
        return []
    return rows


@app.get("/api/training/metrics/{run_id}")
def training_metrics(run_id: str, _user: dict = Depends(auth_mod.require_user)):
    """Jonli grafiklar uchun: har epochdagi loss/mAP/precision/recall qatorlari."""
    safe = re.sub(r"[^A-Za-z0-9_.-]", "", run_id)
    project_dir = BASE_DIR / "training_runs" / safe
    rows = _read_results_csv(project_dir)
    return {"run_id": safe, "epochs": len(rows), "rows": rows}


# --------------------------------------------------------------------------- #
# O'qitishdan keyingi natijalar: plotlar, namuna bashoratlar, eksport, compare #
# --------------------------------------------------------------------------- #
# Har bir plot uchun nomzod fayl nomlari (Ultralytics versiyalari bo'yicha farqlanadi:
# yangi versiyalar "Box" prefiksini qo'shadi — BoxPR_curve.png va h.k.).
_PLOT_SPECS = [
    ("results", ["results.png"]),
    ("confusion_matrix", ["confusion_matrix.png"]),
    ("confusion_matrix_normalized", ["confusion_matrix_normalized.png"]),
    ("PR_curve", ["BoxPR_curve.png", "PR_curve.png"]),
    ("F1_curve", ["BoxF1_curve.png", "F1_curve.png"]),
    ("P_curve", ["BoxP_curve.png", "P_curve.png"]),
    ("R_curve", ["BoxR_curve.png", "R_curve.png"]),
    ("labels", ["labels.jpg"]),
]


@app.get("/api/training/plots/{run_id}")
def training_plots(run_id: str, _user: dict = Depends(auth_mod.require_user)):
    """Ultralytics o'qitish chiqargan grafiklar va namuna bashoratlar ro'yxati."""
    safe = re.sub(r"[^A-Za-z0-9_.-]", "", run_id)
    proj = BASE_DIR / "training_runs" / safe
    available = []
    for key, names in _PLOT_SPECS:
        found = None
        for nm in names:
            found = next((p for p in proj.rglob(nm) if p.is_file()), None)
            if found:
                break
        if found:
            available.append({"key": key, "file": found.name})
    preds = sorted(p.name for p in proj.rglob("val_batch*_pred.jpg") if p.is_file())[:8]
    return {"run_id": safe, "plots": available, "predictions": preds}


@app.get("/api/training/plot/{run_id}")
def training_plot(run_id: str, name: str, _user: dict = Depends(auth_mod.require_user)):
    """Bitta plot/bashorat rasmini uzatadi (auth talab qiladi)."""
    safe = re.sub(r"[^A-Za-z0-9_.-]", "", run_id)
    fname = os.path.basename(name)
    proj = BASE_DIR / "training_runs" / safe
    f = next((p for p in proj.rglob(fname) if p.is_file()), None)
    if not f:
        raise HTTPException(404, f"rasm topilmadi: {fname}")
    media = "image/jpeg" if f.suffix.lower() in (".jpg", ".jpeg") else "image/png"
    return FileResponse(str(f), media_type=media)


# Eksport jobs: export_id -> holat
EXPORT_JOBS: dict = {}
_EXPORT_FMT = {"onnx": "onnx", "tensorrt": "engine", "openvino": "openvino"}


def _run_export(export_id: str, run_id: str, fmt_key: str, imgsz: int, half: bool):
    state = EXPORT_JOBS.get(export_id, {})
    try:
        proj = BASE_DIR / "training_runs" / run_id
        best = next((p for p in proj.rglob("best.pt") if p.is_file()), None)
        if best is None:
            raise RuntimeError("best.pt topilmadi — avval o'qitishni yakunlang")
        from ultralytics import YOLO
        m = YOLO(str(best))
        out = m.export(format=_EXPORT_FMT[fmt_key], imgsz=imgsz, half=half)
        state["status"] = "done"
        state["output"] = str(out)
    except Exception as e:  # noqa: BLE001
        state["status"] = "failed"
        state["error"] = f"{type(e).__name__}: {e}"
    state["finished_at"] = datetime.now(timezone.utc).isoformat()
    EXPORT_JOBS[export_id] = state


class ExportBody(BaseModel):
    run_id: str
    format: str = "onnx"   # onnx | tensorrt | openvino
    imgsz: int = 640
    half: bool = False


@app.post("/api/training/export")
def training_export(body: ExportBody, _user: dict = Depends(auth_mod.require_user)):
    """Model'ni ONNX/TensorRT/OpenVINO formatiga eksport qilishni boshlaydi (fonda)."""
    fmt = (body.format or "onnx").lower()
    if fmt not in _EXPORT_FMT:
        raise HTTPException(400, f"noma'lum format: {fmt}")
    safe = re.sub(r"[^A-Za-z0-9_.-]", "", body.run_id)
    export_id = "exp_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:6]
    EXPORT_JOBS[export_id] = {
        "status": "running", "run_id": safe, "format": fmt,
        "started_at": datetime.now(timezone.utc).isoformat(),
    }
    threading.Thread(
        target=_run_export,
        args=(export_id, safe, fmt, int(body.imgsz or 640), bool(body.half)),
        daemon=True,
    ).start()
    return {"export_id": export_id, "status": "running"}


@app.get("/api/training/export/status/{export_id}")
def training_export_status(export_id: str, _user: dict = Depends(auth_mod.require_user)):
    state = EXPORT_JOBS.get(export_id)
    if not state:
        raise HTTPException(404, "eksport topilmadi")
    out = dict(state)
    if out.get("output"):
        out["filename"] = os.path.basename(out["output"])
    return {"export_id": export_id, **out}


@app.get("/api/training/export/download/{export_id}")
def training_export_download(export_id: str, _user: dict = Depends(auth_mod.require_user)):
    state = EXPORT_JOBS.get(export_id)
    if not state or state.get("status") != "done" or not state.get("output"):
        raise HTTPException(404, "eksport hali tayyor emas")
    out = Path(state["output"])
    if out.is_dir():
        # OpenVINO papkani zip qilib beramiz
        import shutil
        zpath = shutil.make_archive(str(out), "zip", str(out))
        out = Path(zpath)
    if not out.exists():
        raise HTTPException(404, "eksport fayli topilmadi")
    return FileResponse(
        str(out), media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{out.name}"'},
    )


@app.get("/api/training/compare")
def training_compare(runs: str, _user: dict = Depends(auth_mod.require_user)):
    """Bir nechta run'ning yakuniy metrikalarini yonma-yon qaytaradi."""
    ids = [re.sub(r"[^A-Za-z0-9_.-]", "", r) for r in runs.split(",") if r.strip()][:5]
    out = []
    for rid in ids:
        proj = BASE_DIR / "training_runs" / rid
        rows = _read_results_csv(proj)
        fr = rows[-1] if rows else {}

        def g(*keys):
            for k in keys:
                v = fr.get(k)
                if isinstance(v, (int, float)):
                    return round(float(v), 4)
            return None

        params = (TRAINING_RUNS.get(rid) or {}).get("params", {})
        out.append({
            "run_id": rid,
            "epochs": len(rows),
            "mAP50": g("metrics/mAP50(B)", "metrics/mAP_0.5"),
            "mAP50_95": g("metrics/mAP50-95(B)", "metrics/mAP_0.5:0.95"),
            "precision": g("metrics/precision(B)", "metrics/precision"),
            "recall": g("metrics/recall(B)", "metrics/recall"),
            "base_model": params.get("base_model"),
            "imgsz": params.get("imgsz"),
        })
    return {"runs": out}


@app.get("/api/training/validate")
def training_validate(
    yaml_path: str = Query(..., alias="yaml"),
    _user: dict = Depends(auth_mod.require_user),
):
    """data.yaml tekshiruvi: rasm soni, class taqsimoti, rasm↔label mosligi,
    bo'sh/buzuq fayllar ogohlantirishi."""
    yp = Path(yaml_path)
    if not yp.exists():
        raise HTTPException(404, f"data.yaml topilmadi: {yaml_path}")
    import yaml as _yaml
    try:
        data = _yaml.safe_load(yp.read_text(encoding="utf-8")) or {}
    except Exception as e:
        raise HTTPException(400, f"data.yaml o'qib bo'lmadi: {e}")

    ydir = yp.parent
    base = data.get("path")
    if base:
        base = Path(base)
        base = base if base.is_absolute() else (ydir / base)
    else:
        base = ydir

    names_raw = data.get("names")
    names: dict = {}
    if isinstance(names_raw, dict):
        names = {int(k): str(v) for k, v in names_raw.items()}
    elif isinstance(names_raw, list):
        names = {i: str(v) for i, v in enumerate(names_raw)}
    nc = int(data.get("nc") or len(names) or 0)

    IMG_EXT = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}

    def split_info(split_key: str):
        rel = data.get(split_key)
        if not rel:
            return None
        if isinstance(rel, list):
            rel = rel[0] if rel else None
        if not rel:
            return None
        sp = Path(rel)
        img_dir = sp if sp.is_absolute() else (base / sp)
        info = {
            "path": str(img_dir), "exists": img_dir.is_dir(),
            "images": 0, "labels": 0, "missing_labels": 0,
            "orphan_labels": 0, "empty_images": 0, "class_counts": {},
        }
        if not img_dir.is_dir():
            return info
        # YOLO konvensiyasi: images/ -> labels/
        lbl_dir = Path(str(img_dir).replace("images", "labels", 1))
        imgs = [p for p in img_dir.rglob("*") if p.suffix.lower() in IMG_EXT]
        info["images"] = len(imgs)
        img_stems = set()
        for p in imgs:
            img_stems.add(p.stem)
            try:
                if p.stat().st_size == 0:
                    info["empty_images"] += 1
            except Exception:
                pass
        lbl_files = list(lbl_dir.rglob("*.txt")) if lbl_dir.is_dir() else []
        info["labels"] = len(lbl_files)
        lbl_stems = set()
        cc: dict = {}
        for lf in lbl_files:
            lbl_stems.add(lf.stem)
            try:
                for line in lf.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        cid = int(float(line.split()[0]))
                    except (ValueError, IndexError):
                        continue
                    cc[cid] = cc.get(cid, 0) + 1
            except Exception:
                continue
        info["class_counts"] = {names.get(k, str(k)): v for k, v in sorted(cc.items())}
        info["missing_labels"] = len(img_stems - lbl_stems)
        info["orphan_labels"] = len(lbl_stems - img_stems)
        return info

    return {"yaml": str(yp), "names": names, "nc": nc,
            "train": split_info("train"), "val": split_info("val")}


@app.get("/api/system/gpu")
def system_gpu(_user: dict = Depends(auth_mod.require_user)):
    """nvidia-smi orqali GPU holati: VRAM band/jami, utilization, harorat.
    Hamda torch CUDA'ni ko'ra oladimi — training GPU'da ketishini bildiradi."""
    out: dict = {"available": False, "gpus": []}
    try:
        r = subprocess.run(
            ["nvidia-smi",
             "--query-gpu=index,name,memory.total,memory.used,memory.free,utilization.gpu,temperature.gpu",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5,
        )
        if r.returncode == 0:
            for line in r.stdout.strip().splitlines():
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 7:
                    out["gpus"].append({
                        "index": int(parts[0]), "name": parts[1],
                        "mem_total_mb": float(parts[2]), "mem_used_mb": float(parts[3]),
                        "mem_free_mb": float(parts[4]), "util_pct": float(parts[5]),
                        "temp_c": float(parts[6]),
                    })
            out["available"] = bool(out["gpus"])
    except Exception as e:
        out["error"] = str(e)
    try:
        import torch
        out["torch_cuda"] = bool(torch.cuda.is_available())
        out["torch_version"] = torch.__version__
    except Exception:
        out["torch_cuda"] = False
    return out


# --------------------------------------------------------------------------- #
# Hisobot generatori — strukturaviy topilmalar -> mammografiya hisoboti        #
# --------------------------------------------------------------------------- #
class ReportDetection(BaseModel):
    laterality: str = ""
    view: str = ""
    quadrant: str = ""
    cx: Optional[float] = None
    cy: Optional[float] = None
    type: str = "mass"
    size_mm: Optional[float] = None
    margin: str = ""
    birads: str = "0"
    confidence: Optional[float] = None


class ReportGenerateBody(BaseModel):
    detections: list[ReportDetection] = []
    findings: Optional[dict] = None
    dicom_meta: dict = {}
    study_views: list[str] = []
    mode: str = "auto"        # auto | template | llm
    lang: str = "uz"
    examples: list[str] = []


@app.post("/api/report/generate")
def report_generate(body: ReportGenerateBody, _user: dict = Depends(auth_mod.require_user)):
    """Strukturaviy topilmalardan mammografiya hisoboti qoralamasini yaratadi.
    mode=auto: Claude (ANTHROPIC_API_KEY bo'lsa) yoki shablonga fallback."""
    from . import report_findings as rf
    from . import report_gen as rg
    findings = body.findings or rf.build_findings(
        [d.model_dump() for d in body.detections],
        dicom_meta=body.dicom_meta,
        study_views=body.study_views,
    )
    out = rg.generate_report(
        findings, mode=body.mode, examples=(body.examples or None), lang=body.lang
    )
    return {"findings": findings, **out}


@app.get("/api/report/status")
def report_status(_user: dict = Depends(auth_mod.require_user)):
    """Qaysi hisobot backendlari mavjud: shablon (doim), lokal Ollama, bulutli Claude."""
    from . import report_gen as rg
    models = rg._ollama_available()
    return {
        "template": True,
        "ollama": models is not None,
        "ollama_models": models or [],
        "ollama_default": rg.OLLAMA_MODEL,
        "anthropic_key": bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")),
    }


class ReportExportBody(BaseModel):
    source: str
    ref: str
    report: str
    findings: Optional[dict] = None
    verified: bool = False


@app.post("/api/report/export-sr")
def report_export_sr(body: ReportExportBody, user: dict = Depends(auth_mod.require_user)):
    """Tasdiqlangan hisobotni DICOM Comprehensive SR sifatida eksport qiladi
    (bemor/study metadata manba DICOM'dan meros olinadi)."""
    _validate_source(body.source)
    _validate_ref(body.source, body.ref)
    src_path = _resolve_dicom_path(body.source, body.ref)
    if not (body.report or "").strip():
        raise HTTPException(400, "Hisobot matni bo'sh")
    try:
        data = dsr.report_to_sr(
            src_path, body.report,
            findings=body.findings,
            author=user.get("sub"),
            verified=body.verified,
        )
    except Exception as e:
        raise HTTPException(500, f"SR build failed: {e}")
    base = Path(body.ref).stem or "report"
    fname = f"{base}_report_sr.dcm"
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/dicom",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )


# --------------------------------------------------------------------------- #
# Model management dashboard — statistika, delete, versionlar                  #
# --------------------------------------------------------------------------- #
@app.get("/api/models/stats")
def models_stats(_user: dict = Depends(auth_mod.require_user)):
    """Har model uchun: hajm, qachon qo'shilgan, nechta annotation chiqargan."""
    from datetime import datetime as _dt
    models = inf.list_models()
    # Annotation fayllaridan har model ishlatilgan sonni hisoblaymiz
    usage: dict = {}
    for ann_path in ANNOT_DIR.glob("*.json"):
        try:
            data = json.loads(ann_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        for a in data.get("annotations") or []:
            cb = str(a.get("created_by", ""))
            if cb.startswith("ai:"):
                model_name = cb[3:]
                usage[model_name] = usage.get(model_name, 0) + 1
    out = []
    for m in models:
        p = inf.MODELS_DIR / m["name"]
        try:
            mtime = p.stat().st_mtime
            added = _dt.fromtimestamp(mtime, tz=timezone.utc).isoformat()
        except Exception:
            added = None
        is_trained = m["name"].startswith("trained_")
        out.append({
            "name": m["name"],
            "size_bytes": m["size_bytes"],
            "size_mb": round(m["size_bytes"] / 1e6, 1),
            "added_at": added,
            "annotations_produced": usage.get(m["name"], 0),
            "is_trained_locally": is_trained,
            "is_deletable": is_trained,  # faqat lokal o'qitilganlar o'chiriladi
        })
    out.sort(key=lambda x: (-x["annotations_produced"], x["name"]))
    return {"models": out, "models_dir": str(inf.MODELS_DIR)}


@app.delete("/api/models/{name}")
def delete_model(name: str, _user: dict = Depends(auth_mod.require_user)):
    """Lokal o'qitilgan modelni o'chirish. Built-in (digitaleye/yolov8 va h.k.) o'chmaydi."""
    safe = Path(name).name
    if not safe.endswith(".pt"):
        safe += ".pt"
    if not safe.startswith("trained_"):
        raise HTTPException(403, "Faqat lokal o'qitilgan (trained_*) modellarni o'chirish mumkin")
    p = inf.MODELS_DIR / safe
    if not p.exists():
        raise HTTPException(404, f"Model topilmadi: {safe}")
    try:
        p.unlink()
    except Exception as e:
        raise HTTPException(500, f"O'chirib bo'lmadi: {e}")
    # Inference cache'ni tozalash
    try:
        if str(p) in inf._model_cache:
            with inf._cache_lock:
                inf._model_cache.pop(str(p), None)
    except Exception:
        pass
    return {"deleted": safe}


# --------------------------------------------------------------------------- #
# Active learning eslatmasi — qancha "modifikatsiyalangan AI annotation" bor   #
# --------------------------------------------------------------------------- #
ACTIVE_LEARNING_THRESHOLD = int(os.environ.get("ACTIVE_LEARNING_THRESHOLD", "50") or "50")


@app.get("/api/training/suggestion")
def training_suggestion(_user: dict = Depends(auth_mod.require_user)):
    """AI'dan farqli yoki tasdiqlangan annotation'lar sonini sanab, retrain
    kerakligi to'g'risida tavsiya beradi."""
    edited = 0
    approved = 0
    human = 0
    total = 0
    for ann_path in ANNOT_DIR.glob("*.json"):
        try:
            data = json.loads(ann_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        for a in data.get("annotations") or []:
            total += 1
            st = str(a.get("status", ""))
            cb = str(a.get("created_by", ""))
            if cb.startswith("ai:"):
                if st in ("edited", "ai_review", "ai_accepted"):
                    edited += 1
                elif st in ("approved", "submitted"):
                    approved += 1
            else:
                human += 1
    eligible = human + edited + approved
    should = eligible >= ACTIVE_LEARNING_THRESHOLD
    return {
        "total_annotations": total,
        "human_annotations": human,
        "edited_ai": edited,
        "approved_ai": approved,
        "eligible_for_training": eligible,
        "threshold": ACTIVE_LEARNING_THRESHOLD,
        "should_retrain": should,
        "message": (
            f"✓ Yangi modelni o'qitishga vaqt keldi ({eligible} ta yangi annotation)"
            if should else
            f"Yana {ACTIVE_LEARNING_THRESHOLD - eligible} ta annotation kerak"
        ),
    }


class TrainingPrepareBody(BaseModel):
    destination: str
    target_size: int = 1024
    val_frac: float = 0.15
    include_ai: bool = False                # AI tomonidan yaratilgan annotation ham qo'shiladimi
    statuses: Optional[list[str]] = None    # filtr (None = barchasi)
    class_list: Optional[list[str]] = None  # None = annotation label'laridan avto
    image_format: str = "png"               # "png" | "jpg"
    seed: int = 42
    zip_after: bool = False                 # ZIP qilib ko'chirish uchun tayyorlash


def _polygon_to_bbox_pts(points: list[list[float]]) -> tuple[float, float, float, float]:
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    x0, x1 = max(0.0, min(xs)), min(1.0, max(xs))
    y0, y1 = max(0.0, min(ys)), min(1.0, max(ys))
    return x0, y0, max(0.0, x1 - x0), max(0.0, y1 - y0)


@app.post("/api/training/prepare")
def training_prepare(
    body: TrainingPrepareBody,
    _user: dict = Depends(auth_mod.require_user),
):
    """Annotation'lardan YOLO (Ultralytics) dataset yaratadi:
        <dest>/
            images/{train,val}/<id>.png
            labels/{train,val}/<id>.txt
            data.yaml
    """
    import random
    import shutil
    import zipfile

    dest_str = (body.destination or "").strip()
    if not dest_str:
        raise HTTPException(400, "destination kerak")
    dest = Path(dest_str)
    forbidden_starts = [r"C:\Windows", r"C:\Program Files", "/etc", "/usr", "/bin", "/sbin", "/sys", "/proc"]
    if any(str(dest).lower().startswith(x.lower()) for x in forbidden_starts):
        raise HTTPException(400, f"Bu papkaga yozish taqiqlangan: {dest}")
    try:
        dest.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        raise HTTPException(400, f"Papka yaratib bo'lmadi: {e}")

    target_size = max(256, min(4096, int(body.target_size)))
    val_frac = max(0.0, min(0.5, float(body.val_frac)))
    img_ext = "jpg" if body.image_format.lower() in ("jpg", "jpeg") else "png"

    # 1-bosqich: annotation fayllarni o'qib, tasniflash
    items: list[dict] = []
    label_set: set[str] = set()
    for ann_path in sorted(ANNOT_DIR.glob("upload__*.json")):
        file_id = ann_path.stem.replace("upload__", "", 1)
        dcm = UPLOAD_DIR / f"{file_id}.dcm"
        if not dcm.exists():
            continue
        try:
            data = json.loads(ann_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        anns = data.get("annotations") or []
        # Filtrlar
        kept = []
        for a in anns:
            cb = str(a.get("created_by", ""))
            if not body.include_ai and cb.startswith("ai:"):
                continue
            if body.statuses and a.get("status") not in body.statuses:
                continue
            t = a.get("type")
            if t == "bbox" and a.get("bbox"):
                bx, by, bw, bh = a["bbox"][:4]
                kept.append({"label": str(a.get("label", "") or "lesion"), "bbox": [bx, by, bw, bh]})
                label_set.add(kept[-1]["label"])
            elif t == "polygon" and a.get("points") and len(a["points"]) >= 3:
                bx, by, bw, bh = _polygon_to_bbox_pts(a["points"])
                kept.append({"label": str(a.get("label", "") or "lesion"), "bbox": [bx, by, bw, bh]})
                label_set.add(kept[-1]["label"])
        if not kept:
            continue
        # Study guruhi uchun PatientID + StudyUID o'qiymiz
        try:
            ds = pydicom.dcmread(str(dcm), stop_before_pixels=True, force=True)
            pid = str(getattr(ds, "PatientID", "") or "")
            suid = str(getattr(ds, "StudyInstanceUID", "") or "")
        except Exception:
            pid = suid = ""
        group_key = pid or suid or file_id
        items.append({"file_id": file_id, "dcm": dcm, "annotations": kept, "group": group_key})

    if not items:
        raise HTTPException(400, "Annotation bo'lgan fayl topilmadi (yoki filtr juda tor)")

    # 2-bosqich: classlar tartibi
    if body.class_list:
        classes = list(dict.fromkeys(body.class_list))
    else:
        classes = sorted(label_set)
    cls_to_id = {name: i for i, name in enumerate(classes)}

    # 3-bosqich: patient-level train/val split
    rng = random.Random(body.seed)
    groups = sorted({it["group"] for it in items})
    rng.shuffle(groups)
    n_val_groups = max(1, int(round(len(groups) * val_frac))) if val_frac > 0 else 0
    val_groups = set(groups[:n_val_groups])

    # 4-bosqich: papka tuzilmasi
    for sub in ("images/train", "images/val", "labels/train", "labels/val"):
        (dest / sub).mkdir(parents=True, exist_ok=True)

    counts = {"train_imgs": 0, "val_imgs": 0, "train_lbls": 0, "val_lbls": 0, "skipped": 0}

    # 5-bosqich: har bir item ni qayta ishlash
    for it in items:
        split = "val" if it["group"] in val_groups else "train"
        try:
            png_bytes = render_frame_png(it["dcm"], frame=0, max_dim=target_size)
        except Exception:
            counts["skipped"] += 1
            continue
        # Agar JPG kerak bo'lsa, qayta kodlaymiz
        img_bytes = png_bytes
        if img_ext == "jpg":
            try:
                from PIL import Image
                im = Image.open(io.BytesIO(png_bytes))
                if im.mode != "RGB":
                    im = im.convert("RGB")
                buf = io.BytesIO()
                im.save(buf, format="JPEG", quality=92)
                img_bytes = buf.getvalue()
            except Exception:
                img_ext = "png"  # fallback

        img_path = dest / f"images/{split}/{it['file_id']}.{img_ext}"
        lbl_path = dest / f"labels/{split}/{it['file_id']}.txt"
        img_path.write_bytes(img_bytes)
        if split == "train":
            counts["train_imgs"] += 1
        else:
            counts["val_imgs"] += 1

        # YOLO label faylini yozish: <cls> <cx> <cy> <w> <h> (normallashtirilgan)
        n_lines = 0
        with lbl_path.open("w", encoding="utf-8") as f:
            for a in it["annotations"]:
                lbl_name = a["label"]
                cls_id = cls_to_id.get(lbl_name)
                if cls_id is None:
                    continue
                bx, by, bw, bh = a["bbox"]
                cx = bx + bw / 2.0
                cy = by + bh / 2.0
                cx = max(0.0, min(1.0, cx)); cy = max(0.0, min(1.0, cy))
                bw = max(0.0, min(1.0, bw)); bh = max(0.0, min(1.0, bh))
                if bw <= 0 or bh <= 0:
                    continue
                f.write(f"{cls_id} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}\n")
                n_lines += 1
        if split == "train":
            counts["train_lbls"] += n_lines
        else:
            counts["val_lbls"] += n_lines

    # 6-bosqich: data.yaml
    yaml_path = dest / "data.yaml"
    yaml_lines = [
        f"# MAMOGRAF training dataset — {datetime.now(timezone.utc).isoformat()}",
        f"path: {dest.as_posix()}",
        "train: images/train",
        "val: images/val",
        f"nc: {len(classes)}",
        "names:",
    ]
    for i, n in enumerate(classes):
        yaml_lines.append(f"  {i}: {n}")
    yaml_path.write_text("\n".join(yaml_lines) + "\n", encoding="utf-8")

    # Train buyrug'i ko'rsatmasi
    readme = dest / "README_TRAIN.md"
    readme.write_text(
        "# YOLO training dataset (MAMOGRAF)\n\n"
        f"Yaratilgan: {datetime.now(timezone.utc).isoformat()}\n"
        f"Klasslar ({len(classes)}): {classes}\n\n"
        "## Ultralytics bilan train:\n\n"
        "```bash\n"
        "pip install ultralytics\n"
        "yolo task=detect mode=train model=yolo11n.pt "
        f"data={(yaml_path).as_posix()} epochs=100 imgsz={target_size} batch=8\n"
        "```\n\n"
        "## Yoki Python:\n\n"
        "```python\n"
        "from ultralytics import YOLO\n"
        "m = YOLO('yolo11n.pt')\n"
        f"m.train(data=r'{yaml_path}', epochs=100, imgsz={target_size}, batch=8)\n"
        "```\n",
        encoding="utf-8",
    )

    zip_path = None
    if body.zip_after:
        zip_path = dest.parent / (dest.name + ".zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for p in dest.rglob("*"):
                if p.is_file():
                    zf.write(p, p.relative_to(dest.parent))

    return {
        "destination": str(dest),
        "data_yaml": str(yaml_path),
        "readme": str(readme),
        "zip": str(zip_path) if zip_path else None,
        "classes": classes,
        "items_total": len(items),
        "val_groups": n_val_groups,
        "total_groups": len(groups),
        **counts,
    }


# (C1) 4-view side-by-side: shu fayl bilan bir Study'dagi barcha proyeksiyalar
@app.get("/api/files/{file_id}/study_views")
def study_views(file_id: str):
    p = UPLOAD_DIR / f"{file_id}.dcm"
    if not p.exists():
        raise HTTPException(404)
    try:
        ds = pydicom.dcmread(str(p), stop_before_pixels=True, force=True)
    except Exception as e:
        raise HTTPException(500, f"read failed: {e}")
    study_uid = str(getattr(ds, "StudyInstanceUID", "") or "")
    if not study_uid:
        return {"views": [], "study_uid": ""}
    out = []
    for f in UPLOAD_DIR.glob("*.dcm"):
        try:
            ds2 = pydicom.dcmread(str(f), stop_before_pixels=True, force=True)
        except Exception:
            continue
        if str(getattr(ds2, "StudyInstanceUID", "") or "") != study_uid:
            continue
        view = str(getattr(ds2, "ViewPosition", "") or "").upper()
        lat = str(getattr(ds2, "ImageLaterality", "") or "").upper()
        out.append({
            "id": f.stem,
            "view": view,
            "laterality": lat,
            "key": f"{lat}{view}",   # mas. LCC, RCC, LMLO, RMLO
            "kind": "upload",
        })
    # Standart mammografiya tartibi
    ORDER = ["LCC", "RCC", "LMLO", "RMLO"]
    def sort_key(v):
        try:
            return (ORDER.index(v["key"]), v["id"])
        except ValueError:
            return (99, v["id"])
    out.sort(key=sort_key)
    return {"views": out, "study_uid": study_uid}


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


@app.get("/api/files/{file_id}/auto_window")
def auto_window_ep(file_id: str, frame: int = 0):
    """Histogramma asosida avtomatik WC/WW (oyna taglari yo'q rasmlar uchun ham)."""
    p = UPLOAD_DIR / f"{file_id}.dcm"
    if not p.exists():
        raise HTTPException(404)
    try:
        wc, ww = auto_window(p, frame=frame)
    except NoPixelDataError:
        raise HTTPException(422, "no pixels")
    except Exception as e:
        raise HTTPException(500, f"auto_window failed: {e}")
    return {"wc": wc, "ww": ww}


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
                "labels": a.get("labels") or ([a["label"]] if a.get("label") else []),
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
            bbox = a.get("bbox") or [0, 0, 0, 0]
            if len(bbox) != 4:
                continue
            labs = exporters.ann_labels(a) or ["other"]
            x_n, y_n, w_n, h_n = bbox
            if rows and cols:
                x = x_n * cols
                y = y_n * rows
                w = w_n * cols
                h = h_n * rows
            else:
                x, y, w, h = x_n, y_n, w_n, h_n

            ann_type = a.get("type") or "bbox"
            # Geometry/segmentation is computed once and shared across labels.
            seg_fields: dict = {}
            if ann_type == "polygon" and a.get("points"):
                pts = a["points"]
                if rows and cols:
                    flat_px: list[float] = []
                    for px, py in pts:
                        flat_px.append(round(px * cols, 2))
                        flat_px.append(round(py * rows, 2))
                    seg_fields["segmentation"] = [flat_px]
                    pts_px = [(px * cols, py * rows) for px, py in pts]
                    seg_fields["area"] = round(abs(_polygon_area(pts_px)), 2)
                else:
                    flat_n: list[float] = []
                    for px, py in pts:
                        flat_n.append(px)
                        flat_n.append(py)
                    seg_fields["segmentation_normalized"] = [flat_n]
                    seg_fields["area"] = round(w * h, 2)
                seg_fields["points_count"] = len(pts)
            else:
                seg_fields["area"] = round(w * h, 2)

            # Multi-label: emit one COCO annotation per label, sharing group_id.
            group_id = a.get("id") or f"g{next_ann_id}"
            for lab in labs:
                if lab not in label_ix:
                    label_ix[lab] = len(label_ix) + 1
                ann_out = {
                    "id": next_ann_id,
                    "image_id": img_id,
                    "category_id": label_ix[lab],
                    "group_id": group_id,
                    "label": lab,
                    "labels": labs,
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
                ann_out.update(seg_fields)
                if link_for_image and link_for_image.get("patient_id"):
                    ann_out["patient_id"] = link_for_image["patient_id"]
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


@app.get("/api/export/mask")
def export_mask(
    source: str,
    ref: str,
    format: str = "png",
    _user: dict = Depends(auth_mod.require_user),
):
    """Segmentation mask for one image, built from its polygons + bboxes.

    format=png   → label-indexed PNG (0 = background, 1..N = label classes)
    format=nifti → label-indexed .nii.gz (same indexing)

    The class→label legend is returned in the ``X-Mask-Legend`` header (JSON).
    """
    fmt = format.lower()
    if fmt not in ("png", "nifti"):
        raise HTTPException(400, "format must be 'png' or 'nifti'")
    _validate_source(source)
    _validate_ref(source, ref)
    data = annot_store.load(ANNOT_DIR, source, ref)
    annotations = data.get("annotations", []) or []
    if not annotations:
        raise HTTPException(404, "no annotations to export")
    rows, cols = _resolve_dims(source, ref, data.get("rows"), data.get("cols"))
    if not rows or not cols:
        raise HTTPException(422, "image dimensions unknown; cannot rasterize mask")

    label_names = [l["name"] for l in load_labels_config()[0]]
    label_index = {name: i + 1 for i, name in enumerate(label_names)}
    # Include any ad-hoc labels not in config so nothing is silently dropped.
    for a in annotations:
        for lab in exporters.ann_labels(a):
            if lab not in label_index:
                label_index[lab] = len(label_index) + 1

    try:
        mask = exporters.build_label_mask(annotations, rows, cols, label_index)
    except Exception as e:
        raise HTTPException(500, f"mask build failed: {e}")

    base = Path(ref).stem or "annotations"
    legend = json.dumps(exporters.mask_legend(label_index), ensure_ascii=False)
    if fmt == "png":
        body = exporters.mask_to_png_bytes(mask)
        media, suffix = "image/png", "mask.png"
    else:
        body = exporters.mask_to_nifti_bytes(mask)
        media, suffix = "application/gzip", "mask.nii.gz"

    return StreamingResponse(
        io.BytesIO(body),
        media_type=media,
        headers={
            "Content-Disposition": f'attachment; filename="{base}_{suffix}"',
            "X-Mask-Legend": legend,
        },
    )


def _radiomics_for(source: str, ref: str, bins: int, only_id: Optional[str] = None):
    """Compute radiomics features for one or all annotations on an image.

    Returns ``(image_meta, [ {annotation_id, label, labels, frame, features}, ... ])``.
    """
    path = _resolve_dicom_path(source, ref)
    data = annot_store.load(ANNOT_DIR, source, ref)
    annotations = data.get("annotations", []) or []
    if only_id:
        annotations = [a for a in annotations if a.get("id") == only_id]
    if not annotations:
        raise HTTPException(404, "no matching annotations")
    rows, cols = _resolve_dims(source, ref, data.get("rows"), data.get("cols"))
    if not rows or not cols:
        raise HTTPException(422, "image dimensions unknown")

    # Load each needed frame once (radiomics is per-frame).
    frame_cache: dict[int, tuple] = {}
    out: list[dict] = []
    for a in annotations:
        frame = int(a.get("frame") or 0)
        if frame not in frame_cache:
            try:
                frame_cache[frame] = load_frame_array(path, frame=frame)
            except Exception as e:
                raise HTTPException(500, f"pixel load failed: {e}")
        image, spacing = frame_cache[frame]
        fr_rows, fr_cols = image.shape[:2]
        mask = radiomics_mod.roi_mask_from_annotation(a, fr_rows, fr_cols)
        if not mask.any():
            continue
        try:
            feats = radiomics_mod.extract(image, mask, spacing=spacing, bins=bins)
        except Exception as e:
            raise HTTPException(500, f"radiomics failed for {a.get('id')}: {e}")
        out.append({
            "annotation_id": a.get("id"),
            "label": a.get("label"),
            "labels": exporters.ann_labels(a),
            "bi_rads": a.get("bi_rads") or "",
            "frame": frame,
            "type": a.get("type") or "bbox",
            "spacing_mm": list(spacing) if spacing else None,
            "features": feats,
        })
    if not out:
        raise HTTPException(422, "ROI(s) produced no usable mask")
    return {"source": source, "ref": ref, "rows": rows, "cols": cols, "bins": bins}, out


@app.get("/api/radiomics")
def get_radiomics(
    source: str,
    ref: str,
    annotation_id: Optional[str] = None,
    bins: int = 32,
    _user: dict = Depends(auth_mod.require_user),
):
    """Radiomics features for one annotation (annotation_id) or all on the image."""
    _validate_source(source)
    _validate_ref(source, ref)
    bins = max(8, min(128, int(bins)))
    meta, items = _radiomics_for(source, ref, bins, only_id=annotation_id)
    return {**meta, "results": items}


@app.get("/api/radiomics/csv")
def get_radiomics_csv(
    source: str,
    ref: str,
    bins: int = 32,
    _user: dict = Depends(auth_mod.require_user),
):
    """All ROIs on an image as a CSV — one row per annotation, one column per feature."""
    _validate_source(source)
    _validate_ref(source, ref)
    bins = max(8, min(128, int(bins)))
    _meta, items = _radiomics_for(source, ref, bins)

    # Stable, flattened column order: family.feature
    cols_keys: list[str] = []
    for fam, feats in items[0]["features"].items():
        for fname in feats:
            cols_keys.append(f"{fam}.{fname}")
    header = ["annotation_id", "label", "labels", "bi_rads", "frame", "type"] + cols_keys

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(header)
    for it in items:
        flat = {f"{fam}.{fn}": v for fam, feats in it["features"].items() for fn, v in feats.items()}
        row = [
            it["annotation_id"], it["label"] or "", ";".join(it["labels"]),
            it["bi_rads"], it["frame"], it["type"],
        ] + [flat.get(k, "") for k in cols_keys]
        writer.writerow(row)

    body = ("﻿" + buf.getvalue()).encode("utf-8")
    base = Path(ref).stem or "annotations"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return StreamingResponse(
        io.BytesIO(body),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{base}_radiomics_{stamp}.csv"'},
    )


@app.get("/api/stats/local_dicom")
def stats_local_dicom(_user: dict = Depends(auth_mod.require_user)):
    """LOCAL_DICOM_ROOT papkasidagi DICOM fayl va noyob bemorlar soni.
    Natija 10 daqiqaga keshlanadi (skanerlash juda sekin)."""
    import time
    cached = _cache_get("local_dicom_stats")
    if cached is not None:
        return cached

    if LOCAL_ROOT is None or not LOCAL_ROOT.is_dir():
        out = {
            "enabled": False,
            "root": LOCAL_ROOT_ENV or "(o'rnatilmagan)",
            "dicom_files": 0,
            "unique_patients": 0,
            "scan_duration_s": 0.0,
            "message": "LOCAL_DICOM_ROOT env-var sozlanmagan yoki papka mavjud emas",
        }
        _cache_set("local_dicom_stats", out)
        return out

    t0 = time.time()
    # 1. Fayllarni sanash (tez)
    dcm_files = []
    for ext in ("*.dcm", "*.cdcm", "*.DCM"):
        dcm_files.extend(LOCAL_ROOT.rglob(ext))
    n_files = len(dcm_files)

    # 2. Bemorlar (PatientID) — har faylni o'qib, header'dan olamiz
    # PatientID'lar to'plamida unique sanash. Katta fayllar — header o'qish tez,
    # ammo 5000+ fayl bo'lsa 10-30 sek bo'lishi mumkin.
    patient_ids: set[str] = set()
    by_modality: dict[str, int] = {}
    errors = 0
    for f in dcm_files:
        try:
            ds = pydicom.dcmread(str(f), stop_before_pixels=True, force=True, specific_tags=["PatientID", "Modality"])
            pid = str(getattr(ds, "PatientID", "") or "").strip()
            if pid:
                patient_ids.add(pid)
            mod = str(getattr(ds, "Modality", "") or "").strip() or "UNKNOWN"
            by_modality[mod] = by_modality.get(mod, 0) + 1
        except Exception:
            errors += 1
    dt = time.time() - t0

    # 3. Yuqori darajadagi papkalar (foydali ko'rsatkich)
    top_dirs = []
    try:
        for d in sorted(LOCAL_ROOT.iterdir()):
            if d.is_dir():
                n = sum(1 for _ in d.rglob("*.dcm")) + sum(1 for _ in d.rglob("*.cdcm"))
                top_dirs.append({"name": d.name, "dicom_count": n})
        top_dirs.sort(key=lambda x: -x["dicom_count"])
        top_dirs = top_dirs[:20]
    except Exception:
        top_dirs = []

    out = {
        "enabled": True,
        "root": str(LOCAL_ROOT),
        "dicom_files": n_files,
        "unique_patients": len(patient_ids),
        "by_modality": [{"modality": k, "count": v} for k, v in sorted(by_modality.items(), key=lambda x: -x[1])],
        "top_subdirs": top_dirs,
        "errors": errors,
        "scan_duration_s": round(dt, 2),
    }
    _cache_set("local_dicom_stats", out)
    return out


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


def _export_images() -> list[dict]:
    """Normalized per-image view used by YOLO/VOC/CSV/mask exporters."""
    out: list[dict] = []
    for entry in annot_store.iter_all(ANNOT_DIR):
        source = entry.get("source")
        ref = entry.get("ref")
        if not source or not ref:
            continue
        rows, cols = _resolve_dims(source, ref, entry.get("rows"), entry.get("cols"))
        out.append({
            "source": source,
            "ref": ref,
            "rows": rows,
            "cols": cols,
            "annotations": entry.get("annotations", []) or [],
        })
    return out


def _build_yolo_dataset_zip(imgsz: int = 1024, val_frac: float = 0.2, seed: int = 42) -> bytes:
    """Annotatsiyalardan TO'LIQ, yuklab olinadigan YOLO dataset:
        images/{train,val}/<id>.png + labels/{train,val}/<id>.txt + data.yaml
    Rasmlar DICOM'dan render qilinadi, train/val bemor darajasida bo'linadi."""
    import random
    import zipfile

    items: list[dict] = []
    label_set: set[str] = set()
    for ann_path in sorted(ANNOT_DIR.glob("upload__*.json")):
        file_id = ann_path.stem.replace("upload__", "", 1)
        dcm = UPLOAD_DIR / f"{file_id}.dcm"
        if not dcm.exists():
            continue
        try:
            data = json.loads(ann_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        kept = []
        for a in (data.get("annotations") or []):
            t = a.get("type")
            if t == "bbox" and a.get("bbox"):
                bx, by, bw, bh = a["bbox"][:4]
            elif t == "polygon" and a.get("points") and len(a["points"]) >= 3:
                bx, by, bw, bh = _polygon_to_bbox_pts(a["points"])
            else:
                continue
            lbl = str(a.get("label", "") or "lesion")
            kept.append({"label": lbl, "bbox": [bx, by, bw, bh]})
            label_set.add(lbl)
        if not kept:
            continue
        try:
            ds = pydicom.dcmread(str(dcm), stop_before_pixels=True, force=True)
            pid = str(getattr(ds, "PatientID", "") or "")
            suid = str(getattr(ds, "StudyInstanceUID", "") or "")
        except Exception:
            pid = suid = ""
        items.append({"file_id": file_id, "dcm": dcm, "annotations": kept, "group": pid or suid or file_id})

    if not items:
        raise HTTPException(400, "Annotatsiya bo'lgan fayl topilmadi")

    classes = sorted(label_set)
    cls_to_id = {n: i for i, n in enumerate(classes)}
    imgsz = max(256, min(4096, int(imgsz)))
    val_frac = max(0.0, min(0.5, float(val_frac)))
    rng = random.Random(seed)
    groups = sorted({it["group"] for it in items})
    rng.shuffle(groups)
    if len(groups) <= 1 and len(items) > 1:
        # Bitta bemor: rasm darajasida bo'linish (train bo'sh qolmasligi uchun)
        order = list(range(len(items)))
        rng.shuffle(order)
        n_val_items = max(1, int(round(len(items) * val_frac))) if val_frac > 0 else 0
        n_val_items = min(n_val_items, len(items) - 1)  # kamida 1 ta train
        val_idx = set(order[:n_val_items])
        for i, it in enumerate(items):
            it["_split"] = "val" if i in val_idx else "train"
    else:
        n_val_groups = max(1, int(round(len(groups) * val_frac))) if val_frac > 0 else 0
        if len(groups) > 1:
            n_val_groups = min(n_val_groups, len(groups) - 1)  # train bo'sh qolmasin
        val_groups = set(groups[:n_val_groups])
        for it in items:
            it["_split"] = "val" if it["group"] in val_groups else "train"

    n_train = n_val = 0
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for it in items:
            split = it["_split"]
            try:
                png = render_frame_png(it["dcm"], frame=0, max_dim=imgsz)
            except Exception:
                continue
            z.writestr(f"images/{split}/{it['file_id']}.png", png)
            lines = []
            for a in it["annotations"]:
                cid = cls_to_id.get(a["label"])
                if cid is None:
                    continue
                bx, by, bw, bh = a["bbox"]
                cx = max(0.0, min(1.0, bx + bw / 2.0))
                cy = max(0.0, min(1.0, by + bh / 2.0))
                bw = max(0.0, min(1.0, bw))
                bh = max(0.0, min(1.0, bh))
                if bw <= 0 or bh <= 0:
                    continue
                lines.append(f"{cid} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}")
            z.writestr(f"labels/{split}/{it['file_id']}.txt", ("\n".join(lines) + "\n") if lines else "")
            n_train, n_val = (n_train + 1, n_val) if split == "train" else (n_train, n_val + 1)
        names = "\n".join(f"  {i}: {n}" for i, n in enumerate(classes))
        z.writestr("data.yaml",
                   "# MAMOGRAF to'liq YOLO dataset (rasm + label + split)\n"
                   "path: .\ntrain: images/train\nval: images/val\n"
                   f"nc: {len(classes)}\nnames:\n{names}\n")
        z.writestr("README.txt",
                   "MAMOGRAF to'liq YOLO dataset.\n"
                   f"Train rasm: {n_train}, Val rasm: {n_val}, klasslar: {len(classes)}.\n\n"
                   "Foydalanish:\n"
                   "1) ZIP ni biror papkaga oching.\n"
                   "2) Model Studio'da 'data.yaml' yo'lini kiriting va o'qiting,\n"
                   "   yoki: yolo train data=data.yaml model=yolo11n.pt epochs=100 imgsz=1024\n")
    return buf.getvalue()


_EXPORT_FORMATS = {
    "coco": ("application/json", "json"),
    "yolo": ("application/zip", "zip"),
    "voc": ("application/zip", "zip"),
    "csv": ("text/csv; charset=utf-8", "csv"),
}


@app.get("/api/export")
def export(format: str = "coco", imgsz: int = 1024, val_frac: float = 0.2):
    fmt = format.lower()
    if fmt not in _EXPORT_FORMATS:
        raise HTTPException(400, f"unsupported format; use one of: {', '.join(_EXPORT_FORMATS)}")
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    media, ext = _EXPORT_FORMATS[fmt]

    if fmt == "coco":
        body = json.dumps(_build_coco(), ensure_ascii=False, indent=2).encode("utf-8")
        fname = f"annotations_coco_{stamp}.json"
    elif fmt == "yolo":
        # TO'LIQ dataset: rasmlar + label'lar + train/val + data.yaml (o'qitishga tayyor)
        body = _build_yolo_dataset_zip(imgsz=imgsz, val_frac=val_frac)
        fname = f"yolo_dataset_{stamp}.zip"
    else:
        images = _export_images()
        if fmt == "voc":
            body = exporters.build_voc_zip(images)
            fname = f"annotations_voc_{stamp}.zip"
        else:  # csv
            body = exporters.build_csv(images)
            fname = f"annotations_{stamp}.csv"

    return StreamingResponse(
        io.BytesIO(body),
        media_type=media,
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


ENSEMBLE_MODEL = "__ensemble__"


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
    tta: bool = False
    models: Optional[list[str]] = None  # for ensemble; default = all available


class BatchInferenceBody(BaseModel):
    items: list[dict]
    model: str
    conf: float = 0.25
    iou: float = 0.5
    imgsz: int = 1024
    auto_save: bool = False
    tta: bool = False
    models: Optional[list[str]] = None


def _run_inference(png_bytes: bytes, *, model: str, conf: float, iou: float, imgsz: int,
                   tta: bool, models: Optional[list[str]]):
    """Dispatch to a single model or the WBF ensemble of several models."""
    if model == ENSEMBLE_MODEL:
        names = models or [m["name"] for m in inf.list_models()]
        return inf.infer_ensemble(png_bytes, names, conf=conf, iou=iou, imgsz=imgsz, tta=tta)
    return inf.infer_png(png_bytes, model_name=model, conf=conf, iou=iou, imgsz=imgsz, tta=tta)


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
            inf_res = _run_inference(
                png_bytes, model=body.model, conf=body.conf, iou=body.iou,
                imgsz=body.imgsz, tta=body.tta, models=body.models,
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


# --------------------------------------------------------------------------- #
# (A3) Uncertainty heatmap — modellar kelishmagan joyni ko'rsatadi              #
# --------------------------------------------------------------------------- #
def _compute_uncertainty_map(
    per_model_dets: list[list[dict]],
    image_size_wh: tuple[int, int],
) -> "tuple[object, dict]":
    """Har piksel uchun noaniqlik = ovoz qarama-qarshiligi × o'rtacha ishonch.
    Tushuntirish:
      vote(p) = (necha model shu nuqtada lezyon ko'radi) / N
      disagree(p) = 4 · vote · (1 - vote)        — peak vote=0.5 da
      mean_conf(p) = ovoz bergan modellarning ishonchini o'rtachasi
      heat(p) = disagree · mean_conf             — ikkalasi yuqori bo'lsa qizil
    """
    import numpy as np
    W, H = image_size_wh
    n_models = max(1, len(per_model_dets))
    info = {"n_models": n_models, "max_heat": 0.0, "nonzero_pct": 0.0}
    if n_models < 2:
        return np.zeros((H, W), dtype=np.float32), info

    vote = np.zeros((H, W), dtype=np.float32)
    conf_sum = np.zeros((H, W), dtype=np.float32)

    for dets in per_model_dets:
        mask = np.zeros((H, W), dtype=bool)
        cmap = np.zeros((H, W), dtype=np.float32)
        for d in dets:
            bbox = d.get("bbox") or [0, 0, 0, 0]
            if len(bbox) < 4:
                continue
            # bbox normallashtirilgan [x,y,w,h] (0..1)
            x = int(round(float(bbox[0]) * W))
            y = int(round(float(bbox[1]) * H))
            w = int(round(float(bbox[2]) * W))
            h = int(round(float(bbox[3]) * H))
            x2 = max(0, min(W, x + w))
            y2 = max(0, min(H, y + h))
            x = max(0, min(W, x))
            y = max(0, min(H, y))
            if x2 <= x or y2 <= y:
                continue
            mask[y:y2, x:x2] = True
            c = float(d.get("confidence", 0.0))
            cmap[y:y2, x:x2] = np.maximum(cmap[y:y2, x:x2], c)
        vote += mask.astype(np.float32)
        conf_sum += cmap

    v_norm = vote / float(n_models)
    disagreement = 4.0 * v_norm * (1.0 - v_norm)
    with np.errstate(invalid="ignore", divide="ignore"):
        mean_conf = np.where(vote > 0, conf_sum / vote, 0.0)
    heat = (disagreement * mean_conf).astype(np.float32)

    info["max_heat"] = float(heat.max())
    info["nonzero_pct"] = float((heat > 0.01).mean() * 100.0)
    return heat, info


def _render_uncertainty_png(heat) -> bytes:
    """heat (HxW float32) -> RGBA PNG: sariq->qizil gradient, alpha = heat."""
    import numpy as np
    from PIL import Image
    H, W = heat.shape
    if heat.max() > 0:
        h = heat / heat.max()
    else:
        h = heat
    h = np.clip(h, 0.0, 1.0) ** 0.7  # gamma — yuqori qiymatlarni ko'rsatish uchun
    rgba = np.zeros((H, W, 4), dtype=np.uint8)
    rgba[..., 0] = 255                          # R doim 255
    rgba[..., 1] = (255 * (1.0 - h)).astype(np.uint8)  # G susayadi -> qizillashadi
    rgba[..., 2] = 0                            # B = 0
    rgba[..., 3] = (200 * h).astype(np.uint8)   # alpha = heat
    img = Image.fromarray(rgba, mode="RGBA")
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


@app.post("/api/inference/uncertainty")
@limiter.limit("10/minute")
def inference_uncertainty(
    request: Request,
    body: InferenceBody,
    _user: dict = Depends(auth_mod.require_user),
):
    """Bir nechta modelni ishga tushirib, noaniqlik xaritasini PNG sifatida qaytaradi.
    body.models — solishtirish uchun modellar ro'yxati (kamida 2 ta). Bo'sh bo'lsa — barchasi.
    """
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

    model_names = body.models or [m["name"] for m in inf.list_models()]
    if len(model_names) < 2:
        raise HTTPException(400, "Uncertainty kamida 2 ta modelni talab qiladi")

    per_model_dets: list[list[dict]] = []
    image_size_wh: Optional[tuple[int, int]] = None
    used_models: list[str] = []
    failed: list[str] = []
    for m in model_names:
        try:
            res = inf.infer_png(
                png_bytes, model_name=m,
                conf=body.conf, iou=body.iou, imgsz=body.imgsz, tta=body.tta,
            )
        except Exception:
            failed.append(m)
            continue
        per_model_dets.append(res.get("detections", []) or [])
        used_models.append(m)
        if image_size_wh is None:
            sz = res.get("image_size") or [0, 0]
            if len(sz) >= 2 and sz[0] > 0 and sz[1] > 0:
                image_size_wh = (int(sz[0]), int(sz[1]))

    if len(per_model_dets) < 2 or image_size_wh is None:
        raise HTTPException(503, f"Yetarli model ishlamadi (used={used_models}, failed={failed})")

    heat, info = _compute_uncertainty_map(per_model_dets, image_size_wh)
    png = _render_uncertainty_png(heat)

    headers = {
        "X-Uncertainty-Models": ",".join(used_models),
        "X-Uncertainty-Failed": ",".join(failed),
        "X-Uncertainty-MaxHeat": f"{info['max_heat']:.4f}",
        "X-Uncertainty-NonzeroPct": f"{info['nonzero_pct']:.2f}",
        "X-Uncertainty-ImageW": str(image_size_wh[0]),
        "X-Uncertainty-ImageH": str(image_size_wh[1]),
    }
    return StreamingResponse(io.BytesIO(png), media_type="image/png", headers=headers)


# --------------------------------------------------------------------------- #
# (A4) Smart-click segmentation — bir bosish bilan polygon                      #
# --------------------------------------------------------------------------- #
class SmartClickBody(BaseModel):
    source: str
    ref: str
    frame: int = 0
    x: float       # normallashtirilgan 0..1
    y: float       # normallashtirilgan 0..1
    wc: Optional[float] = None
    ww: Optional[float] = None
    tolerance: int = 25       # intensivlik chegaralari (0..255)
    max_area_frac: float = 0.15  # rasm yuzasidan ko'pi tashlanadi


@app.post("/api/inference/smart_click")
@limiter.limit("60/minute")
def inference_smart_click(
    request: Request,
    body: SmartClickBody,
    _user: dict = Depends(auth_mod.require_user),
):
    """OpenCV asosida flood-fill + kontur soddalashtirish.
    Bemorning bosgan nuqtasi atrofidagi o'xshash intensivlikdagi sohani topib,
    polygon nuqtalarini (normallashtirilgan) qaytaradi."""
    import numpy as np
    import cv2

    _validate_source(body.source)
    _validate_ref(body.source, body.ref)
    if not (0.0 <= body.x <= 1.0 and 0.0 <= body.y <= 1.0):
        raise HTTPException(400, "x, y normallashtirilgan 0..1 bo'lishi kerak")

    if body.source == "upload":
        path = UPLOAD_DIR / f"{body.ref}.dcm"
    else:
        path = _resolve_local(body.ref)

    try:
        png_bytes = render_frame_png(path, frame=body.frame, wc=body.wc, ww=body.ww, max_dim=2048)
    except Exception as e:
        raise HTTPException(500, f"render failed: {e}")

    arr = np.frombuffer(png_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise HTTPException(500, "Image decode failed")
    H, W = img.shape[:2]
    px = int(round(body.x * (W - 1)))
    py = int(round(body.y * (H - 1)))
    px = max(0, min(W - 1, px))
    py = max(0, min(H - 1, py))

    # Flood fill maska
    mask = np.zeros((H + 2, W + 2), dtype=np.uint8)
    tol = int(max(1, min(120, body.tolerance)))
    flags = 4 | cv2.FLOODFILL_FIXED_RANGE | (255 << 8)
    try:
        cv2.floodFill(img.copy(), mask, (px, py), 0, loDiff=tol, upDiff=tol, flags=flags)
    except Exception as e:
        raise HTTPException(500, f"floodFill failed: {e}")
    region = mask[1:-1, 1:-1]
    area = int(region.sum() // 255)
    max_area = int(body.max_area_frac * W * H)
    if area == 0:
        raise HTTPException(400, "Hech narsa topilmadi — boshqa nuqtaga bosing")
    if area > max_area:
        # Juda katta — morfologik eroziyaga harakat qilamiz
        k = max(3, min(31, int(min(W, H) * 0.005)) | 1)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
        region = cv2.erode(region, kernel, iterations=2)
        area = int(region.sum() // 255)
        if area > max_area or area == 0:
            raise HTTPException(400, f"Soha juda katta ({100*area/(W*H):.1f}% rasm) — toleranceni kamaytiring")

    # Kontur va polygon
    contours, _ = cv2.findContours(region, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        raise HTTPException(400, "Kontur topilmadi")
    # Bosilgan nuqtani o'z ichiga olgan eng katta konturni tanlaymiz
    best = None
    for c in contours:
        if cv2.pointPolygonTest(c, (px, py), False) >= 0:
            if best is None or cv2.contourArea(c) > cv2.contourArea(best):
                best = c
    if best is None:
        best = max(contours, key=cv2.contourArea)
    # Soddalashtirish: 0.3% perimeter
    eps = 0.003 * cv2.arcLength(best, True)
    approx = cv2.approxPolyDP(best, eps, True)
    if len(approx) < 3:
        # juda agressiv — kamroq qiling
        approx = cv2.approxPolyDP(best, eps * 0.3, True)
    if len(approx) < 3:
        raise HTTPException(400, "Polygon yaratib bo'lmadi")

    pts = [[float(p[0][0]) / W, float(p[0][1]) / H] for p in approx]

    return {
        "points": pts,
        "image_size": [W, H],
        "click_pixel": [px, py],
        "area_pixels": area,
        "area_pct": round(100.0 * area / (W * H), 3),
        "n_vertices": len(pts),
    }


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
        result = _run_inference(
            png_bytes, model=body.model, conf=body.conf, iou=body.iou,
            imgsz=body.imgsz, tta=body.tta, models=body.models,
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
