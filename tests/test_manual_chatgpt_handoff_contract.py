import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from brickhouse.api import app
from brickhouse.scene import ArchitecturalScene
from brickhouse.survey import ArchitecturalSurvey

FIXTURES = Path("tests/fixtures")
FRONTEND = Path("frontend")
client = TestClient(app)

def _json(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))

def _text(name: str) -> str:
    return (FRONTEND / name).read_text(encoding="utf-8")

def _embedded_survey_skeleton() -> dict:
    contract = _text("brickhouse-survey-output-contract.txt")
    start = contract.index("{\n")
    end = contract.index("\n\nRÈGLES DE STRUCTURE", start)
    return json.loads(contract[start:end])

def test_active_manual_handoff_uses_two_stage_survey_then_scene_flow() -> None:
    photo_html = _text("photo.html")
    survey_entry = _text("brickhouse-survey-package.js")
    survey_generator = _text("brickhouse-survey-package-v04.js")
    output_contract = _text("brickhouse-survey-output-contract.txt")
    survey_importer = _text("survey-import.js")
    scene_handoff = _text("scene-handoff-photo-evidence.js")
    scene_gate = _text("scene-survey-gate.js")
    assert "brickhouse-survey-package.js" in photo_html
    assert "scene-handoff-photo-evidence.js" in photo_html
    assert "brickhouse-single-package.js" not in photo_html
    assert "analysis-package-download-v1.js?v=exchange-v1-sophie-r001" in survey_entry
    assert "brickhouse-survey-package-v04.js?v=pdf-handoff-0.4" not in survey_entry
    assert "brickhouse-survey-hybrid-pdf.js" not in survey_entry
    assert "const PDF_HANDOFF_VERSION = 'pdf-handoff-0.4'" in survey_generator
    assert "const PACKAGE_FILENAME = 'BRICKHOUSE-SURVEY-pdf-handoff-0.4.pdf'" in survey_generator
    assert "brickhouse-survey-output-contract.txt" in survey_generator
    assert "brickhouse-survey-result.json" in survey_generator
    assert "DIRECTEMENT l’objet ArchitecturalSurvey v0.1" in survey_generator
    assert '"schema_version": "0.1"' in output_contract
    assert '"x_direction": "front_view_left_to_right"' in output_contract
    assert '"description":' in output_contract
    assert '"source": {"kind": "observed"' in output_contract
    assert '"kind": "front_width"' in output_contract
    assert '"units": "m"' in output_contract
    assert '"observations": [' in output_contract
    assert 'AUCUNE clé physical_objects' in output_contract
    assert 'AUCUN objet parent "ArchitecturalSurvey"' in output_contract
    assert "/api/v1/validate-survey" in survey_importer
    assert "valid_for_scene_fusion" in survey_importer
    assert "BRICKHOUSE-SURVEY-TO-SCENE-pdf-handoff-0.2.pdf" in scene_handoff
    assert "scene-handoff-0.5-single-hybrid-pdf" in scene_handoff
    assert "PDF HYBRIDE UNIQUE" in scene_handoff
    assert "BRICKHOUSE-SURVEY-TO-SCENE.txt" in scene_handoff
    assert "BRICKHOUSE-SURVEY-pdf-handoff-0.4.pdf" in scene_handoff
    assert "brickhouse-scene-result.json" in scene_handoff
    assert "/api/v1/validate-scene-against-survey" in scene_gate
    assert "/api/v1/validate-scene" in scene_gate

def test_embedded_canonical_survey_skeleton_is_backend_valid() -> None:
    raw = _embedded_survey_skeleton()
    survey = ArchitecturalSurvey.model_validate(raw)
    assert survey.schema_version == "0.1"
    observation_ids = {item.id for item in survey.observations}
    assert observation_ids
    for relation in survey.relations:
        assert relation.subject_id in observation_ids
        assert relation.object_id in observation_ids
    response = client.post("/api/v1/validate-survey", json=raw)
    assert response.status_code == 200

