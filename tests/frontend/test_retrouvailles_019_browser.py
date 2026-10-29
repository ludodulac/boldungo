"""RETROUVAILLES: one real Chromium browser pass through the pre-existing viewer, no new renderer."""
from __future__ import annotations
from collections import Counter
from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
import json
import threading
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]
FRONTEND=ROOT/"frontend"

def main():
    full=json.loads((FRONTEND/"data/boldungo2-lego-house-019.json").read_text(encoding="utf-8"))
    d=Counter(part.get("component") for part in full["brick_model"]["parts"])
    assert full["bom"]["total_parts"]==len(full["brick_model"]["parts"])==2852
    assert (d["stair_lower"],d["stair_upper"])==(7,9)
    assert d["roof"] and d["gable"] and d["timber_deck"] and d["concrete_platform"]
    assert d["railing_post"] and d["deck_post"] and d["house_chimney"]
    view=(FRONTEND/"viewer.html").read_text()
    home=(FRONTEND/"index.html").read_text()
    for source in (view,home):
        assert "Voir ma maison complète" in source
        assert "Construction LEGO — 356 pièces" in source
    handler=partial(SimpleHTTPRequestHandler,directory=str(FRONTEND))
    srv=ThreadingHTTPServer(("127.0.0.1",0),handler)
    threading.Thread(target=srv.serve_forever,daemon=True).start()
    out=ROOT/"artifacts/retrouvailles";out.mkdir(parents=True,exist_ok=True)
    address=f"http://127.0.0.1:{srv.server_port}/"
    try:
        with sync_playwright() as playwright:
            browser=playwright.chromium.launch(headless=True,args=[
                "--use-gl=angle","--use-angle=swiftshader",
                "--enable-webgl","--ignore-gpu-blocklist"])
            for phone in (False,True):
                ctx=browser.new_context(viewport={"width":390 if phone else 1280,"height":844 if phone else 900},
                    is_mobile=phone,has_touch=phone,device_scale_factor=1)
                page=ctx.new_page()
                errors=[]
                page.on("pageerror",lambda e:errors.append(str(e)))
                page.goto(address+"viewer.html?bundle=./data/boldungo2-lego-house-019.json",wait_until="domcontentloaded",timeout=45000)
                page.wait_for_function(
                    "window.__BRICKHOUSE_CURRENT_BUNDLE__ && window.__BRICKHOUSE_CURRENT_BUNDLE__.brick_model.parts.length===2852",
                    timeout=70000)
                assert page.locator("#model-summary dd").nth(1).inner_text()=="2852"
                canvas=page.locator("#viewer")
                canvas.scroll_into_view_if_needed()
                page.wait_for_timeout(1000)
                assert page.evaluate("document.querySelector('#viewer').width>160")
                initial=canvas.screenshot(path=str(out/("phone-019-initial.png" if phone else "desktop-019-initial.png")))
                for name in ("view-front","view-rear","view-left","view-right","reset-view"):
                    page.locator("#"+name).click(timeout=20000)
                canvas.scroll_into_view_if_needed()
                page.wait_for_timeout(650)
                box=canvas.bounding_box();assert box
                x=box["x"]+box["width"]*.5;y=box["y"]+box["height"]*.5
                if phone:
                    cdp=ctx.new_cdp_session(page)
                    def touch(typ,points):
                        cdp.send("Input.dispatchTouchEvent",{"type":typ,"touchPoints":points})
                    touch("touchStart",[{"x":x-35,"y":y,"id":1},{"x":x+35,"y":y,"id":2}])
                    touch("touchMove",[{"x":x-85,"y":y,"id":1},{"x":x+85,"y":y,"id":2}])
                    touch("touchEnd",[])
                    touch("touchStart",[{"x":x,"y":y,"id":3}])
                    touch("touchMove",[{"x":x+90,"y":y+35,"id":3}])
                    touch("touchEnd",[])
                else:
                    page.mouse.move(x,y);page.mouse.down();page.mouse.move(x+100,y+30,steps=12);page.mouse.up()
                    page.mouse.wheel(0,-400)
                page.wait_for_timeout(750)
                after=canvas.screenshot(path=str(out/("phone-019-interaction.png" if phone else "desktop-019-interaction.png")))
                assert after!=initial,"Viewer canvas unchanged after 4 views + zoom + orbit"
                assert not errors,"Browser JavaScript exception(s): "+str(errors)
                print(("PHONE_TOUCH" if phone else "DESKTOP")+"_COMPLETE_HOUSE_2852_RENDER_4_SIDES_ZOOM_ROTATE_PASS",flush=True)
                ctx.close()
            browser.close()
    finally:
        srv.shutdown();srv.server_close()

if __name__=="__main__":
    main()
