#!/usr/bin/env python3
"""Bulk AI auto-annotatsiya — barcha DICOM'larga 8-klass detektor bilan.

Xavfsizlik kafolatlari:
  * AI belgilar `created_by="ai:8class"` deb teglanadi.
  * Har fayl uchun: mavjud annotatsiyalardan AI BO'LMAGAN (inson) belgilar
    O'ZGARISHSIZ saqlanadi; faqat eski `ai:8class` belgilar yangilanadi (idempotent).
  * ALL_dicom ref'lari inson belgilari (sorted_by_diagnosis ref) dan alohida
    keyspace'da — fizik jihatdan boshqa fayllar. Inson mehnatiga tegilmaydi.

Konteyner ichida ishlaydi:
  docker exec -w /app mamograf-app python /tmp/auto_annotate.py [--limit N] [--conf 0.25]
"""
from __future__ import annotations
import argparse, glob, json, os, time, uuid
from datetime import datetime, timezone
from pathlib import Path

from app import inference, dicom_utils
from app import annotations as annot_store

LOCAL_ROOT = Path(os.environ.get("LOCAL_DICOM_ROOT", "/data/dicom"))
ANNOT_DIR = Path("/app/app/annotations")
SUBTREE = "ALL_dicom"                 # shu shox aylanadi (to'liq to'plam)
AI_TAG = "ai:8class"                  # AI belgilar shu created_by bilan
STATE = Path("/app/app/auto_annotate_state.json")
LOG = Path("/app/app/auto_annotate.log")
# Web monitor uchun — FAQAT raqamlar (bemor yo'llari YO'Q), static'da ochiq servis qilinadi.
# .html kengaytmasi: edge-proxy faqat .html yo'lini ilovaga uzatadi (.json -> SPA fallback).
STATUS_PUB = Path("/app/app/static/auto_annotate_status.html")
STATUS_PUB_JSON = Path("/app/app/static/auto_annotate_status.json")  # backward (lokal)
# Asosiy monitor sahifasi — ma'lumot BEVOSITA ichiga joylanadi (alohida fetch YO'Q).
# .html yo'li edge-proxy orqali ilovaga o'tadi; sahifa har 8s o'zini qayta yuklaydi.
PAGE_PUB = Path("/app/app/static/auto_annotate.html")
_T0 = [time.time()]
_DONE0 = [0]                      # sessiya boshidagi 'done' (resume bazasi)

