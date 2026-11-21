"""076: bounded, non-mutating validation of a central 1x1 roof post."""
from pathlib import Path

import pytest
from lego_geometry_engine import LDrawLibrary

from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.ridge_central_post_076 import assess_central_ridge_post


def roof(pid, side, x, y, z, rotation=0, part_id="BRICK_SLOPED_18_4X2"):
    return BrickModelPart(
        placement_id=pid, part_id=part_id, category="roof_tile",
        component="roof", roof_side=side, x_studs=x, y_studs=y,
        z_plates=z, rotation_quarter_turns=rotation,
    )


def wall(pid, x, y, z):
    return BrickModelPart(
        placement_id=pid, part_id="BRICK_1X1", category="brick",
        component="wall", facade="front", x_studs=x, y_studs=y,
        z_plates=z, rotation_quarter_turns=0,
    )


def house(*parts):
    return BrickModel(
        building_id="different-house", volume_id="v",
        width_studs=100, depth_studs=100, height_plates=180,
        parts=list(parts),
    )


def anchored(x, y, top):
    return [wall(f"support-{x}-{y}-{z}", x, y, z)
            for z in range(0, top+1, 3)]


def pitched(shift=0, anchor=True):
    return house(
        roof("neg", "negative", 38+shift, 0, 117),
        roof("pos", "positive", 39+shift, 0, 117),
        *(anchored(40+shift, 0, 111)
          if anchor else [wall("floating", 40+shift, 0, 111)]),
    )


def perpendicular():
    return house(
        roof("neg", "negative", 14, 2, 93, 1),
        roof("pos", "positive", 14, 2, 93, 1),
        *anchored(14, 3, 87),
    )


def test_real_central_1x1_has_distinct_stud_cells_and_nominal_wall_path():
    m = pitched()
    before = m.model_dump_json()
    result = assess_central_ridge_post(m)
    assert result["sites_checked"] == 1
    row = result["sites"][0]
    assert row["tile_part_id"] == "TILE_2X3"
    assert row["post_cell"] == [40, 0]
    assert row["post_top_plane"] == 120
    assert row["post_count"] == 2
    assert row["studs_distinct_from_both_slopes"] is True
    assert row["two_slope_studs_documented"] is True
    assert row["stud_overlap_with_slopes"] == []
    assert row["slope_ids"] == {"negative": ["neg"], "positive": ["pos"]}
    assert row["anchor_chain"]["status"] == "DOCUMENTED_NOMINAL_WALL_STUD_PATH_TO_Z0"
    assert row["anchor_chain"]["route_base_to_anchor"][0] == "support-40-0-0"
    assert row["post_connector_statuses"] == ["VALID", "VALID"]
    assert row["post_to_tile"].startswith("UNKNOWN")
    assert row["tile_to_negative_slope"].startswith("UNKNOWN")
    assert row["tile_to_positive_slope"].startswith("UNKNOWN")
    assert row["status"] == "UNKNOWN_THREE_PART_CLUTCH_NOT_DEMONSTRATED"
    assert result["physical_certification"] == "NOT_CERTIFIED"
    assert result["model_mutated"] is False
    assert result["original_part_count"] == len(m.parts)
    assert m.model_dump_json() == before


def test_other_house_position_uses_actual_geometry_not_hardcoded_40():
    m = pitched(shift=12)
    r = assess_central_ridge_post(m)
    row = r["sites"][0]
    assert row["post_cell"] == [52, 0]
    assert row["stud_overlap_with_slopes"] == []
    assert row["status"] == "UNKNOWN_THREE_PART_CLUTCH_NOT_DEMONSTRATED"


def test_second_roof_orientation_2x4_underside_is_not_invented():
    m = perpendicular()
    before = m.model_dump_json()
    r = assess_central_ridge_post(m)
    assert r["sites_checked"] == 1
    row = r["sites"][0]
    assert row["tile_part_id"] == "TILE_2X4"
    assert row["post_cell"] == [14, 3]
    assert row["post_top_plane"] == 96
    assert row["stud_overlap_with_slopes"] == []
    assert row["post_to_tile"] == "UNKNOWN_UNREVIEWED_OTHER_TILE_UNDERSIDE"
    assert row["status"] == "UNKNOWN_THREE_PART_CLUTCH_NOT_DEMONSTRATED"
    assert m.model_dump_json() == before


