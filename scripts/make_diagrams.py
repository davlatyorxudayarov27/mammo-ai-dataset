# -*- coding: utf-8 -*-
"""MAMOGRAF hujjati uchun diagrammalar (PNG) generatori — matplotlib."""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUT = Path(__file__).resolve().parent.parent / "doc_assets"
OUT.mkdir(exist_ok=True)

ACCENT = "#0E7490"     # teal (asosiy)
ACCENT2 = "#06B6D4"    # cyan (urg'u)
LIGHT = "#CFF0F5"      # och teal (quticha foni)
GREEN = "#22A35A"
YELLOW = "#E0A800"
RED = "#D63B3B"
GREY = "#6B7280"
DARK = "#103A40"       # quyuq teal-grafit (matn)
PURPLE = "#7A4FB0"

plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["font.size"] = 11


def _box(ax, x, y, w, h, text, fc=LIGHT, ec=ACCENT, tc=DARK, fs=11, bold=True, round_=0.025):
    p = FancyBboxPatch((x, y), w, h,
                       boxstyle=f"round,pad=0.01,rounding_size={round_}",
                       linewidth=1.6, edgecolor=ec, facecolor=fc, mutation_aspect=1)
    ax.add_patch(p)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fs, color=tc, fontweight=("bold" if bold else "normal"),
            wrap=True)


def _arrow(ax, x1, y1, x2, y2, color=ACCENT, lw=2.2, style="-|>", rad=0.0, ls="-"):
    a = FancyArrowPatch((x1, y1), (x2, y2),
                        arrowstyle=style, mutation_scale=18,
                        linewidth=lw, color=color,
                        connectionstyle=f"arc3,rad={rad}", linestyle=ls)
    ax.add_patch(a)


# ---------------------------------------------------------------------------
# 1. To'liq tsikl — Active Learning Loop
# ---------------------------------------------------------------------------
def diagram_cycle():
    fig, ax = plt.subplots(figsize=(11, 5.2))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 50)
    ax.axis("off")

    stages = [
        ("1. UPLOAD\nDICOM yuklash\n+ avto de-identify", LIGHT),
        ("2. AUTO-AI\nYOLO inference\n+ ishonch zonalari", "#FCE9C9"),
        ("3. ANNOTATION\nRadiolog\ntekshiradi /\ntahrirlaydi", "#D6EAD9"),
        ("4. DATASET\nYOLO format\n(img + labels\n+ data.yaml)", LIGHT),
        ("5. YANGI MODEL\nYOLO o'qitish\n+ deploy", "#E6D6F2"),
    ]
    n = len(stages)
    w, h = 16.5, 13
    gap = (100 - n * w) / (n + 1)
    y = 28
    centers = []
    for i, (txt, fc) in enumerate(stages):
        x = gap + i * (w + gap)
        _box(ax, x, y, w, h, txt, fc=fc, fs=9.5)
        centers.append((x + w / 2, y))
        if i < n - 1:
            _arrow(ax, x + w + 0.6, y + h / 2, x + w + gap - 0.6, y + h / 2)

    # Active-learning return arrow: 5 -> 2
    x5 = centers[-1][0]
    x2 = centers[1][0]
    _arrow(ax, x5, y - 0.4, x2, y - 0.4, color=GREEN, lw=2.6, rad=-0.45, ls="--")
    ax.text((x5 + x2) / 2, 9.5,
            "AKTIV O'QITISH (Active Learning) — har ~50 yangi annotation'da qayta o'qitiladi",
            ha="center", va="center", fontsize=10.5, color=GREEN, fontweight="bold")

    ax.text(50, 47, "MAMOGRAF — to'liq ish tsikli (yopiq sikl)",
            ha="center", va="center", fontsize=15, color=ACCENT, fontweight="bold")
    fig.savefig(OUT / "cycle.png", dpi=170, bbox_inches="tight", facecolor="white")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 2. Tizim arxitekturasi (qatlamli)
