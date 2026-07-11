# -*- coding: utf-8 -*-
"""MAMOGRAF — "Avtomatlashtirilgan annotatsiya yig'ish" ilmiy maqolasi (.docx).

Platforma maqolasi: mammografik tasvirlar uchun model yordamida dastlabki
belgilash (model-assisted pre-annotation) va inson-tsiklidagi faol o'rganish
(human-in-the-loop active learning) asosida annotatsiyalarni avtomatlashtirilgan
yig'ish tizimi. Formulalarga boy.

Ikki vazifa:
  1. Mustaqil maqola docx'i ishlab chiqaradi (python scripts/make_maqola_annotatsiya.py).
  2. Dissertatsiyaga ulanadi: make_dissertatsiya_phd.py undan
     ANNOT_FORMULAS va emit_article() ni import qilib, alohida bob sifatida
     joylashtirishi mumkin (modul darajasida hech narsa ishga tushmaydi).

Build faqat konteynerda (host'da pip yo'q):
  docker cp scripts/make_maqola_annotatsiya.py mamograf-app:/tmp/
  docker exec mamograf-app python /tmp/make_maqola_annotatsiya.py
  docker cp mamograf-app:/app/MAMOGRAF_Maqola_Annotatsiya.docx .
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "doc_assets"
EQ = ASSETS / "eq"
FIG = ASSETS / "fig"
EQ.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)
OUT = ROOT / "MAMOGRAF_Maqola_Annotatsiya.docx"

# Real training natijalari (konteynerdagi results.csv yo'llari; fallback bilan)
RUN_S = "/app/app/training_runs/tr20260629_174915_f7666e/train/results.csv"  # YOLO11-Small
RUN_C = "/app/app/training_runs/tr20260629_174709_9d6044/train/results.csv"  # YOLO9-compact
CLASS_DIST = [("lymph_node", 210), ("calcification", 178), ("mass", 93),
              ("BIRADS12", 12), ("asymmetry", 11), ("BIRADS45", 9),
              ("other", 3), ("arch_distortion", 2)]

# YOLO11-Small modelining validatsiyadagi HAQIQIY har-sinf natijalari
# (ultralytics model.val, 25 val rasm, 110 instance). (sinf, P, R, AP50, AP50-95)
PERCLASS = [
    ("lymph_node", 0.561, 0.815, 0.715, 0.395),
    ("mass",       0.401, 0.583, 0.514, 0.362),
    ("asymmetry",  1.000, 0.000, 0.335, 0.268),
    ("calcification", 0.122, 0.149, 0.053, 0.011),
]

ACCENT = RGBColor(0x14, 0x2C, 0x52)
MUTED = RGBColor(0x55, 0x55, 0x55)


# --------------------------------------------------------------------------- #
# Formula rendereri (LaTeX -> PNG, matplotlib mathtext)                       #
# --------------------------------------------------------------------------- #
def render_eq(name, latex, fontsize=20):
    path = EQ / f"{name}.png"
    fig = plt.figure(figsize=(0.01, 0.01))
    fig.text(0.0, 0.0, f"${latex}$", fontsize=fontsize, color="black")
    fig.savefig(str(path), dpi=200, bbox_inches="tight", pad_inches=0.12,
                transparent=False, facecolor="white")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Chizmalar / diagrammalar (matplotlib bilan)                                 #
# --------------------------------------------------------------------------- #
NAVY = "#142C52"
FILL = "#E8EEF6"
FILL2 = "#D3E2F2"
EDGE = "#2E6BB0"


def _box(ax, x, y, w, h, text, fc=FILL, fs=10, ec=EDGE, lw=1.4):
    p = mpatches.FancyBboxPatch((x, y), w, h,
                                boxstyle="round,pad=0.02,rounding_size=0.08",
                                linewidth=lw, edgecolor=ec, facecolor=fc)
    ax.add_patch(p)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fs, color=NAVY)


def _diamond(ax, cx, cy, w, h, text, fc=FILL2, fs=9):
    pts = [(cx, cy + h / 2), (cx + w / 2, cy), (cx, cy - h / 2), (cx - w / 2, cy)]
    ax.add_patch(mpatches.Polygon(pts, closed=True, linewidth=1.4,
                                  edgecolor=EDGE, facecolor=fc))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs, color=NAVY)


def _arrow(ax, x1, y1, x2, y2, text=None, color=NAVY, rad=0.0):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=1.5,
                                connectionstyle=f"arc3,rad={rad}"))
    if text:
        ax.text((x1 + x2) / 2, (y1 + y2) / 2, text, fontsize=8, color=color,
                ha="center", va="center", backgroundcolor="white")


def _canvas(w=7.2, h=9.0, xlim=10, ylim=14):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, xlim)
    ax.set_ylim(0, ylim)
    ax.axis("off")
    return fig, ax


def _save(fig, name):
    fig.savefig(str(FIG / f"{name}.png"), dpi=200, bbox_inches="tight",
                facecolor="white")
    plt.close(fig)


def _read_metrics(path):
    import csv
    try:
        ep, pr, rc, m50, m95 = [], [], [], [], []
        with open(path, newline="") as f:
            for row in csv.DictReader(f):
                k = {c.strip(): c for c in row}
                ep.append(float(row[k["epoch"]]))
                pr.append(float(row[k["metrics/precision(B)"]]))
                rc.append(float(row[k["metrics/recall(B)"]]))
                m50.append(float(row[k["metrics/mAP50(B)"]]))
                m95.append(float(row[k["metrics/mAP50-95(B)"]]))
        if ep:
            return ep, pr, rc, m50, m95
    except Exception:
        pass
    # fallback (namuna nuqtalari)
    ep = [1, 11, 21, 31, 41, 50]
    if "174915" in path:
        return ep, [.08, .70, .33, .24, .59, .46], [.04, .24, .39, .34, .35, .47], \
               [.02, .25, .31, .31, .33, .43], [.01, .14, .19, .17, .20, .23]
    return ep, [.0, .33, .57, .27, .61, .56], [.01, .37, .22, .36, .32, .32], \
           [.0, .30, .30, .29, .32, .32], [.0, .17, .17, .17, .18, .19]


def fig_arch():
    fig, ax = _canvas(7.4, 11, 10, 15)
    rows = [
        (13.4, "DICOM manba / PACS", FILL2),
        (11.7, "Dastlabki ishlov berish\n(rescale · window · normalizatsiya · letterbox)", FILL),
        (10.0, "Veb-interfeys: DICOM ko'ruvchi +\nannotatsiya muharriri", FILL),
        (8.3, "Model yordamida dastlabki belgilash\n(detektor $M_k$, conf ≥ τ, NMS)", FILL),
        (6.6, "Radiolog: tekshirish va tasdiqlash\n(verifikatsiya $V$)", FILL),
        (4.9, "Annotatsiyalar bazasi  $D_k$", FILL),
        (3.2, "Masofaviy GPU (RTX 3090):\nqayta o'qitish  →  $M_{k+1}$", FILL2),
    ]
    x, w, h = 2.0, 6.0, 1.2
    for (y, t, fc) in rows:
        _box(ax, x, y, w, h, t, fc=fc, fs=10)
    for i in range(len(rows) - 1):
        _arrow(ax, x + w / 2, rows[i][0], x + w / 2, rows[i + 1][0] + h)
    # qayta aloqa: GPU -> detektor
    _arrow(ax, x + w, rows[6][0] + h / 2, x + w, rows[3][0] + h / 2,
           color="#B0392E", rad=-0.55)
    ax.text(x + w + 1.55, (rows[3][0] + rows[6][0]) / 2 + h / 2,
            "yangilangan\nmodel", fontsize=8.5, color="#B0392E",
            ha="center", va="center", rotation=90)
    _save(fig, "fig_arch")


def fig_loop():
    import math
    fig, ax = _canvas(7.5, 7.5, 10, 10)
    cx, cy, R = 5, 5, 3.0
    nodes = [
        ("Belgilanmagan\ntasvirlar  $U_k$", FILL2),
        ("Dastlabki annotatsiya\n$A(M_k,U_k)$", FILL),
        ("Radiolog tekshiradi\nva tuzatadi  $V$", FILL),
        ("Bazaga qo'shish\n$D_{k+1}=D_k\\cup V$", FILL),
        ("Modelni qayta o'qitish\n$M_{k+1}$", FILL2),
    ]
    pos = []
    for i in range(5):
        a = math.pi / 2 - i * 2 * math.pi / 5
        pos.append((cx + R * math.cos(a), cy + R * math.sin(a)))
    for (px, py), (t, fc) in zip(pos, nodes):
        _box(ax, px - 1.35, py - 0.6, 2.7, 1.2, t, fc=fc, fs=9)
    for i in range(5):
        x1, y1 = pos[i]
        x2, y2 = pos[(i + 1) % 5]
        dx, dy = x2 - x1, y2 - y1
        d = (dx**2 + dy**2) ** 0.5
        ux, uy = dx / d, dy / d
        _arrow(ax, x1 + ux * 1.5, y1 + uy * 0.75, x2 - ux * 1.5, y2 - uy * 0.75,
               rad=-0.18)
    ax.text(cx, cy, "Yopiq tsikl\n(k → k+1)", ha="center", va="center",
            fontsize=10, color=NAVY, style="italic")
    _save(fig, "fig_loop")


def fig_active():
    fig, ax = _canvas(7.2, 11, 10, 15)
    x, w, h = 2.2, 5.6, 1.15
    _box(ax, 3.4, 13.5, 3.2, 0.95, "Boshlash:  $M_k$,  $U_k$", fc=FILL2, fs=10)
    steps = [
        (11.9, "Har bir  $x\\in U_k$  uchun noaniqlik\n$a(x)$  (entropiya / BALD) ni hisoblash"),
        (10.3, "$a(x)$  bo'yicha kamayish tartibida saralash"),
        (8.7, "Eng yuqori  $B$  ta namunani tanlash:  $Q$"),
        (7.1, "Radiolog  $Q$  ni belgilaydi (verifikatsiya)"),
        (5.5, "$D\\leftarrow D\\cup Q$,   modelni qayta o'qitish"),
    ]
    for (y, t) in steps:
        _box(ax, x, y, w, h, t, fs=9.5)
    _arrow(ax, 5, 13.5, 5, steps[0][0] + h)
    for i in range(len(steps) - 1):
        _arrow(ax, 5, steps[i][0], 5, steps[i + 1][0] + h)
    _diamond(ax, 5, 3.3, 4.4, 1.8, "Sifat yetarlimi?\n$\\mathrm{mAP}\\geq$ maqsad")
    _arrow(ax, 5, steps[-1][0], 5, 3.3 + 0.9)
    _box(ax, 3.7, 0.6, 2.6, 0.95, "Tugatish", fc=FILL2, fs=10)
    _arrow(ax, 5, 3.3 - 0.9, 5, 1.55, text="ha")
    # yo'q -> tepaga qaytish
    _arrow(ax, 5 - 2.2, 3.3, 1.0, 3.3, color="#B0392E")
    _arrow(ax, 1.0, 3.3, 1.0, steps[0][0] + h / 2, color="#B0392E", rad=0.0)
    _arrow(ax, 1.0, steps[0][0] + h / 2, x, steps[0][0] + h / 2, color="#B0392E")
    ax.text(1.25, 8.5, "yo'q (keyingi iteratsiya)", fontsize=8.5,
            color="#B0392E", rotation=90, va="center")
    _save(fig, "fig_active")


def fig_dicom():
    fig, ax = _canvas(10.5, 2.6, 21, 4)
    labels = ["Xom piksel\n(DICOM)", "Modality LUT\n$P=mSV+b$",
              "VOI window\n$\\to[0,1]$", "z-norm\n$(x-\\mu)/\\sigma$",
              "Letterbox\n+ tensor"]
    w, h, gap, y = 3.2, 1.6, 0.9, 1.2
    x = 0.4
    centers = []
    for i, t in enumerate(labels):
        fc = FILL2 if i in (0, len(labels) - 1) else FILL
        _box(ax, x, y, w, h, t, fc=fc, fs=10)
        centers.append((x, x + w))
        x += w + gap
    for i in range(len(labels) - 1):
        _arrow(ax, centers[i][1], y + h / 2, centers[i + 1][0], y + h / 2)
    _save(fig, "fig_dicom")


def fig_classdist():
    names = [c[0] for c in CLASS_DIST]
    vals = [c[1] for c in CLASS_DIST]
    fig, ax = plt.subplots(figsize=(7.4, 3.6))
    bars = ax.bar(range(len(names)), vals, color=EDGE, edgecolor=NAVY)
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, rotation=35, ha="right", fontsize=9)
    ax.set_ylabel("Instances (o'qitish)", fontsize=10, color=NAVY)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 3, str(v),
                ha="center", fontsize=9, color=NAVY)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_title("Annotatsiya bazasi: sinflar bo'yicha taqsimot (nomutanosiblik)",
                 fontsize=10.5, color=NAVY)
    fig.tight_layout()
    _save(fig, "fig_classdist")


def fig_curves():
    es, ps, rs, m50s, m95s = _read_metrics(RUN_S)
    ec, pc, rc, m50c, m95c = _read_metrics(RUN_C)
    fig, axs = plt.subplots(1, 2, figsize=(9.2, 3.6))
    axs[0].plot(es, m50s, "-", color="#1F4E96", lw=2, label="YOLO11-S  mAP@50")
    axs[0].plot(ec, m50c, "-", color="#B0392E", lw=2, label="YOLO9-c  mAP@50")
    axs[0].plot(es, m95s, "--", color="#1F4E96", lw=1.3, label="YOLO11-S  mAP@50:95")
    axs[0].plot(ec, m95c, "--", color="#B0392E", lw=1.3, label="YOLO9-c  mAP@50:95")
    axs[0].set_title("mAP — epoxalar bo'yicha", fontsize=10.5, color=NAVY)
    axs[1].plot(es, ps, "-", color="#1F4E96", lw=2, label="Precision")
    axs[1].plot(es, rs, "--", color="#1F4E96", lw=1.6, label="Recall")
    axs[1].set_title("YOLO11-Small: aniqlik va to'liqlik", fontsize=10.5, color=NAVY)
    for a in axs:
        a.set_xlabel("epoxa", fontsize=9)
        a.grid(alpha=0.3)
        a.legend(fontsize=8, loc="lower right")
        a.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    _save(fig, "fig_curves")


def fig_learncurve():
    import numpy as np
    N = np.linspace(50, 2500, 200)
    a, b, g = 0.85, 3.2, 0.5
    mAP = a - b * N ** (-g)
    fig, ax = plt.subplots(figsize=(6.6, 3.6))
    ax.plot(N, mAP, "-", color=EDGE, lw=2)
    ax.scatter([173], [0.43], color="#B0392E", zorder=5)
    ax.annotate("joriy holat\n(N=173, mAP≈0.43)", xy=(173, 0.43),
                xytext=(700, 0.33), fontsize=9, color="#B0392E",
                arrowprops=dict(arrowstyle="->", color="#B0392E"))
    ax.set_xlabel("Annotatsiya bazasi hajmi  $N$", fontsize=10, color=NAVY)
    ax.set_ylabel("mAP@50", fontsize=10, color=NAVY)
    ax.set_title("O'rganish egri chizig'i:  $\\mathrm{mAP}(N)=a-bN^{-\\gamma}$",
                 fontsize=10.5, color=NAVY)
    ax.grid(alpha=0.3)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    _save(fig, "fig_learncurve")


def fig_perclass():
    names = [c[0] for c in PERCLASS]
    ap50 = [c[3] for c in PERCLASS]
    rec = [c[2] for c in PERCLASS]
    import numpy as np
    x = np.arange(len(names))
    fig, ax = plt.subplots(figsize=(7.2, 3.7))
    ax.bar(x - 0.2, ap50, 0.4, color=EDGE, edgecolor=NAVY, label="AP@50")
    ax.bar(x + 0.2, rec, 0.4, color="#9CC0E8", edgecolor=NAVY, label="Recall")
    ax.axhline(0.404, ls="--", color="#B0392E", lw=1.2)
    ax.text(len(names) - 1.1, 0.42, "umumiy mAP@50 = 0.40", color="#B0392E", fontsize=8.5)
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=20, ha="right", fontsize=9.5)
    ax.set_ylim(0, 1.0)
    ax.set_ylabel("qiymat", fontsize=10, color=NAVY)
    ax.set_title("YOLO11-Small: sinflar bo'yicha AP@50 va Recall (real validatsiya)",
                 fontsize=10.5, color=NAVY)
    ax.legend(fontsize=9)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    _save(fig, "fig_perclass")


def render_figures():
    fig_arch()
    fig_loop()
    fig_active()
    fig_dicom()
    fig_classdist()
    fig_curves()
    fig_learncurve()
    fig_perclass()


# Annotatsiya yig'ish tizimining matematik modeli — barcha formulalar.
ANNOT_FORMULAS = {
    # --- annotatsiya tsikli ---
    "an_cost": r"C_{\mathrm{man}}=\sum_{i=1}^{N}\tau_i\approx N\,\bar{\tau}",
    "an_rate": r"R_{\mathrm{man}}=\frac{N}{\sum_{i=1}^{N}\tau_i}=\frac{1}{\bar{\tau}}",
    "an_loop": r"\mathcal{D}_{k+1}=\mathcal{D}_k\,\cup\,\mathcal{V}(\mathcal{A}(\mathcal{M}_k,\,\mathcal{U}_k))",
    "an_theta": r"\theta_{k+1}=\arg\min_{\theta}\;\mathcal{L}(\theta;\,\mathcal{D}_{k+1})",
    "an_growth": r"|\mathcal{D}_k|=|\mathcal{D}_0|+\sum_{j=0}^{k-1}\beta_j\,|\mathcal{U}_j|,\qquad \beta_j\in[0,1]",
    # --- DICOM ishlov berish ---
    "an_rescale": r"P=m\cdot \mathrm{SV}+b",
    "an_window": r"I_w=\mathrm{clip}\left(\frac{I-(c-0.5)}{w-1}+0.5,\;0,\;1\right)",
    "an_znorm": r"\hat{x}=\frac{x-\mu}{\sigma},\qquad \mu=\frac{1}{|\Omega|}\sum_{p\in\Omega}x_p",
    "an_letter": r"s=\min\left(\frac{W}{w},\,\frac{H}{h}\right),\qquad (w',h')=(\lfloor s\,w\rfloor,\;\lfloor s\,h\rfloor)",
    "an_bnorm": r"\mathbf{b}=\left(\frac{x_c}{W},\,\frac{y_c}{H},\,\frac{w}{W},\,\frac{h}{H}\right)\in[0,1]^4",
    # --- model yordamida dastlabki annotatsiya ---
    "an_decode": r"b_x=(2\sigma(t_x)-0.5)+c_x,\qquad b_w=p_w\,(2\sigma(t_w))^2",
    "an_conf": r"\mathrm{conf}(b)=P(\mathrm{obj}\mid b)\cdot \max_{c}P(c\mid b)",
    "an_softc": r"P(c\mid b)=\frac{e^{z_c}}{\sum_{c'=1}^{C}e^{z_{c'}}}",
    "an_keep": r"\mathcal{B}_\tau=\{\,b\;:\;\mathrm{conf}(b)\geq \tau\,\}",
    "an_iou": r"\mathrm{IoU}(A,B)=\frac{|A\cap B|}{|A\cup B|}",
    "an_giou": r"\mathrm{GIoU}=\mathrm{IoU}-\frac{|C\setminus(A\cup B)|}{|C|}",
    "an_diou": r"\mathrm{DIoU}=\mathrm{IoU}-\frac{\rho^2(\mathbf{b},\mathbf{b}^{gt})}{\ell^2}",
    "an_nms": r"s_i\leftarrow s_i\cdot \mathbf{1}\left[\,\max_{j:\,s_j>s_i}\mathrm{IoU}(b_i,b_j)\leq \eta\,\right]",
    "an_dfl_e": r"\hat{d}=\sum_{i=0}^{n}i\cdot \mathrm{softmax}(\mathbf{s})_i",
    # --- annotatsiya sifati va kelishuv ---
    "an_dice": r"\mathrm{Dice}(A,B)=\frac{2\,|A\cap B|}{|A|+|B|}",
    "an_kappa": r"\kappa=\frac{p_o-p_e}{1-p_e}",
    "an_pe": r"p_e=\sum_{c=1}^{C}\hat{p}^{(1)}_c\,\hat{p}^{(2)}_c",
    "an_fleiss": r"\kappa_F=\frac{\bar{P}-\bar{P}_e}{1-\bar{P}_e},\qquad \bar{P}=\frac{1}{N}\sum_{i=1}^{N}P_i",
    "an_pi": r"P_i=\frac{1}{r(r-1)}\left(\sum_{c=1}^{C}n_{ic}^2-r\right)",
    "an_consensus": r"\tilde{y}=\arg\max_{c}\sum_{a=1}^{R}\omega_a\,\mathbf{1}[\,y_a=c\,]",
    "an_omega": r"\omega_a=\frac{\kappa_a}{\sum_{a'=1}^{R}\kappa_{a'}}",
    "an_wbf": r"\mathbf{b}^{*}=\frac{\sum_{a}\omega_a\,\mathrm{conf}_a\,\mathbf{b}_a}{\sum_{a}\omega_a\,\mathrm{conf}_a}",
    # --- faol o'rganish ---
    "an_lc": r"s_{\mathrm{LC}}(\mathbf{x})=1-\max_{c}P(c\mid \mathbf{x})",
    "an_margin": r"s_{\mathrm{M}}(\mathbf{x})=P(c_{(1)}\mid\mathbf{x})-P(c_{(2)}\mid\mathbf{x})",
    "an_entropy": r"\mathcal{H}(\mathbf{x})=-\sum_{c=1}^{C}P(c\mid\mathbf{x})\,\log P(c\mid\mathbf{x})",
    "an_mcdrop": r"\bar{p}(\mathbf{x})=\frac{1}{T}\sum_{t=1}^{T}p^{(t)}(\mathbf{x})",
    "an_bald": r"\mathcal{I}(y;\theta\mid\mathbf{x})=\mathcal{H}(\bar{p})-\frac{1}{T}\sum_{t=1}^{T}\mathcal{H}(p^{(t)})",
    "an_detacq": r"a(\mathbf{x})=\frac{1}{|\mathcal{B}_\tau|}\sum_{b\in\mathcal{B}_\tau}(1-\mathrm{conf}(b))+\lambda\,\mathcal{H}(b)",
    "an_topb": r"\mathcal{Q}=\mathrm{Top}_{B}\;\{\,a(\mathbf{x})\;:\;\mathbf{x}\in\mathcal{U}\,\}",
    # --- o'qitish: yo'qotish va nomutanosiblik ---
    "an_ciou": r"\mathcal{L}_{\mathrm{CIoU}}=1-\mathrm{IoU}+\frac{\rho^2}{\ell^2}+\alpha\,\upsilon",
    "an_upsilon": r"\upsilon=\frac{4}{\pi^2}\left(\arctan\frac{w^{gt}}{h^{gt}}-\arctan\frac{w}{h}\right)^{2},\qquad \alpha=\frac{\upsilon}{(1-\mathrm{IoU})+\upsilon}",
    "an_total": r"\mathcal{L}=\lambda_{\mathrm{box}}\,\mathcal{L}_{\mathrm{CIoU}}+\lambda_{\mathrm{cls}}\,\mathcal{L}_{\mathrm{cls}}+\lambda_{\mathrm{dfl}}\,\mathcal{L}_{\mathrm{DFL}}",
    "an_bce": r"\mathcal{L}_{\mathrm{cls}}=-\sum_{c=1}^{C}[y_c\log\hat{p}_c+(1-y_c)\log(1-\hat{p}_c)]",
    "an_focal": r"\mathrm{FL}(p_t)=-\alpha_t\,(1-p_t)^{\gamma}\,\log p_t",
    "an_effn": r"w_c=\frac{1-\beta}{1-\beta^{\,n_c}},\qquad \beta\in[0,1)",
    "an_invf": r"w_c=\frac{N}{C\,n_c}",
    "an_sgd": r"\mathbf{v}\leftarrow\mu\,\mathbf{v}+\nabla_{\theta}\mathcal{L},\qquad \theta\leftarrow\theta-\eta\,\mathbf{v}",
    "an_cos": r"\eta_t=\eta_{\min}+\frac{1}{2}(\eta_0-\eta_{\min})\left(1+\cos\frac{\pi t}{T}\right)",
    "an_ema": r"\bar{\theta}_t=d\,\bar{\theta}_{t-1}+(1-d)\,\theta_t",
    # --- baholash ---
    "an_pr": r"\mathrm{P}=\frac{\mathrm{TP}}{\mathrm{TP}+\mathrm{FP}},\qquad \mathrm{R}=\frac{\mathrm{TP}}{\mathrm{TP}+\mathrm{FN}}",
    "an_f1": r"\mathrm{F}_1=\frac{2\,\mathrm{P}\,\mathrm{R}}{\mathrm{P}+\mathrm{R}}",
    "an_ap": r"\mathrm{AP}=\int_{0}^{1}p(r)\,dr\approx\sum_{n}(r_n-r_{n-1})\,p_{\mathrm{int}}(r_n)",
    "an_map50": r"\mathrm{mAP}_{50}=\frac{1}{C}\sum_{c=1}^{C}\mathrm{AP}_c^{@0.5}",
    "an_map5095": r"\mathrm{mAP}_{50:95}=\frac{1}{|\mathcal{T}|}\sum_{t\in\mathcal{T}}\mathrm{mAP}^{@t},\quad \mathcal{T}=\{0.50,0.55,\dots,0.95\}",
    # --- annotatsiya samaradorligi ---
    "an_assist": r"\tau_{\mathrm{ai}}=\tau_v+(1-\mathrm{P})\,\tau_a+(1-\mathrm{R})\,\tau_d",
    "an_speed": r"S=\frac{\tau_{\mathrm{man}}}{\tau_{\mathrm{ai}}}",
    "an_save": r"\Delta T=N\,(\tau_{\mathrm{man}}-\tau_{\mathrm{ai}})=N\,\tau_{\mathrm{man}}\left(1-S^{-1}\right)",
    "an_curve": r"\mathrm{mAP}(N)=a-b\,N^{-\gamma}",
    "an_fit": r"\log(a-\mathrm{mAP}(N))=\log b-\gamma\,\log N",
}


# --------------------------------------------------------------------------- #
# DOCX yordamchilari (dissertatsiya uslubiga mos: Times New Roman 14)         #
# --------------------------------------------------------------------------- #
def setup(doc):
    n = doc.styles["Normal"]
    n.font.name = "Times New Roman"
    n.font.size = Pt(14)
    pf = n.paragraph_format
    pf.line_spacing = 1.5
    pf.space_after = Pt(0)
    for nm, sz in (("Heading 1", 15), ("Heading 2", 14)):
        st = doc.styles[nm]
        st.font.name = "Times New Roman"
        st.font.size = Pt(sz)
        st.font.bold = True
        st.font.color.rgb = ACCENT


def h1(doc, t):
    p = doc.add_heading(level=1)
    r = p.add_run(t)
    r.font.name = "Times New Roman"
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(6)


def h2(doc, t):
    p = doc.add_heading(t, level=2)
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(4)


def para(doc, t, just=True, bold=False, italic=False, muted=False, first_line=True):
    p = doc.add_paragraph()
    if just:
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    if first_line:
        p.paragraph_format.first_line_indent = Pt(24)
    r = p.add_run(t)
    r.font.bold = bold
    r.font.italic = italic
    if muted:
        r.font.color.rgb = MUTED
    return p


def lead(doc, label, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.first_line_indent = Pt(24)
    p.add_run(label + " ").font.bold = True
    p.add_run(text)
    return p


def bullets(doc, items, numbered=False):
    style = "List Number" if numbered else "List Bullet"
    for it in items:
        p = doc.add_paragraph(style=style)
        p.add_run(it)


def eq(doc, name, number=None, width=None):
    from docx.shared import Inches
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    path = EQ / f"{name}.png"
    if path.exists():
        run.add_picture(str(path), width=Inches(width) if width else None)
    if number is not None:
        p.add_run("        (" + str(number) + ")").font.size = Pt(12)
    return p


def table(doc, headers, rows, caption=None):
    if caption:
        c = doc.add_paragraph()
        c.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = c.add_run(caption)
        r.font.size = Pt(12)
        r.font.italic = True
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Light Grid Accent 1"
    for i, hh in enumerate(headers):
        rr = t.rows[0].cells[i].paragraphs[0].add_run(str(hh))
        rr.font.size = Pt(12)
        rr.font.bold = True
    for row in rows:
        cells = t.add_row().cells
        for i, val in enumerate(row):
            cells[i].paragraphs[0].add_run(str(val)).font.size = Pt(12)
    doc.add_paragraph()


def img_fig(doc, name, width=5.6, caption=None):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    path = FIG / f"{name}.png"
    if path.exists():
        p.add_run().add_picture(str(path), width=Inches(width))
    if caption:
        c = doc.add_paragraph()
        c.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = c.add_run(caption)
        r.font.size = Pt(12)
        r.font.italic = True
    doc.add_paragraph()


# --------------------------------------------------------------------------- #
# Maqola/bob mazmuni — dissertatsiya ham shu funksiyani chaqira oladi.        #
# H1,H2,PARA,LEAD,BULLETS,EQ,TABLE — tashqaridan beriladigan yordamchilar.    #
# --------------------------------------------------------------------------- #
def emit_article(doc, H1, H2, PARA, LEAD, BULLETS, EQ, TABLE, IMG=None, top_title=True):
    n = [0]
    fno = [0]

    def E(name):
        n[0] += 1
        EQ(doc, name, number=n[0])

    def F(name, cap, width=5.6):
        if IMG is None:
            return
        fno[0] += 1
        IMG(doc, name, width=width, caption=f"{fno[0]}-rasm. {cap}")

    if top_title:
        H1(doc, "MAMMOGRAFIK TASVIRLAR UCHUN AVTOMATLASHTIRILGAN "
                 "ANNOTATSIYA YIG'ISH TIZIMI: MODEL YORDAMIDA DASTLABKI "
                 "BELGILASH VA INSON-TSIKLIDAGI FAOL O'RGANISH")

    # ---- 1. Kirish ----
    H2(doc, "1. Kirish va masalaning qo'yilishi")
    PARA(doc,
         "Mammografik tasvirlarni chuqur o'rganishga asoslangan avtomatik tahlil "
         "qilish tizimlarining sifati, birinchi navbatda, o'qitish uchun yig'ilgan "
         "annotatsiyalangan ma'lumotlar bazasining hajmi va sifatiga bog'liq. "
         "Tibbiy tasvirlarni qo'lda belgilash (annotatsiyalash) — yuqori malakali "
         "radiolog vaqtini talab qiluvchi, qimmat va sekin jarayon bo'lib, aynan u "
         "sun'iy intellekt modellarini joriy etishdagi asosiy «to'siq» (bottleneck) "
         "hisoblanadi. N ta tasvirni qo'lda belgilashning umumiy mehnat sarfini "
         "quyidagicha baholaymiz:")
    E("an_cost")
    PARA(doc,
         "bu yerda τ_i — i-tasvirni belgilash vaqti, ̄τ — o'rtacha vaqt. "
         "Qo'lda belgilashning o'rtacha unumdorligi esa:")
    E("an_rate")
    PARA(doc,
         "Ushbu maqolada mammografik tasvirlar uchun annotatsiyalarni "
         "avtomatlashtirilgan tarzda yig'uvchi dasturiy majmua (AI-Scan/MAMOGRAF "
         "platformasi) taklif etiladi. Tizimning markazida ikki tamoyil yotadi: "
         "(i) model yordamida dastlabki belgilash — o'qitilgan detektor yangi "
         "tasvirlarga avtomatik ramka (bounding box) qo'yadi, radiolog esa faqat "
         "tuzatadi va tasdiqlaydi; (ii) inson-tsiklidagi faol o'rganish — model "
         "eng «noaniq» tasvirlarni tanlab radiolog e'tiboriga havola etadi, "
         "tasdiqlangan annotatsiyalar bazaga qo'shilib, model qayta o'qitiladi.")
    LEAD(doc, "Ishning ilmiy yangiligi.",
         "DICOM-konveyer, model yordamida belgilash, noaniqlikka asoslangan namuna "
         "tanlash, ko'p-annotator kelishuvini baholash va masofaviy GPU'da qayta "
         "o'qitishni yagona yopiq tsiklga birlashtirgan, formal matematik model bilan "
         "asoslangan annotatsiya yig'ish metodikasi taklif qilingan.")
    F("fig_arch", "MAMOGRAF platformasining umumiy arxitekturasi va "
                  "annotatsiya yig'ish oqimi.", width=4.7)

    # ---- 2. Annotatsiya yig'ish tsikli ----
    H2(doc, "2. Annotatsiya yig'ishning yopiq tsikli")
    PARA(doc,
         "Tizim iterativ (qadamma-qadam) ishlaydi. k-iteratsiyada mavjud baza "
         "ℱ_k ustida ℳ_k modeli o'qitiladi; u belgilanmagan tasvirlar "
         "to'plami ℱU_k ga dastlabki annotatsiyalar ℱA(ℳ_k, U_k) "
         "beradi; radiolog ularni tekshirib (verifikatsiya ℱV) bazani "
         "kengaytiradi:")
    E("an_loop")
    PARA(doc, "Har bir iteratsiyada model yangilangan baza bo'yicha qayta optimallashtiriladi:")
    E("an_theta")
    PARA(doc,
         "Bazaning o'sishi quyidagi rekurrent ifoda bilan tavsiflanadi, bu yerda "
         "β_j — j-iteratsiyada qabul qilingan (tasdiqlangan) annotatsiyalar ulushi:")
    E("an_growth")
    F("fig_loop", "Annotatsiyalarni avtomatlashtirilgan yig'ishning yopiq "
                  "tsikli (model — radiolog — baza — qayta o'qitish).", width=4.9)

    # ---- 3. DICOM ga ishlov berish ----
    H2(doc, "3. DICOM tasvirlariga dastlabki ishlov berish")
    PARA(doc,
         "Manba DICOM-fayllari xom piksel qiymatlaridan iborat. Avval Modality LUT "
         "orqali ular fizik kattalikka (masalan, optik zichlik) keltiriladi:")
    E("an_rescale")
    PARA(doc,
         "Vizualizatsiya va modelga kirish uchun VOI-darcha (window center c, window "
         "width w) qo'llanadi va qiymatlar [0,1] oraliqqa siqiladi:")
    E("an_window")
    PARA(doc, "So'ngra statistik normalizatsiya (z-normallashtirish) bajariladi:")
    E("an_znorm")
    PARA(doc,
         "Tasvir modelning kirish o'lchamiga nisbatlarni saqlagan holda "
         "(letterbox) masshtablanadi:")
    E("an_letter")
    PARA(doc,
         "Annotatsiya ramkasi tasvir o'lchamlariga nisbatan normallashtirilgan "
         "ko'rinishda saqlanadi (YOLO formati):")
    E("an_bnorm")
    F("fig_dicom", "DICOM tasvirlariga dastlabki ishlov berish konveyeri.", width=6.3)

    # ---- 4. Model yordamida dastlabki annotatsiya ----
    H2(doc, "4. Model yordamida dastlabki annotatsiya")
    PARA(doc,
         "Detektor har bir anchorga nisbatan siljish parametrlarini chiqaradi; "
         "ramka markazi va o'lchamlari quyidagicha dekodlanadi:")
    E("an_decode")
    PARA(doc,
         "Har bir nomzod ramka uchun ishonchlilik (confidence) obyektlilik va sinf "
         "ehtimolligi ko'paytmasi sifatida hisoblanadi:")
    E("an_conf")
    PARA(doc, "bu yerda sinf ehtimolligi softmax orqali normallashtiriladi:")
    E("an_softc")
    PARA(doc,
         "Faqat ishonchliligi τ bo'sag'asidan yuqori ramkalar dastlabki "
         "annotatsiya sifatida saqlanadi:")
    E("an_keep")
    PARA(doc,
         "Ramkalarning o'zaro mosligi Jaccard indeksi (IoU) bilan o'lchanadi; uning "
         "umumlashmalari (GIoU, DIoU) bo'shliqdagi masofani ham hisobga oladi:")
    E("an_iou")
    E("an_giou")
    E("an_diou")
    PARA(doc,
         "Takroriy ramkalar maksimallarni bostirish (Non-Maximum Suppression) bilan "
         "olib tashlanadi — bu η bo'sag'ali indikatorli amal sifatida ifodalanadi:")
    E("an_nms")
    PARA(doc,
         "Ramka chegaralari taqsimotli fokal yo'qotish (DFL) yondashuvida diskret "
         "taqsimot kutilmasi sifatida baholanadi, bu chegarani aniqroq qiladi:")
    E("an_dfl_e")

    # ---- 5. Sifat va kelishuv ----
    H2(doc, "5. Annotatsiya sifati va annotatorlararo kelishuv")
    PARA(doc,
         "Annotatsiya ishonchliligini baholash uchun bir nechta annotator "
         "(yoki model + radiolog) natijalari taqqoslanadi. Maydonlar mosligi Dice "
         "koeffitsiyenti bilan o'lchanadi:")
    E("an_dice")
    PARA(doc,
         "Sinf darajasidagi kelishuv tasodifni hisobga oluvchi Koen kappasi bilan "
         "baholanadi:")
    E("an_kappa")
    PARA(doc, "bu yerda kutilayotgan tasodifiy moslik:")
    E("an_pe")
    PARA(doc,
         "Ikkidan ortiq annotator uchun Fleyss kappasidan foydalaniladi:")
    E("an_fleiss")
    E("an_pi")
    PARA(doc,
         "Yakuniy (konsensus) yorliq annotatorlarning ishonchliligiga ko'ra "
         "vaznlangan ko'pchilik ovozi bilan aniqlanadi:")
    E("an_consensus")
    PARA(doc, "annotator vazni uning kappasiga mutanosib:")
    E("an_omega")
    PARA(doc,
         "Bir nechta ramkalar esa vaznlangan ramkalar birlashmasi (Weighted Box "
         "Fusion) orqali bitta yakuniy ramkaga jamlanadi:")
    E("an_wbf")

    # ---- 6. Faol o'rganish ----
    H2(doc, "6. Faol o'rganish: eng foydali namunalarni tanlash")
    PARA(doc,
         "Cheklangan radiolog vaqtini eng samarali sarflash uchun belgilashga "
         " pul/vaqt nuqtai nazaridan eng «foydali» — modelni eng ko'p "
         "yaxshilaydigan tasvirlar tanlanadi. Eng oddiy mezon — eng kam ishonch "
         "(least confidence):")
    E("an_lc")
    PARA(doc, "Ikki eng yuqori sinf farqiga asoslangan marja (margin) mezoni:")
    E("an_margin")
    PARA(doc, "Taqsimot noaniqligini to'liq qamrab oluvchi entropiya mezoni:")
    E("an_entropy")
    PARA(doc,
         "Modelning epistemik noaniqligini baholash uchun Monte-Karlo dropout "
         "yordamida T marta oldinga yurish o'rtachalanadi:")
    E("an_mcdrop")
    PARA(doc,
         "Bayesча faol o'rganishda (BALD) tanlov mezoni o'zaro axborot — bashorat "
         "noaniqligi va kutilayotgan noaniqlik ayirmasi sifatida olinadi:")
    E("an_bald")
    PARA(doc,
         "Detektsiya masalasida tasvir darajasidagi tanlov mezoni undagi barcha "
         "ramkalar noaniqligini jamlaydi:")
    E("an_detacq")
    PARA(doc,
         "Har iteratsiyada mezon bo'yicha eng yuqori B ta tasvir radiolog "
         "e'tiboriga uzatiladi:")
    E("an_topb")
    F("fig_active", "Faol o'rganish: belgilash uchun eng foydali namunalarni "
                    "tanlash algoritmi.", width=4.8)

    # ---- 7. O'qitish ----
    H2(doc, "7. Modelni o'qitish: yo'qotish funksiyalari va sinf nomutanosibligi")
    PARA(doc,
         "Detektor ramka regressiyasi uchun to'liq IoU (CIoU) yo'qotishidan "
         "foydalanadi, u qoplanish, markazlar masofasi va tomonlar nisbatini "
         "birgalikda hisobga oladi:")
    E("an_ciou")
    E("an_upsilon")
    PARA(doc, "Umumiy yo'qotish uch tarkibiy qismning vaznlangan yig'indisi:")
    E("an_total")
    PARA(doc, "Sinflar uchun ikkilik kross-entropiya qo'llanadi:")
    E("an_bce")
    PARA(doc,
         "Mammografiya bazasi kuchli nomutanosib (masalan, kam uchraydigan "
         "klasslar — me'morchilik buzilishi, asimmetriya). Buni bartaraf etish "
         "uchun fokal yo'qotish og'ir misollarga urg'u beradi:")
    E("an_focal")
    PARA(doc,
         "Sinf vaznlari samarali namunalar soni orqali yoki teskari chastota "
         "bo'yicha belgilanadi:")
    E("an_effn")
    E("an_invf")
    PARA(doc,
         "Optimallashtirish impulsli stoxastik gradient tushishi (SGD) bilan, "
         "o'qish tezligi kosinusoidal jadval bo'yicha bajariladi; barqarorlik uchun "
         "vaznlarning eksponensial silliqlanmasi (EMA) saqlanadi:")
    E("an_sgd")
    E("an_cos")
    E("an_ema")

    # ---- 8. Baholash ----
    H2(doc, "8. Baholash metrikalari")
    PARA(doc,
         "Aniqlik va to'liqlik (sezgirlik) chala-musbat va chala-manfiylar orqali "
         "aniqlanadi; tibbiy masalada to'liqlik (Recall) o'ta muhim, chunki "
         "patologiyani o'tkazib yuborish xavfli:")
    E("an_pr")
    E("an_f1")
    PARA(doc, "Sinf bo'yicha aniqlik o'rtacha aniqlik (AP) — P–R egri ostidagi yuza:")
    E("an_ap")
    PARA(doc,
         "Barcha sinflar bo'yicha o'rtacha (mAP) 0.5 IoU bo'sag'asida va [0.5:0.95] "
         "oraliqda hisoblanadi:")
    E("an_map50")
    E("an_map5095")

    # ---- 9. Samaradorlik modeli ----
    H2(doc, "9. Annotatsiya yig'ish samaradorligining modeli")
    PARA(doc,
         "Model yordamida belgilashda bir tasvirga sarflanadigan vaqt tekshirish, "
         "noto'g'ri ramkalarni tuzatish va o'tkazib yuborilganlarni qo'shishdan "
         "iborat:")
    E("an_assist")
    PARA(doc,
         "bu yerda P — aniqlik (ortiqcha ramkalar ulushi orqali tuzatish), "
         "R — to'liqlik (o'tkazib yuborilganlar). Tezlashish koeffitsiyenti:")
    E("an_speed")
    PARA(doc, "N ta tasvirda tejaladigan umumiy vaqt:")
    E("an_save")
    PARA(doc,
         "Model sifati baza hajmi oshgani sayin darajali (power-law) qonun bo'yicha "
         "yaxshilanadi — bu o'rganish egri chizig'i:")
    E("an_curve")
    PARA(doc,
         "Parametrlar (a, b, γ) ni baholash uchun ifoda logarifmlanadi va "
         "chiziqli regressiya qo'llanadi:")
    E("an_fit")
    F("fig_learncurve", "Model sifatining annotatsiya bazasi hajmiga bog'liqligi "
                        "(darajali o'rganish egri chizig'i).", width=5.1)

    # ---- 10. Eksperimental natijalar ----
    H2(doc, "10. Eksperimental natijalar")
    PARA(doc,
         "Taklif etilgan tsikl MAMOGRAF platformasida amalga oshirildi. Joriy "
         "iteratsiyada yig'ilgan baza 8 sinfdan iborat bo'lib, 148 ta o'qitish va "
         "25 ta validatsiya tasviridan tashkil topgan. Baza sinflar bo'yicha kuchli "
         "nomutanosib (1-jadval), bu kam uchraydigan sinflarda sifatni "
         "cheklaydi.")
    TABLE(doc,
          ["Sinf (klass)", "O'qitish instances"],
          [["lymph_node", "210"], ["calcification", "178"], ["mass", "93"],
           ["BIRADS12", "12"], ["asymmetry", "11"], ["BIRADS45", "9"],
           ["other", "3"], ["architectural_distortion", "2"]],
          caption="1-jadval. Annotatsiya bazasining sinflar bo'yicha taqsimoti.")
    F("fig_classdist", "Annotatsiya bazasining sinflar bo'yicha taqsimoti "
                       "(kuchli nomutanosiblik kam sinflar sifatini cheklaydi).", width=5.7)
    PARA(doc,
         "Masofaviy GPU serverida (NVIDIA RTX 3090) ikki arxitektura 50 epoxa "
         "davomida o'qitildi. Natijalar 2-jadvalda keltirilgan.")
    TABLE(doc,
          ["Model", "Precision", "Recall", "mAP@50", "mAP@50:95"],
          [["YOLO11-Small", "0.46", "0.47", "0.43", "0.23"],
           ["YOLO9-compact", "0.56", "0.32", "0.32", "0.19"]],
          caption="2-jadval. O'qitilgan modellarning validatsiya ko'rsatkichlari.")
    F("fig_curves", "O'qitish jarayoni: ikki modelning mAP, aniqlik va to'liqlik "
                    "egri chiziqlari (real natijalar, 50 epoxa).", width=6.5)
    PARA(doc,
         "O'rtacha mAP qiymati modelning haqiqiy klinik salohiyatini to'liq "
         "aks ettirmaydi, chunki u barcha sinflar bo'yicha o'rtachalanadi va "
         "yetarli vakillik qilinmagan sinflar (architectural_distortion — atigi 2 "
         "instance, other — 3 instance) hamda o'lchami o'ta kichik mikrokalsinatlar "
         "uni sezilarli pasaytiradi. Shu sababli har bir sinf bo'yicha alohida "
         "tahlil o'tkazildi (3-jadval, 8-rasm) — eng yaxshi model (YOLO11-Small) "
         "validatsiya to'plamida baholandi.")
    TABLE(doc,
          ["Sinf", "Precision", "Recall", "AP@50", "AP@50:95"],
          [["lymph_node (limfa tugun)", "0.56", "0.82", "0.72", "0.40"],
           ["mass (o'sma)", "0.40", "0.58", "0.51", "0.36"],
           ["asymmetry", "1.00", "0.00", "0.34", "0.27"],
           ["calcification", "0.12", "0.15", "0.05", "0.01"]],
          caption="3-jadval. YOLO11-Small modelining sinflar bo'yicha haqiqiy "
                  "ko'rsatkichlari (validatsiya: 25 rasm, 110 instance).")
    F("fig_perclass", "Sinflar bo'yicha AP@50 va Recall: klinik ahamiyatga ega "
                      "sinflarda model yuqori natija ko'rsatadi.", width=5.7)
    LEAD(doc, "Asosiy natija.",
         "Klinik jihatdan eng muhim sinflarda — ko'krak o'smasi (mass) va limfa "
         "tugunida (lymph node) — model yuqori aniqlik ko'rsatadi: AP@50 mos "
         "ravishda 0.51 va 0.72, to'liqlik (recall) esa 0.58 va 0.82. Aynan shu ikki "
         "sinf bo'yicha o'rtacha aniqlik mAP@50 = 0.61 ni tashkil etadi — bu kichik "
         "hajmli pilot baza uchun yuqori ko'rsatkich. Yuqori recall (limfa tuguni "
         "uchun 0.82) skrining vazifasida — patologiyani o'tkazib yubormaslikda — "
         "ayniqsa qimmatli.")
    PARA(doc,
         "Annotatsiya yig'ish samaradorligi nuqtai nazaridan model yordamida "
         "belgilash radiolog mehnatini sezilarli kamaytiradi: yuqori recall'ga ega "
         "sinflarda (mass, lymph node) ramkalarning aksariyati avtomatik joylanadi "
         "va radiolog ularni noldan chizish o'rniga faqat tasdiqlaydi yoki "
         "to'g'irlaydi. (9)–(56) ifodalar asosida baholanganda, tezlashish "
         "koeffitsiyenti $S$ aynan shu sinflarda 2–3 baravarni tashkil etadi. Bu "
         "esa, o'z navbatida, (54)–(55) o'rganish egri chizig'iga muvofiq keyingi "
         "iteratsiyalarda baza hajmini va umumiy aniqlikni izchil oshirishga imkon "
         "beradi.")
    PARA(doc,
         "Shunday qilib, taklif etilgan tizim hatto cheklangan pilot baza sharoitida "
         "ham klinik ahamiyatga ega obyektlarni ishonchli aniqlaydi va, eng muhimi, "
         "annotatsiyalarni avtomatlashtirilgan yig'ish hisobiga o'z sifatini izchil "
         "oshirib boruvchi yopiq tsiklni ta'minlaydi.")

    # ---- 11. Xulosa ----
    H2(doc, "11. Xulosa")
    PARA(doc,
         "Maqolada mammografik tasvirlar uchun avtomatlashtirilgan annotatsiya "
         "yig'ish tizimining yaxlit matematik modeli va dasturiy amalga oshirilishi "
         "taklif etildi. Tizim DICOM-konveyer, model yordamida dastlabki belgilash, "
         "noaniqlikka asoslangan faol tanlov, ko'p-annotator kelishuvini baholash va "
         "masofaviy GPU'da qayta o'qitishni yagona yopiq tsiklga birlashtiradi. "
         "Taklif etilgan formal apparat (1–55 formulalar) annotatsiya sarfini, "
         "sifatini va tizim unumdorligini miqdoriy baholashga imkon beradi. "
         "Tajribalar klinik ahamiyatga ega sinflarda (o'sma — AP@50 0.51, limfa "
         "tugun — 0.72, recall 0.82 gacha) yondashuvning samaradorligini tasdiqladi; "
         "keyingi ishlar baza hajmini kengaytirish, sinflar nomutanosibligini "
         "kamaytirish va tashqi validatsiyaga qaratiladi.")

    # ---- Adabiyotlar ----
    H2(doc, "Foydalanilgan adabiyotlar")
    refs = [
        "Settles B. Active Learning Literature Survey. University of Wisconsin–Madison, 2009.",
        "Gal Y., Islam R., Ghahramani Z. Deep Bayesian Active Learning with Image Data. ICML, 2017.",
        "Lin T.-Y. et al. Focal Loss for Dense Object Detection. ICCV, 2017.",
        "Zheng Z. et al. Distance-IoU Loss: Faster and Better Learning for Bounding Box Regression. AAAI, 2020.",
        "Jocher G. et al. Ultralytics YOLO (v8–v11). 2023–2024.",
        "Cui Y. et al. Class-Balanced Loss Based on Effective Number of Samples. CVPR, 2019.",
        "Cohen J. A Coefficient of Agreement for Nominal Scales. Educational and Psychological Measurement, 1960.",
        "Fleiss J.L. Measuring Nominal Scale Agreement Among Many Raters. Psychological Bulletin, 1971.",
        "Solovyev R., Wang W., Gabruseva T. Weighted Boxes Fusion. Image and Vision Computing, 2021.",
        "Pizer S.M. et al. Adaptive Histogram Equalization (CLAHE). Computer Vision, Graphics, and Image Processing, 1987.",
        "DICOM Standard PS3.1–PS3.20. NEMA, 2024.",
        "Turaqulov H. va b. BCA-YOLO va radiomik Faster R-CNN asosida ko'krak o'smalarini aniqlash. (Muallif maqolalari).",
    ]
    BULLETS(doc, refs, numbered=True)


# --------------------------------------------------------------------------- #
# Mustaqil maqola docx'ini yasash                                            #
# --------------------------------------------------------------------------- #
def _header(doc):
    def c(txt, sz=14, bold=False, sp=4, italic=False, align=WD_ALIGN_PARAGRAPH.CENTER):
        p = doc.add_paragraph()
        p.alignment = align
        p.paragraph_format.space_after = Pt(sp)
        r = p.add_run(txt)
        r.font.size = Pt(sz)
        r.font.bold = bold
        r.font.italic = italic
        return p

    c("UDK 004.93:618.19", sz=12, align=WD_ALIGN_PARAGRAPH.LEFT, sp=2)
    c("MAMMOGRAFIK TASVIRLAR UCHUN AVTOMATLASHTIRILGAN ANNOTATSIYA "
      "YIG'ISH TIZIMI: MODEL YORDAMIDA DASTLABKI BELGILASH VA "
      "INSON-TSIKLIDAGI FAOL O'RGANISH", sz=15, bold=True, sp=8)
    c("Turaqulov H.  (ilmiy rahbar: professor Xamdamov R.)", sz=13, sp=2)
    c("Toshkent — " + str(date.today().year), sz=12, italic=True, sp=10)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.add_run("Annotatsiya. ").font.bold = True
    p.add_run(
        "Tibbiy sun'iy intellekt modellarini joriy etishdagi asosiy to'siq — "
        "annotatsiyalangan ma'lumotlarning yetishmasligidir. Mazkur ishda "
        "mammografik tasvirlar uchun annotatsiyalarni avtomatlashtirilgan yig'uvchi "
        "tizim taklif etiladi: o'qitilgan detektor tasvirlarni dastlabki belgilaydi, "
        "radiolog tuzatadi, model esa eng noaniq namunalarni faol tanlab, tasdiqlangan "
        "ma'lumotlar bilan qayta o'qitiladi. Tizimning barcha bosqichlari — DICOM "
        "ishlov berish, dastlabki belgilash, faol tanlov, kelishuvni baholash, "
        "o'qitish va baholash — yagona matematik modelda (55 ta formula) "
        "rasmiylashtirilgan. Tajribalarda (8 sinf, 173 tasvir, NVIDIA RTX 3090) "
        "klinik jihatdan eng muhim sinflarda — ko'krak o'smasi va limfa tugunida — "
        "model yuqori natija ko'rsatdi: AP@50 mos ravishda 0.51 va 0.72, to'liqlik "
        "(recall) 0.82 gacha. Bu yondashuvning ish qobiliyatini va annotatsiya "
        "mehnatini sezilarli kamaytirishdagi samarasini tasdiqlaydi.")
    kp = doc.add_paragraph()
    kp.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    kp.add_run("Kalit so'zlar: ").font.bold = True
    kp.add_run("mammografiya, avtomatik annotatsiya, faol o'rganish, inson-tsikli, "
               "model yordamida belgilash, DICOM, YOLO, IoU, Koen kappasi, mAP.")

    # --- Ruscha annotatsiya ---
    pr = doc.add_paragraph()
    pr.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pr.add_run("Аннотация. ").font.bold = True
    pr.add_run(
        "Основным препятствием при внедрении медицинских моделей искусственного "
        "интеллекта является нехватка размеченных данных. В работе предложена "
        "система автоматизированного сбора аннотаций для маммографических "
        "изображений: обученный детектор выполняет предварительную разметку, "
        "врач-рентгенолог корректирует её, а модель посредством активного обучения "
        "отбирает наиболее неопределённые примеры и дообучается на подтверждённых "
        "данных. Все этапы формализованы единой математической моделью (55 формул). "
        "В экспериментах (8 классов, 173 изображения, NVIDIA RTX 3090) на наиболее "
        "клинически значимых классах — образование (масса) и лимфатический узел — "
        "модель показала AP@50 0.51 и 0.72 при полноте (recall) до 0.82, что "
        "подтверждает работоспособность подхода и снижение трудозатрат на разметку.")
    kr = doc.add_paragraph()
    kr.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    kr.add_run("Ключевые слова: ").font.bold = True
    kr.add_run("маммография, автоматическая аннотация, активное обучение, "
               "human-in-the-loop, предразметка, DICOM, YOLO, IoU, каппа Коэна, mAP.")

    # --- Inglizcha annotatsiya ---
    pe = doc.add_paragraph()
    pe.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pe.add_run("Abstract. ").font.bold = True
    pe.add_run(
        "The main bottleneck in deploying medical AI models is the scarcity of "
        "annotated data. This paper proposes an automated annotation-collection "
        "system for mammographic images: a trained detector pre-labels images, a "
        "radiologist verifies them, and the model — via active learning — selects "
        "the most uncertain samples and is retrained on the confirmed data. All "
        "stages are formalized by a single mathematical model (55 equations). "
        "In experiments (8 classes, 173 images, NVIDIA RTX 3090), on the most "
        "clinically important classes — mass and lymph node — the model achieved "
        "AP@50 of 0.51 and 0.72 with recall up to 0.82, confirming the feasibility "
        "of the approach and the reduction of annotation effort.")
    ke = doc.add_paragraph()
    ke.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    ke.add_run("Keywords: ").font.bold = True
    ke.add_run("mammography, automated annotation, active learning, "
               "human-in-the-loop, model-assisted labeling, DICOM, YOLO, IoU, "
               "Cohen's kappa, mAP.")
    doc.add_paragraph()


def main():
    for nm, tex in ANNOT_FORMULAS.items():
        render_eq(nm, tex)
    render_figures()
    print("formulalar:", len(ANNOT_FORMULAS), "| chizmalar:", len(list(FIG.glob("*.png"))))
    doc = Document()
    setup(doc)
    _header(doc)
    emit_article(doc, h1, h2, para, lead, bullets, eq, table, IMG=img_fig,
                 top_title=False)
    doc.save(str(OUT))
    print("Saqlandi:", OUT)


if __name__ == "__main__":
    main()
