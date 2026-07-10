# -*- coding: utf-8 -*-
"""m2_body_i18n.py — 2-maqola matnining ruscha va inglizcha professional tarjimasi."""

BODY = {
    "ru": {
        "intro": [
            "В маммографическом скрининге ценность автоматической системы измеряется не общей "
            "долей найденных патологий, а тем, что она не пропускает **редкие, но жизненно "
            "важные** находки. В практических базах классы резко несбалансированы: в нашей базе "
            "лимфатический узел встречается в 9 483 ROI, а архитектурная перестройка — лишь в 13. "
            "Поэтому обычная точность (accuracy) почти не отражает клиническую полезность модели: "
            "высокую точность получит и «модель», относящая все ROI к мажоритарному классу.",

            "Глубокие детекторы (семейство YOLO) хорошо усваивают форму и контекст, однако их "
            "softmax-уверенность систематически занижена на малочисленных классах. С другой "
            "стороны, предложенный Хамдамовым [1] отбор признаков на основе булева "
            "программирования и строящийся на нём классификатор минимального расстояния вычисляет "
            "нормированное расстояние до центров классов — этот подход нечувствителен к объёму "
            "класса, поскольку каждый класс участвует наравне со своим центроидом. Ошибки двух "
            "потоков имеют разную природу, а значит, их объединение обещает выигрыш.",

            "Литература об ансамблях обширна, однако многие публикации в области медицинских "
            "изображений страдают двумя серьёзными методологическими изъянами. Первый — **подбор "
            "веса смеси на оценочном наборе**: если оптимизировать $\\alpha$ по val, а затем "
            "объявлять результат на том же val, оценка смещается в оптимистичную сторону. "
            "Второй — **утечка данных**: не проверяется пересечение обучающего набора "
            "предобученной модели с новым оценочным набором.",

            "В настоящей работе мы открыто учитываем оба изъяна. Величина $\\alpha^{*}$ "
            "подбирается только на обучающей части. Поскольку два детектора из трёх обучались на "
            "старой базе, они «видели» 24 изображения нового оценочного набора — мы помечаем все "
            "относящиеся к этим изображениям детекции, исключаем их и отдельно приводим "
            "**измеренное влияние утечки**. Насколько нам известно, в работах по ансамблям в "
            "маммографии влияние утечки количественно так не показывалось.",
        ],
        "m21":
            "Первый поток — детектор YOLO11: он выдаёт рамку $B$ и уверенность класса $c_p$. "
            "Второй поток — `boolfs`: из каждой ROI извлекаются 38 признаков (8 статистик "
            "интенсивности, 10 компонент LBP, 6 признаков формы, 12 показателей GLCM и 2 "
            "градиентных), $n'^{*} = 36$ из них отбираются по критерию булева программирования, и "
            "применяется классификатор минимального расстояния. Отбор признаков и центроиды "
            "настраиваются **только на обучающей части**; оценочный набор не участвует в потоке "
            "ни в каком виде.",
        "m22":
            "Чтобы сравнить два потока на одном объекте, детекции сопоставляются с истинными "
            "рамками. Применяется жадное сопоставление в порядке убывания уверенности; пара "
            "принимается при выполнении условия:",
        "m23_a":
            "Из уверенности детектора $c_p$ и предсказанного класса $\\hat{c}_p$ строится "
            "сглаженный вектор вероятностей (остаточная масса распределяется поровну):",
        "m23_b":
            "В потоке boolfs вычисляются центроид и рассеяние класса $k$:",
        "m23_c":
            "Нормированное на рассеяние расстояние от ROI $p$ до каждого класса, затем вероятность "
            "через softmax (знак минус: чем меньше расстояние, тем больше вероятность):",
        "m23_d":
            "Наконец, два вектора линейно смешиваются, и решение принимается по максимуму:",
        "m24":
            "Важнейшее методологическое правило этой работы: $\\alpha^{*}$ **никогда** не ищется "
            "на оценочном наборе. Мы находим его только на сопоставленных ROI обучающей части, "
            "максимизируя сбалансированную точность:",
        "m25_a":
            "На несбалансированной базе обычная точность непригодна. В качестве основных критериев "
            "берутся сбалансированная точность (макро чувствительность) и макро специфичность:",
        "m25_b":
            "Дополнительно — показатели, учитывающие всю структуру матрицы ошибок: многоклассовый "
            "коэффициент Мэтьюса и каппа Коэна:",
        "m25_c":
            "Качество, не зависящее от порога, измеряется макро ROC-AUC «один против остальных»:",
        "m26_a":
            "Для каждой метрики 95%-й доверительный интервал строится персентильным бутстрепом "
            "($B = 1000$, выборка объектов с возвращением):",
        "m26_b":
            "При сравнении ансамбля с одиночным детектором используется **парный** бутстреп: в "
            "каждом повторении один и тот же набор индексов применяется к обеим моделям, и по нему "
            "вычисляется разность. Это устраняет общую дисперсию состава ROI и заметно повышает "
            "мощность $p$-значения:",
        "m3_a":
            "На предыдущем этапе проекта два детектора — YOLO11s и YOLO11l — обучались на старой "
            "базе из 445 изображений. Новая база собрана независимо, однако в обеих встречаются "
            "изображения из одного и того же архива. Проверка показала, что 24 изображения нового "
            "оценочного набора входили в обучающую часть старой базы. Для честной оценки строится "
            "очищенный набор:",
        "m3_b":
            "Таблица 1 приводит число утёкших детекций для каждого детектора: YOLO11s — 66, "
            "YOLO11l — 70, YOLO11l-v2 — 67. Поскольку третий детектор обучался именно на **этой** "
            "базе, его 67 детекций не являются настоящей утечкой; однако ради полной "
            "сопоставимости все детекторы оцениваются на одном и том же очищенном наборе. Тем "
            "самым условия оценивания для трёх моделей одинаковы.",
        "r41":
            "Рис. 1 показывает зависимость сбалансированной точности от $\\alpha$ на обоих "
            "наборах. Обучающая кривая достигает максимума при $\\alpha = 0{,}55$, и именно это "
            "значение принимается за $\\alpha^{*}$. Оценочная кривая имеет несколько более высокую "
            "точку при $\\alpha \\approx 0{,}25$ — если бы мы подбирали $\\alpha$ на val, "
            "результат оказался бы искусственно улучшенным. Разница в положении максимумов двух "
            "кривых как раз и показывает величину этого оптимистичного смещения. Существенно, что "
            "вблизи $\\alpha^{*} = 0{,}55$ оценочная кривая пологая — следовательно, выбор "
            "нечувствителен к точной точке, и метод устойчив.",
        "r42_a":
            "Таблица 2 приводит полный набор метрик на очищенном наборе. Одиночный поток boolfs "
            "слаб по точности ($0{,}603$), но его макро ROC-AUC равен $0{,}936$ — то есть он "
            "обладает способностью **упорядочивать** классы, и лишь решающий порог расположен "
            "неверно. Одиночный YOLO обладает обратным свойством: высокая точность ($0{,}923$), но "
            "низкая сбалансированная точность ($0{,}640$) и AUC $0{,}897$.",
        "r42_b":
            "Ансамбль объединяет сильные стороны обоих потоков: сбалансированная точность "
            "$0{,}692$, макро AUC $0{,}976$, а точность остаётся на уровне $0{,}915$. Таблица 3 "
            "даёт статистическую значимость разностей. Прирост в $+5{,}2$ процентных пункта по "
            "сбалансированной точности и чувствительности значим ($p = 0{,}036$), прирост AUC в "
            "$+7{,}9$ п.п. — высоко значим ($p < 0{,}001$). Снижение точности на $-0{,}8$ п.п. "
            "статистически незначимо ($p = 0{,}074$), небольшие снижения MCC и каппы также лежат "
            "на границе значимости ($p = 0{,}056$ и $p = 0{,}068$).",
        "r42_c":
            "Правильное прочтение этого результата существенно. Ансамбль не увеличивает **общее** "
            "число верных ответов; он **перераспределяет** их от мажоритарного класса к "
            "миноритарным. В несбалансированной клинической задаче это именно нужный размен: цена "
            "одной лишней ошибки на лимфоузле и цена одного пропущенного BIRADS 4–5 не равны.",
        "r43":
            "ROC-кривые на рис. 2 подтверждают вывод независимо от порога. Кривая ансамбля лежит "
            "выше обеих одиночных на всём рабочем диапазоне. Особенно в области малых FPR "
            "(клинически важнейшая зона, $\\text{FPR} < 0{,}1$) чувствительность ансамбля "
            "достигает $0{,}97$, тогда как одиночный YOLO остаётся около $0{,}75$. Примечательно: "
            "одиночный поток boolfs превосходит YOLO по AUC ($0{,}936$ против $0{,}897$) — это "
            "показывает, что упорядочивающая способность вручную спроектированных текстурных "
            "признаков всё ещё конкурентоспособна.",
        "r44_a":
            "Таблица 4 и рис. 3 ясно показывают, откуда берётся выигрыш. Чувствительность "
            "BIRADS 1–2 выросла с $0{,}667$ до $0{,}833$, асимметрии — с $0{,}429$ до $0{,}571$, "
            "кальцификации — с $0{,}954$ до $0{,}995$. Чувствительность мажоритарного класса — "
            "лимфоузла — снизилась с $0{,}932$ до $0{,}910$. В классе BIRADS 4–5 оценочный набор "
            "содержит всего 2 ROI, и обе модели их не обнаружили; никаких выводов по этому классу "
            "сделать нельзя, и мы открыто фиксируем это как ограничение.",
        "r44_b":
            "Матрица ошибок на рис. 4 раскрывает структуру ошибок и показывает цену прироста "
            "чувствительности. Наибольшая внедиагональная ячейка — отнесение лимфоузла к "
            "BIRADS 1–2 (62 ROI); далее лимфоузел → образование (42) и лимфоузел → кальцификация "
            "(27). Именно эти 62 ложноположительных срабатывания опускают precision класса "
            "BIRADS 1–2 до $0{,}074$ (5 верных обнаружений против 63 ложноположительных). Иначе "
            "говоря, ансамбль поднял чувствительность этого класса до $0{,}833$ ценой смещения "
            "решающей границы в его сторону. Тот же механизм виден и на кальцификации: "
            "чувствительность $0{,}954 \to 0{,}995$, однако precision упал с $1{,}000$ до "
            "$0{,}915$. В контексте скрининга — когда система не ставит окончательный диагноз, а "
            "указывает рентгенологу область — такой размен оправдан; но фиксировать его нужно "
            "открыто.",
        "r45_a":
            "Таблица 5 приводит влияние ансамбля для всех трёх детекторов и содержит важное "
            "предостережение. На свободном от утечки YOLO11l-v2 ансамбль полезен: точность значимо "
            "не снижается, а сбалансированная точность значимо растёт. На затронутом утечкой "
            "YOLO11l ансамбль снижает точность с $0{,}938$ до $0{,}872$ ($p < 0{,}001$), а рост "
            "сбалансированной точности незначим ($p = 0{,}248$). У YOLO11s картина промежуточная: "
            "сбалансированная точность растёт на $+10{,}3$ п.п., но доверительный интервал "
            "накрывает ноль ($p = 0{,}194$).",
        "r45_b":
            "Причина видна в значениях $\\alpha^{*}$: у затронутых утечкой моделей поток YOLO на "
            "обучающем наборе выглядит искусственно сильным, поэтому оптимальный вес смещается в "
            "сторону boolfs ($\\alpha^{*} = 0{,}30$ и $0{,}35$), тогда как на чистой модели "
            "выбирается сбалансированное $0{,}55$. Иначе говоря, утечка искажает не только "
            "метрику, но и **сам выученный гиперпараметр**.",
        "r45_c":
            "Таблица 6 и рис. 5 дают непосредственно измеренное влияние утечки. На неочищенном "
            "наборе все три детектора показывают несколько более высокую точность. Разности малы "
            "($\\leq 0{,}4$ п.п.), поскольку и доля утёкших детекций мала (66–70, то есть "
            "$\\approx 3\\%$). Тем не менее эти разности однонаправленны — как и следует ожидать, "
            "модель работает лучше на изображениях, которые она видела. При большей доле утечки "
            "вывод мог бы быть искажён полностью; поэтому её нужно измерять **всегда**.",
        "r46":
            "Все приведённые выше результаты получены при пороге сопоставления "
            "$\\text{IoU} \\geq 0{,}3$. Чтобы убедиться, что этот порог не предопределил "
            "выводы, мы заново выполнили весь конвейер — сопоставление, повторный подбор "
            "$\\alpha^{*}$ на train и оценку на очищенном val — при "
            "$\\text{IoU} \\in \\{0{,}3;\\ 0{,}5;\\ 0{,}7\\}$ для трёх детекторов "
            "(таблица 7).",
        "r46_b":
            "Результат, с одной стороны, укрепляет вывод, а с другой — **ограничивает** его. "
            "Укрепляющая часть: прирост макро ROC-AUC положителен и значим в **девяти** случаях "
            "из девяти (от $+6{,}9$ до $+18{,}6$ п.п.). Это единственный вывод, не зависящий ни "
            "от порога, ни от настроек конвейера: ансамбль повышает качество упорядочивания "
            "классов при любом режиме сопоставления.",
        "r46_c":
            "Ограничивающая часть: на чистом детекторе выигрыш в сбалансированной точности значим "
            "при $\\text{IoU} = 0{,}3$ и $0{,}5$ ($p = 0{,}036$ и $p = 0{,}042$), но при "
            "$0{,}7$ исчезает полностью ($\\Delta = -0{,}8$ п.п., $p = 0{,}648$). Причина "
            "очевидна: строгий порог оставляет лишь чётко локализованные, «лёгкие» ROI (с 2088 до "
            "1828), а именно на таких ROI силён и сам одиночный детектор — его сбалансированная "
            "точность поднимается с $0{,}640$ до $0{,}693$, и ансамблю уже нечего добавить. "
            "Любопытно, что на затронутых утечкой детекторах картина обратная: с ужесточением "
            "порога выигрыш ансамбля **растёт** (для YOLO11s с $+10{,}3$ до $+25{,}9$ п.п.), "
            "поскольку их одиночная сбалансированная точность, наоборот, падает.",
        "r46_d":
            "Таким образом, польза ансамбля зависит от **трудности** ROI: она возникает на "
            "нечётко локализованных областях с размытой границей и исчезает на лёгких. Для "
            "скрининга это удобное свойство — ведь именно трудные области требуют внимания "
            "рентгенолога.",
        "d1":
            "**Главный вывод.** Классификатор на основе булева программирования не способен "
            "заменить современный глубокий детектор (одиночная точность $0{,}603$ против "
            "$0{,}923$), но он его **дополняет**: поскольку ошибки двух потоков не коррелированы, "
            "смесь повышает чувствительность на малочисленных классах и заметно улучшает качество "
            "упорядочивания ($\\text{AUC}$). Это показывает, что у вручную спроектированных, "
            "интерпретируемых признаков есть своё место и в эпоху глубокого обучения.",
        "d2":
            "**Клиническая интерпретация.** Основная цена в скрининге — пропущенная патология. "
            "Ансамбль, повышая чувствительность к BIRADS 1–2 и асимметрии за счёт небольшой потери "
            "на мажоритарном классе, снижает именно эту цену. На практике система не ставит "
            "окончательный диагноз, а указывает рентгенологу области, требующие внимания; в таком "
            "режиме высокая чувствительность важнее высокой precision.",
        "d3":
            "**Методологический вывод.** Представление, будто «ансамбль всегда помогает», неверно. "
            "Из трёх наших детекторов ансамбль дал последовательный выигрыш лишь на одном — том, "
            "что был честно обучен на своей базе. На затронутых утечкой детекторах ансамбль значимо "
            "снизил точность. Не проверь мы утечку, мы сделали бы ошибочный общий вывод: «ансамбль "
            "вредит» для YOLO11l.",
        "d4":
            "**Ограничения.** (i) В классах BIRADS 4–5 и архитектурной перестройки оценочная "
            "выборка крайне мала (2 и 0 ROI) — выводы по этим классам не делаются. (ii) Оценка "
            "ограничена архивом одного центра. (iii) Как показано в разделе 4.6, выигрыш "
            "в сбалансированной точности зависит от порога сопоставления: он значим при "
            "$\\text{IoU} \\leq 0{,}5$ и исчезает при $0{,}7$ для чистого детектора. При всех "
            "порогах сохраняется лишь преимущество по ROC-AUC. Поэтому основная ценность "
            "ансамбля — в **качестве упорядочивания**, а не в конкретном решающем правиле. "
            "(iv) $\\alpha$ — глобальная константа; классозависимый вес является темой будущей "
            "работы.",
        "d5":
            "Наконец, следует отдельно остановиться на критерии надёжности $P$, приведённом в "
            "работе Хамдамова, — доле верно классифицированных объектов. Из его определения видно, "
            "что $P$ **тождественно совпадает** с обычной точностью. На нашем очищенном наборе он "
            "равен $0{,}603$ для одиночного потока boolfs, $0{,}923$ для одиночного YOLO и "
            "$0{,}915$ для ансамбля. Именно эти значения вскрывают границу применимости критерия: "
            "по $P$ ансамбль выглядит «хуже» одиночного детектора, хотя он значимо повысил "
            "чувствительность на малочисленных классах. Следовательно, на несбалансированной базе "
            "$P$ нельзя использовать как единственный критерий и его необходимо дополнять "
            "сбалансированной точностью:",
        "c": [
            "Линейный ансамбль YOLO11 и классификатора на основе булева программирования испытан "
            "на восьмиклассовой базе из 13 968 обучающих / 2 359 оценочных ROI; вес ансамбля "
            "подбирался только на обучающей части.",
            "24 изображения нового оценочного набора обнаружены в обучающем наборе старых "
            "детекторов; все метрики вычислены на очищенной от утечки части, а влияние утечки "
            "измерено отдельно.",
            "На свободном от утечки детекторе ансамбль повысил сбалансированную точность на "
            "$+5{,}2$ п.п. ($p = 0{,}036$) и макро ROC-AUC на $+7{,}9$ п.п. ($p < 0{,}001$); "
            "снижение обычной точности на $-0{,}8$ п.п. незначимо ($p = 0{,}074$).",
            "Выигрыш целиком приходится на малочисленные классы: чувствительность BIRADS 1–2 "
            "$0{,}667 \\to 0{,}833$, асимметрии $0{,}429 \\to 0{,}571$, кальцификации "
            "$0{,}954 \\to 0{,}995$.",
            "На затронутых утечкой детекторах ансамбль значимо снизил точность — следовательно, "
            "польза ансамбля не безусловна, и её необходимо проверять для каждого детектора "
            "отдельно, с контролем утечки.",
            "Анализ чувствительности к порогу сопоставления (три детектора × три порога) показал, "
            "что преимущество по ROC-AUC сохраняется во всех девяти случаях "
            "($+6{,}9 \\ldots +18{,}6$ п.п.), тогда как выигрыш в сбалансированной точности "
            "зависит от трудности ROI: при $\\text{IoU} = 0{,}7$, когда остаются лишь лёгкие ROI, "
            "он исчезает.",
        ],
    },

    "en": {
        "intro": [
            "In mammographic screening the value of an automated system is measured not by the "
            "overall proportion of pathologies it finds, but by its not missing the **rare yet "
            "vitally important** findings. In practical databases the classes are severely "
            "imbalanced: in ours the lymph node occurs in 9,483 ROIs, architectural distortion in "
            "just 13. Plain accuracy therefore barely reflects a model's clinical usefulness: even "
            "a «model» that assigns every ROI to the majority class attains a high accuracy.",

            "Deep detectors (the YOLO family) capture shape and context well, yet their softmax "
            "confidence is systematically under-estimated on under-represented classes. The "
            "Boolean-programming feature selection proposed by Khamdamov [1], and the "
            "minimum-distance classifier built upon it, instead compute a normalised distance to "
            "the class centres — an approach insensitive to class size, since every class "
            "participates on equal footing through its own centroid. The errors of the two streams "
            "are of different natures, so combining them promises a gain.",

            "The literature on ensembles is extensive, yet many publications in medical imaging "
            "suffer from two serious methodological defects. The first is **selecting the mixing "
            "weight on the evaluation set**: optimising $\\alpha$ on val and then reporting the "
            "result on that same val biases the estimate optimistically. The second is **data "
            "leakage**: the intersection of a pre-trained model's training set with the new "
            "evaluation set is not checked.",

            "In the present work we account for both defects openly. The value $\\alpha^{*}$ is "
            "selected on the training partition alone. Because two of the three detectors were "
            "trained on an older database, they have «seen» 24 images of the new evaluation set — "
            "we flag every detection belonging to those images, exclude them, and report the "
            "**measured effect of the leakage** separately. To our knowledge, the effect of "
            "leakage has not been quantified in this way in ensemble work on mammography.",
        ],
        "m21":
            "The first stream is the YOLO11 detector: it yields a box $B$ and a class confidence "
            "$c_p$. The second stream is `boolfs`: 38 features are extracted from every ROI (8 "
            "intensity statistics, 10 LBP components, 6 shape features, 12 GLCM descriptors and 2 "
            "gradient features), $n'^{*} = 36$ of them are selected by the Boolean "
            "programming criterion, and a minimum-distance classifier is applied. Feature "
            "selection and the centroids are fitted **on the training partition only**; the "
            "evaluation set takes no part in the pipeline in any form.",
        "m22":
            "To compare the two streams on the same object, detections are matched against "
            "ground-truth boxes. Greedy matching in decreasing order of confidence is used; a pair "
            "is accepted when the following condition holds:",
        "m23_a":
            "From the detector confidence $c_p$ and the predicted class $\\hat{c}_p$ a smoothed "
            "probability vector is built (the residual mass is spread evenly):",
        "m23_b":
            "In the boolfs stream the centroid and the scatter of class $k$ are computed:",
        "m23_c":
            "The scatter-normalised distance from ROI $p$ to every class, and then a probability "
            "via softmax (with a minus sign: the smaller the distance, the larger the "
            "probability):",
        "m23_d":
            "Finally the two vectors are mixed linearly and the decision is taken by the maximum:",
        "m24":
            "The single most important methodological rule of this work: $\\alpha^{*}$ is "
            "**never** searched for on the evaluation set. We obtain it solely on the matched ROIs "
            "of the training partition, by maximising balanced accuracy:",
        "m25_a":
            "On an imbalanced database plain accuracy is unusable. As the principal criteria we "
            "adopt balanced accuracy (macro sensitivity) and macro specificity:",
        "m25_b":
            "In addition, quantities that account for the entire structure of the confusion "
            "matrix — the multiclass Matthews correlation coefficient and Cohen's kappa:",
        "m25_c":
            "Threshold-independent quality is measured by the macro one-versus-rest ROC-AUC:",
        "m26_a":
            "For every metric a 95% confidence interval is constructed by the percentile bootstrap "
            "($B = 1000$, sampling objects with replacement):",
        "m26_b":
            "When the ensemble is compared with the standalone detector a **paired** bootstrap is "
            "used: in each replicate the same index set is applied to both models and the "
            "difference is computed from it. This removes the variance common to the ROI "
            "composition and appreciably increases the power of the $p$-value:",
        "m3_a":
            "At an earlier stage of the project two detectors — YOLO11s and YOLO11l — were trained "
            "on an older database of 445 images. The new database was collected independently, yet "
            "images from the same archive occur in both. Inspection revealed that 24 images of the "
            "new evaluation set had been part of the older database's training partition. For an "
            "honest evaluation a cleaned set is constructed:",
        "m3_b":
            "Table 1 reports the number of leaked detections for each detector: YOLO11s — 66, "
            "YOLO11l — 70, YOLO11l-v2 — 67. Since the third detector was trained on **this very** "
            "database, its 67 detections are not a genuine leak; nevertheless, for full "
            "comparability all detectors are evaluated on the same cleaned set. The evaluation "
            "conditions are thereby identical for the three models.",
        "r41":
            "Fig. 1 shows balanced accuracy as a function of $\\alpha$ on both sets. The training "
            "curve peaks at $\\alpha = 0.55$, and precisely this value is adopted as "
            "$\\alpha^{*}$. The evaluation curve has a slightly higher point at "
            "$\\alpha \\approx 0.25$ — had we tuned $\\alpha$ on val, the result would have been "
            "artificially improved. The offset between the two maxima is exactly the magnitude of "
            "that optimistic bias. Importantly, the evaluation curve is flat around "
            "$\\alpha^{*} = 0.55$ — the choice is therefore insensitive to the exact point, and "
            "the method is robust.",
        "r42_a":
            "Table 2 reports the full metric set on the cleaned evaluation set. The standalone "
            "boolfs stream is weak in accuracy ($0.603$), yet its macro ROC-AUC is $0.936$ — that "
            "is, it possesses the ability to **rank** the classes, and only its decision threshold "
            "is misplaced. The standalone YOLO has the converse property: a high accuracy "
            "($0.923$) but a low balanced accuracy ($0.640$) and an AUC of $0.897$.",
        "r42_b":
            "The ensemble unites the strengths of both streams: balanced accuracy $0.692$, macro "
            "AUC $0.976$, while accuracy remains at $0.915$. Table 3 gives the statistical "
            "significance of the differences. The gain of $+5.2$ percentage points in balanced "
            "accuracy and sensitivity is significant ($p = 0.036$), and the $+7.9$ p.p. gain in "
            "AUC is highly significant ($p < 0.001$). The $-0.8$ p.p. decline in accuracy is "
            "statistically insignificant ($p = 0.074$), and the small declines in MCC and kappa "
            "also lie at the boundary of significance ($p = 0.056$ and $p = 0.068$).",
        "r42_c":
            "Reading this result correctly matters. The ensemble does not increase the **total** "
            "number of correct answers; it **redistributes** them from the majority class to the "
            "minority ones. In an imbalanced clinical task that is precisely the desired trade: "
            "the cost of one extra error on a lymph node and the cost of one missed BIRADS 4–5 are "
            "not equal.",
        "r43":
            "The ROC curves of Fig. 2 confirm the conclusion independently of any threshold. The "
            "ensemble curve lies above both standalone curves across the whole operating range. In "
            "the low-FPR region especially (the clinically most important zone, "
            "$\\text{FPR} < 0.1$) the ensemble sensitivity reaches $0.97$, whereas the standalone "
            "YOLO stays near $0.75$. Notably, the standalone boolfs stream surpasses YOLO in AUC "
            "($0.936$ versus $0.897$) — evidence that the ranking power of hand-designed textural "
            "features remains competitive.",
        "r44_a":
            "Table 4 and Fig. 3 show plainly where the gain comes from. BIRADS 1–2 sensitivity "
            "rose from $0.667$ to $0.833$, asymmetry from $0.429$ to $0.571$, and calcification "
            "from $0.954$ to $0.995$. The sensitivity of the majority class — lymph node — fell "
            "from $0.932$ to $0.910$. In the BIRADS 4–5 class the evaluation set contains only 2 "
            "ROIs and neither model detected them; no conclusion can be drawn for that class, and "
            "we record this openly as a limitation.",
        "r44_b":
            "The confusion matrix in Fig. 4 exposes the structure of the errors and reveals the "
            "price of the sensitivity gain. The largest off-diagonal cell is lymph node classified "
            "as BIRADS 1–2 (62 ROIs); next come lymph node → mass (42) and lymph node → "
            "calcification (27). It is precisely these 62 false positives that push the precision "
            "of the BIRADS 1–2 class down to $0.074$ (5 correct detections against 63 false "
            "positives). Put differently, the ensemble raised that class's sensitivity to $0.833$ "
            "at the cost of shifting the decision boundary toward it. The same mechanism is "
            "visible for calcification: sensitivity $0.954 \to 0.995$, yet precision fell from "
            "$1.000$ to $0.915$. In a screening context — where the system issues no final "
            "diagnosis but points the radiologist to a region — such a trade is justified; it must "
            "nonetheless be stated openly.",
        "r45_a":
            "Table 5 reports the effect of the ensemble for all three detectors and carries an "
            "important warning. On the leakage-free YOLO11l-v2 the ensemble is beneficial: accuracy "
            "does not fall significantly while balanced accuracy rises significantly. On the "
            "leakage-affected YOLO11l, by contrast, the ensemble lowers accuracy from $0.938$ to "
            "$0.872$ ($p < 0.001$), and the rise in balanced accuracy is insignificant "
            "($p = 0.248$). YOLO11s is intermediate: balanced accuracy rises by $+10.3$ p.p., yet "
            "the confidence interval covers zero ($p = 0.194$).",
        "r45_b":
            "The reason is visible in the values of $\\alpha^{*}$: on the leakage-affected models "
            "the YOLO stream appears artificially strong on the training set, so the optimal weight "
            "shifts toward boolfs ($\\alpha^{*} = 0.30$ and $0.35$), whereas on the clean model a "
            "balanced $0.55$ is chosen. In other words, leakage corrupts not only the metric but "
            "**the learned hyperparameter itself**.",
        "r45_c":
            "Table 6 and Fig. 5 give the directly measured effect of leakage. On the uncleaned set "
            "all three detectors post a slightly higher accuracy. The differences are small "
            "($\\leq 0.4$ p.p.), because the fraction of leaked detections is small too (66–70, "
            "i.e. $\\approx 3\\%$). They are nonetheless unidirectional — as one would expect, a "
            "model performs better on images it has seen. Had the leaked fraction been larger, the "
            "conclusion could have been distorted entirely; hence it must **always** be measured.",
        "r46":
            "All the results above were obtained at a matching threshold of "
            "$\\text{IoU} \\geq 0.3$. To confirm that this threshold did not predetermine the "
            "conclusions, we re-ran the entire pipeline — matching, re-selection of $\\alpha^{*}$ "
            "on train, and evaluation on the cleaned val — at "
            "$\\text{IoU} \\in \\{0.3,\\ 0.5,\\ 0.7\\}$ for all three detectors "
            "(Table 7).",
        "r46_b":
            "The outcome both strengthens the conclusion and **constrains** it. The strengthening "
            "part: the gain in macro ROC-AUC is positive and significant in **nine** cases out of "
            "nine (from $+6.9$ to $+18.6$ p.p.). This is the one conclusion independent of the "
            "threshold and of the pipeline settings: the ensemble improves class-ranking quality "
            "under any matching regime.",
        "r46_c":
            "The constraining part: on the clean detector the gain in balanced accuracy is "
            "significant at $\\text{IoU} = 0.3$ and $0.5$ ($p = 0.036$ and $p = 0.042$), yet at "
            "$0.7$ it vanishes entirely ($\\Delta = -0.8$ p.p., $p = 0.648$). The reason is "
            "plain: a strict threshold retains only sharply localised, «easy» ROIs (from 2,088 "
            "down to 1,828), and on precisely such ROIs the standalone detector is itself "
            "strong — its balanced accuracy rises from $0.640$ to $0.693$, leaving the ensemble "
            "nothing to add. Curiously, on the leakage-affected detectors the picture is "
            "reversed: as the threshold tightens the ensemble's gain **grows** (for YOLO11s from "
            "$+10.3$ to $+25.9$ p.p.), because their standalone balanced accuracy falls instead.",
        "r46_d":
            "The benefit of the ensemble therefore depends on the **difficulty** of the ROI: it "
            "emerges on poorly localised regions with blurred boundaries and disappears on easy "
            "ones. For screening this is a convenient property — it is exactly the difficult "
            "regions that demand the radiologist's attention.",
        "d1":
            "**Principal conclusion.** The Boolean-programming classifier cannot replace a modern "
            "deep detector (standalone accuracy $0.603$ versus $0.923$), but it **complements** "
            "it: because the errors of the two streams are uncorrelated, the mixture raises "
            "sensitivity on the under-represented classes and appreciably improves ranking quality "
            "($\\text{AUC}$). This shows that hand-designed, interpretable features retain a place "
            "even in the era of deep learning.",
        "d2":
            "**Clinical interpretation.** The dominant cost in screening is a missed pathology. By "
            "raising sensitivity to BIRADS 1–2 and asymmetry at the price of a small loss on the "
            "majority class, the ensemble reduces exactly that cost. In practice the system does "
            "not issue a final diagnosis but points the radiologist to regions demanding "
            "attention; in such a regime high sensitivity outweighs high precision.",
        "d3":
            "**Methodological conclusion.** The notion that «an ensemble always helps» is false. "
            "Of our three detectors, the ensemble delivered a consistent gain on only one — the "
            "one honestly trained on its own database. On the leakage-affected detectors the "
            "ensemble significantly lowered accuracy. Had we not checked for leakage, we would have "
            "drawn the erroneous general conclusion that «the ensemble hurts» for YOLO11l.",
        "d4":
            "**Limitations.** (i) In the BIRADS 4–5 and architectural distortion classes the "
            "evaluation sample is extremely small (2 and 0 ROIs) — no conclusions are drawn for "
            "them. (ii) The evaluation is confined to a single-centre archive. (iii) As shown in Section 4.6, the "
            "gain in balanced accuracy depends on the matching threshold: it is significant at "
            "$\\text{IoU} \\leq 0.5$ and vanishes at $0.7$ for the clean detector. Only the "
            "ROC-AUC advantage persists at every threshold. The ensemble's principal value "
            "therefore lies in **ranking quality** rather than in any particular decision rule. "
            "(iv) $\\alpha$ is a global constant; a class-dependent weight is a topic for future "
            "work.",
        "d5":
            "Finally, the reliability criterion $P$ given in Khamdamov's work — the proportion of "
            "correctly classified objects — deserves separate comment. Its definition shows that "
            "$P$ is **identically the same** quantity as plain accuracy. On our cleaned set it "
            "equals $0.603$ for the standalone boolfs stream, $0.923$ for the standalone YOLO and "
            "$0.915$ for the ensemble. These very values expose the limit of the criterion: by $P$ "
            "the ensemble looks «worse» than the standalone detector, even though it significantly "
            "raised sensitivity on the under-represented classes. On an imbalanced database, "
            "therefore, $P$ cannot serve as the sole criterion and must be complemented by balanced "
            "accuracy:",
        "c": [
            "A linear ensemble of YOLO11 and a Boolean-programming classifier was evaluated on an "
            "eight-class database of 13,968 training / 2,359 evaluation ROIs; the ensemble weight "
            "was selected on the training partition alone.",
            "24 images of the new evaluation set were found in the training set of the older "
            "detectors; all metrics were computed on the leakage-free subset, and the effect of "
            "leakage was measured separately.",
            "On the leakage-free detector the ensemble raised balanced accuracy by $+5.2$ p.p. "
            "($p = 0.036$) and macro ROC-AUC by $+7.9$ p.p. ($p < 0.001$); the $-0.8$ p.p. decline "
            "in plain accuracy is insignificant ($p = 0.074$).",
            "The gain falls entirely on the under-represented classes: BIRADS 1–2 sensitivity "
            "$0.667 \\to 0.833$, asymmetry $0.429 \\to 0.571$, calcification $0.954 \\to 0.995$.",
            "On the leakage-affected detectors the ensemble significantly lowered accuracy — hence "
            "the benefit of an ensemble is not unconditional and must be verified for each "
            "detector separately, with leakage control.",
            "A sensitivity analysis over the matching threshold (three detectors × three "
            "thresholds) showed that the ROC-AUC advantage persists in all nine cases "
            "($+6.9 \\ldots +18.6$ p.p.), whereas the gain in balanced accuracy depends on ROI "
            "difficulty: at $\\text{IoU} = 0.7$, when only easy ROIs remain, it disappears.",
        ],
    },
}
