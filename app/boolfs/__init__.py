"""boolfs — bulcha dasturlash asosida informativ belgilar tanlash va
minimal masofa klassifikatori.

Metodologik asos: R.X. Xamdamov, «Задачи, модели и методы булева
программирования» (Toshkent, 2017):
  - III bob — informativ belgilar to'plamini qurish, (3.2.2) kriteriy;
  - 3.4 — umumlashgan tengsizliklar (ranjirlangan qator) usuli, (3.4.4)-(3.4.5);
  - 3.6 — minimal masofa klassifikatori, (3.6.2)-(3.6.4).

YOLO detektori ROI lokalizatsiyasini beradi; ROI'dan klassik radiomika
belgilar ajratiladi (features.py), informativ qism-to'plam tanlanadi
(criterion.py + selector.py), sinf minimal masofa qoidasi bilan qayta
baholanadi (classifier.py) va YOLO score bilan ensemble qilinadi (pipeline.py).
"""

__version__ = "1.0.0"
