"""
Train and evaluate XS-Classifier on the local mammography corpus.

Outputs (under paper/figures/):
    metrics.json           — full per-model results
    confusion_*.png        — confusion matrices
    pr_curves.png          — precision-recall curves
    roc_curves.png         — ROC curves
    feature_importances.txt — top features per class

Usage:
    python -m app.research.train_classifier
"""
from __future__ import annotations

import json
import re
import sys
import warnings
from pathlib import Path

import numpy as np

warnings.filterwarnings("ignore", category=UserWarning)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import (
    accuracy_score, average_precision_score, confusion_matrix,
    f1_score, precision_recall_curve, precision_score, recall_score,
    roc_auc_score, roc_curve,
)
from sklearn.model_selection import StratifiedKFold

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from app.db import get_conn  # noqa: E402
from app.models_arch.xs_classifier import (  # noqa: E402
    make_xs_pipeline, make_word_only_baseline, make_char_only_baseline,
    make_baseline_pipeline, XSConfig, split_by_script,
)


CANCER_PATTERNS = [
    r"\bC\s*[\-\.]?\s*50", r"С\s*[\-\.]?\s*50",
    r"\bs\s*[\-\.]\s*50",
    r"\bsarat[oa]n", r"\bсарат[оа]н",
    r"\bрак\b", r"раков", r"раком", r"\braka?\b",
    r"саратон", r"saraton",
    r"karsinom", r"карцином",
    r"\bM\s*8500/3\b", r"opux", r"опух",
    r"malign", r"малигн",
    r"neoplasm", r"новообраз",
]
CANCER_RE = re.compile("|".join(CANCER_PATTERNS), re.IGNORECASE | re.UNICODE)


def detect_cancer(text: str) -> bool:
    return bool(CANCER_RE.search(text)) if text else False


OUT = ROOT / "paper" / "figures"
OUT.mkdir(parents=True, exist_ok=True)


def load_dataset():
    with get_conn() as c:
        rows = [
            dict(r) for r in c.execute(
                "SELECT id, complaints, history, clinical_findings, "
                "diagnosis, report FROM records"
            ).fetchall()
        ]
    X, y, ids = [], [], []
    for r in rows:
        text = " ".join(filter(None, [
            r.get("complaints") or "",
            r.get("history") or "",
            r.get("clinical_findings") or "",
        ]))
        text = text.strip()
        if not text:
            continue
        target_text = " ".join(filter(None, [
            r.get("diagnosis") or "",
            r.get("report") or "",
        ]))
        is_cancer = detect_cancer(target_text)
        X.append(text)
        y.append(int(is_cancer))
        ids.append(r["id"])
    return X, np.asarray(y), ids


def script_summary(X):
    cyr_dom = lat_dom = mixed = 0
    for t in X:
        cyr, lat = split_by_script(t)
        cl, ll = len(cyr), len(lat)
        if cl > 2 * ll:
            cyr_dom += 1
        elif ll > 2 * cl:
            lat_dom += 1
        else:
            mixed += 1
    return {"cyrillic_dominant": cyr_dom, "latin_dominant": lat_dom, "mixed": mixed}


