"""Real phone-size Chromium, existing BOLDÜNGO viewer, three-step roof/support."""
import functools,json,threading
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
D=ROOT/"missions/TOITURE1"
def main():
    b=json.loads((D/"VIEWER-3.json").read_text())
    assert len(b["brick_model"]["parts"])==3
    assert [p["ldraw_ref"] for p in b["brick_model"]["parts"]]==["3622.dat","3622.dat","30363.dat"]
    server=ThreadingHTTPServer(("127.0.0.1",0),functools.partial(SimpleHTTPRequestHandler,directory=str(ROOT)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    try:
        with sync_playwright() as pw:
            br=pw.chromium.launch(headless=True,args=["--use-gl=angle","--use-angle=swiftshader","--enable-webgl","--ignore-gpu-blocklist"])
            ctx=br.new_context(viewport={"width":390,"height":844},is_mobile=True,has_touch=True)
            page=ctx.new_page()
            errors=[]
            page.on("pageerror",lambda e:errors.append(str(e)))
            page.goto(f"http://127.0.0.1:{server.server_port}/frontend/viewer.html?bundle=../missions/TOITURE1/VIEWER-3.json",wait_until="domcontentloaded",timeout=50000)
            page.wait_for_function("window.__BRICKHOUSE_CURRENT_BUNDLE__?.assembly_plan?.steps.length===3",timeout=50000)
            assert page.locator("#model-summary dd").nth(1).inner_text()=="3"
            assert page.locator("#assembly-card").is_visible()
            titles=[x["title"] for x in b["assembly_plan"]["steps"]]
            for i in range(3):
                page.locator("#assembly-range").evaluate("(e,n)=>{e.value=String(n);e.dispatchEvent(new Event('input',{bubbles:true}))}",i)
                assert titles[i] in page.locator("#assembly-title").inner_text()
            canvas=page.locator("#viewer")
            canvas.scroll_into_view_if_needed()
            page.wait_for_timeout(600)
            canvas.screenshot(path=str(D/"roof-mobile.png"))
            assert not errors,errors
            report_path=D/"RESULTAT.json"
            r=json.loads(report_path.read_text())
            r["visualization"]="PASS — original 30363 and two 3622 real LDraw references shown in existing BOLDÜNGO viewer, three steps mobile Chromium"
            report_path.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
            print("TOITURE1_CHROMIUM_3_STEPS_PASS",flush=True)
            ctx.close();br.close()
    finally:
        server.shutdown();server.server_close()
if __name__=="__main__":main()
