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
    IdentityInquiryState,
    detect_identity_uncertainties,
    LocalObservation,
    EvidenceRegion,
    CandidateEvidenceTarget,
    DiscriminatingTest,
    InquiryState,
    InquiryTestResult,
    ObservablePrediction,
    ObservableProperty,
    HypothesisClaim,
    derive_observable_prediction,
    derive_candidate_evidence_targets,
    assess_discrimination_targets,
    select_discrimination_targets,
    DiscriminationPotential,
    EvidenceTargetSelection,
    ApplicabilityState,
    derive_discriminant_applicability,
    StructuredUncertainty,
    derive_competing_hypotheses,
    detect_continuity_uncertainties,
    VisualEvidenceStatus,
    VisualEvidenceResponse,
    VisualInquiryRequest,
    build_visual_inquiry_request,
    visual_evidence_response_schema,
    visual_evidence_response_invariants,
    build_executable_visual_inquiry,
    import_visual_evidence_response,
    VisualBootstrapRequest,
    VisualBootstrapResponse,
    build_visual_bootstrap_request,
    import_visual_bootstrap_response,
    visual_bootstrap_response_schema,
    visual_bootstrap_response_invariants,
    derive_discriminating_question,
    VisualInquiry,
    apply_inquiry_test,
    MultiViewPass,
    MultiViewWorkspace,
    OpenHypothesis,
    ViewAssessment,
    VisibilityStatus,
    inquiry_property_registry_payload,
    INQUIRY_PROPERTY_REGISTRY,

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



def _targeting_chain(observations: list[LocalObservation]):
    hypotheses = [
        _structured_hypothesis("h-continues", "CONTINUES", ["h-terminates"]),
        _structured_hypothesis("h-terminates", "TERMINATES", ["h-continues"]),
    ]
    predictions = [derive_observable_prediction(item) for item in hypotheses]
    question = derive_discriminating_question(predictions)
    assert question is not None
    targets = derive_candidate_evidence_targets(question, hypotheses, observations)
    return hypotheses, predictions, question, targets


def _target_observation(
    observation_id: str,
    photo_index: int,
    *,
    visibility: VisibilityStatus = VisibilityStatus.VISIBLE,
    region: NormalizedImageRegion | None = None,
) -> LocalObservation:
    return LocalObservation(
        id=observation_id,
        photo_index=photo_index,
        status=(
            ClaimStatus.OBSERVED
            if visibility is VisibilityStatus.VISIBLE
            else ClaimStatus.INFERRED
        ),
        visibility=visibility,
        region=region or NormalizedImageRegion(x0=0.1, y0=0.2, x1=0.4, y1=0.5),
        statement="Synthetic observation used only for generic evidence targeting.",
    )


def test_linked_visible_region_becomes_testable_candidate_target():
    _, _, _, targets = _targeting_chain([
        _target_observation("surface-s", 2),
    ])

    assert len(targets) == 1
    assert targets[0].photo_index == 2
    assert targets[0].source_observation_ids == ["surface-s"]
    assert targets[0].discriminant_property == "continuation"
    assert targets[0].testable is True


def test_multiple_linked_regions_are_preserved_without_ranking():
    _, _, _, targets = _targeting_chain([
        _target_observation("surface-s", 2),
        _target_observation(
            "surface-s",
            4,
            region=NormalizedImageRegion(x0=0.5, y0=0.1, x1=0.8, y1=0.4),
        ),
    ])

    assert [item.photo_index for item in targets] == [2, 4]
    assert all(item.testable for item in targets)


def test_occluded_or_non_visible_linked_regions_are_context_not_testable_targets():
    _, _, _, targets = _targeting_chain([
        _target_observation("surface-s", 2, visibility=VisibilityStatus.OCCLUDED),
        _target_observation("surface-s", 3, visibility=VisibilityStatus.NON_VISIBLE),
    ])

    assert len(targets) == 2
    assert all(item.testable is False for item in targets)
    assert {item.visibility for item in targets} == {
        VisibilityStatus.OCCLUDED,
        VisibilityStatus.NON_VISIBLE,
    }


def test_no_exploitable_region_yields_no_testable_evidence_target():
    _, _, _, targets = _targeting_chain([
        _target_observation("surface-s", 2, visibility=VisibilityStatus.OCCLUDED),
    ])

    assert not [item for item in targets if item.testable]


def test_visually_similar_but_unlinked_observation_is_rejected():
    similar = LocalObservation(
        id="different-surface",
        photo_index=5,
        status=ClaimStatus.OBSERVED,
        visibility=VisibilityStatus.VISIBLE,
        region=NormalizedImageRegion(x0=0.2, y0=0.2, x1=0.6, y1=0.6),
        proposed_category="surface",
        statement="Looks similar but is not structurally referenced by the hypothesis.",
    )

    _, _, _, targets = _targeting_chain([similar])

    assert targets == []


def test_end_to_end_derived_target_can_build_test_and_resolve_inquiry():
    observation = _target_observation("surface-s", 3)
    hypotheses, predictions, question, targets = _targeting_chain([observation])
    testable = [item for item in targets if item.testable]
    assert len(testable) == 1
    target = testable[0]

    test = DiscriminatingTest(
        id="derived-target-test",
        photo_index=target.photo_index,
        region=target.region,
        prediction_ids=question.prediction_ids,
        evidence_sought=target.discriminant_property,
    )
    inquiry = VisualInquiry(
        id="end-to-end-011",
        question=question.human_readable_question,
        hypothesis_ids=[item.id for item in hypotheses],
        predictions=predictions,
        tests=[test],
    )
    result = InquiryTestResult(
        test_id=test.id,
        inspected=True,
        region_in_frame=True,
        visibility=VisibilityStatus.VISIBLE,
        sufficient_visibility=True,
        statement="Compatible continuation is visible in the automatically targeted ROI.",
        compatible_prediction_ids=["derived-h-continues"],
        discriminating=True,
    )

    resolved = apply_inquiry_test(inquiry, result)

    assert resolved.state is InquiryState.RESOLVED
    assert resolved.resolved_hypothesis_id == "h-continues"
    assert test.photo_index == observation.photo_index
    assert test.region == observation.region


def test_no_testable_candidate_can_end_as_irreducible_unknown_without_invented_roi():
    hypotheses, predictions, question, targets = _targeting_chain([
        _target_observation("surface-s", 2, visibility=VisibilityStatus.OCCLUDED),
    ])
    assert not [item for item in targets if item.testable]

    context_target = targets[0]
    inquiry = VisualInquiry(
        id="no-target-011",
        question=question.human_readable_question,
        hypothesis_ids=[item.id for item in hypotheses],
        predictions=predictions,
        tests=[
            DiscriminatingTest(
                id="context-only-test",
                photo_index=context_target.photo_index,
                region=context_target.region,
                prediction_ids=question.prediction_ids,
                evidence_sought=question.discriminants[0].property_name,
            )
        ],
    )
    inaccessible = InquiryTestResult(
        test_id="context-only-test",
        inspected=True,
        region_in_frame=True,
        visibility=VisibilityStatus.OCCLUDED,
        sufficient_visibility=False,
        statement="The only structurally linked ROI is occluded.",
        compatible_prediction_ids=question.prediction_ids,
        discriminating=False,
    )

    unresolved = apply_inquiry_test(
        inquiry,
        inaccessible,
        no_more_candidate_evidence=True,
        information_missing="No testable structurally linked ROI is available.",
    )

    assert unresolved.state is InquiryState.IRREDUCIBLE_UNKNOWN
    assert unresolved.viable_hypothesis_ids == ["h-continues", "h-terminates"]



def test_discriminating_candidate_is_preferred_over_merely_visible_candidate():
    observations = [
        _target_observation("surface-s", 2),
        _target_observation(
            "surface-s", 4,
            region=NormalizedImageRegion(x0=0.5, y0=0.1, x1=0.8, y1=0.4),
        ),
    ]
    observations[0].observable_properties = {"shape"}
    observations[1].observable_properties = {"continuation"}
    _, _, question, targets = _targeting_chain(observations)
    assessments = assess_discrimination_targets(question, targets, observations)
    selection = select_discrimination_targets(assessments)
    assert [item.potential for item in assessments] == [
        DiscriminationPotential.TESTABLE,
        DiscriminationPotential.DISCRIMINATING,
    ]
    assert [item.photo_index for item in selection.best_candidates] == [4]
    assert selection.tied is False

def test_occluded_candidate_never_beats_visible_testable_discriminating_candidate():
    observations = [
        _target_observation("surface-s", 2, visibility=VisibilityStatus.OCCLUDED),
        _target_observation("surface-s", 4),
    ]
    for observation in observations:
        observation.observable_properties = {"continuation"}
    _, _, question, targets = _targeting_chain(observations)
    assessments = assess_discrimination_targets(question, targets, observations)
    selection = select_discrimination_targets(assessments)
    assert assessments[0].potential is DiscriminationPotential.NONE
    assert assessments[1].potential is DiscriminationPotential.DISCRIMINATING
    assert [item.photo_index for item in selection.best_candidates] == [4]


def test_equal_discrimination_potential_preserves_tied_best_candidates():
    observations = [
        _target_observation("surface-s", 2),
        _target_observation("surface-s", 4),
    ]
    for observation in observations:
        observation.observable_properties = {"continuation"}
    _, _, question, targets = _targeting_chain(observations)
    assessments = assess_discrimination_targets(question, targets, observations)
    selection = select_discrimination_targets(assessments)
    assert selection.tied is True
    assert [item.photo_index for item in selection.best_candidates] == [2, 4]


def test_no_discriminating_target_produces_no_artificial_selection():
    observations = [_target_observation("surface-s", 2)]
    observations[0].observable_properties = {"shape"}
    _, _, question, targets = _targeting_chain(observations)
    assessments = assess_discrimination_targets(question, targets, observations)
    selection = select_discrimination_targets(assessments)
    assert assessments[0].potential is DiscriminationPotential.TESTABLE
    assert selection.best_candidates == []
    assert selection.tied is False


