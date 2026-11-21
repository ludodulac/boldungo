"""084: bounded exact assembly steps, explicit 30363 HOLD and fail-closed order."""
from pathlib import Path

import pytest

from brickhouse.bricks.ridge_technique_candidates_083 import _orthogonal_transverse_spine
from brickhouse.bricks.ridge_trial_assembly_084 import review_ridge_trial_assembly_084


def test_exact_24_frame_steps_are_top_accessible_with_support_to_datum():
    r = review_ridge_trial_assembly_084()
    assert r["step_count"] == r["frame_parts"] == 24
    assert r["total_kit_parts"] == 30
    assert r["frame_nominal_joint_count"] == 26
    assert r["nominal_chain_to_datum_count"] == 24
    assert r["frame_top_approaches_clear"] is True
    assert r["frame_connector_gate"] == "ELIGIBLE_FOR_FURTHER_DESIGN_CHECKS"
    assert r["frame_trial_status"] == "READY_FOR_USER_FRAME_ASSEMBLY_TRIAL"
    assert r["frame_rejection_reasons"] == []
    assert all(x["status"] == "READY_FOR_PHYSICAL_STEP_TEST" for x in r["steps"])
    assert all(x["insertion_screen"] == "GEOMETRY_CLEAR_ONLY" for x in r["steps"])
    assert r["physical_certification"] == "NOT_CERTIFIED"


def test_every_non_ground_step_has_earlier_documented_support():
    r = review_ridge_trial_assembly_084()
    installed = set()
    for step in r["steps"]:
        if step["on_structural_ground_datum"]:
            assert step["position"]["z_plates"] == 0
        else:
            assert step["documented_prior_supports"]
            assert all(s["from"] in installed and s["connector"] == "VALID"
                       for s in step["documented_prior_supports"])
        installed.add(step["placement_id"])
    assert len(installed) == 24


def test_six_30363_pieces_are_held_not_falsely_approved():
    r = review_ridge_trial_assembly_084()
    assert len(r["roof_pieces"]) == 6
    assert {p["part_id"] for p in r["roof_pieces"]} == {"BRICK_SLOPED_18_4X2"}
    assert all("NOT_APPROVED_FOR_INSTALLATION" in p["status"] for p in r["roof_pieces"])
    assert not ({x["placement_id"] for x in r["steps"]}
                & {x["placement_id"] for x in r["roof_pieces"]})
    assert r["roof_attach_status"].startswith("REJECTED_")


def test_bad_order_is_rejected_at_first_unanchored_beam():
    _, _, ids, _ = _orthogonal_transverse_spine()
    order = [ids[-1], *ids[:-1]]
    r = review_ridge_trial_assembly_084(frame_order=order)
    assert r["frame_trial_status"] == "REJECTED_BEFORE_FRAME_TRIAL"
    assert r["frame_rejection_reasons"]
    assert r["frame_rejection_reasons"][0]["step"] == 1
    assert r["frame_rejection_reasons"][0]["reason"] == "REJECTED_MISSING_PRIOR_DOCUMENTED_SUPPORT"
    assert r["physical_certification"] == "NOT_CERTIFIED"


def test_incomplete_or_duplicate_assembly_order_is_forbidden():
    _, _, ids, _ = _orthogonal_transverse_spine()
    with pytest.raises(ValueError, match="exactly 24 unique"):
        review_ridge_trial_assembly_084(frame_order=ids[:-1])
    with pytest.raises(ValueError, match="exactly 24 unique"):
        review_ridge_trial_assembly_084(frame_order=[*ids[:-1], ids[0]])


def test_exported_1890_guided004_not_mutated_by_trial():
    p = Path("artifacts/lego2-guided-004/brick-model.json")
    if not p.is_file():
        pytest.skip("actual canonical export absent in checkout")
    from brickhouse.bricks.brick_model import BrickModel
    canonical = BrickModel.model_validate_json(p.read_text(encoding="utf-8"))
    assert len(canonical.parts) == 1890
    before = canonical.model_dump_json()
    r = review_ridge_trial_assembly_084()
    assert r["model_mutated"] is False
    assert canonical.model_dump_json() == before
