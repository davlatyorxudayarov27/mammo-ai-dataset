from __future__ import annotations

import hashlib
import json
import threading
from pathlib import Path
from typing import Iterator

_LOCK = threading.Lock()


def _annot_path(annot_dir: Path, source: str, ref: str) -> Path:
    if source == "upload":
        key = ref
    else:
        key = hashlib.sha1(ref.encode("utf-8")).hexdigest()
    return annot_dir / f"{source}__{key}.json"


def load(annot_dir: Path, source: str, ref: str) -> dict:
    p = _annot_path(annot_dir, source, ref)
    if not p.exists():
        return {"source": source, "ref": ref, "annotations": [], "rows": None, "cols": None}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"source": source, "ref": ref, "annotations": [], "rows": None, "cols": None}
    data.setdefault("source", source)
    data.setdefault("ref", ref)
    data.setdefault("annotations", [])
    return data


def save(annot_dir: Path, source: str, ref: str, payload: dict) -> None:
    p = _annot_path(annot_dir, source, ref)
    annotations = payload.get("annotations", []) or []

    with _LOCK:
        if not annotations:
            if p.exists():
                p.unlink()
            return
        p.parent.mkdir(parents=True, exist_ok=True)
        body = {
            "source": source,
            "ref": ref,
            "rows": payload.get("rows"),
            "cols": payload.get("cols"),
            "annotations": annotations,
        }
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(body, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(p)


def count(annot_dir: Path, source: str, ref: str) -> int:
    p = _annot_path(annot_dir, source, ref)
    if not p.exists():
        return 0
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return len(data.get("annotations", []) or [])
    except Exception:
        return 0


def iter_all(annot_dir: Path) -> Iterator[dict]:
    if not annot_dir.exists():
        return
    for p in sorted(annot_dir.glob("*.json")):
        try:
            yield json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
