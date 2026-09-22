from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from brickhouse.vision.multiview import (
    AspectCertainty,
    CertaintyLevel,
    ClaimStatus,
    Contradiction,
    IdentityCandidate,
    IdentityStatus,
    LocalObservation,
    DiscriminatingTest,
    InquiryState,
    InquiryTestResult,
    ObservablePrediction,
    ObservableProperty,
    HypothesisClaim,
    derive_observable_prediction,
    derive_discriminating_question,
    VisualInquiry,
    apply_inquiry_test,
    MultiViewPass,
    MultiViewWorkspace,
    OpenHypothesis,
    ViewAssessment,
    VisibilityStatus,
)
from brickhouse.vision.openai_provider import PhotoInput, analyze_building_photos
from brickhouse.survey.models import NormalizedImageRegion


def _obs(identifier: str, photo: int, category: str = "opening") -> LocalObservation:
    return LocalObservation(
        id=identifier,
        photo_index=photo,
        status=ClaimStatus.OBSERVED,
        visibility=VisibilityStatus.VISIBLE,
        proposed_category=category,
        statement=f"{category} is locally visible",
        certainty=AspectCertainty(
            existence=CertaintyLevel.CERTAIN,
            category=CertaintyLevel.PLAUSIBLE,
            metric=CertaintyLevel.UNKNOWN,
        ),
    )


def test_case_a_same_window_can_be_explicitly_linked_across_views():
    a, b = _obs("p1-window", 1), _obs("p2-window", 2)
    identity = IdentityCandidate(
        id="window-correspondence",
        observation_ids=[a.id, b.id],
        status=IdentityStatus.SAME_PHYSICAL_OBJECT,
        corroborating_photo_indexes=[1, 2],
        certainty=CertaintyLevel.CERTAIN,
    )
    workspace = MultiViewWorkspace(
        photo_count=2,
        pass_1=MultiViewPass(pass_number=1, observations=[a, b], identities=[identity]),
        pass_2=MultiViewPass(pass_number=2, observations=[a, b], identities=[identity]),
    )
    assert workspace.pass_2.identities[0].status is IdentityStatus.SAME_PHYSICAL_OBJECT


def test_case_b_occluded_facade_is_not_absent():
    assessment = ViewAssessment(
        photo_index=2,
        subject_hint="opening seen in photo 1",
        visibility=VisibilityStatus.OCCLUDED,
        statement="The relevant wall region is blocked by foreground structure.",
    )
    assert assessment.visibility is VisibilityStatus.OCCLUDED
    assert assessment.visibility is not VisibilityStatus.ABSENT


def test_case_c_incompatible_similar_objects_are_not_merged():
    a, b = _obs("left-window", 1), _obs("right-window", 2)
    identity = IdentityCandidate(
        id="incompatible-openings",
        observation_ids=[a.id, b.id],
        status=IdentityStatus.INCOMPATIBLE,
        conflicting_photo_indexes=[1, 2],
        certainty=CertaintyLevel.CERTAIN,
    )
    assert identity.status is IdentityStatus.INCOMPATIBLE


def test_case_d_probable_door_keeps_existence_stronger_than_type():
    opening = LocalObservation(
        id="possible-door",
        photo_index=1,
        status=ClaimStatus.OBSERVED,
        visibility=VisibilityStatus.VISIBLE,
        proposed_category="door",
        statement="An opening exists; door is a plausible subtype.",
        certainty=AspectCertainty(
            existence=CertaintyLevel.CERTAIN,
            category=CertaintyLevel.PLAUSIBLE,
            metric=CertaintyLevel.UNKNOWN,
        ),
    )
    assert opening.certainty.existence is CertaintyLevel.CERTAIN
    assert opening.certainty.category is CertaintyLevel.PLAUSIBLE
    assert opening.certainty.metric is CertaintyLevel.UNKNOWN


def test_case_e_conflicting_topologies_remain_unresolved_hypotheses():
    contradiction = Contradiction(
        id="stair-topology-conflict",
        claim_refs=["straight-run", "turning-run"],
        statement="Views support incompatible unresolved topology candidates.",
        photo_indexes=[1, 2],
    )
    straight = OpenHypothesis(
        id="straight-run",
        subject_refs=["stair"],
        statement="The stair may continue straight.",
        competing_with=["turning-run"],
    )
    turning = OpenHypothesis(
        id="turning-run",
        subject_refs=["stair"],
        statement="The stair may turn at an occluded landing.",
        competing_with=["straight-run"],
    )
    phase = MultiViewPass(
        pass_number=2,
        contradictions=[contradiction],
        hypotheses=[straight, turning],
    )
    assert phase.contradictions[0].resolved is False
    assert {h.id for h in phase.hypotheses} == {"straight-run", "turning-run"}


