# -*- coding: utf-8 -*-
"""Radiomika benign/malignant klassifikatorini OFFLINE o'qitish.

Yorliqlar PATOLOGIYA (biopsiya) bilan tasdiqlangan bo'lishi kerak. Ularni CSV
orqali beriladi:

    labels CSV ustunlari (sarlavha bilan, katta-kichik harf farqsiz):
        ref            -> fayl id (app/uploads/<ref>.dcm)
        annotation_id  -> (ixtiyoriy) aniq annotatsiya id; bo'sh bo'lsa shu
                          ref'dagi barcha massa annotatsiyalariga tegishli
        outcome        -> benign | malignant | 0 | 1 | b | m

Misol:
    ref,annotation_id,outcome
    18cf5a48...,,malignant
    9b2443dd...,a1b2c3,benign

Ishga tushirish:
    .venv\\Scripts\\python.exe scripts\\train_radiomics_clf.py ^
        --labels app\\research\\malignancy_labels.csv --model logreg

Natija: app/models/radiomics_clf.joblib + metrikalar (cross-val AUC/aniqlik).
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import radiomics as rad           # noqa: E402
from app import radiomics_clf as clf        # noqa: E402
from app.dicom_utils import load_frame_array  # noqa: E402

ANNOT_DIR = ROOT / "app" / "annotations"
UPLOAD_DIR = ROOT / "app" / "uploads"

# "faqat usmaga" — massa turidagi annotatsiyalar
MASS_LABELS = {"mass", "massa", "usma", "o'simta", "tumor", "birads12"}


def _norm_outcome(v: str):
    v = (v or "").strip().lower()
    if v in ("1", "m", "malignant", "xavfli", "zlokachestvennyy", "rak"):
        return 1
    if v in ("0", "b", "benign", "xavfsiz", "dobrokachestvennyy"):
        return 0
    return None


def load_labels(path: Path) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fields = {(k or "").strip().lower(): k for k in (reader.fieldnames or [])}
        ref_c = fields.get("ref") or fields.get("file") or fields.get("id")
        ann_c = fields.get("annotation_id") or fields.get("ann_id") or fields.get("annotation")
        out_c = (fields.get("outcome") or fields.get("malignancy")
                 or fields.get("label") or fields.get("class"))
        if not ref_c or not out_c:
            raise SystemExit("CSV'da 'ref' va 'outcome' ustunlari bo'lishi shart.")
        for r in reader:
            y = _norm_outcome(r.get(out_c))
            if y is None:
                continue
            rows.append({
                "ref": (r.get(ref_c) or "").strip(),
                "ann_id": (r.get(ann_c) or "").strip() if ann_c else "",
                "y": y,
            })
    return rows


def outcome_for(ann_id: str, ref: str, labels: list[dict]):
    """Annotatsiya uchun yorliq: avval aniq annotation_id, keyin ref bo'yicha."""
    exact = [l for l in labels if l["ref"] == ref and l["ann_id"] == ann_id]
    if exact:
        return exact[0]["y"]
    generic = [l for l in labels if l["ref"] == ref and not l["ann_id"]]
    if generic:
        return generic[0]["y"]
    return None


def is_mass(a: dict) -> bool:
    lbls = [str(a.get("label") or "").lower()]
    for x in (a.get("labels") or []):
        lbls.append(str(x).lower())
    return any(l in MASS_LABELS for l in lbls)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--labels", required=True, help="patologiya yorliqlari CSV")
    ap.add_argument("--model", default="logreg", choices=["logreg", "rf", "gb"])
    ap.add_argument("--bins", type=int, default=32)
    ap.add_argument("--no-birads", action="store_true", help="BI-RADS belgisini ishlatmaslik")
    ap.add_argument("--all-types", action="store_true", help="faqat massa emas, barcha turlar")
    args = ap.parse_args()

    labels = load_labels(Path(args.labels))
    if not labels:
        raise SystemExit("CSV'da yaroqli yorliq topilmadi.")
    use_birads = not args.no_birads

    feature_names = None
    rows: list[list[float]] = []
    ys: list[int] = []
    skipped = 0

    for jf in sorted(ANNOT_DIR.glob("upload__*.json")):
        try:
            data = json.loads(jf.read_text(encoding="utf-8"))
        except Exception:
            continue
        ref = data.get("ref") or jf.stem.replace("upload__", "")
        dcm = UPLOAD_DIR / f"{ref}.dcm"
        if not dcm.exists():
            continue
        anns = data.get("annotations") or []
        frame_cache: dict = {}
        for a in anns:
            if a.get("status") == "rejected":
                continue
            if not args.all_types and not is_mass(a):
                continue
            y = outcome_for(a.get("id") or "", ref, labels)
            if y is None:
                continue
            frame = int(a.get("frame") or 0)
            if frame not in frame_cache:
                try:
                    frame_cache[frame] = load_frame_array(dcm, frame=frame)
                except Exception:
                    frame_cache[frame] = None
            if frame_cache[frame] is None:
                skipped += 1
                continue
            image, spacing = frame_cache[frame]
            rws, cls = image.shape[:2]
            mask = rad.roi_mask_from_annotation(a, rws, cls)
            if not mask.any():
                skipped += 1
                continue
            try:
                feat = rad.extract(image, mask, spacing=spacing, bins=args.bins)
            except Exception:
                skipped += 1
                continue
            names, vals = clf.build_feature_row(feat, a.get("bi_rads"), use_birads)
            if feature_names is None:
                feature_names = names
            if names != feature_names:
                # tartibni moslashtirib qo'yamiz
                by = dict(zip(names, vals))
                vals = [by.get(n, float("nan")) for n in feature_names]
            rows.append(vals)
            ys.append(y)

    n = len(ys)
    print(f"Namunalar: {n} (malignant={sum(ys)}, benign={n - sum(ys)}) | o'tkazib yuborildi: {skipped}")
    if n == 0:
        raise SystemExit("O'qitish uchun namuna topilmadi — CSV ref/annotation_id'lar mosligini tekshiring.")

    pipe, metrics = clf.train(feature_names, rows, ys,
                              use_birads=use_birads, model_type=args.model)
    clf.save_model(pipe, feature_names, use_birads, metrics, args.model)
    print("MODEL SAQLANDI:", clf.MODEL_PATH)
    print("Metrikalar:", json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
