from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_clarification_lab_runtime_static_contract():
    photo_html = (ROOT / "frontend" / "photo.html").read_text(encoding="utf-8")
    clarification_lab = (ROOT / "frontend" / "clarification-lab.js").read_text(encoding="utf-8")
    photo_shell = (ROOT / "frontend" / "photo-shell.js").read_text(encoding="utf-8")

    assert 'id="clarification-lab"' in photo_html
    assert "clarification-lab.js" in photo_html

    assert "params.get('clarification-lab') === 'real-house-5'" in clarification_lab
    assert "./benchmarks/real-house-5/clarifications-v1.json" in clarification_lab
    assert "updateProjectClarificationState" in clarification_lab
    assert "activeQuestionQueue" in clarification_lab
    assert "evaluateClarificationGate" in clarification_lab
    assert "dataset.currentClarificationId" in clarification_lab

    assert "document.querySelector('#clarification-lab')" in photo_shell
    assert "move(clarificationLab,photoScroll)" in photo_shell

    lowered = clarification_lab.lower()
    for marker in (
        "openai",
        "anthropic",
        "gemini",
        "llm",
        "api.openai",
        "vision api",
    ):
        assert marker not in lowered

    assert "http://" not in lowered
    assert "https://" not in lowered
