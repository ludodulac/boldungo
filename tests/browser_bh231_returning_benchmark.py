from contextlib import contextmanager
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import shutil
import threading

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SURVEY = ROOT / 'frontend' / 'benchmarks' / 'real-house-5' / 'accepted-survey-v0.1.json'


@contextmanager
def serve_repo():
    class QuietHandler(SimpleHTTPRequestHandler):
        def log_message(self, *_args):
            pass

    server = ThreadingHTTPServer(('127.0.0.1', 0), lambda *args, **kwargs: QuietHandler(*args, directory=ROOT, **kwargs))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_port
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()


def browser_binary():
    for candidate in ('google-chrome', 'google-chrome-stable', 'chromium', 'chromium-browser'):
        path = shutil.which(candidate)
        if path:
            return path
    raise AssertionError('BH-231 browser proof requires Chromium/Chrome')


def collect_preview_diagnostic(page, runtime_errors, console_errors, failed_requests):
    browser_state = page.evaluate(
        """() => {
          const visible = element => {
            if (!element) return false;
            const style = getComputedStyle(element);
            const rect = element.getBoundingClientRect();
            return style.display !== 'none'
              && style.visibility !== 'hidden'
              && Number(style.opacity || 1) !== 0
              && rect.width > 0
              && rect.height > 0;
          };

          const slotState = slotName => {
            const slot = document.querySelector(`.guided-photo-slot[data-slot="${slotName}"]`);
            const input = slot?.querySelector('.guided-photo-input') || null;
            return {
              slot_exists: Boolean(slot),
              slot_visible: visible(slot),
              input_exists: Boolean(input),
              input_disabled: input ? input.disabled : null,
              input_files_length: input?.files?.length ?? null,
              selected_photo_preview_count: slot?.querySelectorAll('.selected-photo-preview').length ?? null,
              persisted_photo_item_count: slot?.querySelectorAll('.persisted-photo-item').length ?? null,
            };
          };

          const projectCreatePanel = document.querySelector('#project-create-panel');
          const projectPicker = document.querySelector('#project-picker');

          return {
            DOCUMENT_READY_STATE: document.readyState,
            PROJECT_PHOTO_INTAKE_READY: document.documentElement.dataset.projectPhotoIntakeReady ?? null,
            BODY_BENCHMARK: document.body?.dataset?.benchmark ?? null,
            BENCHMARK_FIXTURE_CONTEXT: document.body?.dataset?.benchmarkFixtureContext ?? null,
            AI_PACKAGE_STATUS: document.querySelector('#ai-package-status')?.textContent?.trim() ?? null,
            PROJECT_SAVE_STATUS: document.querySelector('#project-save-status')?.textContent?.trim() ?? null,
            PROJECT_CREATE_PANEL: projectCreatePanel
              ? (projectCreatePanel.hidden || !visible(projectCreatePanel) ? 'hidden' : 'visible')
              : 'missing',
            ACTIVE_USER_PROJECT_COUNT: projectPicker
              ? projectPicker.querySelectorAll('option').length
              : null,
            FRONT_INPUT: slotState('front'),
            RIGHT_INPUT: slotState('right'),
            LEFT_INPUT: slotState('left'),
            REAR_INPUT: slotState('rear'),
            TOTAL_SELECTED_PREVIEW_COUNT: document.querySelectorAll('.selected-photo-preview').length,
          };
        }"""
    )
    browser_state['PAGE_ERRORS'] = list(runtime_errors)
    browser_state['CONSOLE_ERRORS'] = list(console_errors)
    browser_state['FAILED_REQUESTS'] = list(failed_requests)
    return browser_state


def main():
    accepted_survey = json.loads(SURVEY.read_text(encoding='utf-8'))
    stale_pending = {
        'survey': accepted_survey,
        'issues': [],
        'valid_for_scene_fusion': True,
    }

    with serve_repo() as port, sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=browser_binary(), args=['--no-sandbox'])
        context = browser.new_context(viewport={'width': 390, 'height': 844}, accept_downloads=True)
        context.add_init_script(
            script=f"""
            (() => {{
              if (location.pathname.endsWith('/photo.html')) {{
                localStorage.setItem('brickhouse.pendingArchitecturalSurvey', {json.dumps(json.dumps(stale_pending))});
                localStorage.setItem('brickhouse.knownFrontWidthM', '12.34');
                localStorage.setItem('brickhouse.lastRejectedArchitecturalScene', '{{"stale":true}}');
                localStorage.setItem('brickhouse.lastSceneValidationError', 'stale');
              }}
            }})();
            """
        )
        page = context.new_page()
        runtime_errors = []
        console_errors = []
        failed_requests = []
        page.on('pageerror', lambda error: runtime_errors.append(f'pageerror: {error}'))
        page.on('console', lambda message: console_errors.append(message.text) if message.type == 'error' else None)
        page.on('requestfailed', lambda request: failed_requests.append(f'{request.method} {request.url}: {request.failure}'))

        url = f'http://127.0.0.1:{port}/frontend/photo.html?benchmark=real-house-5&checkpoint=bh231-ci'
        response = page.goto(url, wait_until='domcontentloaded', timeout=30000)
        assert response and response.ok
        page.wait_for_selector('body.boldungo-shell-enabled', timeout=15000)
        try:
            page.wait_for_function(
                "() => document.querySelectorAll('.selected-photo-preview').length === 5",
                timeout=15000,
            )
        except PlaywrightTimeoutError:
            diagnostic = collect_preview_diagnostic(page, runtime_errors, console_errors, failed_requests)
            print('BH231_RUNTIME_DIAGNOSTIC')
            print(json.dumps(diagnostic, indent=2, sort_keys=True))
            raise

        cockpit = page.locator('.boldungo-cockpit')
        assert cockpit.get_attribute('data-shell-state') == 'photos'
        assert page.locator('#shell-state-title').text_content().strip() == '1. Photos'
        assert page.locator('.selected-photo-preview').count() == 5
        assert page.locator('#shell-primary-button').text_content().strip() == 'Créer le ZIP'
        assert page.locator('#download-ai-package').text_content().strip() == 'Créer le ZIP pour Sophie'
        for key in (
            'brickhouse.pendingArchitecturalSurvey',
            'brickhouse.knownFrontWidthM',
            'brickhouse.lastRejectedArchitecturalScene',
            'brickhouse.lastSceneValidationError',
        ):
            assert page.evaluate('(key) => localStorage.getItem(key)', key) is None
        assert page.evaluate('1 + 1') == 2

        page.locator('[data-shell-state="survey"]').click(timeout=5000)
        assert cockpit.get_attribute('data-shell-state') == 'survey'
        page.locator('[data-shell-state="photos"]').click(timeout=5000)
        assert cockpit.get_attribute('data-shell-state') == 'photos'

        # The benchmark fixture intentionally bypasses user-project creation.
        # The authoritative ZIP V1 action must therefore fail clearly rather
        # than falling back to the historical PDF handoff.
        page.locator('#shell-primary-button').click(timeout=5000)
        page.wait_for_function(
            "() => document.querySelector('#ai-package-status')?.textContent?.includes('Impossible de créer le ZIP : Aucun projet actif')",
            timeout=15000,
        )
        assert cockpit.get_attribute('data-shell-state') == 'survey'
        assert not runtime_errors, runtime_errors
        assert not failed_requests, failed_requests
        context.close()
        browser.close()

    print('BH-231 local returning-browser benchmark proof passed')


if __name__ == '__main__':
    main()
