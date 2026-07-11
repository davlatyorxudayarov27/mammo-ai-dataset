# PROMPT — Claude Code uchun

Quyidagi vazifani bajar. Bu mavjud mammografiya loyihasiga (YOLO asosidagi detektsiya, 8 sinf) **ikkinchi bosqichli, interpretatsiya qilinadigan klassifikator** qoʻshish vazifasi. Metodologik asos: R.X. Xamdamov, «Задачи, модели и методы булева программирования» (Toshkent, 2017) — III bob (informativ belgilar toʻplamini qurish) va 3.6-boʻlim (minimal masofa klassifikatori).

---

## 0. Kontekst

- Loyiha: mammogrammalarda patologiyalarni aniqlash. Detektor: `yolo11s`, 8 sinf, ~173 ta rasm, mAP50≈0.43.
- Muammolar: (1) sinflar kuchli nomutanosib (`architectural_distortion` — atigi 2 ta misol), (2) kichik dataset tufayli YOLO klassifikatsiya qismi overfitting qiladi va sinflar chalkashadi, (3) kalsifikatsiyalar kichik obyekt boʻlgani uchun yomon aniqlanadi.
- Yechim gʻoyasi: YOLO faqat ROI lokalizatsiyasini beradi; har bir ROI'dan klassik radiomika belgilar ajratiladi, bulcha dasturlash usuli bilan informativ belgilar qism-toʻplami tanlanadi va ROI sinfi minimal masofa qoidasi bilan qayta baholanadi. Natija YOLO class score bilan ensemble qilinadi.

**Boshlashdan oldin:** loyiha strukturasini oʻrganib chiq — dataset joylashuvi (YOLO formatdagi `images/` + `labels/`, `data.yaml`), sinf nomlari roʻyxati, train/val boʻlinishi qayerda ekanini aniqla va shu real yoʻllardan foydalan. Hech narsani taxmin qilma, topolmasang mendan soʻra.

---

## 1. Yangi modul: `boolfs/` (boolean feature selection)

Quyidagi fayllarni yarat:

```
boolfs/
├── __init__.py
├── features.py        # ROI'dan belgi ajratish
├── criterion.py       # a_j, b_j, c_j va Ф(λ) hisoblash
├── selector.py        # ranjirlangan qator usuli bilan λ* tanlash
├── classifier.py      # minimal masofa klassifikatori (3.6.2–3.6.3)
├── pipeline.py        # end-to-end: dataset → hisobot
└── report.py          # natijalar hisoboti (markdown + grafiklar)
```

## 2. `features.py` — belgi ajratish

Har bir ROI (bounding box kesib olingan grayscale patch, 8-bit ga normallashtirilgan) uchun **faqat skimage/numpy/scipy** bilan (pyradiomics ISHLATMA) quyidagi belgilar vektorini hisobla:

1. **Intensivlik statistikasi (8 ta):** mean, std, median, skewness, kurtosis, entropy (histogram, 64 bin), 10- va 90-persentil.
2. **GLCM tekstura (skimage.feature.graycomatrix/graycoprops):** distances=[1, 3], angles=[0, π/4, π/2, 3π/4], xossalar: contrast, dissimilarity, homogeneity, energy, correlation, ASM. Har xossa boʻyicha 4 burchak boʻyicha oʻrtacha olinadi → 6 xossa × 2 masofa = 12 belgi.
3. **LBP (local binary pattern):** P=8, R=1, method='uniform' → 10-binli normalangan gistogramma = 10 belgi.
4. **Shakl belgilari (label maskasidan, Otsu threshold orqali):** area_ratio (obyekt/box), eccentricity, solidity, extent, perimeter/√area (kompaktlik), bbox aspect ratio = 6 belgi.
5. **Gradient:** Sobel magnitude'ning mean va std = 2 belgi.