def test_selection_is_semantically_independent_of_candidate_input_order():
    observations = [
        _target_observation("surface-s", 4),
        _target_observation("surface-s", 2),
    ]
    for observation in observations:
        observation.observable_properties = {"continuation"}
    _, _, question, targets = _targeting_chain(observations)
    forward = select_discrimination_targets(
        assess_discrimination_targets(question, targets, observations)
    )
    reverse = select_discrimination_targets(
        assess_discrimination_targets(question, list(reversed(targets)), observations)
    )
    assert forward == reverse
    assert [item.photo_index for item in forward.best_candidates] == [2, 4]


def test_end_to_end_012_selects_unique_target_then_resolves():
    observation = _target_observation("surface-s", 5)
    observation.observable_properties = {"continuation"}
    hypotheses, predictions, question, targets = _targeting_chain([observation])
    assessments = assess_discrimination_targets(question, targets, [observation])
    selection = select_discrimination_targets(assessments)
    assert len(selection.best_candidates) == 1
    target = selection.best_candidates[0]
    test = DiscriminatingTest(
        id="selected-012",
        photo_index=target.photo_index,
        region=target.region,
        prediction_ids=question.prediction_ids,
        evidence_sought=target.discriminant_property,
    )
    inquiry = VisualInquiry(
        id="end-to-end-012",
        question=question.human_readable_question,
        hypothesis_ids=[item.id for item in hypotheses],
        predictions=predictions,
        tests=[test],
    )
    result = InquiryTestResult(
        test_id=test.id,
        inspected=True,
        region_in_frame=True,
        visibility=VisibilityStatus.VISIBLE,
        sufficient_visibility=True,
        statement="Continuation is visible in the selected discriminating target.",
        compatible_prediction_ids=["derived-h-continues"],
        discriminating=True,
    )
    resolved = apply_inquiry_test(inquiry, result)
    assert resolved.state is InquiryState.RESOLVED
    assert resolved.resolved_hypothesis_id == "h-continues"



def test_013_good_subject_and_property_derives_applicable():
    observation = _target_observation("surface-s", 2)
    observation.observable_properties = {"continuation"}
    _, _, question, targets = _targeting_chain([observation])
    assert derive_discriminant_applicability(
        targets[0], [observation]
    ) is ApplicabilityState.APPLICABLE


def test_013_good_subject_wrong_property_is_not_applicable():
    observation = _target_observation("surface-s", 2)
    observation.observable_properties = {"shape"}
    _, _, _, targets = _targeting_chain([observation])
    assert derive_discriminant_applicability(
        targets[0], [observation]
    ) is ApplicabilityState.NOT_APPLICABLE


def test_013_wrong_subject_with_right_property_is_not_applicable():
    subject = _target_observation("surface-s", 2)
    subject.observable_properties = {"shape"}
    other = _target_observation("other-surface", 2, region=subject.region)
    other.observable_properties = {"continuation"}
    _, _, _, targets = _targeting_chain([subject, other])
    assert derive_discriminant_applicability(
        targets[0], [other]
    ) is ApplicabilityState.NOT_APPLICABLE


def test_013_relevant_but_occluded_cannot_be_discriminating_evidence():
    observation = _target_observation(
        "surface-s", 2, visibility=VisibilityStatus.OCCLUDED
    )
    observation.observable_properties = {"continuation"}
    _, _, question, targets = _targeting_chain([observation])
    assessments = assess_discrimination_targets(question, targets, [observation])
    assert assessments[0].discriminant_applicability is ApplicabilityState.APPLICABLE
    assert assessments[0].potential is DiscriminationPotential.NONE


def test_013_missing_structured_property_information_is_unknown_not_false():
    observation = _target_observation("surface-s", 2)
    assert observation.observable_properties is None
    _, _, _, targets = _targeting_chain([observation])
    assert derive_discriminant_applicability(
        targets[0], [observation]
    ) is ApplicabilityState.UNKNOWN


def test_013_end_to_end_derives_applicability_then_resolves_without_manual_map():
    observation = _target_observation("surface-s", 5)
    observation.observable_properties = {"continuation"}
    hypotheses, predictions, question, targets = _targeting_chain([observation])
    assessments = assess_discrimination_targets(question, targets, [observation])
    selection = select_discrimination_targets(assessments)
    assert assessments[0].discriminant_applicability is ApplicabilityState.APPLICABLE
    assert len(selection.best_candidates) == 1
    target = selection.best_candidates[0]
    test = DiscriminatingTest(
        id="derived-applicability-013",
        photo_index=target.photo_index,
        region=target.region,
        prediction_ids=question.prediction_ids,
        evidence_sought=target.discriminant_property,
    )
    inquiry = VisualInquiry(
        id="end-to-end-013",
        question=question.human_readable_question,
        hypothesis_ids=[item.id for item in hypotheses],
        predictions=predictions,
        tests=[test],
    )
    resolved = apply_inquiry_test(
        inquiry,
        InquiryTestResult(
            test_id=test.id,
            inspected=True,
            region_in_frame=True,
            visibility=VisibilityStatus.VISIBLE,
            sufficient_visibility=True,
            statement="Continuation is visible.",
            compatible_prediction_ids=["derived-h-continues"],
            discriminating=True,
        ),
    )
    assert resolved.state is InquiryState.RESOLVED


def test_013_visible_observations_without_applicable_property_yield_no_target():
    observations = [
        _target_observation("surface-s", 2),
        _target_observation("surface-s", 4),
    ]
    for observation in observations:
        observation.observable_properties = {"shape"}
    _, _, question, targets = _targeting_chain(observations)
    assessments = assess_discrimination_targets(question, targets, observations)
    selection = select_discrimination_targets(assessments)
    assert all(
        item.discriminant_applicability is ApplicabilityState.NOT_APPLICABLE
        for item in assessments
    )
    assert selection.best_candidates == []



def _uncertainty_014(resolved_state=None, property_name="continuity"):
    return StructuredUncertainty(
        id="uncertainty-s-continuity",
        subject_ref="surface-s",
        property_name=property_name,
        source_observation_ids=["surface-s"],
        resolved_state=resolved_state,
    )


def test_014_continuity_uncertainty_generates_exact_competing_alternatives():
    hypotheses = derive_competing_hypotheses(_uncertainty_014())
    assert [item.claim.relation for item in hypotheses] == ["CONTINUES", "TERMINATES"]
    assert hypotheses[0].competing_with == [hypotheses[1].id]
    assert hypotheses[1].competing_with == [hypotheses[0].id]


def test_014_hypotheses_preserve_uncertainty_and_observation_provenance():
    uncertainty = _uncertainty_014()
    hypotheses = derive_competing_hypotheses(uncertainty)
    assert {item.source_uncertainty_id for item in hypotheses} == {uncertainty.id}
    assert uncertainty.source_observation_ids == ["surface-s"]


def test_014_unknown_property_derives_no_hypotheses():
    assert derive_competing_hypotheses(
        _uncertainty_014(property_name="unsupported-property")
    ) == []


def test_014_resolved_uncertainty_does_not_recreate_competing_hypotheses():
    assert derive_competing_hypotheses(
        _uncertainty_014(resolved_state="CONTINUES")
    ) == []


def test_014_repeated_derivation_is_deterministic_and_deduplicable():
    uncertainty = _uncertainty_014()
    first = derive_competing_hypotheses(uncertainty)
    second = derive_competing_hypotheses(uncertainty)
    assert first == second
    assert len({item.id for item in first + second}) == 2


def test_014_end_to_end_from_uncertainty_to_resolved():
    observation = _target_observation("surface-s", 5)
    observation.observable_properties = {"continuation"}
    uncertainty = _uncertainty_014()
    hypotheses = derive_competing_hypotheses(uncertainty)
    predictions = [derive_observable_prediction(item) for item in hypotheses]
    assert all(item is not None for item in predictions)
    question = derive_discriminating_question(predictions)
    targets = derive_candidate_evidence_targets(
        question, hypotheses, [observation]
    )
    assessments = assess_discrimination_targets(question, targets, [observation])
    selection = select_discrimination_targets(assessments)
    assert len(selection.best_candidates) == 1
    target = selection.best_candidates[0]
    test = DiscriminatingTest(
        id="generated-from-uncertainty-014",
        photo_index=target.photo_index,
        region=target.region,
        prediction_ids=question.prediction_ids,
        evidence_sought=target.discriminant_property,
    )
    inquiry = VisualInquiry(
        id="end-to-end-014",
        question=question.human_readable_question,
        hypothesis_ids=[item.id for item in hypotheses],
        predictions=predictions,
        tests=[test],
    )
    result = InquiryTestResult(
        test_id=test.id,
        inspected=True,
        region_in_frame=True,
        visibility=VisibilityStatus.VISIBLE,
        sufficient_visibility=True,
        statement="Continuation is visible.",
        compatible_prediction_ids=[f"derived-{hypotheses[0].id}"],
        discriminating=True,
    )
    resolved = apply_inquiry_test(inquiry, result)
    assert resolved.state is InquiryState.RESOLVED
    assert resolved.resolved_hypothesis_id == hypotheses[0].id
    assert hypotheses[0].source_uncertainty_id == uncertainty.id
    assert uncertainty.source_observation_ids == [observation.id]
    assert test.photo_index == observation.photo_index
    assert test.region == observation.region


