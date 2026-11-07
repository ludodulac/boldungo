"""Use BOLDÜNGO's existing viewer, 13 steps, five original B3 roof pieces.

Visual proxies are explicitly not the official meshes used for validation.
One real mobile Chromium execution, no edit to frontend.
"""
from __future__ import annotations
import functools,json,threading
from pathlib import Path
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
D=ROOT/"missions/TOITURE4"

def main():
    model=json.loads((D/"VIEWER-12.json").read_text())
    parts=model["brick_model"]["parts"]
    steps=model["assembly_plan"]["steps"]
    assert len(parts)==13 and len(steps)==13
    assert sum(p["ldraw_ref"]=="30363.dat" for p in parts)==5
    assert sum(p["source_annotation"].startswith("TOITURE4-NEW") for p in parts)==2
    assert set(x["placement_id"] for x in parts)==set(s["placement_ids"][0] for s in steps)
    server=ThreadingHTTPServer(("127.0.0.1",0),functools.partial(SimpleHTTPRequestHandler,directory=str(ROOT)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True,args=[
              "--use-gl=angle","--use-angle=swiftshader","--enable-webgl","--ignore-gpu-blocklist"])
            context=browser.new_context(viewport={"width":390,"height":844},is_mobile=True,has_touch=True)
            page=context.new_page();errors=[]
            page.on("pageerror",lambda err:errors.append(str(err)))
            page.goto(f"http://127.0.0.1:{server.server_port}/frontend/viewer.html?bundle=../missions/TOITURE4/VIEWER-12.json",
                      wait_until="domcontentloaded",timeout=55000)
            page.wait_for_function("window.__BRICKHOUSE_CURRENT_BUNDLE__?.brick_model?.parts.length===13",timeout=55000)
            assert page.locator("#model-summary dd").nth(1).inner_text()=="13"
            assert page.locator("#assembly-card").is_visible()
            assert page.locator("#assembly-range").get_attribute("max")=="12"
            for i,step in enumerate(steps):
                page.locator("#assembly-range").evaluate(
                    "(e,n)=>{e.value=String(n);e.dispatchEvent(new Event('input',{bubbles:true}))}",i)
                assert step["title"] in page.locator("#assembly-title").inner_text()
                assert f"Étape {i+1}/13" in page.locator("#assembly-progress").inner_text()
            canvas=page.locator("#viewer");canvas.scroll_into_view_if_needed()
            page.wait_for_timeout(650)
            canvas.screenshot(path=str(D/"toiture4-mobile.png"))
            assert not errors,errors
            path=D/"RESULTAT.json"
            report=json.loads(path.read_text())
            report["visualization"]="PASS — 13-step existing BOLDÜNGO viewer, five original roof slopes, original B3 gables and one wall, real Chromium mobile"
            path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
            print("TOITURE4_CHROMIUM_13_STEPS_PASS",flush=True)
            context.close();browser.close()
    finally:
        server.shutdown();server.server_close()
if __name__=="__main__":main()