class _FakeResponses:
    def __init__(self, payload):
        self.payload = payload
        self.kwargs = None

    def create(self, **kwargs):
        self.kwargs = kwargs
        return SimpleNamespace(output_text=json.dumps(self.payload))


class _FakeClient:
    def __init__(self, payload):
        self.responses = _FakeResponses(payload)


def _minimal_building():
    return {
        "schema_version": "0.1",
        "id": "synthetic-house",
        "name": "Synthetic house",
        "building_type": "house",
        "units": "m",
        "volumes": [{
            "id": "main",
            "shape": "rectangular_prism",
            "position": {"x": 0, "y": 0, "z": 0},
            "width": 8,
            "depth": 6,
            "height": 5,
            "floors": 2,
            "source": {"kind": "inferred", "confidence": 0.5},
        }],
        "openings": [],
        "roofs": [],
        "appearance": {},
        "metadata": {"created_from": "photo_analysis"},
    }

def test_provider_requests_structured_multiview_workspace_without_extra_ai_calls():
    a, b = _obs("p1-opening", 1), _obs("p2-opening", 2)
    identity = IdentityCandidate(
        id="opening-match",
        observation_ids=[a.id, b.id],
        status=IdentityStatus.LIKELY_SAME,
        corroborating_photo_indexes=[1, 2],
        certainty=CertaintyLevel.PLAUSIBLE,
    )
    workspace = MultiViewWorkspace(
        photo_count=2,
        pass_1=MultiViewPass(pass_number=1, observations=[a, b], identities=[identity]),
        pass_2=MultiViewPass(pass_number=2, observations=[a, b], identities=[identity]),
    )
    payload = {
        "schema_version": "0.4",
        "building": _minimal_building(),
        "confidence": 0.6,
        "needs_confirmation": True,
        "multiview_workspace": workspace.model_dump(mode="json"),
    }
    client = _FakeClient(payload)
    result = analyze_building_photos(
        [
            PhotoInput(content=b"a", media_type="image/jpeg", filename="a.jpg"),
            PhotoInput(content=b"b", media_type="image/jpeg", filename="b.jpg"),
        ],
        client=client,
        model="synthetic-model",
    )
    assert result.multiview_workspace is not None
    assert result.multiview_workspace.pass_2.identities[0].status is IdentityStatus.LIKELY_SAME
    assert client.responses.kwargs is not None
    schema = client.responses.kwargs["text"]["format"]["schema"]
    assert "multiview_workspace" in schema["properties"]
    prompt_text = client.responses.kwargs["input"][0]["content"][0]["text"]
    assert "both multiview passes" in prompt_text



def _inquiry_fixture() -> tuple[VisualInquiry, list[OpenHypothesis]]:
    continues = OpenHypothesis(
        id="continues",
        subject_refs=["obs-a", "obs-b"],
        statement="The structure continues behind the occluder.",
        competing_with=["terminates"],
    )
    terminates = OpenHypothesis(
        id="terminates",
        subject_refs=["obs-a", "obs-b"],
        statement="The structure terminates behind the occluder.",
        competing_with=["continues"],
    )
    inquiry = VisualInquiry(
        id="continuity",
        question="Does the structure continue behind the occluder?",
        hypothesis_ids=["continues", "terminates"],
        predictions=[
            ObservablePrediction(
                id="p-continues",
                hypothesis_id="continues",
                statement="A compatible continuation reappears in the target ROI.",
            ),
            ObservablePrediction(
                id="p-terminates",
                hypothesis_id="terminates",
                statement="No continuation is present in the target ROI.",
            ),
        ],
        tests=[
            DiscriminatingTest(
                id="view-2-roi",
                photo_index=2,
                region=NormalizedImageRegion(x0=0.4, y0=0.2, x1=0.7, y1=0.6),
                prediction_ids=["p-continues", "p-terminates"],
                evidence_sought="Inspect whether a compatible continuation reappears.",
            )
        ],
    )
    return inquiry, [continues, terminates]


def test_inquiry_resolves_only_from_tested_discriminating_roi():
    inquiry, _ = _inquiry_fixture()
    result = InquiryTestResult(
        test_id="view-2-roi",
        inspected=True,
        region_in_frame=True,
        visibility=VisibilityStatus.VISIBLE,
        sufficient_visibility=True,
        statement="A compatible continuation is clearly visible.",
        compatible_prediction_ids=["p-continues"],
        discriminating=True,
    )

    resolved = apply_inquiry_test(inquiry, result)

    assert resolved.state is InquiryState.RESOLVED
    assert resolved.resolved_hypothesis_id == "continues"
    assert resolved.resolution_test_id == "view-2-roi"
    assert resolved.test_results[0].test_id == "view-2-roi"
    assert resolved.predictions[0].statement != resolved.test_results[0].statement


