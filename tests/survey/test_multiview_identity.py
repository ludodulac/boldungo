from copy import deepcopy

from brickhouse.survey import (
    ArchitecturalSurvey,
    analyze_multiview_identity,
    validate_survey_semantics,
)

SOURCE = {"kind": "inferred", "confidence": 0.7}


def _survey(*, identity=None, certainty="certain", evidence=(1, 2)):
    attributes = {}
    attribute_certainty = {}
    if identity is not None:
        attributes["multiview_identity"] = identity
        attribute_certainty["multiview_identity"] = certainty
    return ArchitecturalSurvey.model_validate({
        "schema_version": "0.1",
        "id": "multiview-test",
        "name": "Multiview test",
        "photos": [
            {"photo_index": 1, "facade": "front", "description": "front", "source": SOURCE, "image_left_maps_to_facade_offset": "low"},
            {"photo_index": 2, "facade": "right", "description": "right", "source": SOURCE, "image_left_maps_to_facade_offset": "low"},
            {"photo_index": 3, "facade": "rear", "description": "rear", "source": SOURCE, "image_left_maps_to_facade_offset": "low"},
        ],
        "observations": [{
            "id": "chimney-a",
            "kind": "chimney",
            "certainty": "certain",
            "statement": "chimney candidate tracked across views",
            "evidence": [{"photo_index": index, "observation": f"candidate visible in photo {index}"} for index in evidence],
            "attributes": attributes,
            "attribute_certainty": attribute_certainty,
        }],
    })


def _relational_survey(*, identity, certainty="certain", relation_b_certainty="plausible"):
    observations = [{
        "id": "chimney-a",
        "kind": "chimney",
        "certainty": "certain",
        "statement": "chimney candidate tracked across three views",
        "evidence": [
            {"photo_index": 1, "observation": "chimney visible near anchor-a"},
            {"photo_index": 2, "observation": "chimney visible near anchor-b"},
            {"photo_index": 3, "observation": "chimney visible near anchor-c"},
        ],
        "attributes": {"multiview_identity": identity},
        "attribute_certainty": {"multiview_identity": certainty},
    }]
    for index, anchor_id in enumerate(("anchor-a", "anchor-b", "anchor-c", "anchor-d"), start=1):
        observations.append({
            "id": anchor_id,
            "kind": "opening",
            "facade": "front" if index == 1 else "right",
            "certainty": "certain",
            "statement": f"stable local anchor {anchor_id}",
            "evidence": [{"photo_index": min(index, 3), "observation": f"{anchor_id} visible"}],
            "attributes": {"physical_object_count": 1},
        })

    return ArchitecturalSurvey.model_validate({
        "schema_version": "0.1",
        "id": "relational-multiview-test",
        "name": "Relational multiview test",
        "photos": [
            {"photo_index": 1, "facade": "front", "description": "front", "source": SOURCE, "image_left_maps_to_facade_offset": "low"},
            {"photo_index": 2, "facade": "right", "description": "right", "source": SOURCE, "image_left_maps_to_facade_offset": "low"},
            {"photo_index": 3, "facade": "rear", "description": "rear", "source": SOURCE, "image_left_maps_to_facade_offset": "low"},
        ],
        "observations": observations,
        "relations": [
            {
                "id": "rel-chimney-anchor-a",
                "kind": "left_of",
                "subject_id": "chimney-a",
                "object_id": "anchor-a",
                "certainty": "certain",
                "statement": "chimney is left of anchor-a in the front view",
                "evidence": [{"photo_index": 1, "observation": "local ordering visible"}],
            },
            {
                "id": "rel-chimney-anchor-b",
                "kind": "adjacent_to",
                "subject_id": "chimney-a",
                "object_id": "anchor-b",
                "certainty": relation_b_certainty,
                "statement": "chimney remains adjacent to anchor-b in the side view",
                "evidence": [{"photo_index": 2, "observation": "local neighborhood visible"}],
            },
            {
                "id": "rel-anchor-a-anchor-d",
                "kind": "aligned_with",
                "subject_id": "anchor-a",
                "object_id": "anchor-d",
                "certainty": "certain",
                "statement": "two anchors align independently of the chimney",
                "evidence": [{"photo_index": 1, "observation": "anchor alignment visible"}],
            },
        ],
    })


def _codes(survey):
    return {issue.code for issue in validate_survey_semantics(survey)}


def test_certain_same_object_identity_accepts_discriminating_cue():
    survey = _survey(identity={
        "status": "same_physical_object",
        "photo_indexes": [1, 2],
        "cues": ["relative_position", "shape_detail"],
    })

    report = analyze_multiview_identity(survey)

    assert report.issues == []
    assert report.facts[0].identity.photo_indexes == [1, 2]


