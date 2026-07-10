# -*- coding: utf-8 -*-
"""omml.py — Word native (OMML) tenglama qurish yordamchilari.

LaTeX→PNG rasm O'RNIGA to'g'ridan-to'g'ri `m:oMath` XML quriladi. Natija —
Word'da tahrirlanadigan, MathType bilan mos keluvchi haqiqiy tenglama obyektlari
(rasm emas). Namespace: m = officeDocument/2006/math (python-docx nsmap'ida bor).
"""
from __future__ import annotations

from docx.oxml import OxmlElement
from docx.oxml.ns import qn


def _e(tag, *children, **attrs):
    el = OxmlElement(tag)
    for k, v in attrs.items():
        el.set(qn(k.replace("__", ":")), v)
    for c in children:
        if c is not None:
            el.append(c)
    return el


def run(text, upright=False):
    """m:r — matn tuguni. upright=True → funksiya nomi/son (tik), aks holda kursiv."""
    children = []
    if upright:
        children.append(_e("m:rPr", _e("m:sty", **{"m__val": "p"})))
    t = _e("m:t")
    t.set(qn("xml:space"), "preserve")
    t.text = text
    children.append(t)
    return _e("m:r", *children)


def _seq(items):
    """str yoki element ro'yxatini elementlar ro'yxatiga aylantiradi."""
    out = []
    for it in items if isinstance(items, (list, tuple)) else [items]:
        out.append(run(it) if isinstance(it, str) else it)
    return out


def _E(items):
    return _e("m:e", *_seq(items))


def frac(num, den):
    return _e("m:f", _e("m:fPr", _e("m:ctrlPr")),
              _e("m:num", *_seq(num)), _e("m:den", *_seq(den)))


def sub(base, s):
    return _e("m:sSub", _E(base), _e("m:sub", *_seq(s)))


def sup(base, s):
    return _e("m:sSup", _E(base), _e("m:sup", *_seq(s)))


def subsup(base, sb, sp):
    return _e("m:sSubSup", _E(base), _e("m:sub", *_seq(sb)), _e("m:sup", *_seq(sp)))


def delim(inner, beg="(", end=")"):
    return _e("m:d", _e("m:dPr", _e("m:begChr", **{"m__val": beg}),
                        _e("m:endChr", **{"m__val": end}), _e("m:ctrlPr")),
              _E(inner))


def _has(x):
    """lxml elementini truth-test qilmaslik uchun (FutureWarning)."""
    if x is None:
        return False
    if isinstance(x, (list, tuple)):
        return len(x) > 0
    if isinstance(x, str):
        return len(x) > 0
    return True


def nary(chr_, sub_, sup_, body, lim_loc="undOvr"):
    """N-ary (∑, ∏, ∫ ...) — limitlar chr belgisi ostida/ustida."""
    hs, hp = _has(sub_), _has(sup_)
    pr = _e("m:naryPr", _e("m:chr", **{"m__val": chr_}),
            _e("m:limLoc", **{"m__val": lim_loc}),
            _e("m:subHide", **{"m__val": "0" if hs else "1"}),
            _e("m:supHide", **{"m__val": "0" if hp else "1"}),
            _e("m:ctrlPr"))
    return _e("m:nary", pr,
              _e("m:sub", *_seq(sub_)) if hs else _e("m:sub"),
              _e("m:sup", *_seq(sup_)) if hp else _e("m:sup"), _E(body))


def acc(base, chr_="̄"):
    """Aksent (masalan x̄ — chr U+0304 = combining overline)."""
    return _e("m:acc", _e("m:accPr", _e("m:chr", **{"m__val": chr_}), _e("m:ctrlPr")),
              _E(base))


def limlow(base, lim):
    """Ostki limit: base ning tagida lim (argmin_p ko'rinishi uchun)."""
    return _e("m:limLow", _e("m:limLowPr", _e("m:ctrlPr")),
              _E(base), _e("m:lim", *_seq(lim)))


def func(name, arg):
    """funktsiya: nom (tik) + argument."""
    fname = name if not isinstance(name, str) else run(name, upright=True)
    return _e("m:func", _e("m:funcPr", _e("m:ctrlPr")),
              _e("m:fName", fname), _E(arg))


def arg_op(op, under, body):
    """argmin/argmax kabi operator: nomi tik, limiti ostida, so'ng argument."""
    return func(limlow(run(op, upright=True), under), body)


def add_equation(doc, *nodes, number=None):
    """Markazlashtirilgan tenglama paragrafi. number berilsa o'ngda (n) qo'yiladi."""
    from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    omath = _e("m:oMath", *nodes)
    p._p.append(omath)
    if number:
        from docx.shared import Cm
        pf = p.paragraph_format
        pf.tab_stops.add_tab_stop(Cm(16.5), WD_TAB_ALIGNMENT.RIGHT)
        r = p.add_run("\t(" + str(number) + ")")
        r.font.name = "Times New Roman"
    return p