def test_manual_survey_fixture_validates_at_domain_and_api_boundaries() -> None:
    raw = _json("manual_handoff_survey_valid.json")
    survey = ArchitecturalSurvey.model_validate(raw)
    assert survey.schema_version == "0.1"
    assert survey.photos[0].photo_index == 1
    assert survey.known_measurements[0].kind == "front_width"
    response = client.post("/api/v1/validate-survey", json=raw)
    assert response.status_code == 200
    payload = response.json()
    assert payload["valid_for_scene_fusion"] is True
    assert payload["issues"] == []
    assert payload["survey"]["id"] == survey.id

def test_manual_scene_fixture_validates_and_cross_checks_against_validated_survey() -> None:
    survey_raw = _json("manual_handoff_survey_valid.json")
    scene_raw = _json("manual_handoff_scene_valid.json")
    scene = ArchitecturalScene.model_validate(scene_raw)
    assert scene.schema_version == "0.2"
    assert scene.volumes[0].width.source.kind.value == "user_provided"
    assert scene.volumes[0].depth.source.kind.value == "inferred"
    cross = client.post("/api/v1/validate-scene-against-survey", json={"survey": survey_raw, "scene": scene_raw})
    assert cross.status_code == 200
    assert cross.json()["issues"] == []
    geometric = client.post("/api/v1/validate-scene", json=scene_raw)
    assert geometric.status_code == 200
    assert geometric.json()["scene"]["id"] == scene.id

def test_topology_summary_cannot_masquerade_as_architectural_survey() -> None:
    topology_like = {"schema_version": "0.1", "topology": {"facades": ["front"], "objects": [{"kind": "opening", "statement": "One opening is visible."}]}, "summary": "This is reasoning output, not the complete Survey contract."}
    with pytest.raises(ValidationError):
        ArchitecturalSurvey.model_validate(topology_like)
    response = client.post("/api/v1/validate-survey", json=topology_like)
    assert response.status_code == 422

def test_real_neutral_chat_failure_shape_stays_invalid_and_is_explicitly_forbidden() -> None:
    observed_failure = {"ArchitecturalSurvey": {"schema_version": "0.1", "name": "brickhouse-survey", "canonical_frame": {"front_facade": "front", "x_direction": "left_to_right", "y_direction": "front_to_rear", "z_direction": "bottom_to_top"}, "photos": [{"photo_index": 1, "filename": "01-original.jpg", "capture_role": "facade_view", "facade": "front", "image_left_maps_to_facade_offset": "low", "orientation_source": "capture_hint"}], "known_measurements": [{"subject_id": "building_main", "attribute": "front_facade_width", "value": 10, "unit": "m", "certainty": "certain", "source": "user"}], "observations": [], "physical_objects": [{"id": "building_main", "kind": "building"}], "relations": [], "representation_policy": {}, "notes": []}}
    with pytest.raises(ValidationError):
        ArchitecturalSurvey.model_validate(observed_failure)
    response = client.post("/api/v1/validate-survey", json=observed_failure)
    assert response.status_code == 422
    generator = _text("brickhouse-survey-package-v04.js")
    contract = _text("brickhouse-survey-output-contract.txt")
    for forbidden in ('{\\"ArchitecturalSurvey\\":{...}}', 'physical_objects'):
        assert forbidden in generator
    assert 'filename ni orientation_source' in contract
    assert 'kind/value/units/source' in contract
    assert 'notes est une chaîne ou null' in contract

def test_legacy_external_bundle_remains_compatibility_only() -> None:
    active_page = _text("photo.html")
    legacy_importer = _text("external-bundle-import.js")
    assert "brickhouse-single-package.js" not in active_page
    assert "external-bundle-0.1" in legacy_importer
    assert "brickhouse_external_result" in legacy_importer
    assert "value?.survey?.schema_version === '0.1'" in legacy_importer
    assert "value?.scene?.schema_version === '0.2'" in legacy_importer
