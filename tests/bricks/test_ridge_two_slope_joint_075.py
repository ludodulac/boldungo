"""075: a bridge tile may not mate with two sets of identical studs at once."""
from pathlib import Path

import pytest
from lego_geometry_engine import LDrawLibrary

from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.ridge_two_slope_joint_075 import assess_two_slope_ridge_connection


def slope(pid, side, x, y, z, rotation=0, part_id="BRICK_SLOPED_18_4X2"):
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
        building_id="different-gable", volume_id="main",
        width_studs=110, depth_studs=110, height_plates=180,
        parts=list(parts),
    )


def support_stack(x, y, top):
    return [wall(f"wall-{z}", x, y, z)
            for z in range(0, top + 1, 3)]


def gable(shift=0, anchored=True):
    return house(
        slope("negative", "negative", 38 + shift, 0, 117),
        slope("positive", "positive", 39 + shift, 0, 117),
        *(support_stack(40 + shift, 0, 111)
          if anchored else [wall("floating", 40 + shift, 0, 111)]),
    )


def perpendicular():
    return house(
        slope("negative", "negative", 14, 2, 93, 1),
        slope("positive", "positive", 14, 2, 93, 1),
        *support_stack(14, 3, 87),
    )


def test_actual_30363_and_3002_compete_for_same_stud_cylinders():
    m = gable()
    before = m.model_dump_json()
    r = assess_two_slope_ridge_connection(m)
    assert r["proposed_sites"] == 1
    assert r["sites_checked"] == 1
    site = r["sites"][0]
    assert site["ridge_part"] == "TILE_2X3"
    assert site["status"] == "INVALID_DUPLICATED_STUD_OCCUPANCY"
    assert site["two_slope_stud_overlap_count"] == 4
    assert site["headpiece_stud_count"] == 6
    assert site["shared_stud_cells_by_side"]["negative"]
    assert site["shared_stud_cells_by_side"]["positive"]
    assert all(z == 120 for side in ("negative", "positive")
               for _, _, z in site["shared_stud_cells_by_side"][side])
    assert site["two_slope_cover_clutch"].startswith("UNKNOWN")
    assert site["headpiece_to_cover_clutch"].startswith("UNKNOWN")
    assert "NARROW_1X1_POST" in site["alternative"]
    assert site["roof_support_path"] == "DOCUMENTED_NOMINAL_WALL_STUD_PATH_TO_Z0"
    assert r["physical_certification"] == "NOT_CERTIFIED"
    assert r["model_mutated"] is False
    assert m.model_dump_json() == before


def test_identical_blockage_in_a_different_house_location():
    m = gable(shift=11)
    r = assess_two_slope_ridge_connection(m)
    site = r["sites"][0]
    assert site["status"] == "INVALID_DUPLICATED_STUD_OCCUPANCY"
    assert sorted({x for side in ("negative", "positive")
                   for x, _, _ in site["shared_stud_cells_by_side"][side]}) == [50, 52]
    assert r["original_part_count"] == len(m.parts)


def test_unanchored_wall_does_not_create_false_bridge():
    m = gable(shift=20, anchored=False)
    r = assess_two_slope_ridge_connection(m)
    assert r["sites"][0]["status"] == "UNKNOWN_NO_SUPPORTED_3002_HEADPIECE"
    assert r["sites"][0]["roof_support_path"] == "UNKNOWN_NO_DOCUMENTED_WALL_LOAD_PATH"
    assert r["physical_certification"] == "NOT_CERTIFIED"


def test_rotated_gable_has_2x4_cover_so_2x3_head_not_assumed():
    m = perpendicular()
    before = m.model_dump_json()
    r = assess_two_slope_ridge_connection(m)
    assert r["proposed_sites"] == 1
    site = r["sites"][0]
    assert site["ridge_part"] == "TILE_2X4"
    assert site["status"] == "UNKNOWN_NO_SUPPORTED_3002_HEADPIECE"
    assert not any(site["shared_stud_cells_by_side"].values())
    assert m.model_dump_json() == before


def test_mono_pitch_has_no_invented_opposing_connector():
    m = house(slope("mono", "slope", 3, 5, 12,
                    part_id="BRICK_SLOPED_45_2X4"))
    r = assess_two_slope_ridge_connection(m)
    assert r["proposed_sites"] == 0
    assert r["sites"] == []
    assert r["physical_certification"] == "NOT_CERTIFIED"


def test_ldraw_probe_uses_existing_mesh_engine_but_does_not_override_stud_blocker():
    m = gable()
    library = LDrawLibrary(Path("lego_geometry_engine/tests/fixtures/ldraw"))
    r = assess_two_slope_ridge_connection(m, library)
    site = r["sites"][0]
    assert site["status"] == "INVALID_DUPLICATED_STUD_OCCUPANCY"
    assert len(site["mesh_pairs"]) == 5
    assert r["ldraw_mesh_pairs_checked"] == 5
    assert all(item["status"] in (
        "UNKNOWN_GEOMETRY_UNAVAILABLE",
        "MESH_INTERSECTION_REVIEW_REQUIRED",
        "MESH_CONTACT_REVIEW_REQUIRED",
        "MESH_SEPARATED",
    ) for item in site["mesh_pairs"])
    assert r["physical_certification"] == "NOT_CERTIFIED"


def test_mesh_budget_truncation_visible():
    r = assess_two_slope_ridge_connection(
        gable(), LDrawLibrary(Path("lego_geometry_engine/tests/fixtures/ldraw")),
        max_mesh_pairs=1)
    assert r["ldraw_mesh_pairs_checked"] == 1
    assert r["sites"][0]["mesh_budget_truncated"] is True
    assert r["sites"][0]["status"] == "INVALID_DUPLICATED_STUD_OCCUPANCY"


def test_invalid_budgets_refused():
    for kw in ({"max_sites": 0}, {"max_mesh_pairs": 0}):
        with pytest.raises(ValueError):
            assess_two_slope_ridge_connection(gable(), **kw)


def test_guided004_canonical_piece_count_and_content_unchanged():
    path = Path("artifacts/lego2-guided-004/brick-model.json")
    if not path.is_file():
        pytest.skip("real canonical export absent locally")
    model = BrickModel.model_validate_json(path.read_text(encoding="utf-8"))
    assert len(model.parts) == 1890
    before = model.model_dump_json()
    r = assess_two_slope_ridge_connection(model, max_sites=2)
    assert r["original_part_count"] == 1890
    assert r["model_mutated"] is False
    assert r["physical_certification"] == "NOT_CERTIFIED"
    assert model.model_dump_json() == before
