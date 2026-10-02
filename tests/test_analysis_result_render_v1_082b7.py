from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"


def read(name: str) -> str:
    return (FRONTEND / name).read_text(encoding="utf-8")


def test_sophie_r001_photo_question_runtime_contract() -> None:
    completed = subprocess.run(
        ["node", "tests/analysis_result_render_v1_082b7.mjs"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "BOLDUNGO-082B7 Sophie R001 photo/question view contract passed" in completed.stdout


def test_renderer_uses_persisted_result_and_real_project_blobs() -> None:
    renderer = read("analysis-result-render-v1.js")
    assert "getActiveProjectSnapshot" in renderer
    assert "analysis_result_imports" in renderer
    assert "latestPersistedSophieR001Result" in renderer
    assert "URL.createObjectURL" not in renderer
    assert "urlApi.createObjectURL(item.photo.blob)" in renderer
    assert "urlApi.revokeObjectURL(url)" in renderer


def test_visible_phone_survey_step_contains_renderer_host() -> None:
    shell = read("photo-shell.js")
    css = read("photo-shell.css")
    package = read("brickhouse-survey-package.js")

    assert 'id="sophie-r001-result-view"' in shell
    assert "boldungo:photo-shell-ready" in shell
    assert "analysis-result-render-v1.js?v=exchange-v1-sophie-r001-view" in package
    assert ".sophie-r001-result-view" in css
    assert ".sophie-v1-photo-block" in css
    assert ".sophie-v1-global-questions" in css


def test_import_success_emits_local_rerender_event() -> None:
    importer = read("analysis-result-import-v1.js")
    assert "boldungo:analysis-result-v1-imported" in importer
    assert "eventTarget?.dispatchEvent" in importer


def test_no_answer_controls_or_human_answers_added() -> None:
    renderer = read("analysis-result-render-v1.js")
    lowered = renderer.lower()
    assert "human_answers" not in lowered
    assert "createelement('button')" not in lowered
    assert 'createelement("button")' not in lowered
    assert "createelement('input')" not in lowered
    assert 'createelement("input")' not in lowered
    assert "createelement('textarea')" not in lowered
    assert 'createelement("textarea")' not in lowered
