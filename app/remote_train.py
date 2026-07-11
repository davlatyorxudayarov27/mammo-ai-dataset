"""
Masofaviy (GPU server) training klienti.

REMOTE_TRAIN_URL env o'rnatilgan bo'lsa, Model Studio'dagi ▶ Train lokal
subprocess o'rniga GPU serverdagi train_server.py xizmatiga jo'natiladi:
dataset zip qilib yuklanadi, status/log proxy qilinadi, tayyor best.pt
qaytarib olinadi. URL bo'sh bo'lsa — ENABLED=False, eski lokal yo'l ishlaydi.
"""
from __future__ import annotations

import io
import os
import json
import tempfile
import zipfile
from pathlib import Path

import httpx

REMOTE_URL = os.environ.get("REMOTE_TRAIN_URL", "").strip().rstrip("/")
REMOTE_TOKEN = os.environ.get("REMOTE_TRAIN_TOKEN", "").strip()
ENABLED = bool(REMOTE_URL)

# Dataset yuklash / model yuklab olish uchun keng timeout (sekund)
_TIMEOUT = httpx.Timeout(connect=15.0, read=1200.0, write=1200.0, pool=15.0)
_STATUS_TIMEOUT = httpx.Timeout(connect=10.0, read=60.0, write=60.0, pool=10.0)


def _headers() -> dict:
    return {"X-Train-Token": REMOTE_TOKEN} if REMOTE_TOKEN else {}


def health() -> dict:
    r = httpx.get(f"{REMOTE_URL}/health", headers=_headers(), timeout=_STATUS_TIMEOUT)
    r.raise_for_status()
    return r.json()


def _zip_dataset_to_tmp(dataset_dir: Path) -> Path:
    """Dataset papkasini vaqtinchalik zip faylga (siqishsiz) joylaydi."""
    tmp = tempfile.NamedTemporaryFile(prefix="ds_", suffix=".zip", delete=False)
    tmp.close()
    with zipfile.ZipFile(tmp.name, "w", zipfile.ZIP_STORED) as z:
        for f in dataset_dir.rglob("*"):
            if f.is_file():
                z.write(f, f.relative_to(dataset_dir))
    return Path(tmp.name)


def push_dataset(name: str, dataset_dir: Path) -> dict:
    """Dataset papkasini GPU serverga oldindan (tayyorlash paytida) yuklaydi.

    GPU `datasets/<name>/` ga ochib saqlaydi; keyin submit(dataset_name=...)
    qayta yuklamasdan ishlatadi → ▶ Train darhol boshlanadi."""
    zip_path = _zip_dataset_to_tmp(Path(dataset_dir))
    try:
        with open(zip_path, "rb") as zf:
            files = {"dataset": ("dataset.zip", zf, "application/zip")}
            r = httpx.post(f"{REMOTE_URL}/datasets", data={"name": name}, files=files,
                           headers=_headers(), timeout=_TIMEOUT)
        r.raise_for_status()
        return r.json()
    finally:
        try:
            zip_path.unlink()
        except Exception:
            pass


def list_datasets() -> dict:
    r = httpx.get(f"{REMOTE_URL}/datasets", headers=_headers(), timeout=_STATUS_TIMEOUT)
    r.raise_for_status()
    return r.json()


def delete_dataset(name: str) -> dict:
    r = httpx.delete(f"{REMOTE_URL}/datasets/{name}", headers=_headers(), timeout=_STATUS_TIMEOUT)
    r.raise_for_status()
    return r.json()


def submit(run_id: str, params: dict, models_dir: str) -> dict:
    """Parametrlarni GPU serverga jo'natadi va training boshlaydi.

    `params["dataset_name"]` bo'lsa — dataset GPU'da allaqachon mavjud (push_dataset
    bilan tayyorlash paytida yuklangan), shu sabab zip yuborilmaydi → darhol start.
    Aks holda eski yo'l: dataset zip qilib yuboriladi."""
    wp = dict(params)
    wp["run_id"] = run_id
    form = {"params": json.dumps(wp, ensure_ascii=False)}

    # Lokal trained_*.pt base model bo'lsa — uni ham yuklaymiz
    base_model = (params.get("base_model") or "").strip()
    bm_path = Path(models_dir) / base_model if base_model else None
    bm_is_file = bool(bm_path and bm_path.exists() and bm_path.is_file())

    dataset_name = (params.get("dataset_name") or "").strip()

    # --- Tez yo'l: dataset GPU'da oldindan mavjud, faqat parametr yuboramiz --- #
    if dataset_name:
        bm_fh = None
        files = {}
        if bm_is_file:
            bm_fh = open(bm_path, "rb")
            files["base_model_file"] = (bm_path.name, bm_fh, "application/octet-stream")
        try:
            r = httpx.post(f"{REMOTE_URL}/jobs", data=form, files=(files or None),
                           headers=_headers(), timeout=_TIMEOUT)
        finally:
            if bm_fh:
                bm_fh.close()
        r.raise_for_status()
        return r.json()

    # --- Eski yo'l: dataset zip qilib yuboriladi (dataset_name yo'q bo'lsa) --- #
    data_yaml = Path(params["data_yaml"])
    dataset_dir = data_yaml.parent
    zip_path = _zip_dataset_to_tmp(dataset_dir)
    try:
        with open(zip_path, "rb") as zf:
            files = {"dataset": ("dataset.zip", zf, "application/zip")}
            bm_fh = None
            if bm_is_file:
                bm_fh = open(bm_path, "rb")
                files["base_model_file"] = (bm_path.name, bm_fh, "application/octet-stream")
            try:
                r = httpx.post(f"{REMOTE_URL}/jobs", data=form, files=files,
                               headers=_headers(), timeout=_TIMEOUT)
            finally:
                if bm_fh:
                    bm_fh.close()
        r.raise_for_status()
        return r.json()
    finally:
        try:
            zip_path.unlink()
        except Exception:
            pass


def status(run_id: str, tail: int = 200) -> dict:
    r = httpx.get(f"{REMOTE_URL}/jobs/{run_id}/status",
                  params={"tail": tail}, headers=_headers(), timeout=_STATUS_TIMEOUT)
    r.raise_for_status()
    return r.json()


def stop(run_id: str) -> dict:
    r = httpx.post(f"{REMOTE_URL}/jobs/{run_id}/stop",
                   headers=_headers(), timeout=_STATUS_TIMEOUT)
    r.raise_for_status()
    return r.json()


def download_best(run_id: str) -> bytes:
    r = httpx.get(f"{REMOTE_URL}/jobs/{run_id}/best",
                  headers=_headers(), timeout=_TIMEOUT)
    r.raise_for_status()
    return r.content
