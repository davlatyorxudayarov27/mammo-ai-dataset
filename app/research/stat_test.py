"""Paired statistical significance test (XS-Classifier vs baselines)."""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import StratifiedKFold
from scipy.stats import ttest_rel, wilcoxon

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.research.train_classifier import load_dataset
from app.models_arch.xs_classifier import (
    make_xs_pipeline, make_word_only_baseline,
    make_char_only_baseline, make_baseline_pipeline,
)


def fold_scores(pipeline, X, y, n_splits=5, seed=42):
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    accs, f1s = [], []
    for tr, te in skf.split(X, y):
        X_tr = [X[i] for i in tr]; X_te = [X[i] for i in te]
        pipeline.fit(X_tr, y[tr])
        y_p = pipeline.predict(X_te)
        accs.append(accuracy_score(y[te], y_p))
        f1s.append(f1_score(y[te], y_p))
    return np.asarray(accs), np.asarray(f1s)


def main():
    X, y, _ = load_dataset()
    print(f"n={len(X)}, positives={int(y.sum())}\n")

    print("Running 5-fold CV per model (deterministic seed)...")
    xs_acc, xs_f1 = fold_scores(make_xs_pipeline(), X, y)
    print(f"  XS-Classifier:           acc={xs_acc.mean():.4f}, f1={xs_f1.mean():.4f}")

    word_acc, word_f1 = fold_scores(make_word_only_baseline(), X, y)
    print(f"  Word-only:               acc={word_acc.mean():.4f}, f1={word_f1.mean():.4f}")

    char_acc, char_f1 = fold_scores(make_char_only_baseline(), X, y)
    print(f"  Char n-gram:             acc={char_acc.mean():.4f}, f1={char_f1.mean():.4f}")

    print("\nPaired tests (XS-Classifier vs baselines, 5 folds):")
    for label, base_acc, base_f1 in [
        ("Word-only", word_acc, word_f1),
        ("Char n-gram", char_acc, char_f1),
    ]:
        d_acc = xs_acc - base_acc
        d_f1 = xs_f1 - base_f1
        try:
            t_acc = ttest_rel(xs_acc, base_acc)
            t_f1 = ttest_rel(xs_f1, base_f1)
            print(f"  vs {label}:")
            print(f"    Δacc = {d_acc.mean()*100:+.3f}pp, "
                  f"paired-t p={t_acc.pvalue:.4f}")
            print(f"    Δf1  = {d_f1.mean()*100:+.3f}pp, "
                  f"paired-t p={t_f1.pvalue:.4f}")
            try:
                w_acc = wilcoxon(xs_acc, base_acc)
                w_f1 = wilcoxon(xs_f1, base_f1)
                print(f"    Wilcoxon acc p={w_acc.pvalue:.4f}, "
                      f"f1 p={w_f1.pvalue:.4f}")
            except Exception:
                pass
        except Exception as e:
            print(f"  test failed: {e}")


if __name__ == "__main__":
    main()