def cv_evaluate(name, pipeline, X, y, n_splits=5, seed=42):
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    accs, f1s, precs, recs, aurocs, auprs = [], [], [], [], [], []
    all_y_true, all_y_pred, all_y_score = [], [], []

    for fold, (tr, te) in enumerate(skf.split(X, y)):
        X_tr = [X[i] for i in tr]
        X_te = [X[i] for i in te]
        y_tr, y_te = y[tr], y[te]
        pipeline.fit(X_tr, y_tr)
        y_pred = pipeline.predict(X_te)
        try:
            y_score = pipeline.predict_proba(X_te)[:, 1]
        except Exception:
            y_score = pipeline.decision_function(X_te)
        accs.append(accuracy_score(y_te, y_pred))
        f1s.append(f1_score(y_te, y_pred))
        precs.append(precision_score(y_te, y_pred))
        recs.append(recall_score(y_te, y_pred))
        try:
            aurocs.append(roc_auc_score(y_te, y_score))
            auprs.append(average_precision_score(y_te, y_score))
        except Exception:
            pass
        all_y_true.extend(y_te.tolist())
        all_y_pred.extend(y_pred.tolist())
        all_y_score.extend(np.asarray(y_score).tolist())

    return {
        "name": name,
        "accuracy": (np.mean(accs), np.std(accs)),
        "f1": (np.mean(f1s), np.std(f1s)),
        "precision": (np.mean(precs), np.std(precs)),
        "recall": (np.mean(recs), np.std(recs)),
        "auroc": (np.mean(aurocs), np.std(aurocs)) if aurocs else (None, None),
        "auprc": (np.mean(auprs), np.std(auprs)) if auprs else (None, None),
        "y_true": np.asarray(all_y_true),
        "y_pred": np.asarray(all_y_pred),
        "y_score": np.asarray(all_y_score),
    }


