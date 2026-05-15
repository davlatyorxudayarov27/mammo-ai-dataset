"""
Researcher PDF — real DICOM workflow bilan amaliy skreeshotlar.
"""
from __future__ import annotations

import asyncio
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import markdown
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
SHOTS = DOCS / "researcher_screenshots"
MD_FILE = ROOT / "TADQIQOTCHI_QOLLANMA.md"
PDF_FILE = ROOT / "TADQIQOTCHI_QOLLANMA.pdf"
HTML_FILE = DOCS / "_researcher.html"

BASE_URL = "http://127.0.0.1:8765"
ADMIN_USER = "admin"
ADMIN_PASS = "admin123"


async def shoot(page, name: str, full_page: bool = False):
    SHOTS.mkdir(parents=True, exist_ok=True)
    out = SHOTS / f"{name}.png"
    await page.screenshot(path=str(out), full_page=full_page)
    print(f"   ✓ {out.name}")
    return out.name


async def login(page):
    await page.goto(BASE_URL, wait_until="networkidle")
    await page.wait_for_selector("#loginModal:not([hidden])", timeout=8000)
    await page.fill("#loginUsername", ADMIN_USER)
    await page.fill("#loginPassword", ADMIN_PASS)
    await page.click("#loginSubmit")
    await page.wait_for_function(
        "() => { const m = document.getElementById('loginModal'); return !m || m.hidden; }",
        timeout=10000,
    )
    await page.wait_for_timeout(800)


async def open_dicom_local(page, ref: str):
    await page.click('button.tab[data-tab="local"]')
    await page.wait_for_timeout(400)
    parts = ref.split("/")
    for i in range(len(parts) - 1):
        sub = "/".join(parts[: i + 1])
        try:
            await page.click(f'#localList li[data-path="{sub}"]', timeout=5000)
            await page.wait_for_timeout(500)
        except Exception:
            pass
    await page.click(f'#localList li[data-path="{ref}"]', timeout=10000)
    await page.wait_for_function(
        "() => !document.getElementById('imgStack').hidden",
        timeout=20000,
    )
    await page.wait_for_timeout(2500)


async def cleanup_annotations(page, ref="DCMDT/D0000000.dcm"):
    token = await page.evaluate("() => localStorage.getItem('mamograf_jwt')")
    try:
        req = urllib.request.Request(
            f"{BASE_URL}/api/annotations",
            data=f'{{"source":"local","ref":"{ref}","annotations":[]}}'.encode(),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
            method="PUT",
        )
        urllib.request.urlopen(req, timeout=5).read()
    except Exception:
        pass