PAGE_TMPL = """<!doctype html>
<html lang="uz"><head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<meta http-equiv="Cache-Control" content="no-store"/>
<title>AI Auto-annotatsiya — jonli holat</title>
<style>
 :root{color-scheme:light dark}*{box-sizing:border-box}
 body{margin:0;font-family:system-ui,Segoe UI,Roboto,sans-serif;background:#0f1420;color:#e6ebf5;padding:24px}
 @media(prefers-color-scheme:light){body{background:#f4f6fb;color:#1a2233}.card{background:#fff!important}}
 .wrap{max-width:720px;margin:0 auto}h1{font-size:20px;margin:0 0 4px}
 .sub{opacity:.6;font-size:13px;margin-bottom:18px}
 .card{background:#1a2233;border-radius:14px;padding:20px 22px;margin-bottom:16px;box-shadow:0 1px 3px rgba(0,0,0,.2)}
 .bar{height:16px;background:rgba(128,128,128,.2);border-radius:8px;overflow:hidden;margin:10px 0}
 .bar>div{height:100%;background:linear-gradient(90deg,#3b82f6,#22d3ee);transition:width .6s}
 .big{font-size:34px;font-weight:700}
 .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:12px;margin-top:14px}
 .stat{background:rgba(128,128,128,.08);border-radius:10px;padding:12px 14px}
 .stat .n{font-size:22px;font-weight:600}.stat .l{font-size:12px;opacity:.65;margin-top:2px}
 .ok{color:#4ade80}.warn{color:#fca5a5}.muted{opacity:.6}
 .dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:6px}
 .live{background:#4ade80;animation:p 1.6s infinite}.done{background:#60a5fa}.stop{background:#fca5a5}
 @keyframes p{0%{box-shadow:0 0 0 0 rgba(74,222,128,.6)}70%{box-shadow:0 0 0 8px rgba(74,222,128,0)}100%{box-shadow:0 0 0 0 rgba(74,222,128,0)}}
</style></head><body><div class="wrap">
 <h1>&#129302; AI Auto-annotatsiya &mdash; jonli holat</h1>
 <div class="sub">8-klass detektor barcha DICOM'larni belgilaydi &middot; inson belgilariga tegmaydi &middot; har 8 soniyada yangilanadi</div>
 <div class="card">
  <div><span id="dot" class="dot"></span><span id="state"></span></div>
  <div class="big"><span id="pct">0</span>%</div>
  <div class="bar"><div id="fill" style="width:0"></div></div>
  <div class="muted" id="counts"></div>
  <div class="grid">
   <div class="stat"><div class="n ok" id="with_det">0</div><div class="l">belgilangan rasm</div></div>
   <div class="stat"><div class="n" id="dets">0</div><div class="l">deteksiya (AI belgi)</div></div>
   <div class="stat"><div class="n" id="human">0</div><div class="l">inson-fayl (tegilmadi)</div></div>
   <div class="stat"><div class="n muted" id="nopix">0</div><div class="l">rasmsiz (skip)</div></div>
   <div class="stat"><div class="n warn" id="errors">0</div><div class="l">xato</div></div>
   <div class="stat"><div class="n" id="eta">&mdash;</div><div class="l">taxminiy tugash</div></div>
  </div>
 </div>
 <div class="sub" id="updated"></div>
</div>
<script>
 var D=__DATA__;
 function g(i){return document.getElementById(i)}
 g('pct').textContent=(D.percent||0).toFixed(1);
 g('fill').style.width=(D.percent||0)+'%';
 g('counts').textContent=(D.done||0)+' / '+(D.total||0)+" DICOM \\u00b7 "+(D.rate_per_s||0)+' fayl/s';
 g('with_det').textContent=D.with_det||0; g('dets').textContent=D.dets||0;
 g('human').textContent=D.skipped_human||0; g('nopix').textContent=D.skipped_nopix||0;
 g('errors').textContent=D.errors||0;
 g('eta').textContent=(D.eta_min!=null)?(D.eta_min+' daq'):"\\u2014";
 if(D.running){g('dot').className='dot live';g('state').textContent="\\u2699\\ufe0f Ishlayapti"}
 else if((D.percent||0)>=100){g('dot').className='dot done';g('state').textContent="\\u2705 Tugadi"}
 else{g('dot').className='dot stop';g('state').textContent="\\u23f8 To'xtagan"}
 g('updated').textContent='Yangilangan: '+String(D.updated_at||'').replace('T',' ').slice(0,19)+' UTC \\u00b7 ochildi '+new Date().toLocaleTimeString();
 if(D.running){setTimeout(function(){location.replace(location.pathname+'?t='+Date.now())},8000)}
</script></body></html>"""


def log(msg: str) -> None:
    line = f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def write_status(stats: dict, done_n: int, running: bool = True) -> None:
    """Monitor: ma'lumotni sahifa ICHIGA joylab yozadi + backward JSON."""
    tot = max(1, stats.get("total", 1))
    elapsed = time.time() - _T0[0]
    session = max(0, done_n - _DONE0[0])          # shu sessiyada bajarilgan
    rate = session / elapsed if (elapsed > 2 and session > 0) else 0
    remaining = max(0, stats.get("total", 0) - done_n)
    payload = json.dumps({
        "running": running,
        "done": done_n, "total": stats.get("total", 0),
        "percent": round(100 * done_n / tot, 1),
        "with_det": stats.get("with_det", 0), "dets": stats.get("dets", 0),
        "skipped_human": stats.get("skipped_human", 0),
        "skipped_nopix": stats.get("skipped_nopix", 0),
        "errors": stats.get("errors", 0),
        "rate_per_s": round(rate, 2),
        "eta_min": round(remaining / rate / 60, 0) if rate > 0 else None,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    })
    # 1) Asosiy sahifa — ma'lumot ichига joylangan (fetch kerak emas)
    try:
        PAGE_PUB.write_text(PAGE_TMPL.replace("__DATA__", payload), encoding="utf-8")
    except Exception:
        pass
    # 2) Backward: alohida status fayllar (lokal/debug)
    for pth in (STATUS_PUB, STATUS_PUB_JSON):
        try:
            pth.write_text(payload, encoding="utf-8")
        except Exception:
            pass


