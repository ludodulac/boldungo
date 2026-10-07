import json
from pathlib import Path
from brickhouse.scene import ArchitecturalScene

SCENE = Path("frontend/data/boldungo2-guided-005d-m2-scene.json")
SCENE_005C = Path("frontend/data/boldungo2-guided-005c-m2-scene.json")
VIEWER = Path("frontend/scene-viewer.js")

def raw(path=SCENE):
    return json.loads(path.read_text(encoding="utf-8"))

def platforms(prefix):
    return [p for p in raw()["platforms"] if p["id"].startswith(prefix)]

def top(p):
    return p["position"]["z"] + p["thickness"]

def test_005d_architectural_scene_is_valid_and_m3_absent():
    scene = ArchitecturalScene.model_validate(raw())
    assert scene.schema_version == "0.2"
    assert len(scene.volumes) == 1
    assert scene.stairs == []
    assert not any(p.material and p.material.value == "timber" for p in scene.platforms)

def test_005d_has_7_landing_9_discrete_horizontal_steps_at_112_width():
    r7, r9 = platforms("m2-run7-step-"), platforms("m2-run9-step-")
    landing = next(p for p in raw()["platforms"] if p["id"] == "m2-intermediate-square-landing")
    assert len(r7) == 7 and len(r9) == 9
    assert all(p["depth"] == 1.12 for p in r7)
    assert all(p["width"] == 1.12 for p in r9)
    assert landing["width"] == landing["depth"] == 1.12
    assert all(b > a for a,b in zip(map(top,r7), list(map(top,r7))[1:]))
    assert all(b > a for a,b in zip(map(top,r9), list(map(top,r9))[1:]))

def test_005d_lower_to_landing_to_upper_is_continuous_and_aligned():
    r7, r9 = platforms("m2-run7-step-"), platforms("m2-run9-step-")
    landing = next(p for p in raw()["platforms"] if p["id"] == "m2-intermediate-square-landing")
    last7 = r7[-1]
    assert abs(last7["position"]["x"] + last7["width"] - landing["position"]["x"]) < 1e-4
    assert last7["position"]["y"] == landing["position"]["y"]
    # Upper corridor uses exactly the landing's x band and starts at its front edge.
    assert all(p["position"]["x"] == landing["position"]["x"] for p in r9)
    first9 = r9[0]
    assert abs(first9["position"]["y"] + first9["depth"] - landing["position"]["y"]) < 1e-4

def test_005d_upper_reaches_enlarged_terrace_at_same_high_level():
    d=raw(); r9=platforms("m2-run9-step-")
    terrace=next(p for p in d["platforms"] if p["id"]=="m2-high-concrete-terrace")
    old=raw(SCENE_005C); oldt=next(p for p in old["platforms"] if p["id"]=="m2-high-concrete-platform")
    assert abs(top(r9[-1]) - top(terrace)) < 1e-4
    assert terrace["width"] * terrace["depth"] > oldt["width"] * oldt["depth"] * 1.5
    assert terrace["source"]["kind"] == "inferred"

def test_005d_terrace_preserves_open_void_and_door_landmark():
    d=raw(); terrace=next(p for p in d["platforms"] if p["id"]=="m2-high-concrete-terrace")
    door=d["openings"][0]
    assert top(terrace) > 2.5 and terrace["thickness"] < .5
    assert len(terrace["supports"]) == 2
    assert all(v["id"]=="house-main-reference" for v in d["volumes"])
    assert door["facade"] == "left"
    # Door longitudinal position lies beneath/within the terrace's covered span.
    assert terrace["position"]["y"] <= door["offset_horizontal"] <= terrace["position"]["y"] + terrace["depth"]

def test_005d_parapets_are_geometric_canonical_and_step_silhouette():
    d=raw(); walls=d["partial_wall_segments"]
    lower=[w for w in walls if w["id"].startswith("m2-run7-parapet-")]
    upper=[w for w in walls if w["id"].startswith("m2-run9-parapet-")]
    assert len(lower)==14 and len(upper)==18
    assert all(w["start"]["z"] == w["end"]["z"] for w in walls)
    assert all(w["material"]=="masonry" for w in lower+upper)
    assert len({w["height"]["value"] for w in lower}) == 7
    assert len({w["height"]["value"] for w in upper}) == 9

def test_005d_whole_m2_is_source_geometry_and_viewer_unchanged_contract():
    d=raw(); old=raw(SCENE_005C)
    old_landing=next(p for p in old["platforms"] if p["id"]=="m2-intermediate-square-landing")
    new_landing=next(p for p in d["platforms"] if p["id"]=="m2-intermediate-square-landing")
    assert new_landing["position"]["y"] != old_landing["position"]["y"]
    assert d["stairs"] == []
    viewer=VIEWER.read_text(encoding="utf-8")
    assert "new THREE.BoxGeometry(width, thickness, depth)" in viewer
    assert "renderVolumes(); renderOpenings(); renderPlatforms(); renderPartialWallSegments(); renderStairs();" in viewer
