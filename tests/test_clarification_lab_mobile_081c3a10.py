from contextlib import contextmanager
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import shutil
import threading

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]


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
    raise AssertionError("BOLDUNGO-081C3A10 browser proof requires Chromium/Chrome")


def wait_project_and_lab_ready(page):
    page.wait_for_function(
        "() => document.documentElement.dataset.projectPhotoIntakeReady === 'true'",
        timeout=15000,
    )
    page.wait_for_function(
        "() => window.boldungoClarificationLabReady === true",
        timeout=15000,
    )


def wait_saved(page):
    page.evaluate(
        """async () => {
          if (window.boldungoProjectPhotoSavePromise) {
            await window.boldungoProjectPhotoSavePromise;
          }
        }"""
    )
    page.wait_for_function(
        "() => document.querySelector('#project-save-status')?.textContent === 'Enregistré sur cet appareil'",
        timeout=10000,
    )


def visual_geometry(page, selector):
    locator = page.locator(selector)
    locator.scroll_into_view_if_needed(timeout=5000)
    page.wait_for_timeout(60)
    return locator.evaluate(
        """el => {
          const item = el.getBoundingClientRect();
          const scrollerNode = document.querySelector('.shell-photo-scroll');
          const scroller = scrollerNode.getBoundingClientRect();
          const visibleHeight = Math.max(
            0,
            Math.min(item.bottom, scroller.bottom) - Math.max(item.top, scroller.top),
          );
          const visibleWidth = Math.max(
            0,
            Math.min(item.right, scroller.right) - Math.max(item.left, scroller.left),
          );
          return {
            insideScroller: scrollerNode.contains(el),
            itemHeight: item.height,
            itemWidth: item.width,
            visibleHeight,
            visibleWidth,
            itemTop: item.top,
            itemBottom: item.bottom,
            scrollerTop: scroller.top,
            scrollerBottom: scroller.bottom,
          };
        }"""
    )


def assert_reachable(page, selector, min_visible_height=40):
    locator = page.locator(selector)
    assert locator.is_visible(), selector
    geometry = visual_geometry(page, selector)
    assert geometry["insideScroller"], (selector, geometry)
    assert geometry["itemHeight"] > 0, (selector, geometry)
    assert geometry["itemWidth"] > 40, (selector, geometry)
    assert geometry["visibleHeight"] >= min_visible_height, (selector, geometry)
    assert geometry["visibleWidth"] > 40, (selector, geometry)


def test_clarification_lab_mobile_project_creation_is_visually_reachable_and_loads_first_question():
    with serve_repo() as port, sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            executable_path=browser_binary(),
            args=["--no-sandbox"],
        )
        context = browser.new_context(viewport={"width": 390, "height": 844})
        page = context.new_page()

        url = f"http://127.0.0.1:{port}/frontend/photo.html?clarification-lab=real-house-5"
        response = page.goto(url, wait_until="domcontentloaded", timeout=30000)
        assert response and response.ok
        wait_project_and_lab_ready(page)

        assert page.viewport_size == {"width": 390, "height": 844}
        assert page.locator(".shell-photo-scroll").evaluate(
            "el => ['auto', 'scroll'].includes(getComputedStyle(el).overflowY)"
        )

        # Case A — no project: prove real visible/reachable geometry, not DOM presence only.
        assert page.locator("#project-picker option").count() == 0
        assert page.locator(".project-intake-card").is_visible()
        assert page.locator("#project-create-panel").is_visible()
        assert page.locator(".project-intake-heading small").is_visible()
        assert page.locator("#project-save-status").is_visible()

        assert_reachable(page, ".project-intake-card")
        assert_reachable(page, "#project-create-panel")
        assert_reachable(page, "#new-project-name")
        assert_reachable(page, "#confirm-new-project")

        subtitle_geometry = visual_geometry(page, ".project-intake-heading small")
        status_geometry = visual_geometry(page, "#project-save-status")
        assert subtitle_geometry["visibleHeight"] > 0, subtitle_geometry
        assert status_geometry["visibleHeight"] > 0, status_geometry

        assert "Aucun projet actif" in page.locator("#clarification-project").text_content()
        assert "En attente d’un projet utilisateur." in page.locator("#clarification-question").text_content()

        # Case B — create a real project through the visible controls.
        page.locator("#new-project-name").fill("Maison test LAB")
        page.locator("#confirm-new-project").click()
        wait_saved(page)

        page.wait_for_function(
            "() => document.querySelector('.project-intake-card')?.dataset.projectMode === 'active'",
            timeout=10000,
        )
        page.wait_for_function(
            "() => document.querySelector('#clarification-lab')?.dataset.projectId",
            timeout=10000,
        )
        page.wait_for_function(
            "() => document.querySelector('#clarification-lab')?.dataset.currentClarificationId",
            timeout=10000,
        )

        assert page.locator("#project-existing-controls").is_visible()
        assert_reachable(page, "#project-existing-controls")
        assert_reachable(page, "#project-name")
        assert page.locator("#project-name").input_value() == "Maison test LAB"
        assert page.locator("#project-picker option").all_text_contents() == ["Maison test LAB"]

        assert "Maison test LAB" in page.locator("#clarification-project").text_content()
        assert "En attente d’un projet utilisateur." not in page.locator("#clarification-question").text_content()
        assert page.locator("#clarification-lab").get_attribute("data-current-clarification-id")
        first_question = page.locator("#clarification-question").text_content().strip()
        assert first_question
        assert first_question != "Aucune question active."

        context.close()
        browser.close()
