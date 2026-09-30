from contextlib import contextmanager
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import shutil
import threading

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = ROOT / "frontend" / "benchmarks" / "real-house-5"
IMAGES = [BENCHMARK / f"{index:02d}-original.jpg" for index in range(1, 6)]


@contextmanager
def serve_repo():
    class QuietHandler(SimpleHTTPRequestHandler):
        def log_message(self, *_args):
            pass

    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        lambda *args, **kwargs: QuietHandler(*args, directory=ROOT, **kwargs),
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_port
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()


def browser_binary():
    for candidate in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser"):
        path = shutil.which(candidate)
        if path:
            return path
    raise AssertionError("BOLDUNGO-080 browser proof requires Chromium/Chrome")


def wait_saved(page):
    page.wait_for_timeout(450)
    page.evaluate(
        """async () => {
          if (window.boldungoProjectPhotoSavePromise) {
            try { await window.boldungoProjectPhotoSavePromise; } catch {}
          }
        }"""
    )
    page.wait_for_function(
        "() => document.querySelector('#project-save-status')?.textContent === 'Enregistré sur cet appareil'",
        timeout=10000,
    )


def ids_for(page, slot):
    return page.locator(
        f'[data-slot="{slot}"] .persisted-photo-item'
    ).evaluate_all("nodes => nodes.map(node => node.dataset.photoId)")


def set_hidden_value(page, selector, value):
    page.eval_on_selector(
        selector,
        """(el, value) => {
          el.value = value;
          el.dispatchEvent(new Event('input', { bubbles: true }));
          el.dispatchEvent(new Event('change', { bubbles: true }));
        }""",
        value,
    )


