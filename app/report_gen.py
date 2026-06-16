"""Strukturaviy 'findings' -> mammografiya hisoboti.

Ikki yo'l:
  1) render_template_report  — deterministik shablon (LLMsiz, doim ishonchli).
  2) draft_llm_report        — Claude (claude-opus-4-8) tabiiy QORALAMA yozadi,
                               FAQAT berilgan topilmalardan (to'qib chiqarmaydi).

generate_report(mode="auto") — LLM mavjud bo'lsa undan, aks holda shablondan
foydalanadi. Har qanday holatda chiqish radiolog tasdig'i uchun QORALAMA.

Eslatma: LLM yo'li uchun `pip install anthropic` va ANTHROPIC_API_KEY kerak.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Optional

from . import report_findings as rf

# Bulutli (Anthropic) model — faqat ANTHROPIC_API_KEY bo'lsa
REPORT_MODEL = "claude-opus-4-8"

# Lokal model (Ollama) — kalitsiz, o'z tizimingizda. O'rnatilmagan bo'lsa
# avtomatik shablonga tushadi.
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:3b")

_LANG_NAME = {"uz": "o'zbek", "tr": "turk", "en": "ingliz", "ru": "rus"}


def render_template_report(findings: dict, lang: str = "uz") -> dict:
    """Findings JSON'dan deterministik BI-RADS strukturaviy hisobot (LLMsiz)."""
    lesions = findings.get("lesions", [])
    study = findings.get("study", {})

    if not lesions:
        findings_txt = "Ikkala ko'krakda patologik o'choq aniqlanmadi."
    else:
        parts = []
        for i, l in enumerate(lesions, 1):
            lat = (l.get("laterality") or "").upper()
            side = "Chap" if lat.startswith("L") else ("O'ng" if lat.startswith("R") else (lat or "—"))
            t = rf.LESION_TYPES.get(l.get("type", ""), l.get("type", ""))
            seg = f"{i}. {side} ko'krak"
            if l.get("view"):
                seg += f" ({l['view']})"
            if l.get("quadrant"):
                seg += f", {l['quadrant']}"
            seg += f": {t}"
            if l.get("size_mm"):
                seg += f", ~{float(l['size_mm']):.0f} mm"
            if l.get("margin"):
                seg += f", {l['margin']} chegarali"
            seg += f" — BI-RADS {l.get('birads', '?')}"
            parts.append(seg)
        findings_txt = "\n".join(parts)

    density = (study.get("acr_density") or "").lower()
    density_txt = rf.ACR_DENSITY.get(density, "")
    overall = findings.get("overall_birads", "")
    rec = findings.get("recommendation", "")

    views = study.get("views") or []
    blocks = ["MAMMOGRAFIYA XULOSASI (qoralama)"]
    intro = "Tekshiruv: raqamli mammografiya"
    if views:
        intro += f" (proeksiyalar: {', '.join(views)})"
    blocks.append(intro + ".")
    if density:
        dl = f"Ko'krak to'qimasi zichligi: ACR {density.upper()}"
        if density_txt:
            dl += f" — {density_txt}"
        blocks.append(dl + ".")
    blocks.append(f"Topilmalar:\n{findings_txt}")
    # Xulosa jumlasi
    if lesions:
        concl = (f"Xulosa: jami {len(lesions)} ta o'choq aniqlandi; "
                 f"eng yuqori baho BI-RADS {overall}.")
    else:
        concl = "Xulosa: shubhali o'choq aniqlanmadi."
    blocks.append(concl)
    blocks.append(f"Umumiy baho: BI-RADS {overall}\nTavsiya: {rec}")
    report = "\n\n".join(blocks) + "\n"
    return {
        "report": report,
        "findings": findings_txt,
        "diagnosis": f"BI-RADS {overall}",
        "recommendations": rec,
        "birads": overall,
        "mode": "template",
    }


def _build_prompt(findings: dict, examples: Optional[list], lang: str) -> tuple[str, str]:
    lang_name = _LANG_NAME.get(lang, lang)
    system = (
        "Siz mammografiya hisobotlarini tayyorlovchi yordamchisiz. "
        "QAT'IY QOIDA: faqat sizga berilgan strukturaviy topilmalardan foydalaning. "
        "Yangi topilma, o'lcham, lokalizatsiya, BI-RADS yoki tashxis O'YLAB TOPMANG. "
        "Berilmagan ma'lumotni yozmang va taxmin qilmang. "
        "Bu hisobot radiolog tomonidan tekshirib tasdiqlanadigan QORALAMA. "
        f"Hisobotni {lang_name} tilida, qisqa va klinik uslubda yozing. "
        "Tuzilma: 'Topilmalar', 'Umumiy baho (BI-RADS)', 'Tavsiya'."
    )
    ex_block = ""
    if examples:
        joined = "\n---\n".join(str(e).strip() for e in examples[:5])
        ex_block = (
            "Quyida mavjud hisobotlardan uslub namunalari (FAQAT yozuv uslubi uchun; "
            "ulardagi topilmalar yoki bemor ma'lumotlarini ko'chirmang):\n\n"
            f"{joined}\n\n"
        )
    user = (
        ex_block
        + "Quyidagi strukturaviy topilmalardan mammografiya hisoboti qoralamasini yozing.\n\n"
        + "TOPILMALAR (JSON):\n"
        + json.dumps(findings, ensure_ascii=False, indent=2)
    )
    return system, user


