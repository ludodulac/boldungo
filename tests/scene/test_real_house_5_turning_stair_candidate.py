import json
import math
from copy import deepcopy
from pathlib import Path

from fastapi.testclient import TestClient

from brickhouse.api import app
from brickhouse.scene import ArchitecturalScene, analyze_multi_run_stair_geometry, validate_scene_against_survey
from brickhouse.survey import ArchitecturalSurvey
from brickhouse.survey.human_facts import HumanAttributeFact, apply_human_attribute_facts


ROOT = Path(__file__).resolve().parents[2]
BENCHMARK = ROOT / "frontend" / "benchmarks" / "real-house-5"
SURVEY_PATH = BENCHMARK / "accepted-survey-v0.1.json"
OWNER_FACTS_PATH = BENCHMARK / "owner-spatial-topology-survey-facts-v0.1.json"
SCENE_PATH = ROOT / "tests" / "fixtures" / "real_house_5_scene_candidate.json"
OVERLAY_PATH = BENCHMARK / "turning-stair-scene-overlay-v0.1.json"
CLIENT = TestClient(app)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _survey_with_owner_topology() -> tuple[ArchitecturalSurvey, ArchitecturalSurvey]:
    source = ArchitecturalSurvey.model_validate(_load(SURVEY_PATH))
    journal = _load(OWNER_FACTS_PATH)
    stair_facts = [
        HumanAttributeFact.model_validate(item)
        for item in journal["attribute_facts"]
        if item["observation_id"] == "stair-exterior-1"
    ]
    candidate = apply_human_attribute_facts(source, stair_facts).candidate
    return source, candidate


def _turning_scene() -> ArchitecturalScene:
    payload = _load(SCENE_PATH)
    overlay = _load(OVERLAY_PATH)
    replaced = set(overlay["replaces_scene_stair_ids"])
    payload["stairs"] = [item for item in payload.get("stairs", []) if item["id"] not in replaced]
    payload["stairs"].extend(deepcopy(overlay["stairs"]))
    payload["stair_system_links"] = deepcopy(overlay["stair_system_links"])

    updates = {item["relation_id"]: item for item in overlay["relation_updates"]}
    for relation in payload.get("relations", []):
        update = updates.get(relation["id"])
        if update is None:
            continue
        relation["subject_id"] = update["subject_id"]
        relation["object_id"] = update["object_id"]
        relation["geometry_status"] = update["geometry_status"]
        relation["statement"] = update["statement"]

    return ArchitecturalScene.model_validate(payload)


def test_turning_overlay_realizes_owner_confirmed_route_without_mutating_survey() -> None:
    source, survey = _survey_with_owner_topology()
    source_before = deepcopy(source.model_dump())
    scene = _turning_scene()

    report = analyze_multi_run_stair_geometry(survey, scene)
    fact = next(item for item in report.facts if item.observation_id == "stair-exterior-1")
    error_codes = {
        issue.code
        for issue in validate_scene_against_survey(survey, scene)
        if issue.severity.value == "error"
    }

    assert source.model_dump() == source_before
    assert source.known_measurements == []
    assert survey.known_measurements == []
    assert fact.component_run_ids == [
        "stair-exterior-1-run-lower-v1",
        "stair-exterior-1-run-upper-v1",
    ]
    assert fact.all_components_present is True
    assert fact.connected is True
    assert fact.spanning_path_exists is True
    assert fact.direction_change_realized is True
    assert "multi_run_stair_topology_unresolved" not in error_codes
    assert "multi_run_stair_direction_change_not_realized" not in error_codes
    assert "multi_run_stair_components_disconnected" not in error_codes

    runs = {item.id: item for item in scene.stairs}
    lower = runs["stair-exterior-1-run-lower-v1"]
    upper = runs["stair-exterior-1-run-upper-v1"]
    main = next(item for item in scene.volumes if item.id == "volume_main")
    landing = next(item for item in scene.platforms if item.id == "platform-massive-1")

    # Ascending Scene run orientation is ground -> turn -> platform, so descent is
    # the reverse: platform -> WEST (+y) -> left turn -> SOUTH (-x) -> courtyard.
    assert upper.end.x == upper.start.x
    assert upper.start.y > upper.end.y
    assert lower.start.x < lower.end.x
    assert lower.start.y == lower.end.y
    assert upper.start == lower.end

    rear_west_plane = main.position.y + main.depth.value
    assert upper.start.y > rear_west_plane

    # The top endpoint still meets the masonry/concrete platform at its rear edge.
    assert math.isclose(upper.end.y, landing.position.y + landing.depth)
    assert landing.position.x <= upper.end.x <= landing.position.x + landing.width
    assert math.isclose(upper.end.z, landing.position.z)


def test_turning_overlay_reuses_existing_provisional_dimensions_instead_of_adding_metrics() -> None:
    overlay = _load(OVERLAY_PATH)
    runs = overlay["stairs"]

    assert len(runs) == 2
    assert all(item["source"] == {"kind": "inferred", "confidence": 0.18} for item in runs)
    assert {item["width"] for item in runs} == {1.0}
    assert {item["start"]["z"] for item in runs} | {item["end"]["z"] for item in runs} == {0.0, 1.15, 2.3}

    horizontal_lengths = sorted(
        round(math.hypot(item["end"]["x"] - item["start"]["x"], item["end"]["y"] - item["start"]["y"]), 6)
        for item in runs
    )
    assert horizontal_lengths == [0.9, 2.5]
    assert overlay["owner_fact_journal"] == "owner-spatial-topology-survey-facts-v0.1.json"
    assert any("no new stair dimension" in note.lower() for note in overlay["inference_notes"])
    assert any("remain unresolved" in note.lower() for note in overlay["inference_notes"])


def test_turning_scene_still_builds_a_conservative_partial_lego_preview() -> None:
    scene = _turning_scene()
    response = CLIENT.post(
        "/api/v1/build-scene",
        json={"scene": scene.model_dump(mode="json"), "front_width_studs": 48, "allow_partial": True},
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["brick_model"]["parts"]
    assert payload["assembly_plan"]["steps"]
    assert payload["bom"]["total_parts"] == len(payload["brick_model"]["parts"])