def plot_confusion(y_true, y_pred, title, fname):
    cm = confusion_matrix(y_true, y_pred)
    fig, ax = plt.subplots(figsize=(4, 3.6))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks([0, 1]); ax.set_yticks([0, 1])
    ax.set_xticklabels(["non-cancer", "cancer"])
    ax.set_yticklabels(["non-cancer", "cancer"])
    ax.set_xlabel("Predicted"); ax.set_ylabel("True")
    ax.set_title(title)
    for i in range(2):
        for j in range(2):
            color = "white" if cm[i, j] > cm.max() / 2 else "black"
            ax.text(j, i, str(cm[i, j]), ha="center", va="center",
                    color=color, fontsize=12, fontweight="bold")
    fig.colorbar(im, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(OUT / fname, dpi=150)
    plt.close(fig)


def plot_curves(results, fname_pr, fname_roc):
    fig, ax = plt.subplots(figsize=(5, 4))
    for r in results:
        if "y_score" not in r or r["auprc"][0] is None:
            continue
        prec, rec, _ = precision_recall_curve(r["y_true"], r["y_score"])
        ax.plot(rec, prec, label=f"{r['name']} (AUPRC={r['auprc'][0]:.3f})")
    ax.set_xlabel("Recall"); ax.set_ylabel("Precision")
    ax.set_title("Precision–Recall (5-fold CV pooled)")
    ax.legend(loc="lower left", fontsize=8); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(OUT / fname_pr, dpi=150); plt.close(fig)

    fig, ax = plt.subplots(figsize=(5, 4))
    for r in results:
        if r["auroc"][0] is None:
            continue
        fpr, tpr, _ = roc_curve(r["y_true"], r["y_score"])
        ax.plot(fpr, tpr, label=f"{r['name']} (AUROC={r['auroc'][0]:.3f})")
    ax.plot([0, 1], [0, 1], "--", color="gray", lw=0.8)
    ax.set_xlabel("False Positive Rate"); ax.set_ylabel("True Positive Rate")
    ax.set_title("ROC (5-fold CV pooled)")
    ax.legend(loc="lower right", fontsize=8); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(OUT / fname_roc, dpi=150); plt.close(fig)


def plot_class_balance(y, fname):
    fig, ax = plt.subplots(figsize=(4, 3))
    counts = np.bincount(y)
    ax.bar(["non-cancer", "cancer"], counts, color=["#3b82f6", "#ef4444"])
    for i, c in enumerate(counts):
        ax.text(i, c + 5, str(c), ha="center", fontweight="bold")
    ax.set_ylabel("count")
    ax.set_title(f"Class distribution (n={int(counts.sum())})")
    fig.tight_layout(); fig.savefig(OUT / fname, dpi=150); plt.close(fig)


def plot_script_distribution(stats, fname):
    fig, ax = plt.subplots(figsize=(4, 3))
    keys = ["cyrillic_dominant", "latin_dominant", "mixed"]
    vals = [stats[k] for k in keys]
    colors = ["#7c3aed", "#0ea5e9", "#10b981"]
    ax.bar([k.replace("_", "\n") for k in keys], vals, color=colors)
    for i, v in enumerate(vals):
        ax.text(i, v + 8, str(v), ha="center", fontweight="bold")
    ax.set_ylabel("documents")
    ax.set_title("Script distribution")
    fig.tight_layout(); fig.savefig(OUT / fname, dpi=150); plt.close(fig)


def main():
    print("=" * 60)
    print("Loading dataset...")
    X, y, ids = load_dataset()
    n = len(X)
    n_pos = int(y.sum())
    print(f"  total: {n}, positive: {n_pos} ({n_pos/n*100:.1f}%), "
          f"negative: {n-n_pos}")

    plot_class_balance(y, "class_balance.png")

    print("Script analysis...")
    stats = script_summary(X)
    print(f"  {stats}")
    plot_script_distribution(stats, "script_distribution.png")

    models = {
        "Word-only TF-IDF (Latin-blind)": make_word_only_baseline(),
        "Char n-gram TF-IDF (script-blind)": make_char_only_baseline(),
        "Word + char hybrid (single stream)": make_baseline_pipeline(
            analyzer="char_wb", ngram=(3, 5)),
        "XS-Classifier (proposed)": make_xs_pipeline(),
    }

    print("\nRunning 5-fold stratified CV...")
    print("-" * 60)
    results = []
    for name, pipe in models.items():
        print(f"  · {name}")
        r = cv_evaluate(name, pipe, X, y, n_splits=5)
        results.append(r)
        print(f"      acc={r['accuracy'][0]:.4f}±{r['accuracy'][1]:.3f}, "
              f"F1={r['f1'][0]:.4f}±{r['f1'][1]:.3f}, "
              f"AUROC={r['auroc'][0]:.4f}, AUPRC={r['auprc'][0]:.4f}")

    print("\nGenerating plots...")
    plot_curves(results, "pr_curves.png", "roc_curves.png")
    for r in results:
        slug = re.sub(r"[^a-z0-9]+", "_", r["name"].lower()).strip("_")
        plot_confusion(r["y_true"], r["y_pred"], r["name"], f"cm_{slug}.png")

    out_metrics = {
        "n_samples": n, "n_positive": n_pos, "n_negative": n - n_pos,
        "script_distribution": stats,
        "models": [{
            "name": r["name"],
            "accuracy_mean": float(r["accuracy"][0]),
            "accuracy_std": float(r["accuracy"][1]),
            "f1_mean": float(r["f1"][0]),
            "f1_std": float(r["f1"][1]),
            "precision_mean": float(r["precision"][0]),
            "precision_std": float(r["precision"][1]),
            "recall_mean": float(r["recall"][0]),
            "recall_std": float(r["recall"][1]),
            "auroc_mean": float(r["auroc"][0]) if r["auroc"][0] is not None else None,
            "auprc_mean": float(r["auprc"][0]) if r["auprc"][0] is not None else None,
        } for r in results],
    }
    (OUT / "metrics.json").write_text(
        json.dumps(out_metrics, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\n" + "=" * 60)
    print("RESULTS SUMMARY (5-fold CV)")
    print("=" * 60)
    print(f"{'Model':<42} {'Acc':>10} {'F1':>10} {'AUROC':>10} {'AUPRC':>10}")
    print("-" * 90)
    for r in results:
        print(f"{r['name']:<42}  "
              f"{r['accuracy'][0]:.4f}  "
              f"{r['f1'][0]:.4f}  "
              f"{r['auroc'][0]:.4f}  "
              f"{r['auprc'][0]:.4f}")

    print(f"\nFigures saved to: {OUT}")
    print(f"Metrics JSON:    {OUT / 'metrics.json'}")


if __name__ == "__main__":
    main()
