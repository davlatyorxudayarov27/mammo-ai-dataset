"""
Build PDF documentation with screenshots.

Usage:
    python build_pdf.py

Yaratadi:
    docs/screenshots/*.png
    FOYDALANUVCHI_QOLLANMA.pdf
"""
from __future__ import annotations

import asyncio
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import markdown
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
SHOTS = DOCS / "screenshots"
MD_FILE = ROOT / "FOYDALANUVCHI_QOLLANMA.md"
PDF_FILE = ROOT / "FOYDALANUVCHI_QOLLANMA.pdf"
HTML_FILE = DOCS / "_manual.html"

BASE_URL = "http://127.0.0.1:8765"
ADMIN_USER = "admin"
ADMIN_PASS = "admin123"


async def wait_visible(page, sel, timeout=8000):
    await page.wait_for_selector(sel + ":not([hidden])", timeout=timeout)


async def login(page):
    await page.goto(BASE_URL, wait_until="networkidle")
    await wait_visible(page, "#loginModal")
    await page.fill("#loginUsername", ADMIN_USER)
    await page.fill("#loginPassword", ADMIN_PASS)
    await page.click("#loginSubmit")
    await page.wait_for_function(
        "() => { const m = document.getElementById('loginModal'); return !m || m.hidden; }",
        timeout=10000,
    )
    await page.wait_for_timeout(800)


async def shoot(page, name: str, full_page: bool = False):
    SHOTS.mkdir(parents=True, exist_ok=True)
    out = SHOTS / f"{name}.png"
    await page.screenshot(path=str(out), full_page=full_page)
    print(f"   ✓ {out.name}")
    return out.name


async def open_dicom_local(page, ref: str):
    await page.click('button.tab[data-tab="local"]')
    await page.wait_for_timeout(400)
    await page.click(f'#localList li[data-path="{ref}"]')
    await page.wait_for_function(
        "() => !document.getElementById('imgStack').hidden",
        timeout=15000,
    )
    await page.wait_for_timeout(1500)


async def add_demo_annotation(page):
    label_sel = await page.query_selector("#labelSelect")
    if label_sel:
        opts = await label_sel.query_selector_all("option")
        if opts:
            await page.select_option("#labelSelect", index=0)
    await page.click("#toolBbox")
    box = await page.bounding_box("#canvasWrap")
    if box:
        cx, cy = box["x"] + box["width"] * 0.45, box["y"] + box["height"] * 0.40
        await page.mouse.move(cx, cy)
        await page.mouse.down()
        await page.mouse.move(cx + 100, cy + 100, steps=10)
        await page.mouse.up()
        await page.wait_for_timeout(1500)
    await page.click("#toolSelect")
    await page.wait_for_timeout(400)


