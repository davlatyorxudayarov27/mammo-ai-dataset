---
title: ""
---

::: {custom-style="TitleCenter"}
**O'ZBEKISTON RESPUBLIKASI OLIY TA'LIM, FAN VA INNOVATSIYALAR VAZIRLIGI**
:::

::: {custom-style="TitleCenter"}
**[OLIY TA'LIM MUASSASASI NOMI]**
:::

\

\

::: {custom-style="RightAlign"}
*Qo'lyozma huquqida*

UDK 004.93+004.8
:::

\

\

\

::: {custom-style="TitleCenter"}
**TURAQULOV SHOXRUX XUDAYAROVICH**
:::

\

\

::: {custom-style="TitleCenter"}
**MULTILINGUAL KLINIK MATNLAR VA MAMMOGRAFIYA TASVIRLARI UCHUN MULTIMODAL SUN'IY INTELLEKT ASOSIDA KO'KRAK BEZI SARATONIGA TASHXIS QO'YISH ALGORITMLARI**
:::

\

\

::: {custom-style="CenterText"}
05.01.11 — Raqamli texnologiyalar va sun'iy intellekt
:::

\

\

::: {custom-style="CenterText"}
Texnika fanlari bo'yicha falsafa doktori (PhD)

ilmiy darajasini olish uchun yozilgan

**DISSERTATSIYA**
:::

\

\

::: {custom-style="RightAlign"}
**Ilmiy rahbar:** [familiya ismi otasining ismi],

texnika fanlari doktori, professor
:::

\

\

\

::: {custom-style="CenterText"}
[Shahar nomi]–2026
:::

\newpage

# MUNDARIJA

[Mundarija avtomatik ravishda Word'da yangilanadi: References → Update Table]

\newpage

# KIRISH

**Dissertatsiya mavzusining dolzarbligi va zarurati.** Jahonda onkologik kasalliklar, ayniqsa ko'krak bezi saratoni, ayollar o'limining yetakchi sabablaridan biri bo'lib qolmoqda. Jahon Sog'liqni Saqlash Tashkiloti (JSST) ma'lumotlariga ko'ra, 2022-yilda dunyo bo'ylab 2.3 milliondan ortiq ayolda ko'krak bezi saratoni aniqlangan va 670 mingga yaqin ayol shu kasallikdan vafot etgan. Erta tashxislash 5 yillik yashash ko'rsatkichini sezilarli darajada — I-II bosqichlarda 95%dan ortiq, III-IV bosqichlarda 25%dan kam darajaga oshirish imkonini beradi. Mammografiya skriningi ko'krak bezi saratonining oltin standart tashxislash usuli bo'lib qolmoqda, biroq uning samaradorligi radiologning tajribasi va tasvirning sifatiga bog'liq.

So'nggi yillarda sun'iy intellekt (SI), xususan chuqur o'qitish texnologiyalari tibbiy tasvirlarni avtomatik tahlil qilishda sezilarli muvaffaqiyatlarga erishdi. Mammografiya bo'yicha bir qator yetakchi tijorat tizimlari (Lunit INSIGHT MMG, ScreenPoint Transpara, iCAD ProFound AI) AQSh va Yevropa bozorlarida mavjud. Biroq bu tizimlarning barchasi *faqat tasvirga* asoslangan bo'lib, klinik matn (radiologik xulosalar, anamnestik ma'lumotlar) bilan ishlamaydi va asosan ingliz tilida o'qitilgan. O'zbekiston va boshqa post-sovet markaziy Osiyo davlatlarida mammografiya bilan birga keladigan klinik matn **uch xil yozuvda** — o'zbek-kirill, o'zbek-lotin va rus tillarida, ko'pincha bir hujjat ichida aralash holda — yoziladi. An'anaviy ko'p tilli NLP modellari (mBERT, XLM-R) ushbu kontekst uchun mos kelmaydi: ular og'ir, qimmat va ko'pincha mahalliy klinik leksikani noto'g'ri qabul qiladi.

Jahon miqyosida ushbu yo'nalishda, jumladan AQSh, Buyuk Britaniya, Yaponiya, Janubiy Koreya, Hindiston, Xitoy, Germaniya, Fransiya, Kanada va Rossiya Federatsiyasi mamlakatlarida tibbiy tasvirlar va matnlarni multimodal tahlil qilish, weak supervision (zaif nazoratlash) va radiolog-in-the-loop verifikatsiya tizimlari bo'yicha keng qamrovli ilmiy-tadqiqot ishlari olib borilmoqda.

Respublikamizda mazkur yo'nalishda tibbiy tasvirlar tahliliga asoslangan tashxislash tizimlarini ishlab chiqish va amaliyotda qo'llash bo'yicha kompleks chora-tadbirlar yaratishga alohida e'tibor qaratilmoqda. O'zbekiston Respublikasini yanada rivojlantirish bo'yicha "O'zbekiston-2030" strategiyasi 17-bandida belgilangan onkologik kasalliklarni erta aniqlash va o'lim ko'rsatkichini kamaytirish vazifasi, ya'ni *«30–69 yoshdagi aholi orasida onkologik kasalliklarni profilaktik ko'riklarda, erta bosqichlarida aniqlab, 5 yillik umr davomiyligi ko'rsatkichlarini 2 barobar oshirish, 1 yilgacha o'lim ko'rsatkichini 2 barobar kamaytirish»* vazifalari belgilangan. Mazkur dissertatsiya ana shu vazifalarni amalga oshirishga muayyan darajada xizmat qiladi.

O'zbekiston Respublikasi Prezidentining 2020-yil 5-oktabridagi PF-6079-son «Raqamli O'zbekiston-2030 strategiyasini tasdiqlash va uni samarali amalga oshirish chora-tadbirlari to'g'risida»gi Farmoni, 2021-yil 17-fevraldagi PQ-4996-son «Sun'iy intellekt texnologiyalarini jadal joriy etish uchun shart-sharoitlar yaratish chora-tadbirlari to'g'risida»gi Qarori va boshqa me'yoriy-huquqiy hujjatlarda belgilangan vazifalarni amalga oshirishga ushbu dissertatsiya tadqiqoti muayyan darajada xizmat qiladi.

**Tadqiqotning respublika fan va texnologiyalari rivojlanishining ustuvor yo'nalishlariga mosligi.** Mazkur tadqiqot respublika fan va texnologiyalar rivojlanishining IV. *«Axborotlashtirish va axborot kommunikatsiya texnologiyalarini rivojlantirish»* ustuvor yo'nalishiga mos ravishda bajarilgan.

**Muammoning o'rganilganlik darajasi.** Tibbiy tasvirlarga ishlov berish, tahlil qilish va tanib olish modellari, usul va algoritmlarini ishlab chiqish hamda ularning amaliy qo'llanilishi R. Gonzales, R. Woods, L. Shapiro, G. Stockman, V.V. Aleksandrov, N.D. Gorskiy, R.O. Duda, Y.I. Juravlyov, N.Yu. Ilyasova, U.K. Prett, V.A. Soyfer, V.V. Starovoytov, P.I. Xart va boshqa xorijiy olimlarning ilmiy ishlarida o'rganilgan.

Mammografiya tasvirlarini avtomatik tahlil qilishda CNN-asosli modellar (D. Ribli, A. Akselrod-Ballin), FCOS-style anchor-free detektorlar (Z. Tian va h.k.), U-Net segmentatsiya (O. Ronneberger), GAN-asosli sintetik tasvirlar yaratish (I. Goodfellow, J. Zhu) tadqiqotlari mashhurdir. Ko'p tilli klinik matnlarni qayta ishlashda T. Mikolov, A. Vaswani, J. Devlin, A. Conneau, T. Wolf, G.I. Winata kabi tadqiqotchilarning ishlari fundamental ahamiyatga ega.

O'zbekistonda timsollarni tanib olish hamda tasvirlarga ishlov berish va tahlil qilishning nazariy asoslarini rivojlantirishga M.M. Kamilov, S.S. Sodiqov, F.T. Adilova, Sh.E. Tulyaganov, E.M. Aliyev, Sh.X. Fazilov, R.X. Xamdamov, N.M. Mirzayev, N.S. Mamatov, S.S. Radjabov va boshqalar o'zlarining katta hissalarini qo'shganlar.

Mualliflik tomonidan tibbiy tasvirlarni qayta ishlash sohasida olib borilgan oldingi tadqiqotlar — fraktal raqamli qayta ishlash usullari (EHM № DGU 36888) va MRT tasvirlarini bipolyar noravshan to'plamlar bilan chuqur o'qitish modellari yordamida tasniflash (EHM № DGU 45451) — mazkur dissertatsiyada multimodal mammografiya tashxis tizimini yaratish uchun nazariy va amaliy asos bo'lib xizmat qildi.

Hozirgi kunda tibbiy tasvirlarni qayta ishlash sohasidagi zamonaviy tadqiqotlar tahlili ko'rsatadiki:

(a) **mavjud mammografiya tashxis tizimlarining aksariyati monomodal** (faqat tasvir bilan ishlaydi) bo'lib, klinik matn ichidagi qimmatli ma'lumotlarni e'tiborga olmaydi;

(b) **ko'p tilli — kod-aralash klinik matnlarni** (o'zbek-kirill, o'zbek-lotin, rus) bir vaqtda qayta ishlovchi yengil va samarali NLP modellari adabiyotda yetarli darajada o'rganilmagan;

(c) mahalliy DICOM tasvirlar uchun **bbox annotatsiyalar yo'q** holatda multimodal detektorni qanday o'qitish bo'yicha amaliy yopiq tsikl yondashuv ishlab chiqilmagan;

(d) klinik matndagi spatial ko'rsatmalar (lateralligi, kvadrant, soat pozitsiyasi, o'lcham) asosida **piksel fazoda zaif annotatsiyalar** sintez qilish va keyinchalik radiolog tomonidan tasdiqlash uchun yagona ishlab chiqarish darajasidagi tizim mavjud emas.

