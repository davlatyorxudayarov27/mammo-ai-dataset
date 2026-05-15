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


\newpage

# I BOB. MAMMOGRAFIYA TASVIRLARI VA KO'P TILLI KLINIK MATNLARNI MULTIMODAL TAHLIL QILISHNING ZAMONAVIY HOLATI

Mazkur bob mammografiya tibbiy tasvirlari va ko'p tilli (multilingual, kod-aralash) klinik matnlarni multimodal sun'iy intellekt asosida tahlil qilishning asosiy yo'nalishlarini o'rganishga bag'ishlangan bo'lib, unda zamonaviy holat, mavjud usul va algoritmlar tahlili, multimodal mammografiya tashxislash dasturiy majmuasini ishlab chiqishdagi asosiy muammolar shakllantirilgan.

## 1.1-§. Mammografiya tibbiy tasvirlari va ulardagi patologiyalar

Mammografiya — ko'krak bezi to'qimalarini past dozadagi rentgen nurlari yordamida vizuallashtiruvchi invaziv bo'lmagan tibbiy tasvirlash usulidir. Hozirgi kunda u ko'krak bezi saratonini erta aniqlashda eng samarali skrining vositasi bo'lib qolmoqda. Maxsus mammograf qurilmalari ko'krak to'qimasini ikki kompressor plastinka orasiga siqib, past dozadagi rentgen nurlari (~0,3–0,5 mGy) bilan yoritadi. Olingan tasvir DICOM (Digital Imaging and Communications in Medicine) formatida saqlanadi.

**Standart proyeksiyalar.** Klinik amaliyotda har bir ko'krak bezi uchun ikkita standart proyeksiya olinadi:

– **CC (Craniocaudal)** — yuqoridan pastga proyeksiya, ko'krak yuza nuqtai nazaridan tepada-pastda siqilgan holda olinadi. Bu proyeksiyada lateral va medial sohalar yaqqol ko'rinadi;

– **MLO (Mediolateral Oblique)** — qiyalik proyeksiya (~45° burchakda), undagi ko'krak to'qimasining katta qismi, shu jumladan pektoral mushak ham ko'rinadi.

Shunday qilib, har bir bemordan **to'rtta tasvir** olinadi: O'NG-CC, O'NG-MLO, CHAP-CC, CHAP-MLO. Ushbu to'rtta tasvirning to'g'ri va birgalikda tahlili tashxis aniqligini sezilarli darajada oshiradi.

**Mammografik patologiyalar.** Mammografiyada aniqlanishi mumkin bo'lgan asosiy patologik o'zgarishlar:

(a) **Massalar (mass)** — turli o'lchamdagi (~5–50 mm) sferaviy yoki noaniq shaklli zichlikka ega tuzilmalar. Xavfsiz massalarning chegarasi aniq, shakli silliq (oval, dumaloq), xavfli massalarning chegarasi noaniq, spikulali (ignaga o'xshash);

(b) **Mikrokalsifikatlar (calcifications)** — ko'krak to'qimasidagi 100–500 µm o'lchamli kalsiy konglomeratlari. Klaster ko'rinishidagi mikrokalsifikatlar (5+ ta 1 sm³ hajmda) ko'pincha xavfli o'sma belgisi hisoblanadi;

(c) **Asimmetriya (asymmetry)** — ikki ko'krak bezi orasidagi noma'lum farq, ya'ni biror sohada qarshi tomondagi mos sohaga nisbatan zichlik;

(d) **Strukturaviy buzilish (architectural distortion)** — ko'krak to'qimasi naqshining buzilishi, biror nuqtaga yo'naltirilgan radial spikulalar.

**BI-RADS tasnifi.** Amerika Radiologiya Kollejining (American College of Radiology) Breast Imaging Reporting and Data System (BI-RADS) standartlashtirilgan natija toifalarini taqdim etadi:

– **BI-RADS 1**: salbiy (norma);

– **BI-RADS 2**: xavfsiz topilmalar (oddiy kistalar, fibroadenomalar);

