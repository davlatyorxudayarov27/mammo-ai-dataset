# -*- coding: utf-8 -*-
"""MAMOGRAF — to'liq UI skrinshotlari (playwright/chromium).

Server :8002 da ishlab turishi va `demo`/`Demo12345!` admin user bo'lishi kerak.
Barcha asosiy ekranlarni doc_assets/ ga saqlaydi.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright
from pydicom.data import get_testdata_file

BASE = "http://127.0.0.1:8002"
OUT = Path(__file__).resolve().parent.parent / "doc_assets"
OUT.mkdir(exist_ok=True)
USER, PWD = "demo", "Demo12345!"
SAMPLE = get_testdata_file("examples_jpeg2k.dcm")


def shot(page, name):
    page.screenshot(path=str(OUT / name))
    print(name, "OK")


def open_modal(page, btn_id, name, settle=900):
    """Toolbar tugmasini bosib, modalni skrinshot qiladi."""
    try:
        page.evaluate(f"document.getElementById('{btn_id}')?.click()")
        page.wait_for_timeout(settle)
        shot(page, name)
        # modalni yopish (Escape yoki overlayni yashirish)
        page.keyboard.press("Escape")
        page.wait_for_timeout(250)
    except Exception as e:
        print(f"{name} SKIP:", e)


def run():
    sample_bytes = Path(SAMPLE).read_bytes()
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(viewport={"width": 1480, "height": 920},
                                  device_scale_factor=2)
        page = ctx.new_page()

        # 1) Login
        page.goto(BASE, wait_until="domcontentloaded")
        page.wait_for_selector("#loginModal", state="visible", timeout=10000)
        page.wait_for_timeout(600)
        shot(page, "ui_login.png")

        page.fill("#loginUsername", USER)
        page.fill("#loginPassword", PWD)
        page.click("#loginSubmit")
        page.wait_for_selector("#loginModal", state="hidden", timeout=10000)
        page.wait_for_timeout(900)
        token = page.evaluate("localStorage.getItem('mamograf_jwt')")
        print("token:", "yes" if token else "NO")

        # 2) Namuna DICOM yuklash
        file_id = None
        try:
            resp = ctx.request.post(
                BASE + "/api/upload",
                headers={"Authorization": f"Bearer {token}"},
                multipart={"files": {"name": "namuna.dcm",
                                     "mimeType": "application/dicom",
                                     "buffer": sample_bytes}},
            )
            j = resp.json()
            file_id = j["files"][0]["id"]
            rows = j["files"][0].get("rows") or 640
            cols = j["files"][0].get("cols") or 480
            print("upload OK:", file_id, rows, cols)
        except Exception as e:
            print("upload error:", e)
            rows, cols = 640, 480

        # 3) Annotatsiya qo'shish (massa + BI-RADS 4B)
        if file_id:
            try:
                ann = {
                    "source": "upload", "ref": file_id, "rows": rows, "cols": cols,
                    "annotations": [{
                        "id": "demo1", "type": "box", "label": "massa",
                        "labels": ["massa"], "bi_rads": "4B",
                        "bbox": [0.30, 0.26, 0.20, 0.18], "frame": 0,
                        "note": "shubhali o'choq",
                    }],
                }
                r2 = ctx.request.put(
                    BASE + "/api/annotations",
                    headers={"Authorization": f"Bearer {token}",
                             "Content-Type": "application/json"},
                    data=json.dumps(ann),
                )
                print("annotation PUT:", r2.status)
            except Exception as e:
                print("annotation error:", e)

        # 4) Viewer — faylni tanlab, annotatsiyani ko'rsatish
        page.reload(wait_until="domcontentloaded")
        page.wait_for_timeout(1500)
        try:
            page.wait_for_selector("#uploadList li.file", timeout=8000)
            page.click("#uploadList li.file")
            page.wait_for_timeout(3000)
        except Exception as e:
            print("file select error:", e)
        shot(page, "ui_viewer.png")

        # 5) Hisobot modali — generatsiya kutib skrinshot
        try:
            page.evaluate("document.getElementById('reportBtn')?.click()")
            # report matni paydo bo'lishini kutamiz (Ollama ~10s)
            page.wait_for_function(
                "() => { const t=document.getElementById('reportText'); return t && t.value && t.value.length>40; }",
                timeout=60000,
            )
            page.wait_for_timeout(800)
            shot(page, "ui_report.png")
            page.evaluate("document.getElementById('reportCloseBtn')?.click()")
            page.wait_for_timeout(300)
        except Exception as e:
            print("ui_report SKIP:", e)
            try:
                shot(page, "ui_report.png")
            except Exception:
                pass

        # 6) Modallar (toolbar tugmalari)
        open_modal(page, "statsBtn", "ui_stats.png", settle=1500)
        open_modal(page, "modelMgrBtn", "ui_models.png", settle=1200)
        open_modal(page, "pacsBtn", "ui_pacs.png", settle=900)
        open_modal(page, "trainPrepBtn", "ui_datasetprep.png", settle=900)
        open_modal(page, "auditBtn", "ui_audit.png", settle=1200)
        open_modal(page, "adminBtn", "ui_admin.png", settle=1200)

        # 7) Model Studio (alohida sahifa)
        page.evaluate("(t) => localStorage.setItem('mamograf_jwt', t)", token)
        page.goto(BASE + "/train.html", wait_until="domcontentloaded")
        page.wait_for_timeout(2500)
        shot(page, "ui_studio.png")

        browser.close()


if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        print("FATAL:", e)
        sys.exit(1)
