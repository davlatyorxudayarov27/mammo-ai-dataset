"""Generate a single .docx with all source code for DGU software copyright filing.

Usage:  .venv\\Scripts\\python make_dgu_docx.py
Output: MAMOGRAF_source_code_DGU.docx in the project root.
"""
from __future__ import annotations

from pathlib import Path
from datetime import date

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.shared import Pt, RGBColor

PROJECT = Path(__file__).resolve().parent
OUT = PROJECT / "AI_Scan_dasturiy_kompleks_manba_kodi.docx"

PROGRAM_TITLE = (
    "«AI Scan» — sun'iy intellekt va chuqur o'rganish algoritmlariga "
    "asoslangan, sut bezi o'smalarini erta aniqlash hamda BI-RADS "
    "toifalashtirish maqsadida mammografiya DICOM tasvirlarini "
    "avtomatlashtirilgan tahlil qilish, anonimlashtirish va annotatsiyalashga "
    "mo'ljallangan dasturiy kompleks"
)
PROGRAM_SHORT = "«AI Scan» dasturiy kompleksi"
PROGRAM_SUBTITLE = (
    "Dasturlar uchun davlat guvohnomasini (DGU) ro'yxatga olish uchun "
    "taqdim etiladigan manba kodlari to'plami"
)
PROGRAM_ANNOTATION = (
    "Dasturiy kompleks sut bezi saratonini erta aniqlash maqsadida "
    "mammografiya rentgenologik tasvirlarini (DICOM standartida) qabul "
    "qilish, bemor identifikatorlarini avtomatik anonimlashtirish "
    "(de-identifikatsiya), sun'iy intellekt yordamida shubhali "
    "o'choqlarni avtomatik aniqlash (BCA-YOLO, TILLNet-Det chuqur "
    "neyron tarmoq arxitekturalari), radiomika belgilari asosida "
    "BI-RADS toifalashtirish (XS-Classifier), shifokorlar tomonidan "
    "annotatsiyalash, klinik PACS tizimlari bilan integratsiya va "
    "natijalarni DICOM SEG / DICOM SR formatlarida eksport qilish "
    "imkoniyatlarini birlashtirgan ko'p foydalanuvchili veb-tizimdir."
)


def _set_page_numbers(doc: Document) -> None:
    section = doc.sections[0]
    footer = section.footer
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    fldChar1 = OxmlElement("w:fldChar"); fldChar1.set(qn("w:fldCharType"), "begin")
    instrText = OxmlElement("w:instrText"); instrText.text = "PAGE"
    fldChar2 = OxmlElement("w:fldChar"); fldChar2.set(qn("w:fldCharType"), "end")
    run._r.append(fldChar1); run._r.append(instrText); run._r.append(fldChar2)


def _shade(paragraph, hex_color: str = "F2F2F2") -> None:
    """Light gray paragraph shading for code blocks."""
    pPr = paragraph._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), hex_color)
    pPr.append(shd)


def add_code_block(doc: Document, text: str) -> None:
    """Render source code: each line is one paragraph (zero spacing, monospace)."""
    lines = text.splitlines() or [""]
    width = len(str(len(lines)))
    for i, line in enumerate(lines, 1):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.left_indent = Pt(6)
        _shade(p)
        r = p.add_run(f"{i:>{width}}  {line}")
        r.font.name = "Consolas"
        r.font.size = Pt(8)
        rPr = r._element.get_or_add_rPr()
        rFonts = rPr.find(qn("w:rFonts"))
        if rFonts is None:
            rFonts = OxmlElement("w:rFonts"); rPr.append(rFonts)
        rFonts.set(qn("w:ascii"), "Consolas"); rFonts.set(qn("w:hAnsi"), "Consolas")


def add_file(doc: Document, rel_path: str) -> bool:
    p = PROJECT / rel_path
    if not p.exists() or not p.is_file():
        return False
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        text = f"<o'qib bo'lmadi: {exc}>"
    h = doc.add_heading(rel_path.replace("\\", "/"), level=2)
    h.paragraph_format.space_before = Pt(12)
    info = doc.add_paragraph()
    info.add_run(f"Fayl yo'li: {rel_path}    |    Qatorlar: {len(text.splitlines())}    |    Hajm: {len(text)} bayt").italic = True
    add_code_block(doc, text)
    doc.add_paragraph()
    return True


