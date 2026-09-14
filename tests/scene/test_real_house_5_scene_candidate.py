import json
from pathlib import Path

from fastapi.testclient import TestClient

from brickhouse.api import app
from brickhouse.scene import ArchitecturalScene, validate_scene_against_survey
from brickhouse.survey import ArchitecturalSurvey


ROOT = Path(__file__).resolve().parents[2]
SURVEY_PATH = ROOT / "frontend" / "benchmarks" / "real-house-5" / "accepted-survey-v0.1.json"
SCENE_PATH = ROOT / "tests" / "fixtures" / "real_house_5_scene_candidate.json"
CLIENT = TestClient(app)


def _raw_survey() -> dict:
    return json.loads(SURVEY_PATH.read_text(encoding="utf-8"))


def _raw_scene() -> dict:
    return json.loads(SCENE_PATH.read_text(encoding="utf-8"))


def test_candidate_is_schema_valid_and_preserves_accepted_survey() -> None:
    survey = ArchitecturalSurvey.model_validate(_raw_survey())
    scene = ArchitecturalScene.model_validate(_raw_scene())

    errors = [
        issue for issue in validate_scene_against_survey(survey, scene)
        if issue.severity.value == "error"
    ]
    assert errors == []
    assert survey.known_measurements == []
    assert scene.volumes[0].width.source.kind.value == "inferred"
    assert scene.openings[5].id == "front-opening-6"
    assert scene.openings[5].type.value == "unknown"


def test_candidate_passes_public_scene_validation_endpoints() -> None:
    response = CLIENT.post(
        "/api/v1/validate-scene-against-survey",
        json={"survey": _raw_survey(), "scene": _raw_scene()},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert not [issue for issue in payload["issues"] if issue["severity"] == "error"]

    response = CLIENT.post("/api/v1/validate-scene", json=_raw_scene())
    assert response.status_code == 200, response.text
    assert response.json()["scene"]["schema_version"] == "0.2"


def test_candidate_can_build_a_conservative_partial_lego_preview() -> None:
    response = CLIENT.post(
        "/api/v1/build-scene",
        json={"scene": _raw_scene(), "front_width_studs": 48, "allow_partial": True},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["brick_model"]["parts"]
    assert payload["assembly_plan"]["steps"]
    assert payload["bom"]["total_parts"] == len(payload["brick_model"]["parts"])
