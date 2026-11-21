"""TOITURE-5: existing BOLDÜNGO viewer, 43 original wall-to-roof pieces, mobile Chromium.

The visual is schematic. Strict geometric evidence is provided by the
pinned LDraw engine in separate JSON reports; this never certifies actual
mechanical strength or foundation.
"""
from __future__ import annotations
import functools
import json
import threading
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
DIR=ROOT/"missions/TOITURE5"

def main():
    bundle=json.loads((DIR/"VIEWER-43.json").read_text())
    all_parts=bundle["brick_model"]["parts"]
    plan=bundle["assembly_plan"]["steps"]
    assert len(all_parts)==43 and len(plan)==43
    assert sum(p["ldraw_ref"]=="3008.dat" for p in all_parts)==35
    assert sum(p["ldraw_ref"]=="30363.dat" for p in all_parts)==5
    assert len({p["placement_id"] for p in all_parts})==43
    assert len({x for item in plan for x in item["placement_ids"]})==43
    server=ThreadingHTTPServer(("127.0.0.1",0),functools.partial(SimpleHTTPRequestHandler,directory=str(ROOT)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True,args=[
                "--use-gl=angle","--use-angle=swiftshader",
                "--enable-webgl","--ignore-gpu-blocklist"])
            ctx=browser.new_context(viewport={"width":390,"height":844},is_mobile=True,has_touch=True)
            page=ctx.new_page()
            errors=[]
            page.on("pageerror",lambda error:errors.append(str(error)))
            page.goto(f"http://127.0.0.1:{server.server_port}/frontend/viewer.html?bundle=../missions/TOITURE5/VIEWER-43.json",
                      wait_until="domcontentloaded",timeout=60000)
            page.wait_for_function("window.__BRICKHOUSE_CURRENT_BUNDLE__?.assembly_plan?.steps?.length===43",timeout=60000)
            assert page.locator("#model-summary dd").nth(1).inner_text()=="43"
            assert page.locator("#assembly-card").is_visible()
            assert page.locator("#assembly-range").get_attribute("max")=="42"
            for i,item in enumerate(plan):
                page.locator("#assembly-range").evaluate(
                    "(el,n)=>{el.value=String(n);el.dispatchEvent(new Event('input',{bubbles:true}))}",i)
                assert item["title"] in page.locator("#assembly-title").inner_text()
                assert f"Étape {i+1}/43" in page.locator("#assembly-progress").inner_text()
            canvas=page.locator("#viewer")
            canvas.scroll_into_view_if_needed()
            page.wait_for_timeout(750)
            canvas.screenshot(path=str(DIR/"toiture5-mobile.png"))
            assert not errors,errors
            report_path=DIR/"RESULTAT.json"
            result=json.loads(report_path.read_text())
            result["visualization"]="PASS: real mobile Chromium, 43 pieces, 31 B3 wall courses, five original roof slopes, 43 assembly steps"
            report_path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
            print("TOITURE5_CHROMIUM_WALL_31_ROOF_5_STEPS_43_PASS",flush=True)
            ctx.close();browser.close()
    finally:
        server.shutdown();server.server_close()

if __name__=="__main__":
    main()