# ---------------------------------------------------------------------------
def diagram_architecture():
    fig, ax = plt.subplots(figsize=(11, 7.4))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    ax.text(50, 97, "MAMOGRAF — tizim arxitekturasi", ha="center", va="center",
            fontsize=15, color=ACCENT, fontweight="bold")

    # Layer 1: Frontend
    _box(ax, 4, 80, 92, 12, "", fc="#F3F7FC", ec=ACCENT, round_=0.02)
    ax.text(7, 90, "FRONTEND (statik UI — HTML/JS/CSS)", ha="left", va="center",
            fontsize=10, color=ACCENT, fontweight="bold")
    for i, t in enumerate(["DICOM\nko'ruvchi", "Annotatsiya\n(bbox/polygon)", "AI taklif\nko'rinishi", "Model Studio\n(o'qitish)", "PACS / Worklist"]):
        _box(ax, 7 + i * 18, 81.5, 15.5, 5.6, t, fc="#FFFFFF", ec=GREY, tc=DARK, fs=8.5, bold=False)

    # Layer 2: API
    _box(ax, 4, 64, 92, 11, "", fc="#EAF1FA", ec=ACCENT, round_=0.02)
    ax.text(7, 73, "BACKEND — FastAPI (REST API + WebSocket)", ha="left", va="center",
            fontsize=10, color=ACCENT, fontweight="bold")
    for i, t in enumerate(["Upload /\nFiles", "Annotations /\nStatus", "Training\nprepare/run", "Inference\nrun/batch", "Auth\nJWT+TOTP"]):
        _box(ax, 7 + i * 18, 65, 15.5, 5.2, t, fc="#FFFFFF", ec=GREY, tc=DARK, fs=8.5, bold=False)

    # Layer 3: AI / processing
    _box(ax, 4, 44, 92, 15, "", fc="#F2ECF8", ec="#7A4FB0", round_=0.02)
    ax.text(7, 57, "AI / QAYTA ISHLASH QATLAMI", ha="left", va="center",
            fontsize=10, color="#7A4FB0", fontweight="bold")
    ai = ["BCA-YOLO\n(deteksiya)", "TILLNet-Det\n(matn+vizual)", "XS-Classifier\n(hisobot)", "Radiomics\n(GLCM/GLRLM..)", "Inference\nWBF+TTA"]
    for i, t in enumerate(ai):
        _box(ax, 7 + i * 18, 46, 15.5, 8.5, t, fc="#FFFFFF", ec="#7A4FB0", tc=DARK, fs=8.5, bold=False)

    # Layer 4: Data / storage / external
    _box(ax, 4, 24, 92, 15, "", fc="#EDEFF2", ec=GREY, round_=0.02)
    ax.text(7, 37, "MA'LUMOT VA INTEGRATSIYA", ha="left", va="center",
            fontsize=10, color=DARK, fontweight="bold")
    data = ["uploads/\n(DICOM)", "annotations/\n(JSON)", "SQLite DB\n(metama'lumot)", "De-identify\n(PHI tozalash)", "PACS\nC-FIND/STORE", "Eksport\nYOLO/VOC/SEG/SR"]
    for i, t in enumerate(data):
        _box(ax, 6 + i * 15, 26, 13.5, 8.5, t, fc="#FFFFFF", ec=GREY, tc=DARK, fs=8, bold=False)

    # connecting arrows between layers
    for cx in (20, 50, 80):
        _arrow(ax, cx, 80, cx, 75.3, color=ACCENT, lw=1.6)
        _arrow(ax, cx, 64, cx, 59.3, color="#7A4FB0", lw=1.6)
        _arrow(ax, cx, 44, cx, 39.3, color=GREY, lw=1.6)

    # Security footer
    _box(ax, 4, 14, 92, 7, "Xavfsizlik: JWT autentifikatsiya · TOTP 2FA · rate-limit (slowapi) · audit jurnali · avtomatik PHI de-identifikatsiya",
         fc="#FDECEC", ec=RED, tc=DARK, fs=9, bold=False, round_=0.02)

    fig.savefig(OUT / "architecture.png", dpi=170, bbox_inches="tight", facecolor="white")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 3. Ishonch zonalari
# ---------------------------------------------------------------------------
def diagram_zones():
    fig, ax = plt.subplots(figsize=(10, 2.8))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 30)
    ax.axis("off")

    # gradient-like bar split into 4 zones by threshold
    zones = [
        (0, 20, "#9AA0A6", "conf < 0.20\nTASHLANADI", 8.5),
        (20, 40, RED, "0.20–0.40\nSHUBHALI\nai_suspect", 8.0),
        (40, 85, YELLOW, "0.40–0.85\nKO'RIB CHIQISH (sariq)\nai_review", 8.5),
        (85, 100, GREEN, "≥ 0.85\nAVTO-QABUL\nai_accepted", 7.6),
    ]
    for x0, x1, c, label, fs in zones:
        ax.add_patch(FancyBboxPatch((x0, 8), x1 - x0 - 0.4, 10,
                                    boxstyle="round,pad=0.01,rounding_size=0.5",
                                    linewidth=0, facecolor=c, alpha=0.9))
        ax.text((x0 + x1) / 2, 13, label, ha="center", va="center",
                fontsize=fs, color="white", fontweight="bold")

    # axis ticks
    for t in (0.20, 0.40, 0.85):
        ax.plot([t * 100, t * 100], [6.5, 8], color=DARK, lw=1)
        ax.text(t * 100, 5, f"{t:.2f}", ha="center", va="top", fontsize=9, color=DARK)
    ax.text(50, 23, "AI ishonch (confidence) zonalari", ha="center", va="center",
            fontsize=13, color=ACCENT, fontweight="bold")
    ax.annotate("", xy=(100, 7), xytext=(0, 7),
                arrowprops=dict(arrowstyle="-|>", color=DARK, lw=1.4))
    ax.text(99, 3.2, "ishonch →", ha="right", va="top", fontsize=8.5, color=GREY)

    fig.savefig(OUT / "zones.png", dpi=170, bbox_inches="tight", facecolor="white")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 4. Stepper — taqdimot uchun (aktiv bosqich ajratilgan)
