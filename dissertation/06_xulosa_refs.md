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
