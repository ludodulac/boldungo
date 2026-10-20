"""072: documented 1x1 -> 2x3 load-spreader, not a ridge certificate."""
from pathlib import Path

import pytest
from lego_geometry_engine import LDrawLibrary

from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.ridge_cap_adapter_072 import assess_ridge_cap_adapters


def sloped(pid, side, x, y, z, rotation=0, part_id="BRICK_SLOPED_18_4X2"):
    return BrickModelPart(
        placement_id=pid, part_id=part_id, category="roof_tile",
        component="roof", roof_side=side, x_studs=x, y_studs=y,
        z_plates=z, rotation_quarter_turns=rotation,
    )


def wall(pid, x, y, z, part_id="BRICK_1X1"):
    return BrickModelPart(
        placement_id=pid, part_id=part_id, category="brick",
        component="wall", facade="front", x_studs=x, y_studs=y,
        z_plates=z, rotation_quarter_turns=0,
    )


def connected_wall(x, y, host_z):
    return [wall(f"ground-chain-{z}", x, y, z)
            for z in range(0, host_z + 1, 3)]


def house(*parts):
    return BrickModel(
        building_id="non-guided-architecture", volume_id="v",
        width_studs=100, depth_studs=100, height_plates=180,
        parts=list(parts),
    )


def normal_gable(*hosts):
    return house(
        sloped("neg", "negative", 38, 0, 117),
        sloped("pos", "positive", 39, 0, 117), *hosts,
    )


def test_headpiece_part_3002_is_on_nominally_connected_1x1_post():
    model = normal_gable(*connected_wall(40, 0, 111))
    saved = model.model_dump_json()
    result = assess_ridge_cap_adapters(model)
    assert result["sites_checked"] == 1
    site = result["sites"][0]
    assert site["status"] == "UNKNOWN_LDRAW_LIBRARY_REQUIRED"
    assert site["existing_wall_anchor"] == "ground-chain-111"
    assert site["host_support_path"] == "DOCUMENTED_NOMINAL_WALL_STUD_PATH_TO_Z0"
    assert site["lower_post_to_headpiece"] == "VALID"
    assert site["headpiece"]["ldraw_id"] == "3002"
    assert site["headpiece"]["part_id"] == "BRICK_2X3"
    assert (site["headpiece"]["x_studs"], site["headpiece"]["y_studs"],
            site["headpiece"]["z_plates"],
            site["headpiece"]["rotation_quarter_turns"]) == (39, 0, 117, 1)
    assert site["replaces_experimental_post_top"] is True
    assert site["headpiece_to_ridge_tile"].startswith("UNKNOWN")
    assert site["roof_slope_connections"].startswith("UNKNOWN")
    assert site["torsional_stability"] == "UNKNOWN_NOT_MEASURED"
    assert result["physical_certification"] == "NOT_CERTIFIED"
    assert result["original_part_count"] == len(model.parts)
    assert result["model_mutated"] is False
    assert model.model_dump_json() == saved


def test_second_roof_orientation_places_real_cap_without_shifting_roof():
    m = house(sloped("neg", "negative", 14, 2, 93, 1),
              sloped("pos", "positive", 14, 2, 93, 1),
              *connected_wall(14, 3, 87))
    before = m.model_dump_json()
    r = assess_ridge_cap_adapters(m)
    assert r["sites_checked"] == 1
    site = r["sites"][0]
    assert site["lower_post_to_headpiece"] == "VALID"
    assert (site["headpiece"]["x_studs"], site["headpiece"]["y_studs"],
            site["headpiece"]["z_plates"],
            site["headpiece"]["rotation_quarter_turns"]) == (14, 2, 93, 0)
    assert m.model_dump_json() == before


def test_no_wall_anchor_stops_cap_proposal():
    m = normal_gable(wall("floating", 40, 0, 111))
    r = assess_ridge_cap_adapters(m)
    assert r["sites"][0]["headpiece"] is None
    assert r["sites"][0]["status"] == "UNKNOWN_NO_VALID_POST_FOR_CAP"


def test_one_post_length_stays_unresolved_without_reconfiguring_wall():
    m = normal_gable(*connected_wall(40, 0, 114))
    r = assess_ridge_cap_adapters(m)
    assert r["sites"][0]["status"] == "UNKNOWN_NO_ROOM_FOR_HEADPIECE"
    assert r["sites"][0]["headpiece"] is None


def test_existing_ldraw_mesh_gate_uses_actual_parts_and_never_proves_clutch():
    m = normal_gable(*connected_wall(40, 0, 111))
    before = m.model_dump_json()
    library = LDrawLibrary(Path("lego_geometry_engine/tests/fixtures/ldraw"))
    r = assess_ridge_cap_adapters(m, library=library)
    site = r["sites"][0]
    assert site["mesh_pairs_required"] >= 1
    assert r["mesh_pairs_checked"] == site["mesh_pairs_required"]
    assert any("EXPERIMENT-072-TILE" in
               (check["part_a"] + check["part_b"])
               for check in site["mesh_checks"])
    assert site["status"] in (
        "MESH_INTERSECTION_REVIEW_REQUIRED",
        "UNKNOWN_UNREVIEWED_OR_MISSING_LDRAW_GEOMETRY",
        "HEADPIECE_MESH_SCREEN_ONLY_CLUTCH_UNKNOWN",
    )
    assert site["headpiece_to_ridge_tile"] == "UNKNOWN_UNREVIEWED_TILE_UNDERSIDE"
    assert r["physical_certification"] == "NOT_CERTIFIED"
    assert m.model_dump_json() == before


def test_mesh_budget_fail_closed():
    m = normal_gable(*connected_wall(40, 0, 111))
    r = assess_ridge_cap_adapters(
        m, LDrawLibrary(Path("lego_geometry_engine/tests/fixtures/ldraw")),
        max_mesh_pairs=1,
    )
    assert r["sites"][0]["mesh_pairs_required"] > 1
    assert r["sites"][0]["status"] == "UNKNOWN_MESH_BUDGET_EXCEEDED"
    assert r["mesh_pairs_checked"] == 0


def test_mono_pitch_needs_no_two_sided_ridge():
    m = house(sloped("mono", "slope", 5, 3, 12, part_id="BRICK_SLOPED_45_2X4"))
    r = assess_ridge_cap_adapters(m)
    assert r["sites_checked"] == 0
    assert r["original_part_count"] == 1
    assert r["physical_certification"] == "NOT_CERTIFIED"


def test_guided004_1890_parts_are_not_modified():
    p = Path("artifacts/lego2-guided-004/brick-model.json")
    if not p.exists():
        pytest.skip("GUIDED-004 canonical export not present in this checkout")
    model = BrickModel.model_validate_json(p.read_text(encoding="utf-8"))
    assert len(model.parts) == 1890
    before = model.model_dump_json()
    r = assess_ridge_cap_adapters(model, max_sites=2)
    assert r["original_part_count"] == 1890
    assert r["model_mutated"] is False
    assert r["physical_certification"] == "NOT_CERTIFIED"
    assert model.model_dump_json() == before


def test_invalid_limits():
    m = normal_gable(*connected_wall(40, 0, 111))
    with pytest.raises(ValueError):
        assess_ridge_cap_adapters(m, max_sites=0)
    with pytest.raises(ValueError):
        assess_ridge_cap_adapters(m, max_mesh_pairs=0)
