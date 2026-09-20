from pathlib import Path

VIEWER=Path("frontend/viewer.js")

def test_visual_action_experiment_is_strictly_step_12_and_opt_in():
    js=VIEWER.read_text(encoding="utf-8")
    assert "visualActionPrototype=index===11&&new URLSearchParams(window.location.search).get('visual')==='action'" in js
    assert "visualActionPrototype?'notice-current':'current'" in js
    assert "visualActionPrototype?'previous':'normal'" in js
    assert "visualActionPrototype?1.06:1.22" in js

def test_step_12_experiment_does_not_invent_motion_or_change_plan():
    js=VIEWER.read_text(encoding="utf-8")
    assert "function noticeAssemblyStepState(bundle,index)" in js
    assert "const added=new Set(step.placement_ids)" in js
    assert "arrow" not in js[js.index("function applyNoticeAssemblyStep"):js.index("function goToNoticeStep")].lower()
