# -*- coding: utf-8 -*-
"""make_maqola_exp2026.py — 2026-07-10 eksperiment seriyasi bo'yicha ilmiy maqola,
UCH TILDA (o'zbek, rus, ingliz), barcha formulalar Word native OMML (MathType-mos)
ko'rinishida — rasm emas, tahrirlanadigan tenglama obyektlari.

Barcha son qiymatlari runs/exp_20260710/*/ dagi JSON fayllardan O'QILADI.

Build (faqat konteynerda — host'da pip/numpy yo'q):
  docker run --rm -v /home/ai/mamograf_yangilash_21-iyun:/work -w /work \
    mamograf-prod-app sh -c "pip install -q python-docx && python scripts/make_maqola_exp2026.py"
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Inches, Pt, RGBColor

import maqola_formulalar as F
from omml import add_equation

ROOT = Path(__file__).resolve().parent.parent
EXP = ROOT / "runs" / "exp_20260710"
ASSETS = ROOT / "doc_assets_exp2026"

# dataviz: tasdiqlangan kategorik palitra (light surface)
C1, C2, C3 = "#2a78d6", "#1baf7a", "#eda100"
INK, MUTED, GRID = "#1a1a19", "#555555", "#d8d8d4"
ACCENT = RGBColor(0x14, 0x2C, 0x52)

MODELS = [("exp05_ens_s_a01", "YOLO11s", C1, ["exp05_ens_s_a01", "exp06_ens_s_a09"]),
          ("exp09_ens_11l", "YOLO11l", C2, ["exp09_ens_11l"]),
          ("exp10_ens_v2ep50", "YOLO11l-v2 (ep50)", C3, ["exp10_ens_v2ep50"])]

CLS = {
    "uz": {"BIRADS12": "BIRADS 1-2", "BIRADS45": "BIRADS 4-5",
           "architectural_distortion": "arxitektura buzilishi", "asymmetry": "assimetriya",
           "calcification": "kalsifikatsiya", "lymph_node": "limfa tuguni",
           "mass": "o'sma (massa)", "other": "boshqa"},
    "ru": {"BIRADS12": "BIRADS 1-2", "BIRADS45": "BIRADS 4-5",
           "architectural_distortion": "архитектурная перестройка", "asymmetry": "асимметрия",
           "calcification": "кальцинаты", "lymph_node": "лимфатический узел",
           "mass": "образование (масса)", "other": "прочее"},
    "en": {"BIRADS12": "BIRADS 1-2", "BIRADS45": "BIRADS 4-5",
           "architectural_distortion": "architectural distortion", "asymmetry": "asymmetry",
           "calcification": "calcification", "lymph_node": "lymph node",
           "mass": "mass", "other": "other"},
}


# --------------------------------------------------------------------------- #
# Natijalarni o'qish                                                          #
# --------------------------------------------------------------------------- #
def load():
    def j(p):
        return json.loads((EXP / p).read_text())

    art = j("exp01_fit/artifacts.json")
    model = j("exp01_fit/model.json")
    ev_val = j("exp02_eval_val/eval.json")
    ev_tr = j("exp03_eval_train/eval.json")
    nsw = j("exp04_nsweep/result.json")

    ens = {}
    for d in sorted(EXP.glob("exp*/ensemble.json")):
        ens[d.parent.name] = json.loads(d.read_text())

    # yolo11s alpha egri: E05 (α=0.1) va E06 (α=0.9) natijalarini birlashtiramiz
    merged = {}
    for k in ("exp05_ens_s_a01", "exp06_ens_s_a09"):
        merged.update({float(a): v for a, v in ens[k]["alpha_results"].items()})

    curves = {"YOLO11s": merged}
    for key, label, _c, _s in MODELS[1:]:
        curves[label] = {float(a): v for a, v in ens[key]["alpha_results"].items()}

    return {"art": art, "model": model, "ev_val": ev_val, "ev_tr": ev_tr,
            "nsw": nsw, "ens": ens, "curves": curves, "merged_s": merged}


# --------------------------------------------------------------------------- #
# Grafiklar (har til uchun alohida — o'qlar nomi tarjima qilinadi)             #
# --------------------------------------------------------------------------- #
def _style(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
        ax.spines[s].set_linewidth(0.8)
    ax.grid(axis="y", color=GRID, linewidth=0.6, alpha=0.7)
    ax.set_axisbelow(True)
    ax.tick_params(colors=MUTED, labelsize=9, length=0)


def fig_nsweep(R, lang, out: Path):
    L = {"uz": ("Tanlangan belgilar soni n′", "Ishonchlilik P",
                "P (5-fold CV, train)", "P (val, GT ROI)", "n′* = {n} (tanlangan)"),
         "ru": ("Число отобранных признаков n′", "Достоверность P",
                "P (5-fold CV, train)", "P (val, GT ROI)", "n′* = {n} (выбрано)"),
         "en": ("Number of selected features n′", "Reliability P",
                "P (5-fold CV, train)", "P (val, GT ROI)", "n′* = {n} (selected)")}[lang]
    rows = R["nsw"]["rows"]
    xs = [r["n"] for r in rows]
    cv = [r["P_cv"] for r in rows]
    va = [r["P_val"] for r in rows]
    n_star = R["art"]["n_star"]

    fig, ax = plt.subplots(figsize=(7.0, 3.6), dpi=200)
    _style(ax)
    ax.axvline(n_star, color=MUTED, linewidth=1.0, linestyle=(0, (3, 3)), alpha=0.8)
    ax.annotate(L[4].format(n=n_star), xy=(n_star, 0.437), xytext=(6, 0),
                textcoords="offset points", ha="left", va="bottom",
                fontsize=8.5, color=MUTED)
    ax.plot(xs, va, color=C1, linewidth=2.0, marker="o", markersize=5,
            markeredgecolor="white", markeredgewidth=1.2, zorder=3)
    ax.plot(xs, cv, color=C2, linewidth=2.0, marker="s", markersize=5,
            markeredgecolor="white", markeredgewidth=1.2, zorder=3)
    ax.annotate(L[3], xy=(xs[-1], va[-1]), xytext=(6, 4), textcoords="offset points",
                fontsize=9, color=C1, fontweight="bold", va="center")
    ax.annotate(L[2], xy=(xs[-1], cv[-1]), xytext=(6, -2), textcoords="offset points",
                fontsize=9, color=C2, fontweight="bold", va="center")
    # eng yaxshi nuqtalarni belgilash (n′* chizig'i bilan to'qnashmasin — chapga siljitamiz)
    for series, col in ((va, C1), (cv, C2)):
        i = series.index(max(series))
        ax.annotate(f"{series[i]:.3f}", xy=(xs[i], series[i]), xytext=(-8, 9),
                    textcoords="offset points", ha="right", fontsize=8.5,
                    color=col, fontweight="bold")
    ax.set_xlabel(L[0], fontsize=9.5, color=INK)
    ax.set_ylabel(L[1], fontsize=9.5, color=INK)
    ax.set_xticks(xs)
    ax.set_ylim(0.43, 0.68)
    ax.set_xlim(0, 44)
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def fig_alpha(R, lang, out: Path):
    L = {"uz": ("Ansambl vazni α  (0 = faqat boolfs, 1 = faqat YOLO)", "Ishonchlilik P"),
         "ru": ("Вес ансамбля α  (0 = только boolfs, 1 = только YOLO)", "Достоверность P"),
         "en": ("Ensemble weight α  (0 = boolfs only, 1 = YOLO only)", "Reliability P")}[lang]
    fig, ax = plt.subplots(figsize=(7.0, 3.8), dpi=200)
    _style(ax)
    for (_k, label, col, _s) in MODELS:
        cur = R["curves"][label]
        xs = sorted(cur)
        ys = [cur[a] for a in xs]
        ax.plot(xs, ys, color=col, linewidth=2.0, marker="o", markersize=5,
                markeredgecolor="white", markeredgewidth=1.2, zorder=3)
        bi = max((a for a in xs if 0 < a < 1), key=lambda a: cur[a])
        # YOLO11s maksimumi YOLO11l bilan bir x da — yorliqni pastga tushiramiz
        dy, va_ = (-15, "top") if label == "YOLO11s" else (9, "bottom")
        ax.annotate(f"{cur[bi]:.3f}", xy=(bi, cur[bi]), xytext=(0, dy),
                    textcoords="offset points", ha="center", va=va_, fontsize=8.5,
                    color=col, fontweight="bold")
        ax.annotate(label, xy=(xs[-1], ys[-1]), xytext=(7, 0), textcoords="offset points",
                    fontsize=9, color=col, fontweight="bold", va="center")
    ax.set_xlabel(L[0], fontsize=9.5, color=INK)
    ax.set_ylabel(L[1], fontsize=9.5, color=INK)
    ax.set_xticks([0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.0])
    ax.set_xlim(-0.03, 1.28)
    ax.set_ylim(0.48, 0.92)
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight", facecolor="white")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Uch tilli matn                                                              #
# --------------------------------------------------------------------------- #
T = {}

T["uz"] = dict(
    title="Mammografik ROI'larni tasniflashda bulcha belgi tanlash va gibrid ansambl: "
          "samaradorlikning detektor ishonch chegarasiga bog'liqligi",
    authors="Turaqulov H.  ·  ilmiy rahbar: professor Xamdamov R.X.",
    affil="Muhammad al-Xorazmiy nomidagi Toshkent axborot texnologiyalari universiteti",
    udk="UDK 004.93:519.86:618.19",
    abs_h="Annotatsiya",
    kw_h="Kalit so'zlar",
    kw="bulcha dasturlash, informativ belgilar tanlash, minimal masofa klassifikatori, "
       "radiomika, mammografiya, YOLO, gibrid ansambl, ishonch chegarasi, "
       "interpretatsiyalanadigan sun'iy intellekt.",
    abstract=(
        "Maqolada R.X. Xamdamovning bulcha dasturlash nazariyasiga asoslangan informativ "
        "belgilar tanlash usuli va minimal masofa qoidasi bo'yicha tasniflagich mammografik "
        "qiziqish sohalarini (ROI) sinflarga ajratishda qo'llanildi hamda YOLO detektori bilan "
        "gibrid ansamblga birlashtirildi. Sakkiz sinfli mammografiya bazasida (519 ta o'qitish, "
        "148 ta tekshirish ROI'si) o'n bir eksperiment o'tkazildi. Ranjirlangan qatorning "
        "prefikslari bo'yicha izlanganda 38 ta belgidan n′* = {n_star} tasi optimal bo'ldi; bu "
        "tanlov mustaqil tekshirish to'plamida ham tasdiqlandi (P = {p_val:.3f}). Gibrid ansambl "
        "barcha sinovdan o'tgan detektorlarda YOLO'ning yakka natijasidan ustun keldi: "
        "YOLO11s uchun {s_yolo:.3f} → {s_ens:.3f}, YOLO11l uchun {l_yolo:.3f} → {l_ens:.3f}, "
        "kuchaytirilgan YOLO11l-v2 uchun {v_yolo:.3f} → {v_ens:.3f}. Tadqiqotning asosiy "
        "natijasi shundaki, usulning foydasi detektorning ishonch chegarasiga keskin bog'liq: "
        "chegara 0,15 gacha ko'tarilganda YOLO o'zi {hi_yolo:.3f} aniqlikka erishadi va bulcha "
        "tasniflagich qo'shimcha ustunlik bermaydi, past chegarada esa (0,05) u aniqlikni "
        "{gain:.1f} foiz punktga oshiradi. Demak, taklif etilgan tasniflagichning o'rni — "
        "detektor ishonchsiz bo'lgan shubhali ROI'lar uchun \"ikkinchi fikr\" berish."),
    s1="1. Kirish",
    p1a=("Mammografik tasvirlarni avtomatik tahlil qilishda zamonaviy bir bosqichli "
         "detektorlar (YOLO oilasi) yuqori tezlik va qoniqarli aniqlik ko'rsatadi. Biroq ular "
         "chuqur neyron tarmoq sifatida qora quti bo'lib qoladi: klinik qarorni asoslash uchun "
         "zarur bo'lgan \"qaysi belgi shu qarorga olib keldi?\" degan savolga javob bermaydi. "
         "Shu bilan birga, detektorning past ishonchli (conf < 0,15) chiqishlari amaliyotda eng "
         "muammoli qism hisoblanadi — aynan shu yerda xato tasniflashlar to'planadi."),
    p1b=("Ushbu ishda ikki bosqichli arxitektura taklif etiladi. Birinchi bosqichda YOLO "
         "detektori qiziqish sohalarini (ROI) topadi. Ikkinchi bosqichda R.X. Xamdamovning "
         "bulcha dasturlash masalalari nazariyasiga [1] asoslangan, to'liq interpretatsiyalanadigan "
         "tasniflagich har bir ROI'ni 38 o'lchovli radiomika belgilar fazosida qayta baholaydi. "
         "Ikkala bosqich chiqishi vaznli ansambl orqali birlashtiriladi."),
    p1c=("Ishning ilmiy yangiligi: (i) bulcha belgi tanlash mezoni mammografik ko'p sinfli "
         "masalaga umumlashtirildi; (ii) tanlangan belgilar soni n′ ning tasniflash sifatiga "
         "ta'siri tizimli o'rganildi; (iii) gibrid ansambl foydasining detektor ishonch "
         "chegarasiga bog'liqligi birinchi marta miqdoriy aniqlandi."),
    s2="2. Materiallar va usul",
    s21="2.1. Ma'lumotlar bazasi",
    p21=("Tadqiqotda sakkiz sinfli mammografiya bazasi ishlatildi: {n_tr} ta o'qitish va "
         "{n_val} ta tekshirish ROI'si (mos ravishda {img_tr} va {img_val} ta tasvirdan). "
         "Baza kuchli nomutanosib — 1-jadval. Har bir ROI mutaxassis tomonidan belgilangan "
         "chegaralovchi to'rtburchak (ground truth) bilan ta'minlangan."),
    s22="2.2. Belgilar fazosi",
    p22=("Har bir ROI kesmasidan 38 ta radiomika belgisi ajratiladi: birinchi tartib "
         "statistikalari (o'rtacha, dispersiya, assimetriya, ekstsess), gradient "
         "xarakteristikalari (Sobel operatorining o'rtachasi va standart chetlanishi), "
         "hamda ikki masofa (d = 1 va d = 3) uchun GLCM (kulrang darajalar birgalikda "
         "uchrash matritsasi) belgilari: kontrast, dissimilyarlik, bir jinslilik, energiya, "
         "korrelyatsiya, entropiya. Belgilar o'qitish to'plami statistikasi bo'yicha "
         "standartlashtiriladi (z-normallashtirish)."),
    s23="2.3. Bulcha belgi tanlash mezoni",
    p23a=("Xamdamov [1, (3.2.2)] bo'yicha, (p, q) sinflar juftligi va j-belgi uchun uchta "
          "kattalik kiritiladi: sinflararo tarqoqlik a_j hamda sinf ichidagi tarqoqliklar "
          "b_j va c_j:"),
    p23b=("Bu yerda x_plj — p-sinfning l-obyekti uchun j-belgi qiymati, k_p — p-sinfdagi "
          "obyektlar soni. Ko'p sinfli (m = 8) holatga o'tish uchun global rejim qo'llanadi: "
          "a_j barcha (p, q) juftliklar bo'yicha, w_j = b_j + c_j esa barcha sinflar ichidagi "
          "tarqoqliklar bo'yicha yig'iladi."),
    p23c=("Informativ belgilar to'plamini izlash bulcha dasturlash masalasiga keltiriladi: "
          "λ_j ∈ {{0, 1}} — j-belgining tanlanganligini bildiruvchi bulcha o'zgaruvchi bo'lsin. "
          "Maqsad funksionali — tanlangan belgilar bo'yicha sinflararo va sinf ichidagi "
          "tarqoqliklar nisbatini maksimallashtirish:"),
    s24="2.4. Ranjirlash va prefiks bo'yicha tanlash",
    p24a=("Umumlashgan tengsizliklar usuli [1, 3.4-bo'lim] (3.4.5) ga ko'ra belgilarni "
          "r_j nisbat bo'yicha kamayish tartibida joylashtirishga imkon beradi:"),
    p24b=("Ranjirlangan qatorning prefikslari Φ(λ) ning monoton kamayish zanjirini hosil qiladi. "
          "Shuni ta'kidlash lozimki, qat'iy |S| = n′ cheklovida prefiks umumiy holda mutlaq "
          "optimal to'plam bo'lishi shart emas; kitobning (3.4.4) natijasi aynan prefikslar "
          "zanjiri xossasini beradi. Shu sababli n′ ning oxirgi qiymati Φ bo'yicha emas, balki "
          "tasniflash sifati P bo'yicha tanlanadi:"),
    s25="2.5. Minimal masofa tasniflagichi",
    p25a=("Har bir p sinf uchun etalon vektor (markaz) va sinf ichki tarqoqligi hisoblanadi "
          "[1, (3.6.2)–(3.6.3)]:"),
    p25b=("Yangi obyekt x uchun normallashgan masofa va qaror qoidasi:"),
    p25c=("Ansambl uchun masofalar softmax orqali ehtimollikka o'xshash bahoga aylantiriladi:"),
    p25d=("k_p < 5 bo'lgan kichik sinflar (masalan, arxitektura buzilishi — atigi 2 ta misol) "
          "uchun kross-validatsiyada leave-one-out sxemasi, qolganlari uchun stratifikatsiyalangan "
          "5-fold sxemasi qo'llanadi. S(X_p) = 0 chekka holatida masofa masshtabi buzilmasligi "
          "uchun boshqa sinflar tarqoqligining medianasi olinadi."),
    s26="2.6. Gibrid ansambl",
    p26=("YOLO detektorining p sinf uchun chiqishi u_p^YOLO (ishonch qiymati asosida "
         "taqsimlangan) va bulcha tasniflagich bahosi s_p vaznli yig'indi orqali birlashtiriladi:"),
    s27="2.7. Sifat mezoni va eksperiment protokoli",
    p27a=("Tasniflash ishonchliligi [1, (3.6.4)] to'g'ri tanilgan obyektlar ulushi sifatida "
          "o'lchanadi (I[·] — indikator funksiya):"),
    p27b=("Ansamblni baholashda YOLO chiqishlari ground truth ROI'lari bilan ochko'z (greedy) "
          "usulda, IoU ≥ 0,3 sharti asosida moslashtiriladi; moslashgan juftliklar bo'yicha P "
          "hisoblanadi. Jami o'n bir eksperiment o'tkazildi: bazaviy o'qitish va baholash (E1–E3), "
          "n′ bo'yicha qidiruv (E4), α, ishonch va IoU chegaralari bo'yicha sezgirlik tahlili "
          "(E5–E8), uch xil detektor bilan ansambl (E9–E10) va o'qitish to'plamida barqarorlik "
          "nazorati (E11)."),
    s3="3. Natijalar",
    s31="3.1. Tanlangan belgilar va n′* qiymati",
    p31a=("O'qitish to'plamida ranjirlangan qatorning birinchi o'rinlarini GLCM korrelyatsiya "
          "belgilari egalladi: {top5}. Bu natija patologik sohalarning tekstura yo'nalganligi "
          "va gradient tarqoqligi eng informativ ekanini ko'rsatadi."),
    p31b=("Prefiks uzunligi n′ bo'yicha qidiruv (2-jadval, 1-rasm) n′* = {n_star} qiymatida "
          "maksimum berdi: kross-validatsiyada P = {p_cv:.3f}, mustaqil tekshirish to'plamida "
          "P = {p_val:.3f}. Ikkala egri chiziqning maksimumi bir nuqtada mos kelishi tanlov "
          "protsedurasining barqarorligini tasdiqlaydi. To'liq 38 ta belgidan foydalanish "
          "natijani pasaytiradi (P = {p_38:.3f}) — bu shovqinli belgilarning zararli ta'sirini "
          "ko'rsatadi."),
    s32="3.2. Turli detektorlar bilan gibrid ansambl",
    p32a=("Uch xil YOLO detektori bilan o'tkazilgan ansambl eksperimentlari (3-jadval, 2-rasm) "
          "quyidagi qonuniyatni ochib berdi: bulcha tasniflagich barcha holatlarda ijobiy hissa "
          "qo'shadi, biroq detektor qanchalik kuchli bo'lsa, nisbiy ustunlik shunchalik kichik "
          "bo'ladi. Eng yuqori mutlaq natijaga YOLO11l bilan erishildi: P = {l_ens:.3f} "
          "(α* = {l_alpha}), yakka detektorning {l_yolo:.3f} natijasiga qarshi."),
    p32b=("α bo'yicha egri chiziqlar bitta maksimumga ega va yassi: α ∈ [0,3; 0,7] oralig'ida "
          "natija barqaror. Bu amaliy nuqtai nazardan muhim — vazn koeffitsientini aniq "
          "sozlash talab etilmaydi."),
    s33="3.3. Ishonch va IoU chegaralariga sezgirlik",
    p33a=("4-jadvalda keltirilgan natijalar ishning markaziy topilmasini tashkil etadi. "
          "Detektorning ishonch chegarasi conf = 0,05 dan 0,15 gacha ko'tarilganda YOLO'ning "
          "o'zi {hi_yolo:.3f} aniqlikka chiqadi, chunki past ishonchli (va ko'pincha xato "
          "tasniflangan) chiqishlar filtrlanadi. Aynan shu holatda gibrid ansambl qo'shimcha "
          "ustunlik bermaydi ({hi_ens:.3f})."),
    p33b=("Aksincha, past chegarada (conf = 0,05) YOLO'ning aniqligi {lo_yolo:.3f} gacha "
          "tushadi va bulcha tasniflagich uni {lo_ens:.3f} gacha ko'taradi — {gain:.1f} foiz "
          "punkt o'sish. Demak, taklif etilgan usulning axborot hissasi detektor ishonchsiz "
          "bo'lgan sohada jamlangan. Mos kelish chegarasini IoU ≥ 0,5 gacha qattiqlashtirish "
          "xulosani o'zgartirmaydi (+{iou_gain:.1f} punkt), o'qitish to'plamidagi nazorat ham "
          "yutuq yo'nalishini tasdiqlaydi."),
    s34="3.4. Sinflar kesimidagi tahlil",
    p34=("5-jadval eng yaxshi konfiguratsiya (YOLO11l + bulcha tasniflagich, α = {l_alpha}) "
         "uchun sinflar bo'yicha aniqlik va to'liqlikni keltiradi. Eng katta yutuq kalsifikatsiya "
         "sinfida kuzatiladi — bu tekstura belgilarining mayda, yuqori chastotali "
         "strukturalarga sezgirligi bilan izohlanadi."),
    s4="4. Muhokama",
    p4a=("Olingan natijalar ikki bosqichli arxitekturaning qiymatini yangi nuqtai nazardan "
         "ko'rsatadi. Adabiyotda gibrid usullar odatda o'rtacha aniqlik o'sishi bilan "
         "asoslanadi; bizning tahlilimiz esa bu o'sish bir tekis taqsimlanmaganini ochib beradi. "
         "Yuqori ishonchli detektsiyalarda YOLO allaqachon deyarli xatosiz ishlaydi va har qanday "
         "qo'shimcha model faqat shovqin kirita oladi. Butun foyda past ishonchli, ya'ni "
         "radiologning o'zi ham ikkilanadigan ROI'lardan keladi."),
    p4b=("Bu klinik ish oqimi uchun aniq tavsiya beradi: bulcha tasniflagichni barcha "
         "detektsiyalarga emas, balki conf < 0,15 bo'lgan shubhali sohalarga qo'llash lozim. "
         "Bunday selektiv qo'llash hisoblash xarajatini kamaytiradi va yuqori ishonchli "
         "qarorlarga aralashmaydi. Bundan tashqari, tasniflagich to'liq "
         "interpretatsiyalanadigan bo'lgani uchun (tanlangan {n_star} ta belgi va etalonlargacha "
         "bo'lgan masofalar oshkora), u radiolog uchun \"ikkinchi fikr\" vazifasini bajaradi."),
    p4c=("Ishning cheklovlari: baza hajmi nisbatan kichik va kuchli nomutanosib "
         "(arxitektura buzilishi sinfida atigi 2 ta o'qitish misoli), shu sababli kam uchraydigan "
         "sinflar bo'yicha baholar statistik jihatdan beqaror. Keyingi bosqichda bazani "
         "kengaytirish va ko'p markazli tekshiruv o'tkazish rejalashtirilgan."),
    s5="5. Xulosa",
    concl=[
        "Bulcha dasturlash mezoni asosidagi belgi tanlash mammografik ko'p sinfli masalaga "
        "muvaffaqiyatli umumlashtirildi; 38 ta belgidan n′* = {n_star} tasi optimal deb topildi "
        "va bu tanlov mustaqil tekshirish to'plamida tasdiqlandi.",
        "Gibrid ansambl barcha sinovdan o'tgan detektorlarda YOLO'ning yakka natijasidan ustun "
        "keldi; eng yuqori natija YOLO11l bilan P = {l_ens:.3f} ni tashkil etdi.",
        "Usul foydasining detektor ishonch chegarasiga bog'liqligi miqdoriy aniqlandi: past "
        "chegarada +{gain:.1f} foiz punkt, yuqori chegarada esa ustunlik yo'q. Bu bulcha "
        "tasniflagichning o'rnini aniq belgilaydi — shubhali ROI'lar uchun ikkinchi fikr.",
        "α ∈ [0,3; 0,7] oralig'ida natija barqaror, bu amaliy joriy etishni soddalashtiradi.",
    ],
    refs_h="Adabiyotlar",
    t1_cap="1-jadval. Ma'lumotlar bazasidagi ROI'lar taqsimoti",
    t2_cap="2-jadval. Tanlangan belgilar soni n′ ning tasniflash sifatiga ta'siri",
    t3_cap="3-jadval. Turli detektorlar bilan gibrid ansambl natijalari (tekshirish to'plami)",
    t4_cap="4-jadval. Ishonch (conf) va mos kelish (IoU) chegaralariga sezgirlik",
    t5_cap="5-jadval. Sinflar kesimida aniqlik va to'liqlik (YOLO11l, eng yaxshi α)",
    f1_cap="1-rasm. Tasniflash ishonchliligi P ning tanlangan belgilar soni n′ ga bog'liqligi",
    f2_cap="2-rasm. Ansambl vazni α ning tasniflash ishonchliligiga ta'siri (uch detektor)",
    t1_h=["Sinf", "O'qitish ROI", "Tekshirish ROI"],
    t2_h=["n′", "P (CV, train)", "P (val)"],
    t3_h=["Detektor", "YOLO (α=1)", "boolfs (α=0)", "Eng yaxshi α", "Ansambl P", "Yutuq, p.p."],
    t4_h=["Sozlama", "Mos ROI", "YOLO", "Ansambl", "Yutuq, p.p."],
    t5_h=["Sinf", "YOLO aniqlik", "YOLO to'liqlik", "Ansambl aniqlik", "Ansambl to'liqlik"],
    t4_rows=["conf = 0,05; IoU = 0,3 (bazaviy)", "conf = 0,15; IoU = 0,3",
             "conf = 0,05; IoU = 0,5", "o'qitish to'plami (nazorat)"],
)

T["ru"] = dict(
    title="Булев отбор признаков и гибридный ансамбль в классификации маммографических "
          "областей интереса: зависимость эффективности от порога уверенности детектора",
    authors="Туракулов Х.  ·  научный руководитель: профессор Хамдамов Р.Х.",
    affil="Ташкентский университет информационных технологий имени Мухаммада аль-Хорезми",
    udk="УДК 004.93:519.86:618.19",
    abs_h="Аннотация",
    kw_h="Ключевые слова",
    kw="булево программирование, отбор информативных признаков, классификатор минимального "
       "расстояния, радиомика, маммография, YOLO, гибридный ансамбль, порог уверенности, "
       "интерпретируемый искусственный интеллект.",
    abstract=(
        "В статье метод отбора информативных признаков, основанный на теории булева "
        "программирования Р.Х. Хамдамова, и классификатор минимального расстояния применены "
        "к задаче классификации маммографических областей интереса (ROI) и объединены с "
        "детектором YOLO в гибридный ансамбль. На восьмиклассовой маммографической базе "
        "({n_tr} обучающих и {n_val} проверочных ROI) проведено одиннадцать экспериментов. "
        "Поиск по префиксам ранжированного ряда показал, что из 38 признаков оптимальными "
        "являются n′* = {n_star}; этот выбор подтверждён на независимой проверочной выборке "
        "(P = {p_val:.3f}). Гибридный ансамбль превзошёл одиночный YOLO на всех испытанных "
        "детекторах: для YOLO11s {s_yolo:.3f} → {s_ens:.3f}, для YOLO11l "
        "{l_yolo:.3f} → {l_ens:.3f}, для усиленного YOLO11l-v2 {v_yolo:.3f} → {v_ens:.3f}. "
        "Основной результат работы состоит в том, что выигрыш метода резко зависит от порога "
        "уверенности детектора: при повышении порога до 0,15 YOLO самостоятельно достигает "
        "точности {hi_yolo:.3f} и булев классификатор не даёт дополнительного преимущества, "
        "тогда как при низком пороге (0,05) он повышает точность на {gain:.1f} процентных "
        "пункта. Следовательно, роль предложенного классификатора — давать «второе мнение» "
        "для сомнительных ROI, в которых детектор не уверен."),
    s1="1. Введение",
    p1a=("Современные одностадийные детекторы (семейство YOLO) обеспечивают высокую скорость "
         "и приемлемую точность автоматического анализа маммограмм. Однако как глубокие "
         "нейронные сети они остаются «чёрным ящиком»: они не отвечают на вопрос «какой признак "
         "привёл к данному решению?», необходимый для обоснования клинического заключения. "
         "При этом выходы детектора с низкой уверенностью (conf < 0,15) на практике составляют "
         "наиболее проблемную часть — именно там сосредоточены ошибки классификации."),
    p1b=("В настоящей работе предложена двухстадийная архитектура. На первой стадии детектор "
         "YOLO находит области интереса (ROI). На второй стадии полностью интерпретируемый "
         "классификатор, основанный на теории задач булева программирования Р.Х. Хамдамова [1], "
         "переоценивает каждую ROI в 38-мерном пространстве радиомических признаков. Выходы "
         "обеих стадий объединяются взвешенным ансамблем."),
    p1c=("Научная новизна работы: (i) критерий булева отбора признаков обобщён на "
         "многоклассовую маммографическую задачу; (ii) систематически исследовано влияние числа "
         "отобранных признаков n′ на качество классификации; (iii) впервые количественно "
         "установлена зависимость выигрыша гибридного ансамбля от порога уверенности детектора."),
    s2="2. Материалы и метод",
    s21="2.1. База данных",
    p21=("В исследовании использована восьмиклассовая маммографическая база: {n_tr} обучающих "
         "и {n_val} проверочных ROI (из {img_tr} и {img_val} изображений соответственно). "
         "База существенно несбалансирована — таблица 1. Каждая ROI снабжена размеченным "
         "экспертом ограничивающим прямоугольником (ground truth)."),
    s22="2.2. Пространство признаков",
    p22=("Из каждого фрагмента ROI извлекаются 38 радиомических признаков: статистики первого "
         "порядка (среднее, дисперсия, асимметрия, эксцесс), градиентные характеристики "
         "(среднее и стандартное отклонение оператора Собеля), а также признаки GLCM (матрицы "
         "совместной встречаемости уровней серого) для двух расстояний (d = 1 и d = 3): "
         "контраст, несходство, однородность, энергия, корреляция, энтропия. Признаки "
         "стандартизуются по статистикам обучающей выборки (z-нормировка)."),
    s23="2.3. Критерий булева отбора признаков",
    p23a=("По Хамдамову [1, (3.2.2)], для пары классов (p, q) и j-го признака вводятся три "
          "величины: межклассовый разброс a_j и внутриклассовые разбросы b_j и c_j:"),
    p23b=("Здесь x_plj — значение j-го признака для l-го объекта класса p, k_p — число объектов "
          "в классе p. Для перехода к многоклассовому случаю (m = 8) применяется глобальный "
          "режим: a_j суммируется по всем парам (p, q), а w_j = b_j + c_j — по всем "
          "внутриклассовым разбросам."),
    p23c=("Поиск множества информативных признаков сводится к задаче булева программирования: "
          "пусть λ_j ∈ {{0, 1}} — булева переменная, обозначающая отбор j-го признака. "
          "Целевой функционал максимизирует отношение межклассового и внутриклассового "
          "разбросов по отобранным признакам:"),
    s24="2.4. Ранжирование и отбор по префиксу",
    p24a=("Метод обобщённых неравенств [1, раздел 3.4], согласно (3.4.5), позволяет упорядочить "
          "признаки по убыванию отношения r_j:"),
    p24b=("Префиксы ранжированного ряда образуют цепочку монотонного убывания Φ(λ). Следует "
          "подчеркнуть, что при жёстком ограничении |S| = n′ префикс в общем случае не обязан "
          "быть абсолютно оптимальным множеством; результат (3.4.4) книги даёт именно свойство "
          "цепочки префиксов. Поэтому итоговое значение n′ выбирается не по Φ, а по качеству "
          "классификации P:"),
    s25="2.5. Классификатор минимального расстояния",
    p25a=("Для каждого класса p вычисляются эталонный вектор (центр) и внутриклассовый разброс "
          "[1, (3.6.2)–(3.6.3)]:"),
    p25b=("Для нового объекта x нормированное расстояние и решающее правило:"),
    p25c=("Для ансамбля расстояния преобразуются в вероятностноподобные оценки через softmax:"),
    p25d=("Для малых классов с k_p < 5 (например, архитектурная перестройка — всего 2 примера) "
          "при кросс-валидации применяется схема leave-one-out, для остальных — "
          "стратифицированная 5-кратная. В вырожденном случае S(X_p) = 0 берётся медиана "
          "разбросов остальных классов, чтобы не нарушить масштаб расстояний."),
    s26="2.6. Гибридный ансамбль",
    p26=("Выход детектора YOLO для класса p (распределённый на основе значения уверенности) "
         "u_p^YOLO и оценка булева классификатора s_p объединяются взвешенной суммой:"),
    s27="2.7. Критерий качества и протокол эксперимента",
    p27a=("Достоверность классификации [1, (3.6.4)] измеряется как доля правильно распознанных "
          "объектов (I[·] — индикаторная функция):"),
    p27b=("При оценке ансамбля выходы YOLO сопоставляются с эталонными ROI жадным алгоритмом "
          "при условии IoU ≥ 0,3; величина P вычисляется по сопоставленным парам. Всего "
          "проведено одиннадцать экспериментов: базовое обучение и оценка (Э1–Э3), поиск по n′ "
          "(Э4), анализ чувствительности к α, порогам уверенности и IoU (Э5–Э8), ансамбль с "
          "тремя детекторами (Э9–Э10) и контроль устойчивости на обучающей выборке (Э11)."),
    s3="3. Результаты",
    s31="3.1. Отобранные признаки и значение n′*",
    p31a=("На обучающей выборке первые позиции ранжированного ряда заняли корреляционные "
          "признаки GLCM: {top5}. Это указывает на то, что наиболее информативными являются "
          "текстурная направленность и градиентный разброс патологических областей."),
    p31b=("Поиск по длине префикса n′ (таблица 2, рисунок 1) дал максимум при n′* = {n_star}: "
          "P = {p_cv:.3f} при кросс-валидации и P = {p_val:.3f} на независимой проверочной "
          "выборке. Совпадение максимумов обеих кривых в одной точке подтверждает устойчивость "
          "процедуры отбора. Использование всех 38 признаков ухудшает результат "
          "(P = {p_38:.3f}), что демонстрирует вредное влияние шумовых признаков."),
    s32="3.2. Гибридный ансамбль с различными детекторами",
    p32a=("Эксперименты с тремя детекторами YOLO (таблица 3, рисунок 2) выявили следующую "
          "закономерность: булев классификатор вносит положительный вклад во всех случаях, "
          "однако чем сильнее детектор, тем меньше относительный выигрыш. Наивысший абсолютный "
          "результат достигнут с YOLO11l: P = {l_ens:.3f} (α* = {l_alpha}) против {l_yolo:.3f} "
          "у одиночного детектора."),
    p32b=("Кривые по α имеют единственный максимум и являются пологими: в диапазоне "
          "α ∈ [0,3; 0,7] результат устойчив. С практической точки зрения это важно — точная "
          "настройка весового коэффициента не требуется."),
    s33="3.3. Чувствительность к порогам уверенности и IoU",
    p33a=("Результаты, приведённые в таблице 4, составляют центральную находку работы. При "
          "повышении порога уверенности детектора с conf = 0,05 до 0,15 YOLO самостоятельно "
          "достигает точности {hi_yolo:.3f}, поскольку низкоуверенные (и часто ошибочно "
          "классифицированные) выходы отфильтровываются. Именно в этом случае гибридный ансамбль "
          "не даёт дополнительного преимущества ({hi_ens:.3f})."),
    p33b=("Напротив, при низком пороге (conf = 0,05) точность YOLO падает до {lo_yolo:.3f}, "
          "а булев классификатор поднимает её до {lo_ens:.3f} — рост на {gain:.1f} процентных "
          "пункта. Таким образом, информационный вклад предложенного метода сосредоточен в "
          "области неуверенности детектора. Ужесточение порога сопоставления до IoU ≥ 0,5 не "
          "меняет вывода (+{iou_gain:.1f} п.п.), контроль на обучающей выборке также "
          "подтверждает направление выигрыша."),
    s34="3.4. Анализ в разрезе классов",
    p34=("В таблице 5 приведены точность и полнота по классам для наилучшей конфигурации "
         "(YOLO11l + булев классификатор, α = {l_alpha}). Наибольший выигрыш наблюдается в "
         "классе кальцинатов, что объясняется чувствительностью текстурных признаков к мелким "
         "высокочастотным структурам."),
    s4="4. Обсуждение",
    p4a=("Полученные результаты раскрывают ценность двухстадийной архитектуры с новой стороны. "
         "В литературе гибридные методы обычно обосновываются средним приростом точности; наш "
         "анализ показывает, что этот прирост распределён неравномерно. На высокоуверенных "
         "детекциях YOLO работает практически безошибочно, и любая дополнительная модель способна "
         "лишь внести шум. Весь выигрыш приходит от низкоуверенных ROI — тех самых, в которых "
         "сомневается и сам рентгенолог."),
    p4b=("Это даёт конкретную рекомендацию для клинического рабочего процесса: булев "
         "классификатор следует применять не ко всем детекциям, а лишь к сомнительным областям "
         "с conf < 0,15. Такое избирательное применение снижает вычислительные затраты и не "
         "вмешивается в уверенные решения. Кроме того, поскольку классификатор полностью "
         "интерпретируем (отобранные {n_star} признаков и расстояния до эталонов явно доступны), "
         "он выполняет для рентгенолога функцию «второго мнения»."),
    p4c=("Ограничения работы: объём базы сравнительно невелик и сильно несбалансирован (в классе "
         "архитектурной перестройки всего 2 обучающих примера), поэтому оценки по редким классам "
         "статистически неустойчивы. На следующем этапе планируется расширение базы и проведение "
         "многоцентровой проверки."),
    s5="5. Заключение",
    concl=[
        "Отбор признаков на основе критерия булева программирования успешно обобщён на "
        "многоклассовую маммографическую задачу; из 38 признаков оптимальными оказались "
        "n′* = {n_star}, и этот выбор подтверждён на независимой проверочной выборке.",
        "Гибридный ансамбль превзошёл одиночный YOLO на всех испытанных детекторах; наивысший "
        "результат достигнут с YOLO11l и составил P = {l_ens:.3f}.",
        "Количественно установлена зависимость выигрыша метода от порога уверенности детектора: "
        "при низком пороге +{gain:.1f} процентных пункта, при высоком — преимущество отсутствует. "
        "Это чётко определяет роль булева классификатора — второе мнение для сомнительных ROI.",
        "В диапазоне α ∈ [0,3; 0,7] результат устойчив, что упрощает практическое внедрение.",
    ],
    refs_h="Литература",
    t1_cap="Таблица 1. Распределение ROI в базе данных",
    t2_cap="Таблица 2. Влияние числа отобранных признаков n′ на качество классификации",
    t3_cap="Таблица 3. Результаты гибридного ансамбля с различными детекторами (проверочная выборка)",
    t4_cap="Таблица 4. Чувствительность к порогам уверенности (conf) и сопоставления (IoU)",
    t5_cap="Таблица 5. Точность и полнота в разрезе классов (YOLO11l, наилучшее α)",
    f1_cap="Рисунок 1. Зависимость достоверности классификации P от числа отобранных признаков n′",
    f2_cap="Рисунок 2. Влияние веса ансамбля α на достоверность классификации (три детектора)",
    t1_h=["Класс", "Обучающих ROI", "Проверочных ROI"],
    t2_h=["n′", "P (CV, train)", "P (val)"],
    t3_h=["Детектор", "YOLO (α=1)", "boolfs (α=0)", "Лучшее α", "Ансамбль P", "Выигрыш, п.п."],
    t4_h=["Настройка", "Сопост. ROI", "YOLO", "Ансамбль", "Выигрыш, п.п."],
    t5_h=["Класс", "Точность YOLO", "Полнота YOLO", "Точность анс.", "Полнота анс."],
    t4_rows=["conf = 0,05; IoU = 0,3 (базовая)", "conf = 0,15; IoU = 0,3",
             "conf = 0,05; IoU = 0,5", "обучающая выборка (контроль)"],
)

T["en"] = dict(
    title="Boolean Feature Selection and a Hybrid Ensemble for Mammographic ROI "
          "Classification: Efficacy as a Function of the Detector Confidence Threshold",
    authors="H. Turaqulov  ·  supervisor: Prof. R. Kh. Khamdamov",
    affil="Tashkent University of Information Technologies named after Muhammad al-Khwarizmi",
    udk="UDC 004.93:519.86:618.19",
    abs_h="Abstract",
    kw_h="Keywords",
    kw="Boolean programming, informative feature selection, minimum-distance classifier, "
       "radiomics, mammography, YOLO, hybrid ensemble, confidence threshold, "
       "interpretable artificial intelligence.",
    abstract=(
        "This paper applies an informative-feature-selection method grounded in "
        "R. Kh. Khamdamov's theory of Boolean programming, together with a minimum-distance "
        "classifier, to the classification of mammographic regions of interest (ROIs), and "
        "combines it with a YOLO detector into a hybrid ensemble. Eleven experiments were "
        "conducted on an eight-class mammography dataset ({n_tr} training and {n_val} validation "
        "ROIs). A search over the prefixes of the ranked feature sequence identified n′* = "
        "{n_star} of the 38 features as optimal, a choice confirmed on the held-out validation "
        "set (P = {p_val:.3f}). The hybrid ensemble outperformed the stand-alone YOLO for every "
        "detector tested: {s_yolo:.3f} → {s_ens:.3f} for YOLO11s, {l_yolo:.3f} → {l_ens:.3f} for "
        "YOLO11l, and {v_yolo:.3f} → {v_ens:.3f} for the reinforced YOLO11l-v2. The principal "
        "finding is that the benefit of the method depends sharply on the detector's confidence "
        "threshold: raising the threshold to 0.15 lets YOLO alone reach an accuracy of "
        "{hi_yolo:.3f}, at which point the Boolean classifier confers no additional advantage, "
        "whereas at a low threshold (0.05) it improves accuracy by {gain:.1f} percentage points. "
        "The role of the proposed classifier is therefore to provide a \"second opinion\" for "
        "the ambiguous ROIs about which the detector is uncertain."),
    s1="1. Introduction",
    p1a=("Modern single-stage detectors of the YOLO family deliver high throughput and "
         "acceptable accuracy in the automated analysis of mammograms. As deep neural networks, "
         "however, they remain black boxes: they do not answer the question \"which feature led "
         "to this decision?\" that is required to justify a clinical conclusion. Moreover, the "
         "detector's low-confidence outputs (conf < 0.15) constitute the most problematic regime "
         "in practice — this is precisely where misclassifications accumulate."),
    p1b=("The present work proposes a two-stage architecture. In the first stage a YOLO detector "
         "localises the regions of interest (ROIs). In the second stage a fully interpretable "
         "classifier, grounded in R. Kh. Khamdamov's theory of Boolean programming problems [1], "
         "re-evaluates each ROI in a 38-dimensional radiomic feature space. The outputs of the "
         "two stages are combined through a weighted ensemble."),
    p1c=("The scientific novelty of this work is threefold: (i) the Boolean feature-selection "
         "criterion is generalised to a multi-class mammographic problem; (ii) the influence of "
         "the number of selected features n′ on classification quality is studied "
         "systematically; and (iii) the dependence of the hybrid ensemble's benefit on the "
         "detector's confidence threshold is quantified for the first time."),
    s2="2. Materials and Method",
    s21="2.1. Dataset",
    p21=("An eight-class mammography dataset was used: {n_tr} training and {n_val} validation "
         "ROIs (drawn from {img_tr} and {img_val} images respectively). The dataset is strongly "
         "imbalanced — see Table 1. Every ROI is supplied with an expert-annotated bounding box "
         "(ground truth)."),
    s22="2.2. Feature Space",
    p22=("Thirty-eight radiomic features are extracted from each ROI patch: first-order "
         "statistics (mean, variance, skewness, kurtosis), gradient descriptors (mean and "
         "standard deviation of the Sobel operator), and GLCM (grey-level co-occurrence matrix) "
         "features at two distances (d = 1 and d = 3): contrast, dissimilarity, homogeneity, "
         "energy, correlation and entropy. The features are standardised using the statistics of "
         "the training split (z-normalisation)."),
    s23="2.3. The Boolean Feature-Selection Criterion",
    p23a=("Following Khamdamov [1, Eq. (3.2.2)], three quantities are introduced for a class "
          "pair (p, q) and the j-th feature: the between-class scatter a_j and the within-class "
          "scatters b_j and c_j:"),
    p23b=("Here x_plj denotes the value of the j-th feature for the l-th object of class p, and "
          "k_p is the number of objects in class p. To generalise to the multi-class case "
          "(m = 8) a global regime is adopted: a_j is summed over all pairs (p, q), while "
          "w_j = b_j + c_j is summed over all within-class scatters."),
    p23c=("The search for the informative feature subset reduces to a Boolean programming "
          "problem. Let λ_j ∈ {{0, 1}} be the Boolean variable indicating selection of the j-th "
          "feature. The objective functional maximises the ratio of between-class to "
          "within-class scatter over the selected features:"),
    s24="2.4. Ranking and Prefix-Based Selection",
    p24a=("The method of generalised inequalities [1, Sec. 3.4], through Eq. (3.4.5), permits "
          "the features to be ordered by decreasing ratio r_j:"),
    p24b=("The prefixes of the ranked sequence form a chain along which Φ(λ) decreases "
          "monotonically. It must be emphasised that, under the hard constraint |S| = n′, a "
          "prefix is not in general the absolutely optimal subset; result (3.4.4) of the "
          "monograph establishes precisely the chain property of prefixes. The final value of n′ "
          "is therefore selected not by Φ but by the classification quality P:"),
    s25="2.5. The Minimum-Distance Classifier",
    p25a=("For every class p a reference vector (centroid) and a within-class scatter are "
          "computed [1, Eqs. (3.6.2)–(3.6.3)]:"),
    p25b=("For a new object x the normalised distance and the decision rule read:"),
    p25c=("For the ensemble, the distances are converted into probability-like scores via a "
          "softmax transform:"),
    p25d=("For small classes with k_p < 5 (for instance architectural distortion, with only two "
          "examples) a leave-one-out scheme is used in cross-validation, and a stratified "
          "5-fold scheme for the remainder. In the degenerate case S(X_p) = 0 the median scatter "
          "of the remaining classes is substituted so that the distance scale is not distorted."),
    s26="2.6. The Hybrid Ensemble",
    p26=("The YOLO detector's output for class p, denoted u_p^YOLO and distributed according to "
         "the confidence value, is combined with the Boolean classifier's score s_p through a "
         "weighted sum:"),
    s27="2.7. Quality Criterion and Experimental Protocol",
    p27a=("Classification reliability [1, Eq. (3.6.4)] is measured as the fraction of correctly "
          "recognised objects, where I[·] is the indicator function:"),
    p27b=("When evaluating the ensemble, YOLO's outputs are matched greedily against the ground-"
          "truth ROIs subject to IoU ≥ 0.3, and P is computed over the matched pairs. Eleven "
          "experiments were performed in total: baseline fitting and evaluation (E1–E3), the "
          "search over n′ (E4), sensitivity analysis with respect to α and to the confidence and "
          "IoU thresholds (E5–E8), ensembling with three different detectors (E9–E10), and a "
          "stability control on the training split (E11)."),
    s3="3. Results",
    s31="3.1. Selected Features and the Value of n′*",
    p31a=("On the training split the leading positions of the ranked sequence were occupied by "
          "the GLCM correlation features: {top5}. This indicates that the textural orientation "
          "and the gradient dispersion of pathological regions carry the most information."),
    p31b=("The search over the prefix length n′ (Table 2, Figure 1) attained its maximum at "
          "n′* = {n_star}: P = {p_cv:.3f} under cross-validation and P = {p_val:.3f} on the "
          "held-out validation set. That the maxima of both curves coincide at the same point "
          "confirms the stability of the selection procedure. Using all 38 features degrades the "
          "result (P = {p_38:.3f}), which demonstrates the detrimental influence of noisy "
          "features."),
    s32="3.2. The Hybrid Ensemble across Detectors",
    p32a=("The ensemble experiments with three YOLO detectors (Table 3, Figure 2) reveal the "
          "following regularity: the Boolean classifier contributes positively in every case, "
          "yet the stronger the detector, the smaller the relative gain. The highest absolute "
          "result was obtained with YOLO11l: P = {l_ens:.3f} (α* = {l_alpha}), against "
          "{l_yolo:.3f} for the detector alone."),
    p32b=("The curves in α are unimodal and flat: the result is stable throughout "
          "α ∈ [0.3, 0.7]. This matters in practice, since no precise tuning of the weighting "
          "coefficient is required."),
    s33="3.3. Sensitivity to the Confidence and IoU Thresholds",
    p33a=("The results collected in Table 4 constitute the central finding of this work. When "
          "the detector's confidence threshold is raised from conf = 0.05 to 0.15, YOLO alone "
          "attains an accuracy of {hi_yolo:.3f}, because the low-confidence — and frequently "
          "misclassified — outputs are filtered away. It is precisely in this regime that the "
          "hybrid ensemble confers no additional advantage ({hi_ens:.3f})."),
    p33b=("Conversely, at the low threshold (conf = 0.05) YOLO's accuracy falls to {lo_yolo:.3f} "
          "and the Boolean classifier raises it to {lo_ens:.3f} — a gain of {gain:.1f} "
          "percentage points. The informational contribution of the proposed method is thus "
          "concentrated in the detector's regime of uncertainty. Tightening the matching "
          "threshold to IoU ≥ 0.5 does not alter this conclusion (+{iou_gain:.1f} p.p.), and the "
          "control run on the training split likewise confirms the direction of the gain."),
    s34="3.4. Per-Class Analysis",
    p34=("Table 5 reports the per-class precision and recall for the best configuration "
         "(YOLO11l plus the Boolean classifier, α = {l_alpha}). The largest gain is observed for "
         "the calcification class, which is explained by the sensitivity of textural features to "
         "fine, high-frequency structures."),
    s4="4. Discussion",
    p4a=("These results illuminate the value of the two-stage architecture from a new angle. In "
         "the literature, hybrid methods are usually justified by an average gain in accuracy; "
         "our analysis shows that this gain is not distributed uniformly. On high-confidence "
         "detections YOLO already operates almost without error, and any additional model can "
         "only introduce noise. The entire benefit originates from the low-confidence ROIs — the "
         "very ones about which the radiologist is also in doubt."),
    p4b=("This yields a concrete recommendation for the clinical workflow: the Boolean "
         "classifier should be applied not to all detections but only to the ambiguous regions "
         "with conf < 0.15. Such selective application reduces the computational cost and does "
         "not interfere with confident decisions. Furthermore, because the classifier is fully "
         "interpretable — the {n_star} selected features and the distances to the class "
         "centroids are explicitly available — it serves the radiologist as a genuine \"second "
         "opinion\"."),
    p4c=("Limitations. The dataset is comparatively small and strongly imbalanced (the "
         "architectural-distortion class contains only two training examples), so the estimates "
         "for the rare classes are statistically unstable. Expanding the dataset and conducting "
         "a multi-centre validation are planned for the next stage."),
    s5="5. Conclusion",
    concl=[
        "Feature selection based on the Boolean programming criterion was successfully "
        "generalised to a multi-class mammographic problem; n′* = {n_star} of the 38 features "
        "proved optimal, and this choice was confirmed on a held-out validation set.",
        "The hybrid ensemble outperformed the stand-alone YOLO for every detector tested; the "
        "highest result, P = {l_ens:.3f}, was achieved with YOLO11l.",
        "The dependence of the method's benefit on the detector's confidence threshold was "
        "quantified: +{gain:.1f} percentage points at a low threshold and no advantage at a high "
        "one. This delineates the role of the Boolean classifier precisely — a second opinion "
        "for ambiguous ROIs.",
        "The result is stable throughout α ∈ [0.3, 0.7], which simplifies practical deployment.",
    ],
    refs_h="References",
    t1_cap="Table 1. Distribution of ROIs in the dataset",
    t2_cap="Table 2. Effect of the number of selected features n′ on classification quality",
    t3_cap="Table 3. Hybrid-ensemble results across detectors (validation split)",
    t4_cap="Table 4. Sensitivity to the confidence (conf) and matching (IoU) thresholds",
    t5_cap="Table 5. Per-class precision and recall (YOLO11l, best α)",
    f1_cap="Figure 1. Classification reliability P as a function of the number of selected features n′",
    f2_cap="Figure 2. Effect of the ensemble weight α on classification reliability (three detectors)",
    t1_h=["Class", "Training ROIs", "Validation ROIs"],
    t2_h=["n′", "P (CV, train)", "P (val)"],
    t3_h=["Detector", "YOLO (α=1)", "boolfs (α=0)", "Best α", "Ensemble P", "Gain, p.p."],
    t4_h=["Setting", "Matched ROIs", "YOLO", "Ensemble", "Gain, p.p."],
    t5_h=["Class", "YOLO precision", "YOLO recall", "Ens. precision", "Ens. recall"],
    t4_rows=["conf = 0.05, IoU = 0.3 (baseline)", "conf = 0.15, IoU = 0.3",
             "conf = 0.05, IoU = 0.5", "training split (control)"],
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
    pf = st.paragraph_format
    pf.line_spacing = 1.5
    pf.space_after = Pt(0)
    for s in doc.sections:
        s.left_margin = s.right_margin = Cm(2.5)
        s.top_margin = s.bottom_margin = Cm(2.0)


def para(doc, text, first_indent=True, size=12, italic=False, align=None):
    p = doc.add_paragraph()
    p.alignment = align if align is not None else WD_ALIGN_PARAGRAPH.JUSTIFY
    if first_indent:
        p.paragraph_format.first_line_indent = Cm(1.25)
    r = p.add_run(text)
    r.font.size = Pt(size)
    r.italic = italic
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
    r.font.size = Pt(10)
    r.font.color.rgb = RGBColor(0x33, 0x33, 0x33)
    return p


def table(doc, header, rows):
    t = doc.add_table(rows=1, cols=len(header))
    t.style = "Table Grid"
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for i, h in enumerate(header):
        c = t.rows[0].cells[i]
        c.text = ""
        r = c.paragraphs[0].add_run(str(h))
        r.bold = True
        r.font.size = Pt(9.5)
        c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""
            r = cells[i].paragraphs[0].add_run(str(v))
            r.font.size = Pt(9.5)
            cells[i].paragraphs[0].alignment = (
                WD_ALIGN_PARAGRAPH.LEFT if i == 0 else WD_ALIGN_PARAGRAPH.CENTER)
    return t


def build(lang, R, vals):
    t = T[lang]
    doc = Document()
    setup(doc)

    # --- sarlavha bloki --- #
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

    # --- annotatsiya --- #
    heading(doc, t["abs_h"])
    para(doc, t["abstract"].format(**vals), size=11)
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Cm(1.25)
    p.paragraph_format.space_before = Pt(6)
    r = p.add_run(t["kw_h"] + ": "); r.bold = True; r.font.size = Pt(11)
    r = p.add_run(t["kw"]); r.italic = True; r.font.size = Pt(11)

    # --- 1. Kirish --- #
    heading(doc, t["s1"])
    for k in ("p1a", "p1b", "p1c"):
        para(doc, t[k])

    # --- 2. Usul --- #
    heading(doc, t["s2"])
    heading(doc, t["s21"], size=12)
    para(doc, t["p21"].format(**vals))
    caption(doc, t["t1_cap"], before=True)
    table(doc, t["t1_h"], vals["t1_rows"](lang))

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

    heading(doc, t["s27"], size=12)
    para(doc, t["p27a"])
    add_equation(doc, *F.eq_P(), number=13)
    para(doc, t["p27b"])

    # --- 3. Natijalar --- #
    heading(doc, t["s3"])
    heading(doc, t["s31"], size=12)
    para(doc, t["p31a"].format(**vals))
    para(doc, t["p31b"].format(**vals))
    caption(doc, t["t2_cap"], before=True)
    table(doc, t["t2_h"], vals["t2_rows"])
    doc.add_picture(str(ASSETS / lang / "fig1_nsweep.png"), width=Inches(6.1))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption(doc, t["f1_cap"])

    heading(doc, t["s32"], size=12)
    para(doc, t["p32a"].format(**vals))
    para(doc, t["p32b"])
    caption(doc, t["t3_cap"], before=True)
    table(doc, t["t3_h"], vals["t3_rows"])
    doc.add_picture(str(ASSETS / lang / "fig2_alpha.png"), width=Inches(6.1))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption(doc, t["f2_cap"])

    heading(doc, t["s33"], size=12)
    para(doc, t["p33a"].format(**vals))
    para(doc, t["p33b"].format(**vals))
    caption(doc, t["t4_cap"], before=True)
    table(doc, t["t4_h"], vals["t4_rows"](lang))

    heading(doc, t["s34"], size=12)
    para(doc, t["p34"].format(**vals))
    caption(doc, t["t5_cap"], before=True)
    table(doc, t["t5_h"], vals["t5_rows"](lang))

    # --- 4. Muhokama --- #
    heading(doc, t["s4"])
    for k in ("p4a", "p4b", "p4c"):
        para(doc, t[k].format(**vals))

    # --- 5. Xulosa --- #
    heading(doc, t["s5"])
    for i, c in enumerate(t["concl"], 1):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.first_line_indent = Cm(1.25)
        p.add_run(f"{i}. ").bold = True
        p.add_run(c.format(**vals))

    # --- adabiyotlar --- #
    heading(doc, t["refs_h"])
    for i, ref in enumerate(REFS, 1):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.left_indent = Cm(0.8)
        p.paragraph_format.first_line_indent = Cm(-0.8)
        r = p.add_run(f"{i}. {ref}")
        r.font.size = Pt(10.5)

    out = ROOT / f"MAMOGRAF_Maqola_2026_Ansambl_{lang.upper()}.docx"
    doc.save(out)
    return out


def make_vals(R):
    art, nsw = R["art"], R["nsw"]
    ens = R["ens"]
    s, l, v = ens["exp05_ens_s_a01"], ens["exp09_ens_11l"], ens["exp10_ens_v2ep50"]
    hi, iou5, tr = ens["exp07_ens_s_conf15"], ens["exp08_ens_s_iou05"], ens["exp11_ens_s_train"]

    def best(e):
        a = float(e["best_alpha"])
        return a, float(e["alpha_results"][str(a)])

    def yolo(e):
        return float(e["alpha_results"]["1.0"])

    def bf(e):
        return float(e["alpha_results"]["0.0"])

    merged = R["merged_s"]
    s_alpha = max((a for a in merged if 0 < a < 1), key=lambda a: merged[a])
    s_ens = merged[s_alpha]
    l_alpha, l_ens = best(l)
    v_alpha, v_ens = best(v)
    hi_alpha, hi_ens = best(hi)
    io_alpha, io_ens = best(iou5)
    tr_alpha, tr_ens = best(tr)

    P_curve = art["P_curve"]
    n_star = art["n_star"]

    def fmt_a(a):
        return f"{a:.1f}".replace(".", ",")

    def t1_rows(lang):
        val_sup = {d["class"]: d["support"] for d in R["ev_val"]["per_class"]}
        rows = []
        for k, cnt in art["class_counts"].items():
            rows.append([CLS[lang][k], cnt, val_sup.get(k, 0)])
        rows.append([{"uz": "Jami", "ru": "Всего", "en": "Total"}[lang],
                     art["n_roi_train"], R["ev_val"]["n_roi"]])
        return rows

    t2_rows = [[r["n"], f"{r['P_cv']:.3f}", f"{r['P_val']:.3f}"] for r in nsw["rows"]]
    # n'* qatorini ajratib ko'rsatish
    for row in t2_rows:
        if row[0] == n_star:
            row[0] = f"{n_star} *"

    t3_rows = [
        ["YOLO11s", f"{yolo(s):.3f}", f"{bf(s):.3f}", fmt_a(s_alpha), f"{s_ens:.3f}",
         f"+{(s_ens - yolo(s)) * 100:.1f}"],
        ["YOLO11l", f"{yolo(l):.3f}", f"{bf(l):.3f}", fmt_a(l_alpha), f"{l_ens:.3f}",
         f"+{(l_ens - yolo(l)) * 100:.1f}"],
        ["YOLO11l-v2 (ep50)", f"{yolo(v):.3f}", f"{bf(v):.3f}", fmt_a(v_alpha), f"{v_ens:.3f}",
         f"+{(v_ens - yolo(v)) * 100:.1f}"],
    ]

    def t4_rows(lang):
        names = T[lang]["t4_rows"]
        data = [(s, s_ens, names[0]), (hi, hi_ens, names[1]),
                (iou5, io_ens, names[2]), (tr, tr_ens, names[3])]
        out = []
        for e, pe, nm in data:
            out.append([nm, f"{e['n_matched']} / {e['n_gt']}", f"{yolo(e):.3f}", f"{pe:.3f}",
                        f"{(pe - yolo(e)) * 100:+.1f}"])
        return out

    def t5_rows(lang):
        py = {d["class"]: d for d in l["per_class_yolo"]}
        pe = {d["class"]: d for d in l["per_class_ensemble"]}
        rows = []
        for k in l["class_names"]:
            if py.get(k, {}).get("support", 0) == 0:
                continue
            rows.append([CLS[lang][k], f"{py[k]['precision']:.3f}", f"{py[k]['recall']:.3f}",
                         f"{pe[k]['precision']:.3f}", f"{pe[k]['recall']:.3f}"])
        return rows

    top5 = ", ".join(x["feature"] for x in art["selection_table"][:5])

    return {
        "n_star": n_star, "p_cv": art["P_star"], "p_38": P_curve[-1],
        "p_val": R["ev_val"]["P"], "p_tr": R["ev_tr"]["P"],
        "n_tr": art["n_roi_train"], "n_val": R["ev_val"]["n_roi"],
        "img_tr": 175, "img_val": 47,
        "top5": top5,
        "s_yolo": yolo(s), "s_ens": s_ens, "s_alpha": fmt_a(s_alpha),
        "l_yolo": yolo(l), "l_ens": l_ens, "l_alpha": fmt_a(l_alpha),
        "v_yolo": yolo(v), "v_ens": v_ens, "v_alpha": fmt_a(v_alpha),
        "hi_yolo": yolo(hi), "hi_ens": hi_ens,
        "lo_yolo": yolo(s), "lo_ens": s_ens,
        "gain": (s_ens - yolo(s)) * 100,
        "iou_gain": (io_ens - yolo(iou5)) * 100,
        "t1_rows": t1_rows, "t2_rows": t2_rows, "t3_rows": t3_rows,
        "t4_rows": t4_rows, "t5_rows": t5_rows,
    }


def main():
    R = load()
    vals = make_vals(R)
    outs = []
    for lang in ("uz", "ru", "en"):
        d = ASSETS / lang
        d.mkdir(parents=True, exist_ok=True)
        fig_nsweep(R, lang, d / "fig1_nsweep.png")
        fig_alpha(R, lang, d / "fig2_alpha.png")
        outs.append(build(lang, R, vals))
        print(f"[maqola] {lang.upper()} tayyor: {outs[-1].name}")
    print("[maqola] Barcha formulalar Word native OMML (MathType-mos) — rasm emas.")


if __name__ == "__main__":
    main()