def test_014_no_discriminating_evidence_ends_irreducible_unknown():
    observation = _target_observation(
        "surface-s", 3, visibility=VisibilityStatus.OCCLUDED
    )
    observation.observable_properties = {"continuation"}
    uncertainty = _uncertainty_014()
    hypotheses = derive_competing_hypotheses(uncertainty)
    predictions = [derive_observable_prediction(item) for item in hypotheses]
    question = derive_discriminating_question(predictions)
    targets = derive_candidate_evidence_targets(
        question, hypotheses, [observation]
    )
    assessments = assess_discrimination_targets(question, targets, [observation])
    assert select_discrimination_targets(assessments).best_candidates == []

    fallback_test = DiscriminatingTest(
        id="unavailable-evidence-014",
        photo_index=targets[0].photo_index,
        region=targets[0].region,
        prediction_ids=question.prediction_ids,
        evidence_sought=targets[0].discriminant_property,
    )
    inquiry = VisualInquiry(
        id="irreducible-014",
        question=question.human_readable_question,
        hypothesis_ids=[item.id for item in hypotheses],
        predictions=predictions,
        tests=[fallback_test],
    )
    result = InquiryTestResult(
        test_id=fallback_test.id,
        inspected=True,
        region_in_frame=True,
        visibility=VisibilityStatus.OCCLUDED,
        sufficient_visibility=False,
        statement="The relevant region is occluded.",
        compatible_prediction_ids=question.prediction_ids,
        discriminating=False,
    )
    unresolved = apply_inquiry_test(
        inquiry,
        result,
        no_more_candidate_evidence=True,
        information_missing="No non-occluded observation exposes continuation.",
    )
    assert unresolved.state is InquiryState.IRREDUCIBLE_UNKNOWN
    assert set(unresolved.viable_hypothesis_ids) == {item.id for item in hypotheses}



def test_015_relevant_but_unresolved_continuity_creates_uncertainty():
    observation = _target_observation("surface-s", 2)
    observation.observable_properties = {"continuation"}
    detected = detect_continuity_uncertainties([observation])
    assert len(detected) == 1
    assert detected[0].subject_ref == "surface-s"
    assert detected[0].property_name == "continuity"


def test_015_known_continues_creates_no_uncertainty():
    observation = _target_observation("surface-s", 2)
    observation.observable_properties = {"continuation"}
    observation.observed_property_states = {"continuation": "CONTINUES"}
    assert detect_continuity_uncertainties([observation]) == []


def test_015_known_terminates_creates_no_uncertainty():
    observation = _target_observation("surface-s", 2)
    observation.observable_properties = {"continuation"}
    observation.observed_property_states = {"continuation": "TERMINATES"}
    assert detect_continuity_uncertainties([observation]) == []


def test_015_unmentioned_property_does_not_create_uncertainty():
    observation = _target_observation("surface-s", 2)
    observation.observable_properties = {"shape"}
    assert detect_continuity_uncertainties([observation]) == []


def test_015_occlusion_preserves_unknown_and_never_invents_terminates():
    observation = _target_observation(
        "surface-s", 2, visibility=VisibilityStatus.OCCLUDED
    )
    observation.observable_properties = {"continuation"}
    detected = detect_continuity_uncertainties([observation])
    assert len(detected) == 1
    assert detected[0].resolved_state is None
    assert derive_competing_hypotheses(detected[0])[1].claim.relation == "TERMINATES"
    assert all(item.certainty is CertaintyLevel.UNPROVEN for item in derive_competing_hypotheses(detected[0]))


def test_015_detection_is_stably_deduplicated():
    observation_a = _target_observation("surface-s", 2)
    observation_b = _target_observation("surface-s", 4)
    observation_a.observable_properties = {"continuation"}
    observation_b.observable_properties = {"continuation"}
    first = detect_continuity_uncertainties([observation_a, observation_b])
    second = detect_continuity_uncertainties([observation_b, observation_a])
    assert first == second
    assert len(first) == 1


def test_015_detected_uncertainty_preserves_source_observation_provenance():
    observation = _target_observation("surface-s", 3)
    observation.observable_properties = {"continuation"}
    uncertainty = detect_continuity_uncertainties([observation])[0]
    assert uncertainty.source_observation_ids == [observation.id]


def test_015_end_to_end_from_observations_to_resolved():
    observation = _target_observation("surface-s", 5)
    observation.observable_properties = {"continuation"}
    uncertainties = detect_continuity_uncertainties([observation])
    assert len(uncertainties) == 1
    uncertainty = uncertainties[0]
    hypotheses = derive_competing_hypotheses(uncertainty)
    predictions = [derive_observable_prediction(item) for item in hypotheses]
    question = derive_discriminating_question(predictions)
    targets = derive_candidate_evidence_targets(question, hypotheses, [observation])
    assessments = assess_discrimination_targets(question, targets, [observation])
    selection = select_discrimination_targets(assessments)
    assert len(selection.best_candidates) == 1
    target = selection.best_candidates[0]
    test = DiscriminatingTest(
        id="detected-uncertainty-015",
        photo_index=target.photo_index,
        region=target.region,
        prediction_ids=question.prediction_ids,
        evidence_sought=target.discriminant_property,
    )
    inquiry = VisualInquiry(
        id="end-to-end-015",
        question=question.human_readable_question,
        hypothesis_ids=[item.id for item in hypotheses],
        predictions=predictions,
        tests=[test],
    )
    resolved = apply_inquiry_test(
        inquiry,
        InquiryTestResult(
            test_id=test.id,
            inspected=True,
            region_in_frame=True,
            visibility=VisibilityStatus.VISIBLE,
            sufficient_visibility=True,
            statement="Continuation is visible.",
            compatible_prediction_ids=[f"derived-{hypotheses[0].id}"],
            discriminating=True,
        ),
    )
    assert resolved.state is InquiryState.RESOLVED
    assert hypotheses[0].source_uncertainty_id == uncertainty.id
    assert uncertainty.source_observation_ids == [observation.id]


def test_015_end_to_end_from_observations_to_irreducible_unknown():
    observation = _target_observation(
        "surface-s", 3, visibility=VisibilityStatus.OCCLUDED
    )
    observation.observable_properties = {"continuation"}
    uncertainty = detect_continuity_uncertainties([observation])[0]
    hypotheses = derive_competing_hypotheses(uncertainty)
    predictions = [derive_observable_prediction(item) for item in hypotheses]
    question = derive_discriminating_question(predictions)
    targets = derive_candidate_evidence_targets(question, hypotheses, [observation])
    assessments = assess_discrimination_targets(question, targets, [observation])
    assert select_discrimination_targets(assessments).best_candidates == []
    test = DiscriminatingTest(
        id="no-evidence-015",
        photo_index=targets[0].photo_index,
        region=targets[0].region,
        prediction_ids=question.prediction_ids,
        evidence_sought=targets[0].discriminant_property,
    )
    inquiry = VisualInquiry(
        id="unknown-015",
        question=question.human_readable_question,
        hypothesis_ids=[item.id for item in hypotheses],
        predictions=predictions,
        tests=[test],
    )
    unresolved = apply_inquiry_test(
        inquiry,
        InquiryTestResult(
            test_id=test.id,
            inspected=True,
            region_in_frame=True,
            visibility=VisibilityStatus.OCCLUDED,
            sufficient_visibility=False,
            statement="Relevant continuity region is occluded.",
            compatible_prediction_ids=question.prediction_ids,
            discriminating=False,
        ),
        no_more_candidate_evidence=True,
        information_missing="No testable continuity observation is available.",
    )
    assert unresolved.state is InquiryState.IRREDUCIBLE_UNKNOWN
    assert set(unresolved.viable_hypothesis_ids) == {item.id for item in hypotheses}



def _visual_exchange_016(visibility=VisibilityStatus.VISIBLE):
    observation = _target_observation("surface-s", 5, visibility=visibility)
    observation.observable_properties = {"continuation"}
    uncertainty = detect_continuity_uncertainties([observation])[0]
    hypotheses = derive_competing_hypotheses(uncertainty)
    predictions = [derive_observable_prediction(item) for item in hypotheses]
    question = derive_discriminating_question(predictions)
    targets = derive_candidate_evidence_targets(question, hypotheses, [observation])
    assessments = assess_discrimination_targets(question, targets, [observation])
    if visibility is VisibilityStatus.VISIBLE:
        target = select_discrimination_targets(assessments).best_candidates[0]
    else:
        target = targets[0]
    test = DiscriminatingTest(
        id="visual-exchange-test-016",
        photo_index=target.photo_index,
        region=target.region,
        prediction_ids=question.prediction_ids,
        evidence_sought=target.discriminant_property,
    )
    inquiry = VisualInquiry(
        id="visual-exchange-inquiry-016",
        question=question.human_readable_question,
        hypothesis_ids=[item.id for item in hypotheses],
        predictions=predictions,
        tests=[test],
    )
    request = build_visual_inquiry_request(inquiry, question, hypotheses, target)
    return observation, uncertainty, hypotheses, question, inquiry, request


def test_016_request_is_generated_from_real_experimental_inquiry_chain():
    _, _, hypotheses, question, inquiry, request = _visual_exchange_016()
    assert request.inquiry_id == inquiry.id
    assert request.question == question
    assert request.predictions == inquiry.predictions
    assert request.subject_ref == hypotheses[0].claim.subject_ref
    assert request.target.photo_index == 5
    assert request.property_name == "continuation"


def test_016_request_json_round_trip_is_lossless():
    *_, request = _visual_exchange_016()
    payload = request.model_dump_json()
    restored = VisualInquiryRequest.model_validate_json(payload)
    assert restored == request


def test_016_observed_response_imports_as_discriminating_result():
    *_, request = _visual_exchange_016()
    response = VisualEvidenceResponse(
        request_id=request.request_id,
        inquiry_id=request.inquiry_id,
        test_id=request.test_id,
        photo_index=request.target.photo_index,
        region=request.target.region,
        property_name=request.property_name,
        status=VisualEvidenceStatus.OBSERVED,
        observed_value="visible",
        certainty=CertaintyLevel.CERTAIN,
        source_observation_ids=request.target.source_observation_ids,
    )
    restored = VisualEvidenceResponse.model_validate_json(response.model_dump_json())
    result = import_visual_evidence_response(request, restored)
    assert result.discriminating is True
    assert len(result.compatible_prediction_ids) == 1


def test_016_occluded_response_never_becomes_absence():
    *_, request = _visual_exchange_016()
    response = VisualEvidenceResponse(
        request_id=request.request_id, inquiry_id=request.inquiry_id,
        test_id=request.test_id, photo_index=request.target.photo_index,
        region=request.target.region, property_name=request.property_name,
        status=VisualEvidenceStatus.OCCLUDED, certainty=CertaintyLevel.UNKNOWN,
        source_observation_ids=request.target.source_observation_ids,
    )
    result = import_visual_evidence_response(request, response)
    assert result.visibility is VisibilityStatus.OCCLUDED
    assert result.discriminating is False
    assert result.compatible_prediction_ids == request.question.prediction_ids


