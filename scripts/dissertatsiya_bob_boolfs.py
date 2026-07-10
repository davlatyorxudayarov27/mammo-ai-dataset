# -*- coding: utf-8 -*-
"""dissertatsiya_bob_boolfs.py — dissertatsiyaga qo'shiladigan bo'lim:
"II bob (davomi). Bulcha dasturlash asosida informativ belgilarni tanlash va gibrid ansambl".

make_dissertatsiya_phd.py dan chaqiriladi (bob2 dan keyin). Barcha formulalar Word native
OMML (MathType-mos), barcha sonlar runs/exp_20260710/metrics/*.json dan avtomatik o'qiladi.
Matn maqolaning o'zbekcha variantidan (make_maqola_exp2026.T["uz"]) foydalanmaydi — bu yerda
dissertatsiya uslubidagi mustaqil bayon, lekin son qiymatlari bir manbadan.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import maqola_figures as FG
import maqola_formulalar as F
import make_maqola_exp2026 as MA
from omml import add_equation

ROOT = Path(__file__).resolve().parent.parent
FIGDIR = ROOT / "doc_assets_exp2026" / "uz"

# tenglama raqamlari — II bob (2.14) dan keyin davom etadi
EQN = {i: f"2.{14 + i}" for i in range(1, 14)}
LANG = "uz"


def ensure_figures():
    if not (FIGDIR / "fig5_cm.png").exists():
        FG.build_all(LANG, FIGDIR)


def emit(doc, h1, h2, para, lead, bullets, table, concl, img_fn):
    met, nsw, art = MA.load()
    v = MA.vals_for(LANG, met, nsw, art)
    T = MA.T[LANG]
    ensure_figures()

    def eq(fn, n):
        add_equation(doc, *fn(), number=EQN[n])

    h1(doc, "II bob (davomi). Bulcha dasturlash asosida informativ belgilarni tanlash "
            "va interpretatsiyalanadigan gibrid ansambl")

    para(doc, "Ushbu bo'lim ikkinchi bobda bayon etilgan chuqur o'rganish algoritmlarini "
              "mustaqil, to'liq **interpretatsiyalanadigan** ikkinchi bosqich bilan to'ldiradi. "
              "Nazariy asos — ilmiy rahbar professor R.X. Xamdamovning bulcha dasturlash "
              "masalalari nazariyasi (Toshkent, 2017, III bob). Bo'limning asosiy ilmiy natijasi "
              "shundan iboratki, nomutanosib mammografik bazada gibrid ansamblning foydasi "
              "umumiy aniqlikda emas, balki **sezgirlik va ajratuvchanlik (ROC-AUC)** da namoyon "
              "bo'lishi statistik jihatdan (ishonch oraliqlari va juftlashgan bootstrap bilan) "
              "birinchi marta ko'rsatildi.")

    # ---------------------------------------------------------------- 2.8 --- #
    h2(doc, "2.8-§. Masalaning qo'yilishi, ma'lumotlar bazasi va eksperiment protokoli")
    para(doc, "Birinchi bosqichda YOLO detektori mammogrammada qiziqish sohalarini (ROI) topadi. "
              "Chuqur neyron tarmoq sifatida u \"qora quti\" bo'lib qoladi: klinik qarorni "
              "asoslash uchun zarur bo'lgan \"qaysi belgi shu qarorga olib keldi?\" degan "
              "savolga javob bermaydi. Shu sababli ikkinchi bosqich sifatida bulcha belgi "
              "tanlash mezoni va minimal masofa qoidasiga asoslangan tasniflagich taklif "
              "etiladi.")
    para(doc, "Har bir ROI kesmasidan 38 ta radiomika belgisi ajratiladi: 8 ta intensivlik "
              "statistikasi (o'rtacha, standart chetlanish, mediana, assimetriya, ekssess, "
              "entropiya va ikkita kvantil), 10 ta lokal binar naqsh (LBP) gistogrammasi "
              "komponenti, 6 ta shakl belgisi (yuza nisbati, ekssentrisitet, solidlik, "
              "to'ldirish, ixchamlik, tomonlar nisbati), to'rt yo'nalish bo'yicha "
              "o'rtachalangan va ikki masofa (d = 1 va d = 3) uchun hisoblangan 12 ta GLCM "
              "ko'rsatkichi (kontrast, dissimilyarlik, bir jinslilik, energiya, korrelyatsiya, "
              "ASM) hamda 2 ta gradient belgisi (Sobel operatorining o'rtachasi va standart "
              "chetlanishi). Belgilar o'qitish to'plami statistikasi bo'yicha "
              "z-normallashtiriladi.")
    para(doc, "Tadqiqotda sakkiz sinfli mammografiya bazasi ishlatildi: {n_tr} ta o'qitish va "
              "{n_val} ta tekshirish ROI'si (mos ravishda {img_tr} va {img_val} tasvirdan). "
              "Baza kuchli nomutanosib (2.5-jadval): limfa tugunlari ROI'larning katta qismini "
              "egallaydi, arxitektura buzilishi esa atigi ikki misolda uchraydi. Aynan shu "
              "nomutanosiblik quyida keltiriladigan asosiy xulosaning sababidir.".format(**v))
    table(doc, T["t1_h"], MA.t1_rows(LANG, met, art),
          caption="2.5-jadval. Ma'lumotlar bazasidagi ROI'lar taqsimoti")

    lead(doc, "Eksperiment protokoli.",
         "Ansambl vazni α* faqat o'qitish to'plamidagi moslashgan detektsiyalarda, muvozanatli "
         "aniqlik bo'yicha tanlandi; tekshirish to'plami hech qanday tanlovda ishtirok etmadi va "
         "faqat yakuniy baholashga xizmat qildi. Har bir metrika uchun 95% ishonch oralig'i 1000 "
         "marta bootstrap qayta tanlash bilan hisoblandi; ansambl va yakka detektor farqi (Δ) "
         "juftlashgan bootstrap orqali baholanib, ikki tomonlama p-qiymat keltirildi. YOLO "
         "chiqishlari etalon ROI'lar bilan ochko'z usulda, IoU ≥ 0,3 sharti asosida "
         "moslashtiriladi.")

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
         "yakuniy qiymati Φ bo'yicha emas, balki kross-validatsiyadagi tasniflash sifati P "
         "bo'yicha tanlanadi:")
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
              "stratifikatsiyalangan 5-fold sxemasi qo'llanadi. Baho fold'lar bo'yicha o'rtacha "
              "sifatida emas, balki to'plangan (pooled) bashoratlar bo'yicha olinadi: kichik "
              "sinflar uchun LOO fold'i bitta namunadan iborat bo'lgani sababli fold aniqligi "
              "faqat 0 yoki 1 qiymat oladi va o'rtacha ± standart chetlanish sun'iy ravishda "
              "katta (≈0,37) chiqadi.")

    # --------------------------------------------------------------- 2.12 --- #
    h2(doc, "2.12-§. Gibrid ansambl va sifat mezonlari")
    para(doc, "YOLO detektorining p sinf uchun chiqishi (ishonch qiymati asosida taqsimlangan) "
              "va bulcha tasniflagich bahosi vaznli yig'indi orqali birlashtiriladi:")
    eq(F.eq_ensemble, 12)
    para(doc, "Tasniflash ishonchliligi [1, (3.6.4)] to'g'ri tanilgan obyektlar ulushi sifatida "
              "o'lchanadi (I[·] — indikator funksiya):")
    eq(F.eq_P, 13)
    lead(doc, "Nima uchun bitta mezon yetarli emas.",
         "Nomutanosib bazada (2.5-jadval) umumiy aniqlik ko'p sonli sinf tomonidan boshqariladi "
         "va model sifatini yashirishi mumkin. Shuning uchun har bir c sinf \"bir-hammaga "
         "qarshi\" ko'rinishida qaralib, sezgirlik TP/(TP+FN), o'ziga xoslik TN/(TN+FP), aniqlik "
         "TP/(TP+FP) va F1 hisoblanadi; ularning makro o'rtachasi, shuningdek makro ROC-AUC, "
         "Metyus korrelyatsiya koeffitsienti (MCC) va Cohen κ keltiriladi. Muvozanatli aniqlik "
         "makro sezgirlikka tengdir.")

    # --------------------------------------------------------------- 2.13 --- #
    h2(doc, "2.13-§. Eksperimental tadqiqot natijalari")

    lead(doc, "Tanlangan belgilar va n′* qiymati.",
         "O'qitish to'plamida ranjirlangan qatorning birinchi o'rinlarini GLCM korrelyatsiya "
         "belgilari egalladi: {top5}. Prefiks uzunligi bo'yicha qidiruv (2.6-jadval, 2.5-rasm) "
         "kross-validatsiyada n′* = {n_star} qiymatida maksimum berdi (P = {cv_ci}); mustaqil "
         "tekshirish to'plamida shu n′ uchun aniqlik {val_ci}, makro AUC {val_auc_ci}. To'liq "
         "38 ta belgidan foydalanish natijani biroz pasaytiradi (CV {cv38}, val {acc38}) — bu "
         "shovqinli belgilarning zararli ta'sirini ko'rsatadi.".format(**v))
    table(doc, T["t2_h"], MA.t2_rows(LANG, nsw),
          caption="2.6-jadval. Tanlangan belgilar soni n′ ning tasniflash sifatiga ta'siri "
                  "(qavsda 95% bootstrap ishonch oralig'i)")
    img_fn(doc, FIGDIR / "fig1_nsweep.png", width=6.0,
           caption="2.5-rasm. Tasniflash sifatining n′ ga bog'liqligi; soya — 95% bootstrap "
                   "ishonch oralig'i")
    lead(doc, "Halol talqin.",
         "2.5-rasmdagi ishonch oraliqlari qo'shni n′ qiymatlari uchun kuchli kesishadi: masalan "
         "n′ = 13 va n′ = {n_star} uchun tekshirish to'plamidagi oraliqlar qoplanadi. Demak "
         "ma'lumotlar hajmi n′ ni bir birlik aniqlikda ajratishga yetarli emas; n′* = {n_star} — "
         "kross-validatsiya bo'yicha eng yaxshi tanlov, biroq qo'shni qiymatlardan statistik "
         "ustunligi isbotlanmagan. Bu holat yashirilmasdan ochiq qayd etiladi.".format(**v))

    lead(doc, "Bulcha tasniflagichning yolg'iz ishlashi.",
         "Etalon ROI'lar ustida (detektorsiz, {n_val} ta ROI) tasniflagich aniqlik {bf_acc}, "
         "makro sezgirlik {bf_sens}, makro o'ziga xoslik {bf_spec} va makro ROC-AUC {bf_auc} "
         "ko'rsatdi. Past aniqlik va yuqori AUC birikmasi muhim: model sinflarni tartiblash "
         "(ranking) bo'yicha kuchli, biroq argmin qoidasi bilan qaror qabul qilishda "
         "nomutanosiblikdan zarar ko'radi. Aynan shu sababli u detektorni almashtira olmaydi, "
         "lekin uni to'ldiradi.".format(**v))

    lead(doc, "Gibrid ansambl: qaysi mezon o'sadi?",
         "Uch detektor uchun to'liq metrika to'plami 2.7-jadvalda, farqlarning statistik "
         "ahamiyati 2.8-jadvalda keltirilgan. Natija bir xil emas va aynan shu ilmiy qiziqish "
         "uyg'otadi.")
    bullets(doc, [
        "**YOLO11s** (kuchsizroq detektor, α* = {s_a}, {s_n} mos ROI): barcha asosiy mezonlar "
        "sezilarli o'sdi — aniqlik {s_y_acc} → {s_e_acc} (Δ = {s_d_acc}, {s_p_acc}), makro "
        "sezgirlik {s_y_sens} → {s_e_sens} ({s_p_sens}), makro AUC {s_y_auc} → {s_e_auc} "
        "({s_p_auc}), Cohen κ {s_y_kappa} → {s_e_kappa}.".format(**v),
        "**YOLO11l** (kuchli detektor, α* = {l_a}, {l_n} mos ROI): umumiy aniqlik deyarli "
        "o'zgarmadi — {l_y_acc} → {l_e_acc} ({l_p_acc}, statistik jihatdan ahamiyatsiz). Ammo "
        "makro sezgirlik {l_y_sens} → {l_e_sens} (Δ = {l_d_sens}, {l_p_sens}) va makro AUC "
        "{l_y_auc} → {l_e_auc} sezilarli yaxshilandi.".format(**v),
        "**YOLO11l-v2** (eng kuchli detektor, α* = {v_a}, {v_n} mos ROI): aniqlik {v_y_acc} → "
        "{v_e_acc} ({v_p_acc}) — ahamiyatsiz; faqat makro AUC {v_y_auc} → {v_e_auc} "
        "({v_p_auc}) sezilarli o'sdi.".format(**v),
    ])
    table(doc, T["t3_h"], MA.t3_rows(LANG, met),
          caption="2.7-jadval. Tekshirish to'plamidagi to'liq metrika to'plami "
                  "(95% ishonch oralig'i bilan)")
    table(doc, T["t4_h"], MA.t4_rows(LANG, met),
          caption="2.8-jadval. Ansambl va yakka detektor farqi Δ: juftlashgan bootstrap, "
                  "95% CI va p-qiymat")
    img_fn(doc, FIGDIR / "fig2_alpha.png", width=6.0,
           caption="2.6-rasm. Ansambl vazni α ning muvozanatli aniqlikka ta'siri (YOLO11l); "
                   "α* o'qitish to'plamida tanlanadi")
    para(doc, "Bu manzara aniq qonuniyatni ochadi: **detektor qanchalik kuchli bo'lsa, "
              "ansamblning foydasi shunchalik toraydi va aniqlikdan sezgirlik hamda "
              "ajratuvchanlik (AUC) tomon siljiydi.** Umumiy aniqlikning o'zgarmasligi ansambl "
              "foydasiz degani emas — u shunchaki ko'p sonli sinf (limfa tuguni) tomonidan "
              "boshqariladi.")

    lead(doc, "Yutuq qayerdan keladi.",
         "2.9-jadval va 2.7-rasm buni yaqqol ko'rsatadi (YOLO11l). Ansambl kam uchraydigan, "
         "klinik jihatdan muhim sinflarda sezgirlikni keskin oshiradi: kalsifikatsiya "
         "{calc_y} → {calc_e}, assimetriya {asym_y} → {asym_e}, BIRADS 1-2 {b12_y} → {b12_e}. "
         "Buning evaziga ko'p sonli limfa tuguni sinfida sezgirlik {lymph_y} dan {lymph_e} "
         "gacha tushadi. Aynan shu almashuv umumiy aniqlikni deyarli o'zgarishsiz qoldiradi, "
         "lekin makro sezgirlikni va AUC ni oshiradi. Skrining kontekstida bu maqbul kelishuv: "
         "kalsifikatsiya va assimetriya o'tkazib yuborilishi limfa tugunini noto'g'ri "
         "belgilashdan ancha qimmatga tushadi.".format(**v))
    table(doc, T["t5_h"], MA.t5_rows(LANG, met),
          caption="2.9-jadval. Sinflar kesimida sezgirlik, o'ziga xoslik va aniqlik (YOLO11l)")
    img_fn(doc, FIGDIR / "fig4_sens.png", width=6.0,
           caption="2.7-rasm. Sinflar kesimida sezgirlik: yakka YOLO11l va gibrid ansambl")
    img_fn(doc, FIGDIR / "fig3_roc.png", width=4.5,
           caption="2.8-rasm. Makro ROC egri chiziqlari (YOLO11l): ansambl butun ishlash "
                   "nuqtalari bo'ylab yakka detektordan ustun")
    img_fn(doc, FIGDIR / "fig5_cm.png", width=5.3,
           caption="2.9-rasm. Ansambl chalkashlik matritsasi (YOLO11l); rang qator bo'yicha "
                   "normallashtirilgan")

    lead(doc, "Ishonch va IoU chegaralariga sezgirlik.",
         "2.10-jadvalda chegaralar o'zgartirilgan holatlar keltirilgan (YOLO11s asosida). "
         "Chegara conf = 0,15 ga ko'tarilganda ({hi_n} mos ROI) detektorning o'zi {hi_y_acc} "
         "aniqlikka chiqadi, chunki past ishonchli chiqishlar filtrlanadi; ansambl bu holda "
         "qarorlarni umuman o'zgartirmaydi ({hi_e_acc}, {hi_p_acc}). Shu bilan birga makro AUC "
         "{hi_y_auc} dan {hi_e_auc} gacha o'sadi — tartiblash sifati baribir yaxshilanadi. Mos "
         "kelish chegarasi IoU ≥ 0,5 gacha qattiqlashtirilganda ({io_n} mos ROI) ansambl "
         "aniqlikni {io_y_acc} dan {io_e_acc} gacha ({io_pp_acc} foiz punkt, {io_p_acc}) "
         "ko'taradi.".format(**v))
    table(doc, T["t6_h"], MA.t6_rows(LANG, met),
          caption="2.10-jadval. Ishonch (conf) va mos kelish (IoU) chegaralariga sezgirlik")

    # --------------------------------------------------------------- 2.14 --- #
    h2(doc, "2.14-§. Natijalarni muhokama qilish, klinik talqin va cheklovlar")
    para(doc, "Adabiyotda gibrid usullar odatda o'rtacha aniqlik o'sishi bilan asoslanadi. "
              "O'tkazilgan tahlil shuni ko'rsatadiki, kuchli detektor va nomutanosib baza "
              "sharoitida bunday asoslash yetarli emas va hatto chalg'ituvchi bo'lishi mumkin: "
              "YOLO11l uchun aniqlik amalda o'zgarmadi ({l_p_acc}), holbuki makro sezgirlik "
              "{l_d_sens} ga o'sdi. Agar faqat aniqlik keltirilganda edi, usul \"foydasiz\" deb "
              "baholanardi; agar faqat sezgirlik keltirilganda edi, o'sish bo'rttirilardi. "
              "To'g'ri yondashuv — ikkala mezonni birga keltirish.".format(**v))
    para(doc, "Ikkinchi muhim kuzatuv — bulcha tasniflagichning yolg'iz o'zi yuqori AUC "
              "({bf_auc}) va past aniqlik ({bf_acc}) ko'rsatishi. Bu uning axborot hissasi qaror "
              "qabul qilish qoidasida emas, balki sinflarni tartiblashda ekanini bildiradi. "
              "Ansambl aynan shu tartiblash axborotini detektorning ishonch bahosiga "
              "qo'shadi.".format(**v))
    para(doc, "Klinik ish oqimi uchun tavsiya: bulcha tasniflagichni kuchli detektorning yuqori "
              "ishonchli qarorlariga aralashtirmaslik, uni kam uchraydigan sinflar shubhasi bor "
              "va past ishonchli sohalarda \"ikkinchi fikr\" sifatida ishlatish maqsadga "
              "muvofiq. Tasniflagich to'liq interpretatsiyalanadigan bo'lgani uchun (tanlangan "
              "{n_star} ta belgi va etalonlargacha bo'lgan masofalar oshkora), uning bahosi "
              "radiolog tomonidan tekshirilishi mumkin — bu dissertatsiyaning izohlanuvchan "
              "sun'iy intellekt bo'yicha qo'yilgan vazifasiga bevosita javob beradi.".format(**v))
    lead(doc, "Cheklovlar.",
         "Baza hajmi kichik: tekshirish to'plamida moslashgan detektsiyalar soni 75–105 "
         "oralig'ida, ba'zi sinflarda atigi 3–6 ta misol. Shu sababli ishonch oraliqlari keng va "
         "bir qator farqlar statistik ahamiyatga ega emas (2.8-jadval). α* o'qitish to'plamida "
         "tanlangan bo'lsa-da, u ham cheklangan hajmga ega. Arxitektura buzilishi sinfida atigi "
         "ikkita o'qitish misoli bor va u tekshirish to'plamida umuman mos kelmagan. Xulosalar "
         "ko'p markazli, kattaroq bazada takrorlanishi lozim.")

    concl(doc, "II (davomi)", [
        "Bulcha dasturlash mezoni asosidagi belgi tanlash mammografik ko'p sinfli masalaga "
        "umumlashtirildi; kross-validatsiya bo'yicha 38 ta belgidan n′* = {n_star} tasi eng "
        "yaxshi natija berdi (P = {cv_ci}), biroq qo'shni n′ qiymatlaridan statistik ustunligi "
        "isbotlanmadi.".format(**v),
        "Qat'iy |S| = n′ cheklovida ranjirlangan qator prefiksi mutlaq optimal to'plam bo'lishi "
        "shart emasligi ko'rsatildi; shu sababli n′* tasniflash sifati P bo'yicha tanlanadi.",
        "Nomutanosib bazada umumiy aniqlik yolg'iz mezon sifatida yetarli emasligi ko'rsatildi: "
        "YOLO11l uchun ansambl aniqlikni o'zgartirmadi ({l_p_acc}), lekin makro sezgirlikni "
        "{l_y_sens} dan {l_e_sens} gacha ({l_p_sens}) va makro AUC ni {l_y_auc} dan {l_e_auc} "
        "gacha oshirdi.".format(**v),
        "Kuchsizroq detektor (YOLO11s) uchun ansambl barcha mezonlarni sezilarli yaxshiladi: "
        "aniqlik {s_y_acc} → {s_e_acc} ({s_p_acc}), makro AUC {s_y_auc} → {s_e_auc}, "
        "Cohen κ {s_y_kappa} → {s_e_kappa}.".format(**v),
        "Yutuq kam uchraydigan, klinik jihatdan muhim sinflarda jamlangan (kalsifikatsiya "
        "{calc_y} → {calc_e}, assimetriya {asym_y} → {asym_e}) va ko'p sonli sinf hisobiga "
        "erishiladi — skrining uchun maqbul almashuv.".format(**v),
        "Bulcha tasniflagich yolg'iz yuqori ajratuvchanlik ({bf_auc}) va past aniqlik "
        "({bf_acc}) ko'rsatadi, ya'ni uning roli detektorni to'ldirish — o'rin bosish "
        "emas.".format(**v),
    ])
