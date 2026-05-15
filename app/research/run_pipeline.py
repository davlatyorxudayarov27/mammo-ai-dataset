"""End-to-end mammography lesion-detection pipeline runner.

Orchestrates the six research stages we built as one resumable, idempotent
command. Each stage runs as a subprocess (isolated failure, full logs
captured), and each stage skips itself if its sentinel output already
exists (use --force to override per-stage).

Stages:
    0  preprocess       DICOM (local)         → preprocessed PNG + manifest
    1  cbis_convert     CBIS-DDSM root        → YOLO-format dataset
    2a train_yolo       cbis_yolo/dataset.yaml → YOLOv8 baseline + FROC
    2b train_tillnet0   cbis_yolo + (img-only) → stage-1 TILLNet on CBIS
    3  pseudo_labels    local manifest + DB    → weak YOLO labels + review queue
    3b load_review      review_queue.jsonl     → review_decisions DB rows (pending)
    4  train_tillnet1   stage1 ckpt + pseudo   → stage-2 multimodal TILLNet
    --- HUMAN STEP: radiologist reviews via MAMOGRAF UI; statuses flip to ---
    --- accepted/edited/rejected. Re-run from `gold_to_yolo` afterwards.   ---
    4b gold_to_yolo     review_decisions DB    → gold-label YOLO dataset
    4c train_tillnet2   stage2 ckpt + gold     → stage-3 fine-tune
    5  summarise        all FROC summaries     → run.summary.{json,md}

Every stage's output goes under <out_root>/, with one log file per stage
under <out_root>/logs/. Re-running with the same flags resumes where the
last invocation stopped.

Example:
    python -m app.research.run_pipeline \\
        --local-dicoms  /data/MAMOGRAF/uploads \\
        --cbis-root     /data/CBIS-DDSM \\
        --texts-csv     /data/MAMOGRAF/reports.csv \\
        --out-root      runs/full \\
        --gpu           0 \\
        --imgsz         1024 \\
        --epochs-stage1 100 \\
        --epochs-stage2 30
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import warnings
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Callable

warnings.filterwarnings("ignore")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


@dataclass
class PipelineCfg:
    out_root: Path
    local_dicoms: Path | None
    cbis_root: Path | None
    texts_csv: Path | None
    db_path: Path
    imgsz: int = 1024
    batch: int = 8
    epochs_stage1: int = 100
    epochs_stage2: int = 30
    gpu: str = "0"
    yolo_model: str = "yolov8m.pt"
    workers: int = 4
    skip: set[str] = field(default_factory=set)
    only: set[str] = field(default_factory=set)
    force: set[str] = field(default_factory=set)
    dry_run: bool = False
    min_pseudo_conf: float = 0.5

    @property
    def logs_dir(self) -> Path:
        return self.out_root / "logs"

    @property
    def preprocessed_dir(self) -> Path:
        return self.out_root / "local_preprocessed"

    @property
    def cbis_yolo_dir(self) -> Path:
        return self.out_root / "cbis_yolo"

    @property
    def pseudo_dir(self) -> Path:
        return self.out_root / "local_pseudo"

    @property
    def runs_dir(self) -> Path:
        return self.out_root / "runs"

    @property
    def gold_yolo_dir(self) -> Path:
        return self.out_root / "gold_yolo"


# ---------------------------------------------------------------------------
# Stage runner — subprocess with tee'd log
# ---------------------------------------------------------------------------


def _run(cmd: list[str], log_path: Path, dry_run: bool) -> int:
    """Run a subprocess, streaming stdout to console + log file."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"\n[$] {' '.join(str(c) for c in cmd)}")
    if dry_run:
        return 0
    t0 = time.time()
    with log_path.open("w", encoding="utf-8") as logf:
        logf.write(f"# {' '.join(str(c) for c in cmd)}\n")
        logf.flush()
        try:
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace", bufsize=1,
            )
        except FileNotFoundError as e:
            print(f"[err] {e}")
            return 127
        for line in proc.stdout:                                # type: ignore[union-attr]
            sys.stdout.write(line)
            logf.write(line)
            logf.flush()
        rc = proc.wait()
    dt = time.time() - t0
    print(f"[done] rc={rc}  ({dt:.1f}s)  log → {log_path}")
    return rc


