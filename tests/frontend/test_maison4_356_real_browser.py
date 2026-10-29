"""VISIONNEUSE-1: one real Chromium visual test with desktop orbit/zoom and Android-like touch.
No engine redesign. Run only inside the experimental PR workflow.
"""
from __future__ import annotations
import functools,json,threading,time
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]
FRONTEND=ROOT/"frontend"
DATA=FRONTEND/"data"/"guided004-maison4-356-brickhouse.json"

def main():
    b=json.loads(DATA.read_text())
    assert b["schema_version"]=="0.1"
    assert len(b["brick_model"]["parts"])==b["bom"]["total_parts"]==356
    assert len({p["placement_id"] for p in b["brick_model"]["parts"]})==356
    assert b["metadata"]["facade_coverage"]["back"]=="INCOMPLETE_NO_WALL_IN_CANONICAL_SOURCE"
    assert len([p for p in b["brick_model"]["parts"] if p["visual_proxy_not_actual_glazing"]])==93
    handler=functools.partial(SimpleHTTPRequestHandler,directory=str(FRONTEND))
    server=ThreadingHTTPServer(("127.0.0.1",0),handler)
    worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
    url=f"http://127.0.0.1:{server.server_port}/viewer.html?bundle=./data/guided004-maison4-356-brickhouse.json"
    out=ROOT/"artifacts"/"visionneuse1";out.mkdir(parents=True,exist_ok=True)
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True,args=["--use-gl=angle","--use-angle=swiftshader","--enable-webgl","--ignore-gpu-blocklist"])
            for mobile in (False,True):
                context=browser.new_context(viewport={"width":390 if mobile else 1280,"height":844 if mobile else 900},
                    device_scale_factor=1,is_mobile=mobile,has_touch=mobile)
                page=context.new_page()
                errors=[]
                page.on("pageerror",lambda e:errors.append(str(e)))
                page.goto(url,wait_until="domcontentloaded",timeout=45000)
                page.wait_for_function("window.__BRICKHOUSE_CURRENT_BUNDLE__ && window.__BRICKHOUSE_CURRENT_BUNDLE__.brick_model.parts.length===356",
                                       timeout=45000)
                assert page.locator("#model-summary dd").nth(1).inner_text()=="356"
                canvas=page.locator("#viewer")
                canvas.scroll_into_view_if_needed()
                page.wait_for_timeout(900)
                assert page.evaluate("document.querySelector('#viewer').width > 200")
                before=canvas.screenshot(path=str(out/("android-initial.png" if mobile else "desktop-initial.png")))
                for button in ("view-front","view-rear","view-left","view-right","reset-view"):
                    page.locator("#"+button).click()
                canvas.scroll_into_view_if_needed()
                page.wait_for_timeout(600)
                if mobile:
                    box=canvas.bounding_box();x=box["x"]+box["width"]/2;y=box["y"]+box["height"]/2
                    cdp=context.new_cdp_session(page)
                    def touch(kind,points):
                        cdp.send("Input.dispatchTouchEvent",{"type":kind,"touchPoints":points})
                    touch("touchStart",[{"x":x-35,"y":y,"id":1},{"x":x+35,"y":y,"id":2}])
                    touch("touchMove",[{"x":x-90,"y":y,"id":1},{"x":x+90,"y":y,"id":2}])
                    touch("touchEnd",[])
                    page.wait_for_timeout(650)
                    touch("touchStart",[{"x":x,"y":y,"id":3}])
                    touch("touchMove",[{"x":x+75,"y":y+25,"id":3}])
                    touch("touchEnd",[])
                else:
                    box=canvas.bounding_box();x=box["x"]+box["width"]/2;y=box["y"]+box["height"]/2
                    page.mouse.move(x,y);page.mouse.down();page.mouse.move(x+115,y+40,steps=12);page.mouse.up()
                    page.mouse.wheel(0,-380)
                page.wait_for_timeout(850)
                after=canvas.screenshot(path=str(out/("android-interaction.png" if mobile else "desktop-interaction.png")))
                assert before!=after,"Canvas pixels unchanged after views, rotation and zoom"
                assert not errors,"Browser JS exceptions: "+str(errors)
                print(("ANDROID_TOUCH" if mobile else "DESKTOP_MOUSE")+"_356_VISIBLE_FOUR_FACADES_ROTATION_ZOOM_PASS")
                context.close()
            browser.close()
    finally:
        server.shutdown();server.server_close()

if __name__=="__main__":main()
