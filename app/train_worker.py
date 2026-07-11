"""Alohida training subprocess — Ultralytics YOLO train.

Model Studio'dagi ▶ Train shu skriptni `python -m app.train_worker <params.json>`
ko'rinishida alohida jarayon sifatida ishga tushiradi. Alohida jarayon bo'lgani
uchun uni tashqaridan ⏹ Stop bilan to'xtatib bo'ladi (in-process `m.train()`
da bu imkonsiz edi).

stdout/stderr ota-jarayon (uvicorn) tomonidan log faylga yo'naltiriladi.
Yakuniy holat `<project_dir>/status.json` ga atomik yoziladi — serverning
monitor thread'i va status endpointi shuni o'qiydi.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_status(project_dir: Path, data: dict) -> None:
    """status.json'ni atomik yozish (yarim o'qilmasligi uchun tmp+rename)."""
    project_dir.mkdir(parents=True, exist_ok=True)
    tmp = project_dir / "status.json.tmp"
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(project_dir / "status.json")


def _read_last_metrics(project_dir: Path) -> dict:
    """results.csv'ning oxirgi qatorini metrikalar lug'atiga aylantirish."""
    for csv_path in project_dir.rglob("results.csv"):
        try:
            lines = csv_path.read_text(encoding="utf-8").splitlines()
            if len(lines) >= 2:
                headers = [h.strip() for h in lines[0].split(",")]
                last = [v.strip() for v in lines[-1].split(",")]
                return dict(zip(headers, last))
        except Exception:
            continue
    return {}


def main() -> int:
    if len(sys.argv) < 2:
        print("[worker] xato: params.json yo'li berilmadi", flush=True)
        return 2

    params = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    run_id = params["run_id"]
    project_dir = Path(params["project_dir"])
    models_dir = Path(params["models_dir"])

    status: dict = {
        "run_id": run_id,
        "status": "running",
        "started_at": _now(),
        "pid": os.getpid(),
        "params": params,
    }
    _write_status(project_dir, status)

    print(f"# Run: {run_id}", flush=True)
    print(f"# Started: {status['started_at']}  (pid={os.getpid()})", flush=True)

    # --- train kwargs (main.py'dagi mantiq bilan bir xil) ---
    train_kwargs = dict(
        data=params["data_yaml"],
        epochs=int(params["epochs"]),
        imgsz=int(params["imgsz"]),
        batch=int(params["batch"]),
        optimizer=params.get("optimizer", "auto"),
        lr0=float(params.get("lr0", 0.01)),
        lrf=float(params.get("lrf", 0.01)),
        momentum=float(params.get("momentum", 0.937)),
        weight_decay=float(params.get("weight_decay", 0.0005)),
        warmup_epochs=float(params.get("warmup_epochs", 3.0)),
        patience=int(params.get("patience", 50)),
        seed=int(params.get("seed", 0)),
        cos_lr=bool(params.get("cos_lr", False)),
        pretrained=bool(params.get("pretrained", True)),
        hsv_h=float(params.get("hsv_h", 0.015)),
        hsv_s=float(params.get("hsv_s", 0.7)),
        hsv_v=float(params.get("hsv_v", 0.4)),
        fliplr=float(params.get("fliplr", 0.5)),
        flipud=float(params.get("flipud", 0.0)),
        scale=float(params.get("scale", 0.5)),
        mosaic=float(params.get("mosaic", 1.0)),
        mixup=float(params.get("mixup", 0.0)),
        workers=int(params.get("workers", 4)),
        cache=params.get("cache") if params.get("cache") in ("ram", "disk") else False,
        project=str(project_dir),
        name="train",
        exist_ok=True,
        verbose=True,
    )
    device = params.get("device") or ""
    if device:
        train_kwargs["device"] = device

    resume = params.get("resume")
    if resume:
        last_pt = project_dir.parent / resume / "train" / "weights" / "last.pt"
        if last_pt.exists():
            train_kwargs["resume"] = True
            model_for_train = str(last_pt)
        else:
            status["error_warning"] = f"resume topilmadi: {resume}"
            model_for_train = params["base_model"]
    else:
        model_for_train = params["base_model"]

    print(f"# Base model: {model_for_train}", flush=True)
    print(f"# Kwargs: {json.dumps({k: str(v) for k, v in train_kwargs.items()})}\n", flush=True)

    try:
        from ultralytics import YOLO

        m = YOLO(model_for_train)
        m.train(**train_kwargs)

        # eng yaxshi modelni topish
        best_pt = next(iter(project_dir.rglob("best.pt")), None)
        if best_pt and params.get("deploy_after", True):
            name_suffix = params.get("project_name") or run_id
            safe_suffix = re.sub(r"[^A-Za-z0-9_-]+", "_", name_suffix)
            models_dir.mkdir(parents=True, exist_ok=True)
            target = models_dir / f"trained_{safe_suffix}.pt"
            shutil.copy2(best_pt, target)
            status["model_deployed"] = str(target)
            print(f"\n# Deploy: {target}", flush=True)

        status["best_pt"] = str(best_pt) if best_pt else None
        status["last_metrics"] = _read_last_metrics(project_dir)
        status["status"] = "done"
        status["return_code"] = 0
        print("\n# DONE", flush=True)
    except KeyboardInterrupt:
        status["status"] = "stopped"
        status["error"] = "Foydalanuvchi to'xtatdi (KeyboardInterrupt)"
        status["last_metrics"] = _read_last_metrics(project_dir)
        print("\n# STOPPED (KeyboardInterrupt)", flush=True)
    except Exception as e:  # noqa: BLE001
        status["status"] = "failed"
        status["error"] = f"{type(e).__name__}: {e}"
        status["last_metrics"] = _read_last_metrics(project_dir)
        print(f"\n# FAILED: {type(e).__name__}: {e}", flush=True)

    status["finished_at"] = _now()
    _write_status(project_dir, status)
    return 0 if status["status"] == "done" else 1


if __name__ == "__main__":
    sys.exit(main())