def _exists_nonempty(path: Path) -> bool:
    if not path.exists():
        return False
    if path.is_file():
        return path.stat().st_size > 0
    # directory: at least one file inside
    for _ in path.rglob("*"):
        return True
    return False


def _python() -> str:
    """Return the current Python executable so children inherit our venv."""
    return sys.executable or "python"


# ---------------------------------------------------------------------------
# Stages
# ---------------------------------------------------------------------------


class Pipeline:
    def __init__(self, cfg: PipelineCfg):
        self.cfg = cfg
        cfg.out_root.mkdir(parents=True, exist_ok=True)
        cfg.logs_dir.mkdir(parents=True, exist_ok=True)

    def _device_arg(self) -> list[str]:
        return ["--device", self.cfg.gpu] if self.cfg.gpu else []

    # 0 ----------------------------------------------------------------
    def stage_preprocess(self) -> None:
        cfg = self.cfg
        manifest = cfg.preprocessed_dir / "manifest.jsonl"
        if not cfg.local_dicoms:
            print("[skip] preprocess: --local-dicoms not provided")
            return
        if _exists_nonempty(manifest) and "preprocess" not in cfg.force:
            print(f"[skip] preprocess: {manifest} already populated")
            return
        rc = _run(
            [_python(), "-m", "app.research.preprocess",
             "--input", str(cfg.local_dicoms),
             "--output", str(cfg.preprocessed_dir),
             "--size", str(cfg.imgsz)],
            cfg.logs_dir / "0_preprocess.log",
            cfg.dry_run,
        )
        if rc != 0:
            raise RuntimeError(f"preprocess stage failed (rc={rc})")

    # 1 ----------------------------------------------------------------
    def stage_cbis_convert(self) -> None:
        cfg = self.cfg
        yaml_path = cfg.cbis_yolo_dir / "dataset.yaml"
        if not cfg.cbis_root:
            print("[skip] cbis_convert: --cbis-root not provided")
            return
        if _exists_nonempty(yaml_path) and "cbis_convert" not in cfg.force:
            print(f"[skip] cbis_convert: {yaml_path} exists")
            return
        rc = _run(
            [_python(), "-m", "app.research.datasets.cbis_ddsm",
             "--root", str(cfg.cbis_root),
             "--out", str(cfg.cbis_yolo_dir),
             "--size", str(cfg.imgsz)],
            cfg.logs_dir / "1_cbis_convert.log",
            cfg.dry_run,
        )
        if rc != 0:
            raise RuntimeError(f"cbis_convert stage failed (rc={rc})")

    # 2a ---------------------------------------------------------------
    def stage_train_yolo(self) -> None:
        cfg = self.cfg
        run_dir = cfg.runs_dir / "cbis_yolo_baseline"
        best = run_dir / "weights" / "best.pt"
        if not (cfg.cbis_yolo_dir / "dataset.yaml").exists():
            print("[skip] train_yolo: cbis dataset.yaml missing")
            return
        if _exists_nonempty(best) and "train_yolo" not in cfg.force:
            print(f"[skip] train_yolo: {best} exists")
            return
        rc = _run(
            [_python(), "-m", "app.research.train_detector",
             "--data", str(cfg.cbis_yolo_dir / "dataset.yaml"),
             "--model", cfg.yolo_model,
             "--epochs", str(cfg.epochs_stage1),
             "--imgsz", str(cfg.imgsz),
             "--batch", str(cfg.batch),
             "--workers", str(cfg.workers),
             "--project", str(cfg.runs_dir),
             "--name", "cbis_yolo_baseline",
             *self._device_arg()],
            cfg.logs_dir / "2a_train_yolo.log",
            cfg.dry_run,
        )
        if rc != 0:
            raise RuntimeError(f"train_yolo stage failed (rc={rc})")

    # 2b ---------------------------------------------------------------
    def stage_train_tillnet0(self) -> None:
        cfg = self.cfg
        run_dir = cfg.runs_dir / "cbis_tillnet_imgonly"
        best = run_dir / "best.pt"
        if not (cfg.cbis_yolo_dir / "dataset.yaml").exists():
            print("[skip] train_tillnet0: cbis dataset.yaml missing")
            return
        if _exists_nonempty(best) and "train_tillnet0" not in cfg.force:
            print(f"[skip] train_tillnet0: {best} exists")
            return
        # Stage-1: train image-only on CBIS (no text branch).
        rc = _run(
            [_python(), "-m", "app.research.train_tillnet",
             "--data", str(cfg.cbis_yolo_dir / "dataset.yaml"),
             "--epochs", str(cfg.epochs_stage1),
             "--imgsz", str(cfg.imgsz),
             "--batch", str(cfg.batch),
             "--workers", str(cfg.workers),
             "--device", cfg.gpu or "cpu",
             "--out", str(run_dir),
             "--no-text"],
            cfg.logs_dir / "2b_train_tillnet0.log",
            cfg.dry_run,
        )
        if rc != 0:
            raise RuntimeError(f"train_tillnet0 stage failed (rc={rc})")

    # 3 ----------------------------------------------------------------
    def stage_pseudo_labels(self) -> None:
        cfg = self.cfg
        manifest = cfg.preprocessed_dir / "manifest.jsonl"
        review = cfg.pseudo_dir / "review_queue.jsonl"
        if not _exists_nonempty(manifest):
            print("[skip] pseudo_labels: preprocessed manifest missing")
            return
        if _exists_nonempty(review) and "pseudo_labels" not in cfg.force:
            print(f"[skip] pseudo_labels: {review} exists")
            return
        cmd = [_python(), "-m", "app.research.pseudo_labels",
               "--manifest", str(manifest),
               "--images-root", str(cfg.preprocessed_dir / "images"),
               "--db", str(cfg.db_path),
               "--out", str(cfg.pseudo_dir),
               "--min-confidence", str(cfg.min_pseudo_conf)]
        if cfg.texts_csv:
            cmd += ["--text-csv", str(cfg.texts_csv)]
        rc = _run(cmd, cfg.logs_dir / "3_pseudo_labels.log", cfg.dry_run)
        if rc != 0:
            raise RuntimeError(f"pseudo_labels stage failed (rc={rc})")

    # 4 ----------------------------------------------------------------
    def stage_train_tillnet1(self) -> None:
        cfg = self.cfg
        prev_best = cfg.runs_dir / "cbis_tillnet_imgonly" / "best.pt"
        run_dir = cfg.runs_dir / "local_tillnet_stage2"
        best = run_dir / "best.pt"
        if not _exists_nonempty(prev_best):
            print("[skip] train_tillnet1: stage-1 best.pt missing")
            return
        if not (cfg.pseudo_dir / "dataset.yaml").exists():
            print("[skip] train_tillnet1: pseudo dataset.yaml missing")
            return
        if _exists_nonempty(best) and "train_tillnet1" not in cfg.force:
            print(f"[skip] train_tillnet1: {best} exists")
            return
        cmd = [_python(), "-m", "app.research.train_tillnet",
               "--data", str(cfg.pseudo_dir / "dataset.yaml"),
               "--epochs", str(cfg.epochs_stage2),
               "--imgsz", str(cfg.imgsz),
               "--batch", str(cfg.batch),
               "--workers", str(cfg.workers),
               "--device", cfg.gpu or "cpu",
               "--out", str(run_dir),
               "--resume", str(prev_best),
               "--lr", "5e-5"]
        if cfg.texts_csv:
            cmd += ["--texts", str(cfg.texts_csv)]
        rc = _run(cmd, cfg.logs_dir / "4_train_tillnet1.log", cfg.dry_run)
        if rc != 0:
            raise RuntimeError(f"train_tillnet1 stage failed (rc={rc})")

    # 3b ---------------------------------------------------------------
    def stage_load_review(self) -> None:
        """Ingest the pseudo_labels/review_queue.jsonl into review_decisions DB."""
        cfg = self.cfg
        queue = cfg.pseudo_dir / "review_queue.jsonl"
        if not _exists_nonempty(queue):
            print("[skip] load_review: pseudo_dir/review_queue.jsonl missing")
            return
        # Idempotency: this stage is itself idempotent at the loader level
        # (UNIQUE constraint on (sop_uid, source_queue)). We always re-invoke
        # so newly-generated queue rows get loaded — `--force` is not needed.
        rc = _run(
            [_python(), "-m", "app.research.load_review_queue",
             "--queue", str(queue),
             "--preproc-out", str(cfg.preprocessed_dir),
             "--source-tag", f"pipeline_{cfg.out_root.name}"],
            cfg.logs_dir / "3b_load_review.log",
            cfg.dry_run,
        )
        if rc != 0:
            raise RuntimeError(f"load_review stage failed (rc={rc})")

    # 4b ---------------------------------------------------------------
    def stage_gold_to_yolo(self) -> None:
        """Convert radiologist-verified rows into a YOLO dataset."""
        cfg = self.cfg
        yaml_path = cfg.gold_yolo_dir / "dataset.yaml"
        if _exists_nonempty(yaml_path) and "gold_to_yolo" not in cfg.force:
            print(f"[skip] gold_to_yolo: {yaml_path} exists")
            return
        rc = _run(
            [_python(), "-m", "app.research.gold_to_yolo",
             "--out", str(cfg.gold_yolo_dir),
             "--target-size", str(cfg.imgsz),
             "--include", "accepted,edited",
             "--copy"],
            cfg.logs_dir / "4b_gold_to_yolo.log",
            cfg.dry_run,
        )
        if rc != 0:
            print("[note] gold_to_yolo returned non-zero — likely no gold rows yet")
            print("       (radiologist must finish reviewing through the MAMOGRAF UI)")

    # 4c ---------------------------------------------------------------
    def stage_train_tillnet2(self) -> None:
        """Stage-3 fine-tune of TILLNet on radiologist-verified gold labels."""
        cfg = self.cfg
        prev_best = cfg.runs_dir / "local_tillnet_stage2" / "best.pt"
        run_dir = cfg.runs_dir / "local_tillnet_stage3"
        best = run_dir / "best.pt"
        if not _exists_nonempty(prev_best):
            print("[skip] train_tillnet2: stage-2 best.pt missing")
            return
        if not (cfg.gold_yolo_dir / "dataset.yaml").exists():
            print("[skip] train_tillnet2: gold dataset.yaml missing")
            return
        if _exists_nonempty(best) and "train_tillnet2" not in cfg.force:
            print(f"[skip] train_tillnet2: {best} exists")
            return
        cmd = [_python(), "-m", "app.research.train_tillnet",
               "--data", str(cfg.gold_yolo_dir / "dataset.yaml"),
               "--epochs", str(max(10, cfg.epochs_stage2 // 2)),     # shorter, lower LR
               "--imgsz", str(cfg.imgsz),
               "--batch", str(cfg.batch),
               "--workers", str(cfg.workers),
               "--device", cfg.gpu or "cpu",
               "--out", str(run_dir),
               "--resume", str(prev_best),
               "--lr", "2e-5"]
        if cfg.texts_csv:
            cmd += ["--texts", str(cfg.texts_csv)]
        rc = _run(cmd, cfg.logs_dir / "4c_train_tillnet2.log", cfg.dry_run)
        if rc != 0:
            raise RuntimeError(f"train_tillnet2 stage failed (rc={rc})")

    # 5 ----------------------------------------------------------------
    def stage_summarise(self) -> None:
        cfg = self.cfg
        out: dict = {"stages": {}, "config": {k: str(v) for k, v in asdict(cfg).items()}}

        def _read_json(p: Path):
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                return None

        def _last_history(p: Path):
            try:
                lines = [l for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
                return json.loads(lines[-1]) if lines else None
            except Exception:
                return None

        out["stages"]["preprocess"] = {
            "manifest_lines": sum(1 for _ in (cfg.preprocessed_dir / "manifest.jsonl").open(
                "r", encoding="utf-8")) if (cfg.preprocessed_dir / "manifest.jsonl").exists() else 0,
        }
        out["stages"]["cbis_convert"] = {
            "exists": (cfg.cbis_yolo_dir / "dataset.yaml").exists(),
        }

        yolo_summary = _read_json(cfg.runs_dir / "cbis_yolo_baseline" / "froc_summary.json")
        if yolo_summary:
            out["stages"]["train_yolo"] = {
                "n_images": yolo_summary.get("n_images"),
                "sens_at_fp": yolo_summary.get("sens_at_fp"),
                "iou_threshold": yolo_summary.get("iou_threshold"),
            }

        tn0 = _last_history(cfg.runs_dir / "cbis_tillnet_imgonly" / "history.jsonl")
        if tn0:
            out["stages"]["train_tillnet0"] = {
                "epoch": tn0.get("epoch"),
                "val_sens_at_fp": (tn0.get("val") or {}).get("sens_at_fp"),
                "train_loss": (tn0.get("train") or {}).get("loss"),
            }

        tn1 = _last_history(cfg.runs_dir / "local_tillnet_stage2" / "history.jsonl")
        if tn1:
            out["stages"]["train_tillnet1"] = {
                "epoch": tn1.get("epoch"),
                "val_sens_at_fp": (tn1.get("val") or {}).get("sens_at_fp"),
                "train_loss": (tn1.get("train") or {}).get("loss"),
            }

        tn2 = _last_history(cfg.runs_dir / "local_tillnet_stage3" / "history.jsonl")
        if tn2:
            out["stages"]["train_tillnet2"] = {
                "epoch": tn2.get("epoch"),
                "val_sens_at_fp": (tn2.get("val") or {}).get("sens_at_fp"),
                "train_loss": (tn2.get("train") or {}).get("loss"),
            }

        out["stages"]["pseudo_labels"] = {
            "review_queue_lines": sum(1 for _ in (cfg.pseudo_dir / "review_queue.jsonl").open(
                "r", encoding="utf-8")) if (cfg.pseudo_dir / "review_queue.jsonl").exists() else 0,
        }

        # Review-decisions DB stats for radiologist progress tracking
        try:
            from app.db import get_conn
            with get_conn() as c:
                rows = c.execute(
                    "SELECT status, COUNT(*) AS n FROM review_decisions GROUP BY status"
                ).fetchall()
            out["stages"]["review_decisions"] = {r["status"]: r["n"] for r in rows}
        except Exception:
            pass

        if (cfg.gold_yolo_dir / "dataset.yaml").exists():
            n_train = len(list((cfg.gold_yolo_dir / "labels" / "train").glob("*.txt"))) \
                if (cfg.gold_yolo_dir / "labels" / "train").exists() else 0
            n_val = len(list((cfg.gold_yolo_dir / "labels" / "val").glob("*.txt"))) \
                if (cfg.gold_yolo_dir / "labels" / "val").exists() else 0
            out["stages"]["gold_to_yolo"] = {"train": n_train, "val": n_val}

        json_path = cfg.out_root / "run.summary.json"
        md_path = cfg.out_root / "run.summary.md"
        json_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

        # Human-readable markdown summary
        lines = ["# Pipeline run summary", "", "## Configuration", "```json",
                 json.dumps(out["config"], indent=2), "```", "", "## Stages", ""]
        for name, st in out["stages"].items():
            lines.append(f"### {name}")
            lines.append("```json")
            lines.append(json.dumps(st, indent=2, ensure_ascii=False))
            lines.append("```")
            lines.append("")
        md_path.write_text("\n".join(lines), encoding="utf-8")
        print(f"\n[summary] {json_path}")
        print(f"[summary] {md_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


_STAGES: dict[str, str] = {
    "preprocess":     "stage_preprocess",
    "cbis_convert":   "stage_cbis_convert",
    "train_yolo":     "stage_train_yolo",
    "train_tillnet0": "stage_train_tillnet0",
    "pseudo_labels":  "stage_pseudo_labels",
    "load_review":    "stage_load_review",
    "train_tillnet1": "stage_train_tillnet1",
    "gold_to_yolo":   "stage_gold_to_yolo",
    "train_tillnet2": "stage_train_tillnet2",
    "summarise":      "stage_summarise",
}


def _comma(s: str) -> set[str]:
    return {x.strip() for x in s.split(",") if x.strip()}


def main():
    ap = argparse.ArgumentParser(description="End-to-end mammography research pipeline runner")
    ap.add_argument("--out-root", required=True, help="Where all artifacts will be written")
    ap.add_argument("--local-dicoms", default=None, help="Local DICOM root (recursive)")
    ap.add_argument("--cbis-root", default=None, help="Extracted CBIS-DDSM root folder")
    ap.add_argument("--texts-csv", default=None, help="CSV/JSONL of (filename,text) for TILLNet")
    ap.add_argument("--db", default="app/db.sqlite3", help="SQLite DB for clinical text lookup")
    ap.add_argument("--imgsz", type=int, default=1024)
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--epochs-stage1", type=int, default=100)
    ap.add_argument("--epochs-stage2", type=int, default=30)
    ap.add_argument("--gpu", default="0", help="GPU id (or 'cpu', or '' to omit)")
    ap.add_argument("--yolo-model", default="yolov8m.pt")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--min-pseudo-conf", type=float, default=0.5)
    ap.add_argument("--skip", default="",
                    help=f"Comma-separated stages to skip. Stages: {','.join(_STAGES)}")
    ap.add_argument("--only", default="",
                    help="Comma-separated stages to run (overrides --skip)")
    ap.add_argument("--force", default="",
                    help="Comma-separated stages to re-run even if outputs exist")
    ap.add_argument("--dry-run", action="store_true", help="Print commands without executing")
    args = ap.parse_args()

    cfg = PipelineCfg(
        out_root=Path(args.out_root).resolve(),
        local_dicoms=Path(args.local_dicoms).resolve() if args.local_dicoms else None,
        cbis_root=Path(args.cbis_root).resolve() if args.cbis_root else None,
        texts_csv=Path(args.texts_csv).resolve() if args.texts_csv else None,
        db_path=Path(args.db).resolve(),
        imgsz=args.imgsz, batch=args.batch,
        epochs_stage1=args.epochs_stage1, epochs_stage2=args.epochs_stage2,
        gpu=args.gpu, yolo_model=args.yolo_model, workers=args.workers,
        skip=_comma(args.skip), only=_comma(args.only), force=_comma(args.force),
        dry_run=args.dry_run, min_pseudo_conf=args.min_pseudo_conf,
    )

    bad = (cfg.skip | cfg.only | cfg.force) - set(_STAGES)
    if bad:
        raise SystemExit(f"unknown stage names: {sorted(bad)}; valid: {sorted(_STAGES)}")

    pipeline = Pipeline(cfg)

    print(f"[start] out_root = {cfg.out_root}")
    print(f"        stages   = {list(_STAGES)}")
    if cfg.only:
        print(f"        only     = {sorted(cfg.only)}")
    if cfg.skip:
        print(f"        skip     = {sorted(cfg.skip)}")
    if cfg.force:
        print(f"        force    = {sorted(cfg.force)}")

    n_run = n_skipped = n_failed = 0
    failures: list[tuple[str, str]] = []
    t_global = time.time()
    for name, method_name in _STAGES.items():
        if cfg.only and name not in cfg.only:
            continue
        if name in cfg.skip:
            print(f"\n[skip] {name} (--skip)")
            n_skipped += 1
            continue
        print(f"\n========== STAGE: {name} ==========")
        try:
            getattr(pipeline, method_name)()
            n_run += 1
        except Exception as e:
            print(f"[fail] {name}: {e}")
            failures.append((name, str(e)))
            n_failed += 1
            # Continue downstream stages — they'll skip themselves if their inputs are missing.

    dt = time.time() - t_global
    print(f"\n[summary] ran={n_run}  skipped={n_skipped}  failed={n_failed}  ({dt/60:.1f} min total)")
    if failures:
        print("[failed stages]")
        for name, err in failures:
            print(f"  - {name}: {err}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
