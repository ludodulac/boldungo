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
    raise AssertionError("BOLDUNGO-081C browser proof requires Chromium/Chrome")


def wait_project_saved(page):
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


def wait_clarification_saved(page):
    page.evaluate(
        """async () => {
          if (window.boldungoClarificationSavePromise) {
            try { await window.boldungoClarificationSavePromise; } catch {}
          }
        }"""
    )
    page.wait_for_timeout(80)


def project_snapshot(page):
    return page.evaluate(
        """async () => {
          const database = await new Promise((resolve, reject) => {
            const request = indexedDB.open('boldungo-project-photo-intake');
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error || new Error('IndexedDB open failed'));
          });
          const projects = await new Promise((resolve, reject) => {
            const tx = database.transaction('projects', 'readonly');
            const request = tx.objectStore('projects').getAll();
            request.onsuccess = () => resolve(request.result || []);
            request.onerror = () => reject(request.error || new Error('IndexedDB project read failed'));
          });
          database.close();
          return projects.map(project => ({
            project_id: project.project_id,
            project_name: project.project_name,
            clarification_fixture_id: project.clarification_fixture_id || null,
            clarifications: project.clarifications || [],
            human_facts: project.human_facts || [],
          }));
        }"""
    )


def main():
    with serve_repo() as port, sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            executable_path=browser_binary(),
            args=["--no-sandbox"],
        )
        context = browser.new_context(viewport={"width": 390, "height": 844})
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

        url = (
            f"http://127.0.0.1:{port}/frontend/photo.html"
            "?clarification-lab=real-house-5"
        )
        response = page.goto(url, wait_until="domcontentloaded", timeout=30000)
        assert response and response.ok
        page.wait_for_function(
            "() => document.documentElement.dataset.projectPhotoIntakeReady === 'true'",
            timeout=15000,
        )
        page.wait_for_function(
            "() => window.boldungoClarificationLabReady === true",
            timeout=15000,
        )

        lab = page.locator("#clarification-lab")
        assert lab.is_hidden()
        assert page.locator("#project-picker option").count() == 0
        assert lab.get_attribute("data-project-id") in (None, "")

        # Explicit user project creation: LAB must never fabricate one.
        page.locator("#new-project-name").fill("Clarification Projet A")
        page.locator("#confirm-new-project").click()
        wait_project_saved(page)
        project_a = page.locator("#project-picker").input_value()
        page.wait_for_function(
            "(id) => document.querySelector('#clarification-lab')?.dataset.projectId === id",
            arg=project_a,
            timeout=10000,
        )
        wait_clarification_saved(page)
        assert lab.is_visible()
        assert lab.get_attribute("data-fixture-id") == "real-house-5-081"
        assert lab.get_attribute("data-current-clarification-id") == "A01_TARGET_BOUNDARY"
        assert page.locator("#clarification-gate").get_attribute("data-gate") == "BLOCKED"

        # Q1 and Q2 are HUMAN_FACT answers, then A03 becomes current.
        page.locator('[data-clarification-answer="NO"]').click()
        wait_clarification_saved(page)
        page.wait_for_function(
            "() => document.querySelector('#clarification-lab')?.dataset.currentClarificationId === 'A02_CHIMNEY_OWNERSHIP'",
            timeout=10000,
        )
        page.locator('[data-clarification-answer="NONE"]').click()
        wait_clarification_saved(page)
        page.wait_for_function(
            "() => document.querySelector('#clarification-lab')?.dataset.currentClarificationId === 'A03_STAIR_TOPOLOGY'",
            timeout=10000,
        )

        # UNKNOWN is not converted into a business answer and exposes targeted-photo escalation.
        page.locator("#clarification-unknown").click()
        wait_clarification_saved(page)
        assert lab.get_attribute("data-current-clarification-id") == "A03_STAIR_TOPOLOGY"
        assert page.locator("#clarification-request-photo").is_visible()
        assert "JE NE SAIS PAS" in page.locator("#clarification-choices").text_content()
        page.locator("#clarification-request-photo").click()
        wait_clarification_saved(page)
        assert page.locator("#clarification-photo-spec").is_visible()
        assert "Photo demandée" in page.locator("#clarification-photo-spec").text_content()
        assert page.locator("#clarification-gate").get_attribute("data-gate") == "BLOCKED"

        # Reload must restore answers, human facts and PHOTO_REQUESTED.
        page.reload(wait_until="domcontentloaded", timeout=30000)
        page.wait_for_function(
            "() => document.documentElement.dataset.projectPhotoIntakeReady === 'true'",
            timeout=15000,
        )
        page.wait_for_function(
            "(id) => document.querySelector('#clarification-lab')?.dataset.projectId === id",
            arg=project_a,
            timeout=15000,
        )
        assert lab.get_attribute("data-current-clarification-id") == "A03_STAIR_TOPOLOGY"
        assert page.locator("#clarification-photo-spec").is_visible()
        summary = page.locator("#clarification-summary").text_content()
        assert "A01_TARGET_BOUNDARY · NO" in summary
        assert "A02_CHIMNEY_OWNERSHIP · NONE" in summary
        assert "A03_STAIR_TOPOLOGY · PHOTO DEMANDÉE" in summary

        # A second project gets its own fixture state and no copied answers.
        page.locator("#new-project").click()
        page.locator("#new-project-name").fill("Clarification Projet B")
        page.locator("#confirm-new-project").click()
        wait_project_saved(page)
        project_b = page.locator("#project-picker").input_value()
        assert project_b != project_a
        page.wait_for_function(
            "(id) => document.querySelector('#clarification-lab')?.dataset.projectId === id",
            arg=project_b,
            timeout=10000,
        )
        wait_clarification_saved(page)
        assert lab.get_attribute("data-current-clarification-id") == "A01_TARGET_BOUNDARY"
        assert "A01_TARGET_BOUNDARY · NO" not in page.locator("#clarification-summary").text_content()

        # Switching back restores Project A exactly.
        page.locator("#project-picker").select_option(project_a)
        wait_project_saved(page)
        page.wait_for_function(
            "(id) => document.querySelector('#clarification-lab')?.dataset.projectId === id",
            arg=project_a,
            timeout=10000,
        )
        assert lab.get_attribute("data-current-clarification-id") == "A03_STAIR_TOPOLOGY"
        assert page.locator("#clarification-photo-spec").is_visible()

        snapshot = project_snapshot(page)
        records = {record["project_id"]: record for record in snapshot}
        assert set(records) == {project_a, project_b}
        a = records[project_a]
        b = records[project_b]
        assert a["clarification_fixture_id"] == "real-house-5-081"
        assert b["clarification_fixture_id"] == "real-house-5-081"
        assert {fact["clarification_id"] for fact in a["human_facts"]} == {
            "A01_TARGET_BOUNDARY",
            "A02_CHIMNEY_OWNERSHIP",
        }
        assert b["human_facts"] == []
        a03 = next(item for item in a["clarifications"] if item["clarification_id"] == "A03_STAIR_TOPOLOGY")
        b03 = next(item for item in b["clarifications"] if item["clarification_id"] == "A03_STAIR_TOPOLOGY")
        assert a03["answer_state"] == "PHOTO_REQUESTED"
        assert a03["answer"] is None
        assert b03["answer_state"] == "OPEN"

        assert not runtime_errors, runtime_errors
        assert not failed_requests, failed_requests
        context.close()
        browser.close()

    print("BOLDUNGO-081C clarification lab browser proof passed")


if __name__ == "__main__":
    main()
