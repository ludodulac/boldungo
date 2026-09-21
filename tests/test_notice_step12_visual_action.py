from pathlib import Path

VIEWER=Path("frontend/viewer.js")
STYLES=Path("frontend/styles.css")

def test_step_12_reference_experiment_is_strictly_opt_in():
    js=VIEWER.read_text(encoding="utf-8")
    assert "const noticeReferenceGrammar=new URLSearchParams(window.location.search).get('visual')==='action'" in js
    assert "const visualActionPrototype=noticeReferenceGrammar" in js
    assert "state.before.has(id)?'normal':'hidden'" in js
    assert "visualActionPrototype?'perspective-left':'perspective'" in js
    assert "visualActionPrototype?.92:1.22" in js

def test_step_12_preserves_real_colors_and_uses_outline_only():
    js=VIEWER.read_text(encoding="utf-8")
    assert "if(s==='notice-current')return mat(p,'normal')" in js
    assert "new THREE.BoxHelper(mesh,0x2563eb)" in js
    assert "const insertionArrows=[]" in js

def test_step_12_pli_is_recognizable_and_large_on_desktop():
    js=VIEWER.read_text(encoding="utf-8")
    css=STYLES.read_text(encoding="utf-8")
    assert "preview.className='notice-part-preview'" in js
    assert "ctx.ellipse" in js
    assert "@media(min-width:761px)" in css
    assert "width:118px;height:72px" in css

def test_step_12_does_not_change_assembly_plan():
    js=VIEWER.read_text(encoding="utf-8")
    assert "function noticeAssemblyStepState(bundle,index)" in js
    assert "const added=new Set(step.placement_ids)" in js
