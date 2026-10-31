"""Existing viewer, one mobile Chromium proof of all ten assembly slider steps."""
from __future__ import annotations
import functools,json,threading
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
D=ROOT/"missions/VALIDATION2"
def main():
    model=json.loads((D/"SEQUENCE-10.json").read_text(encoding="utf-8"))
    steps=model["assembly_plan"]["steps"]
    assert len(steps)==10 and len(model["brick_model"]["parts"])==10
    assert len({x for step in steps for x in step["placement_ids"]})==10
    server=ThreadingHTTPServer(("127.0.0.1",0),functools.partial(SimpleHTTPRequestHandler,directory=str(ROOT)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True,args=["--use-gl=angle","--use-angle=swiftshader",
                                                           "--enable-webgl","--ignore-gpu-blocklist"])
            ctx=browser.new_context(viewport={"width":390,"height":844},is_mobile=True,has_touch=True)
            page=ctx.new_page()
            errors=[]
            page.on("pageerror",lambda err:errors.append(str(err)))
            page.goto(f"http://127.0.0.1:{server.server_port}/frontend/viewer.html?bundle=../missions/VALIDATION2/SEQUENCE-10.json",
                      wait_until="domcontentloaded",timeout=60000)
            page.wait_for_function("window.__BRICKHOUSE_CURRENT_BUNDLE__?.assembly_plan?.steps.length===10",timeout=60000)
            assert page.locator("#model-summary dd").nth(1).inner_text()=="10"
            assert page.locator("#assembly-card").is_visible()
            assert page.locator("#assembly-range").get_attribute("max")=="9"
            for i,step in enumerate(steps):
                page.locator("#assembly-range").evaluate("(e, n)=>{e.value=String(n);e.dispatchEvent(new Event('input',{bubbles:true}))}",i)
                assert step["title"] in page.locator("#assembly-title").inner_text()
                assert f"Étape {i+1}/10" in page.locator("#assembly-progress").inner_text()
            canvas=page.locator("#viewer")
            canvas.scroll_into_view_if_needed()
            page.wait_for_timeout(500)
            canvas.screenshot(path=str(D/"sequence-mobile.png"))
            assert not errors,errors
            report_path=D/"RESULTAT.json"
            report=json.loads(report_path.read_text(encoding="utf-8"))
            report["visualization"]="PASS — 10 successive assembly steps in actual Chromium mobile viewport"
            report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
            print("VALIDATION2_VIEWER_10_STEPS_MOBILE_PASS",flush=True)
            ctx.close();browser.close()
    finally:
        server.shutdown();server.server_close()
if __name__=="__main__":main()
