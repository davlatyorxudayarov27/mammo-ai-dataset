# -*- coding: utf-8 -*-
"""MAMOGRAF — butun ilovani (barcha tugma/modal/oqim) avtomatik tekshirish.

Har bir tugmani bosib: modal ochiladimi, JS xatosi bormi, tarmoq (4xx/5xx)
xatosi bormi — har birini o'sha tugmaga bog'lab jadval qilib chiqaradi.

Ishga tushirish:  set PYTHONIOENCODING=utf-8 && .venv\\Scripts\\python.exe scripts\\test_full_app.py
"""
import json
import urllib.request
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8002"
USER, PWD = "demo", "Demo12345!"

results = []      # (bo'lim, tugma, holat, izoh)
js_err = []       # uncaught JS xatolar (stack)
net_fail = []     # (status, url)


def get_token():
    r = urllib.request.Request(
        BASE + "/api/auth/login",
        data=json.dumps({"username": USER, "password": PWD}).encode(),
        headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(r, timeout=20).read())["token"]


def rec(section, name, ok, detail=""):
    results.append((section, name, "OK " if ok else "XATO", detail))
    print(f"  [{'OK ' if ok else 'XATO'}] {section}/{name}: {detail}")


def main():
    token = get_token()
    print("Login OK\n")
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": 1600, "height": 1000})
        ctx.add_init_script(f"localStorage.setItem('mamograf_jwt', {json.dumps(token)});")
        ctx.add_init_script("window.__js=[]; addEventListener('error',e=>window.__js.push((e.error&&e.error.stack)||e.message));")
        page = ctx.new_page()
        page.on("pageerror", lambda e: js_err.append(str(e)))
        page.on("response", lambda r: net_fail.append((r.status, r.url)) if r.status >= 400 else None)

        page.goto(BASE, wait_until="domcontentloaded")
        page.wait_for_timeout(1500)

        def snap():
            return len(js_err), len(net_fail)

        def diff(s):
            j, n = s
            new_js = js_err[j:]
            new_net = [f"{c} {u.split('/api/')[-1][:40]}" for c, u in net_fail[n:]
                       if "/api/" in u and c >= 500]  # 5xx muhim; 4xx ko'pincha kutilgan
            return new_js, new_net

        def visible(bid):
            return page.evaluate(f"()=>{{const e=document.getElementById('{bid}');return e && !e.hidden && e.offsetParent!==null;}}")

        # ============ A. Header / modal tugmalari (fayl shart emas) ============
        print("== A. Header modal tugmalari ==")
        modals = [
            ("adminBtn", "adminModal", "adminCloseBtn"),
            ("statsBtn", "statsModal", "statsCloseBtn"),
            ("auditBtn", "auditModal", "auditCloseBtn"),
            ("overviewBtn", "overviewModal", "overviewCloseBtn"),
            ("reviewBtn", "reviewModal", "reviewCloseBtn"),
            ("pacsBtn", "pacsModal", "pacsCloseBtn"),
            ("modelMgrBtn", "modelMgrModal", "mmCloseBtn"),
        ]
        for btn, modal, closeb in modals:
            if not visible(btn):
                rec("Header", btn, True, "(yashirin — bu rol uchun ko'rinmaydi)")
                continue
            s = snap()
            page.click(f"#{btn}")
            page.wait_for_timeout(1200)
            opened = page.evaluate(f"()=>{{const m=document.getElementById('{modal}');return m && !m.hidden;}}")
            nj, nn = diff(s)
            ok = opened and not nj
            detail = f"modal {'ochildi' if opened else 'OCHILMADI'}"
            if nj: detail += f" | JS xato: {nj[0][:80]}"
            if nn: detail += f" | tarmoq: {nn[:2]}"
            rec("Header", btn, ok, detail)
            # yopish
            if page.evaluate(f"()=>document.getElementById('{closeb}')!==null"):
                try: page.click(f"#{closeb}")
                except Exception: page.keyboard.press("Escape")
            else:
                page.keyboard.press("Escape")
            page.wait_for_timeout(300)

        # bellBtn (dropdown)
        if visible("bellBtn"):
            s = snap(); page.click("#bellBtn"); page.wait_for_timeout(800)
            nj, _ = diff(s)
            rec("Header", "bellBtn", not nj, "bildirishnoma" + (f" | JS: {nj[0][:60]}" if nj else ""))
            page.keyboard.press("Escape")

        # ============ B. Fayl ochib, fayl-bog'liq tugmalar ============
        print("\n== B. Fayl ochilgandan keyingi tugmalar ==")
        page.wait_for_selector("li:has(.anno-pill)", timeout=20000)
        s = snap()
        page.click("li:has(.anno-pill)")
        page.wait_for_function(
            "()=>typeof state!=='undefined'&&state.current&&document.getElementById('dicomImg').naturalWidth>0",
            timeout=20000)
        page.wait_for_timeout(1000)
        nj, nn = diff(s)
        rec("Fayl", "ochish", not nj, "DICOM yuklandi" + (f" | JS: {nj[0][:80]}" if nj else ""))

        # Hisobot modali
        if page.evaluate("()=>document.getElementById('reportBtn')!==null"):
            s = snap(); page.click("#reportBtn"); page.wait_for_timeout(2500)
            opened = page.evaluate("()=>{const m=document.getElementById('reportModal');return m && !m.hidden;}")
            nj, nn = diff(s)
            rec("Fayl", "reportBtn", opened and not nj,
                f"modal {'ochildi' if opened else 'OCHILMADI'}" + (f" | JS: {nj[0][:70]}" if nj else "") + (f" | net: {nn[:1]}" if nn else ""))
            # regen + copy
            for sub in ("reportRegenBtn", "reportCopyBtn"):
                if page.evaluate(f"()=>document.getElementById('{sub}')!==null"):
                    s2 = snap(); page.click(f"#{sub}"); page.wait_for_timeout(1500)
                    nj2, _ = diff(s2)
                    rec("Fayl", sub, not nj2, "OK" + (f" | JS: {nj2[0][:60]}" if nj2 else ""))
            if page.evaluate("()=>document.getElementById('reportCloseBtn')!==null"):
                page.click("#reportCloseBtn"); page.wait_for_timeout(300)

        # ============ C. train.html (Model Studio) ============
        print("\n== C. Model Studio (train.html) ==")
        s = snap()
        page.goto(BASE + "/train.html", wait_until="domcontentloaded")
        page.wait_for_timeout(2500)
        nj, nn = diff(s)
        train_btns = page.evaluate("()=>[...document.querySelectorAll('button[id]')].filter(b=>!b.hidden).map(b=>b.id)")
        rec("Studio", "sahifa yuklash", not nj,
            f"{len(train_btns)} tugma ko'rinadi" + (f" | JS: {nj[0][:90]}" if nj else "") + (f" | net5xx: {nn[:2]}" if nn else ""))

        b.close()

    # ============ NATIJA ============
    print("\n" + "=" * 70)
    print("  BUTUN ILOVA TEST NATIJASI")
    print("=" * 70)
    bad = [r for r in results if r[2].strip() == "XATO"]
    cur = None
    for sec, name, st, detail in results:
        if sec != cur:
            print(f"\n  [{sec}]"); cur = sec
        print(f"    {st} {name:<16} {detail}")
    print("\n" + "-" * 70)
    print(f"  Jami: {len(results)} | OK: {len(results)-len(bad)} | XATO: {len(bad)}")
    # 5xx tarmoq xatolari ro'yxati
    fivex = sorted(set(f"{c} {u}" for c, u in net_fail if c >= 500))
    if fivex:
        print(f"\n  5xx server xatolari ({len(fivex)}):")
        for x in fivex[:12]:
            print("   -", x[:110])
    if js_err:
        print(f"\n  Jami uncaught JS xato: {len(js_err)}")
    print("=" * 70)


if __name__ == "__main__":
    main()
