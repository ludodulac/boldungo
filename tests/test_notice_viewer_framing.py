from pathlib import Path
import subprocess

VIEWER = Path("frontend/viewer.js")

def test_notice_framing_uses_only_current_visible_assembly_placements():
    js = VIEWER.read_text(encoding="utf-8")
    assert "function noticePlacementFrame(placementIds)" in js
    assert "const mesh=meshByPlacementId.get(id);" in js
    assert "box.expandByObject(mesh,true);" in js
    assert "frameNoticePlacements([...state.before,...state.added],state.step.view||'perspective');" in js

def test_notice_framing_accounts_for_mobile_viewport_without_changing_normal_viewer():
    js = VIEWER.read_text(encoding="utf-8")
    assert "resizeRenderer();" in js
    assert "horizontalFov=2*Math.atan(Math.tan(verticalFov/2)*camera.aspect)" in js
    assert "halfWidth/Math.tan(horizontalFov/2)" in js
    assert "halfHeight/Math.tan(verticalFov/2)" in js
    assert "function frameModel(){frameCanonicalView('perspective');}" in js
    assert "resetButton.addEventListener('click',()=>{if(lastBundle)frameCanonicalView('perspective');});" in js

def test_viewer_javascript_remains_syntactically_valid():
    result = subprocess.run(["node","--check",str(VIEWER)],capture_output=True,text=True)
    assert result.returncode == 0, result.stderr
