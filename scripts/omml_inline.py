# -*- coding: utf-8 -*-
"""omml_inline.py — satr ichidagi LaTeX ($...$) ni Word native OMML tenglamaga o'giradi.

Dissertatsiya matnida `$\\alpha$`, `$F_v^{(s)}$` kabi bo'laklar xom LaTeX ko'rinishida
chiqib qolgan edi (para() satr-ichi matematikani render qilmaydi). Bu modul ularni
`m:oMath` inline obyektlariga aylantiradi — Word'da tahrirlanadigan, MathType-mos.

Qo'llab-quvvatlanadi: yunon harflari, _ va ^ (indekslar), {guruh}, \\text/\\mathrm/\\texttt
(tik), \\mathbf (qalin tik), \\mathbb{R} → ℝ, \\bar{x} → x̄, \\times \\dots \\in \\leq \\geq,
\\{ \\} qavslar, oddiy harf/son/operatorlar.
"""
from __future__ import annotations

import re

from docx.oxml import OxmlElement
from docx.oxml.ns import qn

# ------------------------------------------------------------ belgilar --- #
SYMBOLS = {
    "alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ", "Delta": "Δ",
    "epsilon": "ε", "varepsilon": "ε", "zeta": "ζ", "eta": "η", "theta": "θ",
    "Theta": "Θ", "iota": "ι", "kappa": "κ", "lambda": "λ", "Lambda": "Λ",
    "mu": "μ", "nu": "ν", "xi": "ξ", "pi": "π", "Pi": "Π", "rho": "ρ",
    "sigma": "σ", "Sigma": "Σ", "tau": "τ", "phi": "φ", "Phi": "Φ",
    "chi": "χ", "psi": "ψ", "omega": "ω", "Omega": "Ω",
    "times": "×", "cdot": "·", "dots": "…", "ldots": "…", "cdots": "⋯",
    "in": "∈", "notin": "∉", "leq": "≤", "le": "≤", "geq": "≥", "ge": "≥",
    "neq": "≠", "approx": "≈", "sim": "∼", "propto": "∝", "infty": "∞",
    "rightarrow": "→", "to": "→", "leftarrow": "←", "Rightarrow": "⇒",
    "subset": "⊂", "subseteq": "⊆", "cup": "∪", "cap": "∩",
    "forall": "∀", "exists": "∃", "partial": "∂", "nabla": "∇",
    "pm": "±", "mp": "∓", "circ": "∘", "star": "⋆", "oplus": "⊕", "odot": "⊙",
    "quad": " ", "qquad": "  ", ",": " ", ";": " ", "!": "",
}
BLACKBOARD = {"R": "ℝ", "N": "ℕ", "Z": "ℤ", "Q": "ℚ", "C": "ℂ"}
UPRIGHT_CMDS = {"text", "mathrm", "texttt", "operatorname", "mathsf"}


def _el(tag, *children, **attrs):
    e = OxmlElement(tag)
    for k, v in attrs.items():
        e.set(qn(k.replace("__", ":")), v)
    for c in children:
        if c is not None:
            e.append(c)
    return e


def _run(text, sty=None):
    kids = []
    if sty:
        kids.append(_el("m:rPr", _el("m:sty", **{"m__val": sty})))
    t = _el("m:t")
    t.set(qn("xml:space"), "preserve")
    t.text = text
    kids.append(t)
    return _el("m:r", *kids)


def _e(nodes):
    return _el("m:e", *nodes)


def _ssub(base, sub):
    return _el("m:sSub", _e(base), _el("m:sub", *sub))


def _ssup(base, sup):
    return _el("m:sSup", _e(base), _el("m:sup", *sup))


def _ssubsup(base, sub, sup):
    return _el("m:sSubSup", _e(base), _el("m:sub", *sub), _el("m:sup", *sup))


def _acc(base):
    return _el("m:acc", _el("m:accPr", _el("m:chr", **{"m__val": "̄"}), _el("m:ctrlPr")),
               _e(base))


# ------------------------------------------------------------ tokenizer --- #
_TOKEN = re.compile(r"""
    (?P<cmd>\\[a-zA-Z]+)          |
    (?P<esc>\\[{}\\_^&%\#$,;!])   |
    (?P<open>\{)                  |
    (?P<close>\})                 |
    (?P<sub>_)                    |
    (?P<sup>\^)                   |
    (?P<space>\s+)                |
    (?P<ch>.)
""", re.VERBOSE)


def _tokens(s):
    for m in _TOKEN.finditer(s):
        yield m.lastgroup, m.group()


def _plain_runs(text):
    """Harflar — kursiv (standart), son/operator — tik."""
    out, buf, buf_is_alpha = [], "", None
    for ch in text:
        is_alpha = ch.isalpha()
        if buf and is_alpha != buf_is_alpha:
            out.append(_run(buf) if buf_is_alpha else _run(buf, sty="p"))
            buf = ""
        buf += ch
        buf_is_alpha = is_alpha
    if buf:
        out.append(_run(buf) if buf_is_alpha else _run(buf, sty="p"))
    return out