Shu sababli, multilingual klinik matnlarni script-aware tahlil qilish, multimodal mammografiya detektorini ishlab chiqish va radiolog-in-the-loop yopiq tsikl tizimini yaratish bilan bog'liq masalalarni hal etish dolzarb hisoblanadi.

**Dissertatsiya tadqiqotining dissertatsiya bajarilgan oliy ta'lim va ilmiy-tadqiqot muassasasining ilmiy-tadqiqot ishlari rejasi bilan bog'liqligi.** Dissertatsiya tadqiqoti [muassasa nomi] ilmiy-tadqiqot ishlari rejasining "[mavzu nomi]" (2024–2026) mavzudagi tadqiqot ishlari doirasida bajarilgan.

**Tadqiqotning maqsadi** — o'zbek-kirill, o'zbek-lotin va rus tillaridagi kod-aralash mammografiya klinik matnlarini script-aware usulda tasniflash, ko'krak bezi saratoniga oid tasvir va matn ma'lumotlarini multimodal tarzda birlashtiruvchi neyron tarmoq arxitekturasi (TILLNet-Det) hamda radiolog-in-the-loop yopiq tsiklli MAMOGRAF dasturiy majmuasini ishlab chiqishdan iborat.

**Tadqiqotning vazifalari:**

– o'zbek-kirill, o'zbek-lotin va rus tillaridagi kod-aralash klinik matnlarni qayta ishlashning zamonaviy holatini tahlil qilish va tadqiqot masalasini shakllantirish;