def draft_llm_report(
    findings: dict,
    examples: Optional[list] = None,
    lang: str = "uz",
    model: str = REPORT_MODEL,
) -> dict:
    """Claude bilan grounded tabiiy hisobot qoralamasi.

    ANTHROPIC_API_KEY (yoki ANTHROPIC_AUTH_TOKEN) va `anthropic` SDK talab qilinadi.
    """
    try:
        import anthropic
    except ImportError as e:
        raise RuntimeError("anthropic SDK o'rnatilmagan — `pip install anthropic`") from e
    if not (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")):
        raise RuntimeError("ANTHROPIC_API_KEY o'rnatilmagan — LLM qoralama uchun kerak")

    system, user = _build_prompt(findings, examples, lang)
    client = anthropic.Anthropic()
    resp = client.messages.create(
        model=model,
        max_tokens=8000,
        thinking={"type": "adaptive"},
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    text = "".join(b.text for b in resp.content if b.type == "text").strip()
    return {
        "report": text,
        "diagnosis": f"BI-RADS {findings.get('overall_birads', '')}",
        "recommendations": findings.get("recommendation", ""),
        "birads": findings.get("overall_birads", ""),
        "mode": "llm",
        "model": model,
    }


def _ollama_available(timeout: float = 2.0) -> Optional[list]:
    """Ollama serveri ishlayaptimi? Ishlasa o'rnatilgan modellar ro'yxati, aks holda None."""
    try:
        with urllib.request.urlopen(OLLAMA_HOST + "/api/tags", timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8"))
        return [m.get("name", "") for m in data.get("models", [])]
    except Exception:
        return None


def draft_local_report(
    findings: dict,
    examples: Optional[list] = None,
    lang: str = "uz",
    model: Optional[str] = None,
) -> dict:
    """Lokal Ollama modeli bilan grounded tabiiy hisobot qoralamasi (kalitsiz)."""
    model = model or OLLAMA_MODEL
    system, user = _build_prompt(findings, examples, lang)
    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "stream": False,
        "options": {"temperature": 0.2},
    }).encode("utf-8")
    req = urllib.request.Request(
        OLLAMA_HOST + "/api/chat", data=payload,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            data = json.loads(r.read().decode("utf-8"))
    except urllib.error.URLError as e:
        raise RuntimeError(
            f"Ollama'ga ulanib bo'lmadi ({OLLAMA_HOST}) — server ishlab turganini tekshiring"
        ) from e
    if data.get("error"):
        raise RuntimeError(f"Ollama xatosi: {data['error']}")
    text = ((data.get("message") or {}).get("content") or "").strip()
    if not text:
        raise RuntimeError("Ollama bo'sh javob qaytardi (model yuklanmaganmi?)")
    return {
        "report": text,
        "diagnosis": f"BI-RADS {findings.get('overall_birads', '')}",
        "recommendations": findings.get("recommendation", ""),
        "birads": findings.get("overall_birads", ""),
        "mode": "local",
        "model": model,
    }


def generate_report(
    findings: dict,
    mode: str = "auto",
    examples: Optional[list] = None,
    lang: str = "uz",
) -> dict:
    """mode:
    'template' — deterministik shablon (modelsiz, doim ishlaydi)
    'local'    — lokal Ollama modeli
    'cloud'    — Anthropic Claude (ANTHROPIC_API_KEY kerak)
    'auto'     — lokal (Ollama) bo'lsa undan, aks holda shablonga tushadi
    """
    if mode == "template":
        return render_template_report(findings, lang)
    if mode == "local":
        return draft_local_report(findings, examples=examples, lang=lang)
    if mode in ("cloud", "llm"):
        return draft_llm_report(findings, examples=examples, lang=lang)
    # auto: lokal (Ollama) -> shablon
    try:
        return draft_local_report(findings, examples=examples, lang=lang)
    except Exception as e:  # noqa: BLE001
        out = render_template_report(findings, lang)
        out["mode"] = "template_fallback"
        out["local_error"] = str(e)
        return out
