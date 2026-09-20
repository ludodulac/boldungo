from pathlib import Path

VIEWER=Path("frontend/viewer.js")

def test_visual_action_experiment_is_strictly_step_12_and_opt_in():
    js=VIEWER.read_text(encoding="utf-8")
    assert "visualActionPrototype=index===11&&new URLSearchParams(window.location.search).get('visual')==='action'" in js
    assert "visualActionPrototype?'notice-current':'current'" in js
    assert "state.before.has(id)?'normal':'hidden'" in js
    assert "visualActionPrototype?'perspective-left':'perspective'" in js
    assert "visualActionPrototype?1.06:1.22" in js
    assert "if(s==='notice-current')return noticeActionMaterial" in js

def test_step_12_experiment_does_not_invent_motion_or_change_plan():
    js=VIEWER.read_text(encoding="utf-8")
    assert "function noticeAssemblyStepState(bundle,index)" in js
    assert "const added=new Set(step.placement_ids)" in js
    block=js[js.index("function applyNoticeAssemblyStep"):js.index("function goToNoticeStep")]
    assert "arrow" not in block.lower()


def test_step_12_float_requires_real_support_immediately_below():
    js=VIEWER.read_text(encoding="utf-8")
    assert "function noticeStep12SupportEvidence(state)" in js
    assert "candidate.z_plates+3===part.z_plates&&overlap" in js
    assert "if(!supports.length)return null" in js
    assert "axis:'vertical',direction:'down'" in js
    assert "if(mesh)mesh.position.y+=1.35" in js


def test_step_12_action_keeps_old_build_opaque_and_has_two_proven_arrows():
    js=VIEWER.read_text(encoding="utf-8")
    assert "function noticeStep12InsertionArrows(state,supportEvidence)" in js
    assert "const insertionArrows=[]" in js
    assert "insertion_arrow_count:insertionArrows.length" in js


def test_step_12_uses_real_color_outline_and_real_part_preview():
    js=VIEWER.read_text(encoding="utf-8")
    assert "if(s==='notice-current')return mat(p,'normal')" in js
    assert "new THREE.BoxHelper(mesh,0x1d4ed8)" in js
    assert "preview.className='notice-part-preview'" in js
    assert "ctx.ellipse" in js