– skript bo'yicha bo'lingan TF-IDF oqimlariga asoslangan ko'p tilli klinik matn klassifikatori (XS-Classifier) algoritmini ishlab chiqish;

– matnni 256-element ASCII bucket'lariga akslantiruvchi, multilingual klinik matnlarni qayta ishlovchi 4-qatlamli xarakter darajasidagi Transformer matn enkoderini ishlab chiqish;

– *zero-init FiLM* fuzioni asosida tasvir va matn xususiyatlarini multimodal birlashtiruvchi TILLNet-Det neyron tarmog'i arxitekturasini ishlab chiqish va uning matematik xossalarini isbotlash;

– klinik matndagi spatial cue'lar (lateralligi, kvadrant, soat pozitsiyasi, o'lcham) asosida piksel fazoda zaif annotatsiyalarni avtomatik sintez qiluvchi multilingual weak supervision quvuri (pipeline)ni ishlab chiqish;

– 3-bosqichli o'qitish kurrikulumi: (i) CBIS-DDSM ommaviy ma'lumotlar to'plamida bootstrap, (ii) text-guided pseudo-labels'da fine-tune, (iii) radiolog tomonidan tasdiqlangan gold-labels'da Stage-3 fine-tune;

– FastAPI backend va vanilla JS + SVG frontend asosida MAMOGRAF dasturiy majmuasini ishlab chiqish, unda 5 ta REST API endpoint asosida radiolog verifikatsiya UI'ini ichki integratsiya qilish;

