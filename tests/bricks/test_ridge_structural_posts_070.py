"""070: limited structural ridge post design, not physical certification."""
from pathlib import Path

import pytest
from lego_geometry_engine import LDrawLibrary
from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.ridge_structural_posts_070 import assess_structural_ridge_posts


def roof(pid, side, x, y, z, rotation=0, part_id="BRICK_SLOPED_18_4X2"):
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


def house(*parts):
    return BrickModel(
        building_id="any-house", volume_id="v", width_studs=80,
        depth_studs=80, height_plates=150, parts=list(parts),
    )


def gable(*other):
    return house(roof("neg", "negative", 38, 0, 117),
                 roof("pos", "positive", 39, 0, 117), *other)


def anchored_wall(x, y, top):
    # True nominal path to global model z=0; not a foundation certificate.
    return [wall(f"support-{x}-{y}-{z}", x, y, z)
            for z in range(0, top, 3)]


def test_real_wall_top_uses_existing_1x1_parts_not_moving_roof():
    model = gable(*anchored_wall(40, 0, 111), wall("host", 40, 0, 111))
    before = model.model_dump_json()
    r = assess_structural_ridge_posts(model)
    assert r["candidate_cover_count"] == 1
    site = r["sites"][0]
    assert site["anchor_id"] == "host"
    assert site["post_cell"] == [40, 0]
    assert [(p["part_id"], p["z_plates"]) for p in site["post_parts"]] == [
        ("BRICK_1X1", 114), ("BRICK_1X1", 117)]
    assert site["post_connector_statuses"] == ["VALID", "VALID"]
    assert site["status"] == "UNKNOWN_LDRAW_LIBRARY_REQUIRED"
    assert site["lid_to_slopes"].startswith("UNKNOWN")
    assert site["post_to_lid"].startswith("UNKNOWN")
    assert site["insertion"].startswith("UNKNOWN")
    assert r["original_part_count"] == len(model.parts)
    assert site["host_support_path"]["status"] == "DOCUMENTED_NOMINAL_WALL_STUD_PATH_TO_Z0"
    assert site["host_support_path"]["route_base_to_anchor"][0] == "support-40-0-0"
    assert site["host_support_path"]["ground_foundation"].startswith("UNKNOWN")
    assert r["physical_certification"] == "NOT_CERTIFIED"
    assert r["model_mutated"] is False
    assert model.model_dump_json() == before


def test_perpendicular_roof_axis_uses_real_interior_row_and_wall():
    m = house(roof("neg", "negative", 14, 2, 93, 1),
              roof("pos", "positive", 14, 2, 93, 1),
              *anchored_wall(14, 3, 87), wall("host", 14, 3, 87))
    r = assess_structural_ridge_posts(m)
    assert r["candidate_cover_count"] == 1
    site = r["sites"][0]
    assert site["ridge_tile"]["rotation_quarter_turns"] == 0
    assert site["post_cell"] == [14, 3]
    assert site["post_height_plates"] == 6


def test_no_existing_support_does_not_invent_floating_column():
    m = gable()
    r = assess_structural_ridge_posts(m)
    assert r["sites"][0]["status"] == "NO_EXISTING_ANCHOR_UNDER_RIDGE"
    assert r["sites"][0]["post_parts"] == []


def test_unreviewed_anchor_connector_is_not_promoted_to_valid():
    m = gable(wall("host", 40, 0, 111, "BRICK_1X4"))
    r = assess_structural_ridge_posts(m)
    assert r["sites"][0]["status"] == "UNKNOWN_OR_INVALID_POST_CONNECTORS"
    assert r["sites"][0]["post_connector_statuses"] == ["UNKNOWN", "VALID"]


def test_non_brick_height_fails_closed_without_fabricated_plate_joint():
    m = gable(wall("host", 40, 0, 110))
    r = assess_structural_ridge_posts(m)
    assert r["sites"][0]["status"] == "UNKNOWN_NON_BRICK_HEIGHT_REQUIRES_REDESIGN"
    assert r["sites"][0]["post_parts"] == []


def test_foreign_masonry_blocks_column_without_removing_existing_part():
    m = gable(*anchored_wall(40, 0, 111), wall("host", 40, 0, 111),
              wall("interfering", 40, 0, 119))
    before = m.model_dump_json()
    r = assess_structural_ridge_posts(m)
    assert r["sites"][0]["status"] == "BLOCKED_EXISTING_MASONRY"
    assert r["sites"][0]["blocking_host_ids"] == ["interfering"]
    assert m.model_dump_json() == before


def test_ldraw_is_required_and_missing_roof_mesh_stays_unknown():
    m = gable(*anchored_wall(40, 0, 111), wall("host", 40, 0, 111))
    lib = LDrawLibrary(Path("lego_geometry_engine/tests/fixtures/ldraw"))
    r = assess_structural_ridge_posts(m, lib)
    site = r["sites"][0]
    assert site["mesh_pairs_required"] >= 1
    assert site["status"] in (
        "UNKNOWN_INCOMPLETE_LDRAW_GEOMETRY",
        "BLOCKED_MESH_INTERSECTION_REQUIRES_REVIEW",
    )
    assert r["mesh_pairs_checked"] == site["mesh_pairs_required"]
    assert r["physical_certification"] == "NOT_CERTIFIED"


def test_mono_roof_not_falsely_required_to_have_two_sided_ridge():
    m = house(roof("mono", "slope", 4, 2, 12,
                   part_id="BRICK_SLOPED_45_2X4"))
    r = assess_structural_ridge_posts(m)
    assert r["roof_pattern"] == "MONO_PITCH"
    assert r["sites"] == []
    assert r["candidate_cover_count"] == 0


def test_limited_budget_and_non_mutation():
    m = gable(*anchored_wall(40, 0, 111), wall("host", 40, 0, 111))
    r = assess_structural_ridge_posts(
        m, LDrawLibrary(Path("lego_geometry_engine/tests/fixtures/ldraw")),
        max_mesh_pairs=1)
    assert r["sites"][0]["status"] == "UNKNOWN_MESH_BUDGET_EXCEEDED"
    assert r["mesh_pairs_checked"] == 0
    for kwargs in ({"max_sites": 0}, {"max_post_plates": 2},
                   {"max_mesh_pairs": 0}):
        with pytest.raises(ValueError):
            assess_structural_ridge_posts(m, **kwargs)


def test_guided004_remains_identical_and_never_certified():
    p = Path("artifacts/lego2-guided-004/brick-model.json")
    if not p.is_file():
        pytest.skip("canonical export not present in this checkout")
    model = BrickModel.model_validate_json(p.read_text(encoding="utf-8"))
    before = model.model_dump_json()
    assert len(model.parts) == 1890
    r = assess_structural_ridge_posts(model, max_sites=2)
    assert r["original_part_count"] == 1890
    assert r["model_mutated"] is False
    assert r["physical_certification"] == "NOT_CERTIFIED"
    assert model.model_dump_json() == before
