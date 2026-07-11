# -*- coding: utf-8 -*-
"""MAMOGRAF — to'liq ish tsikli bo'yicha taqdimot (.pptx) generatori.

Diagrammalar doc_assets/ ichida bo'lishi kerak (make_diagrams.py).
"""
from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "doc_assets"
OUT = ROOT / "MAMOGRAF_taqdimot.pptx"

# Teal / tibbiy moviy rang sxemasi
ACCENT = RGBColor(0x0E, 0x74, 0x90)    # teal (asosiy)
ACCENT2 = RGBColor(0x06, 0xB6, 0xD4)   # cyan (urg'u)
GREEN = RGBColor(0x22, 0xA3, 0x5A)
DARK = RGBColor(0x10, 0x3A, 0x40)      # quyuq teal-grafit
MUTED = RGBColor(0x5B, 0x70, 0x74)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
LIGHTBG = RGBColor(0xF0, 0xFD, 0xFF)
CHIP = RGBColor(0xDB, 0xF3, 0xF7)

EMUW = Inches(13.333)
EMUH = Inches(7.5)

prs = Presentation()
prs.slide_width = EMUW
prs.slide_height = EMUH
BLANK = prs.slide_layouts[6]


def _imgsize(path: Path):
    from PIL import Image
    with Image.open(path) as im:
        return im.size  # (w, h) px


def new_slide():
    return prs.slides.add_slide(BLANK)


def rect(slide, l, t, w, h, fill, line=None, line_w=1.0):
    shp = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, l, t, w, h)
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line
        shp.line.width = Pt(line_w)
    shp.shadow.inherit = False
    return shp


def textbox(slide, l, t, w, h, anchor=MSO_ANCHOR.TOP):
    tb = slide.shapes.add_textbox(l, t, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = Pt(2)
    tf.margin_right = Pt(2)
    return tb, tf


def set_run(r, text, size, color, bold=False, italic=False, font="Calibri"):
    r.text = text
    r.font.size = Pt(size)
    r.font.color.rgb = color
    r.font.bold = bold
    r.font.italic = italic
    r.font.name = font


def header_bar(slide, title, num=None):
    """To'q ko'k yuqori chiziq + sarlavha."""
    rect(slide, 0, 0, EMUW, Inches(1.05), ACCENT)
    rect(slide, 0, Inches(1.05), EMUW, Inches(0.06), GREEN)
    tb, tf = textbox(slide, Inches(0.5), Inches(0.12), Inches(12.3), Inches(0.8),
                     anchor=MSO_ANCHOR.MIDDLE)
    p = tf.paragraphs[0]
    set_run(p.add_run(), title, 28, WHITE, bold=True)
    if num is not None:
        tb2, tf2 = textbox(slide, Inches(11.8), Inches(0.12), Inches(1.0), Inches(0.8),
                           anchor=MSO_ANCHOR.MIDDLE)
        p2 = tf2.paragraphs[0]
        p2.alignment = PP_ALIGN.RIGHT
        set_run(p2.add_run(), num, 16, RGBColor(0xBF, 0xD3, 0xEA), bold=True)


def bullets(slide, items, l, t, w, h, size=18, gap=8):
    tb, tf = textbox(slide, l, t, w, h)
    for i, it in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(gap)
        # sub-bullet if tuple (text, True)
        sub = False
        if isinstance(it, tuple):
            it, sub = it[0], it[1]
        r = p.add_run()
        prefix = "–  " if sub else "▸  "
        set_run(r, prefix + it, size - (2 if sub else 0),
                MUTED if sub else DARK, bold=False)
        if sub:
            p.level = 1
    return tb


def chip(slide, text, l, t, w=Inches(5.2), h=Inches(0.5), fill=CHIP, tcolor=ACCENT):
    shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, l, t, w, h)
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill
    shp.line.color.rgb = ACCENT2
    shp.line.width = Pt(1.0)
    shp.shadow.inherit = False
    tf = shp.text_frame
    tf.word_wrap = True
    tf.margin_top = Pt(2)
    tf.margin_bottom = Pt(2)
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    set_run(p.add_run(), text, 13, tcolor, bold=True, font="Consolas")
    return shp


def picture_fit(slide, path, l, t, max_w, max_h, center_l=None):
    path = Path(path)
    pw, ph = _imgsize(path)
    ar = pw / ph
    w = max_w
    h = Emu(int(w / ar))
    if h > max_h:
        h = max_h
        w = Emu(int(h * ar))
    if center_l is not None:
        l = center_l + Emu(int((max_w - w) / 2))
    slide.shapes.add_picture(str(path), l, t, width=w, height=h)
    return w, h


