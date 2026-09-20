from pathlib import Path
import subprocess

VIEWER = Path("frontend/viewer.js")

def test_notice_keeps_validated_three_quarter_camera_primitive():
    js=VIEWER.read_text(encoding="utf-8")
    assert "view==='perspective'?new THREE.Vector3(.72,.92,1.18)" in js
    assert "const f=noticePlacementFrame(placementIds);" in js
    assert "halfWidth/Math.tan(horizontalFov/2)" in js
    assert "halfHeight/Math.tan(verticalFov/2)" in js
    assert "frameNoticePlacements([...state.before,...state.added],state.step.view||'perspective');" in js
    assert "function frameModel(){frameCanonicalView('perspective');}" in js

def test_viewer_javascript_remains_syntactically_valid():
    result=subprocess.run(["node","--check",str(VIEWER)],capture_output=True,text=True)
    assert result.returncode==0,result.stderr
