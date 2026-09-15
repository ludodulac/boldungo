import pytest

from brickhouse.scene import ArchitecturalScene

SOURCE = {"kind": "inferred", "confidence": 0.6}


def _payload():
    return {
        "schema_version": "0.2",
        "id": "scene-refined-survey-object",
        "name": "Refined architectural identity",
        "units": "m",
        "volumes": [{
            "id": "main", "position": {"x": 0, "y": 0, "z": 0},
            "width": {"value": 10, "source": SOURCE},
            "depth": {"value": 8, "source": SOURCE},
            "height": {"value": 6, "source": SOURCE},
            "floors": 2, "source": SOURCE,
        }],
        "platforms": [{
            "id": "landing", "host_volume_id": "main",
            "position": {"x": -2, "y": 3, "z": 1.4},
            "width": 2, "depth": 2, "thickness": 0.2,
            "material": "concrete", "source": SOURCE,
        }],
        "stairs": [
            {
                "id": "stair-run-a", "start": {"x": -1, "y": 1, "z": 0},
                "end": {"x": -1, "y": 2, "z": 0.7}, "width": 1,
                "material": "concrete", "source": SOURCE,
            },
            {
                "id": "stair-run-b", "start": {"x": -1, "y": 2, "z": 0.7},
                "end": {"x": -0.2, "y": 2, "z": 1.1}, "width": 1,
                "material": "concrete", "source": SOURCE,
            },
        ],
        "survey_realizations": [{
            "survey_observation_id": "stair-exterior",
            "scene_object_ids": ["stair-run-a", "stair-run-b"],
            "evidence": [{"photo_index": 2, "observation": "same stair system is visible across the turn"}],
        }],
        "relations": [{
            "id": "stair-to-landing", "kind": "connects_to",
            "subject_id": "stair-exterior", "object_id": "landing",
            "certainty": "certain", "geometry_status": "unresolved",
            "statement": "architectural connection is certain; exact junction remains hidden",
            "evidence": [{"photo_index": 3, "observation": "stair system continues toward landing"}],
        }],
        "appearance": {"walls": {"color": "off_white"}, "roof": {"color": "dark_gray"}, "frames": {"color": "white"}},
    }


def test_one_survey_object_can_be_realized_by_multiple_scene_primitives():
    scene = ArchitecturalScene.model_validate(_payload())
    realization = scene.survey_realizations[0]
    assert realization.survey_observation_id == "stair-exterior"
    assert realization.scene_object_ids == ["stair-run-a", "stair-run-b"]
    assert realization.evidence[0].photo_index == 2


def test_certain_relation_survives_refinement_without_metric_promotion():
    scene = ArchitecturalScene.model_validate(_payload())
    relation = scene.relations[0]
    assert relation.subject_id == "stair-exterior"
    assert relation.certainty.value == "certain"
    assert relation.geometry_status == "unresolved"


def test_realization_rejects_unknown_scene_primitive():
    payload = _payload()
    payload["survey_realizations"][0]["scene_object_ids"].append("invented-run")
    with pytest.raises(ValueError, match="unknown Scene objects"):
        ArchitecturalScene.model_validate(payload)


def test_unresolved_relation_still_requires_a_represented_endpoint():
    payload = _payload()
    payload["relations"][0]["subject_id"] = "unknown-survey-object"
    payload["relations"][0]["object_id"] = "other-unknown-survey-object"
    with pytest.raises(ValueError, match="directly or through survey_realizations"):
        ArchitecturalScene.model_validate(payload)
