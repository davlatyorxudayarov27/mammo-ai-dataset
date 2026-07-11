# -*- coding: utf-8 -*-
"""MAMOGRAF — barcha interaktiv asboblarni brauzerda avtomatik sinash.

Har bir asbobni haqiqiy foydalanuvchidek bosib/chizib tekshiradi va
qaysi biri XATO ishlayotganini jadval ko'rinishida chiqaradi.

Ishga tushirish:  set PYTHONIOENCODING=utf-8 && .venv\\Scripts\\python.exe scripts\\test_all_tools.py
Server 8002-portda yoqilgan bo'lishi kerak.
"""
import json
import urllib.request
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8002"
USER, PWD = "demo", "Demo12345!"

results = []          # (asbob, holat, izoh)
console_errors = []
net_errors = []       # (status, url)


def rec(tool, ok, detail=""):
    results.append((tool, "OK " if ok else "XATO", detail))
    print(f"  [{'OK ' if ok else 'XATO'}] {tool}: {detail}")


def get_token():
    r = urllib.request.Request(
        BASE + "/api/auth/login",
        data=json.dumps({"username": USER, "password": PWD}).encode(),
        headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(r, timeout=20).read())["token"]


def n_ann(page):
    return page.evaluate("() => (typeof state!=='undefined' && state.annotations) ? state.annotations.length : -1")


def last_type(page):
    return page.evaluate("() => { if(typeof state==='undefined'||!state.annotations.length) return null; "
                         "return state.annotations[state.annotations.length-1].type; }")


def fresh_rect(page):
    return page.evaluate("""() => { const r=document.getElementById('annoSvg').getBoundingClientRect();
        return {x:r.x, y:r.y, w:r.width, h:r.height}; }""")


def pt(r, fx, fy):
    return r["x"] + r["w"] * fx, r["y"] + r["h"] * fy


def clear_anns(page):
    """Har bir chizish asbobini toza kanvasda sinash uchun — xalalni oldini oladi."""
    page.evaluate("() => { state.annotations = []; state.selectedId = null; "
                  "renderSvg(); renderAnnoList(); }")


