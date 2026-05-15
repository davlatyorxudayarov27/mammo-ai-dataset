"""Build the full PhD dissertation .docx from markdown sources via pandoc.

Math expressions are converted to OMML (Word's native math format), which is
fully MathType-compatible (formulas can be opened and edited in MathType).
Screenshots are embedded from the actual project directory.
"""
from __future__ import annotations

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import pypandoc

ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent

# Order of dissertation sections
SECTIONS = [
    "01_title_kirish.md",
    "02_bob1.md",
    "03_bob2.md",
    "04_bob3.md",
    "05_bob4.md",
    "06_xulosa_refs.md",
    "07_ilovalar.md",
]

OUTPUT = ROOT / "DISSERTATSIYA_v2.docx"


def main():
    # Concatenate all markdown sources (separated by blank lines)
    parts = []
    for fname in SECTIONS:
        p = ROOT / fname
        if not p.exists():
            print(f"[warn] missing: {p}")
            continue
        parts.append(p.read_text(encoding="utf-8"))
    full_md = "\n\n".join(parts)

    # Rewrite relative image paths (`docs/`, `paper/`) to absolute paths
    # so pandoc can find them regardless of working dir.
    full_md = full_md.replace("](docs/", f"]({PROJECT_ROOT.as_posix()}/docs/")
    full_md = full_md.replace("](paper/", f"]({PROJECT_ROOT.as_posix()}/paper/")

    # Save concatenated source for reference
    (ROOT / "FULL_SOURCE.md").write_text(full_md, encoding="utf-8")
    print(f"[md] {len(full_md)} chars, {full_md.count(chr(10)) + 1} lines")

    # Pandoc args:
    #  --resource-path: where to look for image references
    #  -V geometry: page setup (A4, 25/20/20/20 mm)
    #  -V mainfont: Times New Roman 14 pt is academic standard in Uzbekistan
    pandoc_args = [
        f"--resource-path={PROJECT_ROOT}",
        "-V", "geometry:a4paper,top=20mm,bottom=20mm,left=30mm,right=15mm",
        "-V", "fontsize=14pt",
        "-V", "linestretch=1.5",
        "-V", "lang=uz",
        "--toc",
        "--toc-depth=3",
        "--number-sections=false",
        "--standalone",
    ]

    print(f"[pandoc] writing {OUTPUT}")
    out = pypandoc.convert_text(
        full_md,
        to="docx",
        format="markdown+raw_attribute+pipe_tables+task_lists",
        outputfile=str(OUTPUT),
        extra_args=pandoc_args,
    )
    sz = OUTPUT.stat().st_size
    print(f"[ok] {OUTPUT} — {sz / 1024:.1f} KB")


if __name__ == "__main__":
    main()
