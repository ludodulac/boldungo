"""VISIONNEUSE-2: one actual mobile Chromium pass for both existing models and their controls."""
from __future__ import annotations
import json
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]
FRONTEND=ROOT/"frontend"

def test_mobile_both_models_status_no_overlay_and_controls():
    view=(FRONTEND/"viewer.html").read_text(encoding="utf-8")
    script=(FRONTEND/"viewer.js").read_text(encoding="utf-8")
    assert 'Repère canonique : avant = y faible' not in view
    assert 'class="viewer-hint"' not in view
    assert 'id="model-kind-status"' in view
    assert 'updateModelKind(b);' in script
    for path,quantity in [
        ("boldungo2-lego-house-019.json",2852),
        ("guided004-maison4-356-brickhouse.json",356),
    ]:
        bundle=json.loads((FRONTEND/"data"/path).read_text())
        assert bundle["bom"]["total_parts"]==len(bundle["brick_model"]["parts"])==quantity
    handler=partial(SimpleHTTPRequestHandler,directory=str(FRONTEND))
    server=ThreadingHTTPServer(("127.0.0.1",0),handler)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    out=ROOT/"artifacts/visionneuse2";out.mkdir(parents=True,exist_ok=True)
    try:
        with sync_playwright() as playwright:
            browser=playwright.chromium.launch(headless=True,args=[
                "--use-gl=angle","--use-angle=swiftshader",
                "--enable-webgl","--ignore-gpu-blocklist"])
            ctx=browser.new_context(viewport={"width":390,"height":844},
                                    is_mobile=True,has_touch=True,device_scale_factor=1)
            page=ctx.new_page()
            errors=[]
            page.on("pageerror",lambda e:errors.append(str(e)))
            base=f"http://127.0.0.1:{server.server_port}/"
            options=[
                ("boldungo2-lego-house-019.json",2852,"visual","Maison complète — modèle visuel approximatif","non certifié LEGO","visual"),
                ("guided004-maison4-356-brickhouse.json",356,"lego","Construction LEGO — 356 pièces","Modèle de travail","lego"),
            ]
            for filename,count,kind,heading,subtitle,suffix in options:
                page.goto(base+"viewer.html?bundle=./data/"+filename,
                          wait_until="domcontentloaded",timeout=45000)
                page.wait_for_function("(n)=>window.__BRICKHOUSE_CURRENT_BUNDLE__?.brick_model?.parts.length===n",
                                      arg=count,timeout=70000)
                banner=page.locator("#model-kind-status")
                assert banner.is_visible(),"Status must be visible on loading "+filename
                assert banner.get_attribute("data-kind")==kind
                assert heading in page.locator("#model-kind-title").inner_text()
                assert subtitle.lower() in page.locator("#model-kind-detail").inner_text().lower()
                assert page.locator("#model-summary dd").nth(1).inner_text()==str(count)
                assert page.locator(".viewer-hint").count()==0
                assert page.locator("#load-guided004-full").count()==1
                assert page.locator("#load-maison4-356").count()==1
                canvas=page.locator("#viewer")
                b=banner.bounding_box();c=canvas.bounding_box()
                assert b and c and b["y"]+b["height"]<=c["y"]+1, "Status must NOT cover image on mobile"
                canvas.scroll_into_view_if_needed()
                page.wait_for_timeout(750)
                initial=canvas.screenshot(path=str(out/(suffix+"-initial.png")))
                for button in ("view-front","view-rear","view-left","view-right","reset-view"):
                    page.locator("#"+button).click()
                canvas.scroll_into_view_if_needed()
                page.wait_for_timeout(300)
                frame=canvas.bounding_box();assert frame
                x=frame["x"]+frame["width"]/2;y=frame["y"]+frame["height"]/2
                cdp=ctx.new_cdp_session(page)
                def touch(kind,points):
                    cdp.send("Input.dispatchTouchEvent",{"type":kind,"touchPoints":points})
                touch("touchStart",[{"x":x-35,"y":y,"id":1},{"x":x+35,"y":y,"id":2}])
                touch("touchMove",[{"x":x-90,"y":y,"id":1},{"x":x+90,"y":y,"id":2}])
                touch("touchEnd",[])
                touch("touchStart",[{"x":x,"y":y,"id":3}])
                touch("touchMove",[{"x":x+75,"y":y+30,"id":3}])
                touch("touchEnd",[])
                page.wait_for_timeout(850)
                after=canvas.screenshot(path=str(out/(suffix+"-touch-zoom.png")))
                assert after!=initial, "Canvas pixels unchanged after four views and mobile gestures"
                assert not errors,"JavaScript browser exceptions: "+str(errors)
                print("VISIONNEUSE2_PHONE_"+suffix.upper()+"_STATUS_NO_OVERLAY_ROTATE_ZOOM_PASS",flush=True)
            ctx.close()
            browser.close()
    finally:
        server.shutdown();server.server_close()