def test_016_ambiguous_and_insufficient_preserve_all_predictions():
    *_, request = _visual_exchange_016()
    for status in [
        VisualEvidenceStatus.AMBIGUOUS,
        VisualEvidenceStatus.INSUFFICIENT_EVIDENCE,
    ]:
        response = VisualEvidenceResponse(
            request_id=request.request_id, inquiry_id=request.inquiry_id,
            test_id=request.test_id, photo_index=request.target.photo_index,
            region=request.target.region, property_name=request.property_name,
            status=status, source_observation_ids=request.target.source_observation_ids,
        )
        result = import_visual_evidence_response(request, response)
        assert result.discriminating is False
        assert result.compatible_prediction_ids == request.question.prediction_ids


def test_016_invalid_or_incomplete_response_is_safely_rejected():
    *_, request = _visual_exchange_016()
    with pytest.raises(ValueError):
        VisualEvidenceResponse(
            request_id=request.request_id, inquiry_id=request.inquiry_id,
            test_id=request.test_id, photo_index=request.target.photo_index,
            region=request.target.region, property_name=request.property_name,
            status=VisualEvidenceStatus.OBSERVED,
            source_observation_ids=request.target.source_observation_ids,
        )
    response = VisualEvidenceResponse(
        request_id="wrong-request", inquiry_id=request.inquiry_id,
        test_id=request.test_id, photo_index=request.target.photo_index,
        region=request.target.region, property_name=request.property_name,
        status=VisualEvidenceStatus.OBSERVED, observed_value="visible",
        source_observation_ids=request.target.source_observation_ids,
    )
    with pytest.raises(ValueError, match="provenance"):
        import_visual_evidence_response(request, response)


def test_016_full_json_exchange_round_trip_resolves():
    _, uncertainty, hypotheses, _, inquiry, request = _visual_exchange_016()
    request_json = request.model_dump_json()
    external_request = VisualInquiryRequest.model_validate_json(request_json)
    external_response = VisualEvidenceResponse(
        request_id=external_request.request_id,
        inquiry_id=external_request.inquiry_id,
        test_id=external_request.test_id,
        photo_index=external_request.target.photo_index,
        region=external_request.target.region,
        property_name=external_request.property_name,
        status=VisualEvidenceStatus.OBSERVED,
        observed_value="visible",
        certainty=CertaintyLevel.CERTAIN,
        source_observation_ids=external_request.target.source_observation_ids,
        comment="Synthetic external inspection.",
    )
    imported_response = VisualEvidenceResponse.model_validate_json(
        external_response.model_dump_json()
    )
    result = import_visual_evidence_response(request, imported_response)
    resolved = apply_inquiry_test(inquiry, result)
    assert resolved.state is InquiryState.RESOLVED
    assert hypotheses[0].source_uncertainty_id == uncertainty.id


def test_016_inconclusive_json_exchange_preserves_hypotheses():
    *_, inquiry, request = _visual_exchange_016()
    response = VisualEvidenceResponse(
        request_id=request.request_id, inquiry_id=request.inquiry_id,
        test_id=request.test_id, photo_index=request.target.photo_index,
        region=request.target.region, property_name=request.property_name,
        status=VisualEvidenceStatus.INSUFFICIENT_EVIDENCE,
        source_observation_ids=request.target.source_observation_ids,
    )
    result = import_visual_evidence_response(
        VisualInquiryRequest.model_validate_json(request.model_dump_json()),
        VisualEvidenceResponse.model_validate_json(response.model_dump_json()),
    )
    updated = apply_inquiry_test(inquiry, result)
    assert updated.state is InquiryState.OPEN
    assert set(updated.viable_hypothesis_ids) == set(inquiry.hypothesis_ids)



def _bootstrap_017b_request():
    return build_visual_bootstrap_request(
        "bootstrap-017b",
        [f"photo-{index}.jpg" for index in range(1, 6)],
    )


def _bootstrap_017b_observation(
    *,
    observation_id="fragment-s",
    photo_index=2,
    properties=None,
    states=None,
):
    observation = _target_observation(observation_id, photo_index)
    observation.observable_properties = properties
    observation.observed_property_states = states
    return observation


def test_017b_a_bootstrap_request_is_json_serializable():
    request = _bootstrap_017b_request()
    restored = VisualBootstrapRequest.model_validate_json(request.model_dump_json())
    assert restored == request
    assert len(restored.photos) == 5


def test_017b_b_multi_observation_response_is_json_serializable():
    response = VisualBootstrapResponse(
        bootstrap_id="bootstrap-017b",
        photo_count=5,
        observations=[
            _bootstrap_017b_observation(observation_id="fragment-a", photo_index=1),
            _bootstrap_017b_observation(observation_id="fragment-b", photo_index=4),
        ],
    )
    assert VisualBootstrapResponse.model_validate_json(response.model_dump_json()) == response


def test_017b_c_import_creates_existing_workspace_and_local_observations():
    request = _bootstrap_017b_request()
    response = VisualBootstrapResponse(
        bootstrap_id=request.bootstrap_id,
        photo_count=5,
        observations=[_bootstrap_017b_observation()],
    )
    workspace = import_visual_bootstrap_response(request, response)
    assert isinstance(workspace, MultiViewWorkspace)
    assert isinstance(workspace.pass_1.observations[0], LocalObservation)
    assert workspace.pass_2.observations == []


def test_017b_d_roi_is_preserved_exactly_as_image_region():
    request = _bootstrap_017b_request()
    observation = _bootstrap_017b_observation()
    workspace = import_visual_bootstrap_response(
        request,
        VisualBootstrapResponse(
            bootstrap_id=request.bootstrap_id, photo_count=5, observations=[observation]
        ),
    )
    assert workspace.pass_1.observations[0].region == observation.region


def test_017b_e_observable_properties_are_preserved():
    request = _bootstrap_017b_request()
    observation = _bootstrap_017b_observation(properties={"continuation", "shape"})
    workspace = import_visual_bootstrap_response(
        request,
        VisualBootstrapResponse(
            bootstrap_id=request.bootstrap_id, photo_count=5, observations=[observation]
        ),
    )
    assert workspace.pass_1.observations[0].observable_properties == {"continuation", "shape"}


def test_017b_f_observed_property_states_are_preserved():
    request = _bootstrap_017b_request()
    observation = _bootstrap_017b_observation(
        properties={"continuation"}, states={"continuation": "CONTINUES"}
    )
    workspace = import_visual_bootstrap_response(
        request,
        VisualBootstrapResponse(
            bootstrap_id=request.bootstrap_id, photo_count=5, observations=[observation]
        ),
    )
    assert workspace.pass_1.observations[0].observed_property_states == {
        "continuation": "CONTINUES"
    }


def test_017b_g_identity_candidates_are_not_promoted_to_certain_identity():
    request = _bootstrap_017b_request()
    observations = [
        _bootstrap_017b_observation(observation_id="fragment-a", photo_index=1),
        _bootstrap_017b_observation(observation_id="fragment-b", photo_index=3),
    ]
    candidate = IdentityCandidate(
        id="identity-candidate-ab",
        observation_ids=["fragment-a", "fragment-b"],
        status=IdentityStatus.LIKELY_SAME,
        corroborating_photo_indexes=[1, 3],
        certainty=CertaintyLevel.PLAUSIBLE,
    )
    workspace = import_visual_bootstrap_response(
        request,
        VisualBootstrapResponse(
            bootstrap_id=request.bootstrap_id,
            photo_count=5,
            observations=observations,
            identity_candidates=[candidate],
        ),
    )
    assert workspace.pass_1.identities[0].status is IdentityStatus.LIKELY_SAME
    assert workspace.pass_1.identities[0].status is not IdentityStatus.SAME_PHYSICAL_OBJECT


def test_017b_h_bootstrap_unknown_continuity_starts_inquiry_engine():
    request = _bootstrap_017b_request()
    observation = _bootstrap_017b_observation(properties={"continuation"})
    workspace = import_visual_bootstrap_response(
        request,
        VisualBootstrapResponse(
            bootstrap_id=request.bootstrap_id, photo_count=5, observations=[observation]
        ),
    )
    uncertainty = detect_continuity_uncertainties(workspace.pass_1.observations)[0]
    hypotheses = derive_competing_hypotheses(uncertainty)
    predictions = [derive_observable_prediction(item) for item in hypotheses]
    question = derive_discriminating_question(predictions)
    assert uncertainty.subject_ref == observation.id
    assert {item.claim.relation for item in hypotheses} == {"CONTINUES", "TERMINATES"}
    assert question is not None
    assert question.discriminants[0].property_name == "continuation"


def test_017b_i_known_continues_does_not_create_uncertainty():
    request = _bootstrap_017b_request()
    observation = _bootstrap_017b_observation(
        properties={"continuation"}, states={"continuation": "CONTINUES"}
    )
    workspace = import_visual_bootstrap_response(
        request,
        VisualBootstrapResponse(
            bootstrap_id=request.bootstrap_id, photo_count=5, observations=[observation]
        ),
    )
    assert detect_continuity_uncertainties(workspace.pass_1.observations) == []


def test_017b_j_unmentioned_continuation_does_not_create_uncertainty():
    request = _bootstrap_017b_request()
    observation = _bootstrap_017b_observation(properties={"shape"})
    workspace = import_visual_bootstrap_response(
        request,
        VisualBootstrapResponse(
            bootstrap_id=request.bootstrap_id, photo_count=5, observations=[observation]
        ),
    )
    assert detect_continuity_uncertainties(workspace.pass_1.observations) == []