def footer(slide, text="AI Scan · MAMOGRAF"):
    tb, tf = textbox(slide, Inches(0.5), Inches(7.05), Inches(12.3), Inches(0.35))
    p = tf.paragraphs[0]
    set_run(p.add_run(), text, 9, MUTED, italic=True)


# ============================================================ SLAYDLAR
# 1. Title
def slide_title():
    s = new_slide()
    rect(s, 0, 0, EMUW, EMUH, ACCENT)
    rect(s, 0, Inches(4.35), EMUW, Inches(0.08), GREEN)
    tb, tf = textbox(s, Inches(1), Inches(2.2), Inches(11.3), Inches(1.4),
                     anchor=MSO_ANCHOR.MIDDLE)
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    set_run(p.add_run(), "AI Scan — MAMOGRAF", 48, WHITE, bold=True)
    tb2, tf2 = textbox(s, Inches(1), Inches(3.55), Inches(11.3), Inches(0.8),
                       anchor=MSO_ANCHOR.MIDDLE)
    p2 = tf2.paragraphs[0]
    p2.alignment = PP_ALIGN.CENTER
    set_run(p2.add_run(),
            "Sun'iy intellekt asosida ko'krak bezi o'smalarini erta aniqlash tizimi",
            20, RGBColor(0xC9, 0xDB, 0xEF))
    tb3, tf3 = textbox(s, Inches(1), Inches(4.7), Inches(11.3), Inches(1.0),
                       anchor=MSO_ANCHOR.MIDDLE)
    p3 = tf3.paragraphs[0]
    p3.alignment = PP_ALIGN.CENTER
    set_run(p3.add_run(),
            "To'liq ish tsikli:  Upload → Auto-AI → Annotation → Dataset → Yangi model",
            18, WHITE, bold=True)


# 2. Loyiha haqida
def slide_intro():
    s = new_slide()
    header_bar(s, "Loyiha haqida")
    bullets(s, [
        "MAMOGRAF — mammografiya tasvirlari yordamida ko'krak bezi o'smalarini "
        "(xavfsiz / xavfli) erta aniqlovchi AI tizim",
        "DICOM ko'ruvchi + annotatsiya muharriri + AI inference + model o'qitish — "
        "barchasi bitta veb-ilovada (FastAPI)",
        "Maqsad: radiolog ishini tezlashtirish, diagnostika aniqligini oshirish",
        "Asosiy g'oya — YOPIQ SIKL (Active Learning): tizim ishlatilgani sari "
        "aniqroq bo'lib boradi",
    ], Inches(0.7), Inches(1.5), Inches(12), Inches(3), size=20, gap=14)
    chip(s, "Diqqat markazida: Upload → Auto-AI → Annotation → Dataset → Yangi model",
         Inches(0.7), Inches(5.6), w=Inches(11.9), h=Inches(0.6))
    footer(s)


# 3. Arxitektura
def slide_arch():
    s = new_slide()
    header_bar(s, "Tizim arxitekturasi")
    picture_fit(s, ASSETS / "architecture.png", Inches(0.6), Inches(1.35),
                Inches(12.1), Inches(5.4), center_l=Inches(0.6))
    footer(s)


# 4. Tsikl umumiy
def slide_cycle_overview():
    s = new_slide()
    header_bar(s, "To'liq ish tsikli — umumiy ko'rinish")
    picture_fit(s, ASSETS / "cycle.png", Inches(0.6), Inches(1.4),
                Inches(12.1), Inches(4.0), center_l=Inches(0.6))
    chip(s, "Har ~50 yangi (tekshirilgan) annotatsiyada model AVTOMATIK qayta o'qitiladi",
         Inches(0.9), Inches(6.05), w=Inches(11.5), h=Inches(0.6),
         fill=RGBColor(0xE3, 0xF4, 0xEA), tcolor=GREEN)
    footer(s)


# 5–9. Bosqich slaydlari
def slide_stage(num, title, endpoint, items, extra_img=None, code=None):
    s = new_slide()
    header_bar(s, title, num=f"BOSQICH {num}/5")
    # stepper
    picture_fit(s, ASSETS / f"stepper_{num}.png", Inches(0.6), Inches(1.25),
                Inches(12.1), Inches(1.25), center_l=Inches(0.6))
    chip(s, endpoint, Inches(0.7), Inches(2.65), w=Inches(7.2), h=Inches(0.5))
    # bullets
    bw = Inches(7.6) if (extra_img or code) else Inches(12)
    bullets(s, items, Inches(0.7), Inches(3.35), bw, Inches(3.4), size=16, gap=9)
    if extra_img:
        picture_fit(s, ASSETS / extra_img, Inches(8.5), Inches(3.5),
                    Inches(4.4), Inches(2.6))
    if code:
        shp = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(8.5), Inches(3.4),
                                 Inches(4.3), Inches(2.6))
        shp.fill.solid(); shp.fill.fore_color.rgb = RGBColor(0x0F, 0x14, 0x1C)
        shp.line.color.rgb = ACCENT2; shp.line.width = Pt(1)
        shp.shadow.inherit = False
        tf = shp.text_frame; tf.word_wrap = True
        tf.margin_left = Pt(8); tf.margin_top = Pt(8)
        for i, line in enumerate(code):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            set_run(p.add_run(), line, 12, RGBColor(0x7E, 0xE7, 0x9A),
                    font="Consolas")
    footer(s)


