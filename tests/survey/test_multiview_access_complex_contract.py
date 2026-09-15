from brickhouse.survey import ArchitecturalSurvey, analyze_multiview_identity, validate_survey_semantics

SOURCE = {"kind": "observed", "confidence": 0.8}


def _evidence(photo_index, observation):
    return {"photo_index": photo_index, "observation": observation}


def test_generic_multiview_access_complex_preserves_identity_topology_and_unknown_geometry():
    survey = ArchitecturalSurvey.model_validate({
        "schema_version": "0.1",
        "id": "generic-multiview-access-complex",
        "name": "Generic multi-view access complex",
        "photos": [
            {"photo_index": 1, "facade": "left", "description": "oblique access view", "source": SOURCE, "image_left_maps_to_facade_offset": "low"},
            {"photo_index": 2, "facade": "rear", "description": "rear access view", "source": SOURCE, "image_left_maps_to_facade_offset": "low"},
            {"photo_index": 3, "facade": "right", "description": "opposite access view", "source": SOURCE, "image_left_maps_to_facade_offset": "low"},
        ],
        "observations": [
            {
                "id": "deck",
                "kind": "platform",
                "certainty": "certain",
                "statement": "One elevated timber deck is observed across two views; the covered space below is open where visible.",
                "evidence": [_evidence(1, "timber deck edge and open underside visible"), _evidence(2, "same deck edge and supports continue")],
                "attributes": {
                    "multiview_identity": {"status": "same_physical_object", "photo_indexes": [1, 2], "cues": ["structural_continuity"]},
                    "open_below_where_observed": True,
                },
                "attribute_certainty": {"multiview_identity": "certain", "open_below_where_observed": "certain"},
            },
            {
                "id": "landing",
                "kind": "platform",
                "certainty": "certain",
                "statement": "Distinct masonry landing beside the deck.",
                "evidence": [_evidence(2, "material break distinguishes masonry landing from timber deck")],
            },
            {
                "id": "stair-system",
                "kind": "stair",
                "certainty": "certain",
                "statement": "One architectural stair system is tracked across views; exact hidden junction geometry is unknown.",
                "evidence": [_evidence(1, "lower portion of stair system visible"), _evidence(3, "continuing portion of same stair system visible")],
                "attributes": {
                    "multiview_identity": {"status": "same_physical_object", "photo_indexes": [1, 3], "cues": ["structural_continuity"]},
                    "future_scene_primitive_count": "unknown",
                },
                "attribute_certainty": {"multiview_identity": "certain", "future_scene_primitive_count": "unproven"},
            },
            {
                "id": "access-complex",
                "kind": "context",
                "certainty": "certain",
                "statement": "Observed architectural access ensemble; this identity does not merge its component objects.",
                "evidence": [_evidence(2, "deck and landing read as one access ensemble"), _evidence(3, "landing and stair read as same access ensemble")],
            },
        ],
        "relations": [
            {
                "id": "deck-connects-landing",
                "kind": "connects_to",
                "subject_id": "deck",
                "object_id": "landing",
                "certainty": "certain",
                "statement": "Circulation continuity is visible; exact metric seam is not asserted.",
                "evidence": [_evidence(2, "visible circulation continuity at material transition")],
            },
            {
                "id": "stair-connects-landing",
                "kind": "connects_to",
                "subject_id": "stair-system",
                "object_id": "landing",
                "certainty": "certain",
                "statement": "Architectural connection is visible while the exact hidden junction geometry remains unknown.",
                "evidence": [_evidence(3, "stair system reaches landing zone but junction is partly occluded")],
            },
            *[
                {
                    "id": f"{component}-part-of-access",
                    "kind": "part_of",
                    "subject_id": component,
                    "object_id": "access-complex",
                    "certainty": "certain",
                    "statement": "Component belongs to the observed access ensemble without becoming the same physical object.",
                    "evidence": [_evidence(photo, "component and ensemble continuity visible")],
                }
                for component, photo in (("deck", 2), ("landing", 2), ("stair-system", 3))
            ],
        ],
    })

    assert validate_survey_semantics(survey) == []
    identity = {fact.observation_id: fact for fact in analyze_multiview_identity(survey).facts}
    assert identity["deck"].identity.status == "same_physical_object"
    assert identity["stair-system"].identity.photo_indexes == [1, 3]
    assert survey.observations[0].attributes["open_below_where_observed"] is True
    assert survey.observations[2].certainty_for_attribute("future_scene_primitive_count").value == "unproven"

    relations = {relation.id: relation for relation in survey.relations}
    assert relations["stair-connects-landing"].certainty.value == "certain"
    assert relations["stair-connects-landing"].kind.value == "connects_to"
    assert not any(relation.kind.value == "same_physical_object" for relation in survey.relations)
    assert not any(
        {relation.subject_id, relation.object_id} == {"deck", "stair-system"}
        and relation.kind.value == "connects_to"
        for relation in survey.relations
    )
