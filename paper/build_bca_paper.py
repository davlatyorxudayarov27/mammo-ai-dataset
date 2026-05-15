"""Render BCA-YOLO paper to PDF with MathJax for equation rendering."""
import asyncio
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import markdown
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent
MD = ROOT / "BCA_YOLO_paper.md"
HTML = ROOT / "_bca_paper.html"
PDF = ROOT / "BCA_YOLO_paper.pdf"

CSS = """
@page {
  size: A4;
  margin: 22mm 20mm 22mm 22mm;
  @bottom-right {
    content: counter(page);
    font-size: 9pt;
    color: #888;
  }
}
body {
  font-family: "Times New Roman", "Liberation Serif", Georgia, serif;
  font-size: 11pt;
  line-height: 1.45;
  text-align: justify;
  color: #111;
  margin: 0;
}
h1 {
  font-size: 16pt; font-weight: bold;
  margin: 0 0 6pt; line-height: 1.3;
}
h2 {
  font-size: 12pt; font-weight: bold;
  margin: 18pt 0 4pt;
  page-break-after: avoid;
}
h3 {
  font-size: 11pt; font-weight: bold; font-style: italic;
  margin: 10pt 0 2pt;
  page-break-after: avoid;
}
h4 { font-size: 11pt; font-weight: bold; margin: 6pt 0 1pt; }
p { margin: 0 0 6pt; text-indent: 0; }
strong { font-weight: bold; }
em { font-style: italic; }

table {
  border-collapse: collapse;
  margin: 8pt auto;
  font-size: 9.5pt;
  page-break-inside: avoid;
}
table th, table td {
  border: 1px solid #444;
  padding: 3pt 6pt;
  text-align: left;
  vertical-align: top;
}
table th { background: #e8e8e8; font-weight: bold; }

ul, ol { margin: 4pt 0 8pt 18pt; padding: 0; }
li { margin: 1pt 0; }

code, pre {
  font-family: "Consolas", "Liberation Mono", monospace;
  font-size: 9pt;
}
code { background: #f0f0f0; padding: 0 2pt; }
pre {
  background: #f6f6f6; border: 1px solid #ccc;
  padding: 6pt 8pt; margin: 6pt 0;
  white-space: pre; overflow: hidden;
  page-break-inside: avoid;
}
pre code { background: none; padding: 0; }

hr { border: none; border-top: 0.5pt solid #888; margin: 12pt 0; }

mjx-container {
  page-break-inside: avoid;
}
mjx-container[display="true"] {
  margin: 8pt 0 !important;
}

.MathJax_Preview, .MJX-TEX { font-size: 11pt !important; }
"""


def to_html(md_text: str) -> str:
    body = markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code"],
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<title>BCA-YOLO</title>
<style>{CSS}</style>
<script>
MathJax = {{
  tex: {{
    inlineMath: [['$', '$']],
    displayMath: [['$$', '$$']],
    processEscapes: true,
  }},
  svg: {{ fontCache: 'global' }},
  startup: {{
    typeset: false,
    ready() {{
      MathJax.startup.defaultReady();
      MathJax.startup.promise.then(() => {{
        return MathJax.typesetPromise();
      }}).then(() => {{
        window.__mathjax_done = true;
      }});
    }}
  }}
}};
</script>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"></script>
</head>
<body>
{body}
</body>
</html>
"""


async def render():
    md_text = MD.read_text(encoding="utf-8")
    html = to_html(md_text)
    HTML.write_text(html, encoding="utf-8")

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(HTML.resolve().as_uri(), wait_until="networkidle")
        await page.wait_for_function("window.__mathjax_done === true", timeout=60000)
        await page.wait_for_timeout(800)
        await page.pdf(
            path=str(PDF),
            format="A4",
            margin={"top": "22mm", "bottom": "22mm", "left": "22mm", "right": "20mm"},
            print_background=True,
        )
        await browser.close()
    sz = PDF.stat().st_size
    print(f"[ok] {PDF} — {sz/1024:.1f} KB")


if __name__ == "__main__":
    asyncio.run(render())
