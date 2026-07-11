# -*- coding: utf-8 -*-
"""make_manuscript_tex.py — IEEE JBHI qo'lyozmasini (LaTeX) natijalar JSON'idan quradi.

Muhim tamoyil: **birorta raqam qo'lda terilmaydi.** Barchasi runs/ dagi JSON'lardan
olinadi va \newcommand makroslariga aylantiriladi, so'ng matnda faqat makros ishlatiladi.
Shu sababli natija qayta hisoblansa, qo'lyozma avtomatik yangilanadi.

Chiqish: manuscript_jbhi/manuscript.tex  (+ fig/ ga vektor PDF'lar nusxalanadi)
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIG = ROOT / "runs/exp_big_20260710"
SMALL = ROOT / "runs/exp_20260710/exp01_fit"
EXT = ROOT / "runs/exp_external_cbis"
FIGSRC = ROOT / "doc_assets_big/en"
OUT = ROOT / "manuscript_jbhi"
BEST = "trained_8class_ai_v2_ep50"

FIGS = ["m1_f1_nsweep", "m1_f2_stability", "m1_f3_ranking", "m1_f4_phi",
        "m2_f1_alpha", "m2_f2_roc", "m2_f3_sens", "m2_f4_cm", "m2_f5_leakage",
        "m3_f1_ksweep"]

# harmonizatsiya zinapoyasi
HARM_RUNGS = ["V0_raw", "V1_intensity", "V2_scale", "V3_noshape"]
HARM_SCALE = "V2_scale"        # intensivlik+masshtab moslashtirilgan asosiy zinapoya


def _opt(path):
    return json.loads(path.read_text()) if path.exists() else None


def load():
    d = {
        "art": json.loads((BIG / "artifacts.json").read_text()),
        "met": json.loads((BIG / "metrics/metrics.json").read_text()),
        "stab": json.loads((BIG / "stability_multi.json").read_text()),
        "agr": json.loads((BIG / "agreement.json").read_text()),
        "iou": json.loads((BIG / "iou_sensitivity.json").read_text()),
        "small": json.loads((SMALL / "artifacts.json").read_text()),
    }
    d["ext"] = _opt(EXT / "results.json")
    d["harm"] = _opt(EXT / "harmonise.json")
    d["subset"] = _opt(EXT / "subset_transfer.json")
    d["ksweep"] = _opt(EXT / "k_sweep.json")
    return d


# ───────────────────────── formatlash ────────────────────────── #

def n(x, nd=3):
    if x is None or (isinstance(x, float) and x != x):
        return "--"
    return f"{x:.{nd}f}"


def pp(x, nd=1):
    return f"{x * 100:+.{nd}f}"


def pv(p):
    if p is None:
        return "--"
    return "$<$0.001" if p < 0.001 else f"{p:.3f}"


def ci(v, c, nd=3):
    if not c:
        return n(v, nd)
    return f"{n(v, nd)} [{n(c['lo'], nd)}, {n(c['hi'], nd)}]"


def thousands(x):
    return f"{int(x):,}"


# ───────────────────── makroslar (raqamlar) ───────────────────── #

def macros(D):
    art, met, stab, agr, iou = D["art"], D["met"], D["stab"], D["agr"], D["iou"]
    best = met["detectors"][BEST]
    big = {l["n"]: l for l in stab["big"]["levels"]}
    sm = {l["n"]: l for l in stab["small"]["levels"]}
    nsw = {r["n"]: r for r in art["nsweep"]}
    tb, ts = stab["big"]["top_ranks"], stab["small"]["top_ranks"]

    M = {
        # datasetlar
        "RoiTrain": thousands(art["n_roi_train"]),
        "RoiVal": thousands(art["n_roi_val"]),
        "RoiSmall": thousands(stab["small"]["n_roi"]),
        "NStar": str(art["n_star"]),
        "NStarSmall": str(D["small"]["n_star"]),
        "NFeat": "38",
        # boolfs val
        "BfAcc": n(art["val_at_nstar"]["accuracy"]),
        "BfBacc": ci(art["val_at_nstar"]["balanced_accuracy"],
                     art["val_at_nstar"]["ci"]["balanced_accuracy"]),
        "BfAuc": ci(art["val_at_nstar"]["auc_macro"], art["val_at_nstar"]["ci"]["auc_macro"]),
        "BfMcc": n(art["val_at_nstar"]["mcc"]),
        # barqarorlik
        "KunBigMin": n(min(l["kuncheva"] for l in stab["big"]["levels"])),
        "KunBigFive": n(big[5]["kuncheva"]),
        "KunSmallMin": n(min(l["kuncheva"] for l in stab["small"]["levels"])),
        "JacBigMax": n(big[36]["jaccard"]),
        "Spearman": n(agr["spearman"]),
        "AgrThree": n(agr["agreement"]["3"]),
        "AgrFive": n(agr["agreement"]["5"]),
        "AgrEight": n(agr["agreement"]["8"]),
        "TopBig": tb[0]["feature"].replace("_", r"\_"),
        "TopBigMean": n(tb[0]["mean_rank"], 2),
        "TopBigStd": n(tb[0]["std_rank"], 2),
        "TopSmall": ts[0]["feature"].replace("_", r"\_"),
        "TopSmallMean": n(ts[0]["mean_rank"], 2),
        "TopSmallStd": n(ts[0]["std_rank"], 2),
        # n' sweep
        "CvBaccThirteen": n(nsw[13]["cv_bacc"]),
        "CvBaccTwentyone": n(nsw[21]["cv_bacc"]),
        "CvAccFull": n(nsw[38]["cv_acc"]),
        "CvAccStar": n(nsw[36]["cv_acc"]),
        "CvBaccFull": n(nsw[38]["cv_bacc"]),
        "CvBaccStar": n(nsw[36]["cv_bacc"]),
        "PhiOne": n(art["selection_table"][0]["phi_prefix"], 2),
        "PhiFull": n(art["selection_table"][-1]["phi_prefix"], 2),
        # ansambl (toza detektor)
        "NClean": thousands(best["n_matched_clean"]),
        "AlphaStar": n(best["alpha_star"], 2),
        "YAcc": n(best["yolo"]["accuracy"]),
        "EAcc": n(best["ensemble"]["accuracy"]),
        "PAcc": pv(best["delta"]["accuracy"]["p"]),
        "DAcc": pp(best["delta"]["accuracy"]["delta"]),
        "YBacc": n(best["yolo"]["balanced_accuracy"]),
        "EBacc": n(best["ensemble"]["balanced_accuracy"]),
        "PBacc": pv(best["delta"]["balanced_accuracy"]["p"]),
        "DBacc": pp(best["delta"]["balanced_accuracy"]["delta"]),
        "YAuc": n(best["yolo"]["auc_macro"]),
        "EAuc": n(best["ensemble"]["auc_macro"]),
        "PAuc": pv(best["delta"]["auc_macro"]["p"]),
        "DAuc": pp(best["delta"]["auc_macro"]["delta"]),
        "BfOnlyAcc": n(best["boolfs"]["accuracy"]),
        "BfOnlyAuc": n(best["boolfs"]["auc_macro"]),
        # leakage
        "NLeakImgs": "24",
        "LeakS": str(met["detectors"]["yolo11s_8class"]["n_leaked"]),
        "LeakL": str(met["detectors"]["trained_8class_yolo11l"]["n_leaked"]),
        "LeakV": str(best["n_leaked"]),
        "AlphaS": n(met["detectors"]["yolo11s_8class"]["alpha_star"], 2),
        "AlphaL": n(met["detectors"]["trained_8class_yolo11l"]["alpha_star"], 2),
        # IoU sezuvchanlik
        "IouSevenBacc": pp(iou["detectors"][BEST]["0.7"]["delta"]["balanced_accuracy"]["delta"]),
        "IouSevenP": pv(iou["detectors"][BEST]["0.7"]["delta"]["balanced_accuracy"]["p"]),
        "IouFiveBacc": pp(iou["detectors"][BEST]["0.5"]["delta"]["balanced_accuracy"]["delta"]),
        "IouFiveP": pv(iou["detectors"][BEST]["0.5"]["delta"]["balanced_accuracy"]["p"]),
        "IouSevenN": thousands(iou["detectors"][BEST]["0.7"]["n_clean"]),
        "IouSevenYBacc": n(iou["detectors"][BEST]["0.7"]["yolo"]["balanced_accuracy"]),
        "AucGainMin": pp(min(iou["detectors"][t][k]["delta"]["auc_macro"]["delta"]
                             for t in iou["detectors"] for k in ("0.3", "0.5", "0.7"))),
        "AucGainMax": pp(max(iou["detectors"][t][k]["delta"]["auc_macro"]["delta"]
                             for t in iou["detectors"] for k in ("0.3", "0.5", "0.7"))),
        # sinf kesimi
        "SensBiradsY": n([p for p in best["yolo"]["per_class"] if p["class"] == "BIRADS12"][0]["sensitivity"]),
        "SensBiradsE": n([p for p in best["ensemble"]["per_class"] if p["class"] == "BIRADS12"][0]["sensitivity"]),
        "SensAsymY": n([p for p in best["yolo"]["per_class"] if p["class"] == "asymmetry"][0]["sensitivity"]),
        "SensAsymE": n([p for p in best["ensemble"]["per_class"] if p["class"] == "asymmetry"][0]["sensitivity"]),
        "PrecBirads": n([p for p in best["ensemble"]["per_class"] if p["class"] == "BIRADS12"][0]["precision"]),
    }

    EXT_KEYS = ["ExtTrain", "ExtTest", "ExtInAcc", "ExtInBacc", "ExtInAuc", "ExtZsAcc",
                "ExtZsBacc", "ExtZsAuc", "ExtRevBacc", "ExtRevAuc", "ExtOursBacc",
                "ExtOursAuc", "ExtRhoBig", "ExtAgrBigThree", "ExtAgrBigFive",
                "ExtAgrOursThree", "ExtRhoOurs", "ExtTopOne", "ExtTopTwo", "ExtKunMin",
                # harmonizatsiya zinapoyasi + to'plam-ko'chirish
                "HarmRhoRaw", "HarmRhoScale", "HarmTopThree", "HarmTopFive",
                "HarmInOurs", "HarmInCbis", "HarmTransfer",
                "KsMedPct", "KsFracBeat", "KsNComp"]
    M.update({k: "??" for k in EXT_KEYS})     # tashqi natija yo'q bo'lsa ham .tex qurilsin

    harm = D["harm"]
    if harm:
        rg = harm["rungs"]
        sc = rg[HARM_SCALE]
        M.update({
            "HarmRhoRaw": n(rg["V0_raw"]["spearman"], 2),
            "HarmRhoScale": n(sc["spearman"], 2),
            # top-3 kesishuvi barcha zinapoyada eng katta qiymati (hammasi 0.000)
            "HarmTopThree": n(max(rg[r]["agreement"]["3"] for r in HARM_RUNGS)),
            "HarmTopFive": n(sc["agreement"]["5"]),
            "HarmInOurs": n(sc["in_ours"]["balanced_accuracy"]),
            "HarmInCbis": n(sc["in_cbis"]["balanced_accuracy"]),
            "HarmTransfer": n(sc["ours_to_cbis"]["balanced_accuracy"]),
        })

    ks = D["ksweep"]
    if ks:
        # faqat haqiqatan farqli to'plamlar (kesishuv < 0.6) bo'yicha manba persentili
        ps = [row["src_pctile_bacc"]
              for rd in ks["rungs"].values()
              for dirn in ("ours_to_cbis", "cbis_to_ours")
              for row in rd[dirn] if row["overlap"] < 0.6]
        ps.sort()
        med = ps[len(ps) // 2] if len(ps) % 2 else (ps[len(ps) // 2 - 1] + ps[len(ps) // 2]) / 2
        M.update({
            "KsMedPct": str(int(round(med * 100))),
            "KsFracBeat": str(int(round(100 * sum(p > 0.5 for p in ps) / len(ps)))),
            "KsNComp": str(len(ps)),
        })

    ext = D["ext"]
    if ext:
        M.update({
            "ExtTrain": thousands(sum(ext["counts"]["cbis_train"].values())),
            "ExtTest": thousands(sum(ext["counts"]["cbis_test"].values())),
            "ExtInAcc": n(ext["in_domain_cbis"]["accuracy"]),
            "ExtInBacc": n(ext["in_domain_cbis"]["balanced_accuracy"]),
            "ExtInAuc": n(ext["in_domain_cbis"]["auc_macro"]),
            "ExtZsAcc": n(ext["zero_shot_ours_to_cbis"]["accuracy"]),
            "ExtZsBacc": n(ext["zero_shot_ours_to_cbis"]["balanced_accuracy"]),
            "ExtZsAuc": n(ext["zero_shot_ours_to_cbis"]["auc_macro"]),
            "ExtRevBacc": n(ext["zero_shot_cbis_to_ours"]["balanced_accuracy"]),
            "ExtRevAuc": n(ext["zero_shot_cbis_to_ours"]["auc_macro"]),
            "ExtOursBacc": n(ext["in_domain_ours"]["balanced_accuracy"]),
            "ExtOursAuc": n(ext["in_domain_ours"]["auc_macro"]),
            "ExtRhoBig": n(ext["cross_db"]["big8_vs_cbis"]["spearman"]),
            "ExtAgrBigThree": n(ext["cross_db"]["big8_vs_cbis"]["agreement"]["3"]),
            "ExtAgrBigFive": n(ext["cross_db"]["big8_vs_cbis"]["agreement"]["5"]),
            "ExtAgrOursThree": n(ext["cross_db"]["ours2_vs_cbis"]["agreement"]["3"]),
            "ExtRhoOurs": n(ext["cross_db"]["ours2_vs_cbis"]["spearman"]),
            "ExtTopOne": ext["orders"]["cbis"][0].replace("_", r"\_"),
            "ExtTopTwo": ext["orders"]["cbis"][1].replace("_", r"\_"),
            "ExtKunMin": n(min(l["kuncheva"] for l in ext["stability_cbis"]["levels"])),
        })
    return M


def emit_macros(M):
    return "\n".join(rf"\newcommand{{\{k}}}{{{v}}}" for k, v in sorted(M.items()))


# ─────────────────────── jadvallar ─────────────────────── #

def tab_metrics(D):
    b = D["met"]["detectors"][BEST]
    rows = [
        ("Accuracy", "accuracy"), ("Balanced accuracy", "balanced_accuracy"),
        ("Sensitivity (macro)", "sensitivity_macro"), ("Specificity (macro)", "specificity_macro"),
        ("Precision (macro)", "precision_macro"), ("F1 (macro)", "f1_macro"),
        ("ROC-AUC (macro)", "auc_macro"), ("MCC", "mcc"), ("Cohen's $\\kappa$", "kappa"),
    ]
    out = []
    for lab, k in rows:
        d = b["delta"].get(k)
        out.append(f"{lab} & {ci(b['boolfs'][k], b['boolfs']['ci'].get(k))} & "
                   f"{ci(b['yolo'][k], b['yolo']['ci'].get(k))} & "
                   f"\\textbf{{{ci(b['ensemble'][k], b['ensemble']['ci'].get(k))}}} & "
                   f"{pp(d['delta']) if d else '--'} & {pv(d['p']) if d else '--'} \\\\")
    return "\n".join(out)


def tab_iou(D):
    iou = D["iou"]
    lbl = {"yolo11s_8class": "YOLO11s", "trained_8class_yolo11l": "YOLO11l",
           BEST: "YOLO11l-v2 (clean)"}
    out = []
    for tag in ("yolo11s_8class", "trained_8class_yolo11l", BEST):
        for i, thr in enumerate(("0.3", "0.5", "0.7")):
            e = iou["detectors"][tag][thr]
            d = e["delta"]
            name = lbl[tag] if i == 0 else ""
            out.append(f"{name} & {thr} & {thousands(e['n_clean'])} & {n(e['alpha_star'], 2)} & "
                       f"{pp(d['accuracy']['delta'])} ({pv(d['accuracy']['p'])}) & "
                       f"{pp(d['balanced_accuracy']['delta'])} ({pv(d['balanced_accuracy']['p'])}) & "
                       f"{pp(d['auc_macro']['delta'])} ({pv(d['auc_macro']['p'])}) \\\\")
        out.append(r"\addlinespace[2pt]")
    return "\n".join(out[:-1])


def tab_stability(D):
    big = {l["n"]: l for l in D["stab"]["big"]["levels"]}
    sm = {l["n"]: l for l in D["stab"]["small"]["levels"]}
    ag = D["agr"]["agreement"]
    ext = D["ext"]
    ek = {l["n"]: l["kuncheva"] for l in ext["stability_cbis"]["levels"]} if ext else {}
    out = []
    for k in (3, 5, 8, 13, 21, 28, 34, 36):
        e = n(ek[k]) if k in ek else "--"
        out.append(f"{k} & {n(big[k]['kuncheva'])} & {n(big[k]['jaccard'])} & "
                   f"{n(sm[k]['kuncheva'])} & {e} & {n(ag[str(k)])} \\\\")
    return "\n".join(out)


def tab_external(D):
    e = D["ext"]
    if not e:
        return "% tashqi natijalar hali yo'q"
    rows = [
        ("In-domain: Ours $\\to$ Ours", e["in_domain_ours"]),
        ("In-domain: CBIS $\\to$ CBIS", e["in_domain_cbis"]),
        ("Transfer: Ours $\\to$ CBIS", e["zero_shot_ours_to_cbis"]),
        ("Transfer: CBIS $\\to$ Ours", e["zero_shot_cbis_to_ours"]),
    ]
    return "\n".join(
        f"{lab} & {r['n']} & {n(r['accuracy'])} & {ci(r['balanced_accuracy'], r['ci']['balanced_accuracy'])} "
        f"& {ci(r['auc_macro'], r['ci']['auc_macro'])} & {n(r['mcc'])} \\\\"
        for lab, r in rows)


def tab_crossdb(D):
    e = D["ext"]
    if not e:
        return "% tashqi natijalar hali yo'q"
    lbl = {"big8_vs_small8": "Large (ours) vs.\\ Small (ours) --- same archive",
           "big8_vs_cbis": "Large (ours) vs.\\ CBIS-DDSM --- independent",
           "small8_vs_cbis": "Small (ours) vs.\\ CBIS-DDSM --- independent",
           "ours2_vs_cbis": "Large, 2-class vs.\\ CBIS-DDSM --- matched classes"}
    order = ["big8_vs_small8", "big8_vs_cbis", "small8_vs_cbis", "ours2_vs_cbis"]
    return "\n".join(
        f"{lbl[k]} & {n(e['cross_db'][k]['spearman'])} & "
        + " & ".join(n(e["cross_db"][k]["agreement"][str(t)]) for t in (3, 5, 8, 13)) + r" \\"
        for k in order)


def tab_harmonise(D):
    h = D["harm"]
    if not h:
        return "% harmonizatsiya natijalari hali yo'q"
    lbl = {"V0_raw": "V0: raw (as extracted)",
           "V1_intensity": "V1: $+$ per-ROI min--max",
           "V2_scale": "V2: $+$ resize to $128\\times128$",
           "V3_noshape": "V3: $-$ shape features"}
    out = []
    for r in HARM_RUNGS:
        rd = h["rungs"][r]
        out.append(
            f"{lbl[r]} & {n(rd['spearman'], 2)} & {n(rd['agreement']['3'])} & "
            f"{n(rd['agreement']['5'])} & {n(rd['in_ours']['balanced_accuracy'])} & "
            f"{n(rd['in_cbis']['balanced_accuracy'])} & "
            f"{n(rd['ours_to_cbis']['balanced_accuracy'])} \\\\")
    return "\n".join(out)


def copy_figs():
    (OUT / "fig").mkdir(parents=True, exist_ok=True)
    got = []
    for f in FIGS:
        src = FIGSRC / f"{f}.pdf"
        if src.exists():
            shutil.copy(src, OUT / "fig" / f"{f}.pdf")
            got.append(f)
    return got


if __name__ == "__main__":
    D = load()
    M = macros(D)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "macros.tex").write_text(emit_macros(M) + "\n")
    # OXIRIDA "%" — \input tabular ichida bo'lganda EOF dagi bo'shliq
    # "Misplaced \noalign" xatosini beradi; izoh uni yutadi.
    for name, body in (("tab_metrics", tab_metrics(D)), ("tab_iou", tab_iou(D)),
                       ("tab_stability", tab_stability(D)),
                       ("tab_external", tab_external(D)), ("tab_crossdb", tab_crossdb(D)),
                       ("tab_harmonise", tab_harmonise(D))):
        (OUT / f"{name}.tex").write_text(body + "%")
    figs = copy_figs()
    print(f"[tex] makros: {len(M)} ta, rasm: {len(figs)} ta, "
          f"tashqi natija: {'bor' if D['ext'] else 'YO`Q'}")
