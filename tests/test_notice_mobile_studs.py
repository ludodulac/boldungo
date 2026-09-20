from pathlib import Path

VIEWER=Path("frontend/viewer.js")

def test_notice_forces_studs_on_mobile_for_all_steps_1_to_34_without_changing_normal_policy():
    js=VIEWER.read_text(encoding="utf-8")
    assert "studDetailEnabled=!window.matchMedia('(max-width: 760px)').matches" in js
    assert "studMeshBudgetEnabled&&(noticePrototypeMode||studDetailEnabled||w*l<=4)" in js
    assert "noticePrototypeMode=noticeStepNumber!==null&&noticeStepNumber>=1&&noticeStepNumber<=34" in js

def test_notice_stud_change_preserves_validated_framing_and_camera():
    js=VIEWER.read_text(encoding="utf-8")
    assert "frameNoticePlacements([...state.before,...state.added],visualActionPrototype?'perspective-left':'perspective',visualActionPrototype?1.06:1.22);" in js
    assert "box.expandByObject(mesh,true);" in js
    assert "view==='perspective'?new THREE.Vector3(.72,.92,1.18)" in js
