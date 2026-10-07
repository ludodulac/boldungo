import json
from pathlib import Path

from brickhouse.scene import ArchitecturalScene

SCENE_PATH = Path("frontend/data/boldungo2-guided-005c-m2-scene.json")
VIEWER_PATH = Path("frontend/scene-viewer.js")


def _raw():
    return json.loads(SCENE_PATH.read_text(encoding="utf-8"))


def _scene():
    return ArchitecturalScene.model_validate(_raw())


def test_005c_is_canonical_m1_reference_plus_m2_without_m3():
    scene = _scene()
    assert scene.schema_version == "0.2"
    assert len(scene.volumes) == 1
    assert scene.volumes[0].width.value == 9.3
    assert scene.volumes[0].depth.value == 8.2
    assert scene.stairs == []
    assert not any(item.material and item.material.value == "timber" for item in scene.platforms)
    assert "M3 absent" in (scene.notes or "")


def test_005c_contains_seven_plus_landing_plus_nine_discrete_rendered_steps():
    raw = _raw()
    run7 = [p for p in raw["platforms"] if p["id"].startswith("m2-run7-step-")]
    run9 = [p for p in raw["platforms"] if p["id"].startswith("m2-run9-step-")]
    landing = [p for p in raw["platforms"] if p["id"] == "m2-intermediate-square-landing"]
    assert len(run7) == 7
    assert len(landing) == 1
    assert len(run9) == 9
    assert all(p["material"] == "masonry" for p in run7 + run9)
    # Platforms are rendered by the existing viewer as horizontal boxes.
    viewer = VIEWER_PATH.read_text(encoding="utf-8")
    assert "new THREE.BoxGeometry(width, thickness, depth)" in viewer
    assert "renderVolumes(); renderOpenings(); renderPlatforms();" in viewer


def test_005c_step_tops_rise_discretely_and_upper_flight_moves_west():
    raw = _raw()
    run7 = [p for p in raw["platforms"] if p["id"].startswith("m2-run7-step-")]
    run9 = [p for p in raw["platforms"] if p["id"].startswith("m2-run9-step-")]
    tops7 = [p["position"]["z"] + p["thickness"] for p in run7]
    tops9 = [p["position"]["z"] + p["thickness"] for p in run9]
    assert all(b > a for a, b in zip(tops7, tops7[1:]))
    assert all(b > a for a, b in zip(tops9, tops9[1:]))
    assert all(b["position"]["y"] > a["position"]["y"] for a, b in zip(run9, run9[1:]))
    assert all("WEST" in p["evidence"][0]["observation"] for p in run9)


def test_005c_preserves_112_width_and_moves_stair_mass_outer_south():
    raw = _raw()
    run7 = [p for p in raw["platforms"] if p["id"].startswith("m2-run7-step-")]
    run9 = [p for p in raw["platforms"] if p["id"].startswith("m2-run9-step-")]
    # lower flight width is platform depth; upper flight width is platform width
    assert all(p["depth"] == 1.12 for p in run7)
    assert all(p["width"] == 1.12 for p in run9)
    assert max(p["position"]["x"] for p in run9) < -1.0
    platform = next(p for p in raw["platforms"] if p["id"] == "m2-high-concrete-platform")
    assert platform["position"]["x"] == -1.08
    assert platform["position"]["x"] + platform["width"] == 0


def test_005c_door_reads_into_covered_void_not_under_stair():
    raw = _raw()
    door = raw["openings"][0]
    slab = next(p for p in raw["platforms"] if p["id"] == "m2-high-concrete-platform")
    run9 = [p for p in raw["platforms"] if p["id"].startswith("m2-run9-step-")]
    assert door["facade"] == "left"
    assert slab["position"]["z"] > 2
    assert slab["thickness"] < 0.5
    assert len(slab["supports"]) == 2
    # Slab touches the south facade; upper stair remains in the outer band.
    assert slab["position"]["x"] + slab["width"] == 0
    assert all(p["position"]["x"] + p["width"] <= slab["position"]["x"] for p in run9)
    assert all(v["id"] == "house-main-reference" for v in raw["volumes"])


def test_005c_no_ramp_geometry_and_only_horizontal_parapet():
    raw = _raw()
    assert raw["stairs"] == []
    assert len(raw["partial_wall_segments"]) == 1
    wall = raw["partial_wall_segments"][0]
    assert wall["start"]["z"] == wall["end"]["z"]
    assert "inclined stair parapets remain evidence-only" in raw["notes"]
