"""068: full-length ridge analysis, no unauthorized geometry changes."""
from pathlib import Path

import pytest

from lego_geometry_engine import LDrawLibrary
from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.ridge_full_length_audit_068 import audit_full_ridge

FIXTURE = Path("lego_geometry_engine/tests/fixtures/ldraw")


def slope(pid, side, x, y, z, turns=0):
    return BrickModelPart(
        placement_id=pid, part_id="BRICK_SLOPED_18_4X2",
        category="roof_tile", component="roof", roof_side=side,
        x_studs=x, y_studs=y, z_plates=z, rotation_quarter_turns=turns,
    )


def house(*parts, name="general-house"):
    return BrickModel(
        building_id=name, volume_id="main", width_studs=80,
        depth_studs=60, height_plates=130, parts=list(parts),
    )


def test_all_three_longitudinal_sites_and_two_shifted_neighbors():
    model = house(*[
        slope(f"{side}-{i}", side, x, i * 2, 117)
        for side, x in (("negative", 38), ("positive", 39))
        for i in range(3)
    ])
    before = model.model_dump_json()
    r = audit_full_ridge(model, LDrawLibrary(FIXTURE), max_sites=25)
    assert r["status"] == "ALL_PROPOSALS_SAMPLED"
    assert r["proposed_sites"] == 3
    assert r["evaluated_sites"] == 3
    assert r["not_evaluated_sites"] == 0
    assert len(r["sites"]) == 3
    assert [x["positive_id"] for x in r["sites"]] == [
        "positive-0", "positive-1", "positive-2"
    ]
    assert all(x["status"] == "UNKNOWN" for x in r["sites"])
    assert len(r["adjacent_shifted_tile_checks"]) == 2
    assert all(x["mesh_relation"] == "UNKNOWN" for x in r["adjacent_shifted_tile_checks"])
    assert r["physical_certification"] == "NOT_CERTIFIED"
    assert r["model_mutated"] is False
    assert before == model.model_dump_json()


def test_sampling_limit_is_explicit_and_not_claimed_complete():
    model = house(*[
        slope(f"{side}-{i}", side, x, i * 2, 117)
        for side, x in (("negative", 38), ("positive", 39))
        for i in range(3)
    ])
    r = audit_full_ridge(model, LDrawLibrary(FIXTURE), max_sites=1)
    assert r["status"] == "PARTIAL_SAMPLE"
    assert r["evaluated_sites"] == 1
    assert r["not_evaluated_sites"] == 2
    assert r["adjacent_shifted_tile_checks"] == []


def test_only_mono_pitch_needs_no_two_sided_ridge():
    model = house(slope("single", "negative", 0, 0, 6))
    r = audit_full_ridge(model, LDrawLibrary(FIXTURE))
    assert r["status"] == "NO_PROPOSED_RIDGE_SITES"
    assert r["physical_certification"] == "NOT_CERTIFIED"


def test_invalid_budget_and_offset_explicit():
    model = house(slope("a", "negative", 38, 0, 117),
                  slope("b", "positive", 39, 0, 117))
    with pytest.raises(ValueError, match="max_sites"):
        audit_full_ridge(model, LDrawLibrary(FIXTURE), max_sites=0)
    with pytest.raises(ValueError, match="shift_studs"):
        audit_full_ridge(model, LDrawLibrary(FIXTURE), shift_studs=7)


def test_real_guided004_all_23_candidates_covered_without_mutation():
    path = Path("artifacts/lego2-guided-004/brick-model.json")
    if not path.exists():
        pytest.skip("real GUIDED-004 export missing in this checkout")
    model = BrickModel.model_validate_json(path.read_text())
    assert len(model.parts) == 1890
    before = model.model_dump_json()
    r = audit_full_ridge(model, LDrawLibrary(FIXTURE), max_sites=25)
    assert r["status"] == "ALL_PROPOSALS_SAMPLED"
    assert r["proposed_sites"] == r["evaluated_sites"] == 23
    assert r["not_evaluated_sites"] == 0
    assert len(r["adjacent_shifted_tile_checks"]) == 22
    assert r["existing_ridge_pieces"] == 12
    assert r["hypothetical_bridge_pieces"] == 23
    assert r["sites"][0]["negative_id"] == "roof-000185"
    assert r["sites"][0]["positive_id"] == "roof-000392"
    assert all(x["shift_studs"] == 3 for x in r["sites"])
    assert r["physical_certification"] == "NOT_CERTIFIED"
    assert r["model_mutated"] is False
    assert before == model.model_dump_json()


def test_shift_of_only_highest_course_breaks_required_roof_pitch():
    model = house(
        slope("neg", "negative", 38, 0, 117),
        slope("pos", "positive", 39, 0, 117),
        slope("previous", "positive", 42, 0, 114),
    )
    original = model.model_dump_json()
    r = audit_full_ridge(model, LDrawLibrary(FIXTURE), max_sites=1)
    site = r["sites"][0]
    profile = site["course_advance_validation"]
    assert profile["family"] == "18"
    assert profile["required_advance_studs"] == 3
    assert profile["original_advance_studs"] == 3
    assert profile["shifted_advance_studs"] == 0
    assert site["status"] == "BROKEN_ROOF_COURSE_GEOMETRY"
    assert r["nominal_course_geometry_counts"] == {
        "BROKEN_NOMINAL_COURSE_ADVANCE": 1
    }
    assert r["physical_certification"] == "NOT_CERTIFIED"
    assert model.model_dump_json() == original