def _parse(tokens, stop_at_close=False):
    """Tokenlardan OMML tugunlari ro'yxatini quradi."""
    nodes = []
    pending_text = ""

    def flush():
        nonlocal pending_text
        if pending_text:
            nodes.extend(_plain_runs(pending_text))
            pending_text = ""

    while True:
        try:
            kind, tok = next(tokens)
        except StopIteration:
            break
        if kind == "close":
            if stop_at_close:
                break
            pending_text += "}"
        elif kind == "open":
            flush()
            nodes.extend(_parse(tokens, stop_at_close=True))
        elif kind == "esc":
            pending_text += " " if tok[1] in ",;!" else tok[1]
        elif kind == "space":
            pending_text += " "
        elif kind == "sub" or kind == "sup":
            flush()
            if not nodes:
                nodes.append(_run(""))
            base = [nodes.pop()]
            arg = _parse_atom(tokens)
            if nodes and False:
                pass
            # ketma-ket _ va ^ (yoki ^ va _) → sSubSup
            nxt_kind, nxt_tok = _peek(tokens)
            if nxt_kind in ("sub", "sup") and nxt_kind != kind:
                next(tokens)
                arg2 = _parse_atom(tokens)
                if kind == "sub":
                    nodes.append(_ssubsup(base, arg, arg2))
                else:
                    nodes.append(_ssubsup(base, arg2, arg))
            else:
                nodes.append(_ssub(base, arg) if kind == "sub" else _ssup(base, arg))
        elif kind == "cmd":
            name = tok[1:]
            if name in UPRIGHT_CMDS:
                flush()
                inner = _raw_group(tokens)
                nodes.append(_run(inner, sty="p"))
            elif name == "mathbf":
                flush()
                nodes.append(_run(_raw_group(tokens), sty="b"))
            elif name == "mathbb":
                flush()
                g = _raw_group(tokens)
                pending_text += BLACKBOARD.get(g, g)
            elif name in ("bar", "overline"):
                flush()
                nodes.append(_acc(_parse_atom(tokens)))
            elif name in SYMBOLS:
                pending_text += SYMBOLS[name]
            else:
                pending_text += name          # noma'lum buyruq — nomini yozamiz
        else:
            pending_text += tok
    flush()
    return nodes


class _Peekable:
    def __init__(self, it):
        self._it = it
        self._buf = []

    def __next__(self):
        if self._buf:
            return self._buf.pop(0)
        return next(self._it)

    def peek(self):
        if not self._buf:
            try:
                self._buf.append(next(self._it))
            except StopIteration:
                return (None, None)
        return self._buf[0]


def _peek(tokens):
    return tokens.peek() if isinstance(tokens, _Peekable) else (None, None)


def _parse_atom(tokens):
    """_ yoki ^ dan keyingi bitta atom: {guruh} yoki bitta belgi/buyruq."""
    kind, tok = next(tokens)
    if kind == "open":
        return _parse(tokens, stop_at_close=True)
    if kind == "cmd":
        name = tok[1:]
        if name in SYMBOLS:
            return _plain_runs(SYMBOLS[name])
        if name in UPRIGHT_CMDS:
            return [_run(_raw_group(tokens), sty="p")]
        return _plain_runs(name)
    return _plain_runs(tok)


def _raw_group(tokens):
    """{...} ichidagi xom matn (ichki buyruqlar soddalashtiriladi)."""
    kind, tok = next(tokens)
    if kind != "open":
        return tok
    depth, out = 1, ""
    while True:
        try:
            kind, tok = next(tokens)
        except StopIteration:
            break
        if kind == "open":
            depth += 1
        elif kind == "close":
            depth -= 1
            if depth == 0:
                break
        if kind == "cmd":
            out += SYMBOLS.get(tok[1:], tok[1:])
        elif kind == "esc":
            out += tok[1]
        else:
            out += tok
    return out


def latex_to_omath(latex: str):
    """`m:oMath` elementini qaytaradi (paragrafga to'g'ridan qo'shiladi)."""
    nodes = _parse(_Peekable(_tokens(latex)))
    return _el("m:oMath", *nodes)


# --------------------------------------------------------------- public --- #
_MATH = re.compile(r"\$([^$]+)\$")


def has_math(text: str) -> bool:
    return bool(_MATH.search(text))


def emit_rich(p, text, *, size=None, bold_all=False, italic=False, color=None):
    """Paragrafga matn qo'shadi: `$...$` — inline OMML, `**...**` — qalin.

    p — python-docx Paragraph. Qaytadi: p.
    """
    parts = _MATH.split(text)          # [matn, math, matn, math, ...]
    bold_state = False
    for i, seg in enumerate(parts):
        if i % 2 == 1:                 # matematik bo'lak
            p._p.append(latex_to_omath(seg))
            continue
        for j, chunk in enumerate(seg.split("**")):
            if j > 0:
                bold_state = not bold_state
            if not chunk:
                continue
            r = p.add_run(chunk)
            r.bold = bold_all or bold_state
            r.italic = italic
            if size is not None:
                r.font.size = size
            if color is not None:
                r.font.color.rgb = color
    return p