# 10. Aktiv o'qitish
def slide_loop():
    s = new_slide()
    header_bar(s, "Aktiv o'qitish — nega yopiq sikl?")
    bullets(s, [
        "Yangi o'qitilgan model keyingi UPLOAD'larda Auto-AI sifatida ishlatiladi",
        "Aniqroq AI → radiolog kamroq tuzatadi → annotatsiya tez to'planadi",
        "Ko'proq sifatli annotatsiya → yana aniqroq model",
        "Natija: har aylanishda model yaxshilanadi, qo'l mehnati kamayadi",
    ], Inches(0.7), Inches(1.4), Inches(12), Inches(2.4), size=19, gap=12)
    picture_fit(s, ASSETS / "cycle.png", Inches(1.2), Inches(4.0),
                Inches(11), Inches(2.9), center_l=Inches(1.2))
    footer(s)


# UI skrinshot slaydi
def slide_ui(title, img, caption_items):
    s = new_slide()
    header_bar(s, title)
    w, h = picture_fit(s, ASSETS / img, Inches(0.6), Inches(1.35),
                       Inches(9.0), Inches(5.0), center_l=Inches(0.45))
    # o'ng tomonda izohlar
    bullets(s, caption_items, Inches(9.7), Inches(1.7), Inches(3.4),
            Inches(4.6), size=14, gap=10)
    footer(s)


# Model arxitekturasi slaydi
def slide_model(title, img, items):
    s = new_slide()
    header_bar(s, title)
    picture_fit(s, ASSETS / img, Inches(0.6), Inches(1.3),
                Inches(12.1), Inches(3.7), center_l=Inches(0.6))
    bullets(s, items, Inches(0.8), Inches(5.25), Inches(11.7), Inches(1.7),
            size=14, gap=6)
    footer(s)


# 11. Xulosa
def slide_summary():
    s = new_slide()
    header_bar(s, "Xulosa va texnologiyalar")
    bullets(s, [
        "Yopiq AI sikli: Upload → Auto-AI → Annotation → Dataset → Yangi model",
        "Backend: Python · FastAPI · Uvicorn  |  AI: PyTorch · Ultralytics YOLO",
        "DICOM: pydicom · highdicom · pylibjpeg  |  Radiomics: GLCM/GLRLM/GLSZM/NGTDM",
        "Xavfsizlik: JWT + TOTP (2FA) · avtomatik PHI de-identifikatsiya · audit",
        "Eksport: YOLO · VOC · CSV · DICOM-SEG · DICOM-SR · NIfTI",
        "Maxsus model arxitekturalari: BCA-YOLO · TILLNet-Det · XS-Classifier",
    ], Inches(0.7), Inches(1.5), Inches(12), Inches(4.2), size=18, gap=12)
    chip(s, "Faqat ilmiy-tadqiqot maqsadida · klinikada qo'llashdan oldin validatsiya talab etiladi",
         Inches(0.7), Inches(6.1), w=Inches(11.9), h=Inches(0.6),
         fill=RGBColor(0xFD, 0xEC, 0xEC), tcolor=RGBColor(0xC0, 0x39, 0x2B))
    footer(s)


