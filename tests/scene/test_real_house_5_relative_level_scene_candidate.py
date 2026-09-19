import json
from copy import deepcopy
from pathlib import Path

from fastapi.testclient import TestClient

from brickhouse.api import app
from brickhouse.scene import (
    ArchitecturalScene,
    analyze_multi_run_stair_geometry,
    validate_scene_against_human_relative_level_facts,
    validate_scene_against_survey,
)
from brickhouse.survey import ArchitecturalSurvey
from brickhouse.survey.human_facts import HumanAttributeFact, apply_human_attribute_facts
from brickhouse.survey.human_spatial_facts import HumanRelativeLevelFact, validate_human_relative_level_facts

ROOT = Path(__file__).resolve().parents[2]
BENCHMARK = ROOT / "frontend" / "benchmarks" / "real-house-5"
SURVEY_PATH = BENCHMARK / "accepted-survey-v0.1.json"
SCENE_PATH = ROOT / "tests" / "fixtures" / "real_house_5_scene_candidate.json"
STAIR_OVERLAY_PATH = BENCHMARK / "turning-stair-scene-overlay-v0.1.json"
LEVEL_OVERLAY_PATH = BENCHMARK / "relative-level-scene-overlay-v0.1.json"
CLIENT = TestClient(app)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _survey_with_user_turn(source: ArchitecturalSurvey) -> ArchitecturalSurvey:
    fact = HumanAttributeFact.model_validate(
        {
            "observation_id": "stair-exterior-1",
            "attribute_name": "stair_topology",
            "value": {"minimum_run_count": 2, "direction_change": True, "turning_node_kind": "turn_or_landing"},
            "certainty": "certain",
            "source": {"kind": "user_provided", "confidence": 1.0},
            "statement": "User confirms exactly two stair runs with a direction change.",\n            "supersedes_existing": True,
        }
    )
    return apply_human_attribute_facts(source, [fact]).candidate


def _combined_scene() -> ArchitecturalScene:
    payload = _load(SCENE_PATH)
    stair = _load(STAIR_OVERLAY_PATH)
    level = _load(LEVEL_OVERLAY_PATH)

    replaced = set(stair["replaces_scene_stair_ids"])
    payload["stairs"] = [item for item in payload.get("stairs", []) if item["id"] not in replaced]
    payload["stairs"].extend(deepcopy(stair["stairs"]))
    payload["stair_system_links"] = deepcopy(stair["stair_system_links"])
    updates = {item["relation_id"]: item for item in stair["relation_updates"]}
    for relation in payload.get("relations", []):
        update = updates.get(relation["id"])
        if update:
            relation.update({key: update[key] for key in ("subject_id", "object_id", "geometry_status", "statement")})

    platform_updates = {item["platform_id"]: item for item in level["platform_updates"]}
    for platform in payload.get("platforms", []):
        update = platform_updates.get(platform["id"])
        if not update:
            continue
        platform["position"]["z"] = update["position_z"]
        platform["source"] = deepcopy(update["source"])
        platform["evidence"] = deepcopy(update["evidence"])
        for support in platform.get("supports", []):
            support["height"] = update["support_height"]
            support["source"] = deepcopy(update["source"])

    return ArchitecturalScene.model_validate(payload)


def test_combined_candidate_satisfies_human_level_ordering_and_turning_stair() -> None:
    source = ArchitecturalSurvey.model_validate(_load(SURVEY_PATH))
    source_before = deepcopy(source.model_dump())
    survey = _survey_with_user_turn(source)
    scene = _combined_scene()
    level_overlay = _load(LEVEL_OVERLAY_PATH)
    level_fact = HumanRelativeLevelFact.model_validate(level_overlay["human_relative_level_fact"])
    validated_levels = validate_human_relative_level_facts(survey, [level_fact])

    level_report = validate_scene_against_human_relative_level_facts(survey, scene, validated_levels.facts)
    stair_report = analyze_multi_run_stair_geometry(survey, scene)
    stair_fact = next(item for item in stair_report.facts if item.observation_id == "stair-exterior-1")
    error_codes = {issue.code for issue in validate_scene_against_survey(survey, scene) if issue.severity.value == "error"}

    timber = next(item for item in scene.platforms if item.id == "platform-timber-1")
    landing = next(item for item in scene.platforms if item.id == "platform-massive-1")
    assert source.model_dump() == source_before
    assert source.known_measurements == []
    assert survey.known_measurements == []
    assert timber.position.z < landing.position.z
    assert level_report.issues == []
    assert stair_fact.connected is True
    assert stair_fact.spanning_path_exists is True
    assert stair_fact.direction_change_realized is True
    assert "multi_run_stair_topology_unresolved" not in error_codes


def test_level_overlay_keeps_metric_delta_explicitly_revisable_inference() -> None:
    overlay = _load(LEVEL_OVERLAY_PATH)
    update = overlay["platform_updates"][0]
    assert overlay["human_relative_level_fact"]["source"]["kind"] == "user_provided"
    assert update["source"]["kind"] == "inferred"
    assert update["source"]["confidence"] < 0.2
    assert "not a user measurement" in update["statement"].lower()
    assert any("no exact vertical delta" in note.lower() for note in overlay["inference_notes"])


def test_combined_candidate_builds_partial_lego_preview() -> None:
    scene = _combined_scene()
    response = CLIENT.post(
        "/api/v1/build-scene",
        json={"scene": scene.model_dump(mode="json"), "front_width_studs": 48, "allow_partial": True},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["brick_model"]["parts"]
    assert payload["assembly_plan"]["steps"]
    assert payload["bom"]["total_parts"] == len(payload["brick_model"]["parts"])
