"""One real browser run for 10 actual selected pieces (existing 3D renderer)."""
from pathlib import Path
import json,functools,threading
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
def main():
    root=ROOT
    current=json.loads((root/"missions/VALIDATION1/VIEWER-10.json").read_text())
    assert len(current["brick_model"]["parts"])==10
    assert current["bom"]["total_parts"]==10
    assert len({p["placement_id"] for p in current["brick_model"]["parts"]})==10
    server=ThreadingHTTPServer(("127.0.0.1",0),functools.partial(SimpleHTTPRequestHandler,directory=str(root)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True,args=[
                "--use-gl=angle","--use-angle=swiftshader",
                "--enable-webgl","--ignore-gpu-blocklist"])
            ctx=browser.new_context(viewport={"width":390,"height":844},is_mobile=True,has_touch=True)
            page=ctx.new_page()
            errors=[]
            page.on("pageerror",lambda err:errors.append(str(err)))
            page.goto(f"http://127.0.0.1:{server.server_port}/frontend/viewer.html?bundle=../missions/VALIDATION1/VIEWER-10.json",
                      wait_until="domcontentloaded",timeout=45000)
            page.wait_for_function("window.__BRICKHOUSE_CURRENT_BUNDLE__?.brick_model?.parts.length===10",timeout=45000)
            assert page.locator("#model-summary dd").nth(1).inner_text()=="10"
            canvas=page.locator("#viewer")
            canvas.scroll_into_view_if_needed()
            page.wait_for_timeout(700)
            p=ROOT/"missions/VALIDATION1/visuel-mobile.png"
            before=canvas.screenshot()
            for button in ("view-front","view-rear","view-left","view-right","reset-view"):
                page.locator("#"+button).click()
            canvas.scroll_into_view_if_needed()
            box=canvas.bounding_box()
            x=box["x"]+box["width"]/2;y=box["y"]+box["height"]/2
            cdp=ctx.new_cdp_session(page)
            cdp.send("Input.dispatchTouchEvent",{"type":"touchStart","touchPoints":[
                {"x":x-30,"y":y,"id":1},{"x":x+30,"y":y,"id":2}]})
            cdp.send("Input.dispatchTouchEvent",{"type":"touchMove","touchPoints":[
                {"x":x-90,"y":y,"id":1},{"x":x+90,"y":y,"id":2}]})
            cdp.send("Input.dispatchTouchEvent",{"type":"touchEnd","touchPoints":[]})
            cdp.send("Input.dispatchTouchEvent",{"type":"touchStart","touchPoints":[{"x":x,"y":y,"id":3}]})
            cdp.send("Input.dispatchTouchEvent",{"type":"touchMove","touchPoints":[{"x":x+70,"y":y+25,"id":3}]})
            cdp.send("Input.dispatchTouchEvent",{"type":"touchEnd","touchPoints":[]})
            page.wait_for_timeout(700)
            after=canvas.screenshot(path=str(p))
            assert before!=after and not errors,errors
            report_path=ROOT/"missions/VALIDATION1/RESULTAT.json"
            report=json.loads(report_path.read_text())
            report["visualization"]="PASS (real Chromium Android-like mobile touch, 10 pieces displayed; four views, zoom and orbit)"
            report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
            print("VALIDATION1_VISUAL_10_CHROMIUM_MOBILE_PASS",flush=True)
            ctx.close();browser.close()
    finally:
        server.shutdown();server.server_close()
if __name__=="__main__": main()