def test_017b_k_invalid_bootstrap_response_is_rejected_safely():
    request = _bootstrap_017b_request()
    with pytest.raises(ValueError):
        VisualBootstrapResponse(
            bootstrap_id=request.bootstrap_id,
            photo_count=5,
            observations=[
                _bootstrap_017b_observation(
                    observation_id="fragment-a", photo_index=1
                ),
                _bootstrap_017b_observation(
                    observation_id="fragment-a", photo_index=2
                ),
            ],
        )
    valid = VisualBootstrapResponse(
        bootstrap_id="wrong-bootstrap",
        photo_count=5,
        observations=[_bootstrap_017b_observation()],
    )
    with pytest.raises(ValueError, match="ID"):
        import_visual_bootstrap_response(request, valid)


# Experiment 020 — machine-strict, self-describing bootstrap contract.

def test_020_a_embedded_schema_is_exact_importer_model_schema():
    request = _bootstrap_017b_request()
    assert request.response_schema == visual_bootstrap_response_schema()
    assert request.response_schema == VisualBootstrapResponse.model_json_schema()


def test_020_b_schema_exposes_required_fields_enums_roi_and_extra_policy():
    schema = _bootstrap_017b_request().response_schema
    assert set(schema["required"]) >= {"bootstrap_id", "photo_count"}
    assert schema["additionalProperties"] is False
    defs = schema["$defs"]
    assert defs["LocalObservation"]["additionalProperties"] is False
    assert defs["IdentityCandidate"]["additionalProperties"] is False
    assert set(defs["NormalizedImageRegion"]["properties"]) == {"x0", "y0", "x1", "y1"}
    assert set(defs["NormalizedImageRegion"]["required"]) == {"x0", "y0", "x1", "y1"}
    assert set(defs["VisibilityStatus"]["enum"]) == {"visible", "absent", "non_visible", "occluded"}
    assert set(defs["ClaimStatus"]["enum"]) == {"observed", "inferred", "unknown"}
    assert set(defs["IdentityStatus"]["enum"]) == {
        "same_physical_object", "likely_same", "unresolved", "incompatible"
    }
    assert set(defs["CertaintyLevel"]["enum"]) == {
        "certain", "plausible", "unproven", "unknown"
    }


def test_020_c_synthetic_contract_response_roundtrips_into_workspace():
    request = _bootstrap_017b_request()
    payload = {
        "schema_version": "0.1",
        "bootstrap_id": request.bootstrap_id,
        "photo_count": 5,
        "observations": [{
            "id": "synthetic-fragment",
            "photo_index": 2,
            "status": "observed",
            "visibility": "visible",
            "region": {"x0": 0.1, "y0": 0.2, "x1": 0.3, "y1": 0.4},
            "qualitative_position": None,
            "proposed_category": None,
            "statement": "Synthetic fragment is visible.",
            "certainty": {
                "existence": "certain", "category": "unknown", "identity": "unknown",
                "spatial_relation": "unknown", "topology": "unknown", "metric": "unknown"
            },
            "observable_properties": ["shape"],
            "observed_property_states": None
        }],
        "identity_candidates": [],
        "observer_comment": None
    }
    serialized = json.dumps(payload)
    response = VisualBootstrapResponse.model_validate_json(serialized)
    workspace = import_visual_bootstrap_response(request, response)
    assert workspace.photo_count == 5
    assert workspace.pass_1.observations[0].id == "synthetic-fragment"


@pytest.mark.parametrize("mutation", [
    "missing_photo_count",
    "extra_source_photos",
    "wrong_identity_field",
    "array_roi",
    "missing_observation_contract_fields",
    "invalid_visibility",
])
def test_020_d_real_019_failure_shapes_are_rejected_by_new_contract(mutation):
    request = _bootstrap_017b_request()
    payload = {
        "schema_version": "0.1",
        "bootstrap_id": request.bootstrap_id,
        "photo_count": 5,
        "observations": [{
            "id": "fragment",
            "photo_index": 1,
            "status": "observed",
            "visibility": "visible",
            "region": {"x0": 0.1, "y0": 0.1, "x1": 0.2, "y1": 0.2},
            "statement": "Synthetic fragment.",
            "certainty": {
                "existence": "certain", "category": "unknown", "identity": "unknown",
                "spatial_relation": "unknown", "topology": "unknown", "metric": "unknown"
            }
        }],
        "identity_candidates": []
    }
    if mutation == "missing_photo_count":
        payload.pop("photo_count")
    elif mutation == "extra_source_photos":
        payload["source_photos"] = [{"photo_index": 1, "filename": "x.jpg"}]
    elif mutation == "wrong_identity_field":
        payload["cross_view_identity_candidates"] = payload.pop("identity_candidates")
    elif mutation == "array_roi":
        payload["observations"][0]["region"] = [0.1, 0.1, 0.2, 0.2]
    elif mutation == "missing_observation_contract_fields":
        for field in ("status", "statement", "certainty"):
            payload["observations"][0].pop(field)
    elif mutation == "invalid_visibility":
        payload["observations"][0]["visibility"] = "mostly_visible"
    with pytest.raises(ValueError):
        VisualBootstrapResponse.model_validate(payload)


def test_020_e_request_instruction_forbids_schema_redesign():
    instruction = _bootstrap_017b_request().instruction
    assert "Do not add fields" in instruction
    assert "Do not invent enum values" in instruction
    assert "validates exactly against response_schema" in instruction


# Experiment 023 — expose non-JSON-Schema validation/import invariants.

def test_023_a_request_embeds_exact_invariant_contract():
    request = _bootstrap_017b_request()
    assert request.response_invariants == visual_bootstrap_response_invariants()
    joined = "\n".join(request.response_invariants)
    assert "status='observed', visibility MUST be 'visible'" in joined
    assert "partially masked but still directly observed" in joined


def _valid_023_payload(request):
    return {
        "schema_version": "0.1", "bootstrap_id": request.bootstrap_id, "photo_count": 5,
        "observations": [{
            "id": "fragment-a", "photo_index": 1, "status": "observed",
            "visibility": "visible",
            "region": {"x0": .1, "y0": .1, "x1": .2, "y1": .2},
            "statement": "Synthetic visible fragment.",
            "certainty": {"existence": "certain", "category": "unknown", "identity": "unknown",
                          "spatial_relation": "unknown", "topology": "unknown", "metric": "unknown"}
        }],
        "identity_candidates": []
    }


def test_023_b_observed_visible_valid_and_imports():
    request = _bootstrap_017b_request()
    response = VisualBootstrapResponse.model_validate(_valid_023_payload(request))
    workspace = import_visual_bootstrap_response(request, response)
    assert workspace.pass_1.observations[0].visibility.value == "visible"


def test_023_c_real_022_observed_occluded_shape_rejected():
    request = _bootstrap_017b_request()
    payload = _valid_023_payload(request)
    payload["observations"][0]["visibility"] = "occluded"
    with pytest.raises(ValueError, match="observed local claims require visibility='visible'"):
        VisualBootstrapResponse.model_validate(payload)


@pytest.mark.parametrize("mutation", [
    "duplicate_observation_ids", "photo_above_count", "identity_unknown_observation",
    "identity_duplicate_ids", "same_object_unsupported", "roi_non_positive_x",
])
def test_023_d_all_validation_invariants_are_rejected(mutation):
    request = _bootstrap_017b_request()
    payload = _valid_023_payload(request)
    if mutation == "duplicate_observation_ids":
        payload["observations"].append(dict(payload["observations"][0]))
    elif mutation == "photo_above_count":
        payload["observations"][0]["photo_index"] = 6
    elif mutation == "identity_unknown_observation":
        payload["identity_candidates"] = [{"id":"i","observation_ids":["fragment-a","missing"],
          "status":"likely_same","certainty":"plausible"}]
    elif mutation == "identity_duplicate_ids":
        payload["identity_candidates"] = [{"id":"i","observation_ids":["fragment-a","fragment-a"],
          "status":"likely_same","certainty":"plausible"}]
    elif mutation == "same_object_unsupported":
        payload["observations"].append({**payload["observations"][0], "id":"fragment-b", "photo_index":2})
        payload["identity_candidates"] = [{"id":"i","observation_ids":["fragment-a","fragment-b"],
          "status":"same_physical_object","certainty":"unknown"}]
    elif mutation == "roi_non_positive_x":
        payload["observations"][0]["region"]["x1"] = payload["observations"][0]["region"]["x0"]
    with pytest.raises(ValueError):
        VisualBootstrapResponse.model_validate(payload)


@pytest.mark.parametrize("mutation", ["bootstrap_id", "photo_count", "unexpected_photo_index"])
def test_023_e_all_import_invariants_are_rejected(mutation):
    request = _bootstrap_017b_request()
    payload = _valid_023_payload(request)
    if mutation == "bootstrap_id":
        payload["bootstrap_id"] = "other"
    elif mutation == "photo_count":
        payload["photo_count"] = 4
    elif mutation == "unexpected_photo_index":
        # structurally valid against response photo_count, but not a request photo index
        payload["photo_count"] = 6
        payload["observations"][0]["photo_index"] = 6
        # isolate unexpected-index import check by making request length match count
        request.photos.append(type(request.photos[0])(photo_index=7, filename="synthetic-6.jpg"))
    response = VisualBootstrapResponse.model_validate(payload)
    with pytest.raises(ValueError):
        import_visual_bootstrap_response(request, response)


def test_023_f_invariant_inventory_mentions_every_runtime_rule():
    joined = "\n".join(visual_bootstrap_response_invariants())
    expected = [
        "status='observed'", "observation_ids MUST contain unique",
        "same_physical_object", "x1 MUST be greater than x0",
        "Observation IDs MUST be unique", "photo_index MUST be <= photo_count",
        "MUST reference an existing", "bootstrap_id MUST equal",
        "photo_count MUST equal", "MUST be one of the photo_index",
    ]
    for phrase in expected:
        assert phrase in joined


# Experiment 026 — canonical inquiry-property vocabulary.

def _obs026(props=None, states=None):
    return LocalObservation(id="synthetic-fragment", photo_index=1, status="observed",
        visibility="visible", region={"x0":.1,"y0":.1,"x1":.3,"y1":.3},
        statement="Synthetic fragment.", observable_properties=props,
        observed_property_states=states)

