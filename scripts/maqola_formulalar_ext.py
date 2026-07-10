# -*- coding: utf-8 -*-
"""maqola_formulalar_ext.py — 2026-yilgi ikki maqola uchun QO'SHIMCHA OMML tenglamalari.

Barqarorlik indekslari (Kuncheva, Jaccard, o'rtacha o'rin), ansambl vaznini tanlash,
va baholash metrikalarining rasmiy ta'riflari. Barchasi Word-native (m:oMath) —
rasm emas, MathType bilan mos.
"""
from __future__ import annotations

from omml import (absv, acc, arg_op, delim, frac, func, nary, rad, run, sub,
                  subsup, sup)

# ─────────────────────────── umumiy bo'laklar ──────────────────────────── #


def _pairsum(body):
    """Σ_{i<j} body — juftliklar bo'yicha yig'indi (tanasi ichida)."""
    return nary("∑", [run("i"), run("<", upright=True), run("j")], None, body)


def _binom_pairs():
    """2 / (B(B−1))"""
    return frac(run("2", upright=True),
                [run("B"), delim([run("B"), run("−"), run("1", upright=True)])])


# ═══════════════════ 1-MAQOLA: barqarorlik metrikalari ═══════════════════ #


def eq_subset():
    """S_b = { j : π_b(j) ≤ n′ } — b-bootstrap namunadagi tanlangan to'plam."""
    return [sub(run("S"), run("b")), run(" = ", upright=True),
            delim([run("j"), run(" : ", upright=True),
                   sub(run("π"), run("b")), delim(run("j")),
                   run(" ≤ ", upright=True), sup(run("n"), run("′"))],
                  "{", "}")]


def eq_kuncheva():
    """Kuncheva (2007) tasodifga tuzatilgan barqarorlik indeksi."""
    n2 = frac(sup(run("n"), run("′2")), run("N"))
    r = frac([absv([sub(run("S"), run("i")), run("∩"), sub(run("S"), run("j"))]),
              run(" − ", upright=True), n2],
             [sup(run("n"), run("′")), run(" − ", upright=True),
              frac(sup(run("n"), run("′2")), run("N"))])
    return [sub(run("I"), run("C", upright=True)), run(" = ", upright=True),
            _binom_pairs(), _pairsum(r)]


def eq_jaccard():
    """Juftlik-o'rtacha Jaccard o'xshashligi."""
    return [run("J"), run(" = ", upright=True), _binom_pairs(),
            _pairsum(frac(absv([sub(run("S"), run("i")), run("∩"), sub(run("S"), run("j"))]),
                          absv([sub(run("S"), run("i")), run("∪"), sub(run("S"), run("j"))])))]


def eq_meanrank():
    """Belgining o'rtacha o'rni va o'rin bo'yicha standart chetlanishi."""
    mean = [acc(sub(run("r"), run("j"))), run(" = ", upright=True),
            frac(run("1", upright=True), run("B")),
            nary("∑", [run("b"), run(" = ", upright=True), run("1", upright=True)],
                 run("B"), [sub(run("π"), run("b")), delim(run("j"))])]
    std = [run(",  ", upright=True), sub(run("σ"), run("j")), run(" = ", upright=True),
           rad([frac(run("1", upright=True), run("B")),
                nary("∑", run("b"), None,
                     sup(delim([sub(run("π"), run("b")), delim(run("j")),
                                run(" − ", upright=True),
                                acc(sub(run("r"), run("j")))]), run("2", upright=True)))])]
    return mean + std


def eq_agreement():
    """Ikki bazadagi top-n′ to'plamlarining kesishuv ulushi."""
    return [sub(run("A"), [run("s"), run(","), run("l")]), run(" = ", upright=True),
            frac(absv([sup(sub(run("S"), run("s")), run("*")), run("∩"),
                       sup(sub(run("S"), run("l")), run("*"))]),
                 sup(run("n"), run("′")))]


# ═════════════ 2-MAQOLA: ansambl va baholash metrikalari ═════════════════ #


def eq_yolo_vec():
    """Detektor ishonchidan yumshatilgan ehtimollik vektori."""
    frac_rest = frac([run("1", upright=True), run(" − ", upright=True),
                      sub(run("c"), run("p"))],
                     [run("m"), run(" − ", upright=True), run("1", upright=True)])
    return [sup(sub(run("u"), [run("p"), run("k")]), run("YOLO", upright=True)),
            run(" = ", upright=True),
            delim([sub(run("c"), run("p")), run(",  k = ", upright=True),
                   sub(run("ĉ"), run("p")), run(";   ", upright=True),
                   frac_rest, run(",  k ≠ ", upright=True), sub(run("ĉ"), run("p"))],
                  "{", "")]


def eq_alpha_star():
    """α* FAQAT train to'plamda muvozanatli aniqlik bo'yicha tanlanadi."""
    grid = [run("α"), run(" ∈ ", upright=True),
            delim([run("0", upright=True), run(", 0.05, …, 1", upright=True)], "{", "}")]
    return [sup(run("α"), run("*")), run(" = ", upright=True),
            arg_op("argmax", grid,
                   [sub(run("BAcc"), run("train", upright=True)),
                    delim([run("α"), run(";  "), sup(run("D"), run("train", upright=True))])])]


