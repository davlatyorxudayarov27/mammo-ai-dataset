# -*- coding: utf-8 -*-
"""aiscan.airi.uz (yoki boshqa MAMOGRAF serveri) dan annotatsiyalangan
DICOM'lar + annotatsiyalarni LOKAL app'ga ko'chirish.

Ishlatish:
    1) Brauzerda aiscan.airi.uz ga admin/reviewer bo'lib kiring.
    2) F12 -> Console -> quyidagini yozib, chiqqan tokenni nusxalang:
           localStorage.getItem('mamograf_jwt')
    3) Pastdagi BASE va TOKEN ni to'ldiring (yoki USER/PWD ni).
    4) Loyiha papkasida ishga tushiring:
           .venv\\Scripts\\python.exe scripts\\pull_from_aiscan.py

Natija: app/uploads/<id>.dcm va app/annotations/upload__<id>.json fayllar.
So'ng lokal serverni yoqib, Model Studio'da o'qitasiz yoki
http://127.0.0.1:8002/api/export?format=yolo dan to'liq dataset olasiz.
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

# ===================== SOZLAMALAR (to'ldiring) =====================
BASE = "https://aiscan.airi.uz"          # server manzili
TOKEN = ""                                # browser localStorage.getItem('mamograf_jwt')
USER = ""                                 # TOKEN bo'sh bo'lsa: login uchun
PWD = ""
TOTP = ""                                 # 2FA yoqilgan bo'lsa kodi (aks holda bo'sh)
# ===================================================================

ROOT = Path(__file__).resolve().parent.parent
UPLOADS = ROOT / "app" / "uploads"
ANNOTS = ROOT / "app" / "annotations"
TIMEOUT = 120


def _req(url, token=None, data=None, raw=False):
    req = urllib.request.Request(url, method="POST" if data is not None else "GET")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    if data is not None:
        req.add_header("Content-Type", "application/json")
        data = json.dumps(data).encode("utf-8")
    with urllib.request.urlopen(req, data=data, timeout=TIMEOUT) as r:
        body = r.read()
    return body if raw else json.loads(body)


def login() -> str:
    payload = {"username": USER, "password": PWD}
    if TOTP:
        payload["totp_code"] = TOTP
    return _req(f"{BASE}/api/auth/login", data=payload)["token"]


def main():
    token = TOKEN
    if not token:
        if not (USER and PWD):
            print("XATO: TOKEN yoki USER/PWD ni to'ldiring (fayl boshidagi izohga qarang).")
            sys.exit(1)
        try:
            token = login()
            print("Login OK")
        except Exception as e:
            print("Login xato:", e)
            sys.exit(1)

    UPLOADS.mkdir(parents=True, exist_ok=True)
    ANNOTS.mkdir(parents=True, exist_ok=True)

    files = _req(f"{BASE}/api/files").get("files", [])
    annotated = [f for f in files if f.get("annotation_count")]
    print(f"Serverda {len(files)} fayl, shundan {len(annotated)} ta annotatsiyalangan.")
    if not annotated:
        print("Annotatsiyalangan fayl topilmadi.")
        return

    ok = anns_total = 0
    for i, f in enumerate(annotated, 1):
        fid = f["id"]
        try:
            ann = _req(f"{BASE}/api/annotations?source=upload&ref={fid}")
            (ANNOTS / f"upload__{fid}.json").write_text(
                json.dumps(ann, ensure_ascii=False), encoding="utf-8")
            dcm = _req(f"{BASE}/api/deidentify/download?source=upload&ref={fid}",
                       token=token, raw=True)
            (UPLOADS / f"{fid}.dcm").write_bytes(dcm)
            n = len(ann.get("annotations") or [])
            anns_total += n
            ok += 1
            print(f"  [{i}/{len(annotated)}] {fid}  ({n} ta annotatsiya) OK")
        except Exception as e:
            print(f"  [{i}/{len(annotated)}] {fid}  XATO: {e}")

    print(f"\nTUGADI: {ok} ta fayl + jami {anns_total} ta annotatsiya ko'chirildi.")
    print("Endi lokal serverni yoqib (run.bat), Model Studio'da o'qiting yoki")
    print("http://127.0.0.1:8002/api/export?format=yolo dan to'liq dataset oling.")


if __name__ == "__main__":
    main()
