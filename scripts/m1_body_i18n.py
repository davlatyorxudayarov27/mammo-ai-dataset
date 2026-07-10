# -*- coding: utf-8 -*-
"""m1_body_i18n.py — 1-maqola matnining ruscha va inglizcha professional tarjimasi."""

BODY = {
    "ru": {
        "intro": [
            "В автоматическом анализе маммографических изображений глубокие свёрточные детекторы "
            "в последние годы заняли доминирующее положение. Однако они остаются чёрным ящиком: "
            "неясно, какое именно текстурное свойство внесло вклад в решение, что ограничивает "
            "доверие к ним в клинической практике. Поэтому задача автоматического выделения "
            "интерпретируемого набора признаков со строгим математическим определением не утратила "
            "своей актуальности.",

            "Н. Хамдамов [1] сформулировал отбор признаков как задачу булева программирования: "
            "каждому признаку сопоставляется бинарная переменная $\\lambda_j \\in \\{0, 1\\}$, и "
            "максимизируется функционал $\\Phi(\\lambda)$, выражающий отношение межклассовой "
            "разделимости к внутриклассовому рассеянию. Существенное свойство метода состоит в том, "
            "что решение не требует полного перебора: префикс ряда, упорядоченного по показателю "
            "$r_j = a_j / w_j$, даёт оптимальное решение, благодаря чему сложность снижается с "
            "$O(2^N)$ до $O(N \\log N)$.",

            "Однако в литературе почти без внимания остался вопрос: **насколько устойчив сам "
            "список отобранных признаков?** Если $\\lambda^{*}$ заметно колеблется при малом "
            "изменении обучающей выборки, то вывод о «наиболее информативных признаках», "
            "извлечённый из него, не имеет научной ценности. Кунчева [2] поставила эту проблему в "
            "общем виде и предложила индекс устойчивости с поправкой на случайность; Ногейра и "
            "Браун [3] дали статистическое обоснование оценивания устойчивости.",

            "В нашей предыдущей работе [4] метод был испытан на малой базе из 519 ROI. При таком "
            "объёме надёжно измерить устойчивость невозможно. В настоящей статье мы расширяем "
            "анализ на базу, **в 27 раз большую**, — 13 968 обучающих ROI — и, сопоставляя две "
            "базы, отвечаем на следующие три вопроса:",
        ],
        "intro_q": [
            "Насколько процедура отбора устойчива к бутстреп-колебаниям внутри одной базы?",
            "Переносится ли ранжирование, найденное на одной базе, на другую — в особенности его "
            "голова?",
            "Как оптимальная мощность $n'^{*}$ связана с объёмом выборки?",
        ],
        "intro_end":
            "Ответы, забегая вперёд, кажутся противоречащими друг другу: внутри процедура крайне "
            "устойчива, а вовне её важнейшая часть — первые три признака — смещается. Объяснение "
            "этого противоречия и составляет основной вклад статьи.",

        "m21":
            "Каждая ROI рассматривается как полутоновое изображение $I(x, y)$, из которого "
            "извлекаются $N = 38$ признаков: 8 гистограммных статистик (среднее, стандартное "
            "отклонение, асимметрия, эксцесс, энтропия, энергия и два квантиля), 24 показателя "
            "GLCM, усреднённых по четырём направлениям для расстояний $d \\in \\{1, 3\\}$ "
            "(контраст, несходство, однородность, энергия, корреляция, ASM), а также 6 градиентных "
            "признаков (среднее, стандартное отклонение и квантили модуля Собеля). Все признаки "
            "подвергаются $z$-нормировке; параметры нормировки вычисляются только по обучающей "
            "части.",

        "m22_a":
            "Для $j$-го признака и пары классов $(k, l)$ разность межклассовых центров $a_{j}$ и "
            "внутриклассовое рассеяние $b_{j}$ определяются следующим образом:",
        "m22_b":
            "Их отношение $c_j$ даёт разделяющую способность признака, а глобальные показатели "
            "усредняются по всем парам классов:",
        "m22_c":
            "Задача булева программирования ставится на векторе $\\lambda \\in \\{0,1\\}^{N}$:",
        "m22_d":
            "Здесь $w_j$ — стоимость $j$-го признака (мы полагаем её равной единице, так что "
            "остаётся лишь ограничение на мощность). Основная лемма, показанная Хамдамовым: "
            "максимум $\\Phi$ достигается на префиксе ряда, отсортированного по убыванию "
            "$r_j = a_j / w_j$:",
        "m22_e":
            "Следовательно, оптимальное решение мощности $n'$ есть попросту первые $n'$ элементов "
            "ряда:",

        "m23_a":
            "По отобранным признакам центр (центроид) класса $k$ и внутриклассовое рассеяние:",
        "m23_b":
            "Нормированное на рассеяние расстояние от ROI $p$ до класса $k$ и решающее правило:",
        "m23_c":
            "При выборе $n'^{*}$ используется **только обучающая часть**. Поскольку классы резко "
            "несбалансированы (крупнейший класс в 1900 раз многочисленнее наименьшего), обычная "
            "точность непригодна как критерий: отнесение всех ROI к мажоритарному классу даёт "
            "точность $0{,}679$. Поэтому мы оптимизируем **сбалансированную точность** (макро "
            "чувствительность). Кроме того, блочная кросс-валидация с исключением по одному (LOO) "
            "оставляет в малых классах ровно один объект на блок, вследствие чего поблочная "
            "точность принимает лишь значения 0 или 1, а стандартное отклонение искусственно "
            "оказывается около $0{,}37$. Чтобы этого избежать, мы собираем **объединённые (pooled)** "
            "предсказания кросс-валидации и строим доверительные интервалы бутстрепом по ним.",

        "m24_a":
            "В $b$-м бутстреп-образце формируется ранжирование $\\pi_b$; из него выделяется "
            "множество мощности $n'$:",
        "m24_b":
            "Устойчивость внутри базы измеряется двумя показателями. Индекс Кунчевой корректирует "
            "пересечение относительно случайного ожидания и потому защищён от искусственного роста "
            "при больших $n'$:",
        "m24_c":
            "Коэффициент Жаккара, напротив, показывает нескорректированное сырое сходство — "
            "приведение обоих вместе раскрывает, насколько необходима поправка:",
        "m24_d":
            "Средний ранг каждого признака и его колебание определяют, какая часть ряда прочна:",
        "m24_e":
            "Наконец, согласие множеств, полученных на двух разных базах (малой $s$ и большой $l$):",

        "m3":
            "Обе базы получены из анонимизированной части маммографического архива «AISCAN». "
            "Большая база размечена восемью классами: лимфатический узел, кальцификация, "
            "образование, асимметрия, BIRADS 1–2, BIRADS 4–5, архитектурная перестройка и прочее. "
            "Признаки извлекаются из истинных (ground-truth) рамок, то есть анализ не зависит от "
            "качества детектора — это позволяет чисто измерить свойства отбора признаков. Все "
            "вычисления выполнены в едином коде (пакет `boolfs`), с одним и тем же зерном "
            "($\\text{seed} = 42$), при 1000 бутстреп-повторениях для доверительных интервалов "
            "метрик и 300 повторениях для индексов устойчивости.",

        "r41":
            "Таблица 2 и рис. 1 приводят результаты развёртки по мощности. Сбалансированная "
            "точность скачкообразно возрастает при переходе от $n' = 13$ к $n' = 21$ "
            "($0{,}410 \\to 0{,}556$), затем медленно насыщается. Максимум по кросс-валидации "
            "достигается при $n'^{*} = 36$. Примечательная деталь: полный набор ($n' = 38$) даёт "
            "более высокую **обычную** точность ($0{,}641$ против $0{,}596$), но более низкую "
            "**сбалансированную** ($0{,}623$ против $0{,}626$). Удаление двух признаков слегка "
            "уменьшает смещение в пользу мажоритарного класса — именно это и важно на "
            "несбалансированной базе.",

        "r42":
            "Таблица 3 и рис. 2 показывают бутстреп-устойчивость. На большой базе индекс Кунчевой "
            "ни при одной мощности не опускается ниже $0{,}830$, а при $n' = 5$ достигает идеальной "
            "воспроизводимости ($I_C = 1{,}000$). На малой базе индекс заметно ниже и при "
            "$n' = 34$ проседает до $0{,}726$. Коэффициент Жаккара монотонно растёт с увеличением "
            "$n'$ и при $n' = 36$ поднимается до $0{,}995$ — и это как раз демонстрирует "
            "обманчивость нескорректированной меры: когда из 38 отбираются 36, любые два множества "
            "почти наверняка совпадают. Индекс Кунчевой устраняет этот артефакт, а потому все "
            "выводы об устойчивости должны опираться только на него.",

        "r43":
            "Теперь перейдём к главному результату. Полные ранжированные ряды на двух базах весьма "
            "согласованы: корреляция Спирмена $\\rho = 0{,}937$ ($N = 38$). Отсюда можно было бы "
            "заключить, что «метод устойчив». Но если посмотреть на **голову** ряда, картина "
            "обратная: согласие множеств топ-3 составляет $A_{s,l} = 0{,}333$ — то есть из трёх "
            "общим оказывается лишь один признак ($\\texttt{grad\\_sobel\\_std}$). В топ-5 согласие "
            "поднимается до $0{,}600$, в топ-8 — до $0{,}875$ (последний столбец таблицы 3).",
        "r43b":
            "Таблица 4 и рис. 3 раскрывают причину. На малой базе первые два места занимает "
            "GLCM-корреляция ($\\bar{r} = 1{,}33 \\pm 0{,}47$ и $1{,}79 \\pm 0{,}59$), тогда как на "
            "большой она вообще не входит в первую пятёрку; вместо неё безусловным лидером "
            "становится стандартное отклонение градиента Собеля ($\\bar{r} = 1{,}00 \\pm 0{,}00$ — "
            "первое место во всех 300 бутстрепах). Объяснение физиологично: на малой выборке "
            "корреляционные признаки улавливают случайное различие между классами, и это различие "
            "выглядит устойчивым на уровне шума; при расширении выборки верх берёт истинный "
            "разделяющий фактор — резкость границы (рассеяние градиента). Иными словами, "
            "«устойчивый» лидер малой базы был на деле артефактом выборки.",
        "r43c":
            "Сосуществование этих двух слоёв (внутри базы $I_C \\approx 0{,}9$, между базами "
            "согласие топ-3 равно $0{,}33$) не является противоречием: бутстреп-образцы берутся из "
            "одного и того же распределения, поэтому устойчивость внутри них измеряет лишь "
            "**статистическую** дисперсию. Смена базы меняет само распределение и вскрывает "
            "**эпистемическую** неопределённость. Высокая бутстреп-устойчивость не гарантирует "
            "переносимости списка признаков — и это важнейший практический вывод.",

        "r44":
            "Рис. 4 показывает убывающую цепочку префиксного функционала $\\Phi(n')$: от "
            "$\\Phi(1) = 6{,}27$ до $\\Phi(38) = 1{,}04$. Убывание строго монотонно — это прямое "
            "следствие сортировки по $r_j$ и эмпирическое подтверждение леммы. Излом кривой "
            "приходится примерно на $n' \\approx 21$: после этой точки каждый добавляемый признак "
            "заметно снижает среднюю информативность, тогда как сбалансированная точность всё ещё "
            "продолжает расти. Расхождение двух критериев напоминает, что информативность и польза "
            "для классификации — не одно и то же: малоинформативный признак в сочетании с другими "
            "может помочь выделить малый класс.",

        "d1":
            "Полученные результаты влекут несколько методологических выводов. **Во-первых**, в "
            "любой публикации об отборе признаков обязана приводиться мера устойчивости, и она "
            "должна быть скорректирована на случайность: мы показали, что коэффициент Жаккара при "
            "больших $n'$ достигает $0{,}99$ и создаёт впечатление «идеальной устойчивости» — на "
            "деле же это просто переполнение множеств.",
        "d2":
            "**Во-вторых**, рейтинг признаков, полученный на малой выборке, никогда не следует "
            "обобщать как «список наиболее информативных признаков». В нашем случае 519 ROI "
            "выглядят достаточно многочисленными (в большинстве публикаций их меньше), однако его "
            "топ-3 совпал с топ-3 на 13 968 ROI лишь на 33%. Это напрямую связано с кризисом "
            "воспроизводимости в радиомике: одна из причин, по которым объявленные «важнейшими» "
            "текстурные признаки противоречат друг другу от статьи к статье, именно такова.",
        "d3":
            "**В-третьих**, оптимальная мощность $n'^{*}$ растёт с объёмом выборки ($34 \\to 36$), "
            "поскольку на большей выборке удаётся надёжно оценить ковариационную структуру большего "
            "числа признаков. Вместе с тем рост медленный: 27-кратное увеличение объёма добавило к "
            "мощности лишь два признака. Значит, $n'^{*}$ — слабо чувствительный к выборке "
            "параметр, и это практическое достоинство метода.",
        "d4":
            "**Ограничения.** Анализ ограничен архивом одного центра; межаппаратная "
            "(multi-scanner) вариативность не измерялась. Набор признаков ограничен 38 вручную "
            "спроектированными показателями; свойства ранжирования $r_j$ для эмбеддингов глубоких "
            "сетей требуют отдельной проверки. Наконец, в наименее обеспеченных классах "
            "(архитектурная перестройка — 13 ROI) оценки устойчивости обладают слабой "
            "статистической мощностью.",

        "c": [
            "Метод отбора признаков на основе булева программирования впервые сопоставлен на "
            "маммографических базах, различающихся по объёму на два порядка. Префиксная лемма "
            "подтверждена эмпирически: $\\Phi(n')$ образует строго убывающую цепочку.",
            "Процедура обладает высокой воспроизводимостью внутри одной базы — на большой базе "
            "индекс Кунчевой при всех мощностях превышает $0{,}830$.",
            "Между базами полный ряд согласуется ($\\rho = 0{,}937$), однако голова ранжирования "
            "смещается: согласие топ-3 равно $0{,}333$. Лидер малой базы (GLCM-корреляция) на "
            "большой базе выпадает из первой пятёрки.",
            "Оптимальная мощность слабо зависит от объёма выборки: $n'^{*}$ сместилась с $34$ до "
            "$36$; на большой базе сбалансированная точность равна $0{,}638$ [0,606; 0,762], "
            "макро ROC-AUC — $0{,}947$ [0,928; 0,960].",
            "Практическая рекомендация: публикуя рейтинг признаков, следует указывать объём "
            "выборки, на которой он получен, вычислять скорректированный на случайность индекс "
            "устойчивости и не называть голову рейтинга «универсальной», не подтвердив её на "
            "независимой базе.",
        ],
    },

    "en": {
        "intro": [
            "Deep convolutional detectors have come to dominate the automatic analysis of "
            "mammographic images in recent years. They nevertheless remain black boxes: it is not "
            "visible which textural property contributed to a decision, which limits clinical "
            "trust. The problem of automatically extracting an interpretable feature set with a "
            "precise mathematical definition has therefore not lost its relevance.",

            "N. Khamdamov [1] posed feature selection as a Boolean programming problem: a binary "
            "variable $\\lambda_j \\in \\{0, 1\\}$ is attached to every feature, and a functional "
            "$\\Phi(\\lambda)$ expressing the ratio of between-class separability to within-class "
            "scatter is maximised. An essential property of the method is that the solution "
            "requires no exhaustive enumeration: the prefix of the sequence ordered by the index "
            "$r_j = a_j / w_j$ yields the optimum, reducing the complexity from $O(2^N)$ to "
            "$O(N \\log N)$.",

            "One question, however, has been almost entirely overlooked in the literature: "
            "**how stable is the selected feature list itself?** If $\\lambda^{*}$ fluctuates "
            "appreciably under a small perturbation of the training sample, then any conclusion "
            "about the «most informative features» drawn from it carries no scientific weight. "
            "Kuncheva [2] posed this problem in general form and proposed a chance-corrected "
            "stability index; Nogueira and Brown [3] supplied the statistical foundation for "
            "estimating stability.",

            "In our earlier work [4] the method was tested on a small database of 519 ROIs. At such "
            "a size stability cannot be measured reliably. In the present paper we extend the "
            "analysis to a database **27 times larger** — 13,968 training ROIs — and, placing the "
            "two databases side by side, answer the following three questions:",
        ],
        "intro_q": [
            "How resistant is the selection procedure to bootstrap fluctuation within a single "
            "database?",
            "Does a ranking found on one database transfer to another — in particular, does its "
            "head?",
            "How is the optimal cardinality $n'^{*}$ related to sample size?",
        ],
        "intro_end":
            "The answers, stated in advance, appear mutually contradictory: internally the "
            "procedure is highly stable, while externally its most important part — the first "
            "three features — moves. Explaining that contradiction is the principal contribution "
            "of this paper.",

        "m21":
            "Each ROI is treated as a grayscale image $I(x, y)$ from which $N = 38$ features are "
            "extracted: 8 histogram statistics (mean, standard deviation, skewness, kurtosis, "
            "entropy, energy and two quantiles), 24 GLCM descriptors averaged over four directions "
            "for distances $d \\in \\{1, 3\\}$ (contrast, dissimilarity, homogeneity, energy, "
            "correlation, ASM), and 6 gradient features (mean, standard deviation and quantiles of "
            "the Sobel magnitude). All features are $z$-normalised; the normalisation parameters "
            "are computed from the training partition alone.",

        "m22_a":
            "For feature $j$ and the class pair $(k, l)$, the between-class centre difference "
            "$a_{j}$ and the within-class scatter $b_{j}$ are defined as:",
        "m22_b":
            "Their ratio $c_j$ gives the discriminating power of the feature, and the global "
            "quantities are averaged over all class pairs:",
        "m22_c":
            "The Boolean programming problem is posed over the vector "
            "$\\lambda \\in \\{0,1\\}^{N}$:",
        "m22_d":
            "Here $w_j$ is the cost of feature $j$ (we set it to unity, so that only the "
            "cardinality constraint remains). The key lemma established by Khamdamov states that "
            "the maximum of $\\Phi$ is attained on the prefix of the sequence sorted in decreasing "
            "order of $r_j = a_j / w_j$:",
        "m22_e":
            "Consequently, the optimal solution of cardinality $n'$ is simply the first $n'$ "
            "elements of the sequence:",

        "m23_a":
            "Over the selected features, the centre (centroid) of class $k$ and the within-class "
            "scatter are:",
        "m23_b":
            "The scatter-normalised distance from ROI $p$ to class $k$, and the decision rule:",
        "m23_c":
            "Only the **training partition** is used when choosing $n'^{*}$. Because the classes "
            "are severely imbalanced (the largest class is 1,900 times more populous than the "
            "smallest), plain accuracy is an unusable criterion: assigning every ROI to the "
            "majority class already yields an accuracy of $0.679$. We therefore optimise "
            "**balanced accuracy** (macro sensitivity). Moreover, leave-one-out (LOO) blocked "
            "cross-validation leaves exactly one object per block in the small classes, so that "
            "the per-block accuracy takes only the values 0 or 1 and the $\\pm$ standard deviation "
            "artificially comes out around $0.37$. To avoid this we collect **pooled** "
            "cross-validation predictions and construct confidence intervals by bootstrapping over "
            "them.",

        "m24_a":
            "The $b$-th bootstrap replicate induces a ranking $\\pi_b$, from which a set of "
            "cardinality $n'$ is extracted:",
        "m24_b":
            "Within-database stability is measured by two quantities. The Kuncheva index corrects "
            "the intersection against its chance expectation and is thus protected from spurious "
            "inflation at large $n'$:",
        "m24_c":
            "The Jaccard coefficient, by contrast, reports the raw uncorrected similarity — "
            "presenting the two together reveals just how necessary the correction is:",
        "m24_d":
            "The mean rank of each feature and its fluctuation determine which part of the "
            "sequence is firm:",
        "m24_e":
            "Finally, the agreement between the sets obtained on the two different databases "
            "(small $s$ and large $l$):",

        "m3":
            "Both databases are drawn from the anonymised portion of the «AISCAN» mammography "
            "archive. The large database is annotated with eight classes: lymph node, "
            "calcification, mass, asymmetry, BIRADS 1–2, BIRADS 4–5, architectural distortion and "
            "other. Features are extracted from ground-truth boxes, so the analysis does not depend "
            "on detector quality — this permits a clean measurement of the selection properties. "
            "All computations were performed in a single codebase (the `boolfs` package) with an "
            "identical seed ($\\text{seed} = 42$), using 1,000 bootstrap replicates for metric "
            "confidence intervals and 300 replicates for the stability indices.",

        "r41":
            "Table 2 and Fig. 1 report the cardinality sweep. Balanced accuracy jumps on passing "
            "from $n' = 13$ to $n' = 21$ ($0.410 \\to 0.556$) and then saturates slowly. The "
            "cross-validation maximum is attained at $n'^{*} = 36$. A noteworthy detail: the full "
            "set ($n' = 38$) yields a higher **plain** accuracy ($0.641$ versus $0.596$) but a "
            "lower **balanced** one ($0.623$ versus $0.626$). Discarding two features slightly "
            "reduces the bias toward the majority class — which is precisely what matters on an "
            "imbalanced database.",

        "r42":
            "Table 3 and Fig. 2 present the bootstrap stability. On the large database the "
            "Kuncheva index never falls below $0.830$ at any cardinality, and at $n' = 5$ it "
            "attains perfect reproducibility ($I_C = 1.000$). On the small database the index is "
            "markedly lower and sags to $0.726$ at $n' = 34$. The Jaccard coefficient rises "
            "monotonically with $n'$ and reaches $0.995$ at $n' = 36$ — and this is exactly what "
            "exposes the deceptiveness of the uncorrected measure: when 36 out of 38 are selected, "
            "any two sets almost certainly coincide. The Kuncheva index removes this artefact, and "
            "for that reason every stability conclusion must rest on it alone.",

        "r43":
            "We now turn to the principal result. The full ranked sequences on the two databases "
            "agree closely: the Spearman correlation is $\\rho = 0.937$ ($N = 38$). One might have "
            "concluded from this that «the method is stable». Yet on looking at the **head** of the "
            "sequence, the picture reverses: the agreement of the top-3 sets is "
            "$A_{s,l} = 0.333$ — that is, only one of the three features is shared "
            "($\\texttt{grad\\_sobel\\_std}$). At top-5 the agreement rises to $0.600$, and at "
            "top-8 to $0.875$ (last column of Table 3).",
        "r43b":
            "Table 4 and Fig. 3 disclose the reason. On the small database GLCM correlation "
            "occupies the first two positions ($\\bar{r} = 1.33 \\pm 0.47$ and "
            "$1.79 \\pm 0.59$), whereas on the large one it does not enter the top five at all; in "
            "its place the standard deviation of the Sobel gradient becomes the outright leader "
            "($\\bar{r} = 1.00 \\pm 0.00$ — first place in all 300 bootstraps). The explanation is "
            "physiological: on a small sample the correlation features capture a chance difference "
            "between classes, and that difference looks stable at the noise level; as the sample "
            "grows, the true discriminating factor — edge sharpness, i.e. gradient scatter — "
            "prevails. In other words, the «stable» leader of the small database was in fact a "
            "sample-specific artefact.",
        "r43c":
            "The coexistence of these two layers (within-database $I_C \\approx 0.9$, "
            "between-database top-3 agreement $0.33$) is not a contradiction: bootstrap replicates "
            "are drawn from one and the same distribution, so stability across them measures only "
            "**statistical** variance. Swapping the database changes the distribution itself and "
            "exposes **epistemic** uncertainty. High bootstrap stability is no guarantee that a "
            "feature list will transfer — this is the single most important practical conclusion.",

        "r44":
            "Fig. 4 shows the decreasing chain of the prefix functional $\\Phi(n')$: from "
            "$\\Phi(1) = 6.27$ down to $\\Phi(38) = 1.04$. The decrease is strictly monotone — a "
            "direct consequence of sorting by $r_j$ and an empirical confirmation of the lemma. "
            "The elbow of the curve lies near $n' \\approx 21$: beyond that point each added "
            "feature appreciably lowers the average informativeness, while balanced accuracy still "
            "continues to rise. The divergence of the two criteria is a reminder that "
            "informativeness and classification benefit are not the same thing: a weakly "
            "informative feature may, in combination with others, help isolate a small class.",

        "d1":
            "The results obtained compel several methodological conclusions. **First**, every "
            "publication on feature selection must report a stability measure, and that measure "
            "must be chance-corrected: we have shown that at large $n'$ the Jaccard coefficient "
            "climbs to $0.99$ and creates an impression of «perfect stability» — when in reality "
            "it merely reflects the saturation of the sets.",
        "d2":
            "**Second**, a feature ranking obtained on a small sample must never be generalised as "
            "«the list of most informative features». In our case 519 ROIs appear numerous enough "
            "(most publications use fewer), yet its top-3 agreed with the top-3 on 13,968 ROIs by "
            "only 33%. This bears directly on the reproducibility crisis in radiomics: it is one "
            "reason why the textural features proclaimed «most important» contradict one another "
            "from paper to paper.",
        "d3":
            "**Third**, the optimal cardinality $n'^{*}$ grows with sample size ($34 \\to 36$), "
            "because a larger sample permits a reliable estimate of the covariance structure of "
            "more features. The growth is nonetheless slow: a 27-fold increase in size added just "
            "two features to the cardinality. Hence $n'^{*}$ is a parameter only weakly sensitive "
            "to the sample — a practical advantage of the method.",
        "d4":
            "**Limitations.** The analysis is confined to a single-centre archive; inter-scanner "
            "(multi-scanner) variability was not measured. The feature set is limited to 38 "
            "hand-designed descriptors; the properties of the $r_j$ ranking for deep-network "
            "embeddings require separate verification. Finally, in the least populated classes "
            "(architectural distortion — 13 ROIs) the stability estimates have low statistical "
            "power.",

        "c": [
            "Boolean-programming feature selection has been compared, for the first time, on "
            "mammographic databases differing in size by two orders of magnitude. The prefix lemma "
            "is confirmed empirically: $\\Phi(n')$ forms a strictly decreasing chain.",
            "The procedure is highly reproducible within a single database — on the large database "
            "the Kuncheva index exceeds $0.830$ at every cardinality.",
            "Across databases the full sequence agrees ($\\rho = 0.937$), yet the head of the "
            "ranking moves: top-3 agreement is $0.333$. The leader of the small database (GLCM "
            "correlation) drops out of the top five on the large one.",
            "The optimal cardinality depends only weakly on sample size: $n'^{*}$ shifted from "
            "$34$ to $36$; on the large database balanced accuracy is $0.638$ [0.606; 0.762] and "
            "macro ROC-AUC is $0.947$ [0.928; 0.960].",
            "Practical recommendation: when publishing a feature ranking, state the sample size on "
            "which it was obtained, compute a chance-corrected stability index, and do not call the "
            "head of the ranking «universal» without confirming it on an independent database.",
        ],
    },
}
