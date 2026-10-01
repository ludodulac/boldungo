from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_photo_shell_resynchronizes_project_controls_from_runtime_state():
    shell = (ROOT / "frontend" / "photo-shell.js").read_text(encoding="utf-8")

    assert "function syncProjectControlsVisibility()" in shell
    assert "projectIntake.dataset.projectMode" in shell
    assert "mode==='first'||mode==='legacy'||mode==='additional'" in shell
    assert "createPanel.hidden=!creating" in shell
    assert "existingControls.hidden=mode==='first'||mode==='legacy'" in shell
    assert "window.addEventListener('boldungo:project-photo-intake-ready', syncProjectControlsVisibility)" in shell
    assert "syncProjectControlsVisibility();" in shell


def test_project_runtime_still_publishes_shell_modes_for_empty_and_active_projects():
    runtime = (ROOT / "frontend" / "photo-capture-runtime.js").read_text(encoding="utf-8")

    assert "showProjectCreation('first')" in runtime
    assert "setAttribute('data-project-mode', mode)" in runtime
    assert "setAttribute('data-project-mode', 'active')" in runtime
    assert "boldungo:project-photo-intake-ready" in runtime