def test_certain_same_object_identity_requires_discriminating_cue():
    survey = _survey(identity={
        "status": "same_physical_object",
        "photo_indexes": [1, 2],
        "cues": [],
    })

    assert "certain_multiview_identity_missing_discriminating_cue" in _codes(survey)


def test_unresolved_identity_cannot_be_certain():
    survey = _survey(identity={
        "status": "unresolved",
        "photo_indexes": [1, 2],
        "cues": [],
    })

    assert "unresolved_multiview_identity_cannot_be_certain" in _codes(survey)


def test_identity_photo_indexes_must_be_backed_by_observation_evidence():
    survey = _survey(
        identity={"status": "same_physical_object", "photo_indexes": [1, 3], "cues": ["shape_detail"]},
        evidence=(1, 2),
    )

    assert "multiview_identity_missing_evidence_photo" in _codes(survey)


def test_legacy_multiphoto_observation_remains_valid_without_new_attribute():
    survey = _survey(identity=None)
    before = deepcopy(survey.model_dump())

    report = analyze_multiview_identity(survey)

    assert report.facts == []
    assert report.issues == []
    assert survey.model_dump() == before


def test_unresolved_identity_preserves_uncertainty_without_invention():
    survey = _survey(
        identity={"status": "unresolved", "photo_indexes": [1, 2], "cues": []},
        certainty="unproven",
    )
    before = deepcopy(survey.model_dump())

    report = analyze_multiview_identity(survey)

    assert report.issues == []
    assert report.facts[0].certainty.value == "unproven"
    assert survey.model_dump() == before


def test_relation_backed_relative_position_identity_is_valid():
    survey = _relational_survey(
        identity={
            "status": "same_physical_object",
            "photo_indexes": [1, 2, 3],
            "cues": ["relative_position"],
            "supporting_relation_ids": ["rel-chimney-anchor-a", "rel-chimney-anchor-b"],
        },
        relation_b_certainty="certain",
    )

    report = analyze_multiview_identity(survey)

    assert report.issues == []
    assert report.facts[0].identity.supporting_relation_ids == [
        "rel-chimney-anchor-a",
        "rel-chimney-anchor-b",
    ]


def test_certain_identity_cannot_depend_on_plausible_relation_support():
    survey = _relational_survey(identity={
        "status": "same_physical_object",
        "photo_indexes": [1, 2, 3],
        "cues": ["relative_position"],
        "supporting_relation_ids": ["rel-chimney-anchor-a", "rel-chimney-anchor-b"],
    })

    assert "certain_multiview_identity_requires_certain_relation_support" in _codes(survey)


def test_plausible_identity_accepts_plausible_relation_support():
    survey = _relational_survey(
        identity={
            "status": "same_physical_object",
            "photo_indexes": [1, 2, 3],
            "cues": ["relative_position"],
            "supporting_relation_ids": ["rel-chimney-anchor-a", "rel-chimney-anchor-b"],
        },
        certainty="plausible",
    )

    assert "certain_multiview_identity_requires_certain_relation_support" not in _codes(survey)


def test_supporting_relation_id_must_exist():
    survey = _relational_survey(identity={
        "status": "same_physical_object",
        "photo_indexes": [1, 2, 3],
        "cues": ["relative_position"],
        "supporting_relation_ids": ["missing-relation"],
    })

    assert "multiview_identity_support_relation_missing" in _codes(survey)


def test_supporting_relation_must_be_relevant_to_identity_observation():
    survey = _relational_survey(identity={
        "status": "same_physical_object",
        "photo_indexes": [1, 2, 3],
        "cues": ["relative_position"],
        "supporting_relation_ids": ["rel-anchor-a-anchor-d"],
    })

    assert "multiview_identity_support_relation_not_relevant" in _codes(survey)


def test_relative_position_text_alone_cannot_promote_identity_to_certain():
    survey = _relational_survey(identity={
        "status": "same_physical_object",
        "photo_indexes": [1, 2, 3],
        "cues": ["relative_position"],
    })

    assert "certain_multiview_identity_relative_position_requires_relation_evidence" in _codes(survey)


def test_plausible_relative_position_identity_remains_valid_without_relation_ids():
    survey = _relational_survey(
        identity={
            "status": "same_physical_object",
            "photo_indexes": [1, 2, 3],
            "cues": ["relative_position"],
        },
        certainty="plausible",
    )

    assert "certain_multiview_identity_relative_position_requires_relation_evidence" not in _codes(survey)
