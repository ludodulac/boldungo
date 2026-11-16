"""Real Chromium mobile check of the accessible LDraw project preview, not a physical-build certification."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]
FRONTEND=ROOT/"frontend"

def test_ldraw_mini_roof_renders_in_mobile_chromium():
    page_html=(FRONTEND/"lego-progress.html").read_text(encoding="utf8")
    script=(FRONTEND/"lego-progress.js").read_text(encoding="utf8")
    assert "LDrawLoader" in script and "setPartsLibraryPath" in script
    assert 'aria-label="Visionneuse interactive' in page_html
    for filename,expected in [("toiture.ldr",10),("charpente.ldr",6),("terrasse.ldr",116),("escalier-raccord.ldr",7),("escalier.ldr",1126)]:
        lines=(FRONTEND/"progress"/filename).read_text(encoding="utf8").splitlines()
        assert sum(line.startswith("1 ") for line in lines)==expected,filename
    server=ThreadingHTTPServer(("127.0.0.1",0),partial(SimpleHTTPRequestHandler,directory=str(FRONTEND)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True,args=["--use-gl=angle","--use-angle=swiftshader","--enable-webgl","--ignore-gpu-blocklist"])
            page=browser.new_page(viewport={"width":390,"height":844},device_scale_factor=1,is_mobile=True,has_touch=True)
            errors=[]
            page.on("pageerror",lambda e:errors.append(str(e)))
            page.goto(f"http://127.0.0.1:{server.server_port}/lego-progress.html?mode=toiture",wait_until="domcontentloaded")
            page.wait_for_function("document.querySelector('#loading').hidden === true",timeout=110000)
            assert page.locator("[data-preview=toiture]").get_attribute("aria-pressed")=="true"
            assert "TOITURE M040" in page.locator("#model-description").inner_text()
            assert page.locator("#preview").bounding_box()["height"]>250
            assert not errors,errors
            # Verify switch also loads a second real LDraw model rather than merely changing labels.
            page.locator("[data-preview=charpente]").click()
            page.wait_for_function("document.querySelector('#loading').hidden === true",timeout=110000)
            assert "CHARPENTE M041" in page.locator("#model-description").inner_text()
            assert not errors,errors
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
