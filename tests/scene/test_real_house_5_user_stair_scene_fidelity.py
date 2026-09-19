import json
from pathlib import Path

from brickhouse.scene import ArchitecturalScene, validate_scene_against_survey
from brickhouse.survey import ArchitecturalSurvey
from brickhouse.survey.human_facts import HumanAttributeFact, apply_human_attribute_facts


ROOT = Path(__file__).resolve().parents[2]
SURVEY_PATH = ROOT / "frontend" / "benchmarks" / "real-house-5" / "accepted-survey-v0.1.json"
SCENE_PATH = ROOT / "tests" / "fixtures" / "real_house_5_scene_candidate.json"


def test_current_real_house_scene_is_not_allowed_to_collapse_confirmed_turning_stair() -> None:
    source = ArchitecturalSurvey.model_validate(json.loads(SURVEY_PATH.read_text(encoding="utf-8")))
    scene = ArchitecturalScene.model_validate(json.loads(SCENE_PATH.read_text(encoding="utf-8")))
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
    candidate = apply_human_attribute_facts(source, [fact]).candidate

    codes = {issue.code for issue in validate_scene_against_survey(candidate, scene)}

    assert source.known_measurements == []
    assert candidate.known_measurements == []
    assert len(scene.stairs) == 1
    assert "multi_run_stair_topology_unresolved" in codes
