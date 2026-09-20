from pathlib import Path


VIEWER = Path("frontend/viewer.js")


def test_notice_forces_studs_past_mobile_area_threshold_without_changing_normal_policy():
    js = VIEWER.read_text(encoding="utf-8")

    assert "studDetailEnabled=!window.matchMedia('(max-width: 760px)').matches" in js
    assert "studMeshBudgetEnabled&&(noticeFirstStep||studDetailEnabled||w*l<=4)" in js
    assert "noticeFirstStep=noticeMode==='step-0001'" in js


def test_notice_stud_change_preserves_validated_framing_and_camera():
    js = VIEWER.read_text(encoding="utf-8")

    # #722: frame only the visible InstructionStep placements.
    assert "frameNoticePlacements([...state.before,...state.added],state.step.view||'perspective');" in js
    assert "box.expandByObject(mesh,true);" in js

    # #724: dedicated three-quarter, slightly top-down NOTICE direction.
    assert "view==='perspective'?new THREE.Vector3(.72,.92,1.18)" in js