– taklif etilgan algoritmlarning samaradorligini real ma'lumotlar to'plami asosida tajribaviy tasdiqlash, mavjud baseline'lar bilan statistik solishtirish (paired *t*-test, Wilcoxon).

**Tadqiqotning obyekti** sifatida o'zbek-kirill, o'zbek-lotin va rus tillarida yozilgan ko'p tilli mammografiya klinik matnlari va ularga mos rentgen mammografiya DICOM tasvirlari qaralgan.

**Tadqiqotning predmeti**ni multilingual klinik matnlar va mammografiya tasvirlarini multimodal tarzda qayta ishlash hamda tahlil qilish usullari, modellari va algoritmlari tashkil etadi.

**Tadqiqotning usullari.** Tadqiqotni olib borish jarayonida diskret matematika, ehtimollar nazariyasi va matematik statistika, tasvirlarga ishlov berish, optimallashtirish nazariyasi, kompyuterli ko'rish, mashinaviy o'qitish, chuqur o'qitish, tabiiy tilni qayta ishlash hamda ma'lumotlarni intellektual tahlil qilish usullaridan foydalanilgan.

**Tadqiqotning ilmiy yangiligi quyidagilardan iborat:**

– **skript-adaptiv ko'p tilli matn klassifikatsiya algoritmi (XS-Classifier)** ishlab chiqilgan: o'zbek-kirill, o'zbek-lotin va rus tilidagi kod-aralash klinik matnlarni har bir Unicode-bloki bo'yicha alohida bo'lingan TF-IDF oqimlari sifatida vakillaydi va keyinchalik konkatenatsiya qilingan vektor ustida L2-tartibga solingan logistik regressiya orqali tasniflaydi;

– **xarakter darajasidagi multilingual matn enkoderi** ishlab chiqilgan: 256-element vocabularidan foydalanib, tashqi tokenizator yoki til detektoriga ehtiyojsiz kod-aralash uchta yozuvni yagona embedding fazosida qayta ishlaydi;

– **zero-init FiLM (Feature-wise Linear Modulation) fuzioni** taklif etilgan, unda har bir piramida darajasidagi $\boldsymbol{\gamma}_l, \boldsymbol{\beta}_l$ parametrlari nol bilan boshlanadi, bu esa modelni *initsializatsiya paytida tasvir-faqat baseline'ga matematik teng* qilib qo'yadi (Tasdiq 1, §3.4);

– **TILLNet-Det multimodal detektor arxitekturasi** ishlab chiqilgan: ResNet-50 + 5-darajali FPN + char-Transformer matn enkoderi + zero-init FiLM modulyatori + FCOS-asosli detection head'dan iborat;

