import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from brickhouse.survey.models import ArchitecturalSurvey
from brickhouse.survey.relation_patch import (
    SurveyRelationPatch,
    apply_survey_relation_patch,
    survey_content_fingerprint,
)


FIXTURE = Path("tests/survey/fixtures/relation-patch-base-v0.1.json")


def _base() -> ArchitecturalSurvey:
    return ArchitecturalSurvey.model_validate_json(FIXTURE.read_text(encoding="utf-8"))


def _valid_patch_payload(base: ArchitecturalSurvey) -> dict:
    return {
        "schema_version": "0.1",
        "kind": "survey_relation_patch",
        "survey_id": base.id,
        "base_fingerprint": survey_content_fingerprint(base),
        "patch_id": "patch-adjacency-001",
        "mission": "architectural_relations",
        "add_relations": [
            {
                "id": "relation-timber-landing",
                "kind": "adjacent_to",
                "subject_id": "platform-timber",
                "object_id": "landing-masonry",
                "certainty": "certain",
                "statement": "The timber platform and masonry landing are visibly adjacent while their exact contact remains occluded.",
                "evidence": [
                    {
                        "photo_index": 2,
                        "observation": "Both walking surfaces are visible side by side; the exact junction is hidden."
                    }
                ]
            }
        ]
    }


def test_relation_patch_adds_only_explicit_relation_and_preserves_base() -> None:
    base = _base()
    patch = SurveyRelationPatch.model_validate(_valid_patch_payload(base))

    application = apply_survey_relation_patch(base, patch)
    candidate = application.candidate

    assert candidate.photos == base.photos
    assert candidate.observations == base.observations
    assert candidate.canonical_frame == base.canonical_frame
    assert candidate.known_measurements == base.known_measurements
    assert candidate.representation_policy == base.representation_policy
    assert candidate.name == base.name
    assert candidate.notes == base.notes

    base_count = len(base.relations)
    assert candidate.relations[:base_count] == base.relations
    assert candidate.relations[base_count:] == patch.add_relations
    assert application.added_relations == patch.add_relations

    assert [item.id for item in candidate.observations if item.kind.value == "opening"] == [
        "opening-existing"
    ]
    assert any(item.id == "chimney-existing" for item in candidate.observations)


def test_relation_patch_can_return_no_gain_without_mutating_base() -> None:
    base = _base()
    payload = _valid_patch_payload(base)
    payload["patch_id"] = "patch-no-gain-001"
    payload["add_relations"] = []
    patch = SurveyRelationPatch.model_validate(payload)

    application = apply_survey_relation_patch(base, patch)

    assert application.added_relations == []
    assert application.candidate == base


def test_relation_patch_fingerprint_is_deterministic_and_binds_exact_base() -> None:
    base = _base()
    payload = base.model_dump(mode="json")
    reordered = json.loads(json.dumps(payload, sort_keys=False))
    same = ArchitecturalSurvey.model_validate(reordered)
    assert survey_content_fingerprint(base) == survey_content_fingerprint(same)

    patch_payload = _valid_patch_payload(base)
    patch_payload["base_fingerprint"] = "0" * 64
    patch = SurveyRelationPatch.model_validate(patch_payload)
    with pytest.raises(ValueError, match="base_fingerprint"):
        apply_survey_relation_patch(base, patch)


def test_relation_patch_rejects_unknown_endpoint_and_photo() -> None:
    base = _base()

    endpoint_payload = _valid_patch_payload(base)
    endpoint_payload["add_relations"][0]["object_id"] = "missing-observation"
    endpoint_patch = SurveyRelationPatch.model_validate(endpoint_payload)
    with pytest.raises(ValueError, match="absent from the base Survey"):
        apply_survey_relation_patch(base, endpoint_patch)

    photo_payload = _valid_patch_payload(base)
    photo_payload["add_relations"][0]["evidence"][0]["photo_index"] = 999
    photo_patch = SurveyRelationPatch.model_validate(photo_payload)
    with pytest.raises(ValueError, match="unknown photo"):
        apply_survey_relation_patch(base, photo_patch)


def test_relation_patch_rejects_self_relation_collision_and_duplicate() -> None:
    base = _base()

    self_payload = _valid_patch_payload(base)
    self_payload["add_relations"][0]["object_id"] = "platform-timber"
    with pytest.raises(ValidationError, match="subject_id and object_id must differ"):
        SurveyRelationPatch.model_validate(self_payload)

    collision_payload = _valid_patch_payload(base)
    collision_payload["add_relations"][0]["id"] = "relation-stair-landing"
    collision_patch = SurveyRelationPatch.model_validate(collision_payload)
    with pytest.raises(ValueError, match="collides"):
        apply_survey_relation_patch(base, collision_patch)

    duplicate_payload = _valid_patch_payload(base)
    duplicate_payload["add_relations"][0].update(
        {
            "id": "relation-stair-landing-copy",
            "kind": "connects_to",
            "subject_id": "stair-exterior",
            "object_id": "landing-masonry",
        }
    )
    duplicate_patch = SurveyRelationPatch.model_validate(duplicate_payload)
    with pytest.raises(ValueError, match="duplicates an existing"):
        apply_survey_relation_patch(base, duplicate_patch)


def test_relation_patch_contract_forbids_out_of_scope_content() -> None:
    base = _base()

    top_level = _valid_patch_payload(base)
    top_level["photos"] = []
    with pytest.raises(ValidationError, match="extra"):
        SurveyRelationPatch.model_validate(top_level)

    nested = _valid_patch_payload(base)
    nested["add_relations"][0]["facade"] = "rear"
    with pytest.raises(ValidationError, match="outside SurveyRelation"):
        SurveyRelationPatch.model_validate(nested)

    observation_attempt = _valid_patch_payload(base)
    observation_attempt["observations"] = [{"id": "new-opening"}]
    with pytest.raises(ValidationError, match="extra"):
        SurveyRelationPatch.model_validate(observation_attempt)