def test_floating_wall_cannot_support_a_ridge_even_if_xy_matches():
    m = pitched(shift=8, anchor=False)
    row = assess_central_ridge_post(m)["sites"][0]
    assert row["status"] == "UNKNOWN_NO_DOCUMENTED_CENTRAL_SUPPORT"
    assert row["anchor_chain"]["status"] == "UNKNOWN_NO_DOCUMENTED_WALL_LOAD_PATH"
    assert row["post_count"] == 0
    assert "studs_distinct_from_both_slopes" not in row


def test_missing_opposing_slope_has_no_two_slope_ridge_proposal():
    m = house(roof("one-side", "negative", 38, 0, 117),
              *anchored(40, 0, 111))
    r = assess_central_ridge_post(m)
    assert r["sites"] == []
    assert r["physical_certification"] == "NOT_CERTIFIED"


def test_mono_pitch_requires_no_opposing_ridge_support():
    m = house(roof("mono", "slope", 5, 6, 12,
                   part_id="BRICK_SLOPED_45_2X4"))
    r = assess_central_ridge_post(m)
    assert r["sites_checked"] == 0
    assert r["mesh_pairs_checked"] == 0


def test_ldraw_geometry_unavailable_is_not_accidental_clutch_approval():
    m = pitched()
    before = m.model_dump_json()
    lib = LDrawLibrary(Path("lego_geometry_engine/tests/fixtures/ldraw"))
    r = assess_central_ridge_post(m, lib)
    row = r["sites"][0]
    assert row["status"] in (
        "UNKNOWN_LDRAW_GEOMETRY_UNAVAILABLE",
        "REVIEW_REQUIRED_LDRAW_MESH_INTERSECTION",
        "REVIEW_REQUIRED_EXISTING_POST_ROOF_MESH_INTERSECTION",
    )
    assert r["mesh_pairs_checked"] >= 3
    assert row["mesh_pairs_required"] >= 3
    assert all(check["status"] in (
        "UNKNOWN_GEOMETRY_UNAVAILABLE", "MESH_INTERSECTION_REVIEW_REQUIRED",
        "MESH_CONTACT_REVIEW_REQUIRED", "MESH_SEPARATED",
    ) for check in row["mesh_checks"])
    assert r["physical_certification"] == "NOT_CERTIFIED"
    assert m.model_dump_json() == before


def test_mesh_intersection_causes_review_not_fabricated_valid(monkeypatch):
    def pretend_collision(a, b, library, cache, relations):
        return {"part_a": a.placement_id, "part_b": b.placement_id,
                "status": "MESH_INTERSECTION_REVIEW_REQUIRED",
                "mesh_relation": "COLLISION"}
    monkeypatch.setattr("brickhouse.bricks.ridge_central_post_076._pair",
                        pretend_collision)
    lib = LDrawLibrary(Path("lego_geometry_engine/tests/fixtures/ldraw"))
    r = assess_central_ridge_post(pitched(), lib)
    row = r["sites"][0]
    assert row["status"] == "REVIEW_REQUIRED_LDRAW_MESH_INTERSECTION"
    assert row["stud_overlap_with_slopes"] == []
    assert r["physical_certification"] == "NOT_CERTIFIED"


def test_mesh_budget_exhaustion_is_visible_and_not_a_success():
    r = assess_central_ridge_post(
        pitched(), LDrawLibrary(Path("lego_geometry_engine/tests/fixtures/ldraw")),
        max_mesh_pairs=1)
    row = r["sites"][0]
    assert row["status"] == "UNKNOWN_INCOMPLETE_LDRAW_BUDGET"
    assert row["mesh_budget_truncated"] is True
    assert r["physical_certification"] == "NOT_CERTIFIED"


def test_reject_invalid_budgets():
    for options in ({"max_sites": 0}, {"max_mesh_pairs": 0}):
        with pytest.raises(ValueError):
            assess_central_ridge_post(pitched(), **options)


def test_guided004_1890_parts_not_modified():
    p = Path("artifacts/lego2-guided-004/brick-model.json")
    if not p.is_file():
        pytest.skip("canonical 1890-piece model not available")
    m = BrickModel.model_validate_json(p.read_text(encoding="utf-8"))
    assert len(m.parts) == 1890
    before = m.model_dump_json()
    r = assess_central_ridge_post(m, max_sites=2)
    assert r["original_part_count"] == 1890
    assert r["model_mutated"] is False
    assert r["physical_certification"] == "NOT_CERTIFIED"
    assert m.model_dump_json() == before
