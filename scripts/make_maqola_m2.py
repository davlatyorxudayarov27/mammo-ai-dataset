# -*- coding: utf-8 -*-
"""make_maqola_m2.py — 2-MAQOLA: chuqur detektor va bul-dasturlash klassifikatorining
gibrid ansambli; ma'lumot sizishi nazorati bilan halol baholash (amaliy).

Uch tilda (uz/ru/en), barcha formulalar Word-native OMML (MathType-mos).
Chiqish: MAMOGRAF_Maqola_2026_M2_Ansambl_{UZ,RU,EN}.docx
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
ASSETS = ROOT / "doc_assets_big"
BEST = "trained_8class_ai_v2_ep50"
ORDER = ["yolo11s_8class", "trained_8class_yolo11l", BEST]

CLS = {
    "uz": {"BIRADS12": "BIRADS 1–2", "BIRADS45": "BIRADS 4–5",
           "architectural_distortion": "arxitektura buzilishi", "asymmetry": "assimetriya",
           "calcification": "kalsifikatsiya", "lymph_node": "limfa tuguni", "mass": "o'sma",
           "other": "boshqa"},
    "ru": {"BIRADS12": "BIRADS 1–2", "BIRADS45": "BIRADS 4–5",
           "architectural_distortion": "архит. перестройка", "asymmetry": "асимметрия",
           "calcification": "кальцификация", "lymph_node": "лимфоузел", "mass": "образование",
           "other": "прочее"},
    "en": {"BIRADS12": "BIRADS 1–2", "BIRADS45": "BIRADS 4–5",
           "architectural_distortion": "architectural distortion", "asymmetry": "asymmetry",
           "calcification": "calcification", "lymph_node": "lymph node", "mass": "mass",
           "other": "other"},
}

MET_KEYS = ["accuracy", "balanced_accuracy", "sensitivity_macro", "specificity_macro",
            "precision_macro", "f1_macro", "auc_macro", "mcc", "kappa"]

MET_L = {
    "uz": ["Aniqlik (accuracy)", "Muvozanatli aniqlik", "Sezgirlik (makro)",
           "O'ziga xoslik (makro)", "Aniqlik-precision (makro)", "F1 (makro)",
           "ROC-AUC (makro)", "MCC", "Koen $\\kappa$"],
    "ru": ["Точность (accuracy)", "Сбалансированная точность", "Чувствительность (макро)",
           "Специфичность (макро)", "Точность-precision (макро)", "F1 (макро)",
           "ROC-AUC (макро)", "MCC", "Каппа Коэна"],
    "en": ["Accuracy", "Balanced accuracy", "Sensitivity (macro)", "Specificity (macro)",
           "Precision (macro)", "F1 (macro)", "ROC-AUC (macro)", "MCC", "Cohen's $\\kappa$"],
}


def load():
    met = json.loads((BIG / "metrics/metrics.json").read_text())
    art = json.loads((BIG / "artifacts.json").read_text())
    iou = json.loads((BIG / "iou_sensitivity.json").read_text())
    return met, art, iou


T = {
    "uz": {
        "title": "Chuqur detektor va bul-dasturlash klassifikatorining gibrid ansambli: "
                 "nomutanosib mammografik bazada ma'lumot sizishini nazorat qilgan holda "
                 "halol baholash",
        "authors": ["A. Turaqulov", "Ilmiy rahbar: prof. N. Xamdamov",
                    "Muhammad al-Xorazmiy nomidagi Toshkent axborot texnologiyalari universiteti"],
        "abs_l": "Annotatsiya.",
        "abs": "YOLO11 detektorining ishonch bahosi bilan Xamdamov (2017) bul-dasturlash usuli "
               "asosidagi minimal masofa klassifikatori chiqishi $z_p = \\alpha u_p + "
               "(1 - \\alpha) s_p$ ko'rinishida birlashtirilib, 13 968 o'quv va 2 359 baholash "
               "ROI'sidan iborat sakkiz sinfli mammografik bazada sinovdan o'tkazildi. Ish uch "
               "metodologik talabga qat'iy amal qiladi: (i) ansambl vazni $\\alpha^{*}$ **faqat "
               "o'quv qismida** tanlanadi; (ii) uchta detektordan ikkitasi eski bazada o'qitilgani "
               "aniqlangach, yangi baholash to'plamining 24 ta rasmi ular uchun **ma'lumot sizishi** "
               "manbai ekani ko'rsatildi va barcha metrikalar tozalangan qismda hisoblandi; "
               "(iii) har bir metrika 95% bootstrap ishonch oralig'i, ansambl−detektor farqi esa "
               "juftlashgan bootstrap va ikki tomonlama $p$-qiymat bilan keltiriladi. Sizishdan "
               "toza detektorda ansambl muvozanatli aniqlikni $0{,}640$ dan $0{,}692$ ga "
               "($\\Delta = +5{,}2$ f.p., $p = 0{,}036$) va makro ROC-AUC ni $0{,}897$ dan "
               "$0{,}976$ ga ($\\Delta = +7{,}9$ f.p., $p < 0{,}001$) oshirdi; oddiy aniqlikning "
               "pasayishi statistik ahamiyatsiz ($0{,}923 \\to 0{,}915$, $p = 0{,}074$). Foyda "
               "to'liq kam ta'minlangan sinflar hisobiga: BIRADS 1–2 sezgirligi "
               "$0{,}667 \\to 0{,}833$, assimetriya $0{,}429 \\to 0{,}571$. Sizishga uchragan "
               "detektorlarda esa ansambl aniqlikni ahamiyatli darajada pasaytiradi "
               "($p < 0{,}001$) — bu «ansambl har doim foyda beradi» degan qarashni rad etadi va "
               "sizish nazoratining zarurligini ko'rsatadi.",
        "kw_l": "Kalit so'zlar:",
        "kw": "mammografiya, YOLO11, ansambl, bul dasturlash, ma'lumot sizishi, muvozanatli "
              "aniqlik, ROC-AUC, juftlashgan bootstrap, nomutanosib sinflar.",
        "h1": "1. Kirish",
        "h2": "2. Usul",
        "h21": "2.1. Ikki oqim",
        "h22": "2.2. Detektsiya va haqiqiy ramkalarni moslashtirish",
        "h23": "2.3. Ehtimollik vektorlari va ansambl",
        "h24": "2.4. $\\alpha^{*}$ ni halol tanlash",
        "h25": "2.5. Baholash metrikalari",
        "h26": "2.6. Statistik xulosa chiqarish",
        "h3": "3. Ma'lumot sizishi va uni nazorat qilish",
        "h4": "4. Natijalar",
        "h41": "4.1. Ansambl vaznining tanlanishi",
        "h42": "4.2. Asosiy metrikalar",
        "h43": "4.3. ROC tahlili",
        "h44": "4.4. Sinflar bo'yicha tahlil",
        "h45": "4.5. Uch detektor va sizishning ta'siri",
        "h46": "4.6. Moslashtirish chegarasi $\\text{IoU}$ ga sezuvchanlik",
        "h5": "5. Muhokama",
        "h6": "6. Xulosa",
        "refs_l": "Adabiyotlar",
        "t1_cap": "1-jadval. Baholashda qatnashgan uch detektor va ular uchun aniqlangan "
                  "ma'lumot sizishi",
        "t1_h": ["Detektor", "O'qitilgan baza", "Bashorat", "Mos ROI", "Sizgan ROI",
                 "Toza ROI", "$\\alpha^{*}$"],
        "t2_cap": "2-jadval. Sizishdan toza baholash to'plamida (YOLO11l-v2, $n = 2088$) "
                  "asosiy metrikalar, 95% bootstrap ishonch oralig'i bilan",
        "t2_h": ["Metrika", "Faqat boolfs", "Faqat YOLO", "Ansambl"],
        "t3_cap": "3-jadval. Ansambl va yakka detektor orasidagi farq $\\Delta$ "
                  "(juftlashgan bootstrap, 1000 takrorlash; f.p. — foizli punkt)",
        "t3_h": ["Metrika", "$\\Delta$, f.p.", "95% CI", "$p$", "Xulosa"],
        "t4_cap": "4-jadval. Sinflar kesimida sezgirlik, o'ziga xoslik va ROC-AUC "
                  "(YOLO → Ansambl)",
        "t4_h": ["Sinf", "$n$", "Sezgirlik", "O'ziga xoslik", "Precision", "F1",
                 "AUC (ansambl)"],
        "t5_cap": "5-jadval. Uchala detektor uchun ansamblning ta'siri (sizishdan tozalangan "
                  "to'plamda)",
        "t5_h": ["Detektor", "$\\alpha^{*}$", "Aniqlik", "$p$", "Muv. aniqlik", "$p$", "AUC"],
        "t6_cap": "6-jadval. Ma'lumot sizishining o'lchangan ta'siri: tozalanmagan va tozalangan "
                  "baholash to'plamlari",
        "t6_h": ["Detektor", "Aniqlik (to'liq)", "Aniqlik (toza)", "Farq",
                 "Muv. aniqlik (to'liq)", "Muv. aniqlik (toza)", "Farq"],
        "t7_cap": "7-jadval. Moslashtirish chegarasiga sezuvchanlik: butun oqim (moslashtirish → "
                  "$\\alpha^{*}$ ni train'da tanlash → tozalangan val'da baholash) uch chegarada "
                  "qaytadan bajarildi. $\\Delta$ — ansambl minus yakka detektor, foizli punktda.",
        "t7_h": ["Detektor", "$\\text{IoU}$", "$n$", "$\\alpha^{*}$", "$\\Delta$ aniqlik",
                 "$\\Delta$ muv. aniqlik", "$\\Delta$ AUC"],
        "f1_cap": "1-rasm. Muvozanatli aniqlikning ansambl vazni $\\alpha$ ga bog'liqligi. "
                  "$\\alpha^{*}$ faqat o'quv egrisi (punktir) bo'yicha tanlanadi; baholash "
                  "egrisi (to'ldirilgan) mustaqil qoladi.",
        "f2_cap": "2-rasm. Makro ROC egri chiziqlari (sizishdan toza baholash to'plami). "
                  "Ansambl ikkala yakka oqimdan ham ustun.",
        "f3_cap": "3-rasm. Sinflar bo'yicha sezgirlik: yakka YOLO va ansambl. Foyda butunlay "
                  "kam ta'minlangan sinflarda to'plangan.",
        "f4_cap": "4-rasm. Chalkashlik matritsasi (ansambl, satrlar bo'yicha normallashtirilgan).",
        "f5_cap": "5-rasm. Ma'lumot sizishining ta'siri: tozalangan va tozalanmagan baholash "
                  "to'plamlarida aniqlik. Eski bazada o'qitilgan detektorlar tozalanmagan "
                  "to'plamda yuqoriroq ko'rsatkich beradi.",
        "yes_": "ahamiyatli",
        "no_": "ahamiyatsiz",
        "trained_old": "eski (445-baza)",
        "trained_new": "shu baza",
    },
    "ru": {
        "title": "Гибридный ансамбль глубокого детектора и классификатора на основе булева "
                 "программирования: честная оценка на несбалансированной маммографической базе "
                 "с контролем утечки данных",
        "authors": ["А. Туракулов", "Научный руководитель: проф. Н. Хамдамов",
                    "Ташкентский университет информационных технологий имени Мухаммада аль-Хорезми"],
        "abs_l": "Аннотация.",
        "abs": "Оценка уверенности детектора YOLO11 и выход классификатора минимального "
               "расстояния, построенного на методе булева программирования Хамдамова (2017), "
               "объединены в виде $z_p = \\alpha u_p + (1 - \\alpha) s_p$ и испытаны на "
               "восьмиклассовой маммографической базе из 13 968 обучающих и 2 359 оценочных ROI. "
               "Работа строго следует трём методологическим требованиям: (i) вес ансамбля "
               "$\\alpha^{*}$ подбирается **только на обучающей части**; (ii) после того как "
               "выяснилось, что два детектора из трёх обучались на старой базе, было показано, что "
               "24 изображения нового оценочного набора являются для них источником **утечки "
               "данных**, и все метрики вычислены на очищенной части; (iii) каждая метрика "
               "приводится с 95% бутстреп-доверительным интервалом, а разность ансамбль−детектор — "
               "с парным бутстрепом и двусторонним $p$-значением. На свободном от утечки детекторе "
               "ансамбль повысил сбалансированную точность с $0{,}640$ до $0{,}692$ "
               "($\\Delta = +5{,}2$ п.п., $p = 0{,}036$) и макро ROC-AUC с $0{,}897$ до $0{,}976$ "
               "($\\Delta = +7{,}9$ п.п., $p < 0{,}001$); снижение обычной точности статистически "
               "незначимо ($0{,}923 \\to 0{,}915$, $p = 0{,}074$). Выигрыш полностью обеспечен "
               "малочисленными классами: чувствительность BIRADS 1–2 $0{,}667 \\to 0{,}833$, "
               "асимметрии $0{,}429 \\to 0{,}571$. На детекторах же, затронутых утечкой, ансамбль "
               "значимо снижает точность ($p < 0{,}001$) — это опровергает представление, будто "
               "«ансамбль всегда полезен», и демонстрирует необходимость контроля утечки.",
        "kw_l": "Ключевые слова:",
        "kw": "маммография, YOLO11, ансамбль, булево программирование, утечка данных, "
              "сбалансированная точность, ROC-AUC, парный бутстреп, несбалансированные классы.",
        "h1": "1. Введение",
        "h2": "2. Метод",
        "h21": "2.1. Два потока",
        "h22": "2.2. Сопоставление детекций и истинных рамок",
        "h23": "2.3. Векторы вероятностей и ансамбль",
        "h24": "2.4. Честный выбор $\\alpha^{*}$",
        "h25": "2.5. Метрики оценивания",
        "h26": "2.6. Статистический вывод",
        "h3": "3. Утечка данных и её контроль",
        "h4": "4. Результаты",
        "h41": "4.1. Подбор веса ансамбля",
        "h42": "4.2. Основные метрики",
        "h43": "4.3. ROC-анализ",
        "h44": "4.4. Анализ по классам",
        "h45": "4.5. Три детектора и влияние утечки",
        "h46": "4.6. Чувствительность к порогу сопоставления $\\text{IoU}$",
        "h5": "5. Обсуждение",
        "h6": "6. Заключение",
        "refs_l": "Литература",
        "t1_cap": "Таблица 1. Три детектора, участвовавшие в оценке, и выявленная для них утечка "
                  "данных",
        "t1_h": ["Детектор", "База обучения", "Предсказаний", "Сопост. ROI", "С утечкой",
                 "Чистых ROI", "$\\alpha^{*}$"],
        "t2_cap": "Таблица 2. Основные метрики на очищенном оценочном наборе (YOLO11l-v2, "
                  "$n = 2088$) с 95% бутстреп-доверительными интервалами",
        "t2_h": ["Метрика", "Только boolfs", "Только YOLO", "Ансамбль"],
        "t3_cap": "Таблица 3. Разность $\\Delta$ между ансамблем и одиночным детектором "
                  "(парный бутстреп, 1000 повторений; п.п. — процентный пункт)",
        "t3_h": ["Метрика", "$\\Delta$, п.п.", "95% CI", "$p$", "Вывод"],
        "t4_cap": "Таблица 4. Чувствительность, специфичность и ROC-AUC в разрезе классов "
                  "(YOLO → Ансамбль)",
        "t4_h": ["Класс", "$n$", "Чувствительность", "Специфичность", "Precision", "F1",
                 "AUC (ансамбль)"],
        "t5_cap": "Таблица 5. Влияние ансамбля для всех трёх детекторов (на очищенном наборе)",
        "t5_h": ["Детектор", "$\\alpha^{*}$", "Точность", "$p$", "Сбал. точность", "$p$", "AUC"],
        "t6_cap": "Таблица 6. Измеренное влияние утечки данных: неочищенный и очищенный "
                  "оценочные наборы",
        "t6_h": ["Детектор", "Точность (полн.)", "Точность (чист.)", "Разн.",
                 "Сбал. точн. (полн.)", "Сбал. точн. (чист.)", "Разн."],
        "t7_cap": "Таблица 7. Чувствительность к порогу сопоставления: весь конвейер "
                  "(сопоставление → подбор $\\alpha^{*}$ на train → оценка на очищенном val) "
                  "выполнен заново при трёх порогах. $\\Delta$ — ансамбль минус одиночный "
                  "детектор, в процентных пунктах.",
        "t7_h": ["Детектор", "$\\text{IoU}$", "$n$", "$\\alpha^{*}$", "$\\Delta$ точность",
                 "$\\Delta$ сбал. точность", "$\\Delta$ AUC"],
        "f1_cap": "Рис. 1. Зависимость сбалансированной точности от веса ансамбля $\\alpha$. "
                  "$\\alpha^{*}$ выбирается только по обучающей кривой (пунктир); оценочная кривая "
                  "(сплошная) остаётся независимой.",
        "f2_cap": "Рис. 2. Макро ROC-кривые (очищенный оценочный набор). Ансамбль превосходит оба "
                  "одиночных потока.",
        "f3_cap": "Рис. 3. Чувствительность по классам: одиночный YOLO и ансамбль. Выигрыш целиком "
                  "сосредоточен в малочисленных классах.",
        "f4_cap": "Рис. 4. Матрица ошибок (ансамбль, нормирована по строкам).",
        "f5_cap": "Рис. 5. Влияние утечки данных: точность на очищенном и неочищенном оценочных "
                  "наборах. Детекторы, обученные на старой базе, показывают более высокий "
                  "результат на неочищенном наборе.",
        "yes_": "значимо",
        "no_": "незначимо",
        "trained_old": "старая (база 445)",
        "trained_new": "эта база",
    },
    "en": {
        "title": "A hybrid ensemble of a deep detector and a Boolean-programming classifier: "
                 "honest evaluation on an imbalanced mammographic database with data-leakage "
                 "control",
        "authors": ["A. Turaqulov", "Supervisor: Prof. N. Khamdamov",
                    "Tashkent University of Information Technologies named after Muhammad al-Khwarizmi"],
        "abs_l": "Abstract.",
        "abs": "The confidence score of a YOLO11 detector and the output of a minimum-distance "
               "classifier built on Khamdamov's (2017) Boolean programming method are combined as "
               "$z_p = \\alpha u_p + (1 - \\alpha) s_p$ and evaluated on an eight-class "
               "mammographic database of 13,968 training and 2,359 evaluation ROIs. The study "
               "adheres strictly to three methodological requirements: (i) the ensemble weight "
               "$\\alpha^{*}$ is selected on the **training partition only**; (ii) having "
               "established that two of the three detectors were trained on an older database, we "
               "show that 24 images of the new evaluation set constitute a **data-leakage** source "
               "for them, and all metrics are computed on the cleaned subset; (iii) every metric is "
               "reported with a 95% bootstrap confidence interval, and the ensemble−detector "
               "difference with a paired bootstrap and a two-sided $p$-value. On the leakage-free "
               "detector the ensemble raised balanced accuracy from $0.640$ to $0.692$ "
               "($\\Delta = +5.2$ p.p., $p = 0.036$) and macro ROC-AUC from $0.897$ to $0.976$ "
               "($\\Delta = +7.9$ p.p., $p < 0.001$); the decrease in plain accuracy is "
               "statistically insignificant ($0.923 \\to 0.915$, $p = 0.074$). The gain is derived "
               "entirely from the under-represented classes: BIRADS 1–2 sensitivity "
               "$0.667 \\to 0.833$, asymmetry $0.429 \\to 0.571$. On the leakage-affected "
               "detectors, by contrast, the ensemble significantly lowers accuracy "
               "($p < 0.001$) — refuting the notion that «an ensemble always helps» and "
               "demonstrating the necessity of leakage control.",
        "kw_l": "Keywords:",
        "kw": "mammography, YOLO11, ensemble, Boolean programming, data leakage, balanced "
              "accuracy, ROC-AUC, paired bootstrap, imbalanced classes.",
        "h1": "1. Introduction",
        "h2": "2. Method",
        "h21": "2.1. The two streams",
        "h22": "2.2. Matching detections to ground-truth boxes",
        "h23": "2.3. Probability vectors and the ensemble",
        "h24": "2.4. Honest selection of $\\alpha^{*}$",
        "h25": "2.5. Evaluation metrics",
        "h26": "2.6. Statistical inference",
        "h3": "3. Data leakage and its control",
        "h4": "4. Results",
        "h41": "4.1. Selection of the ensemble weight",
        "h42": "4.2. Principal metrics",
        "h43": "4.3. ROC analysis",
        "h44": "4.4. Per-class analysis",
        "h45": "4.5. Three detectors and the effect of leakage",
        "h46": "4.6. Sensitivity to the matching threshold $\\text{IoU}$",
        "h5": "5. Discussion",
        "h6": "6. Conclusion",
        "refs_l": "References",
        "t1_cap": "Table 1. The three detectors used in the evaluation and the data leakage "
                  "identified for each",
        "t1_h": ["Detector", "Trained on", "Predictions", "Matched ROIs", "Leaked",
                 "Clean ROIs", "$\\alpha^{*}$"],
        "t2_cap": "Table 2. Principal metrics on the leakage-free evaluation set (YOLO11l-v2, "
                  "$n = 2088$) with 95% bootstrap confidence intervals",
        "t2_h": ["Metric", "boolfs only", "YOLO only", "Ensemble"],
        "t3_cap": "Table 3. The difference $\\Delta$ between the ensemble and the standalone "
                  "detector (paired bootstrap, 1,000 replicates; p.p. — percentage points)",
        "t3_h": ["Metric", "$\\Delta$, p.p.", "95% CI", "$p$", "Verdict"],
        "t4_cap": "Table 4. Per-class sensitivity, specificity and ROC-AUC (YOLO → Ensemble)",
        "t4_h": ["Class", "$n$", "Sensitivity", "Specificity", "Precision", "F1",
                 "AUC (ensemble)"],
        "t5_cap": "Table 5. The effect of the ensemble for all three detectors (on the cleaned set)",
        "t5_h": ["Detector", "$\\alpha^{*}$", "Accuracy", "$p$", "Bal. accuracy", "$p$", "AUC"],
        "t6_cap": "Table 6. The measured effect of data leakage: uncleaned versus cleaned "
                  "evaluation sets",
        "t6_h": ["Detector", "Accuracy (full)", "Accuracy (clean)", "Diff.",
                 "Bal. acc. (full)", "Bal. acc. (clean)", "Diff."],
        "t7_cap": "Table 7. Sensitivity to the matching threshold: the entire pipeline "
                  "(matching → selection of $\\alpha^{*}$ on train → evaluation on the cleaned "
                  "val) was re-run at three thresholds. $\\Delta$ is ensemble minus standalone "
                  "detector, in percentage points.",
        "t7_h": ["Detector", "$\\text{IoU}$", "$n$", "$\\alpha^{*}$", "$\\Delta$ accuracy",
                 "$\\Delta$ bal. accuracy", "$\\Delta$ AUC"],
        "f1_cap": "Fig. 1. Balanced accuracy as a function of the ensemble weight $\\alpha$. "
                  "$\\alpha^{*}$ is chosen from the training curve alone (dashed); the evaluation "
                  "curve (solid) remains independent.",
        "f2_cap": "Fig. 2. Macro ROC curves (leakage-free evaluation set). The ensemble dominates "
                  "both standalone streams.",
        "f3_cap": "Fig. 3. Per-class sensitivity: standalone YOLO versus the ensemble. The gain is "
                  "concentrated entirely in the under-represented classes.",
        "f4_cap": "Fig. 4. Confusion matrix (ensemble, row-normalised).",
        "f5_cap": "Fig. 5. The effect of data leakage: accuracy on the cleaned and uncleaned "
                  "evaluation sets. Detectors trained on the older database score higher on the "
                  "uncleaned set.",
        "yes_": "significant",
        "no_": "not significant",
        "trained_old": "older (445 database)",
        "trained_new": "this database",
    },
}

BODY = {"uz": {
    "intro": [
        "Mammografik skriningda avtomatik tizimning qiymati topilgan patologiyalarning umumiy "
        "ulushi bilan emas, balki **kam uchraydigan, ammo hayotiy muhim** topilmalarni "
        "o'tkazib yubormasligi bilan o'lchanadi. Amaliy bazalarda sinflar keskin nomutanosib: "
        "bizning bazamizda limfa tuguni 9 483 ta ROI'da uchraydi, arxitektura buzilishi esa — "
        "atigi 13 tasida. Shu sababli oddiy aniqlik (accuracy) modelning klinik foydaliligini "
        "deyarli aks ettirmaydi: barcha ROI'ni ko'pchilik sinfga tegishli deb e'lon qilgan "
        "«model» ham yuqori aniqlik oladi.",

        "Chuqur detektorlar (YOLO oilasi) shakl va kontekstni yaxshi o'zlashtiradi, biroq "
        "ularning softmax ishonchi kam ta'minlangan sinflarda tizimli ravishda past baholanadi. "
        "Boshqa tomondan, Xamdamov [1] taklif etgan bul-dasturlash asosidagi belgi tanlash va "
        "undan quriladigan minimal masofa klassifikatori sinf markazlarigacha bo'lgan "
        "normallashtirilgan masofani hisoblaydi — bu yondashuv sinf hajmiga sezgir emas, chunki "
        "har bir sinf o'z sentroidi bilan teng huquqda ishtirok etadi. Ikki oqimning xatolari "
        "turli tabiatga ega, demak ularni birlashtirish kutilgan foyda beradi.",

        "Ansambl haqidagi adabiyot keng, ammo tibbiy tasvirlar sohasidagi ko'plab nashrlar ikki "
        "jiddiy metodologik nuqsondan aziyat chekadi. Birinchisi — **aralashma vaznini baholash "
        "to'plamida tanlash**: $\\alpha$ ni val bo'yicha optimallashtirib, so'ng o'sha val'da "
        "natija e'lon qilinsa, baho optimistik siljiydi. Ikkinchisi — **ma'lumot sizishi**: "
        "oldindan o'qitilgan modelning o'quv to'plami yangi baholash to'plami bilan kesishishi "
        "tekshirilmaydi.",

        "Mazkur ishda biz ikkala nuqsonni ham ochiq hisobga olamiz. $\\alpha^{*}$ faqat o'quv "
        "qismida tanlanadi. Uch detektordan ikkitasi eski bazada o'qitilgani sababli yangi "
        "baholash to'plamining 24 ta rasmini «ko'rgan» — biz bu rasmlarga tegishli barcha "
        "detektsiyalarni belgilab, ularni chiqarib tashlaymiz va **sizishning o'lchangan "
        "ta'sirini** alohida keltiramiz. Bizning bilishimizcha, mammografiya bo'yicha ansambl "
        "ishlarida sizish ta'siri bunday miqdoriy ko'rsatilgan emas.",
    ],
    "m21":
        "Birinchi oqim — YOLO11 detektori: u ramka $B$ va sinf ishonchi $c_p$ ni beradi. Ikkinchi "
        "oqim — `boolfs`: har bir ROI'dan 38 ta belgi ajratiladi (8 intensivlik statistikasi, "
        "10 LBP komponenti, 6 shakl belgisi, 12 GLCM ko'rsatkichi va 2 gradient belgisi), "
        "$n'^{*} = 36$ tasi bul-dasturlash mezoni bo'yicha tanlanadi va minimal masofa "
        "klassifikatori qo'llanadi. Belgi tanlash va sentroidlar **faqat o'quv qismida** "
        "sozlangan; baholash to'plami butun oqimda hech qanday ko'rinishda ishtirok etmaydi.",
    "m22":
        "Ikki oqimni bitta obyektda solishtirish uchun detektsiyalar haqiqiy ramkalar bilan "
        "moslashtiriladi. Ishonch bo'yicha kamayish tartibida ochko'z (greedy) moslashtirish "
        "qo'llanadi; juftlik quyidagi shart bajarilganda qabul qilinadi:",
    "m23_a":
        "Detektor ishonchi $c_p$ va bashorat sinfi $\\hat{c}_p$ dan yumshatilgan ehtimollik "
        "vektori quriladi (qolgan massa teng taqsimlanadi):",
    "m23_b":
        "Boolfs oqimida $k$-sinf sentroidi va tarqoqligi hisoblanadi:",
    "m23_c":
        "ROI $p$ dan har bir sinfgacha tarqoqlikka normallashtirilgan masofa, so'ng undan "
        "softmax orqali ehtimollik olinadi (minus ishorasi: masofa qancha kichik bo'lsa, "
        "ehtimollik shuncha katta):",
    "m23_d":
        "Nihoyat ikki vektor chiziqli aralashtiriladi va qaror maksimum bo'yicha qabul qilinadi:",
    "m24":
        "Bu ish uchun eng muhim metodologik qoida shu: $\\alpha^{*}$ **hech qachon** baholash "
        "to'plamida qidirilmaydi. Biz uni faqat o'quv qismidagi moslashgan ROI'lar ustida, "
        "muvozanatli aniqlikni maksimallashtirib topamiz:",
    "m25_a":
        "Nomutanosib bazada oddiy aniqlik yaroqsiz. Asosiy mezon sifatida muvozanatli aniqlik "
        "(makro sezgirlik) va makro o'ziga xoslik olinadi:",
    "m25_b":
        "Qo'shimcha ravishda chalkashlik matritsasining butun tuzilmasini hisobga oluvchi "
        "ko'rsatkichlar — ko'p sinfli Metyus koeffitsienti va Koen kappasi:",
    "m25_c":
        "Chegaraga bog'liq bo'lmagan sifat makro «bittasi-qolganlarga qarshi» ROC-AUC bilan "
        "o'lchanadi:",
    "m26_a":
        "Har bir metrika uchun 95% ishonch oralig'i persentil bootstrap bilan quriladi "
        "($B = 1000$, obyektlar bo'yicha qaytarish bilan tanlash):",
    "m26_b":
        "Ansambl va yakka detektor solishtirilganda **juftlashgan** bootstrap ishlatiladi: har "
        "bir takrorlashda bir xil indekslar to'plami ikkala modelga qo'llanadi, shundan farq "
        "hisoblanadi. Bu ROI tarkibidagi umumiy dispersiyani yo'q qiladi va $p$-qiymatga sezilarli "
        "quvvat beradi:",
    "m3_a":
        "Loyihaning oldingi bosqichida ikki detektor — YOLO11s va YOLO11l — 445 ta rasmdan iborat "
        "eski bazada o'qitilgan edi. Yangi baza mustaqil yig'ilgan, ammo ikkala bazada ham bir xil "
        "arxivdan olingan rasmlar uchraydi. Tekshiruv shuni ko'rsatdiki, yangi baholash "
        "to'plamining 24 ta rasmi eski bazaning o'quv qismida bo'lgan. Halol baholash uchun toza "
        "to'plam quriladi:",
    "m3_b":
        "1-jadval har bir detektor uchun sizgan detektsiyalar sonini keltiradi: YOLO11s — 66, "
        "YOLO11l — 70, YOLO11l-v2 — 67. Uchinchi detektor aynan **shu** bazada o'qitilgani uchun "
        "uning 67 ta detektsiyasi haqiqiy sizish emas; biroq to'liq qiyoslanuvchanlik uchun barcha "
        "detektorlar bir xil tozalangan to'plamda baholanadi. Shunday qilib, uch model uchun "
        "baholash sharoiti bir xil bo'ladi.",
    "r41":
        "1-rasm muvozanatli aniqlikning $\\alpha$ ga bog'liqligini ikkala to'plamda ko'rsatadi. "
        "O'quv egrisi $\\alpha = 0{,}55$ da maksimumga chiqadi va aynan shu qiymat "
        "$\\alpha^{*}$ sifatida qabul qilinadi. Baholash egrisi $\\alpha \\approx 0{,}25$ da biroz "
        "yuqoriroq nuqtaga ega — agar biz $\\alpha$ ni val'da tanlaganimizda, natija sun'iy "
        "yaxshilangan bo'lardi. Ikki egrining maksimum joylashuvidagi farq aynan shu optimistik "
        "siljishning kattaligini ko'rsatadi. Muhim jihat: $\\alpha^{*} = 0{,}55$ atrofida val "
        "egrisi yassi — demak, tanlov aniq nuqtaga sezgir emas va usul mustahkam.",
    "r42_a":
        "2-jadval sizishdan toza to'plamdagi to'liq metrika to'plamini keltiradi. Yakka boolfs "
        "oqimi aniqlik bo'yicha kuchsiz ($0{,}603$), lekin uning makro ROC-AUC si $0{,}936$ — "
        "ya'ni u sinflarni **tartiblash** qobiliyatiga ega, faqat qaror chegarasi noto'g'ri "
        "joylashgan. Yakka YOLO teskari xususiyatga ega: aniqligi yuqori ($0{,}923$), ammo "
        "muvozanatli aniqligi past ($0{,}640$) va AUC si $0{,}897$.",
    "r42_b":
        "Ansambl ikki oqimning kuchli tomonlarini birlashtiradi: muvozanatli aniqlik $0{,}692$, "
        "makro AUC $0{,}976$, aniqlik esa $0{,}915$ da qoladi. 3-jadval farqlarning statistik "
        "ahamiyatini beradi. Muvozanatli aniqlik va sezgirlikdagi $+5{,}2$ foizli punktlik o'sish "
        "ahamiyatli ($p = 0{,}036$), AUC dagi $+7{,}9$ f.p. — juda ahamiyatli ($p < 0{,}001$). "
        "Aniqlikdagi $-0{,}8$ f.p. pasayish statistik ahamiyatsiz ($p = 0{,}074$), MCC va "
        "kappadagi kichik pasayishlar ham ahamiyatlilik chegarasida ($p = 0{,}056$ va "
        "$p = 0{,}068$).",
    "r42_c":
        "Bu natijani to'g'ri o'qish muhim. Ansambl **umumiy** to'g'ri javoblar sonini oshirmaydi; "
        "u to'g'ri javoblarni ko'pchilik sinfdan kamchilik sinflariga **qayta taqsimlaydi**. "
        "Nomutanosib klinik masalada bu aynan kerakli almashuv: bitta ortiqcha limfa tuguni "
        "xatosi bilan bitta o'tkazib yuborilgan BIRADS 4–5 ning narxi teng emas.",
    "r43":
        "2-rasmdagi ROC egri chiziqlari xulosani chegaradan mustaqil holda tasdiqlaydi. Ansambl "
        "egrisi butun ish oralig'ida ikkala yakka oqimdan yuqorida yotadi. Ayniqsa past FPR "
        "sohasida (klinik jihatdan eng muhim zona, $\\text{FPR} < 0{,}1$) ansambl sezgirligi "
        "$0{,}97$ ga yetadi, yakka YOLO esa $0{,}75$ atrofida qoladi. Diqqatga sazovor: yakka "
        "boolfs oqimi ham AUC bo'yicha ($0{,}936$) YOLO'dan ($0{,}897$) ustun — bu qo'lda "
        "loyihalangan tekstura belgilarining tartiblash quvvati hali ham raqobatbardosh ekanini "
        "ko'rsatadi.",
    "r44_a":
        "4-jadval va 3-rasm foydaning qayerdan kelayotganini aniq ko'rsatadi. BIRADS 1–2 "
        "sezgirligi $0{,}667$ dan $0{,}833$ ga, assimetriya $0{,}429$ dan $0{,}571$ ga, "
        "kalsifikatsiya $0{,}954$ dan $0{,}995$ ga ko'tarildi. Ko'pchilik sinf — limfa tuguni — "
        "sezgirligi $0{,}932$ dan $0{,}910$ ga tushdi. BIRADS 4–5 sinfida baholash to'plamida "
        "atigi 2 ta ROI bor va ikkala model ham ularni topa olmadi; bu sinf bo'yicha hech qanday "
        "xulosa chiqarib bo'lmaydi va biz uni ochiq cheklov sifatida qayd etamiz.",
    "r44_b":
        "4-rasmdagi chalkashlik matritsasi xato tuzilmasini ochadi va sezgirlik o'sishining "
        "narxini ko'rsatadi. Eng katta diagonaldan tashqari katak — limfa tugunining BIRADS 1–2 "
        "deb tasniflanishi (62 ta ROI); undan keyin limfa tuguni → o'sma (42) va limfa tuguni → "
        "kalsifikatsiya (27). Aynan shu 62 ta yolg'on musbat BIRADS 1–2 sinfining precision "
        "ko'rsatkichini $0{,}074$ ga tushiradi (5 ta to'g'ri topilishga 63 ta yolg'on musbat). "
        "Boshqacha aytganda, ansambl kam ta'minlangan sinf tomon «siljigan» chegara evaziga uning "
        "sezgirligini $0{,}833$ ga ko'targan. Xuddi shu mexanizm kalsifikatsiyada ham ko'rinadi: "
        "sezgirlik $0{,}954 \to 0{,}995$, ammo precision $1{,}000$ dan $0{,}915$ ga tushdi. "
        "Skrining kontekstida — tizim yakuniy tashxis qo'ymay, radiologga sohani ko'rsatganda — "
        "bunday almashuv oqlanadi; ammo uni yashirmasdan qayd etish shart.",
    "r45_a":
        "5-jadval ansamblning uchala detektor uchun ta'sirini keltiradi va muhim ogohlantirish "
        "beradi. Sizishga uchramagan YOLO11l-v2 da ansambl foydali: aniqlik ahamiyatli "
        "pasaymaydi, muvozanatli aniqlik esa ahamiyatli o'sadi. Sizishga uchragan YOLO11l da esa "
        "ansambl aniqlikni $0{,}938$ dan $0{,}872$ ga tushiradi ($p < 0{,}001$), muvozanatli "
        "aniqlikdagi o'sish esa ahamiyatsiz ($p = 0{,}248$). YOLO11s da manzara oraliq: "
        "muvozanatli aniqlik $+10{,}3$ f.p. o'sadi, lekin ishonch oralig'i nolni qamrab oladi "
        "($p = 0{,}194$).",
    "r45_b":
        "Buning sababi $\\alpha^{*}$ qiymatlarida ko'rinadi: sizishga uchragan modellarda o'quv "
        "to'plamida YOLO oqimi sun'iy ravishda kuchli ko'rinadi, shu sababli optimal vazn boolfs "
        "tomonga siljiydi ($\\alpha^{*} = 0{,}30$ va $0{,}35$), toza modelda esa muvozanatli "
        "$0{,}55$ tanlanadi. Boshqacha aytganda, sizish nafaqat metrikani, balki **o'rganilgan "
        "giperparametrni ham** buzadi.",
    "r45_c":
        "6-jadval va 5-rasm sizishning bevosita o'lchangan ta'sirini beradi. Tozalanmagan "
        "to'plamda uchala detektor ham biroz yuqoriroq aniqlik ko'rsatadi. Farqlar kichik "
        "($\\leq 0{,}4$ f.p.), chunki sizgan detektsiyalar ulushi ham kichik (66–70 ta, ya'ni "
        "$\\approx 3\\%$). Shunga qaramay, bu farqlar bir yo'nalishda — modelning o'zi ko'rgan "
        "rasmlarda yaxshiroq ishlashi kutilganidek. Agar sizish ulushi kattaroq bo'lganda, xulosa "
        "butunlay buzilishi mumkin edi; shuning uchun uni **har doim** o'lchash kerak.",
    "r46":
        "Barcha yuqoridagi natijalar $\\text{IoU} \\geq 0{,}3$ moslashtirish chegarasida "
        "olindi. Bu chegara xulosalarni belgilab qo'ymaganini tekshirish uchun biz butun oqimni — "
        "moslashtirish, $\\alpha^{*}$ ni train'da qayta tanlash va tozalangan val'da baholashni — "
        "$\\text{IoU} \\in \\{0{,}3;\\ 0{,}5;\\ 0{,}7\\}$ uchun uch detektorda qaytadan "
        "bajardik (7-jadval).",
    "r46_b":
        "Natija bir tomondan xulosani mustahkamlaydi, ikkinchi tomondan uni **cheklaydi**. "
        "Mustahkamlovchi qismi: makro ROC-AUC dagi o'sish to'qqizta holatning **to'qqiztasida** "
        "ham ijobiy va ahamiyatli ($+6{,}9$ dan $+18{,}6$ f.p. gacha). Bu — chegaraga bog'liq "
        "bo'lmagan, oqim sozlamalaridan mustaqil yagona xulosa: ansambl sinflarni tartiblash "
        "sifatini har qanday moslashtirish rejimida oshiradi.",
    "r46_c":
        "Cheklovchi qismi: toza detektorda muvozanatli aniqlikdagi foyda $\\text{IoU} = 0{,}3$ "
        "va $0{,}5$ da ahamiyatli ($p = 0{,}036$ va $p = 0{,}042$), ammo $0{,}7$ da butunlay "
        "yo'qoladi ($\\Delta = -0{,}8$ f.p., $p = 0{,}648$). Sabab ochiq: qat'iy chegara faqat "
        "aniq lokalizatsiyalangan, «oson» ROI'larni qoldiradi (2088 dan 1828 ga), va aynan "
        "bunday ROI'larda yakka detektorning o'zi ham kuchli — uning muvozanatli aniqligi "
        "$0{,}640$ dan $0{,}693$ ga ko'tariladi, ansamblga esa qo'shadigan narsa qolmaydi. "
        "Qiziq tomoni shuki, sizishga uchragan detektorlarda teskari manzara: chegara qat'iylashgan "
        "sari ansambl foydasi **o'sadi** (YOLO11s uchun $+10{,}3 \\to +25{,}9$ f.p.), chunki "
        "ularning yakka muvozanatli aniqligi aksincha pasayadi.",
    "r46_d":
        "Demak, ansambl foydasi ROI'ning **qiyinligiga** bog'liq: u noaniq lokalizatsiyalangan, "
        "chegarasi noravshan sohalarda paydo bo'ladi va oson sohalarda yo'qoladi. Skrining uchun "
        "bu qulay xossa — chunki aynan qiyin sohalar radiologning e'tiborini talab qiladi.",
    "d1":
        "**Asosiy xulosa.** Bul-dasturlash asosidagi klassifikator zamonaviy chuqur detektorni "
        "almashtira olmaydi (yakka aniqligi $0{,}603$ ga qarshi $0{,}923$), biroq uni "
        "**to'ldiradi**: ikki oqimning xatolari korrelyatsiyalanmagani sababli aralashma kam "
        "ta'minlangan sinflarda sezgirlikni oshiradi va tartiblash sifatini ($\\text{AUC}$) "
        "sezilarli yaxshilaydi. Bu qo'lda loyihalangan, interpretatsiya qilinadigan belgilarning "
        "chuqur o'rganish davrida ham o'z o'rni borligini ko'rsatadi.",
    "d2":
        "**Klinik talqin.** Skriningda asosiy xarajat — o'tkazib yuborilgan patologiya. Ansambl "
        "BIRADS 1–2 va assimetriya sezgirligini oshirib, ko'pchilik sinfdagi kichik yo'qotish "
        "hisobiga aynan shu xarajatni kamaytiradi. Amaliyotda tizim yakuniy tashxis qo'ymaydi, "
        "balki radiologga diqqat talab qiluvchi sohalarni ko'rsatadi; bunday rejimda yuqori "
        "sezgirlik yuqori precision'dan muhimroq.",
    "d3":
        "**Metodologik xulosa.** «Ansambl har doim yordam beradi» degan qarash noto'g'ri. Bizning "
        "uchta detektorimizdan faqat bittasida — o'z bazasida halol o'qitilganida — ansambl "
        "izchil foyda berdi. Sizishga uchragan detektorlarda esa ansambl aniqlikni ahamiyatli "
        "pasaytirdi. Agar biz sizishni tekshirmaganimizda, YOLO11l uchun «ansambl zarar keltiradi» "
        "degan noto'g'ri umumiy xulosa chiqargan bo'lardik.",
    "d4":
        "**Cheklovlar.** (i) BIRADS 4–5 va arxitektura buzilishi sinflarida baholash namunasi "
        "juda kichik (2 va 0 ROI) — bu sinflar bo'yicha xulosa chiqarilmaydi. (ii) Baholash "
        "bitta markaz arxivi bilan chegaralangan. (iii) 4.6-bo'limda ko'rsatilganidek, "
        "muvozanatli aniqlikdagi foyda moslashtirish chegarasiga bog'liq: u "
        "$\\text{IoU} \\leq 0{,}5$ da ahamiyatli, $0{,}7$ da esa toza detektor uchun yo'qoladi. "
        "Faqat ROC-AUC dagi ustunlik barcha chegaralarda saqlanadi. Shuning uchun ansamblning "
        "asosiy qiymati **tartiblash sifatida**, aniq qaror qoidasida emas. (iv) $\\alpha$ "
        "global konstanta; sinfga bog'liq vazn kelajakdagi ish mavzusi.",
    "d5":
        "Nihoyat, Xamdamov ishida keltirilgan ishonchlilik mezoni $P$ — to'g'ri tasniflangan "
        "obyektlar ulushi — haqida alohida to'xtalish kerak. Uning ta'rifidan ko'rinadiki, $P$ "
        "oddiy aniqlik bilan **ayni bir xil** kattalik. Bizning toza to'plamimizda u yakka boolfs "
        "oqimi uchun $0{,}603$, yakka YOLO uchun $0{,}923$, ansambl uchun $0{,}915$ ni tashkil "
        "etadi. Aynan shu qiymatlar mezonning chegarasini ochib beradi: $P$ bo'yicha ansambl "
        "yakka detektordan «yomonroq» ko'rinadi, holbuki u kam ta'minlangan sinflarda sezgirlikni "
        "ahamiyatli oshirgan. Demak, nomutanosib bazada $P$ ni yakka mezon sifatida ishlatib "
        "bo'lmaydi va uni muvozanatli aniqlik bilan to'ldirish shart:",
    "c": [
        "YOLO11 va bul-dasturlash klassifikatorining chiziqli ansambli 13 968 o'quv / 2 359 "
        "baholash ROI'sidan iborat sakkiz sinfli bazada sinovdan o'tkazildi; ansambl vazni faqat "
        "o'quv qismida tanlandi.",
        "Yangi baholash to'plamining 24 ta rasmi eski detektorlarning o'quv to'plamida topildi; "
        "barcha metrikalar sizishdan tozalangan qismda hisoblandi va sizishning ta'siri alohida "
        "o'lchandi.",
        "Sizishdan toza detektorda ansambl muvozanatli aniqlikni $+5{,}2$ f.p. ($p = 0{,}036$), "
        "makro ROC-AUC ni $+7{,}9$ f.p. ($p < 0{,}001$) oshirdi; oddiy aniqlikning $-0{,}8$ f.p. "
        "pasayishi ahamiyatsiz ($p = 0{,}074$).",
        "Foyda to'liq kam ta'minlangan sinflarda: BIRADS 1–2 sezgirligi $0{,}667 \\to 0{,}833$, "
        "assimetriya $0{,}429 \\to 0{,}571$, kalsifikatsiya $0{,}954 \\to 0{,}995$.",
        "Sizishga uchragan detektorlarda ansambl aniqlikni ahamiyatli pasaytirdi — demak ansambl "
        "foydasi shartsiz emas va uni har bir detektor uchun alohida, sizish nazorati bilan "
        "tekshirish shart.",
        "Moslashtirish chegarasiga sezuvchanlik tahlili (uch detektor × uch chegara) shuni "
        "ko'rsatdiki, ROC-AUC dagi ustunlik to'qqizta holatning to'qqiztasida ham saqlanadi "
        "($+6{,}9 \\ldots +18{,}6$ f.p.), muvozanatli aniqlikdagi foyda esa ROI qiyinligiga "
        "bog'liq: $\\text{IoU} = 0{,}7$ da, faqat oson ROI'lar qolganda, u yo'qoladi.",
    ],
}}

import m2_body_i18n as _i18n  # noqa: E402
BODY.update(_i18n.BODY)

REFS = [
    "Хамдамов Н.Х. Метод отбора информативных признаков на основе булева программирования // "
    "Проблемы вычислительной и прикладной математики. — 2017. — № 4(10). — С. 63–71.",
    "Jocher G., Qiu J. Ultralytics YOLO11. — 2024. — URL: https://github.com/ultralytics/ultralytics",
    "Kaufman S., Rosset S., Perlich C. Leakage in data mining: formulation, detection, and "
    "avoidance // ACM Transactions on Knowledge Discovery from Data. — 2012. — Vol. 6, "
    "No. 4. — Art. 15.",
    "Brodersen K.H., Ong C.S., Stephan K.E., Buhmann J.M. The balanced accuracy and its posterior "
    "distribution // Proc. 20th Int. Conf. on Pattern Recognition (ICPR). — 2010. — P. 3121–3124.",
    "Chicco D., Jurman G. The advantages of the Matthews correlation coefficient (MCC) over F1 "
    "score and accuracy in binary classification evaluation // BMC Genomics. — 2020. — Vol. 21. "
    "— Art. 6.",
    "Efron B., Tibshirani R.J. An Introduction to the Bootstrap. — New York: Chapman & Hall, "
    "1993. — 436 p.",
    "Dietterich T.G. Ensemble methods in machine learning // Multiple Classifier Systems. "
    "Lecture Notes in Computer Science. — 2000. — Vol. 1857. — P. 1–15.",
    "Kuncheva L.I., Whitaker C.J. Measures of diversity in classifier ensembles and their "
    "relationship with the ensemble accuracy // Machine Learning. — 2003. — Vol. 51, "
    "No. 2. — P. 181–207.",
    "D'Orsi C.J. et al. ACR BI-RADS Atlas: Breast Imaging Reporting and Data System. — 5th ed. "
    "— Reston: American College of Radiology, 2013. — 688 p.",
    "Haralick R.M., Shanmugam K., Dinstein I. Textural features for image classification // "
    "IEEE Transactions on Systems, Man, and Cybernetics. — 1973. — Vol. SMC-3, No. 6. — P. 610–621.",
    "Rodriguez-Ruiz A. et al. Stand-alone artificial intelligence for breast cancer detection in "
    "mammography // Journal of the National Cancer Institute. — 2019. — Vol. 111, No. 9. "
    "— P. 916–922.",
    "Varoquaux G., Cheplygina V. Machine learning for medical imaging: methodological failures "
    "and recommendations for the future // npj Digital Medicine. — 2022. — Vol. 5. — Art. 48.",
]


# ═══════════════════════════════ jadvallar ═══════════════════════════════ #

def t1_rows(lang, met):
    t = T[lang]
    rows = []
    for tag in ORDER:
        e = met["detectors"][tag]
        rows.append([e["label"],
                     t["trained_old"] if e["trained_on_old_data"] else t["trained_new"],
                     K.INT(e["n_pred"], lang), K.INT(e["n_matched_all"], lang),
                     str(e["n_leaked"]), K.INT(e["n_matched_clean"], lang),
                     K.N(e["alpha_star"], lang, 2)])
    return rows


def t2_rows(lang, met):
    e = met["detectors"][BEST]
    bo, yo, en = e["boolfs"], e["yolo"], e["ensemble"]
    rows = []
    for i, k in enumerate(MET_KEYS):
        rows.append([MET_L[lang][i],
                     K.CI(bo[k], bo["ci"].get(k), lang),
                     K.CI(yo[k], yo["ci"].get(k), lang),
                     "**" + K.CI(en[k], en["ci"].get(k), lang) + "**"])
    return rows


def t3_rows(lang, met):
    t = T[lang]
    e = met["detectors"][BEST]
    rows = []
    for i, k in enumerate(MET_KEYS):
        d = e["delta"].get(k)
        if not d:
            continue
        sig = t["yes_"] if d["p"] < 0.05 else t["no_"]
        rows.append([MET_L[lang][i], K.PP(d["delta"], lang),
                     f"[{K.PP(d['lo'], lang)}; {K.PP(d['hi'], lang)}]",
                     K.PV(d["p"], lang), sig])
    return rows


def t4_rows(lang, met):
    e = met["detectors"][BEST]
    auc = e["ensemble"]["auc_per_class"]
    rows = []
    for pe, py in zip(e["ensemble"]["per_class"], e["yolo"]["per_class"]):
        if pe["support"] == 0:
            continue
        a = auc.get(str(pe["class_idx"]), auc.get(pe["class_idx"]))
        rows.append([CLS[lang][pe["class"]], K.INT(pe["support"], lang),
                     f"{K.N(py['sensitivity'], lang, 3)} → **{K.N(pe['sensitivity'], lang, 3)}**",
                     f"{K.N(py['specificity'], lang, 3)} → {K.N(pe['specificity'], lang, 3)}",
                     f"{K.N(py['precision'], lang, 3)} → {K.N(pe['precision'], lang, 3)}",
                     f"{K.N(py['f1'], lang, 3)} → {K.N(pe['f1'], lang, 3)}",
                     K.N(a, lang, 3)])
    return rows


def t5_rows(lang, met):
    rows = []
    for tag in ORDER:
        e = met["detectors"][tag]
        rows.append([e["label"], K.N(e["alpha_star"], lang, 2),
                     f"{K.N(e['yolo']['accuracy'], lang)} → {K.N(e['ensemble']['accuracy'], lang)}",
                     K.PV(e["delta"]["accuracy"]["p"], lang),
                     f"{K.N(e['yolo']['balanced_accuracy'], lang)} → "
                     f"**{K.N(e['ensemble']['balanced_accuracy'], lang)}**",
                     K.PV(e["delta"]["balanced_accuracy"]["p"], lang),
                     f"{K.N(e['yolo']['auc_macro'], lang)} → "
                     f"**{K.N(e['ensemble']['auc_macro'], lang)}**"])
    return rows


def t6_rows(lang, met):
    rows = []
    for tag in ORDER:
        e = met["detectors"][tag]
        f = e["full_val"]
        ca, cb = e["yolo"]["accuracy"], e["yolo"]["balanced_accuracy"]
        rows.append([e["label"], K.N(f["yolo_acc"], lang), K.N(ca, lang),
                     K.PP(f["yolo_acc"] - ca, lang, 2),
                     K.N(f["yolo_bacc"], lang), K.N(cb, lang),
                     K.PP(f["yolo_bacc"] - cb, lang, 2)])
    return rows


def t7_rows(lang, iou):
    rows = []
    for tag in ORDER:
        lbl = {"yolo11s_8class": "YOLO11s", "trained_8class_yolo11l": "YOLO11l",
               BEST: "YOLO11l-v2"}[tag]
        for thr in ("0.3", "0.5", "0.7"):
            e = iou["detectors"][tag][thr]
            d = e["delta"]
            def cell(k):
                s = K.PP(d[k]["delta"], lang)
                return f"{s} ({K.PV(d[k]['p'], lang)})"
            rows.append([lbl, K.N(float(thr), lang, 1), K.INT(e["n_clean"], lang),
                         K.N(e["alpha_star"], lang, 2),
                         cell("accuracy"), cell("balanced_accuracy"), cell("auc_macro")])
    return rows


# ═════════════════════════════════ qurish ════════════════════════════════ #

def build(lang, met, art, iou):
    t, b = T[lang], BODY[lang]
    fig = ASSETS / lang
    doc = Document()
    K.setup(doc)

    K.title(doc, t["title"])
    K.authors(doc, t["authors"])
    K.abstract(doc, t["abs_l"], t["abs"], t["kw_l"], t["kw"])

    K.heading(doc, t["h1"])
    for p in b["intro"]:
        K.para(doc, p)

    K.heading(doc, t["h2"])
    K.subheading(doc, t["h21"])
    K.para(doc, b["m21"])

    K.subheading(doc, t["h22"])
    K.para(doc, b["m22"])
    add_equation(doc, *X.eq_iou(), number=1)

    K.subheading(doc, t["h23"])
    K.para(doc, b["m23_a"])
    add_equation(doc, *X.eq_yolo_vec(), number=2)
    K.para(doc, b["m23_b"])
    add_equation(doc, *F.eq_centroid(), number=3)
    add_equation(doc, *F.eq_scatter(), number=4)
    K.para(doc, b["m23_c"])
    add_equation(doc, *F.eq_rho(), number=5)
    add_equation(doc, *F.eq_softmax(), number=6)
    K.para(doc, b["m23_d"])
    add_equation(doc, *F.eq_ensemble(), number=7)
    add_equation(doc, *F.eq_decision(), number=8)

    K.subheading(doc, t["h24"])
    K.para(doc, b["m24"])
    add_equation(doc, *X.eq_alpha_star(), number=9)

    K.subheading(doc, t["h25"])
    K.para(doc, b["m25_a"])
    add_equation(doc, *X.eq_bacc(), number=10)
    add_equation(doc, *X.eq_spec(), number=11)
    K.para(doc, b["m25_b"])
    add_equation(doc, *X.eq_mcc(), number=12)
    add_equation(doc, *X.eq_kappa(), number=13)
    K.para(doc, b["m25_c"])
    add_equation(doc, *X.eq_auc_ovr(), number=14)

    K.subheading(doc, t["h26"])
    K.para(doc, b["m26_a"])
    add_equation(doc, *X.eq_bootstrap_ci(), number=15)
    K.para(doc, b["m26_b"])
    add_equation(doc, *X.eq_delta(), number=16)

    K.heading(doc, t["h3"])
    K.para(doc, b["m3_a"])
    add_equation(doc, *X.eq_leak(), number=17)
    K.para(doc, b["m3_b"])
    K.caption(doc, t["t1_cap"], before=True)
    K.table(doc, t["t1_h"], t1_rows(lang, met), size=8.0)

    K.heading(doc, t["h4"])
    K.subheading(doc, t["h41"])
    K.para(doc, b["r41"])
    K.picture(doc, fig / "m2_f1_alpha.png", t["f1_cap"])

    K.subheading(doc, t["h42"])
    K.para(doc, b["r42_a"])
    K.caption(doc, t["t2_cap"], before=True)
    K.table(doc, t["t2_h"], t2_rows(lang, met), size=8.0)
    K.para(doc, b["r42_b"])
    K.caption(doc, t["t3_cap"], before=True)
    K.table(doc, t["t3_h"], t3_rows(lang, met), size=8.5)
    K.para(doc, b["r42_c"])

    K.subheading(doc, t["h43"])
    K.para(doc, b["r43"])
    K.picture(doc, fig / "m2_f2_roc.png", t["f2_cap"], width=4.7)

    K.subheading(doc, t["h44"])
    K.para(doc, b["r44_a"])
    K.caption(doc, t["t4_cap"], before=True)
    K.table(doc, t["t4_h"], t4_rows(lang, met), size=7.6)
    K.picture(doc, fig / "m2_f3_sens.png", t["f3_cap"])
    K.para(doc, b["r44_b"])
    K.picture(doc, fig / "m2_f4_cm.png", t["f4_cap"], width=5.3)

    K.subheading(doc, t["h45"])
    K.para(doc, b["r45_a"])
    K.caption(doc, t["t5_cap"], before=True)
    K.table(doc, t["t5_h"], t5_rows(lang, met), size=8.0)
    K.para(doc, b["r45_b"])
    K.para(doc, b["r45_c"])
    K.caption(doc, t["t6_cap"], before=True)
    K.table(doc, t["t6_h"], t6_rows(lang, met), size=7.8)
    K.picture(doc, fig / "m2_f5_leakage.png", t["f5_cap"])

    K.subheading(doc, t["h46"])
    K.para(doc, b["r46"])
    K.caption(doc, t["t7_cap"], before=True)
    K.table(doc, t["t7_h"], t7_rows(lang, iou), size=7.4)
    K.para(doc, b["r46_b"])
    K.para(doc, b["r46_c"])
    K.para(doc, b["r46_d"])

    K.heading(doc, t["h5"])
    for k in ("d1", "d2", "d3", "d4"):
        K.para(doc, b[k])
    K.para(doc, b["d5"])
    add_equation(doc, *F.eq_P(), number=18)

    K.heading(doc, t["h6"])
    for i, c in enumerate(b["c"], 1):
        K.para(doc, f"**{i}.** {c}")

    K.refs(doc, t["refs_l"], REFS)
    return doc


def main():
    met, art, iou = load()
    for lg in (sys.argv[1:] or ["uz", "ru", "en"]):
        doc = build(lg, met, art, iou)
        out = ROOT / f"MAMOGRAF_Maqola_2026_M2_Ansambl_{lg.upper()}.docx"
        doc.save(out)
        print(f"[m2] {lg}: {out}")


if __name__ == "__main__":
    main()
