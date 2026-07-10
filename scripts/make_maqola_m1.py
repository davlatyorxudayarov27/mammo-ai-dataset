# -*- coding: utf-8 -*-
"""make_maqola_m1.py — 1-MAQOLA: Bul dasturlash asosidagi belgi tanlashning
namuna hajmiga bog'liq barqarorligi (nazariy-metodologik).

Uch tilda (uz/ru/en), barcha formulalar Word-native OMML (MathType-mos).
Chiqish: MAMOGRAF_Maqola_2026_M1_Barqarorlik_{UZ,RU,EN}.docx
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from docx import Document

import maqola_formulalar as F
import maqola_formulalar_ext as X
import maqola_kit as K
from omml import add_equation

ROOT = Path(__file__).resolve().parent.parent
BIG = ROOT / "runs/exp_big_20260710"
SMALL = ROOT / "runs/exp_20260710/exp01_fit"
ASSETS = ROOT / "doc_assets_big"
N_LIST = [3, 5, 8, 13, 21, 28, 34, 36]


def load():
    art = json.loads((BIG / "artifacts.json").read_text())
    stab = json.loads((BIG / "stability_multi.json").read_text())
    agr = json.loads((BIG / "agreement.json").read_text())
    small = json.loads((SMALL / "artifacts.json").read_text())
    return art, stab, agr, small


# ═══════════════════════════════ matnlar ═════════════════════════════════ #

FEAT = {
    "grad_sobel_std": {"uz": "grad_sobel_std", "ru": "grad_sobel_std", "en": "grad_sobel_std"},
}


def fname(f):
    return f"$\\texttt{{{f}}}$".replace("_", r"\_")


T = {
    "uz": {
        "title": "Bul dasturlash asosidagi belgi tanlashning namuna hajmiga bog'liq "
                 "barqarorligi: mammografik ROI'lar bo'yicha ko'lamli tadqiqot",
        "authors": ["A. Turaqulov", "Ilmiy rahbar: prof. N. Xamdamov",
                    "Muhammad al-Xorazmiy nomidagi Toshkent axborot texnologiyalari universiteti"],
        "abs_l": "Annotatsiya.",
        "abs": "Bul dasturlash masalasi sifatida qo'yilgan belgi tanlash usuli (Xamdamov, 2017) "
               "mammografik qiziqish sohalari (ROI) uchun ilk marta ikki tartibga farq qiluvchi "
               "hajmdagi bazalarda — 519 va 13 968 ta ROI'da — qiyosiy o'rganildi. Har bir ROI'dan "
               "$N = 38$ ta gistogramma, GLCM va gradient belgisi ajratildi; tanlov (3.2.2) "
               "kriteriysi va $r_j = a_j / w_j$ ranjirlashi asosida amalga oshirildi. 300 tadan "
               "bootstrap takrorlash bilan Kuncheva tasodifga tuzatilgan indeksi, juftlik-o'rtacha "
               "Jaccard koeffitsienti va belgilarning o'rtacha o'rni $\\bar{r}_j \\pm \\sigma_j$ "
               "o'lchandi. Asosiy natija ikki qatlamli: (i) tanlov protsedurasi HAR BIR baza ichida "
               "yuqori takrorlanuvchanlikka ega ($I_C \\geq 0{,}83$ katta bazada barcha $n'$ larda), "
               "biroq (ii) bazalar O'RTASIDA ranjirlashning boshi ko'chib ketadi: to'liq qatorlar "
               "Spirmen bo'yicha $\\rho = 0{,}937$ darajada mos kelsa-da, top-3 to'plamlarining "
               "kesishuvi atigi $0{,}333$ ni tashkil etadi. Kichik bazada birinchi o'rinni GLCM "
               "korrelyatsiyasi egallasa, katta bazada u Sobel gradientining standart chetlanishiga "
               "o'tadi ($\\bar{r} = 1{,}0 \\pm 0{,}0$). Bundan tanlangan belgilar ro'yxatini kichik "
               "namunadan olib, uni «universal» deb e'lon qilish metodologik xato ekani kelib chiqadi. "
               "Optimal quvvat $n'^{*}$ namuna hajmi bilan birga $34 \\to 36$ ga siljidi va "
               "muvozanatli aniqlik $0{,}638$ [0,606; 0,762], makro ROC-AUC $0{,}947$ [0,928; 0,960] "
               "ga yetdi.",
        "kw_l": "Kalit so'zlar:",
        "kw": "belgi tanlash, bul dasturlash, tanlov barqarorligi, Kuncheva indeksi, mammografiya, "
              "GLCM, minimal masofa klassifikatori, bootstrap.",
        "h1": "1. Kirish",
        "h2": "2. Usul",
        "h21": "2.1. Belgilar fazosi",
        "h22": "2.2. Bul dasturlash mezoni va ranjirlash",
        "h23": "2.3. Klassifikator va $n'^{*}$ ni tanlash",
        "h24": "2.4. Barqarorlikni o'lchash",
        "h3": "3. Eksperiment sozlamalari",
        "h4": "4. Natijalar",
        "h41": "4.1. Quvvat bo'yicha o'tkazish: $n'$ ning ta'siri",
        "h42": "4.2. Baza ichidagi barqarorlik",
        "h43": "4.3. Bazalar orasidagi ranjirlash kelishuvi",
        "h44": "4.4. $\\Phi$ prefiks zanjirining monotonligi",
        "h5": "5. Muhokama",
        "h6": "6. Xulosa",
        "refs_l": "Adabiyotlar",
        # jadval sarlavhalari
        "t1_cap": "1-jadval. Tadqiqotda ishlatilgan ikki baza tavsifi",
        "t1_h": ["Ko'rsatkich", "Kichik baza", "Katta baza"],
        "t2_cap": "2-jadval. Katta bazada quvvat $n'$ bo'yicha o'tkazish natijalari "
                  "(pooled CV va val; 95% bootstrap ishonch oralig'i)",
        "t2_h": ["$n'$", "CV aniqlik [95% CI]", "CV muvozanatli aniqlik [95% CI]",
                 "val aniqlik", "val muv. aniqlik", "val AUC"],
        "t3_cap": "3-jadval. Belgi tanlash barqarorligi: Kuncheva indeksi $I_C$ va Jaccard $J$ "
                  "(300 bootstrap takrorlash)",
        "t3_h": ["$n'$", "$I_C$ katta", "$J$ katta", "$I_C$ kichik", "$J$ kichik",
                 "Kelishuv $A_{s,l}$"],
        "t4_cap": "4-jadval. Bootstrap bo'yicha eng yuqori 5 belgi: o'rtacha o'rin "
                  "$\\bar{r}_j \\pm \\sigma_j$",
        "t4_h": ["O'rin", "Katta baza (13 968 ROI)", "$\\bar{r} \\pm \\sigma$",
                 "Kichik baza (519 ROI)", "$\\bar{r} \\pm \\sigma$"],
        "t5_cap": "5-jadval. Katta bazadagi ranjirlashning birinchi sakkiz belgisi: "
                  "$r_j$ va prefiks funksionali $\\Phi(n')$",
        "t5_h": ["$n'$", "Belgi", "$r_j$", "$\\Phi(n')$"],
        # rasm sarlavhalari
        "f1_cap": "1-rasm. Quvvat $n'$ ga bog'liq muvozanatli aniqlik (chapda, 95% bootstrap "
                  "yo'lagi bilan) va makro ROC-AUC (o'ngda). Vertikal chiziq — tanlangan $n'^{*}$.",
        "f2_cap": "2-rasm. Belgi tanlash barqarorligi ikkala bazada: to'ldirilgan chiziq — "
                  "Kuncheva tasodifga tuzatilgan indeksi, punktir — Jaccard koeffitsienti.",
        "f3_cap": "3-rasm. Bootstrap bo'yicha eng yuqori belgilarning o'rtacha o'rni va uning "
                  "standart chetlanishi. Ikki bazada qatorning boshi butunlay boshqacha.",
        "f4_cap": "4-rasm. Prefiks funksionali $\\Phi(n')$ ning kamayuvchi zanjiri (katta baza). "
                  "Egrining tirsagi $n' \\approx 21$ da; undan keyin qo'shilgan belgilarning "
                  "o'rtacha informativligi keskin pasayadi.",
        "eq_l": "bu yerda",
    },
    "ru": {
        "title": "Устойчивость отбора признаков на основе булева программирования в зависимости "
                 "от объёма выборки: масштабное исследование на маммографических ROI",
        "authors": ["А. Туракулов", "Научный руководитель: проф. Н. Хамдамов",
                    "Ташкентский университет информационных технологий имени Мухаммада аль-Хорезми"],
        "abs_l": "Аннотация.",
        "abs": "Метод отбора признаков, сформулированный как задача булева программирования "
               "(Хамдамов, 2017), впервые сопоставительно исследован на маммографических областях "
               "интереса (ROI) для двух баз, различающихся на два порядка по объёму, — 519 и 13 968 "
               "ROI. Из каждой ROI извлекались $N = 38$ гистограммных, GLCM- и градиентных "
               "признаков; отбор выполнялся по критерию (3.2.2) и ранжированию $r_j = a_j / w_j$. "
               "По 300 бутстреп-повторениям измерялись индекс Кунчевой с поправкой на случайность, "
               "попарно усреднённый коэффициент Жаккара и средний ранг признака "
               "$\\bar{r}_j \\pm \\sigma_j$. Главный результат двухслойный: (i) процедура отбора "
               "обладает высокой воспроизводимостью ВНУТРИ каждой базы ($I_C \\geq 0{,}83$ на "
               "большой базе при всех $n'$), однако (ii) МЕЖДУ базами голова ранжирования смещается: "
               "при том что полные ряды согласуются по Спирмену на уровне $\\rho = 0{,}937$, "
               "пересечение множеств топ-3 составляет лишь $0{,}333$. На малой базе первое место "
               "занимает GLCM-корреляция, на большой — стандартное отклонение градиента Собеля "
               "($\\bar{r} = 1{,}0 \\pm 0{,}0$). Отсюда следует, что перенос списка признаков, "
               "полученного на малой выборке, в качестве «универсального» является методологической "
               "ошибкой. Оптимальная мощность $n'^{*}$ вместе с объёмом выборки сместилась "
               "$34 \\to 36$, а сбалансированная точность достигла $0{,}638$ [0,606; 0,762] при "
               "макро ROC-AUC $0{,}947$ [0,928; 0,960].",
        "kw_l": "Ключевые слова:",
        "kw": "отбор признаков, булево программирование, устойчивость отбора, индекс Кунчевой, "
              "маммография, GLCM, классификатор минимального расстояния, бутстреп.",
        "h1": "1. Введение",
        "h2": "2. Метод",
        "h21": "2.1. Пространство признаков",
        "h22": "2.2. Критерий булева программирования и ранжирование",
        "h23": "2.3. Классификатор и выбор $n'^{*}$",
        "h24": "2.4. Измерение устойчивости",
        "h3": "3. Постановка эксперимента",
        "h4": "4. Результаты",
        "h41": "4.1. Развёртка по мощности: влияние $n'$",
        "h42": "4.2. Устойчивость внутри базы",
        "h43": "4.3. Согласованность ранжирований между базами",
        "h44": "4.4. Монотонность префиксной цепочки $\\Phi$",
        "h5": "5. Обсуждение",
        "h6": "6. Заключение",
        "refs_l": "Литература",
        "t1_cap": "Таблица 1. Характеристика двух использованных баз",
        "t1_h": ["Показатель", "Малая база", "Большая база"],
        "t2_cap": "Таблица 2. Развёртка по мощности $n'$ на большой базе "
                  "(объединённая CV и val; 95% бутстреп-доверительный интервал)",
        "t2_h": ["$n'$", "CV точность [95% CI]", "CV сбаланс. точность [95% CI]",
                 "val точность", "val сбал. точность", "val AUC"],
        "t3_cap": "Таблица 3. Устойчивость отбора признаков: индекс Кунчевой $I_C$ и Жаккар $J$ "
                  "(300 бутстреп-повторений)",
        "t3_h": ["$n'$", "$I_C$ больш.", "$J$ больш.", "$I_C$ мал.", "$J$ мал.",
                 "Согласие $A_{s,l}$"],
        "t4_cap": "Таблица 4. Пять старших признаков по бутстрепу: средний ранг "
                  "$\\bar{r}_j \\pm \\sigma_j$",
        "t4_h": ["Ранг", "Большая база (13 968 ROI)", "$\\bar{r} \\pm \\sigma$",
                 "Малая база (519 ROI)", "$\\bar{r} \\pm \\sigma$"],
        "t5_cap": "Таблица 5. Первые восемь признаков ранжирования на большой базе: "
                  "$r_j$ и префиксный функционал $\\Phi(n')$",
        "t5_h": ["$n'$", "Признак", "$r_j$", "$\\Phi(n')$"],
        "f1_cap": "Рис. 1. Сбалансированная точность в зависимости от мощности $n'$ (слева, с "
                  "95% бутстреп-коридором) и макро ROC-AUC (справа). Вертикальная линия — "
                  "выбранное $n'^{*}$.",
        "f2_cap": "Рис. 2. Устойчивость отбора признаков на обеих базах: сплошная линия — индекс "
                  "Кунчевой с поправкой на случайность, пунктир — коэффициент Жаккара.",
        "f3_cap": "Рис. 3. Средний ранг старших признаков по бутстрепу и его стандартное "
                  "отклонение. На двух базах голова ряда совершенно различна.",
        "f4_cap": "Рис. 4. Убывающая цепочка префиксного функционала $\\Phi(n')$ (большая база). "
                  "Излом кривой при $n' \\approx 21$; далее средняя информативность добавляемых "
                  "признаков резко падает.",
        "eq_l": "где",
    },
    "en": {
        "title": "Sample-size dependence of Boolean-programming feature selection: "
                 "a scale study on mammographic regions of interest",
        "authors": ["A. Turaqulov", "Supervisor: Prof. N. Khamdamov",
                    "Tashkent University of Information Technologies named after Muhammad al-Khwarizmi"],
        "abs_l": "Abstract.",
        "abs": "Feature selection posed as a Boolean programming problem (Khamdamov, 2017) is, for "
               "the first time, studied comparatively on mammographic regions of interest (ROIs) "
               "across two databases differing by two orders of magnitude in size — 519 versus "
               "13,968 ROIs. From each ROI, $N = 38$ histogram, GLCM and gradient features were "
               "extracted; selection followed criterion (3.2.2) and the ranking "
               "$r_j = a_j / w_j$. Using 300 bootstrap replicates we measured the "
               "chance-corrected Kuncheva index, the pairwise-averaged Jaccard coefficient, and "
               "each feature's mean rank $\\bar{r}_j \\pm \\sigma_j$. The principal result has two "
               "layers: (i) the selection procedure is highly reproducible WITHIN each database "
               "($I_C \\geq 0.83$ on the large database at every $n'$), yet (ii) BETWEEN databases "
               "the head of the ranking moves: although the full orderings agree at Spearman "
               "$\\rho = 0.937$, the intersection of the top-3 sets is only $0.333$. On the small "
               "database GLCM correlation ranks first, whereas on the large one the leader becomes "
               "the standard deviation of the Sobel gradient ($\\bar{r} = 1.0 \\pm 0.0$). It follows "
               "that promoting a feature list obtained on a small sample to a «universal» "
               "one is a methodological error. The optimal cardinality $n'^{*}$ shifted with sample "
               "size from $34 \\to 36$, and balanced accuracy reached $0.638$ [0.606; 0.762] at a "
               "macro ROC-AUC of $0.947$ [0.928; 0.960].",
        "kw_l": "Keywords:",
        "kw": "feature selection, Boolean programming, selection stability, Kuncheva index, "
              "mammography, GLCM, minimum-distance classifier, bootstrap.",
        "h1": "1. Introduction",
        "h2": "2. Method",
        "h21": "2.1. The feature space",
        "h22": "2.2. The Boolean programming criterion and ranking",
        "h23": "2.3. Classifier and the choice of $n'^{*}$",
        "h24": "2.4. Measuring stability",
        "h3": "3. Experimental setup",
        "h4": "4. Results",
        "h41": "4.1. Cardinality sweep: the effect of $n'$",
        "h42": "4.2. Within-database stability",
        "h43": "4.3. Cross-database ranking agreement",
        "h44": "4.4. Monotonicity of the $\\Phi$ prefix chain",
        "h5": "5. Discussion",
        "h6": "6. Conclusion",
        "refs_l": "References",
        "t1_cap": "Table 1. Description of the two databases used in the study",
        "t1_h": ["Quantity", "Small database", "Large database"],
        "t2_cap": "Table 2. Cardinality sweep over $n'$ on the large database "
                  "(pooled CV and val; 95% bootstrap confidence intervals)",
        "t2_h": ["$n'$", "CV accuracy [95% CI]", "CV balanced accuracy [95% CI]",
                 "val accuracy", "val bal. accuracy", "val AUC"],
        "t3_cap": "Table 3. Feature-selection stability: Kuncheva index $I_C$ and Jaccard $J$ "
                  "(300 bootstrap replicates)",
        "t3_h": ["$n'$", "$I_C$ large", "$J$ large", "$I_C$ small", "$J$ small",
                 "Agreement $A_{s,l}$"],
        "t4_cap": "Table 4. Top five features by bootstrap: mean rank "
                  "$\\bar{r}_j \\pm \\sigma_j$",
        "t4_h": ["Rank", "Large database (13,968 ROIs)", "$\\bar{r} \\pm \\sigma$",
                 "Small database (519 ROIs)", "$\\bar{r} \\pm \\sigma$"],
        "t5_cap": "Table 5. The first eight features of the ranking on the large database: "
                  "$r_j$ and the prefix functional $\\Phi(n')$",
        "t5_h": ["$n'$", "Feature", "$r_j$", "$\\Phi(n')$"],
        "f1_cap": "Fig. 1. Balanced accuracy versus cardinality $n'$ (left, with a 95% bootstrap "
                  "band) and macro ROC-AUC (right). The vertical line marks the selected $n'^{*}$.",
        "f2_cap": "Fig. 2. Feature-selection stability on both databases: solid line — "
                  "chance-corrected Kuncheva index, dashed — Jaccard coefficient.",
        "f3_cap": "Fig. 3. Bootstrap mean rank of the leading features and its standard deviation. "
                  "The head of the ordering is entirely different on the two databases.",
        "f4_cap": "Fig. 4. The decreasing chain of the prefix functional $\\Phi(n')$ (large "
                  "database). The elbow lies at $n' \\approx 21$; beyond it the average "
                  "informativeness of newly added features drops sharply.",
        "eq_l": "where",
    },
}

# ─────────────────────── uzun matnli bo'limlar ──────────────────────────── #

BODY = {
    "uz": {
        "intro": [
            "Mammografik tasvirlarni avtomatik tahlil qilishda chuqur konvolyutsion detektorlar "
            "so'nggi yillarda hukmron o'ringa chiqdi. Biroq ular qora quti bo'lib qolmoqda: "
            "qaysi tekstura xossasi qaror qabul qilishga hissa qo'shgani ko'rinmaydi, bu esa "
            "klinik amaliyotda ishonchni cheklaydi. Shu sababli interpretatsiya qilinadigan, "
            "aniq matematik ta'rifga ega belgilar to'plamini avtomatik ajratish masalasi o'z "
            "ahamiyatini yo'qotgani yo'q.",

            "N. Xamdamov [1] belgi tanlashni bul dasturlash masalasi sifatida qo'ydi: har bir "
            "belgiga $\\lambda_j \\in \\{0, 1\\}$ ikkilik o'zgaruvchisi biriktiriladi va sinflararo "
            "ajratuvchanlik bilan sinf ichidagi tarqoqlik nisbatini ifodalovchi $\\Phi(\\lambda)$ "
            "funksionali maksimallashtiriladi. Usulning muhim xossasi — yechim to'liq sanab "
            "chiqishni talab qilmaydi: $r_j = a_j / w_j$ ko'rsatkichi bo'yicha ranjirlangan qator "
            "prefiksi optimal yechimni beradi, ya'ni murakkablik $O(2^N)$ dan $O(N \\log N)$ ga "
            "tushadi.",

            "Ammo adabiyotda deyarli e'tiborsiz qolgan savol shundaki: **tanlangan belgilar "
            "ro'yxatining o'zi qanchalik barqaror?** Agar $\\lambda^{*}$ o'quv namunasining kichik "
            "o'zgarishidan sezilarli tebransa, undan chiqarilgan «eng informativ belgilar» "
            "haqidagi xulosa ilmiy qiymatga ega bo'lmaydi. Kuncheva [2] bu muammoni umumiy holda "
            "qo'ygan va tasodifga tuzatilgan barqarorlik indeksini taklif etgan; Nogueira va "
            "Braun [3] esa barqarorlikni baholashning statistik asosini keltirgan.",

            "Bizning oldingi ishimizda [4] usul 519 ta ROI'dan iborat kichik bazada sinovdan "
            "o'tkazilgan edi. Bunday hajmda barqarorlikni ishonchli o'lchash mumkin emas. "
            "Mazkur maqolada biz tahlilni **27 marta katta** bazaga — 13 968 ta o'quv ROI'ga "
            "kengaytiramiz va ikki bazani yonma-yon qo'yib, quyidagi uch savolga javob beramiz:",
        ],
        "intro_q": [
            "Tanlov protsedurasi bitta baza ichida bootstrap tebranishlariga qanchalik chidamli?",
            "Bir bazada topilgan ranjirlash boshqasiga ko'chadimi — ayniqsa uning boshi?",
            "Optimal quvvat $n'^{*}$ namuna hajmiga qanday bog'langan?",
        ],
        "intro_end":
            "Javoblar, oldindan aytganda, bir-biriga zid ko'rinadi: protsedura ichkarida juda "
            "barqaror, tashqarida esa uning eng muhim qismi — birinchi uch belgisi — ko'chib ketadi. "
            "Shu ziddiyatning izohi maqolaning asosiy hissasidir.",

        "m21":
            "Har bir ROI $I(x, y)$ kul-rang tasvir sifatida qaraladi va undan $N = 38$ ta belgi "
            "ajratiladi: 8 ta gistogramma statistikasi (o'rtacha, standart chetlanish, "
            "assimetriya, ekssess, entropiya, energiya va ikkita kvantil), $d \\in \\{1, 3\\}$ "
            "masofalar va to'rt yo'nalish uchun o'rtachalangan 24 ta GLCM ko'rsatkichi "
            "(kontrast, dissimilyarlik, bir jinslilik, energiya, korrelyatsiya, ASM) hamda 6 ta "
            "gradient belgisi (Sobel modulining o'rtachasi, standart chetlanishi, kvantillari). "
            "Barcha belgilar $z$-normallashtiriladi; normallashtirish parametrlari faqat o'quv "
            "qismidan hisoblanadi.",

        "m22_a":
            "$j$-belgi va $(k, l)$ sinflar jufti uchun sinflararo markazlar farqi $a_{j}$ va sinf "
            "ichidagi tarqoqlik $b_{j}$ quyidagicha aniqlanadi:",
        "m22_b":
            "Ularning nisbati $c_j$ belgining ajratuvchanlik quvvatini beradi, global "
            "ko'rsatkichlar esa barcha sinf juftlari bo'yicha o'rtachalanadi:",
        "m22_c":
            "Bul dasturlash masalasi $\\lambda \\in \\{0,1\\}^{N}$ vektor ustida qo'yiladi:",
        "m22_d":
            "Bu yerda $w_j$ — $j$-belgining narxi (biz uni birga teng olamiz, ya'ni faqat quvvat "
            "cheklovi qoladi). Xamdamov ko'rsatgan asosiy lemma: $\\Phi$ ning maksimumi "
            "$r_j = a_j / w_j$ bo'yicha kamayish tartibida saralangan qator prefiksida erishiladi:",
        "m22_e":
            "Demak, quvvati $n'$ bo'lgan optimal yechim shunchaki qatorning birinchi $n'$ ta "
            "elementidan iborat:",

        "m23_a":
            "Tanlangan belgilar bo'yicha $k$-sinf markazi (sentroidi) va sinf ichidagi tarqoqlik:",
        "m23_b":
            "ROI $p$ dan $k$-sinfgacha bo'lgan tarqoqlikka normallashtirilgan masofa va qaror "
            "qoidasi:",
        "m23_c":
            "$n'^{*}$ ni tanlashda **faqat o'quv qismi** ishlatiladi. Sinflar keskin nomutanosib "
            "bo'lgani uchun (eng katta sinf eng kichigidan 1900 marta ko'p) oddiy aniqlik "
            "yaroqsiz mezondir: barcha ROI'ni ko'pchilik sinfga tegishli deb e'lon qilish "
            "$0{,}679$ aniqlik beradi. Shuning uchun biz **muvozanatli aniqlik** (makro "
            "sezgirlik) bo'yicha optimallashtiramiz. Bundan tashqari, kichik sinflarda «bittasini "
            "tashlab qo'yish» (LOO) blokli krossvalidatsiya har bir blokda bitta obyektni "
            "qoldiradi, natijada blok bo'yicha aniqlik faqat 0 yoki 1 qiymat oladi va $\\pm$ "
            "standart chetlanish sun'iy ravishda $0{,}37$ atrofida chiqadi. Buning oldini olish "
            "uchun biz **birlashtirilgan (pooled)** krossvalidatsiya bashoratlarini yig'ib, "
            "ishonch oralig'ini ular ustidan bootstrap bilan quramiz.",

        "m24_a":
            "$b$-bootstrap namunada ranjirlash $\\pi_b$ ni hosil qiladi; undan quvvati $n'$ bo'lgan "
            "to'plam ajratiladi:",
        "m24_b":
            "Baza ichidagi barqarorlik ikki ko'rsatkich bilan o'lchanadi. Kuncheva indeksi "
            "kesishuvni tasodifiy kutilmaga nisbatan tuzatadi, shu sababli u $n'$ katta bo'lganda "
            "sun'iy o'sishdan himoyalangan:",
        "m24_c":
            "Jaccard koeffitsienti esa tuzatilmagan xom o'xshashlikni ko'rsatadi — ikkalasini birga "
            "keltirish tuzatishning qanchalik zarurligini ochib beradi:",
        "m24_d":
            "Har bir belgining o'rtacha o'rni va uning tebranishi qatorning qaysi qismi mustahkam "
            "ekanini aniqlaydi:",
        "m24_e":
            "Nihoyat, ikki turli bazada (kichik $s$ va katta $l$) olingan to'plamlarning kelishuvi:",

        "m3":
            "Ikkala baza ham «AISCAN» mammografiya arxivining anonimlashtirilgan qismidan olingan. "
            "Katta baza sakkiz sinf bilan belgilangan: limfa tuguni, kalsifikatsiya, o'sma, "
            "assimetriya, BIRADS 1–2, BIRADS 4–5, arxitektura buzilishi va boshqalar. Belgilar "
            "haqiqiy (ground-truth) ramkalardan ajratiladi, ya'ni tahlil detektorning sifatiga "
            "bog'liq emas — bu belgi tanlash xossalarini toza o'lchash imkonini beradi. "
            "Barcha hisob-kitoblar bir xil kodda (`boolfs` paketi), bir xil urug' bilan "
            "($\\text{seed} = 42$), 1000 ta bootstrap takrorlash bilan metrika ishonch oralig'i "
            "va 300 ta takrorlash bilan barqarorlik indekslari uchun bajarildi.",

        "r41":
            "2-jadval va 1-rasm quvvat bo'yicha o'tkazish natijalarini keltiradi. Muvozanatli "
            "aniqlik $n' = 13$ dan $n' = 21$ ga o'tishda sakrab oshadi ($0{,}410 \\to 0{,}556$), "
            "so'ng sekin to'yinadi. Krossvalidatsiya bo'yicha maksimum $n'^{*} = 36$ da erishiladi. "
            "Diqqatga sazovor tafsilot: to'liq to'plam ($n' = 38$) yuqoriroq **oddiy** aniqlik "
            "beradi ($0{,}641$ ga qarshi $0{,}596$), lekin **muvozanatli** aniqligi pastroq "
            "($0{,}623$ ga qarshi $0{,}626$). Ikki belgini olib tashlash ko'pchilik sinf foydasiga "
            "bo'lgan siljishni biroz kamaytiradi — nomutanosib bazada aynan shu muhim.",

        "r42":
            "3-jadval va 2-rasm bootstrap barqarorligini ko'rsatadi. Katta bazada Kuncheva indeksi "
            "barcha quvvatlarda $0{,}830$ dan past tushmaydi, $n' = 5$ da esa mukammal "
            "takrorlanuvchanlikka erishadi ($I_C = 1{,}000$). Kichik bazada indeks sezilarli "
            "pastroq va $n' = 34$ da $0{,}726$ gacha cho'kadi. Jaccard koeffitsienti $n'$ o'sishi "
            "bilan monoton ko'tariladi va $n' = 36$ da $0{,}995$ ga chiqadi — bu esa aynan "
            "tuzatilmagan o'lchovning aldamchiligini ko'rsatadi: 38 tadan 36 tasi tanlanganda "
            "istalgan ikki to'plam deyarli albatta ustma-ust tushadi. Kuncheva indeksi bu "
            "artefaktni yo'qotadi, shu sababli barqarorlik haqidagi barcha xulosalar faqat unga "
            "asoslanishi kerak.",

        "r43":
            "Endi asosiy natijaga o'tamiz. To'liq ranjirlangan qatorlar ikki bazada bir-biriga "
            "juda mos: Spirmen korrelyatsiyasi $\\rho = 0{,}937$ ($N = 38$). Bu «usul barqaror» "
            "degan xulosaga olib kelishi mumkin edi. Lekin qatorning **boshiga** qaralsa, manzara "
            "teskari: top-3 to'plamlarining kelishuvi $A_{s,l} = 0{,}333$ — ya'ni uchtadan atigi "
            "bittasi umumiy ($\\texttt{grad\\_sobel\\_std}$). Top-5 da kelishuv $0{,}600$ ga, "
            "top-8 da $0{,}875$ ga ko'tariladi (3-jadvalning oxirgi ustuni).",
        "r43b":
            "4-jadval va 3-rasm buning sababini ochadi. Kichik bazada birinchi ikki o'rinni "
            "GLCM korrelyatsiyasi egallaydi ($\\bar{r} = 1{,}33 \\pm 0{,}47$ va "
            "$1{,}79 \\pm 0{,}59$), katta bazada esa u umuman birinchi beshlikka kirmaydi; "
            "uning o'rniga Sobel gradientining standart chetlanishi mutlaq yetakchiga aylanadi "
            "($\\bar{r} = 1{,}00 \\pm 0{,}00$ — 300 ta bootstrapning barchasida birinchi o'rin). "
            "Izohi fiziologik: kichik namunada korrelyatsiya belgilari sinflar orasidagi tasodifiy "
            "farqni ushlaydi va bu farq shovqin darajasida barqaror ko'rinadi; namuna kengayganda "
            "esa haqiqiy ajratuvchi omil — chegara o'tkirligi (gradient tarqoqligi) — ustunlik "
            "qiladi. Ya'ni kichik bazadagi «barqaror» yetakchi aslida namunaga xos artefakt edi.",
        "r43c":
            "Bu ikki qatlamning birga turishi (baza ichida $I_C \\approx 0{,}9$, bazalar orasida "
            "top-3 kelishuvi $0{,}33$) ziddiyat emas: bootstrap namunalari bitta taqsimotdan "
            "olinadi, shuning uchun ular ichidagi barqarorlik faqat **statistik** dispersiyani "
            "o'lchaydi. Bazalarni almashtirish esa taqsimotning o'zini o'zgartiradi va "
            "**epistemik** noaniqlikni ochadi. Bootstrap barqarorligi yuqori bo'lishi belgilar "
            "ro'yxatining ko'chib o'tishiga kafolat bermaydi — bu amaliy xulosaning eng muhimi.",

        "r44":
            "4-rasm $\\Phi(n')$ prefiks funksionalining kamayuvchi zanjirini ko'rsatadi: "
            "$\\Phi(1) = 6{,}27$ dan $\\Phi(38) = 1{,}04$ gacha. Kamayish qat'iy monoton — bu "
            "$r_j$ bo'yicha saralashning bevosita natijasi va lemmani empirik tasdiqlaydi. Egri "
            "chiziqning tirsagi $n' \\approx 21$ atrofida: shu nuqtadan keyin qo'shilgan har bir "
            "belgi o'rtacha informativlikni sezilarli pasaytiradi, ammo muvozanatli aniqlik hali "
            "ham o'sishda davom etadi. Bu ikki mezon o'rtasidagi farq — informativlik va "
            "klassifikatsiya foydasi bir xil narsa emasligini eslatadi: kam informativ belgi ham "
            "boshqalar bilan birgalikda kichik sinfni ajratishga yordam berishi mumkin.",

        "d1":
            "Olingan natijalar bir necha metodologik xulosani majburiy qiladi. **Birinchidan**, "
            "belgi tanlash haqidagi har qanday nashrda barqarorlik ko'rsatkichi keltirilishi shart, "
            "va u tasodifga tuzatilgan bo'lishi lozim: biz ko'rsatdikki, Jaccard koeffitsienti "
            "$n'$ katta bo'lganda $0{,}99$ ga chiqib, «mukammal barqarorlik» taassurotini "
            "yaratadi — aslida esa bu shunchaki to'plamlarning to'lib ketishi.",
        "d2":
            "**Ikkinchidan**, kichik namunada olingan belgi reytingi hech qachon «eng informativ "
            "belgilar ro'yxati» sifatida umumlashtirilmasligi kerak. Bizning holatda "
            "519 ta ROI yetarlicha ko'p ko'rinadi (aksariyat nashrlarda undan kam), biroq uning "
            "top-3 si 13 968 ROI'dagi top-3 bilan atigi 33% mos keldi. Bu radiomika sohasidagi "
            "takrorlanuvchanlik inqiroziga bevosita aloqador: turli maqolalarda «eng muhim» "
            "deb e'lon qilingan tekstura belgilari bir-biriga zid bo'lishining bir sababi shu.",
        "d3":
            "**Uchinchidan**, optimal quvvat $n'^{*}$ namuna hajmi bilan o'sadi ($34 \\to 36$), "
            "chunki katta namunada ko'proq belgining kovariatsiya tuzilmasini ishonchli baholash "
            "mumkin bo'ladi. Shu bilan birga o'sish sekin: hajmni 27 marta oshirish quvvatga atigi "
            "ikki belgi qo'shdi. Demak, $n'^{*}$ namunaga nisbatan zaif sezgir parametr — bu "
            "usulning amaliy afzalligi.",
        "d4":
            "**Cheklovlar.** Tahlil bitta markaz arxivi bilan chegaralangan; qurilmalararo "
            "(multi-scanner) o'zgaruvchanlik o'lchanmagan. Belgilar to'plami qo'lda "
            "loyihalangan 38 ta ko'rsatkich bilan cheklangan; chuqur tarmoq embeddinglari uchun "
            "$r_j$ ranjirlashining xossalari alohida tekshirilishi kerak. Nihoyat, "
            "eng kam ta'minlangan sinflarda (arxitektura buzilishi — 13 ta ROI) barqarorlik "
            "baholari kuchsiz statistik quvvatga ega.",

        "c": [
            "Bul dasturlash asosidagi belgi tanlash usuli ikki tartibga farq qiluvchi hajmdagi "
            "mammografik bazalarda ilk marta qiyoslandi. Prefiks lemmasi empirik tasdiqlandi: "
            "$\\Phi(n')$ qat'iy kamayuvchi zanjir hosil qiladi.",
            "Protsedura bitta baza ichida yuqori takrorlanuvchanlikka ega — katta bazada Kuncheva "
            "indeksi barcha quvvatlarda $0{,}830$ dan yuqori.",
            "Bazalar o'rtasida to'liq qator mos keladi ($\\rho = 0{,}937$), lekin ranjirlash boshi "
            "ko'chadi: top-3 kelishuvi $0{,}333$. Kichik bazadagi yetakchi (GLCM korrelyatsiyasi) "
            "katta bazada birinchi beshlikdan tushib qoladi.",
            "Optimal quvvat namuna hajmiga zaif bog'liq: $n'^{*}$ $34$ dan $36$ ga siljidi; "
            "katta bazada muvozanatli aniqlik $0{,}638$ [0,606; 0,762], makro ROC-AUC "
            "$0{,}947$ [0,928; 0,960].",
            "Amaliy tavsiya: belgi reytingini nashr etishda uni olingan namuna hajmi bilan birga "
            "keltirish, tasodifga tuzatilgan barqarorlik indeksini hisoblash va reytingning boshini "
            "mustaqil bazada tasdiqlamasdan turib «universal» deb atamaslik kerak.",
        ],
    },
}

import m1_body_i18n as _i18n  # noqa: E402
BODY.update(_i18n.BODY)

REFS = [
    "Хамдамов Н.Х. Метод отбора информативных признаков на основе булева программирования // "
    "Проблемы вычислительной и прикладной математики. — 2017. — № 4(10). — С. 63–71.",
    "Kuncheva L.I. A stability index for feature selection // Proc. 25th IASTED Int. Conf. on "
    "Artificial Intelligence and Applications. — 2007. — P. 390–395.",
    "Nogueira S., Sechidis K., Brown G. On the stability of feature selection algorithms // "
    "Journal of Machine Learning Research. — 2018. — Vol. 18, No. 174. — P. 1–54.",
    "Turaqulov A., Khamdamov N. Boolean feature selection and a minimum-distance classifier for "
    "mammographic ROI analysis // Materials of the Republican scientific conference. — Tashkent, "
    "2026. — P. 41–48.",
    "Haralick R.M., Shanmugam K., Dinstein I. Textural features for image classification // "
    "IEEE Transactions on Systems, Man, and Cybernetics. — 1973. — Vol. SMC-3, No. 6. — P. 610–621.",
    "Zwanenburg A. et al. The Image Biomarker Standardisation Initiative: standardised quantitative "
    "radiomics for high-throughput image-based phenotyping // Radiology. — 2020. — Vol. 295, "
    "No. 2. — P. 328–338.",
    "Efron B., Tibshirani R.J. An Introduction to the Bootstrap. — New York: Chapman & Hall, "
    "1993. — 436 p.",
    "Brodersen K.H., Ong C.S., Stephan K.E., Buhmann J.M. The balanced accuracy and its posterior "
    "distribution // Proc. 20th Int. Conf. on Pattern Recognition (ICPR). — 2010. — P. 3121–3124.",
    "Guyon I., Elisseeff A. An introduction to variable and feature selection // Journal of "
    "Machine Learning Research. — 2003. — Vol. 3. — P. 1157–1182.",
    "Traverso A. et al. Repeatability and reproducibility of radiomic features: a systematic "
    "review // Int. Journal of Radiation Oncology, Biology, Physics. — 2018. — Vol. 102, "
    "No. 4. — P. 1143–1158.",
]


# ═══════════════════════════════ jadvallar ═══════════════════════════════ #

def t1_rows(lang, art, small, stab):
    L = {"uz": ["ROI soni (o'quv)", "ROI soni (baholash)", "Sinflar soni", "Belgilar soni $N$",
                "Tanlangan quvvat $n'^{*}$", "Rasm o'lchami", "Bootstrap takrorlash"],
         "ru": ["Число ROI (обучение)", "Число ROI (оценка)", "Число классов", "Число признаков $N$",
                "Выбранная мощность $n'^{*}$", "Размер изображения", "Бутстреп-повторений"],
         "en": ["ROIs (training)", "ROIs (evaluation)", "Classes", "Features $N$",
                "Selected cardinality $n'^{*}$", "Image size", "Bootstrap replicates"]}[lang]
    v = [(K.INT(stab["small"]["n_roi"], lang), K.INT(art["n_roi_train"], lang)),
         ("—", K.INT(art["n_roi_val"], lang)),
         ("6", "8"), ("38", "38"),
         (str(small["n_star"]), str(art["n_star"])),
         ("640 × 640", "1280 × 1280"), ("300", "300")]
    return [[L[i], v[i][0], v[i][1]] for i in range(len(L))]


def t2_rows(lang, art):
    rows = []
    for r in art["nsweep"]:
        if r["n"] not in (1, 3, 5, 8, 13, 21, 28, 34, 36, 38):
            continue
        star = "*" if r["n"] == art["n_star"] else ""
        rows.append([f"{r['n']}{star}",
                     K.CI(r["cv_acc"], {"lo": r["cv_acc_lo"], "hi": r["cv_acc_hi"]}, lang),
                     K.CI(r["cv_bacc"], {"lo": r["cv_bacc_lo"], "hi": r["cv_bacc_hi"]}, lang),
                     K.N(r["val_acc"], lang), K.N(r["val_bacc"], lang), K.N(r["val_auc"], lang)])
    return rows


def t3_rows(lang, stab, agr):
    big = {l["n"]: l for l in stab["big"]["levels"]}
    sm = {l["n"]: l for l in stab["small"]["levels"]}
    ag = {int(k): v for k, v in agr["agreement"].items()}
    return [[str(n), K.N(big[n]["kuncheva"], lang), K.N(big[n]["jaccard"], lang),
             K.N(sm[n]["kuncheva"], lang), K.N(sm[n]["jaccard"], lang), K.N(ag[n], lang)]
            for n in N_LIST]


def t4_rows(lang, stab):
    b, s = stab["big"]["top_ranks"], stab["small"]["top_ranks"]
    rows = []
    for i in range(5):
        rows.append([str(i + 1), fname(b[i]["feature"]),
                     f"{K.N(b[i]['mean_rank'], lang, 2)} ± {K.N(b[i]['std_rank'], lang, 2)}",
                     fname(s[i]["feature"]),
                     f"{K.N(s[i]['mean_rank'], lang, 2)} ± {K.N(s[i]['std_rank'], lang, 2)}"])
    return rows


def t5_rows(lang, art):
    return [[str(t["n"]), fname(t["feature"]), K.N(t["r_j"], lang), K.N(t["phi_prefix"], lang)]
            for t in art["selection_table"][:8]]


# ═════════════════════════════════ qurish ════════════════════════════════ #

def build(lang, art, stab, agr, small):
    t = T[lang]
    b = BODY[lang]
    fig = ASSETS / lang
    doc = Document()
    K.setup(doc)

    K.title(doc, t["title"])
    K.authors(doc, t["authors"])
    K.abstract(doc, t["abs_l"], t["abs"], t["kw_l"], t["kw"])

    # 1. Kirish
    K.heading(doc, t["h1"])
    for p in b["intro"]:
        K.para(doc, p)
    for i, q in enumerate(b["intro_q"], 1):
        K.para(doc, f"**({i})** {q}", first_indent=True)
    K.para(doc, b["intro_end"])

    # 2. Usul
    K.heading(doc, t["h2"])
    K.subheading(doc, t["h21"])
    K.para(doc, b["m21"])

    K.subheading(doc, t["h22"])
    K.para(doc, b["m22_a"])
    add_equation(doc, *F.eq_a(), number=1)
    add_equation(doc, *F.eq_b(), number=2)
    K.para(doc, b["m22_b"])
    add_equation(doc, *F.eq_c(), number=3)
    K.para(doc, b["m22_c"])
    add_equation(doc, *F.eq_phi(), number=4)
    K.para(doc, b["m22_d"])
    add_equation(doc, *F.eq_rank(), number=5)
    K.para(doc, b["m22_e"])
    add_equation(doc, *F.eq_nstar(), number=6)

    K.subheading(doc, t["h23"])
    K.para(doc, b["m23_a"])
    add_equation(doc, *F.eq_centroid(), number=7)
    add_equation(doc, *F.eq_scatter(), number=8)
    K.para(doc, b["m23_b"])
    add_equation(doc, *F.eq_rho(), number=9)
    add_equation(doc, *F.eq_decision(), number=10)
    K.para(doc, b["m23_c"])

    K.subheading(doc, t["h24"])
    K.para(doc, b["m24_a"])
    add_equation(doc, *X.eq_subset(), number=11)
    K.para(doc, b["m24_b"])
    add_equation(doc, *X.eq_kuncheva(), number=12)
    K.para(doc, b["m24_c"])
    add_equation(doc, *X.eq_jaccard(), number=13)
    K.para(doc, b["m24_d"])
    add_equation(doc, *X.eq_meanrank(), number=14)
    K.para(doc, b["m24_e"])
    add_equation(doc, *X.eq_agreement(), number=15)

    # 3. Sozlamalar
    K.heading(doc, t["h3"])
    K.para(doc, b["m3"])
    K.caption(doc, t["t1_cap"], before=True)
    K.table(doc, t["t1_h"], t1_rows(lang, art, small, stab))

    # 4. Natijalar
    K.heading(doc, t["h4"])
    K.subheading(doc, t["h41"])
    K.para(doc, b["r41"])
    K.caption(doc, t["t2_cap"], before=True)
    K.table(doc, t["t2_h"], t2_rows(lang, art), size=8.0)
    K.picture(doc, fig / "m1_f1_nsweep.png", t["f1_cap"])

    K.subheading(doc, t["h42"])
    K.para(doc, b["r42"])
    K.caption(doc, t["t3_cap"], before=True)
    K.table(doc, t["t3_h"], t3_rows(lang, stab, agr), size=8.5, first_left=False)
    K.picture(doc, fig / "m1_f2_stability.png", t["f2_cap"])

    K.subheading(doc, t["h43"])
    K.para(doc, b["r43"])
    K.para(doc, b["r43b"])
    K.caption(doc, t["t4_cap"], before=True)
    K.table(doc, t["t4_h"], t4_rows(lang, stab), size=8.0, first_left=False)
    K.picture(doc, fig / "m1_f3_ranking.png", t["f3_cap"])
    K.para(doc, b["r43c"])

    K.subheading(doc, t["h44"])
    K.para(doc, b["r44"])
    K.caption(doc, t["t5_cap"], before=True)
    K.table(doc, t["t5_h"], t5_rows(lang, art), size=8.5, first_left=False)
    K.picture(doc, fig / "m1_f4_phi.png", t["f4_cap"])

    # 5. Muhokama
    K.heading(doc, t["h5"])
    for k in ("d1", "d2", "d3", "d4"):
        K.para(doc, b[k])

    # 6. Xulosa
    K.heading(doc, t["h6"])
    for i, c in enumerate(b["c"], 1):
        K.para(doc, f"**{i}.** {c}")

    K.refs(doc, t["refs_l"], REFS)
    return doc


def main():
    art, stab, agr, small = load()
    langs = sys.argv[1:] or ["uz", "ru", "en"]
    for lg in langs:
        doc = build(lg, art, stab, agr, small)
        out = ROOT / f"MAMOGRAF_Maqola_2026_M1_Barqarorlik_{lg.upper()}.docx"
        doc.save(out)
        print(f"[m1] {lg}: {out}")


if __name__ == "__main__":
    main()
