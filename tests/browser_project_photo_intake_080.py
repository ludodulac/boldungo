from contextlib import contextmanager
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
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


def collect_first_photo_save_diagnostic(page, runtime_errors, console_errors):
    diagnostic = page.evaluate(
        """async () => {
          const slotState = (slotName, inputSelector) => {
            const slot = document.querySelector(`[data-slot="${slotName}"]`);
            const input = slot?.querySelector(inputSelector) || null;
            return {
              input_files_length: input?.files?.length ?? null,
              dom_persisted_ids: slot
                ? [...slot.querySelectorAll('.persisted-photo-item')].map(node => node.dataset.photoId)
                : [],
              selected_preview_count: slot?.querySelectorAll('.selected-photo-preview').length ?? 0,
            };
          };

          const idbSnapshot = async () => {
            try {
              const database = await new Promise((resolve, reject) => {
                const request = indexedDB.open('boldungo-project-photo-intake');
                request.onsuccess = () => resolve(request.result);
                request.onerror = () => reject(request.error || new Error('IndexedDB open failed'));
              });

              const readAll = storeName => new Promise((resolve, reject) => {
                const transaction = database.transaction(storeName, 'readonly');
                const request = transaction.objectStore(storeName).getAll();
                request.onsuccess = () => resolve(request.result || []);
                request.onerror = () => reject(request.error || new Error(`IndexedDB read failed: ${storeName}`));
              });

              const [projects, photos, settings] = await Promise.all([
                readAll('projects'),
                readAll('photos_v2'),
                readAll('settings'),
              ]);
              database.close();

              return {
                PROJECT_RECORDS: projects.map(project => ({
                  project_id: project.project_id,
                  project_name: project.project_name,
                  photo_id_counters: project.photo_id_counters,
                })),
                PHOTO_RECORDS: photos.map(photo => ({
                  project_id: photo.project_id,
                  photo_id: photo.photo_id,
                  primary_face: photo.primary_face,
                  detail_group_id: photo.detail_group_id,
                  original_filename: photo.original_filename,
                  capture_order: photo.capture_order,
                })),
                SETTINGS_RECORDS: settings,
              };
            } catch (error) {
              return {
                PROJECT_RECORDS: [],
                PHOTO_RECORDS: [],
                SETTINGS_RECORDS: [],
                INDEXEDDB_DIAGNOSTIC_ERROR: String(error?.stack || error),
              };
            }
          };

          const front = slotState('front', '.guided-photo-input');
          const left = slotState('left', '.guided-photo-input');
          const detail1 = slotState('detail_1', '.detail-photo-input');
          const indexedDb = await idbSnapshot();

          return {
            PROJECT_SAVE_STATUS: document.querySelector('#project-save-status')?.textContent?.trim() ?? null,
            PROJECT_NAME_FIELD: document.querySelector('#project-name')?.value ?? null,
            PROJECT_PICKER_VALUE: document.querySelector('#project-picker')?.value ?? null,
            PROJECT_PICKER_OPTIONS: [...document.querySelectorAll('#project-picker option')].map(option => ({
              value: option.value,
              text: option.textContent,
            })),
            WINDOW_SAVE_PROMISE_PRESENT: Boolean(window.boldungoProjectPhotoSavePromise),
            FRONT_INPUT_FILES_LENGTH: front.input_files_length,
            LEFT_INPUT_FILES_LENGTH: left.input_files_length,
            DETAIL_1_INPUT_FILES_LENGTH: detail1.input_files_length,
            FRONT_DOM_PERSISTED_IDS: front.dom_persisted_ids,
            LEFT_DOM_PERSISTED_IDS: left.dom_persisted_ids,
            DETAIL_1_DOM_PERSISTED_IDS: detail1.dom_persisted_ids,
            FRONT_SELECTED_PREVIEW_COUNT: front.selected_preview_count,
            LEFT_SELECTED_PREVIEW_COUNT: left.selected_preview_count,
            DETAIL_1_SELECTED_PREVIEW_COUNT: detail1.selected_preview_count,
            ...indexedDb,
          };
        }"""
    )
    diagnostic["PAGE_ERRORS"] = list(runtime_errors)
    diagnostic["CONSOLE_ERRORS"] = list(console_errors)
    return diagnostic


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
        console_errors = []
        failed_requests = []
        page.on("pageerror", lambda error: runtime_errors.append(f"pageerror: {error}"))
        page.on(
            "console",
            lambda message: console_errors.append(message.text)
            if message.type == "error"
            else None,
        )
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

        zip_box = page.locator("#shell-primary-button").bounding_box()
        assert zip_box
        assert 0 <= zip_box["y"] < 844
        assert zip_box["y"] + zip_box["height"] <= 844

        # 080B: fresh browser state must not silently create "Ma maison".
        assert page.locator("#project-create-panel").is_visible()
        assert page.locator("#project-create-label").text_content().strip() == "Nom du projet"
        assert page.locator("#project-picker option").count() == 0

        page.locator("#new-project-name").fill("Maison Brest")
        page.locator("#confirm-new-project").click()
        wait_saved(page)
        assert page.locator("#project-name").input_value() == "Maison Brest"
        assert page.locator("#project-picker option").all_text_contents() == ["Maison Brest"]
        brest_project_id = page.locator("#project-picker").input_value()

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

        first_photo_ids = {
            "front": ids_for(page, "front"),
            "left": ids_for(page, "left"),
            "detail_1": ids_for(page, "detail_1"),
        }
        if first_photo_ids != {
            "front": ["FRONT_001"],
            "left": ["LEFT_001", "LEFT_002"],
            "detail_1": ["DETAIL_001"],
        }:
            diagnostic = collect_first_photo_save_diagnostic(
                page, runtime_errors, console_errors
            )
            print("BOLDUNGO_080G_RUNTIME_DIAGNOSTIC")
            print(json.dumps(diagnostic, indent=2, sort_keys=True))

        assert ids_for(page, "front") == ["FRONT_001"]
        assert ids_for(page, "left") == ["LEFT_001", "LEFT_002"]
        assert ids_for(page, "detail_1") == ["DETAIL_001"]
        assert page.locator('[data-photo-id="FRONT_001"] small').text_content().strip() == IMAGES[0].name
        assert page.locator('[data-slot="front"] .guided-photo-input').evaluate("el => el.files.length") == 0
        assert page.locator('[data-slot="left"] .guided-photo-input').evaluate("el => el.files.length") == 0
        assert page.locator('[data-slot="detail_1"] .detail-photo-input').evaluate("el => el.files.length") == 0
        assert page.locator('[data-slot="front"] .selected-photo-preview').count() == 0
        assert page.locator('[data-slot="left"] .selected-photo-preview').count() == 0
        assert page.locator('[data-slot="detail_1"] .selected-photo-preview').count() == 0

        # Reload: project name, metadata, IDs and photos survive.
        page.reload(wait_until="domcontentloaded", timeout=30000)
        page.wait_for_function(
            "() => document.documentElement.dataset.projectPhotoIntakeReady === 'true'",
            timeout=15000,
        )
        assert page.locator("#project-name").input_value() == "Maison Brest"
        assert page.locator("#project-picker").input_value() == brest_project_id
        assert page.locator("#city").input_value() == "Brest"
        assert page.locator("#known-width").input_value() == "9.8"
        assert page.locator("#notes").input_value() == "Rue montante, dossier persistant."
        assert page.locator("#studs").input_value() == "64"
        assert page.locator('[data-slot="front"] .guided-photo-note').input_value() == "note façade avant"
        assert ids_for(page, "front") == ["FRONT_001"]
        assert ids_for(page, "left") == ["LEFT_001", "LEFT_002"]
        assert ids_for(page, "detail_1") == ["DETAIL_001"]

        # Additional project: opening and cancelling the form creates nothing.
        page.locator("#new-project").click()
        assert page.locator("#project-create-panel").is_visible()
        assert page.locator("#project-create-label").text_content().strip() == "Nom du nouveau projet"
        page.locator("#new-project-name").fill("Projet annulé")
        page.locator("#cancel-new-project").click()
        assert page.locator("#project-picker option").count() == 1
        assert page.locator("#project-name").input_value() == "Maison Brest"

        # Create second named project before any record exists for it.
        page.locator("#new-project").click()
        page.locator("#new-project-name").fill("Maison Nantes")
        page.locator("#confirm-new-project").click()
        wait_saved(page)
        nantes_project_id = page.locator("#project-picker").input_value()
        assert nantes_project_id != brest_project_id
        assert set(page.locator("#project-picker option").all_text_contents()) == {"Maison Brest", "Maison Nantes"}
        assert page.locator("#project-name").input_value() == "Maison Nantes"
        assert ids_for(page, "front") == []

        # Same canonical photo ID may exist in the second project without collision.
        page.locator('[data-slot="front"] .guided-photo-input').set_input_files(str(IMAGES[4]))
        wait_saved(page)
        assert ids_for(page, "front") == ["FRONT_001"]
        assert page.locator('[data-photo-id="FRONT_001"] small').text_content().strip() == IMAGES[4].name

        # Switch projects: each project gets its own photos.
        page.locator("#project-picker").select_option(brest_project_id)
        wait_saved(page)
        assert page.locator("#project-name").input_value() == "Maison Brest"
        assert ids_for(page, "front") == ["FRONT_001"]
        assert page.locator('[data-photo-id="FRONT_001"] small').text_content().strip() == IMAGES[0].name

        page.locator("#project-picker").select_option(nantes_project_id)
        wait_saved(page)
        assert page.locator("#project-name").input_value() == "Maison Nantes"
        assert ids_for(page, "front") == ["FRONT_001"]
        assert page.locator('[data-photo-id="FRONT_001"] small').text_content().strip() == IMAGES[4].name

        # Rename must not steal focus or replace text during autosave.
        name_field = page.locator("#project-name")
        name_field.fill("Maison Lorient")
        wait_saved(page)
        assert page.evaluate("document.activeElement?.id") == "project-name"
        assert name_field.input_value() == "Maison Lorient"
        assert "Maison Lorient" in page.locator("#project-picker option").all_text_contents()
        assert "Maison Nantes" not in page.locator("#project-picker option").all_text_contents()

        page.reload(wait_until="domcontentloaded", timeout=30000)
        page.wait_for_function(
            "() => document.documentElement.dataset.projectPhotoIntakeReady === 'true'",
            timeout=15000,
        )
        assert page.locator("#project-name").input_value() == "Maison Lorient"
        assert page.locator("#project-picker").input_value() == nantes_project_id
        assert set(page.locator("#project-picker option").all_text_contents()) == {"Maison Brest", "Maison Lorient"}
        assert ids_for(page, "front") == ["FRONT_001"]
        assert page.locator('[data-photo-id="FRONT_001"] small').text_content().strip() == IMAGES[4].name

        # Return to Brest and prove persisted deletion fully consumes transient selection state.
        page.locator("#project-picker").select_option(brest_project_id)
        wait_saved(page)
        assert ids_for(page, "front") == ["FRONT_001"]
        page.locator('[data-delete-photo-id="FRONT_001"]').click()
        wait_saved(page)
        front_slot = page.locator('[data-slot="front"]')
        assert ids_for(page, "front") == []
        assert front_slot.locator(".persisted-photo-item").count() == 0
        assert front_slot.locator(".selected-photo-preview").count() == 0
        assert front_slot.locator(".guided-photo-name").text_content().strip() == "Aucune photo enregistrée"
        assert front_slot.locator("img:visible").count() == 0
        assert front_slot.locator(".guided-photo-input").evaluate("el => el.files.length") == 0

        # Re-add after delete: canonical ID must advance, never reuse FRONT_001.
        front_slot.locator(".guided-photo-input").set_input_files(str(IMAGES[0]))
        wait_saved(page)
        assert ids_for(page, "front") == ["FRONT_002"]
        assert front_slot.locator(".selected-photo-preview").count() == 0
        assert front_slot.locator(".guided-photo-input").evaluate("el => el.files.length") == 0
        page.reload(wait_until="domcontentloaded", timeout=30000)
        page.wait_for_function(
            "() => document.documentElement.dataset.projectPhotoIntakeReady === 'true'",
            timeout=15000,
        )
        assert page.locator("#project-name").input_value() == "Maison Brest"
        assert ids_for(page, "front") == ["FRONT_002"]
        assert page.locator('[data-photo-id="FRONT_002"] small').text_content().strip() == IMAGES[0].name

        # Retain the existing LEFT delete/reload stable-ID proof.
        assert ids_for(page, "left") == ["LEFT_001", "LEFT_002"]
        page.locator('[data-delete-photo-id="LEFT_001"]').click()
        wait_saved(page)
        page.reload(wait_until="domcontentloaded", timeout=30000)
        page.wait_for_function(
            "() => document.documentElement.dataset.projectPhotoIntakeReady === 'true'",
            timeout=15000,
        )
        assert page.locator("#project-name").input_value() == "Maison Brest"
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
        assert page.locator("#project-name").input_value() == "Maison Brest"
        assert ids_for(page, "right") == ["RIGHT_001", "RIGHT_002", "RIGHT_003", "RIGHT_004"]
        assert "LEFT_001" not in ids_for(page, "left")
        assert ids_for(page, "left") == ["LEFT_002", "LEFT_003"]
        assert page.locator('[data-slot="front"] .guided-photo-input').evaluate("el => el.files.length") == 0
        assert page.locator('[data-slot="right"] .guided-photo-input').evaluate("el => el.files.length") == 0

        # ZIP V1 must refuse the persisted DETAIL_001 rather than silently
        # dropping it or inventing an orientation.
        assert ids_for(page, "detail_1") == ["DETAIL_001"]
        page.locator("#shell-primary-button").click(timeout=5000)
        page.wait_for_function(
            """() => {
              const text = document.querySelector('#ai-package-status')?.textContent || '';
              return text.includes('Impossible de créer le ZIP')
                && text.includes('primary_face manquant ou invalide')
                && text.includes('DETAIL_001');
            }""",
            timeout=15000,
        )

        assert not runtime_errors, runtime_errors
        assert not failed_requests, failed_requests
        context.close()
        browser.close()

    print("BOLDUNGO-080 project photo intake browser proof passed")


if __name__ == "__main__":
    main()