Jami ≈38 belgi. Har bir belgiga barqaror string nom ber (masalan `glcm_d1_contrast`). Barcha belgilar train toʻplami boʻyicha z-score normalizatsiya qilinsin (mean/std saqlansin — inference'da qayta ishlatiladi).

ROI manbai ikki rejimda:
- `--source gt` — ground-truth labellardan (train/val uchun);
- `--source pred` — YOLO detektsiyalaridan (inference/ensemble uchun).

## 3. `criterion.py` — Xamdamov formulalari

Sinflar juftligi (p, q) va j-belgi uchun **aynan quyidagi formulalarni** implement qil (kitobdagi (3.2.2)):

```
a_j = Σ_{l=1..k_p} Σ_{t=1..k_q} (x_plj − x_qtj)²      # sinflararo
b_j = Σ_{l=1..k_p} Σ_{t=1..k_p} (x_plj − x_ptj)²      # p-sinf ichida
c_j = Σ_{l=1..k_q} Σ_{t=1..k_q} (x_qlj − x_qtj)²      # q-sinf ichida
```

Bularni vektorlashtirilgan holda hisobla (hint: Σ_l Σ_t (u_l − v_t)² = k_q·Σu² + k_p·Σv² − 2·Σu·Σv — O(k) da hisoblanadi, ikki karra sikl yozma).

Koʻp sinf (m=8) uchun ikkita rejim:
- `pairwise` — har bir (p,q) juftlik uchun alohida;
- `global` — a_j = Σ_{p<q} a_j^{(pq)}, b_j+c_j = Σ_p (sinf ichidagi yigʻindi), asosiy rejim shu.

Funksional (kitobdagi Ф₁):

```
Ф(λ) = Σ_j a_j·λ_j / Σ_j (b_j + c_j)·λ_j → max,  λ_j ∈ {0,1}
```

## 4. `selector.py` — umumlashgan tengsizliklar usuli (3.4)

1. Belgilarni r_j = a_j / (b_j + c_j) nisbati boʻyicha kamayish tartibida ranjirla — (3.4.5) qator.
2. Har bir nʹ = 1..n uchun optimal toʻplam — ranjirlangan qatorning dastlabki nʹ elementi ekanligidan foydalanib, Ф(nʹ) qiymatlarini prefiks-yigʻindilar orqali hisobla (kitobdagi (3.4.4) tengsizliklar zanjiriga mos).
3. Natija: har bir nʹ uchun (tanlangan belgilar roʻyxati, Ф qiymati) jadvali.

Yakuniy nʹ* ni Ф boʻyicha emas, **klassifikatsiya sifati boʻyicha** tanla (5-band, kitobdagi P(n*) = max P(nʹ) prinsipi).

## 5. `classifier.py` — minimal masofa qoidasi (3.6.2–3.6.4)

Har bir sinf p uchun etalon x̄ᵖ (train boʻyicha oʻrtacha vektor) va sinf ichki tarqoqligi S(X_p) hisoblansin. Yangi obyekt x uchun:

```
ρ_p(x) = Σ_j λ_j·(x_j − x̄ᵖ_j)² / S(X_p)
sinf(x) = argmin_p ρ_p(x)                        # (3.6.3)
```

Ishonchlilik oʻlchovi: P = toʻgʻri tanilganlar / jami (3.6.4). k_p < 5 boʻlgan sinflar uchun (masalan architectural_distortion) leave-one-out rejimida bahola; qolganlar uchun stratified 5-fold CV. nʹ = 1..n boʻyicha P(nʹ) egri chizigʻini qur va P maksimal boʻlgan nʹ* ni tanla.

Softmax-koʻrinishdagi score ham qaytar: s_p = exp(−ρ_p) / Σ_q exp(−ρ_q) — ensemble uchun kerak.

## 6. `pipeline.py` va CLI

```
python -m boolfs.pipeline fit      --data <data.yaml> --source gt  --out runs/boolfs/
python -m boolfs.pipeline evaluate --data <data.yaml> --model runs/boolfs/model.json
python -m boolfs.pipeline ensemble --pred <yolo_preds> --model runs/boolfs/model.json --alpha 0.5
```

- `fit`: belgilar ajratish → a_j/b_j/c_j → ranjirlash → nʹ* tanlash → `model.json` ga saqlash (belgi nomlari, λ*, x̄ᵖ, S(X_p), normalizatsiya parametrlari).
- `evaluate`: confusion matrix, per-class precision/recall, P qiymati.
- `ensemble`: yakuniy score = α·YOLO_score + (1−α)·s_p; α ∈ {0.3, 0.5, 0.7} boʻyicha natijalarni taqqosla.

## 7. `report.py` — hisobot (markdown, `runs/boolfs/report.md`)

Majburiy boʻlimlar:
1. Ranjirlangan qator jadvali: top-20 belgi, r_j qiymatlari bilan.
2. Ф(nʹ) va P(nʹ) grafigi (matplotlib, bitta rasmda ikki oʻq).
3. **Sinf juftliklari ajraluvchanlik matritsasi** (8×8): har (p,q) uchun tanlangan belgilar boʻyicha pairwise Ф qiymati — qaysi sinflar belgi fazosida ajralmasligini koʻrsatadi. Bu ilmiy maqola uchun asosiy jadval.
4. Confusion matrix: faqat YOLO vs YOLO+boolfs ensemble taqqoslash.
5. Xulosa: qaysi sinflarda yaxshilanish boʻldi, kam sonli sinflar boʻyicha alohida izoh.

## 8. Sifat talablari

- Python 3.10+, faqat: numpy, scipy, scikit-image, matplotlib, pyyaml, ultralytics (mavjud boʻlsa). Yangi ogʻir dependency qoʻshma.
- Har bir modulga docstring — formulalar kitobdagi raqami bilan ((3.2.2), (3.4.5), (3.6.2)...) izohlansin.
- `tests/test_boolfs.py`: (1) a_j/b_j/c_j vektorlashtirilgan hisobini toʻgʻridan-toʻgʻri ikki karra sikl bilan solishtiruvchi test (kichik sunʼiy data), (2) selector'ning monotonligi (ranjirlangan prefiks optimalligi) testi, (3) sintetik ajraladigan 3 sinf uchun P=1.0 boʻlishini tekshiruvchi test. Testlar oʻtmaguncha tugatma.
- Har bosqichda nima qilinganini qisqa log qilib bor; dataset yoʻllari topilmasa toʻxtab mendan soʻra.

Ishni `fit` → `evaluate` → `report` tartibida bajarib, oxirida `report.md` dagi asosiy natijalarni menga qisqacha yozib ber.