def test_026_a_non_relevant_continuation_absent():
    assert detect_continuity_uncertainties([_obs026({"shape"})]) == []

def test_026_b_relevant_unknown_runs_015_014_010_009():
    uncertainties=detect_continuity_uncertainties([_obs026({"continuation"})])
    assert len(uncertainties)==1
    hypotheses=derive_competing_hypotheses(uncertainties[0])
    predictions=[derive_observable_prediction(h) for h in hypotheses]
    assert all(predictions)
    question=derive_discriminating_question(predictions)
    assert question is not None
    assert [d.property_name for d in question.discriminants] == ["continuation"]

@pytest.mark.parametrize("state", ["CONTINUES","TERMINATES"])
def test_026_c_d_canonical_established_states_create_no_uncertainty(state):
    assert detect_continuity_uncertainties([_obs026({"continuation"},{"continuation":state})]) == []

def test_026_e_noncanonical_value_fails_closed_as_unresolved():
    uncertainties=detect_continuity_uncertainties([_obs026({"continuation"},{"continuation":"MAYBE"})])
    assert len(uncertainties)==1

def test_026_registry_is_single_supported_family_and_request_is_synchronized():
    assert set(INQUIRY_PROPERTY_REGISTRY) == {"continuation"}
    spec=INQUIRY_PROPERTY_REGISTRY["continuation"]
    assert spec.recognized_states == ("CONTINUES","TERMINATES")
    request=build_visual_bootstrap_request("synthetic-026",["one.jpg"])
    assert request.inquiry_property_registry == inquiry_property_registry_payload()
    assert request.inquiry_property_registry == [spec.model_dump(mode="json")]
    rule="\n".join(request.information_to_record)
    assert "If relevant but no state is established" in rule
    assert "If not relevant, omit it" in rule
    assert "Absence never means false" in rule
    assert "merely because the engine supports it" in rule


# Experiment 029 — deterministic executable inquiry construction.

def _chain029():
    observation=_obs026({"continuation"})
    uncertainties=detect_continuity_uncertainties([observation])
    assert len(uncertainties)==1
    uncertainty=uncertainties[0]
    hypotheses=derive_competing_hypotheses(uncertainty)
    predictions=[derive_observable_prediction(h) for h in hypotheses]
    assert all(predictions)
    question=derive_discriminating_question(predictions)
    assert question is not None
    targets=derive_candidate_evidence_targets(question,hypotheses,[observation])
    assessments=assess_discrimination_targets(question,targets,[observation])
    selection=select_discrimination_targets(assessments)
    return observation,uncertainty,hypotheses,predictions,question,targets,assessments,selection

def test_029_a_vertical_015_to_visual_request_is_deterministic():
    observation,uncertainty,hypotheses,predictions,question,targets,assessments,selection=_chain029()
    inquiry1=build_executable_visual_inquiry(
        uncertainty,hypotheses,predictions,question,assessments,selection)
    inquiry2=build_executable_visual_inquiry(
        uncertainty,hypotheses,predictions,question,assessments,selection)
    assert inquiry1 is not None and inquiry1 == inquiry2
    assert len(inquiry1.tests)==1
    test=inquiry1.tests[0]
    target=selection.best_candidates[0]
    assert test.photo_index == target.photo_index
    assert test.region == target.region
    assert test.source_observation_ids == target.source_observation_ids == [observation.id]
    assert test.evidence_sought == target.discriminant_property == "continuation"
    assert test.prediction_ids == question.prediction_ids
    request=build_visual_inquiry_request(inquiry1,question,hypotheses,target)
    assert request.target == target
    assert request.test_id == test.id
    assert request.predictions == predictions
    assert request.model_dump(mode="json") == build_visual_inquiry_request(
        inquiry2,question,hypotheses,target).model_dump(mode="json")

def test_029_b_consumes_prediction_outcomes_without_recoding_continuation_semantics():
    _,uncertainty,hypotheses,predictions,question,_,assessments,selection=_chain029()
    assert question.discriminants[0].expected_outcomes == {
        predictions[0].hypothesis_id: "visible",
        predictions[1].hypothesis_id: "absent",
    }
    altered=predictions[0].model_copy(deep=True)
    altered.observable_properties[0].value="different"
    assert build_executable_visual_inquiry(
        uncertainty,hypotheses,[altered,predictions[1]],question,assessments,selection
    ) is None

def test_029_c_fail_closed_without_unique_discriminating_target():
    _,uncertainty,hypotheses,predictions,question,_,assessments,selection=_chain029()
    empty=EvidenceTargetSelection(reason="none")
    assert build_executable_visual_inquiry(
        uncertainty,hypotheses,predictions,question,assessments,empty) is None
    tied=selection.model_copy(deep=True)
    tied.tied=True
    assert build_executable_visual_inquiry(
        uncertainty,hypotheses,predictions,question,assessments,tied) is None
    nondiscriminating=[item.model_copy(update={"potential":DiscriminationPotential.TESTABLE}) for item in assessments]
    assert build_executable_visual_inquiry(
        uncertainty,hypotheses,predictions,question,nondiscriminating,selection) is None

def test_029_d_fail_closed_on_incoherent_hypotheses_or_discriminant_or_provenance():
    _,uncertainty,hypotheses,predictions,question,_,assessments,selection=_chain029()
    bad_h=hypotheses[0].model_copy(update={"source_uncertainty_id":"other"})
    assert build_executable_visual_inquiry(
        uncertainty,[bad_h,hypotheses[1]],predictions,question,assessments,selection) is None
    bad_q=question.model_copy(deep=True)
    bad_q.discriminants[0].property_name="other"
    assert build_executable_visual_inquiry(
        uncertainty,hypotheses,predictions,bad_q,assessments,selection) is None
    bad_sel=selection.model_copy(deep=True)
    bad_sel.best_candidates[0].source_observation_ids=[]
    assert build_executable_visual_inquiry(
        uncertainty,hypotheses,predictions,question,assessments,bad_sel) is None


# Experiment 030 — self-describing strict VisualEvidenceResponse contract.

def _request030():
    _,uncertainty,hypotheses,predictions,question,_,assessments,selection=_chain029()
    inquiry=build_executable_visual_inquiry(
        uncertainty,hypotheses,predictions,question,assessments,selection)
    assert inquiry is not None
    return inquiry,question,hypotheses,selection.best_candidates[0],build_visual_inquiry_request(
        inquiry,question,hypotheses,selection.best_candidates[0])

def _response030(request,status="observed",value="visible",**overrides):
    payload={
        "schema_version":"0.1","request_id":request.request_id,
        "inquiry_id":request.inquiry_id,"test_id":request.test_id,
        "photo_index":request.target.photo_index,
        "region":request.target.region.model_dump(mode="json"),
        "property_name":request.property_name,"status":status,
        "observed_value":value,"certainty":"certain",
        "source_observation_ids":list(request.target.source_observation_ids),
        "comment":"Synthetic external evidence."
    }
    payload.update(overrides)
    return payload

def test_030_a_b_request_embeds_schema_directly_from_response_model():
    *_,request=_request030()
    assert request.response_schema == visual_evidence_response_schema()
    assert request.response_schema == VisualEvidenceResponse.model_json_schema()
    assert request.response_schema["additionalProperties"] is False

def test_030_c_request_embeds_runtime_invariants():
    *_,request=_request030()
    assert request.response_invariants == visual_evidence_response_invariants()
    joined="\n".join(request.response_invariants)
    for phrase in ["observed","not_observed","occluded","non_visible","ambiguous",
                   "insufficient_evidence","observed_value","request_id","inquiry_id",
                   "test_id","photo_index","region","property_name","source_observation_ids"]:
        assert phrase in joined

def test_030_d_decisive_json_response_validates_and_imports():
    *_,request=_request030()
    response=VisualEvidenceResponse.model_validate_json(json.dumps(_response030(request)))
    result=import_visual_evidence_response(request,response)
    assert result.discriminating
    assert len(result.compatible_prediction_ids)==1

@pytest.mark.parametrize("status",["occluded","non_visible","ambiguous","insufficient_evidence"])
def test_030_e_h_inconclusive_statuses_remain_nondiscriminating(status):
    *_,request=_request030()
    payload=_response030(request,status=status,value=None)
    response=VisualEvidenceResponse.model_validate_json(json.dumps(payload))
    result=import_visual_evidence_response(request,response)
    assert not result.discriminating
    assert result.compatible_prediction_ids == request.question.prediction_ids
    assert not result.sufficient_visibility

def test_030_i_inconclusive_value_is_rejected():
    *_,request=_request030()
    with pytest.raises(ValueError,match="inconclusive visual evidence cannot carry"):
        VisualEvidenceResponse.model_validate(_response030(request,status="occluded",value="absent"))

@pytest.mark.parametrize("status",["observed","not_observed"])
def test_030_j_decisive_missing_value_is_rejected(status):
    *_,request=_request030()
    with pytest.raises(ValueError,match="decisive visual evidence requires"):
        VisualEvidenceResponse.model_validate(_response030(request,status=status,value=None))

def test_030_k_unexpected_decisive_value_fails_closed_at_import():
    *_,request=_request030()
    response=VisualEvidenceResponse.model_validate(_response030(request,value="NON_CANONICAL"))
    with pytest.raises(ValueError,match="matches no expected outcome"):
        import_visual_evidence_response(request,response)

@pytest.mark.parametrize(("field","value"),[
    ("request_id","wrong-request"),("inquiry_id","wrong-inquiry"),("test_id","wrong-test"),
    ("photo_index",2),("property_name","wrong-property"),
    ("source_observation_ids",["wrong-source"]),
])
def test_030_l_o_q_r_provenance_mismatch_rejected(field,value):
    *_,request=_request030()
    response=VisualEvidenceResponse.model_validate(_response030(request,**{field:value}))
    with pytest.raises(ValueError,match="provenance does not match"):
        import_visual_evidence_response(request,response)