def build():
    slide_title()
    slide_intro()
    slide_arch()
    slide_cycle_overview()
    slide_stage(
        1, "Bosqich 1 — Upload (DICOM yuklash)",
        "POST /api/upload",
        ["DICOM fayl noyob ID bilan uploads/<id>.dcm ga saqlanadi",
         "pydicom validatsiyasi — yaroqsiz fayl rad etiladi (HTTP 400)",
         "AVTO DE-IDENTIFY: PHI tag'lari DARHOL tozalanadi (annotatsiyadan oldin)",
         "Metama'lumot qaytariladi: o'lcham, modality, view, laterality, kadrlar",
         "Auto-AI fon (background) vazifasiga navbatga qo'yiladi",
         ("Upload bloklanmaydi — DICOM darhol ko'rinadi, bbox ~10–20s da paydo bo'ladi", True)],
    )
    slide_stage(
        2, "Bosqich 2 — Auto-AI (avtomatik inference)",
        "_auto_infer_uploaded  (background)",
        ["DICOM → PNG render → YOLO inference (infer_png)",
         "Har bir deteksiya ISHONCH (confidence) zonasiga ajratiladi",
         "Pseudo-annotatsiya: created_by = \"ai:<model>\"",
         "conf < 0.20 — saqlanmaydi (tashlanadi)",
         ("Funksiya hech qachon xato qaytarmaydi — upload xavfsiz", True)],
        extra_img="zones.png",
    )
    slide_stage(
        3, "Bosqich 3 — Annotation (radiolog)",
        "PUT /api/annotations · /status · /history",
        ["Radiolog AI takliflarini tasdiqlaydi / tahrirlaydi / o'chiradi",
         "Zarur bo'lsa yangi bbox yoki polygon qo'shadi",
         "Multi-label: bitta belgi bir nechta yorliqqa ega bo'lishi mumkin",
         "Status: edited / approved / submitted",
         "Har bir o'zgarish audit jurnaliga yoziladi (kim · qachon · nima)",
         "/training/suggestion → ≥50 annotatsiyada 'qayta o'qitish' tavsiyasi"],
    )
    slide_stage(
        4, "Bosqich 4 — Training dataset",
        "POST /api/training/prepare",
        ["Annotatsiyalardan Ultralytics YOLO formatidagi dataset yaratiladi",
         "Filtrlar: include_ai (AI belgilarini qo'shish), statuses",
         "bbox / polygon → YOLO normalized formatga aylantiriladi",
         "BEMOR darajasida train/val split — data leakage oldini oladi",
         "seed orqali takrorlanuvchi (reproducible) bo'linish"],
        code=["<dest>/", "  images/{train,val}/", "    <id>.png",
              "  labels/{train,val}/", "    <id>.txt", "  data.yaml"],
    )
    slide_stage(
        5, "Bosqich 5 — Yangi model (o'qitish + deploy)",
        "POST /api/training/run → _run_yolo_train",
        ["Ultralytics YOLO o'qitish fon rejimida boshlanadi (run_id)",
         "Parametrlar: base_model · epochs · imgsz · batch · optimizer · lr",
         "Augmentation: hsv · fliplr · scale · mosaic · mixup · early stopping",
         "deploy_after=True → o'qitilgan model AVTOMATIK joylanadi",
         "Holat kuzatuvi: /training/status/{run_id} · /training/runs",
         ("Yangi model keyingi Auto-AI'da ishlatiladi → sikl yopiladi", True)],
    )
    slide_loop()

    # --- Real UI skrinshotlari ---
    slide_ui(
        "Veb-interfeys — kirish (login)", "ui_login.png",
        ["JWT autentifikatsiya",
         "Ixtiyoriy TOTP (2FA)",
         "Rollar: admin · reviewer · annotator",
         "Rate-limit himoyasi (10/min)"],
    )
    slide_ui(
        "Veb-interfeys — DICOM ko'ruvchi va annotatsiya", "ui_viewer.png",
        ["BBox · Polygon · Ruler · Angle · Smart click",
         "AI takliflari rangli zonalar bilan",
         "Metadata PHI'siz (ANONYMOUS^PATIENT)",
         "Eksport: COCO · YOLO · VOC · CSV",
         "DICOM-SEG · SR · Mask · Radiomics"],
    )
    slide_ui(
        "Veb-interfeys — Model Studio (o'qitish)", "ui_studio.png",
        ["Dataset (data.yaml) tanlash",
         "Base model · pretrained · resume",
         "Epochs · batch · imgsz · optimizer · LR",
         "Augmentation sozlamalari",
         "Run tarixi va aktiv o'qitish maslahati"],
    )

    # --- Maxsus model arxitekturalari ---
    slide_model(
        "Model arxitekturasi — BCA-YOLO", "arch_bca_yolo.png",
        ["Bilateral Cross-Attention (BCA): chap/o'ng ko'krak assimetriyasini hisobga oladi",
         "Inter-View Consistency (IVC): CC + MLO ko'rinishlarini birlashtiradi",
         "Ordinal BI-RADS regressiya boshi (cumulative link)"],
    )
    slide_model(
        "Model arxitekturasi — TILLNet-Det", "arch_tillnet.png",
        ["Cross-script matn enkoderi (o'zbek-Cy / o'zbek-Lat / rus / ingliz)",
         "FiLM modulyatsiya: hisobot matni vizual FPN'ni shartlashtiradi",
         "Anchor-free FCOS head — classification · regression · centerness"],
    )

    slide_summary()
    prs.save(str(OUT))
    print(f"Saqlandi: {OUT}  ({len(prs.slides.__iter__.__self__._sldIdLst)} slayd)")


if __name__ == "__main__":
    build()