def run_aggregate(nshard: int) -> None:
    """Shard holatlarини yig'ib bitta monitor sahifasini yozadi (har 4s)."""
    all_files = sorted(glob.glob(str(LOCAL_ROOT / SUBTREE / "**" / "*.dcm"), recursive=True))
    total = len(all_files)
    base_done: set[str] = set()
    base_stats: dict = {}
    if STATE.exists():
        try:
            _s = json.loads(STATE.read_text())
            base_done = set(_s.get("done", []))
            base_stats = _s.get("stats", {}) or {}
        except Exception:
            pass
    _T0[0] = time.time()
    _DONE0[0] = len(base_done)
    log(f"AGGREGATOR: {nshard} shard | total={total} | baseline done={len(base_done)}")
    ticks = 0
    while ticks < 5400:                                   # ~6 soat xavfsizlik chegarasi
        ticks += 1
        done = set(base_done)
        agg = {"total": total, "with_det": 0, "dets": 0,
               "skipped_nopix": 0, "skipped_human": 0, "errors": 0}
        for k in ("with_det", "dets", "skipped_nopix", "skipped_human", "errors"):
            agg[k] += int(base_stats.get(k, 0) or 0)
        seen = finished = 0
        for i in range(nshard):
            sp = Path(f"/app/app/auto_annotate_state.{i}.json")
            if not sp.exists():
                continue
            seen += 1
            try:
                s = json.loads(sp.read_text())
            except Exception:
                continue
            done |= set(s.get("done", []))
            st = s.get("stats", {}) or {}
            for k in ("with_det", "dets", "skipped_nopix", "skipped_human", "errors"):
                agg[k] += int(st.get(k, 0) or 0)
            if s.get("finished"):
                finished += 1
        done_n = len(done)
        all_done = (done_n >= total) or (seen >= nshard and finished >= nshard)
        write_status(agg, done_n, running=not all_done)
        if all_done:
            # global holatga birlashtiramiz (keyingi resume/Phase 2 toza bo'lsin)
            try:
                merged = dict(agg)
                merged["processed"] = done_n
                STATE.write_text(json.dumps({"done": sorted(done), "stats": merged}))
            except Exception:
                pass
            log(f"AGGREGATOR TUGADI: {done_n}/{total}")
            break
        time.sleep(4)


