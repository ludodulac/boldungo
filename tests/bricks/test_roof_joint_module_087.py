"""LEGO2-087: test the first ACTUAL shared bridge between two roof slopes.

Only 3 existing LEGO parts. Do not promote nominal LEGO stud alignment
to clutch, stable roof, assembled notice or physical N6 certificate.
"""
import pytest

from brickhouse.bricks.roof_joint_module_087 import (
    propose_two_slope_bridge_087, screen_two_slope_ldraw_087,
    choose_bounded_two_slope_trial_087,
)


@pytest.mark.parametrize("gap,cap,rotation", [
    (0, "BRICK_2X2", 0), (0, "BRICK_2X2", 1),
    (1, "BRICK_2X3", 0), (1, "BRICK_2X3", 1),
])
def test_each_proposal_uses_four_distinct_exposed_30363_studs_and_ONE_real_cap(
        gap, cap, rotation):
    candidate = propose_two_slope_bridge_087(
        seam_gap_studs=gap, roof_rotation=rotation)
    model = candidate.model
    before = model.model_dump_json()
    assert len(model.parts) == 3
    assert [p.part_id for p in model.parts] == [
        "BRICK_SLOPED_18_4X2", "BRICK_SLOPED_18_4X2", cap]
    assert [p.roof_side for p in model.parts[:2]] == ["negative", "positive"]
    assert candidate.status == "NOMINAL_TWO_SIDED_STUD_ALIGNMENT_PHYSICAL_CLUTCH_UNTESTED"
    a = set(candidate.documented_slope_top_studs["negative"])
    b = set(candidate.documented_slope_top_studs["positive"])
    footprint = set(candidate.bridge_receiver_cells)
    assert len(a) == len(b) == 2
    assert len(a & b) == 0
    assert a | b <= footprint
    assert {p[2] for p in a | b} == {model.parts[2].z_plates}
    assert all(len(v) == 2 for v in candidate.nominal_engagement_studs.values())
    assert model.model_dump_json() == before
    assert candidate.report()["physical_certification"] == "NOT_CERTIFIED"


@pytest.mark.parametrize("rotation", [0, 1])
def test_translation_invariant_for_other_houses(rotation):
    a = propose_two_slope_bridge_087(roof_rotation=rotation)
    b = propose_two_slope_bridge_087(
        roof_rotation=rotation, x_studs=37, y_studs=51, z_plates=39)
    assert a.status == b.status
    a_studs = a.documented_slope_top_studs
    b_studs = b.documented_slope_top_studs
    for side in ("negative", "positive"):
        assert {(x + 29, y + 43, z + 39) for x, y, z in a_studs[side]} == set(b_studs[side])


def test_reject_non_supported_or_negative_parameters():
    for kwargs in ({"seam_gap_studs": -1}, {"seam_gap_studs": 2},
                   {"roof_rotation": 2}, {"roof_rotation": -1},
                   {"x_studs": -1}, {"y_studs": -1}, {"z_plates": -1}):
        with pytest.raises(ValueError):
            propose_two_slope_bridge_087(**kwargs)


def test_unverified_material_uses_no_fake_valid_clutch_claims():
    r = choose_bounded_two_slope_trial_087()
    assert r["candidates_tested"] == 4
    assert r["recommendation"].startswith("THREE_PIECE_HAND_ASSEMBLY_ONLY")
    assert r["no_purchase_certification"] is True
    assert r["physical_certification"] == "NOT_CERTIFIED"
    assert r["canonical_model_changed"] is False
    assert all(candidate["part_count"] == 3 for candidate in r["candidates"])
    assert all(candidate["stability"] == "NOT_TESTED" for candidate in r["candidates"])
    assert all(candidate["slope_underface_attachment"] == "NOT_PROVEN"
               for candidate in r["candidates"])
    assert all(len(candidate["joint_plan"]) == 2
               and all(j["physical_clutch"] == "NOT_TESTED" for j in candidate["joint_plan"])
               for candidate in r["candidates"])


def test_ldraw_screen_is_bounded_to_three_pair_checks_only(ldraw_087_library):
    candidate = propose_two_slope_bridge_087()
    result = screen_two_slope_ldraw_087(candidate, ldraw_087_library)
    assert len(result["pair_checks"]) == 3
    assert result["physical_certification"] == "NOT_CERTIFIED"
    assert result["cap_joint_physical_clutch"] == "NOT_TESTED"
    assert result["decision"] in {
        "REJECTED_SLOPE_BODY_INTERSECTION",
        "BLOCKED_MISSING_LDRAW_EVIDENCE",
        "PROPOSE_PHYSICAL_THREE_PIECE_JOIN_TEST_NOT_CERTIFIED",
    }


def test_bounded_real_mesh_search_never_promotes_lone_stud_touch_to_clutch(
        ldraw_087_library):
    result = choose_bounded_two_slope_trial_087(ldraw_087_library)
    assert len(result["candidates"]) == 4
    assert result["physical_certification"] == "NOT_CERTIFIED"
    assert all(len(c["ldraw"]["pair_checks"]) == 3 for c in result["candidates"])
    if result["recommended_experiment_id"] is None:
        assert result["recommendation"] == "NO_CANDIDATE_PASSED_SCOPED_GATES"
    else:
        source = next(c for c in result["candidates"]
                      if c["building_id"] == result["recommended_experiment_id"])
        assert source["ldraw"]["decision"] == "PROPOSE_PHYSICAL_THREE_PIECE_JOIN_TEST_NOT_CERTIFIED"


@pytest.fixture(scope="module")
def ldraw_087_library():
    import os
    from pathlib import Path
    from lego_geometry_engine import LDrawLibrary
    path = os.environ.get("LDRAW_TEST_ROOT_087")
    if not path or not Path(path).is_dir():
        pytest.skip("real bounded pinned LDraw subset not provided")
    return LDrawLibrary(Path(path))
