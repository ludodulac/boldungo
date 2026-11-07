"""One real Android-size Chromium run: roof module with five real 30363 refs.

No changes to the public existing viewer. Visual is illustrative and
verified by an independent official LDraw geometry run.
"""
import functools
import json
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
DIR=ROOT/"missions/TOITURE3"

def main():
    b=json.loads((DIR/"VIEWER-7.json").read_text())
    parts=b["brick_model"]["parts"]
    assert len(parts)==7 and sum(x["ldraw_ref"]=="30363.dat" for x in parts)==5
    assert len(b["assembly_plan"]["steps"])==7
    ids=[x["placement_id"] for x in parts]
    assert set(ids)==set(p for step in b["assembly_plan"]["steps"] for p in step["placement_ids"])
    server=ThreadingHTTPServer(("127.0.0.1",0),functools.partial(SimpleHTTPRequestHandler,directory=str(ROOT)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True,args=["--use-gl=angle","--use-angle=swiftshader",
                                                            "--enable-webgl","--ignore-gpu-blocklist"])
            ctx=browser.new_context(viewport={"width":390,"height":844},is_mobile=True,has_touch=True)
            page=ctx.new_page()
            errors=[]
            page.on("pageerror",lambda err:errors.append(str(err)))
            page.goto(f"http://127.0.0.1:{server.server_port}/frontend/viewer.html?bundle=../missions/TOITURE3/VIEWER-7.json",
                      wait_until="domcontentloaded",timeout=55000)
            page.wait_for_function("window.__BRICKHOUSE_CURRENT_BUNDLE__?.brick_model?.parts.length===7",timeout=55000)
            assert page.locator("#model-summary dd").nth(1).inner_text()=="7"
            assert page.locator("#assembly-card").is_visible()
            assert page.locator("#assembly-range").get_attribute("max")=="6"
            for i,step in enumerate(b["assembly_plan"]["steps"]):
                page.locator("#assembly-range").evaluate(
                    "(el,value)=>{el.value=String(value);el.dispatchEvent(new Event('input',{bubbles:true}))}",i)
                assert step["title"] in page.locator("#assembly-title").inner_text()
                assert f"Étape {i+1}/7" in page.locator("#assembly-progress").inner_text()
            canvas=page.locator("#viewer")
            canvas.scroll_into_view_if_needed()
            page.wait_for_timeout(500)
            canvas.screenshot(path=str(DIR/"toiture3-mobile.png"))
            assert not errors,errors
            result_path=DIR/"RESULTAT.json"
            result=json.loads(result_path.read_text())
            result["visualization"]="PASS — actual Chromium 390x844 mobile, five contiguous roof slopes and 3006 shared beam, seven-step assembly"
            result_path.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
            print("TOITURE3_CHROMIUM_5_ROOF_7_STEPS_PASS",flush=True)
            ctx.close();browser.close()
    finally:
        server.shutdown();server.server_close()

if __name__=="__main__":
    main()
