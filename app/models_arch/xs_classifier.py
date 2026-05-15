"""
XS-Classifier — Cross-Script adaptive classifier for mammography reports.

The task: binary classification of mammography clinical text (Uzbek-Cyrillic,
Uzbek-Latin, Russian, frequently code-switched within a single document) into
{cancer, non-cancer}.

The novel idea: a *script-aware* feature stream. Each token is independently
classified into a script bucket via Unicode-block detection; we extract one
TF-IDF vector per bucket and concatenate them, allowing the linear classifier
to learn script-specific oncology vocabulary while implicitly sharing
character-level features across the two scripts of Uzbek.

Components:
    - ScriptSegmenter           : per-token script detection
    - CrossScriptVectorizer     : two-stream TF-IDF (Cyrillic + Latin) with
                                  shared char-n-gram backbone
    - XSClassifier              : sklearn-compatible Pipeline factory
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

import numpy as np
import scipy.sparse as sp
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline


# ---------------------------------------------------------------------------
# 1. Script detection
# ---------------------------------------------------------------------------


_TOKEN_RE = re.compile(r"\b\w+\b", flags=re.UNICODE)


def script_of_char(ch: str) -> str:
    """Return 'cyrillic', 'latin', or 'other' for a single character."""
    if not ch.isalpha():
        return "other"
    o = ord(ch)
    if 0x0400 <= o <= 0x04FF or 0x0500 <= o <= 0x052F:
        return "cyrillic"
    if 0x0041 <= o <= 0x024F:
        return "latin"
    return "other"


def dominant_script(token: str) -> str:
    counts = {"cyrillic": 0, "latin": 0, "other": 0}
    for ch in token:
        counts[script_of_char(ch)] += 1
    if counts["cyrillic"] > counts["latin"]:
        return "cyrillic"
    if counts["latin"] > counts["cyrillic"]:
        return "latin"
    return "other"


def split_by_script(text: str) -> tuple[str, str]:
    """Return (cyrillic_tokens_joined, latin_tokens_joined)."""
    cyr, lat = [], []
    for tok in _TOKEN_RE.findall(text or ""):
        s = dominant_script(tok)
        norm = unicodedata.normalize("NFKC", tok.lower())
        if s == "cyrillic":
            cyr.append(norm)
        elif s == "latin":
            lat.append(norm)
        else:
            cyr.append(norm)
            lat.append(norm)
    return " ".join(cyr), " ".join(lat)


# ---------------------------------------------------------------------------
# 2. Stream selectors (transformers picking one stream from a (text, label) pair)
# ---------------------------------------------------------------------------


class _StreamSelector(BaseEstimator, TransformerMixin):
    def __init__(self, stream: str = "cyrillic"):
        self.stream = stream

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        out = []
        for text in X:
            cyr, lat = split_by_script(text)
            out.append(cyr if self.stream == "cyrillic" else lat)
        return out


# ---------------------------------------------------------------------------
# 3. Pipeline factory
# ---------------------------------------------------------------------------


@dataclass
class XSConfig:
    word_min_df: int = 2
    word_max_df: float = 0.95
    word_ngram: tuple = (1, 2)
    char_min_df: int = 2
    char_max_df: float = 0.95
    char_ngram: tuple = (3, 5)
    sublinear_tf: bool = True
    C: float = 1.0
    class_weight: str | None = "balanced"
    max_iter: int = 2000


def make_xs_pipeline(cfg: XSConfig | None = None) -> Pipeline:
    """Two-stream Cross-Script classifier.

    The architecture:
       text → ScriptSegmenter →
         ├─ Cyrillic stream → word TF-IDF + char TF-IDF
         └─ Latin    stream → word TF-IDF + char TF-IDF
       → concatenate sparse features → Logistic Regression(L2)
    """
    cfg = cfg or XSConfig()

    def stream_branch(stream: str) -> Pipeline:
        return Pipeline([
            ("select", _StreamSelector(stream=stream)),
            ("union", FeatureUnion([
                ("word", TfidfVectorizer(
                    analyzer="word", ngram_range=cfg.word_ngram,
                    min_df=cfg.word_min_df, max_df=cfg.word_max_df,
                    sublinear_tf=cfg.sublinear_tf, token_pattern=r"\b\w+\b",
                )),
                ("char", TfidfVectorizer(
                    analyzer="char_wb", ngram_range=cfg.char_ngram,
                    min_df=cfg.char_min_df, max_df=cfg.char_max_df,
                    sublinear_tf=cfg.sublinear_tf,
                )),
            ])),
        ])

    return Pipeline([
        ("xs", FeatureUnion([
            ("cyrillic", stream_branch("cyrillic")),
            ("latin",    stream_branch("latin")),
        ])),
        ("clf", LogisticRegression(
            C=cfg.C, max_iter=cfg.max_iter,
            class_weight=cfg.class_weight, solver="liblinear",
        )),
    ])


def make_baseline_pipeline(
    analyzer: str = "char_wb",
    ngram: tuple = (3, 5),
    C: float = 1.0,
) -> Pipeline:
    """Single-stream TF-IDF baseline (no script awareness)."""
    return Pipeline([
        ("tfidf", TfidfVectorizer(
            analyzer=analyzer, ngram_range=ngram,
            min_df=2, max_df=0.95, sublinear_tf=True,
            token_pattern=r"\b\w+\b" if analyzer == "word" else None,
        )),
        ("clf", LogisticRegression(
            C=C, max_iter=2000, class_weight="balanced", solver="liblinear",
        )),
    ])


def make_word_only_baseline() -> Pipeline:
    return make_baseline_pipeline(analyzer="word", ngram=(1, 2))


def make_char_only_baseline() -> Pipeline:
    return make_baseline_pipeline(analyzer="char_wb", ngram=(3, 5))


# ---------------------------------------------------------------------------
# 4. Sanity entry point
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    samples = [
        "Шикояти: Унг сут безидаги хосилага. Анамнесис: бемор узи 2024 йилда",
        "Shikoyati: O'ng sut bezidagi xosilaga. Anamnesis morbi: bemor o'zini",
        "Жалобы: на образование в правой молочной железе.",
    ]
    for s in samples:
        cyr, lat = split_by_script(s)
        print(f"  cyr: {cyr[:60]!r}")
        print(f"  lat: {lat[:60]!r}")
        print()

    pipe = make_xs_pipeline()
    pipe.fit(samples + samples, [0, 1, 0, 1, 0, 1])
    print(f"  XS pipeline fit OK, predict: {pipe.predict(samples)}")
