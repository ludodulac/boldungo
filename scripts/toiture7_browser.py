"""TOITURE7 mobile Chromium on retained 75 exactly (never failed 80).

Schematic viewer success is independent of physical proof and does not
certify the two experimental variants, which remain out of the viewer.
"""
import functools,json,threading
from pathlib import Path
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
DIR=ROOT/"missions/TOITURE7"

def main():
    b=json.loads((DIR/"VIEWER-RETENU.json").read_text())
    parts=b["brick_model"]["parts"]
    steps=b["assembly_plan"]["steps"]
    assert len(parts)==75 and len(steps)==75
    assert len({p["placement_id"] for p in parts})==75
    assert sum(p["ldraw_ref"]=="3811.dat" for p in parts)==1
    assert sum(p["ldraw_ref"]=="30363.dat" for p in parts)==5
    assert {p["placement_id"] for p in parts}=={n for s in steps for n in s["placement_ids"]}
    srv=ThreadingHTTPServer(("127.0.0.1",0),functools.partial(SimpleHTTPRequestHandler,directory=str(ROOT)))
    threading.Thread(target=srv.serve_forever,daemon=True).start()
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True,args=[
                "--use-gl=angle","--use-angle=swiftshader","--enable-webgl","--ignore-gpu-blocklist"])
            ctx=browser.new_context(viewport={"width":390,"height":844},is_mobile=True,has_touch=True)
            page=ctx.new_page()
            errs=[]
            page.on("pageerror",lambda e:errs.append(str(e)))
            page.goto(f"http://127.0.0.1:{srv.server_port}/frontend/viewer.html?bundle=../missions/TOITURE7/VIEWER-RETENU.json",
                wait_until="domcontentloaded",timeout=60000)
            page.wait_for_function(
                "window.__BRICKHOUSE_CURRENT_BUNDLE__?.brick_model?.parts.length===75",timeout=60000)
            assert page.locator("#model-summary dd").nth(1).inner_text()=="75"
            assert page.locator("#assembly-card").is_visible()
            assert page.locator("#assembly-range").get_attribute("max")=="74"
            for i,s in enumerate(steps):
                page.locator("#assembly-range").evaluate(
                    "(el,n)=>{el.value=String(n);el.dispatchEvent(new Event('input',{bubbles:true}))}",i)
                assert s["title"] in page.locator("#assembly-title").inner_text()
                assert f"Étape {i+1}/75" in page.locator("#assembly-progress").inner_text()
            page.locator("#viewer").scroll_into_view_if_needed()
            page.wait_for_timeout(700)
            page.locator("#viewer").screenshot(path=str(DIR/"toiture7-retained-mobile.png"))
            assert not errs,errs
            reportpath=DIR/"RESULTAT.json"
            report=json.loads(reportpath.read_text())
            report["mobile_retained_75"]="PASS: actual mobile Chromium 390x844, EXACT retained 75 pieces, 75 verified assembly UI steps, original BOLDUNGO viewer"
            reportpath.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
            print("TOITURE7_RETAINED_75_MOBILE_CHROMIUM_PASS",flush=True)
            ctx.close();browser.close()
    finally:
        srv.shutdown();srv.server_close()

if __name__=="__main__":
    main()
