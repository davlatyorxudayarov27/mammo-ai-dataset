# -*- coding: utf-8 -*-
"""dissertatsiya_bob_boolfs_katta.py — II bobning ikkinchi davomi.

Bulcha dasturlash usulini KATTA bazada (13 968 / 2 359 ROI) tekshirish:
belgi tanlash barqarorligi, ma'lumot sizishi nazorati, gibrid ansamblning
halol bahosi va moslashtirish chegarasiga sezuvchanlik.

Manba: `mamograf_yangilash_21-iyun` loyihasidagi exp20–exp24 eksperimentlari
va shulardan yozilgan ikkita maqola (M1 barqarorlik, M2 ansambl).

Raqamlash (avvalgi davomdan keyin):
  §    2.15 … 2.20
  eq   2.28 … 2.40
  jad  2.11 … 2.17
  rasm 2.10 … 2.16
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import maqola_formulalar as F
import maqola_formulalar_ext as X
import make_maqola_m1 as M1
import make_maqola_m2 as M2
from omml import add_equation

ROOT = Path(__file__).resolve().parent.parent
FIGDIR = ROOT / "doc_assets_big" / "uz"
LANG = "uz"

# tenglama raqamlari — avvalgi davom 2.27 da tugagan
EQN = {i: f"2.{27 + i}" for i in range(1, 14)}


def emit(doc, h1, h2, para, lead, bullets, table, concl, img_fn):
    art, stab, agr, small = M1.load()
    met, _art2, iou = M2.load()
    best = met["detectors"][M2.BEST]

    def eq(fn, n):
        add_equation(doc, *fn(), number=EQN[n])

    def N(x, nd=3):
        return M1.K.N(x, LANG, nd)

    def P(x):
        return M1.K.PV(x, LANG)

    h1(doc, "II bob (davomi-2). Bulcha belgi tanlash usulini katta hajmli bazada "
            "tekshirish: barqarorlik, ma'lumot sizishi va ansamblning halol bahosi")

    para(doc, "Oldingi bo'limda bulcha dasturlash usuli 519 ta ROI'dan iborat bazada sinovdan "
              "o'tkazildi. Bunday hajm usulning ishlashini ko'rsatish uchun yetarli, ammo ikkita "
              "muhim savolga javob bera olmaydi: **tanlangan belgilar ro'yxatining o'zi qanchalik "
              "barqaror** va **ansamblning foydasi haqiqiymi**. Ushbu bo'limda tahlil "
              f"{M1.K.INT(art['n_roi_train'], LANG)} ta o'quv va "
              f"{M1.K.INT(art['n_roi_val'], LANG)} ta baholash ROI'sini o'z ichiga olgan, ya'ni "
              "**27 marta katta** bazaga kengaytiriladi. Bo'limning uchta yangi ilmiy natijasi "
              "quyidagilardan iborat: (i) belgi tanlash protsedurasining barqarorligi ikki "
              "qatlamli ekani aniqlandi; (ii) baholash to'plamida **ma'lumot sizishi** topildi va "
              "uning ta'siri miqdoriy o'lchandi; (iii) ansamblning foydasi shartsiz emasligi, u "
              "ROI'ning qiyinligiga bog'liqligi ko'rsatildi.")

    # ---------------------------------------------------------------- 2.15 -- #
    h2(doc, "2.15-§. Katta baza va eksperiment protokoli")
    para(doc, "Tadqiqot `d_ai_8class_1280` bazasida olib borildi: 4 573 ta o'quv va 798 ta "
              "baholash mammogrammasi, sakkiz sinf bilan belgilangan. Haqiqiy (ground-truth) "
              "ramkalardan ajratilgan ROI'lar soni — "
              f"{M1.K.INT(art['n_roi_train'], LANG)} / {M1.K.INT(art['n_roi_val'], LANG)}. "
              "Belgilar detektorning chiqishidan emas, balki haqiqiy ramkalardan ajratilgani "
              "belgi tanlash xossalarini detektor sifatidan mustaqil o'lchash imkonini beradi.")
    para(doc, "Sinflar keskin nomutanosib: limfa tuguni 9 483 ta ROI'da uchraydi, arxitektura "
              "buzilishi esa atigi 13 tasida — nisbat 1 : 730. Shu sababli oddiy aniqlik "
              "yaroqsiz mezondir: barcha ROI'ni ko'pchilik sinfga tegishli deb e'lon qilish "
              "0,679 aniqlik beradi. Optimallashtirish va model tanlash **muvozanatli aniqlik** "
              "(makro sezgirlik) bo'yicha olib boriladi.")
    lead(doc, "Halol baholash protokoli.",
         "Uch qoida qat'iy bajarildi. Birinchidan, belgilarni normallashtirish, ranjirlash, "
         "sentroidlarni hisoblash va ansambl vaznini tanlash — barchasi **faqat o'quv qismida**. "
         "Ikkinchidan, har bir metrika 1000 takrorlashli persentil bootstrap ishonch oralig'i "
         "bilan keltiriladi. Uchinchidan, ikki modelni solishtirishda **juftlashgan** bootstrap "
         "va ikki tomonlama p-qiymat ishlatiladi.")
    table(doc, ["Ko'rsatkich", "Kichik baza", "Katta baza"],
          M1.t1_rows(LANG, art, small, stab),
          caption="2.11-jadval. Qiyoslanayotgan ikki bazaning tavsifi")

    # ---------------------------------------------------------------- 2.16 -- #
    h2(doc, "2.16-§. Belgi tanlash barqarorligini o'lchash usuli")
    para(doc, "Adabiyotda deyarli e'tiborsiz qolgan savol shundaki: agar o'quv namunasi biroz "
              "o'zgarsa, tanlangan belgilar to'plami o'zgaradimi? Agar javob «ha» bo'lsa, "
              "«eng informativ belgilar» haqidagi xulosa ilmiy qiymatga ega bo'lmaydi. "
              "Barqarorlikni o'lchash uchun o'quv to'plamidan qaytarish bilan 300 ta bootstrap "
              "namuna olinadi; har birida ranjirlash $\\pi_b$ hosil bo'ladi va undan quvvati "
              "$n'$ bo'lgan to'plam ajratiladi:")
    eq(X.eq_subset, 1)
    para(doc, "Kuncheva indeksi to'plamlar kesishuvini **tasodifiy kutilmaga nisbatan tuzatadi**, "
              "shu sababli $n'$ katta bo'lganda sun'iy o'sishdan himoyalangan:")
    eq(X.eq_kuncheva, 2)
    para(doc, "Taqqoslash uchun tuzatilmagan Jaccard koeffitsienti ham hisoblanadi:")
    eq(X.eq_jaccard, 3)
    para(doc, "Har bir belgining o'rtacha o'rni va uning tebranishi ranjirlashning qaysi qismi "
              "mustahkam ekanini ko'rsatadi:")
    eq(X.eq_meanrank, 4)
    para(doc, "Nihoyat, ikki turli bazada (kichik $s$ va katta $l$) olingan to'plamlarning "
              "kelishuv koeffitsienti kiritiladi — bu ko'rsatkich adabiyotda uchramaydi va "
              "mazkur ishning metodologik hissasidir:")
    eq(X.eq_agreement, 5)

    # ---------------------------------------------------------------- 2.17 -- #
    h2(doc, "2.17-§. Barqarorlik natijalari: ikki qatlamli manzara")
    lead(doc, "Baza ichida — yuqori takrorlanuvchanlik.",
         "Katta bazada Kuncheva indeksi barcha quvvatlarda 0,830 dan past tushmaydi, "
         "$n' = 5$ da esa mukammal takrorlanuvchanlikka erishadi ($I_C = 1{,}000$). Kichik "
         "bazada indeks sezilarli pastroq va $n' = 34$ da 0,726 gacha cho'kadi. Demak namuna "
         "hajmining oshishi tanlov protsedurasini barqarorlashtiradi.")
    lead(doc, "Tuzatilmagan o'lchov aldaydi.",
         "Jaccard koeffitsienti $n'$ o'sishi bilan monoton ko'tariladi va $n' = 36$ da 0,995 ga "
         "chiqadi. Bu «mukammal barqarorlik» taassurotini yaratadi, aslida esa 38 tadan 36 tasi "
         "tanlanganda istalgan ikki to'plam deyarli albatta ustma-ust tushadi. Kuncheva indeksi "
         "bu artefaktni yo'qotadi. **Barqarorlik haqidagi har qanday xulosa faqat tasodifga "
         "tuzatilgan ko'rsatkichga asoslanishi shart.**")
    table(doc, ["$n'$", "$I_C$ katta", "$J$ katta", "$I_C$ kichik", "$J$ kichik",
                "Kelishuv $A_{s,l}$"],
          M1.t3_rows(LANG, stab, agr),
          caption="2.12-jadval. Belgi tanlash barqarorligi: Kuncheva indeksi va Jaccard "
                  "koeffitsienti (300 bootstrap takrorlash), hamda bazalararo kelishuv")
    img_fn(doc, FIGDIR / "m1_f2_stability.png", width=6.0,
           caption="2.10-rasm. Barqarorlik indekslarining $n'$ ga bog'liqligi ikkala bazada; "
                   "to'ldirilgan chiziq — Kuncheva, punktir — Jaccard")

    lead(doc, "Bazalar orasida — ranjirlash boshi ko'chadi.",
         f"To'liq ranjirlangan qatorlar ikki bazada juda mos keladi: Spirmen korrelyatsiyasi "
         f"$\\rho = {N(agr['spearman'])}$ ($N = 38$). Bundan «usul barqaror» degan xulosa "
         f"chiqarish mumkin edi. Biroq qatorning **boshiga** qaralsa, manzara teskari: top-3 "
         f"to'plamlarining kelishuvi atigi {N(agr['agreement']['3'])} — uchtadan bittasi umumiy. "
         f"Top-5 da kelishuv {N(agr['agreement']['5'])} ga, top-8 da "
         f"{N(agr['agreement']['8'])} ga ko'tariladi.")
    para(doc, "Sababi 2.13-jadvalda ko'rinadi. Kichik bazada birinchi ikki o'rinni GLCM "
              "korrelyatsiyasi egallaydi, katta bazada esa u umuman birinchi beshlikka kirmaydi; "
              "uning o'rniga Sobel gradientining standart chetlanishi mutlaq yetakchiga aylanadi "
              "(300 ta bootstrapning barchasida birinchi o'rin). Izohi fizik: kichik namunada "
              "korrelyatsiya belgilari sinflar orasidagi tasodifiy farqni ushlaydi va bu farq "
              "shovqin darajasida barqaror ko'rinadi; namuna kengayganda haqiqiy ajratuvchi "
              "omil — chegara o'tkirligi — ustunlik qiladi. Ya'ni kichik bazadagi «barqaror» "
              "yetakchi aslida namunaga xos artefakt edi.")
    table(doc, ["O'rin", "Katta baza (13 968 ROI)", "$\\bar{r} \\pm \\sigma$",
                "Kichik baza (519 ROI)", "$\\bar{r} \\pm \\sigma$"],
          M1.t4_rows(LANG, stab),
          caption="2.13-jadval. Bootstrap bo'yicha eng yuqori 5 belgi va ularning o'rtacha o'rni")
    img_fn(doc, FIGDIR / "m1_f3_ranking.png", width=6.0,
           caption="2.11-rasm. Yetakchi belgilarning o'rtacha o'rni va standart chetlanishi; "
                   "ikki bazada qatorning boshi butunlay boshqacha")

    lead(doc, "Ziddiyat emas, ikki xil noaniqlik.",
         "Baza ichida $I_C \\approx 0{,}9$, bazalar orasida esa top-3 kelishuvi 0,33 bo'lishi "
         "qarama-qarshilik emas. Bootstrap namunalari bitta taqsimotdan olinadi, shuning uchun "
         "ular ichidagi barqarorlik faqat **statistik** dispersiyani o'lchaydi. Bazani "
         "almashtirish esa taqsimotning o'zini o'zgartiradi va **epistemik** noaniqlikni ochadi. "
         "Yuqori bootstrap barqarorligi belgilar ro'yxatining boshqa bazaga ko'chishiga kafolat "
         "bermaydi — bu radiomikadagi takrorlanuvchanlik inqirozining bevosita izohidir.")

    # ---------------------------------------------------------------- 2.18 -- #
    h2(doc, "2.18-§. Ma'lumot sizishini aniqlash va nazorat qilish")
    para(doc, "Loyihaning oldingi bosqichida ikki detektor — YOLO11s va YOLO11l — 445 ta rasmdan "
              "iborat eski bazada o'qitilgan edi. Yangi baza mustaqil yig'ilgan, biroq ikkala "
              "bazada ham bir xil arxivdan olingan rasmlar uchraydi. Tekshiruv shuni ko'rsatdiki, "
              "yangi baholash to'plamining **24 ta rasmi** eski bazaning o'quv qismida bo'lgan. "
              "Bunday holat adabiyotda ma'lumot sizishi (data leakage) deb ataladi va u modelni "
              "sun'iy ravishda yaxshi ko'rsatadi. Halol baholash uchun tozalangan to'plam "
              "quriladi:")
    eq(X.eq_leak, 6)
    para(doc, "Detektsiyalar haqiqiy ramkalar bilan ochko'z (greedy) usulda moslashtiriladi; "
              "juftlik quyidagi shart bajarilganda qabul qilinadi:")
    eq(X.eq_iou, 7)
    para(doc, "Har bir detektor uchun sizgan detektsiyalar soni 2.14-jadvalda keltirilgan. "
              "Uchinchi detektor aynan shu bazada o'qitilgani uchun uning 67 ta detektsiyasi "
              "haqiqiy sizish emas; biroq to'liq qiyoslanuvchanlik uchun barcha detektorlar bir "
              "xil tozalangan to'plamda baholanadi.")
    table(doc, M2.T[LANG]["t1_h"], M2.t1_rows(LANG, met),
          caption="2.14-jadval. Uch detektor va ular uchun aniqlangan ma'lumot sizishi")
    img_fn(doc, FIGDIR / "m2_f5_leakage.png", width=5.8,
           caption="2.12-rasm. Sizishning o'lchangan ta'siri: tozalangan va tozalanmagan "
                   "baholash to'plamlaridagi aniqlik")
    lead(doc, "Sizish giperparametrni ham buzadi.",
         "Sizgan modellarda o'quv to'plamida YOLO oqimi sun'iy ravishda kuchli ko'rinadi, shu "
         "sababli optimal ansambl vazni boolfs tomonga siljiydi ($\\alpha^{*} = 0{,}30$ va "
         "$0{,}35$), toza modelda esa muvozanatli $0{,}55$ tanlanadi. Demak sizish nafaqat "
         "yakuniy metrikani, balki **o'rganilgan giperparametrni ham** buzadi — bu ilgari "
         "e'tibor berilmagan ta'sirdir.")

    # ---------------------------------------------------------------- 2.19 -- #
    h2(doc, "2.19-§. Gibrid ansamblning halol bahosi")
    para(doc, "Detektor ishonchidan yumshatilgan ehtimollik vektori quriladi, boolfs oqimidan "
              "esa sentroidgacha bo'lgan normallashtirilgan masofa softmax orqali ehtimollikka "
              "aylantiriladi; ikki vektor chiziqli aralashtiriladi:")
    eq(X.eq_yolo_vec, 8)
    eq(F.eq_ensemble, 9)
    para(doc, "Eng muhim metodologik qoida: ansambl vazni **hech qachon** baholash to'plamida "
              "qidirilmaydi. U faqat o'quv qismidagi moslashgan ROI'lar ustida, muvozanatli "
              "aniqlikni maksimallashtirib topiladi:")
    eq(X.eq_alpha_star, 10)
    para(doc, "Baholash mezonlari sifatida muvozanatli aniqlik, makro o'ziga xoslik, Metyus "
              "koeffitsienti va chegaraga bog'liq bo'lmagan makro ROC-AUC olinadi:")
    eq(X.eq_bacc, 11)
    eq(X.eq_mcc, 12)
    para(doc, "Ansambl va yakka detektor farqi juftlashgan bootstrap bilan baholanadi — har "
              "takrorlashda bir xil indekslar to'plami ikkala modelga qo'llanadi:")
    eq(X.eq_delta, 13)

    lead(doc, "Natija: aniqlik emas, sezgirlik va ajratuvchanlik.",
         f"Sizishdan toza detektorda ($n = {M1.K.INT(best['n_matched_clean'], LANG)}$, "
         f"$\\alpha^{{*}} = {N(best['alpha_star'], 2)}$) ansambl muvozanatli aniqlikni "
         f"{N(best['yolo']['balanced_accuracy'])} dan {N(best['ensemble']['balanced_accuracy'])} "
         f"ga ko'tardi (p = {P(best['delta']['balanced_accuracy']['p'])}), makro ROC-AUC ni esa "
         f"{N(best['yolo']['auc_macro'])} dan {N(best['ensemble']['auc_macro'])} ga "
         f"(p {P(best['delta']['auc_macro']['p'])}). Oddiy aniqlikning "
         f"{N(best['yolo']['accuracy'])} dan {N(best['ensemble']['accuracy'])} ga pasayishi esa "
         f"statistik ahamiyatsiz (p = {P(best['delta']['accuracy']['p'])}).")
    table(doc, M2.T[LANG]["t2_h"], M2.t2_rows(LANG, met),
          caption="2.15-jadval. Sizishdan toza baholash to'plamidagi asosiy metrikalar "
                  "(qavsda 95% bootstrap ishonch oralig'i)")
    img_fn(doc, FIGDIR / "m2_f2_roc.png", width=4.6,
           caption="2.13-rasm. Makro ROC egri chiziqlari; ansambl ikkala yakka oqimdan ustun")

    lead(doc, "Foyda qayerdan keladi.",
         "Ansambl **umumiy** to'g'ri javoblar sonini oshirmaydi; u to'g'ri javoblarni ko'pchilik "
         "sinfdan kamchilik sinflariga qayta taqsimlaydi. BIRADS 1–2 sezgirligi 0,667 dan 0,833 "
         "ga, assimetriya 0,429 dan 0,571 ga, kalsifikatsiya 0,954 dan 0,995 ga ko'tarildi; "
         "limfa tuguni sezgirligi 0,932 dan 0,910 ga tushdi. Nomutanosib klinik masalada bu "
         "aynan kerakli almashuv: bitta ortiqcha limfa tuguni xatosi bilan bitta o'tkazib "
         "yuborilgan BIRADS 4–5 ning narxi teng emas.")
    img_fn(doc, FIGDIR / "m2_f3_sens.png", width=6.0,
           caption="2.14-rasm. Sinflar bo'yicha sezgirlik: yakka detektor va ansambl")
    lead(doc, "Almashuvning narxi.",
         "Chalkashlik matritsasida eng katta diagonaldan tashqari katak — limfa tugunining "
         "BIRADS 1–2 deb tasniflanishi (62 ta ROI). Aynan shu 62 ta yolg'on musbat BIRADS 1–2 "
         "sinfining precision ko'rsatkichini 0,074 ga tushiradi. Ya'ni sezgirlik o'sishi chegara "
         "siljishi evaziga erishilgan. Tizim yakuniy tashxis qo'ymay, radiologga sohani "
         "ko'rsatgan rejimda bunday almashuv oqlanadi, ammo uni yashirmasdan qayd etish shart.")
    img_fn(doc, FIGDIR / "m2_f4_cm.png", width=5.2,
           caption="2.15-rasm. Ansamblning chalkashlik matritsasi (satrlar bo'yicha "
                   "normallashtirilgan)")

    # ---------------------------------------------------------------- 2.20 -- #
    h2(doc, "2.20-§. Ansambl foydasining shartlari va sezuvchanlik tahlili")
    para(doc, "Barcha yuqoridagi natijalar $\\text{IoU} \\geq 0{,}3$ moslashtirish chegarasida "
              "olindi. Bu chegara xulosalarni belgilab qo'ymaganini tekshirish uchun butun oqim — "
              "moslashtirish, $\\alpha^{*}$ ni o'quv qismida qayta tanlash va tozalangan "
              "to'plamda baholash — $\\text{IoU} \\in \\{0{,}3;\\ 0{,}5;\\ 0{,}7\\}$ uchun uch "
              "detektorda qaytadan bajarildi.")
    table(doc, M2.T[LANG]["t7_h"], M2.t7_rows(LANG, iou),
          caption="2.16-jadval. Moslashtirish chegarasiga sezuvchanlik; $\\Delta$ — ansambl "
                  "minus yakka detektor, foizli punktda (qavsda p-qiymat)")
    lead(doc, "Chegaradan mustaqil yagona xulosa.",
         "Makro ROC-AUC dagi o'sish to'qqizta holatning to'qqiztasida ham ijobiy va ahamiyatli "
         "(+6,9 dan +18,6 foizli punktgacha). Ansambl sinflarni tartiblash sifatini har qanday "
         "moslashtirish rejimida oshiradi.")
    lead(doc, "Muvozanatli aniqlikdagi foyda esa shartli.",
         "Toza detektorda u $\\text{IoU} = 0{,}3$ va $0{,}5$ da ahamiyatli (p = 0,036 va "
         "p = 0,042), ammo 0,7 da butunlay yo'qoladi ($\\Delta = -0{,}8$ f.p., p = 0,648). "
         "Sabab ochiq: qat'iy chegara faqat aniq lokalizatsiyalangan, «oson» ROI'larni qoldiradi "
         "(2 088 dan 1 828 ga), va aynan bunday ROI'larda yakka detektorning o'zi ham kuchli — "
         "uning muvozanatli aniqligi 0,640 dan 0,693 ga ko'tariladi, ansamblga qo'shadigan narsa "
         "qolmaydi. Sizishga uchragan detektorlarda esa teskari manzara: chegara qat'iylashgani "
         "sari ansambl foydasi o'sadi (YOLO11s uchun +10,3 dan +25,9 f.p. gacha).")
    para(doc, "Demak, ansambl foydasi ROI'ning **qiyinligiga** bog'liq: u noaniq "
              "lokalizatsiyalangan, chegarasi noravshan sohalarda paydo bo'ladi va oson sohalarda "
              "yo'qoladi. Skrining uchun bu qulay xossa, chunki aynan qiyin sohalar radiologning "
              "e'tiborini talab qiladi. Ansamblning asosiy qiymati — **tartiblash sifatida**, "
              "aniq qaror qoidasida emas.")

    lead(doc, "Ishonchlilik mezoni $P$ haqida.",
         "Professor Xamdamov kiritgan ishonchlilik mezoni $P$ — to'g'ri tasniflangan obyektlar "
         "ulushi — ta'rifi bo'yicha oddiy aniqlik bilan ayni bir xil kattalikdir. Toza "
         "to'plamda u yakka boolfs oqimi uchun 0,603, yakka detektor uchun 0,923, ansambl uchun "
         "0,915 ni tashkil etadi. Aynan shu qiymatlar mezonning chegarasini ochib beradi: $P$ "
         "bo'yicha ansambl «yomonroq» ko'rinadi, holbuki u kam ta'minlangan sinflarda "
         "sezgirlikni ahamiyatli oshirgan. Nomutanosib bazada $P$ ni yakka mezon sifatida "
         "ishlatib bo'lmaydi va uni muvozanatli aniqlik bilan to'ldirish shart:")
    add_equation(doc, *F.eq_P(), number=EQN[13])

    concl(doc, "II (davomi-2)", [
        "Bulcha dasturlash asosidagi belgi tanlash usuli ikki tartibga farq qiluvchi hajmdagi "
        "mammografik bazalarda birinchi marta qiyoslandi; prefiks lemmasi empirik tasdiqlandi.",
        "Tanlov protsedurasi bitta baza ichida yuqori takrorlanuvchanlikka ega (katta bazada "
        "Kuncheva indeksi barcha quvvatlarda 0,830 dan yuqori), ammo bazalar o'rtasida "
        "ranjirlashning boshi ko'chadi: to'liq qatorlar $\\rho = 0{,}937$ darajada mos kelsa-da, "
        "top-3 kelishuvi atigi 0,333. Kichik namunadagi belgi reytingini «universal» deb e'lon "
        "qilish metodologik xatodir.",
        "Tuzatilmagan Jaccard koeffitsienti katta $n'$ larda 0,99 ga chiqib «mukammal "
        "barqarorlik» taassurotini yaratadi; barqarorlik faqat tasodifga tuzatilgan Kuncheva "
        "indeksi bilan o'lchanishi kerak.",
        "Baholash to'plamida 24 ta rasm bo'yicha ma'lumot sizishi aniqlandi va uning ta'siri "
        "miqdoriy o'lchandi; sizish yakuniy metrikadan tashqari o'rganilgan giperparametrni "
        "($\\alpha^{*}$) ham buzishi ko'rsatildi.",
        "Sizishdan toza detektorda gibrid ansambl muvozanatli aniqlikni +5,2 foizli punktga "
        "(p = 0,036), makro ROC-AUC ni +7,9 foizli punktga (p < 0,001) oshiradi; oddiy "
        "aniqlikning pasayishi statistik ahamiyatsiz. Foyda butunlay kam ta'minlangan sinflar "
        "hisobiga: BIRADS 1–2 sezgirligi 0,667 → 0,833, assimetriya 0,429 → 0,571.",
        "Sezuvchanlik tahlili (uch detektor × uch chegara) ansambl foydasining shartli ekanini "
        "ko'rsatdi: ROC-AUC dagi ustunlik to'qqizta holatda ham saqlanadi, muvozanatli "
        "aniqlikdagi foyda esa ROI qiyinligiga bog'liq va oson ROI'larda yo'qoladi. Ansamblning "
        "asosiy qiymati — tartiblash sifatida.",
    ])
