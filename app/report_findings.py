"""Strukturaviy 'findings' — detektor + radiomics + DICOM metadata'dan.

Bu hisobot generatorining (report_gen.py) yagona kirish formati. Detektor hali
o'rgatilmagan bo'lsa ham, bu modulni mock ma'lumot bilan sinash mumkin.

Oqim:
    detektor qutilari + DICOM meta + radiomics  ->  build_findings()  ->  findings JSON
    findings JSON  ->  report_gen.generate_report()  ->  hisobot matni
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Optional

# BI-RADS kategoriyasi -> klinik tavsiya (o'zbekcha)
BIRADS_RECOMMENDATION = {
    "0": "Baho to'liq emas — qo'shimcha tasvirlash yoki oldingi tasvirlar bilan solishtirish kerak",
    "1": "Patologiya aniqlanmadi — rutin skrining (yiliga bir marta)",
    "2": "Benign (xavfsiz) topilma — rutin skrining",
    "3": "Ehtimol benign — 6 oydan keyin qisqa muddatli nazorat",
    "4": "Shubhali topilma — biopsiya tavsiya etiladi",
    "4A": "Past darajadagi shubha — biopsiya tavsiya etiladi",
    "4B": "O'rtacha shubha — biopsiya tavsiya etiladi",
    "4C": "Yuqori shubha — biopsiya tavsiya etiladi",
    "5": "Xavfli o'simta ehtimoli yuqori — biopsiya / jarrohlik konsultatsiyasi",
    "6": "Biopsiya bilan tasdiqlangan rak — davolash rejasi",
}

# Umumiy kategoriya uchun og'irlik tartibi (eng yuqorisini tanlash uchun)
_BIRADS_SEVERITY = {
    "0": 3, "1": 1, "2": 2, "3": 3,
    "4": 4, "4A": 4, "4B": 5, "4C": 6, "5": 7, "6": 8,
}

# Lezyon turlari (kalit -> o'zbekcha nom)
LESION_TYPES = {
    "mass": "massa",
    "calcification": "mikrokalsifikatsiya",
    "asymmetry": "asimmetriya",
    "architectural_distortion": "arxitektura buzilishi",
}

# ACR ko'krak zichligi izohlari
ACR_DENSITY = {
    "a": "deyarli butunlay yog' to'qimasi",
    "b": "tarqoq fibroglandulyar zichlik",
    "c": "heterogen zich (kichik o'choqlarni yashirishi mumkin)",
    "d": "o'ta zich (sezgirlik pasayadi)",
}

_QUADRANTS = {
    ("upper", "outer"): "yuqori-tashqi kvadrant (UOQ)",
    ("upper", "inner"): "yuqori-ichki kvadrant (UIQ)",
    ("lower", "outer"): "pastki-tashqi kvadrant (LOQ)",
    ("lower", "inner"): "pastki-ichki kvadrant (LIQ)",
}


def quadrant_from_bbox(cx: float, cy: float, laterality: str) -> str:
    """Quti markazidan (normallashtirilgan 0..1) taxminiy kvadrant.

    DIQQAT: bu taxminiy — proeksiya yo'nalishiga bog'liq. Annotatsiyada aniq
    kvadrant bo'lsa, o'shani ishlating (build_findings 'quadrant'ni afzal ko'radi).
    """
    vert = "upper" if cy < 0.5 else "lower"
    lat = (laterality or "").upper()
    # Tasvirda ko'krak yo'nalishi laterallikka bog'liq (taxminiy yondashuv)
    if lat.startswith("R"):
        horiz = "outer" if cx < 0.5 else "inner"
    else:
        horiz = "outer" if cx >= 0.5 else "inner"
    return _QUADRANTS[(vert, horiz)]


def aggregate_birads(birads_list: list) -> str:
    """Bir nechta lezyondan umumiy (eng yuqori og'irlikdagi) BI-RADS."""
    cats = [str(b) for b in birads_list if str(b)]
    if not cats:
        return "1"
    return max(cats, key=lambda b: _BIRADS_SEVERITY.get(b, 0))


@dataclass
class Lesion:
    laterality: str = ""             # "L" | "R"
    view: str = ""                   # "CC" | "MLO" | ""
    quadrant: str = ""               # UOQ/UIQ/LOQ/LIQ/retroareolyar
    type: str = "mass"               # mass|calcification|asymmetry|architectural_distortion
    size_mm: Optional[float] = None
    margin: str = ""                 # spikulali | aniq chegarali | noaniq | ...
    birads: str = "0"
    confidence: Optional[float] = None

    def to_dict(self) -> dict:
        return asdict(self)


def build_findings(
    detections: list,
    dicom_meta: Optional[dict] = None,
    study_views: Optional[list] = None,
) -> dict:
    """Detektor chiqishi + DICOM meta'dan strukturaviy findings JSON quradi.

    `detections` — har biri dict: laterality, view, quadrant (yoki cx/cy),
    type, size_mm, margin, birads, confidence.
    """
    dicom_meta = dicom_meta or {}
    lesions: list[Lesion] = []
    for d in detections:
        lat = d.get("laterality") or dicom_meta.get("laterality") or ""
        view = d.get("view") or dicom_meta.get("view") or ""
        quad = d.get("quadrant") or ""
        if not quad and ("cx" in d and "cy" in d) and lat:
            quad = quadrant_from_bbox(float(d["cx"]), float(d["cy"]), lat)
        lesions.append(Lesion(
            laterality=lat,
            view=view,
            quadrant=quad,
            type=d.get("type", "mass"),
            size_mm=(float(d["size_mm"]) if d.get("size_mm") is not None else None),
            margin=d.get("margin", ""),
            birads=str(d.get("birads", "0")),
            confidence=(float(d["confidence"]) if d.get("confidence") is not None else None),
        ))
    overall = aggregate_birads([l.birads for l in lesions])
    return {
        "study": {
            "views": study_views or [],
            "acr_density": dicom_meta.get("acr_density", ""),
        },
        "lesions": [l.to_dict() for l in lesions],
        "overall_birads": overall,
        "recommendation": BIRADS_RECOMMENDATION.get(overall, ""),
    }


def mock_findings() -> dict:
    """Detektorsiz sinash uchun namunaviy findings."""
    return build_findings(
        detections=[
            {"laterality": "L", "view": "MLO",
             "quadrant": "yuqori-tashqi kvadrant (UOQ)", "type": "mass",
             "size_mm": 14.0, "margin": "spikulali", "birads": "4B",
             "confidence": 0.82},
            {"laterality": "R", "view": "CC",
             "quadrant": "pastki-ichki kvadrant (LIQ)", "type": "calcification",
             "margin": "", "birads": "2", "confidence": 0.61},
        ],
        dicom_meta={"acr_density": "c"},
        study_views=["L-CC", "L-MLO", "R-CC", "R-MLO"],
    )