def test_inquiry_becomes_irreducible_unknown_when_accessible_evidence_is_exhausted():
    inquiry, _ = _inquiry_fixture()
    result = InquiryTestResult(
        test_id="view-2-roi",
        inspected=True,
        region_in_frame=True,
        visibility=VisibilityStatus.OCCLUDED,
        sufficient_visibility=False,
        statement="The target region is blocked.",
        compatible_prediction_ids=["p-continues", "p-terminates"],
        discriminating=False,
    )

    unresolved = apply_inquiry_test(
        inquiry,
        result,
        no_more_candidate_evidence=True,
        information_missing="An unoccluded view of the target region is unavailable.",
    )

    assert unresolved.state is InquiryState.IRREDUCIBLE_UNKNOWN
    assert unresolved.viable_hypothesis_ids == ["continues", "terminates"]
    assert "unoccluded" in unresolved.information_missing
    assert unresolved.stop_reason


def test_occluded_absence_cannot_refute_a_hypothesis():
    inquiry, _ = _inquiry_fixture()

    with pytest.raises(ValueError, match="discriminating evidence requires|occluded/non-visible ROI"):
        InquiryTestResult(
            test_id="view-2-roi",
            inspected=True,
            region_in_frame=True,
            visibility=VisibilityStatus.OCCLUDED,
            sufficient_visibility=False,
            statement="No continuation is visible because the ROI is occluded.",
            compatible_prediction_ids=["p-terminates"],
            discriminating=True,
        )

    safe_result = InquiryTestResult(
        test_id="view-2-roi",
        inspected=True,
        region_in_frame=True,
        visibility=VisibilityStatus.OCCLUDED,
        sufficient_visibility=False,
        statement="No continuation can be assessed in the occluded ROI.",
        compatible_prediction_ids=["p-continues", "p-terminates"],
        discriminating=False,
    )
    still_open = apply_inquiry_test(inquiry, safe_result)
    assert still_open.state is InquiryState.OPEN
    assert still_open.viable_hypothesis_ids == ["continues", "terminates"]


def test_existing_workspace_remains_valid_without_inquiry_fields():
    legacy_payload = {
        "schema_version": "0.1",
        "photo_count": 1,
        "pass_1": {"pass_number": 1},
        "pass_2": {"pass_number": 2},
    }

    workspace = MultiViewWorkspace.model_validate(legacy_payload)

    assert workspace.inquiries == []


def test_workspace_inquiry_reuses_existing_hypotheses_without_survey_promotion():
    inquiry, hypotheses = _inquiry_fixture()
    workspace = MultiViewWorkspace(
        photo_count=2,
        pass_1=MultiViewPass(pass_number=1),
        pass_2=MultiViewPass(pass_number=2, hypotheses=hypotheses),
        inquiries=[inquiry],
    )

    assert workspace.inquiries[0].hypothesis_ids == ["continues", "terminates"]



def _structured_prediction(
    prediction_id: str,
    hypothesis_id: str,
    **properties: str,
) -> ObservablePrediction:
    return ObservablePrediction(
        id=prediction_id,
        hypothesis_id=hypothesis_id,
        statement="Human-readable wording is not used for semantic comparison.",
        observable_properties=[
            ObservableProperty(name=name, value=value)
            for name, value in properties.items()
        ],
    )


def test_discriminating_question_is_derived_from_structured_prediction_difference():
    question = derive_discriminating_question([
        _structured_prediction(
            "p-continues", "continues", continuation="visible"
        ),
        _structured_prediction(
            "p-terminates", "terminates", continuation="absent"
        ),
    ])

    assert question is not None
    assert question.hypothesis_ids == ["continues", "terminates"]
    assert question.prediction_ids == ["p-continues", "p-terminates"]
    assert [item.property_name for item in question.discriminants] == ["continuation"]
    assert question.discriminants[0].expected_outcomes == {
        "continues": "visible",
        "terminates": "absent",
    }
    assert question.evidence_needed == ["continuation"]


def test_equivalent_structured_predictions_generate_no_false_question():
    question = derive_discriminating_question([
        _structured_prediction("p-a", "h-a", continuation="visible"),
        _structured_prediction("p-b", "h-b", continuation="visible"),
    ])

    assert question is None


def test_multiple_observable_differences_are_all_preserved_without_ranking():
    question = derive_discriminating_question([
        _structured_prediction(
            "p-a", "h-a", continuation="visible", edge_alignment="aligned"
        ),
        _structured_prediction(
            "p-b", "h-b", continuation="absent", edge_alignment="offset"
        ),
    ])

    assert question is not None
    assert [item.property_name for item in question.discriminants] == [
        "continuation",
        "edge_alignment",
    ]
    assert question.evidence_needed == ["continuation", "edge_alignment"]


