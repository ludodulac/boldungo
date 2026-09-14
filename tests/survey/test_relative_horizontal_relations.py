from brickhouse.survey import Certainty, PhotoEvidence, RelationKind, SurveyRelation


def _relation(kind: RelationKind) -> SurveyRelation:
    return SurveyRelation(
        id=f"relation-{kind.value}",
        kind=kind,
        subject_id="opening-a",
        object_id="opening-b",
        certainty=Certainty.PLAUSIBLE,
        statement="Relative horizontal ordering observed directly in a facade photo.",
        evidence=[
            PhotoEvidence(
                photo_index=3,
                observation="Opening A is visibly offset horizontally from opening B.",
            )
        ],
    )


def test_left_of_and_right_of_accept_photo_evidence_without_user_source() -> None:
    for kind in (RelationKind.LEFT_OF, RelationKind.RIGHT_OF):
        relation = _relation(kind)
        assert relation.kind is kind
        assert relation.certainty is Certainty.PLAUSIBLE
        assert relation.evidence[0].photo_index == 3
        assert not hasattr(relation, "source")


def test_horizontal_relation_round_trip_is_stable() -> None:
    for kind in (RelationKind.LEFT_OF, RelationKind.RIGHT_OF):
        relation = _relation(kind)
        restored = SurveyRelation.model_validate_json(relation.model_dump_json())
        assert restored == relation


def test_existing_relation_values_are_unchanged() -> None:
    assert RelationKind.CONNECTS_TO.value == "connects_to"
    assert RelationKind.ADJACENT_TO.value == "adjacent_to"
    assert RelationKind.ALIGNED_WITH.value == "aligned_with"
    assert RelationKind.SUPPORTS.value == "supports"
    assert RelationKind.PART_OF.value == "part_of"
    assert RelationKind.SAME_PHYSICAL_OBJECT.value == "same_physical_object"
