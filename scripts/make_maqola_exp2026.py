# -*- coding: utf-8 -*-
"""make_maqola_exp2026.py — ilmiy maqola UCH TILDA (o'zbek, rus, ingliz).

Barcha formulalar Word native OMML (MathType-mos) — rasm emas.
Barcha son qiymatlari runs/exp_20260710/metrics/*.json dan O'QILADI (qo'lda kiritilmaydi).

Metodologik protokol (halol):
  • α* ansambl vazni FAQAT train to'plamda tanlanadi; val — yakuniy baholash uchun.
  • Har bir metrika 95% bootstrap ishonch oralig'i bilan; Δ (ansambl − YOLO) juftlashgan
    bootstrap bilan tekshiriladi (p-qiymat).
  • Nomutanosib bazada aniqlik (accuracy) yolg'iz yetarli emas — muvozanatli aniqlik
    (= makro sezgirlik), o'ziga xoslik, F1, AUC, MCC va Cohen κ ham keltiriladi.

Build:
  docker run --rm -v $PWD:/work -w /work -e PYTHONPATH=/work:/work/scripts \
    mamograf-prod-app sh -c "pip install -q python-docx && python scripts/make_maqola_exp2026.py"
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Inches, Pt, RGBColor

import maqola_figures as FG
import maqola_formulalar as F
from omml import add_equation

ROOT = Path(__file__).resolve().parent.parent
MET = ROOT / "runs" / "exp_20260710" / "metrics"
ASSETS = ROOT / "doc_assets_exp2026"
ACCENT = RGBColor(0x14, 0x2C, 0x52)

DET_ORDER = ["yolo11s", "yolo11l", "yolo11l_v2"]
IMG_TR, IMG_VAL = 175, 47


# --------------------------------------------------------------------------- #
# Son formatlash (uz/ru — vergul, en — nuqta)                                 #
# --------------------------------------------------------------------------- #
def N(x, lang, nd=3):
    s = f"{x:.{nd}f}"
    return s if lang == "en" else s.replace(".", ",")


def CI(v, ci, lang, nd=3):
    return f"{N(v, lang, nd)} [{N(ci['lo'], lang, nd)}; {N(ci['hi'], lang, nd)}]"


def PV(p, lang):
    if p < 0.001:
        return "p < 0,001" if lang != "en" else "p < 0.001"
    return f"p = {N(p, lang, 3)}"


def DLT(d, lang, nd=3):
    sgn = "+" if d["delta"] >= 0 else "−"
    return (f"{sgn}{N(abs(d['delta']), lang, nd)} "
            f"[{N(d['lo'], lang, nd)}; {N(d['hi'], lang, nd)}]")


def PP(x, lang):
    """foiz punkt"""
    return N(abs(x) * 100, lang, 1)


CLS = FG.CLS


# --------------------------------------------------------------------------- #
# Ma'lumot                                                                     #
# --------------------------------------------------------------------------- #
def load():
    met = json.loads((MET / "metrics.json").read_text())
    nsw = json.loads((MET / "nsweep_ci.json").read_text())
    art = json.loads((MET.parent / "exp01_fit" / "artifacts.json").read_text())
    return met, nsw, art


def vals_for(lang, met, nsw, art):
    n_star = nsw["n_star_by_cv"]
    row = next(r for r in nsw["rows"] if r["n"] == n_star)
    row38 = next(r for r in nsw["rows"] if r["n"] == 38)
    bg = met["boolfs_gt"]
    s, l, v = (met["detectors"][k] for k in DET_ORDER)
    hi = met["sensitivity"]["yolo11s_conf15"]
    io = met["sensitivity"]["yolo11s_iou05"]

    def det(d, meth, key):
        return d[meth][key]

    v_ = {
        "n_star": n_star,
        "cv_ci": f"{N(row['cv_acc'], lang)} [{N(row['cv_acc_lo'], lang)}; {N(row['cv_acc_hi'], lang)}]",
        "val_ci": CI(row["val_acc"], row["ci"]["accuracy"], lang),
        "val_auc_ci": CI(row["val_auc"], row["ci"]["auc_macro"], lang),
        "val_bacc": N(row["val_bacc"], lang),
        "acc38": N(row38["val_acc"], lang),
        "cv38": N(row38["cv_acc"], lang),
        "n_tr": art["n_roi_train"], "n_val": bg["n"], "img_tr": IMG_TR, "img_val": IMG_VAL,
        "top5": ", ".join(x["feature"] for x in art["selection_table"][:5]),
        # boolfs yolg'iz
        "bf_acc": CI(bg["accuracy"], bg["ci"]["accuracy"], lang),
        "bf_sens": CI(bg["sensitivity_macro"], bg["ci"]["sensitivity_macro"], lang),
        "bf_spec": CI(bg["specificity_macro"], bg["ci"]["specificity_macro"], lang),
        "bf_auc": CI(bg["auc_macro"], bg["ci"]["auc_macro"], lang),
        # detektorlar
        "s_a": N(s["alpha_star"], lang, 2), "l_a": N(l["alpha_star"], lang, 2),
        "v_a": N(v["alpha_star"], lang, 2),
        "s_n": s["n_matched"], "l_n": l["n_matched"], "v_n": v["n_matched"],
    }
    for tag, d in (("s", s), ("l", l), ("v", v)):
        for meth in ("yolo", "ensemble"):
            mm = "y" if meth == "yolo" else "e"
            v_[f"{tag}_{mm}_acc"] = N(det(d, meth, "accuracy"), lang)
            v_[f"{tag}_{mm}_sens"] = N(det(d, meth, "sensitivity_macro"), lang)
            v_[f"{tag}_{mm}_spec"] = N(det(d, meth, "specificity_macro"), lang)
            v_[f"{tag}_{mm}_auc"] = N(det(d, meth, "auc_macro"), lang)
            v_[f"{tag}_{mm}_mcc"] = N(det(d, meth, "mcc"), lang)
            v_[f"{tag}_{mm}_kappa"] = N(det(d, meth, "kappa"), lang)
        for k in ("accuracy", "sensitivity_macro", "auc_macro", "mcc", "kappa"):
            short = {"accuracy": "acc", "sensitivity_macro": "sens", "auc_macro": "auc",
                     "mcc": "mcc", "kappa": "kappa"}[k]
            dd = d["delta"][k]
            v_[f"{tag}_d_{short}"] = DLT(dd, lang)
            v_[f"{tag}_p_{short}"] = PV(dd["p"], lang)
            v_[f"{tag}_pp_{short}"] = PP(dd["delta"], lang)

    v_.update({
        "hi_y_acc": N(hi["yolo"]["accuracy"], lang), "hi_e_acc": N(hi["ensemble"]["accuracy"], lang),
        "hi_y_auc": N(hi["yolo"]["auc_macro"], lang), "hi_e_auc": N(hi["ensemble"]["auc_macro"], lang),
        "hi_p_acc": PV(hi["delta"]["accuracy"]["p"], lang),
        "hi_p_auc": PV(hi["delta"]["auc_macro"]["p"], lang),
        "hi_n": hi["n_matched"],
        "io_y_acc": N(io["yolo"]["accuracy"], lang), "io_e_acc": N(io["ensemble"]["accuracy"], lang),
        "io_pp_acc": PP(io["delta"]["accuracy"]["delta"], lang),
        "io_p_acc": PV(io["delta"]["accuracy"]["p"], lang),
        "io_n": io["n_matched"],
    })

    # sinf kesimi (YOLO11l)
    py = {x["class"]: x for x in l["yolo"]["per_class"]}
    pe = {x["class"]: x for x in l["ensemble"]["per_class"]}
    for cname, tag in (("calcification", "calc"), ("asymmetry", "asym"),
                       ("lymph_node", "lymph"), ("BIRADS12", "b12")):
        v_[f"{tag}_y"] = N(py[cname]["sensitivity"] or 0.0, lang, 2)
        v_[f"{tag}_e"] = N(pe[cname]["sensitivity"] or 0.0, lang, 2)
    return v_


# --------------------------------------------------------------------------- #
# Jadval qatorlari                                                             #
# --------------------------------------------------------------------------- #
def t1_rows(lang, met, art):
    val_sup = {d["class"]: d["support"] for d in met["boolfs_gt"]["per_class"]}
    rows = [[CLS[lang][k], c, val_sup.get(k, 0)] for k, c in art["class_counts"].items()]
    rows.append([{"uz": "Jami", "ru": "Всего", "en": "Total"}[lang],
                 art["n_roi_train"], met["boolfs_gt"]["n"]])
    return rows


def t2_rows(lang, nsw):
    out = []
    for r in nsw["rows"]:
        if r["n"] not in (1, 3, 8, 13, 21, 28, 34, 38):
            continue
        n = f"{r['n']} *" if r["n"] == nsw["n_star_by_cv"] else str(r["n"])
        out.append([n,
                    f"{N(r['cv_acc'], lang)} [{N(r['cv_acc_lo'], lang)}; {N(r['cv_acc_hi'], lang)}]",
                    CI(r["val_acc"], r["ci"]["accuracy"], lang),
                    N(r["val_bacc"], lang),
                    CI(r["val_auc"], r["ci"]["auc_macro"], lang)])
    return out


def t3_rows(lang, met):
    lbl = {"uz": ("YOLO yolg'iz", "boolfs yolg'iz", "Ansambl"),
           "ru": ("YOLO отдельно", "boolfs отдельно", "Ансамбль"),
           "en": ("YOLO alone", "boolfs alone", "Ensemble")}[lang]
    rows = []
    for k in DET_ORDER:
        d = met["detectors"][k]
        for meth, name in (("yolo", lbl[0]), ("boolfs", lbl[1]), ("ensemble", lbl[2])):
            e = d[meth]
            rows.append([d["label"] if meth == "yolo" else "", name,
                         CI(e["accuracy"], e["ci"]["accuracy"], lang),
                         CI(e["balanced_accuracy"], e["ci"]["balanced_accuracy"], lang),
                         N(e["specificity_macro"], lang),
                         N(e["f1_macro"], lang),
                         CI(e["auc_macro"], e["ci"]["auc_macro"], lang),
                         N(e["mcc"], lang), N(e["kappa"], lang)])
    return rows


def t4_rows(lang, met):
    keys = ("accuracy", "sensitivity_macro", "auc_macro", "mcc", "kappa")
    rows = []
    for k in DET_ORDER:
        d = met["detectors"][k]
        for kk in keys:
            dd = d["delta"][kk]
            star = "✓" if dd["p"] < 0.05 else "—"
            rows.append([d["label"] if kk == "accuracy" else "",
                         METRIC_NAMES[lang][kk], DLT(dd, lang), PV(dd["p"], lang), star])
    return rows


def t5_rows(lang, met):
    d = met["detectors"]["yolo11l"]
    py = {x["class"]: x for x in d["yolo"]["per_class"]}
    pe = {x["class"]: x for x in d["ensemble"]["per_class"]}
    rows = []
    for c in met["class_names"]:
        if py[c]["support"] == 0:
            continue
        f = lambda x: "—" if x is None or x != x else N(x, lang, 2)
        rows.append([CLS[lang][c], py[c]["support"],
                     f(py[c]["sensitivity"]), f(pe[c]["sensitivity"]),
                     f(py[c]["specificity"]), f(pe[c]["specificity"]),
                     f(py[c]["precision"]), f(pe[c]["precision"])])
    return rows


def t6_rows(lang, met):
    names = T[lang]["t6_names"]
    s = met["detectors"]["yolo11s"]
    out = [[names[0], f"{s['n_matched']} / {s['n_gt']}",
            N(s["yolo"]["accuracy"], lang), N(s["ensemble"]["accuracy"], lang),
            N(s["yolo"]["sensitivity_macro"], lang), N(s["ensemble"]["sensitivity_macro"], lang),
            N(s["yolo"]["auc_macro"], lang), N(s["ensemble"]["auc_macro"], lang),
            PV(s["delta"]["accuracy"]["p"], lang)]]
    for key, i in (("yolo11s_conf15", 1), ("yolo11s_iou05", 2)):
        e = met["sensitivity"][key]
        out.append([names[i], f"{e['n_matched']} / {e['n_gt']}",
                    N(e["yolo"]["accuracy"], lang), N(e["ensemble"]["accuracy"], lang),
                    N(e["yolo"]["sensitivity_macro"], lang),
                    N(e["ensemble"]["sensitivity_macro"], lang),
                    N(e["yolo"]["auc_macro"], lang), N(e["ensemble"]["auc_macro"], lang),
                    PV(e["delta"]["accuracy"]["p"], lang)])
    return out


METRIC_NAMES = {
    "uz": {"accuracy": "Aniqlik", "sensitivity_macro": "Sezgirlik (makro)",
           "auc_macro": "AUC (makro)", "mcc": "MCC", "kappa": "Cohen κ"},
    "ru": {"accuracy": "Точность", "sensitivity_macro": "Чувствительность (макро)",
           "auc_macro": "AUC (макро)", "mcc": "MCC", "kappa": "Каппа Коэна"},
    "en": {"accuracy": "Accuracy", "sensitivity_macro": "Sensitivity (macro)",
           "auc_macro": "AUC (macro)", "mcc": "MCC", "kappa": "Cohen's κ"},
}

# --------------------------------------------------------------------------- #
# Matn (uch til)                                                              #
# --------------------------------------------------------------------------- #
T = {}

T["uz"] = dict(
    title="Mammografik ROI'larni tasniflashda bulcha belgi tanlash va gibrid ansambl: "
          "aniqlik emas, sezgirlik va ajratuvchanlik o'sadi",
    authors="Turaqulov H.  ·  ilmiy rahbar: professor Xamdamov R.X.",
    affil="Muhammad al-Xorazmiy nomidagi Toshkent axborot texnologiyalari universiteti",
    udk="UDK 004.93:519.86:618.19",
    abs_h="Annotatsiya", kw_h="Kalit so'zlar",
    kw="bulcha dasturlash, informativ belgilar tanlash, minimal masofa klassifikatori, "
       "radiomika, mammografiya, YOLO, gibrid ansambl, sezgirlik, ROC-AUC, "
       "nomutanosib sinflar, interpretatsiyalanadigan sun'iy intellekt.",
    abstract=(
        "Maqolada R.X. Xamdamovning bulcha dasturlash nazariyasiga asoslangan informativ "
        "belgilar tanlash usuli va minimal masofa qoidasi bo'yicha tasniflagich mammografik "
        "qiziqish sohalarini (ROI) sinflarga ajratishda qo'llanildi hamda YOLO detektori bilan "
        "gibrid ansamblga birlashtirildi. Sakkiz sinfli, kuchli nomutanosib mammografiya "
        "bazasida ({n_tr} ta o'qitish, {n_val} ta tekshirish ROI'si) tajribalar o'tkazildi. "
        "Ansambl vazni α* faqat o'qitish to'plamida tanlandi, tekshirish to'plami esa yakuniy "
        "baholash uchun ajratildi; har bir metrika 95% bootstrap ishonch oralig'i bilan, "
        "ansambl va detektor farqi juftlashgan bootstrap bilan tekshirildi. 38 ta belgidan "
        "n′* = {n_star} tasi optimal bo'ldi (kross-validatsiya P = {cv_ci}). "
        "Asosiy natija: nomutanosib bazada umumiy aniqlik yolg'iz yo'l qo'ymaydigan mezon "
        "ekani ko'rsatildi — kuchli detektor (YOLO11l) uchun ansambl aniqlikni sezilarli "
        "o'zgartirmaydi ({l_y_acc} → {l_e_acc}, {l_p_acc}), biroq makro sezgirlikni "
        "{l_y_sens} dan {l_e_sens} gacha ({l_p_sens}) va makro ROC-AUC ni {l_y_auc} dan "
        "{l_e_auc} gacha oshiradi. Kuchsizroq detektor (YOLO11s) uchun barcha mezonlar "
        "sezilarli yaxshilanadi: aniqlik {s_y_acc} → {s_e_acc} ({s_p_acc}), AUC "
        "{s_y_auc} → {s_e_auc}, Cohen κ {s_y_kappa} → {s_e_kappa}. Bulcha tasniflagichning "
        "yolg'iz o'zi past aniqlik ({bf_acc}) bilan yuqori ajratuvchanlikni ({bf_auc}) "
        "birlashtiradi — bu uning detektorni to'ldiruvchi, o'rin bosmaydigan roli haqida "
        "guvohlik beradi. Yutuq kam uchraydigan, klinik jihatdan muhim sinflarda jamlangan: "
        "kalsifikatsiya sezgirligi {calc_y} → {calc_e}, assimetriya {asym_y} → {asym_e}."),
    s1="1. Kirish",
    p1a=("Mammografik tasvirlarni avtomatik tahlil qilishda zamonaviy bir bosqichli "
         "detektorlar (YOLO oilasi) yuqori tezlik va qoniqarli aniqlik ko'rsatadi. Biroq ular "
         "chuqur neyron tarmoq sifatida qora quti bo'lib qoladi va klinik qarorni asoslash "
         "uchun zarur \"qaysi belgi shu qarorga olib keldi?\" degan savolga javob bermaydi."),
    p1b=("Bundan tashqari, mammografiya bazalari tabiatan kuchli nomutanosib: bizning "
         "to'plamimizda limfa tugunlari {n_tr} ta ROI'ning katta qismini egallaydi, "
         "arxitektura buzilishi esa atigi ikki misolda uchraydi. Bunday sharoitda umumiy "
         "aniqlik (accuracy) ko'p sonli sinf tomonidan boshqariladi va model sifatini "
         "yashirishi mumkin. Shuning uchun ushbu ishda muvozanatli aniqlik (makro sezgirlik), "
         "o'ziga xoslik, F1, ROC-AUC, Metyus korrelyatsiya koeffitsienti (MCC) va Cohen κ "
         "birgalikda keltiriladi."),
    p1c=("Ishda ikki bosqichli arxitektura taklif etiladi. Birinchi bosqichda YOLO detektori "
         "qiziqish sohalarini (ROI) topadi. Ikkinchi bosqichda R.X. Xamdamovning bulcha "
         "dasturlash masalalari nazariyasiga [1] asoslangan, to'liq interpretatsiyalanadigan "
         "tasniflagich har bir ROI'ni 38 o'lchovli radiomika belgilar fazosida qayta baholaydi. "
         "Ikkala bosqich chiqishi vaznli ansambl orqali birlashtiriladi."),
    p1d=("Ishning ilmiy yangiligi: (i) bulcha belgi tanlash mezoni mammografik ko'p sinfli "
         "masalaga umumlashtirildi; (ii) gibrid ansamblning foydasi qaysi mezonda va qaysi "
         "sinflarda paydo bo'lishi statistik jihatdan (ishonch oraliqlari va juftlashgan "
         "bootstrap bilan) aniqlandi; (iii) foydaning detektor kuchi va ishonch chegarasiga "
         "bog'liqligi miqdoriy ko'rsatildi."),
    s2="2. Materiallar va usul",
    s21="2.1. Ma'lumotlar bazasi va eksperiment protokoli",
    p21=("Sakkiz sinfli mammografiya bazasi: {n_tr} ta o'qitish va {n_val} ta tekshirish ROI'si "
         "(mos ravishda {img_tr} va {img_val} tasvirdan). Baza kuchli nomutanosib — 1-jadval."),
    p21b=("**Protokol.** Ansambl vazni α* faqat o'qitish to'plamidagi moslashgan detektsiyalarda, "
          "muvozanatli aniqlik bo'yicha tanlandi; tekshirish to'plami hech qanday tanlovda "
          "ishlatilmadi va faqat yakuniy baholashga xizmat qildi. Har bir metrika uchun 95% "
          "ishonch oralig'i 1000 marta bootstrap qayta tanlash bilan hisoblandi. Ansambl va "
          "yakka detektor farqi (Δ) juftlashgan bootstrap orqali baholanib, ikki tomonlama "
          "p-qiymat keltiriladi. YOLO chiqishlari etalon ROI'lar bilan ochko'z usulda, "
          "IoU ≥ 0,3 sharti asosida moslashtiriladi."),
    s22="2.2. Belgilar fazosi",
    p22=("Har bir ROI kesmasidan 38 ta radiomika belgisi ajratiladi: birinchi tartib "
         "statistikalari (o'rtacha, dispersiya, assimetriya, ekstsess), gradient "
         "xarakteristikalari (Sobel operatorining o'rtachasi va standart chetlanishi) hamda "
         "ikki masofa (d = 1 va d = 3) uchun GLCM belgilari: kontrast, dissimilyarlik, bir "
         "jinslilik, energiya, korrelyatsiya, entropiya. Belgilar o'qitish to'plami "
         "statistikasi bo'yicha z-normallashtiriladi."),
    s23="2.3. Bulcha belgi tanlash mezoni",
    p23a=("Xamdamov [1, (3.2.2)] bo'yicha, (p, q) sinflar juftligi va j-belgi uchun sinflararo "
          "tarqoqlik a_j hamda sinf ichidagi tarqoqliklar b_j va c_j kiritiladi:"),
    p23b=("bu yerda x_plj — p-sinfning l-obyekti uchun j-belgi qiymati, k_p — p-sinfdagi "
          "obyektlar soni. Ko'p sinfli (m = 8) holatga o'tish uchun global rejim qo'llanadi: "
          "a_j barcha (p, q) juftliklar bo'yicha, w_j = b_j + c_j esa barcha sinf ichidagi "
          "tarqoqliklar bo'yicha yig'iladi."),
    p23c=("Informativ belgilar to'plamini izlash bulcha dasturlash masalasiga keltiriladi: "
          "λ_j ∈ {{0, 1}} — j-belgining tanlanganligini bildiruvchi bulcha o'zgaruvchi. "
          "Maqsad funksionali tanlangan belgilar bo'yicha sinflararo va sinf ichidagi "
          "tarqoqliklar nisbatini maksimallashtiradi:"),
    s24="2.4. Ranjirlash va prefiks bo'yicha tanlash",
    p24a=("Umumlashgan tengsizliklar usuli [1, 3.4-bo'lim] (3.4.5) ga ko'ra belgilarni r_j "
          "nisbat bo'yicha kamayish tartibida joylashtirishga imkon beradi:"),
    p24b=("Ranjirlangan qatorning prefikslari Φ(λ) ning monoton kamayish zanjirini hosil qiladi. "
          "Shuni ta'kidlash lozimki, qat'iy |S| = n′ cheklovida prefiks umumiy holda mutlaq "
          "optimal to'plam bo'lishi shart emas; kitobning (3.4.4) natijasi aynan prefikslar "
          "zanjiri xossasini beradi. Shu sababli n′ ning yakuniy qiymati Φ bo'yicha emas, balki "
          "kross-validatsiyadagi tasniflash sifati P bo'yicha tanlanadi:"),
    s25="2.5. Minimal masofa tasniflagichi",
    p25a=("Har bir p sinf uchun etalon vektor (markaz) va sinf ichki tarqoqligi hisoblanadi "
          "[1, (3.6.2)–(3.6.3)]:"),
    p25b=("Yangi obyekt x uchun normallashgan masofa va qaror qoidasi:"),
    p25c=("Ansambl uchun masofalar softmax orqali ehtimollikka o'xshash bahoga aylantiriladi:"),
    p25d=("k_p < 5 bo'lgan kichik sinflar uchun kross-validatsiyada leave-one-out sxemasi, "
          "qolganlari uchun stratifikatsiyalangan 5-fold sxemasi qo'llanadi. Fold'lar bo'yicha "
          "o'rtacha emas, balki to'plangan (pooled) bashoratlar bo'yicha baho olinadi: kichik "
          "sinflar uchun LOO fold'i bitta namunadan iborat bo'lgani sababli fold aniqligi faqat "
          "0 yoki 1 qiymat oladi va o'rtacha ± standart chetlanish sun'iy ravishda katta chiqadi."),
    s26="2.6. Gibrid ansambl va sifat mezonlari",
    p26=("YOLO detektorining p sinf uchun chiqishi (ishonch qiymati asosida taqsimlangan) va "
         "bulcha tasniflagich bahosi vaznli yig'indi orqali birlashtiriladi:"),
    p26b=("Tasniflash ishonchliligi [1, (3.6.4)] to'g'ri tanilgan obyektlar ulushi sifatida "
          "o'lchanadi (I[·] — indikator funksiya):"),
    p26c=("Nomutanosib baza uchun bu mezon yolg'iz yetarli emas. Shuning uchun har bir c sinf "
          "\"bir-hammaga qarshi\" ko'rinishida qaralib, sezgirlik TP/(TP+FN), o'ziga xoslik "
          "TN/(TN+FP), aniqlik TP/(TP+FP) va F1 hisoblanadi; ularning makro o'rtachasi, "
          "shuningdek makro ROC-AUC, MCC va Cohen κ keltiriladi. Muvozanatli aniqlik makro "
          "sezgirlikka tengdir."),
    s3="3. Natijalar",
    s31="3.1. Tanlangan belgilar va n′* qiymati",
    p31a=("Ranjirlangan qatorning birinchi o'rinlarini GLCM korrelyatsiya belgilari egalladi: "
          "{top5}. Bu patologik sohalarning tekstura yo'nalganligi va gradient tarqoqligi eng "
          "informativ ekanini ko'rsatadi."),
    p31b=("Prefiks uzunligi bo'yicha qidiruv (2-jadval, 1-rasm) kross-validatsiyada n′* = "
          "{n_star} qiymatida maksimum berdi (P = {cv_ci}); mustaqil tekshirish to'plamida shu "
          "n′ uchun aniqlik {val_ci}, makro AUC {val_auc_ci}. To'liq 38 ta belgidan foydalanish "
          "natijani biroz pasaytiradi (CV {cv38}, val {acc38})."),
    p31c=("**Halol talqin.** 1-rasmdagi ishonch oraliqlari qo'shni n′ qiymatlari uchun kuchli "
          "kesishadi: masalan n′ = 13 va n′ = {n_star} uchun val ishonch oraliqlari qoplanadi. "
          "Demak ma'lumotlar hajmi n′ ni bir birlik aniqlikda ajratishga yetarli emas; "
          "n′* = {n_star} — kross-validatsiya bo'yicha eng yaxshi tanlov, lekin qo'shni "
          "qiymatlardan statistik jihatdan ustunligi isbotlanmagan. Buni yashirish o'rniga "
          "ochiq qayd etamiz."),
    s32="3.2. Bulcha tasniflagichning yolg'iz ishlashi",
    p32=("Etalon ROI'lar ustida (detektorsiz, {n_val} ta ROI) bulcha tasniflagich aniqlik "
         "{bf_acc}, makro sezgirlik {bf_sens}, makro o'ziga xoslik {bf_spec} va makro ROC-AUC "
         "{bf_auc} ko'rsatdi. Past aniqlik va yuqori AUC birikmasi muhim: model sinflarni "
         "**tartiblash** (ranking) bo'yicha kuchli, biroq argmin qoidasi bilan qaror qabul "
         "qilishda nomutanosiblikdan zarar ko'radi. Aynan shuning uchun u detektorni "
         "almashtira olmaydi, lekin uni to'ldiradi."),
    s33="3.3. Gibrid ansambl: qaysi mezon o'sadi?",
    p33a=("Uch detektor uchun to'liq metrika to'plami 3-jadvalda, farqlarning statistik "
          "ahamiyati 4-jadvalda keltirilgan. Natija bir xil emas va aynan shu qiziq:"),
    p33_b1=("**YOLO11s** (kuchsizroq detektor, α* = {s_a}, {s_n} mos ROI): barcha asosiy "
            "mezonlar sezilarli o'sdi — aniqlik {s_y_acc} → {s_e_acc} (Δ = {s_d_acc}, "
            "{s_p_acc}), makro sezgirlik {s_y_sens} → {s_e_sens} ({s_p_sens}), makro AUC "
            "{s_y_auc} → {s_e_auc} ({s_p_auc}), Cohen κ {s_y_kappa} → {s_e_kappa} ({s_p_kappa})."),
    p33_b2=("**YOLO11l** (kuchli detektor, α* = {l_a}, {l_n} mos ROI): umumiy aniqlik deyarli "
            "o'zgarmadi — {l_y_acc} → {l_e_acc} (Δ = {l_d_acc}, {l_p_acc}, ya'ni statistik "
            "jihatdan ahamiyatsiz). Ammo makro sezgirlik {l_y_sens} → {l_e_sens} "
            "(Δ = {l_d_sens}, {l_p_sens}) va makro AUC {l_y_auc} → {l_e_auc} ({l_p_auc}) "
            "sezilarli yaxshilandi."),
    p33_b3=("**YOLO11l-v2** (eng kuchli detektor, α* = {v_a}, {v_n} mos ROI): aniqlik "
            "{v_y_acc} → {v_e_acc} ({v_p_acc}) — ahamiyatsiz; faqat makro AUC {v_y_auc} → "
            "{v_e_auc} ({v_p_auc}) sezilarli o'sdi."),
    p33c=("Bu manzara aniq qonuniyatni ochadi: **detektor qanchalik kuchli bo'lsa, ansamblning "
          "foydasi shunchalik toraydi va aniqlikdan sezgirlik hamda ajratuvchanlik (AUC) "
          "tomon siljiydi.** Umumiy aniqlikning o'zgarmasligi ansambl foydasiz degani emas — "
          "u shunchaki ko'p sonli sinf (limfa tuguni) tomonidan boshqariladi."),
    s34="3.4. Yutuq qayerdan keladi: sinflar kesimi",
    p34a=("5-jadval va 4-rasm buni yaqqol ko'rsatadi (YOLO11l). Ansambl kam uchraydigan, "
          "klinik jihatdan muhim sinflarda sezgirlikni keskin oshiradi: kalsifikatsiya "
          "{calc_y} → {calc_e}, assimetriya {asym_y} → {asym_e}, BIRADS 1-2 {b12_y} → {b12_e}. "
          "Buning evaziga ko'p sonli limfa tuguni sinfida sezgirlik {lymph_y} dan {lymph_e} "
          "gacha tushadi."),
    p34b=("Aynan shu almashuv umumiy aniqlikni deyarli o'zgarishsiz qoldiradi, lekin makro "
          "sezgirlikni va AUC ni oshiradi. Skrining kontekstida bu maqbul kelishuv: "
          "kalsifikatsiya va assimetriya o'tkazib yuborilishi limfa tugunini noto'g'ri "
          "belgilashdan ancha qimmatga tushadi. 3-rasmdagi ROC egri chiziqlari ansamblning "
          "butun ishlash nuqtalari bo'ylab ustunligini tasdiqlaydi."),
    s35="3.5. Ishonch va IoU chegaralariga sezgirlik",
    p35a=("6-jadvalda ishonch chegarasi va mos kelish chegarasi o'zgartirilgan holatlar "
          "keltirilgan (YOLO11s asosida). Chegara conf = 0,15 ga ko'tarilganda ({hi_n} mos ROI) "
          "detektorning o'zi {hi_y_acc} aniqlikka chiqadi, chunki past ishonchli chiqishlar "
          "filtrlanadi; ansambl bu holda qarorlarni umuman o'zgartirmaydi ({hi_e_acc}, "
          "{hi_p_acc}). Shu bilan birga makro AUC {hi_y_auc} dan {hi_e_auc} gacha o'sadi — "
          "ya'ni tartiblash sifati baribir yaxshilanadi, garchi argmax qarori o'zgarmasa ham."),
    p35b=("Mos kelish chegarasi IoU ≥ 0,5 gacha qattiqlashtirilganda ({io_n} mos ROI) ansambl "
          "aniqlikni {io_y_acc} dan {io_e_acc} gacha ({io_pp_acc} foiz punkt, {io_p_acc}) "
          "ko'taradi. Demak, geometrik jihatdan aniqroq, lekin tasniflashda qiyinroq "
          "detektsiyalarda bulcha tasniflagichning hissasi saqlanadi."),
    s4="4. Muhokama",
    p4a=("Adabiyotda gibrid usullar odatda o'rtacha aniqlik o'sishi bilan asoslanadi. Bizning "
         "tahlilimiz shuni ko'rsatadiki, kuchli detektor va nomutanosib baza sharoitida bu "
         "asoslash yetarli emas va hatto chalg'ituvchi bo'lishi mumkin: YOLO11l uchun aniqlik "
         "amalda o'zgarmadi ({l_p_acc}), holbuki makro sezgirlik {l_d_sens} ga o'sdi. Agar "
         "faqat aniqlik keltirilganda edi, usul \"foydasiz\" deb baholanardi; agar faqat "
         "sezgirlik keltirilganda edi, o'sish bo'rttirilardi. To'g'ri xulosa — ikkalasini "
         "birga keltirish."),
    p4b=("Ikkinchi muhim kuzatuv — bulcha tasniflagichning yolg'iz o'zi yuqori AUC ({bf_auc}) "
         "va past aniqlik ({bf_acc}) ko'rsatishi. Bu uning axborot hissasi qaror qabul qilish "
         "qoidasida emas, balki sinflarni tartiblashda ekanini bildiradi. Ansambl aynan shu "
         "tartiblash axborotini detektorning ishonch bahosiga qo'shadi."),
    p4c=("Klinik ish oqimi uchun tavsiya: bulcha tasniflagichni kuchli detektorning yuqori "
         "ishonchli qarorlariga aralashtirmaslik, uni kam uchraydigan sinflar shubhasi bor "
         "va past ishonchli sohalarda \"ikkinchi fikr\" sifatida ishlatish maqsadga muvofiq. "
         "Tasniflagich to'liq interpretatsiyalanadigan bo'lgani uchun (tanlangan {n_star} ta "
         "belgi va etalonlargacha bo'lgan masofalar oshkora) uning bahosi radiolog tomonidan "
         "tekshirilishi mumkin."),
    p4d=("**Cheklovlar.** Baza hajmi kichik: tekshirish to'plamida moslashgan detektsiyalar "
         "soni 75–105 oralig'ida, ba'zi sinflarda 3–6 ta misol. Shu sababli ishonch oraliqlari "
         "keng va bir qator farqlar statistik ahamiyatga ega emas (4-jadval). α* o'qitish "
         "to'plamida tanlangan bo'lsa-da, u ham cheklangan hajmga ega. Arxitektura buzilishi "
         "sinfida atigi ikkita o'qitish misoli bor va u tekshirish to'plamida mos kelmagan. "
         "Xulosalar ko'p markazli, kattaroq bazada takrorlanishi lozim."),
    s5="5. Xulosa",
    concl=[
        "Bulcha dasturlash mezoni asosidagi belgi tanlash mammografik ko'p sinfli masalaga "
        "umumlashtirildi; kross-validatsiya bo'yicha 38 ta belgidan n′* = {n_star} tasi eng "
        "yaxshi natija berdi (P = {cv_ci}), biroq qo'shni n′ qiymatlaridan statistik ustunligi "
        "isbotlanmadi.",
        "Nomutanosib bazada umumiy aniqlik yolg'iz mezon sifatida yetarli emasligi "
        "ko'rsatildi: YOLO11l uchun ansambl aniqlikni o'zgartirmadi ({l_p_acc}), lekin makro "
        "sezgirlikni {l_y_sens} dan {l_e_sens} gacha ({l_p_sens}) va makro AUC ni {l_y_auc} dan "
        "{l_e_auc} gacha oshirdi.",
        "Kuchsizroq detektor (YOLO11s) uchun ansambl barcha mezonlarni sezilarli yaxshiladi: "
        "aniqlik {s_y_acc} → {s_e_acc} ({s_p_acc}), AUC {s_y_auc} → {s_e_auc}, "
        "Cohen κ {s_y_kappa} → {s_e_kappa}.",
        "Yutuq kam uchraydigan, klinik jihatdan muhim sinflarda jamlangan (kalsifikatsiya "
        "{calc_y} → {calc_e}, assimetriya {asym_y} → {asym_e}) va ko'p sonli sinf hisobiga "
        "erishiladi — skrining uchun maqbul almashuv.",
        "Bulcha tasniflagich yolg'iz yuqori ajratuvchanlik ({bf_auc}) va past aniqlik "
        "({bf_acc}) ko'rsatadi, ya'ni uning roli detektorni to'ldirish — o'rin bosish emas.",
    ],
    refs_h="Adabiyotlar",
    t1_cap="1-jadval. Ma'lumotlar bazasidagi ROI'lar taqsimoti",
    t2_cap="2-jadval. Tanlangan belgilar soni n′ ning tasniflash sifatiga ta'siri "
           "(qavsda 95% bootstrap ishonch oralig'i)",
    t3_cap="3-jadval. Tekshirish to'plamidagi to'liq metrika to'plami (95% ishonch oralig'i bilan)",
    t4_cap="4-jadval. Ansambl va yakka detektor farqi Δ: juftlashgan bootstrap, 95% CI va p-qiymat",
    t5_cap="5-jadval. Sinflar kesimida sezgirlik, o'ziga xoslik va aniqlik (YOLO11l)",
    t6_cap="6-jadval. Ishonch (conf) va mos kelish (IoU) chegaralariga sezgirlik (YOLO11s)",
    f1_cap="1-rasm. Tasniflash sifatining tanlangan belgilar soni n′ ga bog'liqligi; "
           "soya — 95% bootstrap ishonch oralig'i",
    f2_cap="2-rasm. Ansambl vazni α ning muvozanatli aniqlikka ta'siri (YOLO11l). "
           "α* o'qitish to'plamida tanlanadi, val egri chizig'i faqat baholash uchun",
    f3_cap="3-rasm. Makro ROC egri chiziqlari (YOLO11l): ansambl butun ishlash nuqtalari "
           "bo'ylab yakka detektordan ustun",
    f4_cap="4-rasm. Sinflar kesimida sezgirlik: yakka YOLO11l va gibrid ansambl "
           "(qavsda tekshirish to'plamidagi misollar soni)",
    f5_cap="5-rasm. Ansambl chalkashlik matritsasi (YOLO11l); ranglar qator bo'yicha "
           "normallashtirilgan, raqamlar — ROI soni",
    t1_h=["Sinf", "O'qitish ROI", "Tekshirish ROI"],
    t2_h=["n′", "CV aniqlik (train)", "Aniqlik (val)", "Muvoz. aniqlik", "AUC (makro)"],
    t3_h=["Detektor", "Usul", "Aniqlik", "Muvoz. aniqlik", "O'ziga xoslik", "F1 (makro)",
          "AUC (makro)", "MCC", "κ"],
    t4_h=["Detektor", "Mezon", "Δ (ansambl − YOLO)", "p-qiymat", "Ahamiyatli"],
    t5_h=["Sinf", "n", "Sezg. YOLO", "Sezg. ansambl", "O'z.xos. YOLO", "O'z.xos. ansambl",
          "Aniq. YOLO", "Aniq. ansambl"],
    t6_h=["Sozlama", "Mos ROI", "Aniq. YOLO", "Aniq. ans.", "Sezg. YOLO", "Sezg. ans.",
          "AUC YOLO", "AUC ans.", "Δaniqlik p"],
    t6_names=["conf = 0,05; IoU = 0,3 (bazaviy)", "conf = 0,15; IoU = 0,3", "conf = 0,05; IoU = 0,5"],
)

T["ru"] = dict(
    title="Булев отбор признаков и гибридный ансамбль в классификации маммографических "
          "областей интереса: растёт не точность, а чувствительность и разделяющая способность",
    authors="Туракулов Х.  ·  научный руководитель: профессор Хамдамов Р.Х.",
    affil="Ташкентский университет информационных технологий имени Мухаммада аль-Хорезми",
    udk="УДК 004.93:519.86:618.19",
    abs_h="Аннотация", kw_h="Ключевые слова",
    kw="булево программирование, отбор информативных признаков, классификатор минимального "
       "расстояния, радиомика, маммография, YOLO, гибридный ансамбль, чувствительность, "
       "ROC-AUC, несбалансированные классы, интерпретируемый искусственный интеллект.",
    abstract=(
        "В статье метод отбора информативных признаков, основанный на теории булева "
        "программирования Р.Х. Хамдамова, и классификатор минимального расстояния применены к "
        "классификации маммографических областей интереса (ROI) и объединены с детектором YOLO "
        "в гибридный ансамбль. Эксперименты проведены на восьмиклассовой, сильно "
        "несбалансированной маммографической базе ({n_tr} обучающих, {n_val} проверочных ROI). "
        "Вес ансамбля α* выбирался исключительно на обучающей выборке, проверочная выборка "
        "использовалась только для итоговой оценки; для каждой метрики построен 95% "
        "бутстреп-доверительный интервал, а разность между ансамблем и детектором проверена "
        "парным бутстрепом. Из 38 признаков оптимальными оказались n′* = {n_star} "
        "(кросс-валидация P = {cv_ci}). Основной результат: показано, что на несбалансированной "
        "базе общая точность непригодна как единственный критерий — для сильного детектора "
        "(YOLO11l) ансамбль практически не меняет точность ({l_y_acc} → {l_e_acc}, {l_p_acc}), "
        "однако повышает макро-чувствительность с {l_y_sens} до {l_e_sens} ({l_p_sens}) и "
        "макро-ROC-AUC с {l_y_auc} до {l_e_auc}. Для более слабого детектора (YOLO11s) значимо "
        "улучшаются все критерии: точность {s_y_acc} → {s_e_acc} ({s_p_acc}), AUC "
        "{s_y_auc} → {s_e_auc}, каппа Коэна {s_y_kappa} → {s_e_kappa}. Булев классификатор сам "
        "по себе сочетает низкую точность ({bf_acc}) с высокой разделяющей способностью "
        "({bf_auc}), что свидетельствует о его дополняющей, а не замещающей роли. Выигрыш "
        "сосредоточен в редких, клинически значимых классах: чувствительность к кальцинатам "
        "{calc_y} → {calc_e}, к асимметрии {asym_y} → {asym_e}."),
    s1="1. Введение",
    p1a=("Современные одностадийные детекторы (семейство YOLO) обеспечивают высокую скорость и "
         "приемлемую точность анализа маммограмм. Однако как глубокие нейронные сети они "
         "остаются «чёрным ящиком» и не отвечают на вопрос «какой признак привёл к данному "
         "решению?», необходимый для обоснования клинического заключения."),
    p1b=("Кроме того, маммографические базы по своей природе сильно несбалансированы: в нашей "
         "выборке лимфатические узлы составляют значительную долю из {n_tr} ROI, тогда как "
         "архитектурная перестройка встречается лишь в двух примерах. В таких условиях общая "
         "точность (accuracy) определяется преобладающим классом и способна маскировать "
         "качество модели. Поэтому в настоящей работе совместно приводятся сбалансированная "
         "точность (макро-чувствительность), специфичность, F1, ROC-AUC, коэффициент "
         "корреляции Мэтьюса (MCC) и каппа Коэна."),
    p1c=("Предложена двухстадийная архитектура. На первой стадии детектор YOLO находит области "
         "интереса (ROI). На второй стадии полностью интерпретируемый классификатор, основанный "
         "на теории задач булева программирования Р.Х. Хамдамова [1], переоценивает каждую ROI "
         "в 38-мерном пространстве радиомических признаков. Выходы обеих стадий объединяются "
         "взвешенным ансамблем."),
    p1d=("Научная новизна: (i) критерий булева отбора признаков обобщён на многоклассовую "
         "маммографическую задачу; (ii) статистически (доверительные интервалы и парный "
         "бутстреп) установлено, в каком критерии и в каких классах проявляется выигрыш "
         "гибридного ансамбля; (iii) количественно показана зависимость выигрыша от силы "
         "детектора и порога уверенности."),
    s2="2. Материалы и метод",
    s21="2.1. База данных и протокол эксперимента",
    p21=("Восьмиклассовая маммографическая база: {n_tr} обучающих и {n_val} проверочных ROI "
         "(из {img_tr} и {img_val} изображений соответственно). База существенно "
         "несбалансирована — таблица 1."),
    p21b=("**Протокол.** Вес ансамбля α* выбирался только на сопоставленных детекциях обучающей "
          "выборки по сбалансированной точности; проверочная выборка не участвовала ни в каком "
          "выборе и служила исключительно для итоговой оценки. Для каждой метрики 95% "
          "доверительный интервал получен бутстрепом (1000 пересэмплирований). Разность между "
          "ансамблем и одиночным детектором (Δ) оценена парным бутстрепом с двусторонним "
          "p-значением. Выходы YOLO сопоставляются с эталонными ROI жадным алгоритмом при "
          "условии IoU ≥ 0,3."),
    s22="2.2. Пространство признаков",
    p22=("Из каждого фрагмента ROI извлекаются 38 радиомических признаков: статистики первого "
         "порядка (среднее, дисперсия, асимметрия, эксцесс), градиентные характеристики "
         "(среднее и стандартное отклонение оператора Собеля), а также признаки GLCM для двух "
         "расстояний (d = 1 и d = 3): контраст, несходство, однородность, энергия, корреляция, "
         "энтропия. Признаки стандартизуются по статистикам обучающей выборки."),
    s23="2.3. Критерий булева отбора признаков",
    p23a=("По Хамдамову [1, (3.2.2)], для пары классов (p, q) и j-го признака вводятся "
          "межклассовый разброс a_j и внутриклассовые разбросы b_j и c_j:"),
    p23b=("Здесь x_plj — значение j-го признака для l-го объекта класса p, k_p — число объектов "
          "в классе p. Для многоклассового случая (m = 8) применяется глобальный режим: a_j "
          "суммируется по всем парам (p, q), а w_j = b_j + c_j — по всем внутриклассовым "
          "разбросам."),
    p23c=("Поиск множества информативных признаков сводится к задаче булева программирования: "
          "λ_j ∈ {{0, 1}} — булева переменная отбора j-го признака. Целевой функционал "
          "максимизирует отношение межклассового и внутриклассового разбросов:"),
    s24="2.4. Ранжирование и отбор по префиксу",
    p24a=("Метод обобщённых неравенств [1, раздел 3.4] согласно (3.4.5) позволяет упорядочить "
          "признаки по убыванию отношения r_j:"),
    p24b=("Префиксы ранжированного ряда образуют цепочку монотонного убывания Φ(λ). При жёстком "
          "ограничении |S| = n′ префикс в общем случае не обязан быть абсолютно оптимальным "
          "множеством; результат (3.4.4) книги даёт именно свойство цепочки префиксов. Поэтому "
          "итоговое n′ выбирается не по Φ, а по качеству классификации P при кросс-валидации:"),
    s25="2.5. Классификатор минимального расстояния",
    p25a=("Для каждого класса p вычисляются эталонный вектор (центр) и внутриклассовый разброс "
          "[1, (3.6.2)–(3.6.3)]:"),
    p25b=("Для нового объекта x нормированное расстояние и решающее правило:"),
    p25c=("Для ансамбля расстояния преобразуются в вероятностноподобные оценки через softmax:"),
    p25d=("Для малых классов с k_p < 5 при кросс-валидации применяется схема leave-one-out, для "
          "остальных — стратифицированная 5-кратная. Оценка вычисляется не как среднее по "
          "фолдам, а по объединённым (pooled) предсказаниям: для малых классов LOO-фолд состоит "
          "из одного объекта, поэтому точность фолда принимает лишь значения 0 или 1, а среднее "
          "± стандартное отклонение оказывается искусственно завышенным."),
    s26="2.6. Гибридный ансамбль и критерии качества",
    p26=("Выход детектора YOLO для класса p (распределённый на основе уверенности) и оценка "
         "булева классификатора объединяются взвешенной суммой:"),
    p26b=("Достоверность классификации [1, (3.6.4)] измеряется как доля правильно распознанных "
          "объектов (I[·] — индикаторная функция):"),
    p26c=("Для несбалансированной базы этого критерия недостаточно. Поэтому каждый класс c "
          "рассматривается в схеме «один против всех» и вычисляются чувствительность "
          "TP/(TP+FN), специфичность TN/(TN+FP), точность TP/(TP+FP) и F1; приводятся их "
          "макро-средние, а также макро-ROC-AUC, MCC и каппа Коэна. Сбалансированная точность "
          "равна макро-чувствительности."),
    s3="3. Результаты",
    s31="3.1. Отобранные признаки и значение n′*",
    p31a=("Первые позиции ранжированного ряда заняли корреляционные признаки GLCM: {top5}. Это "
          "указывает на наибольшую информативность текстурной направленности и градиентного "
          "разброса патологических областей."),
    p31b=("Поиск по длине префикса (таблица 2, рисунок 1) дал максимум кросс-валидации при "
          "n′* = {n_star} (P = {cv_ci}); на независимой проверочной выборке для этого n′ "
          "точность составила {val_ci}, макро-AUC — {val_auc_ci}. Использование всех 38 "
          "признаков несколько ухудшает результат (CV {cv38}, val {acc38})."),
    p31c=("**Честная интерпретация.** Доверительные интервалы на рисунке 1 для соседних "
          "значений n′ существенно перекрываются: например, для n′ = 13 и n′ = {n_star} "
          "интервалы на проверочной выборке накладываются. Следовательно, объём данных "
          "недостаточен, чтобы различать n′ с точностью до единицы; n′* = {n_star} — наилучший "
          "выбор по кросс-валидации, но его статистическое превосходство над соседними "
          "значениями не доказано. Мы фиксируем это открыто, а не умалчиваем."),
    s32="3.2. Работа булева классификатора отдельно",
    p32=("На эталонных ROI (без детектора, {n_val} ROI) булев классификатор показал точность "
         "{bf_acc}, макро-чувствительность {bf_sens}, макро-специфичность {bf_spec} и "
         "макро-ROC-AUC {bf_auc}. Сочетание низкой точности с высоким AUC существенно: модель "
         "сильна в **ранжировании** классов, но страдает от несбалансированности при принятии "
         "решения по правилу argmin. Именно поэтому она не может заменить детектор, но "
         "дополняет его."),
    s33="3.3. Гибридный ансамбль: какой критерий растёт?",
    p33a=("Полный набор метрик для трёх детекторов приведён в таблице 3, статистическая "
          "значимость разностей — в таблице 4. Результат неоднороден, и это самое интересное:"),
    p33_b1=("**YOLO11s** (более слабый детектор, α* = {s_a}, {s_n} сопоставленных ROI): значимо "
            "выросли все основные критерии — точность {s_y_acc} → {s_e_acc} (Δ = {s_d_acc}, "
            "{s_p_acc}), макро-чувствительность {s_y_sens} → {s_e_sens} ({s_p_sens}), макро-AUC "
            "{s_y_auc} → {s_e_auc} ({s_p_auc}), каппа Коэна {s_y_kappa} → {s_e_kappa} "
            "({s_p_kappa})."),
    p33_b2=("**YOLO11l** (сильный детектор, α* = {l_a}, {l_n} ROI): общая точность практически "
            "не изменилась — {l_y_acc} → {l_e_acc} (Δ = {l_d_acc}, {l_p_acc}, статистически "
            "незначимо). Однако макро-чувствительность выросла {l_y_sens} → {l_e_sens} "
            "(Δ = {l_d_sens}, {l_p_sens}), а макро-AUC — {l_y_auc} → {l_e_auc} ({l_p_auc})."),
    p33_b3=("**YOLO11l-v2** (сильнейший детектор, α* = {v_a}, {v_n} ROI): точность "
            "{v_y_acc} → {v_e_acc} ({v_p_acc}) — незначимо; значимо вырос только макро-AUC "
            "{v_y_auc} → {v_e_auc} ({v_p_auc})."),
    p33c=("Картина вскрывает чёткую закономерность: **чем сильнее детектор, тем уже выигрыш "
          "ансамбля и тем больше он смещается от точности к чувствительности и разделяющей "
          "способности (AUC).** Неизменность общей точности не означает бесполезности ансамбля "
          "— она попросту определяется преобладающим классом (лимфатический узел)."),
    s34="3.4. Откуда берётся выигрыш: разрез по классам",
    p34a=("Таблица 5 и рисунок 4 показывают это наглядно (YOLO11l). Ансамбль резко повышает "
          "чувствительность в редких, клинически значимых классах: кальцинаты {calc_y} → "
          "{calc_e}, асимметрия {asym_y} → {asym_e}, BIRADS 1-2 {b12_y} → {b12_e}. Ценой этого "
          "чувствительность к преобладающему классу лимфатических узлов снижается с {lymph_y} "
          "до {lymph_e}."),
    p34b=("Именно этот обмен оставляет общую точность почти неизменной, но повышает "
          "макро-чувствительность и AUC. В контексте скрининга это приемлемый компромисс: "
          "пропуск кальцинатов и асимметрии обходится значительно дороже, чем неверная разметка "
          "лимфатического узла. ROC-кривые на рисунке 3 подтверждают превосходство ансамбля во "
          "всём диапазоне рабочих точек."),
    s35="3.5. Чувствительность к порогам уверенности и IoU",
    p35a=("В таблице 6 приведены варианты с изменёнными порогами (на базе YOLO11s). При "
          "повышении порога до conf = 0,15 ({hi_n} сопоставленных ROI) детектор сам достигает "
          "точности {hi_y_acc}, поскольку низкоуверенные выходы отфильтровываются; ансамбль в "
          "этом случае вообще не меняет решений ({hi_e_acc}, {hi_p_acc}). При этом макро-AUC "
          "растёт с {hi_y_auc} до {hi_e_auc} — качество ранжирования всё равно улучшается, хотя "
          "решение argmax не меняется."),
    p35b=("При ужесточении порога сопоставления до IoU ≥ 0,5 ({io_n} ROI) ансамбль повышает "
          "точность с {io_y_acc} до {io_e_acc} ({io_pp_acc} процентных пункта, {io_p_acc}). "
          "Таким образом, на геометрически более точных, но труднее классифицируемых детекциях "
          "вклад булева классификатора сохраняется."),
    s4="4. Обсуждение",
    p4a=("В литературе гибридные методы обычно обосновываются средним приростом точности. Наш "
         "анализ показывает, что в условиях сильного детектора и несбалансированной базы такое "
         "обоснование недостаточно и даже способно ввести в заблуждение: для YOLO11l точность "
         "фактически не изменилась ({l_p_acc}), тогда как макро-чувствительность выросла на "
         "{l_d_sens}. Если бы приводилась только точность, метод сочли бы бесполезным; если бы "
         "только чувствительность — прирост был бы преувеличен. Верное решение — приводить обе "
         "величины вместе."),
    p4b=("Второе важное наблюдение — булев классификатор сам по себе даёт высокий AUC "
         "({bf_auc}) при низкой точности ({bf_acc}). Это означает, что его информационный "
         "вклад заключён не в решающем правиле, а в ранжировании классов. Ансамбль как раз "
         "добавляет эту ранжирующую информацию к оценке уверенности детектора."),
    p4c=("Рекомендация для клинического рабочего процесса: не вмешивать булев классификатор в "
         "уверенные решения сильного детектора, а применять его как «второе мнение» в областях "
         "с низкой уверенностью и при подозрении на редкие классы. Поскольку классификатор "
         "полностью интерпретируем (отобранные {n_star} признаков и расстояния до эталонов явно "
         "доступны), его оценка может быть проверена рентгенологом."),
    p4d=("**Ограничения.** Объём базы невелик: число сопоставленных детекций на проверочной "
         "выборке составляет 75–105, в отдельных классах 3–6 примеров. Поэтому доверительные "
         "интервалы широки, и ряд разностей статистически незначим (таблица 4). Хотя α* "
         "выбирался на обучающей выборке, она также ограничена по объёму. В классе "
         "архитектурной перестройки всего два обучающих примера, и на проверочной выборке он не "
         "был сопоставлен. Выводы требуют воспроизведения на большей многоцентровой базе."),
    s5="5. Заключение",
    concl=[
        "Отбор признаков на основе критерия булева программирования обобщён на многоклассовую "
        "маммографическую задачу; по кросс-валидации наилучший результат дали n′* = {n_star} "
        "признаков из 38 (P = {cv_ci}), однако статистическое превосходство над соседними "
        "значениями n′ не доказано.",
        "Показано, что на несбалансированной базе общая точность недостаточна как единственный "
        "критерий: для YOLO11l ансамбль не изменил точность ({l_p_acc}), но повысил "
        "макро-чувствительность с {l_y_sens} до {l_e_sens} ({l_p_sens}) и макро-AUC с "
        "{l_y_auc} до {l_e_auc}.",
        "Для более слабого детектора (YOLO11s) ансамбль значимо улучшил все критерии: точность "
        "{s_y_acc} → {s_e_acc} ({s_p_acc}), AUC {s_y_auc} → {s_e_auc}, каппа Коэна "
        "{s_y_kappa} → {s_e_kappa}.",
        "Выигрыш сосредоточен в редких, клинически значимых классах (кальцинаты {calc_y} → "
        "{calc_e}, асимметрия {asym_y} → {asym_e}) и достигается за счёт преобладающего класса "
        "— приемлемый для скрининга компромисс.",
        "Булев классификатор отдельно показывает высокую разделяющую способность ({bf_auc}) при "
        "низкой точности ({bf_acc}), то есть его роль — дополнять детектор, а не заменять его.",
    ],
    refs_h="Литература",
    t1_cap="Таблица 1. Распределение ROI в базе данных",
    t2_cap="Таблица 2. Влияние числа отобранных признаков n′ на качество классификации "
           "(в скобках 95% бутстреп-доверительный интервал)",
    t3_cap="Таблица 3. Полный набор метрик на проверочной выборке (с 95% доверительными интервалами)",
    t4_cap="Таблица 4. Разность Δ между ансамблем и одиночным детектором: парный бутстреп, "
           "95% ДИ и p-значение",
    t5_cap="Таблица 5. Чувствительность, специфичность и точность в разрезе классов (YOLO11l)",
    t6_cap="Таблица 6. Чувствительность к порогам уверенности (conf) и сопоставления (IoU) (YOLO11s)",
    f1_cap="Рисунок 1. Зависимость качества классификации от числа отобранных признаков n′; "
           "затенение — 95% бутстреп-доверительный интервал",
    f2_cap="Рисунок 2. Влияние веса ансамбля α на сбалансированную точность (YOLO11l). "
           "α* выбирается на обучающей выборке, кривая val — только для оценки",
    f3_cap="Рисунок 3. Макро-ROC-кривые (YOLO11l): ансамбль превосходит одиночный детектор во "
           "всём диапазоне рабочих точек",
    f4_cap="Рисунок 4. Чувствительность в разрезе классов: одиночный YOLO11l и гибридный "
           "ансамбль (в скобках число примеров в проверочной выборке)",
    f5_cap="Рисунок 5. Матрица ошибок ансамбля (YOLO11l); цвет нормирован по строкам, "
           "числа — количество ROI",
    t1_h=["Класс", "Обучающих ROI", "Проверочных ROI"],
    t2_h=["n′", "Точность CV (train)", "Точность (val)", "Сбаланс. точность", "AUC (макро)"],
    t3_h=["Детектор", "Метод", "Точность", "Сбаланс. точн.", "Специфичность", "F1 (макро)",
          "AUC (макро)", "MCC", "κ"],
    t4_h=["Детектор", "Критерий", "Δ (ансамбль − YOLO)", "p-значение", "Значимо"],
    t5_h=["Класс", "n", "Чувств. YOLO", "Чувств. анс.", "Специф. YOLO", "Специф. анс.",
          "Точн. YOLO", "Точн. анс."],
    t6_h=["Настройка", "Сопост. ROI", "Точн. YOLO", "Точн. анс.", "Чувств. YOLO", "Чувств. анс.",
          "AUC YOLO", "AUC анс.", "p (Δточность)"],
    t6_names=["conf = 0,05; IoU = 0,3 (базовая)", "conf = 0,15; IoU = 0,3", "conf = 0,05; IoU = 0,5"],
)

T["en"] = dict(
    title="Boolean Feature Selection and a Hybrid Ensemble for Mammographic ROI "
          "Classification: Sensitivity and Discrimination Improve, Accuracy Does Not",
    authors="H. Turaqulov  ·  supervisor: Prof. R. Kh. Khamdamov",
    affil="Tashkent University of Information Technologies named after Muhammad al-Khwarizmi",
    udk="UDC 004.93:519.86:618.19",
    abs_h="Abstract", kw_h="Keywords",
    kw="Boolean programming, informative feature selection, minimum-distance classifier, "
       "radiomics, mammography, YOLO, hybrid ensemble, sensitivity, ROC-AUC, class imbalance, "
       "interpretable artificial intelligence.",
    abstract=(
        "This paper applies an informative-feature-selection method grounded in R. Kh. "
        "Khamdamov's theory of Boolean programming, together with a minimum-distance classifier, "
        "to the classification of mammographic regions of interest (ROIs), and combines it with "
        "a YOLO detector into a hybrid ensemble. Experiments were conducted on an eight-class, "
        "strongly imbalanced mammography dataset ({n_tr} training and {n_val} validation ROIs). "
        "The ensemble weight α* was selected exclusively on the training split, the validation "
        "split being reserved for final evaluation; every metric is reported with a 95% "
        "bootstrap confidence interval, and the ensemble-versus-detector difference is assessed "
        "by a paired bootstrap. Of the 38 features, n′* = {n_star} proved optimal "
        "(cross-validation P = {cv_ci}). The principal finding is that on an imbalanced dataset "
        "overall accuracy is inadequate as a sole criterion: for the strong detector (YOLO11l) "
        "the ensemble leaves accuracy essentially unchanged ({l_y_acc} → {l_e_acc}, {l_p_acc}), "
        "yet raises macro sensitivity from {l_y_sens} to {l_e_sens} ({l_p_sens}) and macro "
        "ROC-AUC from {l_y_auc} to {l_e_auc}. For the weaker detector (YOLO11s) every criterion "
        "improves significantly: accuracy {s_y_acc} → {s_e_acc} ({s_p_acc}), AUC "
        "{s_y_auc} → {s_e_auc}, Cohen's κ {s_y_kappa} → {s_e_kappa}. The Boolean classifier "
        "alone combines low accuracy ({bf_acc}) with high discrimination ({bf_auc}), which "
        "attests to a complementary rather than a substitutive role. The gain is concentrated "
        "in the rare, clinically important classes: sensitivity to calcification "
        "{calc_y} → {calc_e}, to asymmetry {asym_y} → {asym_e}."),
    s1="1. Introduction",
    p1a=("Modern single-stage detectors of the YOLO family deliver high throughput and "
         "acceptable accuracy in the analysis of mammograms. As deep neural networks, however, "
         "they remain black boxes and do not answer the question \"which feature led to this "
         "decision?\" that is required to justify a clinical conclusion."),
    p1b=("Furthermore, mammography datasets are inherently imbalanced: in our collection lymph "
         "nodes account for a large share of the {n_tr} ROIs, whereas architectural distortion "
         "appears in only two examples. Under such conditions overall accuracy is governed by "
         "the majority class and can mask a model's true quality. This paper therefore reports "
         "balanced accuracy (macro sensitivity), specificity, F1, ROC-AUC, the Matthews "
         "correlation coefficient (MCC) and Cohen's κ together."),
    p1c=("A two-stage architecture is proposed. In the first stage a YOLO detector localises the "
         "regions of interest (ROIs). In the second stage a fully interpretable classifier, "
         "grounded in R. Kh. Khamdamov's theory of Boolean programming problems [1], "
         "re-evaluates each ROI in a 38-dimensional radiomic feature space. The outputs of the "
         "two stages are combined through a weighted ensemble."),
    p1d=("The scientific novelty is threefold: (i) the Boolean feature-selection criterion is "
         "generalised to a multi-class mammographic problem; (ii) it is established "
         "statistically — through confidence intervals and a paired bootstrap — in which "
         "criterion and in which classes the hybrid ensemble's benefit actually appears; and "
         "(iii) the dependence of that benefit on detector strength and on the confidence "
         "threshold is quantified."),
    s2="2. Materials and Method",
    s21="2.1. Dataset and Experimental Protocol",
    p21=("An eight-class mammography dataset was used: {n_tr} training and {n_val} validation "
         "ROIs (drawn from {img_tr} and {img_val} images respectively). The dataset is strongly "
         "imbalanced — see Table 1."),
    p21b=("**Protocol.** The ensemble weight α* was selected solely on the matched detections of "
          "the training split, by balanced accuracy; the validation split took part in no "
          "selection whatsoever and served only for the final evaluation. For every metric a 95% "
          "confidence interval was obtained by bootstrap (1000 resamples). The difference "
          "between the ensemble and the stand-alone detector (Δ) was assessed by a paired "
          "bootstrap with a two-sided p-value. YOLO's outputs are matched greedily against the "
          "ground-truth ROIs subject to IoU ≥ 0.3."),
    s22="2.2. Feature Space",
    p22=("Thirty-eight radiomic features are extracted from each ROI patch: first-order "
         "statistics (mean, variance, skewness, kurtosis), gradient descriptors (mean and "
         "standard deviation of the Sobel operator), and GLCM features at two distances "
         "(d = 1 and d = 3): contrast, dissimilarity, homogeneity, energy, correlation and "
         "entropy. The features are standardised using the training-split statistics."),
    s23="2.3. The Boolean Feature-Selection Criterion",
    p23a=("Following Khamdamov [1, Eq. (3.2.2)], the between-class scatter a_j and the "
          "within-class scatters b_j and c_j are introduced for a class pair (p, q) and the "
          "j-th feature:"),
    p23b=("Here x_plj denotes the value of the j-th feature for the l-th object of class p, and "
          "k_p is the number of objects in class p. To generalise to the multi-class case "
          "(m = 8) a global regime is adopted: a_j is summed over all pairs (p, q), while "
          "w_j = b_j + c_j is summed over all within-class scatters."),
    p23c=("The search for the informative feature subset reduces to a Boolean programming "
          "problem, where λ_j ∈ {{0, 1}} indicates selection of the j-th feature. The objective "
          "functional maximises the ratio of between-class to within-class scatter:"),
    s24="2.4. Ranking and Prefix-Based Selection",
    p24a=("The method of generalised inequalities [1, Sec. 3.4], through Eq. (3.4.5), permits "
          "the features to be ordered by decreasing ratio r_j:"),
    p24b=("The prefixes of the ranked sequence form a chain along which Φ(λ) decreases "
          "monotonically. Under the hard constraint |S| = n′ a prefix is not in general the "
          "absolutely optimal subset; result (3.4.4) of the monograph establishes precisely the "
          "chain property of prefixes. The final value of n′ is therefore selected not by Φ but "
          "by the cross-validated classification quality P:"),
    s25="2.5. The Minimum-Distance Classifier",
    p25a=("For every class p a reference vector (centroid) and a within-class scatter are "
          "computed [1, Eqs. (3.6.2)–(3.6.3)]:"),
    p25b=("For a new object x the normalised distance and the decision rule read:"),
    p25c=("For the ensemble, the distances are converted into probability-like scores via a "
          "softmax transform:"),
    p25d=("For small classes with k_p < 5 a leave-one-out scheme is used in cross-validation, "
          "and a stratified 5-fold scheme for the remainder. The estimate is computed from "
          "pooled predictions rather than as a mean over folds: for the small classes a "
          "leave-one-out fold contains a single object, so its accuracy takes only the values 0 "
          "or 1 and a mean ± standard deviation would be spuriously large."),
    s26="2.6. The Hybrid Ensemble and the Quality Criteria",
    p26=("The YOLO detector's output for class p, distributed according to the confidence value, "
         "is combined with the Boolean classifier's score through a weighted sum:"),
    p26b=("Classification reliability [1, Eq. (3.6.4)] is measured as the fraction of correctly "
          "recognised objects, where I[·] is the indicator function:"),
    p26c=("For an imbalanced dataset this criterion alone is insufficient. Each class c is "
          "therefore treated in a one-versus-rest scheme and the sensitivity TP/(TP+FN), "
          "specificity TN/(TN+FP), precision TP/(TP+FP) and F1 are computed; their macro "
          "averages are reported together with the macro ROC-AUC, MCC and Cohen's κ. Balanced "
          "accuracy equals macro sensitivity."),
    s3="3. Results",
    s31="3.1. Selected Features and the Value of n′*",
    p31a=("The leading positions of the ranked sequence were occupied by the GLCM correlation "
          "features: {top5}. This indicates that the textural orientation and the gradient "
          "dispersion of pathological regions carry the most information."),
    p31b=("The search over the prefix length (Table 2, Figure 1) attained its cross-validation "
          "maximum at n′* = {n_star} (P = {cv_ci}); on the held-out validation split the "
          "accuracy for this n′ was {val_ci} and the macro AUC {val_auc_ci}. Using all 38 "
          "features degrades the result slightly (CV {cv38}, val {acc38})."),
    p31c=("**An honest reading.** The confidence intervals in Figure 1 overlap substantially "
          "between neighbouring values of n′: for instance, the validation intervals for "
          "n′ = 13 and n′ = {n_star} overlap. The data are therefore insufficient to resolve n′ "
          "to a single unit; n′* = {n_star} is the best choice by cross-validation, but its "
          "statistical superiority over neighbouring values is not established. We state this "
          "openly rather than conceal it."),
    s32="3.2. The Boolean Classifier in Isolation",
    p32=("On the ground-truth ROIs (without a detector, {n_val} ROIs) the Boolean classifier "
         "attained an accuracy of {bf_acc}, a macro sensitivity of {bf_sens}, a macro "
         "specificity of {bf_spec} and a macro ROC-AUC of {bf_auc}. The combination of low "
         "accuracy with high AUC is telling: the model is strong at **ranking** the classes but "
         "suffers from the imbalance when a decision is taken by the argmin rule. That is "
         "precisely why it cannot replace the detector, yet complements it."),
    s33="3.3. The Hybrid Ensemble: Which Criterion Improves?",
    p33a=("The full metric set for the three detectors appears in Table 3, and the statistical "
          "significance of the differences in Table 4. The result is not uniform — and that is "
          "the interesting part:"),
    p33_b1=("**YOLO11s** (the weaker detector, α* = {s_a}, {s_n} matched ROIs): every principal "
            "criterion improved significantly — accuracy {s_y_acc} → {s_e_acc} (Δ = {s_d_acc}, "
            "{s_p_acc}), macro sensitivity {s_y_sens} → {s_e_sens} ({s_p_sens}), macro AUC "
            "{s_y_auc} → {s_e_auc} ({s_p_auc}), Cohen's κ {s_y_kappa} → {s_e_kappa} "
            "({s_p_kappa})."),
    p33_b2=("**YOLO11l** (a strong detector, α* = {l_a}, {l_n} ROIs): overall accuracy barely "
            "moved — {l_y_acc} → {l_e_acc} (Δ = {l_d_acc}, {l_p_acc}, i.e. not statistically "
            "significant). Macro sensitivity, however, rose {l_y_sens} → {l_e_sens} "
            "(Δ = {l_d_sens}, {l_p_sens}) and macro AUC {l_y_auc} → {l_e_auc} ({l_p_auc})."),
    p33_b3=("**YOLO11l-v2** (the strongest detector, α* = {v_a}, {v_n} ROIs): accuracy "
            "{v_y_acc} → {v_e_acc} ({v_p_acc}) — not significant; only the macro AUC improved "
            "significantly, {v_y_auc} → {v_e_auc} ({v_p_auc})."),
    p33c=("This picture reveals a clear regularity: **the stronger the detector, the narrower "
          "the ensemble's benefit, and the more it shifts from accuracy towards sensitivity and "
          "discrimination (AUC).** An unchanged overall accuracy does not mean the ensemble is "
          "useless — accuracy is simply dominated by the majority class (lymph node)."),
    s34="3.4. Where the Gain Comes From: A Per-Class View",
    p34a=("Table 5 and Figure 4 make this plain (YOLO11l). The ensemble sharply raises "
          "sensitivity in the rare, clinically important classes: calcification "
          "{calc_y} → {calc_e}, asymmetry {asym_y} → {asym_e}, BIRADS 1-2 {b12_y} → {b12_e}. "
          "The price is a fall in sensitivity for the majority lymph-node class, from "
          "{lymph_y} to {lymph_e}."),
    p34b=("It is exactly this trade that leaves overall accuracy almost unchanged while raising "
          "macro sensitivity and AUC. In a screening context the trade is acceptable: missing "
          "calcifications and asymmetries costs considerably more than mislabelling a lymph "
          "node. The ROC curves of Figure 3 confirm the ensemble's superiority across the whole "
          "range of operating points."),
    s35="3.5. Sensitivity to the Confidence and IoU Thresholds",
    p35a=("Table 6 reports the variants with altered thresholds (based on YOLO11s). When the "
          "threshold is raised to conf = 0.15 ({hi_n} matched ROIs) the detector alone reaches "
          "an accuracy of {hi_y_acc}, because the low-confidence outputs are filtered away; in "
          "this regime the ensemble changes no decisions at all ({hi_e_acc}, {hi_p_acc}). Yet "
          "the macro AUC still rises from {hi_y_auc} to {hi_e_auc} — the ranking quality "
          "improves even though the argmax decision does not change."),
    p35b=("When the matching threshold is tightened to IoU ≥ 0.5 ({io_n} ROIs) the ensemble "
          "raises accuracy from {io_y_acc} to {io_e_acc} ({io_pp_acc} percentage points, "
          "{io_p_acc}). The Boolean classifier's contribution is thus preserved on the "
          "geometrically more precise but harder-to-classify detections."),
    s4="4. Discussion",
    p4a=("In the literature, hybrid methods are usually justified by an average gain in "
         "accuracy. Our analysis shows that, with a strong detector and an imbalanced dataset, "
         "such a justification is insufficient and can even mislead: for YOLO11l the accuracy "
         "did not in fact change ({l_p_acc}), whereas macro sensitivity rose by {l_d_sens}. Had "
         "accuracy alone been reported, the method would have been judged useless; had "
         "sensitivity alone been reported, the gain would have been overstated. The correct "
         "course is to report both."),
    p4b=("A second important observation is that the Boolean classifier in isolation yields a "
         "high AUC ({bf_auc}) at a low accuracy ({bf_acc}). Its informational contribution "
         "therefore resides not in the decision rule but in the ranking of classes. The ensemble "
         "adds precisely this ranking information to the detector's confidence estimate."),
    p4c=("A recommendation for the clinical workflow follows: do not let the Boolean classifier "
         "interfere with a strong detector's confident decisions; apply it as a \"second "
         "opinion\" in low-confidence regions and where a rare class is suspected. Because the "
         "classifier is fully interpretable — the {n_star} selected features and the distances "
         "to the class centroids are explicitly available — its verdict can be audited by the "
         "radiologist."),
    p4d=("**Limitations.** The dataset is small: the number of matched detections on the "
         "validation split ranges from 75 to 105, with only 3–6 examples in some classes. The "
         "confidence intervals are consequently wide and several differences are not "
         "statistically significant (Table 4). Although α* was selected on the training split, "
         "that split too is limited in size. The architectural-distortion class has only two "
         "training examples and was not matched at all on the validation split. These findings "
         "should be reproduced on a larger, multi-centre dataset."),
    s5="5. Conclusion",
    concl=[
        "Feature selection based on the Boolean programming criterion was generalised to a "
        "multi-class mammographic problem; by cross-validation, n′* = {n_star} of the 38 "
        "features gave the best result (P = {cv_ci}), although statistical superiority over "
        "neighbouring values of n′ was not established.",
        "Overall accuracy was shown to be inadequate as a sole criterion on an imbalanced "
        "dataset: for YOLO11l the ensemble left accuracy unchanged ({l_p_acc}) but raised macro "
        "sensitivity from {l_y_sens} to {l_e_sens} ({l_p_sens}) and macro AUC from {l_y_auc} to "
        "{l_e_auc}.",
        "For the weaker detector (YOLO11s) the ensemble significantly improved every criterion: "
        "accuracy {s_y_acc} → {s_e_acc} ({s_p_acc}), AUC {s_y_auc} → {s_e_auc}, Cohen's κ "
        "{s_y_kappa} → {s_e_kappa}.",
        "The gain is concentrated in the rare, clinically important classes (calcification "
        "{calc_y} → {calc_e}, asymmetry {asym_y} → {asym_e}) and is obtained at the expense of "
        "the majority class — a trade acceptable for screening.",
        "In isolation the Boolean classifier shows high discrimination ({bf_auc}) at low "
        "accuracy ({bf_acc}); its role is therefore to complement the detector, not to replace "
        "it.",
    ],
    refs_h="References",
    t1_cap="Table 1. Distribution of ROIs in the dataset",
    t2_cap="Table 2. Effect of the number of selected features n′ on classification quality "
           "(95% bootstrap confidence interval in brackets)",
    t3_cap="Table 3. Full metric set on the validation split (with 95% confidence intervals)",
    t4_cap="Table 4. Difference Δ between the ensemble and the stand-alone detector: paired "
           "bootstrap, 95% CI and p-value",
    t5_cap="Table 5. Per-class sensitivity, specificity and precision (YOLO11l)",
    t6_cap="Table 6. Sensitivity to the confidence (conf) and matching (IoU) thresholds (YOLO11s)",
    f1_cap="Figure 1. Classification quality as a function of the number of selected features "
           "n′; shading is the 95% bootstrap confidence interval",
    f2_cap="Figure 2. Effect of the ensemble weight α on balanced accuracy (YOLO11l). α* is "
           "selected on the training split; the validation curve is shown for evaluation only",
    f3_cap="Figure 3. Macro ROC curves (YOLO11l): the ensemble dominates the stand-alone "
           "detector across the whole range of operating points",
    f4_cap="Figure 4. Per-class sensitivity: stand-alone YOLO11l versus the hybrid ensemble "
           "(number of validation examples in brackets)",
    f5_cap="Figure 5. Ensemble confusion matrix (YOLO11l); colour is row-normalised, figures "
           "are ROI counts",
    t1_h=["Class", "Training ROIs", "Validation ROIs"],
    t2_h=["n′", "CV accuracy (train)", "Accuracy (val)", "Balanced acc.", "AUC (macro)"],
    t3_h=["Detector", "Method", "Accuracy", "Balanced acc.", "Specificity", "F1 (macro)",
          "AUC (macro)", "MCC", "κ"],
    t4_h=["Detector", "Criterion", "Δ (ensemble − YOLO)", "p-value", "Significant"],
    t5_h=["Class", "n", "Sens. YOLO", "Sens. ens.", "Spec. YOLO", "Spec. ens.",
          "Prec. YOLO", "Prec. ens."],
    t6_h=["Setting", "Matched ROIs", "Acc. YOLO", "Acc. ens.", "Sens. YOLO", "Sens. ens.",
          "AUC YOLO", "AUC ens.", "p (Δaccuracy)"],
    t6_names=["conf = 0.05, IoU = 0.3 (baseline)", "conf = 0.15, IoU = 0.3", "conf = 0.05, IoU = 0.5"],
)

REFS = [
    "Хамдамов Р.Х. Задачи, модели и методы булева программирования. — Ташкент, 2017. — Гл. III.",
    "Haralick R.M., Shanmugam K., Dinstein I. Textural Features for Image Classification // "
    "IEEE Transactions on Systems, Man, and Cybernetics. — 1973. — Vol. SMC-3, No. 6. — P. 610–621.",
    "Jocher G., Qiu J., Chaurasia A. Ultralytics YOLO (Version 11). — 2024. — "
    "https://github.com/ultralytics/ultralytics",
    "van Griethuysen J.J.M. et al. Computational Radiomics System to Decode the Radiographic "
    "Phenotype // Cancer Research. — 2017. — Vol. 77, No. 21. — P. e104–e107.",
    "Guyon I., Elisseeff A. An Introduction to Variable and Feature Selection // Journal of "
    "Machine Learning Research. — 2003. — Vol. 3. — P. 1157–1182.",
    "Chicco D., Jurman G. The advantages of the Matthews correlation coefficient (MCC) over F1 "
    "score and accuracy in binary classification evaluation // BMC Genomics. — 2020. — Vol. 21. — P. 6.",
    "Efron B., Tibshirani R.J. An Introduction to the Bootstrap. — New York: Chapman & Hall, 1993.",
    "Rudin C. Stop Explaining Black Box Machine Learning Models for High Stakes Decisions and "
    "Use Interpretable Models Instead // Nature Machine Intelligence. — 2019. — Vol. 1. — P. 206–215.",
]


# --------------------------------------------------------------------------- #
# Docx qurish                                                                 #
# --------------------------------------------------------------------------- #
def setup(doc):
    st = doc.styles["Normal"]
    st.font.name = "Times New Roman"
    st.font.size = Pt(12)
    st.paragraph_format.line_spacing = 1.5
    st.paragraph_format.space_after = Pt(0)
    for s in doc.sections:
        s.left_margin = s.right_margin = Cm(2.2)
        s.top_margin = s.bottom_margin = Cm(2.0)


def para(doc, text, first_indent=True, size=12, align=None):
    p = doc.add_paragraph()
    p.alignment = align if align is not None else WD_ALIGN_PARAGRAPH.JUSTIFY
    if first_indent:
        p.paragraph_format.first_line_indent = Cm(1.25)
    for i, seg in enumerate(text.split("**")):
        r = p.add_run(seg)
        r.font.size = Pt(size)
        r.bold = (i % 2 == 1)
    return p


def heading(doc, text, size=13):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(4)
    r = p.add_run(text)
    r.bold = True
    r.font.size = Pt(size)
    r.font.color.rgb = ACCENT
    return p


def caption(doc, text, before=False):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6 if before else 2)
    p.paragraph_format.space_after = Pt(8 if not before else 2)
    r = p.add_run(text)
    r.italic = True
    r.font.size = Pt(9.5)
    r.font.color.rgb = RGBColor(0x33, 0x33, 0x33)


def table(doc, header, rows, size=8.5):
    t = doc.add_table(rows=1, cols=len(header))
    t.style = "Table Grid"
    for i, h in enumerate(header):
        c = t.rows[0].cells[i]
        c.text = ""
        r = c.paragraphs[0].add_run(str(h))
        r.bold = True
        r.font.size = Pt(size)
        c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""
            r = cells[i].paragraphs[0].add_run(str(v))
            r.font.size = Pt(size)
            cells[i].paragraphs[0].alignment = (
                WD_ALIGN_PARAGRAPH.LEFT if i == 0 else WD_ALIGN_PARAGRAPH.CENTER)
    return t


def picture(doc, path, cap, width=6.2):
    doc.add_picture(str(path), width=Inches(width))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption(doc, cap)


def build(lang, met, nsw, art):
    t = T[lang]
    v = vals_for(lang, met, nsw, art)
    fig = ASSETS / lang
    doc = Document()
    setup(doc)

    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(t["udk"]); r.font.size = Pt(10); r.font.color.rgb = RGBColor(0x55, 0x55, 0x55)
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(8)
    r = p.add_run(t["title"]); r.bold = True; r.font.size = Pt(15); r.font.color.rgb = ACCENT
    for txt, sz in ((t["authors"], 12), (t["affil"], 10.5)):
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(txt); r.font.size = Pt(sz)
        if sz < 12:
            r.italic = True
            r.font.color.rgb = RGBColor(0x55, 0x55, 0x55)

    heading(doc, t["abs_h"])
    para(doc, t["abstract"].format(**v), size=11)
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Cm(1.25)
    p.paragraph_format.space_before = Pt(6)
    r = p.add_run(t["kw_h"] + ": "); r.bold = True; r.font.size = Pt(11)
    r = p.add_run(t["kw"]); r.italic = True; r.font.size = Pt(11)

    heading(doc, t["s1"])
    for k in ("p1a", "p1b", "p1c", "p1d"):
        para(doc, t[k].format(**v))

    heading(doc, t["s2"])
    heading(doc, t["s21"], size=12)
    para(doc, t["p21"].format(**v))
    para(doc, t["p21b"])
    caption(doc, t["t1_cap"], before=True)
    table(doc, t["t1_h"], t1_rows(lang, met, art), size=9.5)

    heading(doc, t["s22"], size=12)
    para(doc, t["p22"])
    heading(doc, t["s23"], size=12)
    para(doc, t["p23a"])
    add_equation(doc, *F.eq_a(), number=1)
    add_equation(doc, *F.eq_b(), number=2)
    add_equation(doc, *F.eq_c(), number=3)
    para(doc, t["p23b"])
    para(doc, t["p23c"])
    add_equation(doc, *F.eq_phi(), number=4)

    heading(doc, t["s24"], size=12)
    para(doc, t["p24a"])
    add_equation(doc, *F.eq_rank(), number=5)
    para(doc, t["p24b"])
    add_equation(doc, *F.eq_nstar(), number=6)

    heading(doc, t["s25"], size=12)
    para(doc, t["p25a"])
    add_equation(doc, *F.eq_centroid(), number=7)
    add_equation(doc, *F.eq_scatter(), number=8)
    para(doc, t["p25b"])
    add_equation(doc, *F.eq_rho(), number=9)
    add_equation(doc, *F.eq_decision(), number=10)
    para(doc, t["p25c"])
    add_equation(doc, *F.eq_softmax(), number=11)
    para(doc, t["p25d"])

    heading(doc, t["s26"], size=12)
    para(doc, t["p26"])
    add_equation(doc, *F.eq_ensemble(), number=12)
    para(doc, t["p26b"])
    add_equation(doc, *F.eq_P(), number=13)
    para(doc, t["p26c"])

    heading(doc, t["s3"])
    heading(doc, t["s31"], size=12)
    para(doc, t["p31a"].format(**v))
    para(doc, t["p31b"].format(**v))
    caption(doc, t["t2_cap"], before=True)
    table(doc, t["t2_h"], t2_rows(lang, nsw), size=9)
    picture(doc, fig / "fig1_nsweep.png", t["f1_cap"])
    para(doc, t["p31c"].format(**v))

    heading(doc, t["s32"], size=12)
    para(doc, t["p32"].format(**v))

    heading(doc, t["s33"], size=12)
    para(doc, t["p33a"])
    for k in ("p33_b1", "p33_b2", "p33_b3"):
        para(doc, t[k].format(**v))
    caption(doc, t["t3_cap"], before=True)
    table(doc, t["t3_h"], t3_rows(lang, met), size=7.5)
    caption(doc, t["t4_cap"], before=True)
    table(doc, t["t4_h"], t4_rows(lang, met), size=8.5)
    picture(doc, fig / "fig2_alpha.png", t["f2_cap"])
    para(doc, t["p33c"])

    heading(doc, t["s34"], size=12)
    para(doc, t["p34a"].format(**v))
    caption(doc, t["t5_cap"], before=True)
    table(doc, t["t5_h"], t5_rows(lang, met), size=8.5)
    picture(doc, fig / "fig4_sens.png", t["f4_cap"])
    para(doc, t["p34b"])
    picture(doc, fig / "fig3_roc.png", t["f3_cap"], width=4.6)
    picture(doc, fig / "fig5_cm.png", t["f5_cap"], width=5.4)

    heading(doc, t["s35"], size=12)
    para(doc, t["p35a"].format(**v))
    para(doc, t["p35b"].format(**v))
    caption(doc, t["t6_cap"], before=True)
    table(doc, t["t6_h"], t6_rows(lang, met), size=8)

    heading(doc, t["s4"])
    for k in ("p4a", "p4b", "p4c", "p4d"):
        para(doc, t[k].format(**v))

    heading(doc, t["s5"])
    for i, c in enumerate(t["concl"], 1):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.first_line_indent = Cm(1.25)
        p.add_run(f"{i}. ").bold = True
        for j, seg in enumerate(c.format(**v).split("**")):
            p.add_run(seg).bold = (j % 2 == 1)

    heading(doc, t["refs_h"])
    for i, ref in enumerate(REFS, 1):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.left_indent = Cm(0.8)
        p.paragraph_format.first_line_indent = Cm(-0.8)
        p.add_run(f"{i}. {ref}").font.size = Pt(10.5)

    out = ROOT / f"MAMOGRAF_Maqola_2026_Ansambl_{lang.upper()}.docx"
    doc.save(out)
    return out


def main():
    met, nsw, art = load()
    for lang in ("uz", "ru", "en"):
        FG.build_all(lang, ASSETS / lang)
        out = build(lang, met, nsw, art)
        print(f"[maqola] {lang.upper()} tayyor: {out.name}")
    print("[maqola] Formulalar — Word native OMML; sonlar — metrics.json dan.")


if __name__ == "__main__":
    main()