async def take_all(page):
    print(" 1. Login modal...")
    await page.goto(BASE_URL, wait_until="networkidle")
    await wait_visible(page, "#loginModal")
    await shoot(page, "01_login")

    print(" 2. Login...")
    await page.fill("#loginUsername", ADMIN_USER)
    await page.fill("#loginPassword", ADMIN_PASS)
    await page.click("#loginSubmit")
    await page.wait_for_function(
        "() => { const m = document.getElementById('loginModal'); return !m || m.hidden; }",
        timeout=10000,
    )
    await page.wait_for_timeout(1000)

    print(" 3. Empty main UI...")
    await shoot(page, "02_empty_ui")

    print(" 4. Open DICOM...")
    try:
        await open_dicom_local(page, "DCMDT/D0000000.dcm")
    except Exception as e:
        print(f"    ! DICOM ochishda xato: {e}")

    print(" 5. DICOM viewer with image...")
    await shoot(page, "03_dicom_viewer")

    print(" 6. Add demo bbox...")
    try:
        await add_demo_annotation(page)
        await shoot(page, "04_with_annotation")
    except Exception as e:
        print(f"    ! annotation xato: {e}")

    print(" 7. Right pane: Annotations tab...")
    try:
        await page.click('.meta-pane .tab[data-rtab="anno"]')
        await page.wait_for_timeout(400)
        await shoot(page, "05_annotations_tab")
    except Exception:
        pass

    print(" 8. Right pane: Hisobot tab...")
    try:
        await page.click('.meta-pane .tab[data-rtab="report"]')
        await page.wait_for_timeout(800)
        await shoot(page, "06_report_tab")
    except Exception:
        pass

    print(" 9. Stats modal...")
    try:
        await page.click("#statsBtn")
        await wait_visible(page, "#statsModal")
        await page.wait_for_timeout(800)
        await shoot(page, "07_stats_modal")
        await page.click("#statsCloseBtn")
        await page.wait_for_timeout(300)
    except Exception as e:
        print(f"    ! stats: {e}")

    print("10. Audit timeline...")
    try:
        await page.click("#auditBtn")
        await wait_visible(page, "#auditModal")
        await page.wait_for_timeout(600)
        await shoot(page, "08_audit_modal")
        await page.click("#auditCloseBtn")
        await page.wait_for_timeout(300)
    except Exception as e:
        print(f"    ! audit: {e}")

    print("11. Overview modal...")
    try:
        await page.click("#overviewBtn")
        await wait_visible(page, "#overviewModal")
        await page.wait_for_timeout(600)
        await shoot(page, "09_overview_modal")
        await page.click("#overviewCloseBtn")
        await page.wait_for_timeout(300)
    except Exception as e:
        print(f"    ! overview: {e}")

    print("12. PACS modal...")
    try:
        await page.click("#pacsBtn")
        await wait_visible(page, "#pacsModal")
        await page.wait_for_timeout(500)
        await shoot(page, "10_pacs_modal")
        await page.click("#pacsCloseBtn")
        await page.wait_for_timeout(300)
    except Exception as e:
        print(f"    ! pacs: {e}")

    print("13. Admin modal...")
    try:
        await page.click("#adminBtn")
        await wait_visible(page, "#adminModal")
        await page.wait_for_timeout(800)
        await shoot(page, "11_admin_modal")
        await page.click("#adminCloseBtn")
        await page.wait_for_timeout(300)
    except Exception as e:
        print(f"    ! admin: {e}")

    print("14. TOTP modal...")
    try:
        await page.click("#totpBtn")
        await wait_visible(page, "#totpModal")
        await page.wait_for_timeout(1500)
        await shoot(page, "12_totp_modal")
        await page.click("#totpCloseBtn")
        await page.wait_for_timeout(300)
    except Exception as e:
        print(f"    ! totp: {e}")

    print("15. Worklist tab...")
    try:
        await page.click('button.tab[data-tab="worklist"]')
        await page.wait_for_timeout(800)
        await shoot(page, "13_worklist")
    except Exception as e:
        print(f"    ! worklist: {e}")

    print("16. Mening ishim tab...")
    try:
        await page.click('button.tab[data-tab="dashboard"]')
        await page.wait_for_timeout(800)
        await shoot(page, "14_dashboard")
    except Exception as e:
        print(f"    ! dashboard: {e}")

    print("17. Cleanup demo annotations...")
    try:
        token = await page.evaluate("() => localStorage.getItem('mamograf_jwt')")
        import urllib.request
        req = urllib.request.Request(
            f"{BASE_URL}/api/annotations",
            data=b'{"source":"local","ref":"DCMDT/D0000000.dcm","annotations":[]}',
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
            method="PUT",
        )
        urllib.request.urlopen(req, timeout=5).read()
    except Exception:
        pass


SHOT_PLACEMENTS = {
    r"## 1\. Boshlash": "01_login",
    r"## 2\. Asosiy interfeys": "02_empty_ui",
    r"## 4\. DICOM ochish va ko'rish": "03_dicom_viewer",
    r"## 5\. Annotatsiya jarayoni": "04_with_annotation",
    r"### 5\.5 O'ng panelda annotatsiyalar": "05_annotations_tab",
    r"## 6\. Hisobot tab": "06_report_tab",
    r"## 9\. PACS integratsiyasi": "10_pacs_modal",
    r"## 12\. Admin paneli": "11_admin_modal",
    r"## 13\. Statistika": "07_stats_modal",
    r"## 14\. Audit timeline": "08_audit_modal",
    r"## 15\. Annotated DICOMs overview": "09_overview_modal",
    r"## 16\. 2FA \(Two-Factor Authentication\)": "12_totp_modal",
    r"## 17\. Worklist": "13_worklist",
    r"### Annotator \(radiolog stajori\)": "14_dashboard",
}