– **multilingual weak supervision quvuri** taklif etilgan: 9 ta tilshunoslik regex pattern, ko'rinish-aware spatial proyeksiya va o'z-o'zini baholovchi confidence score asosida klinik matndan piksel fazoda bbox sintez qiladi;

– **3-bosqichli o'qitish kurrikulumi va radiolog-in-the-loop yopiq tsikl** taklif etilgan: ommaviy bootstrap → matn-asosli pseudo-labels → radiolog tomonidan tasdiqlangan gold-labels;

– **MAMOGRAF dasturiy majmuasi va integratsiyalashgan radiolog verifikatsiya UI'i** ishlab chiqilgan: 5 ta REST API endpoint, JWT/2FA autentifikatsiya, PACS integratsiyasi, audit log va de-identifikatsiya bilan jihozlangan ishlab chiqarish darajasidagi dastur.

**Tadqiqotning amaliy natijalari quyidagilardan iborat:**

– XS-Classifier algoritmi 1839 ta haqiqiy mammografiya klinik yozuvi ustida 5-fold stratified cross-validation orqali tekshirilgan va $\text{aniqlik} = 0{,}9821 \pm 0{,}007$, $F_1 = 0{,}9544 \pm 0{,}015$, $\text{AUROC} = 0{,}9931$, $\text{AUPRC} = 0{,}9676$ ko'rsatkichlariga erishgan, char $n$-gram baseline'idan paired *t*-test bo'yicha $p = 0{,}008$ darajasida statistik ahamiyatga ega ravishda ustun chiqqan;

– TILLNet-Det modeli to'liq multimodal versiyada $36{,}52$ M, image-only ablation versiyada $32{,}11$ M parametrga ega bo'lib, FiLM modullarining identity-at-initialisation xossasi machine precision aniqligida tasdiqlangan ($\max |\Delta| = 0{,}0$);

– MAMOGRAF dasturiy majmuasi $\sim 23$ KLOC Python va $\sim 4{,}4$ KLOC JavaScript hajmidagi ishlab chiqarish darajasidagi tizim sifatida joriy etilgan;

– 10-bosqichli to'liq tadqiqot pipeline'i (run\_pipeline.py) yagona buyruq orqali idempotent va resumable tarzda barcha bosqichlarni dispatch qiladi.

**Tadqiqot natijalarining ishonchliligi** algoritmlarni ishlab chiqishda tasvirlarga ishlov berish, tabiiy tilni qayta ishlash, optimallashtirish va matematik statistika apparatining to'g'ri qo'llanilganligi, paired *t*-test va Wilcoxon kabi statistik testlarning qo'llanilishi hamda 1839 ta haqiqiy klinik yozuv ustida o'tkazilgan tajribaviy tadqiqotlarning ijobiy natijalari bilan tasdiqlanadi.

**Tadqiqotning ilmiy va amaliy ahamiyati.** Tadqiqot natijalarining ilmiy ahamiyati ishlab chiqilgan va takomillashtirilgan model, algoritm va arxitekturalar — xususan zero-init FiLM va Tasdiq 1 — multimodal sun'iy intellekt va tibbiy tasvirlarni tahlil qilish nazariy asoslarining istiqbolli rivojlanishiga hissa qo'shishi bilan izohlanadi.

Tadqiqot natijalarining amaliy ahamiyati ishlab chiqilgan dasturiy majmuani tibbiyot muassasalari, klinikalarida ko'krak bezi saratonini tashxislash va rejali davolash uchun to'g'ri qarorlar qabul qilishda muhim bo'lgan multilingual klinik matnlarni va mammografiya tasvirlarini birgalikda qayta ishlash masalalarini yechishga qo'llash mumkinligi bilan izohlanadi.

