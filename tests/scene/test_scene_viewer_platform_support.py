import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[2]
SUPPORT_MODULE = ROOT / "frontend" / "scene-viewer-platform-support.js"
VIEWER = ROOT / "frontend" / "scene-viewer.js"


def _run_support(support: dict):
    script = f"""
import {{ platformSupportBox }} from {json.dumps(SUPPORT_MODULE.as_uri())};
const result = platformSupportBox({json.dumps(support)});
console.log(JSON.stringify(result));
"""
    completed = subprocess.run(
        ["node", "--input-type=module", "--eval", script],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def test_platform_support_box_uses_only_declared_position_and_dimensions():
    result = _run_support(
        {
            "id": "support-1",
            "position": {"x": -2.5, "y": 6.25, "z": 0.0},
            "width": 0.16,
            "depth": 0.2,
            "height": 2.1,
        }
    )

    assert result == {
        "width": 0.16,
        "depth": 0.2,
        "height": 2.1,
        "center": {"x": -2.42, "y": 1.05, "z": 6.35},
    }


def test_platform_support_box_refuses_missing_or_invalid_geometry():
    assert _run_support(
        {
            "id": "support-missing-height",
            "position": {"x": 0, "y": 0, "z": 0},
            "width": 0.2,
            "depth": 0.2,
        }
    ) is None
    assert _run_support(
        {
            "id": "support-zero-width",
            "position": {"x": 0, "y": 0, "z": 0},
            "width": 0,
            "depth": 0.2,
            "height": 2.0,
        }
    ) is None


def test_viewer_renders_only_declared_platform_supports_without_bracing_generation():
    viewer_source = VIEWER.read_text(encoding="utf-8")
    assert "for (const support of platform.supports ?? [])" in viewer_source
    assert "platformSupportBox(support)" in viewer_source
    assert "new THREE.BoxGeometry(box.width, box.height, box.depth)" in viewer_source
    assert "brace" not in viewer_source.lower()
    assert "diagonal" not in viewer_source.lower()
