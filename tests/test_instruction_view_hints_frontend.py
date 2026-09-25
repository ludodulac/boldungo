from pathlib import Path


def test_instruction_renderer_consumes_backend_step_view_hint():
    source = Path("frontend/instructions.js").read_text(encoding="utf-8")

    assert "perspective:'Perspective'" in source
    assert "buildStepPreview(bundle,new Set(visibleIds),currentIds,step.view,previousView," in source
    assert "view=VIEW_LABELS[requestedView]?requestedView:chooseStepView(currentParts,previousView)" in source