**Tadqiqot natijalarining joriy qilinishi.** Multilingual klinik matnlarni tasniflash, mammografiya tasvirlarida ko'krak o'sma sohalarini multimodal aniqlash va radiolog verifikatsiya tsiklli MAMOGRAF dasturiy majmuasi quyidagi tashkilotlarda joriy etilgan:

– [Tibbiyot muassasasi 1 nomi] — joriy etish to'g'risida [yil-kun-oy]dagi [hujjat raqami]-sonli ma'lumotnoma;

– [Tibbiyot muassasasi 2 nomi] — [yil-kun-oy]dagi [hujjat raqami]-sonli ma'lumotnoma;

– [Tibbiyot muassasasi 3 nomi] — [yil-kun-oy]dagi [hujjat raqami]-sonli ma'lumotnoma.

[*Eslatma: joriy etish dalolatnomalari mualliflik tomonidan to'ldiriladi.*]

**Tadqiqot natijalarining aprobatsiyasi.** Mazkur tadqiqot natijalari [N] ta xalqaro va [M] ta respublika ilmiy-amaliy anjumanlarida ma'ruza qilingan va muhokamadan o'tkazilgan.

**Tadqiqot natijalarining e'lon qilinganligi.** Tadqiqot mavzusi bo'yicha [K] ta ilmiy ish chop etilgan bo'lib, shulardan O'zbekiston Respublikasi Oliy attestatsiya komissiyasining dissertatsiyalar asosiy ilmiy natijalarini chop etish tavsiya etilgan ilmiy nashrlarda [N1] ta maqola, jumladan [N2] tasi xorijiy va [N3] tasi respublika jurnallarida nashr qilingan. Tadqiqot natijalari asosida quyidagi ilmiy maqolalar tayyorlangan:

1. *XS-Classifier: Cross-Script Adaptive Tokenization for Cancer Detection in Code-Switched Mammographic Reports* — Q1 jurnali uchun (Journal of Biomedical Informatics yoki AI in Medicine);

2. *TILLNet-Det: Text-Informed Lesion Localization Network for Multilingual Mammography Detection* — Q1 jurnali uchun (Medical Image Analysis);

3. *A Closed-Loop System for Multilingual Mammography Lesion Detection in Low-Annotation Settings* — Q1 jurnali uchun (Medical Image Analysis);

4. *BCA-YOLO: Bilateral Cross-Attention with Ipsilateral Consistency for Mammography* — Q2 jurnali uchun;

5. *MAMOGRAF: Unified Web-based Platform for Mammography DICOM Annotation, AI Inference and PACS Integration* — Q2-Q3 jurnali uchun.

Mualliflik tomonidan tibbiy tasvirlarni qayta ishlash sohasida quyidagi EHM uchun yaratilgan dasturiy vositalarga rasmiy guvohnomalar olingan:

– **№ DGU 36888** (27.04.2024) — *«Tibbiy tasvirlarni fraktal raqamli qayta ishlash»* (mualliflar: Soxibova X.D., Turaqulov Sh.X.) — mazkur dissertatsiyada bayon etilgan tibbiy tasvirlarga dastlabki ishlov berish algoritmlarining bevosita asosini tashkil etadi;

– **№ DGU 45451** (12.12.2024) — *«MRT tasvirlarini bipolyar noravshan to'plamlar orqali qayta ishlab chuqur o'qitish modellari yordamida tasniflash dasturi»* (mualliflar: Iskandarova S.N., Turaqulov Sh.X.) — chuqur o'qitish va noravshan to'plamlar bilan tibbiy tasvirlarni tasniflash bo'yicha mualliflik metodologiyasini ko'rsatadi.

Mazkur dissertatsiya doirasida tayyorlangan **MAMOGRAF dasturiy majmuasi** uchun EHM guvohnomasi olish jarayonida.

**Dissertatsiyaning tuzilishi va hajmi.** Dissertatsiya kirish, to'rtta bob, xulosa, foydalanilgan adabiyotlar ro'yxati va ilovalardan iborat. Dissertatsiya hajmi [bet soni] betni tashkil etadi.