async def take_all(page):
    print("[1] Login + DICOM ochish...")
    await login(page)
    try:
        await open_dicom_local(page, "DCMDT/D0000000.dcm")
    except Exception as e:
        print(f"  ! DICOM ochish: {e}")
    await shoot(page, "01_dicom_open")

    print("[2] Metadata tab...")
    try:
        await page.click('.meta-pane .tab[data-rtab="meta"]', timeout=3000)
        await page.wait_for_timeout(500)
        await shoot(page, "02_metadata")
    except Exception as e:
        print(f"  ! meta: {e}")

    print("[3] Hisobot tab (xlsx integratsiyasi)...")
    try:
        await page.click('.meta-pane .tab[data-rtab="report"]', timeout=3000)
        await page.wait_for_timeout(1500)
        await shoot(page, "03_hisobot_match")
    except Exception as e:
        print(f"  ! hisobot: {e}")

    print("[4] AI model tanlash...")
    try:
        await page.select_option("#aiModelSelect", value="digitaleye_yolo11_l.pt")
        await page.wait_for_timeout(400)
    except Exception as e:
        print(f"  ! ai-select: {e}")

    print("[5] AI tahlil yugurish (real digitaleye, ~10 sec)...")
    try:
        await page.click("#aiRunBtn", timeout=3000)
        for _ in range(40):
            await page.wait_for_timeout(500)
            status_text = await page.text_content("#status")
            if status_text and ("AI:" in status_text or "taklif" in status_text):
                break
        await page.wait_for_timeout(1500)
        await shoot(page, "04_ai_suggestions")
    except Exception as e:
        print(f"  ! ai-run: {e}")

    print("[6] Threshold slayder pastga...")
    try:
        await page.fill("#aiConfSlider", "10")
        await page.dispatch_event("#aiConfSlider", "input")
        await page.wait_for_timeout(800)
        await shoot(page, "05_threshold_low")
    except Exception as e:
        print(f"  ! threshold: {e}")

    print("[7] Hammasini qabul qilish...")
    try:
        await page.evaluate("""
            () => {
                if (typeof state !== 'undefined' && state.allSuggestions) {
                    state.allSuggestions.forEach(s => {
                        const ann = {
                            id: 'demo_' + Math.random().toString(36).slice(2,8),
                            type: 'bbox', label: 'mass', bi_rads: '4B',
                            note: 'AI: ' + s.label + ' ' + (s.confidence*100).toFixed(1) + '%',
                            frame: 0, bbox: s.bbox.slice(),
                            created_at: new Date().toISOString(),
                            updated_at: new Date().toISOString(),
                        };
                        state.annotations.push(ann);
                    });
                    state.allSuggestions = [];
                    state.suggestions = [];
                    if (typeof renderSvg === 'function') renderSvg();
                    if (typeof renderAnnoList === 'function') renderAnnoList();
                    if (typeof scheduleAutosave === 'function') scheduleAutosave();
                }
            }
        """)
        await page.wait_for_timeout(2000)
        await shoot(page, "06_after_accept")
    except Exception as e:
        print(f"  ! accept: {e}")

    print("[8] Annotatsiyalar tab...")
    try:
        await page.click('.meta-pane .tab[data-rtab="anno"]', timeout=3000)
        await page.wait_for_timeout(500)
        await shoot(page, "07_annotations_tab")
    except Exception as e:
        print(f"  ! anno-tab: {e}")

    print("[9] Polygon chizish...")
    try:
        await page.click("#toolPoly", timeout=3000)
        await page.wait_for_timeout(300)
        wrap = await page.evaluate(
            "() => { const r = document.getElementById('canvasWrap').getBoundingClientRect();"
            " return {x: r.x, y: r.y, w: r.width, h: r.height}; }"
        )
        cx, cy = wrap["x"] + wrap["w"] * 0.3, wrap["y"] + wrap["h"] * 0.6
        for dx, dy in [(0, 0), (40, 5), (60, 30), (50, 60), (10, 50), (-10, 20)]:
            await page.mouse.click(cx + dx, cy + dy)
            await page.wait_for_timeout(150)
        await page.keyboard.press("Enter")
        await page.wait_for_timeout(1500)
        await shoot(page, "08_polygon")
        await page.click("#toolSelect", timeout=2000)
    except Exception as e:
        print(f"  ! poly: {e}")

    print("[10] Eksport tugmasi (COCO)...")
    try:
        await page.evaluate("() => { const b = document.getElementById('exportBtn'); if (b) b.scrollIntoView(); }")
        await page.wait_for_timeout(300)
        await shoot(page, "09_export_buttons")
    except Exception as e:
        print(f"  ! export-btn: {e}")

    print("[11] Stats modal (dataset-darajadagi)...")
    try:
        await page.click("#statsBtn", timeout=3000)
        await page.wait_for_selector("#statsModal:not([hidden])", timeout=5000)
        await page.wait_for_timeout(1000)
        await shoot(page, "10_stats")
        await page.click("#statsCloseBtn")
        await page.wait_for_timeout(300)
    except Exception as e:
        print(f"  ! stats: {e}")

    print("[12] De-ID modal — real PHI tag'lar...")
    try:
        await page.click("#deidBtn", timeout=3000)
        await page.wait_for_selector("#deidModal:not([hidden])", timeout=5000)
        await page.wait_for_timeout(1500)
        await shoot(page, "11_deid_phi")
        await page.click("#deidCloseBtn")
        await page.wait_for_timeout(300)
    except Exception as e:
        print(f"  ! deid: {e}")

    print("[13] Mening ishim tab — approved annotatsiyalar...")
    try:
        await page.click('button.tab[data-tab="dashboard"]', timeout=3000)
        await page.wait_for_timeout(800)
        await shoot(page, "12_dashboard")
    except Exception as e:
        print(f"  ! dash: {e}")

    print("[14] Cleanup...")
    await cleanup_annotations(page)


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


