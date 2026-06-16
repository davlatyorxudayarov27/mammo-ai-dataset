# -*- coding: utf-8 -*-
"""MAMOGRAF UI skrinshotlari — playwright (chromium).

Server oldindan ishga tushgan bo'lishi kerak (uvicorn :8099).
"""
from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright
from pydicom.data import get_testdata_file

BASE = "http://127.0.0.1:8099"
OUT = Path(__file__).resolve().parent.parent / "doc_assets"
OUT.mkdir(exist_ok=True)
USER, PWD = "demo", "Demo12345!"

SAMPLE = get_testdata_file("examples_jpeg2k.dcm")  # 480x640 namuna


def run():
    sample_bytes = Path(SAMPLE).read_bytes()
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(viewport={"width": 1480, "height": 920},
                                  device_scale_factor=2)
        page = ctx.new_page()

        # 1) Login ekrani
        page.goto(BASE, wait_until="domcontentloaded")
        page.wait_for_selector("#loginModal", state="visible", timeout=10000)
        page.wait_for_timeout(600)
        page.screenshot(path=str(OUT / "ui_login.png"))
        print("ui_login.png OK")

        # login
        page.fill("#loginUsername", USER)
        page.fill("#loginPassword", PWD)
        page.click("#loginSubmit")
        page.wait_for_selector("#loginModal", state="hidden", timeout=10000)
        page.wait_for_timeout(1000)
        token = page.evaluate("localStorage.getItem('mamograf_jwt')")
        print("token:", "yes" if token else "NO")

        # 2) Namuna DICOM yuklash (API orqali, Bearer bilan)
        try:
            resp = ctx.request.post(
                BASE + "/api/upload",
                headers={"Authorization": f"Bearer {token}"},
                multipart={"files": {"name": "namuna.dcm",
                                     "mimeType": "application/dicom",
                                     "buffer": sample_bytes}},
            )
            print("upload status:", resp.status)
        except Exception as e:
            print("upload error:", e)

        # 3) Viewer — faylni tanlab, rasmni ko'rsatish
        page.reload(wait_until="domcontentloaded")
        page.wait_for_timeout(1500)
        try:
            page.wait_for_selector("#uploadList li.file", timeout=8000)
            page.click("#uploadList li.file")
            page.wait_for_timeout(3000)  # render kutish
        except Exception as e:
            print("file select error:", e)
        page.screenshot(path=str(OUT / "ui_viewer.png"))
        print("ui_viewer.png OK")

        # 4) Model Studio (train.html)
        page.evaluate("(t) => localStorage.setItem('mamograf_token', t)", token)
        page.goto(BASE + "/train.html", wait_until="domcontentloaded")
        page.wait_for_timeout(2000)
        page.screenshot(path=str(OUT / "ui_studio.png"))
        print("ui_studio.png OK")

        browser.close()


if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        print("FATAL:", e)
        sys.exit(1)