CSS = """
@page {
  size: A4;
  margin: 18mm 16mm 18mm 18mm;
  @bottom-right {
    content: counter(page) " / " counter(pages);
    color: #888;
    font-size: 9pt;
  }
}
body {
  font-family: "Segoe UI", "Arial", sans-serif;
  font-size: 10pt;
  line-height: 1.5;
  color: #1a1a1a;
  margin: 0;
}
h1 { color: #1f6feb; border-bottom: 2px solid #1f6feb; padding-bottom: 4px; }
h2 { color: #1f6feb; margin-top: 22px; border-bottom: 1px solid #cdd5e0; padding-bottom: 3px; page-break-after: avoid; }
h3 { color: #2b3344; margin-top: 14px; page-break-after: avoid; }
h4 { color: #2b3344; margin-top: 10px; }
table { border-collapse: collapse; width: 100%; margin: 8px 0 14px; font-size: 9pt; page-break-inside: avoid; }
table th, table td { border: 1px solid #d0d7de; padding: 4px 7px; text-align: left; vertical-align: top; }
table th { background: #f0f4fa; font-weight: 600; }
code, pre { background: #f4f5f7; border-radius: 3px; font-family: "Cascadia Mono", "Consolas", monospace; }
code { padding: 1px 4px; font-size: 9pt; }
pre { padding: 8px 10px; font-size: 8.5pt; overflow-x: auto; page-break-inside: avoid; }
ul, ol { margin: 6px 0 12px 22px; padding: 0; }
li { margin: 2px 0; }
img.shot { max-width: 100%; border: 1px solid #cdd5e0; border-radius: 4px; margin: 12px 0; box-shadow: 0 2px 6px rgba(0,0,0,0.08); page-break-inside: avoid; }
.cover { text-align: center; margin-top: 80mm; page-break-after: always; }
.cover h1 { font-size: 26pt; border: none; }
.cover .sub { color: #555; font-size: 13pt; margin-top: 6px; }
.cover .meta { color: #888; font-size: 10pt; margin-top: 24px; }
.toc { page-break-after: always; }
.toc ul { list-style: none; margin-left: 0; }
.toc li { margin: 3px 0; }
.toc a { text-decoration: none; color: #1f6feb; }
hr { border: none; border-top: 1px solid #cdd5e0; margin: 18px 0; }
"""


def _slugify(text: str) -> str:
    s = re.sub(r"[^\w\s-]", "", text).strip().lower()
    return re.sub(r"\s+", "-", s)