SHOT_PLACEMENTS = {
    r"## 1\. Maqsad va workflow": "01_dicom_open",
    r"### 2\.1 DICOM yig'ish": "02_metadata",
    r"### 2\.2 xlsx bilan bog'lash": "03_hisobot_match",
    r"### 2\.3 AI bootstrap": "04_ai_suggestions",
    r"#### Threshold sozlash": "05_threshold_low",
    r"### 2\.4 Batch AI inference": "06_after_accept",
    r"### 2\.5 Manual tuzatish": "07_annotations_tab",
    r"## 3\. Eksport formatlari": "09_export_buttons",
    r"### 3\.4 De-identification": "11_deid_phi",
    r"## 6\. Natijalarni baholash": "10_stats",
    r"### 7\.4 Quality monitoring": "12_dashboard",
    r"## 10\. Tipik tadqiqot stseneriya'lari": "08_polygon",
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
h1 { color: #2563eb; border-bottom: 2px solid #2563eb; padding-bottom: 4px; }
h2 { color: #2563eb; margin-top: 22px; border-bottom: 1px solid #cdd5e0; padding-bottom: 3px; page-break-after: avoid; }
h3 { color: #1e3a8a; margin-top: 14px; page-break-after: avoid; }
h4 { color: #1e3a8a; margin-top: 10px; }
table { border-collapse: collapse; width: 100%; margin: 8px 0 14px; font-size: 9pt; page-break-inside: avoid; }
table th, table td { border: 1px solid #d0d7de; padding: 4px 7px; text-align: left; vertical-align: top; }
table th { background: #eff6ff; font-weight: 600; color: #1e3a8a; }
code, pre { background: #f4f5f7; border-radius: 3px; font-family: "Cascadia Mono", "Consolas", monospace; }
code { padding: 1px 4px; font-size: 9pt; color: #be185d; }
pre { padding: 8px 10px; font-size: 8.5pt; overflow-x: auto; page-break-inside: avoid; border: 1px solid #e2e8f0; }
pre code { color: #1a1a1a; padding: 0; background: none; }
ul, ol { margin: 6px 0 12px 22px; padding: 0; }
li { margin: 2px 0; }
img.shot {
  max-width: 100%; max-height: 140mm;
  border: 1px solid #cdd5e0; border-radius: 4px;
  margin: 12px auto; display: block;
  box-shadow: 0 2px 6px rgba(0,0,0,0.08);
  page-break-inside: avoid;
}
.cover { text-align: center; margin-top: 60mm; page-break-after: always; }
.cover h1 { font-size: 24pt; border: none; }
.cover .sub { color: #555; font-size: 13pt; margin-top: 6px; }
.cover .badge {
  display: inline-block; margin-top: 18px; padding: 6px 14px;
  background: #eff6ff; color: #1e3a8a; border-radius: 18px;
  font-size: 11pt; font-weight: 600;
}
.cover .meta { color: #888; font-size: 10pt; margin-top: 24px; }
.toc { page-break-after: always; }
.toc ul { list-style: none; margin-left: 0; }
.toc li { margin: 3px 0; }
.callout {
  background: #eff6ff; border-left: 3px solid #2563eb;
  padding: 8px 12px; margin: 12px 0; font-size: 9.5pt;
}
hr { border: none; border-top: 1px solid #cdd5e0; margin: 18px 0; }
blockquote {
  border-left: 3px solid #94a3b8; padding-left: 10px; color: #475569;
  margin: 8px 0; font-style: italic;
}
"""


def build_html(md_text: str, screenshots: set) -> str:
    lines = md_text.splitlines()
    out_lines = []
    for ln in lines:
        out_lines.append(ln)
        for pattern, name in SHOT_PLACEMENTS.items():
            if re.match(pattern, ln) and name in screenshots:
                out_lines.append("")
                out_lines.append(f"![{name}](researcher_screenshots/{name}.png)")
                out_lines.append("")
                break

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
            if level == 1:
                continue
            headings.append((level, text))

    toc_items = []
    for level, text in headings[:35]:
        indent = (level - 2) * 14
        toc_items.append(f'<li style="margin-left:{indent}px">{text}</li>')
    toc_html = "<ul>" + "".join(toc_items) + "</ul>"

    cover = f"""
    <div class="cover">
      <div class="badge">🔬 Tibbiy AI Tadqiqotchi</div>
      <h1>MAMOGRAF DICOM Viewer</h1>
      <div class="sub">Trening dataset yaratish va custom YOLO modellarini o'rgatish</div>
      <div class="meta">{time.strftime('%Y-%m-%d')} · {len(screenshots)} skreenshot · amaliy qo'llanma</div>
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
<title>MAMOGRAF — Tadqiqotchi qo'llanmasi</title>
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


def start_server() -> subprocess.Popen:
    print("[server] ishga tushirilmoqda...")
    import os
    env = {
        **os.environ,
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
    print(f"\n[shots] {len(available)} ta rasm")

    html = build_html(md, available)
    HTML_FILE.write_text(html, encoding="utf-8")
    await render_pdf(HTML_FILE, PDF_FILE)


if __name__ == "__main__":
    asyncio.run(main())
