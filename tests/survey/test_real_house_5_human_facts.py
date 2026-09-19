from copy import deepcopy
import json
from pathlib import Path

from brickhouse.survey.human_facts import HumanAttributeFact, apply_human_attribute_facts
from brickhouse.survey.models import ArchitecturalSurvey
from brickhouse.survey.stair_topology import analyze_survey_stair_topology


FIXTURE = (
    Path(__file__).parents[2]
    / "frontend"
    / "benchmarks"
    / "real-house-5"
    / "accepted-survey-v0.1.json"
)


def test_real_house_5_user_confirmed_stair_turn_is_non_metric_overlay() -> None:
    source = ArchitecturalSurvey.model_validate(json.loads(FIXTURE.read_text(encoding="utf-8")))
    before = deepcopy(source.model_dump())

    fact = HumanAttributeFact.model_validate(
        {
            "observation_id": "stair-exterior-1",
            "attribute_name": "stair_topology",
            "value": {
                "minimum_run_count": 2,
                "direction_change": True,
                "exact_run_count": 2,
                "turning_node_kind": "turn",
            },
            "certainty": "certain",
            "source": {"kind": "user_provided", "confidence": 1.0},
            "statement": "User confirms exactly two stair runs with a direction change.",
            "supersedes_existing": True,
        }
    )

    application = apply_human_attribute_facts(source, [fact])

    # Accepted benchmark truth is not rewritten by the runtime clarification.
    assert source.model_dump() == before
    assert source.known_measurements == []
    assert application.candidate.known_measurements == []

    topology = analyze_survey_stair_topology(application.candidate)
    assert topology.issues == []
    stair_fact = next(item for item in topology.facts if item.observation_id == "stair-exterior-1")
    assert stair_fact.requires_multiple_scene_runs is True
    assert stair_fact.topology.minimum_run_count == 2
    assert stair_fact.topology.direction_change is True
    assert stair_fact.topology.exact_run_count == 2

    # The clarification is semantic/topological only: no metric fields are added.
    stair_observation = next(
        item for item in application.candidate.observations if item.id == "stair-exterior-1"
    )
    assert "run_length" not in stair_observation.attributes["stair_topology"]
    assert "turn_coordinate" not in stair_observation.attributes["stair_topology"]
