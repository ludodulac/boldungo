"""One existing BOLDÜNGO mobile Chromium viewer, 80-part TOITURE6 experiment.

Visual proxies do NOT certify physical stability, baseplate ground anchoring,
or extra roof integration. Only measured official LDraw reports decide PASS.
"""
import functools,json,threading
from pathlib import Path
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
DIR=ROOT/"missions/TOITURE6"

def main():
    b=json.loads((DIR/"VIEWER-80.json").read_text())
    parts=b["brick_model"]["parts"]
    steps=b["assembly_plan"]["steps"]
    assert len(parts)==80 and len(steps)==80
    assert sum(p["ldraw_ref"]=="3811.dat" for p in parts)==1
    assert sum(p["ldraw_ref"]=="30363.dat" for p in parts)==6
    assert len({p["placement_id"] for p in parts})==80
    assert {p["placement_id"] for p in parts}==set(x for s in steps for x in s["placement_ids"])
    server=ThreadingHTTPServer(("127.0.0.1",0),functools.partial(SimpleHTTPRequestHandler,directory=str(ROOT)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True,args=["--use-gl=angle","--use-angle=swiftshader",
                                                           "--enable-webgl","--ignore-gpu-blocklist"])
            ctx=browser.new_context(viewport={"width":390,"height":844},is_mobile=True,has_touch=True)
            page=ctx.new_page()
            errors=[]
            page.on("pageerror",lambda e:errors.append(str(e)))
            page.goto(f"http://127.0.0.1:{server.server_port}/frontend/viewer.html?bundle=../missions/TOITURE6/VIEWER-80.json",wait_until="domcontentloaded",timeout=60000)
            page.wait_for_function("window.__BRICKHOUSE_CURRENT_BUNDLE__?.assembly_plan?.steps?.length===80",timeout=60000)
            assert page.locator("#model-summary dd").nth(1).inner_text()=="80"
            assert page.locator("#assembly-card").is_visible()
            assert page.locator("#assembly-range").get_attribute("max")=="79"
            # Tour every build step in the existing untouched viewer.
            for i,s in enumerate(steps):
                page.locator("#assembly-range").evaluate(
                  "(e,n)=>{e.value=String(n);e.dispatchEvent(new Event('input',{bubbles:true}))}",i)
                assert s["title"] in page.locator("#assembly-title").inner_text()
            page.locator("#viewer").scroll_into_view_if_needed()
            page.wait_for_timeout(650)
            page.locator("#viewer").screenshot(path=str(DIR/"toiture6-mobile.png"))
            assert not errors,errors
            reportpath=DIR/"RESULTAT.json"
            report=json.loads(reportpath.read_text())
            report["viewer"]="PASS — 80 real LEGO refs, 80 steps, mobile Chromium 390x844 using existing unmodified BOLDÜNGO viewer; visual proxies only"
            reportpath.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
            print("TOITURE6_MOBILE_CHROMIUM_80_PARTS_80_STEPS_PASS",flush=True)
            ctx.close();browser.close()
    finally:
        server.shutdown();server.server_close()

if __name__=="__main__":
    main()
