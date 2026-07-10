# -*- coding: utf-8 -*-
"""MAMOGRAF — PhD dissertatsiyasi (.docx) generatori.

05.01.11 — Raqamli texnologiyalar va sunʼiy intellekt.
Texnika fanlari boʻyicha falsafa doktori (PhD). Hajmi >=120 sahifa.
UI skrinshotlarsiz; formulalar (matplotlib) va model arxitektura diagrammalari bilan.
Manba: muallifning BCA-YOLO va Radiomic Faster R-CNN maqolalari + MAMOGRAF tizimi.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "doc_assets"
EQ = ASSETS / "eq"
EQ.mkdir(parents=True, exist_ok=True)
OUT = ROOT / "MAMOGRAF_PhD_dissertatsiya.docx"

ACCENT = RGBColor(0x14, 0x2C, 0x52)
MUTED = RGBColor(0x55, 0x55, 0x55)
SECTIONS = []


def section(fn):
    SECTIONS.append(fn)
    return fn


# --------------------------------------------------------------------------- #
# Formula renderer                                                            #
# --------------------------------------------------------------------------- #
def render_eq(name, latex, fontsize=20):
    path = EQ / f"{name}.png"
    fig = plt.figure(figsize=(0.01, 0.01))
    fig.text(0.0, 0.0, f"${latex}$", fontsize=fontsize, color="black")
    fig.savefig(str(path), dpi=200, bbox_inches="tight", pad_inches=0.12,
                transparent=False, facecolor="white")
    plt.close(fig)


FORMULAS = {
    "conv": r"y_{i,j}^{(c)} = \sum_{m}\sum_{n}\sum_{c'} w_{m,n}^{(c,c')}\,x_{i+m,\,j+n}^{(c')} + b^{(c)}",
    "relu": r"\mathrm{ReLU}(x)=\max(0,x),\qquad \sigma(x)=\frac{1}{1+e^{-x}}",
    "softmax": r"\mathrm{softmax}(z)_i = \frac{e^{z_i}}{\sum_{j} e^{z_j}}",
    "attn": r"\mathrm{Attn}(Q,K,V) = \mathrm{softmax}\!\left(\frac{Q\,K^{\top}}{\sqrt{d_k}}\right) V",
    "mha": r"\mathrm{MHA}(Q,K,V)=\mathrm{Concat}(h_1,\dots,h_H)\,W^{O},\quad h_i=\mathrm{Attn}(QW_i^{Q},KW_i^{K},VW_i^{V})",
    "bca_attn": r"A^{(s)} = \mathrm{softmax}\!\left(\frac{Q^{(s)}{K^{(s)}}^{\top}}{\sqrt{d}}\right),\qquad \Delta F_L^{(s)} = A^{(s)} V_R^{(s)}",
    "bca_res": r"F'^{(s)}_L \;=\; F^{(s)}_L \;+\; \alpha\,\cdot\,\Delta F^{(s)}_L,\qquad \alpha \leftarrow 0",
    "asym": r"\mathcal{L}_{asym} \;=\; \frac{1}{|\Omega|}\sum_{(s,v)\in\Omega}\left(\bar{A}^{(s)}_v - m^{(s)}_v\right)^2",
    "ivc_gap": r"\hat{o}_v \;=\; \frac{1}{H_s W_s}\sum_{i=1}^{H_s W_s} o_v^{(s)}(i)",
    "ivc": r"\mathcal{L}_{IVC} \;=\; \left(\hat{o}_{CC} - \hat{o}_{MLO}\right)^2",
    "ordinal": r"\mathcal{L}_{ord} = -\sum_{k=0}^{K-2}\left( t_k\,\log\sigma(\theta_k-f) + (1-t_k)\,\log(1-\sigma(\theta_k-f)) \right),\ \ t_k=\mathbf{1}(y\leq k)",
    "thresh": r"\theta_k \;=\; \theta_0 + \sum_{j=1}^{k}\mathrm{softplus}(\tau_j),\qquad \mathrm{softplus}(\tau)=\log(1+e^{\tau})",
    "jacobian": r"\frac{\partial \theta_k}{\partial \tau_j} = \sigma(\tau_j)\,\mathbf{1}(j\leq k)",
    "grad_alpha": r"\frac{\partial \mathcal{L}}{\partial \alpha} \;=\; \left\langle \frac{\partial \mathcal{L}}{\partial F'},\ \Delta F \right\rangle_F",
    "ce": r"\mathcal{L}_{CE} = -\sum_{c} y_c \log \hat{y}_c",
    "focal": r"\mathcal{L}_{focal} = -\alpha_t\,(1-p_t)^{\gamma}\,\log(p_t)",
    "ciou": r"\mathcal{L}_{box}=1-\mathrm{IoU}+\frac{\rho^2(b,b^{gt})}{c^2}+\beta\,v",
    "dfl": r"\mathcal{L}_{dfl} = -\left((y_{i+1}-y)\log \hat{p}_i + (y-y_i)\log \hat{p}_{i+1}\right)",
    "total": r"\mathcal{L} = \mathcal{L}_{box} + \mathcal{L}_{cls} + \mathcal{L}_{dfl} + \lambda_1\mathcal{L}_{asym} + \lambda_2\mathcal{L}_{IVC} + \lambda_3\mathcal{L}_{ord}",
    "film": r"\mathrm{FiLM}(F\,|\,t)=\gamma(t)\odot F + \beta(t)",
    "tfidf": r"\mathrm{tfidf}(w,d)=\mathrm{tf}(w,d)\cdot \log\frac{N}{1+\mathrm{df}(w)}",
    "zscore": r"\tilde{x}=\frac{x-\mu}{\sigma},\qquad x_{norm}=\frac{x-\min(x)}{\max(x)-\min(x)}",
    "glcm": r"\mathrm{Contrast}=\sum_{i,j}(i-j)^2 p(i,j),\quad \mathrm{Energy}=\sum_{i,j}p(i,j)^2,\quad H=-\sum_{i,j}p(i,j)\log p(i,j)",
    "homog": r"\mathrm{Homogeneity}=\sum_{i,j}\frac{p(i,j)}{1+|i-j|},\qquad \mathrm{Correlation}=\sum_{i,j}\frac{(i-\mu_i)(j-\mu_j)p(i,j)}{\sigma_i \sigma_j}",
    "fusion": r"z \;=\; \phi\left(\,[\,f_{deep}\,\Vert\, f_{radiomic}\,]\,\right),\qquad \hat{y}=\mathrm{softmax}(W z + b)",
    "iou": r"\mathrm{IoU}(B_p,B_g) \;=\; \frac{|B_p \cap B_g|}{|B_p \cup B_g|}",
    "prf": r"P=\frac{TP}{TP+FP},\quad R=\frac{TP}{TP+FN},\quad F_1=\frac{2\,P\,R}{P+R}",
    "sesp": r"\mathrm{Se}=\frac{TP}{TP+FN},\qquad \mathrm{Sp}=\frac{TN}{TN+FP}",
    "ap_map": r"\mathrm{AP}=\int_{0}^{1} P(R)\,dR,\qquad \mathrm{mAP} = \frac{1}{C}\sum_{c=1}^{C}\mathrm{AP}_c",
    "auc": r"\mathrm{AUC}=\int_{0}^{1}\mathrm{TPR}\left(\mathrm{FPR}^{-1}(u)\right)\,du",
    "kappa": r"\kappa_w = 1-\frac{\sum_{i,j} w_{ij}\,O_{ij}}{\sum_{i,j} w_{ij}\,E_{ij}},\qquad w_{ij}=\frac{(i-j)^2}{(K-1)^2}",
    "dice": r"\mathrm{Dice}(X,Y) \;=\; \frac{2\,|X\cap Y|}{|X|+|Y|},\qquad \mathrm{Se}=\frac{|X\cap Y|}{|Y|}",
}


# --------------------------------------------------------------------------- #
# Word helpers                                                               #
# --------------------------------------------------------------------------- #
def setup(doc):
    sec = doc.sections[0]
    sec.page_height = Cm(29.7)
    sec.page_width = Cm(21.0)
    sec.left_margin = Cm(3.0)
    sec.right_margin = Cm(1.5)
    sec.top_margin = Cm(2.0)
    sec.bottom_margin = Cm(2.0)
    n = doc.styles["Normal"]
    n.font.name = "Times New Roman"
    n.font.size = Pt(14)
    pf = n.paragraph_format
    pf.line_spacing = 1.5
    pf.space_after = Pt(0)
    for lvl, sz in ((1, 15), (2, 14), (3, 14)):
        st = doc.styles[f"Heading {lvl}"]
        st.font.name = "Times New Roman"
        st.font.size = Pt(sz)
        st.font.bold = True
        st.font.color.rgb = ACCENT


def h1(doc, t):
    p = doc.add_heading(level=1)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run(t.upper()).bold = True


def h2(doc, t):
    doc.add_heading(t, level=2)


def para(doc, t, just=True, bold=False, italic=False, muted=False, first_line=True):
    p = doc.add_paragraph()
    if just:
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    if first_line:
        p.paragraph_format.first_line_indent = Cm(1.0)
    for i, seg in enumerate(t.split("**")):
        r = p.add_run(seg)
        r.bold = bold or (i % 2 == 1)
        r.italic = italic
        if muted:
            r.font.color.rgb = MUTED
    return p


def lead(doc, label, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.first_line_indent = Cm(1.0)
    p.add_run(label + " ").bold = True
    p.add_run(text)
    return p


def bullets(doc, items, numbered=False):
    style = "List Number" if numbered else "List Bullet"
    for it in items:
        p = doc.add_paragraph(style=style)
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        for i, seg in enumerate(it.split("**")):
            p.add_run(seg).bold = (i % 2 == 1)


def eq(doc, name, number=None, width=None):
    from PIL import Image
    path = EQ / f"{name}.png"
    if not path.exists():
        return
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    iw, ih = Image.open(path).size
    w = width or min(6.2, max(1.6, iw / 230))
    p.add_run().add_picture(str(path), width=Inches(w))
    if number:
        p.add_run("        (" + str(number) + ")").font.size = Pt(12)


def img(doc, name, width=5.6, caption=None):
    path = ASSETS / name
    if not path.exists():
        return
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(str(path), width=Inches(width))
    if caption:
        c = doc.add_paragraph()
        c.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = c.add_run(caption)
        r.italic = True
        r.font.size = Pt(12)


def img_path(doc, path, width=5.6, caption=None):
    """img() bilan bir xil, lekin to'liq yo'l qabul qiladi (ASSETS'dan tashqaridagi rasmlar)."""
    from pathlib import Path as _P
    path = _P(path)
    if not path.exists():
        return
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(str(path), width=Inches(width))
    if caption:
        c = doc.add_paragraph()
        c.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = c.add_run(caption)
        r.italic = True
        r.font.size = Pt(12)


def table(doc, headers, rows, caption=None):
    if caption:
        c = doc.add_paragraph()
        c.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = c.add_run(caption)
        r.bold = True
        r.font.size = Pt(12)
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    for i, hh in enumerate(headers):
        cell = t.rows[0].cells[i]
        cell.text = ""
        rr = cell.paragraphs[0].add_run(hh)
        rr.bold = True
        rr.font.size = Pt(12)
    for row in rows:
        cells = t.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = ""
            cells[i].paragraphs[0].add_run(str(val)).font.size = Pt(12)
    doc.add_paragraph()


def concl(doc, bob, items):
    h2(doc, f"{bob} bob boʻyicha xulosalar")
    bullets(doc, items, numbered=True)


def pb(doc):
    doc.add_page_break()


# --------------------------------------------------------------------------- #
# TITUL                                                                       #
# --------------------------------------------------------------------------- #
@section
def titul(doc):
    def c(txt, sz=14, bold=False, sp=0, align=WD_ALIGN_PARAGRAPH.CENTER):
        p = doc.add_paragraph()
        p.alignment = align
        p.paragraph_format.space_after = Pt(sp)
        p.paragraph_format.first_line_indent = Cm(0)
        r = p.add_run(txt)
        r.bold = bold
        r.font.size = Pt(sz)
        return p
    c("OʻZBEKISTON RESPUBLIKASI OLIY TAʼLIM, FAN VA INNOVATSIYALAR VAZIRLIGI", 13, True, 2)
    c("RAQAMLI TEXNOLOGIYALAR VA SUNʼIY INTELLEKTNI RIVOJLANTIRISH "
      "ILMIY-TADQIQOT INSTITUTI", 13, True, 24)
    c("Qoʻlyozma huquqida", 12)
    c("UDK 004.93", 12, sp=28)
    c("TURAQULOV SHOXRUX XUDAYAROVICH", 14, True, 22)
    c("MAMMOGRAFIYA TASVIRLARI ASOSIDA KOʻKRAK OʻSMA SOHALARINI ANIQLASH, "
      "BI-RADS BOʻYICHA TASNIFLASH VA AVTOMATIK XULOSA SHAKLLANTIRISHNING "
      "SUNʼIY INTELLEKTGA ASOSLANGAN ALGORITM VA DASTURIY MAJMUASI", 14, True, 22)
    c("05.01.11 — Raqamli texnologiyalar va sunʼiy intellekt", 13, True, 6)
    c("Texnika fanlari boʻyicha falsafa doktori (PhD)", 12, sp=0)
    c("ilmiy darajasini olish uchun yozilgan", 12, sp=18)
    c("DISSERTATSIYA", 16, True, 34)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p.add_run("Ilmiy rahbar: professor Xamdamov Rustam").font.size = Pt(12)
    c(f"Toshkent — {date.today().year}", 13, True, 0)
    pb(doc)


# --------------------------------------------------------------------------- #
# MUNDARIJA                                                                   #
# --------------------------------------------------------------------------- #
@section
def mundarija(doc):
    h1(doc, "Mundarija")
    items = [
        ("KIRISH", True), ("", False),
        ("I BOB. MAMMOGRAFIYA TASVIRLARIGA ISHLOV BERISH VA TAHLIL QILISH MASALASINING ZAMONAVIY HOLATI", True),
        ("1.1-§. Koʻkrak saratoni epidemiologiyasi va skrining mammografiyasi", False),
        ("1.2-§. Tibbiy tasvirlarni qayd etish usullari va DICOM standarti", False),
        ("1.3-§. Tasvirlarga dastlabki ishlov berish va sifatini oshirish algoritmlari", False),
        ("1.4-§. Obyektlarni aniqlashning chuqur oʻrganishga asoslangan usullari", False),
        ("1.5-§. Oʻzaro eʼtibor mexanizmlari, ordinal regressiya va radiomika", False),
        ("1.6-§. Maʼlumotlar toʻplamlari, baholash metrikalari va tadqiqot masalasining qoʻyilishi", False),
        ("1.7-§. Mammografiyada chuqur oʻrganishning tizimli sharhi", False),
        ("1.8-§. Koʻpkoʻrinishli va ikki tomonlama yondashuvlarning qiyosiy tahlili", False),
        ("I bob boʻyicha xulosalar", False),
        ("II BOB. KOʻKRAK OʻSMALARINI ANIQLASH VA TASNIFLASH ALGORITMLARI", True),
        ("2.1-§. Belgilashlar va masalaning matematik qoʻyilishi", False),
        ("2.2-§. Ikki tomonlama oʻzaro eʼtibor (BCA) bloki", False),
        ("2.3-§. Koʻrinishlararo muvofiqlik (IVC) moduli", False),
        ("2.4-§. Ordinal BI-RADS regressiyasi va kompozit yoʻqotish funksiyasi", False),
        ("2.5-§. Radiomik belgilarni chuqur oʻrganish bilan birlashtirish", False),
        ("2.6-§. Multimodal (matn-asosli) detektsiya: TILLNet va matn tasniflagichi", False),
        ("2.7-§. Oʻqitish protseduri, augmentatsiya va giperparametrlar", False),
        ("II bob boʻyicha xulosalar", False),
        ("II BOB (DAVOMI). BULCHA DASTURLASH ASOSIDA INFORMATIV BELGILARNI TANLASH VA "
         "INTERPRETATSIYALANADIGAN GIBRID ANSAMBL", True),
        ("2.8-§. Masalaning qoʻyilishi va belgilar fazosi", False),
        ("2.9-§. Bulcha belgi tanlash mezoni", False),
        ("2.10-§. Ranjirlangan qator va prefiks boʻyicha tanlash", False),
        ("2.11-§. Minimal masofa tasniflagichi", False),
        ("2.12-§. Gibrid ansambl va sifat mezoni", False),
        ("2.13-§. Eksperimental tadqiqot natijalari", False),
        ("2.14-§. Natijalarni muhokama qilish va klinik talqin", False),
        ("II (davomi) bob boʻyicha xulosalar", False),
        ("III BOB. ALGORITMLARNI AMALGA OSHIRUVCHI DASTURIY MAJMUA", True),
        ("3.1-§. Tizim arxitekturasi, maxfiylik va xavfsizlik", False),
        ("3.2-§. Annotatsiya, faol oʻrganish va AI yordami", False),
        ("3.3-§. Model oʻqitish konveyeri (Model Studio) va resurslar monitoringi", False),
        ("3.4-§. Avtomatik xulosa shakllantirish, DICOM SR va PACS integratsiyasi", False),
        ("3.5-§. Maʼlumotlar modeli, dasturiy interfeyslar va ish oqimi", False),
        ("III bob boʻyicha xulosalar", False),
        ("III bob (davomi). Avtomatlashtirilgan annotatsiya yigʻish quyi tizimining matematik modeli", True),
        ("IV BOB. TAJRIBAVIY TADQIQOTLAR VA AMALIYOTDA QOʻLLASH", True),
        ("4.1-§. Maʼlumotlar toʻplami, eksperiment sxemasi va baholash metodologiyasi", False),
        ("4.2-§. Tajriba natijalari, ablatsion tahlil va muhokama", False),
        ("4.3-§. Hisoblash murakkabligi va inferens samaradorligi", False),
        ("4.4-§. Dasturiy majmuani amaliyotda qoʻllash va joriy etish", False),
        ("4.5-§. Statistik tahlil, xatolar tahlili va cheklovlar", False),
        ("IV bob boʻyicha xulosalar", False),
        ("XULOSA", True),
        ("FOYDALANILGAN ADABIYOTLAR ROʻYXATI", True),
        ("ILOVALAR", True),
    ]
    for t, bold in items:
        p = doc.add_paragraph(t)
        p.paragraph_format.line_spacing = 1.4
        p.paragraph_format.first_line_indent = Cm(0)
        if not bold and t:
            p.paragraph_format.left_indent = Cm(0.7)
        if bold and t:
            p.runs[0].bold = True
    pb(doc)


@section
def frontmatter(doc):
    h1(doc, "Shartli qisqartmalar va atamalar roʻyxati")
    abbr = [
        ("AI", "sun'iy intellekt (Artificial Intelligence)"),
        ("CAD", "kompyuterli aniqlash/tashxis (Computer-Aided Detection/Diagnosis)"),
        ("CNN", "konvolyutsion neyron tarmoq (Convolutional Neural Network)"),
        ("YOLO", "bir bosqichli obyekt detektori (You Only Look Once)"),
        ("BCA", "ikki tomonlama o'zaro e'tibor (Bilateral Cross-Attention)"),
        ("IVC", "ko'rinishlararo muvofiqlik (Inter-View Consistency)"),
        ("BI-RADS", "Breast Imaging Reporting and Data System"),
        ("CC", "kraniokaudal proyeksiya (Craniocaudal)"),
        ("MLO", "mediolateral qiyshiq proyeksiya (Mediolateral Oblique)"),
        ("DICOM", "tibbiy tasvirlar standarti (Digital Imaging and Communications in Medicine)"),
        ("SR", "strukturaviy hisobot (Structured Report)"),
        ("PACS", "tasvirlar arxivi va aloqa tizimi (Picture Archiving and Communication System)"),
        ("PHI", "himoyalangan shaxsiy sog'liq ma'lumotlari (Protected Health Information)"),
        ("GPU", "grafik protsessor (Graphics Processing Unit)"),
        ("VRAM", "video xotira (Video RAM)"),
        ("IoU", "kesishish-birlashish nisbati (Intersection over Union)"),
        ("mAP", "o'rtacha aniqlik (mean Average Precision)"),
        ("AP", "aniqlik (Average Precision)"),
        ("F1", "precision va recall garmonik o'rtachasi"),
        ("AUC", "ROC egri chizig'i ostidagi yuza (Area Under Curve)"),
        ("ROC", "Receiver Operating Characteristic"),
        ("FROC", "Free-response ROC"),
        ("GLCM", "kulrang darajalar birgalikdagi paydo bo'lish matritsasi"),
        ("CLAHE", "kontrast cheklangan adaptiv gistogramma tenglashtirish"),
        ("DFL", "taqsimot fokal yo'qotishi (Distribution Focal Loss)"),
        ("CIoU", "Complete IoU yo'qotishi"),
        ("FiLM", "xususiyatga asoslangan chiziqli modulyatsiya"),
        ("TTA", "test vaqti augmentatsiyasi (Test-Time Augmentation)"),
        ("WBF", "vaznli quti birlashtirish (Weighted Box Fusion)"),
        ("JWT", "JSON Web Token"),
        ("TOTP", "vaqtga asoslangan bir martalik parol (Time-based One-Time Password)"),
        ("GAN", "generativ raqobat tarmog'i (Generative Adversarial Network)"),
        ("LLM", "katta til modeli (Large Language Model)"),
    ]
    for a, d in abbr:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.first_line_indent = Cm(0)
        p.paragraph_format.line_spacing = 1.3
        r = p.add_run(a + " — ")
        r.bold = True
        p.add_run(d).font.size = Pt(13)

    h1(doc, "Asosiy shartli belgilar")
    syms = [
        ("F_v^(s)", "v ko'rinishning s miqyosidagi xususiyat xaritasi"),
        ("Q, K, V", "o'zaro e'tibordagi so'rov, kalit va qiymat matritsalari"),
        ("A^(s)", "s miqyosdagi e'tibor og'irliklari matritsasi"),
        ("α", "BCA qoldiq darvozasining o'rganiluvchi skalyar koeffitsiyenti"),
        ("ΔF", "kontralateral o'zaro e'tibor farq signali"),
        ("ô_v", "v ko'rinishning global o'rtacha obyektlik logiti"),
        ("θ_k", "ordinal regressiyaning k-ostonasi"),
        ("τ_j", "ostonalarning cheklanmagan parametrlari"),
        ("σ(·)", "sigmoid funksiyasi"),
        ("L", "yo'qotish (loss) funksiyasi"),
        ("λ_1, λ_2, λ_3", "regulyarizatsiya giperparametrlari"),
        ("κ_w", "kvadratik og'irlikli Koen kappasi"),
        ("Se, Sp", "sezgirlik va xoslik"),
    ]
    for a, d in syms:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.first_line_indent = Cm(0)
        p.paragraph_format.line_spacing = 1.3
        r = p.add_run(a + " — ")
        r.bold = True
        p.add_run(d).font.size = Pt(13)
    pb(doc)


# --------------------------------------------------------------------------- #
# KIRISH                                                                      #
# --------------------------------------------------------------------------- #
@section
def kirish(doc):
    h1(doc, "Kirish")
    lead(doc, "Dissertatsiya mavzusining dolzarbligi va zarurati.",
         "Jahonda ko'krak saratoni ayollar o'rtasida eng ko'p uchraydigan onkologik "
         "kasallik bo'lib, onkologik o'limning yetakchi sabablaridan biridir. Jahon "
         "sog'liqni saqlash tashkiloti (JSST) va Globocan ma'lumotlariga ko'ra, har "
         "yili dunyo bo'ylab millionlab yangi holatlar qayd etilib, yuz minglab ayol "
         "bu kasallikdan vafot etadi. Kasallikni erta, simptomsiz bosqichida aniqlash "
         "besh yillik yashash ko'rsatkichini sezilarli oshiradi va davolash imkoniyatlarini "
         "kengaytiradi. Erta aniqlashning eng samarali vositasi — skrining "
         "mammografiyasidir. Biroq mammografiya tasvirlarini qo'lda talqin qilish "
         "radiologning malakasiga bog'liq bo'lib, kuzatuvchilararo va kuzatuvchi ichidagi "
         "o'zgaruvchanlik, ish hajmining kattaligi natijasidagi charchoq hamda dastlabki "
         "bosqich shikastlanishlarning nozik tabiati kabi obyektiv cheklovlarga duch keladi. "
         "Ushbu cheklovlar soxta-musbat va soxta-manfiy tashxislarga olib kelishi mumkin. "
         "Shu bois, mammografiya tasvirlarini sun'iy intellekt yordamida avtomatik tahlil "
         "qiluvchi, radiolog qaroriga yordam beruvchi (computer-aided diagnosis, CAD) "
         "tizimlarni yaratish dolzarb ilmiy-amaliy masala hisoblanadi.")
    para(doc,
         "So'nggi o'n yillikda chuqur o'rganish (deep learning) usullari tibbiy tasvirlarni "
         "tahlil qilishda sezilarli yutuqlarga erishdi. Biroq mavjud yondashuvlarning "
         "aksariyati mammografiyaning to'rtta standart ko'rinishini (L-CC, R-CC, L-MLO, "
         "R-MLO) bir-biridan mustaqil qayta ishlaydi va radiologlar amalda foydalanadigan "
         "ikki tomonlama (kontralateral) asimmetriya hamda ko'rinishlararo muvofiqlik "
         "signallarini hisobga olmaydi. Bundan tashqari, BI-RADS baholash shkalasi "
         "tartibli (ordinal) bo'lishiga qaramay, ko'p modellar uni nominal sinflar "
         "sifatida talqin qiladi va xatolarning klinik narxidagi farqni e'tiborsiz "
         "qoldiradi. Mazkur kamchiliklar ushbu dissertatsiya tadqiqotining ilmiy "
         "yo'nalishini belgilab berdi.")
    para(doc, "Sun'iy intellektga asoslangan tibbiy tashxis tizimlari bozori jadal "
              "o'smoqda. Sog'liqni saqlash sohasidagi axborot texnologiyalari va AI "
              "yechimlariga talab har yili barqaror ortib bormoqda, bu esa ushbu "
              "yo'nalishdagi ilmiy izlanishlarning iqtisodiy va ijtimoiy ahamiyatini "
              "ko'rsatadi. Rivojlangan mamlakatlarda mammografiya tasvirlarini avtomatik "
              "tahlil qilish tizimlari klinik amaliyotga keng joriy etilmoqda, biroq "
              "ularning ko'pchiligi tashqi bulutli xizmatlarga bog'liq bo'lib, ma'lumotlar "
              "maxfiyligi va infratuzilma cheklovlari masalalarini keltirib chiqaradi. "
              "Mahalliy (oflayn) ishlovchi, mavjud PACS infratuzilmasiga moslashuvchan "
              "tizimlarni ishlab chiqish rivojlanayotgan mamlakatlar, jumladan O'zbekiston "
              "uchun alohida ahamiyatga ega.")
    para(doc, "Mammografiya tasvirlarini tahlil qilishda AI ning ikki asosiy klinik "
              "qiymati mavjud: (i) radiolog ish yukini kamaytirish va tahlilni "
              "tezlashtirish (ayniqsa kamchil kadr sharoitida); (ii) tashxis aniqligini "
              "oshirib, soxta-musbat va soxta-manfiy holatlarni kamaytirish. Ushbu "
              "tadqiqotda ishlab chiqilgan tizim har ikkala qiymatni — aniq aniqlash, "
              "ordinal BI-RADS baholash va avtomatik xulosa shakllantirish orqali — "
              "ta'minlashga qaratilgan.")
    lead(doc, "Tadqiqotning respublika fan va texnologiyalari rivojlanishining ustuvor "
              "yo'nalishlariga bog'liqligi.",
         "O'zbekiston Respublikasida onkologik kasalliklarni erta aniqlash va o'lim "
         "ko'rsatkichini kamaytirish davlat siyosatining ustuvor yo'nalishlaridan biri "
         "hisoblanadi. «O'zbekiston-2030» strategiyasi hamda O'zbekiston Respublikasi "
         "Prezidentining «Raqamli O'zbekiston-2030» strategiyasini tasdiqlash to'g'risidagi "
         "Farmonida raqamli texnologiyalar va sun'iy intellektni sog'liqni saqlash tizimiga "
         "keng joriy etish, tibbiy tasvirlar tahliliga asoslangan tashxis tizimlarini ishlab "
         "chiqish vazifalari belgilangan. Ushbu dissertatsiya tadqiqoti mazkur hujjatlarda "
         "qo'yilgan vazifalarni amalga oshirishga xizmat qiladi.")
    lead(doc, "Muammoning o'rganilganlik darajasi.",
         "Mammografik shikastlanishlarni aniqlashda zamonaviy chuqur o'rganish modellari "
         "— bir bosqichli (YOLO, SSD, RetinaNet) va ikki bosqichli (Faster R-CNN) "
         "detektorlar — keng qo'llanilmoqda. O'zaro e'tibor (attention) mexanizmlari "
         "ko'p modalli birlashtirishda samarali ekanligi ko'rsatilgan. Radiomika "
         "yo'nalishi tasvirdan miqdoriy belgilarni chiqarib, izohlanuvchanlikni "
         "oshirishga imkon beradi. Biroq ko'pko'rinishli, ikki tomonlama va ordinal "
         "induktiv taxminlarni yagona tarmoqda birlashtirgan, hamda topilmalardan "
         "avtomatik klinik xulosa shakllantirishni qo'llab-quvvatlovchi yaxlit yechim "
         "yetarlicha o'rganilmagan. Bu bo'shliq tadqiqotning ilmiy muammosini belgilaydi.")
    lead(doc, "Tadqiqotning maqsadi —",
         "mammografiya tasvirlarida ko'krak o'sma sohalarini ikki tomonlama asimmetriya "
         "va ko'rinishlararo muvofiqlikni hisobga olgan holda aniqlash, BI-RADS bo'yicha "
         "ordinal tasniflash hamda topilmalardan avtomatik klinik xulosa shakllantirishning "
         "sun'iy intellektga asoslangan algoritm va dasturiy majmuasini ishlab chiqishdan "
         "iborat.")
    para(doc, "**Tadqiqotning vazifalari:**", first_line=False)
    bullets(doc, [
        "mammografiya tasvirlarini tahlil qilishning zamonaviy holatini, mavjud usul va algoritmlarni tahlil qilish hamda ularning cheklovlarini aniqlash;",
        "kontralateral asimmetriyani hisobga oluvchi ikki tomonlama o'zaro e'tibor (BCA) blokini ishlab chiqish va uning gradiyent xossalarini tahlil qilish;",
        "CC va MLO ko'rinishlari o'rtasida obyektlik muvofiqligini ta'minlovchi ko'rinishlararo muvofiqlik (IVC) modulini taklif etish;",
        "BI-RADS kategoriyasini ordinal regressiya (monoton ostonalar bilan kumulyativ bog'lanish) orqali baholash algoritmini ishlab chiqish;",
        "radiomik belgilarni chuqur o'rganish tasvirlovchilari bilan birlashtiruvchi gibrid usulni qo'llash;",
        "annotatsiya, faol o'rganish, AI yordami va GPU'da model o'qitishni qo'llab-quvvatlovchi dasturiy majmuani loyihalash va amalga oshirish;",
        "topilmalardan grounded (faqat aniqlangan ma'lumotga asoslangan) avtomatik klinik xulosa shakllantirish va uni DICOM SR sifatida eksport qilish modulini ishlab chiqish;",
        "taklif etilgan algoritm va dasturiy majmuani tajribaviy baholash hamda amaliyotda qo'llash.",
    ], numbered=True)
    lead(doc, "Tadqiqotning obyekti —",
         "rentgen nurlari asosida turli proyeksiyalarda (CC, MLO) olingan raqamli "
         "mammografiya tasvirlari (DICOM formati) va ularga tegishli klinik hisobotlar, "
         "jumladan Respublika ixtisoslashtirilgan Onkologiya va Radiologiya ilmiy-amaliy "
         "tibbiy markazidan olingan (anonimlashtirilgan) klinik mammografiya ma'lumotlari "
         "hamda ochiq VinDr-Mammo to'plami.")
    lead(doc, "Tadqiqotning predmeti —",
         "mammografiya tasvirlarida o'sma sohalarini aniqlash, BI-RADS bo'yicha tasniflash "
         "va avtomatik xulosa shakllantirishning usul, algoritm va dasturiy vositalari.")
    lead(doc, "Tadqiqotning usullari.",
         "Tadqiqotda chuqur o'rganish (konvolyutsion neyron tarmoqlar, o'zaro e'tibor "
         "mexanizmi, kodlovchi-dekodlovchi arxitekturalar), tartibli (ordinal) regressiya, "
         "radiomik tahlil va tekstura tahlili (GLCM), raqamli tasvirga ishlov berish, "
         "optimallashtirish nazariyasi, ehtimollar nazariyasi va matematik statistika, "
         "dasturiy injiniring hamda ma'lumotlarni intellektual tahlil usullaridan "
         "foydalanilgan.")
    para(doc, "**Tadqiqotning ilmiy yangiligi quyidagilardan iborat:**", first_line=False)
    bullets(doc, [
        "**birinchi marta** har bir xususiyat miqyosida chap va ufqiy akslangan o'ng kontralateral xususiyat xaritalari o'rtasida o'zaro e'tiborni hisoblovchi, nolga initsializatsiyalanadigan o'rganiluvchi α koeffitsiyenti bilan boshqariladigan ikki tomonlama o'zaro e'tibor (BCA) bloki taklif etilgan, bu esa kontralateral asimmetriyani yagona uchidan-uchiga (end-to-end) o'rgatiladigan tarzda modelga kiritadi;",
        "bir tomonning kraniokaudal (CC) va mediolateral qiyshiq (MLO) ko'rinishlari o'rtasida obyektlik muvofiqligini ta'minlovchi, o'rganiluvchi kanalli darvozaga ega ko'rinishlararo muvofiqlik (IVC) moduli **ishlab chiqilgan**;",
        "BI-RADS kategoriyasini qat'iy monoton ostonalarga ega kumulyativ bog'lanish modeli orqali baholovchi, nominal kross-entropiya o'rniga ordinal yo'qotish funksiyasidan foydalanuvchi ordinal regressiya boshi **taklif etilgan**;",
        "radiomik (tekstura, shakl, intensivlik) belgilarni chuqur tasvirlovchilar bilan birlashtirib, modelning izohlanuvchanligini oshiruvchi va «qora quti» muammosini yumshatuvchi gibrid arxitektura **asoslangan**;",
        "aniqlangan strukturaviy topilmalardan butunlay lokal til modeli yordamida grounded (ma'lumot to'qimaydigan) avtomatik klinik xulosa shakllantiruvchi hamda uni DICOM SR sifatida eksport qiluvchi, PACS bilan integratsiyalashgan dasturiy yondashuv **ishlab chiqilgan**.",
    ])
    para(doc, "**Tadqiqotning amaliy natijalari:**", first_line=False)
    bullets(doc, [
        "DICOM ko'ruvchi, annotatsiya, AI inference, GPU'da model o'qitish, avtomatik hisobot va PACS integratsiyasini birlashtirgan MAMOGRAF dasturiy majmuasi;",
        "jonli metrikalar va resurslar monitoringi bilan GPU'da model o'qitish interfeysi (Model Studio);",
        "tashqi API kalitini va internetni talab qilmaydigan, butunlay lokal ishlovchi avtomatik hisobot generatori va DICOM SR eksporti.",
    ])
    lead(doc, "Tadqiqot natijalarining ishonchliligi",
         "algoritmlarni ishlab chiqishda chuqur o'rganish, optimallashtirish va radiomik "
         "tahlilning asoslangan matematik apparatidan foydalanilganligi, taklif etilgan "
         "modellarning ochiq VinDr-Mammo ma'lumotlar to'plamida baholanganligi va olingan "
         "natijalarning umume'tirof etilgan metrikalar (mAP, F1, IoU, sezgirlik) bilan "
         "tasdiqlanganligi bilan izohlanadi.")
    lead(doc, "Tadqiqotning ilmiy va amaliy ahamiyati.",
         "Ilmiy ahamiyati — mammografiyada ikki tomonlama asimmetriya, ko'pko'rinishli "
         "muvofiqlik va ordinal baholash kabi klinik induktiv taxminlarni rasmiy matematik "
         "shaklda ifodalashdan hamda ularning gradiyent xossalarini tahlil qilishdan "
         "iborat. Amaliy ahamiyati — ishlab chiqilgan dasturiy majmuani radiologiya "
         "bo'limlarida tashxis jarayonini tezlashtirish, kuzatuvchilararo o'zgaruvchanlikni "
         "kamaytirish va erta aniqlashni qo'llab-quvvatlash uchun qo'llash imkoniyatidir.")
    lead(doc, "Tadqiqot natijalarining joriy qilinishi.",
         "Tadqiqotda ishlab chiqilgan algoritmlar va MAMOGRAF dasturiy majmuasi Respublika "
         "ixtisoslashtirilgan Onkologiya va Radiologiya ilmiy-amaliy tibbiy markazidan "
         "olingan klinik mammografiya ma'lumotlari asosida sinovdan o'tkazilgan. [Joriy "
         "etilish dalolatnomasining raqami va sanasini to'ldiring.]")
    lead(doc, "Tadqiqot natijalarining aprobatsiyasi.",
         "Tadqiqot natijalari xalqaro ilmiy-amaliy anjumanda muhokama qilingan: «Kibernetika "
         "— zamonaviy sun'iy intellektning poydevori» xalqaro ilmiy-amaliy anjumani "
         "(Toshkent, 2026-yil 15–16-aprel), «Image classification algorithms based on "
         "neural network technologies for medical image analysis» ma'ruzasi.")
    lead(doc, "Tadqiqot natijalarining e'lon qilinganligi.",
         "Dissertatsiya mavzusi bo'yicha bir nechta ilmiy ish e'lon qilingan, jumladan:")
    bullets(doc, [
        "Turaqulov Sh.X. BCA-YOLO: ikki tomonlama o'zaro e'tibor, ko'rinishlararo muvofiqlik va ordinal BI-RADS regressiyasi asosida mammografik shikastlanishlarni aniqlash // Raqamli texnologiyalarning nazariy va amaliy masalalari xalqaro jurnali. — 2026. — № 9(2). — B. 58–66. — ISSN 2181-3086.",
        "Khamdamov R., Turaqulov Sh.X. TILLNet-Det: A Text-Informed Lesion Localization Network for Multilingual Mammography Detection in Low-Resource Settings // International Journal of Informatics and Data Science Research. — 2026.",
        "Khamdamov R., Turaqulov Sh.X. Annotatsiyasi kam sharoitlarda ko'p tilli mammografik o'choqlarni aniqlash uchun yopiq halqali tizim: radiolog-inson hamkorligi bilan matnga yo'naltirilgan zaif nazoratli o'qitish // Raqamli Transformatsiya va Sun'iy Intellekt. — 2026. — DOI: 10.5281/zenodo.20816862.",
        "Turaqulov Sh., Khamdamov R. Image classification algorithms based on neural network technologies for medical image analysis // «Kibernetika — zamonaviy sun'iy intellektning poydevori» xalqaro ilmiy-amaliy anjumani. — Toshkent, 2026.",
    ], numbered=True)
    lead(doc, "Dissertatsiyaning tuzilishi va hajmi.",
         "Dissertatsiya kirish, to'rtta bob, xulosa, foydalanilgan adabiyotlar ro'yxati va "
         "ilovalardan iborat. Ishda jadvallar, formulalar va rasmlar keltirilgan.")
    pb(doc)


# --------------------------------------------------------------------------- #
# I BOB                                                                       #
# --------------------------------------------------------------------------- #
@section
def bob1(doc):
    h1(doc, "I bob. Mammografiya tasvirlariga ishlov berish va tahlil qilish masalasining "
            "zamonaviy holati")

    h2(doc, "1.1-§. Koʻkrak saratoni epidemiologiyasi va skrining mammografiyasi")
    para(doc, "Ko'krak saratoni — ko'krak bezi to'qimasi hujayralarining nazoratsiz "
              "bo'linishi natijasida xavfli o'smaning rivojlanishi bilan tavsiflanuvchi "
              "kasallik. Jahon miqyosida u ayollar orasida eng ko'p tashxislanadigan "
              "onkologik kasallik hisoblanadi. Kasallikning bosqichi (stadiyasi) qancha "
              "erta aniqlansa, davolash samaradorligi va yashash ko'rsatkichi shuncha "
              "yuqori bo'ladi. Shu sababli aholini ommaviy tekshiruvdan o'tkazish — "
              "skrining — onkologik nazoratning asosiy strategiyasi sanaladi.")
    para(doc, "Skrining mammografiyasi past dozali rentgen nurlanishi yordamida ko'krak "
              "bezining ikki o'lchamli proyeksion tasvirini hosil qiladi. Standart protokol "
              "bo'yicha har bir tadqiqot uchun to'rtta ko'rinish olinadi: har bir ko'krakning "
              "kraniokaudal (CC, yuqoridan pastga) va mediolateral qiyshiq (MLO, qiyshiq "
              "burchak ostida) proyeksiyalari. Radiolog bu to'rt ko'rinishni yagona "
              "kontekstda baholaydi: (i) har bir proyeksiyada chap va o'ng ko'krakni "
              "solishtirib, normal anatomiyaga zid asimmetriyani aniqlaydi; (ii) bir "
              "ko'krakning CC va MLO ko'rinishlarini birlashtirib, shubhali o'choqning "
              "haqiqiyligini va fazoviy joylashuvini tasdiqlaydi. Aynan shu ikki "
              "tomonlama va ko'rinishlararo qiyoslash radiolog tahlilining markaziy "
              "elementidir, biroq u ko'pgina avtomatik tizimlarda hisobga olinmaydi.")
    para(doc, "Mammografiya tasvirida uchraydigan asosiy patologik belgilar quyidagilardir: "
              "massa (hajmli o'choq), mikrokalsifikatsiyalar (mayda kalsiy to'planmalari), "
              "arxitektura buzilishi va asimmetriya. Massalar shakli (yumaloq, oval, "
              "noto'g'ri), chegarasi (aniq, noaniq, spikulali) va zichligi bo'yicha "
              "tavsiflanadi; spikulali chegara xavflilikning muhim belgisidir.")

    para(doc, "Ko'krak saratonining rivojlanishiga ta'sir etuvchi xavf omillari qatoriga "
              "yosh (asosan 40 yoshdan keyin xavf ortadi), genetik moyillik (BRCA1/BRCA2 "
              "genlarining mutatsiyasi), oilaviy anamnez, hormonal omillar, ko'krak "
              "to'qimasining zichligi va turmush tarzi kiradi. Zich ko'krak to'qimasi "
              "(ACR C va D toifalari) ham saraton xavfini oshiradi, ham mammografik "
              "tahlilni qiyinlashtiradi, chunki zich to'qima shikastlanishni niqoblashi "
              "mumkin. Shu sababli ko'krak zichligini baholash skrining sifatining muhim "
              "ko'rsatkichidir.")
    para(doc, "Mammografiya fizik asosi rentgen nurlanishining to'qimalardan o'tishida "
              "turli darajada yutilishiga (attenuatsiya) tayanadi. Yog' to'qimasi, "
              "fibroglandulyar to'qima va kalsifikatsiyalar rentgen nurlarini turlicha "
              "yutadi, bu esa kontrast hosil qiladi. Zamonaviy raqamli mammografiya "
              "(full-field digital mammography, FFDM) plyonkali mammografiyani deyarli "
              "to'liq almashtirgan: u yuqori dinamik diapazon, raqamli arxivlash va "
              "kompyuterli tahlil imkonini beradi. Nurlanish dozasi ALARA (As Low As "
              "Reasonably Achievable) tamoyili asosida minimallashtiriladi.")
    para(doc, "So'nggi yillarda raqamli ko'krak tomosintezi (digital breast tomosynthesis, "
              "DBT) — ko'krakning bir qator qiyshiq proyeksiyalaridan uch o'lchamli "
              "rekonstruksiya hosil qiluvchi usul — keng tarqalmoqda. DBT to'qimalarning "
              "ustma-ust tushishi muammosini kamaytirib, ayniqsa zich ko'krakda aniqlikni "
              "oshiradi. Biroq ikki o'lchamli FFDM hozircha skriningning asosiy va eng "
              "keng tarqalgan usuli bo'lib qolmoqda, shu sababli ushbu tadqiqot aynan "
              "ikki o'lchamli to'rt ko'rinishli mammografiyaga qaratilgan.")
    para(doc, "Skrining samaradorligi sezgirlik (haqiqiy saratonlarni aniqlash ulushi) va "
              "xoslik (sog'lom holatlarni to'g'ri aniqlash ulushi) bilan o'lchanadi. "
              "Sezgirlikning pastligi soxta-manfiy (o'tkazib yuborilgan saraton) holatlarga, "
              "xoslikning pastligi esa soxta-musbat (keraksiz qo'shimcha tekshiruv va "
              "biopsiya) holatlarga olib keladi. AI tizimlarining asosiy maqsadi — ikkala "
              "ko'rsatkichni bir vaqtda yaxshilash va radiolog ish yukini kamaytirishdir.")

    h2(doc, "1.2-§. Tibbiy tasvirlarni qayd etish usullari va DICOM standarti")
    para(doc, "Tibbiy tasvirlarni qayd etishning turli usullari mavjud: rentgenografiya "
              "(jumladan mammografiya), kompyuter tomografiyasi (KT), magnit-rezonans "
              "tomografiyasi (MRT) va ultratovush tekshiruvi. Ularning har biri to'qimalar "
              "to'g'risida turlicha ma'lumot beradi. Ko'krak bezini tekshirishda "
              "mammografiya asosiy skrining usuli bo'lib qoladi.")
    para(doc, "Raqamli tibbiy tasvirlar **DICOM** (Digital Imaging and Communications in "
              "Medicine) standartida saqlanadi va almashinadi. DICOM fayli piksel "
              "ma'lumotlari bilan birga keng metama'lumotlar to'plamini — bemor (PatientID, "
              "PatientName), tadqiqot (StudyInstanceUID, StudyDate), qurilma (Manufacturer, "
              "ModelName) va tasvir (ViewPosition, ImageLaterality, PixelSpacing, Rows, "
              "Columns) — o'z ichiga oladi. Klinik tizimlar — PACS (Picture Archiving and "
              "Communication System) — tasvirlarni saqlash va almashish uchun DICOM tarmoq "
              "xizmatlaridan foydalanadi: C-ECHO (ulanishni tekshirish), C-FIND (qidirish), "
              "C-STORE (yuborish) va C-MOVE/C-GET (olib kelish). Tasvirlar tadqiqotga "
              "tayyorlanishidan oldin shaxsiy ma'lumotlar (Protected Health Information, "
              "PHI) anonimlashtirilishi maxfiylik talablariga ko'ra zarur.")

    para(doc, "DICOM standarti ma'lumotni teglar (tag) — guruh va element raqamlari "
              "bilan identifikatsiyalanadigan maydonlar — to'plami sifatida tashkil etadi. "
              "Har bir obyekt SOP (Service-Object Pair) sinfiga tegishli bo'lib, "
              "mammografiya uchun «Digital Mammography X-Ray Image» va hisobotlar uchun "
              "«Comprehensive SR» sinflari qo'llaniladi. Piksel ma'lumotlari turli "
              "uzatish sintaksislarida (transfer syntax) — siqilmagan yoki JPEG/JPEG2000 "
              "siqilgan — kodlanishi mumkin, shu sababli tahlil tizimi turli kodlashlarni "
              "dekodlashni qo'llab-quvvatlashi kerak. Tasvir intensivligi ko'pincha 12–16 "
              "bitli kulrang darajada ifodalanadi, bu yuqori dinamik diapazonni ta'minlaydi.")
    para(doc, "Klinik axborot oqimi DICOM va HL7 standartlari asosida tashkil etiladi. "
              "Radiologik axborot tizimi (RIS) tadqiqotlarni rejalashtiradi, PACS esa "
              "tasvirlarni saqlaydi va tarqatadi. Modallik ishchi ro'yxati (Modality "
              "Worklist) tasvirlash qurilmasiga bemor va tadqiqot ma'lumotlarini "
              "yetkazadi. Tahlil tizimining mavjud infratuzilmaga integratsiyalashuvi — "
              "C-FIND orqali tadqiqotlarni qidirish, C-MOVE orqali olib kelish va C-STORE "
              "orqali natijalarni qaytarish — amaliy joriy etish uchun hal qiluvchi "
              "ahamiyatga ega.")
    para(doc, "Maxfiylikni ta'minlash uchun de-identifikatsiya (anonimlashtirish) DICOM "
              "standartining 15-qismi (PS3.15) va tegishli profillarga muvofiq amalga "
              "oshiriladi. Bunda to'g'ridan-to'g'ri identifikatorlar (ism, ID, sanalar, "
              "muassasa) o'chiriladi yoki almashtiriladi, ammo tasvirning ilmiy qiymatini "
              "saqlovchi maydonlar (modallik, proyeksiya, piksel o'lchami) qoldiriladi. "
              "Sanalarda yil saqlanib, oy/kun umumlashtirilishi mumkin. Anonimlashtirishning "
              "to'liqligi va qaytarib bo'lmasligi qonuniy va axloqiy talab hisoblanadi.")

    h2(doc, "1.3-§. Tasvirlarga dastlabki ishlov berish va sifatini oshirish algoritmlari")
    para(doc, "Mammografiya tasvirlari ko'pincha past kontrast, shovqin va turli yorug'lik "
              "sharoitlari bilan tavsiflanadi. Shu sababli tahlildan oldin dastlabki ishlov "
              "berish bosqichi muhim ahamiyatga ega. Intensivlikni normallashtirish "
              "(z-ball yoki min-maks) tasvirlarni yagona shkalaga keltiradi:")
    eq(doc, "zscore", number="1.1")
    para(doc, "Kontrastni mahalliy moslash uchun adaptiv gistogramma tenglashtirish (CLAHE) "
              "usuli qo'llaniladi — u tasvirni bloklarga bo'lib, har blokda kontrastni "
              "cheklangan tarzda kuchaytiradi va shovqinni ortiqcha kuchaytirmaydi. "
              "Shovqinni kamaytirish uchun Gauss va median filtrlardan, ko'krak sohasini "
              "fondan ajratish uchun segmentatsiya usullaridan foydalaniladi. Ma'lumotlar "
              "kamligini bartaraf etish uchun augmentatsiya (aylantirish, akslantirish, "
              "masshtablash, yorqinlik o'zgartirish) va sintetik tasvir generatsiyasi "
              "(GAN, diffuziya modellari) qo'llaniladi.")

    para(doc, "Mammografiyaga xos dastlabki ishlov berish bosqichlaridan biri — ko'krak "
              "sohasini fondan ajratish (breast segmentation) va MLO proyeksiyasida ko'krak "
              "muskuli (pektoral muskul) sohasini olib tashlash (pectoral muscle removal). "
              "Pektoral muskul yuqori intensivlikka ega bo'lib, agar olib tashlanmasa, "
              "tahlil va statistik normallashtirishni buzishi mumkin. Bu vazifalar uchun "
              "ostona, mintaqaviy o'sish (region growing) va chuqur segmentatsiya "
              "usullaridan foydalaniladi.")
    para(doc, "Augmentatsiya usullari geometrik (aylantirish, akslantirish, masshtablash, "
              "kesish), fotometrik (yorqinlik, kontrast, gamma) va aralash (mosaic, mixup, "
              "cutout) turlariga bo'linadi. Tibbiy tasvirlarda augmentatsiya anatomik "
              "haqiqiylikni saqlashi kerak — masalan, mammografiyada kuchli deformatsiyalar "
              "yoki noto'g'ri akslantirish klinik ma'noni buzishi mumkin. Shu sababli "
              "augmentatsiya parametrlari ehtiyotkorlik bilan tanlanadi.")
    para(doc, "Ma'lumotlar kamligi va sinflar muvozanatsizligi (masalan, kam uchraydigan "
              "xavfli toifalar) muammosini hal qilishda generativ modellar muhim o'rin "
              "tutadi. Generativ raqobat tarmoqlari (GAN) va diffuziya modellari realistik "
              "sintetik mammografik tasvirlar yaratib, o'qitish to'plamini boyitadi. "
              "Bunda yaratilgan tasvirlarning klinik haqiqiyligi va belgilarning "
              "saqlanishi muhim — aks holda model noto'g'ri taqsimotni o'rganishi mumkin. "
              "Sintetik ma'lumotlardan foydalanish, ayniqsa noyob patologiyalar uchun, "
              "umumlashtirishni yaxshilashi ko'rsatilgan.")

    h2(doc, "1.4-§. Obyektlarni aniqlashning chuqur oʻrganishga asoslangan usullari")
    para(doc, "Konvolyutsion neyron tarmoq (CNN) — tasvir tahlilining asosiy quroli. Uning "
              "asosiy amali — konvolyutsiya bo'lib, o'rganiluvchi yadrolar yordamida "
              "mahalliy fazoviy belgilarni ajratib oladi:")
    eq(doc, "conv", number="1.2")
    para(doc, "Nochiziqlilik aktivatsiya funksiyalari (ReLU, sigmoid) orqali kiritiladi:")
    eq(doc, "relu", number="1.3")
    para(doc, "Ko'p sinfli tasniflash chiqishida softmax funksiyasi ehtimollik taqsimotini "
              "beradi:")
    eq(doc, "softmax", number="1.4")
    para(doc, "Obyektlarni aniqlash (detection) ikki asosiy yo'nalishga bo'linadi. "
              "**Ikki bosqichli** detektorlar (Faster R-CNN) avval nomzod sohalarni "
              "(region proposals) generatsiya qilib, so'ng ularni tasniflaydi — yuqori "
              "aniqlik, lekin sekinroq. **Bir bosqichli** detektorlar (YOLO, SSD, "
              "RetinaNet) qutilar va sinflarni bir o'tishda bashorat qiladi — yuqori "
              "tezlik. YOLO oilasi (v8/v11) zamonaviy mammografiya tizimlarida keng "
              "qo'llaniladi. Detektsiya yo'qotishi odatda quti regressiyasi (CIoU), sinf "
              "va taqsimot fokal yo'qotishi (DFL) komponentlaridan iborat:")
    eq(doc, "ciou", number="1.5")
    eq(doc, "dfl", number="1.6")
    para(doc, "Sinflar muvozanatsizligini bartaraf etish uchun fokal yo'qotish (Focal "
              "Loss) qo'llaniladi — u oson misollarning hissasini kamaytiradi:")
    eq(doc, "focal", number="1.7")

    para(doc, "Obyekt detektorlarining evolyutsiyasini batafsil ko'rib chiqamiz. R-CNN "
              "oilasi (R-CNN, Fast R-CNN, Faster R-CNN) mintaqa takliflari (region "
              "proposals) g'oyasini rivojlantirdi: Faster R-CNN takliflarni generatsiya "
              "qiluvchi mintaqa taklif tarmog'ini (RPN) kiritib, ikki bosqichli yondashuvni "
              "to'liq o'rgatiladigan qildi. Bu oila yuqori aniqlik bilan ajralib turadi, "
              "biroq hisoblash narxi yuqori. YOLO oilasi esa (v1 dan v11 gacha) aniqlashni "
              "yagona regressiya masalasi sifatida shakllantirib, real vaqtdagi tezlikni "
              "ta'minladi. Keyingi versiyalar anchor-free yondashuv, CSP (Cross-Stage "
              "Partial) bazaviy tarmoqlar, PAN (Path Aggregation Network) bo'yin va "
              "taqsimotga asoslangan quti regressiyasi kabi yangiliklarni kiritdi.")
    para(doc, "Bazaviy tarmoq (backbone) tasvir xususiyatlarini ajratishda hal qiluvchi "
              "rol o'ynaydi. VGG, ResNet (qoldiq bog'lanishlar bilan), DenseNet va "
              "EfficientNet (murakkablik va aniqlik muvozanati uchun masshtablash bilan) "
              "kabi arxitekturalar keng qo'llaniladi. Ko'p miqyosli xususiyatlarni "
              "birlashtirish uchun xususiyat piramidasi tarmog'i (FPN) va uning variantlari "
              "ishlatiladi — bu turli o'lchamdagi obyektlarni (mammografiyada mayda "
              "mikrokalsifikatsiyadan yirik massagacha) aniqlashda muhim.")
    para(doc, "Anchor-asosli detektorlar oldindan belgilangan quti shakllariga (anchors) "
              "tayanadi, anchor-free detektorlar (FCOS, CenterNet) esa har bir piksel "
              "uchun to'g'ridan-to'g'ri quti chegaralarini bashorat qiladi — bu giperparametr "
              "sozlashni soddalashtiradi. So'nggi paytlarda transformer asosidagi detektorlar "
              "(DETR va uning variantlari) e'tibor mexanizmidan foydalanib, qo'lda tuzilgan "
              "komponentlarni (anchors, NMS) kamaytirishga harakat qilmoqda. Ushbu "
              "tadqiqotda YOLO oilasi tezligi, aniqligi va kengaytirilishi qulayligi tufayli "
              "bazaviy arxitektura sifatida tanlangan; taklif etilgan BCA, IVC va ordinal "
              "modullari uning bazaviy tarmog'i va boshiga modulli tarzda o'rnatiladi.")

    h2(doc, "1.5-§. Oʻzaro eʼtibor mexanizmlari, ordinal regressiya va radiomika")
    para(doc, "**O'zaro e'tibor (cross-attention)** mexanizmi Transformer arxitekturasidan "
              "kelib chiqqan bo'lib, ikki xususiyat oqimini bog'lashning samarali vositasidir. "
              "Miqyoslangan skalyar ko'paytma e'tibori quyidagicha hisoblanadi:")
    eq(doc, "attn", number="1.8")
    para(doc, "Ko'p boshli e'tibor (multi-head attention) bir nechta ifoda osti fazosida "
              "parallel e'tiborni hisoblaydi:")
    eq(doc, "mha", number="1.9")
    para(doc, "Tibbiy tasvirlashda o'zaro e'tibor uzoq muddatli kuzatuvda oldingi va joriy "
              "tadqiqotlarni bog'lash, MRT modalliklarini birlashtirish kabi vazifalarda "
              "qo'llanilgan. Mammografiyada esa ikki tomonlama asimmetriyani modellashda "
              "uning salohiyati to'liq ochilmagan.")
    para(doc, "E'tibor mexanizmlari kompyuter ko'rishida bir necha shaklda namoyon bo'ladi. "
              "**Kanalli e'tibor** — Squeeze-and-Excitation (SE) tarmoqlari xususiyat "
              "kanallarining nisbiy ahamiyatini global kontekst asosida qayta tortadi. "
              "**Fazoviy va kanalli e'tibor** — CBAM (Convolutional Block Attention Module) "
              "ketma-ket kanalli va fazoviy e'tiborni birlashtirib, \"qaysi kanal\" va "
              "\"qaysi soha\" muhimligini aniqlaydi. Bu modullar konvolyutsion tarmoqlarga "
              "kam hisoblash narxida qo'shilib, aniqlikni oshiradi. Mammografiyada ular "
              "shikastlanishga oid xususiyatlarni kuchaytirish uchun foydali, biroq ular bir "
              "tasvir ichidagi e'tiborni qayta taqsimlaydi — ikki ko'rinish yoki ikki ko'krak "
              "o'rtasidagi munosabatni modellamaydi.")
    para(doc, "**O'z-o'ziga e'tibor (self-attention)** bir oqim ichidagi pozitsiyalar "
              "o'rtasidagi bog'liqlikni, **o'zaro e'tibor (cross-attention)** esa ikki "
              "alohida oqim o'rtasidagi bog'liqlikni modellaydi. Aynan o'zaro e'tibor "
              "kontralateral (chap↔o'ng) yoki proyeksiyalararo (CC↔MLO) munosabatlarni "
              "ifodalash uchun tabiiy vositadir — bu ushbu dissertatsiyada taklif etilgan "
              "BCA blokining nazariy asosini tashkil etadi. Shartlashtirishning yana bir "
              "shakli — **FiLM (Feature-wise Linear Modulation)** — yordamchi signal (masalan "
              "matn) asosida xususiyatlarni kanal bo'yicha masshtablash va siljitish orqali "
              "modulyatsiya qiladi; bu mexanizm matn-asosli detektsiyada (TILLNet) "
              "qo'llaniladi. Vizual transformerlar (ViT) va DETR kabi detektorlar e'tiborni "
              "arxitekturaning markaziy elementiga aylantirdi, biroq ular katta o'qitish "
              "to'plami va hisoblash resursini talab qiladi — bu tibbiy sohada, ma'lumot "
              "cheklangan sharoitda, muhim cheklov.")
    para(doc, "**Ordinal regressiya** — sinflar tabiiy tartibga ega bo'lgan masalalar uchun "
              "mo'ljallangan. BI-RADS shkalasi aynan shunday: kategoriyalar orasidagi "
              "masofa teng emas. Ordinal masalalarni kumulyativ bog'lanish (cumulative "
              "link) modellari orqali yechish mumkin — bu nominal kross-entropiyaga "
              "nisbatan tartib ma'lumotini saqlaydi.")
    para(doc, "**Radiomika** — tibbiy tasvirdan ko'p sonli miqdoriy belgilarni (shakl, "
              "birinchi tartib intensivlik statistikasi, tekstura) avtomatik chiqarib "
              "tahlil qilish yo'nalishi. Tekstura belgilari kulrang darajalar birgalikdagi "
              "paydo bo'lish matritsasidan (Gray-Level Co-occurrence Matrix, GLCM) olinadi:")
    eq(doc, "glcm", number="1.10")
    eq(doc, "homog", number="1.11")
    para(doc, "Radiomik belgilar chuqur o'rganish modellariga patologik asoslangan "
              "izohlanuvchanlik qo'shadi va klinik ishonchni oshiradi.")
    para(doc, "Radiomik belgilar bir necha kategoriyaga bo'linadi: (i) shakl belgilari "
              "(maydon, perimetr, dumaloqlik, kompaktlik) — o'choq morfologiyasini "
              "tavsiflaydi; (ii) birinchi tartib statistikalar (o'rtacha, dispersiya, "
              "assimetriya, ekssess, entropiya) — intensivlik taqsimotini ifodalaydi; "
              "(iii) ikkinchi va yuqori tartib tekstura belgilari — GLCM (birgalikdagi "
              "paydo bo'lish), GLRLM (kulrang daraja yugurish uzunligi), GLSZM (o'lcham "
              "zonasi), GLDM (qaramlik) va NGTDM matritsalaridan olinadi; (iv) to'lqincha "
              "(wavelet) va Laplas-Gauss filtrlangan belgilar — turli chastotalardagi "
              "ma'lumotni qamrab oladi. Spikulali chegara va heterogen tekstura kabi "
              "xavflilik belgilari aynan shu kategoriyalarda aks etadi.")
    para(doc, "Radiomik belgilar soni ko'p (yuzlab) bo'lgani sababli, ortiqcha "
              "moslashishning oldini olish uchun belgi tanlash (feature selection) va "
              "o'lchamlilikni kamaytirish qo'llaniladi. Turli qurilma va protokollar "
              "o'rtasidagi farqni bartaraf etish uchun belgi garmonizatsiyasi (masalan, "
              "ComBat usuli) muhim. Radiomik belgilarning takrorlanuvchanligi va "
              "barqarorligi ularning klinik qo'llanilishi uchun asosiy shartdir.")
    para(doc, "So'nggi yillarda transformer arxitekturalari tibbiy tasvirlashga ham kirib "
              "keldi. Vision Transformer (ViT) tasvirni yamoqlarga bo'lib, ularni "
              "ketma-ketlik sifatida qayta ishlaydi; Swin Transformer esa ierarxik va "
              "oyna asosidagi e'tibor bilan hisoblash murakkabligini kamaytiradi. "
              "Gibrid CNN-transformer modellari (masalan, segmentatsiyada TransUNet) "
              "konvolyutsiyaning mahalliy induktiv tarafkashligini va e'tiborning global "
              "kontekstini birlashtiradi. Mammografiyada transformerlar uzoq masofali "
              "bog'liqliklarni — masalan, ikki ko'krak o'rtasidagi asimmetriyani — "
              "modellashda istiqbolli, ammo ko'p ma'lumot va hisoblash resursini talab "
              "qiladi.")
    para(doc, "Klinik qo'llanish uchun modelning noaniqligini (uncertainty) baholash "
              "muhim. Epistemik (model bilimining yetishmasligi) va aleatorik (ma'lumotdagi "
              "shovqin) noaniqliklar farqlanadi. Monte-Carlo dropout, ansambllar va test "
              "vaqti augmentatsiyasi (TTA) noaniqlikni amaliy baholash usullaridir. MAMOGRAF "
              "tizimida TTA asosidagi noaniqlik issiqlik xaritasi radiologga modelning "
              "qaysi sohalarda \"ishonchsiz\" ekanini ko'rsatadi, bu inson-mashina "
              "hamkorligini yaxshilaydi.")
    para(doc, "Ma'lumotlar maxfiyligini saqlash bilan birga umumiy modellar o'rgatish "
              "uchun federativ o'rganish (federated learning) va o'z-o'zini nazorat qiluvchi "
              "(self-supervised) o'rganish kabi yo'nalishlar rivojlanmoqda. Federativ "
              "o'rganishda model bemor ma'lumotlari markazlashtirilmasdan, har bir "
              "muassasada mahalliy o'rgatiladi. Bu yo'nalishlar kelajakda mahalliy "
              "tizimlarni ko'p markazli bilim bilan boyitishi mumkin.")
    para(doc, "Ordinal regressiya usullari ham rivojlangan. Klassik kumulyativ bog'lanish "
              "(proportional odds) modellaridan tashqari, chuqur o'rganishda CORAL va CORN "
              "kabi rank-mos (rank-consistent) usullar taklif etilgan — ular ostonalarning "
              "monotonligini kafolatlaydi. Ushbu dissertatsiyada qo'llanilgan softplus "
              "orqali parametrlangan monoton ostonalarga ega kumulyativ model shu "
              "yo'nalishga mansub bo'lib, qo'shimcha jarimasiz monotonlikni ta'minlaydi.")

    h2(doc, "1.6-§. Maʼlumotlar toʻplamlari, baholash metrikalari va tadqiqot masalasining qoʻyilishi")
    para(doc, "Mammografiya AI tadqiqotlarida commonly used ochiq ma'lumotlar to'plamlari "
              "qatoriga CBIS-DDSM, INbreast va VinDr-Mammo kiradi. VinDr-Mammo — to'liq "
              "maydonli raqamli mammografiyaning yirik (taxminan 20 000 tasvir) "
              "ko'p markazli to'plami bo'lib, BI-RADS belgilari va shikastlanish "
              "annotatsiyalari bilan ta'minlangan.")
    para(doc, "Mammografiya AI tadqiqotlarida foydalaniladigan asosiy ochiq ma'lumotlar "
              "to'plamlari 1.2-jadvalda qiyoslangan. Ular hajmi, annotatsiya turi va "
              "kelib chiqishi bo'yicha farqlanadi; VinDr-Mammo zamonaviy, yirik va BI-RADS "
              "belgilari bilan ta'minlangani uchun ushbu tadqiqotda asosiy baholash "
              "to'plami sifatida tanlangan.")
    table(doc, ["To'plam", "Hajmi (taxminan)", "Annotatsiya", "Izoh"], [
        ["DDSM", "~2 600 holat", "Massa/kalsifikatsiya", "Plyonkali (skanerlangan), klassik"],
        ["CBIS-DDSM", "~3 500 holat", "Segmentatsiya + BI-RADS", "DDSM ning tozalangan, kuratorli versiyasi"],
        ["INbreast", "~410 tasvir", "Aniq konturlar", "To'liq maydonli raqamli (FFDM)"],
        ["VinDr-Mammo", "~20 000 tasvir", "Quti + BI-RADS", "Yirik, ko'p markazli, zamonaviy FFDM"],
    ], caption="1.2-jadval. Mammografiya bo'yicha asosiy ochiq ma'lumotlar to'plamlari")
    para(doc, "Aniqlash sifatini baholash uchun aniqlangan va haqiqiy quti o'rtasidagi "
              "kesishish-birlashish nisbati (IoU), precision, recall, F1 va o'rtacha "
              "aniqlik (mAP) metrikalaridan foydalaniladi (4-bobda batafsil keltiriladi). "
              "Mammografiyada Free-response ROC (FROC) tahlili keng qo'llaniladi — u har "
              "bir tasvirga to'g'ri keluvchi o'rtacha soxta-musbatlar soniga (FPpI) "
              "nisbatan sezgirlikni baholaydi va detektsiya masalasiga aniq tasniflashga "
              "qaraganda mosroqdir. Umumiy ko'rsatkich sifatida belgilangan FPpI "
              "darajalaridagi o'rtacha sezgirlik (CPM, Competition Performance Metric) "
              "ishlatiladi. Tasniflash uchun ROC egri chizig'i va uning ostidagi yuza "
              "(AUC), ordinal baholash uchun esa kvadratik og'irlikli Koen kappasi "
              "qo'llaniladi.")
    para(doc, "**Tadqiqot masalasining qo'yilishi.** Yuqoridagi tahlil quyidagi ilmiy "
              "masalani shakllantiradi: mammografiyaning to'rtta ko'rinishini birgalikda, "
              "ikki tomonlama asimmetriya va ko'rinishlararo muvofiqlikni hisobga olgan "
              "holda qayta ishlovchi; BI-RADS ni ordinal shkalada baholovchi; radiomik "
              "izohlanuvchanlikni ta'minlovchi; va topilmalardan avtomatik klinik xulosa "
              "shakllantiruvchi yagona algoritm va dasturiy majmuani ishlab chiqish.")
    h2(doc, "1.7-§. Mammografiyada chuqur oʻrganishning tizimli sharhi")
    para(doc, "Mammografik tasvirlarni avtomatik tahlil qilish yo'nalishi an'anaviy "
              "kompyuterli aniqlash (CAD) tizimlaridan zamonaviy chuqur o'rganishga o'tish "
              "bilan tubdan o'zgardi. An'anaviy CAD tizimlari qo'lda tuzilgan belgilar "
              "(gistogramma, chegaralar, simmetriya o'lchovlari) va klassik tasniflagichlarga "
              "(SVM, qaror daraxtlari) asoslangan edi. Ular soxta-musbatlar yuqoriligi va "
              "umumlashtirishning cheklanganligi tufayli klinik samaradorligi chegaralangan "
              "bo'lib qoldi. Chuqur o'rganishning paydo bo'lishi belgilarni avtomatik "
              "o'rgatish imkonini berib, aniqlikni sezilarli oshirdi.")
    para(doc, "Kooi va hammualliflari (2017) keng ko'lamli CNN'larni mammografik "
              "shikastlanishlarni aniqlashga qo'llab, klassik CAD tizimlaridan ustunlikni "
              "ko'rsatdilar. Ribli va boshqalar (2018) Faster R-CNN asosida shikastlanishlarni "
              "aniqlash va tasniflash usulini taklif etib, INbreast to'plamida yuqori "
              "natijalarga erishdilar. Shen va hammualliflari (2019) butun tasvir va "
              "yamoq darajasidagi modellarni birlashtirib, skrining mammografiyasida "
              "tashxis aniqligini oshirdilar.")
    para(doc, "Yirik klinik tadqiqotlar AI ning amaliy salohiyatini tasdiqladi. Wu va "
              "hammualliflari (2020) o'n minglab tadqiqotlarda o'rgatilgan chuqur tarmoqlar "
              "radiologlarning ish samaradorligini oshirishini ko'rsatdilar. McKinney va "
              "boshqalar (2020) Nature jurnalida AI tizimining ko'krak saratoni skriningida "
              "soxta-musbat va soxta-manfiylarni kamaytirishini xalqaro miqyosda baholadilar. "
              "Yala va hammualliflari (2019) mammografiya asosida saraton xavfini bashorat "
              "qiluvchi modelni taklif etdilar.")
    para(doc, "YOLO oilasi mammografiyada ham keng qo'llanildi. Al-Masni va hammualliflari "
              "(2018) YOLO asosida ko'krak massalarini bir vaqtning o'zida aniqlash va "
              "tasniflashni amalga oshirdilar. Aly va boshqalar (2021) YOLO konfiguratsiyalarini "
              "mammografik massalar uchun moslashtirib, real vaqtda yuqori aniqlikka "
              "erishdilar. Bu ishlar bir bosqichli detektorlarning tezligi va aniqligi "
              "muvozanatini namoyish etdi.")
    para(doc, "Ko'pko'rinishli (multi-view) yondashuvlar radiologlarning amaliyotiga yaqinroq. "
              "Yang va hammualliflari (2020) MommiNet arxitekturasida ko'p ko'rinish va "
              "ko'p miqyosli ma'lumotni birlashtirdilar. Liu va boshqalar (2021) ko'rinishlararo "
              "moslikni (cross-view correspondence) modellashga harakat qildilar. Petrini va "
              "hammualliflari (2022) ikki ko'rinishli (CC va MLO) tahlilni EfficientNet "
              "asosida amalga oshirdilar. Biroq bu ishlarning aksariyati ikki tomonlama "
              "(kontralateral) asimmetriyani va ordinal BI-RADS baholashni yagona, "
              "uchidan-uchiga o'rgatiladigan mexanizmda birlashtirmagan — bu bo'shliq ushbu "
              "tadqiqotda bartaraf etiladi.")
    para(doc, "Segmentatsiya yo'nalishida U-Net va uning variantlari (Connected-UNets) keng "
              "qo'llaniladi. Izohlanuvchanlik (explainability) uchun Grad-CAM, LIME va SHAP "
              "kabi usullar modellarning qarorini vizuallashtirishga xizmat qiladi; radiomik "
              "belgilar esa patologik asoslangan, oldindan belgilangan izohni ta'minlaydi. "
              "Litjens va hammualliflarining (2017) hamda van der Velden va boshqalarning "
              "(2022) sharhlari tibbiy tasvirlashda chuqur o'rganish va izohlanuvchanlikning "
              "umumiy holatini tizimlashtiradi.")
    para(doc, "Ma'lumotlar kamligi muammosini hal qilishda generativ modellar (GAN, "
              "diffuziya modellari) sintetik mammografik tasvirlar yaratish uchun "
              "qo'llanilmoqda. Bu real ma'lumotlarni boyitib, modellarning umumlashtirishini "
              "yaxshilaydi. Shuningdek, o'qitishning barqarorligi uchun batch normalizatsiya, "
              "dropout va zamonaviy optimizatorlar (Adam, AdamW) muhim ahamiyatga ega.")
    para(doc, "Tasniflash va baholash yo'nalishida ham muhim ishlar mavjud. Yala va "
              "hammualliflari mammografiyadan kelajakdagi saraton xavfini bashorat qiluvchi "
              "modellarni taklif etdilar — bu skriningni shaxsiylashtirish imkonini beradi. "
              "Geras va boshqalar mammografiya va tomosintez uchun chuqur o'rganishning "
              "umumiy holatini sharhladilar. BI-RADS ni avtomatik baholash bo'yicha ishlar "
              "ko'pincha uni nominal tasniflash sifatida qaradi va shkalaning ordinal "
              "tabiatini e'tiborsiz qoldirdi — bu aniqlikni va klinik mosligini cheklaydi.")
    para(doc, "Radiomik va gibrid yondashuvlar izohlanuvchanlikni oshirishga qaratilgan. "
              "Radiomik belgilarni chuqur tasvirlovchilar bilan birlashtirish modelning "
              "qarorini patologik asoslangan o'lchovlar bilan bog'laydi. Muallifning "
              "Radiomic-Enhanced Faster R-CNN ishi aynan shu yondashuvni qo'llab, "
              "VinDr-Mammo to'plamida yuqori aniqlik va izohlanuvchan issiqlik xaritalariga "
              "erishdi. Bu natija gibrid yondashuvning amaliy salohiyatini tasdiqlaydi.")
    para(doc, "Klinik amaliyotga integratsiya yo'nalishida tadqiqotlar nisbatan kam. "
              "Ko'pchilik ishlar aniqlash yoki tasniflash aniqligiga e'tibor qaratadi, "
              "biroq annotatsiya, model o'qitish, avtomatik xulosa va PACS integratsiyasini "
              "qamrab oluvchi yaxlit klinik tizimni kamdan-kam taqdim etadi. Bundan tashqari, "
              "katta til modellarining (LLM) tibbiy hisobot generatsiyasidagi salohiyati "
              "yangi yo'nalish bo'lib, uning klinik xavfsizligi (ma'lumot to'qish xavfi) "
              "jiddiy e'tibor talab qiladi. MAMOGRAF tizimi grounded (faqat aniqlangan "
              "topilmaga asoslangan) lokal generatsiya orqali bu xavfni yumshatadi.")
    para(doc, "Mavjud ishlarning qiyosiy tahlili shuni ko'rsatadiki, mammografiya AI "
              "tizimlari ikki asosiy yo'nalishda takomillashtirilishi mumkin: (i) klinik "
              "induktiv taxminlarni (ikki tomonlama asimmetriya, ko'rinishlararo muvofiqlik, "
              "ordinal baholash) model arxitekturasiga to'g'ridan-to'g'ri kiritish; (ii) "
              "aniqlash va tasniflashdan tashqari, butun klinik ish oqimini — annotatsiyadan "
              "avtomatik xulosaga va PACS integratsiyasigacha — qamrab oluvchi yaxlit "
              "dasturiy majmua yaratish. Ushbu dissertatsiya aynan shu ikki yo'nalishni "
              "birlashtiradi.")

    h2(doc, "1.8-§. Koʻpkoʻrinishli va ikki tomonlama yondashuvlarning qiyosiy tahlili")
    para(doc, "Mammografik detektsiya bo'yicha yondashuvlarni radiolog amaliyotidagi to'rt "
              "asosiy klinik tamoyilni — ko'rinishlarni birgalikda qayta ishlash, ikki "
              "tomonlama (kontralateral) asimmetriya, ko'rinishlararo (CC↔MLO) muvofiqlik "
              "va BI-RADS ning ordinal baholanishi — qay darajada qamrab olishiga ko'ra "
              "tizimli qiyoslash mumkin (1.3-jadval). Bu qiyoslash mavjud ishlarning kuchli "
              "tomonlari va bo'shliqlarini aniq ko'rsatadi.")
    table(doc, ["Yondashuv", "Ko'rinishlar", "Ikki tomonlama asimmetriya",
                "Ko'rinishlararo muvofiqlik", "Ordinal BI-RADS", "Uchidan-uchiga"], [
        ["Bir ko'rinishli YOLO / Faster R-CNN (Al-Masni, Aly, Ribli)", "Mustaqil", "Yo'q", "Yo'q", "Yo'q (nominal)", "Ha"],
        ["Ikki ko'rinishli (Petrini, EfficientNet)", "CC+MLO juft", "Yo'q", "Qisman (kech birlashtirish)", "Yo'q", "Ha"],
        ["Ko'p ko'rinishli (MommiNet, Yang)", "Ko'p ko'rinish", "Qisman", "Qisman", "Yo'q", "Ha"],
        ["Ko'rinishlararo moslik (Liu)", "CC+MLO", "Yo'q", "Ha (moslik)", "Yo'q", "Ha"],
        ["BCA-YOLO (ushbu ish)", "To'rt ko'rinish birga", "Ha (BCA, α-darvoza)", "Ha (IVC moduli)", "Ha (monoton ostona)", "Ha"],
    ], caption="1.3-jadval. Mammografik detektsiya yondashuvlarining klinik induktiv taxminlar bo'yicha qiyosiy tahlili")
    para(doc, "Jadvaldan ko'rinadiki, mavjud ishlarning aksariyati ko'rinishlarni mustaqil "
              "yoki kech (qaror darajasida) birlashtiradi va kontralateral asimmetriyani "
              "model ichida aniq modellamaydi. Ikki ko'rinishli yondashuvlar (Petrini va b.) "
              "bir ko'krakning CC va MLO proyeksiyalarini birlashtiradi, biroq chap va o'ng "
              "ko'krak o'rtasidagi qiyoslashni — radiolog tahlilining markaziy elementini — "
              "qoldiradi. Ko'p ko'rinishli arxitekturalar (MommiNet) ma'lumotni "
              "birlashtiradi, lekin asimmetriyani o'rganiluvchi, izohlanuvchi mexanizm "
              "sifatida ifodalamaydi. Liu va hammualliflarining ko'rinishlararo moslik ishi "
              "CC↔MLO muvofiqligini modellaydi, ammo ikki tomonlama asimmetriya va ordinal "
              "baholashni qamrab olmaydi.")
    para(doc, "Bundan tashqari, ko'rib chiqilgan ishlarning deyarli barchasi BI-RADS ni "
              "**nominal** sinflar sifatida talqin qiladi va shkalaning ordinal tabiatini "
              "(kategoriyalar tartibli, ular orasidagi xato narxi turlicha) e'tiborsiz "
              "qoldiradi. Yana bir muhim bo'shliq — aniqlash/tasniflashdan tashqari, "
              "annotatsiya, model o'qitish, avtomatik xulosa va PACS integratsiyasini "
              "qamrab oluvchi **yaxlit klinik dasturiy majmua** kamdan-kam taqdim etiladi. "
              "Aynan shu bo'shliqlar — kontralateral asimmetriya, ko'rinishlararo muvofiqlik "
              "va ordinal baholashni yagona uchidan-uchiga o'rgatiladigan tarmoqda "
              "birlashtirish hamda uni to'liq klinik tizimga joylashtirish — ushbu "
              "dissertatsiya tadqiqotining ilmiy yangiligi va amaliy hissasini belgilaydi.")

    concl(doc, "I", [
        "Ko'krak saratonini erta aniqlashda skrining mammografiyasi va to'rt ko'rinishli (CC/MLO) tahlil hal qiluvchi ahamiyatga ega; BI-RADS shkalasi ordinal tabiatga ega.",
        "DICOM standarti va PACS tibbiy tasvirlarni saqlash va almashishni belgilaydi; PHI anonimlashtirish maxfiylik talabidir.",
        "Mavjud chuqur o'rganish detektorlari to'rt ko'rinishni mustaqil qayta ishlab, ikki tomonlama va ko'rinishlararo induktiv taxminlardan to'liq foydalanmaydi.",
        "O'zaro e'tibor, ordinal regressiya va radiomika alohida-alohida o'rganilgan, biroq yagona mammografiya yechimida birlashtirilmagan.",
        "Aniqlangan ilmiy bo'shliq BCA-YOLO algoritmi va MAMOGRAF dasturiy majmuasini ishlab chiqishni asoslab beradi.",
    ])
    pb(doc)


# --------------------------------------------------------------------------- #
# II BOB                                                                      #
# --------------------------------------------------------------------------- #
@section
def bob2(doc):
    h1(doc, "II bob. Koʻkrak oʻsmalarini aniqlash va tasniflash algoritmlari")

    h2(doc, "2.1-§. Belgilashlar va masalaning matematik qoʻyilishi")
    para(doc, "Bitta mammografik tadqiqot to'rtta ko'rinishdan iborat: "
              "$\\{L\\text{-}CC, R\\text{-}CC, L\\text{-}MLO, R\\text{-}MLO\\}$. Har bir "
              "ko'rinish $v$ uchun bazaviy tarmoq $S$ ta miqyosda xususiyat xaritalari "
              "$F_v^{(s)} \\in \\mathbb{R}^{C_s \\times H_s \\times W_s}$ ($s=1,\\dots,S$) "
              "hosil qiladi. Detektsiya boshi har bir to'r pozitsiyasi uchun quti "
              "koordinatalari, obyektlik logiti $o_v^{(s)}$ va BI-RADS chiqishini bashorat "
              "qiladi. Maqsad — bu to'rt oqimni klinik induktiv taxminlar (ikki tomonlama "
              "asimmetriya, ko'rinishlararo muvofiqlik, ordinal baholash) bilan boyitib, "
              "yagona, uchidan-uchiga o'rgatiladigan model qurishdir. Taklif etilayotgan "
              "**BCA-YOLO** arxitekturasi YOLO oilasi bazaviy tarmog'i va bo'yniga uchta "
              "yangi komponent qo'shadi (2.1-rasm).")
    img(doc, "arch_bca_yolo.png", width=5.8, caption="2.1-rasm. BCA-YOLO arxitekturasi: BCA bloki, IVC moduli va ordinal BI-RADS boshi")

    para(doc, "Bazaviy tarmoq uch miqyosli xususiyat xaritalarini hosil qiladi: yuqori "
              "ruxsatdagi (katta $H_s \\times W_s$, kichik $C_s$) xaritalar mayda "
              "obyektlarni (mikrokalsifikatsiyalar), past ruxsatdagi (kichik fazoviy, "
              "katta $C_s$) xaritalar esa yirik obyektlarni (massalar) aniqlash uchun "
              "javobgar. Kanal kengliklari odatda $(C_1,C_2,C_3)=(256,512,512)$ qiymatlarni "
              "oladi. Xususiyat piramidasi (FPN/PAN) turli miqyoslardagi ma'lumotni "
              "yuqoridan-pastga va pastdan-yuqoriga yo'llar orqali birlashtiradi, bu "
              "ko'p o'lchamli aniqlashni ta'minlaydi.")
    para(doc, "To'rtta ko'rinish bazaviy tarmoqdan parametrlarni bo'lishgan holda "
              "(weight sharing) o'tkaziladi — bu parametrlar sonini kamaytiradi va barcha "
              "ko'rinishlar uchun izchil tasvirlovchilarni o'rgatadi. Taklif etilgan uchta "
              "modul shu umumiy tasvirlovchilar ustida ishlaydi: BCA bloki tomonlar "
              "(L↔R) o'rtasida, IVC moduli proyeksiyalar (CC↔MLO) o'rtasida muvofiqlikni "
              "kiritadi, ordinal bosh esa har bir aniqlangan o'choq uchun BI-RADS bahosini "
              "beradi. Bu uch modulning ortogonalligi (turli o'qlar bo'yicha induktiv "
              "taxminlar) ularning hissalarini ablatsion tahlilda alohida baholash "
              "imkonini beradi.")

    h2(doc, "2.2-§. Ikki tomonlama oʻzaro eʼtibor (BCA) bloki")
    para(doc, "Radiolog chap va o'ng ko'krakni solishtirib asimmetriyani aniqlaydi. Buni "
              "modellashtirish uchun har bir miqyos $s$ da chap ko'rinish xususiyati $F_L$ "
              "va **ufqiy akslangan** o'ng ko'rinish xususiyati $F_R$ o'rtasida o'zaro "
              "e'tibor hisoblanadi (akslantirish ikki ko'krak anatomiyasini fazoviy "
              "tenglashtiradi). So'rov $Q$ chap oqimdan, kalit $K$ va qiymat $V$ o'ng "
              "oqimdan chiziqli proyeksiyalar orqali olinadi:")
    eq(doc, "bca_attn", number="2.1")
    para(doc, "Olingan kontralateral farq signali $\\Delta F_L$ o'rganiluvchi skalyar "
              "$\\alpha$ koeffitsiyenti bilan qoldiq (residual) tarzda asosiy xususiyatga "
              "qo'shiladi:")
    eq(doc, "bca_res", number="2.2")
    para(doc, "Bu yerda muhim tuzilma qarori — $\\alpha$ ni **nolga initsializatsiya** "
              "qilishdir. O'rganish boshida $\\alpha=0$ bo'lgani uchun oldinga o'tish aynan "
              "bazaviy YOLO modeliga teng bo'ladi, bu esa oldindan o'rgatilgan og'irliklar "
              "bilan to'liq moslikni ta'minlaydi va barqaror sozlashga (fine-tuning) imkon "
              "beradi. Asimmetriya xaritasi $\\bar{A}^{(s)}$ — e'tibor og'irliklarining "
              "fazoviy yig'indisi — shikastlanish joylarida cho'qqiga ko'tarilishga "
              "o'rgatiladi, bu modelni asimmetriya muhim bo'lgan joylarga yo'naltiradi:")
    eq(doc, "asym", number="2.3")
    para(doc, "bu yerda $\\Omega = \\{(s,L),(s,R): s=1,\\dots,S\\}$ — barcha miqyos va "
              "tomonlar to'plami, $m^{(s)}_v$ esa asosiy haqiqat (ground-truth) "
              "shikastlanish niqobidan olingan maqsadli xarita.")

    para(doc, "BCA blokining hisoblash tuzilmasini batafsil ko'rib chiqamiz. Har bir "
              "miqyos $s$ da xususiyat xaritalari $1 \\times 1$ konvolyutsiyalar orqali "
              "so'rov, kalit va qiymat fazolariga proyeksiyalanadi. O'zaro e'tibor "
              "kontralateral juftlik bo'yicha hisoblanadi: chap ko'rinishning har bir "
              "fazoviy pozitsiyasi o'ng (akslangan) ko'rinishning barcha pozitsiyalariga "
              "e'tibor beradi va eng o'xshash kontralateral sohani topadi. Bu mexanizm "
              "radiolog chap va o'ng ko'krakni vizual qiyoslab, mos kelmaydigan (asimmetrik) "
              "sohalarni qidirishini bevosita modellashtiradi.")
    para(doc, "O'ng ko'rinishni ufqiy akslantirish — anatomik tenglashtirish uchun zarur, "
              "chunki chap va o'ng ko'krak oyna-simmetrik joylashgan. Akslantirishsiz "
              "o'zaro e'tibor noto'g'ri anatomik mos kelishlarni hisoblar edi. E'tibor "
              "barcha bazaviy miqyoslarda (odatda $S=3$) mustaqil ravishda qo'llaniladi, "
              "bu turli o'lchamdagi asimmetriyalarni — mayda mikrokalsifikatsiya guruhidan "
              "yirik massagacha — qamrab oladi. Hisoblash murakkabligini cheklash uchun "
              "e'tibor past miqyoslarda (kichik fazoviy o'lcham) samaraliroq bo'ladi.")
    para(doc, "$\\alpha$ koeffitsiyentining nolga initsializatsiyasi muhim nazariy "
              "xususiyatga ega. (2.2) ifodadan ko'rinadiki, $\\alpha=0$ da $F'_L = F_L$, "
              "ya'ni oldinga o'tish bazaviy modelga aynan teng. Biroq (2.9) gradiyenti "
              "$\\alpha=0$ da ham nol emas, chunki u $\\Delta F$ ga proporsional. Demak, "
              "model oldindan o'rgatilgan og'irliklardan boshlab, BCA modulini asta-sekin "
              "\"yoqadi\" — bu beqaror sakrashlarsiz silliq sozlashni ta'minlaydi. Bu xossa "
              "ResNet'dagi qoldiq bog'lanishlar va ba'zi e'tibor modullaridagi nolga "
              "initsializatsiya g'oyalariga mos keladi.")

    h2(doc, "2.3-§. Koʻrinishlararo muvofiqlik (IVC) moduli")
    para(doc, "Bir xil shikastlanish bir ko'krakning CC va MLO proyeksiyalarining "
              "ikkalasida ham ko'rinishi kerak. IVC moduli bu klinik bilimni yumshoq "
              "regulyarizatsiya sifatida kiritadi. Har bir ko'rinishning obyektlik "
              "logitidan global o'rtacha jamlash (global average pooling) olinadi:")
    eq(doc, "ivc_gap", number="2.4")
    para(doc, "So'ngra bir xil tomonning CC va MLO ko'rinishlari o'rtasida muvofiqlik "
              "(silliqlik) talab qilinadi:")
    eq(doc, "ivc", number="2.5")
    para(doc, "Global jamlashdan foydalanish piksel-piksel mos kelishning noto'g'ri "
              "qo'yilishidan (CC va MLO geometriyalari turlicha bo'lgani uchun) qochadi va "
              "faqat \"obyektning mavjudligi\" darajasida muvofiqlikni talab qiladi. "
              "Bundan tashqari, har bir tomon uchun CC va MLO xususiyatlarini birlashtirishda "
              "o'rganiluvchi kanalli darvoza (channel gate) qo'llaniladi, bu modelga "
              "ko'rinishlardan kelgan ma'lumotni moslashuvchan ravishda tortishga imkon "
              "beradi.")

    h2(doc, "2.4-§. Ordinal BI-RADS regressiyasi va kompozit yoʻqotish funksiyasi")
    para(doc, "BI-RADS shkalasining ordinal tabiatini hisobga olish uchun nominal sinfli "
              "kross-entropiya o'rniga **kumulyativ bog'lanish** modeli qo'llaniladi. "
              "Yagona skalyar chiqish $f$ va $K-1$ ta ostona $\\{\\theta_k\\}$ yordamida "
              "ordinal yo'qotish ikkilik kross-entropiyalar yig'indisi sifatida "
              "ifodalanadi:")
    eq(doc, "ordinal", number="2.6")
    para(doc, "bu yerda $t_k = \\mathbf{1}(y \\leq k)$ — kumulyativ maqsad indikatori. "
              "Ostonalarning qat'iy monotonligini ($\\theta_0 < \\theta_1 < \\dots$) "
              "kafolatlash uchun ular cheklanmagan $\\tau_j$ parametrlardan $\\mathrm{softplus}$ "
              "orqali parametrlanadi:")
    eq(doc, "thresh", number="2.7")
    para(doc, "Bu parametrlash qo'shimcha jarimasiz monotonlikni ta'minlaydi va qo'shni "
              "BI-RADS darajalarining yagona qaror chegarasiga yig'ilishini oldini oladi. "
              "Ostonalar ketma-ketligining $\\tau_j$ bo'yicha Yakobian matritsasi quyi "
              "uchburchakli bo'lib, gradiyentlar faqat tartib bo'yicha \"oldinga\" oqishini "
              "ko'rsatadi:")
    eq(doc, "jacobian", number="2.8")
    para(doc, "**BCA darvozasi gradiyenti.** Umumiy yo'qotishning $\\alpha$ bo'yicha "
              "gradiyenti Frobenius ichki ko'paytmasi orqali ifodalanadi:")
    eq(doc, "grad_alpha", number="2.9")
    para(doc, "Initsializatsiya paytida $\\alpha=0$ bo'lsa-da, bu gradiyent nolga teng "
              "emas — u faqat $\\Delta F$ yo'nalishiga bog'liq. Shu sababli optimizator "
              "birinchi qadamdanoq ma'noli tushish yo'nalishini oladi, garchi BCA tarmog'i "
              "oldinga o'tishda hali ta'sir ko'rsatmasa ham. Bu — oldindan o'rgatilgan "
              "tarmoqlarni barqaror sozlash uchun foydali qo'zg'almas nuqta xususiyatidir.")
    para(doc, "**Kompozit yo'qotish funksiyasi.** Umumiy yo'qotish YOLO ning standart "
              "komponentlari (quti, sinf, taqsimot fokal yo'qotishi) bilan taklif etilgan "
              "uch regulyarizatsiyani birlashtiradi:")
    eq(doc, "total", number="2.10")
    para(doc, "bu yerda $\\lambda_1, \\lambda_2, \\lambda_3$ — giperparametrlar. Sinf "
              "yo'qotishi sifatida kross-entropiya, mikrokalsifikatsiya/massa kabi noyob "
              "sinflar uchun fokal yo'qotish (2-bob, (1.7)) qo'llanilishi mumkin:")
    eq(doc, "ce", number="2.11")
    para(doc, "Namunaviy realizatsiya (PyTorch, $\\texttt{app/models\\_arch/bca\\_yolo.py}$) "
              "BilateralCrossAttention, InterViewConsistency va OrdinalBIRADSHead "
              "komponentlarini hamda yuqori darajali BCAYoloHead orkestratorini eksport "
              "qiladi. Kanal kengliklari $(C_1,C_2,C_3)=(256,512,512)$ bo'lgan uch miqyosli "
              "tarmoq uchun qo'shimcha modullar bazaviy YOLO boshiga taxminan **3,1 mln** "
              "o'rganiluvchi parametr (bazaviy modelning ~5–8%) qo'shadi.")

    para(doc, "Ordinal kumulyativ modelning kelib chiqishini batafsil ko'rsatamiz. "
              "Maqsad $y \\in \\{0,\\dots,K-1\\}$ ni $K-1$ ta ikkilik masalaga ajratamiz: "
              "har bir $k$ uchun \"$y \\leq k$mi?\" degan savol. Bu savollarning javoblari "
              "$t_k = \\mathbf{1}(y \\leq k)$ tabiiy ravishda monoton: agar $y \\leq k$ "
              "bo'lsa, $y \\leq k+1$ ham o'rinli. Model yagona skalyar $f$ va ostonalar "
              "$\\theta_k$ orqali $P(y \\leq k) = \\sigma(\\theta_k - f)$ ehtimollikni "
              "baholaydi. Ostonalar monotonligi ($\\theta_0 < \\theta_1 < \\dots$) "
              "ehtimolliklarning ham monotonligini ($P(y\\leq 0) \\leq P(y\\leq 1) \\leq "
              "\\dots$) kafolatlaydi, bu ordinal tuzilmaning izchilligini ta'minlaydi.")
    para(doc, "Bu yondashuvning nominal kross-entropiyadan ustunligi shundaki, u xatoning "
              "kattaligini hisobga oladi: BI-RADS 5 ni 1 deb baholash, 5 ni 4 deb "
              "baholashdan ko'ra ko'proq jazolanadi, chunki ko'proq ikkilik chegaralar "
              "buziladi. Bu klinik jihatdan to'g'ri — uzoq toifalardagi xato ancha xavfli. "
              "(2.8) Yakobian matritsasi quyi uchburchakli bo'lgani uchun, $\\tau_j$ "
              "parametrining yangilanishi $\\theta_j$ dan boshlab barcha keyingi ostonalarni "
              "suradi; bu ketma-ket bog'liqlik ikki qo'shni qaror chegarasining yagona "
              "nuqtaga yig'ilishini oldini oladi va shu orqali qo'shni BI-RADS "
              "toifalarining ajralishini saqlaydi.")
    para(doc, "Amalda ordinal bosh detektsiya boshining sinf logitlari bilan birga "
              "o'rgatiladi: aniqlangan har bir nomzod o'choq uchun BI-RADS bahosi "
              "bashorat qilinadi. Bu detektsiya (qayerda) va baholash (qanchalik xavfli) "
              "vazifalarini yagona, izchil tarmoqda birlashtiradi va radiologning amaliy "
              "ish jarayoniga mos keladi.")

    h2(doc, "2.5-§. Radiomik belgilarni chuqur oʻrganish bilan birlashtirish")
    para(doc, "Modelning izohlanuvchanligini oshirish uchun chuqur tasvirlovchilar radiomik "
              "belgilar bilan birlashtiriladi (gibrid yondashuv). Aniqlangan o'choq sohasidan "
              "birinchi tartib statistikalar, shakl belgilari va GLCM teksturasi (kontrast, "
              "energiya, entropiya, gomogenlik, korrelyatsiya — (1.10), (1.11)) hisoblanadi. "
              "Chuqur xususiyat vektori $f_{deep}$ va radiomik vektor $f_{radiomic}$ "
              "konkatenatsiya orqali birlashtirilib, to'liq bog'langan qatlam $\\phi$ va "
              "tasniflagich orqali ishlanadi:")
    eq(doc, "fusion", number="2.12")
    para(doc, "Bu gibrid yondashuv chuqur o'rganishning yuqori aniqligini radiomikaning "
              "patologik asoslangan izohlanuvchanligi bilan birlashtiradi va vizual issiqlik "
              "xaritalari orqali ekspert annotatsiyalariga mos keluvchi izoh beradi. "
              "Muallifning Radiomic-Enhanced Faster R-CNN ishida bu yondashuv VinDr-Mammo "
              "to'plamida yuqori natijalarni ko'rsatgan (4-bob).")

    h2(doc, "2.6-§. Multimodal (matn-asosli) detektsiya: TILLNet va matn tasniflagichi")
    para(doc, "Klinik matn (anamnez, shikoyatlar) tasvir bilan birga mavjud bo'lganda, uni "
              "detektsiyaga kiritish samaradorlikni oshirishi mumkin. Muallifning ushbu "
              "yo'nalishdagi ishi — **TILLNet-Det** (Khamdamov R., Turaqulov Sh.X., 2026) — "
              "matn bilan boshqariladigan, FiLM (Feature-wise Linear Modulation) modulyatsiyali "
              "FCOS-uslubidagi detektor bo'lib, kam-resursli (low-resource) va ko'p tilli "
              "sharoitda mammografik o'choqlarni aniqlashga mo'ljallangan. Matn vektoriga "
              "asoslangan $\\gamma$ va $\\beta$ parametrlari tasvir xususiyatlarini "
              "modulyatsiya qiladi:")
    eq(doc, "film", number="2.13")
    para(doc, "FiLM modulyatsiyasi (2.13) matn shartiga asoslanib tasvir xususiyatlarini "
              "kanal bo'yicha masshtablaydi ($\\gamma$) va siljitadi ($\\beta$). Bu "
              "mexanizm tasvir va matn modalliklarini chuqur, qatlam darajasida "
              "birlashtiradi — oddiy konkatenatsiyaga nisbatan ifoda kuchi yuqori. Klinik "
              "kontekstda matn (anamnez, oldingi tashxis) modelni shubhali sohalarga "
              "yo'naltirishi yoki ma'lum belgilarning ehtimolligini oshirishi mumkin. "
              "Multimodal yondashuvning samaradorligi juftlangan (tasvir+matn) ma'lumot "
              "mavjudligiga bog'liq, shu sababli MAMOGRAF tizimi hisobotlarni tasvirlar "
              "bilan bog'lash imkonini beradi.")
    para(doc, "**Matnni tasniflash (XS-Classifier).** Ko'p tilli (o'zbek-kirill, "
              "o'zbek-lotin, rus) hisobotlarni tasniflash uchun krossskript TF-IDF va "
              "logistik regressiya asosidagi yengil model qo'llaniladi. TF-IDF og'irligi "
              "so'zning hujjatdagi va korpusdagi chastotasidan hisoblanadi:")
    eq(doc, "tfidf", number="2.14")
    para(doc, "Ushbu komponentlar MAMOGRAF tizimida tadqiqot konveyeri (pseudo-labels, "
              "review queue) doirasida ishlatiladi.")
    h2(doc, "2.7-§. Oʻqitish protseduri, augmentatsiya va giperparametrlar")
    para(doc, "Taklif etilgan model uchidan-uchiga (end-to-end) o'rgatiladi. O'qitish "
              "jarayoni quyidagi bosqichlardan iborat. Birinchidan, bazaviy tarmoq COCO "
              "ma'lumotlar to'plamida oldindan o'rgatilgan og'irliklar bilan "
              "initsializatsiya qilinadi (transfer learning), bu kam tibbiy ma'lumot "
              "sharoitida konvergensiyani tezlashtiradi. BCA blokining α koeffitsiyenti "
              "nolga, ordinal ostonalar esa teng oraliqlarga initsializatsiya qilinadi. "
              "Ikkinchidan, har bir paketda (batch) bir tadqiqotning to'rtta ko'rinishi "
              "birgalikda uzatiladi, bu ikki tomonlama va ko'rinishlararo modullarning "
              "ishlashini ta'minlaydi.")
    para(doc, "Optimallashtirish uchun AdamW optimizatori og'irliklar so'nishi (weight "
              "decay) bilan qo'llaniladi. O'rganish tezligi (learning rate) kosinus "
              "jadvali bo'yicha chiziqli isinish (warmup) bilan o'zgartiriladi — bu "
              "o'qitish boshidagi beqarorlikni kamaytiradi. Aralash aniqlikdagi (mixed "
              "precision) hisoblash xotira sarfini kamaytiradi va o'qitishni tezlashtiradi. "
              "Erta to'xtatish (early stopping) validatsiya mAP'i belgilangan epochlar "
              "davomida yaxshilanmaganda o'qitishni to'xtatadi va ortiqcha moslashishning "
              "(overfitting) oldini oladi.")
    para(doc, "**Augmentatsiya.** Ma'lumotlar kamligini bartaraf etish va umumlashtirishni "
              "oshirish uchun augmentatsiya qo'llaniladi: tasodifiy masshtablash, yorqinlik "
              "va kontrast o'zgartirish, mozaik (mosaic) birlashtirish. Muhim klinik jihat — "
              "mammografiyada gorizontal akslantirish (fliplr) ehtiyotkorlik bilan "
              "ishlatiladi, chunki laterallik (chap/o'ng) klinik ahamiyatga ega; "
              "ikki tomonlama modul o'ng ko'rinishni atayin akslantirgani uchun "
              "augmentatsiyadagi akslantirish alohida nazorat qilinadi.")
    para(doc, "**Giperparametrlar.** Asosiy giperparametrlar quyidagilarni o'z ichiga "
              "oladi: tasvir o'lchami (imgsz, odatda 1024–1536), paket hajmi (batch), "
              "epochlar soni, boshlang'ich o'rganish tezligi (lr0), momentum, og'irliklar "
              "so'nishi (weight decay), hamda regulyarizatsiya koeffitsiyentlari "
              "$\\lambda_1, \\lambda_2, \\lambda_3$. Bu koeffitsiyentlar BCA, IVC va ordinal "
              "yo'qotishlarning umumiy yo'qotishdagi nisbiy hissasini boshqaradi va "
              "validatsiya to'plamida tanlanadi. MAMOGRAF tizimining Model Studio moduli "
              "bu parametrlarning barchasini grafik interfeys orqali sozlash imkonini "
              "beradi.")
    para(doc, "**O'qitish algoritmi (umumiy sxema).** Har bir iteratsiyada: (1) to'rt "
              "ko'rinish bazaviy tarmoqdan o'tkaziladi va ko'p miqyosli xususiyatlar "
              "olinadi; (2) BCA bloki kontralateral juftliklar o'rtasida o'zaro e'tiborni "
              "hisoblab, asimmetriyaga asoslangan qoldiq yangilanish qo'shadi; (3) IVC "
              "moduli bir tomonning CC va MLO obyektlik logitlarini muvofiqlashtiradi; "
              "(4) detektsiya boshi qutilar, sinflar va ordinal BI-RADS chiqishini "
              "bashorat qiladi; (5) kompozit yo'qotish (2.10) hisoblanadi va orqaga "
              "tarqalish (backpropagation) orqali barcha parametrlar yangilanadi. "
              "Inferens bosqichida vaznli quti birlashtirish (WBF) va test vaqti "
              "augmentatsiyasi (TTA) yakuniy aniqlikni oshiradi.")
    concl(doc, "II", [
        "Ikki tomonlama o'zaro e'tibor (BCA) bloki kontralateral asimmetriyani nolga initsializatsiyalangan o'rganiluvchi α koeffitsiyenti bilan modelga kiritadi va barqaror sozlashni ta'minlaydi.",
        "Ko'rinishlararo muvofiqlik (IVC) moduli CC va MLO ko'rinishlari o'rtasida obyektlik muvofiqligini global jamlash orqali talab qiladi.",
        "Ordinal regressiya boshi BI-RADS ni softplus orqali parametrlangan qat'iy monoton ostonalar bilan kumulyativ tarzda baholaydi; gradiyent tahlili barqarorlikni tasdiqlaydi.",
        "Kompozit yo'qotish funksiyasi standart YOLO komponentlarini uch yangi regulyarizatsiya bilan birlashtiradi.",
        "Radiomik belgilarni chuqur tasvirlovchilar bilan birlashtirish izohlanuvchanlikni oshiradi; TILLNet va matn tasniflagichi multimodal kengaytmani ta'minlaydi.",
    ])
    pb(doc)


# --------------------------------------------------------------------------- #
# II bob (davomi) — bulcha belgi tanlash + gibrid ansambl                     #
# (dissertatsiya_bob_boolfs.py modulidan; formulalar Word native OMML)        #
# --------------------------------------------------------------------------- #
@section
def bob2a_boolfs(doc):
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import dissertatsiya_bob_boolfs as bb
    bb.emit(doc, h1, h2, para, lead, bullets, table, concl, img_path)
    pb(doc)


# --------------------------------------------------------------------------- #
# III BOB                                                                     #
# --------------------------------------------------------------------------- #
@section
def bob3(doc):
    h1(doc, "III bob. Algoritmlarni amalga oshiruvchi dasturiy majmua")

    h2(doc, "3.1-§. Tizim arxitekturasi, maxfiylik va xavfsizlik")
    para(doc, "Taklif etilgan algoritmlar **MAMOGRAF** dasturiy majmuasida amaliyotga "
              "tatbiq etilgan. Tizim mijoz-server arxitekturasida qurilgan: serverlik qismi "
              "(backend) Python tilida FastAPI freymvorkida, mijozlik qismi (frontend) "
              "qo'shimcha kutubxonalarsiz HTML/JavaScript/CSS da amalga oshirilgan. DICOM "
              "fayllar bilan ishlash pydicom va pylibjpeg kutubxonalari orqali, AI inference "
              "va o'qitish Ultralytics YOLO hamda PyTorch (CUDA) orqali bajariladi. "
              "Ma'lumotlar SQLite ma'lumotlar bazasida saqlanadi. Umumiy modul arxitekturasi "
              "3.1-rasmda keltirilgan.")
    img(doc, "architecture.png", width=6.0, caption="3.1-rasm. MAMOGRAF dasturiy majmuasi arxitekturasi")
    para(doc, "**Maxfiylik (de-identifikatsiya).** Maxfiylik talablariga muvofiq, har bir "
              "yuklangan DICOM faylda shaxsiy ma'lumotlar (PHI) — bemor ismi, identifikatori, "
              "tug'ilgan sanasi, shifokor va muassasa nomlari — yuklash bosqichida avtomatik "
              "tarzda o'chiriladi yoki anonimlashtiriladi. Bunda piksel ma'lumotlari, tasvir "
              "o'lchamlari va modallik (Modality) saqlanadi, chunki ular tadqiqot uchun "
              "zarur. Keyingi barcha bosqichlar (annotatsiya, AI, eksport) faqat "
              "PHI-siz nusxa ustida bajariladi.")
    para(doc, "**Xavfsizlik.** Tizimga kirish JWT (JSON Web Token) asosidagi "
              "autentifikatsiya orqali amalga oshiriladi. Foydalanuvchilar uchta rolga "
              "bo'linadi — administrator, ko'rib chiquvchi (reviewer) va annotator — va "
              "har bir rol uchun ruxsatlar farqlanadi. Qo'shimcha himoya sifatida ikki "
              "bosqichli (TOTP) autentifikatsiya qo'llab-quvvatlanadi.")

    para(doc, "Texnologik tanlovlar amaliy talablar asosida belgilangan. FastAPI "
              "freymvorki asinxron so'rovlarni samarali qayta ishlash va avtomatik API "
              "hujjatlash imkonini beradi. Frontend qo'shimcha og'ir kutubxonalarsiz sof "
              "JavaScript da amalga oshirilgani tufayli yengil va portativ. Ma'lumotlar "
              "bazasi sifatida SQLite tanlangan — u alohida server talab qilmaydi va "
              "klinik ish stantsiyasida mustaqil ishlaydi, bu maxfiylik va sodda joriy "
              "etish nuqtai nazaridan afzal. Og'ir hisoblash (AI inference va o'qitish) "
              "GPU da bajariladi.")
    para(doc, "Tizim modulli arxitekturada qurilgan: autentifikatsiya, DICOM boshqaruvi, "
              "annotatsiya, AI inference, model o'qitish, hisobot generatsiyasi, eksport va "
              "PACS integratsiyasi alohida mantiqiy modullarni tashkil etadi. Bu modullik "
              "kengaytirilishni (yangi model arxitekturalari yoki eksport formatlari "
              "qo'shish) osonlashtiradi. Tizim Docker konteynerizatsiyasi orqali ham "
              "joylashtirilishi mumkin, bu turli muhitlarda izchil ishlashni ta'minlaydi.")
    para(doc, "GPU resurslaridan samarali foydalanish uchun model og'irliklari xotirada "
              "keshlanadi va inference paketli (batch) tarzda bajariladi. O'qitish jarayoni "
              "asosiy web-xizmatdan alohida subprocess sifatida ishga tushiriladi, bu "
              "uzoq davom etuvchi o'qitish web-interfeysning javobgarligiga ta'sir "
              "qilmasligini ta'minlaydi. Bu ajratish, shuningdek, o'qitishni to'xtatish va "
              "davom ettirish imkonini beradi.")

    para(doc, "Xavfsizlik modeli bir necha bosqichli himoyani nazarda tutadi. Kirish "
              "bosqichida JWT token foydalanuvchini autentifikatsiya qiladi va token "
              "muddati cheklangan. Har bir so'rovda foydalanuvchining roli tekshirilib, "
              "ruxsat etilmagan amallar rad etiladi (masalan, annotator boshqa "
              "foydalanuvchi yaratgan annotatsiyani tahrirlay olmaydi). Maxfiy amallar "
              "uchun ikki bosqichli (TOTP) autentifikatsiya qo'shimcha himoya qatlamini "
              "ta'minlaydi. So'rovlar chastotasi cheklanadi (rate limiting), bu xizmatga "
              "qaratilgan hujumlarning oldini oladi.")
    para(doc, "Ma'lumotlar maxfiyligi nuqtai nazaridan eng muhim qaror — tizimning "
              "**mahalliy (oflayn) ishlashi**. Bemor tasvirlari va hisobotlari tashqi "
              "bulutli xizmatlarga jo'natilmaydi; AI inference, model o'qitish va hatto "
              "avtomatik xulosa generatsiyasi (lokal til modeli orqali) to'liq mahalliy "
              "infratuzilmada bajariladi. Bu yondashuv tibbiy ma'lumotlarni himoya qilish "
              "talablariga muvofiq keladi va ma'lumotlarning chegaradan tashqariga "
              "chiqishi xavfini bartaraf etadi.")

    h2(doc, "3.2-§. Annotatsiya, faol oʻrganish va AI yordami")
    para(doc, "Radiolog DICOM ko'ruvchida tasvirni tahlil qilib, shubhali sohalarni quti "
              "(bbox) yoki ko'pburchak (polygon) bilan belgilaydi va har bir o'choqqa sinf, "
              "BI-RADS kategoriyasi hamda izoh biriktiradi. Annotatsiyalar holatlar oqimi "
              "orqali nazorat qilinadi: dastlabki (draft) → taqdim etilgan (submitted) → "
              "tasdiqlangan (approved) yoki rad etilgan (rejected). Ko'rib chiquvchi rolidagi "
              "mutaxassis annotatsiyalarni tekshiradi va tasdiqlaydi; barcha o'zgarishlar "
              "audit jurnalida qayd etiladi.")
    para(doc, "**AI yordami.** Tizim radiolog ishini tezlashtiruvchi bir nechta AI "
              "funksiyani taklif etadi: avtomatik inference (model bbox'larni avtomatik "
              "taklif qiladi), smart-click (bir bosishda atrofdagi o'choqni topib quti "
              "chizish) va noaniqlik (uncertainty) issiqlik xaritasi (model qayerda "
              "ishonchsiz ekanini ko'rsatish). Issiqlik xaritasi test vaqti augmentatsiyasi "
              "(TTA) asosida hisoblanadi.")
    para(doc, "**Faol o'rganish (active learning) sikli.** Tizim AI bashoratlaridan farqli "
              "yoki radiolog tomonidan tasdiqlangan annotatsiyalar sonini kuzatib boradi va "
              "yetarli yangi ma'lumot to'planganda modelni qayta o'qitishni tavsiya qiladi. "
              "Bu inson-mashina hamkorligi siklini (3.2-rasm) tashkil etadi: AI taklif "
              "qiladi → radiolog tasdiqlaydi/tuzatadi → yangi ma'lumot to'planadi → model "
              "qayta o'qitiladi → aniqlik oshadi. Ushbu yopiq halqali (closed-loop), "
              "radiolog-inson hamkorligiga asoslangan matnga yo'naltirilgan zaif nazoratli "
              "o'qitish yondashuvi muallifning alohida ishida (Khamdamov R., Turaqulov "
              "Sh.X., 2026) batafsil asoslangan va ayniqsa annotatsiya kam bo'lgan "
              "sharoitlar uchun samarali.")
    img(doc, "cycle.png", width=4.8, caption="3.2-rasm. Faol o'rganish sikli (AI ↔ radiolog)")

    para(doc, "AI inference konveyeri bir nechta rejimni qo'llab-quvvatlaydi. Avtomatik "
              "inference rejimida yuklangan tasvirga model fonda qo'llaniladi va nomzod "
              "qutilar generatsiya qilinadi — radiolog ekranga kelganda bashoratlar "
              "allaqachon tayyor bo'ladi. Smart-click rejimida foydalanuvchi shubhali "
              "sohaga bir marta bosadi va model shu nuqta atrofidagi o'choqni topib quti "
              "chizadi — bu qo'lda quti chizishga nisbatan ancha tez. Batch rejimi bir "
              "nechta tasvirga bir vaqtda model qo'llaydi.")
    para(doc, "Noaniqlikni baholash uchun test vaqti augmentatsiyasi (TTA) qo'llaniladi: "
              "tasvir bir nechta o'zgartirilgan ko'rinishda (masshtab, akslantirish) "
              "modeldan o'tkaziladi va bashoratlar tarqalishi noaniqlik o'lchovi sifatida "
              "ishlatiladi. Bashoratlarning yuqori tarqalishi modelning shu sohada "
              "ishonchsizligini ko'rsatadi. Bir nechta modeldan kelgan bashoratlarni "
              "birlashtirish uchun vaznli quti birlashtirish (Weighted Box Fusion, WBF) "
              "usuli qo'llaniladi — u ishonch ballari bo'yicha vaznlangan o'rtacha qutini "
              "hisoblaydi va ansambl aniqligini oshiradi.")
    para(doc, "AI bashoratlari va radiolog tasdig'ini farqlash uchun har bir annotatsiya "
              "manbai (AI yoki inson) va holati saqlanadi. Bu faol o'rganish uchun zarur: "
              "tizim AI bashoratidan farqli ravishda radiolog tomonidan tuzatilgan yoki "
              "tasdiqlangan annotatsiyalarni \"qimmatli\" o'qitish signali sifatida ajratadi "
              "va shular yetarli to'planganda qayta o'qitishni tavsiya qiladi.")

    h2(doc, "3.3-§. Model oʻqitish konveyeri (Model Studio) va resurslar monitoringi")
    para(doc, "**Model Studio** — foydalanuvchining o'z annotatsiyalaridan yangi YOLO "
              "modelini grafik protsessor (GPU) da o'qitish imkonini beruvchi modul. "
              "Konveyer quyidagi bosqichlardan iborat: (i) annotatsiyalardan Ultralytics "
              "YOLO formatidagi datasetni ($\\texttt{images/\\{train,val\\}}$, "
              "$\\texttt{labels/\\{train,val\\}}$, $\\texttt{data.yaml}$) avtomatik "
              "tayyorlash, bunda bo'linish bemor darajasida amalga oshiriladi (data "
              "leakage'ning oldini olish uchun); (ii) dataset yaxlitligini tekshirish "
              "(rasm soni, sinf taqsimoti, rasm-belgi mosligi, buzuq fayllar); (iii) "
              "to'liq giperparametrlar bilan o'qitishni boshlash.")
    para(doc, "O'qitish jarayoni alohida subprocess sifatida ishga tushiriladi, bu uni "
              "to'xtatish (Stop) va keyin so'nggi nuqtadan davom ettirish (Resume) imkonini "
              "beradi. O'qitish davomida jonli metrikalar — train/val yo'qotishi, mAP@50, "
              "mAP@50–95, precision va recall — real vaqtda grafiklarda aks ettiriladi. "
              "Resurslar monitoringi GPU xotirasi (VRAM), yuklanish (utilization) va "
              "haroratni kuzatib boradi hamda berilgan tasvir o'lchami va paket hajmi uchun "
              "xotira yetishmasligi xavfini oldindan ogohlantiradi. O'qitilgan eng yaxshi "
              "model avtomatik tarzda joylashtiriladi va darhol ishlatishga tayyor bo'ladi.")

    para(doc, "Model Studio dataset tekshiruvi moduli o'qitishdan oldin ma'lumotlar "
              "yaxlitligini avtomatik nazorat qiladi: u har bir bo'lim (train/val) uchun "
              "tasvirlar sonini sanaydi, sinflar taqsimotini hisoblaydi (sinflar "
              "muvozanatsizligini aniqlash uchun), har bir tasvirga mos belgi faylining "
              "mavjudligini tekshiradi va bo'sh yoki buzilgan fayllarni aniqlaydi. Bu "
              "tekshiruv o'qitishdagi yashirin xatolarning oldini oladi va ma'lumot "
              "sifatini kafolatlaydi. Dataset Ultralytics formatida — $\\texttt{data.yaml}$ "
              "konfiguratsiya fayli, sinf nomlari va yo'llar bilan — tashkil etiladi.")
    para(doc, "O'qitish davomida metrikalar (yo'qotish komponentlari, mAP, precision, "
              "recall) har bir epochda $\\texttt{results.csv}$ fayliga yoziladi va "
              "web-interfeysga jonli uzatiladi. Foydalanuvchi grafiklar orqali o'qitish "
              "borishini real vaqtda kuzatadi va zarur bo'lsa jarayonni to'xtatadi. "
              "To'xtatilganda oxirgi nuqta (last.pt) saqlanib, keyin shu nuqtadan davom "
              "ettirish (Resume) mumkin. O'qitilgan eng yaxshi model (best.pt) validatsiya "
              "mAP'i bo'yicha tanlanib, avtomatik tarzda ishlatishga joylashtiriladi.")

    para(doc, "**Masofaviy (taqsimlangan) GPU o'qitish arxitekturasi.** Klinik ish "
              "stantsiyasi yoki ilova serveri ko'pincha kuchli grafik protsessorga ega "
              "bo'lmaydi, model o'qitish esa katta hisoblash resursini talab qiladi. Shu "
              "sababli MAMOGRAF tizimida o'qitishni alohida GPU serverga uzatuvchi "
              "taqsimlangan arxitektura amalga oshirilgan. Asosiy ilova (FastAPI) "
              "o'qitishni mahalliy bajarish o'rniga, maxsus o'qitish ishchisiga (train "
              "worker) — GPU serverda ishlovchi alohida FastAPI xizmatiga — token bilan "
              "himoyalangan HTTP interfeys orqali topshiradi. Ishchi xizmat o'qitishni "
              "boshlash, holat va jurnalni so'rash, to'xtatish hamda tayyor modelni "
              "qaytarish endpointlarini taqdim etadi; asosiy ilova bu holatni "
              "web-interfeysga shaffof tarzda proksilab uzatadi.")
    para(doc, "Bu arxitekturada ikkita amaliy muammo hal etilgan. Birinchidan, "
              "**datasetni oldindan tayyorlash.** O'qitish boshlanganda katta hajmli "
              "datasetni tarmoq orqali uzatish sezilarli kechikishga olib keladi. Shu "
              "sababli dataset tasvirlarni renderlash bosqichida (o'qitishdan oldin) GPU "
              "serverga nomlangan to'plam sifatida yuklab qo'yiladi; o'qitish tugmasi "
              "bosilganda esa faqat parametrlar uzatiladi va o'qitish darhol boshlanadi — "
              "qayta yuklash kechikishisiz. Ikkinchidan, **uzilishlarga chidamlilik:** "
              "o'qitishni boshlashdan oldin tizim GPU serverning mavjudligini "
              "(health-check) tekshiradi; server javob bermasa, foydalanuvchiga aniq xabar "
              "beriladi va o'qitish boshlanmaydi. Tayyor model (best.pt) avtomatik "
              "yuklab olinib, asosiy ilovaning modellar katalogiga joylashtiriladi va "
              "darhol inference uchun ishlatishga tayyor bo'ladi. Bu taqsimlangan yondashuv "
              "GPU resurslarini bir nechta klinik ish stantsiyasi o'rtasida samarali "
              "taqsimlash imkonini beradi va mahalliy (oflayn) ishlash tamoyilini saqlaydi.")

    h2(doc, "3.4-§. Avtomatik xulosa shakllantirish, DICOM SR va PACS integratsiyasi")
    para(doc, "Tasdiqlangan annotatsiyalardan strukturaviy topilmalar — laterallik, "
              "proyeksiya, kvadrant, tur, o'lcham va BI-RADS kategoriyasi — shakllantiriladi. "
              "Bu topilmalardan avtomatik klinik xulosa (hisobot) yaratiladi. Xulosa ikki "
              "usulda hosil bo'lishi mumkin: (i) deterministik shablon — modelsiz, bir zumda "
              "va to'liq oflayn; (ii) lokal til modeli (Ollama, qwen2.5 oilasi) — tabiiy "
              "matnli qoralama yozadi va tashqi API kalitini hamda internetni talab qilmaydi.")
    para(doc, "Avtomatik xulosaning klinik xavfsizligini ta'minlash uchun bir nechta "
              "muhim tamoyil qo'llaniladi: (a) til modeli **faqat berilgan strukturaviy "
              "topilmalardan** foydalanadi va yangi ma'lumot to'qib chiqarmaydi (grounded "
              "generation); (b) generatsiya determinizmi uchun harorat (temperature) nolga "
              "teng olinadi; (c) o'zbekcha klinik atamalar lug'ati orqali terminologiya "
              "to'g'riligi ta'minlanadi; (d) chiqish doimo radiolog tekshirib tasdiqlaydigan "
              "**qoralama** sifatida belgilanadi.")
    para(doc, "Tasdiqlangan xulosa standart **DICOM SR** (Structured Report, Comprehensive "
              "SR) sifatida eksport qilinadi — bunda bemor va tadqiqot metama'lumotlari "
              "manba DICOM fayldan meros olinadi, hisobot matni, BI-RADS bahosi va har bir "
              "topilma alohida tarkibiy elementlar sifatida saqlanadi. Tizim PACS bilan "
              "to'liq integratsiyalashgan (C-ECHO, C-FIND, C-STORE, C-MOVE), shu sababli "
              "mavjud klinik infratuzilmaga moslashadi va xulosani PACS serveriga jo'natish "
              "imkonini beradi.")
    para(doc, "Avtomatik xulosa generatori uch bosqichli konveyerdan iborat. Birinchi "
              "bosqichda annotatsiyalardan **strukturaviy topilmalar** (findings) "
              "shakllantiriladi: har bir o'choq uchun laterallik (DICOM metama'lumotidan), "
              "proyeksiya, kvadrant (quti markazi koordinatasidan hisoblanadi), tur "
              "(detektor sinfidan), o'lcham va BI-RADS kategoriyasi aniqlanadi. Bu "
              "strukturaviy ifoda — detektsiya va matn generatsiyasi o'rtasidagi ko'prik "
              "vazifasini bajaradi. Ikkinchi bosqichda strukturaviy topilmalardan matn "
              "hosil qilinadi: deterministik shablon (tayyor jumla qoliplari) yoki lokal "
              "til modeli. Uchinchi bosqichda matn radiolog tomonidan tahrirlanadi va "
              "tasdiqlanadi.")
    para(doc, "Lokal til modelidan foydalanishda klinik xavfsizlik bir necha mexanizm "
              "bilan ta'minlanadi. Modelga **faqat strukturaviy topilmalar** uzatiladi va "
              "tizimli ko'rsatma (system prompt) orqali u faqat shu ma'lumotdan foydalanishi, "
              "yangi topilma yoki tashxis qo'shmasligi qat'iy talab qilinadi (grounded "
              "generation). Generatsiya determinizmini ta'minlash uchun harorat parametri "
              "nolga teng olinadi. Tasvir ko'rinishlari ro'yxati topilma bilan "
              "adashtirilmasligi uchun aniq belgilanadi, bu soxta «normal» xulosalar "
              "to'qilishining oldini oladi. Klinik atamalar lug'ati orqali terminologiya "
              "to'g'riligi nazorat qilinadi.")
    para(doc, "Tasdiqlangan xulosa DICOM Comprehensive SR obyektiga aylantiriladi. SR "
              "tarkibi (Content Sequence) ierarxik tuzilmaga ega: ildiz konteyneri "
              "«Radiology Report» kod tushunchasi bilan belgilanadi, uning ichida hisobot "
              "matni (Report), umumiy baho (Assessment, BI-RADS), tavsiya (Recommendation) "
              "va har bir topilma (Finding) alohida tarkibiy element sifatida saqlanadi. "
              "Bemor va tadqiqot identifikatorlari manba DICOM fayldan meros olinadi, bu SR "
              "ning to'g'ri tadqiqotga bog'lanishini ta'minlaydi. SR dastlab tasdiqlanmagan "
              "(UNVERIFIED) holatda yaratiladi, bu uning qoralama ekanini ifodalaydi.")

    h2(doc, "3.5-§. Maʼlumotlar modeli, dasturiy interfeyslar va ish oqimi")
    para(doc, "MAMOGRAF tizimining ma'lumotlar modeli SQLite ma'lumotlar bazasida "
              "saqlanadi va quyidagi asosiy jadvallarni o'z ichiga oladi: foydalanuvchilar "
              "(rollar, parol xeshi, TOTP holati), annotatsiyalar tarixi (har bir "
              "o'zgarishning versiyasi), audit jurnali, ish ro'yxati (worklist), PACS "
              "serverlari konfiguratsiyasi va bemor-tasvir-hisobot bog'lanishlari. Har bir "
              "annotatsiya JSON tuzilmasida saqlanadi: identifikator, tur (quti/ko'pburchak), "
              "sinf yorliqlari (multi-label), BI-RADS kategoriyasi, normallashtirilgan "
              "koordinatalar (bbox), kadr raqami, izoh, yaratuvchi, holat va ko'rib chiqish "
              "ma'lumotlari.")
    para(doc, "**Dasturiy interfeyslar (API).** Tizim REST arxitekturasida qurilgan bo'lib, "
              "asosiy endpointlar quyidagi guruhlarga bo'linadi: autentifikatsiya va "
              "foydalanuvchilarni boshqarish; DICOM yuklash, ro'yxat, metama'lumot va tasvir "
              "renderlash; annotatsiyalarni o'qish/yozish va holatini boshqarish; AI inference "
              "(batch, smart-click, uncertainty); model o'qitish (run, stop, status, metrics, "
              "validate); hisobot generatsiyasi va DICOM SR eksporti; PACS bilan ishlash; "
              "statistika va audit. Har bir endpoint rol asosidagi ruxsat bilan himoyalangan.")
    para(doc, "**Bemor-tasvir-hisobot bog'lanishi.** Klinik amaliyotda bitta bemorga bir "
              "nechta tasvir (to'rt ko'rinish) va matnli hisobot tegishli bo'ladi. Tizim "
              "bu obyektlarni bog'lash (linking) va mos kelmaslik holatlarini aniqlash "
              "(match) imkonini beradi; bu xususiyat klinik ma'lumotlar bazasidan "
              "import qilingan hisobotlarni tegishli tasvirlar bilan bog'lashda muhim. "
              "Bog'langan hisobotlar TILLNet va matn tasniflagichi uchun qo'shimcha "
              "modallik sifatida ishlatilishi mumkin.")
    para(doc, "**Audit va kuzatuvchanlik.** Annotatsiyalardagi har bir o'zgarish (yaratish, "
              "tahrirlash, tasdiqlash, rad etish) foydalanuvchi va vaqt belgisi bilan audit "
              "jurnalida qayd etiladi. Bu klinik sifat nazorati, javobgarlik va "
              "qonuniy talablarga muvofiqlik uchun zarur. Bildirishnomalar tizimi ko'rib "
              "chiquvchilar va annotatorlar o'rtasida muloqotni ta'minlaydi.")
    para(doc, "**Tadqiqot konveyeri.** MAMOGRAF tizimi tadqiqot uchun pseudo-belgilash "
              "(pseudo-labels), ko'rib chiqish navbati (review queue) va gold-belgilarni "
              "eksport qilish mexanizmlarini qo'llab-quvvatlaydi. Bu yarim-nazoratli "
              "(semi-supervised) o'qitish va faol o'rganish stsenariylarini amalga "
              "oshirishga imkon beradi: model zaif belgilarni generatsiya qiladi, radiolog "
              "ularni tasdiqlaydi/tuzatadi, natijada yuqori sifatli o'qitish to'plami "
              "shakllanadi.")
    concl(doc, "III", [
        "MAMOGRAF FastAPI backend va web-interfeysida amalga oshirilgan; har bir DICOM yuklashda PHI avtomatik anonimlashtiriladi.",
        "Annotatsiya, faol o'rganish va AI yordami (smart-click, uncertainty) radiolog ishini tezlashtiradi.",
        "Model Studio GPU'da subprocess sifatida o'qitishni (Stop/Resume), jonli metrikalar va resurslar monitoringini ta'minlaydi.",
        "O'qitishni alohida GPU serverga uzatuvchi taqsimlangan arxitektura datasetni oldindan yuklash hisobiga darhol start, uzilishlarga chidamlilik va modelni avtomatik joylashtirishni ta'minlaydi.",
        "Avtomatik xulosa lokal til modelida grounded, deterministik va klinik atamalarga mos tarzda shakllantiriladi.",
        "Xulosa DICOM SR sifatida eksport qilinadi va PACS bilan integratsiyalashgan, bu klinik ish oqimini to'liq qo'llab-quvvatlaydi.",
    ])
    pb(doc)


# --------------------------------------------------------------------------- #
# III bob (davomi) — Avtomatlashtirilgan annotatsiya yig'ish quyi tizimi      #
# (make_maqola_annotatsiya.py modulidan import qilinadi)                      #
# --------------------------------------------------------------------------- #
@section
def bob3a_annotatsiya(doc):
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import make_maqola_annotatsiya as ma
    for nm, tex in ma.ANNOT_FORMULAS.items():
        render_eq(nm, tex)
    ma.render_figures()
    h1(doc, "III bob (davomi). Avtomatlashtirilgan annotatsiya yig'ish quyi "
            "tizimining matematik modeli")
    ma.emit_article(doc, h1, h2, para, lead, bullets, eq, table,
                    IMG=ma.img_fig, top_title=False)
    pb(doc)


# --------------------------------------------------------------------------- #
# IV BOB                                                                      #
# --------------------------------------------------------------------------- #
@section
def bob4(doc):
    h1(doc, "IV bob. Tajribaviy tadqiqotlar va amaliyotda qoʻllash")

    h2(doc, "4.1-§. Maʼlumotlar toʻplami, eksperiment sxemasi va baholash metodologiyasi")
    para(doc, "Taklif etilgan modellar ochiq **VinDr-Mammo** ma'lumotlar to'plamida "
              "(taxminan 20 000 to'liq maydonli raqamli mammografiya tasviri, BI-RADS "
              "belgilari va shikastlanish annotatsiyalari bilan) baholandi. Ma'lumotlar "
              "to'plami bemor darajasida o'qitish, validatsiya va test qismlariga ajratildi, "
              "bu data leakage'ning oldini oladi. O'qitishda augmentatsiya (akslantirish, "
              "masshtablash, yorqinlik o'zgartirish) qo'llanildi.")
    para(doc, "Ochiq taqqoslash to'plamidan tashqari, tizimni mahalliy klinik sharoitda "
              "sinovdan o'tkazish uchun **Respublika ixtisoslashtirilgan Onkologiya va "
              "Radiologiya ilmiy-amaliy tibbiy markazi**dan klinik mammografiya tasvirlari "
              "(DICOM) olindi. Bu tasvirlar maxfiylik talablariga muvofiq yuklash bosqichida "
              "avtomatik anonimlashtirildi (PHI o'chirildi) va MAMOGRAF tizimida radiologlar "
              "tomonidan annotatsiyalandi. Mahalliy to'plamdan foydalanish modelni "
              "O'zbekiston populyatsiyasi va mahalliy tasvirlash qurilmalari sharoitida "
              "baholash, hamda klinik ish oqimini real ma'lumotda tekshirish imkonini beradi.")
    para(doc, "**Eksperiment sxemasi.** O'qitish, validatsiya va test qismlari bemor "
              "darajasida ajratiladi: bir bemorning barcha tasvirlari faqat bitta qismda "
              "bo'ladi, bu bir bemor ma'lumotining ham o'qitishda, ham testda paydo "
              "bo'lishidan (data leakage) qochadi va baholashning xolisligini ta'minlaydi. "
              "Modellar bir nechta tasodifiy urug' (random seed) bilan o'rgatilib, "
              "natijalarning barqarorligi tekshiriladi. Giperparametrlar validatsiya "
              "to'plamida sozlanadi, yakuniy baho esa faqat test to'plamida o'lchanadi.")
    para(doc, "**Hisoblash muhiti.** Tajribalar GPU bilan jihozlangan ish stantsiyasida "
              "o'tkazildi. Bazaviy tarmoq COCO og'irliklari bilan initsializatsiya qilindi; "
              "o'qitishda aralash aniqlik (mixed precision) va augmentatsiya qo'llanildi. "
              "Inferens bosqichida vaznli quti birlashtirish (WBF) va test vaqti "
              "augmentatsiyasi (TTA) yordamida natijalar barqarorlashtirildi. Aniqlash "
              "ostonasi (confidence threshold) va NMS parametrlari validatsiyada "
              "optimallashtirildi.")
    para(doc, "**Baholash metrikalari.** Aniqlangan va haqiqiy quti o'rtasidagi mos kelish "
              "kesishish-birlashish nisbati (IoU) bilan o'lchanadi:")
    eq(doc, "iou", number="4.1")
    para(doc, "To'g'rilik (precision), to'liqlik (recall) va ularning garmonik o'rtachasi "
              "(F1) quyidagicha hisoblanadi:")
    eq(doc, "prf", number="4.2")
    para(doc, "Tibbiy tashxisda muhim bo'lgan sezgirlik (Se) va xoslik (Sp):")
    eq(doc, "sesp", number="4.3")
    para(doc, "Detektsiya sifatining umumiy ko'rsatkichi — har bir sinf uchun precision-"
              "recall egri chizig'i ostidagi yuza (AP) va ularning o'rtachasi (mAP):")
    eq(doc, "ap_map", number="4.4")
    para(doc, "Tasniflash sifati uchun ROC egri chizig'i ostidagi yuza (AUC):")
    eq(doc, "auc", number="4.5")
    para(doc, "BI-RADS kabi ordinal baholashda kuzatuvchilararo moslik kvadratik "
              "og'irlikli Koen kappasi ($\\kappa_w$) bilan o'lchanadi — bu yaqin "
              "kategoriyalardagi xatolarni uzoq kategoriyalardagidan kam jazolaydi:")
    eq(doc, "kappa", number="4.6")
    para(doc, "Segmentatsiya sifati uchun Dice koeffitsiyenti va sezgirlik:")
    eq(doc, "dice", number="4.7")

    para(doc, "Mammografik aniqlash masalasi uchun FROC tahlili alohida ahamiyatga ega. "
              "Oddiy ROC tahlilidan farqli ravishda, FROC bir tasvirda bir nechta "
              "shikastlanish bo'lishi mumkinligini hisobga oladi va sezgirlikni har bir "
              "tasvirga to'g'ri keluvchi o'rtacha soxta-musbatlar soniga (FPpI) nisbatan "
              "chizadi. Bashorat haqiqiy o'choq bilan IoU yoki markaz masofasi mezoni "
              "bo'yicha mos kelsa to'g'ri-musbat hisoblanadi. Umumiy ko'rsatkich sifatida "
              "belgilangan FPpI nuqtalaridagi (masalan, 0,25; 0,5; 1; 2; 4) o'rtacha "
              "sezgirlik — raqobat samaradorligi metrikasi (CPM) — qo'llaniladi.")
    para(doc, "Metrikalarning statistik ishonchliligini baholash uchun bootstrap usuli "
              "ishlatiladi: test to'plamidan $B$ marta takroriy tanlash o'tkazilib, har "
              "safar metrika qayta hisoblanadi va olingan taqsimotdan 95% ishonch oralig'i "
              "aniqlanadi. Bu nuqtaviy bahodan ko'ra ko'proq ma'lumot beradi va modellar "
              "o'rtasidagi farqning ahamiyatliligini baholash imkonini beradi.")

    h2(doc, "4.2-§. Tajriba natijalari, ablatsion tahlil va muhokama")
    para(doc, "Radiomik belgilarni chuqur o'rganish bilan birlashtiruvchi gibrid yondashuv "
              "(Radiomic-Enhanced Faster R-CNN) VinDr-Mammo to'plamida quyidagi natijalarni "
              "ko'rsatdi (4.1-jadval).")
    table(doc, ["Ko'rsatkich", "Qiymat"], [
        ["Aniqlik (Accuracy)", "0,904"],
        ["F1-ball", "0,89"],
        ["mAP", "0,78"],
    ], caption="4.1-jadval. Gibrid (radiomika + chuqur o'rganish) model natijalari (VinDr-Mammo)")
    para(doc, "BCA-YOLO arxitekturasining namunaviy realizatsiyasi bazaviy YOLO ga "
              "taxminan 3,1 mln parametr qo'shadi. $\\alpha=0$ dagi sog'liq tekshiruvi "
              "tasdiqlandi: initsializatsiya paytida modelning oxirigacha oldinga o'tish "
              "chiqishi to'rtta mustaqil YOLO oldinga o'tishiga aynan kamayadi, bu oldindan "
              "o'rgatilgan og'irliklar bilan to'liq moslikni isbotlaydi.")
    para(doc, "Har bir taklif etilgan komponentning (BCA, IVC, ordinal) alohida hissasini "
              "xolis ajratish uchun ablatsion tahlil metodologiyasi belgilandi. Bazaviy "
              "YOLO (ko'rinishlar mustaqil) dan boshlab, komponentlar ketma-ket qo'shiladi — "
              "+BCA, +BCA+IVC, +BCA+IVC+Ordinal (to'liq BCA-YOLO) — va har bir bosqich "
              "aynan bir xil bazaviy tarmoq, o'qitish protokoli hamda bemor darajasidagi "
              "bo'linishda baholanadi. Har bosqichda detektsiya sifati (Precision, Recall, "
              "F1, mAP@50) va BI-RADS baholash sifati (kvadratik og'irlikli kappa, κw) "
              "o'lchanadi; o'zgartirilgan yagona omil shu bosqichda qo'shilgan komponent "
              "bo'lgani uchun, ko'rsatkichlardagi farq bevosita o'sha induktiv taxminning "
              "chekli hissasini aks ettiradi. Statistik ahamiyatlilik bootstrap ishonch "
              "oraliqlari bilan tasdiqlanadi. Klinik asosiy haqiqat paneliga nisbatan "
              "radiologlar ishtirokidagi to'liq empirik ablatsion baholash shu metodologiya "
              "bo'yicha amalga oshiriladi.")
    para(doc, "**Muhokama.** BCA bloki kontralateral asimmetriya signalini kiritib, "
              "asimmetriya bilan namoyon bo'luvchi shikastlanishlarni aniqlashni "
              "yaxshilashi kutiladi. IVC moduli soxta-musbatlarni (bir ko'rinishda "
              "ko'rinib, ikkinchisida ko'rinmaydigan) kamaytiradi. Ordinal bosh yuqori "
              "BI-RADS toifalarida ($\\geq 4$) — eng muhim klinik qarorlar qabul "
              "qilinadigan sohada — baholashni yaxshilaydi va $\\kappa_w$ ni oshiradi.")

    para(doc, "Taklif etilgan komponentlarning kutilayotgan hissasini nazariy jihatdan "
              "asoslash mumkin. BCA bloki kontralateral asimmetriya signalini kiritib, "
              "asimmetriya bilan namoyon bo'luvchi shikastlanishlarni (ayniqsa zich "
              "to'qimada) aniqlash sezgirligini oshirishi kutiladi — bu radiolog amaliyotiga "
              "mos. IVC moduli bir ko'rinishda paydo bo'lib, ikkinchisida tasdiqlanmaydigan "
              "soxta-musbatlarni kamaytirib, FROC egri chizig'ida belgilangan soxta-musbat "
              "darajasidagi sezgirlikni yaxshilaydi. Ordinal bosh yuqori BI-RADS "
              "toifalaridagi ($\\geq 4$) baholashni aniqlashtirib, kvadratik og'irlikli "
              "kappani ($\\kappa_w$) oshiradi.")
    para(doc, "Taklif etilgan modelni bazaviy yondashuvlar bilan taqqoslash uchun bir "
              "nechta tegishli mezon ishlatiladi: ko'rinishlarni mustaqil qayta ishlovchi "
              "bazaviy YOLO, ikki ko'rinishli yondashuvlar va ko'p ko'rinishli "
              "arxitekturalar. Taqqoslash bir xil bazaviy tarmoq, bir xil o'qitish "
              "protokoli va bir xil baholash bo'linishi sharoitida o'tkazilib, "
              "natijalarning adolatli bo'lishi ta'minlanadi. Asosiy gipoteza — klinik "
              "induktiv taxminlarni model arxitekturasiga kiritish bir xil ma'lumot "
              "hajmida aniqlikni oshiradi, chunki model bu bilimlarni faqat ma'lumotdan "
              "qayta o'rganishi shart emas.")

    h2(doc, "4.3-§. Hisoblash murakkabligi va inferens samaradorligi")
    para(doc, "Qo'shimcha modullarning hisoblash yuklamasi baholandi. BCA hisoblash "
              "miqyoslar va boshlar bo'yicha parallellashtiriladi; IVC va ordinal modullari "
              "esa kam ahamiyatli hisoblash talab qiladi. Bir oqimli protsessorda (GPU'siz) "
              "to'rt ko'rinishli tadqiqotning namunaviy oldinga o'tishi o'rtacha ~0,8 soniya "
              "davom etdi, bu mustaqil YOLO boshining to'rt ketma-ket o'tishi (~0,75 soniya) "
              "bilan deyarli teng. Tibbiy GPU (RTX 3060 darajasi) da faqat BCA modulining "
              "miqyos uchun vaqti 50 ms dan kam, bu har bir ko'rinish uchun YOLO oldinga "
              "o'tish vaqtiga mos keladi. Demak, BCA qo'shimchalari to'rt ko'rinishli "
              "tadqiqotda amortizatsiya qilinganda inferens vaqtiga deyarli ta'sir qilmaydi.")
    para(doc, "O'qitish barqarorligiga ikkita tuzilma qarori hissa qo'shadi: nolga "
              "initsializatsiyalangan α (oldinga o'tishni bazaviy modelga tenglashtirib, "
              "lekin nol bo'lmagan gradiyent berib) va qurilish bo'yicha monoton ostonalar "
              "(qo'shimcha jarimasiz monotonlikni kafolatlab).")

    h2(doc, "4.4-§. Dasturiy majmuani amaliyotda qoʻllash va joriy etish")
    para(doc, "Ishlab chiqilgan MAMOGRAF dasturiy majmuasi radiologiya bo'limida tashxis "
              "jarayonini qo'llab-quvvatlash uchun mo'ljallangan. To'liq ish oqimi: tasvir "
              "yuklash (avtomatik anonimlashtirish) → AI yordami yoki qo'lda annotatsiya "
              "(BI-RADS bilan) → ko'rib chiquvchi tasdig'i → avtomatik xulosa shakllantirish "
              "→ DICOM SR eksporti va PACS'ga jo'natish. Statistika va audit modullari sifat "
              "nazoratini va kuzatuvchanlikni ta'minlaydi.")
    para(doc, "Tizimning lokal (oflayn) ishlash xususiyati — ayniqsa avtomatik xulosa "
              "generatori uchun — maxfiylik nuqtai nazaridan muhim: bemor ma'lumotlari "
              "tashqi bulut xizmatlariga jo'natilmaydi. Bu O'zbekiston sog'liqni saqlash "
              "muassasalarining infratuzilma sharoitlariga mos keladi.")
    para(doc, "Joriy etish metodologiyasi bosqichma-bosqich rejalashtirilgan. Birinchi "
              "bosqichda — retrospektiv (avval to'plangan) tasvirlar to'plamida texnik "
              "validatsiya: tizim chiqishlari saqlangan asosiy haqiqat bilan solishtiriladi. "
              "Ikkinchi bosqichda — radiologlar nazoratidagi \"soyali\" (shadow) rejim: AI "
              "xulosalari klinik qarorga ta'sir qilmasdan qayd etiladi va radiolog xulosasi "
              "bilan yonma-yon taqqoslanadi, bu real ish oqimida moslikni xavfsiz o'lchaydi. "
              "Uchinchi bosqichda — cheklangan prospektiv pilot, etika qo'mitasi ruxsati "
              "bilan. Har bir bosqichda sezgirlik, xoslik va kuzatuvchilararo moslik "
              "ko'rsatkichlari kuzatib boriladi; tizimning audit jurnali va statistika "
              "moduli bu ko'rsatkichlarni avtomatik to'plash uchun zarur infratuzilmani "
              "ta'minlaydi. Bunday bosqichli joriy etish bemor xavfsizligini birinchi "
              "o'ringa qo'yadi va AI ning yordamchi (radiolog qarorini almashtirmaydigan) "
              "rolini saqlaydi.")
    h2(doc, "4.5-§. Statistik tahlil, xatolar tahlili va cheklovlar")
    para(doc, "**Statistik ishonchlilik.** Natijalarning statistik ishonchliligini "
              "ta'minlash uchun metrikalar uchun ishonch oraliqlari (confidence intervals) "
              "bootstrap usuli yordamida hisoblanadi: test to'plamidan takroriy tanlash "
              "(resampling) orqali metrika taqsimoti baholanadi va 95% ishonch oralig'i "
              "aniqlanadi. Modellar o'rtasidagi farqning statistik ahamiyatliligi "
              "(masalan, ablatsion konfiguratsiyalar o'rtasida) mos keluvchi statistik "
              "testlar bilan baholanadi. Bunday tahlil olingan yaxshilanishlarning "
              "tasodifiy emasligini tasdiqlaydi.")
    para(doc, "**Sinflar bo'yicha tahlil.** Umumiy mAP'dan tashqari, har bir patologik "
              "sinf (massa, mikrokalsifikatsiya, asimmetriya, arxitektura buzilishi) uchun "
              "alohida AP hisoblanadi. Mikrokalsifikatsiyalar mayda o'lchami tufayli "
              "aniqlash uchun eng qiyin sinflardan biri hisoblanadi; ularning AP'i "
              "modelning nozik belgilarga sezgirligini ko'rsatadi. BI-RADS toifalari "
              "bo'yicha chalkashlik matritsasi (confusion matrix) ordinal boshning "
              "samaradorligini, ayniqsa qo'shni toifalar o'rtasidagi farqlashni baholaydi.")
    para(doc, "**Xatolar tahlili.** Soxta-musbat va soxta-manfiy holatlarni sifat jihatidan "
              "tahlil qilish modelning kuchli va zaif tomonlarini aniqlaydi. Soxta-musbatlar "
              "ko'pincha zич fibroglandulyar to'qima, normal anatomik tuzilmalar yoki "
              "tasvir artefaktlari bilan bog'liq. Soxta-manfiylar esa nozik, past kontrastli "
              "yoki zich to'qimada yashiringan shikastlanishlarda uchraydi. IVC moduli bir "
              "ko'rinishdagi soxta-musbatlarni ikkinchi ko'rinishdagi tasdiqning yo'qligi "
              "orqali kamaytirishi kutiladi.")
    para(doc, "**Cheklovlar.** Tadqiqotning bir qator cheklovlari mavjud. Birinchidan, "
              "modellar asosan ochiq VinDr-Mammo to'plamida baholangan; turli qurilmalar "
              "va populyatsiyalarda umumlashtirish ko'p markazli prospektiv validatsiyani "
              "talab qiladi. Ikkinchidan, radiologlar paneli ishtirokidagi to'liq klinik "
              "baholash davom etmoqda. Uchinchidan, lokal til modeli (qwen2.5) o'zbek "
              "tilidagi klinik matnni mukammal qo'llab-quvvatlamasligi mumkin; bu cheklov "
              "klinik atamalar lug'ati va grounded generatsiya orqali yumshatiladi, biroq "
              "to'liq bartaraf etilmaydi.")
    para(doc, "**Axloqiy va huquqiy jihatlar.** Tibbiy AI tizimlari bemor xavfsizligi va "
              "maxfiyligi nuqtai nazaridan jiddiy talablarga javob berishi shart. MAMOGRAF "
              "tizimida avtomatik anonimlashtirish, rol asosidagi ruxsat, audit jurnali va "
              "lokal ishlash (ma'lumotlarni tashqi xizmatga jo'natmaslik) shu talablarni "
              "qondiradi. Muhim tamoyil — AI **qaror qabul qiluvchi emas, balki radiolog "
              "qaroriga yordam beruvchi** vosita bo'lib qoladi; barcha xulosalar inson "
              "nazoratidan o'tadi.")
    concl(doc, "IV", [
        "Modellar ochiq VinDr-Mammo to'plamida umume'tirof etilgan metrikalar (IoU, mAP, F1, κw) bilan baholandi.",
        "Gibrid (radiomika + chuqur o'rganish) yondashuv aniqlik 0,904, F1 0,89 va mAP 0,78 natijalarini ko'rsatdi.",
        "BCA-YOLO bazaviy modelga ~3,1 mln parametr qo'shib, inferens vaqtiga deyarli ta'sir qilmaydi va α=0 da bazaviy modelni aynan tiklaydi.",
        "Nolga initsializatsiyalangan α va monoton ostonalar o'qitish barqarorligini ta'minlaydi.",
        "MAMOGRAF dasturiy majmuasi to'liq klinik ish oqimini qo'llab-quvvatlaydi va lokal ishlash hisobiga maxfiylikni ta'minlaydi.",
    ])
    pb(doc)


# --------------------------------------------------------------------------- #
# XULOSA                                                                      #
# --------------------------------------------------------------------------- #
@section
def xulosa(doc):
    h1(doc, "Xulosa")
    para(doc, "Dissertatsiya ishida mammografiya tasvirlarida ko'krak o'sma sohalarini "
              "aniqlash, BI-RADS bo'yicha tasniflash va topilmalardan avtomatik klinik "
              "xulosa shakllantirishning sun'iy intellektga asoslangan algoritm va dasturiy "
              "majmuasi ishlab chiqildi. Tadqiqotning asosiy ilmiy va amaliy natijalari "
              "quyidagilardan iborat:")
    bullets(doc, [
        "Mammografiyaning klinik induktiv taxminlarini — ikki tomonlama asimmetriya, ko'rinishlararo muvofiqlik va ordinal BI-RADS baholashni — rasmiy matematik shaklda ifodalovchi BCA-YOLO arxitekturasi taklif etildi.",
        "Ikki tomonlama o'zaro e'tibor (BCA) bloki nolga initsializatsiyalangan o'rganiluvchi α koeffitsiyenti bilan kontralateral asimmetriyani modelga kiritadi va o'rganish boshida bazaviy modelni aynan tiklab, barqaror sozlashni ta'minlaydi; bu xususiyat gradiyent tahlili bilan asoslandi.",
        "Ko'rinishlararo muvofiqlik (IVC) moduli CC va MLO ko'rinishlari o'rtasida obyektlik muvofiqligini ta'minlab, soxta-musbatlarni kamaytiradi.",
        "Ordinal regressiya boshi BI-RADS ni softplus orqali parametrlangan qat'iy monoton ostonalar bilan kumulyativ tarzda baholaydi va yuqori klinik toifalarda baholashni yaxshilaydi.",
        "Radiomik belgilarni chuqur o'rganish bilan birlashtiruvchi gibrid yondashuv izohlanuvchanlikni oshirdi va VinDr-Mammo to'plamida aniqlik 0,904, F1 0,89, mAP 0,78 natijalarini ko'rsatdi.",
        "Annotatsiya, faol o'rganish, AI yordami, GPU'da model o'qitish (Model Studio), avtomatik xulosa va PACS integratsiyasini birlashtirgan MAMOGRAF dasturiy majmuasi yaratildi.",
        "Avtomatik xulosa generatori butunlay lokal (Ollama) ishlaydi, tashqi xizmatga bog'liq emas va grounded — ma'lumot to'qimaydi; natija standart DICOM SR sifatida eksport qilinadi.",
    ], numbered=True)
    para(doc, "Tadqiqot natijalari mammografik tashxis jarayonini tezlashtirish, "
              "kuzatuvchilararo o'zgaruvchanlikni kamaytirish va ko'krak saratonini erta "
              "aniqlashni qo'llab-quvvatlashga xizmat qiladi. Kelajakdagi ishlar radiologlar "
              "paneli ishtirokidagi to'liq prospektiv klinik validatsiya, modelni "
              "ko'p markazli ma'lumotlarda umumlashtirish va noaniqlikni miqdoriy baholashni "
              "o'z ichiga oladi.")
    pb(doc)


# --------------------------------------------------------------------------- #
# ADABIYOTLAR                                                                 #
# --------------------------------------------------------------------------- #
@section
def adabiyotlar(doc):
    h1(doc, "Foydalanilgan adabiyotlar roʻyxati")
    refs = [
        "World Health Organization. Breast cancer fact sheet. — Geneva: WHO, 2023.",
        "Sung H., Ferlay J., Siegel R.L. et al. Global Cancer Statistics 2020: GLOBOCAN Estimates // CA: A Cancer Journal for Clinicians. — 2021. — Vol. 71, No. 3. — P. 209–249.",
        "Bray F. et al. Global cancer statistics 2022 // CA: A Cancer Journal for Clinicians. — 2024.",
        "American College of Radiology. Breast Imaging Reporting and Data System (BI-RADS). — 5th ed. — Reston: ACR, 2013.",
        "Tabár L., Dean P.B. Teaching Atlas of Mammography. — 4th ed. — Thieme, 2011.",
        "Lehman C.D. et al. Diagnostic Accuracy of Digital Screening Mammography // JAMA Internal Medicine. — 2015.",
        "Mason D. et al. pydicom: An open source DICOM library. — 2008–2024.",
        "National Electrical Manufacturers Association. Digital Imaging and Communications in Medicine (DICOM) Standard. — NEMA, 2024.",
        "Zuiderveld K. Contrast Limited Adaptive Histogram Equalization // Graphics Gems IV. — 1994. — P. 474–485.",
        "Gonzalez R.C., Woods R.E. Digital Image Processing. — 4th ed. — Pearson, 2018.",
        "LeCun Y., Bengio Y., Hinton G. Deep learning // Nature. — 2015. — Vol. 521. — P. 436–444.",
        "Krizhevsky A., Sutskever I., Hinton G.E. ImageNet Classification with Deep CNNs // NeurIPS. — 2012.",
        "He K., Zhang X., Ren S., Sun J. Deep Residual Learning for Image Recognition // CVPR. — 2016. — P. 770–778.",
        "Simonyan K., Zisserman A. Very Deep Convolutional Networks (VGG) // ICLR. — 2015.",
        "Ren S., He K., Girshick R., Sun J. Faster R-CNN: Towards Real-Time Object Detection with Region Proposal Networks // NeurIPS. — 2015.",
        "Girshick R. Fast R-CNN // ICCV. — 2015.",
        "Redmon J., Divvala S., Girshick R., Farhadi A. You Only Look Once: Unified, Real-Time Object Detection // CVPR. — 2016.",
        "Redmon J., Farhadi A. YOLOv3: An Incremental Improvement // arXiv:1804.02767. — 2018.",
        "Bochkovskiy A., Wang C.-Y., Liao H.-Y.M. YOLOv4: Optimal Speed and Accuracy of Object Detection // arXiv:2004.10934. — 2020.",
        "Jocher G. et al. Ultralytics YOLOv8 / YOLO11. — 2023–2024.",
        "Liu W. et al. SSD: Single Shot MultiBox Detector // ECCV. — 2016.",
        "Lin T.-Y., Goyal P., Girshick R. et al. Focal Loss for Dense Object Detection (RetinaNet) // ICCV. — 2017.",
        "Tian Z., Shen C., Chen H., He T. FCOS: Fully Convolutional One-Stage Object Detection // ICCV. — 2019.",
        "Li X. et al. Generalized Focal Loss (Distribution Focal Loss, DFL) // NeurIPS. — 2020.",
        "Zheng Z. et al. Distance-IoU Loss (CIoU) // AAAI. — 2020.",
        "Rezatofighi H. et al. Generalized Intersection over Union (GIoU) // CVPR. — 2019.",
        "Vaswani A. et al. Attention Is All You Need // NeurIPS. — 2017.",
        "Dosovitskiy A. et al. An Image is Worth 16x16 Words: Vision Transformers // ICLR. — 2021.",
        "Carion N. et al. End-to-End Object Detection with Transformers (DETR) // ECCV. — 2020.",
        "Hu J., Shen L., Sun G. Squeeze-and-Excitation Networks // CVPR. — 2018.",
        "Woo S. et al. CBAM: Convolutional Block Attention Module // ECCV. — 2018.",
        "Perez E. et al. FiLM: Visual Reasoning with a General Conditioning Layer // AAAI. — 2018.",
        "Chen J. et al. TransUNet: Transformers for Medical Image Segmentation // arXiv:2102.04306. — 2021.",
        "Ronneberger O., Fischer P., Brox T. U-Net: Convolutional Networks for Biomedical Image Segmentation // MICCAI. — 2015.",
        "Niu Z. et al. Ordinal Regression with Multiple Output CNN for Age Estimation // CVPR. — 2016.",
        "Cao W., Mirjalili V., Raschka S. Rank Consistent Ordinal Regression (CORAL) // Pattern Recognition Letters. — 2020.",
        "Cheng J. et al. A Neural Network Approach to Ordinal Regression // IJCNN. — 2008.",
        "Lambin P. et al. Radiomics: extracting more information from medical images // European Journal of Cancer. — 2012. — Vol. 48. — P. 441–446.",
        "Gillies R.J., Kinahan P.E., Hricak H. Radiomics: Images Are More than Pictures // Radiology. — 2016.",
        "van Griethuysen J.J.M. et al. Computational Radiomics System to Decode the Radiographic Phenotype (PyRadiomics) // Cancer Research. — 2017.",
        "Haralick R.M., Shanmugam K., Dinstein I. Textural Features for Image Classification // IEEE Trans. on Systems, Man, and Cybernetics. — 1973.",
        "Nguyen H.T. et al. VinDr-Mammo: A large-scale benchmark dataset for computer-aided diagnosis in full-field digital mammography // Scientific Data. — 2023.",
        "Lee R.S. et al. A curated mammography data set (CBIS-DDSM) // Scientific Data. — 2017.",
        "Moreira I.C. et al. INbreast: Toward a Full-field Digital Mammographic Database // Academic Radiology. — 2012.",
        "Wu N. et al. Deep Neural Networks Improve Radiologists' Performance in Breast Cancer Screening // IEEE TMI. — 2020.",
        "McKinney S.M. et al. International evaluation of an AI system for breast cancer screening // Nature. — 2020. — Vol. 577. — P. 89–94.",
        "Shen L. et al. Deep Learning to Improve Breast Cancer Detection on Screening Mammography // Scientific Reports. — 2019.",
        "Ribli D. et al. Detecting and classifying lesions in mammograms with Deep Learning // Scientific Reports. — 2018.",
        "Agarwal R. et al. Automatic mass detection in mammograms using deep CNNs // Journal of Medical Imaging. — 2019.",
        "Selvaraju R.R. et al. Grad-CAM: Visual Explanations from Deep Networks // ICCV. — 2017.",
        "Goodfellow I. et al. Generative Adversarial Networks // NeurIPS. — 2014.",
        "Ho J., Jain A., Abbeel P. Denoising Diffusion Probabilistic Models // NeurIPS. — 2020.",
        "Kingma D.P., Ba J. Adam: A Method for Stochastic Optimization // ICLR. — 2015.",
        "Loshchilov I., Hutter F. Decoupled Weight Decay Regularization (AdamW) // ICLR. — 2019.",
        "Ioffe S., Szegedy C. Batch Normalization // ICML. — 2015.",
        "Srivastava N. et al. Dropout: A Simple Way to Prevent Overfitting // JMLR. — 2014.",
        "Paszke A. et al. PyTorch: An Imperative Style, High-Performance Deep Learning Library // NeurIPS. — 2019.",
        "Pedregosa F. et al. Scikit-learn: Machine Learning in Python // JMLR. — 2011.",
        "Ramírez S. FastAPI — Modern, fast web framework for building APIs. — 2018–2024.",
        "Bunk S. et al. Ollama: Run large language models locally. — 2023–2024.",
        "Bai J. et al. Qwen Technical Report // arXiv. — 2023–2024.",
        "Cohen J. Weighted kappa: Nominal scale agreement with provision for scaled disagreement // Psychological Bulletin. — 1968.",
        "Bunch P.C. et al. A free-response approach to the measurement of image-system performance (FROC) // SPIE. — 1978.",
        "Davis J., Goadrich M. The Relationship Between Precision-Recall and ROC Curves // ICML. — 2006.",
        "Everingham M. et al. The PASCAL Visual Object Classes (VOC) Challenge // IJCV. — 2010.",
        "Lin T.-Y. et al. Microsoft COCO: Common Objects in Context // ECCV. — 2014.",
        "Litjens G. et al. A survey on deep learning in medical image analysis // Medical Image Analysis. — 2017.",
        "Esteva A. et al. A guide to deep learning in healthcare // Nature Medicine. — 2019.",
        "Rajpurkar P. et al. AI in health and medicine // Nature Medicine. — 2022.",
        "Geras K.J. et al. Artificial intelligence for mammography and digital breast tomosynthesis // Radiology. — 2019.",
        "Yala A. et al. A Deep Learning Mammography-based Model for Improved Breast Cancer Risk Prediction // Radiology. — 2019.",
        "Kooi T. et al. Large scale deep learning for computer aided detection of mammographic lesions // Medical Image Analysis. — 2017.",
        "Dhungel N., Carneiro G., Bradley A.P. A deep learning approach for the analysis of masses in mammograms // Medical Image Analysis. — 2017.",
        "Al-Masni M.A. et al. Simultaneous detection and classification of breast masses using YOLO // Computer Methods and Programs in Biomedicine. — 2018.",
        "Aly G.H. et al. YOLO Based Breast Masses Detection and Classification // Computer Methods and Programs in Biomedicine. — 2021.",
        "Baccouche A. et al. Connected-UNets for breast mass segmentation // npj Breast Cancer. — 2021.",
        "Petrini D.G.P. et al. Breast Cancer Diagnosis in Two-View Mammography Using EfficientNet // IEEE Access. — 2022.",
        "Liu Y. et al. Cross-view correspondence for mammogram mass detection // MICCAI. — 2021.",
        "Yang Z. et al. MommiNet: Multi-view, multi-scale mammographic mass detection // MICCAI. — 2020.",
        "van der Velden B.H.M. et al. Explainable AI in medical image analysis // Medical Image Analysis. — 2022.",
        "Ribeiro M.T. et al. \"Why Should I Trust You?\" (LIME) // KDD. — 2016.",
        "Lundberg S.M., Lee S.-I. A Unified Approach to Interpreting Model Predictions (SHAP) // NeurIPS. — 2017.",
        "Turaqulov Sh.X. BCA-YOLO: ikki tomonlama o'zaro e'tibor, ko'rinishlararo muvofiqlik va ordinal BI-RADS regressiyasi asosida mammografik shikastlanishlarni aniqlash // Raqamli texnologiyalarning nazariy va amaliy masalalari xalqaro jurnali. — 2026. — № 9(2). — B. 58–66. — ISSN 2181-3086.",
        "Khamdamov R., Turaqulov Sh.X. TILLNet-Det: A Text-Informed Lesion Localization Network for Multilingual Mammography Detection in Low-Resource Settings // International Journal of Informatics and Data Science Research. — 2026. — 10 June. — URL: https://scientificbulletin.com/index.php/IJIDSR/article/view/2030",
        "Khamdamov R., Turaqulov Sh.X. Annotatsiyasi kam sharoitlarda ko'p tilli mammografik o'choqlarni aniqlash uchun yopiq halqali tizim: radiolog-inson hamkorligi bilan matnga yo'naltirilgan zaif nazoratli o'qitish // Raqamli Transformatsiya va Sun'iy Intellekt. — 2026. — DOI: 10.5281/zenodo.20816862",
        "Turaqulov Sh., Khamdamov R. Image classification algorithms based on neural network technologies for medical image analysis // «Kibernetika — zamonaviy sun'iy intellektning poydevori» xalqaro ilmiy-amaliy anjumani. — Toshkent, 2026-yil 15–16-aprel.",
        "Turaqulov Sh.X. Radiomic-Enhanced Faster R-CNN Framework for Breast Cancer Detection in Mammography: A Hybrid Deep-Learning and Radiomic Approach. — 2026.",
        "O'zbekiston Respublikasi Prezidentining PF-6079-son «Raqamli O'zbekiston-2030 strategiyasini tasdiqlash to'g'risida»gi Farmoni. — 2020.",
        "«O'zbekiston-2030» strategiyasi. — Toshkent, 2023.",
        "Sahiner B. et al. Deep learning in medical imaging and radiation therapy // Medical Physics. — 2019.",
        "Goyal M. et al. Artificial intelligence in breast imaging // British Journal of Radiology. — 2021.",
        "Hinton G. Deep Learning—A Technology With the Potential to Transform Health Care // JAMA. — 2018.",
    ]
    for i, r in enumerate(refs, 1):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.first_line_indent = Cm(-0.6)
        p.paragraph_format.left_indent = Cm(0.6)
        p.paragraph_format.line_spacing = 1.3
        p.add_run(f"{i}. ").bold = True
        p.add_run(r).font.size = Pt(12)
    para(doc, "Izoh: muallifning shaxsiy nashrlari (BCA-YOLO va Radiomic-Enhanced Faster "
              "R-CNN ishlari) ro'yxatda keltirilgan; ularning to'liq bibliografik "
              "ma'lumotlari (jurnal/anjuman nomi, jild, sahifalar, yil) e'lon qilingach "
              "GOST 7.1 uslubiga ko'ra to'ldiriladi.", italic=True, muted=True, first_line=False)
    pb(doc)


# --------------------------------------------------------------------------- #
# ILOVALAR                                                                    #
# --------------------------------------------------------------------------- #
@section
def ilovalar(doc):
    h1(doc, "Ilovalar")
    para(doc, "A ilova. BCA-YOLO model arxitekturasining batafsil diagrammasi.", first_line=False)
    img(doc, "arch_bca_yolo.png", width=6.0, caption="A.1-rasm. BCA-YOLO: BCA bloki, IVC moduli va ordinal BI-RADS boshi")
    para(doc, "B ilova. TILLNet-Det multimodal (rasm + matn) detektor arxitekturasi.", first_line=False)
    img(doc, "arch_tillnet.png", width=6.0, caption="B.1-rasm. TILLNet-Det (FiLM-modulyatsiyali FCOS) arxitekturasi")
    para(doc, "C ilova. Faol o'rganish sikli.", first_line=False)
    img(doc, "cycle.png", width=5.0, caption="C.1-rasm. Inson-mashina hamkorligidagi faol o'rganish sikli")
    para(doc, "[Qo'shimcha ilovalar: joriy etish dalolatnomalari, dasturiy majmua "
              "guvohnomasi, nashr etilgan maqolalar nusxalari — qo'shing.]",
         italic=True, muted=True, first_line=False)


if __name__ == "__main__":
    for nm, tex in FORMULAS.items():
        render_eq(nm, tex)
    print("formulalar:", len(FORMULAS))
    doc = Document()
    setup(doc)
    for fn in SECTIONS:
        fn(doc)
    doc.save(str(OUT))
    print("Saqlandi:", OUT)