def test_030_p_roi_mismatch_rejected():
    *_,request=_request030()
    region=request.target.region.model_dump(mode="json")
    region["x0"]=region["x0"]-0.01 if region["x0"]>=0.01 else region["x0"]+0.01
    response=VisualEvidenceResponse.model_validate(_response030(request,region=region))
    with pytest.raises(ValueError,match="provenance does not match"):
        import_visual_evidence_response(request,response)

def test_030_strict_response_rejects_extra_fields():
    *_,request=_request030()
    with pytest.raises(ValueError):
        VisualEvidenceResponse.model_validate(_response030(request,unexpected="nope"))


# Experiment 032 — persisted resolution memory without rewriting observations.

def _resolved032():
    observation,uncertainty,hypotheses,predictions,question,_,assessments,selection=_chain029()
    inquiry=build_executable_visual_inquiry(
        uncertainty,hypotheses,predictions,question,assessments,selection)
    assert inquiry is not None
    request=build_visual_inquiry_request(
        inquiry,question,hypotheses,selection.best_candidates[0])
    response=VisualEvidenceResponse.model_validate(_response030(request))
    result=import_visual_evidence_response(request,response)
    resolved=apply_inquiry_test(inquiry,result)
    assert resolved.state is InquiryState.RESOLVED
    return observation,uncertainty,hypotheses,resolved

def _detect032(observation,hypotheses,inquiries):
    return detect_continuity_uncertainties(
        [observation], inquiries=inquiries, hypotheses=hypotheses)

def test_032_a_without_inquiry_remains_open():
    observation=_obs026({"continuation"})
    assert len(_detect032(observation,[],[])) == 1

def test_032_b_open_inquiry_remains_open():
    observation,_,hypotheses,resolved=_resolved032()
    opened=resolved.model_copy(deep=True)
    opened.state=InquiryState.OPEN
    opened.resolved_hypothesis_id=None
    opened.resolution_test_id=None
    assert len(_detect032(observation,hypotheses,[opened])) == 1

def test_032_c_resolved_coherent_is_not_open():
    observation,_,hypotheses,resolved=_resolved032()
    assert _detect032(observation,hypotheses,[resolved]) == []

def test_032_d_historical_observation_is_unchanged():
    observation,_,hypotheses,resolved=_resolved032()
    before=observation.model_dump(mode="json")
    assert _detect032(observation,hypotheses,[resolved]) == []
    assert observation.model_dump(mode="json") == before
    assert observation.observed_property_states is None

def test_032_e_workspace_roundtrip_preserves_resolution_suppression():
    observation,_,hypotheses,resolved=_resolved032()
    workspace=MultiViewWorkspace(
        photo_count=1,
        pass_1=MultiViewPass(pass_number=1,observations=[observation],hypotheses=hypotheses),
        pass_2=MultiViewPass(pass_number=2),
        inquiries=[resolved],
    )
    loaded=MultiViewWorkspace.model_validate_json(workspace.model_dump_json())
    assert detect_continuity_uncertainties(
        loaded.pass_1.observations,
        inquiries=loaded.inquiries,
        hypotheses=loaded.pass_1.hypotheses + loaded.pass_2.hypotheses,
    ) == []
    assert loaded.pass_1.observations[0].observed_property_states is None

def test_032_f_missing_resolution_test_does_not_close():
    observation,_,hypotheses,resolved=_resolved032()
    broken=resolved.model_copy(deep=True)
    broken.resolution_test_id=None
    assert len(_detect032(observation,hypotheses,[broken])) == 1

def test_032_g_nondiscriminating_resolution_result_does_not_close():
    observation,_,hypotheses,resolved=_resolved032()
    broken=resolved.model_copy(deep=True)
    broken.test_results[0].discriminating=False
    assert len(_detect032(observation,hypotheses,[broken])) == 1

def test_032_h_wrong_subject_does_not_close():
    observation,_,hypotheses,resolved=_resolved032()
    bad=[item.model_copy(deep=True) for item in hypotheses]
    target=next(item for item in bad if item.id == resolved.resolved_hypothesis_id)
    target.claim.subject_ref="other-subject"
    assert len(_detect032(observation,bad,[resolved])) == 1

def test_032_i_other_uncertainty_does_not_close():
    observation,_,hypotheses,resolved=_resolved032()
    bad=[item.model_copy(deep=True) for item in hypotheses]
    target=next(item for item in bad if item.id == resolved.resolved_hypothesis_id)
    target.source_uncertainty_id="other-uncertainty"
    assert len(_detect032(observation,bad,[resolved])) == 1

def test_032_j_irreducible_unknown_is_not_observed_fact_and_not_resolved():
    observation,_,hypotheses,resolved=_resolved032()
    irreducible=resolved.model_copy(deep=True)
    irreducible.state=InquiryState.IRREDUCIBLE_UNKNOWN
    irreducible.resolved_hypothesis_id=None
    irreducible.resolution_test_id=None
    irreducible.viable_hypothesis_ids=list(irreducible.hypothesis_ids)
    irreducible.information_missing="No accessible discriminating evidence remains."
    irreducible.stop_reason="Available candidate evidence cannot distinguish the remaining hypotheses."
    assert len(_detect032(observation,hypotheses,[irreducible])) == 1
    assert observation.observed_property_states is None


# Experiment 035 — explicit epistemic contract for enquirable identity.

def _idobs035(identifier: str, photo: int, *, roi=True, statement="opaque", category="opaque"):
    return LocalObservation(
        id=identifier,
        photo_index=photo,
        status=ClaimStatus.OBSERVED,
        visibility=VisibilityStatus.VISIBLE,
        region=NormalizedImageRegion(x0=0.1,y0=0.1,x1=0.2,y1=0.2) if roi else None,
        statement=statement,
        proposed_category=category,
        certainty=AspectCertainty(existence=CertaintyLevel.CERTAIN),
    )

def _candidate035(*, status=IdentityStatus.LIKELY_SAME, certainty=CertaintyLevel.PLAUSIBLE,
                  ids=None, inquiry_state=IdentityInquiryState.NOT_ENQUIRABLE, alternatives=None):
    return IdentityCandidate(
        id="candidate-opaque",
        observation_ids=ids or ["obs-a","obs-b"],
        status=status,
        certainty=certainty,
        inquiry_state=inquiry_state,
        open_alternatives=alternatives or [],
    )

def _enquirable035(ids=None):
    return _candidate035(
        ids=ids,
        inquiry_state=IdentityInquiryState.OPEN_ALTERNATIVES,
        alternatives=[IdentityStatus.SAME_PHYSICAL_OBJECT, IdentityStatus.INCOMPATIBLE],
    )

def test_035_a_legacy_likely_same_is_fail_closed():
    obs=[_idobs035("obs-a",1),_idobs035("obs-b",2)]
    assert detect_identity_uncertainties([_candidate035()],obs)==[]

def test_035_b_legacy_unresolved_is_fail_closed():
    obs=[_idobs035("obs-a",1),_idobs035("obs-b",2)]
    candidate=_candidate035(status=IdentityStatus.UNRESOLVED,certainty=CertaintyLevel.UNKNOWN)
    assert detect_identity_uncertainties([candidate],obs)==[]

def test_035_c_acquired_identity_creates_no_uncertainty():
    obs=[_idobs035("obs-a",1),_idobs035("obs-b",2)]
    candidate=_candidate035(status=IdentityStatus.SAME_PHYSICAL_OBJECT,certainty=CertaintyLevel.CERTAIN)
    assert detect_identity_uncertainties([candidate],obs)==[]

def test_035_d_acquired_incompatibility_creates_no_uncertainty():
    obs=[_idobs035("obs-a",1),_idobs035("obs-b",2)]
    candidate=_candidate035(status=IdentityStatus.INCOMPATIBLE,certainty=CertaintyLevel.CERTAIN)
    assert detect_identity_uncertainties([candidate],obs)==[]

def test_035_e_explicit_competition_creates_one_uncertainty():
    obs=[_idobs035("obs-a",1),_idobs035("obs-b",2)]
    found=detect_identity_uncertainties([_enquirable035()],obs)
    assert len(found)==1
    assert found[0].source_kind=="identity_candidate"
    assert found[0].source_ref=="candidate-opaque"
    assert found[0].property_name=="identity"
    assert found[0].open_alternatives==["same_physical_object","incompatible"]

def test_035_f_enquirable_without_sufficient_alternatives_fails_validation():
    with pytest.raises(ValueError):
        _candidate035(inquiry_state=IdentityInquiryState.OPEN_ALTERNATIVES,
                      alternatives=[IdentityStatus.SAME_PHYSICAL_OBJECT])

def test_035_g_non_enquirable_with_open_alternatives_fails_validation():
    with pytest.raises(ValueError):
        _candidate035(alternatives=[IdentityStatus.SAME_PHYSICAL_OBJECT,IdentityStatus.INCOMPATIBLE])

@pytest.mark.parametrize("status", [IdentityStatus.SAME_PHYSICAL_OBJECT,IdentityStatus.INCOMPATIBLE])
def test_035_h_acquired_state_cannot_be_open(status):
    with pytest.raises(ValueError):
        _candidate035(status=status,certainty=CertaintyLevel.CERTAIN,
                      inquiry_state=IdentityInquiryState.OPEN_ALTERNATIVES,
                      alternatives=[IdentityStatus.SAME_PHYSICAL_OBJECT,IdentityStatus.INCOMPATIBLE])

def test_035_i_two_source_observations_are_preserved():
    obs=[_idobs035("obs-a",1),_idobs035("obs-b",2)]
    u=detect_identity_uncertainties([_enquirable035()],obs)[0]
    assert u.source_observation_ids==["obs-a","obs-b"]

def test_035_j_three_source_observations_are_preserved():
    ids=["obs-a","obs-b","obs-c"]
    obs=[_idobs035("obs-a",1),_idobs035("obs-b",2),_idobs035("obs-c",3)]
    u=detect_identity_uncertainties([_enquirable035(ids)],obs)[0]
    assert u.source_observation_ids==ids

