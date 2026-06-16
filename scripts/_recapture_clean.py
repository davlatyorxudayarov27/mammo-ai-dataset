# -*- coding: utf-8 -*-
"""Viewer skrinshotini PHI'siz qayta olish.

Haqiqiy bemor fayllari (MG) vaqtincha chetga olinadi, faqat de-identifikatsiya
qilingan demo (US/ANON) bilan surat olinadi, so'ng haqiqiy fayllar QAYTARILADI.
Hech qanday haqiqiy fayl o'chirilmaydi.
"""
from __future__ import annotations

import glob
import os
import shutil
from pathlib import Path

import pydicom

UP = Path("app/uploads")
BAK = Path("app/_phi_bak")
BAK.mkdir(exist_ok=True)


def is_demo(f: str) -> bool:
    ds = pydicom.dcmread(f, stop_before_pixels=True, force=True)
    return (str(getattr(ds, "Modality", "")) == "US"
            and str(getattr(ds, "PatientID", "")) == "ANON")


moved = []
try:
    for f in glob.glob(str(UP / "*.dcm")):
        if not is_demo(f):                       # haqiqiy bemor fayli
            dst = BAK / Path(f).name
            shutil.move(f, str(dst))
            moved.append(dst)
    print("vaqtincha chetga olindi (haqiqiy):", len(moved))

    from scripts.make_screenshots import run
    run()
finally:
    # demo (US/ANON) fayllarni tozalash
    for f in glob.glob(str(UP / "*.dcm")):
        try:
            if is_demo(f):
                os.remove(f)
        except Exception as e:
            print("demo del err:", e)
    # haqiqiy fayllarni qaytarish
    for d in moved:
        shutil.move(str(d), str(UP / d.name))
    try:
        BAK.rmdir()
    except Exception:
        pass
    print("qaytarildi (haqiqiy):", len(moved))
    print("hozir uploads'da:", len(glob.glob(str(UP / "*.dcm"))), "fayl")
