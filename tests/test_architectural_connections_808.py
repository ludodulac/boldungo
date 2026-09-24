import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from brickhouse.vision.multiview import ArchitecturalConnectionModel

ROOT = Path(__file__).resolve().parents[1]
LOT = ROOT / "frontend" / "architectural-connections-808.json"
HOUSE = ROOT / "frontend" / "house-assembly-806.json"
SECONDARY = ROOT / "frontend" / "terrace-stair-assembly-807.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def connection_model():
    return ArchitecturalConnectionModel.model_validate(load(LOT)["architectural_connection_model"])


def test_808_all_new_pixel_evidence_has_explicit_provenance_and_truth_class():
    model = connection_model()
    assert model.pixel_evidence
    for item in model.pixel_evidence:
        assert item.photo_index in {1, 2, 3, 4, 5}
        assert len(item.roi) == 4
        assert item.property_tested and item.observed_result and item.provenance
        assert item.truth_class == "NEW_PIXEL_DERIVED_ARCHITECTURAL_EVIDENCE"


def test_808_pixel_audit_does_not_rewrite_old_observations():
    lot = load(LOT)
    assert lot["pixel_audit"]["retroactive_observation_rewrite"] is False
    assert lot["preservation"]["house_806"] == "UNCHANGED"
    assert lot["preservation"]["terrace_stair_807"] == "UNCHANGED"
    assert load(HOUSE)["mission"].endswith("806")
    assert load(SECONDARY)["mission"].endswith("807")


def test_808_stair_terrace_remains_unknown_not_fabricated_landing():
    model = connection_model()
    conn = next(x for x in model.connections if x.connection_id == "conn808-stair-terrace")
    assert conn.status.value == "UNKNOWN_CONNECTION"
    assert conn.relation.value == "CONNECTS_TO"
    assert "landing" in conn.unknowns
    assert not any(
        x.status.value == "SUPPORTED" and x.subject_assembly == "stair_assembly_p3_807"
        and x.object_assembly_or_sector == "terrace_assembly_p3_807"
        for x in model.connections
    )


def test_808_terrace_building_connection_does_not_assign_sector_to_p1_house():
    model = connection_model()
    conn = next(x for x in model.connections if x.connection_id == "conn808-terrace-local-building-sector")
    assert conn.status.value == "SUPPORTED"
    assert conn.object_assembly_or_sector == "p3_p4_p5_terrace_bearing_building_sector"
    corr = next(x for x in model.correspondences if x.correspondence_id == "corr808-p1-to-terrace-bearing-sector")
    assert corr.status == "UNRESOLVED"


def test_808_compatibility_or_candidate_correspondence_is_not_connection():
    model = connection_model()
    candidate = next(x for x in model.correspondences if x.correspondence_id == "corr808-p1-p2-house-context")
    assert candidate.status == "SUPPORTED_CORRESPONDENCE_CANDIDATE"
    assert not any(x.object_assembly_or_sector == "p2_house_like_side_sector" for x in model.connections)


def test_808_p5_788_boundary_join_is_not_resurrected():
    lot = load(LOT)
    assert lot["preservation"]["p5_788_boundary_joins_resurrected"] is False
    topology_blob = json.dumps(lot["architectural_connection_model"]["connections"]).lower()
    assert "boundary_joins" not in topology_blob
    assert "788" not in topology_blob


def test_808_approximations_never_supply_connection_evidence():
    lot = load(LOT)
    assert lot["constructive_approximations"]["new_connection_approximations"] == []
    model = connection_model()
    evidence = {ref for conn in model.connections for ref in conn.evidence_refs + conn.pixel_evidence_refs}
    assert not any(ref.startswith("approx-") for ref in evidence)


def test_808_no_metric_connection_geometry_is_invented():
    model = connection_model()
    connection_blob = json.dumps([x.model_dump(mode="json") for x in model.connections]).lower()
    for forbidden in ('"distance"', '"angle"', '"width":', '"height":', '"depth":', '"step_count"', '"coordinates"'):
        assert forbidden not in connection_blob


def test_808_roof_house_connection_is_supported_by_old_and_new_evidence():
    model = connection_model()
    conn = next(x for x in model.connections if x.connection_id == "conn808-roof-house")
    assert conn.status.value == "SUPPORTED"
    assert conn.relation.value == "ROOF_COVERS"
    assert {"obs_p1_roof_edge", "obs_p1_front_wall"}.issubset(conn.evidence_refs)
    assert conn.pixel_evidence_refs == ["px808-p1-roof-house-interface"]


def test_808_save_reload_connection_model():
    model = connection_model()
    restored = ArchitecturalConnectionModel.model_validate_json(model.model_dump_json())
    assert restored == model


def test_808_ready_gate_requires_supported_structural_connection():
    data = load(LOT)["architectural_connection_model"]
    data["connections"] = [
        x for x in data["connections"]
        if x["relation"] == "OPENING_IN_FACE" or x["status"] != "SUPPORTED"
    ]
    with pytest.raises(ValidationError):
        ArchitecturalConnectionModel.model_validate(data)


def test_808_fragment_spec_exists_only_with_ready_gate():
    data = load(LOT)["architectural_connection_model"]
    assert data["global_gate"] == "READY"
    assert data["recognizable_fragment_spec"]
    data["global_gate"] = "BLOCKED"
    with pytest.raises(ValidationError):
        ArchitecturalConnectionModel.model_validate(data)


def test_808_fragment_spec_keeps_truth_categories_separate():
    spec = connection_model().recognizable_fragment_spec
    assert spec is not None
    assert spec.observed_refs
    assert spec.pixel_derived_new_refs
    assert spec.constructive_approximation_refs
    assert spec.unknowns
    assert set(spec.observed_refs).isdisjoint(spec.pixel_derived_new_refs)
    assert set(spec.observed_refs).isdisjoint(spec.constructive_approximation_refs)
    assert set(spec.pixel_derived_new_refs).isdisjoint(spec.constructive_approximation_refs)
