"""LEGO2-083: three bounded design options, one EXACT 30-piece non-certified trial."""
from collections import Counter

import pytest

from brickhouse.bricks.ridge_technique_candidates_083 import (
    _central_post_cap, _orthogonal_transverse_spine,
    _sequential_plate_seam, propose_ridge_techniques_083,
)
from brickhouse.bricks.connector_first_design_082 import screen_connector_first_candidate


def test_three_distinct_techniques_are_compared_not_only_reaudited():
    r = propose_ridge_techniques_083()
    assert r["candidate_count"] == 3
    assert [x["technique"] for x in r["candidates"]] == [
        "A_CENTRAL_COVER", "B_TRANSVERSE_BRACED_SPINE",
        "C_SEQUENTIAL_PLATE_SEAM"]
    assert r["recommendation"] == "B_TRANSVERSE_BRACED_SPINE"
    assert all(x["physical_certification"] == "NOT_CERTIFIED"
               for x in r["candidates"])
    assert r["physical_certification"] == "NOT_CERTIFIED"
    assert r["guided004_mutated"] is False


def test_real_ridge_kit_has_exactly_30_counted_named_lego_parts():
    trial = propose_ridge_techniques_083()["physical_trial"]
    assert trial["total_pieces"] == 30
    assert trial["frame_pieces"] == 24
    assert trial["loose_slope_test_pieces"] == 6
    assert trial["parts"] == [
        {"engine_id": "BRICK_1X1", "ldraw_reference": "3005", "quantity": 18},
        {"engine_id": "BRICK_1X8", "ldraw_reference": "3008", "quantity": 6},
        {"engine_id": "BRICK_SLOPED_18_4X2", "ldraw_reference": "30363", "quantity": 6},
    ]
    assert sum(row["quantity"] for row in trial["parts"]) == 30
    assert len({p["placement_id"] for p in trial["parts_by_placement_id"]}) == 30


def test_structural_frame_has_26_approved_nominal_connections_all_pieces_in_graph():
    model, connections, frame_ids, loose_ids = _orthogonal_transverse_spine()
    assert len(frame_ids) == 24 and len(loose_ids) == 6
    frame = [p for p in model.parts if p.placement_id in frame_ids]
    links = [pair for pair in connections if all(x in frame_ids for x in pair)]
    assert len(links) == 26
    tested = screen_connector_first_candidate(frame, links)
    assert tested["decision"] == "ELIGIBLE_FOR_FURTHER_DESIGN_CHECKS"
    assert tested["documented_nominal_connections"] == 26
    assert tested["parts_without_documented_nominal_connections"] == []
    assert tested["duplicated_top_studs"] == []


def test_six_cladding_slopes_not_silently_approved_by_structural_core():
    model, connections, frame_ids, loose_ids = _orthogonal_transverse_spine()
    before = model.model_dump_json()
    full = screen_connector_first_candidate(model.parts, connections)
    assert full["decision"] != "ELIGIBLE_FOR_FURTHER_DESIGN_CHECKS"
    assert len([r for r in full["blocked_connections"]
                if r["upper_id"] in loose_ids]) == 6
    assert all(row["design_gate"] != "DOCUMENTED_NOMINAL_INTERFACE"
               for row in full["blocked_connections"]
               if row["upper_id"] in loose_ids)
    assert model.model_dump_json() == before


def test_central_post_cap_and_sequential_plates_both_reject_unknown_clutch():
    for build in (_central_post_cap, _sequential_plate_seam):
        model, required, limits = build()
        before = model.model_dump_json()
        r = screen_connector_first_candidate(model.parts, required)
        assert r["decision"] != "ELIGIBLE_FOR_FURTHER_DESIGN_CHECKS"
        assert len(r["blocked_connections"]) >= 2
        assert limits
        assert model.model_dump_json() == before


def test_recommendation_is_strictly_for_unvalidated_physical_experiment():
    r = propose_ridge_techniques_083()
    b = r["candidates"][1]
    assert b["nominal_frame_gate"] == "ELIGIBLE_FOR_FURTHER_DESIGN_CHECKS"
    assert b["nominal_frame_documented_joints"] == 26
    assert b["decision"] == "NOMINAL_FRAME_ONLY__ROOF_CONNECTION_PHYSICAL_TRIAL_REQUIRED"
    assert b["connector_gate"] != "ELIGIBLE_FOR_FURTHER_DESIGN_CHECKS"
    assert r["physical_trial"]["physical_success_condition"]
    assert len(r["physical_trial"]["stop_conditions"]) >= 3


def test_houses_are_separated_experiments_and_not_real_guided004():
    models = [_central_post_cap()[0], _orthogonal_transverse_spine()[0],
              _sequential_plate_seam()[0]]
    assert all("EXP-083" in m.building_id for m in models)
    assert len({m.building_id for m in models}) == 3
    assert all(all(p.placement_id[0] in "ABC" for p in m.parts) for m in models)