def test_035_k_photo_indexes_remain_recoverable_from_provenance():
    obs=[_idobs035("obs-a",2),_idobs035("obs-b",5)]
    u=detect_identity_uncertainties([_enquirable035()],obs)[0]
    by_id={x.id:x for x in obs}
    assert [by_id[x].photo_index for x in u.source_observation_ids]==[2,5]

def test_035_l_existing_roi_is_preserved_without_copy_or_invention():
    obs=[_idobs035("obs-a",1),_idobs035("obs-b",2)]
    u=detect_identity_uncertainties([_enquirable035()],obs)[0]
    by_id={x.id:x for x in obs}
    assert by_id[u.source_observation_ids[0]].region==obs[0].region

def test_035_m_missing_roi_stays_missing():
    obs=[_idobs035("obs-a",1,roi=False),_idobs035("obs-b",2)]
    u=detect_identity_uncertainties([_enquirable035()],obs)[0]
    by_id={x.id:x for x in obs}
    assert by_id[u.source_observation_ids[0]].region is None

def test_035_n_o_p_detector_ignores_text_category_and_id_semantics():
    a=_idobs035("meaningless-X",1,statement="contradictory prose one",category="roof")
    b=_idobs035("meaningless-Y",2,statement="unrelated prose two",category="stair")
    candidate=IdentityCandidate(
        id="semantically-empty-id",
        observation_ids=[a.id,b.id],
        status=IdentityStatus.LIKELY_SAME,
        certainty=CertaintyLevel.PLAUSIBLE,
        inquiry_state=IdentityInquiryState.OPEN_ALTERNATIVES,
        open_alternatives=[IdentityStatus.SAME_PHYSICAL_OBJECT,IdentityStatus.INCOMPATIBLE],
    )
    u=detect_identity_uncertainties([candidate],[a,b])[0]
    assert u.source_ref=="semantically-empty-id"
    assert u.source_observation_ids==["meaningless-X","meaningless-Y"]

def test_035_q_workspace_roundtrip_preserves_identity_contract_and_source():
    obs=[_idobs035("obs-a",1),_idobs035("obs-b",2)]
    candidate=_enquirable035()
    workspace=MultiViewWorkspace(photo_count=2,
        pass_1=MultiViewPass(pass_number=1,observations=obs,identities=[candidate]),
        pass_2=MultiViewPass(pass_number=2))
    loaded=MultiViewWorkspace.model_validate_json(workspace.model_dump_json())
    assert loaded.pass_1.identities[0].inquiry_state is IdentityInquiryState.OPEN_ALTERNATIVES
    assert detect_identity_uncertainties(loaded.pass_1.identities,loaded.pass_1.observations)[0].source_ref==candidate.id

def test_035_r_legacy_workspace_without_new_fields_loads_fail_closed():
    obs=[_idobs035("obs-a",1),_idobs035("obs-b",2)]
    legacy={"schema_version":"0.1","photo_count":2,
      "pass_1":{"pass_number":1,"observations":[x.model_dump(mode="json") for x in obs],
        "identities":[{"id":"legacy","observation_ids":["obs-a","obs-b"],
          "status":"likely_same","certainty":"plausible"}]},
      "pass_2":{"pass_number":2}}
    loaded=MultiViewWorkspace.model_validate(legacy)
    candidate=loaded.pass_1.identities[0]
    assert candidate.inquiry_state is IdentityInquiryState.NOT_ENQUIRABLE
    assert candidate.open_alternatives==[]
    assert detect_identity_uncertainties([candidate],loaded.pass_1.observations)==[]

def test_035_s_continuation_uncertainty_shape_remains_backward_compatible():
    observation=_obs026({"continuation"})
    u=detect_continuity_uncertainties([observation])[0]
    assert u.subject_ref==observation.id
    assert u.source_kind=="observation"
    assert u.source_ref is None
    assert u.open_alternatives==[]
    assert len(derive_competing_hypotheses(u))==2


# Experiment 037 — composite visual evidence transport (levels 1-2).

def _ereg037(source_id, photo, obs=None, roi=True, visibility=VisibilityStatus.VISIBLE):
    return EvidenceRegion(
        source_id=source_id, observation_ref=obs, photo_index=photo,
        region=NormalizedImageRegion(x0=.1,y0=.2,x1=.3,y1=.4) if roi else None,
        visibility=visibility,
    )

def _ctarget037(regions):
    return CandidateEvidenceTarget(
        source_observation_ids=[r.observation_ref for r in regions if r.observation_ref],
        discriminant_property="opaque_token",
        visibility=VisibilityStatus.VISIBLE,
        testable=False,
        reason="Synthetic composite transport only; no sufficiency rule.",
        evidence_regions=regions,
    )

def test_037_a_legacy_target_still_loads():
    raw={"photo_index":1,"region":{"x0":.1,"y0":.1,"x1":.2,"y1":.2},
         "source_observation_ids":["o"],"discriminant_property":"opaque_token",
         "visibility":"visible","testable":True,"reason":"legacy"}
    t=CandidateEvidenceTarget.model_validate(raw)
    assert t.photo_index==1 and t.region is not None and t.evidence_regions==[]

def test_037_b_historical_visual_response_shape_still_loads():
    raw={"schema_version":"0.2","request_id":"r","inquiry_id":"i","test_id":"t",
         "photo_index":1,"region":{"x0":.1,"y0":.1,"x1":.2,"y1":.2},
         "property_name":"opaque_token","status":"observed","observed_value":"yes",
         "certainty":"certain","source_observation_ids":["o"]}
    assert VisualEvidenceResponse.model_validate(raw).photo_index==1

def test_037_c_d_composite_two_and_three_sources_remain_one_target():
    for n in (2,3):
        regions=[_ereg037(f"s{x}",x+1,f"o{x}") for x in range(n)]
        t=_ctarget037(regions)
        assert isinstance(t,CandidateEvidenceTarget) and len(t.evidence_regions)==n

def test_037_e_two_regions_same_photo_are_distinct():
    a=_ereg037("a",1,"oa"); b=_ereg037("b",1,"ob")
    b.region=NormalizedImageRegion(x0=.5,y0=.5,x1=.6,y1=.6)
    t=_ctarget037([a,b])
    assert t.evidence_regions[0].region != t.evidence_regions[1].region

def test_037_f_g_missing_roi_roundtrip_stays_missing():
    t=_ctarget037([_ereg037("a",1,"oa",roi=False),_ereg037("b",2,"ob")])
    loaded=CandidateEvidenceTarget.model_validate_json(t.model_dump_json())
    assert loaded.evidence_regions[0].region is None

def test_037_h_composite_discriminating_test_remains_one_test():
    regions=[_ereg037("a",1,"oa"),_ereg037("b",2,"ob")]
    test=DiscriminatingTest(id="t",prediction_ids=["p1","p2"],evidence_sought="opaque_token",
        source_observation_ids=["oa","ob"],evidence_regions=regions)
    assert test.photo_index is None and len(test.evidence_regions)==2

def test_037_p_source_order_is_not_world_identity():
    a=_ctarget037([_ereg037("a",1,"oa"),_ereg037("b",2,"ob")])
    b=_ctarget037([_ereg037("b",2,"ob"),_ereg037("a",1,"oa")])
    def world(t):
        return {(r.source_id,r.observation_ref,r.photo_index,r.region.model_dump_json() if r.region else None)
                for r in t.evidence_regions}
    assert world(a)==world(b)

def test_037_q_duplicate_source_rejected():
    with pytest.raises(ValueError):
        _ctarget037([_ereg037("dup",1,"oa"),_ereg037("dup",2,"ob")])

def test_037_r_occlusion_does_not_create_negative_outcome():
    t=_ctarget037([_ereg037("a",1,"oa",visibility=VisibilityStatus.OCCLUDED),
                   _ereg037("b",2,"ob")])
    assert t.evidence_regions[0].visibility is VisibilityStatus.OCCLUDED
    assert not hasattr(t.evidence_regions[0],"observed_value")

def test_037_s_composite_without_sufficiency_rule_cannot_claim_discrimination():
    t=_ctarget037([_ereg037("a",1,"oa"),_ereg037("b",2,"ob")])
    assert t.testable is False
    test=DiscriminatingTest(id="t",prediction_ids=["p1","p2"],evidence_sought="opaque_token",
        source_observation_ids=["oa","ob"],evidence_regions=t.evidence_regions)
    assert test.composite_sufficiency_rule is None

def test_037_t_workspace_roundtrip_preserves_composite_test_provenance():
    regions=[_ereg037("a",1,"oa"),_ereg037("b",2,"ob",roi=False)]
    predictions=[ObservablePrediction(id="p1",hypothesis_id="h1",statement="opaque"),
                 ObservablePrediction(id="p2",hypothesis_id="h2",statement="opaque")]
    test=DiscriminatingTest(id="t",prediction_ids=["p1","p2"],evidence_sought="opaque_token",
        source_observation_ids=["oa","ob"],evidence_regions=regions)
    inquiry=VisualInquiry(id="i",question="opaque",hypothesis_ids=["h1","h2"],
        predictions=predictions,tests=[test])
    hs=[OpenHypothesis(id="h1",subject_refs=["oa"],statement="opaque"),
        OpenHypothesis(id="h2",subject_refs=["oa"],statement="opaque")]
    workspace=MultiViewWorkspace(photo_count=2,
        pass_1=MultiViewPass(pass_number=1,hypotheses=hs),
        pass_2=MultiViewPass(pass_number=2),inquiries=[inquiry])
    loaded=MultiViewWorkspace.model_validate_json(workspace.model_dump_json())
    assert loaded.inquiries[0].tests[0].evidence_regions==regions

def test_037_u_legacy_discriminating_test_roundtrip_unchanged():
    raw={"id":"legacy","photo_index":1,"region":{"x0":.1,"y0":.1,"x1":.2,"y1":.2},
         "prediction_ids":["p1","p2"],"evidence_sought":"continuation",
         "source_observation_ids":["o"]}
    test=DiscriminatingTest.model_validate(raw)
    assert test.evidence_regions==[]
    assert DiscriminatingTest.model_validate_json(test.model_dump_json()).region==test.region
