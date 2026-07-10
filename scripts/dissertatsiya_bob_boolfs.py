# -*- coding: utf-8 -*-
"""dissertatsiya_bob_boolfs.py — dissertatsiyaga qo'shiladigan bo'lim:
"II bob (davomi). Bulcha dasturlash asosida informativ belgilarni tanlash va gibrid ansambl".

make_dissertatsiya_phd.py dan chaqiriladi (bob2 dan keyin). Barcha formulalar Word native
OMML (MathType-mos), barcha sonlar runs/exp_20260710/*.json dan avtomatik o'qiladi.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import maqola_formulalar as F
import make_maqola_exp2026 as MA
from omml import add_equation

ROOT = Path(__file__).resolve().parent.parent
FIGDIR = ROOT / "doc_assets_exp2026" / "uz"

# tenglama raqamlari — II bob (2.14) dan keyin davom etadi
EQN = {i: f"2.{14 + i}" for i in range(1, 14)}


def ensure_figures(R):
    FIGDIR.mkdir(parents=True, exist_ok=True)
    if not (FIGDIR / "fig1_nsweep.png").exists():
        MA.fig_nsweep(R, "uz", FIGDIR / "fig1_nsweep.png")
    if not (FIGDIR / "fig2_alpha.png").exists():
        MA.fig_alpha(R, "uz", FIGDIR / "fig2_alpha.png")


def emit(doc, h1, h2, para, lead, bullets, table, concl, img_fn):
    R = MA.load()
    v = MA.make_vals(R)
    ensure_figures(R)

    def eq(fn, n):
        add_equation(doc, *fn(), number=EQN[n])

    h1(doc, "II bob (davomi). Bulcha dasturlash asosida informativ belgilarni tanlash "
            "va interpretatsiyalanadigan gibrid ansambl")

    para(doc, "Ushbu bo'lim dissertatsiyaning ikkinchi bobida bayon etilgan chuqur o'rganish "
              "algoritmlarini mustaqil, to'liq **interpretatsiyalanadigan** ikkinchi bosqich "
              "bilan to'ldiradi. Uning nazariy asosi — ilmiy rahbar professor R.X. Xamdamovning "
              "bulcha dasturlash masalalari nazariyasi (Toshkent, 2017, III bob). Bo'limning "
              "asosiy ilmiy natijasi shundan iboratki, gibrid ansamblning foydasi detektorning "
              "ishonch chegarasiga keskin bog'liq ekani birinchi marta miqdoriy aniqlandi.")

    # ---------------------------------------------------------------- 2.8 --- #
    h2(doc, "2.8-§. Masalaning qo'yilishi va belgilar fazosi")
    para(doc, "Birinchi bosqichda YOLO detektori mammogrammada qiziqish sohalarini (ROI) "
              "topadi. Chuqur neyron tarmoq sifatida u \"qora quti\" bo'lib qoladi: klinik "
              "qarorni asoslash uchun zarur bo'lgan \"qaysi belgi shu qarorga olib keldi?\" "
              "degan savolga javob bermaydi. Bundan tashqari, detektorning past ishonchli "
              "(conf < 0,15) chiqishlari amaliyotda eng muammoli qism hisoblanadi — aynan shu "
              "yerda xato tasniflashlar to'planadi.")
    para(doc, "Shu sababli ikkinchi bosqich sifatida bulcha belgi tanlash mezoni va minimal "
              "masofa qoidasiga asoslangan tasniflagich taklif etiladi. Har bir ROI kesmasidan "
              "38 ta radiomika belgisi ajratiladi: birinchi tartib statistikalari (o'rtacha, "
              "dispersiya, assimetriya, ekstsess), gradient xarakteristikalari (Sobel "
              "operatorining o'rtachasi va standart chetlanishi) hamda ikki masofa (d = 1 va "
              "d = 3) uchun GLCM belgilari: kontrast, dissimilyarlik, bir jinslilik, energiya, "
              "korrelyatsiya, entropiya. Belgilar o'qitish to'plami statistikasi bo'yicha "
              "z-normallashtiriladi.")
    para(doc, "Tadqiqotda sakkiz sinfli mammografiya bazasi ishlatildi: {n_tr} ta o'qitish va "
              "{n_val} ta tekshirish ROI'si (mos ravishda {img_tr} va {img_val} tasvirdan). "
              "Baza kuchli nomutanosib (2.5-jadval), bu kam uchraydigan sinflar bo'yicha "
              "baholarning statistik beqarorligini keltirib chiqaradi.".format(**v))
    table(doc, MA.T["uz"]["t1_h"], v["t1_rows"]("uz"),
          caption="2.5-jadval. Ma'lumotlar bazasidagi ROI'lar taqsimoti")

    # ---------------------------------------------------------------- 2.9 --- #
    h2(doc, "2.9-§. Bulcha belgi tanlash mezoni")
    para(doc, "Xamdamov [1, (3.2.2)] bo'yicha, (p, q) sinflar juftligi va j-belgi uchun uchta "
              "kattalik kiritiladi: sinflararo tarqoqlik va ikkala sinf ichidagi tarqoqliklar:")
    eq(F.eq_a, 1)
    eq(F.eq_b, 2)
    eq(F.eq_c, 3)
    para(doc, "bu yerda x_plj — p-sinfning l-obyekti uchun j-belgi qiymati, k_p — p-sinfdagi "
              "obyektlar soni. Ko'p sinfli (m = 8) holatga o'tish uchun global rejim qo'llanadi: "
              "a_j barcha (p, q) juftliklar bo'yicha, w_j = b_j + c_j esa barcha sinflar ichidagi "
              "tarqoqliklar bo'yicha yig'iladi. Hisoblash vektorlashtirilgan shaklda O(k) "
              "murakkablikda bajariladi.")
    para(doc, "Informativ belgilar to'plamini izlash **bulcha dasturlash masalasiga** keltiriladi. "
              "λ_j ∈ {0, 1} — j-belgining tanlanganligini bildiruvchi bulcha o'zgaruvchi bo'lsin. "
              "Maqsad funksionali tanlangan belgilar bo'yicha sinflararo va sinf ichidagi "
              "tarqoqliklar nisbatini maksimallashtiradi:")
    eq(F.eq_phi, 4)

    # --------------------------------------------------------------- 2.10 --- #
    h2(doc, "2.10-§. Ranjirlangan qator va prefiks bo'yicha tanlash")
    para(doc, "Umumlashgan tengsizliklar usuli [1, 3.4-bo'lim] (3.4.5) ga ko'ra belgilarni "
              "r_j nisbat bo'yicha kamayish tartibida joylashtirishga imkon beradi:")
    eq(F.eq_rank, 5)
    lead(doc, "Muhim nazariy nuans.",
         "Ranjirlangan qatorning prefikslari Φ(λ) ning monoton kamayish zanjirini hosil qiladi. "
         "Biroq qat'iy |S| = n′ cheklovida prefiks umumiy holda mutlaq optimal to'plam bo'lishi "
         "shart emas — buning kontr-misolini qurish mumkin; kitobning (3.4.4) natijasi aynan "
         "prefikslar zanjiri xossasini beradi, mutlaq optimallikni emas. Shu sababli n′ ning "
         "yakuniy qiymati Φ bo'yicha emas, balki tasniflash sifati P bo'yicha tanlanadi:")
    eq(F.eq_nstar, 6)

    # --------------------------------------------------------------- 2.11 --- #
    h2(doc, "2.11-§. Minimal masofa tasniflagichi")
    para(doc, "Har bir p sinf uchun etalon vektor (markaz) va sinf ichki tarqoqligi hisoblanadi "
              "[1, (3.6.2)–(3.6.3)]:")
    eq(F.eq_centroid, 7)
    eq(F.eq_scatter, 8)
    para(doc, "Yangi obyekt x uchun normallashgan masofa va minimal masofa qaror qoidasi:")
    eq(F.eq_rho, 9)
    eq(F.eq_decision, 10)
    para(doc, "Ansamblda ishlatish uchun masofalar softmax almashtirishi orqali ehtimollikka "
              "o'xshash bahoga aylantiriladi:")
    eq(F.eq_softmax, 11)
    para(doc, "k_p < 5 bo'lgan kichik sinflar (masalan, arxitektura buzilishi — atigi 2 ta "
              "misol) uchun kross-validatsiyada leave-one-out sxemasi, qolganlari uchun "
              "stratifikatsiyalangan 5-fold sxemasi qo'llanadi. S(X_p) = 0 chekka holatida "
              "masofa masshtabi buzilmasligi uchun boshqa sinflar tarqoqligining medianasi "
              "olinadi.")

    # --------------------------------------------------------------- 2.12 --- #
    h2(doc, "2.12-§. Gibrid ansambl va sifat mezoni")
    para(doc, "YOLO detektorining p sinf uchun chiqishi (ishonch qiymati asosida taqsimlangan) "
              "va bulcha tasniflagich bahosi vaznli yig'indi orqali birlashtiriladi:")
    eq(F.eq_ensemble, 12)
    para(doc, "Tasniflash ishonchliligi [1, (3.6.4)] to'g'ri tanilgan obyektlar ulushi sifatida "
              "o'lchanadi (I[·] — indikator funksiya):")
    eq(F.eq_P, 13)
    para(doc, "Ansamblni baholashda YOLO chiqishlari etalon ROI'lar bilan ochko'z (greedy) "
              "usulda, IoU ≥ 0,3 sharti asosida moslashtiriladi; P moslashgan juftliklar "
              "bo'yicha hisoblanadi.")

    # --------------------------------------------------------------- 2.13 --- #
    h2(doc, "2.13-§. Eksperimental tadqiqot natijalari")
    para(doc, "Taklif etilgan modelni tekshirish uchun o'n bir eksperiment o'tkazildi: bazaviy "
              "o'qitish va baholash, n′ bo'yicha qidiruv, α, ishonch va IoU chegaralari bo'yicha "
              "sezgirlik tahlili, uch xil detektor bilan ansambl hamda o'qitish to'plamida "
              "barqarorlik nazorati.")

    lead(doc, "Tanlangan belgilar va n′* qiymati.",
         "O'qitish to'plamida ranjirlangan qatorning birinchi o'rinlarini GLCM korrelyatsiya "
         "belgilari egalladi: {top5}. Prefiks uzunligi bo'yicha qidiruv (2.6-jadval, 2.5-rasm) "
         "n′* = {n_star} qiymatida maksimum berdi: kross-validatsiyada P = {p_cv:.3f}, mustaqil "
         "tekshirish to'plamida P = {p_val:.3f}. Ikkala egri chiziq maksimumining bir nuqtada "
         "mos kelishi tanlov protsedurasining barqarorligini tasdiqlaydi. To'liq 38 ta belgidan "
         "foydalanish natijani pasaytiradi (P = {p_38:.3f}) — bu shovqinli belgilarning zararli "
         "ta'sirini ko'rsatadi.".format(**v))
    table(doc, MA.T["uz"]["t2_h"], v["t2_rows"],
          caption="2.6-jadval. Tanlangan belgilar soni n′ ning tasniflash sifatiga ta'siri")
    img_fn(doc, FIGDIR / "fig1_nsweep.png", width=6.0,
           caption="2.5-rasm. Tasniflash ishonchliligi P ning tanlangan belgilar soni n′ ga bog'liqligi")

    lead(doc, "Turli detektorlar bilan ansambl.",
         "Uch xil YOLO detektori bilan o'tkazilgan eksperimentlar (2.7-jadval, 2.6-rasm) "
         "quyidagi qonuniyatni ochib berdi: bulcha tasniflagich barcha holatlarda ijobiy hissa "
         "qo'shadi, biroq detektor qanchalik kuchli bo'lsa, nisbiy ustunlik shunchalik kichik "
         "bo'ladi. Eng yuqori mutlaq natijaga YOLO11l bilan erishildi: P = {l_ens:.3f} "
         "(α* = {l_alpha}), yakka detektorning {l_yolo:.3f} natijasiga qarshi. α bo'yicha egri "
         "chiziqlar bitta maksimumga ega va yassi: α ∈ [0,3; 0,7] oralig'ida natija barqaror, "
         "bu vazn koeffitsientini aniq sozlash talab etilmasligini bildiradi.".format(**v))
    table(doc, MA.T["uz"]["t3_h"], v["t3_rows"],
          caption="2.7-jadval. Turli detektorlar bilan gibrid ansambl natijalari (tekshirish to'plami)")
    img_fn(doc, FIGDIR / "fig2_alpha.png", width=6.0,
           caption="2.6-rasm. Ansambl vazni α ning tasniflash ishonchliligiga ta'siri (uch detektor)")

    lead(doc, "Ishonch chegarasiga bog'liqlik — bo'limning markaziy natijasi.",
         "2.8-jadvalda keltirilgan natijalar taklif etilgan usulning o'rnini aniq belgilaydi. "
         "Detektorning ishonch chegarasi conf = 0,05 dan 0,15 gacha ko'tarilganda YOLO'ning "
         "o'zi {hi_yolo:.3f} aniqlikka chiqadi, chunki past ishonchli (va ko'pincha xato "
         "tasniflangan) chiqishlar filtrlanadi; aynan shu holatda gibrid ansambl qo'shimcha "
         "ustunlik bermaydi ({hi_ens:.3f}). Aksincha, past chegarada (conf = 0,05) YOLO'ning "
         "aniqligi {lo_yolo:.3f} gacha tushadi va bulcha tasniflagich uni {lo_ens:.3f} gacha "
         "ko'taradi — {gain:.1f} foiz punkt o'sish. Mos kelish chegarasini IoU ≥ 0,5 gacha "
         "qattiqlashtirish xulosani o'zgartirmaydi (+{iou_gain:.1f} punkt), o'qitish "
         "to'plamidagi nazorat ham yutuq yo'nalishini tasdiqlaydi.".format(**v))
    table(doc, MA.T["uz"]["t4_h"], v["t4_rows"]("uz"),
          caption="2.8-jadval. Ishonch (conf) va mos kelish (IoU) chegaralariga sezgirlik")

    lead(doc, "Sinflar kesimidagi tahlil.",
         "2.9-jadval eng yaxshi konfiguratsiya (YOLO11l + bulcha tasniflagich, α = {l_alpha}) "
         "uchun sinflar bo'yicha aniqlik va to'liqlikni keltiradi. Eng katta yutuq kalsifikatsiya "
         "sinfida kuzatiladi — bu tekstura belgilarining mayda, yuqori chastotali strukturalarga "
         "sezgirligi bilan izohlanadi.".format(**v))
    table(doc, MA.T["uz"]["t5_h"], v["t5_rows"]("uz"),
          caption="2.9-jadval. Sinflar kesimida aniqlik va to'liqlik (YOLO11l, eng yaxshi α)")

    # --------------------------------------------------------------- 2.14 --- #
    h2(doc, "2.14-§. Natijalarni muhokama qilish va klinik talqin")
    para(doc, "Olingan natijalar ikki bosqichli arxitekturaning qiymatini yangi nuqtai nazardan "
              "ko'rsatadi. Adabiyotda gibrid usullar odatda o'rtacha aniqlik o'sishi bilan "
              "asoslanadi; o'tkazilgan tahlil esa bu o'sish bir tekis taqsimlanmaganini ochib "
              "beradi. Yuqori ishonchli detektsiyalarda YOLO allaqachon deyarli xatosiz ishlaydi "
              "va har qanday qo'shimcha model faqat shovqin kirita oladi. Butun foyda past "
              "ishonchli, ya'ni radiologning o'zi ham ikkilanadigan ROI'lardan keladi.")
    para(doc, "Bu klinik ish oqimi uchun aniq tavsiya beradi: bulcha tasniflagichni barcha "
              "detektsiyalarga emas, balki conf < 0,15 bo'lgan shubhali sohalarga qo'llash "
              "lozim. Bunday selektiv qo'llash hisoblash xarajatini kamaytiradi va yuqori "
              "ishonchli qarorlarga aralashmaydi. Tasniflagich to'liq interpretatsiyalanadigan "
              "bo'lgani uchun (tanlangan {n_star} ta belgi va etalonlargacha bo'lgan masofalar "
              "oshkora), u radiolog uchun \"ikkinchi fikr\" vazifasini bajaradi — bu "
              "dissertatsiyaning izohlanuvchan sun'iy intellekt bo'yicha qo'yilgan "
              "vazifasiga bevosita javob beradi.".format(**v))
    para(doc, "Bo'limning cheklovlari: baza hajmi nisbatan kichik va kuchli nomutanosib "
              "(arxitektura buzilishi sinfida atigi 2 ta o'qitish misoli), shu sababli kam "
              "uchraydigan sinflar bo'yicha baholar statistik jihatdan beqaror. Keyingi "
              "bosqichda bazani kengaytirish va ko'p markazli tekshiruv rejalashtirilgan.")

    concl(doc, "II (davomi)", [
        "Bulcha dasturlash mezoni asosidagi belgi tanlash mammografik ko'p sinfli masalaga "
        "umumlashtirildi; 38 ta belgidan n′* = {n_star} tasi optimal deb topildi va bu tanlov "
        "mustaqil tekshirish to'plamida tasdiqlandi (P = {p_val:.3f}).".format(**v),
        "Qat'iy |S| = n′ cheklovida ranjirlangan qator prefiksi mutlaq optimal to'plam bo'lishi "
        "shart emasligi ko'rsatildi; shu sababli n′* tasniflash sifati P bo'yicha tanlanadi.",
        "Gibrid ansambl barcha sinovdan o'tgan detektorlarda YOLO'ning yakka natijasidan ustun "
        "keldi; eng yuqori natija YOLO11l bilan P = {l_ens:.3f} ni tashkil etdi "
        "(yakka detektor: {l_yolo:.3f}).".format(**v),
        "Usul foydasining detektor ishonch chegarasiga bog'liqligi miqdoriy aniqlandi: past "
        "chegarada +{gain:.1f} foiz punkt, yuqori chegarada esa ustunlik yo'q. Bu bulcha "
        "tasniflagichning o'rnini aniq belgilaydi — shubhali ROI'lar uchun ikkinchi fikr.".format(**v),
        "α ∈ [0,3; 0,7] oralig'ida natija barqaror, bu amaliy joriy etishni soddalashtiradi.",
    ])
