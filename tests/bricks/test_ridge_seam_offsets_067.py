"""Mission 067: bounded, non-mutating roof seam placement experiments."""
from pathlib import Path

import pytest

from lego_geometry_engine import LDrawLibrary
from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.ridge_seam_offsets_067 import probe_ridge_seam_offsets


FIXTURE = Path("lego_geometry_engine/tests/fixtures/ldraw")


def slope(pid, side, x, y, z, turns=0):
    return BrickModelPart(
        placement_id=pid, part_id="BRICK_SLOPED_18_4X2",
        component="roof", category="roof_tile", roof_side=side,
        x_studs=x, y_studs=y, z_plates=z,
        rotation_quarter_turns=turns,
    )


def house(name, *parts):
    return BrickModel(
        building_id=name, volume_id="main", width_studs=70,
        depth_studs=50, height_plates=125, parts=list(parts),
    )


def test_straight_gable_exposes_potential_3_stud_gap_fix_without_changing_original():
    model = house(
        "test-gable",
        slope("neg", "negative", 38, 0, 117),
        slope("pos", "positive", 39, 0, 117),
        slope("prev", "positive", 42, 0, 114),
    )
    before = model.model_dump_json()
    r = probe_ridge_seam_offsets(model, LDrawLibrary(FIXTURE), max_offset=4)
    assert r["status"] == "LOCAL_EXPERIMENT_ONLY"
    assert len(r["offsets"]) == 5
    assert r["previous_course_ids"] == ["prev"]
    assert r["shift_axis"] == "x"
    o = r["offsets"]
    assert o[0]["bridge_candidate"]["part_id"] == "TILE_2X3"
    assert o[0]["bridge_candidate"]["x_studs"] == 39
    assert o[2]["bridge_candidate"] is None
    assert o[2]["bridge_unavailable_reason"] == "NO_SUPPORTED_2_TO_4_WIDE_TILE"
    assert o[3]["bridge_candidate"]["part_id"] == "TILE_2X2"
    assert o[3]["bridge_candidate"]["x_studs"] == 41
    assert all(x["slopes_mesh"]["status"] == "UNKNOWN_GEOMETRY_UNAVAILABLE" for x in o)
    assert r["physical_certification"] == "NOT_CERTIFIED"
    assert r["model_mutated"] is False
    assert model.model_dump_json() == before


def test_perpendicular_gable_uses_y_shift_without_guessed_roof_orientation():
    model = house("test-rotated",
                  slope("neg", "negative", 14, 2, 93, turns=1),
                  slope("pos", "positive", 14, 3, 93, turns=1))
    r = probe_ridge_seam_offsets(model, LDrawLibrary(FIXTURE), max_offset=3)
    assert r["shift_axis"] == "y"
    assert len(r["offsets"]) == 4
    assert r["offsets"][0]["bridge_candidate"]["part_id"] == "TILE_2X3"
    assert r["offsets"][3]["bridge_candidate"]["part_id"] == "TILE_2X2"
    assert r["offsets"][3]["bridge_candidate"]["rotation_quarter_turns"] == 0


def test_no_gable_remains_uncertified_not_repaired():
    model = house("single-slope", slope("only", "negative", 0, 0, 9))
    r = probe_ridge_seam_offsets(model, LDrawLibrary(FIXTURE))
    assert r["status"] == "NO_PROPOSAL_AT_INDEX"
    assert r["physical_certification"] == "NOT_CERTIFIED"


def test_short_execution_limits_and_rejection():
    model = house("test", slope("neg", "negative", 38, 0, 117),
                  slope("pos", "positive", 39, 0, 117))
    with pytest.raises(ValueError, match="max_offset"):
        probe_ridge_seam_offsets(model, LDrawLibrary(FIXTURE), max_offset=5)
    r = probe_ridge_seam_offsets(model, LDrawLibrary(FIXTURE), max_offset=0)
    assert len(r["offsets"]) == 1


def test_canonical_ridge_uses_correct_real_placements_when_available():
    path = Path("artifacts/lego2-guided-004/brick-model.json")
    if not path.exists():
        pytest.skip("real export not present")
    model = BrickModel.model_validate_json(path.read_text())
    assert len(model.parts) == 1890
    r = probe_ridge_seam_offsets(model, LDrawLibrary(FIXTURE), max_offset=3)
    assert r["base_pair"] == ["roof-000185", "roof-000392"]
    assert r["previous_course_ids"] == ["roof-000369"]
    assert len(r["offsets"]) == 4
    assert r["offsets"][3]["bridge_candidate"]["part_id"] == "TILE_2X2"
    assert r["physical_certification"] == "NOT_CERTIFIED"
