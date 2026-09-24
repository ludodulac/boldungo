import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from brickhouse.vision.multiview import HouseShapeModel

ROOT = Path(__file__).resolve().parents[1]
HOUSE = ROOT / "frontend" / "house-assembly-806.json"
BOOTSTRAP = ROOT / "tests" / "fixtures" / "vision" / "visual-bootstrap-response-062.json"
PIVOT = ROOT / "frontend" / "architectural-assembly-pivot-805.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def parsed_house():
    return HouseShapeModel.model_validate(load(HOUSE)["house_shape_model"])


def test_806_observed_components_have_real_p1_provenance():
    artifact = load(HOUSE)
    bootstrap = load(BOOTSTRAP)
    source_ids = {item["observation_id"] for item in bootstrap["observations"]}
    house = parsed_house()
    for component in house.observed_components:
        assert component.truth_class == "OBSERVED_ARCHITECTURAL_EVIDENCE"
        assert component.photo_indexes == [1]
        assert set(component.observation_refs).issubset(source_ids)
    assert set(artifact["source_evidence_audit"]["persisted_p1_observations"]).issubset(source_ids)


def test_806_truth_classes_keep_approximation_revisable_and_replaceable():
    house = parsed_house()
    observed_ids = {item.component_id for item in house.observed_components}
    approximation_ids = {item.approximation_id for item in house.approximated_components}
    assert observed_ids.isdisjoint(approximation_ids)
    assert house.approximated_components
    for item in house.approximated_components:
        assert item.truth_class == "CONSTRUCTIVE_APPROXIMATION"
        assert item.revisable is True
        assert item.reason
        assert item.source_unknowns
        assert item.replacement_condition


def test_806_integrates_only_persisted_p1_openings_without_symmetry_completion():
    artifact = load(HOUSE)
    house = parsed_house()
    opening_refs = {
        ref
        for component in house.observed_components
        if component.kind.value == "OPENING"
        for ref in component.observation_refs
        if ref != "obs_p1_front_wall"
    }
    assert opening_refs == {
        "obs_p1_front_upper_left_window",
        "obs_p1_front_upper_right_window",
        "obs_p1_front_middle_left_window",
        "obs_p1_front_middle_right_window",
        "obs_p1_front_lower_left_opening",
        "obs_p1_front_lower_right_door",
    }
    assert artifact["opening_integration"]["no_symmetry_completion"] is True
    assert artifact["opening_integration"]["metric_dimensions_invented"] is False


def test_806_preserves_only_actual_historical_visible_within_relation():
    artifact = load(HOUSE)
    assert artifact["source_evidence_audit"]["explicit_p1_relation_evidence"] == [{
        "subject_ref": "obs_p1_front_upper_left_window",
        "relation": "VISIBLE_WITHIN",
        "object_ref": "obs_p1_front_wall",
        "epistemic_level": "OBSERVED",
    }]
    other_openings = [
        item for item in parsed_house().observed_components
        if item.kind.value == "OPENING" and item.component_id != "p1-opening-upper-left"
    ]
    assert all(not any("VISIBLE_WITHIN" in rel for rel in item.qualitative_relations) for item in other_openings)


def test_806_roof_is_observed_boundary_not_historical_closed_geometry():
    artifact = load(HOUSE)
    house = parsed_house()
    roof = [item for item in house.observed_components if item.kind.value == "ROOF_BOUNDARY"]
    assert len(roof) == 1
    assert roof[0].observation_refs == ["obs_p1_roof_edge"]
    assert "TWO_SLOPING_SEGMENTS" in roof[0].qualitative_relations
    assert artifact["roof_integration"]["closed_roof_volume_observed"] is False
    assert artifact["roof_integration"]["historical_hardcoded_roof_reused_as_evidence"] is False


def test_806_depth_storeys_and_metric_geometry_remain_unknown():
    house = parsed_house()
    unknowns = {item.unknown_id for item in house.unknown_components}
    assert {"house-depth", "wall-thickness", "facade-metric-width-height", "floor-storey-semantics",
            "roof-depth", "roof-metric-pitch", "roof-hidden-topology", "roof-3d-ridge"}.issubset(unknowns)
    assert not any("metre" in item.statement.lower() or "meter" in item.statement.lower() for item in house.observed_components)


def test_806_rejected_p2_stair_box_never_enter_house_and_other_views_stay_separate():
    artifact = load(HOUSE)
    house = parsed_house()
    observed_blob = json.dumps([item.model_dump(mode="json") for item in house.observed_components])
    assert "obs_p2_stair" not in observed_blob
    assert "obs_p2_box_volume" not in observed_blob
    separate = {item.observation_ref for item in house.separate_house_candidate_evidence}
    assert {"obs_p2_side_wall", "obs_p4_rear_wall", "obs_p5_side_wall"}.issubset(separate)
    assert "cross-view-house-identity" in {item.unknown_id for item in house.unknown_components}
    assert artifact["source_evidence_audit"]["rejected_observations_still_excluded"] == ["obs_p2_stair", "obs_p2_box_volume"]


def test_806_save_reload_roundtrip():
    house = parsed_house()
    payload = house.model_dump_json()
    restored = HouseShapeModel.model_validate_json(payload)
    assert restored == house


def test_806_supported_gate_is_fail_closed():
    house = parsed_house()
    assert house.recognizable_gate == "SUPPORTED"
    without_roof = house.model_dump(mode="json")
    without_roof["observed_components"] = [
        item for item in without_roof["observed_components"] if item["kind"] != "ROOF_BOUNDARY"
    ]
    with pytest.raises(ValidationError):
        HouseShapeModel.model_validate(without_roof)


def test_806_global_gate_remains_blocked_and_805_pivot_is_unchanged_in_role():
    artifact = load(HOUSE)
    pivot = load(PIVOT)
    assert artifact["global_gate"]["status"] == "BLOCKED"
    assert pivot["gate"]["status"] == "BLOCKED"
    assert pivot["gate"]["requirements"]["supported_structural_interassembly_connection"] == "MISSING"
