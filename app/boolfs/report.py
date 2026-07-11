"""report.py — natijalar hisoboti (markdown + grafiklar), runs/boolfs/report.md.

Bo'limlar (prompt 7-band):
  1. Ranjirlangan qator: top-20 belgi, r_j bilan ((3.4.5)).
  2. Ф(n') va P(n') grafigi (bitta rasm, ikki o'q).
  3. Sinf juftliklari ajraluvchanlik matritsasi (pairwise Ф, tanlangan λ bilan).
  4. Confusion matrix: YOLO vs YOLO+boolfs ensemble.
  5. Xulosa: qaysi sinflarda yaxshilanish, kam sonli sinflar izohi.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402


def _load(p: Path) -> dict | None:
    return json.loads(p.read_text()) if p.exists() else None


def _md_matrix(M: list[list], labels: list[str], fmt: str = "{}") -> str:
    short = [l[:14] for l in labels]
    head = "| | " + " | ".join(short) + " |"
    sep = "|---" * (len(short) + 1) + "|"
    rows = []
    for i, row in enumerate(M):
        rows.append("| **" + short[i] + "** | "
                    + " | ".join(fmt.format(v) for v in row) + " |")
    return "\n".join([head, sep] + rows)


def _fig_phi_p(art: dict, out_png: Path) -> None:
    phi = art["phi_curve"]
    P = art["P_curve"]
    ns = np.arange(1, len(phi) + 1)
    fig, ax1 = plt.subplots(figsize=(8, 4.5))
    ax1.plot(ns, phi, "o-", color="#1f77b4", ms=3, label="Ф(n′)")
    ax1.set_xlabel("n′ (tanlangan belgilar soni)")
    ax1.set_ylabel("Ф(n′)", color="#1f77b4")
    ax1.tick_params(axis="y", labelcolor="#1f77b4")
    ax2 = ax1.twinx()
    ax2.plot(ns, P, "s-", color="#d62728", ms=3, label="P(n′)")
    ax2.set_ylabel("P(n′) — CV aniqlik", color="#d62728")
    ax2.tick_params(axis="y", labelcolor="#d62728")
    n_star = art["n_star"]
    ax2.axvline(n_star, color="gray", ls="--", lw=1)
    ax2.annotate(f"n′*={n_star}", xy=(n_star, art["P_star"]),
                 xytext=(n_star + 1, art["P_star"]),
                 fontsize=9, color="gray")
    ax1.set_title("Ф(n′) va P(n′) — ranjirlangan qator prefikslari bo'yicha")
    fig.tight_layout()
    fig.savefig(out_png, dpi=130)
    plt.close(fig)


def build(run_dir: str | Path) -> Path:
    """runs/boolfs/ dagi artefaktlardan report.md quradi (bor bo'limlar bilan)."""
    run_dir = Path(run_dir)
    art = _load(run_dir / "artifacts.json")
    ev = _load(run_dir / "eval.json")
    ens = _load(run_dir / "ensemble.json")
    model = _load(run_dir / "model.json")

    L: list[str] = []
    L.append("# boolfs — bulcha belgi tanlash va minimal masofa klassifikatori hisobot\n")
    L.append("Metod: Xamdamov (2017), III bob — (3.2.2) kriteriy, (3.4.5) ranjirlangan "
             "qator, (3.6.2)–(3.6.4) minimal masofa klassifikatori.\n")

    if art:
        L.append(f"- Train ROI: **{art['n_roi_train']}** ta; sinf taqsimoti: "
                 + ", ".join(f"{k}={v}" for k, v in art["class_counts"].items()))
        L.append(f"- Tanlangan belgilar: **n′\\* = {art['n_star']}** / 38, "
                 f"P(n′\\*) = **{art['P_star']:.4f}** (aralash CV: 5-fold + LOO)\n")

        L.append("## 1. Ranjirlangan qator — top-20 belgi ((3.4.5))\n")
        L.append("| n′ | Belgi | r_j = a_j/(b_j+c_j) | Ф(n′) |")
        L.append("|---|---|---|---|")
        for t in art["selection_table"][:20]:
            rj = "∞" if t["r_j"] is None else f"{t['r_j']:.4f}"
            L.append(f"| {t['n']} | `{t['feature']}` | {rj} | {t['phi_prefix']:.4f} |")
        L.append("")

        L.append("## 2. Ф(n′) va P(n′) grafigi\n")
        _fig_phi_p(art, run_dir / "fig_phi_p.png")
        L.append("![Phi va P egri chiziqlari](fig_phi_p.png)\n")

        L.append("## 3. Sinf juftliklari ajraluvchanlik matritsasi (pairwise Ф, λ\\*)\n")
        L.append("Katta qiymat — sinflar tanlangan belgi fazosida yaxshi ajraladi; "
                 "kichigi — ajralmaydi (maqola uchun asosiy jadval).\n")
        L.append(_md_matrix(art["pairwise_phi"], art["pairwise_phi_classes"], "{:.3f}"))
        L.append("")
        # eng yomon ajraladigan juftliklar
        M = np.array(art["pairwise_phi"])
        cls = art["pairwise_phi_classes"]
        pairs = [(M[i, j], cls[i], cls[j]) for i in range(len(cls))
                 for j in range(i + 1, len(cls))]
        pairs.sort()
        L.append("Eng yomon ajraladigan juftliklar: "
                 + "; ".join(f"{p}–{q} (Ф={v:.3f})" for v, p, q in pairs[:3]) + "\n")

    if ev:
        L.append(f"## 4a. boolfs klassifikatori — {ev['split']} GT ROI baholash\n")
        L.append(f"P ((3.6.4)) = **{ev['P']:.4f}** ({ev['n_roi']} ROI)\n")
        L.append("| Sinf | support | precision | recall |")
        L.append("|---|---|---|---|")
        for r in ev["per_class"]:
            L.append(f"| {r['class']} | {r['support']} | {r['precision']:.3f} | {r['recall']:.3f} |")
        L.append("\nConfusion matrix (qatorda — haqiqiy sinf):\n")
        L.append(_md_matrix(ev["confusion"], ev["class_names"]))
        L.append("")

    if ens:
        L.append("## 4b. YOLO vs YOLO+boolfs ensemble (confusion taqqoslash)\n")
        L.append(f"Moslashtirish: IoU≥{ens['iou_thr']}, conf≥{ens['conf_thr']}; "
                 f"mos kelgan detektsiyalar: {ens['n_matched']} "
                 f"(pred={ens['n_pred']}, GT={ens['n_gt']}); vazn: `{ens['weights']}`\n")
        L.append("| α (YOLO ulushi) | P |")
        L.append("|---|---|")
        for k in sorted(ens["alpha_results"], key=float):
            tag = " — faqat boolfs" if float(k) == 0 else (" — faqat YOLO" if float(k) == 1 else "")
            star = " ★" if abs(float(k) - ens["best_alpha"]) < 1e-9 else ""
            L.append(f"| {float(k):.1f}{tag} | {ens['alpha_results'][k]:.4f}{star} |")
        L.append("\n**YOLO (faqat) confusion:**\n")
        L.append(_md_matrix(ens["confusion_yolo"], ens["class_names"]))
        L.append(f"\n**Ensemble (α={ens['best_alpha']}) confusion:**\n")
        L.append(_md_matrix(ens["confusion_ensemble"], ens["class_names"]))
        L.append("")

        L.append("## 5. Xulosa\n")
        py = {r["class"]: r for r in ens["per_class_yolo"]}
        pe = {r["class"]: r for r in ens["per_class_ensemble"]}
        better, worse = [], []
        for c in py:
            dy = pe[c]["recall"] - py[c]["recall"]
            if dy > 1e-9:
                better.append(f"**{c}** (recall {py[c]['recall']:.2f}→{pe[c]['recall']:.2f})")
            elif dy < -1e-9:
                worse.append(f"{c} ({py[c]['recall']:.2f}→{pe[c]['recall']:.2f})")
        acc_y = ens["alpha_results"]["1.0"]
        acc_e = ens["alpha_results"][[k for k in ens["alpha_results"]
                                      if abs(float(k) - ens["best_alpha"]) < 1e-9][0]]
        L.append(f"- Umumiy P: YOLO {acc_y:.4f} → ensemble {acc_e:.4f} "
                 f"({'+' if acc_e >= acc_y else ''}{(acc_e - acc_y) * 100:.1f} punkt).")
        if better:
            L.append("- Yaxshilangan sinflar: " + ", ".join(better) + ".")
        if worse:
            L.append("- Yomonlashgan sinflar: " + ", ".join(worse) + ".")
        if art:
            small = [k for k, v in art["class_counts"].items() if v < 5]
            if small:
                L.append(f"- Kam sonli sinflar ({', '.join(small)}): baholash leave-one-out "
                         "rejimida; misollar juda oz bo'lgani uchun xulosa statistik jihatdan "
                         "ehtiyotkorlik bilan talqin qilinishi kerak — etalon vektor 1–2 "
                         "misolga tayanadi.")
    elif ev:
        L.append("## 5. Xulosa (qisman)\n")
        L.append("Ensemble bosqichi hali bajarilmadi (`ensemble` buyrug'ini ishga "
                 "tushiring) — YOLO bilan taqqoslash shu bosqichda to'ldiriladi.")

    out_md = run_dir / "report.md"
    out_md.write_text("\n".join(L))
    return out_md
