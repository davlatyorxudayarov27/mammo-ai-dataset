# -*- coding: utf-8 -*-
"""figures_external.py — tashqi validatsiya (CBIS-DDSM) rasmlari, 3 tilda.

  m3_f1_ksweep   ko'chirilgan belgi to'plami tasodifiydan yaxshiroqmi?
                 own(k) / src(k) / rand(k)±band, ikki yo'nalish (V2_scale zinapoya).

Xulosa vizual: src egri rand tasmasidan yuqori EMAS — ko'p k da ichida yoki pastida.
Palitra: own=C1 (ko'k), src=C3 (to'q sariq), rand=kulrang tasma.

Chiqish: doc_assets_big/<til>/m3_f1_ksweep.png (+ .pdf)
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
EXT = ROOT / "runs" / "exp_external_cbis"
RUNG = "V2_scale"          # harmonizatsiya qilingan zinapoya

C1, C3 = "#2a78d6", "#eda100"
INK, MUTED, GRID, BAND = "#1a1a19", "#555555", "#d8d8d4", "#c9c9c4"

L = {
    "uz": dict(
        x="Tanlangan belgilar soni k", y="Muvozanatli aniqlik (maqsad baza)",
        own="own — maqsad baza o'z reytingi", src="src — manba reytingi ko'chirilgan",
        rand="rand — tasodifiy k belgi (95%)",
        o2c="Bizniki → CBIS-DDSM", c2o="CBIS-DDSM → Bizniki",
    ),
    "ru": dict(
        x="Число отобранных признаков k", y="Сбаланс. точность (целевая база)",
        own="own — собственный рейтинг цели", src="src — перенесённый рейтинг источника",
        rand="rand — случайные k признаков (95%)",
        o2c="Наша → CBIS-DDSM", c2o="CBIS-DDSM → наша",
    ),
    "en": dict(
        x="Number of selected features k", y="Balanced accuracy (target database)",
        own="own — target's own ranking", src="src — transferred source ranking",
        rand="rand — random k features (95\\%)".replace("\\%", "%"),
        o2c="Ours $\\to$ CBIS-DDSM".replace("$\\to$", "→").replace("\\", ""),
        c2o="CBIS-DDSM $\\to$ Ours".replace("$\\to$", "→").replace("\\", ""),
    ),
}
# soddalashtirilgan sarlavhalar (matematik belgisiz)
L["en"]["o2c"] = "Ours → CBIS-DDSM"
L["en"]["c2o"] = "CBIS-DDSM → Ours"


def _save(fig, out):
    fig.savefig(out, bbox_inches="tight", facecolor="white", dpi=200)
    fig.savefig(str(out)[:-4] + ".pdf", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def _panel(ax, rows, t):
    k = [r["k"] for r in rows]
    own = [r["own_bacc"] for r in rows]
    src = [r["src_bacc"] for r in rows]
    lo = [r["rand_bacc_lo"] for r in rows]
    hi = [r["rand_bacc_hi"] for r in rows]
    mean = [r["rand_bacc_mean"] for r in rows]

    ax.fill_between(k, lo, hi, color=BAND, alpha=0.55, lw=0, label=t["rand"], zorder=1)
    ax.plot(k, mean, color=MUTED, lw=1.0, ls=(0, (4, 3)), zorder=2)
    ax.plot(k, own, color=C1, lw=2.0, marker="o", ms=5, label=t["own"], zorder=4)
    ax.plot(k, src, color=C3, lw=2.0, marker="s", ms=5, label=t["src"], zorder=3)

    ax.set_xlabel(t["x"], color=INK, fontsize=9)
    ax.set_xticks(k)
    ax.tick_params(colors=MUTED, labelsize=8)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.grid(axis="y", color=GRID, lw=0.6, alpha=0.7)
    ax.set_axisbelow(True)


def build(lang):
    d = json.loads((EXT / "k_sweep.json").read_text())
    rd = d["rungs"][RUNG]
    t = L[lang]
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.1), sharey=True)
    _panel(axes[0], rd["ours_to_cbis"], t)
    _panel(axes[1], rd["cbis_to_ours"], t)
    axes[0].set_title(t["o2c"], color=INK, fontsize=9.5, pad=6)
    axes[1].set_title(t["c2o"], color=INK, fontsize=9.5, pad=6)
    axes[0].set_ylabel(t["y"], color=INK, fontsize=9)

    h, lbls = axes[0].get_legend_handles_labels()
    order = [lbls.index(x) for x in (t["own"], t["src"], t["rand"])]
    fig.legend([h[i] for i in order], [lbls[i] for i in order],
               loc="lower center", ncol=3, frameon=False, fontsize=8,
               bbox_to_anchor=(0.5, -0.02))
    fig.subplots_adjust(bottom=0.28, wspace=0.08)

    out = ROOT / "doc_assets_big" / lang / "m3_f1_ksweep.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    _save(fig, out)
    print(f"[ext-fig] {lang}: {out.name}")


if __name__ == "__main__":
    for lg in ("uz", "ru", "en"):
        build(lg)
