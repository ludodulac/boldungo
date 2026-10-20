"""069: Global roof-side shift is not a valid apex fix if eaves lose support."""
from pathlib import Path

from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.roof_eave_shift_069 import assess_whole_side_shift


def slope(pid, x, y, z, rotation=0):
    return BrickModelPart(
        placement_id=pid, part_id="BRICK_SLOPED_18_4X2",
        category="roof_tile", component="roof", roof_side="positive",
        x_studs=x, y_studs=y, z_plates=z,
        rotation_quarter_turns=rotation,
    )


def wall(pid, x, y, z=90):
    return BrickModelPart(
        placement_id=pid, part_id="BRICK_1X1",
        category="brick", component="wall", facade="front",
        x_studs=x, y_studs=y, z_plates=z, rotation_quarter_turns=0,
    )


def house(*parts):
    return BrickModel(building_id="different-house", volume_id="v",
                      width_studs=90, depth_studs=90,
                      height_plates=140, parts=list(parts))


def test_moving_all_positive_courses_breaks_support_at_eave():
    m = house(slope("eave", 63, 0, 93),
              slope("course1", 60, 0, 96),
              slope("course2", 57, 0, 99),
              wall("wall-at-eave", 63, 0))
    saved = m.model_dump_json()
    r = assess_whole_side_shift(m, shift_studs=3)
    assert r["status"] == "REJECTED_LOST_EAVE_ANCHORS"
    assert r["original_supported_eave_parts"] == 1
    assert r["shifted_supported_eave_parts"] == 0
    assert r["originally_supported_now_unsupported"] == ["eave"]
    assert r["physical_certification"] == "NOT_CERTIFIED"
    assert r["model_mutated"] is False
    assert m.model_dump_json() == saved


def test_aligned_shift_may_retain_anchor_but_does_not_certify_buildability():
    m = house(slope("eave", 63, 0, 93), wall("wide-support", 63, 0),
              wall("other-support", 66, 0))
    r = assess_whole_side_shift(m, shift_studs=3)
    assert r["status"] == "EAVE_PROJECTION_PRESERVED_ONLY"
    assert r["originally_supported_now_unsupported"] == []
    assert r["physical_certification"] == "NOT_CERTIFIED"


def test_no_wall_geometry_must_stay_unknown():
    m = house(slope("eave", 63, 0, 93))
    r = assess_whole_side_shift(m, shift_studs=3)
    assert r["status"] == "UNKNOWN_NO_DOCUMENTED_ORIGINAL_EAVE_ANCHORS"


def test_perpendicular_roof_shifts_along_y_and_does_not_use_house_specific_coords():
    m = house(slope("eave", 15, 63, 93, 1), wall("original-anchor", 15, 63))
    r = assess_whole_side_shift(m, shift_studs=3)
    assert r["shift_axis"] == "y"
    assert r["status"] == "REJECTED_LOST_EAVE_ANCHORS"


def test_exported_1890_piece_guided004_declines_plus_three_shift():
    p = Path("artifacts/lego2-guided-004/brick-model.json")
    if not p.is_file():
        import pytest
        pytest.skip("real GUIDED-004 export not in checkout")
    model = BrickModel.model_validate_json(p.read_text())
    assert len(model.parts) == 1890
    before = model.model_dump_json()
    r = assess_whole_side_shift(model, shift_studs=3)
    assert r["status"] == "REJECTED_LOST_EAVE_ANCHORS"
    assert r["original_supported_eave_parts"] > 0
    assert r["shifted_supported_eave_parts"] == 0
    assert r["originally_supported_now_unsupported"]
    assert r["physical_certification"] == "NOT_CERTIFIED"
    assert model.model_dump_json() == before
