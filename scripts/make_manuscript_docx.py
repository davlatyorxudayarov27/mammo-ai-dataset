# -*- coding: utf-8 -*-
"""make_manuscript_docx.py — JBHI qo'lyozmasini Word (.docx) ga aylantiradi.

Pandoc IEEEtran klassini va \\@@input / \\inputrows ni tushunmaydi, shuning uchun avval
qo'lyozmani "tekislangan" .tex ga aylantiramiz:
  • \\input{macros}          → macros.tex mazmuni (pandoc \\newcommand larni kengaytiradi)
  • \\inputrows{tab_X}       → tab_X.tex mazmuni (jadval qatorlari ichkariga)
  • fig/X.pdf                → png/X.png (Word rasterni yaxshi joylaydi)
  • IEEE ga xos buyruqlar    → oddiy ekvivalent (\\IEEEPARstart, IEEEkeywords, \\thanks)

So'ng pandoc bilan .docx: formulalar Word-native OMML bo'ladi, havolalar ieee.csl bo'yicha
[1] uslubida raqamlanadi (refs.bib + --citeproc).

Chiqish: manuscript_jbhi/MAMOGRAF_JBHI_manuscript.docx
"""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
M = ROOT / "manuscript_jbhi"
FIGSRC = ROOT / "doc_assets_big" / "en"


def read(p):
    return (M / p).read_text()


def build_flat():
    tex = read("manuscript.tex")

    # 1) \input{macros} → macros.tex
    tex = tex.replace(r"\input{macros}", read("macros.tex"))

    # 2) \inputrows{NAME} → NAME.tex (oxirgi % ni olib tashlab)
    def sub_rows(m):
        name = m.group(1)
        return read(f"{name}.tex").rstrip().rstrip("%")
    tex = re.sub(r"\\inputrows\{([^}]+)\}", sub_rows, tex)

    # \inputrows ta'rifi endi keraksiz — makeatletter blokini olib tashlaymiz
    tex = re.sub(r"\\makeatletter\s*\\newcommand\{\\inputrows\}.*?\\makeatother",
                 "", tex, flags=re.S)

    # 3) rasm: fig/NAME.pdf → png/NAME.png
    png = M / "png"
    png.mkdir(exist_ok=True)
    for m in re.finditer(r"fig/([A-Za-z0-9_]+)\.pdf", tex):
        name = m.group(1)
        src = FIGSRC / f"{name}.png"
        if src.exists():
            shutil.copy(src, png / f"{name}.png")
    tex = re.sub(r"fig/([A-Za-z0-9_]+)\.pdf", r"png/\1.png", tex)

    # 4) IEEE ga xos buyruqlar
    # sarlavhadagi \\ qatordan bo'lish so'zlarni yopishtiradi → bo'sh joyga almashtiramiz
    tex = re.sub(r"\\title\{(.*?)\}", lambda m: r"\title{" + re.sub(r"\\\\\s*", " ", m.group(1)) + "}",
                 tex, flags=re.S)
    tex = re.sub(r"\\IEEEPARstart\{(.)\}\{([^}]*)\}", r"\1\2", tex)      # drop cap
    # IEEEkeywords → "Index Terms" xatboshi
    tex = re.sub(r"\\begin\{IEEEkeywords\}(.*?)\\end\{IEEEkeywords\}",
                 lambda m: r"\noindent\textbf{Index Terms---}" + m.group(1).strip(),
                 tex, flags=re.S)
    # \thanks{...} — muallif izohlari; pandoc uchun oddiy izoh sifatida qoldiramiz
    tex = re.sub(r"\\thanks\{", r"\\footnote{", tex)

    (M / "manuscript_flat.tex").write_text(tex)
    return M / "manuscript_flat.tex"


def to_docx(flat):
    out = M / "MAMOGRAF_JBHI_manuscript.docx"
    # pandoc konteynerda; ishchi katalog /data = manuscript_jbhi
    cmd = [
        "docker", "run", "--rm", "-v", f"{M}:/data", "-w", "/data",
        "pandoc/core:latest",
        "manuscript_flat.tex",
        "-f", "latex+raw_tex",
        "-o", out.name,
        "--citeproc",
        "--bibliography=refs.bib",
        "--csl=ieee.csl",
        "--metadata=reference-section-title:References",
        "--number-sections",
        "--resource-path=.:png",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(r.stdout)
    if r.stderr:
        print("STDERR:", r.stderr[-2000:])
    # egalikni tiklash
    subprocess.run(["docker", "run", "--rm", "-v", f"{M}:/data",
                    "--entrypoint", "chown", "pandoc/core:latest",
                    "-R", "1000:1000", "/data"], capture_output=True)
    return out, r.returncode


if __name__ == "__main__":
    flat = build_flat()
    print(f"[docx] tekislangan tex: {flat.name}")
    out, rc = to_docx(flat)
    print(f"[docx] {'TAYYOR' if rc == 0 else 'XATO'}: {out.name} (rc={rc})")