def test_non_observable_conceptual_difference_generates_no_visual_question():
    predictions = [
        ObservablePrediction(
            id="p-a",
            hypothesis_id="h-a",
            statement="Conceptual model A differs, but defines no observable consequence.",
        ),
        ObservablePrediction(
            id="p-b",
            hypothesis_id="h-b",
            statement="Conceptual model B differs, but defines no observable consequence.",
        ),
    ]

    assert derive_discriminating_question(predictions) is None



def _structured_hypothesis(
    hypothesis_id: str,
    relation: str,
    competing_with: list[str] | None = None,
) -> OpenHypothesis:
    return OpenHypothesis(
        id=hypothesis_id,
        subject_refs=["surface-s"],
        statement="Human-readable hypothesis prose is not used to derive the prediction.",
        competing_with=competing_with or [],
        claim=HypothesisClaim(
            subject_ref="surface-s",
            relation=relation,
            object_ref="occluder-o",
        ),
    )


def test_structured_continues_hypothesis_derives_observable_prediction():
    hypothesis = _structured_hypothesis("h-continues", "CONTINUES")

    prediction = derive_observable_prediction(hypothesis)

    assert prediction is not None
    assert prediction.hypothesis_id == "h-continues"
    assert {item.name: item.value for item in prediction.observable_properties} == {
        "continuation": "visible",
        "observability_required": "in_frame+non_occluded+sufficient_visibility",
    }


def test_structured_terminates_hypothesis_derives_different_prediction():
    hypothesis = _structured_hypothesis("h-terminates", "TERMINATES")

    prediction = derive_observable_prediction(hypothesis)

    assert prediction is not None
    assert {item.name: item.value for item in prediction.observable_properties}[
        "continuation"
    ] == "absent"


def test_structured_hypotheses_derive_predictions_then_discriminating_question():
    hypotheses = [
        _structured_hypothesis("h-continues", "CONTINUES", ["h-terminates"]),
        _structured_hypothesis("h-terminates", "TERMINATES", ["h-continues"]),
    ]

    predictions = [derive_observable_prediction(item) for item in hypotheses]

    assert all(item is not None for item in predictions)
    question = derive_discriminating_question(predictions)
    assert question is not None
    assert [item.property_name for item in question.discriminants] == ["continuation"]
    assert question.discriminants[0].expected_outcomes == {
        "h-continues": "visible",
        "h-terminates": "absent",
    }


def test_unknown_structured_relation_has_no_derivable_prediction():
    hypothesis = _structured_hypothesis("h-unknown", "ALIGNED_WITH")

    assert derive_observable_prediction(hypothesis) is None


def test_derived_absence_prediction_does_not_bypass_occlusion_safety():
    hypotheses = [
        _structured_hypothesis("h-continues", "CONTINUES", ["h-terminates"]),
        _structured_hypothesis("h-terminates", "TERMINATES", ["h-continues"]),
    ]
    predictions = [derive_observable_prediction(item) for item in hypotheses]
    inquiry = VisualInquiry(
        id="derived-continuity",
        question="Derived by Experiment 009 from the predictions.",
        hypothesis_ids=[item.id for item in hypotheses],
        predictions=predictions,
        tests=[
            DiscriminatingTest(
                id="occluded-roi",
                photo_index=2,
                region=NormalizedImageRegion(x0=0.2, y0=0.2, x1=0.5, y1=0.5),
                prediction_ids=[item.id for item in predictions],
                evidence_sought="Inspect continuation only if the region is observable.",
            )
        ],
    )

    with pytest.raises(ValueError, match="discriminating evidence requires|occluded/non-visible ROI"):
        InquiryTestResult(
            test_id="occluded-roi",
            inspected=True,
            region_in_frame=True,
            visibility=VisibilityStatus.OCCLUDED,
            sufficient_visibility=False,
            statement="Continuation is not visible because the region is occluded.",
            compatible_prediction_ids=["derived-h-terminates"],
            discriminating=True,
        )

    safe_result = InquiryTestResult(
        test_id="occluded-roi",
        inspected=True,
        region_in_frame=True,
        visibility=VisibilityStatus.OCCLUDED,
        sufficient_visibility=False,
        statement="The derived predictions cannot be tested in this occluded region.",
        compatible_prediction_ids=[item.id for item in predictions],
        discriminating=False,
    )
    still_open = apply_inquiry_test(inquiry, safe_result)
    assert still_open.state is InquiryState.OPEN
    assert still_open.viable_hypothesis_ids == ["h-continues", "h-terminates"]


def test_legacy_text_only_hypothesis_remains_compatible():
    hypothesis = OpenHypothesis(
        id="legacy-h",
        subject_refs=["obs-a"],
        statement="Legacy hypothesis without structured claim.",
    )

    assert hypothesis.claim is None
    assert derive_observable_prediction(hypothesis) is None
