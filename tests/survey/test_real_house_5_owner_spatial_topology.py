from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from brickhouse.survey.human_facts import HumanAttributeFact, apply_human_attribute_facts
from brickhouse.survey.human_spatial_facts import (
    HumanRelativeLevelFact,
    validate_human_relative_level_facts,
)
from brickhouse.survey.models import ArchitecturalSurvey
from brickhouse.survey.stair_topology import analyze_survey_stair_topology


ROOT = Path(__file__).parents[2]
BENCHMARK = ROOT / "frontend" / "benchmarks" / "real-house-5"
SURVEY = BENCHMARK / "accepted-survey-v0.1.json"
JOURNAL = BENCHMARK / "owner-spatial-topology-survey-facts-v0.1.json"
CHECKPOINT = BENCHMARK / "accepted-survey-checkpoint.json"


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_owner_spatial_topology_is_append_only_user_confirmed_survey_truth() -> None:
    survey = ArchitecturalSurvey.model_validate(_json(SURVEY))
    original = deepcopy(survey.model_dump())
    journal = _json(JOURNAL)

    assert journal["reason"] == "USER_CONFIRMED spatial topology from owner sketch/explanation"
    assert journal["source"] == {"kind": "user_provided", "confidence": 1.0}
    assert journal["cardinal_convention"] == {
        "east": "front",
        "west": "rear",
        "south": "left",
        "north": "right",
    }

    attribute_facts = [HumanAttributeFact.model_validate(item) for item in journal["attribute_facts"]]
    application = apply_human_attribute_facts(survey, attribute_facts)

    assert survey.model_dump() == original
    assert application.candidate.known_measurements == []
    assert all(fact.source.kind.value == "user_provided" for fact in application.facts)

    report = analyze_survey_stair_topology(application.candidate)
    assert report.issues == []
    topology = next(item for item in report.facts if item.observation_id == "stair-exterior-1").topology
    assert topology.exact_run_count == 2
    assert topology.minimum_run_count == 2
    assert topology.direction_change is True
    assert topology.turning_node_kind == "turn"

    stair = next(item for item in application.candidate.observations if item.id == "stair-exterior-1")
    route = stair.attributes["descent_route"]
    assert route["starts_from_observation_id"] == "platform-massive-1"
    assert route["run_sequence"] == [
        {"ordinal": 1, "direction": "west", "extends_beyond": "west_rear_plane_of_main_building"},
        {"turn": "left"},
        {"ordinal": 2, "direction": "south", "terminates_at": "low_courtyard_level"},
    ]
    assert route["ascent_is_reverse"] is True
    assert route["metric_geometry_status"] == "unresolved"

    massive = next(item for item in application.candidate.observations if item.id == "platform-massive-1")
    transition = massive.attributes["platform_transition"]
    assert transition == {
        "object_observation_id": "platform-timber-1",
        "kind": "single_step",
        "step_count": 1,
        "step_height": None,
        "metric_geometry_status": "unresolved",
    }

    relative_level_facts = [
        HumanRelativeLevelFact.model_validate(item) for item in journal["relative_level_facts"]
    ]
    level_set = validate_human_relative_level_facts(survey, relative_level_facts)
    assert len(level_set.facts) == 1
    level = level_set.facts[0]
    assert level.subject_observation_id == "platform-timber-1"
    assert level.object_observation_id == "platform-massive-1"
    assert level.relation == "lower_than"
    assert level.source.kind.value == "user_provided"


def test_owner_topology_journal_is_part_of_the_accepted_survey_checkpoint() -> None:
    checkpoint = _json(CHECKPOINT)

    assert checkpoint["post_acceptance_user_fact_journals"] == [
        "owner-spatial-topology-survey-facts-v0.1.json"
    ]
    assert checkpoint["invariants"]["known_measurements_count"] == 0
    assert checkpoint["fixture"] == "accepted-survey-v0.1.json"
