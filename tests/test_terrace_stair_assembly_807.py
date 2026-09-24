import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from brickhouse.vision.multiview import SecondaryAssemblyShapeModel

ROOT = Path(__file__).resolve().parents[1]
LOT = ROOT / "frontend" / "terrace-stair-assembly-807.json"
P3 = ROOT / "frontend" / "p3-perception-expansion-response-794.json"
P4 = ROOT / "frontend" / "composite-interview-discriminant-response-796.json"
P5_799 = ROOT / "frontend" / "p5-perception-expansion-response-799.json"
P5_802 = ROOT / "frontend" / "p5-platform-discriminant-ingestion-802.json"
HOUSE = ROOT / "frontend" / "house-assembly-806.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def models():
    lot = load(LOT)
    return (
        SecondaryAssemblyShapeModel.model_validate(lot["terrace_shape_model"]),
        SecondaryAssemblyShapeModel.model_validate(lot["stair_shape_model"]),
    )


def test_807_p3_is_primary_and_p4_stays_separate_compatible_evidence():
    terrace, stair = models()
    assert terrace.primary_photo_index == stair.primary_photo_index == 3
    assert all(item.photo_indexes == [3] for item in terrace.observed_components + stair.observed_components)
    assert [(x.observation_ref, x.photo_index) for x in terrace.separate_compatible_view_evidence] == [("obs_p4_terrace", 4)]
    assert [(x.observation_ref, x.photo_index) for x in stair.separate_compatible_view_evidence] == [("obs_p4_stair", 4)]
    assert load(LOT)["source_evidence_audit"]["physical_identity_p3_p4"] == "UNRESOLVED"


def test_807_p3_component_provenance_matches_persisted_794_promotions():
    p3 = load(P3)
    localized = {
        "p3-candidate-step-diagonal-region",
        "p3-candidate-raised-platform-region",
        "p3-candidate-visible-junction-region",
    }
    assert localized.issubset({x["candidate_id"] for x in p3["region_results"] if x["outcome"] == "LOCALIZABLE"})
    blob = json.dumps(load(LOT)["terrace_shape_model"]["observed_components"] + load(LOT)["stair_shape_model"]["observed_components"])
    for ref in ("obs_p3_step_diagonal_794", "obs_p3_raised_platform_794", "obs_p3_visible_junction_794"):
        assert ref in blob


def test_807_observed_approximation_unknown_are_separate_and_revisable():
    for model in models():
        observed = {x.component_id for x in model.observed_components}
        approximated = {x.approximation_id for x in model.approximated_components}
        assert observed.isdisjoint(approximated)
        for item in model.approximated_components:
            assert item.truth_class == "CONSTRUCTIVE_APPROXIMATION"
            assert item.revisable is True
            assert item.source_unknowns and item.replacement_condition
        assert model.unknown_components


def test_807_terrace_has_observed_platform_edge_guard_and_supports():
    terrace, _ = models()
    kinds = {x.kind.value for x in terrace.observed_components}
    assert {"PLATFORM_SURFACE_OR_REGION", "VISIBLE_PLATFORM_EDGE", "RAILING_OR_GUARD", "SUPPORTS"}.issubset(kinds)


def test_807_stair_has_flight_boundaries_and_step_pattern_but_no_step_count():
    _, stair = models()
    kinds = {x.kind.value for x in stair.observed_components}
    assert {"FLIGHT_REGION", "VISIBLE_SIDE_BOUNDARY", "STEP_PATTERN", "TOP_TERMINATION"}.issubset(kinds)
    assert "stair-step-count" in {x.unknown_id for x in stair.unknown_components}
    observed_blob = json.dumps([x.model_dump(mode="json") for x in stair.observed_components]).lower()
    assert "step_count unknown" in observed_blob
    assert not any(token in observed_blob for token in ['"step_count":', '"number_of_steps":'])


def test_807_p4_only_contributes_compatible_left_below_not_junction():
    p4 = load(P4)
    props = {x["property_token"]: x for x in p4["property_results"]}
    assert props["STEP_TO_PLATFORM_LATERAL_ORDER"]["relation_tokens"] == ["LEFT_OF"]
    assert props["STEP_TO_PLATFORM_VERTICAL_ORDER"]["relation_tokens"] == ["BELOW"]
    assert props["STEP_PLATFORM_TERMINATION_JUNCTION_CONFIGURATION"]["outcome"] == "NOT_OBSERVABLE"
    assert "NO_RELIABLE_RELATION" in props["STEP_PLATFORM_TERMINATION_JUNCTION_CONFIGURATION"]["relation_tokens"]


def test_807_stair_terrace_connection_fails_closed_unknown():
    conn = load(LOT)["stair_terrace_connection"]
    assert conn["state"] == "UNKNOWN_CONNECTION"
    assert {"LANDS_ON", "CONNECTS_TO"}.issubset(conn["not_established"])
    assert "TERMINATES_AGAINST obs_p3_visible_junction_794" in " ".join(conn["supported_constraints"])
    assert "obs_p3_visible_junction_794 LEFT_OF obs_p3_raised_platform_794" in conn["supported_constraints"]


def test_807_p5_superseded_boundary_join_is_negative_memory_only():
    lot = load(LOT)
    p5 = lot["p5_negative_memory"]
    assert p5["platform_799"] == "AMBIGUOUS"
    assert p5["junction_799"] == "NOT_OBSERVABLE"
    assert p5["boundary_separation_801"] == "NOT_OBSERVABLE"
    assert "SUPERSEDED" in p5["memory_788_boundary_joins"]
    assert p5["repeat_performed"] is False
    constructive_blob = json.dumps([lot["terrace_shape_model"], lot["stair_shape_model"], lot["stair_terrace_connection"]])
    assert "p5_stair_diagonal_sector" not in constructive_blob
    assert "p5_platform_sector" not in constructive_blob


def test_807_p3_projecting_volume_remains_unassigned_local_context():
    lot = load(LOT)
    assert lot["p3_local_context"]["projecting_volume_ref"] == "obs_p3_box_volume"
    assert lot["p3_local_context"]["assignment"] == "LOCAL_ARCHITECTURAL_CONTEXT_UNASSIGNED_TO_HOUSE"
    assert "obs_p3_box_volume" not in json.dumps(load(HOUSE)["house_shape_model"])


def test_807_save_reload_roundtrip():
    for model in models():
        restored = SecondaryAssemblyShapeModel.model_validate_json(model.model_dump_json())
        assert restored == model


@pytest.mark.parametrize("which,required_kind", [("terrace_shape_model", "VISIBLE_PLATFORM_EDGE"), ("stair_shape_model", "VISIBLE_SIDE_BOUNDARY")])
def test_807_supported_local_gates_fail_closed(which, required_kind):
    data = load(LOT)[which]
    data["observed_components"] = [x for x in data["observed_components"] if x["kind"] != required_kind]
    with pytest.raises(ValidationError):
        SecondaryAssemblyShapeModel.model_validate(data)


def test_807_global_gate_remains_blocked_despite_supported_local_gates():
    lot = load(LOT)
    assert lot["terrace_shape_model"]["recognizable_gate"] == "SUPPORTED"
    assert lot["stair_shape_model"]["recognizable_gate"] == "SUPPORTED"
    assert lot["global_gate"]["status"] == "BLOCKED"
    assert lot["stair_terrace_connection"]["state"] == "UNKNOWN_CONNECTION"