def eq_bacc():
    """Muvozanatli aniqlik = makro sezgirlik."""
    return [run("BAcc", upright=True), run(" = ", upright=True),
            frac(run("1", upright=True), run("m")),
            nary("∑", [run("k"), run(" = ", upright=True), run("1", upright=True)],
                 run("m"),
                 frac(sub(run("TP", upright=True), run("k")),
                      [sub(run("TP", upright=True), run("k")), run(" + ", upright=True),
                       sub(run("FN", upright=True), run("k"))]))]


def eq_spec():
    """Makro o'ziga xoslik (specificity)."""
    return [run("Spec", upright=True), run(" = ", upright=True),
            frac(run("1", upright=True), run("m")),
            nary("∑", [run("k"), run(" = ", upright=True), run("1", upright=True)],
                 run("m"),
                 frac(sub(run("TN", upright=True), run("k")),
                      [sub(run("TN", upright=True), run("k")), run(" + ", upright=True),
                       sub(run("FP", upright=True), run("k"))]))]


def eq_mcc():
    """Ko'p sinfli Metyus korrelyatsiya koeffitsienti."""
    num = [run("c"), run("·", upright=True), run("s"), run(" − ", upright=True),
           nary("∑", run("k"), None,
                [sub(run("t"), run("k")), sub(run("p"), run("k"))])]
    den = rad([delim([sup(run("s"), run("2", upright=True)), run(" − ", upright=True),
                      nary("∑", run("k"), None,
                           sup(sub(run("p"), run("k")), run("2", upright=True)))]),
               delim([sup(run("s"), run("2", upright=True)), run(" − ", upright=True),
                      nary("∑", run("k"), None,
                           sup(sub(run("t"), run("k")), run("2", upright=True)))])])
    return [run("MCC", upright=True), run(" = ", upright=True), frac(num, den)]


def eq_kappa():
    """Koen kappasi."""
    return [run("κ"), run(" = ", upright=True),
            frac([sub(run("p"), run("o", upright=True)), run(" − ", upright=True),
                  sub(run("p"), run("e", upright=True))],
                 [run("1", upright=True), run(" − ", upright=True),
                  sub(run("p"), run("e", upright=True))])]


def eq_auc_ovr():
    """Makro «bittasi-qolganlarga qarshi» ROC-AUC."""
    return [sub(run("AUC", upright=True), run("macro", upright=True)),
            run(" = ", upright=True),
            frac(run("1", upright=True), run("m")),
            nary("∑", [run("k"), run(" = ", upright=True), run("1", upright=True)],
                 run("m"), [run("AUC", upright=True), delim([run("k"), run(" vs. rest", upright=True)])])]


def eq_bootstrap_ci():
    """Persentil bootstrap ishonch oralig'i."""
    return [sub(run("CI", upright=True), run("95%", upright=True)),
            run(" = ", upright=True),
            delim([sub(run("q"), [run("2.5", upright=True), run("%")]),
                   delim([sup(run("M"), run("(1)")), run(", …, ", upright=True),
                          sup(run("M"), run("(B)"))], "{", "}"),
                   run(",  ", upright=True),
                   sub(run("q"), [run("97.5", upright=True), run("%")]),
                   delim([sup(run("M"), run("(1)")), run(", …, ", upright=True),
                          sup(run("M"), run("(B)"))], "{", "}")], "[", "]")]


def eq_delta():
    """Juftlashgan bootstrap farqi va ikki tomonlama p-qiymat."""
    d = [run("Δ"), run(" = ", upright=True),
         run("M", upright=True), delim(run("E")), run(" − ", upright=True),
         run("M", upright=True), delim(run("Y"))]
    p = [run(",   p = 2 · min", upright=True),
         delim([frac([run("#"), delim([sup(run("Δ"), run("(b)")),
                                       run(" ≤ 0", upright=True)])], run("B")),
                run(",  ", upright=True),
                frac([run("#"), delim([sup(run("Δ"), run("(b)")),
                                       run(" ≥ 0", upright=True)])], run("B"))])]
    return d + p


def eq_iou():
    """Detektsiya–GT moslashuvi mezoni."""
    return [run("IoU", upright=True),
            delim([run("B"), run(", ", upright=True), run("G")]),
            run(" = ", upright=True),
            frac(absv([run("B"), run("∩"), run("G")]),
                 absv([run("B"), run("∪"), run("G")])),
            run(" ≥ 0.3", upright=True)]


def eq_leak():
    """Ma'lumot sizishidan tozalangan baholash to'plami."""
    return [sup(sub(run("D"), run("val", upright=True)), run("toza")),
            run(" = ", upright=True),
            delim([run("x"), run(" ∈ ", upright=True),
                   sub(run("D"), run("val", upright=True)), run(" : ", upright=True),
                   run("x"), run(" ∉ ", upright=True),
                   sub(run("D"), [run("train", upright=True), run(","), run("eski")])],
                  "{", "}")]
