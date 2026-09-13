import json
import math
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[2]
GABLE_MODULE = ROOT / "frontend" / "scene-viewer-gable-roof.js"
VIEWER = ROOT / "frontend" / "scene-viewer.js"


def _run_geometry(case: dict) -> dict:
    script = f"""
import {{ gableRoofTriangles }} from {json.dumps(GABLE_MODULE.as_uri())};
const result = gableRoofTriangles({json.dumps(case)});
console.log(JSON.stringify(result));
"""
    completed = subprocess.run(
        ["node", "--input-type=module", "--eval", script],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def _points(result: dict):
    values = result["vertices"]
    return [tuple(values[index : index + 3]) for index in range(0, len(values), 3)]


def test_gable_roof_depth_ridge_uses_scene_pitch_overhang_and_volume_top():
    case = {
        "x": 1.0,
        "y": 2.0,
        "z": 3.0,
        "width": 6.0,
        "depth": 8.0,
        "height": 4.0,
        "pitchDegrees": 30.0,
        "overhang": 0.5,
        "ridgeDirection": "depth",
    }
    result = _run_geometry(case)
    points = _points(result)
    expected_top = 7.0
    expected_ridge = expected_top + math.tan(math.radians(30.0)) * 3.5

    assert result["ridgeDirection"] == "depth"
    assert math.isclose(result["topElevation"], expected_top)
    assert math.isclose(result["ridgeElevation"], expected_ridge)
    assert len(points) == 12

    ridge_points = {point for point in points if math.isclose(point[1], expected_ridge)}
    assert ridge_points == {
        (4.0, result["ridgeElevation"], 1.5),
        (4.0, result["ridgeElevation"], 10.5),
    }
    eave_points = {point for point in points if math.isclose(point[1], expected_top)}
    assert {(point[0], point[2]) for point in eave_points} == {
        (0.5, 1.5),
        (0.5, 10.5),
        (7.5, 1.5),
        (7.5, 10.5),
    }


def test_gable_roof_width_ridge_rotates_geometry_without_mirroring():
    case = {
        "x": -2.0,
        "y": 5.0,
        "z": 0.0,
        "width": 10.0,
        "depth": 4.0,
        "height": 6.0,
        "pitchDegrees": 20.0,
        "overhang": 0.25,
        "ridgeDirection": "width",
    }
    result = _run_geometry(case)
    points = _points(result)
    expected_ridge = 6.0 + math.tan(math.radians(20.0)) * 2.25
    ridge_points = {point for point in points if math.isclose(point[1], expected_ridge)}

    assert result["ridgeDirection"] == "width"
    assert ridge_points == {
        (-2.25, result["ridgeElevation"], 7.0),
        (8.25, result["ridgeElevation"], 7.0),
    }


def test_unresolved_gable_geometry_is_not_fabricated_and_existing_roof_paths_remain():
    assert _run_geometry(
        {
            "x": 0,
            "y": 0,
            "z": 0,
            "width": 6,
            "depth": 8,
            "height": 4,
            "pitchDegrees": 30,
            "overhang": 0,
            "ridgeDirection": "unknown",
        }
    ) is None

    viewer_source = VIEWER.read_text(encoding="utf-8")
    assert "roof.type === 'gable'" in viewer_source
    assert "roof.type === 'flat'" in viewer_source
    assert "roof.type !== 'shed'" in viewer_source
    assert "gableRoofTriangles" in viewer_source
