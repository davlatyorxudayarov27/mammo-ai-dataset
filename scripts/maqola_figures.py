# -*- coding: utf-8 -*-
"""maqola_figures.py — maqola/dissertatsiya uchun 5 ta grafik, haqiqiy ma'lumot va
95% bootstrap ishonch oraliqlari bilan.

  fig1_nsweep  — P(n′): pooled CV va val aniqligi, ikkalasi 95% bootstrap CI tasmasi bilan
  fig2_alpha   — α egri: train (tanlov) va val (baholash), α* train'da belgilangan
  fig3_roc     — makro ROC: YOLO / boolfs / ansambl (AUC legendada)
  fig4_sens    — sinflar kesimida sezgirlik: YOLO vs ansambl (support bilan)
  fig5_cm      — chalkashlik matritsasi (ansambl, eng yaxshi detektor)

Palitra dataviz validatorida tekshirilgan (light surface): #2a78d6, #1baf7a, #eda100.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

ROOT = Path(__file__).resolve().parent.parent
MET = ROOT / "runs" / "exp_20260710" / "metrics"

C1, C2, C3 = "#2a78d6", "#1baf7a", "#eda100"
INK, MUTED, GRID = "#1a1a19", "#555555", "#d8d8d4"
BEST = "yolo11l"

L = {
    "uz": dict(
        n_x="Tanlangan belgilar soni n′", pval="Ishonchlilik P",
        cv="CV (train), 95% CI", val="val, 95% CI", nstar="n′* = {n} (CV bo'yicha)",
        a_x="Ansambl vazni α   (0 = faqat boolfs, 1 = faqat YOLO)",
        bacc="Muvozanatli aniqlik", a_tr="train (α* shu yerda tanlanadi)", a_va="val (baholash)",
        astar="α* = {a}", roc_x="1 − o'ziga xoslik (FPR)", roc_y="Sezgirlik (TPR)",
        chance="Tasodif", yolo="YOLO", bf="boolfs", ens="Ansambl",
        sens_y="Sezgirlik (recall)", sup="n=", cm_x="Bashorat qilingan sinf",
        cm_y="Haqiqiy sinf",
    ),
    "ru": dict(
        n_x="Число отобранных признаков n′", pval="Достоверность P",
        cv="CV (train), 95% ДИ", val="val, 95% ДИ", nstar="n′* = {n} (по CV)",
        a_x="Вес ансамбля α   (0 = только boolfs, 1 = только YOLO)",
        bacc="Сбалансированная точность", a_tr="train (здесь выбирается α*)", a_va="val (оценка)",
        astar="α* = {a}", roc_x="1 − специфичность (FPR)", roc_y="Чувствительность (TPR)",
        chance="Случай", yolo="YOLO", bf="boolfs", ens="Ансамбль",
        sens_y="Чувствительность (recall)", sup="n=", cm_x="Предсказанный класс",
        cm_y="Истинный класс",
    ),
    "en": dict(
        n_x="Number of selected features n′", pval="Reliability P",
        cv="CV (train), 95% CI", val="val, 95% CI", nstar="n′* = {n} (by CV)",
        a_x="Ensemble weight α   (0 = boolfs only, 1 = YOLO only)",
        bacc="Balanced accuracy", a_tr="train (α* selected here)", a_va="val (evaluation)",
        astar="α* = {a}", roc_x="1 − specificity (FPR)", roc_y="Sensitivity (TPR)",
        chance="Chance", yolo="YOLO", bf="boolfs", ens="Ensemble",
        sens_y="Sensitivity (recall)", sup="n=", cm_x="Predicted class",
        cm_y="True class",
    ),
}

CLS = {
    "uz": {"BIRADS12": "BIRADS 1-2", "BIRADS45": "BIRADS 4-5",
           "architectural_distortion": "arx. buzilish", "asymmetry": "assimetriya",
           "calcification": "kalsifikatsiya", "lymph_node": "limfa tuguni",
           "mass": "o'sma", "other": "boshqa"},
    "ru": {"BIRADS12": "BIRADS 1-2", "BIRADS45": "BIRADS 4-5",
           "architectural_distortion": "арх. перестройка", "asymmetry": "асимметрия",
           "calcification": "кальцинаты", "lymph_node": "лимфоузел",
           "mass": "образование", "other": "прочее"},
    "en": {"BIRADS12": "BIRADS 1-2", "BIRADS45": "BIRADS 4-5",
           "architectural_distortion": "arch. distortion", "asymmetry": "asymmetry",
           "calcification": "calcification", "lymph_node": "lymph node",
           "mass": "mass", "other": "other"},
}


def _style(ax, ygrid=True):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
        ax.spines[s].set_linewidth(0.8)
    if ygrid:
        ax.grid(axis="y", color=GRID, linewidth=0.6, alpha=0.7)
    ax.set_axisbelow(True)
    ax.tick_params(colors=MUTED, labelsize=9, length=0)


def _save(fig, out):
    fig.savefig(out, bbox_inches="tight", facecolor="white", dpi=200)
    plt.close(fig)


def load():
    met = json.loads((MET / "metrics.json").read_text())
    nsw = json.loads((MET / "nsweep_ci.json").read_text())
    roc = np.load(MET / "roc.npz")
    return met, nsw, roc


# ------------------------------------------------------------------ fig1 --- #
def fig1_nsweep(nsw, lang, out):
    t = L[lang]
    rows = nsw["rows"]
    xs = np.array([r["n"] for r in rows])
    cv = np.array([r["cv_acc"] for r in rows])
    cvlo = np.array([r["cv_acc_lo"] for r in rows])
    cvhi = np.array([r["cv_acc_hi"] for r in rows])
    va = np.array([r["val_acc"] for r in rows])
    lo = np.array([r["ci"]["accuracy"]["lo"] for r in rows])
    hi = np.array([r["ci"]["accuracy"]["hi"] for r in rows])
    n_star = nsw["n_star_by_cv"]

    fig, ax = plt.subplots(figsize=(7.2, 3.9), dpi=200)
    _style(ax)
    ax.axvline(n_star, color=MUTED, linewidth=1.0, linestyle=(0, (3, 3)), alpha=0.8, zorder=1)
    ax.fill_between(xs, lo, hi, color=C1, alpha=0.13, linewidth=0, zorder=2)
    ax.fill_between(xs, cvlo, cvhi, color=C2, alpha=0.13, linewidth=0, zorder=2)
    ax.plot(xs, va, color=C1, linewidth=2.0, marker="o", markersize=4.5,
            markeredgecolor="white", markeredgewidth=1.0, zorder=4)
    ax.plot(xs, cv, color=C2, linewidth=2.0, marker="s", markersize=4.5,
            markeredgecolor="white", markeredgewidth=1.0, zorder=4)
    ax.annotate(t["val"], xy=(xs[-1], va[-1]), xytext=(7, 3), textcoords="offset points",
                fontsize=8.8, color=C1, fontweight="bold", va="center")
    ax.annotate(t["cv"], xy=(xs[-1], cv[-1]), xytext=(7, -2), textcoords="offset points",
                fontsize=8.8, color=C2, fontweight="bold", va="center")
    i = int(np.where(xs == n_star)[0][0])
    ax.annotate(f"{va[i]:.3f}", xy=(n_star, va[i]), xytext=(-9, 8), textcoords="offset points",
                ha="right", fontsize=8.5, color=C1, fontweight="bold")
    ymin = min(lo.min(), cvlo.min()) - 0.03
    ax.annotate(t["nstar"].format(n=n_star), xy=(n_star, ymin), xytext=(6, 0),
                textcoords="offset points", ha="left", va="bottom", fontsize=8.5, color=MUTED)
    ax.set_xlabel(t["n_x"], fontsize=9.5, color=INK)
    ax.set_ylabel(t["pval"], fontsize=9.5, color=INK)
    ax.set_xticks([x for x in xs if x in (1, 3, 5, 8, 13, 21, 28, 34, 38)])
    ax.set_xlim(-1, 46)
    ax.set_ylim(ymin, max(hi.max(), cvhi.max()) + 0.03)
    fig.tight_layout()
    _save(fig, out)


# ------------------------------------------------------------------ fig2 --- #
def fig2_alpha(met, lang, out):
    t = L[lang]
    ac = met["alpha_curves"][BEST]
    a_star = ac["alpha_star"]
    tr = {float(k): v for k, v in ac["train"].items()}
    va = {float(k): v for k, v in ac["val"].items()}
    xs = sorted(tr)

    fig, ax = plt.subplots(figsize=(7.2, 3.9), dpi=200)
    _style(ax)
    ax.axvline(a_star, color=MUTED, linewidth=1.0, linestyle=(0, (3, 3)), alpha=0.85, zorder=1)
    ax.plot(xs, [tr[a] for a in xs], color=C2, linewidth=1.8, linestyle=(0, (5, 2)), zorder=3)
    ax.plot(xs, [va[a] for a in xs], color=C1, linewidth=2.2, zorder=4)
    ax.plot([a_star], [va[a_star]], marker="o", markersize=8, color=C1,
            markeredgecolor="white", markeredgewidth=1.6, zorder=5)
    ax.annotate(t["a_va"], xy=(xs[-1], va[xs[-1]]), xytext=(7, 2), textcoords="offset points",
                fontsize=8.8, color=C1, fontweight="bold", va="center")
    ax.annotate(t["a_tr"], xy=(xs[-1], tr[xs[-1]]), xytext=(7, -2), textcoords="offset points",
                fontsize=8.8, color=C2, fontweight="bold", va="center")
    ax.annotate(f"{t['astar'].format(a=a_star)}\n{va[a_star]:.3f}", xy=(a_star, va[a_star]),
                xytext=(0, 12), textcoords="offset points", ha="center", fontsize=8.6,
                color=C1, fontweight="bold")
    ax.set_xlabel(t["a_x"], fontsize=9.5, color=INK)
    ax.set_ylabel(t["bacc"], fontsize=9.5, color=INK)
    ax.set_xticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_xlim(-0.03, 1.32)
    fig.tight_layout()
    _save(fig, out)


# ------------------------------------------------------------------ fig3 --- #
def fig3_roc(met, roc, lang, out):
    t = L[lang]
    d = met["detectors"][BEST]
    fpr = roc[f"{BEST}_fpr"]
    fig, ax = plt.subplots(figsize=(5.0, 4.6), dpi=200)
    _style(ax, ygrid=False)
    ax.grid(color=GRID, linewidth=0.6, alpha=0.6)
    ax.plot([0, 1], [0, 1], color=MUTED, linewidth=1.0, linestyle=(0, (3, 3)), zorder=1)
    ax.annotate(t["chance"], xy=(0.62, 0.58), fontsize=8.2, color=MUTED, rotation=38)
    for key, col, lab, auc in (
            (f"{BEST}_tpr_ens", C1, t["ens"], d["ensemble"]["auc_macro"]),
            (f"{BEST}_tpr_yolo", C2, t["yolo"], d["yolo"]["auc_macro"]),
            (f"{BEST}_tpr_bool", C3, t["bf"], d["boolfs"]["auc_macro"])):
        ax.plot(fpr, roc[key], color=col, linewidth=2.0, zorder=3,
                label=f"{lab}  (AUC = {auc:.3f})")
    leg = ax.legend(loc="lower right", frameon=False, fontsize=9)
    for txt in leg.get_texts():
        txt.set_color(INK)
    ax.set_xlabel(t["roc_x"], fontsize=9.5, color=INK)
    ax.set_ylabel(t["roc_y"], fontsize=9.5, color=INK)
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.02)
    fig.tight_layout()
    _save(fig, out)


# ------------------------------------------------------------------ fig4 --- #
def fig4_sens(met, lang, out):
    t = L[lang]
    d = met["detectors"][BEST]
    names = met["class_names"]
    py = {x["class"]: x for x in d["yolo"]["per_class"]}
    pe = {x["class"]: x for x in d["ensemble"]["per_class"]}
    present = [n for n in names if py[n]["support"] > 0]
    present.sort(key=lambda n: -py[n]["support"])

    y_ = np.arange(len(present))
    h = 0.36
    fig, ax = plt.subplots(figsize=(7.2, 0.62 * len(present) + 1.3), dpi=200)
    _style(ax, ygrid=False)
    ax.grid(axis="x", color=GRID, linewidth=0.6, alpha=0.7)
    for i, n in enumerate(present):
        sy = py[n]["sensitivity"] or 0.0
        se = pe[n]["sensitivity"] or 0.0
        ax.barh(y_[i] + h / 2 + 0.01, se, height=h, color=C1, zorder=3)
        ax.barh(y_[i] - h / 2 - 0.01, sy, height=h, color=C2, zorder=3)
        ax.annotate(f"{se:.2f}", xy=(se, y_[i] + h / 2 + 0.01), xytext=(4, 0),
                    textcoords="offset points", va="center", fontsize=8.2,
                    color=C1, fontweight="bold")
        ax.annotate(f"{sy:.2f}", xy=(sy, y_[i] - h / 2 - 0.01), xytext=(4, 0),
                    textcoords="offset points", va="center", fontsize=8.2, color=C2)
    ax.set_yticks(y_)
    ax.set_yticklabels([f"{CLS[lang][n]}  ({t['sup']}{py[n]['support']})" for n in present],
                       fontsize=9, color=INK)
    ax.invert_yaxis()
    ax.set_xlabel(t["sens_y"], fontsize=9.5, color=INK)
    ax.set_xlim(0, 1.13)
    handles = [plt.Rectangle((0, 0), 1, 1, color=C1), plt.Rectangle((0, 0), 1, 1, color=C2)]
    leg = ax.legend(handles, [t["ens"], t["yolo"]], loc="lower right", frameon=False, fontsize=9)
    for txt in leg.get_texts():
        txt.set_color(INK)
    fig.tight_layout()
    _save(fig, out)


# ------------------------------------------------------------------ fig5 --- #
def fig5_cm(met, lang, out):
    t = L[lang]
    d = met["detectors"][BEST]
    names = met["class_names"]
    M = np.array(d["ensemble"]["confusion"], dtype=float)
    keep = [i for i in range(len(names)) if M[i].sum() > 0 or M[:, i].sum() > 0]
    M = M[np.ix_(keep, keep)]
    lab = [CLS[lang][names[i]] for i in keep]
    row = M.sum(axis=1, keepdims=True)
    Mn = np.divide(M, np.where(row == 0, 1, row))

    cmap = LinearSegmentedColormap.from_list("blue1", ["#ffffff", C1])
    fig, ax = plt.subplots(figsize=(6.3, 5.4), dpi=200)
    im = ax.imshow(Mn, cmap=cmap, vmin=0, vmax=1)
    for i in range(len(keep)):
        for j in range(len(keep)):
            if M[i, j] == 0:
                continue
            ax.text(j, i, f"{int(M[i, j])}", ha="center", va="center", fontsize=8.6,
                    color="white" if Mn[i, j] > 0.55 else INK,
                    fontweight="bold" if i == j else "normal")
    ax.set_xticks(range(len(keep)))
    ax.set_yticks(range(len(keep)))
    ax.set_xticklabels(lab, rotation=38, ha="right", fontsize=8.6, color=INK)
    ax.set_yticklabels(lab, fontsize=8.6, color=INK)
    ax.set_xlabel(t["cm_x"], fontsize=9.5, color=INK)
    ax.set_ylabel(t["cm_y"], fontsize=9.5, color=INK)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0)
    cb = fig.colorbar(im, ax=ax, fraction=0.045, pad=0.03)
    cb.outline.set_visible(False)
    cb.ax.tick_params(labelsize=8, colors=MUTED, length=0)
    fig.tight_layout()
    _save(fig, out)


def build_all(lang, outdir: Path):
    met, nsw, roc = load()
    outdir.mkdir(parents=True, exist_ok=True)
    fig1_nsweep(nsw, lang, outdir / "fig1_nsweep.png")
    fig2_alpha(met, lang, outdir / "fig2_alpha.png")
    fig3_roc(met, roc, lang, outdir / "fig3_roc.png")
    fig4_sens(met, lang, outdir / "fig4_sens.png")
    fig5_cm(met, lang, outdir / "fig5_cm.png")
    return outdir


if __name__ == "__main__":
    for lg in ("uz", "ru", "en"):
        d = build_all(lg, ROOT / "doc_assets_exp2026" / lg)
        print(f"[figures] {lg}: {d}")