# ---------------------------------------------------------------------------
def diagram_stepper(active: int):
    """active: 1..5 — qaysi bosqich yoritiladi."""
    labels = ["1\nUPLOAD", "2\nAUTO-AI", "3\nANNOTATION",
              "4\nDATASET", "5\nYANGI MODEL"]
    fills = [LIGHT, "#FCE9C9", "#D6EAD9", LIGHT, "#E6D6F2"]
    fig, ax = plt.subplots(figsize=(12, 1.5))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 18)
    ax.axis("off")
    n = len(labels)
    w, h = 16.5, 12
    gap = (100 - n * w) / (n + 1)
    y = 3
    for i, txt in enumerate(labels):
        x = gap + i * (w + gap)
        is_on = (i + 1) == active
        fc = fills[i] if is_on else "#EEEEEE"
        ec = ACCENT if is_on else "#C8C8C8"
        tc = DARK if is_on else "#A0A0A0"
        _box(ax, x, y, w, h, txt, fc=fc, ec=ec, tc=tc,
             fs=12 if is_on else 10.5, round_=0.03)
        if is_on:
            FancyBboxPatch  # noqa
            ax.add_patch(FancyBboxPatch((x - 0.6, y - 0.6), w + 1.2, h + 1.2,
                         boxstyle="round,pad=0.01,rounding_size=0.03",
                         linewidth=2.6, edgecolor=ACCENT, facecolor="none"))
        if i < n - 1:
            _arrow(ax, x + w + 0.5, y + h / 2, x + w + gap - 0.5, y + h / 2,
                   color="#B0B0B0", lw=1.8)
    fig.savefig(OUT / f"stepper_{active}.png", dpi=170,
                bbox_inches="tight", facecolor="white")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 5. BCA-YOLO arxitekturasi
# ---------------------------------------------------------------------------
def diagram_bca_yolo():
    fig, ax = plt.subplots(figsize=(12, 5.4))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 52)
    ax.axis("off")
    ax.text(50, 50, "BCA-YOLO — Bilateral Cross-Attention YOLO",
            ha="center", va="center", fontsize=15, color=ACCENT, fontweight="bold")
    ax.text(50, 45.5, "Ikki tomonlama (chap/o'ng) assimetriyani hisobga oluvchi mammografik o'choq detektori",
            ha="center", va="center", fontsize=10, color=GREY)

    # 1. Input: 4 views
    views = ["L-CC", "R-CC", "L-MLO", "R-MLO"]
    for i, v in enumerate(views):
        _box(ax, 2, 33 - i * 7.2, 11, 5.6, v, fc=LIGHT, ec=ACCENT, fs=10)
    ax.text(7.5, 41, "4 ko'rinish\n1×H×W", ha="center", va="center",
            fontsize=8.5, color=GREY)

    # 2. Backbone
    _box(ax, 19, 14, 14, 24, "Umumiy\nYOLO backbone\nΦ", fc="#E6F6FA", ec=ACCENT, fs=11)
    for i in range(4):
        _arrow(ax, 13, 35.8 - i * 7.2, 19, 26, color=ACCENT, lw=1.4)
    ax.text(26, 11.5, "ko'p masshtabli\nxususiyatlar F_v", ha="center", va="center",
            fontsize=8.5, color=GREY)

    # 3. BCA
    _box(ax, 39, 24, 16, 12, "Bilateral\nCross-Attention\n(BCA)", fc="#D6EFF5", ec=ACCENT2, fs=10.5)
    ax.text(47, 21, "chap↔o'ng, mirror(R)\nassimetriya", ha="center", va="center",
            fontsize=8, color=GREY)
    _arrow(ax, 33, 26, 39, 30, color=ACCENT, lw=2)

    # 4. IVC
    _box(ax, 61, 24, 16, 12, "Inter-View\nConsistency\n(IVC)", fc="#D6EFF5", ec=ACCENT2, fs=10.5)
    ax.text(69, 21, "CC + MLO →\nhar tomon", ha="center", va="center",
            fontsize=8, color=GREY)
    _arrow(ax, 55, 30, 61, 30, color=ACCENT, lw=2)

    # 5. Heads
    _box(ax, 83, 30, 15, 8, "Deteksiya\nboshlari", fc="#FCE9C9", ec="#C98A1E", fs=9.5)
    _box(ax, 83, 18, 15, 9, "Ordinal BI-RADS\nregressiya\n(cumulative link)", fc="#E6D6F2", ec=PURPLE, fs=9)
    _arrow(ax, 77, 31, 83, 34, color=ACCENT, lw=2)
    _arrow(ax, 77, 29, 83, 23, color=ACCENT, lw=2)

    fig.savefig(OUT / "arch_bca_yolo.png", dpi=170, bbox_inches="tight", facecolor="white")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 6. TILLNet-Det arxitekturasi
