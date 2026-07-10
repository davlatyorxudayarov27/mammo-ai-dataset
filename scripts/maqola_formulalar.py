# -*- coding: utf-8 -*-
"""maqola_formulalar.py — maqoladagi 13 ta tenglama, Word native OMML ko'rinishida.

Har bir funksiya `m:oMath` ichiga joylanadigan tugunlar ro'yxatini qaytaradi.
Metodologik manba: R.X. Xamdamov (2017), III bob — (3.2.2), (3.4.5), (3.6.2)–(3.6.4).
"""
from __future__ import annotations

from omml import acc, arg_op, delim, frac, nary, run, sub, subsup, sup

MINUS = "−"   # true minus
SUM = "∑"


def _sq(inner):
    """(...)² — qavs ichidagi ifodaning kvadrati."""
    return sup(delim(inner), "2")


# ---- (1) sinflararo tarqoqlik a_j ---------------------------------------- #
def eq_a():
    return [sub("a", "j"), run(" = "),
            nary(SUM, "l=1", sub("k", "p"),
                 nary(SUM, "t=1", sub("k", "q"),
                      _sq([sub("x", "plj"), run(f" {MINUS} "), sub("x", "qtj")])))]


# ---- (2) p-sinf ichidagi tarqoqlik b_j ----------------------------------- #
def eq_b():
    return [sub("b", "j"), run(" = "),
            nary(SUM, "l=1", sub("k", "p"),
                 nary(SUM, "t=1", sub("k", "p"),
                      _sq([sub("x", "plj"), run(f" {MINUS} "), sub("x", "ptj")])))]


# ---- (3) q-sinf ichidagi tarqoqlik c_j ----------------------------------- #
def eq_c():
    return [sub("c", "j"), run(" = "),
            nary(SUM, "l=1", sub("k", "q"),
                 nary(SUM, "t=1", sub("k", "q"),
                      _sq([sub("x", "qlj"), run(f" {MINUS} "), sub("x", "qtj")])))]


# ---- (4) Ф(λ) funksional — bulcha dasturlash masalasi --------------------- #
def eq_phi():
    return [run("Φ"), delim("λ"), run(" = "),
            frac([nary(SUM, "j=1", "n", [sub("a", "j"), sub("λ", "j")])],
                 [nary(SUM, "j=1", "n", [delim([sub("b", "j"), run(" + "), sub("c", "j")]),
                                         sub("λ", "j")])]),
            run(" → "), run("max", upright=True), run(", "),
            sub("λ", "j"), run(" ∈ "), run("{0, 1}", upright=True)]


# ---- (5) ranjirlash koeffitsienti r_j ------------------------------------ #
def eq_rank():
    return [sub("r", "j"), run(" = "),
            frac([sub("a", "j")], [sub("w", "j")]), run(", "),
            sub("w", "j"), run(" = "), sub("b", "j"), run(" + "), sub("c", "j")]


# ---- (6) informativ belgilar soni n'* ------------------------------------ #
def eq_nstar():
    return [run("n′*"), run(" = "),
            arg_op("argmax", [run("n′ ∈ "), run("{1, …, n}", upright=True)],
                   [run("P"), delim(run("n′"))])]


# ---- (7) sinf etaloni (markaz) ------------------------------------------- #
def eq_centroid():
    return [sup(acc("x"), "p"), run(" = "),
            frac([run("1")], [sub("k", "p")]),
            nary(SUM, "l=1", sub("k", "p"), sub("x", "pl"))]


# ---- (8) sinf ichki tarqoqligi S(X_p) ------------------------------------ #
def eq_scatter():
    return [run("S"), delim([sub("X", "p")]), run(" = "),
            frac([run("1")], [sub("k", "p")]),
            nary(SUM, "l=1", sub("k", "p"),
                 nary(SUM, "j=1", "n",
                      [sub("λ", "j"),
                       _sq([sub("x", "plj"), run(f" {MINUS} "),
                            subsup(acc("x"), "j", "p")])]))]


# ---- (9) normallashgan masofa ρ_p(x) ------------------------------------- #
def eq_rho():
    return [sub("ρ", "p"), delim("x"), run(" = "),
            frac([nary(SUM, "j=1", "n",
                       [sub("λ", "j"),
                        _sq([sub("x", "j"), run(f" {MINUS} "),
                             subsup(acc("x"), "j", "p")])])],
                 [run("S"), delim([sub("X", "p")])])]


# ---- (10) minimal masofa qoidasi ----------------------------------------- #
def eq_decision():
    return [run("class", upright=True), delim("x"), run(" = "),
            arg_op("argmin", [run("p ∈ "), run("{1, …, m}", upright=True)],
                   [sub("ρ", "p"), delim("x")])]


# ---- (11) softmax ishonch bahosi ----------------------------------------- #
def eq_softmax():
    return [sub("s", "p"), delim("x"), run(" = "),
            frac([run("exp", upright=True),
                  delim([run(MINUS), sub("ρ", "p"), delim("x")])],
                 [nary(SUM, "q=1", "m",
                       [run("exp", upright=True),
                        delim([run(MINUS), sub("ρ", "q"), delim("x")])])])]


# ---- (12) gibrid ansambl -------------------------------------------------- #
def eq_ensemble():
    return [sub("z", "p"), delim("x"), run(" = "),
            run("α · "), subsup("u", "p", "YOLO"), delim("x"),
            run(" + "), delim([run("1"), run(f" {MINUS} "), run("α")]),
            run(" · "), sub("s", "p"), delim("x"), run(", "),
            run("α"), run(" ∈ "), run("[0, 1]", upright=True)]


# ---- (13) ishonchlilik mezoni P ------------------------------------------ #
def eq_P():
    return [run("P"), run(" = "),
            frac([run("1")], [run("N")]),
            nary(SUM, "i=1", "N",
                 [run("I", upright=True),
                  delim([run("class", upright=True), delim([sub("x", "i")]),
                         run(" = "), sub("y", "i")], beg="[", end="]")])]


ALL = [eq_a, eq_b, eq_c, eq_phi, eq_rank, eq_nstar, eq_centroid,
       eq_scatter, eq_rho, eq_decision, eq_softmax, eq_ensemble, eq_P]
