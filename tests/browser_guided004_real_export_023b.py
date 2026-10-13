"""Real Chromium smoke test of the latest regenerated GUIDED-004 viewer export.

Requires Chrome/Chromium, Playwright and network access to the Three.js CDN.
Failure is reported as failure, never replaced by JSON-only verification.
"""
from contextlib import contextmanager
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import shutil
import threading
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
EXPORT = ROOT / "artifacts/lego2-guided-004/viewer-export.json"


@contextmanager
def server():
    class Quiet(SimpleHTTPRequestHandler):
        def log_message(self, *_args):
            pass
    httpd = ThreadingHTTPServer(("127.0.0.1", 0),
                                lambda *args, **kwargs: Quiet(*args, directory=ROOT, **kwargs))
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield httpd.server_port
    finally:
        httpd.shutdown()
        thread.join(timeout=3)
        httpd.server_close()


def main():
    assert EXPORT.is_file(), "Regenerated real viewer export is missing"
    import json
    expected_count = len(json.loads(EXPORT.read_text(encoding="utf-8"))["brick_model"]["parts"])
    browser_path = next((shutil.which(n) for n in
                         ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser")
                         if shutil.which(n)), None)
    assert browser_path, "A real Chromium binary is required"
    with server() as port, sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=browser_path,
                                             headless=True, args=["--no-sandbox", "--use-gl=angle",
                                                                  "--use-angle=swiftshader",
                                                                  "--enable-webgl"])
        page = browser.new_page(viewport={"width": 1400, "height": 900})
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(f"http://127.0.0.1:{port}/frontend/viewer.html?bundle=../artifacts/lego2-guided-004/viewer-export.json",
                  wait_until="domcontentloaded")
        page.wait_for_function("window.__BRICKHOUSE_CURRENT_BUNDLE__?.brick_model?.parts?.length > 0",
                               timeout=45000)
        actual = page.evaluate("""() => {
          const bundle = window.__BRICKHOUSE_CURRENT_BUNDLE__;
          const canvas = document.querySelector('#viewer');
          return {
            total: bundle.brick_model.parts.length,
            rendered: document.querySelector('#message')?.textContent,
            canvasWidth: canvas.width, canvasHeight: canvas.height,
            categories: [...new Set(bundle.brick_model.parts.map(p => p.category))],
            sourceIds: bundle.brick_model.parts.map(p => p.placement_id),
          };
        }""")
        assert actual["total"] == expected_count, actual
        assert actual["canvasWidth"] > 0 and actual["canvasHeight"] > 0, actual
        assert not errors, errors
        assert "roof_tile" in actual["categories"], actual
        assert any(x.startswith("scene-platform:") for x in actual["sourceIds"]), "No terrace"
        assert "scene-platform:south-timber-deck-main:hidden-cross-plate:00007-00013" in actual["sourceIds"], "Integrated plate missing in rendered viewer bundle"
        assert all("scene-platform:south-timber-deck-main:board:" + n in actual["sourceIds"] for n in ("00001", "00007", "00013")), "Connected terrace boards missing"
        assert len([pid for pid in actual["sourceIds"] if ":hidden-cross-bond-029:" in pid]) == 8, "Eight integrated 029 bonds missing from Chromium viewer"
        assert len([pid for pid in actual["sourceIds"] if pid.startswith("guided004-030b:")]) == 7, "030B real-house cross-joint repairs missing from Chromium viewer"
        assert len([pid for pid in actual["sourceIds"] if pid.startswith("guided004-031:concrete-timber-cross-joint:")]) == 5, "031 concrete/timber physical cross-joint missing in Chromium viewer"
        assert len([pid for pid in actual["sourceIds"] if pid.startswith("guided004-031:house-")]) == 8, "031 two house transition interfaces missing from Chromium viewer"
        assert any(x.startswith("scene-stair:") for x in actual["sourceIds"]), "No stairs"
        assert any(x.startswith("wall-") for x in actual["sourceIds"]), "No walls"
        page.screenshot(path=str(ROOT / "artifacts/lego2-guided-004/viewer-browser.png"))
        print(f"GUIDED004_VIEWER_BROWSER_PASS parts={actual['total']} "
              f"canvas={actual['canvasWidth']}x{actual['canvasHeight']} errors={len(errors)}")
        browser.close()


if __name__ == "__main__":
    main()
