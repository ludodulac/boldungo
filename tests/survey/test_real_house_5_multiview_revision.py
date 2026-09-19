import json
from pathlib import Path

from brickhouse.survey import ArchitecturalSurvey, analyze_multiview_identity, analyze_survey_stair_topology, validate_survey_semantics


ROOT = Path(__file__).parents[2]
SURVEY = ROOT / "frontend" / "benchmarks" / "real-house-5" / "accepted-survey-v0.1.json"


def _survey() -> ArchitecturalSurvey:
    return ArchitecturalSurvey.model_validate(json.loads(SURVEY.read_text(encoding="utf-8")))


def test_real_house_5_multiview_revision_preserves_topology_without_fake_metrics() -> None:
    survey = _survey()
    assert validate_survey_semantics(survey) == []
    assert len(survey.photos) == 22
    assert survey.known_measurements == []

    observations = {item.id: item for item in survey.observations}
    stair = observations["stair-exterior-1"]
    topology = analyze_survey_stair_topology(survey)
    fact = next(item for item in topology.facts if item.observation_id == stair.id)
    assert topology.issues == []
    assert fact.topology.minimum_run_count == 2
    assert fact.topology.exact_run_count is None
    assert fact.topology.direction_change is True
    assert fact.topology.turning_node_kind == "landing"
    assert not {"width", "height", "run_length", "turn_coordinate"} & set(stair.attributes["stair_topology"])

    landing = observations["platform-massive-1"]
    assert "volume exterieur blanc" not in landing.statement.lower()
    assert "aucun volume fermé sous-jacent n'est démontré" in landing.statement
    assert "enclosure" not in landing.attributes
    assert "parapet" not in landing.attributes

    deck = observations["platform-timber-1"]
    assert deck.attributes["supports"] == [
        "Poteaux et contreventements bois visibles sous la plateforme dans la photo 3."
    ]
    assert "support_count" not in deck.attributes
    assert "support_positions" not in deck.attributes

    assert "DETTE CONTRACTUELLE" in (survey.notes or "")
    assert "géométrie non résolue" in (survey.notes or "")


def test_real_house_5_lower_left_opening_is_now_multiview_confirmed_door() -> None:
    survey = _survey()
    observations = {item.id: item for item in survey.observations}
    door = observations["left-opening-2"]

    assert door.attributes["semantic_type"] == "door"
    assert door.certainty_for_attribute("semantic_type").value == "certain"
    assert {item.photo_index for item in door.evidence} >= {3, 8, 9}

    identities = {item.observation_id: item for item in analyze_multiview_identity(survey).facts}
    identity = identities["left-opening-2"]
    assert identity.identity.status == "same_physical_object"
    assert identity.identity.photo_indexes == [3, 8, 9]
    assert identity.certainty.value == "certain"

    relations = {item.id: item for item in survey.relations}
    assert relations["relation-door-massive-platform"].certainty.value == "certain"
    assert relations["relation-door-massive-platform"].object_id == "platform-massive-1"
    assert relations["relation-massive-timber-platform"].certainty.value == "certain"


def test_real_house_5_rainwater_truth_is_nonmetric_equipment_only() -> None:
    survey = _survey()
    observations = {item.id: item for item in survey.observations}
    drainage = observations["rainwater-downpipe-left-1"]

    assert drainage.kind.value == "equipment"
    assert drainage.certainty.value == "certain"
    assert drainage.attributes == {}
    assert {item.photo_index for item in drainage.evidence} == {9, 22}