def list_py(folder: str, *, first: list[str] | None = None) -> list[str]:
    base = PROJECT / folder
    files = sorted(f.name for f in base.glob("*.py"))
    first = first or []
    rest = [f for f in files if f not in first]
    return [f"{folder}/{n}" for n in first + rest]


SECTIONS: list[tuple[str, list[str]]] = [
    ("1. Konfiguratsiya va deploy fayllari", [
        "requirements.txt",
        "Dockerfile",
        "Dockerfile.prod",
        "docker-compose.yml",
        "docker-compose.prod.yml",
        "Caddyfile",
        "deploy_prod.sh",
        ".gitignore",
    ]),
    ("2. Backend — asosiy ilova kodi (app/)", list_py("app", first=["main.py", "auth.py", "db.py"])),
    ("3. Frontend — veb UI (app/static/)", [
        "app/static/index.html",
        "app/static/style.css",
        "app/static/app.js",
    ]),
    ("4. Model arxitekturalari (app/models_arch/)", list_py("app/models_arch")),
    ("5. O'qitish va tadqiqot skriptlari (app/research/)", list_py("app/research")),
    ("6. Qo'shimcha utilita skriptlari", [
        "build_pdf.py",
        "build_researcher_pdf.py",
        "_render_only.py",
    ]),
]


def build() -> Path:
    doc = Document()

    # Default body font
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)

    # --- Title page ---
    label = doc.add_paragraph()
    label.alignment = WD_ALIGN_PARAGRAPH.CENTER
    rl = label.add_run("DASTURIY MAHSULOTNING NOMI")
    rl.bold = True; rl.font.size = Pt(11)
    rl.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.paragraph_format.space_before = Pt(6)
    title.paragraph_format.space_after = Pt(18)
    rt = title.add_run(PROGRAM_TITLE)
    rt.bold = True; rt.font.size = Pt(18)

    short = doc.add_paragraph()
    short.alignment = WD_ALIGN_PARAGRAPH.CENTER
    rs = short.add_run(f"(Qisqartirilgan nomi: {PROGRAM_SHORT})")
    rs.italic = True; rs.font.size = Pt(12)

    doc.add_paragraph()
    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    rsu = sub.add_run(PROGRAM_SUBTITLE)
    rsu.italic = True; rsu.font.size = Pt(12)

    doc.add_paragraph()

    # Annotatsiya (qisqacha tavsif)
    ann_h = doc.add_paragraph()
    ann_h.alignment = WD_ALIGN_PARAGRAPH.LEFT
    rah = ann_h.add_run("Dasturiy mahsulot annotatsiyasi (qisqacha tavsifi):")
    rah.bold = True; rah.font.size = Pt(11)
    ann = doc.add_paragraph(PROGRAM_ANNOTATION)
    ann.paragraph_format.first_line_indent = Pt(18)
    for r in ann.runs:
        r.font.size = Pt(11)

    doc.add_paragraph()
    meta = doc.add_paragraph()
    meta.alignment = WD_ALIGN_PARAGRAPH.LEFT
    mr = meta.add_run(
        f"Tayyorlangan sana: {date.today().strftime('%d.%m.%Y')}\n"
        f"Dasturlash tili: Python 3.12 (backend), HTML/CSS/JavaScript (frontend)\n"
        f"Asosiy texnologiyalar: FastAPI, SQLite, Docker, Ultralytics YOLO, PyTorch, "
        f"pydicom/highdicom, scikit-image, scikit-learn\n"
        f"Loyiha sohasi: tibbiy radiologiya, raqamli mammografiya, sun'iy intellekt\n"
        f"Foydalanuvchi turlari: administrator, ekspert-rentgenolog (reviewer), "
        f"annotator-shifokor\n"
    )
    mr.font.size = Pt(11)

    doc.add_page_break()

    # --- Mundarija sarlavhasi ---
    doc.add_heading("Mundarija (bo'limlar)", level=1)
    for title_text, _files in SECTIONS:
        doc.add_paragraph(title_text, style="List Number")
    doc.add_page_break()

    # --- Sections ---
    total_files = 0
    for sec_title, files in SECTIONS:
        doc.add_heading(sec_title, level=1)
        added = 0
        for rel in files:
            if add_file(doc, rel):
                added += 1
                total_files += 1
        if added == 0:
            doc.add_paragraph("(bu bo'limda fayllar topilmadi)").italic = True
        doc.add_page_break()

    _set_page_numbers(doc)
    doc.save(OUT)
    print(f"OK — {OUT}")
    print(f"Jami fayllar: {total_files}")
    return OUT


if __name__ == "__main__":
    build()