def _dims(path: Path) -> tuple[int | None, int | None]:
    try:
        import pydicom
        ds = pydicom.dcmread(str(path), stop_before_pixels=True, force=True)
        return int(getattr(ds, "Rows", 0)) or None, int(getattr(ds, "Columns", 0)) or None
    except Exception:
        return None, None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="trained_8class_yolo11l.pt")
    ap.add_argument("--conf", type=float, default=0.25)
    ap.add_argument("--imgsz", type=int, default=1024)
    ap.add_argument("--limit", type=int, default=0)      # 0 = barchasi
    ap.add_argument("--threads", type=int, default=4)    # CPU thread (saytga xalaqit bermaslik)
    ap.add_argument("--restart", action="store_true")    # holatni tozalab qaytadan
    ap.add_argument("--shard", type=int, default=0)      # shu jarayon indeksi (0..nshard-1)
    ap.add_argument("--nshard", type=int, default=1)     # jami parallel jarayonlar
    ap.add_argument("--aggregate", action="store_true")  # faqat monitorni yig'ib turadi
    args = ap.parse_args()

    if args.aggregate:
        run_aggregate(args.nshard)
        return

    global LOG                                            # shard uchun alohida log
    if args.nshard > 1:
        LOG = Path(f"/app/app/auto_annotate.{args.shard}.log")
    state_path = Path(f"/app/app/auto_annotate_state.{args.shard}.json") if args.nshard > 1 else STATE
    sharded = args.nshard > 1

    try:
        import torch
        torch.set_num_threads(max(1, args.threads))
    except Exception:
        pass

    all_files = sorted(glob.glob(str(LOCAL_ROOT / SUBTREE / "**" / "*.dcm"), recursive=True))
    if args.limit:
        all_files = all_files[: args.limit]
    # shu shard'ning ulushi (interleaved)
    files = [f for idx, f in enumerate(all_files) if idx % args.nshard == args.shard]

    # Skip-set: (1) global bosqichда bajarilgan (avvalgi bitta-job) + (2) shu shard resume
    skip: set[str] = set()
    if STATE.exists() and not args.restart:                # global baseline
        try:
            skip |= set(json.loads(STATE.read_text()).get("done", []))
        except Exception:
            pass
    done: set[str] = set()                                 # shu shard yangi bajargani
    saved_stats: dict = {}
    if sharded and state_path.exists() and not args.restart:
        try:
            _st = json.loads(state_path.read_text())
            done = set(_st.get("done", []))
            saved_stats = dict(_st.get("stats") or {})
        except Exception:
            done, saved_stats = set(), {}
    elif not sharded and STATE.exists() and not args.restart:
        try:
            _st = json.loads(STATE.read_text())
            done = set(_st.get("done", []))
            saved_stats = dict(_st.get("stats") or {})
        except Exception:
            done, saved_stats = set(), {}

    now = datetime.now(timezone.utc).isoformat()
    stats = {"total": len(files), "processed": 0, "with_det": 0, "dets": 0,
             "skipped_done": 0, "skipped_nopix": 0, "skipped_human": 0, "errors": 0}
    # Cumulative hisoblagichlarni oldingi sessiyadan tiklaymiz (monitor to'g'ri ko'rsatsin)
    for k in ("with_det", "dets", "skipped_nopix", "skipped_human", "errors"):
        if isinstance(saved_stats.get(k), int):
            stats[k] = saved_stats[k]
    log(f"BOSHLANDI: {len(files)} DICOM | model={args.model} conf={args.conf} "
        f"(oldin bajarilgan: {len(done)})")

    t0 = time.time()
    _T0[0] = t0
    _DONE0[0] = len(done)
    write_status(stats, len(done), running=True)
    for i, fp in enumerate(files, 1):
        path = Path(fp)
        ref = str(path.relative_to(LOCAL_ROOT))
        if ref in skip or ref in done:
            stats["skipped_done"] += 1
            continue
        # INSON belgisi bor faylni UMUMAN tegmaymiz (ochib ham yozmaymiz).
        existing = annot_store.load(ANNOT_DIR, "local", ref)
        old = list(existing.get("annotations") or [])
        human = [a for a in old if str(a.get("created_by", "")) != AI_TAG]
        if human:
            stats["skipped_human"] += 1
            done.add(ref)
            continue

        try:
            png = dicom_utils.render_frame_png(path, frame=0, max_dim=args.imgsz)
        except Exception as e:
            if "no pixel" in str(e).lower() or "SR" in str(e):
                stats["skipped_nopix"] += 1
            else:
                stats["errors"] += 1
            done.add(ref)
            continue
        try:
            res = inference.infer_png(png, args.model, conf=args.conf, imgsz=args.imgsz)
            dets = res.get("detections") or []
        except Exception:
            stats["errors"] += 1
            done.add(ref)
            continue

        ai_anns = []
        for d in dets:
            lbl = d.get("label") or "mass"
            ai_anns.append({
                "id": uuid.uuid4().hex, "type": "bbox", "label": lbl,
                "bi_rads": "", "frame": 0, "bbox": d["bbox"],
                "note": f"AI: {lbl} {d.get('confidence', 0)*100:.1f}%",
                "ai_source": {"label": lbl, "confidence": d.get("confidence"),
                              "class_id": d.get("class_id"), "model": args.model},
                "status": "draft", "created_by": AI_TAG,
                "created_at": now, "updated_by": AI_TAG, "updated_at": now,
            })

        # Bu fayl bo'sh yoki faqat-AI (inson yo'q) — AI belgilarni yozamiz/yangilaymiz.
        if ai_anns:
            rows, cols = existing.get("rows"), existing.get("cols")
            if rows is None or cols is None:
                rows, cols = _dims(path)
            annot_store.save(ANNOT_DIR, "local", ref, {
                "source": "local", "ref": ref, "rows": rows, "cols": cols,
                "annotations": ai_anns,
            })
            stats["with_det"] += 1
            stats["dets"] += len(ai_anns)
        stats["processed"] += 1
        done.add(ref)

        if i % 20 == 0:
            if not sharded:                   # bitta-job: sahifani o'zi yozadi
                write_status(stats, len(done), running=True)
            else:                             # shard: faqat o'z holatini yozadi (aggregator sahifani yig'adi)
                state_path.write_text(json.dumps({"done": sorted(done), "stats": stats, "finished": False}))
        if i % 100 == 0:
            rate = i / max(1e-6, time.time() - t0)
            eta = (len(files) - i) / max(1e-6, rate) / 60
            log(f"{i}/{len(files)} | belgilangan={stats['with_det']} "
                f"det={stats['dets']} nopix={stats['skipped_nopix']} xato={stats['errors']} "
                f"| {rate:.1f} f/s ETA {eta:.0f} daq")
            state_path.write_text(json.dumps({"done": sorted(done), "stats": stats, "finished": False}))

    state_path.write_text(json.dumps({"done": sorted(done), "stats": stats, "finished": True}))
    if not sharded:
        write_status(stats, len(done), running=False)
    log(f"TUGADI: {stats}")


if __name__ == "__main__":
    main()