# ---------------------------------------------------------------------------
def diagram_tillnet():
    fig, ax = plt.subplots(figsize=(12, 5.6))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 54)
    ax.axis("off")
    ax.text(50, 52, "TILLNet-Det — Text-Informed Lesion Localisation Network",
            ha="center", va="center", fontsize=15, color=ACCENT, fontweight="bold")
    ax.text(50, 47.5, "Radiologiya hisobotini (matnni) vizual xususiyatlar piramidasiga shartlashtiruvchi multimodal detektor",
            ha="center", va="center", fontsize=9.5, color=GREY)

    # Vizual tarmoq (yuqori)
    _box(ax, 2, 33, 14, 8, "Mammogram\n(tasvir)", fc=LIGHT, ec=ACCENT, fs=10)
    _box(ax, 20, 33, 14, 8, "Backbone\n(ResNet-50)", fc="#E6F6FA", ec=ACCENT, fs=10)
    _box(ax, 38, 33, 14, 8, "FPN\n(P3…P7)", fc="#E6F6FA", ec=ACCENT, fs=10)
    _arrow(ax, 16, 37, 20, 37, color=ACCENT, lw=2)
    _arrow(ax, 34, 37, 38, 37, color=ACCENT, lw=2)

    # Matn tarmog'i (past)
    _box(ax, 2, 11, 14, 8, "Radiologiya\nhisoboti (matn)", fc="#FCE9C9", ec="#C98A1E", fs=9.5)
    _box(ax, 20, 11, 14, 8, "Cross-script\nchar-token\nembedding", fc="#FCE9C9", ec="#C98A1E", fs=9)
    _box(ax, 38, 11, 14, 8, "4-qatlamli\nTransformer", fc="#FCE9C9", ec="#C98A1E", fs=9.5)
    _arrow(ax, 16, 15, 20, 15, color="#C98A1E", lw=2)
    _arrow(ax, 34, 15, 38, 15, color="#C98A1E", lw=2)
    ax.text(45, 7.5, "semantik vektor  t", ha="center", va="center",
            fontsize=9, color="#C98A1E", fontweight="bold")

    # FiLM birlashma
    _box(ax, 58, 22, 18, 12, "FiLM modulyatsiya\nγ,β = MLP(t)\nP' = (1+γ)·P + β",
         fc="#D6EFF5", ec=ACCENT2, fs=9.5)
    _arrow(ax, 52, 37, 58, 31, color=ACCENT, lw=2)          # FPN -> FiLM
    _arrow(ax, 52, 15, 58, 25, color="#C98A1E", lw=2)        # t -> FiLM

    # FCOS head
    _box(ax, 81, 21, 17, 14,
         "Anchor-free\nFCOS head\n• classification\n• regression (l,t,r,b)\n• centerness",
         fc="#E6D6F2", ec=PURPLE, fs=8.5)
    _arrow(ax, 76, 28, 81, 28, color=ACCENT, lw=2)

    # Output
    ax.text(89.5, 17, "→ o'choq bbox + class", ha="center", va="center",
            fontsize=9, color=ACCENT, fontweight="bold")

    fig.savefig(OUT / "arch_tillnet.png", dpi=170, bbox_inches="tight", facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    diagram_cycle()
    diagram_architecture()
    diagram_zones()
    diagram_bca_yolo()
    diagram_tillnet()
    for i in range(1, 6):
        diagram_stepper(i)
    print("Diagrammalar saqlandi:", OUT)