def main():
    token = get_token()
    print("Login OK (token injection)")
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": 1600, "height": 1000})
        ctx.add_init_script(f"localStorage.setItem('mamograf_jwt', {json.dumps(token)});")
        ctx.add_init_script(
            "window.__errs=[]; window.addEventListener('error', "
            "e=>window.__errs.push((e.error&&e.error.stack)||e.message));")
        page = ctx.new_page()
        page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: console_errors.append("PAGEERROR: " + str(e)))
        page.on("response", lambda r: net_errors.append((r.status, r.url)) if r.status >= 400 else None)

        page.goto(BASE, wait_until="domcontentloaded")
        page.wait_for_selector("li:has(.anno-pill)", timeout=20000)
        page.click("li:has(.anno-pill)")
        page.wait_for_function(
            "() => typeof state!=='undefined' && state.current && "
            "document.getElementById('dicomImg').naturalWidth > 0", timeout=20000)
        # MUHIM: layout to'liq tayyor bo'lguncha (SVG rect noldan katta) kutamiz
        page.wait_for_function(
            "() => document.getElementById('annoSvg').getBoundingClientRect().width > 50", timeout=20000)
        page.wait_for_timeout(400)
        r = fresh_rect(page)
        print(f"Fayl ochildi | SVG rect w={r['w']:.0f} h={r['h']:.0f} | annotatsiya={n_ann(page)}")

        # ================= INTERAKTIV CHIZISH ASBOBLARI =================

        page.click("#toolSelect")
        rec("Select (tanlash)", page.evaluate("() => state.tool==='select'"), "tool=select")

        # --- BBox (drag) — toza kanvasda ---
        clear_anns(page); page.click("#toolBbox")
        x1, y1 = pt(r, 0.30, 0.30); x2, y2 = pt(r, 0.55, 0.55)
        page.mouse.move(x1, y1); page.mouse.down()
        page.mouse.move((x1+x2)/2, (y1+y2)/2, steps=4)
        page.mouse.move(x2, y2, steps=4); page.mouse.up()
        page.wait_for_timeout(300)
        rec("BBox", n_ann(page) == 1 and last_type(page) == "bbox",
            f"0->{n_ann(page)}, type={last_type(page)}")

        # --- Poly ---
        clear_anns(page); page.click("#toolPoly")
        for fx, fy in [(0.30, 0.30), (0.55, 0.32), (0.45, 0.55)]:
            x, y = pt(r, fx, fy); page.mouse.click(x, y); page.wait_for_timeout(140)
        x, y = pt(r, 0.33, 0.50); page.mouse.dblclick(x, y)
        page.wait_for_timeout(300)
        rec("Poly", n_ann(page) == 1 and last_type(page) == "polygon",
            f"0->{n_ann(page)}, type={last_type(page)}")

        # --- Ruler ---
        clear_anns(page); page.click("#toolRuler")
        for fx, fy in [(0.25, 0.40), (0.55, 0.55)]:
            x, y = pt(r, fx, fy); page.mouse.click(x, y); page.wait_for_timeout(160)
        page.wait_for_timeout(300)
        rec("Ruler", n_ann(page) == 1 and last_type(page) == "ruler",
            f"0->{n_ann(page)}, type={last_type(page)}")

        # --- Angle ---
        clear_anns(page); page.click("#toolAngle")
        for fx, fy in [(0.30, 0.40), (0.55, 0.38), (0.62, 0.62)]:
            x, y = pt(r, fx, fy); page.mouse.click(x, y); page.wait_for_timeout(160)
        page.wait_for_timeout(300)
        rec("Angle", n_ann(page) == 1 and last_type(page) == "angle",
            f"0->{n_ann(page)}, type={last_type(page)}")

        # --- Smart-click (backend flood-fill segmentatsiya) ---
        clear_anns(page); page.click("#toolSmartClick")
        x, y = pt(r, 0.45, 0.45); page.mouse.click(x, y)
        page.wait_for_timeout(5000)
        st = page.evaluate("() => document.getElementById('status') ? document.getElementById('status').textContent : ''")
        rec("Smart-click", n_ann(page) == 1 and last_type(page) == "polygon",
            f"0->{n_ann(page)}, status='{st[:50]}'")
        page.click("#toolSelect")

        # ================= KO'RINISH / W-L ASBOBLARI =================

        page.click("#oneToOneBtn"); page.wait_for_timeout(150)
        sc = page.evaluate("() => state.scale")
        rec("1:1", abs(sc-1.0) < 1e-6, f"scale={sc:.4f}")

        page.click("#fitBtn"); page.wait_for_timeout(150)
        sc = page.evaluate("() => state.scale"); fsc = page.evaluate("() => state.fitScale")
        rec("Fit", abs(sc-fsc) < 1e-3, f"scale={sc:.4f}=fit {fsc:.4f}")

        inv0 = page.evaluate("() => state.invert")
        page.click("#invertBtn"); page.wait_for_timeout(150)
        rec("Invert", page.evaluate("() => state.invert") == (not inv0), f"{inv0}->{not inv0}")
        page.click("#invertBtn")

        # W/L reset
        page.evaluate("() => { state.wc = 9999; state.ww = 9999; }")
        page.click("#resetWlBtn"); page.wait_for_timeout(150)
        rec("W/L reset", page.evaluate("() => state.wc!==9999 && state.ww!==9999"),
            f"wc={page.evaluate('()=>state.wc')}, ww={page.evaluate('()=>state.ww')}")

        # W/L presetlar — har birini sentineldan keyin bosib, o'zgarishini tekshiramiz
        for preset, exp in [("mass", 4000), ("calc", 1200), ("skin", 5000), ("auto", None)]:
            page.evaluate("() => { state.wc = -123; state.ww = 1; }")
            btn = page.query_selector(f'.wl-preset[data-preset="{preset}"]')
            if not btn:
                rec(f"W/L {preset}", False, "tugma topilmadi"); continue
            btn.click(); page.wait_for_timeout(250)
            wc = page.evaluate("() => state.wc"); ww = page.evaluate("() => state.ww")
            ok = wc is not None and wc != -123 and ww and ww > 1
            if exp:  # belgilangan preset uchun aniq qiymat
                ok = ok and ww == exp
            rec(f"W/L {preset}", ok, f"WC={wc}, WW={ww}")

        # 4-view
        fv = page.query_selector("#fourViewBtn")
        if fv:
            h0 = page.evaluate("() => document.getElementById('fourViewGrid').hidden")
            fv.click(); page.wait_for_timeout(1800)
            h1 = page.evaluate("() => document.getElementById('fourViewGrid').hidden")
            rec("4-view", h1 != h0, f"grid hidden {h0}->{h1}")
            if not h1:
                fv.click(); page.wait_for_timeout(300)
        else:
            rec("4-view", False, "tugma topilmadi")

        js_stacks = page.evaluate("() => window.__errs || []")
        b.close()

    print("\n" + "=" * 64)
    print("  ASBOBLAR TEST NATIJASI")
    print("=" * 64)
    bad = [x for x in results if x[1].strip() == "XATO"]
    for tool, st, detail in results:
        print(f"  {st}  {tool:<16} {detail}")
    print("-" * 64)
    print(f"  Jami: {len(results)} | OK: {len(results)-len(bad)} | XATO: {len(bad)}")
    if net_errors:
        uniq = sorted(set(net_errors))
        print(f"\n  Tarmoq xatolari ({len(net_errors)}):")
        for st, url in uniq[:15]:
            print(f"   - {st}  {url}")
    if console_errors:
        print(f"\n  Konsol xatolari ({len(console_errors)}):")
        for e in console_errors[:10]:
            print("   -", e[:160])
    if js_stacks:
        print(f"\n  JS xato STACK'lari ({len(js_stacks)}):")
        for s in js_stacks[:6]:
            print("   -", s[:300].replace("\n", " | "))
    print("=" * 64)


if __name__ == "__main__":
    main()
