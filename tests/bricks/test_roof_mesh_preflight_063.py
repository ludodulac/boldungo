"""Small, bounded roof-mesh checks using existing LDraw test fixtures."""
from pathlib import Path

import pytest

from lego_geometry_engine import LDrawLibrary

from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.roof_mesh_preflight import (
    candidate_roof_pairs, preflight_roof_mesh,
)

FIXTURE = Path("lego_geometry_engine/tests/fixtures/ldraw")


def slope(name, side, x, y, z, part_id="BRICK_SLOPED_45_2X4"):
    return BrickModelPart(
        placement_id=name, part_id=part_id, category="roof_tile",
        component="roof", roof_side=side,
        x_studs=x, y_studs=y, z_plates=z, rotation_quarter_turns=0,
    )


def ridge(name, x, y, z):
    return BrickModelPart(
        placement_id=name, part_id="TILE_2X4", category="ridge_tile",
        component="roof", roof_side="ridge",
        x_studs=x, y_studs=y, z_plates=z, rotation_quarter_turns=0,
    )


def house(name, *parts):
    return BrickModel(building_id=name, volume_id="main",
                      width_studs=10, depth_studs=10, height_plates=20,
                      parts=list(parts))


def test_different_gable_house_uses_real_ldraw_mesh_on_one_pair():
    m = house("gable-45", slope("neg", "negative", 0, 0, 6),
              slope("pos", "positive", 1, 0, 6))
    result = preflight_roof_mesh(m, LDrawLibrary(FIXTURE), max_pairs=1)
    assert result["roof_candidate_pairs_discovered"] == 1
    assert result["pairs_examined"] == 1
    assert result["pairs"][0]["kind"] == "OPPOSING_SLOPES"
    assert result["pairs"][0]["mesh_relation"] in {"SEPARATED", "CONTACT", "COLLISION"}
    assert result["pairs"][0]["status"] != "UNKNOWN_GEOMETRY_UNAVAILABLE"
    assert result["physical_certification"] == "NOT_CERTIFIED"


def test_missing_real_ldraw_file_is_unknown_not_clearance():
    m = house("ridge-missing-ldraw", slope("s", "negative", 0, 0, 6),
              ridge("r", 0, 0, 9))
    result = preflight_roof_mesh(m, LDrawLibrary(FIXTURE), max_pairs=1)
    assert result["pairs"][0]["kind"] == "SLOPE_TO_RIDGE"
    assert result["pairs"][0]["status"] == "UNKNOWN_GEOMETRY_UNAVAILABLE"
    assert "FileNotFoundError" in result["pairs"][0]["reason"]


def test_mono_pitch_is_not_mistaken_for_valid_or_ridge_required():
    # The current LDraw slope adapter is explicit about requiring a known
    # orientation side. A shed roof stays UNKNOWN until its transform is mapped.
    m = house("shed", slope("s1", "slope", 0, 0, 3),
              slope("s2", "slope", 1, 0, 3))
    result = preflight_roof_mesh(m, LDrawLibrary(FIXTURE))
    assert result["pairs"][0]["kind"] == "ADJACENT_ROOF_PIECES"
    assert result["pairs"][0]["status"] == "UNKNOWN_GEOMETRY_UNAVAILABLE"
    assert result["physical_certification"] == "NOT_CERTIFIED"


def test_candidate_prioritization_and_short_bounded_sample():
    m = house("multiple-roof", slope("a", "negative", 0, 0, 6),
              slope("b", "positive", 0, 0, 6),
              slope("c", "negative", 0, 0, 9),
              ridge("r", 0, 0, 12))
    candidates, truncated, unsupported = candidate_roof_pairs(m)
    assert not truncated and not unsupported
    assert candidates[0][2] == "OPPOSING_SLOPES"
    result = preflight_roof_mesh(m, LDrawLibrary(FIXTURE), max_pairs=1)
    assert result["pairs_examined"] == 1
    assert result["examination_truncated"]
    assert result["roof_candidate_pairs_discovered"] > 1


def test_invalid_max_pairs_rejected_and_empty_no_roof_is_not_certified():
    m = house("only-wall", BrickModelPart(
        placement_id="wall", part_id="BRICK_1X1", category="brick",
        component="wall", facade="front", x_studs=0, y_studs=0,
        z_plates=0, rotation_quarter_turns=0))
    with pytest.raises(ValueError, match="max_pairs"):
        preflight_roof_mesh(m, LDrawLibrary(FIXTURE), max_pairs=0)
    result = preflight_roof_mesh(m, LDrawLibrary(FIXTURE))
    assert result["pairs_examined"] == 0
    assert result["roof_candidate_pairs_discovered"] == 0
    assert result["physical_certification"] == "NOT_CERTIFIED"
