from __future__ import annotations

import json
from pathlib import Path

from brickhouse.survey import (
    ArchitecturalSurvey,
    SurveyAudit,
    SurveyCorrection,
    SurveyObservation,
    SurveyRelation,
    validate_survey_correction,
)
from brickhouse.scene import ArchitecturalScene


ROOT = Path(__file__).parents[2]
BENCHMARK = ROOT / "frontend" / "benchmarks" / "real-house-5"
SCENE = ROOT / "tests" / "fixtures" / "real_house_5_scene_candidate.json"


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_real_house_5_covered_void_correction_uses_explicit_correction_contract() -> None:
    correction = SurveyCorrection.model_validate(_json(BENCHMARK / "covered-void-survey-correction-v0.1.json"))
    corrected = correction.candidate
    original = corrected.model_copy(deep=True)
    original.observations.insert(
        -2,
        SurveyObservation.model_validate(
            {
                "id": "volume-exterior-1",
                "kind": "volume",
                "facade": "left",
                "certainty": "certain",
                "statement": "Volume exterieur massif blanc sous/au voisinage du palier, avec espace couvert ouvert visible.",
                "evidence": [
                    {"photo_index": 4, "observation": "Parois massives blanches et grande baie ouverte de l'espace couvert."},
                    {"photo_index": 5, "observation": "Le volume est recoupe derriere l'escalier."},
                ],
                "attributes": {},
                "attribute_certainty": {},
            }
        ),
    )
    original.relations.append(
        SurveyRelation.model_validate(
            {
                "id": "relation-volume-supports-platform",
                "kind": "supports",
                "subject_id": "volume-exterior-1",
                "object_id": "platform-massive-1",
                "certainty": "certain",
                "statement": "Le volume massif se trouve sous et porte la surface de palier distinguee au sommet.",
                "evidence": [
                    {"photo_index": 4, "observation": "La surface de palier est directement au sommet du volume blanc."}
                ],
            }
        )
    )

    audit = SurveyAudit.model_validate(_json(BENCHMARK / "covered-void-survey-audit-v0.1.json"))
    assert correction.candidate == corrected
    assert validate_survey_correction(original, audit, correction) == []


def test_real_house_5_scene_preserves_covered_void_instead_of_filling_it() -> None:
    scene = ArchitecturalScene.model_validate(_json(SCENE))

    assert [volume.id for volume in scene.volumes] == ["volume_main"]
    assert {platform.id for platform in scene.platforms} >= {
        "platform-massive-1",
        "platform-timber-1",
    }
    assert {stair.id for stair in scene.stairs} == {"stair-exterior-1"}
    assert all(
        "volume-exterior-1" not in {relation.subject_id, relation.object_id}
        for relation in scene.relations
    )
