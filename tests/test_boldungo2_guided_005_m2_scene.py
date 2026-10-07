import json
from pathlib import Path

from brickhouse.scene import ArchitecturalScene

SCENE_PATH = Path("frontend/data/boldungo2-guided-005-m2-scene.json")
VIEWER_PATH = Path("frontend/scene-viewer.js")


def _raw():
    return json.loads(SCENE_PATH.read_text(encoding="utf-8"))


def _scene():
    return ArchitecturalScene.model_validate(_raw())


def test_guided_005_is_m1_reference_plus_m2_only():
    scene = _scene()
    assert scene.schema_version == "0.2"
    assert len(scene.volumes) == 1
    assert scene.volumes[0].width.value == 9.3
    assert scene.volumes[0].depth.value == 8.2
    assert {item.id for item in scene.platforms} == {
        "m2-intermediate-square-landing",
        "m2-high-concrete-platform",
    }
    assert not any((item.material and item.material.value == "timber") for item in scene.platforms)
    assert "M3 timber terrace is deliberately absent" in (scene.notes or "")


def test_absolute_axis_contract_and_westward_upper_flight():
    raw = _raw()
    notes = raw["notes"]
    assert "front=EAST at scene y=0" in notes
    assert "rear=WEST at increasing scene y" in notes
    assert "south facade=left" in notes

    run7, run9 = raw["stairs"]
    assert run7["id"] == "m2-stair-run-7"
    assert run9["id"] == "m2-stair-run-9"

    # Lower flight approaches the house: x increases from exterior south toward x=0.
    assert run7["end"]["x"] > run7["start"]["x"]
    assert run7["end"]["y"] == run7["start"]["y"]

    # Upper flight is the longitudinal flight: increasing scene y is REAR/WEST.
    assert run9["end"]["y"] > run9["start"]["y"]
    assert run9["end"]["x"] == run9["start"]["x"]
    orientation = run9["evidence"][1]["observation"].upper()
    assert "WEST" in orientation and "REAR" in orientation


def test_user_confirmed_stair_facts_and_intermediate_landing_are_preserved():
    raw = _raw()
    run7, run9 = raw["stairs"]
    assert run7["width"] == 1.12
    assert run9["width"] == 1.12
    assert "FIRST_RUN_7" in run7["evidence"][0]["observation"]
    assert "SECOND_RUN_9" in run9["evidence"][0]["observation"]

    landing = next(item for item in raw["platforms"] if item["id"] == "m2-intermediate-square-landing")
    assert landing["width"] == landing["depth"] == 1.12
    assert landing["source"]["kind"] == "inferred"


def test_high_platform_is_elevated_thin_and_keeps_open_void():
    raw = _raw()
    platform = next(item for item in raw["platforms"] if item["id"] == "m2-high-concrete-platform")
    assert platform["position"]["z"] > 2
    assert platform["thickness"] < 0.5
    assert len(platform["supports"]) >= 1
    support_ids = {item["id"] for item in platform["supports"]}
    assert len(support_ids) == len(platform["supports"])
    # No house/exterior volume occupies the footprint below the elevated slab.
    assert all(item["id"] == "house-main-reference" for item in raw["volumes"])
    assert platform["id"] not in {item["id"] for item in raw["volumes"]}


def test_lower_door_is_reference_only_and_m3_connection_is_reserved_without_m3_geometry():
    raw = _raw()
    assert [item["id"] for item in raw["openings"]] == ["south-lower-door-reference"]
    assert raw["openings"][0]["facade"] == "left"
    assert "left of the entrance/opening" in raw["openings"][0]["evidence"][0]["observation"]
    assert "reserved only as a future topological connection toward M3" in raw["notes"]
    assert all("timber" not in item["id"] for item in raw["platforms"] + raw["partial_wall_segments"])


def test_parapets_follow_both_flights_and_existing_viewer_contract_is_reused():
    raw = _raw()
    ids = {item["id"] for item in raw["partial_wall_segments"]}
    # Canonical v0.2 partial-wall baselines must be horizontal: only the
    # horizontal high-platform parapet is geometry; inclined stair parapets
    # remain documented on their stair evidence.
    assert ids == {"m2-platform-outer-parapet"}
    wall = raw["partial_wall_segments"][0]
    assert wall["start"]["z"] == wall["end"]["z"]
    stair_evidence = " ".join(
        evidence["observation"]
        for stair in raw["stairs"]
        for evidence in stair["evidence"]
    ).lower()
    assert "parapet" in stair_evidence
    assert "inclined-parapet primitive" in stair_evidence

    viewer = VIEWER_PATH.read_text(encoding="utf-8")
    assert "group.scale.z = -1" in viewer
    assert "new URLSearchParams(window.location.search).get('scene')" in viewer
    assert "renderVolumes(); renderOpenings(); renderPlatforms();" in viewer