def main():
    for image in IMAGES:
        assert image.exists(), image

    with serve_repo() as port, sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            executable_path=browser_binary(),
            args=["--no-sandbox"],
        )
        context = browser.new_context(viewport={"width": 390, "height": 844}, accept_downloads=True)
        page = context.new_page()
        runtime_errors = []
        failed_requests = []
        page.on("pageerror", lambda error: runtime_errors.append(f"pageerror: {error}"))
        page.on(
            "requestfailed",
            lambda request: failed_requests.append(
                f"{request.method} {request.url}: {request.failure}"
            ),
        )

        url = f"http://127.0.0.1:{port}/frontend/photo.html?checkpoint=project-photo-intake-080"
        response = page.goto(url, wait_until="domcontentloaded", timeout=30000)
        assert response and response.ok
        page.wait_for_function(
            "() => document.documentElement.dataset.projectPhotoIntakeReady === 'true'",
            timeout=15000,
        )

        # 080A mobile gate: these are not DOM-only assertions. Every required
        # element must be visually reachable inside the dedicated scrolling area.
        assert page.viewport_size == {"width": 390, "height": 844}
        assert page.locator(".shell-photo-scroll").evaluate(
            "el => ['auto', 'scroll'].includes(getComputedStyle(el).overflowY)"
        )
        assert page.locator(".project-intake-card").is_visible()
        assert page.locator("#shell-primary-button").is_visible()

        def assert_reachable(selector):
            locator = page.locator(selector)
            locator.scroll_into_view_if_needed(timeout=5000)
            page.wait_for_timeout(80)
            geometry = locator.evaluate(
                """el => {
                  const item = el.getBoundingClientRect();
                  const scroller = document.querySelector('.shell-photo-scroll').getBoundingClientRect();
                  const visibleHeight = Math.max(0, Math.min(item.bottom, scroller.bottom) - Math.max(item.top, scroller.top));
                  return {
                    visibleHeight,
                    width: item.width,
                    left: item.left,
                    right: item.right,
                    viewportWidth: window.innerWidth,
                  };
                }"""
            )
            assert geometry["visibleHeight"] >= 40, (selector, geometry)
            assert geometry["width"] > 40, (selector, geometry)
            assert geometry["right"] > 0 and geometry["left"] < geometry["viewportWidth"], (selector, geometry)

        assert_reachable(".project-intake-card")
        for slot in ("front", "right", "left", "rear"):
            assert_reachable(f'[data-slot="{slot}"]')

        scroll_metrics = page.locator(".shell-photo-scroll").evaluate(
            "el => ({scrollHeight: el.scrollHeight, clientHeight: el.clientHeight, scrollTop: el.scrollTop})"
        )
        if scroll_metrics["scrollHeight"] > scroll_metrics["clientHeight"]:
            page.locator('[data-slot="rear"]').scroll_into_view_if_needed()
            page.wait_for_timeout(80)
            assert page.locator(".shell-photo-scroll").evaluate("el => el.scrollTop") > 0

        pdf_box = page.locator("#shell-primary-button").bounding_box()
        assert pdf_box
        assert 0 <= pdf_box["y"] < 844
        assert pdf_box["y"] + pdf_box["height"] <= 844

        page.locator("#project-name").fill("Maison test 080")
        page.locator("#city").fill("Brest")
        set_hidden_value(page, "#known-width", "9.8")
        set_hidden_value(page, "#notes", "Rue montante, dossier persistant.")
        set_hidden_value(page, "#studs", "64")
        set_hidden_value(page, '[data-slot="front"] .guided-photo-note', "note façade avant")
        set_hidden_value(page, '[data-slot="left"] .guided-photo-note', "deux vues trois-quarts côté gauche")
        set_hidden_value(page, '[data-slot="detail_1"] .detail-photo-note', "dessous de terrasse")

        page.locator('[data-slot="front"] .guided-photo-input').set_input_files(str(IMAGES[0]))
        page.locator('[data-slot="left"] .guided-photo-input').set_input_files(
            [str(IMAGES[1]), str(IMAGES[2])]
        )
        page.locator('[data-slot="detail_1"] .detail-photo-input').set_input_files(str(IMAGES[3]))
        wait_saved(page)

        assert ids_for(page, "front") == ["FRONT_001"]
        assert ids_for(page, "left") == ["LEFT_001", "LEFT_002"]
        assert ids_for(page, "detail_1") == ["DETAIL_001"]

        page.reload(wait_until="domcontentloaded", timeout=30000)
        page.wait_for_function(
            "() => document.documentElement.dataset.projectPhotoIntakeReady === 'true'",
            timeout=15000,
        )
        assert page.locator("#project-name").input_value() == "Maison test 080"
        assert page.locator("#city").input_value() == "Brest"
        assert page.locator("#known-width").input_value() == "9.8"
        assert page.locator("#notes").input_value() == "Rue montante, dossier persistant."
        assert page.locator("#studs").input_value() == "64"
        assert page.locator('[data-slot="front"] .guided-photo-note').input_value() == "note façade avant"
        assert page.locator('[data-slot="left"] .guided-photo-note').input_value() == "deux vues trois-quarts côté gauche"
        assert page.locator('[data-slot="detail_1"] .detail-photo-note').input_value() == "dessous de terrasse"
        assert ids_for(page, "front") == ["FRONT_001"]
        assert ids_for(page, "left") == ["LEFT_001", "LEFT_002"]
        assert ids_for(page, "detail_1") == ["DETAIL_001"]
        assert page.locator('[data-slot="front"] .guided-photo-input').evaluate("el => el.files.length") == 0
        assert page.locator('[data-slot="left"] .guided-photo-input').evaluate("el => el.files.length") == 0

        page.locator('[data-delete-photo-id="LEFT_001"]').click()
        wait_saved(page)
        page.reload(wait_until="domcontentloaded", timeout=30000)
        page.wait_for_function(
            "() => document.documentElement.dataset.projectPhotoIntakeReady === 'true'",
            timeout=15000,
        )
        assert ids_for(page, "left") == ["LEFT_002"]

        page.locator('[data-slot="left"] .guided-photo-input').set_input_files(str(IMAGES[4]))
        wait_saved(page)
        assert ids_for(page, "left") == ["LEFT_002", "LEFT_003"]

        page.locator('[data-slot="right"] .guided-photo-input').set_input_files(
            [str(path) for path in IMAGES]
        )
        wait_saved(page)
        assert ids_for(page, "right") == ["RIGHT_001", "RIGHT_002", "RIGHT_003", "RIGHT_004"]

        page.reload(wait_until="domcontentloaded", timeout=30000)
        page.wait_for_function(
            "() => document.documentElement.dataset.projectPhotoIntakeReady === 'true'",
            timeout=15000,
        )
        assert ids_for(page, "right") == ["RIGHT_001", "RIGHT_002", "RIGHT_003", "RIGHT_004"]
        assert "LEFT_001" not in ids_for(page, "left")
        assert ids_for(page, "left") == ["LEFT_002", "LEFT_003"]
        assert page.locator('[data-slot="right"] .guided-photo-input').evaluate("el => el.files.length") == 0

        with page.expect_download(timeout=30000) as download_info:
            page.locator("#shell-primary-button").click(timeout=5000)
        download = download_info.value
        assert download.suggested_filename == "BRICKHOUSE-SURVEY-pdf-handoff-0.10.pdf"
        assert download.failure() is None
        pdf_path = download.path()
        assert pdf_path
        pdf_bytes = Path(pdf_path).read_bytes()
        assert len(pdf_bytes) > 5000
        assert b"FRONT_001" in pdf_bytes
        assert b"PRIMARY_FACE=FRONT" in pdf_bytes
        assert b"Maison test 080" in pdf_bytes
        assert b"Brest" in pdf_bytes
        assert b"CITY = CONTEXTUAL_PRIOR" in pdf_bytes

        assert not runtime_errors, runtime_errors
        assert not failed_requests, failed_requests
        context.close()
        browser.close()

    print("BOLDUNGO-080 project photo intake browser proof passed")


if __name__ == "__main__":
    main()
