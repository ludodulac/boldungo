import json
from copy import deepcopy
from pathlib import Path

from fastapi.testclient import TestClient

from brickhouse.api import app
from brickhouse.scene import analyze_multi_run_stair_geometry
from brickhouse.scene.benchmark_scene_recipe import materialize_scene_recipe
from brickhouse.survey import ArchitecturalSurvey
from brickhouse.survey.human_facts import HumanAttributeFact, apply_human_attribute_facts

ROOT = Path(__file__).resolve().parents[2]
BENCHMARK = ROOT / "frontend" / "benchmarks" / "real-house-5"
RECIPE = BENCHMARK / "scene-candidate-v0.2.json"
CLIENT = TestClient(app)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _materialize_recipe():
    return materialize_scene_recipe(RECIPE)


def _survey_with_confirmed_turn() -> tuple[ArchitecturalSurvey, ArchitecturalSurvey]:
    source = ArchitecturalSurvey.model_validate(_load(BENCHMARK / "accepted-survey-v0.1.json"))
    fact = HumanAttributeFact.model_validate(
        {
            "observation_id": "stair-exterior-1",
            "attribute_name": "stair_topology",
            "value": {
                "minimum_run_count": 2,
                "direction_change": True,
                "exact_run_count": 2,\n                "turning_node_kind": "turn",
            },
            "certainty": "certain",
            "source": {"kind": "user_provided", "confidence": 1.0},
            "statement": "User confirms exactly two stair runs with a direction change.",\n            "supersedes_existing": True,
        }
    )
    return source, apply_human_attribute_facts(source, [fact]).candidate


def test_consolidated_recipe_materializes_current_benchmark_geometry() -> None:
    scene = _materialize_recipe()
    recipe = _load(RECIPE)
    scale = _load(BENCHMARK / "front-width-scale-estimate.json")
    height_scale = _load(BENCHMARK / "front-height-scale-estimate.json")
    provenance = _load(BENCHMARK / "scene-candidate-v0.2-provenance.json")

    main = next(item for item in scene.volumes if item.id == "volume_main")
    timber = next(item for item in scene.platforms if item.id == "platform-timber-1")
    landing = next(item for item in scene.platforms if item.id == "platform-massive-1")

    assert scale["min_m"] <= main.width.value <= scale["max_m"]
    assert main.width.value == recipe["retained_metric_values"]["volume_main.width_m"]
    assert recipe["metric_status"]["volume_main.depth_m"].startswith("provisional")
    assert recipe["metric_status"]["volume_main.height_m"] == "photo_derived_low_confidence_consensus"
    assert height_scale["min_m"] <= main.height.value <= height_scale["max_m"]
    assert main.height.value == recipe["retained_metric_values"]["volume_main.height_m"]
    assert provenance["known_measurements_required"] is False
    assert timber.position.z < landing.position.z
    assert len(scene.stairs) >= 2
    assert len(scene.stair_system_links) == 2


def test_consolidated_recipe_builds_lego_without_new_measurements() -> None:
    source_survey, survey = _survey_with_confirmed_turn()
    source_before = deepcopy(source_survey.model_dump())
    scene = _materialize_recipe()
    report = analyze_multi_run_stair_geometry(survey, scene)
    stair = next(item for item in report.facts if item.observation_id == "stair-exterior-1")

    assert source_survey.model_dump() == source_before
    assert source_survey.known_measurements == []
    assert survey.known_measurements == []
    assert stair.connected is True
    assert stair.spanning_path_exists is True
    assert stair.direction_change_realized is True

    response = CLIENT.post(
        "/api/v1/build-scene",
        json={"scene": scene.model_dump(mode="json"), "front_width_studs": 48, "allow_partial": True},
    )
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["brick_model"]["parts"]
    assert result["bom"]["total_parts"] == len(result["brick_model"]["parts"])
    assert result["assembly_plan"]["steps"]
