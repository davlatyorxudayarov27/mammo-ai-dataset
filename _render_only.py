"""Faqat HTML/PDF render — capture qaytariladi."""
import asyncio
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_pdf import build_html, render_pdf, MD_FILE, SHOTS, HTML_FILE, PDF_FILE, DOCS


async def main():
    DOCS.mkdir(parents=True, exist_ok=True)
    md = MD_FILE.read_text(encoding="utf-8")
    available = {p.stem for p in SHOTS.glob("*.png")}
    print(f"[shots] {len(available)} ta rasm")

    html = build_html(md, available)
    HTML_FILE.write_text(html, encoding="utf-8")
    print(f"[html] {HTML_FILE} ({len(html)} bayt)")

    await render_pdf(HTML_FILE, PDF_FILE)


if __name__ == "__main__":
    asyncio.run(main())
