from pathlib import Path

VIEWER=Path("frontend/viewer.js")

def test_notice_decision_is_conservative_and_never_invents_motion():
    js=VIEWER.read_text(encoding="utf-8")
    assert "function noticeReferenceDecision(state,index)" in js
    assert "arrow:false" in js
    assert "closeup:false" in js
    assert "alternate_angle:false" in js
    assert "arrow:false" in js
    assert "fixed_reference:true" in js

def test_notice_decision_does_not_mutate_assembly_truth():
    js=VIEWER.read_text(encoding="utf-8")
    assert "const added=new Set(step.placement_ids)" in js
    assert "reference_decision:decision" in js
