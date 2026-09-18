import json
from pathlib import Path

from brickhouse.survey import ArchitecturalSurvey, validate_survey_semantics


PROMPT = Path("frontend/brickhouse-survey-prompt.txt")
FIXTURE = Path("tests/survey/fixtures/relation-pass-case.json")


def _pair(relation):
    return frozenset((relation.subject_id, relation.object_id))


def test_active_survey_prompt_keeps_supported_weaker_relations() -> None:
    text = PROMPT.read_text(encoding="utf-8")

    assert "PROMPT DE RELEVÉ ARCHITECTURAL v2.9" in text
    assert "PASSE RELATIONNELLE BORNÉE — APRÈS IDENTITÉ, AVANT JSON FINAL" in text
    assert "si les preuves soutiennent un contact, un raccord ou une continuité physique réelle, utilise `connects_to`" in text
    assert "si les preuves soutiennent une juxtaposition architecturale réelle mais que le contact exact reste caché ou non prouvé, utilise `adjacent_to`" in text
    assert "l’absence de preuve suffisante pour `connects_to` ne doit jamais faire disparaître une relation `adjacent_to` pourtant soutenue" in text
    assert "Une ouverture proche d’un escalier ou d’une plateforme n’est PAS automatiquement un accès" in text
    assert "Ne transforme jamais l’échec de `connects_to` en perte automatique de toute relation" in text


def test_generic_relation_fixture_preserves_adjacency_without_hidden_connection() -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    scenario = payload["scenario"]["evidence_rules"]
    survey = ArchitecturalSurvey.model_validate(payload["expected_survey"])

    assert validate_survey_semantics(survey) == []
    assert scenario["stair_to_landing"] == "contact_supported"
    assert scenario["timber_to_landing"] == "adjacency_supported_contact_occluded"
    assert scenario["opening_to_circulation"] == "proximity_only"
    assert scenario["hidden_geometry"] == "unresolved"

    relations = {_pair(item): item for item in survey.relations}
    stair_landing = relations[frozenset(("stair-exterior", "landing-masonry"))]
    timber_landing = relations[frozenset(("platform-timber", "landing-masonry"))]

    assert stair_landing.kind.value == "connects_to"
    assert stair_landing.certainty.value == "certain"
    assert timber_landing.kind.value == "adjacent_to"
    assert timber_landing.certainty.value == "certain"

    assert not any(
        item.kind.value == "connects_to"
        and _pair(item) == frozenset(("platform-timber", "landing-masonry"))
        for item in survey.relations
    )
    assert not any("opening-high" in _pair(item) for item in survey.relations)

    metric_keys = {"x", "y", "z", "width", "depth", "height", "length", "distance", "step_height"}
    for observation in survey.observations:
        assert metric_keys.isdisjoint(observation.attributes)


def test_final_audit_explicitly_checks_relation_completeness() -> None:
    text = PROMPT.read_text(encoding="utf-8")

    assert "pour chaque relation architecturalement importante entre objets déjà identifiés" in text
    assert "`connects_to` si le raccord/contact est soutenu, sinon `adjacent_to` si seule la juxtaposition est soutenue, sinon aucune relation" in text
    assert "aucune zone occultée n’est transformée en `connects_to` certaine" in text