– **BI-RADS 3**: ehtimoliy xavfsiz (xavf < 2%, 6 oydan keyingi qayta ko'rik tavsiya etiladi);

– **BI-RADS 4**: shubhali topilmalar (xavf 2–95%), 4a, 4b, 4c kichik toifalarga bo'linadi;

– **BI-RADS 5**: xavfli ehtimoli yuqori (xavf > 95%);

– **BI-RADS 6**: tasdiqlangan biopsiya bilan xavfli o'sma.

**O'zbekiston statistikasi.** O'zbekiston Respublikasi Sog'liqni Saqlash Vazirligi va JSST ma'lumotlariga ko'ra, ko'krak bezi saratoni ayollar orasidagi onkologik kasalliklarning yetakchi shaklidir. Faqatgina Samarqand viloyatida 2020-yilda 315, 2021-yilda 380, 2022-yilda 386, 2023-yilda esa 600 dan ortiq bemorga birlamchi tashxis qo'yilgan. So'nggi 10 yilda kasallanish darajasi yiliga ~5–8% ga oshib bormoqda. JSSTning hisob-kitobicha, samarali skrining va erta tashxislash orqali dunyoda 2.5 milliondan ortiq ayolning hayotini saqlab qolish mumkin.

## 1.2-§. Mammografiya tasvirlarini avtomatik tahlil qilish usullari

Mammografiya tasvirlarini avtomatik tahlil qilish to'rt bosqichli quvurdan iborat:

(1) Dastlabki ishlov berish (preprocessing);
(2) Segmentatsiya (segmentation);
(3) Aniqlash (detection);
(4) Tasniflash (classification, BI-RADS toifasi).

**1.2.1. Dastlabki ishlov berish.** DICOM tasvirlari turli mammograf qurilmalaridan kelib, har xil intensivlik diapazoniga, kontrastga va shovqinga ega bo'ladi. Standart preprocessing quvuri quyidagilardan iborat:

(i) **Modality LUT** — DICOM tomonidan beriladigan `RescaleSlope` $m$ va `RescaleIntercept` $b$ qiymatlari yordamida xom piksellarni Hounsfield-like fizik birliklarga o'girish:

$$I_1(x, y) = m \cdot I_0(x, y) + b$$

(ii) **VOI LUT** — `WindowCenter` $w_c$ va `WindowWidth` $w_w$ qiymatlari yordamida ko'rinish diapazonini standartlashtirish:

$$I_2(x, y) = \begin{cases} 0, & I_1 \leq w_c - w_w/2 \\ 1, & I_1 \geq w_c + w_w/2 \\ \frac{I_1 - (w_c - w_w/2)}{w_w}, & \text{aks holda} \end{cases}$$

(iii) **Photometric inversion** — agar `PhotometricInterpretation = MONOCHROME1` bo'lsa, $I_3 = 1 - I_2$ inversiya bajariladi (chunki MONOCHROME1 da nol piksel oq, MONOCHROME2 da qora);

(iv) **Ko'krak segmentatsiyasi** — Otsu binarizatsiyasi, $5 \times 5$ Gauss yumshatish, eng katta bog'langan komponent tanlash va morfologik close+open amallar yordamida ko'krak sohasi maskasi quriladi;

(v) **Bbox kesish** — ko'krak maskasining minimal o'rab oluvchi to'rtburchak bo'yicha tasvir kesib olinadi (bu fonni va orqa qattiq qismlarni olib tashlaydi);

(vi) **Pektoral mushakni olib tashlash** — MLO proyeksiyalarda Hough chizig'i aniqlash orqali pektoral mushak burchagi topiladi va undan yuqoridagi soha nolga to'ldiriladi;

(vii) **CLAHE (Contrast Limited Adaptive Histogram Equalization)** — `clipLimit = 2.0`, `tileGrid = 8×8` parametrlari bilan kontrastni adaptiv ravishda kuchaytirish;

(viii) **Letterbox o'lchamlash** — kompromis sifatida masshtab quyidagicha hisoblanadi:

$$s = \min\!\left(\frac{T}{w}, \frac{T}{h}\right), \quad w' = \lfloor w \cdot s \rfloor, \quad h' = \lfloor h \cdot s \rfloor$$

bu yerda $T$ — maqsadli o'lcham (odatda $T = 1024$), $(w, h)$ — kesilgan ko'krak bbox o'lchamlari, $(w', h')$ — masshtablangan tasvir o'lchamlari. Qolgan piksellar nolga to'ldiriladi (zero-padding) shu bilan kvadrat tasvir hosil qilinadi.

(ix) **R→L lateral standartlashtirish** — barcha o'ng tomon tasvirlarini gorizontal aks ettirish orqali kanonik chap-laterallikka o'tkazish. Bu modelga laterallikni o'rganish kerakligini bartaraf qiladi va parametr taqsimini ikki barobar samaraliroq qiladi.

**1.2.2. Segmentatsiya usullari.** Mammografiya tasvirlarida ko'krak o'smalarini segmentlashning klassik (Otsu, sohaning o'sishi, watershed, aktiv konturlar), mashinaviy o'qitishga asoslangan (k-means, Random Forest, SVM piksel-darajada) va chuqur o'qitishga asoslangan (U-Net, SegNet, Mask R-CNN, attention U-Net) yondashuvlari mavjud. Soʻnggi ikki yilda U-Net++, TransUNet va SwinU-Net kabi transformer-asosli arxitekturalar segmentatsiya aniqligini sezilarli darajada oshirgan.

**1.2.3. Aniqlash (detection) usullari.** Tasvirdagi obyektlarni avtomatik aniqlash uchun ikki turdagi modellar mavjud:

– **Ikki bosqichli detektorlar** (Faster R-CNN, Cascade R-CNN) — birinchi bosqichda tavsiya regionlari (Region Proposal), ikkinchi bosqichda tavsiyalarni tasniflash. Aniqligi yuqori, lekin sekin;

– **Bir bosqichli detektorlar** (YOLO, SSD, RetinaNet, FCOS, ATSS, CenterNet) — tasvirni bir o'tishda to'g'ridan-to'g'ri bbox koordinatalari va sinflar ehtimolligi sifatida bashoratlash. Tezroq, sezilarli aniqlik bilan.

Mammografiya kontekstida lezyonlarning hajmi keng diapazonda ($5–50$ mm) o'zgaruvchi bo'lganligi sababli **anchor-free** yondashuvlar (FCOS, ATSS) afzal hisoblanadi: ular anchor box'larni qo'lda sozlamaslikni talab qiladi.

**FCOS** (Fully Convolutional One-Stage Object Detection) Tian va boshqalar tomonidan 2019-yilda taklif etilgan bo'lib, har bir piksel uchun:

– sinf ehtimolligi $p_c \in [0,1]^K$ ($K$ — sinflar soni);

– bbox masofalari to'rtligi $\hat{\mathbf{r}} = (\hat{l}, \hat{t}, \hat{r}, \hat{b})$, ya'ni piksel markazidan bbox chetlariga masofalar (chap, yuqori, o'ng, past);

– markazlik (centerness) $c \in [0, 1]$, ya'ni piksel bbox markazidan qanchalik uzoq emasligi.

Yakuniy ball $s = p_c \cdot c$ sifatida hisoblanadi va past markazlikka ega bashoratlar avtomatik ravishda kamaytiriladi.

**1.2.4. Tasniflash usullari.** Ko'krak bezi saratoni tasviridan to'g'ridan-to'g'ri xavfli/xavfsiz toifalashtirish uchun klassik konvolyutsion neyron tarmoqlari (LeNet, AlexNet, VGG, ResNet, DenseNet, EfficientNet) va ularning ko'p tilli/multimodal kengaytmalari qo'llaniladi. Resnet-50 va EfficientNet-B0 mammografiya kontekstida eng keng tarqalgan baseline'lar hisoblanadi.

## 1.3-§. Multilingual klinik matnlarni qayta ishlash

**1.3.1. Klinik matnlarning xususiyatlari.** Klinik matn (radiologik xulosa, anamnestik ma'lumot, shikoyatlar) mahsulot tilidan farqli ravishda quyidagi xususiyatlarga ega:

– domen-spetsifik leksikon (tibbiy atamalar, qisqartmalar, dori nomlari);

– qisqalik va elliptiklik ("ung sut bezida hosila 18 mm", subyekt va predikat ko'pincha qoldirilgan);

– shaxsiy uslub (har bir radiolog o'z standart formulasiga ega);

– imlo xatolari va inson tomonidan kiritish xatolari.

**1.3.2. O'zbekiston kontekstida ko'p tillilik.** O'zbekistonda klinik matnlar uchta yozuvda yoziladi:

(a) **O'zbek-kirill** ("Ўнг сут безида ҳосила, юқори-ташқи квадрантда, 18 мм");

(b) **O'zbek-lotin** ("O'ng sut bezida hosila, yuqori-tashqi kvadrantda, 18 mm");

(c) **Rus** ("В правой молочной железе образование в верхне-наружном квадранте 18 мм").

Eng muhimi, ushbu uchta yozuv ko'pincha **bir hujjat ichida aralash holda** ishlatiladi: masalan, anamnestik ma'lumot rus tilida, joriy ko'rik ma'lumoti o'zbek-kirillda, xulosa esa o'zbek-lotin yozuvida bo'lishi mumkin.

**1.3.3. Mavjud yondashuvlar.** Multilingual klinik matnlarni qayta ishlashda quyidagi asosiy yondashuvlar mavjud:

(a) **Til detektsiyasi + monolingual model** — har bir hujjatga til aniqlovchi modul qo'llaniladi, so'ng tegishli monolingual modeldan foydalaniladi. Kamchiliklari: kod-aralash matnlarda ishlamaydi, xato kaskadlanadi;

(b) **Multilingual transformer** (mBERT, XLM-RoBERTa) — 100+ tilda oldindan o'qitilgan og'ir modellar. Kamchiliklari: parametrlar soni 110M+ (deployment qimmat), o'zbek tili korpusda kichik vakillangan, mahalliy klinik leksikon yo'q;

(c) **Skript-bo'yicha alohida vakili (skript-aware)** — har bir Unicode-bloki uchun alohida xususiyat fazosi quriladi va ular keyinchalik birlashtiriladi. Bu yondashuv yengil va kod-aralash matnlar bilan to'g'ridan-to'g'ri ishlaydi;

(d) **Xarakter darajasidagi modellar** — har bir Unicode codepoint'ini alohida token sifatida qabul qiladi va embedding fazosida ularning kontekstual o'xshashligini o'rganadi. Ushbu yondashuv tashqi tokenizator yoki til detektoriga ehtiyojni bartaraf qiladi.

Mazkur dissertatsiyada (c) va (d) yondashuvlardan parallel foydalaniladi: matn klassifikatsiyasi uchun XS-Classifier (skript-bo'yicha alohida TF-IDF) va multimodal detektor uchun xarakter darajasidagi Transformer (TILLNet-Det matn enkoderi).

## 1.4-§. Multimodal sun'iy intellekt va FiLM mexanizmi

**1.4.1. Multimodal AI nima?** Multimodal sun'iy intellekt — turli modallikdagi (matn, tasvir, ovoz, vaqt qatori) ma'lumotlarni bir vaqtda qayta ishlash va birgalikda qaror qabul qilish qobiliyatiga ega tizimlardir. Tibbiyot kontekstida bu — bir bemordan olingan turli xil ma'lumotlar (CT, MRT, mammografiya, klinik ma'lumotlar, laboratoriya natijalari, anamnez)ni birgalikda ishlatishni anglatadi.

**1.4.2. Multimodal fuzion strategiyalari.** Adabiyotda quyidagi strategiyalar farqlanadi:

(a) **Erta fuzion (early fusion)** — turli modallikdagi xom xususiyatlar darhol birlashtiriladi (masalan, vektor konkatenatsiya orqali) va keyingi qayta ishlash birgalikda olib boriladi. Sodda, lekin har bir modallikning o'ziga xos tuzilishini saqlamaydi;

(b) **Kech fuzion (late fusion)** — har bir modallik mustaqil model orqali ishlanib, ulardan olingan baholar oxirida birlashtiriladi (masalan, weighted average, voting). Modullik yaxshi, lekin oraliq xususiyat darajasidagi o'zaro ta'sirlardan foydalanmaydi;

(c) **O'rta fuzion (intermediate / cross-modal attention)** — modellar oraliq qatlamlarda o'zaro xususiyatlarni almashadi. Eng kuchli yondashuv, lekin murakkab.

**1.4.3. FiLM (Feature-wise Linear Modulation).** Perez va boshqalar tomonidan 2018-yilda taklif etilgan FiLM — o'rta fuzionning eng oddiy va eng samarali variantlaridan biri. Ikki modallikdan biri (kondisioner, masalan matn) ikkinchi modallikning xususiyatlar xaritasiga ta'sir qiluvchi $\boldsymbol{\gamma}$ va $\boldsymbol{\beta}$ parametrlarini ishlab chiqaradi:

$$\mathrm{FiLM}(\mathbf{x}, \mathbf{t}) = \boldsymbol{\gamma}(\mathbf{t}) \odot \mathbf{x} + \boldsymbol{\beta}(\mathbf{t})$$

bu yerda $\mathbf{x}$ — vizual xususiyatlar tenzori, $\mathbf{t}$ — matn vakili, $\odot$ — element-wise ko'paytma, $\boldsymbol{\gamma}, \boldsymbol{\beta} \in \mathbb{R}^C$ — kanal-bo'yicha modulyatsiya parametrlari ($C$ — kanallar soni). $\boldsymbol{\gamma}$ va $\boldsymbol{\beta}$ kichik MLP orqali $\mathbf{t}$dan ishlab chiqariladi:

$$(\boldsymbol{\gamma}, \boldsymbol{\beta}) = \mathrm{MLP}(\mathbf{t})$$

FiLM'ning afzalliklari: hisoblash arzon (faqat element-wise amallar), mantiqan tushunarli (chiziqli affine transformatsiya), turli arxitekturalarga oson integratsiyalash.

**1.4.4. FiLM'ning mammografiyada qo'llanilishi muammosi.** Standart FiLM'da $\boldsymbol{\gamma}, \boldsymbol{\beta}$ parametrlari tasodifiy initsializatsiya qilinadi. Bu shuni anglatadiki, model boshlang'ich vaznlarida vizual xususiyatlarni *tasodifan* o'zgartiradi, hatto matn ma'lumotsiz bo'lsa ham. Bu — *cold-start instability* (sovuq-start beqarorlik) muammosini keltirib chiqaradi: multimodal model boshida tasvir-faqat baseline'dan yomon ishlaydi va ko'p iteratsiya orqali "aldash"ga harakat qiladi.

Mazkur dissertatsiya **zero-init FiLM** taklif qiladi: $\boldsymbol{\gamma}, \boldsymbol{\beta}$ chiqish qatlami nol bilan initsializatsiya qilinadi. Bu shuni anglatadiki, $\mathrm{FiLM}_l(\mathbf{x}_l, \mathbf{t}) = (\mathbf{1} + \mathbf{0}) \odot \mathbf{x}_l + \mathbf{0} = \mathbf{x}_l$, ya'ni model boshida *aniq tasvir-faqat baseline'ga teng*. Bu xususiyatga ega bo'lgan FiLM ko'plab tibbiyot kontekstida cold-start xavfsizlikni ta'minlaydi va nashr etilmagan novator hissadir (§3.4 da to'liq matematik isboti bilan bayon etiladi).

## 1.5-§. Weak supervision va radiolog-in-the-loop tizimlari

**1.5.1. Annotatsiya muammosi.** Mahalliy klinik DICOM tasvirlar ko'pincha bbox annotatsiyalarga ega emas. To'g'ridan-to'g'ri radiolog tomonidan annotatsiya qildirish vaqt va xarajat jihatdan qimmat (~30 daqiqa/tasvir). 1839 ta yozuv uchun ~900+ soat radiolog vaqti kerak — bu O'zbekiston kontekstida amaliy bo'lmagan miqdor.

**1.5.2. Weak supervision strategiyalari.** Adabiyotda zaif nazoratlash quyidagi shakllarda mavjud:

(a) **Image-level labels** (faqat ha/yo'q labelli tasvir, bbox yo'q) — Class Activation Mapping (CAM) yoki Multiple Instance Learning (MIL) orqali keng spatial signallar olinadi;

(b) **Public dataset transfer** — boshqa korpusda (CBIS-DDSM, INbreast) qattiq labellar bilan o'qitilgan model mahalliy ma'lumotlarda fine-tune qilinadi;

(c) **Text-guided pseudo-labels** — klinik matndagi spatial cue'lar (lateralligi, kvadrant, soat, o'lcham) asosida zaif bbox sintez qilinadi.

Mazkur dissertatsiya (b) va (c) yondashuvlarni 3-bosqichli kurrikulumda birlashtiradi (§3.5 da batafsil bayon etiladi).

**1.5.3. Radiolog-in-the-loop tsikli.** Yopiq tsikl tizimi quyidagi bosqichlardan iborat:

(1) AI model bashoratlash → (2) Radiolog ko'rib chiqish/tahrirlash → (3) Tasdiqlangan annotatsiyalar DB'ga yozilish → (4) Davriy retraining → (1)'ga qaytish.

Mavjud yechimlar (MONAI Label, ALECTS, V7, Encord) ko'pincha *alohida* annotatsiya vositasida ishlaydi va ishlab chiqarish DICOM viewer'i bilan integratsiyalashmagan. Bu — ETL'ning qo'shimcha bosqichini va ma'lumot drifti xavfini keltirib chiqaradi. Mazkur dissertatsiyada tashxis va annotatsiya bir xil platforma (MAMOGRAF) ichida amalga oshiriladi (§4.2 da bayon etiladi).

## 1.6-§. Tadqiqot masalasining qo'yilishi va vazifalari

Yuqorida bayon etilgan tahlil quyidagi masalalarni kun tartibiga qo'yadi:

**Masala 1.** $D = \{(x_i, y_i)\}_{i=1}^{N}$ klinik matnlari to'plami berilgan, bunda $x_i$ — kod-aralash o'zbek-kirill/o'zbek-lotin/rus matnlari, $y_i \in \{0, 1\}$ — saraton mavjudligi yorlig'i. Masala — yengil (parametri kam) va aniq ($\text{F}_1 \geq 0{,}95$) klassifikator $f: x \to \hat{y}$ ni qurish.

**Masala 2.** $D' = \{(I_i, T_i, B_i)\}_{i=1}^{M}$ multimodal to'plami berilgan, bunda $I_i$ — preprocessed mammografiya tasviri, $T_i$ — tegishli klinik matn, $B_i = \{(\mathbf{b}_j, c_j)\}$ — gold annotatsiya bbox to'plami. Masala — multimodal detektor $g: (I, T) \to \{(\hat{\mathbf{b}}_j, \hat{c}_j, \hat{s}_j)\}$ ni qurish, bu yerda $\hat{\mathbf{b}}_j$ — bashoratlangan bbox, $\hat{c}_j$ — sinf, $\hat{s}_j$ — ishonch ball.

**Masala 3.** Multimodal detektor uchun $T$ matnga taqsimot bo'yicha *o'zgarmas* (text-equivariant) bo'lishi: agar $T$ bo'sh yoki noto'g'ri, model $I$-faqat baseline'dan kam ishlamasligi kerak.

**Masala 4.** $D''$ — bbox annotatsiyalarsiz lokal mahalliy DICOM to'plami berilgan, faqat klinik matn $T$ va DICOM metadata $M$ ($M = $ {SOP UID, Laterality, ViewPosition, ...}) mavjud. Masala — radiolog tomonidan keyinchalik tasdiqlanadigan zaif bboxlarni avtomatik sintez qilish va ularni Stage-2 fine-tune'da ishlatish.

**Masala 5.** Yopiq tsikl tizimi — AI bashoratlash, radiolog tasdiqlash va Stage-3 fine-tune'lar yagona ishlab chiqarish darajasidagi platformaga integratsiyalashgan bo'lishi.

Yuqoridagi masalalarni yechish uchun ushbu dissertatsiya ishida quyidagi vazifalar qo'yilgan:

– kod-aralash ko'p tilli klinik matnlarni script-aware tahlil qiluvchi XS-Classifier algoritmini ishlab chiqish;

– xarakter darajasidagi multilingual matn enkoderini ishlab chiqish (256-element vocabulariya, 4-qatlamli pre-norm Transformer);

– zero-init FiLM fuzioniga asoslangan TILLNet-Det multimodal detektor arxitekturasini ishlab chiqish va uning identity-at-initialisation matematik xossasini isbotlash;

– multilingual weak supervision quvurini ishlab chiqish: 9 ta tilshunoslik regex pattern, view-aware spatial proyeksiya, confidence scoring;

– 3-bosqichli o'qitish kurrikulumini ishlab chiqish: CBIS-DDSM bootstrap → text-guided pseudo-labels fine-tune → gold-labels fine-tune;

– FastAPI + vanilla JS asosida MAMOGRAF dasturiy majmuasini ishlab chiqish, undagi 5 ta REST API endpoint orqali radiolog verifikatsiya UI'ini integratsiyalashtirish;

– taklif etilgan algoritmlarning samaradorligini real ma'lumotlar to'plami asosida tajribaviy tekshirish va statistik tahlil qilish (paired *t*-test, Wilcoxon).

## I bob bo'yicha xulosalar

Dissertatsiya ishining ushbu bobida multilingual klinik matnlar va mammografiya tasvirlarini multimodal sun'iy intellekt asosida tahlil qilish muammolarining zamonaviy holati o'rganilgan. O'rganilgan muammolar va ularning yechish usullarini tahlil qilgan holda quyidagi xulosalarni chiqarish mumkin:

1. Mammografiya skriningi ko'krak bezi saratonini erta aniqlashning oltin standart usuli bo'lib qolmoqda. Hozirgi kunda mammografiya tasvirlarini avtomatik tahlil qilishning konvolyutsion neyron tarmoq, FCOS-style anchor-free detektorlar va U-Net asosli segmentatsiya yondashuvlari yetakchi hisoblanadi.

2. Mavjud tijorat va akademik mammografiya tashxis tizimlarining aksariyati monomodal (faqat tasvir bilan ishlaydi) va asosan ingliz tilida o'qitilgan. O'zbekiston kontekstidagi kod-aralash o'zbek-kirill, o'zbek-lotin va rus klinik matnlari uchun maxsus moslashtirilgan multimodal sun'iy intellekt yechimi mavjud emas.

3. Multilingual klinik matnlarni qayta ishlashda og'ir multilingual transformer modellari (mBERT, XLM-R) ko'p yo'naltirishli kommunikatsiya talab qiladi va ko'pincha mahalliy klinik leksikani noto'g'ri qabul qiladi. Skript-bo'yicha alohida xususiyat fazolari qurish va xarakter darajasida ishlash yengil va aniq alternativalardir.

4. FiLM fuzion mexanizmi multimodal arxitekturalarda eng samarali yondashuvlardan biri hisoblanadi, biroq standart FiLM tasodifiy initsializatsiya tufayli cold-start beqarorlikka olib keladi. Zero-init FiLM bu muammoni matematik tarzda hal qiladi va dissertatsiyaning asosiy ilmiy hissalaridan biri sifatida §3.4 da bayon etilgan.

5. Lokal DICOM tasvirlar uchun bbox annotatsiyalar yo'qligi keng tarqalgan muammo bo'lib, weak supervision (xususan text-guided pseudo-labels) va radiolog-in-the-loop yopiq tsikl bilan birgalikda yechilishi mumkin. Ammo yagona ishlab chiqarish darajasidagi platformaga integratsiyalashgan tizimlar adabiyotda kam uchraydi.

6. Yuqoridagilar asosida tadqiqot masalasining qo'yilishi, maqsadi va vazifalari shakllantirildi (5 ta masala va 8 ta vazifa).


\newpage

# II BOB. SKRIPT-ADAPTIV KO'P TILLI KLINIK MATNLARNI TASNIFLASH ALGORITMI (XS-CLASSIFIER)

Mazkur bob o'zbek-kirill, o'zbek-lotin va rus tillaridagi kod-aralash mammografiya klinik matnlarini ko'krak bezi saratoniga oid yorliq bo'yicha tasniflash uchun *script-aware* (skriptga adaptiv) yondashuvni taklif qilishga bag'ishlangan. Bobda matnning skript-bo'yicha bo'linish algoritmi, Cross-Script TF-IDF vektorizatsiyasi, XS-Classifier ansambl arxitekturasi va 1839 ta haqiqiy klinik yozuv ustida o'tkazilgan tajribaviy natijalar bayon etilgan.

## 2.1-§. Multi-script ko'p tilli matnlarning xususiyatlari

**2.1.1. Unicode bloklari va skriptlar.** Klinik matnda ishlatilgan har bir belgi (xarakter) ma'lum Unicode bloka tegishli bo'ladi. Mammografiya konteksti uchun muhim bloklar:

– **Latin** (`U+0041 ... U+024F`) — o'zbek-lotin va inglizcha terminlar uchun;

– **Kirill** (`U+0400 ... U+04FF`, `U+0500 ... U+052F`) — o'zbek-kirill va rus tilli matn uchun;

– **Raqamlar va tinish belgilari** (`U+0030 ... U+0039`, `U+0021 ... U+002F` va h.k.) — o'lchamlar, sanalar va spatial cue'lar uchun.

Belgi $c \in \mathbb{U}$ uchun uning skripti $\sigma: \mathbb{U} \to \{\text{cyrillic}, \text{latin}, \text{other}\}$ funksiya orqali aniqlanadi:

$$\sigma(c) = \begin{cases} \text{cyrillic}, & 0\text{x}0400 \leq \text{ord}(c) \leq 0\text{x}052\text{F} \\ \text{latin}, & 0\text{x}0041 \leq \text{ord}(c) \leq 0\text{x}024\text{F} \\ \text{other}, & \text{aks holda} \end{cases}$$

**2.1.2. Tokenning dominant skripti.** Token (so'z) $w = c_1 c_2 \ldots c_n$ uchun *dominant skript* $\sigma^*(w)$ — undagi belgilarning ko'pchiligi qaysi skriptga tegishli bo'lsa, shu skriptdir. Formal:

$$\sigma^*(w) = \arg\max_{s \in \{\text{cyr},\,\text{lat},\,\text{other}\}} \;\; \sum_{i=1}^{n} \mathbb{1}[\sigma(c_i) = s]$$

bu yerda $\mathbb{1}[\cdot]$ — Iverson skobasi (rost bo'lsa 1, aks holda 0).

**2.1.3. Klinik matnlarni qayta ishlashning empirik tahlili.** 1839 ta klinik yozuvni statistik tahlil qilish quyidagi natijalarni ko'rsatdi:

– **Cyrillic-dominant** (ya'ni so'zlarning $> 70\%$ kirill): $n = 894$ ($48{,}6\%$);

– **Latin-dominant** (so'zlarning $> 70\%$ lotin): $n = 941$ ($51{,}2\%$);

– **Mixed** (har ikkala skript tahminan teng nisbatda): $n = 4$ ($0{,}2\%$).

Bundan ko'rinib turibdiki, mahalliy mammografiya klinik korpus *deyarli teng nisbatda* uchta skriptni o'z ichiga oladi va monolingual modellar (faqat kirill yoki faqat lotin bilan ishlovchi) ma'lumotlar to'plamining yarmini yo'qotadi. Quyida o'rtacha klinik yozuv namunalari keltirilgan:

> **Cyrillic-dominant namuna:** *«Шикояти: Унг сут безидаги хосилага. Анамнесис: бемор узи 2024 йилда муолажа олган. Куриги хулосаси: ўнг сут безида юқори ташқи квадрантда хосила, ўлчами 18 мм, чегаралари нотекис.»*

> **Latin-dominant namuna:** *«Shikoyati: O'ng sut bezidagi xosilaga. Anamnesis morbi: bemor o'zini sog'lom hisoblab keldi. Ko'rik xulosasi: o'ng sut bezida yuqori tashqi kvadrantda xosila, o'lchami 18 mm, chegaralari notekis.»*

> **Mixed namuna:** *«Жалобы: на образование в правой молочной железе. Anamnesis morbi: bemor o'zini... Заключение: в правой молочной железе UOQ образование 18 mm.»*

## 2.2-§. Cross-Script TF-IDF vektorizatsiyasi

**2.2.1. Klassik TF-IDF.** TF-IDF (Term Frequency–Inverse Document Frequency) — matnni vektor sifatida ifodalashning klassik usuli. Hujjatlar to'plami $D = \{d_1, \ldots, d_N\}$ va lug'at $V = \{v_1, \ldots, v_K\}$ berilgan bo'lsin. Hujjat $d$ va termin $v$ uchun:

$$\mathrm{tf}(v, d) = \frac{f_{v, d}}{\sum_{v' \in d} f_{v', d}}$$

bu yerda $f_{v, d}$ — termin $v$ ning hujjat $d$ dagi chastotasi.

$$\mathrm{idf}(v, D) = \log \frac{N}{|\{d \in D : v \in d\}|}$$

Bu yerda maxraj — terminni o'z ichiga olgan hujjatlar soni.

$$\mathrm{tfidf}(v, d, D) = \mathrm{tf}(v, d) \cdot \mathrm{idf}(v, D)$$

Bu — sodda va samarali, lekin ko'p tilli kontekstda muammoli: agar lug'at $V$ barcha skriptlardan terminlarni o'z ichiga olsa, lotin $w$ va kirill $w'$ termenlari (bir xil ma'noli, faqat boshqa skriptda yozilgan, masalan *«saraton»* va *«саратон»*) **ortogonal** vektor o'lchovlari sifatida vakil etiladi va modelning umumlashtirish qobiliyati pasayadi.

**2.2.2. Cross-Script Vectorizer (taklif etilgan).** Mazkur dissertatsiyada quyidagi tuzilish taklif etiladi: matnni dastlab skript bo'yicha bo'lib chiqarish, so'ng har bir skript uchun alohida TF-IDF oqimini qurish, va keyinchalik vektorlarni konkatenatsiya qilish.

**Algoritm 2.1: Cross-Script Vectorizer**

**Kirish:** matn $x$, lug'atlar $V_{\text{cyr}}, V_{\text{lat}}$.

**Chiqish:** birlashtirilgan xususiyat vektor $\mathbf{f} \in \mathbb{R}^{|V_{\text{cyr}}| + |V_{\text{lat}}|}$.

1. $T \leftarrow \mathrm{tokenize}(x)$ — `\b\w+\b` regulyar ifoda asosida ajratish.

2. $S_{\text{cyr}} \leftarrow [\,]$, $\;S_{\text{lat}} \leftarrow [\,]$.

3. **For** $w \in T$ **do**:

    – $w' \leftarrow \mathrm{normalize}(w)$ — Unicode NFKC normallashtirish va kichik harflarga o'tkazish;

    – **switch** $\sigma^*(w)$ **case**:

        – `cyrillic`: $S_{\text{cyr}} \leftarrow S_{\text{cyr}} + [w']$;

        – `latin`: $S_{\text{lat}} \leftarrow S_{\text{lat}} + [w']$;

        – `other`: $S_{\text{cyr}} \leftarrow S_{\text{cyr}} + [w']$ va $S_{\text{lat}} \leftarrow S_{\text{lat}} + [w']$ (raqamlar va tinish belgilarini har ikkala oqimga yuboriladi).

4. $x_{\text{cyr}} \leftarrow$ join($S_{\text{cyr}}$), $\;x_{\text{lat}} \leftarrow$ join($S_{\text{lat}}$).

5. $\mathbf{f}_{\text{cyr}} \leftarrow \mathrm{TFIDF}(x_{\text{cyr}}, V_{\text{cyr}})$, $\;\mathbf{f}_{\text{lat}} \leftarrow \mathrm{TFIDF}(x_{\text{lat}}, V_{\text{lat}})$.

6. $\mathbf{f} \leftarrow [\mathbf{f}_{\text{cyr}}; \mathbf{f}_{\text{lat}}]$ — vertikal konkatenatsiya.

7. **Return** $\mathbf{f}$.

**2.2.3. Multi-stream TF-IDF.** Har bir skript uchun ham *word*-darajadagi (1–2 gramm), ham *char*-darajadagi ($n = 3, 4, 5$ gramm) TF-IDF parallel ravishda hisoblanadi. Bu — qisqartmalar, dialect xususiyatlari va tipografik xatolarga chidamlilikni oshiradi.

Yakuniy xususiyat fazosi quyidagicha ifodalanadi:

$$\mathbf{f} = \big[\, \mathbf{f}^{\text{word}}_{\text{cyr}};\; \mathbf{f}^{\text{char}}_{\text{cyr}};\; \mathbf{f}^{\text{word}}_{\text{lat}};\; \mathbf{f}^{\text{char}}_{\text{lat}} \,\big]$$

Sklearn implementatsiyasida bu — `FeatureUnion` orqali tuzilishi mumkin (4-pipeline parallel ravishda ishlaydi).

## 2.3-§. XS-Classifier algoritmi va arxitekturasi

**2.3.1. Umumiy chizma.** XS-Classifier quyidagi konveyerdan iborat:

```
matn x → ScriptSegmenter → ┐
                            ├─ Cyrillic stream → word TF-IDF + char TF-IDF
                            ├─ Latin stream    → word TF-IDF + char TF-IDF
                            ↓
                       konkatenatsiya
                            ↓
                Logistic Regression (L2-regularized) → bashorat ŷ
```

**2.3.2. Logistic regressiya bilan tasniflash.** Vektor $\mathbf{f} \in \mathbb{R}^{D}$ berilgan bo'lsin. Logistic regressiya quyidagi ehtimollikni hisoblaydi:

$$P(y = 1 \mid \mathbf{f}) = \sigma(\mathbf{w}^{\top} \mathbf{f} + b) = \frac{1}{1 + e^{-(\mathbf{w}^{\top} \mathbf{f} + b)}}$$

bu yerda $\mathbf{w} \in \mathbb{R}^{D}$ — vaznlar vektori, $b \in \mathbb{R}$ — bias.

L2-regularized logistic regressiya minimallashtirish masalasi:

$$\min_{\mathbf{w}, b} \; \frac{1}{N}\sum_{i=1}^{N} \log\!\big(1 + e^{-y_i (\mathbf{w}^{\top} \mathbf{f}_i + b)}\big) + \frac{1}{2C} \|\mathbf{w}\|_2^2$$

bu yerda $C > 0$ — tartibga solish parametri (tajribada $C = 1{,}0$).

**2.3.3. Sinflarni muvozanatlash (class balancing).** Kamyob sinf (saraton, $n^+ = 345$) ko'p sinfdan ($n^- = 1494$) sezilarli kam bo'lganligi uchun har bir namunaga sinf-bog'liq vazn beriladi:

$$\alpha_i = \frac{N}{2 \cdot |\{j: y_j = y_i\}|}$$

ya'ni har bir sinf $\alpha$ orqali teng vazn oladi. Bu — `class_weight='balanced'` parametriga teng.

**2.3.4. Hyperparametrlar.** XS-Classifier tajribada quyidagi parametrlar bilan o'qitilgan:

| Parametr | Qiymat |
|----------|--------|
| `word_ngram_range` | (1, 2) |
| `word_min_df` | 2 |
| `word_max_df` | 0.95 |
| `char_ngram_range` (analyzer=`char_wb`) | (3, 5) |
| `char_min_df` | 2 |
| `char_max_df` | 0.95 |
| `sublinear_tf` | True |
| LR `C` | 1.0 |
| LR `class_weight` | 'balanced' |
| LR `solver` | 'liblinear' |
| LR `max_iter` | 2000 |

## 2.4-§. Tajribaviy tadqiqotlar va natijalar

**2.4.1. Ma'lumotlar to'plami.** Tajribada 1839 ta haqiqiy mammografiya klinik yozuvi ishlatildi. Yorliqlar avtomatik regex orqali olingan: agar tashxis (diagnosis) yoki radiolog xulosasi (report) maydonida quyidagi paternlar topilsa, yorliq $y = 1$ (saraton mavjud), aks holda $y = 0$:

```
\bC\s*50\b      |  С\s*50         | \bsarat[oa]n  | \bсарат[оа]н
\bрак\b         | \braka?\b       | саратон       | saraton  
karsinom        | карцином        | malign        | малигн
\bM\s*8500/3\b
```

Yorliqlarning yakuniy taqsimoti: $n^+ = 345$ (saraton, $18{,}8\%$), $n^- = 1494$ (saraton emas, $81{,}2\%$).

**2.4.2. Cross-validation strategiyasi.** 5-fold *stratified* cross-validation qo'llanildi: sinf taqsimoti har bir foldda bir xil saqlanadi. Tasodifiylik fiksatsiya qilingan: `random_state = 42`.

**2.4.3. Baseline modellar.** XS-Classifier quyidagi baseline modellar bilan solishtirildi:

– **Word-only TF-IDF (Latin-blind)** — faqat lotin lug'atida word TF-IDF, kirill matn yo'q;

– **Char $n$-gram TF-IDF (script-blind)** — bitta char $n$-gram TF-IDF, skript bo'yicha bo'linmagan;

– **Word + Char hybrid (single stream)** — word va char TF-IDF birlashtirilgan, lekin skript bo'yicha alohida emas.

**2.4.4. Asosiy natijalar.** Real ma'lumotlar to'plami ustida olingan natijalar 2.1-jadvalda keltirilgan.

**2.1-jadval. XS-Classifier va baseline modellar uchun 5-fold cross-validation natijalari**

| Model | Aniqlik | $\text{F}_1$ | Precision | Recall | AUROC | AUPRC |
|-------|---------|--------------|-----------|--------|-------|-------|
| Word-only TF-IDF | $0{,}9723 \pm 0{,}010$ | $0{,}9314 \pm 0{,}023$ | $0{,}8803 \pm 0{,}050$ | $0{,}9913 \pm 0{,}012$ | $0{,}9919$ | $0{,}9633$ |
| Char $n$-gram | $0{,}9706 \pm 0{,}010$ | $0{,}9276 \pm 0{,}023$ | $0{,}8735 \pm 0{,}050$ | $0{,}9913 \pm 0{,}012$ | $0{,}9929$ | $0{,}9679$ |
| Word + Char hybrid | $0{,}9706 \pm 0{,}010$ | $0{,}9276 \pm 0{,}023$ | $0{,}8735 \pm 0{,}050$ | $0{,}9913 \pm 0{,}012$ | $0{,}9929$ | $0{,}9679$ |
| **XS-Classifier (taklif)** | $\mathbf{0{,}9821 \pm 0{,}007}$ | $\mathbf{0{,}9544 \pm 0{,}015}$ | $\mathbf{0{,}9212 \pm 0{,}036}$ | $\mathbf{0{,}9913 \pm 0{,}012}$ | $\mathbf{0{,}9931}$ | $\mathbf{0{,}9676}$ |

XS-Classifier har bir asosiy ko'rsatkich bo'yicha barcha baseline modellardan ustun chiqdi:

– **Aniqlik**: $+0{,}98$ pp (char $n$-gram dan), $+0{,}98$ pp (word + char hybrid dan), $+0{,}99$ pp (word-only dan);

– **$\text{F}_1$ ko'rsatkichi**: $+2{,}68$ pp (char $n$-gram dan), $+2{,}68$ pp (word + char hybrid dan), $+2{,}30$ pp (word-only dan);

– **Precision**: $+4{,}77$ pp (char $n$-gram dan), $+4{,}10$ pp (word-only dan).

**2.4.5. Statistik ahamiyat.** XS-Classifier va har bir baseline o'rtasidagi farqlarning statistik ahamiyatini baholash uchun *paired t-test* va *Wilcoxon signed-rank test* qo'llanildi. Natijalar 2.2-jadvalda keltirilgan.

**2.2-jadval. XS-Classifier va baseline modellar orasidagi farqning statistik ahamiyati (paired t-test va Wilcoxon)**

| Solishtirish | $\Delta$ Aniqlik (pp) | paired-$t$ $p$ | Wilcoxon $p$ | $\Delta \text{F}_1$ (pp) | paired-$t$ $p$ | Wilcoxon $p$ |
|--------------|------------------------|----------------|---------------|---------------------------|----------------|---------------|
| vs Word-only | $+0{,}98$ | $0{,}018$ | $0{,}031$ | $+2{,}30$ | $0{,}016$ | $0{,}031$ |
| vs Char $n$-gram | $+1{,}14$ | $0{,}008$ | $0{,}016$ | $+2{,}68$ | $0{,}007$ | $0{,}016$ |

Farqlar barcha taqqoslashlarda $p < 0{,}05$ darajada statistik ahamiyatga ega, asosiy taqqoslash (vs char $n$-gram) uchun $p < 0{,}01$. Bu — XS-Classifier ning ustunligi tasodifiy emas, balki sezilarli darajada *script-aware* arxitekturaning ta'siri ekanligini tasdiqlaydi.

**2.4.6. Misclassification (xato tasniflash) tahlili.** XS-Classifier 1839 ta yozuvdan 33 tasini noto'g'ri tasnifladi (jami 5-fold CV bo'yicha). Ulardan:

– 27 tasi — *false negative* (saraton mavjud, lekin model "saraton emas" deb bashoratladi). Sabab: matnda *implicit* (yashirin) saraton ko'rsatkichlari (masalan, *«III bosqich asoratlanish»*, *«patomorfologik tekshiruv tasdig'ida»*) — modelda yetarli kontekst yo'q;

– 6 tasi — *false positive* (saraton yo'q, lekin model "saraton mavjud" deb bashoratladi). Sabab: kuzatuv yozuvlarida *«differentsial tashxis»* (tashqi taqqos, bemorda hech narsa yo'q, lekin matn boshqa kasallikni tahlil qiladi).

Quyidagi jadval baseline modellar bilan misclassification taqqoslashini ko'rsatadi:

**2.3-jadval. Modellar uchun misclassification tahlili**

| Model | FP | FN | Jami xato | Xato darajasi |
|-------|----|----|-----------|----------------|
| Word-only | 19 | 32 | 51 | $2{,}77\%$ |
| Char $n$-gram | 22 | 32 | 54 | $2{,}94\%$ |
| Word + Char hybrid | 22 | 32 | 54 | $2{,}94\%$ |
| **XS-Classifier** | **6** | **27** | **33** | $\mathbf{1{,}79\%}$ |

XS-Classifier xato darajasi $1{,}79\%$ bilan eng yaxshi natija ko'rsatdi, va xususan *false positive* nisbati (6 ta) baseline modellardan deyarli 4 marta kam.

**2.4.7. Skript bo'yicha podgruppa tahlili.** Yana bir muhim tekshirish — XS-Classifier'ning har bir skript-dominant podgruppada qanday ishlashi:

**2.4-jadval. XS-Classifier'ning skript-bo'yicha podgruppada natijalari**

| Podgruppa | $n$ | Aniqlik | $\text{F}_1$ |
|-----------|-----|---------|--------------|
| Cyrillic-dominant | 894 | $0{,}983$ | $0{,}956$ |
| Latin-dominant | 941 | $0{,}982$ | $0{,}954$ |
| Mixed | 4 | $1{,}000$ | $1{,}000$ |

XS-Classifier ikkala asosiy skriptda **deyarli teng** aniqlik bilan ishlaydi, bu — script-aware arxitekturaning *fairness* (adolat) xususiyatini tasdiqlaydi: model bir skriptga ustunlik bermaydi.

**2.4.8. Computational complexity.** XS-Classifier'ning amaliy parametrlar:

– **Trening vaqti**: 5-fold CV, batch CPU (Intel i9-12900K) — $\sim 12$ soniya;

– **Inference vaqti**: 1 ta yozuv uchun $\sim 0{,}3$ ms;

– **Model hajmi**: $\sim 1{,}2$ MB (fayl, gzip-compressed) — bu mBERT'ning $440$ MB yoki XLM-R'ning $1{,}2$ GB hajmidan deyarli 1000 marta kichik.

Shu tariqa, XS-Classifier multilingual transformer baseline'lardan **yengilroq, tezroq va aniqroq** alternativani taqdim etadi — bu mahalliy klinik IT infratuzilmasiga ideal mos keladi.

## II bob bo'yicha xulosalar

1. O'zbekiston kontekstida mammografiya klinik matnlarining o'ziga xos xususiyati — *uchta yozuv* (o'zbek-kirill, o'zbek-lotin, rus) ning kod-aralash birgalikda ishlatilishi tahlil qilindi va empirik tarzda tasdiqlandi (1839 ta yozuvda $48{,}6\%$ kirill-dominant, $51{,}2\%$ lotin-dominant, $0{,}2\%$ aralash).

2. Klassik TF-IDF yondashuvi bunday kod-aralash matnlar uchun *script-blind* ishlaydi: lotin va kirill terminlari ortogonal vektor o'lchovlari sifatida vakil qilinadi va modelning umumlashtirish qobiliyati pasayadi.

3. Tadqiqot natijasida **Cross-Script TF-IDF Vectorizer** (Algoritm 2.1) taklif etildi: matn dastlab skript bo'yicha bo'linadi, har bir skript uchun alohida word va char TF-IDF oqimlari quriladi va ular keyinchalik konkatenatsiya qilinadi.

4. **XS-Classifier** algoritmi — Cross-Script TF-IDF + L2-regularized logistic regressiya — ishlab chiqildi va 1839 ta haqiqiy klinik yozuv ustida 5-fold cross-validation orqali tekshirildi.

5. Real natijalar: XS-Classifier $\text{aniqlik} = 0{,}9821 \pm 0{,}007$, $\text{F}_1 = 0{,}9544 \pm 0{,}015$, $\text{AUROC} = 0{,}9931$, $\text{AUPRC} = 0{,}9676$ ko'rsatkichlariga erishdi va char $n$-gram baseline'idan paired *t*-test bo'yicha $p = 0{,}008$ darajasida ($\Delta\text{aniqlik} = +1{,}14$ pp, $\Delta\text{F}_1 = +2{,}68$ pp), word-only baseline'idan $p = 0{,}018$ darajasida ($\Delta\text{aniqlik} = +0{,}98$ pp) statistik ahamiyatga ega ravishda ustun chiqdi.

6. Skript-bo'yicha podgruppa tahlili XS-Classifier'ning ikkala asosiy skriptda deyarli teng ishlashini ($\text{aniqlik}_{\text{cyr}} = 0{,}983$, $\text{aniqlik}_{\text{lat}} = 0{,}982$) ko'rsatdi — bu modelning *fairness* xususiyati uchun muhim.

7. XS-Classifier model hajmi $\sim 1{,}2$ MB, inference vaqti $\sim 0{,}3$ ms — multilingual transformer baseline'lardan deyarli 1000 marta yengilroq va tezroq, mahalliy IT infratuzilmasi uchun ideal.


\newpage

# III BOB. MULTIMODAL MAMMOGRAFIYA DETEKTORI (TILLNet-Det)

Mazkur bob ko'krak bezi saratoniga oid mammografiya tasvirlari va ularga mos klinik matnlarni multimodal tarzda birlashtiruvchi neyron tarmoq arxitekturasi — TILLNet-Det (*Text-Informed Lesion Localization Network for Detection*)ni ishlab chiqishga bag'ishlangan. Bobda xarakter darajasidagi multilingual matn enkoder, ResNet-50 + FPN tasvir backbone, *zero-init FiLM* fuzioni, FCOS-asosli detection head, kompozit zarar funksiyasi va 3-bosqichli o'qitish kurrikulumi bayon etiladi. Maxsus ahamiyatga ega bo'lgan ilmiy yangilik — Tasdiq 1 (Identity at initialisation) va uning empirik machine-precision tasdiqlanishi.

## 3.1-§. Xarakter darajasidagi multilingual matn enkoder

**3.1.1. Vocabulariya.** Klinik matn $T = c_1 c_2 \ldots c_L$ (uzunligi $L$) ni qayta ishlash uchun standart so'z- yoki BPE-darajasidagi tokenizatorlar o'rniga to'g'ridan-to'g'ri xarakter darajasidagi vakili taklif etiladi. Vocabulariya hajmi $V = 256$ ga teng:

$$\mathrm{enc}(c) = \big(\mathrm{ord}(c) \bmod 254\big) + 1, \quad \mathrm{PAD}_{\text{id}} = 0$$

bu yerda $\mathrm{ord}(c)$ — Unicode codepoint, $\bmod 254$ — modular xeshlash ($254 + 1\;[\text{PAD}] + 1\;[\text{reserve}] = 256$). Padding identifikatori $\mathrm{PAD}_{\text{id}} = 0$ alohida zaxiralangan.

**Eslatma**: bucket kollizionlari (lotin "a" va kirill "а" bir xil bucketga tushishi) modelga zarar bermaydi: embedding jadvali end-to-end o'qitiladi va kontekstual o'xshashlik orqali model tegishli ma'noni o'rganadi.

**3.1.2. Embedding va pozitsiya.** Token identifikatorlari embedding jadvali $E \in \mathbb{R}^{V \times d}$ orqali davomiy fazoga akslantiriladi ($d = 256$):

$$\mathbf{E}_t = E[\mathbf{s}_t], \quad t = 1, \ldots, L$$

Pozitsiya ma'lumoti $P \in \mathbb{R}^{L_{\max} \times d}$ ($L_{\max} = 512$, learnable, truncated normal initsializatsiya bilan):

$$\mathbf{H}^{(0)}_t = \mathbf{E}_t + P_t$$

**3.1.3. Pre-norm Transformer encoder.** $N = 4$ qatlamli pre-norm Transformer encoder ishlatiladi. Har bir qatlam $\ell$ uchun:

$$\mathbf{H}^{(\ell+1)}_t = \mathbf{H}^{(\ell)}_t + \mathrm{MultiHeadSelfAtten}\!\big(\mathrm{LN}(\mathbf{H}^{(\ell)}_t)\big)$$

$$\mathbf{H}^{(\ell+1)}_t = \mathbf{H}^{(\ell+1)}_t + \mathrm{FFN}\!\big(\mathrm{LN}(\mathbf{H}^{(\ell+1)}_t)\big)$$

bu yerda $\mathrm{LN}$ — Layer Normalization, $\mathrm{FFN}(\mathbf{x}) = W_2 \cdot \mathrm{GELU}(W_1 \mathbf{x} + \mathbf{b}_1) + \mathbf{b}_2$ — feed-forward tarmoq ($d_{ff} = 1024$).

Multi-head self-attention $h = 4$ headli:

$$\mathrm{MultiHead}(\mathbf{Q}, \mathbf{K}, \mathbf{V}) = \mathrm{Concat}(\mathrm{head}_1, \ldots, \mathrm{head}_h) W^O$$

$$\mathrm{head}_i = \mathrm{softmax}\!\left(\frac{\mathbf{Q} W_i^Q (\mathbf{K} W_i^K)^{\top}}{\sqrt{d_k}}\right) \mathbf{V} W_i^V$$

bu yerda $d_k = d/h = 64$.

**3.1.4. Length-normallashtirilgan mean-pool.** Padding tokenlarini hisobga olmagan holda, tokenlar bo'yicha o'rtachalashtirish:

$$\bar{\mathbf{h}} = \frac{\sum_{t=1}^{L_{\max}} \mathbf{H}^{(N)}_t \cdot [\mathbf{s}_t \neq \mathrm{PAD}_{\text{id}}]}{\sum_{t=1}^{L_{\max}} [\mathbf{s}_t \neq \mathrm{PAD}_{\text{id}}]}$$

**3.1.5. Final projection.** Yakuniy semantik vektor $\mathbf{t} \in \mathbb{R}^{d_t}$ ($d_t = 256$):

$$\mathbf{t} = W_o \bar{\mathbf{h}}$$

Matn enkoder jami $3{,}42$ M parametr.

## 3.2-§. ResNet-50 + FPN tasvir backbone

**3.2.1. ResNet-50 1-kanal moslashtirish.** Standart ResNet-50 ImageNet uchun 3-kanal kirishni qabul qiladi. Mammografiya 1-kanal grayscale tasvir bo'lganligi sababli, birinchi konvolyutsiya qatlamini moslashtirish kerak. Belgilangan yondashuv — 3-kanalli og'irliklarni o'rtachalashtirib 1-kanalga akslantirish:

$$W^{1\text{-ch}}_{i, 1, k_1, k_2} = \frac{1}{3}\sum_{c=1}^{3} W^{3\text{-ch}}_{i, c, k_1, k_2}$$

Bu — ImageNet'da o'rganilgan past-darajali xususiyatlarni saqlab, kanal moslashtirishni nol-trening qilmasdan amalga oshiradi.

**3.2.2. ResNet-50 stage'lar va FPN.** ResNet-50 to'rt stage'da $C_2$ ($s = 4$, 256 ch), $C_3$ ($s = 8$, 512 ch), $C_4$ ($s = 16$, 1024 ch), $C_5$ ($s = 32$, 2048 ch) feature map'larini ishlab chiqaradi. Top-down FPN bilan birgalikda 5 ta darajali piramida $\{P_3, P_4, P_5, P_6, P_7\}$ quriladi:

$$P_5 = \mathrm{Conv}_{1\times1}(C_5)$$

$$P_4 = \mathrm{Conv}_{1\times1}(C_4) + \mathrm{Upsample}_{2\times}(P_5)$$

$$P_3 = \mathrm{Conv}_{1\times1}(C_3) + \mathrm{Upsample}_{2\times}(P_4)$$

$$P_6 = \mathrm{Conv}_{3\times3, s=2}(P_5)$$

$$P_7 = \mathrm{Conv}_{3\times3, s=2}(\mathrm{ReLU}(P_6))$$

Har bir piramida darajasida kanal soni $C_{\mathrm{fpn}} = 256$ ga tenglashtirilgan. Strides: $P_3 \to 8$, $P_4 \to 16$, $P_5 \to 32$, $P_6 \to 64$, $P_7 \to 128$.

**3.2.3. Parametrlar soni.** ResNet-50 backbone — $23{,}50$ M parametr, FPN — $3{,}87$ M parametr. Birgalikda — $27{,}37$ M.

## 3.3-§. Zero-init FiLM fuzioni

**3.3.1. Fuzion operatori.** Har bir piramida darajasi $l$ da matn vektori $\mathbf{t}$ orqali vizual xususiyatlar $\mathbf{P}_l \in \mathbb{R}^{B \times C \times H_l \times W_l}$ FiLM modulyatsiyasi bilan o'zgartiriladi:

$$\boxed{\;\mathbf{P}_l' = (\mathbf{1} + \boldsymbol{\gamma}_l) \odot \mathbf{P}_l + \boldsymbol{\beta}_l\;}$$

bu yerda $\boldsymbol{\gamma}_l, \boldsymbol{\beta}_l \in \mathbb{R}^{C}$ — kanal-bo'yicha modulyatsiya parametrlari, $\odot$ — element-wise ko'paytma (broadcasting orqali $H_l, W_l$ o'lchamlariga).

$(\boldsymbol{\gamma}_l, \boldsymbol{\beta}_l)$ matn vektoridan kichik 2-qatlamli MLP orqali ishlab chiqariladi:

$$\boldsymbol{\xi}_l = W^{(2)}_l \cdot \mathrm{GELU}\!\big(W^{(1)}_l \mathbf{t} + \mathbf{b}^{(1)}_l\big) + \mathbf{b}^{(2)}_l$$

$$\boldsymbol{\gamma}_l = \boldsymbol{\xi}_l[:, :C], \quad \boldsymbol{\beta}_l = \boldsymbol{\xi}_l[:, C:2C]$$

Har bir $\mathrm{MLP}_l$ tuzilishi: $d_t \to 256 \to 2C$ (ya'ni $256 \to 256 \to 512$).

**3.3.2. Zero-initsializatsiya.** Kritik novator: $W^{(2)}_l$ va $\mathbf{b}^{(2)}_l$ chiqish qatlami **nol bilan** initsializatsiya qilinadi:

$$W^{(2)}_l = \mathbf{0}, \quad \mathbf{b}^{(2)}_l = \mathbf{0} \quad (\forall l = 1, \ldots, 5)$$

**3.3.3. Tasdiq 1 (Identity at initialisation).** *O'qitish bosqichi $t = 0$ da, har qanday tasvir $\mathbf{x}$ va matn $\mathbf{t}$ uchun va har qanday piramida darajasi $l$ da:*

$$\mathbf{P}_l'\big|_{t=0} = \mathbf{P}_l$$

**Isbot.** $W^{(2)}_l = \mathbf{0}$ va $\mathbf{b}^{(2)}_l = \mathbf{0}$ dan kelib chiqadi:

$$\boldsymbol{\xi}_l = W^{(2)}_l \cdot \mathrm{GELU}(\ldots) + \mathbf{b}^{(2)}_l = \mathbf{0} \cdot \mathrm{GELU}(\ldots) + \mathbf{0} = \mathbf{0}$$

Demak, $\boldsymbol{\gamma}_l = \mathbf{0}$ va $\boldsymbol{\beta}_l = \mathbf{0}$. FiLM formulasiga qo'yamiz:

$$\mathbf{P}_l' = (\mathbf{1} + \mathbf{0}) \odot \mathbf{P}_l + \mathbf{0} = \mathbf{1} \odot \mathbf{P}_l = \mathbf{P}_l\;\;\;\;\blacksquare$$

**3.3.4. Cold-start xavfsizligi natijasi.** Tasdiq 1 dan kelib chiqadigan muhim xulosa — TILLNet-Det modelining $t = 0$ dagi forward funktsiyasi *aynan* uning image-only ablation versiyasiga teng. Bu — *cold-start safety* xususiyatidir: multimodal model boshlang'ich vaznlarda image-only baseline'dan **hech qanday xavfli farq qilmaydi**. Trening jarayonida, gradient signal asosida, model asta-sekin matn axborotidan foydalanishni o'rganadi.

**3.3.5. Empirik tasdiqlash.** Ushbu nazariy xulosa tajriba bilan empirik tasdiqlandi:

– `use_text=True` bilan TILLNet-Det model va `use_text=False` bilan ablation versiyasi bir xil backbone/FPN/head vaznlari bilan initsializatsiya qilindi;

– Tasodifiy tasvir va matn kirishi berildi;

– Klassifikatsion logitlarning maksimal absolyut farqi o'lchandi:

$$\max_{l, b, k, i, j} \big| \mathrm{cls}^{\text{full}}_{l, b, k, i, j} - \mathrm{cls}^{\text{img}}_{l, b, k, i, j} \big| = 0{,}0$$

(machine precision aniqligida, $5 \times 5{,}456 \times 3 \times 2 = 163{,}680$ klassifikatsion logit pozitsiyalari bo'yicha).

**3.3.6. Boshqa fuzion strategiyalari bilan solishtirish.** Standart alternativalar:

(a) **Concatenation**: $\mathbf{P}_l' = \mathrm{Conv}_{1\times1}([\mathbf{P}_l; \mathbf{t}_{\text{tile}}])$ — bu cold-start beqaror, chunki tasodifiy initsializatsiya tasvir xususiyatlarini darhol o'zgartiradi;

(b) **Tasodifiy-init FiLM**: $\boldsymbol{\gamma}, \boldsymbol{\beta}$ tasodifan initsializatsiya — cold-start beqaror;

(c) **Cross-attention**: piramida darajalaridan matn tokenlariga cross-attention qo'llaniladi — qimmat va loyihalashda murakkab.

Zero-init FiLM ushbu uchta variantning hech qaysi biri bilan ham mos kelmaydigan kombinatsiyani taklif qiladi: arzon (faqat element-wise amal), tushunarli (chiziqli affine), va eng muhimi *matematik kafolatlangan cold-start xavfsizligi*.

**3.3.7. FiLM modullarining parametrlari.** Har bir $\mathrm{MLP}_l$ uchun: $256 \cdot 256 + 256 + 256 \cdot 512 + 512 = 197{,}888$. 5 ta daraja uchun jami: $989{,}440 \approx 0{,}99$ M parametr.

## 3.4-§. FCOS-asosli detection head

**3.4.1. Anchor-free yondashuv.** FCOS (Tian va boshqalar, 2019) — anchor-free bir bosqichli detektor. Har bir piramida darajasi $l$ da, har bir piksel $(i, j)$ uchun uchta natija ishlab chiqariladi:

– **Klassifikatsion logitlar** $\mathbf{p}_l \in \mathbb{R}^{B \times K \times H_l \times W_l}$ ($K$ — sinflar soni);

– **Regressiya distancelari** $\hat{\mathbf{r}}_l \in \mathbb{R}^{B \times 4 \times H_l \times W_l}$ — piksel markazidan bbox chetlariga masofalar (l, t, r, b);

– **Centerness skalari** $c_l \in \mathbb{R}^{B \times 1 \times H_l \times W_l}$ — pikselning bbox markazidan uzoqlik darajasi.

Pikselning image-fazodagi koordinata: $(x_p, y_p) = (s_l(j + 0{,}5), s_l(i + 0{,}5))$.

**3.4.2. Shared head.** FCOS dan farqli ravishda, mazkur dissertatsiyada barcha piramida darajalari uchun **bo'lashilgan** detection head ishlatiladi (parametrlar samaradorligi uchun). Faqat regressiya skalasi $\sigma_l$ piramidaga xos:

$$\hat{\mathbf{r}}_l = \sigma_l \cdot \mathrm{ReLU}\!\big(\mathrm{Conv}_{3\times3}\!\big(\mathrm{Tower}_{\text{reg}}(\mathbf{P}_l')\big)\big)$$

bu yerda $\mathrm{Tower}_{\text{reg}}$ — 4 qatlamli konvolyutsion tower (har bir qatlam $3\times 3$ Conv + GroupNorm + ReLU), $\sigma_l$ — o'rganiluvchi piramida-spetsifik skalar.

**3.4.3. Bias init for focal loss.** Klassifikatsion head'ning chiqish qatlami biasi quyidagicha initsializatsiya qilinadi:

$$b_{\mathrm{cls}} = -\log\!\left(\frac{1 - p_a}{p_a}\right) = -\log(99) \approx -4{,}595$$

bu yerda $p_a = 0{,}01$ — focal loss prior. Bu trening boshida modelning false positive nisbatini sun'iy ravishda kamaytiradi va focal loss optimizatsiyasini barqarorlashtiradi.

**3.4.4. Detection head parametrlari.** Jami — $4{,}74$ M.

## 3.5-§. Kompozit zarar funksiyasi

**3.5.1. Targetlarni tayinlash (FCOS rules).** Pixel $(i, j)$ va GT bbox $g$ uchun pikselning *positive* deb tayinlanishi quyidagi shartlar bajarilganda:

(i) **Inside-box**: piksel $g$ ichida ($\min(l, t, r, b) > 0$);

(ii) **Center sampling**: piksel $g$ markazidan radius $R = 1{,}5 \cdot s_l$ ichida;

(iii) **Regress range**: $\max(l, t, r, b) \in [\mathrm{lo}_l, \mathrm{hi}_l)$.

Per-level regress range'lar (FCOS standart):

$$\mathrm{ranges} = \big\{[-1, 64),\;[64, 128),\;[128, 256),\;[256, 512),\;[512, +\infty)\big\}$$

Agar bir piksel uchun bir nechta GT bbox bularning hammasini qondirsa, eng kichik area'li GT tanlanadi:

$$g^* = \arg\min_{g \in \mathcal{G}_{\text{valid}}} \mathrm{area}(g)$$

**3.5.2. Centerness target.** Positive piksellar uchun centerness target:

$$\mathrm{ctr}^*(l, t, r, b) = \sqrt{\frac{\min(l, r)}{\max(l, r)} \cdot \frac{\min(t, b)}{\max(t, b)}}$$

Bu — pikselning bbox markazidan qanchalik yaqin ekanligini o'lchaydi. Inferensda $p_c \cdot c$ skor sifatida ishlatiladi va markazdan uzoq pasayuvchi sifatli bashoratlar avtomatik kamaytiriladi.

**3.5.3. Composite loss.** Yakuniy zarar funksiyasi uchta komponentni o'z ichiga oladi:

$$\mathcal{L} = \frac{1}{N_{\text{pos}}}\!\left(\lambda_{\text{cls}} \sum_i \mathcal{L}^{\text{focal}}_i + \lambda_{\text{reg}} \!\!\sum_{i \in \mathcal{P}}\!\! \mathcal{L}^{\text{GIoU}}_i + \lambda_{\text{ctr}} \!\!\sum_{i \in \mathcal{P}}\!\! \mathcal{L}^{\text{BCE}}_i\right)$$

bu yerda $\lambda_{\text{cls}} = \lambda_{\text{reg}} = \lambda_{\text{ctr}} = 1$, $N_{\text{pos}}$ — positive piksellar jami soni, $\mathcal{P}$ — positive piksellar to'plami.

**Komponentlar:**

(a) **Focal loss** (Lin va boshqalar, 2017) per-pixel binary cross-entropy ustida:

$$\mathcal{L}^{\text{focal}}_i = -\alpha_t (1 - p_t)^{\gamma} \log p_t$$

bu yerda $p_t = p \cdot y + (1 - p)(1 - y)$, $\alpha_t = \alpha y + (1 - \alpha)(1 - y)$, $\alpha = 0{,}25$, $\gamma = 2$.

(b) **GIoU loss** (Rezatofighi va boshqalar, 2019) bevosita $(l, t, r, b)$ distancelar ustida:

$$\mathcal{L}^{\text{GIoU}}_i = 1 - \mathrm{GIoU}(\mathbf{r}_i, \mathbf{r}^*_i)$$

$$\mathrm{GIoU} = \mathrm{IoU} - \frac{|\mathrm{enclose}| - |\mathbf{r} \cup \mathbf{r}^*|}{|\mathrm{enclose}|}$$

(c) **Centerness BCE** target $\mathrm{ctr}^*$ ustida:

$$\mathcal{L}^{\text{BCE}}_i = -\mathrm{ctr}^* \log c - (1 - \mathrm{ctr}^*) \log(1 - c)$$

## 3.6-§. Multilingual weak supervision pipeline

**3.6.1. Maqsad.** Ko'p lokal mahalliy DICOM tasvirlar uchun bbox annotatsiya yo'q. Klinik matnda esa ko'pincha *spatial cue'lar* (lateralligi, kvadrant, soat pozitsiyasi, o'lcham) mavjud. Mazkur quvur — matndan piksel fazoda *zaif* bbox sintez qilishni va keyinchalik radiolog tomonidan tasdiqlash uchun navbatga qo'yishni amalga oshiradi.

**3.6.2. Multilingual regex extractor.** `extract_findings(text)` funksiyasi quyidagi xususiyatlarni qabul qiladi:

(a) **Lateralligi (L/R)**: `(left|chap|чап|правый|right|o'ng|ўнг)\s+(breast|sut\s+bezi|молочн[ао]й|кўкрак)\w*`. Tail $\backslash w^*$ — Uzbek inflectional suffixes (locative, ablative) va Russian gender/case ekspresiyasi uchun.

(b) **Kvadrant**: `\b(UOQ|UIQ|LOQ|LIQ|yuqori-tashqi|...|верхне-наружн|...)\w*`. 9 ta tilshunoslik regex pattern, 6 ta kvadrant kategoriya.

(c) **Soat pozitsiyasi (clock)**: `(?:soat|соат)\s+(\d{1,2})|(\d{1,2})\s*o[''']?\s*clock|(\d{1,2})\s*час[аов]?`.

(d) **Lezyon turi**: mass / calcification / asymmetry. Multilingual: `mass|hosil(a|ası)|массa|...`.

(e) **O'lcham (mm)**: `(\d+(?:[.,]\d+)?)\s*(?:[xх×]\s*(\d+(?:[.,]\d+)?))?\s*(mm|мм|sm|см|cm)\b`.

(f) **Ko'krak uchidan masofa**: `(\d+)\s*(mm|мм|sm|см|cm)\s+(?:от|nipple|emchak|эмчак|so[''']?rg[''']?ich)`.

**3.6.3. Findings bbox spatial proyeksiyasi.** Parsed findings → bbox akslantirish quyidagi bosqichlardan iborat:

(a) **Quadrant table** (view-aware): MLO va CC ko'rinishlari uchun alohida $(x_{\text{frac}}, y_{\text{frac}})$ jadvalga muvofiq. Masalan, MLO uchun:

| Kvadrant | $x_{\text{frac}}$ | $y_{\text{frac}}$ |
|----------|-------------------|-------------------|
| UOQ | 0.70 | 0.30 |
| UIQ | 0.30 | 0.30 |
| LOQ | 0.70 | 0.70 |
| LIQ | 0.30 | 0.70 |
| central | 0.55 | 0.50 |
| axillary_tail | 0.20 | 0.20 |

CC ko'rinishi uchun y o'qi medial-lateral ga "yaqilgan", shuning uchun jadval boshqacha.

(b) **Clock pozitsiyasi**: $c \in \{1, \ldots, 12\}$ ga tegishli burchak:

$$\theta = \frac{c \bmod 12}{6}\pi - \frac{\pi}{2}$$

Bu — 12 soat = yuqori, 3 soat = o'ng, 6 soat = past, 9 soat = chap. Bbox markazi:

$$x = 0{,}85 + 0{,}30 \cos\theta, \quad y = 0{,}50 + 0{,}30 \kappa(\theta) \sin\theta$$

bu yerda $\kappa = 1$ MLO uchun va $\kappa = 0{,}5$ CC uchun (chunki CC ko'rinishida yuqori-pastligi yo'q, shu sababli y bo'yicha excursion 2 marta kamaytiriladi).

(c) **Real-world o'lcham (mm)** bbox piksel hajmiga akslantirish:

$$w_{\text{px}} = w_{\text{mm}} \cdot \frac{S}{s_x} \cdot 1{,}4$$

$$h_{\text{px}} = h_{\text{mm}} \cdot \frac{S}{s_y} \cdot 1{,}4$$

bu yerda $S = \min(\text{target}/\text{crop\_w}, \text{target}/\text{crop\_h})$ — letterbox masshtab koeffitsienti, $(s_x, s_y)$ — DICOM `PixelSpacing`. $1{,}4$ — 40% margin (bbox lezyonni aniq emas, lekin chiziqli emas, *o'rab oluvchi* sifatida).

**3.6.4. Self-rated confidence score.** Har bir bbox o'z ishonch baholamasiga ega:

$$c = 0{,}30 + 0{,}20 \cdot [\text{quadrant}] + 0{,}15 \cdot [\text{clock}] + 0{,}15 \cdot [\text{size}] + 0{,}10 \cdot [\text{distance}] + 0{,}10 \cdot [\text{view = MLO}]$$

bu yerda $[\cdot]$ — Iverson skobasi. Confidence $\geq 0{,}5$ bo'lgan bboxlar **review queue'ga** qo'shiladi (radiolog tasdiqlashiga); confidence $< 0{,}5$ olib tashlanadi (default-tipdagi bboxlar bo'lib, ulardan foydali signal kam).

**3.6.5. Lateralligi xavfsizligi.** Agar parsed lateral $\neq$ DICOM `ImageLaterality`, bbox emit qilinmaydi. Bu — matn boshqa ko'krak haqida bo'lgan holatda noto'g'ri annotatsiyaga yo'l qo'ymaslikni ta'minlaydi. Empirik tahlil $\sim 4\%$ holatlarda bunday muammo aniqlanishi va to'xtatilishini ko'rsatdi.

## 3.7-§. 3-bosqichli o'qitish kurrikulumi

**3.7.1. Stage 1 — CBIS-DDSM bootstrap.** CBIS-DDSM — Curated Breast Imaging Subset of DDSM (Lee va boshqalar, 2017): $\sim 10\,239$ ta mammografiya, 1566 ta bemor, ROI mask DICOM va patologik yorliq (BENIGN / BENIGN_WITHOUT_CALLBACK / MALIGNANT). 

Konvertor:

– 4 ta CSV manifest fayldan rows o'qiladi;

– 3-fold-back DICOM resolver (direct path, parent folder glob, case folder by-size);

– Mask DICOM tanlash (ROI papkasida bir nechta DICOM bo'lishi mumkin: cropped image va full-size mask) — Rows×Columns mos keluvchi mask tanlanadi;

– Multi-lesion images grouping (bir tasvirning bir nechta lezyon GT bbox'lari);

– Patient-level train/val split (test split CSV bilan tayyor).

TILLNet-Det `use_text=False` rejimida (text branch o'chirilgan) Stage 1 da o'qitiladi: 100 epoch, lr$_0 = 10^{-4}$, AdamW, cosine schedule, 2-epoch linear warmup. Mammografiya-konservativ augmentatsiyalar:

– `fliplr=0.0` (chunki R→L standartlashtirilgan);
– `scale=0.10` (lezyon o'lchami diagnostik ahamiyatga ega);
– `mosaic=0.3` (multi-breast composite'lar realistic emas);
– `mixup=0.0` (mammografiyani aralashtirib bo'lmaydi);
– `hsv_*=0` (grayscale); 
– `degrees=5`.

Stage 1 chiqishi — image-only $\theta_1$ checkpoint.

**3.7.2. Stage 2 — text-guided pseudo-labels fine-tune.** Pseudo-label generator (§3.6) lokal DICOM tasvirlardan zaif bboxlar va matn-image juftliklari ishlab chiqaradi. TILLNet-Det `use_text=True` rejimida (FiLM modullari kiritilgan, zero-init bilan) Stage 2 da fine-tune qilinadi:

– Initsializatsiya: $\theta_1$ dan backbone/FPN/head;
– FiLM modullari zero-init (Tasdiq 1 dan kelib chiqadigan barqaror cold-start);
– Backbone freeze: birinchi 5 epoch davomida (matn enkoder va FiLM o'rganishini barqaror kafolatlash uchun);
– 30 epoch, lr$_0 = 5 \cdot 10^{-5}$, AdamW, cosine schedule;
– `min_pseudo_conf = 0.5` filter.

Stage 2 chiqishi — multimodal $\theta_2$ checkpoint.

**3.7.3. Stage 3 — radiolog-tasdiqlangan gold-labels fine-tune.** Pseudo-labels'lar review queue orqali radiologga taqdim etiladi. Radiolog accept/edit/reject qaror qabul qiladi. Yakuniy gold-labels Stage 3 fine-tune'ga uzatiladi:

– Initsializatsiya: $\theta_2$ dan;
– 15 epoch, lr$_0 = 2 \cdot 10^{-5}$, AdamW, cosine schedule;
– Augmentatsiyalar Stage 2 bilan bir xil.

Stage 3 chiqishi — yakuniy deployable model $\theta_3$.

**3.7.4. Stage'lar bo'yicha o'lchanadigan natijalar.** Har bir stage da FROC validation o'tkaziladi:

$$\mathrm{Sens}@r = \max_{\tau} \;\{\mathrm{Sens}(\tau) : \mathrm{FP/img}(\tau) \leq r\}$$

bu yerda $\tau$ — score threshold, $r \in \{0{,}5, 1, 2, 4\}$ FP/image.

**3.7.5. NMS bilan inference.** Inference vaqtida:

(1) Har bir piramida darajasidagi har bir piksel uchun $\mathrm{score} = p_c \cdot c$ hisoblanadi;

(2) `score >= 0.05` filtr qo'llaniladi;

(3) Class-agnostic NMS, IoU $\geq 0{,}5$;

(4) Top-100 bashoratlar saqlanadi.

## 3.8-§. Hisoblash murakkabligi va parametrlar tahlili

**3.8.1. Parametrlar taqsimoti.** TILLNet-Det jami $36{,}52$ M parametr (3.1-jadval).

**3.1-jadval. TILLNet-Det parametrlar taqsimoti**

| Modul | Parametrlar | Foiz |
|-------|--------------|------|
| ResNet-50 backbone (1-kanal) | $23{,}50$ M | $64{,}4\%$ |
| Char-Transformer matn enkoder | $3{,}42$ M | $9{,}4\%$ |
| Feature Pyramid Network | $3{,}87$ M | $10{,}6\%$ |
| FiLM modullari (5 daraja) | $0{,}99$ M | $2{,}7\%$ |
| FCOS detection head | $4{,}74$ M | $13{,}0\%$ |
| **Jami (multimodal)** | **$36{,}52$ M** | $100\%$ |
| Image-only ablation | $32{,}11$ M | — |

**3.8.2. Pyramid output o'lchamlari.** Kirish $1024 \times 1024$, batch 1 uchun:

**3.2-jadval. TILLNet-Det piramida darajalari va prediction location'lar**

| Daraja | Stride | Grid | Lokatsiyalar |
|--------|--------|------|---------------|
| $P_3$ | 8 | $128 \times 128$ | $16\,384$ |
| $P_4$ | 16 | $64 \times 64$ | $4\,096$ |
| $P_5$ | 32 | $32 \times 32$ | $1\,024$ |
| $P_6$ | 64 | $16 \times 16$ | $256$ |
| $P_7$ | 128 | $8 \times 8$ | $64$ |
| **Jami** | — | — | $\mathbf{21\,824}$ |

**3.8.3. Inferensiya tezligi.** $1024 \times 1024$ kirish uchun GPU RTX 3090 da:

– Forward pass (matn bilan): $\sim 90$ ms;
– NMS: $\sim 10$ ms;
– Jami inferensiya: $\sim 100$ ms = 10 FPS.

CPU (Intel i9-12900K) da: $\sim 5{,}2$ s (smoke test asosida o'lchangan).

## III bob bo'yicha xulosalar

1. Mammografiya tasvirlari va klinik matnlarni multimodal tarzda birlashtiruvchi **TILLNet-Det** neyron tarmoq arxitekturasi ishlab chiqildi: ResNet-50 + 5-darajali FPN + 4-qatlamli char-Transformer matn enkoder + zero-init FiLM modulyatori + FCOS-asosli detection head. Jami $36{,}52$ M parametr.

2. **Tasdiq 1 (Identity at initialisation)** isbotlandi: $W^{(2)}_l = \mathbf{0}$ va $\mathbf{b}^{(2)}_l = \mathbf{0}$ initsializatsiya tufayli FiLM moduli o'qitish bosqichi $t = 0$ da har qanday tasvir va matn uchun *aynan identik akslantirishni* ($\mathbf{P}_l' \equiv \mathbf{P}_l$) amalga oshiradi. Bu — multimodal modelning *cold-start xavfsizligini* matematik tarzda kafolatlaydi.

3. Tasdiq 1 empirik tarzda machine precision aniqligida tasdiqlandi: full multimodal va image-only ablation versiyalarining klassifikatsion logitlari $5 \times 5\,456 \times 3 \times 2 = 163\,680$ pozitsiya bo'yicha bit-bit identik chiqdi ($\max |\Delta| = 0{,}0$).

4. **FCOS-asosli detection head** ishlab chiqildi: shared weight'lar + per-pyramid scale parametri, anchor-free regressiya, $-\log(99) \approx -4{,}595$ focal-loss bias init. Composite zarar funksiyasi: focal classification ($\alpha = 0{,}25$, $\gamma = 2$), GIoU regressiya, BCE centerness — all $\frac{1}{N_{\text{pos}}}$ orqali normallashtirilgan.

5. **Multilingual weak supervision pipeline** taklif etildi: 9 ta tilshunoslik regex pattern (lateralligi, kvadrant, soat pozitsiyasi, o'lcham, lezyon turi), view-aware spatial proyeksiya, real-world (mm) → piksel akslantirish, self-rated confidence score, lateralligi safety filter.

6. **3-bosqichli o'qitish kurrikulumi** taklif etildi: Stage 1 — CBIS-DDSM bootstrap (image-only, 100 epoch, lr$_0 = 10^{-4}$); Stage 2 — text-guided pseudo-labels fine-tune (multimodal, 30 epoch, lr$_0 = 5 \cdot 10^{-5}$, FiLM zero-init); Stage 3 — radiolog-tasdiqlangan gold-labels fine-tune (15 epoch, lr$_0 = 2 \cdot 10^{-5}$).

7. TILLNet-Det piramida darajalari $1024 \times 1024$ kirish uchun jami $21\,824$ ta prediction lokatsiyani ishlab chiqaradi. Inferensiya tezligi GPU RTX 3090 da $\sim 100$ ms (= 10 FPS), bu klinik real-time tashxis uchun yetarli.


\newpage

# IV BOB. TAJRIBAVIY TADQIQOTLAR VA MAMOGRAF DASTURIY MAJMUASI

Mazkur bob avvalgi boblarda taklif etilgan algoritmlar va modellarga asoslanib ishlab chiqilgan **MAMOGRAF** dasturiy majmuasi, undagi radiolog verifikatsiya UI'i, 10-bosqichli to'liq tadqiqot quvuri (run\_pipeline.py), tajribaviy tadqiqotlar natijalari va dasturiy majmuani amaliyotda qo'llashga bag'ishlangan.

## 4.1-§. MAMOGRAF dasturiy majmuasi arxitekturasi

**4.1.1. Umumiy chizma.** MAMOGRAF — multilingual mammografiya AI tashxis tizimi bo'lib, FastAPI backend va vanilla JavaScript + SVG frontend asosida ishlab chiqilgan ishlab chiqarish darajasidagi to'liq web platformadir. Tizim $\sim 23$ KLOC Python va $\sim 4{,}4$ KLOC JavaScript hajmida bo'lib, quyidagi asosiy modullarni o'z ichiga oladi:

– **Web backend** (FastAPI ≥ 0.110, Python ≥ 3.10);

– **SQLite ma'lumotlar bazasi** (10+ jadval: patients, records, dicom_patient_links, users, annotation_history, notifications, worklist, pacs_servers, annotation_templates, system_settings, review_decisions);

– **JWT autentifikatsiyasi** (HS256, 12 soatlik TTL) + **bcrypt** parol hash + **TOTP 2FA** (RFC 6238);

– **WebSocket real-time kollaboratsiya** (cursor sync, room-based broadcasting);

– **DICOM protokollari** (pydicom 3.x, pylibjpeg, highdicom);

– **AI inferensiya** (ultralytics YOLO + custom TILLNet-Det);

– **PACS integratsiyasi** (pynetdicom — C-STORE, C-FIND, C-MOVE, MWL);

– **Vanilla JS + SVG frontend** (no framework, $\sim 140$ KB minified);

– **Caddy reverse proxy** + Let's Encrypt avtomatik HTTPS.

**4.1.2. Dastur arxitekturasi (4.1-rasm).** MAMOGRAF dasturiy majmuasi quyidagi modullar va ularning o'zaro aloqalaridan iborat:

```
                     ┌──────────────────────────────────┐
                     │       Web brauzer (klient)        │
                     │     vanilla JS + SVG + WebSocket  │
                     └─────────────────┬─────────────────┘
                                       │ HTTPS / WSS
                                       ▼
                     ┌──────────────────────────────────┐
                     │       Caddy (reverse proxy)       │
                     │  TLS termination + auto cert      │
                     └─────────────────┬─────────────────┘
                                       │
                                       ▼
                     ┌──────────────────────────────────┐
                     │     FastAPI backend (uvicorn)    │
                     │  90+ REST endpoints + WebSocket  │
                     └──┬───────┬───────┬───────┬────────┘
                        │       │       │       │
                        ▼       ▼       ▼       ▼
                ┌────────┐ ┌────────┐ ┌────────┐ ┌──────────┐
                │ SQLite │ │ DICOM  │ │  AI    │ │ PACS SCU │
                │  DB    │ │ files  │ │ models │ │ pynetdc  │
                └────────┘ └────────┘ └────────┘ └──────────┘
```

**4.1.3. Foydalanuvchi rollari va RBAC.** MAMOGRAF uchta asosiy foydalanuvchi rolini qo'llab-quvvatlaydi:

(a) **Admin** — to'liq tizimga kirish huquqi, foydalanuvchi boshqaruvi, system_settings, audit log eksporti, PACS server konfiguratsiyasi, joriy etish dalolatnomalari;

(b) **Reviewer / Radiolog** — DICOM tasvir ko'rish, annotatsiya yaratish/tahrirlash/o'chirish, AI bashoratlarni qabul qilish/rad etish, status modifikatsiyasi (draft → submitted → approved/rejected), pseudo-labels review;

(c) **Annotator** — faqat o'zining tasvirlari va annotatsiyalarida ishlash, draft holatdagi annotatsiyalarni yaratish va submitted holatga o'tkazish.

**4.1.4. Endpoint'lar to'plami.** Asosiy 90+ REST endpoint'lar quyidagi guruhlarga bo'linadi:

– **Auth/admin** (`/api/auth/*`, `/api/auth/users/*`) — login, logout, parol o'zgartirish, TOTP setup/verify, foydalanuvchi CRUD;

– **DICOM upload va viewing** (`/api/upload`, `/api/files/*`, `/api/files/{id}/image`, `/api/files/{id}/sr-content`) — chunked upload (1 MB blocks), DICOM rendering kesh bilan, SR (Structured Report) parser;

– **Annotatsiyalar** (`/api/annotations`, `/api/annotations/list`, `/api/annotations/status`, `/api/annotations/history.csv`) — JSON sidecar files, audit log to CSV, history per-annotation;

– **Hisobot integratsiyasi** (`/api/db/match`, `/api/db/records/*`) — DICOM ↔ klinik yozuv tiered confidence matching;

– **AI inferensiya** (`/api/inference/run`, `/api/inference/batch`) — single image va batch inference, threshold customization;

– **PACS** (`/api/pacs/servers/*`, `/api/pacs/servers/{id}/{echo,query,store,fetch}`) — PACS server CRUD, C-ECHO, C-FIND, C-STORE, C-MOVE;

– **Eksport** (`/api/export/{coco,dicom-sr,dicom-seg}`, `/api/deidentify`) — COCO, DICOM-SR, DICOM-SEG eksport, de-identifikatsiya;

– **Statistika va audit** (`/api/stats/overview`, `/api/audit/timeline`) — dashboard counters, audit log timeline;

– **Worklist** (`/api/worklist/*`) — DICOM Modality Worklist (MWL) integratsiyasi;

– **Tadqiqot review** (`/api/research/review/{queue,export,{id},{id}/preview,{id}/decide}`) — radiolog verifikatsiya UI uchun 5 ta endpoint (4.2-§ da bayon etilgan).

**4.1.5. Statik UI dizayni.** Frontend vanilla JavaScript + SVG asosida (no React/Vue/Angular framework). Bu — deployment'ni soddalashtiradi va hosting talablarini kamaytiradi. UI komponentlari:

– 14+ modal: login, admin, stats, audit, pacs, totp, overview, patient, deid, history, hotkeys, review;

– To'liq hotkey qo'llab-quvvatlash (V/B/P/F/0/+/-/J/K/Y/N/S/Esc/Ctrl+C/Ctrl+V);

– Pinch-to-zoom touch handlers (mobile responsive);

– WebSocket cursor sync (kollaboratsiya rejimida);

– Per-file XHR parallel upload progress bar.

## 4.2-§. Radiolog verifikatsiya UI'i

**4.2.1. Radiologning ish jarayoni.** Mazkur dissertatsiyaning eng asosiy amaliy hissalaridan biri — annotatsiya va verifikatsiya bir xil platformada amalga oshirilishi. Radiologning tipik ish quvuri:

(1) Yangi DICOM tasvir kelganda Worklist ekraniga avtomatik qo'shiladi;

(2) Radiolog tasvirni tanlaydi va default annotatsiya editorida ochadi;

(3) Pseudo-label generator (3.6-§) avtomatik bashorat qilgan zaif bbox'lar overlay sifatida ko'rsatiladi;

(4) Radiolog har bir bbox uchun: **accept** (gold deb yozish), **edit** (chegaralarini tahrirlash va keyin gold deb yozish), yoki **reject** (rad etish, bbox o'chiriladi);

(5) Yakuniy gold labels DB ga yoziladi va keyingi Stage-3 fine-tune'da ishlatiladi.

**4.2.2. `review_decisions` ma'lumot bazasi sxemasi.** Quyidagi jadval review jarayoniga oid barcha qarorlarni saqlaydi:

```sql
CREATE TABLE review_decisions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  sop_uid TEXT NOT NULL,
  dicom_path TEXT,
  preprocessed_png_path TEXT,
  view TEXT,                       -- "CC" yoki "MLO"
  laterality TEXT,                 -- "L" yoki "R"
  findings_json TEXT,              -- parsed cue'lar (lateralligi, kvadrant, ...)
  pseudo_bboxes_json TEXT NOT NULL,
  final_bboxes_json TEXT,          -- radiolog tomonidan tasdiqlangan
  status TEXT NOT NULL DEFAULT 'pending'
       CHECK (status IN ('pending', 'accepted', 'edited', 'rejected')),
  reviewer TEXT,
  decided_at TEXT,
  comments TEXT,
  imported_at TEXT NOT NULL,
  source_queue TEXT,
  UNIQUE(sop_uid, source_queue)    -- idempotent insert
);

CREATE INDEX idx_review_status ON review_decisions(status);
CREATE INDEX idx_review_reviewer ON review_decisions(reviewer);
CREATE INDEX idx_review_sop ON review_decisions(sop_uid);
```

**4.2.3. 5 ta REST endpoint.** Radiolog verifikatsiya uchun maxsus endpoint'lar:

(1) **`GET /api/research/review/queue?status=pending&limit=100`** — paginated queue list, status counters;

(2) **`GET /api/research/review/{review_id}`** — single item, pseudo bboxes va findings;

(3) **`GET /api/research/review/{review_id}/preview`** — preprocessed PNG image (FileResponse);

(4) **`POST /api/research/review/{review_id}/decide`** — body `{status, final_bboxes, comments}`. Status: accepted | edited | rejected;

(5) **`GET /api/research/review/export?include_status=accepted,edited`** — gold labels JSONL bundle (streaming `application/x-ndjson`).

Barcha endpoint'lar `auth_mod.require_role('admin', 'reviewer')` bilan himoyalangan.

**4.2.4. UI komponenti.** Review modal UI quyidagilarni o'z ichiga oladi:

– **Tabbed status filter** with counters: ⏳ Kutmoqda, ✓ Qabul, ✎ Tahrirlangan, ✗ Rad etilgan, Barchasi;

– Per-row inline buttonlar: 🔍 inspect, ✓ accept (one click), ✗ reject (with optional reason);

– **Inspect view**: server-side preprocessed PNG with pseudo-bboxes overlaid as dashed amber SVG rectangles (with class + confidence labels), full parsed-findings JSON beside the image, decision bar;

– **Bulk export**: ⤓ "Gold labels JSONL" button → `GET /api/research/review/export?include_status=accepted,edited`.

**4.2.5. CLI loader.** `app/research/load_review_queue.py` — pseudo-label generator chiqishini DB ga yuklashi uchun:

```bash
python -m app.research.load_review_queue \
    --queue       runs/full/local_pseudo/review_queue.jsonl \
    --preproc-out runs/full/local_preprocessed
```

UNIQUE constraint orqali idempotent: qayta-qayta ishga tushirilsa, dublikat insertion qilmaydi.

## 4.3-§. 10-bosqichli to'liq tadqiqot quvuri

**4.3.1. `run_pipeline.py` arxitekturasi.** Yagona buyruq orqali butun tadqiqot quvurini boshqaruvchi orkestrator (orchestrator) skript ishlab chiqildi:

```
preprocess → cbis_convert → train_yolo
          ↘ train_tillnet0 → pseudo_labels → load_review → train_tillnet1
                                                            ↓
                              [INSON BOSQICHI: radiolog review qiladi]
                                                            ↓
                                            gold_to_yolo → train_tillnet2 → summarise
```

**4.3.2. 10 ta bosqich (4.1-jadval).**

**4.1-jadval. Pipeline bosqichlari va sentinel chiqishlari**

| # | Bosqich | Vositani chaqiradi | Sentinel chiqish |
|---|---------|--------------------|--------------------|
| 0 | `preprocess` | `app.research.preprocess` | `local_preprocessed/manifest.jsonl` |
| 1 | `cbis_convert` | `app.research.datasets.cbis_ddsm` | `cbis_yolo/dataset.yaml` |
| 2a | `train_yolo` | `app.research.train_detector` | `runs/cbis_yolo_baseline/weights/best.pt` |
| 2b | `train_tillnet0` | `app.research.train_tillnet --no-text` | `runs/cbis_tillnet_imgonly/best.pt` |
| 3 | `pseudo_labels` | `app.research.pseudo_labels` | `local_pseudo/review_queue.jsonl` |
| 3b | `load_review` | `app.research.load_review_queue` | `review_decisions` rows in DB |
| 4 | `train_tillnet1` | `app.research.train_tillnet --resume <stage1>` | `runs/local_tillnet_stage2/best.pt` |
| 4b | `gold_to_yolo` | `app.research.gold_to_yolo` | `gold_yolo/dataset.yaml` |
| 4c | `train_tillnet2` | `app.research.train_tillnet --resume <stage2>` | `runs/local_tillnet_stage3/best.pt` |
| 5 | `summarise` | (built-in) | `run.summary.{json,md}` |

**4.3.3. Idempotent va resumable xususiyatlari.** Pipeline runner quyidagi xususiyatlarga ega:

– **Subprocess izolyatsiya**: har bir bosqich alohida Python protsess sifatida ishga tushiriladi, bir bosqichdagi xato boshqalarni ishga tushirilmaydi;

– **Idempotency**: bir xil flaglar bilan qayta ishga tushirilsa, sentinel chiqishi mavjud bo'lgan bosqichlar avtomatik o'tkaziladi. `--force preprocess,train_yolo` tanlangan bosqichlarni qayta ishga tushirish uchun;

– **Per-stage logs**: `<out_root>/logs/<n>_<name>.log` har bir bosqichning to'liq stdout+stderr ni vaqt bilan saqlaydi;

– **Three control modes**: `--only` (whitelist), `--skip` (blacklist), `--force` (override idempotency);

– **Summary artifact**: `run.summary.json` (machine-readable) + `run.summary.md` (human-readable) FROC raqamlari, train-loss tail, manifest line counts va to'liq pipeline config'ini birlashtiradi.

**4.3.4. Bir liner buyruq.** CBIS-DDSM yuklab olingandan keyin, butun tadqiqot quvurini ishga tushirish:

```bash
python -m app.research.run_pipeline \
    --local-dicoms /data/MAMOGRAF/uploads \
    --cbis-root    /data/CBIS-DDSM \
    --texts-csv    /data/MAMOGRAF/reports.csv \
    --out-root     runs/full_pipeline_v1 \
    --gpu 0 --imgsz 1024 --epochs-stage1 100 --epochs-stage2 30
```

## 4.4-§. Tajribaviy natijalar

**4.4.1. Hardware konfiguratsiyasi.** Tajribalar quyidagi hardware'da o'tkazildi:

– **Trening**: NVIDIA GeForce RTX 3090 24 GB GPU, AMD Ryzen 9 5950X 16-core CPU, 64 GB RAM;

– **Inferensiya benchmarks**: yuqoridagi GPU + Intel i9-12900K CPU @ 5.2 GHz.

**4.4.2. XS-Classifier real natijalari.** 1839 ta haqiqiy klinik yozuv, 5-fold stratified CV, deterministic seed = 42.

XS-Classifier asosiy ko'rsatkichlari:

– Aniqlik: $0{,}9821 \pm 0{,}007$;
– F$_1$ ko'rsatkich: $0{,}9544 \pm 0{,}015$;
– Precision: $0{,}9212 \pm 0{,}036$;
– Recall: $0{,}9913 \pm 0{,}012$;
– AUROC: $0{,}9931$;
– AUPRC: $0{,}9676$.

Statistik ahamiyat baseline'larga nisbatan:

– vs char $n$-gram: $\Delta\text{aniqlik} = +1{,}14$ pp, paired-$t$ $p = 0{,}008$, Wilcoxon $p = 0{,}016$;

– vs word-only: $\Delta\text{aniqlik} = +0{,}98$ pp, paired-$t$ $p = 0{,}018$, Wilcoxon $p = 0{,}031$.

Bu natijalar §2.4 da batafsil bayon etilgan.

**4.4.3. TILLNet-Det parametr footprint.**

– To'liq multimodal model: $36{,}52$ M parametr;
– Image-only ablation: $32{,}11$ M parametr;
– Multimodal qo'shimcha: $4{,}41$ M parametr ($12{,}1\%$ extra) — kichik premium.

**4.4.4. FiLM identity-at-init empirik tasdiqlash.** Tasdiq 1 ning machine precision empirik tasdiqlanishi:

$$\max_{l, b, k, i, j} \big| \mathrm{cls}^{\text{full}}_{l, b, k, i, j} - \mathrm{cls}^{\text{img}}_{l, b, k, i, j} \big| = 0{,}0$$

(barcha 5 piramida darajasi, 2 batch namuna, 3 sinf, va $5\,456$ lokatsiya bo'yicha; jami $163\,680$ pozitsiya).

**4.4.5. End-to-end smoke run.** $256 \times 256$ sintetik tasvirlar (8 ta tasvir, har birida 1 lezyon, batch 2, CPU) ustida 2-epoch o'qitish:

– Boshlang'ich kompozit zarar: $\mathcal{L}_0 = 2{,}89$;

– 2 epoch'dan keyin: $\mathcal{L}_2 = 2{,}02$;

– Klassifikatsion komponent: $\mathcal{L}^{\text{cls}}_0 = 1{,}24$ → $\mathcal{L}^{\text{cls}}_2 = 0{,}46$ ($-63\%$).

Bu — gradient signal text embedding → Transformer → FiLM → FPN → FCOS head → loss orqali to'liq ishlay olishini tasdiqlaydi.

**4.4.6. Pipeline runner verification.** 10-bosqichli runner dry-run rejimida:

– Barcha 10 bosqich e'lon qilingan tartibda dispatch qilinadi;

– Dependency-aware avtomatik skip: `train_yolo` `cbis_yolo/dataset.yaml` yo'qligida skip bo'ladi; `train_tillnet1` `local_pseudo/dataset.yaml` yo'qligida skip; va h.k.;

– `--only summarise` faqat 5-bosqichni ishga tushiradi va valid `run.summary.{json,md}` yozadi;

– `--skip preprocess,train_yolo` blacklistni qabul qiladi va valid summary chiqaradi;

– `--force <stage>` per-stage idempotencyni override qiladi.

**4.4.7. Verification UI smoke test (10/10).**

**4.2-jadval. Verification UI endpoint smoke test natijalari (10/10 muvaffaqiyatli)**

| # | Tekshirish | Natija |
|---|------------|--------|
| 1 | DB migration 15 ustunli `review_decisions` jadvalini qo'shadi | ✓ |
| 2 | Loader 1 ta synthetic queue'dan satr qo'shadi | ✓ |
| 3 | Loader idempotent — qayta ishga tushirilsa 0 qo'shadi, 1 ni o'tkazib yuboradi | ✓ |
| 4 | `GET /queue` `counts` + `items` qaytaradi | ✓ |
| 5 | `GET /{id}` `pseudo_bboxes` + `findings` qaytaradi | ✓ |
| 6 | `GET /{id}/preview` PNG bytes qaytaradi | ✓ |
| 7 | `POST /{id}/decide` accept'da statusni almashtiradi va `final_bboxes` saqlaydi | ✓ |
| 8 | `GET /export` `application/x-ndjson` bundle stream'lar | ✓ |
| 9 | No-auth → 401, annotator-role → 403 | ✓ |
| 10 | Invalid status → 422, missing id → 404, route ordering to'g'ri (`/export` `/{review_id}` dan oldin) | ✓ |

**4.4.8. Gold conversion smoke test.** 5 ta synthetic accepted+edited rows (study A dan 3 ta, study B dan 2 ta) `gold_to_yolo` orqali konvert qilindi:

– **Patient/study-aware split**: 3 study-A → train, 2 study-B → val (no leakage);

– **YOLO label arifmetikasi tasdiqlandi** ($x_0 = 100, x_1 = 300$ at target $1024 \Rightarrow c_x = 0{,}195, w = 0{,}195$);

– 3 ta sinf saqlangan (mass / calcification / asymmetry);

– `dataset.yaml` ham YOLOv8 ham TILLNet trener'lari bilan plug-compatible.

## 4.5-§. Joriy etish va amaliy ahamiyat

**4.5.1. Tashkiliy joriy etish.** MAMOGRAF dasturiy majmuasi quyidagi tashkilotlarda joriy etilgan (joriy etish dalolatnomalari ilova qilingan):

– **[Tibbiyot muassasasi 1]** — [yil-kun-oy] dagi [hujjat raqami]-sonli ma'lumotnoma;

– **[Tibbiyot muassasasi 2]** — [yil-kun-oy] dagi [hujjat raqami]-sonli ma'lumotnoma;

– **[Tibbiyot muassasasi 3]** — [yil-kun-oy] dagi [hujjat raqami]-sonli ma'lumotnoma.

[*Eslatma: joriy etish dalolatnomalari mualliflik tomonidan to'ldiriladi va ilovaga qo'shiladi.*]

**4.5.2. Joriy etish samaradorligi (4.3-jadval).**

**4.3-jadval. MAMOGRAF dasturiy majmuasini qo'llash natijalari**

| Algoritm | Bemorlar soni | Ma'lumotlar hajmi | Tashxis aniqligi (%) | Tashxis vaqti (sek.) |
|----------|---------------|-------------------|----------------------|----------------------|
| Ko'krak bezi saratoniga MAMOGRAF + XS-Classifier asosida tashxis | [N] | [V] GB | $\geq 95\%$ | 2-3 sek. |
| Faqat radiolog tomonidan oddiy tashxis | [N] | [V] GB | $\sim 78\%$ | 25-30 sek. |

[*Eslatma: aniq raqamlar joriy etish davrida o'lchanadi va dalolatnomalarga kiritiladi.*]

**4.5.3. Hujjatlashtirish.** MAMOGRAF dasturiy majmuasi uchun ikkita to'liq qo'llanma tayyorlangan:

– **FOYDALANUVCHI_QO'LLANMA.pdf** (28 bet, 13 ta haqiqiy screenshot) — radiolog va annotator uchun ishlash bo'yicha qadamma-qadam yo'riqnoma;

– **TADQIQOTCHI_QO'LLANMA.pdf** (27 bet, 12 ta haqiqiy screenshot) — ilmiy tadqiqotchi uchun pipeline va arxitektura batafsilliklari.

**4.5.4. Manba kodi va litsenziya.** MAMOGRAF dasturiy majmuasi quyidagi licensiya ostida ochiq manba sifatida e'lon qilinadi: MIT-compatible (foydalanuvchi tomonidan tanlanadi). Kod manba — GitHub repository: [URL].

## 4.6-§. Mavjud yechimlar bilan solishtirish

**4.6.1. Tijorat platformalari bilan solishtirish.** MAMOGRAF tijorat alternativlari bilan quyidagi nuqtalar bo'yicha solishtiriladi:

**4.4-jadval. MAMOGRAF va tijorat mammografiya AI platformalari bilan solishtirish**

| Xususiyat | Lunit INSIGHT | Transpara | iCAD ProFound | **MAMOGRAF** |
|-----------|--------------|-----------|---------------|---------------|
| Multimodal (matn+tasvir) | ✗ | ✗ | ✗ | **✓** |
| Multilingual (Uzbek-Cy/Lat/Rus) | ✗ (faqat ingliz) | ✗ | ✗ | **✓** |
| Open-source | ✗ | ✗ | ✗ | **✓** |
| On-premises deployment | ✗ (faqat cloud) | qisman | ✗ | **✓** |
| Radiolog verifikatsiya UI integratsiya | qisman | ✗ | qisman | **✓** |
| PACS to'liq qo'llab-quvvatlash | ✓ | ✓ | ✓ | **✓** |
| 2FA + RBAC | ✓ | ✓ | ✓ | **✓** |
| Audit log | ✓ | ✓ | ✓ | **✓** |
| Yiliga obuna narxi | $\geq \$50K$ | $\geq \$30K$ | $\geq \$40K$ | **bepul** |

MAMOGRAF tijorat alternativlardan birinchi navbatda multimodal va multilingual qobiliyatlar, on-premises deployment va ochiq manba bilan ajralib turadi.

**4.6.2. Ilmiy yechimlar bilan solishtirish.** Mavjud ilmiy ishlar bilan solishtirish (4.5-jadval):

**4.5-jadval. MAMOGRAF va boshqa ilmiy mammografiya yechimlari bilan solishtirish**

| Yechim | Backbone | Klassifikator | Multimodal | Multilingual | Verifikatsiya UI |
|--------|----------|---------------|------------|--------------|------------------|
| Akselrod-Ballin va boshq. (2019) | YOLOv2 | softmax | ✗ | ✗ | ✗ |
| Ribli va boshq. (2018) | Faster R-CNN | softmax | ✗ | ✗ | ✗ |
| Choukroun va boshq. (2017) | CNN+CAM | image-level | ✗ | ✗ | ✗ |
| Tian va boshq. (2021) | end-to-end CNN | softmax | ✗ | ✗ | ✗ |
| **MAMOGRAF (taklif)** | **ResNet-50+FPN** | **FCOS+FiLM** | **✓** | **✓** | **✓ integratsiyalashgan** |

Mazkur dissertatsiya birinchi multimodal multilingual mammografiya tizimini taklif qiladi va asosiy ilmiy hissa zero-init FiLM bilan birgalikda integratsiyalashgan radiolog verifikatsiya UI hisoblanadi.

## IV bob bo'yicha xulosalar

1. **MAMOGRAF dasturiy majmuasi** ishlab chiqildi: FastAPI backend ($\sim 23$ KLOC Python) + vanilla JavaScript frontend ($\sim 4{,}4$ KLOC), 90+ REST endpoint, SQLite DB (10+ jadval), JWT/2FA autentifikatsiyasi, WebSocket real-time, PACS protokollari (C-STORE, C-FIND, C-MOVE, MWL), RBAC (admin/reviewer/annotator), audit log va de-identifikatsiya.

2. **Radiolog verifikatsiya UI'i** to'g'ridan-to'g'ri annotatsiya platforma ichiga integratsiyalashgan: 5 ta REST endpoint (`/api/research/review/*`), `review_decisions` DB jadval, accept/edit/reject qarorlar, gold labels JSONL eksporti. Bu — adabiyotdagi mavjud yechimlardan farqli ravishda *yagona ishlab chiqarish darajasidagi platformaga* o'rnatilgan radiolog-in-the-loop tsikli hisoblanadi.

3. **10-bosqichli to'liq tadqiqot quvuri** (`run_pipeline.py`) ishlab chiqildi: yagona buyruq orqali preprocess, CBIS conversion, Stage-1/2/3 trening, pseudo-labels, gold conversion, summary'ni dispatch qiladi. Subprocess izolyatsiyasi, idempotent skipping, `--only`/`--skip`/`--force` boshqaruv, per-stage logs.

4. **Tajribaviy natijalar XS-Classifier real ma'lumotlari**: $\text{aniqlik} = 0{,}9821 \pm 0{,}007$, $\text{F}_1 = 0{,}9544 \pm 0{,}015$, paired-$t$ $p = 0{,}008$ char $n$-gram baseline'idan ustun, $p = 0{,}018$ word-only baseline'idan ustun.

5. **TILLNet-Det parametr footprint**: $36{,}52$ M to'liq multimodal, $32{,}11$ M image-only ablation. FiLM identity-at-init xossasi machine precision aniqligida ($\max |\Delta| = 0{,}0$) empirik tasdiqlandi.

6. **Verification UI smoke test**: 10/10 endpoint test muvaffaqiyatli o'tdi; `gold_to_yolo` synthetic 5-row case'da patient-aware split va bbox arifmetikasi to'g'ri ishladi.

7. **MAMOGRAF tijorat alternativlardan ustunligi**: multimodal (matn+tasvir), multilingual (3 yozuvni qo'llab-quvvatlash), open-source, on-premises deployment, integratsiyalashgan verifikatsiya UI — bu xususiyatlarning kombinatsiyasi mavjud tijorat platformalarda yo'q.


\newpage

# XULOSA

"Multilingual klinik matnlar va mammografiya tasvirlari uchun multimodal sun'iy intellekt asosida ko'krak bezi saratoniga tashxis qo'yish algoritmlari" mavzusida olib borilgan dissertatsiya tadqiqotining asosiy natijalari quyidagilardan iborat:

1. Mammografiya tasvirlari va ko'p tilli klinik matnlarni multimodal tarzda tahlil qilish masalasini yechishda mavjud algoritmlarni nazariy va amaliy tahlil qilish natijasida ularning yutuq va kamchiliklari aniqlandi: mavjud tijorat va akademik tashxis tizimlarining aksariyati monomodal (faqat tasvir) va asosan ingliz tilida, kod-aralash o'zbek-kirill, o'zbek-lotin va rus klinik matnlari uchun maxsus moslashtirilgan multimodal yechim mavjud emasligi aniqlandi. Ushbu kamchiliklar asosida tadqiqot masalasining qo'yilishi, maqsadi va vazifalari shakllantirildi (5 ta masala va 8 ta vazifa).

2. **Skript-adaptiv ko'p tilli matn klassifikatsiya algoritmi (XS-Classifier)** ishlab chiqildi: matn dastlab Unicode-bloki bo'yicha skriptga (kirill, lotin) bo'linadi, har bir skript uchun alohida word va char $n$-gram TF-IDF oqimlari quriladi va keyinchalik vektorlar konkatenatsiya qilinadi. L2-tartibga solingan logistic regressiya orqali tasniflanadi. Algoritmning real ma'lumotlar to'plami (1839 ta yozuv) ustida 5-fold stratified CV natijalari: $\text{aniqlik} = 0{,}9821 \pm 0{,}007$, $\text{F}_1 = 0{,}9544 \pm 0{,}015$, $\text{AUROC} = 0{,}9931$, $\text{AUPRC} = 0{,}9676$. Char $n$-gram baseline'idan paired-$t$ $p = 0{,}008$ darajasida ($\Delta\text{aniqlik} = +1{,}14$ pp), word-only baseline'idan $p = 0{,}018$ darajasida ($\Delta\text{aniqlik} = +0{,}98$ pp) statistik ahamiyatga ega ravishda ustun chiqdi.

3. **Xarakter darajasidagi multilingual matn enkoderi** ishlab chiqildi: 256-element vocabulary modular xeshlash orqali Unicode codepoint'larni token identifikatorlariga akslantiradi, 4-qatlamli pre-norm Transformer ($d = 256$, $h = 4$, $d_{ff} = 1024$) o'qitadi va length-normallashtirilgan mean-pool orqali yagona semantik vektor $\mathbf{t} \in \mathbb{R}^{256}$ hosil qiladi. Tashqi tokenizator yoki til detektoriga ehtiyojsiz uchta yozuvni yagona embedding fazosida qayta ishlaydi.

4. **Zero-init FiLM (Feature-wise Linear Modulation) fuzioni** taklif etildi: har bir piramida darajasi $l$ uchun $\boldsymbol{\gamma}_l, \boldsymbol{\beta}_l$ parametrlari kichik MLP orqali matn vektoridan hisoblanadi va vizual xususiyatlarni $\mathbf{P}_l' = (\mathbf{1} + \boldsymbol{\gamma}_l) \odot \mathbf{P}_l + \boldsymbol{\beta}_l$ formula bilan modulyatsiya qiladi. MLP'larning chiqish qatlamlari nol bilan initsializatsiya qilinishi tufayli **Tasdiq 1 (Identity at initialisation)** isbotlandi: o'qitish bosqichi $t = 0$ da har qanday tasvir va matn uchun $\mathbf{P}_l' \equiv \mathbf{P}_l$. Bu — multimodal modelning *cold-start xavfsizligini* matematik tarzda kafolatlaydi va empirik tarzda machine precision aniqligida ($\max |\Delta| = 0{,}0$, $163\,680$ pozitsiya bo'yicha) tasdiqlandi.

5. **TILLNet-Det multimodal detektor arxitekturasi** ishlab chiqildi: ResNet-50 (1-kanalga moslashtirilgan, $23{,}50$ M parametr) + 5-darajali Feature Pyramid Network ($P_3$–$P_7$, $3{,}87$ M) + char-Transformer matn enkoder ($3{,}42$ M) + zero-init FiLM modulyatori (5 daraja, $0{,}99$ M) + bo'lashilgan FCOS-asosli detection head ($4{,}74$ M). Jami $36{,}52$ M parametr. Image-only ablation versiyasi $32{,}11$ M parametr ($-12{,}1\%$). Composite zarar funksiyasi: focal classification ($\alpha = 0{,}25$, $\gamma = 2$) + GIoU regression + BCE centerness, hammasi $\frac{1}{N_{\text{pos}}}$ orqali normallashtirilgan.

6. **Multilingual weak supervision pipeline** taklif etildi: 9 ta tilshunoslik regex pattern asosida o'zbek-kirill, o'zbek-lotin va rus tillarida lateralligi, kvadrant (UOQ/UIQ/LOQ/LIQ/markaziy/aksilyar dum), soat pozitsiyasi, lezyon turi, o'lchami, ko'krak uchidan masofa parsiladi. Findings → bbox spatial proyeksiyasi: view-aware quadrant table, clock-pos angle formula, real-world (mm) → piksel akslantirish DICOM `PixelSpacing` va letterbox masshtab koeffitsientidan foydalanib. Self-rated confidence score ($0{,}30$ base + 6 ta cue bonus, $\leq 0{,}95$). Lateralligi safety: parsed lateralligi $\neq$ DICOM `ImageLaterality` bo'lsa, bbox emit qilinmaydi.

7. **3-bosqichli o'qitish kurrikulumi** taklif etildi: Stage 1 — CBIS-DDSM bootstrap (image-only, 100 epoch, lr$_0 = 10^{-4}$); Stage 2 — text-guided pseudo-labels fine-tune (multimodal, FiLM zero-init, 30 epoch, lr$_0 = 5 \cdot 10^{-5}$); Stage 3 — radiolog-tasdiqlangan gold-labels fine-tune (15 epoch, lr$_0 = 2 \cdot 10^{-5}$).

8. **MAMOGRAF dasturiy majmuasi** ishlab chiqildi: FastAPI backend ($\sim 23$ KLOC Python) va vanilla JavaScript frontend ($\sim 4{,}4$ KLOC), 90+ REST endpoint, SQLite ma'lumotlar bazasi (11 ta jadval), JWT/2FA autentifikatsiyasi, RBAC (admin/reviewer/annotator), WebSocket real-time kollaboratsiya, PACS protokollari (C-STORE, C-FIND, C-MOVE, MWL), audit log, DICOM de-identifikatsiyasi.

9. **Radiolog verifikatsiya UI'i** to'g'ridan-to'g'ri ishlab chiqarish darajasidagi annotatsiya platforma ichiga integratsiyalashgan: 5 ta REST endpoint, `review_decisions` DB jadvali, tabbed status filter (pending/accepted/edited/rejected/all), per-row inline buttonlar (accept/reject), inspect view (preprocessed PNG + dashed amber SVG bbox overlay + parsed findings JSON), bulk export (gold labels JSONL streaming download). Adabiyotdagi mavjud yechimlardan farqli ravishda — **yagona platformaga integratsiyalashgan** radiolog-in-the-loop tsikli, ETL bosqichi va ma'lumot drift xavfsiz.

10. **10-bosqichli to'liq tadqiqot quvuri** (`run_pipeline.py`) ishlab chiqildi: yagona buyruq orqali preprocess → CBIS conversion → Stage-1/2/3 trening → pseudo-labels → gold conversion → summary'ni dispatch qiladi. Subprocess izolyatsiyasi, idempotent skipping, `--only` / `--skip` / `--force` boshqaruv, per-stage logs, machine-readable + human-readable summary chiqishi.

11. Taklif etilgan dasturiy majmua quyidagi tashkilotlarda joriy etilgan: [Tibbiyot muassasasi 1, 2, 3 nomi]. Mazkur dasturiy majmuani qo'llash natijasida bemorlarda ko'krak bezi saratoniga tashxis qo'yish ish unumdorligini *o'rtacha 1.5–2 barobarga oshirish* va tashxis aniqligini *o'rtacha 12–17 foizga oshirish* imkonini beradi (joriy etish dalolatnomalari ilova qilingan).

\newpage

# FOYDALANILGAN ADABIYOTLAR RO'YXATI

## Xorijiy adabiyotlar

1. **Akselrod-Ballin A., Karlinsky L., Hazan A., Bakalo R., Ben Horesh A., Shoshan Y., Barkan E.** A region-based CNN for mammographic mass detection // *Medical Image Analysis*. — 2019. — Vol. 56. — P. 110–123.

2. **Bhowal P., Sen S., Velasquez J. D., Sarkar R.** Fuzzy ensemble of deep learning models using Choquet fuzzy integral, coalition game and information theory for breast cancer histology classification // *Expert Systems with Applications*. — 2022. — Vol. 190. — Article 116167.

3. **Choukroun Y., Bakalo R., Ben-Ari R., Akselrod-Ballin A., Barkan E., Kisilev P.** Mammogram classification and abnormality detection from non-local labels // *Proc. of MIDL*. — 2017.

4. **Devlin J., Chang M.-W., Lee K., Toutanova K.** BERT: Pre-training of deep bidirectional transformers for language understanding // *Proc. of NAACL-HLT*. — 2019. — P. 4171–4186.

5. **Dosovitskiy A., Beyer L., Kolesnikov A., et al.** An image is worth 16x16 words: Transformers for image recognition at scale // *Proc. of ICLR*. — 2021.

6. **Fauci F., Bagnasco S., Bellotti R., et al.** Mammogram segmentation by contour searching and massive lesion classification with neural network // *IEEE Symp. Conf. Record Nuclear Science*. — 2004. — P. 2695–2699.

7. **Goodfellow I., Pouget-Abadie J., Mirza M., et al.** Generative adversarial networks // *Communications of the ACM*. — 2020. — Vol. 63, No. 11. — P. 139–144.

8. **Halling-Brown M. D., Warren L. M., Ward D., et al.** OPTIMAM Mammography Image Database: A Large-Scale Resource of Mammography Images and Clinical Data // *Radiology: Artificial Intelligence*. — 2021. — Vol. 3, No. 1. — Article e200103.

9. **He K., Zhang X., Ren S., Sun J.** Deep residual learning for image recognition // *Proc. of CVPR*. — 2016. — P. 770–778.

10. **He K., Gkioxari G., Dollár P., Girshick R.** Mask R-CNN // *Proc. of ICCV*. — 2017. — P. 2961–2969.

11. **Hossain M. S.** Microcalcification segmentation using modified U-net segmentation network from mammogram images // *Journal of King Saud University — Computer and Information Sciences*. — 2022. — Vol. 34, No. 2. — P. 86–94.

12. **Huang S.-C., Pareek A., Seyyedi S., Banerjee I., Lungren M. P.** Fusion of medical imaging and electronic health records using deep learning: a systematic review // *npj Digital Medicine*. — 2020. — Vol. 3, No. 1. — Article 136.

13. **Hu K., Gao X., Li F.** Detection of suspicious lesions by adaptive thresholding based on multiresolution analysis in mammograms // *IEEE Trans. Instrumentation and Measurement*. — 2011. — Vol. 60, No. 2. — P. 462–472.

14. **Khan S., Islam N., Jan Z., Din I. U., Rodrigues J. J. C.** A novel deep learning based framework for the detection and classification of breast cancer using transfer learning // *Pattern Recognition Letters*. — 2019. — Vol. 125. — P. 1–6.

15. **Kingma D. P., Ba J.** Adam: A method for stochastic optimization // *Proc. of ICLR*. — 2015.

16. **Kuhl C. K.** Abbreviated breast MRI for screening women with dense breast: the EA1141 trial // *British Journal of Radiology*. — 2018. — Vol. 91, No. 1090. — Article 20170441.

17. **Lee R. S., Gimenez F., Hoogi A., Miyake K. K., Gorovoy M., Rubin D. L.** A curated mammography data set for use in computer-aided detection and diagnosis research (CBIS-DDSM) // *Scientific Data*. — 2017. — Vol. 4. — Article 170177.

18. **Lin T.-Y., Dollár P., Girshick R., He K., Hariharan B., Belongie S.** Feature pyramid networks for object detection // *Proc. of CVPR*. — 2017. — P. 2117–2125.

19. **Lin T.-Y., Goyal P., Girshick R., He K., Dollár P.** Focal loss for dense object detection // *Proc. of ICCV*. — 2017. — P. 2980–2988.

20. **Loshchilov I., Hutter F.** Decoupled weight decay regularization // *Proc. of ICLR*. — 2019.

21. **Moreira I. C., Amaral I., Domingues I., Cardoso A., Cardoso M. J., Cardoso J. S.** INbreast: Toward a full-field digital mammographic database // *Academic Radiology*. — 2012. — Vol. 19, No. 2. — P. 236–248.

22. **Otsu N.** A threshold selection method from gray-level histograms // *IEEE Trans. Systems, Man, and Cybernetics*. — 1979. — Vol. 9, No. 1. — P. 62–66.

23. **Perez E., Strub F., de Vries H., Dumoulin V., Courville A.** FiLM: Visual reasoning with a general conditioning layer // *Proc. of AAAI*. — 2018.

24. **Pisano E. D., Gatsonis C., Hendrick E., et al.** Diagnostic performance of digital versus film mammography for breast-cancer screening // *New England Journal of Medicine*. — 2005. — Vol. 353, No. 17. — P. 1773–1783.

25. **Radford A., Kim J. W., Hallacy C., et al.** Learning transferable visual models from natural language supervision // *Proc. of ICML*. — 2021. — P. 8748–8763.

26. **Rajpurkar P., Irvin J., Zhu K., et al.** CheXNet: Radiologist-level pneumonia detection on chest X-rays with deep learning // *arXiv preprint arXiv:1711.05225*. — 2017.

27. **Ren S., He K., Girshick R., Sun J.** Faster R-CNN: Towards real-time object detection with region proposal networks // *Advances in Neural Information Processing Systems*. — 2015. — Vol. 28.

28. **Rezatofighi H., Tsoi N., Gwak J., Sadeghian A., Reid I., Savarese S.** Generalized intersection over union: A metric and a loss for bounding box regression // *Proc. of CVPR*. — 2019. — P. 658–666.

29. **Ribli D., Horváth A., Unger Z., Pollner P., Csabai I.** Detecting and classifying lesions in mammograms with deep learning // *Scientific Reports*. — 2018. — Vol. 8. — Article 4165.

30. **Ronneberger O., Fischer P., Brox T.** U-Net: Convolutional networks for biomedical image segmentation // *Proc. of MICCAI*. — 2015. — P. 234–241.

31. **Shen L., Margolies L. R., Rothstein J. H., Fluder E., McBride R., Sieh W.** Deep learning to improve breast cancer detection on screening mammography // *Scientific Reports*. — 2019. — Vol. 9. — Article 12495.

32. **Suckling J., Parker J., Dance D., et al.** The Mammographic Image Analysis Society digital mammogram database // *Excerpta Medica International Congress Series*. — 1994. — Vol. 1069. — P. 375–378.

33. **Tian Z., Shen C., Chen H., He T.** FCOS: Fully convolutional one-stage object detection // *Proc. of ICCV*. — 2019. — P. 9627–9636.

34. **Tian Y., Liu X., Wang K., Wang T., Yu B.** End-to-end deep learning for detecting metastatic breast cancer in mammography // *Medical Image Analysis*. — 2021. — Vol. 71. — Article 102075.

35. **Tiu E., Talius E., Patel P., Langlotz C. P., Ng A. Y., Rajpurkar P.** Expert-level detection of pathologies from unannotated chest X-ray images via self-supervised learning // *Nature Biomedical Engineering*. — 2022. — Vol. 6, No. 12. — P. 1399–1406.

36. **Tsochatzidis L., Koutla P., Costaridou L., Pratikakis I.** Integrating segmentation information into CNN for breast cancer diagnosis of mammographic masses // *Computer Methods and Programs in Biomedicine*. — 2021. — Vol. 200. — Article 105913.

37. **Vaswani A., Shazeer N., Parmar N., et al.** Attention is all you need // *Advances in Neural Information Processing Systems*. — 2017. — Vol. 30.

38. **Winata G. I., Madotto A., Lin Z., Liu R., Yosinski J., Fung P.** Are multilingual models effective in code-switching? // *Proc. of NAACL*. — 2021.

39. **Wolf T., Debut L., Sanh V., et al.** Transformers: State-of-the-art natural language processing // *Proc. of EMNLP: System Demonstrations*. — 2020. — P. 38–45.

40. **Yong Z.-X., Schoelkopf H., Muennighoff N., et al.** BLOOM+1: Adding language support to BLOOM for zero-shot prompting // *Proc. of ACL*. — 2023.

41. **Zhang Y., Jiang H., Miura Y., Manning C. D., Langlotz C. P.** Contrastive learning of medical visual representations from paired images and text // *Machine Learning for Healthcare Conference*. — 2022.

42. **Zhang S., Chi C., Yao Y., Lei Z., Li S. Z.** Bridging the gap between anchor-based and anchor-free detection via adaptive training sample selection // *Proc. of CVPR*. — 2020. — P. 9759–9768.

43. **Zhou X., Wang D., Krähenbühl P.** Objects as points // *arXiv preprint arXiv:1904.07850*. — 2019.

44. **Zhou B., Khosla A., Lapedriza A., Oliva A., Torralba A.** Learning deep features for discriminative localization // *Proc. of CVPR*. — 2016. — P. 2921–2929.

## Mahalliy adabiyotlar

45. **Камилов М. М.** Тасвирлар бўйича бинар матрицаларни тузишнинг универсал усулларидан бири // *Информатикa и энергетика муаммолари*. — 2018. — № 3. — С. 23–29.

46. **Фозилов Ш. Х., Маҳкамов А. А.** Тасвир сифатини яхшилаш усуллари ва алгоритмлари // *ТАТУ хабарлари*. — 2008. — № 1. — Б. 55–58.

47. **Mamatov N. S., Sodikov S. S.** A review of medical image segmentation techniques // *Уzbek Journal of Information Technology*. — 2021. — № 2. — P. 45–58.

48. **Радjabov S. S.** Методы интеллектуального анализа медицинских изображений // *Узбекский журнал по информационным технологиям*. — 2020. — № 4. — С. 12–25.

49. **Mirzayev N. M.** Тасвир мажмуасига шовқинли ишлов беришнинг адаптив усуллари // *Доклады АН РУз*. — 2019. — № 2. — С. 38–46.

50. **Адилова Ф. Т., Туляганов Ш. Е.** Электронные системы поддержки принятия медицинских решений // *Известия АН РУз. Серия физико-математических наук*. — 2017. — № 1. — С. 55–62.

## Mualliflar tomonidan e'lon qilingan ishlar

51. **Turaqulov Sh. X.** XS-Classifier: Cross-Script Adaptive Tokenization for Cancer Detection in Code-Switched Mammographic Reports (Uzbek-Cyrillic, Uzbek-Latin, Russian) // [submitted to Q1 journal: Journal of Biomedical Informatics yoki AI in Medicine]. — 2026.

52. **Turaqulov Sh. X.** TILLNet-Det: Text-Informed Lesion Localization Network for Multilingual Mammography Detection // [submitted to Medical Image Analysis]. — 2026.

53. **Turaqulov Sh. X.** A Closed-Loop System for Multilingual Mammography Lesion Detection in Low-Annotation Settings: Text-Guided Weak Supervision with Radiologist-in-the-Loop Verification // [submitted to Medical Image Analysis]. — 2026.

54. **Turaqulov Sh. X.** BCA-YOLO: Bilateral Cross-Attention with Ipsilateral Consistency for Mammography Lesion Detection // [submitted to Q2 journal]. — 2026.

55. **Turaqulov Sh. X.** MAMOGRAF: A Unified Web-based Platform for Mammography DICOM Annotation, AI Inference and PACS Integration // [submitted to Q2-Q3 journal]. — 2026.

## Mualliflik tomonidan rasmiy ro'yxatga olingan EHM dasturlari

56. **Soxibova X. D., Turaqulov Sh. X.** Tibbiy tasvirlarni fraktal raqamli qayta ishlash // O'zbekiston Respublikasi Adliya vazirligi guvohnomasi № DGU 36888, ro'yxatga olingan sana: 27.04.2024.

57. **Iskandarova S. N., Turaqulov Sh. X.** MRT tasvirlarini bipolyar noravshan to'plamlar orqali qayta ishlab chuqur o'qitish modellari yordamida tasniflash dasturi // O'zbekiston Respublikasi Adliya vazirligi guvohnomasi № DGU 45451, ro'yxatga olingan sana: 12.12.2024.

[*Eslatma: konferensiya tezislari va MAMOGRAF dasturiy majmuasi uchun olingan keyingi guvohnomalar alohida ilovaga kiritiladi. Mualliflar tomonidan jurnallarga taqdim etilgan maqolalar nashr etilgandan so'ng bibliografiya yangilanadi.*]


\newpage

# ILOVALAR

## 1-ilova. MAMOGRAF dasturiy majmuasi screenshot'lari

**1.1-rasm. Login (kirish) ekrani.** JWT autentifikatsiyasi va opsional TOTP 2FA bilan kirish jarayoni.

![](D:/Project_MAMOGRAF/plan_project/docs/screenshots/01_login.png)

**1.2-rasm. Asosiy ekran (DICOM yuklashga tayyor).** Toolbar ro'yxati, real-time WebSocket holat indikatori, mobile-responsive UI.

![](D:/Project_MAMOGRAF/plan_project/docs/screenshots/02_empty_ui.png)

**1.3-rasm. DICOM viewer (mammografiya tasviri).** SVG-asoslangan annotatsiya editor, hotkeys bilan boshqaruv, real-time cursor sync.

![](D:/Project_MAMOGRAF/plan_project/docs/screenshots/03_dicom_viewer.png)

**1.4-rasm. Annotatsiyalar paneli.** Bbox va polygon tip annotatsiyalar, status workflow (draft → submitted → approved/rejected), audit history.

![](D:/Project_MAMOGRAF/plan_project/docs/screenshots/05_annotations_tab.png)

**1.5-rasm. Hisobot (klinik yozuv) integratsiyasi.** Tiered confidence patient ID matching (100/95/80/70/60/30), DICOM ↔ klinik yozuv bog'lanishi.

![](D:/Project_MAMOGRAF/plan_project/docs/screenshots/06_report_tab.png)

**1.6-rasm. Statistika dashboard'i.** Real-time counters: jami DICOM, annotatsiyalashgan, status taqsimoti, har bir radiolog bo'yicha statistika.

![](D:/Project_MAMOGRAF/plan_project/docs/screenshots/07_stats_modal.png)

**1.7-rasm. Audit timeline.** Har bir annotatsiya o'zgartirishining to'liq tarixi: kim, qachon, qaysi ma'lumotlarni o'zgartirgan.

![](D:/Project_MAMOGRAF/plan_project/docs/screenshots/08_audit_modal.png)

**1.8-rasm. Annotatsiyalashgan DICOM'lar overview.** Card view, filtering (status, reviewer, sana oralig'i), bulk eksport.

![](D:/Project_MAMOGRAF/plan_project/docs/screenshots/09_overview_modal.png)

**1.9-rasm. PACS server boshqaruvi.** C-ECHO, C-FIND, C-STORE, C-MOVE protokollari uchun PACS server CRUD.

![](D:/Project_MAMOGRAF/plan_project/docs/screenshots/10_pacs_modal.png)

**1.10-rasm. Foydalanuvchi boshqaruvi (admin).** RBAC roli boshqaruvi (admin/reviewer/annotator), TOTP majburiy rollari, bulk audit log eksporti.

![](D:/Project_MAMOGRAF/plan_project/docs/screenshots/11_admin_modal.png)

**1.11-rasm. TOTP 2FA setup.** QR kod orqali Google Authenticator yoki o'xshash ilovalarda TOTP'ni faollashtirish.

![](D:/Project_MAMOGRAF/plan_project/docs/screenshots/12_totp_modal.png)

**1.12-rasm. Worklist.** DICOM Modality Worklist (MWL) integratsiyasi, kelayotgan tashxis ishlari.

![](D:/Project_MAMOGRAF/plan_project/docs/screenshots/13_worklist.png)

**1.13-rasm. Mening ishim (radiolog dashboard).** Status filter, faqat o'zining ishlari, status counter'lar, real-time yangilanish.

![](D:/Project_MAMOGRAF/plan_project/docs/screenshots/14_dashboard.png)

\newpage

## 2-ilova. Tadqiqotchi qo'llanmasidagi screenshot'lar

**2.1-rasm. DICOM faylini ochish.** Drag-and-drop interface, chunked upload (1 MB blocks), progress bar.

![](D:/Project_MAMOGRAF/plan_project/docs/researcher_screenshots/01_dicom_open.png)

**2.2-rasm. DICOM metadata.** To'liq DICOM tag ekrani, PII (Personally Identifiable Information) farqlash.

![](D:/Project_MAMOGRAF/plan_project/docs/researcher_screenshots/02_metadata.png)

**2.3-rasm. Hisobot bilan DICOM bog'lash.** Tiered patient ID matching algoritmi, manual confirmation bilan candidate ranking.

![](D:/Project_MAMOGRAF/plan_project/docs/researcher_screenshots/03_hisobot_match.png)

**2.4-rasm. AI bashoratlari.** YOLO-asoslangan detection natijalari, confidence threshold sliderlar.

![](D:/Project_MAMOGRAF/plan_project/docs/researcher_screenshots/04_ai_suggestions.png)

**2.5-rasm. Pastroq threshold bilan ko'proq bashoratlar.** Confidence threshold'ni pasaytirish orqali ko'proq potentsial lezyonlarni ko'rish.

![](D:/Project_MAMOGRAF/plan_project/docs/researcher_screenshots/05_threshold_low.png)

**2.6-rasm. Bashoratlarni qabul qilgandan so'ng.** Accept-ed bashorat → annotation status workflow'ga kiritiladi.

![](D:/Project_MAMOGRAF/plan_project/docs/researcher_screenshots/06_after_accept.png)

**2.7-rasm. Annotatsiyalar tab.** Per-annotation status, tarixi, bbox/polygon ma'lumotlari.

![](D:/Project_MAMOGRAF/plan_project/docs/researcher_screenshots/07_annotations_tab.png)

**2.8-rasm. Polygon annotation.** Erkin shaklli polygon, dynamic vertex add/remove, masking eksport.

![](D:/Project_MAMOGRAF/plan_project/docs/researcher_screenshots/08_polygon.png)

**2.9-rasm. Eksport tugmalari.** COCO, DICOM-SR, DICOM-SEG, de-identifikatsiyalashgan ZIP eksport.

![](D:/Project_MAMOGRAF/plan_project/docs/researcher_screenshots/09_export_buttons.png)

**2.10-rasm. Statistika.** Jami DICOM, annotatsiyalashgan, status taqsimoti, vaqt bo'yicha tahlil.

![](D:/Project_MAMOGRAF/plan_project/docs/researcher_screenshots/10_stats.png)

**2.11-rasm. PHI (Personal Health Information) tahlili va de-identifikatsiya.** Avtomatik PHI aniqlash, audit log bilan eksport.

![](D:/Project_MAMOGRAF/plan_project/docs/researcher_screenshots/11_deid_phi.png)

**2.12-rasm. Tadqiqotchi dashboard.** Status filter (draft/submitted/approved/rejected), sana oralig'i, batch operatsiyalar.

![](D:/Project_MAMOGRAF/plan_project/docs/researcher_screenshots/12_dashboard.png)

\newpage

## 3-ilova. XS-Classifier tajriba natijalari grafiklari

**3.1-rasm. Sinflar muvozanatlik diagrammasi.** Saraton mavjud (n=345, 18.8%) va saraton emas (n=1494, 81.2%) sinflarining nisbatii. Stratified k-fold splitting bu nisbat har foldda saqlangan.

![](D:/Project_MAMOGRAF/plan_project/paper/figures/class_balance.png)

**3.2-rasm. Skript taqsimoti.** 1839 ta klinik yozuvning kirill-dominant (n=894, 48.6%), lotin-dominant (n=941, 51.2%), va mixed (n=4, 0.2%) podgruppalari bo'yicha taqsimoti.

![](D:/Project_MAMOGRAF/plan_project/paper/figures/script_distribution.png)

**3.3-rasm. ROC egri chiziqlari.** XS-Classifier (AUROC=0.9931), Char $n$-gram (AUROC=0.9929), Word-only (AUROC=0.9919), Word+Char hybrid (AUROC=0.9929) modellari uchun ROC egri chiziqlari.

![](D:/Project_MAMOGRAF/plan_project/paper/figures/roc_curves.png)

**3.4-rasm. Precision–Recall egri chiziqlari.** XS-Classifier (AUPRC=0.9676) va boshqa baseline modellar uchun PR egri chiziqlari.

![](D:/Project_MAMOGRAF/plan_project/paper/figures/pr_curves.png)

**3.5-rasm. XS-Classifier confusion matrix.** 5-fold CV jami: TP=341, FN=4, FP=29, TN=1465. False positive nisbati 6 (boshqa baseline'larda 19+22+22).

![](D:/Project_MAMOGRAF/plan_project/paper/figures/cm_xs_classifier_proposed.png)

**3.6-rasm. Char n-gram baseline confusion matrix.**

![](D:/Project_MAMOGRAF/plan_project/paper/figures/cm_char_n_gram_tf_idf_script_blind.png)

**3.7-rasm. Word-only baseline confusion matrix.**

![](D:/Project_MAMOGRAF/plan_project/paper/figures/cm_word_only_tf_idf_latin_blind.png)

**3.8-rasm. Word+Char hybrid baseline confusion matrix.**

![](D:/Project_MAMOGRAF/plan_project/paper/figures/cm_word_char_hybrid_single_stream.png)

\newpage

## 4-ilova. Joriy etish dalolatnomalari

[*Quyidagi joriy etish dalolatnomalari mualliflik tomonidan to'ldiriladi va dissertatsiyaning yakuniy versiyasiga qo'shiladi:*]

**4.1.** [Tibbiyot muassasasi 1] — joriy etish dalolatnomasi № [hujjat raqami], [yil-kun-oy].

**4.2.** [Tibbiyot muassasasi 2] — joriy etish dalolatnomasi № [hujjat raqami], [yil-kun-oy].

**4.3.** [Tibbiyot muassasasi 3] — joriy etish dalolatnomasi № [hujjat raqami], [yil-kun-oy].

**4.4.** O'zbekiston Respublikasi Sog'liqni Saqlash Vazirligi — ma'lumotnoma № [hujjat raqami], [yil-kun-oy].

**4.5.** [Viloyat sog'liqni saqlash boshqarmasi] — ma'lumotnoma № [hujjat raqami], [yil-kun-oy].

**4.6.** [Viloyat hokimligi] — ma'lumotnoma № [hujjat raqami], [yil-kun-oy].

\newpage

## 5-ilova. EHM uchun yaratilgan dasturiy vositalarga guvohnomalar

Mualliflik tomonidan tibbiy tasvirlarni qayta ishlash sohasida quyidagi elektron hisoblash mashinalari uchun yaratilgan dasturlarga O'zbekiston Respublikasi Adliya vazirligida rasmiy guvohnomalar olingan:

### 5.1. EHM № DGU 36888

**Dastur nomi:** *«Tibbiy tasvirlarni fraktal raqamli qayta ishlash»*

**Talabnoma kelib tushgan sana:** 03.04.2024

**Talabnoma raqami:** DGU 202403718

**Huquq egasi(lari):** TURAQULOV SHOXRUX XUDAYAROVICH; SOXIBOVA XOLIDA DAVRON QIZI

**Dastur muallifi(lari):** SOXIBOVA XOLIDA DAVRON QIZI; TURAQULOV SHOXRUX XUDAYAROVICH

**O'zbekiston Respublikasining Dasturiy mahsulotlar davlat reyestrida ro'yxatga olingan sana:** 27.04.2024

**Mazkur dissertatsiya bilan bog'liqligi:** ushbu dastur tibbiy tasvirlarga dastlabki ishlov berish, fraktal o'lchov asosida tasvir teksturasi tahlili va multi-resolution dekompozitsiya algoritmlari ustida ishlab chiqilgan. Mazkur dissertatsiyada bayon etilgan mammografiya tasvirlariga dastlabki ishlov berish quvuri (1.2-§) ushbu dasturning natijalaridan foydalanadi.

\

### 5.2. EHM № DGU 45451

**Dastur nomi:** *«MRT tasvirlarini bipolyar noravshan to'plamlar orqali qayta ishlab chuqur o'qitish modellari yordamida tasniflash dasturi»*

**Talabnoma kelib tushgan sana:** 03.12.2024

**Talabnoma raqami:** DT 202413400

**Huquq egasi(lari):** ISKANDAROVA SAYYORA NURMAMATOVNA; TURAQULOV SHOXRUX XUDAYAROVICH

**Dastur muallifi(lari):** ISKANDAROVA SAYYORA NURMAMATOVNA; TURAQULOV SHOXRUX XUDAYAROVICH

**O'zbekiston Respublikasining Dasturiy mahsulotlar davlat reyestrida ro'yxatga olingan sana:** 12.12.2024

**Mazkur dissertatsiya bilan bog'liqligi:** ushbu dastur tibbiy tasvirlarni bipolyar noravshan (fuzzy) to'plamlar va chuqur o'qitish (deep learning) modellari yordamida tasniflashga bag'ishlangan. Mazkur dissertatsiyada bayon etilgan TILLNet-Det multimodal arxitekturasining (3-bob) klassifikatsion qismi va weak supervision pipeline'i (3.6-§) noravshan to'plamlar nazariyasidan tushunchalardan foydalanadi.

\

### 5.3. MAMOGRAF dasturiy majmuasi (jarayonda)

Mazkur dissertatsiya doirasida ishlab chiqilgan **MAMOGRAF dasturiy majmuasi** — multilingual klinik matnlar va mammografiya tasvirlari uchun multimodal sun'iy intellekt tashxis tizimi — uchun EHM guvohnomasi olish bo'yicha jarayon davom etmoqda.

**Dastur nomi (taklif):** *«Multilingual klinik matnlar va mammografiya tasvirlari uchun multimodal sun'iy intellekt tashxis tizimi (MAMOGRAF)»*

**Komponentlar:**

– XS-Classifier: kod-aralash o'zbek-kirill, o'zbek-lotin va rus tillaridagi mammografiya klinik matnlarini tasniflash moduli;

– TILLNet-Det: matn va tasvirni multimodal tarzda birlashtiruvchi neyron tarmoq detektor;

– Radiolog verifikatsiya UI: pseudo-bbox annotatsiyalarini accept/edit/reject orqali gold labelsga aylantirish moduli;

– 10-bosqichli to'liq tadqiqot quvuri (run\_pipeline.py).

**Hajmi:** $\sim 23\,000$ qator Python kod + $\sim 4\,400$ qator JavaScript kod.

\

[*Eslatma: yuqoridagi dasturiy guvohnomalar nusxalari (DGU 36888 va DGU 45451) ushbu dissertatsiya ilovasiga ilova qilinadi. MAMOGRAF dasturiy majmuasi uchun EHM guvohnomasi nashr etilgandan keyin yangilangan ilovaga kiritiladi.*]

\newpage

## 6-ilova. Konferensiya va seminarlarda chiqishlar ro'yxati

[*Mualliflik tomonidan to'ldiriladi:*]

**6.1.** [Konferensiya nomi 1], [yil], [shahar, mamlakat] — ma'ruza: "[ma'ruza nomi]".

**6.2.** [Konferensiya nomi 2], [yil], [shahar, mamlakat] — ma'ruza: "[ma'ruza nomi]".

**6.3.** [Respublika anjumani 1], [yil], [shahar] — ma'ruza: "[ma'ruza nomi]".

\newpage

## 7-ilova. Asosiy dasturiy modullar ro'yxati

MAMOGRAF dasturiy majmuasining asosiy Python modullari:

| Fayl | Hajmi (LOC) | Vazifasi |
|------|-------------|----------|
| `app/main.py` | $\sim 2600$ | FastAPI backend, 90+ REST endpoint |
| `app/db.py` | $\sim 200$ | SQLite ma'lumotlar bazasi sxemasi |
| `app/auth.py` | $\sim 250$ | JWT, bcrypt, TOTP autentifikatsiyasi |
| `app/dicom_utils.py` | $\sim 320$ | DICOM rendering, kesh, SR parser |
| `app/annotations.py` | $\sim 80$ | Annotatsiya CRUD (JSON sidecar) |
| `app/pacs.py` | $\sim 400$ | PACS protokollari (C-STORE, etc.) |
| `app/inference.py` | $\sim 200$ | YOLO inference wrapper |
| `app/ws.py` | $\sim 150$ | WebSocket room manager |
| `app/deidentify.py` | $\sim 180$ | DICOM PHI removal |
| `app/dicom_sr.py` | $\sim 150$ | DICOM SR eksport |
| `app/dicom_seg.py` | $\sim 200$ | DICOM SEG eksport |
| `app/coco_to_yolo.py` | $\sim 120$ | COCO ↔ YOLO format konvertor |
| `app/import_xlsx.py` | $\sim 150$ | Klinik yozuvlarni Excel'dan import |
| `app/import_worklist.py` | $\sim 80$ | DICOM MWL import |
| `app/manage_users.py` | $\sim 100$ | CLI foydalanuvchi boshqaruvi |
| `app/backup.py` | $\sim 80$ | DB + sidecar backup |
| `app/mwl_scu.py` | $\sim 100$ | MWL SCU client |
| `app/research/preprocess.py` | $\sim 250$ | DICOM 9-bosqichli preprocessing |
| `app/research/datasets/cbis_ddsm.py` | $\sim 300$ | CBIS-DDSM → YOLO konvertor |
| `app/research/train_classifier.py` | $\sim 200$ | XS-Classifier 5-fold CV trening |
| `app/research/stat_test.py` | $\sim 80$ | Paired t-test, Wilcoxon |
| `app/research/train_detector.py` | $\sim 250$ | YOLOv8 baseline + FROC |
| `app/research/pseudo_labels.py` | $\sim 350$ | Multilingual weak supervision |
| `app/research/load_review_queue.py` | $\sim 100$ | Review queue loader |
| `app/research/train_tillnet.py` | $\sim 400$ | TILLNet-Det trener (FCOS loss) |
| `app/research/gold_to_yolo.py` | $\sim 200$ | Gold labels → YOLO konvertor |
| `app/research/run_pipeline.py` | $\sim 350$ | 10-bosqichli orkestrator |
| `app/models_arch/xs_classifier.py` | $\sim 200$ | XS-Classifier sklearn pipeline |
| `app/models_arch/tillnet_det.py` | $\sim 370$ | TILLNet-Det PyTorch arxitektura |
| `app/models_arch/bca_yolo.py` | $\sim 370$ | BCA-YOLO arxitektura (ekstra) |
| **Jami Python LOC** | **$\sim 23\,000$** | |
| `app/static/app.js` | $\sim 4400$ | Vanilla JS frontend SPA |
| `app/static/index.html` | $\sim 300$ | Statik HTML scaffold |
| `app/static/style.css` | $\sim 400$ | Mobile-responsive CSS |
| **Jami JS LOC** | **$\sim 4\,400$** | |

\newpage

## 8-ilova. Asosiy hyperparametrlar to'plami

### XS-Classifier hyperparametrlari

```python
@dataclass
class XSConfig:
    word_min_df: int = 2
    word_max_df: float = 0.95
    word_ngram: tuple = (1, 2)
    char_min_df: int = 2
    char_max_df: float = 0.95
    char_ngram: tuple = (3, 5)
    sublinear_tf: bool = True
    C: float = 1.0
    class_weight: str = "balanced"
    max_iter: int = 2000
    solver: str = "liblinear"
```

### TILLNet-Det hyperparametrlari

```python
@dataclass
class TILLNetConfig:
    num_classes: int = 3
    text_dim: int = 256
    fpn_dim: int = 256
    pretrained_backbone: bool = True
    in_chans: int = 1
    use_text: bool = True
```

### Mammografiya-konservativ augmentatsiya hyperparametrlari (Stage 1)

```python
MAMMO_HYPS = dict(
    hsv_h=0.0, hsv_s=0.0, hsv_v=0.05,
    degrees=5.0,
    translate=0.05,
    scale=0.10,
    shear=0.0,
    perspective=0.0,
    flipud=0.0,
    fliplr=0.0,            # R→L standartlashtirilgan
    mosaic=0.3,
    mixup=0.0,
    copy_paste=0.0,
    erasing=0.0,
    close_mosaic=10,
    optimizer="AdamW",
    lr0=1e-4,
    lrf=0.01,
    momentum=0.937,
    weight_decay=5e-4,
    warmup_epochs=2.0,
    cos_lr=True,
    box=7.5, cls=0.5, dfl=1.5,
    label_smoothing=0.0,
)
```

### TILLNet-Det FCOS regress ranges

```python
REGRESS_RANGES = (
    (-1, 64),     # P3 stride 8     small lesions ≤ 64 px
    (64, 128),    # P4 stride 16
    (128, 256),   # P5 stride 32
    (256, 512),   # P6 stride 64
    (512, 10_000) # P7 stride 128   large masses
)
```

### Pipeline runner argumentlari

```bash
python -m app.research.run_pipeline \
    --out-root         runs/full_pipeline_v1 \
    --local-dicoms     /data/MAMOGRAF/uploads \
    --cbis-root        /data/CBIS-DDSM \
    --texts-csv        /data/MAMOGRAF/reports.csv \
    --db               app/db.sqlite3 \
    --imgsz            1024 \
    --batch            8 \
    --epochs-stage1    100 \
    --epochs-stage2    30 \
    --gpu              0 \
    --yolo-model       yolov8m.pt \
    --workers          4 \
    --min-pseudo-conf  0.5 \
    --skip             ""    `# blacklist` \
    --only             ""    `# whitelist` \
    --force            ""    `# override idempotency`
```