def build_html(md_text: str, screenshots: dict[str, str]) -> str:
    lines = md_text.splitlines()
    out_lines = []
    h1_done = False
    for i, ln in enumerate(lines):
        for pattern, name in SHOT_PLACEMENTS.items():
            if re.match(pattern, ln) and name in screenshots:
                pass
        if ln.startswith("## "):
            for pattern, name in SHOT_PLACEMENTS.items():
                if re.match(pattern, ln) and name in screenshots:
                    out_lines.append(ln)
                    out_lines.append("")
                    out_lines.append(f"![{name}](screenshots/{name}.png)")
                    out_lines.append("")
                    break
            else:
                out_lines.append(ln)
        elif ln.startswith("### "):
            for pattern, name in SHOT_PLACEMENTS.items():
                if re.match(pattern, ln) and name in screenshots:
                    out_lines.append(ln)
                    out_lines.append("")
                    out_lines.append(f"![{name}](screenshots/{name}.png)")
                    out_lines.append("")
                    break
            else:
                out_lines.append(ln)
        else:
            out_lines.append(ln)

    annotated = "\n".join(out_lines)
    body_html = markdown.markdown(
        annotated,
        extensions=["tables", "fenced_code", "toc"],
    )
    body_html = re.sub(r'<img([^>]*)>', r'<img class="shot"\1>', body_html)

    headings = []
    for ln in lines:
        m = re.match(r"^(#{1,3}) (.+)$", ln)
        if m and len(m.group(1)) <= 2:
            level = len(m.group(1))
            text = m.group(2).strip()
            if level == 1 and h1_done:
                continue
            if level == 1:
                h1_done = True
                continue
            headings.append((level, text))

    toc_items = []
    for level, text in headings[:30]:
        toc_items.append(f'<li style="margin-left:{(level-2)*14}px">{text}</li>')
    toc_html = "<ul>" + "".join(toc_items) + "</ul>"

    cover = f"""
    <div class="cover">
      <h1>MAMOGRAF DICOM Viewer</h1>
      <div class="sub">Foydalanuvchi qo'llanmasi</div>
      <div class="meta">{time.strftime('%Y-%m-%d')}</div>
    </div>
    <div class="toc">
      <h2 style="border:none">Mundarija</h2>
      {toc_html}
    </div>
    """

    return f"""<!doctype html>
<html lang="uz">
<head>
<meta charset="utf-8" />
<title>MAMOGRAF — Foydalanuvchi qo'llanmasi</title>
<style>{CSS}</style>
</head>
<body>
{cover}
{body_html}
</body>
</html>
"""


async def render_pdf(html_path: Path, pdf_path: Path):
    print(f"\n[render] {pdf_path.name} chiqarilmoqda...")
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(html_path.resolve().as_uri(), wait_until="networkidle")
        await page.wait_for_timeout(800)
        await page.pdf(
            path=str(pdf_path),
            format="A4",
            margin={"top": "18mm", "bottom": "18mm", "left": "18mm", "right": "16mm"},
            print_background=True,
            display_header_footer=False,
        )
        await browser.close()
    sz = pdf_path.stat().st_size
    print(f"[ok] {pdf_path} — {sz/1024/1024:.2f} MB")


async def capture_phase():
    print("[capture] brauzer ochilmoqda...")
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        ctx = await browser.new_context(
            viewport={"width": 1600, "height": 950},
            device_scale_factor=1,
        )
        page = await ctx.new_page()
        try:
            await take_all(page)
        finally:
            await browser.close()


def start_server() -> subprocess.Popen:
    print("[server] ishga tushirilmoqda...")
    env = {
        **__import__("os").environ,
        "LOCAL_DICOM_ROOT": str(ROOT.parent / "dicomfiles"),
    }
    cmd = [
        str(ROOT / ".venv" / "Scripts" / "python.exe"),
        "-m", "uvicorn", "app.main:app",
        "--host", "127.0.0.1", "--port", "8765",
        "--log-level", "warning",
    ]
    proc = subprocess.Popen(cmd, cwd=str(ROOT), env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    import urllib.request, urllib.error
    for _ in range(40):
        try:
            urllib.request.urlopen(f"{BASE_URL}/api/config", timeout=1).read()
            print("[server] tayyor")
            return proc
        except (urllib.error.URLError, ConnectionError):
            time.sleep(0.5)
    raise RuntimeError("server javob bermadi")


async def main():
    if not MD_FILE.exists():
        print(f"[xato] {MD_FILE} topilmadi", file=sys.stderr)
        sys.exit(1)
    DOCS.mkdir(parents=True, exist_ok=True)
    SHOTS.mkdir(parents=True, exist_ok=True)

    server = start_server()
    try:
        await capture_phase()
    finally:
        print("[server] to'xtatilmoqda...")
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()

    md = MD_FILE.read_text(encoding="utf-8")
    available = {p.stem for p in SHOTS.glob("*.png")}
    print(f"\n[shots] {len(available)} ta rasm: {sorted(available)}")

    html = build_html(md, available)
    HTML_FILE.write_text(html, encoding="utf-8")
    await render_pdf(HTML_FILE, PDF_FILE)


if __name__ == "__main__":
    asyncio.run(main())
