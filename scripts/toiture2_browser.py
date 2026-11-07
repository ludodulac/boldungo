"""One real Chromium phone viewport, three original/replacement roof assembly steps."""
from __future__ import annotations
import functools,json,threading
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
DIR=ROOT/"missions"/"TOITURE2"

def main():
    bundle=json.loads((DIR/"VIEWER-3.json").read_text())
    original_ids=[p["ldraw_ref"] for p in bundle["brick_model"]["parts"]]
    assert original_ids==["3622.dat","3002.dat","30363.dat"]
    assert len(bundle["assembly_plan"]["steps"])==3
    server=ThreadingHTTPServer(("127.0.0.1",0),functools.partial(
        SimpleHTTPRequestHandler,directory=str(ROOT)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    try:
        with sync_playwright() as pw:
            b=pw.chromium.launch(headless=True,args=[
                "--use-gl=angle","--use-angle=swiftshader","--enable-webgl","--ignore-gpu-blocklist"])
            ctx=b.new_context(viewport={"width":390,"height":844},is_mobile=True,has_touch=True)
            page=ctx.new_page()
            errors=[]
            page.on("pageerror",lambda e:errors.append(str(e)))
            page.goto(f"http://127.0.0.1:{server.server_port}/frontend/viewer.html?bundle=../missions/TOITURE2/VIEWER-3.json",wait_until="domcontentloaded",timeout=45000)
            page.wait_for_function("window.__BRICKHOUSE_CURRENT_BUNDLE__?.brick_model?.parts.length===3",timeout=45000)
            assert page.locator("#model-summary dd").nth(1).inner_text()=="3"
            assert page.locator("#assembly-card").is_visible()
            assert page.locator("#assembly-range").get_attribute("max")=="2"
            for i,step in enumerate(bundle["assembly_plan"]["steps"]):
                page.locator("#assembly-range").evaluate(
                    "(e,n)=>{e.value=String(n);e.dispatchEvent(new Event('input',{bubbles:true}))}",i)
                assert step["title"] in page.locator("#assembly-title").inner_text()
                assert f"Étape {i+1}/3" in page.locator("#assembly-progress").inner_text()
            page.locator("#viewer").scroll_into_view_if_needed()
            page.wait_for_timeout(500)
            page.locator("#viewer").screenshot(path=str(DIR/"toiture2-mobile.png"))
            assert not errors,errors
            report_path=DIR/"RESULTAT.json"
            report=json.loads(report_path.read_text())
            report["visualization"]="PASS: real mobile Chromium, exact three references and complete 3-step selection; schematic geometry only"
            report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
            print("TOITURE2_CHROMIUM_VIEWER_3_STEPS_PASS",flush=True)
            ctx.close();b.close()
    finally:
        server.shutdown();server.server_close()

if __name__=="__main__":
    main()
