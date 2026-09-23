from __future__ import annotations

import json
import base64
from pathlib import Path
from types import SimpleNamespace

import pytest

from brickhouse.vision.multiview import (
    AspectCertainty,
    import_visual_inquiry_batch_response,
    build_relation_pair_batch_request,
    build_relation_alternative_batch_request,
    record_relation_alternative_batch_response,
    ReasoningDependency,
    assess_investigation_impact,
    select_impactful_investigations,
    derive_reasoning_dependencies_from_hypotheses,
    derive_existing_structured_uncertainties,
    VisualInquiryBatchResult,
    VisualInquiryBatchResponse,
    VisualInquiryBatchRequest,
    RelationPairProducerRequest,
    RelationAlternativeProducerRequest,
    build_next_relation_loop_request,
    exhausted_relation_pair_evidence_sets,
    record_relation_investigation,
    import_relation_pair_producer_response,
    build_relation_pair_producer_request,
    RelationPairElement,
    RelationPairProducerSource,
    RelationPairProducerResponse,
    RelationPairProducerStatus,
    import_relation_alternative_producer_response,
    build_relation_alternative_producer_request,
    RelationAlternativeProposal,
    RelationAlternativeProducerSource,
    RelationAlternativeProducerResponse,
    RelationAlternativeProducerStatus,
    ArchitecturalRelationCandidate,
    CertaintyLevel,
    ClaimStatus,
    Contradiction,
    IdentityCandidate,
    IdentityDiscriminant,
    IdentityDiscriminantInvestigationRecord,
    record_identity_discriminant_investigation,
    RichEvidenceProvenance,
    RichIdentityCue,
    IdentityDiscriminantProducerStatus,
    IdentityDiscriminantCue,
    IdentityDiscriminantProducerResponse,
    IdentityDiscriminantProducerRequest,
    build_identity_discriminant_producer_request,
    import_identity_discriminant_producer_response,
    build_identity_enquiry_bootstrap_request,
    build_rich_multiview_bootstrap_request,
    RichVisualBootstrapResponse,
    import_rich_visual_bootstrap_response,
    derive_identity_world_representation_dependencies,
    build_multiview_world_constraint_graph,
    plan_missing_constraint_perceptual_query,
    MissingConstraintPlannerState,
    identity_discriminant_equivalence_signature,
    build_property_correspondence_producer_request,
    PropertyCorrespondenceProducerResponse,
    PropertyCorrespondenceProducerStatus,
    validate_property_correspondence_response,
    import_property_correspondence_response,
    build_property_outcome_mapping_request,
    mapping_request_equivalent_to_exhausted_identity_discriminant,
    validate_property_outcome_mapping_response,
    PropertyOutcomeMappingResponse,
    record_property_outcome_mapping_investigation,
    render_multiview_world_diagnostic_html,
    audit_workspace_fragmentation,
    build_global_multiview_connectivity_request,
    GlobalMultiviewConnectivityResponse,
    validate_global_multiview_connectivity_response,
    ingest_global_multiview_connectivity_response,
    build_world_hypothesis,
    render_world_hypothesis_html,
    PerceptualEvidenceLevel,
    PerceptualEvidenceRegion,
    PerceptualCue,
    PerceptualIdentityEvidence,
    PerceptualRelationEvidence,
    PerceptualAlternative,
    PerceptualAmbiguity,
    detect_relation_uncertainties,
    RelationInquiryState,
    RelationAlternative,
    exclude_already_investigated_targets,
    build_identity_discriminant_inquiry,
    IdentityStatus,
    IdentityInquiryState,
    detect_identity_uncertainties,
    LocalObservation,
    EvidenceRegion,
    CandidateEvidenceTarget,
    DiscriminatingTest,
    CompositeSufficiencyContract,
    DiscriminatingQuestion,
    DiscriminatingProperty,
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
    CompositeSourceResult,
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
    assert test.evidence_regions == t.evidence_regions and not test.model_dump().get("composite_sufficiency_rule")

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


# Experiment 038 — external composite exchange, synthetic opaque tokens only.

def _bundle038(n=2, same_photo=False, missing_roi=False, exhaustive=True):
    regions=[
        _ereg037(f"s{i}", 1 if same_photo else i+1, f"o{i}", roi=not (missing_roi and i==0))
        for i in range(n)
    ]
    target=_ctarget037(regions).model_copy(update={"requires_exhaustive_sources":exhaustive})
    preds=[
        ObservablePrediction(id="p-alpha",hypothesis_id="h-alpha",statement="opaque",
            observable_properties=[ObservableProperty(name="synthetic_relation",value="alpha")]),
        ObservablePrediction(id="p-beta",hypothesis_id="h-beta",statement="opaque",
            observable_properties=[ObservableProperty(name="synthetic_relation",value="beta")]),
    ]
    q=DiscriminatingQuestion(
        hypothesis_ids=["h-alpha","h-beta"],prediction_ids=["p-alpha","p-beta"],
        discriminants=[DiscriminatingProperty(property_name="synthetic_relation",
            expected_outcomes={"h-alpha":"alpha","h-beta":"beta"})],
        evidence_needed=["opaque"],human_readable_question="opaque?")
    test=DiscriminatingTest(id="tc",prediction_ids=["p-alpha","p-beta"],
        evidence_sought="synthetic_relation",source_observation_ids=[f"o{i}" for i in range(n)],
        evidence_regions=regions)
    inquiry=VisualInquiry(id="ic",question="opaque?",hypothesis_ids=["h-alpha","h-beta"],
        predictions=preds,tests=[test])
    hs=[
        OpenHypothesis(id="h-alpha",subject_refs=["subject"],statement="opaque",
            claim=HypothesisClaim(subject_ref="subject",relation="OPAQUE"),source_uncertainty_id="u"),
        OpenHypothesis(id="h-beta",subject_refs=["subject"],statement="opaque",
            claim=HypothesisClaim(subject_ref="subject",relation="OPAQUE2"),source_uncertainty_id="u"),
    ]
    req=build_visual_inquiry_request(inquiry,q,hs,target.model_copy(update={"discriminant_property":"synthetic_relation"}))
    return regions,target,preds,q,test,inquiry,hs,req

def _response038(req, regions, *, statuses=None, outcome="alpha", composite_status=VisualEvidenceStatus.OBSERVED, order=None):
    statuses=statuses or {}
    seq=list(regions if order is None else [regions[i] for i in order])
    results=[
        CompositeSourceResult(source_id=r.source_id,observation_ref=r.observation_ref,
            photo_index=r.photo_index,region=r.region,status=statuses.get(r.source_id,VisualEvidenceStatus.OBSERVED))
        for r in seq
    ]
    return VisualEvidenceResponse(schema_version="0.3",request_id=req.request_id,inquiry_id=req.inquiry_id,
        test_id=req.test_id,property_name=req.property_name,source_results=results,
        composite_status=composite_status,composite_outcome=outcome)

def test_038_a_b_historical_request_response_import_preserved():
    # Existing legacy helper exercises the exact 030 route.
    observation=_obs("legacy-o",1)
    observation.region=NormalizedImageRegion(x0=.1,y0=.1,x1=.2,y1=.2)
    observation.observable_properties={"continuation"}
    h1=OpenHypothesis(id="h1",subject_refs=["legacy-o"],statement="x",
        claim=HypothesisClaim(subject_ref="legacy-o",relation="CONTINUES"),source_uncertainty_id="u")
    h2=OpenHypothesis(id="h2",subject_refs=["legacy-o"],statement="x",
        claim=HypothesisClaim(subject_ref="legacy-o",relation="TERMINATES"),source_uncertainty_id="u")
    p1=ObservablePrediction(id="p1",hypothesis_id="h1",statement="x",observable_properties=[ObservableProperty(name="continuation",value="visible")])
    p2=ObservablePrediction(id="p2",hypothesis_id="h2",statement="x",observable_properties=[ObservableProperty(name="continuation",value="absent")])
    q=DiscriminatingQuestion(hypothesis_ids=["h1","h2"],prediction_ids=["p1","p2"],
        discriminants=[DiscriminatingProperty(property_name="continuation",expected_outcomes={"h1":"visible","h2":"absent"})],
        evidence_needed=["x"],human_readable_question="x")
    target=CandidateEvidenceTarget(photo_index=1,region=observation.region,source_observation_ids=["legacy-o"],
        discriminant_property="continuation",visibility=VisibilityStatus.VISIBLE,testable=True,reason="legacy")
    test=DiscriminatingTest(id="tl",photo_index=1,region=observation.region,prediction_ids=["p1","p2"],
        evidence_sought="continuation",source_observation_ids=["legacy-o"])
    inquiry=VisualInquiry(id="il",question="x",hypothesis_ids=["h1","h2"],predictions=[p1,p2],tests=[test])
    req=build_visual_inquiry_request(inquiry,q,[h1,h2],target)
    assert req.schema_version=="0.2"
    response=VisualEvidenceResponse(schema_version="0.2",request_id=req.request_id,inquiry_id=req.inquiry_id,
        test_id=req.test_id,photo_index=1,region=observation.region,property_name="continuation",
        status=VisualEvidenceStatus.OBSERVED,observed_value="visible",certainty=CertaintyLevel.CERTAIN,
        source_observation_ids=["legacy-o"])
    assert import_visual_evidence_response(req,response).discriminating is True

def test_038_c_d_e_f_g_request_composite_preserves_sources_and_missing_roi():
    for n in (2,3):
        regions,target,_,_,_,inquiry,_,req=_bundle038(n=n,missing_roi=True)
        assert req.schema_version=="0.3" and len(req.target.evidence_regions)==n and len(inquiry.tests)==1
        assert req.target.evidence_regions[0].region is None
        assert VisualInquiryRequest.model_validate_json(req.model_dump_json()).target.evidence_regions[0].region is None
    regions,_,_,_,_,_,_,req=_bundle038(n=2,same_photo=True)
    assert regions[0].photo_index==regions[1].photo_index and regions[0].source_id!=regions[1].source_id

def test_038_h_p_complete_response_and_permutation_import():
    regions,_,_,_,_,_,_,req=_bundle038()
    a=import_visual_evidence_response(req,_response038(req,regions))
    b=import_visual_evidence_response(req,_response038(req,regions,order=[1,0]))
    assert a.composite_outcome==b.composite_outcome=="alpha"
    assert set(a.composite_source_statuses)==set(b.composite_source_statuses)=={"s0","s1"}

def test_038_i_j_k_l_m_n_o_strict_source_provenance_rejections():
    regions,_,_,_,_,_,_,req=_bundle038()
    good=_response038(req,regions)
    for mutate in ("missing","extra","duplicate","obs","photo","roi","invent_roi"):
        data=good.model_dump()
        if mutate=="missing": data["source_results"]=data["source_results"][:1]
        elif mutate=="extra":
            extra=dict(data["source_results"][0]); extra["source_id"]="unknown"; data["source_results"].append(extra)
        elif mutate=="duplicate": data["source_results"][1]["source_id"]="s0"
        elif mutate=="obs": data["source_results"][0]["observation_ref"]="wrong"
        elif mutate=="photo": data["source_results"][0]["photo_index"]=99
        elif mutate=="roi": data["source_results"][0]["region"]={"x0":.6,"y0":.6,"x1":.7,"y1":.7}
        elif mutate=="invent_roi":
            regions2,_,_,_,_,_,_,req2=_bundle038(missing_roi=True)
            data=_response038(req2,regions2).model_dump()
            data["source_results"][0]["region"]={"x0":.6,"y0":.6,"x1":.7,"y1":.7}
            with pytest.raises(ValueError): import_visual_evidence_response(req2,VisualEvidenceResponse.model_validate(data))
            continue
        with pytest.raises(ValueError):
            response=VisualEvidenceResponse.model_validate(data)
            import_visual_evidence_response(req,response)

def test_038_q_r_s_local_states_never_manufacture_composite_outcome():
    regions,_,_,_,_,_,_,req=_bundle038()
    for status in (VisualEvidenceStatus.OCCLUDED,VisualEvidenceStatus.NON_VISIBLE):
        response=_response038(req,regions,statuses={"s0":status},outcome=None,
            composite_status=VisualEvidenceStatus.INSUFFICIENT_EVIDENCE)
        result=import_visual_evidence_response(req,response)
        assert result.composite_outcome is None and result.discriminating is False
        assert result.composite_source_statuses["s0"]==status.value
    response=_response038(req,regions,outcome=None,composite_status=VisualEvidenceStatus.INSUFFICIENT_EVIDENCE)
    assert import_visual_evidence_response(req,response).composite_outcome is None

def test_038_t_u_v_w_global_outcome_contract():
    regions,_,_,_,_,_,_,req=_bundle038()
    result=import_visual_evidence_response(req,_response038(req,regions,outcome="beta"))
    assert result.composite_outcome=="beta" and result.discriminating is False
    bad=_response038(req,regions,outcome="gamma")
    with pytest.raises(ValueError): import_visual_evidence_response(req,bad)
    data=_response038(req,regions).model_dump(); data["composite_status"]="ambiguous"
    with pytest.raises(ValueError): VisualEvidenceResponse.model_validate(data)
    data=_response038(req,regions).model_dump(); data["composite_outcome"]=None
    with pytest.raises(ValueError): VisualEvidenceResponse.model_validate(data)

def test_038_x_partial_nonexhaustive_transports_but_never_discriminates():
    regions,target,preds,q,test,inquiry,hs,req=_bundle038(exhaustive=False)
    response=_response038(req,regions)
    response=response.model_copy(update={"source_results":response.source_results[:1]})
    result=import_visual_evidence_response(req,response)
    assert len(result.composite_sources)==1 and result.discriminating is False and not result.sufficient_visibility

def test_038_y_apply_composite_without_machine_sufficiency_never_eliminates():
    regions,_,_,_,_,inquiry,_,req=_bundle038()
    result=import_visual_evidence_response(req,_response038(req,regions,outcome="alpha"))
    updated=apply_inquiry_test(inquiry,result)
    assert updated.state is InquiryState.OPEN and set(updated.viable_hypothesis_ids)=={"h-alpha","h-beta"}

def test_038_z_atomic_roundtrip_persists_sources_statuses_and_outcome():
    regions,_,_,_,test,inquiry,_,req=_bundle038()
    result=import_visual_evidence_response(req,_response038(req,regions,statuses={"s1":VisualEvidenceStatus.OCCLUDED},outcome="alpha"))
    updated=apply_inquiry_test(inquiry,result)
    hs=[OpenHypothesis(id="h-alpha",subject_refs=["subject"],statement="opaque"),
        OpenHypothesis(id="h-beta",subject_refs=["subject"],statement="opaque")]
    ws=MultiViewWorkspace(photo_count=2,pass_1=MultiViewPass(pass_number=1,hypotheses=hs),
        pass_2=MultiViewPass(pass_number=2),inquiries=[updated])
    loaded=MultiViewWorkspace.model_validate_json(ws.model_dump_json())
    persisted=loaded.inquiries[0].test_results[0]
    assert persisted.composite_outcome=="alpha"
    assert len(persisted.composite_sources)==2
    assert persisted.composite_source_statuses["s1"]=="occluded"
    assert len(loaded.inquiries[0].tests)==1

def test_038_aa_ab_legacy_roundtrip_and_schema_are_still_machine_generated():
    test_037_u_legacy_discriminating_test_roundtrip_unchanged()
    assert visual_evidence_response_schema()==VisualEvidenceResponse.model_json_schema()
    assert visual_evidence_response_invariants()


# Experiment 039 — minimal machine sufficiency for atomic composite tests.

def _with_sufficiency039(req, inquiry, required):
    contract=CompositeSufficiencyContract(required_source_ids=required)
    inquiry=inquiry.model_copy(deep=True)
    inquiry.tests[0].composite_sufficiency=contract
    req=req.model_copy(update={"composite_sufficiency":contract})
    return req,inquiry

def test_039_a_old_038_composite_without_contract_stays_fail_closed():
    regions,_,_,_,_,inquiry,_,req=_bundle038()
    result=import_visual_evidence_response(req,_response038(req,regions,outcome="alpha"))
    assert not result.sufficient_visibility and not result.discriminating
    assert apply_inquiry_test(inquiry,result).state is InquiryState.OPEN

def test_039_b_legacy_mono_continuation_unchanged():
    test_038_a_b_historical_request_response_import_preserved()

def test_039_c_d_required_occluded_or_nonvisible_is_insufficient():
    for status in (VisualEvidenceStatus.OCCLUDED,VisualEvidenceStatus.NON_VISIBLE):
        regions,_,_,_,_,inquiry,_,req=_bundle038()
        req,inquiry=_with_sufficiency039(req,inquiry,["s0","s1"])
        result=import_visual_evidence_response(req,_response038(req,regions,statuses={"s1":status},outcome="alpha"))
        assert not result.sufficient_visibility and not result.discriminating

def test_039_e_sufficient_sources_without_conclusive_outcome_do_not_discriminate():
    regions,_,_,_,_,inquiry,_,req=_bundle038()
    req,inquiry=_with_sufficiency039(req,inquiry,["s0","s1"])
    response=_response038(req,regions,outcome=None,composite_status=VisualEvidenceStatus.INSUFFICIENT_EVIDENCE)
    result=import_visual_evidence_response(req,response)
    assert result.sufficient_visibility and result.composite_outcome is None and not result.discriminating

def test_039_f_sufficient_outcome_compatible_with_all_is_nondiscriminating():
    regions,target,preds,q,test,inquiry,hs,req=_bundle038()
    q=q.model_copy(deep=True); q.discriminants[0].expected_outcomes={"h-alpha":"same","h-beta":"same"}
    req=req.model_copy(update={"question":q})
    req,inquiry=_with_sufficiency039(req,inquiry,["s0","s1"])
    response=_response038(req,regions,outcome="same")
    result=import_visual_evidence_response(req,response)
    assert result.sufficient_visibility and set(result.compatible_prediction_ids)=={"p-alpha","p-beta"}
    assert not result.discriminating

def test_039_g_h_sufficient_unique_outcome_discriminates_and_apply_eliminates_only_incompatible():
    regions,_,_,_,_,inquiry,_,req=_bundle038()
    req,inquiry=_with_sufficiency039(req,inquiry,["s0","s1"])
    result=import_visual_evidence_response(req,_response038(req,regions,outcome="alpha"))
    assert result.sufficient_visibility and result.discriminating
    assert result.compatible_prediction_ids==["p-alpha"]
    updated=apply_inquiry_test(inquiry,result)
    assert updated.viable_hypothesis_ids==["h-alpha"] and updated.state is InquiryState.RESOLVED

def test_039_i_optional_occluded_source_does_not_break_explicit_required_set():
    regions,_,_,_,_,inquiry,_,req=_bundle038(n=3)
    req,inquiry=_with_sufficiency039(req,inquiry,["s0","s1"])
    result=import_visual_evidence_response(req,_response038(req,regions,statuses={"s2":VisualEvidenceStatus.OCCLUDED},outcome="alpha"))
    assert result.sufficient_visibility and result.discriminating

def test_039_j_missing_required_source_nonexhaustive_is_insufficient_not_absent():
    regions,_,_,_,_,inquiry,_,req=_bundle038(exhaustive=False)
    req,inquiry=_with_sufficiency039(req,inquiry,["s0","s1"])
    response=_response038(req,regions,outcome="alpha").model_copy(update={"source_results":_response038(req,regions).source_results[:1]})
    result=import_visual_evidence_response(req,response)
    assert not result.sufficient_visibility and not result.discriminating
    assert result.composite_source_statuses=={"s0":"observed"}

def test_039_k_exhaustive_missing_still_rejected_before_sufficiency():
    regions,_,_,_,_,inquiry,_,req=_bundle038()
    req,inquiry=_with_sufficiency039(req,inquiry,["s0"])
    response=_response038(req,regions).model_copy(update={"source_results":_response038(req,regions).source_results[:1]})
    with pytest.raises(ValueError): import_visual_evidence_response(req,response)

def test_039_l_m_contract_unknown_or_duplicate_source_rejected():
    regions,_,_,_,test,_,_,_= _bundle038()
    with pytest.raises(ValueError):
        DiscriminatingTest(id="x",prediction_ids=test.prediction_ids,evidence_sought="synthetic_relation",
            source_observation_ids=test.source_observation_ids,evidence_regions=regions,
            composite_sufficiency=CompositeSufficiencyContract(required_source_ids=["unknown"]))
    with pytest.raises(ValueError):
        CompositeSufficiencyContract(required_source_ids=["s0","s0"])

def test_039_n_permutation_preserves_sufficiency():
    regions,_,_,_,_,inquiry,_,req=_bundle038()
    req,inquiry=_with_sufficiency039(req,inquiry,["s0","s1"])
    a=import_visual_evidence_response(req,_response038(req,regions,outcome="alpha"))
    b=import_visual_evidence_response(req,_response038(req,regions,outcome="alpha",order=[1,0]))
    assert a.sufficient_visibility==b.sufficient_visibility==True
    assert a.compatible_prediction_ids==b.compatible_prediction_ids

def test_039_o_p_contract_is_structured_no_text_rule_or_parser():
    contract=CompositeSufficiencyContract(required_source_ids=["a","b"])
    assert contract.model_dump()=={"required_source_ids":["a","b"]}
    assert all(isinstance(x,str) for x in contract.required_source_ids)

def test_039_q_r_s_inconclusive_required_sources_never_become_negative_or_sufficient():
    for status in (VisualEvidenceStatus.OCCLUDED,VisualEvidenceStatus.NON_VISIBLE,
                   VisualEvidenceStatus.AMBIGUOUS,VisualEvidenceStatus.INSUFFICIENT_EVIDENCE):
        regions,_,_,_,_,inquiry,_,req=_bundle038()
        req,inquiry=_with_sufficiency039(req,inquiry,["s0"])
        result=import_visual_evidence_response(req,_response038(req,regions,statuses={"s0":status},outcome="alpha"))
        assert not result.sufficient_visibility and not result.discriminating
        assert result.composite_source_statuses["s0"]==status.value

def test_039_t_workspace_roundtrip_preserves_sufficiency_contract():
    regions,_,_,_,_,inquiry,_,req=_bundle038()
    req,inquiry=_with_sufficiency039(req,inquiry,["s0"])
    result=import_visual_evidence_response(req,_response038(req,regions,outcome="alpha"))
    updated=apply_inquiry_test(inquiry,result)
    hs=[OpenHypothesis(id="h-alpha",subject_refs=["subject"],statement="opaque"),
        OpenHypothesis(id="h-beta",subject_refs=["subject"],statement="opaque")]
    ws=MultiViewWorkspace(photo_count=2,pass_1=MultiViewPass(pass_number=1,hypotheses=hs),
        pass_2=MultiViewPass(pass_number=2),inquiries=[updated])
    loaded=MultiViewWorkspace.model_validate_json(ws.model_dump_json())
    assert loaded.inquiries[0].tests[0].composite_sufficiency.required_source_ids==["s0"]

def test_039_u_old_038_workspace_without_contract_reloads_fail_closed():
    regions,_,_,_,test,inquiry,_,req=_bundle038()
    hs=[OpenHypothesis(id="h-alpha",subject_refs=["subject"],statement="opaque"),
        OpenHypothesis(id="h-beta",subject_refs=["subject"],statement="opaque")]
    ws=MultiViewWorkspace(photo_count=2,pass_1=MultiViewPass(pass_number=1,hypotheses=hs),
        pass_2=MultiViewPass(pass_number=2),inquiries=[inquiry])
    loaded=MultiViewWorkspace.model_validate_json(ws.model_dump_json())
    assert loaded.inquiries[0].tests[0].composite_sufficiency is None
    result=import_visual_evidence_response(req,_response038(req,regions,outcome="alpha"))
    assert not result.sufficient_visibility and not result.discriminating

def test_039_v_continuation_regression_suite_anchor():
    test_038_a_b_historical_request_response_import_preserved()


# Experiment 040 — explicit identity-discriminant consumer, no identity heuristic.

def _id040(n=2, regions=True):
    obs=[]
    for i in range(n):
        obs.append(LocalObservation(
            id=f"opaque-observation-{i}", photo_index=i+1, status=ClaimStatus.OBSERVED,
            visibility=VisibilityStatus.VISIBLE,
            region=NormalizedImageRegion(x0=.1,y0=.1,x1=.2,y1=.2) if regions and i != n-1 else None,
            proposed_category="must-not-be-read", statement="must not be interpreted",
        ))
    candidate=IdentityCandidate(
        id="opaque-candidate", observation_ids=[o.id for o in obs],
        status=IdentityStatus.UNRESOLVED, inquiry_state=IdentityInquiryState.OPEN_ALTERNATIVES,
        open_alternatives=[IdentityStatus.SAME_PHYSICAL_OBJECT,IdentityStatus.INCOMPATIBLE],
        corroborating_photo_indexes=[1], conflicting_photo_indexes=[2],
    )
    uncertainty=detect_identity_uncertainties([candidate],obs)[0]
    sources={o.id:f"source-{i}" for i,o in enumerate(obs)}
    disc=IdentityDiscriminant(
        id="explicit-disc", identity_candidate_id=candidate.id,
        property_name="opaque_perceptual_pattern", source_ids_by_observation=sources,
        outcomes_by_alternative={
            IdentityStatus.SAME_PHYSICAL_OBJECT.value:["MATCH_PATTERN_ALPHA"],
            IdentityStatus.INCOMPATIBLE.value:["MATCH_PATTERN_BETA"],
        },
        required_source_ids=list(sources.values()),
    )
    return obs,candidate,uncertainty,disc

def test_040_a_legacy_identity_without_035_contract_not_enquirable():
    a,b=_obs("legacy-a",1),_obs("legacy-b",2)
    candidate=IdentityCandidate(id="legacy",observation_ids=[a.id,b.id],
        status=IdentityStatus.UNRESOLVED)
    assert detect_identity_uncertainties([candidate],[a,b])==[]

def test_040_b_open_alternatives_without_discriminant_stops_after_uncertainty():
    obs,c,u,d=_id040()
    assert u.property_name=="identity"
    assert build_identity_discriminant_inquiry(c,u,None,obs) is None

def test_040_c_d_explicit_two_and_three_observation_discriminants_preserve_sources():
    for n in (2,3):
        obs,c,u,d=_id040(n)
        a=build_identity_discriminant_inquiry(c,u,d,obs)
        assert a is not None and len(a.predictions)==2
        assert len(a.target.evidence_regions)==n
        assert [x.observation_ref for x in a.target.evidence_regions]==[o.id for o in obs]

def test_040_e_explicit_mapping_yields_structured_discrimination():
    obs,c,u,d=_id040()
    a=build_identity_discriminant_inquiry(c,u,d,obs)
    expected=a.question.discriminants[0].expected_outcomes
    assert set(expected.values())=={"MATCH_PATTERN_ALPHA","MATCH_PATTERN_BETA"}

def test_040_f_same_outcome_for_all_alternatives_fails_closed():
    obs,c,u,d=_id040()
    d=d.model_copy(update={"outcomes_by_alternative":{
        IdentityStatus.SAME_PHYSICAL_OBJECT.value:["SAME_TOKEN"],
        IdentityStatus.INCOMPATIBLE.value:["SAME_TOKEN"]}})
    assert build_identity_discriminant_inquiry(c,u,d,obs) is None

def test_040_g_h_invalid_or_missing_alternative_mapping_rejected_or_closed():
    obs,c,u,d=_id040()
    with pytest.raises(ValueError):
        IdentityDiscriminant(id="x",identity_candidate_id=c.id,property_name="p",
            source_ids_by_observation=d.source_ids_by_observation,
            outcomes_by_alternative={"same_physical_object":["X"],"incompatible":[]},
            required_source_ids=d.required_source_ids)
    bad=d.model_copy(update={"outcomes_by_alternative":{"same_physical_object":["X"]}})
    with pytest.raises(ValueError):
        build_identity_discriminant_inquiry(c,u,bad,obs)

def test_040_i_wrong_candidate_rejected():
    obs,c,u,d=_id040()
    with pytest.raises(ValueError):
        build_identity_discriminant_inquiry(c,u,d.model_copy(update={"identity_candidate_id":"other"}),obs)

def test_040_j_unknown_observation_rejected():
    obs,c,u,d=_id040()
    with pytest.raises(ValueError):
        build_identity_discriminant_inquiry(c,u,d,obs[:-1])

def test_040_k_l_unknown_required_or_duplicate_source_rejected():
    obs,c,u,d=_id040()
    with pytest.raises(ValueError):
        IdentityDiscriminant(id="x",identity_candidate_id=c.id,property_name="p",
            source_ids_by_observation=d.source_ids_by_observation,outcomes_by_alternative=d.outcomes_by_alternative,
            required_source_ids=["unknown"])
    with pytest.raises(ValueError):
        IdentityDiscriminant(id="x",identity_candidate_id=c.id,property_name="p",
            source_ids_by_observation={obs[0].id:"dup",obs[1].id:"dup"},
            outcomes_by_alternative=d.outcomes_by_alternative,required_source_ids=["dup"])

def test_040_m_n_o_roi_exact_or_none_and_never_fabricated():
    obs,c,u,d=_id040(regions=True)
    a=build_identity_discriminant_inquiry(c,u,d,obs)
    assert a.target.evidence_regions[0].region==obs[0].region
    assert a.target.evidence_regions[1].region is None

def test_040_p_q_support_indexes_alone_never_create_discriminant():
    obs,c,u,d=_id040()
    assert c.corroborating_photo_indexes and c.conflicting_photo_indexes
    assert build_identity_discriminant_inquiry(c,u,None,obs) is None

def test_040_r_s_t_prose_category_and_ids_do_not_create_discriminant():
    obs,c,u,d=_id040()
    obs[0]=obs[0].model_copy(update={"statement":"MATCH_PATTERN_ALPHA same looks similar",
                                    "proposed_category":"MATCH_PATTERN_BETA"})
    c=c.model_copy(update={"id":"same-looking-object"})
    u=u.model_copy(update={"source_ref":c.id})
    assert build_identity_discriminant_inquiry(c,u,None,obs) is None

def test_040_u_v_atomic_composite_target_and_test():
    obs,c,u,d=_id040(3)
    a=build_identity_discriminant_inquiry(c,u,d,obs)
    assert len(a.target.evidence_regions)==3
    assert len(a.inquiry.tests)==1 and len(a.inquiry.tests[0].evidence_regions)==3
    assert a.inquiry.tests[0].photo_index is None and a.inquiry.tests[0].region is None

def test_040_w_reuses_exact_039_sufficiency_contract():
    obs,c,u,d=_id040()
    a=build_identity_discriminant_inquiry(c,u,d,obs)
    assert isinstance(a.inquiry.tests[0].composite_sufficiency,CompositeSufficiencyContract)
    assert a.inquiry.tests[0].composite_sufficiency.required_source_ids==d.required_source_ids

def test_040_x_workspace_roundtrip_preserves_discriminant_and_provenance():
    obs,c,u,d=_id040()
    a=build_identity_discriminant_inquiry(c,u,d,obs)
    ws=MultiViewWorkspace(photo_count=2,
        pass_1=MultiViewPass(pass_number=1,observations=obs,identities=[c],hypotheses=a.hypotheses),
        pass_2=MultiViewPass(pass_number=2),inquiries=[a.inquiry],identity_discriminants=[d])
    loaded=MultiViewWorkspace.model_validate_json(ws.model_dump_json())
    assert loaded.identity_discriminants==[d]
    assert loaded.inquiries[0].tests[0].evidence_regions==a.inquiry.tests[0].evidence_regions

def test_040_y_old_035_workspace_without_discriminant_reloads_fail_closed():
    obs,c,u,d=_id040()
    ws=MultiViewWorkspace(photo_count=2,pass_1=MultiViewPass(pass_number=1,observations=obs,identities=[c]),
        pass_2=MultiViewPass(pass_number=2))
    loaded=MultiViewWorkspace.model_validate_json(ws.model_dump_json())
    assert loaded.identity_discriminants==[]
    assert build_identity_discriminant_inquiry(c,u,None,obs) is None

def test_040_z_continuation_non_regression_anchor():
    test_039_b_legacy_mono_continuation_unchanged()


# Experiment 041 — visual producer of explicit identity discriminants.

def _producer041(n=2, last_region=True):
    obs,c,u,d=_id040(n, regions=last_region)
    req=build_identity_discriminant_producer_request(c,obs)
    assert req is not None
    mapping={s.observation_ref:s.source_id for s in req.sources}
    response=IdentityDiscriminantProducerResponse(
        request_id=req.request_id, identity_candidate_id=c.id,
        status=IdentityDiscriminantProducerStatus.DISCRIMINANT_PROPOSED,
        property_name=req.allowed_property_names[0],
        property_description="A precise synthetic perceptual relation, documentation only.",
        source_ids_by_observation=mapping,
        outcomes_by_alternative={
            IdentityStatus.SAME_PHYSICAL_OBJECT.value:[req.allowed_outcomes[0]],
            IdentityStatus.INCOMPATIBLE.value:[req.allowed_outcomes[1]],
        },
        outcome_descriptions={
            req.allowed_outcomes[0]:"Synthetic observable configuration alpha.",
            req.allowed_outcomes[1]:"Synthetic observable configuration beta.",
        },
        required_source_ids=list(mapping.values()),
    )
    return obs,c,req,response

def test_041_a_enquirable_candidate_generates_producer_request():
    obs,c,req,response=_producer041()
    assert req.identity_candidate_id==c.id and len(req.sources)==2

def test_041_b_non_enquirable_candidate_generates_no_request():
    a,b=_obs("a",1),_obs("b",2)
    c=IdentityCandidate(id="legacy",observation_ids=[a.id,b.id],status=IdentityStatus.UNRESOLVED)
    assert build_identity_discriminant_producer_request(c,[a,b]) is None

def test_041_c_d_no_reliable_discriminant_is_valid_and_creates_nothing():
    obs,c,req,response=_producer041()
    no=IdentityDiscriminantProducerResponse(request_id=req.request_id,identity_candidate_id=c.id,
        status=IdentityDiscriminantProducerStatus.NO_RELIABLE_DISCRIMINANT)
    assert import_identity_discriminant_producer_response(req,no) is None

def test_041_e_f_valid_two_and_three_source_discriminants_import_without_pair_reduction():
    for n in (2,3):
        obs,c,req,response=_producer041(n)
        d=import_identity_discriminant_producer_response(req,response)
        assert d is not None and len(d.source_ids_by_observation)==n

def test_041_g_unknown_observation_rejected_by_request_builder():
    obs,c,req,response=_producer041()
    with pytest.raises(ValueError):
        build_identity_discriminant_producer_request(c,obs[:-1])

def test_041_h_unknown_source_id_rejected():
    obs,c,req,response=_producer041()
    bad=response.model_copy(update={"source_ids_by_observation":{**response.source_ids_by_observation,obs[0].id:"unknown"}})
    with pytest.raises(ValueError):
        import_identity_discriminant_producer_response(req,bad)

def test_041_i_duplicate_source_id_rejected():
    obs,c,req,response=_producer041()
    dup={o.id:"dup" for o in obs}
    bad=response.model_copy(update={"source_ids_by_observation":dup,"required_source_ids":["dup"]})
    with pytest.raises(ValueError):
        import_identity_discriminant_producer_response(req,bad)

def test_041_j_unknown_required_source_rejected():
    obs,c,req,response=_producer041()
    with pytest.raises(ValueError):
        import_identity_discriminant_producer_response(req,response.model_copy(update={"required_source_ids":["unknown"]}))

def test_041_k_l_missing_or_extra_alternative_rejected():
    obs,c,req,response=_producer041()
    one={IdentityStatus.SAME_PHYSICAL_OBJECT.value:[req.allowed_outcomes[0]]}
    with pytest.raises(ValueError):
        import_identity_discriminant_producer_response(req,response.model_copy(update={"outcomes_by_alternative":one}))
    extra={**response.outcomes_by_alternative,"other":[req.allowed_outcomes[2]]}
    with pytest.raises(ValueError):
        import_identity_discriminant_producer_response(req,response.model_copy(update={"outcomes_by_alternative":extra}))

def test_041_m_shared_outcome_rejected():
    obs,c,req,response=_producer041()
    shared={x:[req.allowed_outcomes[0]] for x in req.open_alternatives}
    bad=response.model_copy(update={"outcomes_by_alternative":shared,
        "outcome_descriptions":{req.allowed_outcomes[0]:"shared"}})
    with pytest.raises(ValueError):
        import_identity_discriminant_producer_response(req,bad)

def test_041_n_alternative_without_outcome_rejected():
    obs,c,req,response=_producer041()
    bad=response.model_copy(update={"outcomes_by_alternative":{
        req.open_alternatives[0]:[req.allowed_outcomes[0]],req.open_alternatives[1]:[]}})
    with pytest.raises(ValueError):
        import_identity_discriminant_producer_response(req,bad)

def test_041_o_missing_or_invalid_property_rejected():
    obs,c,req,response=_producer041()
    with pytest.raises(ValueError):
        IdentityDiscriminantProducerResponse(request_id=req.request_id,identity_candidate_id=c.id,
            status=IdentityDiscriminantProducerStatus.DISCRIMINANT_PROPOSED)
    with pytest.raises(ValueError):
        import_identity_discriminant_producer_response(req,response.model_copy(update={"property_name":"invented"}))

def test_041_p_extra_response_field_rejected():
    obs,c,req,response=_producer041()
    raw=response.model_dump(); raw["extra"]="forbidden"
    with pytest.raises(ValueError):
        IdentityDiscriminantProducerResponse.model_validate(raw)

def test_041_q_r_null_roi_remains_null_and_is_never_fabricated():
    obs,c,req,response=_producer041(last_region=True)
    assert obs[-1].region is None
    assert req.sources[-1].region is None

def test_041_s_t_support_indexes_alone_do_not_create_discriminant():
    obs,c,u,d=_id040()
    assert c.corroborating_photo_indexes and c.conflicting_photo_indexes
    req=build_identity_discriminant_producer_request(c,obs)
    no=IdentityDiscriminantProducerResponse(request_id=req.request_id,identity_candidate_id=c.id,
        status=IdentityDiscriminantProducerStatus.NO_RELIABLE_DISCRIMINANT)
    assert import_identity_discriminant_producer_response(req,no) is None

def test_041_u_v_w_prose_category_and_id_are_not_interpreted():
    obs,c,u,d=_id040()
    obs[0]=obs[0].model_copy(update={"statement":"outcome_alpha looks same","proposed_category":"same"})
    c=c.model_copy(update={"id":"same-object-name"})
    req=build_identity_discriminant_producer_request(c,obs)
    assert req is not None
    no=IdentityDiscriminantProducerResponse(request_id=req.request_id,identity_candidate_id=c.id,
        status=IdentityDiscriminantProducerStatus.NO_RELIABLE_DISCRIMINANT)
    assert import_identity_discriminant_producer_response(req,no) is None

def test_041_x_valid_response_discriminant_persists_in_workspace():
    obs,c,req,response=_producer041()
    d=import_identity_discriminant_producer_response(req,response)
    ws=MultiViewWorkspace(photo_count=2,pass_1=MultiViewPass(pass_number=1,observations=obs,identities=[c]),
        pass_2=MultiViewPass(pass_number=2),identity_discriminants=[d])
    loaded=MultiViewWorkspace.model_validate_json(ws.model_dump_json())
    assert loaded.identity_discriminants==[d]
    assert loaded.identity_discriminants[0].property_description==d.property_description

def test_041_y_old_workspace_without_producer_or_discriminant_reloads():
    obs,c,u,d=_id040()
    ws=MultiViewWorkspace(photo_count=2,pass_1=MultiViewPass(pass_number=1,observations=obs,identities=[c]),
        pass_2=MultiViewPass(pass_number=2))
    assert MultiViewWorkspace.model_validate_json(ws.model_dump_json()).identity_discriminants==[]

def test_041_z_continuation_non_regression_anchor():
    test_039_b_legacy_mono_continuation_unchanged()

def test_041_contract_embeds_generated_schema_and_machine_invariants():
    obs,c,req,response=_producer041()
    assert req.response_schema==IdentityDiscriminantProducerResponse.model_json_schema()
    assert req.response_invariants
    assert all(isinstance(x,str) for x in req.response_invariants)

def test_041_fresh_bootstrap_is_versioned_and_does_not_embed_discriminant():
    req=build_identity_enquiry_bootstrap_request("real-house-5-bootstrap-v4-041",
        [f"{i:02d}-original.jpg" for i in range(1,6)])
    assert req.schema_version=="0.4"
    assert req.photos[0].filename=="01-original.jpg" and len(req.photos)==5
    assert "open_alternatives" in req.instruction
    assert "subsequent machine request" in req.instruction


# Experiment 044 — inconclusive investigations exhaust only the identical evidence target.

def _continuity_044(region=None, photo_index=1, observation_id="edge"):
    region = region or NormalizedImageRegion(x0=0.1, y0=0.2, x1=0.3, y1=0.8)
    observation = LocalObservation(
        id=observation_id, photo_index=photo_index, status=ClaimStatus.OBSERVED,
        visibility=VisibilityStatus.VISIBLE, region=region, statement="Synthetic edge.",
        observable_properties=["continuation"],
    )
    uncertainty = detect_continuity_uncertainties([observation])[0]
    hypotheses = derive_competing_hypotheses(uncertainty)
    predictions = [derive_observable_prediction(item) for item in hypotheses]
    question = derive_discriminating_question(predictions)
    targets = derive_candidate_evidence_targets(question, hypotheses, [observation])
    assessments = assess_discrimination_targets(question, targets, [observation])
    selection = select_discrimination_targets(assessments)
    inquiry = build_executable_visual_inquiry(
        uncertainty, hypotheses, predictions, question, assessments, selection
    )
    return observation, uncertainty, hypotheses, predictions, question, assessments, inquiry

def test_044_a_resolved_032_suppression_remains_unchanged():
    observation, uncertainty, hypotheses, predictions, question, assessments, inquiry = _continuity_044()
    result = InquiryTestResult(
        test_id=inquiry.tests[0].id, inspected=True, region_in_frame=True,
        visibility=VisibilityStatus.VISIBLE, sufficient_visibility=True,
        statement="Synthetic decisive result.",
        compatible_prediction_ids=[predictions[0].id], discriminating=True,
    )
    resolved = apply_inquiry_test(inquiry, result)
    assert resolved.state is InquiryState.RESOLVED
    assert detect_continuity_uncertainties(
        [observation], inquiries=[resolved], hypotheses=hypotheses
    ) == []

def test_044_b_open_inconclusive_identical_target_is_not_reproposed():
    observation, uncertainty, hypotheses, predictions, question, assessments, inquiry = _continuity_044()
    result = InquiryTestResult(
        test_id=inquiry.tests[0].id, inspected=True, region_in_frame=True,
        visibility=VisibilityStatus.OCCLUDED, sufficient_visibility=False,
        statement="Synthetic occlusion.", compatible_prediction_ids=[item.id for item in predictions],
        discriminating=False,
    )
    opened = apply_inquiry_test(inquiry, result)
    available = exclude_already_investigated_targets(uncertainty, assessments, [opened])
    assert opened.state is InquiryState.OPEN
    assert available == []
    assert detect_continuity_uncertainties(
        [observation], inquiries=[opened], hypotheses=hypotheses
    ) == [uncertainty]

def test_044_c_distinct_target_remains_available():
    observation, uncertainty, hypotheses, predictions, question, assessments, inquiry = _continuity_044()
    result = InquiryTestResult(
        test_id=inquiry.tests[0].id, inspected=True, region_in_frame=False,
        visibility=VisibilityStatus.NON_VISIBLE, sufficient_visibility=False,
        statement="Synthetic non-visible.", compatible_prediction_ids=[item.id for item in predictions],
        discriminating=False,
    )
    opened = apply_inquiry_test(inquiry, result)
    other = assessments[0].model_copy(deep=True)
    other.target.region = NormalizedImageRegion(x0=0.4,y0=0.2,x1=0.5,y1=0.8)
    available = exclude_already_investigated_targets(uncertainty, [assessments[0], other], [opened])
    assert available == [other]

def test_044_d_discriminating_result_still_resolves_normally():
    observation, uncertainty, hypotheses, predictions, question, assessments, inquiry = _continuity_044()
    result = InquiryTestResult(
        test_id=inquiry.tests[0].id, inspected=True, region_in_frame=True,
        visibility=VisibilityStatus.VISIBLE, sufficient_visibility=True,
        statement="Synthetic decisive result.", compatible_prediction_ids=[predictions[1].id],
        discriminating=True,
    )
    resolved = apply_inquiry_test(inquiry, result)
    assert resolved.state is InquiryState.RESOLVED
    assert resolved.resolved_hypothesis_id == predictions[1].hypothesis_id

def test_044_e_historical_observation_is_never_rewritten():
    observation, uncertainty, hypotheses, predictions, question, assessments, inquiry = _continuity_044()
    before = observation.model_dump()
    result = InquiryTestResult(
        test_id=inquiry.tests[0].id, inspected=True, region_in_frame=True,
        visibility=VisibilityStatus.OCCLUDED, sufficient_visibility=False,
        statement="Synthetic occlusion.", compatible_prediction_ids=[item.id for item in predictions],
        discriminating=False,
    )
    opened = apply_inquiry_test(inquiry, result)
    exclude_already_investigated_targets(uncertainty, assessments, [opened])
    assert observation.model_dump() == before


# Experiment 047 — explicit competing binary relation contract.

def _relation_obs_047(obs_id="obs-a"):
    return LocalObservation(
        id=obs_id, photo_index=1, status=ClaimStatus.OBSERVED,
        visibility=VisibilityStatus.VISIBLE, statement="Synthetic provenance.",
    )

def test_047_a_historical_relation_is_not_enquirable():
    old = {
        "id":"rel-old","subject_ref":"A","object_ref":"B","relation":"RELATION_X",
        "status":"inferred","certainty":"unknown","supporting_photo_indexes":[1],
    }
    candidate = ArchitecturalRelationCandidate.model_validate(old)
    assert candidate.inquiry_state is RelationInquiryState.NOT_ENQUIRABLE
    assert candidate.open_alternatives == []
    assert detect_relation_uncertainties([candidate], [_relation_obs_047()]) == []

def test_047_b_plausible_relation_without_explicit_alternatives_is_not_uncertainty():
    candidate = ArchitecturalRelationCandidate(
        id="rel-p", subject_ref="A", object_ref="B", relation="RELATION_X",
        certainty=CertaintyLevel.PLAUSIBLE,
    )
    assert detect_relation_uncertainties([candidate], [_relation_obs_047()]) == []

def test_047_c_unknown_relation_without_explicit_alternatives_is_not_uncertainty():
    candidate = ArchitecturalRelationCandidate(
        id="rel-u", subject_ref="A", object_ref="B", relation="RELATION_X",
        certainty=CertaintyLevel.UNKNOWN,
    )
    assert detect_relation_uncertainties([candidate], [_relation_obs_047()]) == []

def test_047_d_explicit_open_relations_lift_to_one_structured_uncertainty():
    observations=[_relation_obs_047("obs-a"),_relation_obs_047("obs-b")]
    candidate=ArchitecturalRelationCandidate(
        id="rel-open",subject_ref="A",object_ref="B",relation="RELATION_X",
        inquiry_state=RelationInquiryState.OPEN_ALTERNATIVES,
        open_alternatives=[
            RelationAlternative(relation="RELATION_X",source_observation_ids=["obs-a"]),
            RelationAlternative(relation="RELATION_Y",source_observation_ids=["obs-b"]),
        ],
    )
    result=detect_relation_uncertainties([candidate],observations)
    assert len(result)==1
    assert result[0].subject_ref=="A"
    assert result[0].source_ref=="rel-open"
    assert result[0].source_kind=="relation_candidate"
    assert result[0].open_alternatives==["RELATION_X","RELATION_Y"]
    assert result[0].source_observation_ids==["obs-a","obs-b"]

def test_047_e_one_alternative_rejected():
    with pytest.raises(ValueError):
        ArchitecturalRelationCandidate(
            id="rel-one",subject_ref="A",object_ref="B",relation="RELATION_X",
            inquiry_state=RelationInquiryState.OPEN_ALTERNATIVES,
            open_alternatives=[RelationAlternative(relation="RELATION_X",source_observation_ids=["obs-a"])],
        )

def test_047_f_duplicate_alternatives_rejected():
    with pytest.raises(ValueError):
        ArchitecturalRelationCandidate(
            id="rel-dupe",subject_ref="A",object_ref="B",relation="RELATION_X",
            inquiry_state=RelationInquiryState.OPEN_ALTERNATIVES,
            open_alternatives=[
                RelationAlternative(relation="RELATION_X",source_observation_ids=["obs-a"]),
                RelationAlternative(relation="RELATION_X",source_observation_ids=["obs-b"]),
            ],
        )

def test_047_g_incoherent_provenance_fails_closed():
    candidate=ArchitecturalRelationCandidate(
        id="rel-prov",subject_ref="A",object_ref="B",relation="RELATION_X",
        inquiry_state=RelationInquiryState.OPEN_ALTERNATIVES,
        open_alternatives=[
            RelationAlternative(relation="RELATION_X",source_observation_ids=["obs-a"]),
            RelationAlternative(relation="RELATION_Y",source_observation_ids=["missing"]),
        ],
    )
    assert detect_relation_uncertainties([candidate],[_relation_obs_047("obs-a")]) == []

def test_047_h_workspace_roundtrip_preserves_exact_relation_competition():
    observations=[_relation_obs_047("obs-a"),_relation_obs_047("obs-b")]
    candidate=ArchitecturalRelationCandidate(
        id="rel-roundtrip",subject_ref="A",object_ref="B",relation="RELATION_X",
        inquiry_state=RelationInquiryState.OPEN_ALTERNATIVES,
        open_alternatives=[
            RelationAlternative(relation="RELATION_X",source_observation_ids=["obs-a"]),
            RelationAlternative(relation="RELATION_Y",source_observation_ids=["obs-b"]),
        ],
    )
    workspace=MultiViewWorkspace(
        photo_count=1,
        pass_1=MultiViewPass(pass_number=1,observations=observations,relations=[candidate]),
        pass_2=MultiViewPass(pass_number=2),
    )
    loaded=MultiViewWorkspace.model_validate_json(workspace.model_dump_json())
    assert loaded.pass_1.relations[0] == candidate
    assert detect_relation_uncertainties(loaded.pass_1.relations,loaded.pass_1.observations)[0].open_alternatives == ["RELATION_X","RELATION_Y"]

def test_047_workspace_rejects_unknown_relation_provenance():
    candidate=ArchitecturalRelationCandidate(
        id="rel-bad-workspace",subject_ref="A",object_ref="B",relation="RELATION_X",
        inquiry_state=RelationInquiryState.OPEN_ALTERNATIVES,
        open_alternatives=[
            RelationAlternative(relation="RELATION_X",source_observation_ids=["obs-a"]),
            RelationAlternative(relation="RELATION_Y",source_observation_ids=["missing"]),
        ],
    )
    with pytest.raises(ValueError):
        MultiViewWorkspace(
            photo_count=1,
            pass_1=MultiViewPass(pass_number=1,observations=[_relation_obs_047("obs-a")],relations=[candidate]),
            pass_2=MultiViewPass(pass_number=2),
        )


# Experiment 048 — strict external producer of explicit relation alternatives.

def _relation_sources_048():
    return [
        LocalObservation(id="obs-a", photo_index=1, status=ClaimStatus.OBSERVED, visibility=VisibilityStatus.VISIBLE,
                         region=NormalizedImageRegion(x0=.1,y0=.1,x1=.2,y1=.2), statement="Synthetic A."),
        LocalObservation(id="obs-b", photo_index=2, status=ClaimStatus.OBSERVED, visibility=VisibilityStatus.VISIBLE,
                         region=NormalizedImageRegion(x0=.3,y0=.3,x1=.4,y1=.4), statement="Synthetic B."),
    ]

def _relation_request_048():
    return build_relation_alternative_producer_request("producer-048","A","B",_relation_sources_048())

def _relation_response_048(status=RelationAlternativeProducerStatus.OPEN_ALTERNATIVES):
    req=_relation_request_048()
    kwargs=dict(schema_version="0.1",producer_request_id=req.producer_request_id,subject_ref="A",object_ref="B",
                status=status,sources=req.sources)
    if status is RelationAlternativeProducerStatus.OPEN_ALTERNATIVES:
        kwargs.update(alternatives=[
            RelationAlternativeProposal(relation_token="relation_alpha",source_observation_ids=["obs-a"]),
            RelationAlternativeProposal(relation_token="relation_beta",source_observation_ids=["obs-b"]),
        ], relation_descriptions={"relation_alpha":"Synthetic relation A.","relation_beta":"Synthetic relation B."})
    return RelationAlternativeProducerResponse(**kwargs)

def test_048_a_valid_open_alternatives_imports_candidate():
    candidate=import_relation_alternative_producer_response(_relation_request_048(),_relation_response_048())
    assert candidate.inquiry_state is RelationInquiryState.OPEN_ALTERNATIVES
    assert [x.relation for x in candidate.open_alternatives]==["relation_alpha","relation_beta"]

@pytest.mark.parametrize("status",[
    RelationAlternativeProducerStatus.NO_RELIABLE_ALTERNATIVES,
    RelationAlternativeProducerStatus.INSUFFICIENT_VISUAL_EVIDENCE,
])
def test_048_bc_inconclusive_creates_no_competition(status):
    assert import_relation_alternative_producer_response(_relation_request_048(),_relation_response_048(status)) is None

def test_048_d_one_alternative_rejected():
    req=_relation_request_048()
    with pytest.raises(ValueError):
        RelationAlternativeProducerResponse(schema_version="0.1",producer_request_id=req.producer_request_id,
            subject_ref="A",object_ref="B",status="open_alternatives",sources=req.sources,
            alternatives=[RelationAlternativeProposal(relation_token="relation_alpha",source_observation_ids=["obs-a"])],
            relation_descriptions={"relation_alpha":"A"})

def test_048_e_duplicate_rejected():
    req=_relation_request_048()
    with pytest.raises(ValueError):
        RelationAlternativeProducerResponse(schema_version="0.1",producer_request_id=req.producer_request_id,
            subject_ref="A",object_ref="B",status="open_alternatives",sources=req.sources,
            alternatives=[
                RelationAlternativeProposal(relation_token="relation_alpha",source_observation_ids=["obs-a"]),
                RelationAlternativeProposal(relation_token="relation_alpha",source_observation_ids=["obs-b"])],
            relation_descriptions={"relation_alpha":"A"})

def test_048_f_subject_object_mismatch_rejected_on_import():
    response=_relation_response_048().model_copy(update={"subject_ref":"OTHER"})
    with pytest.raises(ValueError):
        import_relation_alternative_producer_response(_relation_request_048(),response)

def test_048_g_unknown_source_observation_rejected():
    response=_relation_response_048()
    response=response.model_copy(update={"alternatives":[
        RelationAlternativeProposal(relation_token="relation_alpha",source_observation_ids=["obs-a"]),
        RelationAlternativeProposal(relation_token="relation_beta",source_observation_ids=["unknown"])]})
    with pytest.raises(ValueError):
        import_relation_alternative_producer_response(_relation_request_048(),response)

def test_048_h_photo_roi_mismatch_rejected():
    response=_relation_response_048()
    bad=response.sources[0].model_copy(update={"photo_index":9})
    response=response.model_copy(update={"sources":[bad,*response.sources[1:]]})
    with pytest.raises(ValueError):
        import_relation_alternative_producer_response(_relation_request_048(),response)

def test_048_i_provenance_source_mapping_mismatch_rejected():
    response=_relation_response_048()
    bad=response.sources[0].model_copy(update={"observation_ref":"obs-b"})
    response=response.model_copy(update={"sources":[bad,*response.sources[1:]]})
    with pytest.raises(ValueError):
        import_relation_alternative_producer_response(_relation_request_048(),response)

def test_048_j_extra_field_rejected():
    payload=_relation_response_048().model_dump()
    payload["extra"]="forbidden"
    with pytest.raises(ValueError):
        RelationAlternativeProducerResponse.model_validate(payload)

def test_048_k_valid_import_detects_exactly_one_uncertainty():
    candidate=import_relation_alternative_producer_response(_relation_request_048(),_relation_response_048())
    result=detect_relation_uncertainties([candidate],_relation_sources_048())
    assert len(result)==1
    assert result[0].open_alternatives==["relation_alpha","relation_beta"]

def test_048_l_persistence_reload_preserves_candidate_and_alternatives():
    candidate=import_relation_alternative_producer_response(_relation_request_048(),_relation_response_048())
    observations=_relation_sources_048()
    workspace=MultiViewWorkspace(photo_count=2,
        pass_1=MultiViewPass(pass_number=1,observations=observations,relations=[candidate]),
        pass_2=MultiViewPass(pass_number=2))
    loaded=MultiViewWorkspace.model_validate_json(workspace.model_dump_json())
    assert loaded.pass_1.relations[0] == candidate

def test_048_inconclusive_with_alternatives_rejected():
    req=_relation_request_048()
    with pytest.raises(ValueError):
        RelationAlternativeProducerResponse(schema_version="0.1",producer_request_id=req.producer_request_id,
            subject_ref="A",object_ref="B",status="no_reliable_alternatives",sources=req.sources,
            alternatives=[
                RelationAlternativeProposal(relation_token="relation_alpha",source_observation_ids=["obs-a"]),
                RelationAlternativeProposal(relation_token="relation_beta",source_observation_ids=["obs-b"])],
            relation_descriptions={"relation_alpha":"A","relation_beta":"B"})


# Experiment 050 — strict visual discovery of a relation-worthy pair.

def _pair_obs_050():
    return [
        LocalObservation(id="o1",photo_index=1,status=ClaimStatus.OBSERVED,visibility=VisibilityStatus.VISIBLE,
            region=NormalizedImageRegion(x0=.1,y0=.1,x1=.2,y1=.2),proposed_category="synthetic-a",statement="Synthetic A."),
        LocalObservation(id="o2",photo_index=2,status=ClaimStatus.OBSERVED,visibility=VisibilityStatus.VISIBLE,
            region=NormalizedImageRegion(x0=.3,y0=.3,x1=.4,y1=.4),proposed_category="synthetic-b",statement="Synthetic B."),
    ]

def _pair_req_050():
    return build_relation_pair_producer_request("pair-request-050",_pair_obs_050(),[])

def _pair_resp_050(status=RelationPairProducerStatus.PAIR_PROPOSED):
    req=_pair_req_050()
    kw=dict(schema_version="0.1",producer_request_id=req.producer_request_id,status=status,sources=req.sources)
    if status is RelationPairProducerStatus.PAIR_PROPOSED:
        kw.update(subject=RelationPairElement(element_ref="element-a",source_observation_ids=["o1"]),
            object=RelationPairElement(element_ref="element-b",source_observation_ids=["o2"]),
            visual_evidence_source_ids=["o1","o2"])
    return RelationPairProducerResponse(**kw)

def test_050_valid_pair_creates_non_enquirable_relationless_candidate():
    candidate=import_relation_pair_producer_response(_pair_req_050(),_pair_resp_050())
    assert candidate.subject_ref=="element-a" and candidate.object_ref=="element-b"
    assert candidate.relation is None
    assert candidate.inquiry_state is RelationInquiryState.NOT_ENQUIRABLE
    assert candidate.open_alternatives==[]

@pytest.mark.parametrize("status",[RelationPairProducerStatus.NO_RELIABLE_PAIR,RelationPairProducerStatus.INSUFFICIENT_VISUAL_EVIDENCE])
def test_050_inconclusive_creates_no_pair(status):
    assert import_relation_pair_producer_response(_pair_req_050(),_pair_resp_050(status)) is None

def test_050_same_element_rejected():
    req=_pair_req_050()
    with pytest.raises(ValueError):
        RelationPairProducerResponse(producer_request_id=req.producer_request_id,status="pair_proposed",sources=req.sources,
            subject=RelationPairElement(element_ref="same",source_observation_ids=["o1"]),
            object=RelationPairElement(element_ref="same",source_observation_ids=["o2"]),visual_evidence_source_ids=["o1","o2"])

def test_050_unknown_or_outside_source_rejected():
    response=_pair_resp_050().model_copy(update={"subject":RelationPairElement(element_ref="a",source_observation_ids=["unknown"])})
    with pytest.raises(ValueError): import_relation_pair_producer_response(_pair_req_050(),response)

@pytest.mark.parametrize("field,value",[
    ("photo_index",9),
    ("region",NormalizedImageRegion(x0=.5,y0=.5,x1=.6,y1=.6)),
    ("statement","changed provenance"),
])
def test_050_source_mismatch_rejected(field,value):
    response=_pair_resp_050(); bad=response.sources[0].model_copy(update={field:value})
    response=response.model_copy(update={"sources":[bad,*response.sources[1:]]})
    with pytest.raises(ValueError): import_relation_pair_producer_response(_pair_req_050(),response)

def test_050_extra_field_rejected():
    payload=_pair_resp_050().model_dump(); payload["extra"]="x"
    with pytest.raises(ValueError): RelationPairProducerResponse.model_validate(payload)

def test_050_persistence_reload_preserves_relationless_candidate():
    candidate=import_relation_pair_producer_response(_pair_req_050(),_pair_resp_050())
    workspace=MultiViewWorkspace(photo_count=2,pass_1=MultiViewPass(pass_number=1,observations=_pair_obs_050(),relations=[candidate]),pass_2=MultiViewPass(pass_number=2))
    loaded=MultiViewWorkspace.model_validate_json(workspace.model_dump_json())
    assert loaded.pass_1.relations[0]==candidate
    assert loaded.pass_1.relations[0].relation is None
    assert loaded.pass_1.relations[0].source_observation_ids_by_element=={"element-a":["o1"],"element-b":["o2"]}
    assert loaded.pass_1.relations[0].visual_evidence_source_ids==["o1","o2"]

def test_050_inconclusive_payload_rejected():
    req=_pair_req_050()
    with pytest.raises(ValueError):
        RelationPairProducerResponse(producer_request_id=req.producer_request_id,status="no_reliable_pair",sources=req.sources,
            subject=RelationPairElement(element_ref="a",source_observation_ids=["o1"]),
            object=RelationPairElement(element_ref="b",source_observation_ids=["o2"]),visual_evidence_source_ids=["o1","o2"])


def test_052_exact_negative_investigation_persists_without_negative_relation():
    pair=import_relation_pair_producer_response(_pair_req_050(),_pair_resp_050())
    observations=_pair_obs_050()
    req=build_relation_alternative_producer_request("r52",pair.subject_ref,pair.object_ref,observations)
    response=RelationAlternativeProducerResponse(
        producer_request_id="r52",subject_ref=pair.subject_ref,object_ref=pair.object_ref,
        status=RelationAlternativeProducerStatus.NO_RELIABLE_ALTERNATIVES,sources=req.sources)
    pair=record_relation_investigation(pair,req,response)
    assert pair.relation is None and pair.open_alternatives==[]
    assert exhausted_relation_pair_evidence_sets([pair])==[["o1","o2"]]
    workspace=MultiViewWorkspace(photo_count=2,pass_1=MultiViewPass(pass_number=1,observations=observations,relations=[pair]),pass_2=MultiViewPass(pass_number=2))
    loaded=MultiViewWorkspace.model_validate_json(workspace.model_dump_json())
    assert exhausted_relation_pair_evidence_sets(loaded.pass_1.relations)==[["o1","o2"]]

def test_052_pair_request_excludes_only_exact_evidence_set():
    req=build_relation_pair_producer_request("next",_pair_obs_050(),[],[["o1","o2"]])
    assert req.excluded_exact_evidence_sets==[["o1","o2"]]
    assert "structurally distinct evidence set remains eligible" in req.instruction


def test_053_loop_router_routes_fresh_pair_to_relation_producer():
    pair=import_relation_pair_producer_response(_pair_req_050(),_pair_resp_050())
    workspace=MultiViewWorkspace(photo_count=2,pass_1=MultiViewPass(pass_number=1,observations=_pair_obs_050(),relations=[pair]),pass_2=MultiViewPass(pass_number=2))
    request=build_next_relation_loop_request("next-rel",workspace,pair)
    assert isinstance(request,RelationAlternativeProducerRequest)
    assert request.subject_ref=="element-a" and request.object_ref=="element-b"
    assert [s.observation_ref for s in request.sources]==["o1","o2"]

def test_053_loop_router_routes_exhausted_state_back_to_pair_producer():
    pair=import_relation_pair_producer_response(_pair_req_050(),_pair_resp_050())
    req=build_relation_alternative_producer_request("r53",pair.subject_ref,pair.object_ref,_pair_obs_050())
    response=RelationAlternativeProducerResponse(producer_request_id="r53",subject_ref=pair.subject_ref,object_ref=pair.object_ref,status=RelationAlternativeProducerStatus.NO_RELIABLE_ALTERNATIVES,sources=req.sources)
    pair=record_relation_investigation(pair,req,response)
    workspace=MultiViewWorkspace(photo_count=2,pass_1=MultiViewPass(pass_number=1,observations=_pair_obs_050(),relations=[pair]),pass_2=MultiViewPass(pass_number=2))
    request=build_next_relation_loop_request("next-pair",workspace)
    assert isinstance(request,RelationPairProducerRequest)
    assert request.excluded_exact_evidence_sets==[["o1","o2"]]


def test_058_batch_builds_multiple_independent_requests_without_architectural_choice():
    workspace=MultiViewWorkspace(photo_count=2,pass_1=MultiViewPass(pass_number=1,observations=_pair_obs_050()),pass_2=MultiViewPass(pass_number=2))
    batch=build_relation_pair_batch_request("batch-058",workspace,max_investigations=3)
    assert len(batch.investigations)==3
    assert len({x.investigation_id for x in batch.investigations})==3
    assert all(x.protocol=="relation_pair" for x in batch.investigations)
    assert all(x.request.sources for x in batch.investigations)

def test_058_batch_import_binds_each_result_to_its_own_request():
    workspace=MultiViewWorkspace(photo_count=2,pass_1=MultiViewPass(pass_number=1,observations=_pair_obs_050()),pass_2=MultiViewPass(pass_number=2))
    batch=build_relation_pair_batch_request("batch-058",workspace,max_investigations=2)
    r1=_pair_resp_050().model_copy(update={"producer_request_id":batch.investigations[0].request.producer_request_id})
    r2=_pair_resp_050().model_copy(update={"producer_request_id":batch.investigations[1].request.producer_request_id})
    response=VisualInquiryBatchResponse(batch_request_id="batch-058",results=[
        VisualInquiryBatchResult(investigation_id=batch.investigations[0].investigation_id,protocol="relation_pair",response=r1),
        VisualInquiryBatchResult(investigation_id=batch.investigations[1].investigation_id,protocol="relation_pair",response=r2),
    ])
    with pytest.raises(ValueError,match="duplicate relation-pair evidence set"):
        import_visual_inquiry_batch_response(batch,response)


def test_059_batch_import_persists_investigation_id_on_each_pair():
    workspace=MultiViewWorkspace(photo_count=2,pass_1=MultiViewPass(pass_number=1,observations=_pair_obs_050()),pass_2=MultiViewPass(pass_number=2))
    batch=build_relation_pair_batch_request("batch-059",workspace,max_investigations=2)
    r1=_pair_resp_050().model_copy(update={"producer_request_id":batch.investigations[0].request.producer_request_id})
    r2=_pair_resp_050().model_copy(update={
        "producer_request_id":batch.investigations[1].request.producer_request_id,
        "subject":RelationPairElement(element_ref="element-c",source_observation_ids=["o2"]),
        "object":RelationPairElement(element_ref="element-d",source_observation_ids=["o1"]),
        "visual_evidence_source_ids":["o2","o1"],
    })
    # Distinct evidence set is required by the batch anti-duplicate invariant; add a third source.
    o3=LocalObservation(id="o3",photo_index=2,status=ClaimStatus.OBSERVED,visibility=VisibilityStatus.VISIBLE,statement="Synthetic C.")
    workspace=MultiViewWorkspace(photo_count=2,pass_1=MultiViewPass(pass_number=1,observations=[*_pair_obs_050(),o3]),pass_2=MultiViewPass(pass_number=2))
    batch=build_relation_pair_batch_request("batch-059",workspace,max_investigations=2)
    def resp(item,a,b,ea,eb):
        return RelationPairProducerResponse(producer_request_id=item.request.producer_request_id,status="pair_proposed",sources=item.request.sources,
            subject=RelationPairElement(element_ref=a,source_observation_ids=[ea]),object=RelationPairElement(element_ref=b,source_observation_ids=[eb]),visual_evidence_source_ids=[ea,eb])
    response=VisualInquiryBatchResponse(batch_request_id="batch-059",results=[
        VisualInquiryBatchResult(investigation_id=batch.investigations[0].investigation_id,protocol="relation_pair",response=resp(batch.investigations[0],"a","b","o1","o2")),
        VisualInquiryBatchResult(investigation_id=batch.investigations[1].investigation_id,protocol="relation_pair",response=resp(batch.investigations[1],"c","d","o2","o3")),
    ])
    imported=import_visual_inquiry_batch_response(batch,response)
    assert [x.batch_investigation_id for x in imported]==[x.investigation_id for x in batch.investigations]
    persisted=MultiViewWorkspace(photo_count=2,pass_1=MultiViewPass(pass_number=1,observations=[*_pair_obs_050(),o3],relations=imported),pass_2=MultiViewPass(pass_number=2))
    loaded=MultiViewWorkspace.model_validate_json(persisted.model_dump_json())
    assert [x.batch_investigation_id for x in loaded.pass_1.relations]==[x.investigation_id for x in batch.investigations]


def test_059_router_batches_fresh_pairs_into_relation_alternative_requests():
    observations=_pair_obs_050()
    workspace=MultiViewWorkspace(photo_count=2,pass_1=MultiViewPass(pass_number=1,observations=observations),pass_2=MultiViewPass(pass_number=2))
    p1=import_relation_pair_producer_response(_pair_req_050(),_pair_resp_050())
    p2=p1.model_copy(update={"id":"pair-2","subject_ref":"element-c","object_ref":"element-d"})
    batch=build_relation_alternative_batch_request("next-batch",workspace,[p1,p2])
    assert len(batch.investigations)==2
    assert all(x.protocol=="relation_alternative" for x in batch.investigations)
    assert [x.request.subject_ref for x in batch.investigations]==["element-a","element-c"]


def test_060_batch_inconclusive_results_persist_exact_exhaustion_memory():
    observations=_pair_obs_050()
    workspace=MultiViewWorkspace(photo_count=2,pass_1=MultiViewPass(pass_number=1,observations=observations),pass_2=MultiViewPass(pass_number=2))
    p1=import_relation_pair_producer_response(_pair_req_050(),_pair_resp_050())
    p2=p1.model_copy(update={"id":"pair-2","subject_ref":"c","object_ref":"d"})
    batch=build_relation_alternative_batch_request("b60",workspace,[p1,p2])
    results=[]
    for item in batch.investigations:
        q=item.request
        response=RelationAlternativeProducerResponse(producer_request_id=q.producer_request_id,subject_ref=q.subject_ref,object_ref=q.object_ref,status="no_reliable_alternatives",sources=q.sources)
        results.append(VisualInquiryBatchResult(investigation_id=item.investigation_id,protocol="relation_alternative",response=response))
    updated=record_relation_alternative_batch_response(batch,VisualInquiryBatchResponse(batch_request_id="b60",results=results),[p1,p2])
    assert all(x.relation is None and not x.open_alternatives for x in updated)
    assert [x.investigations[0].investigation_id for x in updated]==[x.investigation_id for x in batch.investigations]
    assert [x.investigations[0].producer_request_id for x in updated]==[x.request.producer_request_id for x in batch.investigations]
    loaded=MultiViewWorkspace.model_validate_json(MultiViewWorkspace(photo_count=2,pass_1=MultiViewPass(pass_number=1,observations=observations,relations=updated),pass_2=MultiViewPass(pass_number=2)).model_dump_json())
    assert len(loaded.pass_1.relations)==2 and all(len(x.investigations)==1 for x in loaded.pass_1.relations)


def test_060_impact_requires_open_testable_uncertainty_and_explicit_downstream_dependency():
    u=StructuredUncertainty(id="u",subject_ref="o1",property_name="p",source_observation_ids=["o1"],open_alternatives=["a","b"])
    no_dep=assess_investigation_impact(u,discriminating_testable=True,exhausted_or_redundant=False,dependencies=[])
    assert no_dep.investigation_available and no_dep.addresses_open_uncertainty
    assert not no_dep.can_modify_shared_state and no_dep.blocked
    dep=ReasoningDependency(upstream_ref="u",downstream_ref="h1",downstream_kind="hypothesis")
    useful=assess_investigation_impact(u,discriminating_testable=True,exhausted_or_redundant=False,dependencies=[dep])
    assert useful.can_modify_shared_state and not useful.blocked
    exhausted=assess_investigation_impact(u,discriminating_testable=True,exhausted_or_redundant=True,dependencies=[dep])
    assert not exhausted.investigation_available and not exhausted.can_modify_shared_state


def test_060_impact_selection_uses_dependency_set_dominance_and_preserves_ties():
    def a(uid,refs):
        u=StructuredUncertainty(id=uid,subject_ref="o1",property_name="p",source_observation_ids=["o1"],open_alternatives=["a","b"])
        deps=[ReasoningDependency(upstream_ref=uid,downstream_ref=r,downstream_kind="hypothesis") for r in refs]
        return assess_investigation_impact(u,discriminating_testable=True,exhausted_or_redundant=False,dependencies=deps)
    narrow=a("u1",["h1"]); broad=a("u2",["h1","h2"]); incomparable=a("u3",["h3"])
    selected=select_impactful_investigations([narrow,broad,incomparable])
    assert [x.uncertainty_id for x in selected]==["u2","u3"]


def test_061_dependencies_are_lifted_only_from_explicit_hypothesis_source_links():
    u=StructuredUncertainty(id="u",subject_ref="o1",property_name="continuation",source_observation_ids=["o1"],open_alternatives=["CONTINUES","TERMINATES"])
    linked=OpenHypothesis(id="h1",subject_refs=["o1"],statement="A",certainty=CertaintyLevel.UNPROVEN,source_uncertainty_id="u")
    unrelated=OpenHypothesis(id="h2",subject_refs=["o1"],statement="B",certainty=CertaintyLevel.UNPROVEN)
    deps=derive_reasoning_dependencies_from_hypotheses([u],[linked,unrelated])
    assert [(x.upstream_ref,x.downstream_ref,x.downstream_kind) for x in deps]==[("u","h1","hypothesis")]


def test_061_not_enquirable_likely_same_does_not_become_identity_uncertainty():
    observations=_pair_obs_050()
    identity=IdentityCandidate(id="i",observation_ids=["o1","o2"],status=IdentityStatus.LIKELY_SAME,certainty=CertaintyLevel.PLAUSIBLE,inquiry_state=IdentityInquiryState.NOT_ENQUIRABLE)
    workspace=MultiViewWorkspace(photo_count=2,pass_1=MultiViewPass(pass_number=1,observations=observations,identities=[identity]),pass_2=MultiViewPass(pass_number=2))
    assert derive_existing_structured_uncertainties(workspace)==[]


def test_062_rich_bootstrap_exposes_multiview_evidence_without_promoting_candidate_to_truth():
    req=build_rich_multiview_bootstrap_request("rich",["a.jpg","b.jpg"])
    assert req.schema_version=="0.5"
    assert "identity_evidence" in req.response_schema["properties"]
    assert "relation_evidence" in req.response_schema["properties"]
    assert "perceptual_ambiguities" in req.response_schema["properties"]
    assert any("UNKNOWN alone" in x for x in req.information_to_record)


def test_062_rich_evidence_requires_exact_observation_provenance_and_oriented_refs():
    a=_obs("a",1); b=_obs("b",2)
    a=a.model_copy(update={"region":NormalizedImageRegion(x0=.1,y0=.1,x1=.2,y1=.2)})
    b=b.model_copy(update={"region":NormalizedImageRegion(x0=.3,y0=.3,x1=.4,y1=.4)})
    identity=IdentityCandidate(id="i",observation_ids=["a","b"],status=IdentityStatus.LIKELY_SAME,certainty=CertaintyLevel.PLAUSIBLE)
    region=PerceptualEvidenceRegion(observation_ref="a",photo_index=1,region=a.region,visibility=VisibilityStatus.VISIBLE)
    cue=PerceptualCue(cue_token="cue-alpha",description="Synthetic visible cue.",evidence_regions=[region],level=PerceptualEvidenceLevel.CANDIDATE)
    response=VisualBootstrapResponse(bootstrap_id="rich",photo_count=2,observations=[a,b],identity_candidates=[identity],identity_evidence=[PerceptualIdentityEvidence(identity_candidate_ref="i",supports_same=[cue],level="candidate")],relation_evidence=[PerceptualRelationEvidence(id="r",subject_ref="a",relation_token="token-alpha",object_ref="b",evidence_regions=[region],level="candidate")])
    assert response.identity_candidates[0].status is IdentityStatus.LIKELY_SAME
    assert response.relation_evidence[0].subject_ref=="a" and response.relation_evidence[0].object_ref=="b"
    bad=region.model_copy(update={"photo_index":2})
    with pytest.raises(ValueError):
        VisualBootstrapResponse(bootstrap_id="rich",photo_count=2,observations=[a,b],identity_candidates=[identity],identity_evidence=[PerceptualIdentityEvidence(identity_candidate_ref="i",supports_same=[cue.model_copy(update={"evidence_regions":[bad]})],level="candidate")])


def test_062_perceptual_ambiguity_requires_two_distinct_supported_alternatives():
    a=_obs("a",1).model_copy(update={"region":NormalizedImageRegion(x0=.1,y0=.1,x1=.2,y1=.2)})
    region=PerceptualEvidenceRegion(observation_ref="a",photo_index=1,region=a.region,visibility=VisibilityStatus.VISIBLE)
    cue=PerceptualCue(cue_token="c",description="Synthetic cue.",evidence_regions=[region],level="ambiguous")
    with pytest.raises(ValueError):
        PerceptualAmbiguity(id="amb",subject_ref="a",alternatives=[PerceptualAlternative(alternative_token="x",description="X",evidence_cues=[cue]),PerceptualAlternative(alternative_token="x",description="X2",evidence_cues=[cue])])


def _rich_063_payload():
    return {
        "schema_version":"0.5","bootstrap_id":"rich","photo_count":2,
        "observations":[
            {"observation_id":"a","photo_index":1,"roi":[.1,.1,.2,.2],"visibility":"VISIBLE","category_proposal":"surface","observable_properties":{"edge":True}},
            {"observation_id":"b","photo_index":2,"roi":[.3,.3,.4,.4],"visibility":"VISIBLE","category_proposal":"surface","observable_properties":{"edge":True}},
        ],
        "identity_candidates":[{"identity_candidate_id":"idc","observation_refs":["a","b"],"status":"CANDIDATE"}],
        "identity_evidence":[
            {"identity_candidate_ref":"idc","polarity":"SAME","epistemic_level":"CUE","cue":"same cue","provenance":[{"observation_ref":"a","photo_index":1,"roi":[.1,.1,.2,.2]},{"observation_ref":"b","photo_index":2,"roi":[.3,.3,.4,.4]}]},
            {"identity_candidate_ref":"idc","polarity":"DISTINCT","epistemic_level":"CUE","cue":"distinct cue","provenance":[{"observation_ref":"a","photo_index":1,"roi":[.1,.1,.2,.2]},{"observation_ref":"b","photo_index":2,"roi":[.3,.3,.4,.4]}]},
        ],
        "relation_evidence":[{"subject_ref":"a","relation_token":"VISIBLE_WITHIN","object_ref":"b","epistemic_level":"OBSERVED","provenance":[{"observation_ref":"a","photo_index":1,"roi":[.1,.1,.2,.2]}]}],
        "perceptual_ambiguities":[],"observer_comment":None,
    }


def test_063_strict_rich_wire_contract_and_import_preserve_cues_without_truth_promotion():
    request=build_rich_multiview_bootstrap_request("rich",["a.jpg","b.jpg"])
    response=RichVisualBootstrapResponse.model_validate(_rich_063_payload())
    workspace=import_rich_visual_bootstrap_response(request,response)
    assert len(workspace.rich_identity_cues)==2
    assert len(workspace.rich_relation_evidence)==1
    candidate=workspace.pass_1.identities[0]
    assert candidate.status is IdentityStatus.CANDIDATE
    assert candidate.inquiry_state is IdentityInquiryState.OPEN_ALTERNATIVES
    assert set(candidate.open_alternatives)=={IdentityStatus.SAME_PHYSICAL_OBJECT,IdentityStatus.INCOMPATIBLE}
    assert workspace.pass_1.relations==[]
    uncertainties=detect_identity_uncertainties(workspace.pass_1.identities,workspace.pass_1.observations)
    assert len(uncertainties)==1


def test_063_strict_rich_wire_contract_rejects_wrong_provenance_and_unknown_refs():
    payload=_rich_063_payload()
    payload["identity_evidence"][0]["provenance"][0]["roi"]=[.11,.1,.2,.2]
    with pytest.raises(ValueError): RichVisualBootstrapResponse.model_validate(payload)
    payload=_rich_063_payload()
    payload["relation_evidence"][0]["object_ref"]="missing"
    with pytest.raises(ValueError): RichVisualBootstrapResponse.model_validate(payload)


def test_063_same_only_cue_does_not_create_identity_competition():
    payload=_rich_063_payload(); payload["identity_evidence"]=payload["identity_evidence"][:1]
    request=build_rich_multiview_bootstrap_request("rich",["a.jpg","b.jpg"])
    workspace=import_rich_visual_bootstrap_response(request,RichVisualBootstrapResponse.model_validate(payload))
    assert workspace.pass_1.identities[0].inquiry_state is IdentityInquiryState.NOT_ENQUIRABLE
    assert detect_identity_uncertainties(workspace.pass_1.identities,workspace.pass_1.observations)==[]


def test_063_identity_competition_has_generic_future_entity_partition_dependency_without_score():
    request=build_rich_multiview_bootstrap_request("rich",["a.jpg","b.jpg"])
    workspace=import_rich_visual_bootstrap_response(request,RichVisualBootstrapResponse.model_validate(_rich_063_payload()))
    uncertainties=detect_identity_uncertainties(workspace.pass_1.identities,workspace.pass_1.observations)
    dependencies=derive_identity_world_representation_dependencies(uncertainties)
    assert len(dependencies)==1
    assert dependencies[0].upstream_ref==uncertainties[0].id
    assert dependencies[0].downstream_kind=="future_world_representation"
    assert dependencies[0].downstream_ref=="physical-entity-partition:idc"


def test_064_identity_discriminant_request_requires_both_rich_cue_polarities():
    a=_obs("a",1).model_copy(update={"region":NormalizedImageRegion(x0=.1,y0=.1,x1=.2,y1=.2)})
    b=_obs("b",2).model_copy(update={"region":NormalizedImageRegion(x0=.3,y0=.3,x1=.4,y1=.4)})
    candidate=IdentityCandidate(id="idc",observation_ids=["a","b"],status=IdentityStatus.CANDIDATE,certainty=CertaintyLevel.UNKNOWN,inquiry_state=IdentityInquiryState.OPEN_ALTERNATIVES,open_alternatives=[IdentityStatus.SAME_PHYSICAL_OBJECT,IdentityStatus.INCOMPATIBLE])
    pa=RichEvidenceProvenance(observation_ref="a",photo_index=1,roi=(.1,.1,.2,.2))
    pb=RichEvidenceProvenance(observation_ref="b",photo_index=2,roi=(.3,.3,.4,.4))
    same=RichIdentityCue(identity_candidate_ref="idc",polarity="SAME",epistemic_level="CUE",cue="same cue",provenance=[pa,pb])
    distinct=RichIdentityCue(identity_candidate_ref="idc",polarity="DISTINCT",epistemic_level="CUE",cue="distinct cue",provenance=[pa,pb])
    assert build_identity_discriminant_producer_request(candidate,[a,b],[same]) is None
    request=build_identity_discriminant_producer_request(candidate,[a,b],[same,distinct])
    assert request is not None
    assert {cue.polarity for cue in request.cues}=={"SAME","DISTINCT"}
    assert request.open_alternatives==["same_physical_object","incompatible"]
    assert "same cue" in [cue.cue for cue in request.cues]


def test_064_discriminant_available_is_not_identity_resolution():
    a=_obs("a",1).model_copy(update={"region":NormalizedImageRegion(x0=.1,y0=.1,x1=.2,y1=.2)})
    b=_obs("b",2).model_copy(update={"region":NormalizedImageRegion(x0=.3,y0=.3,x1=.4,y1=.4)})
    candidate=IdentityCandidate(id="idc",observation_ids=["a","b"],status=IdentityStatus.CANDIDATE,certainty=CertaintyLevel.UNKNOWN,inquiry_state=IdentityInquiryState.OPEN_ALTERNATIVES,open_alternatives=[IdentityStatus.SAME_PHYSICAL_OBJECT,IdentityStatus.INCOMPATIBLE])
    pa=RichEvidenceProvenance(observation_ref="a",photo_index=1,roi=(.1,.1,.2,.2)); pb=RichEvidenceProvenance(observation_ref="b",photo_index=2,roi=(.3,.3,.4,.4))
    cues=[RichIdentityCue(identity_candidate_ref="idc",polarity=p,epistemic_level="CUE",cue=p,provenance=[pa,pb]) for p in ("SAME","DISTINCT")]
    request=build_identity_discriminant_producer_request(candidate,[a,b],cues)
    response=IdentityDiscriminantProducerResponse(request_id=request.request_id,identity_candidate_id="idc",status=IdentityDiscriminantProducerStatus.DISCRIMINANT_AVAILABLE,property_name="perceptual_discriminant_1",property_description="opaque documented property",source_ids_by_observation={"a":"identity-source-1","b":"identity-source-2"},outcomes_by_alternative={"same_physical_object":["outcome_alpha"],"incompatible":["outcome_beta"]},outcome_descriptions={"outcome_alpha":"observable alpha","outcome_beta":"observable beta"},required_source_ids=["identity-source-1","identity-source-2"])
    discriminant=import_identity_discriminant_producer_response(request,response)
    assert discriminant is not None
    assert candidate.status is IdentityStatus.CANDIDATE
    assert candidate.inquiry_state is IdentityInquiryState.OPEN_ALTERNATIVES


def test_065_no_reliable_identity_discriminant_persists_and_blocks_exact_reproposal():
    a=_obs("a",1).model_copy(update={"region":NormalizedImageRegion(x0=.1,y0=.1,x1=.2,y1=.2)})
    b=_obs("b",2).model_copy(update={"region":NormalizedImageRegion(x0=.3,y0=.3,x1=.4,y1=.4)})
    candidate=IdentityCandidate(
        id="idc", observation_ids=["a","b"], status=IdentityStatus.CANDIDATE,
        certainty=CertaintyLevel.UNKNOWN, inquiry_state=IdentityInquiryState.OPEN_ALTERNATIVES,
        open_alternatives=[IdentityStatus.SAME_PHYSICAL_OBJECT,IdentityStatus.INCOMPATIBLE],
    )
    pa=RichEvidenceProvenance(observation_ref="a",photo_index=1,roi=(.1,.1,.2,.2))
    pb=RichEvidenceProvenance(observation_ref="b",photo_index=2,roi=(.3,.3,.4,.4))
    cues=[
        RichIdentityCue(identity_candidate_ref="idc",polarity=p,epistemic_level="CUE",cue=p,provenance=[pa,pb])
        for p in ("SAME","DISTINCT")
    ]
    request=build_identity_discriminant_producer_request(candidate,[a,b],cues)
    assert request is not None
    response=IdentityDiscriminantProducerResponse(
        request_id=request.request_id, identity_candidate_id="idc",
        status=IdentityDiscriminantProducerStatus.NO_RELIABLE_DISCRIMINANT,
    )
    record=record_identity_discriminant_investigation(request,response)
    assert record is not None and record.outcome=="no_reliable_discriminant"
    workspace=MultiViewWorkspace(
        photo_count=2,
        pass_1=MultiViewPass(pass_number=1,observations=[a,b],identities=[candidate]),
        pass_2=MultiViewPass(pass_number=2),
        rich_identity_cues=cues,
        identity_discriminant_investigations=[record],
    )
    loaded=MultiViewWorkspace.model_validate_json(workspace.model_dump_json())
    loaded_candidate=loaded.pass_1.identities[0]
    assert loaded_candidate.status is IdentityStatus.CANDIDATE
    assert loaded_candidate.inquiry_state is IdentityInquiryState.OPEN_ALTERNATIVES
    assert set(loaded_candidate.open_alternatives)=={IdentityStatus.SAME_PHYSICAL_OBJECT,IdentityStatus.INCOMPATIBLE}
    assert loaded.identity_discriminants==[]
    assert len(loaded.identity_discriminant_investigations)==1
    assert build_identity_discriminant_producer_request(
        loaded_candidate, loaded.pass_1.observations, loaded.rich_identity_cues,
        loaded.identity_discriminant_investigations,
    ) is None


def test_065_negative_memory_is_exact_and_does_not_exhaust_changed_evidence():
    a=_obs("a",1).model_copy(update={"region":NormalizedImageRegion(x0=.1,y0=.1,x1=.2,y1=.2)})
    b=_obs("b",2).model_copy(update={"region":NormalizedImageRegion(x0=.3,y0=.3,x1=.4,y1=.4)})
    candidate=IdentityCandidate(
        id="idc",observation_ids=["a","b"],status=IdentityStatus.CANDIDATE,
        inquiry_state=IdentityInquiryState.OPEN_ALTERNATIVES,
        open_alternatives=[IdentityStatus.SAME_PHYSICAL_OBJECT,IdentityStatus.INCOMPATIBLE],
    )
    pa=RichEvidenceProvenance(observation_ref="a",photo_index=1,roi=(.1,.1,.2,.2))
    pb=RichEvidenceProvenance(observation_ref="b",photo_index=2,roi=(.3,.3,.4,.4))
    cues=[RichIdentityCue(identity_candidate_ref="idc",polarity=p,epistemic_level="CUE",cue=p,provenance=[pa,pb]) for p in ("SAME","DISTINCT")]
    request=build_identity_discriminant_producer_request(candidate,[a,b],cues)
    response=IdentityDiscriminantProducerResponse(
        request_id=request.request_id,identity_candidate_id="idc",
        status=IdentityDiscriminantProducerStatus.NO_RELIABLE_DISCRIMINANT,
    )
    record=record_identity_discriminant_investigation(request,response)
    changed=[cues[0].model_copy(update={"cue":"new independent SAME cue"}),cues[1]]
    assert build_identity_discriminant_producer_request(candidate,[a,b],changed,[record]) is not None


def test_065_exhausted_identity_uncertainty_keeps_dependency_but_has_no_impactful_investigation():
    a=_obs("a",1); b=_obs("b",2)
    candidate=IdentityCandidate(
        id="idc",observation_ids=["a","b"],status=IdentityStatus.CANDIDATE,
        inquiry_state=IdentityInquiryState.OPEN_ALTERNATIVES,
        open_alternatives=[IdentityStatus.SAME_PHYSICAL_OBJECT,IdentityStatus.INCOMPATIBLE],
    )
    uncertainty=detect_identity_uncertainties([candidate],[a,b])[0]
    dependencies=derive_identity_world_representation_dependencies([uncertainty])
    assessment=assess_investigation_impact(
        uncertainty,discriminating_testable=False,exhausted_or_redundant=True,
        dependencies=dependencies,
    )
    assert dependencies[0].downstream_ref=="physical-entity-partition:idc"
    assert assessment.blocked and not assessment.can_modify_shared_state
    assert select_impactful_investigations([assessment])==[]


def test_065_real_064_response_validates_and_persists_without_identity_promotion():
    fixture_dir=Path(__file__).parent/"fixtures"
    # Repository fixture path is stable from tests/vision.
    fixture_dir=Path(__file__).parents[1]/"fixtures"/"vision"
    request=IdentityDiscriminantProducerRequest.model_validate_json(
        (fixture_dir/"identity-discriminant-producer-request-064.json").read_text()
    )
    response=IdentityDiscriminantProducerResponse.model_validate_json(
        (fixture_dir/"identity-discriminant-producer-response-064.json").read_text()
    )
    record=record_identity_discriminant_investigation(request,response)
    assert record is not None
    observations=[
        LocalObservation(
            id=source.observation_ref,photo_index=source.photo_index,status=ClaimStatus.OBSERVED,
            visibility=VisibilityStatus.VISIBLE,region=source.region,statement="Source observation."
        ) for source in request.sources
    ]
    candidate=IdentityCandidate(
        id=request.identity_candidate_id,observation_ids=list(request.observation_ids),
        status=IdentityStatus.CANDIDATE,certainty=CertaintyLevel.UNKNOWN,
        inquiry_state=IdentityInquiryState.OPEN_ALTERNATIVES,
        open_alternatives=[IdentityStatus(value) for value in request.open_alternatives],
    )
    cues=[
        RichIdentityCue(
            identity_candidate_ref=request.identity_candidate_id,polarity=cue.polarity,
            epistemic_level=cue.epistemic_level,cue=cue.cue,provenance=cue.provenance,
        ) for cue in request.cues
    ]
    workspace=MultiViewWorkspace(
        photo_count=5,pass_1=MultiViewPass(pass_number=1,observations=observations,identities=[candidate]),
        pass_2=MultiViewPass(pass_number=2),rich_identity_cues=cues,
        identity_discriminant_investigations=[record],
    )
    loaded=MultiViewWorkspace.model_validate_json(workspace.model_dump_json())
    assert loaded.pass_1.identities[0].status is IdentityStatus.CANDIDATE
    assert loaded.identity_discriminants==[]
    assert build_identity_discriminant_producer_request(
        loaded.pass_1.identities[0],loaded.pass_1.observations,loaded.rich_identity_cues,
        loaded.identity_discriminant_investigations,
    ) is None


def _real_workspace_post_065():
    fixture_dir=Path(__file__).parents[1]/"fixtures"/"vision"
    response=RichVisualBootstrapResponse.model_validate_json(
        (fixture_dir/"visual-bootstrap-response-062.json").read_text()
    )
    request=build_rich_multiview_bootstrap_request(
        "real-house-5-rich-multiview-062",
        ["01-original.jpg","02-original.jpg","03-original.jpg","04-original.jpg","05-original.jpg"],
    )
    workspace=import_rich_visual_bootstrap_response(request,response)
    request064=IdentityDiscriminantProducerRequest.model_validate_json(
        (fixture_dir/"identity-discriminant-producer-request-064.json").read_text()
    )
    response064=IdentityDiscriminantProducerResponse.model_validate_json(
        (fixture_dir/"identity-discriminant-producer-response-064.json").read_text()
    )
    record=record_identity_discriminant_investigation(request064,response064)
    uncertainties=derive_existing_structured_uncertainties(workspace)
    dependencies=derive_identity_world_representation_dependencies(uncertainties)
    return workspace.model_copy(update={
        "identity_discriminant_investigations":[record],
        "reasoning_dependencies":dependencies,
    })


def test_066_graph_is_deterministic_projection_and_survives_workspace_reload():
    workspace=_real_workspace_post_065()
    graph=build_multiview_world_constraint_graph(workspace)
    loaded=MultiViewWorkspace.model_validate_json(workspace.model_dump_json())
    rebuilt=build_multiview_world_constraint_graph(loaded)
    assert graph.model_dump(mode="json")==rebuilt.model_dump(mode="json")
    assert "world_constraint_graph" not in MultiViewWorkspace.model_fields
    assert all(node.kind in {"observation","identity_candidate"} for node in graph.nodes)


def test_066_no_naive_identity_transitivity_or_same_only_competition():
    a,b,c=_obs("a",1),_obs("b",2),_obs("c",3)
    ab=IdentityCandidate(id="ab",observation_ids=["a","b"],status=IdentityStatus.CANDIDATE)
    bc=IdentityCandidate(id="bc",observation_ids=["b","c"],status=IdentityStatus.CANDIDATE)
    workspace=MultiViewWorkspace(
        photo_count=3,pass_1=MultiViewPass(pass_number=1,observations=[a,b,c],identities=[ab,bc]),
        pass_2=MultiViewPass(pass_number=2),
    )
    graph=build_multiview_world_constraint_graph(workspace)
    assert graph.competing_world_organizations==[]
    assert not any(set(item)=={"observation:a","observation:b","observation:c"} for item in graph.components)


def test_066_real_post_065_graph_metrics(capsys):
    graph=build_multiview_world_constraint_graph(_real_workspace_post_065())
    counts={
        "nodes":len(graph.nodes),
        "constraints":len(graph.constraints),
        "components":len(graph.components),
        "same":sum(x.kind=="SAME_CUE" for x in graph.constraints),
        "distinct":sum(x.kind=="DISTINCT_CUE" for x in graph.constraints),
        "relations":sum(x.kind=="PERCEPTUAL_RELATION" for x in graph.constraints),
        "ambiguities":sum(x.kind=="OPEN_UNCERTAINTY" for x in graph.constraints),
        "contradictions":len(graph.contradictions),
        "insufficient":len(graph.insufficiently_connected_components),
        "missing":len(graph.missing_constraints),
        "organizations":len(graph.competing_world_organizations),
    }
    print("WORLD_GRAPH_066_METRICS="+json.dumps(counts,sort_keys=True))
    assert counts["same"]==4
    assert counts["distinct"]==1
    assert counts["relations"]==3
    assert counts["contradictions"]==0
    assert counts["missing"]==1
    assert graph.missing_constraints[0].exhausted is True
    assert graph.missing_constraints[0].downstream_refs==[
        "physical-entity-partition:idc_sidewall_p2_p4"
    ]


def test_067_real_missing_constraint_has_properties_but_no_structured_discriminating_mapping(capsys):
    workspace=_real_workspace_post_065()
    graph=build_multiview_world_constraint_graph(workspace)
    missing=next(x for x in graph.missing_constraints if x.source_uncertainty_id=="identity-uncertainty-idc_sidewall_p2_p4")
    decision=plan_missing_constraint_perceptual_query(workspace,graph,missing)
    assert decision.state is MissingConstraintPlannerState.NO_DISCRIMINATING_MAPPING
    actual={(x.observation_ref,x.property_name) for x in decision.candidate_properties}
    assert actual=={
        ("obs_p2_side_wall","light_render"),("obs_p2_side_wall","upper_window"),
        ("obs_p4_rear_wall","upper_left_window"),("obs_p4_rear_wall","lower_right_window"),
    }
    assert set(decision.missing_structured_information)=={
        "cross_observation_property_correspondence",
        "property_outcome_mapping_to_competing_world_organizations",
    }
    assert len(decision.negative_memory_matches)==1
    print("PLANNER_067="+decision.model_dump_json())


def test_067_planner_is_deterministic_after_workspace_reload():
    workspace=_real_workspace_post_065()
    graph=build_multiview_world_constraint_graph(workspace)
    missing=graph.missing_constraints[0]
    first=plan_missing_constraint_perceptual_query(workspace,graph,missing)
    loaded=MultiViewWorkspace.model_validate_json(workspace.model_dump_json())
    rebuilt=build_multiview_world_constraint_graph(loaded)
    second=plan_missing_constraint_perceptual_query(loaded,rebuilt,rebuilt.missing_constraints[0])
    assert first.model_dump(mode="json")==second.model_dump(mode="json")


def test_067_negative_memory_signature_ignores_request_and_opaque_token_renaming_and_source_order():
    fixture_dir=Path(__file__).parents[1]/"fixtures"/"vision"
    request=IdentityDiscriminantProducerRequest.model_validate_json(
        (fixture_dir/"identity-discriminant-producer-request-064.json").read_text()
    )
    renamed=request.model_copy(update={
        "request_id":"renamed-request",
        "allowed_property_names":["renamed_property"],
        "allowed_outcomes":["renamed_a","renamed_b"],
        "sources":list(reversed(request.sources)),
        "instruction":"different wording must not make perceptual evidence new",
    })
    assert identity_discriminant_equivalence_signature(request)==identity_discriminant_equivalence_signature(renamed)


def test_067_no_properties_reports_no_structured_property_without_combinatorics():
    workspace=_real_workspace_post_065()
    refs={"obs_p2_side_wall","obs_p4_rear_wall"}
    p1=workspace.pass_1.model_copy(update={"observations":[
        x.model_copy(update={"observable_properties":None,"observed_property_states":None}) if x.id in refs else x
        for x in workspace.pass_1.observations
    ]})
    workspace=workspace.model_copy(update={"pass_1":p1})
    graph=build_multiview_world_constraint_graph(workspace)
    decision=plan_missing_constraint_perceptual_query(workspace,graph,graph.missing_constraints[0])
    assert decision.state is MissingConstraintPlannerState.NO_STRUCTURED_PROPERTY


def test_068_real_request_contains_exact_structured_properties_and_provenance(capsys):
    workspace=_real_workspace_post_065()
    graph=build_multiview_world_constraint_graph(workspace)
    missing=next(x for x in graph.missing_constraints if x.source_uncertainty_id=="identity-uncertainty-idc_sidewall_p2_p4")
    request=build_property_correspondence_producer_request(workspace,graph,missing)
    assert request is not None
    by_ref={x.observation_ref:x for x in request.sources}
    assert by_ref["obs_p2_side_wall"].property_names==["light_render","upper_window"]
    assert by_ref["obs_p4_rear_wall"].property_names==["lower_right_window","upper_left_window"]
    assert by_ref["obs_p2_side_wall"].roi==(0.36,0.16,0.86,0.62)
    assert by_ref["obs_p4_rear_wall"].roi==(0.34,0.06,0.72,0.42)
    assert by_ref["obs_p2_side_wall"].visibility is VisibilityStatus.VISIBLE
    assert by_ref["obs_p4_rear_wall"].visibility is VisibilityStatus.VISIBLE
    assert {x.polarity for x in request.cues}=={"SAME","DISTINCT"}
    print("REQUEST_068="+request.model_dump_json())


def test_068_response_cannot_invent_property_or_provenance():
    workspace=_real_workspace_post_065()
    graph=build_multiview_world_constraint_graph(workspace)
    request=build_property_correspondence_producer_request(workspace,graph,graph.missing_constraints[0])
    assert request is not None
    a,b=request.sources
    response=PropertyCorrespondenceProducerResponse.model_validate({
        "request_id":request.request_id,"missing_constraint_id":request.missing_constraint_id,
        "identity_candidate_id":request.identity_candidate_id,"status":"CORRESPONDENCE_AVAILABLE",
        "correspondences":[{
            "observation_ref_a":a.observation_ref,"property_name_a":"invented_property",
            "observation_ref_b":b.observation_ref,"property_name_b":b.property_names[0],
            "provenance_a":{"observation_ref":a.observation_ref,"property_name":"invented_property","source_id":a.source_id,"photo_index":a.photo_index,"roi":a.roi},
            "provenance_b":{"observation_ref":b.observation_ref,"property_name":b.property_names[0],"source_id":b.source_id,"photo_index":b.photo_index,"roi":b.roi},
            "epistemic_level":"COMPARABLE_VISUAL_PROPERTY"}]})
    with pytest.raises(ValueError,match="unavailable property"):
        validate_property_correspondence_response(request,response)


def test_068_inconclusive_response_has_no_correspondence_payload():
    workspace=_real_workspace_post_065()
    graph=build_multiview_world_constraint_graph(workspace)
    request=build_property_correspondence_producer_request(workspace,graph,graph.missing_constraints[0])
    response=PropertyCorrespondenceProducerResponse(
        request_id=request.request_id,missing_constraint_id=request.missing_constraint_id,
        identity_candidate_id=request.identity_candidate_id,status=PropertyCorrespondenceProducerStatus.NO_RELIABLE_CORRESPONDENCE,
        correspondences=None)
    validate_property_correspondence_response(request,response)


def _real_workspace_post_068():
    workspace=_real_workspace_post_065()
    graph=build_multiview_world_constraint_graph(workspace)
    missing=next(x for x in graph.missing_constraints if x.source_uncertainty_id=="identity-uncertainty-idc_sidewall_p2_p4")
    request=build_property_correspondence_producer_request(workspace,graph,missing)
    fixture_dir=Path(__file__).parents[1]/"fixtures"/"vision"
    response=PropertyCorrespondenceProducerResponse.model_validate_json(
        (fixture_dir/"property-correspondence-producer-response-068.json").read_text()
    )
    records=import_property_correspondence_response(request,response)
    return workspace.model_copy(update={"property_correspondences":records})


def test_069_real_068_response_ingests_without_identity_promotion_and_survives_reload():
    workspace=_real_workspace_post_068()
    assert len(workspace.property_correspondences)==1
    record=workspace.property_correspondences[0]
    assert record.correspondence.epistemic_level=="COMPARABLE_VISUAL_PROPERTY"
    candidate=next(x for x in [*workspace.pass_1.identities,*workspace.pass_2.identities] if x.id=="idc_sidewall_p2_p4")
    assert candidate.inquiry_state is IdentityInquiryState.OPEN_ALTERNATIVES
    loaded=MultiViewWorkspace.model_validate_json(workspace.model_dump_json())
    assert loaded.property_correspondences==workspace.property_correspondences


def test_069_planner_replay_leaves_only_outcome_mapping_missing():
    workspace=_real_workspace_post_068()
    graph=build_multiview_world_constraint_graph(workspace)
    missing=next(x for x in graph.missing_constraints if x.source_uncertainty_id=="identity-uncertainty-idc_sidewall_p2_p4")
    decision=plan_missing_constraint_perceptual_query(workspace,graph,missing)
    assert decision.state is MissingConstraintPlannerState.NO_DISCRIMINATING_MAPPING
    assert decision.missing_structured_information==["property_outcome_mapping_to_competing_world_organizations"]


def test_069_mapping_request_is_new_structured_question_not_equivalent_to_064(capsys):
    workspace=_real_workspace_post_068()
    graph=build_multiview_world_constraint_graph(workspace)
    missing=next(x for x in graph.missing_constraints if x.source_uncertainty_id=="identity-uncertainty-idc_sidewall_p2_p4")
    request=build_property_outcome_mapping_request(workspace,graph,missing)
    assert request is not None
    assert request.correspondence.property_name_a=="upper_window"
    assert request.correspondence.property_name_b=="upper_left_window"
    assert set(request.competing_organizations)=={"same_physical_object","incompatible"}
    assert len(request.exhausted_discriminant_signatures)==1
    assert mapping_request_equivalent_to_exhausted_identity_discriminant(request,workspace) is False
    print("REQUEST_069="+request.model_dump_json())


def test_069_mapping_response_fail_closed_requires_distinct_complete_vectors():
    workspace=_real_workspace_post_068()
    graph=build_multiview_world_constraint_graph(workspace)
    request=build_property_outcome_mapping_request(workspace,graph,graph.missing_constraints[0])
    bad=PropertyOutcomeMappingResponse.model_validate({
      "request_id":request.request_id,"missing_constraint_id":request.missing_constraint_id,
      "identity_candidate_id":request.identity_candidate_id,"status":"MAPPING_AVAILABLE",
      "mappings":[
        {"outcome_token":"observable_outcome_1","compatibility_by_organization":{"same_physical_object":"COMPATIBLE","incompatible":"NON_DISCRIMINATING"}},
        {"outcome_token":"observable_outcome_2","compatibility_by_organization":{"same_physical_object":"COMPATIBLE","incompatible":"NON_DISCRIMINATING"}}
      ]})
    with pytest.raises(ValueError,match="different organization compatibility"):
        validate_property_outcome_mapping_response(request,bad)


def _real_workspace_post_069():
    workspace=_real_workspace_post_068()
    graph=build_multiview_world_constraint_graph(workspace)
    missing=next(x for x in graph.missing_constraints if x.source_uncertainty_id=="identity-uncertainty-idc_sidewall_p2_p4")
    request=build_property_outcome_mapping_request(workspace,graph,missing)
    fixture_dir=Path(__file__).parents[1]/"fixtures"/"vision"
    response=PropertyOutcomeMappingResponse.model_validate_json((fixture_dir/"property-outcome-mapping-producer-response-069.json").read_text())
    record=record_property_outcome_mapping_investigation(request,response)
    return workspace.model_copy(update={"property_outcome_mapping_investigations":[record]})


def test_070_negative_069_persists_without_identity_resolution_after_reload():
    workspace=_real_workspace_post_069()
    assert len(workspace.property_outcome_mapping_investigations)==1
    assert workspace.property_outcome_mapping_investigations[0].outcome=="NO_RELIABLE_MAPPING"
    candidate=next(x for x in [*workspace.pass_1.identities,*workspace.pass_2.identities] if x.id=="idc_sidewall_p2_p4")
    assert candidate.inquiry_state is IdentityInquiryState.OPEN_ALTERNATIVES
    loaded=MultiViewWorkspace.model_validate_json(workspace.model_dump_json())
    assert loaded.property_outcome_mapping_investigations==workspace.property_outcome_mapping_investigations
    assert loaded.property_correspondences==workspace.property_correspondences


def test_070_world_milestone_rebuild_and_diagnostic_are_truth_preserving(capsys):
    workspace=_real_workspace_post_069()
    loaded=MultiViewWorkspace.model_validate_json(workspace.model_dump_json())
    graph=build_multiview_world_constraint_graph(loaded)
    html=render_multiview_world_diagnostic_html(loaded,graph)
    assert "pas Scene 3D" in html
    assert "obs_p2_side_wall" in html and "obs_p4_rear_wall" in html
    assert "COMPARABLE_VISUAL_PROPERTY" in html
    assert "NO_RELIABLE_MAPPING" in html
    summary={
      "observations":len([*loaded.pass_1.observations,*loaded.pass_2.observations]),
      "identity_candidates":len([*loaded.pass_1.identities,*loaded.pass_2.identities]),
      "relations":len(loaded.rich_relation_evidence),
      "correspondences":len(loaded.property_correspondences),
      "identity_negative_memories":len(loaded.identity_discriminant_investigations),
      "mapping_negative_memories":len(loaded.property_outcome_mapping_investigations),
      "nodes":len(graph.nodes),"constraints":len(graph.constraints),"components":len(graph.components),
      "open_uncertainties":len([x for x in derive_existing_structured_uncertainties(loaded) if x.resolved_state is None and len(x.open_alternatives)>=2]),
      "competing_world_organizations":len(graph.competing_world_organizations),
      "missing_constraints":len(graph.missing_constraints),"contradictions":len(graph.contradictions),
      "insufficient_components":len(graph.insufficiently_connected_components),
    }
    print("SUMMARY_070="+json.dumps(summary,sort_keys=True))
    print("HTML_070="+base64.b64encode(html.encode()).decode())


def test_071_fragmentation_audit_and_global_request(capsys):
    workspace=_real_workspace_post_069()
    loaded=MultiViewWorkspace.model_validate_json(workspace.model_dump_json())
    graph=build_multiview_world_constraint_graph(loaded)
    audit=audit_workspace_fragmentation(loaded,graph)
    assert audit["count"]==11
    assert sum(1 for x in audit["components"] if x["has_interview_candidate"])==0
    assert sum(1 for x in audit["components"] if x["has_local_relation"])==1
    assert all(x["all_have_properties"] for x in audit["components"])
    assert all(x["all_have_roi"] for x in audit["components"])
    request=build_global_multiview_connectivity_request(loaded,graph)
    assert request is not None
    assert request.photo_indexes==[1,2,3,4,5]
    assert sum(x.priority=="FRAGMENTED" for x in request.sources)==12
    assert sum(x.priority=="ANCHOR" for x in request.sources)==10
    assert len(request.exhausted_investigations)==2
    assert request.existing_property_correspondences[0]["epistemic_level"]=="COMPARABLE_VISUAL_PROPERTY"
    print("AUDIT_071="+json.dumps(audit,sort_keys=True))
    print("REQUEST_071="+request.model_dump_json())


def test_071_ingestion_audit_preserves_category_but_loses_property_values():
    fixture_dir=Path(__file__).parents[1]/"fixtures"/"vision"
    rich=RichVisualBootstrapResponse.model_validate_json((fixture_dir/"visual-bootstrap-response-062.json").read_text())
    workspace=_real_workspace_post_065()
    source={x.observation_id:x for x in rich.observations}
    imported={x.id:x for x in workspace.pass_1.observations}
    assert all(imported[k].proposed_category==v.category_proposal for k,v in source.items())
    assert all(imported[k].observable_properties==set(v.observable_properties) for k,v in source.items())
    assert any(v.observable_properties for v in source.values())


def _metrics_072(workspace):
    graph=build_multiview_world_constraint_graph(workspace)
    observations=[*workspace.pass_1.observations,*workspace.pass_2.observations]
    identities=[*workspace.pass_1.identities,*workspace.pass_2.identities]
    return {
      "observations":len(observations),"identity_candidates":len(identities),
      "identity_cues":len(workspace.rich_identity_cues),
      "property_correspondences":len(workspace.property_correspondences),
      "perceptual_relations":len(workspace.rich_relation_evidence),
      "continuities":sum(1 for x in observations if (x.observed_property_states or {}).get("continuation") is not None),
      "ambiguities":len(workspace.rich_perceptual_ambiguities),
      "nodes":len(graph.nodes),"constraints":len(graph.constraints),"components":len(graph.components),
      "insufficiently_connected_components":len(graph.insufficiently_connected_components),
      "open_uncertainties":len([x for x in derive_existing_structured_uncertainties(workspace) if x.resolved_state is None and len(x.open_alternatives)>=2]),
      "contradictions":len(graph.contradictions),
    },graph


def test_072_real_response_strict_ingestion_save_reload_and_deltas(capsys):
    fixture_dir=Path(__file__).parents[1]/"fixtures"/"vision"
    before=_real_workspace_post_069()
    before_metrics,before_graph=_metrics_072(before)
    request=build_global_multiview_connectivity_request(before,before_graph)
    response=GlobalMultiviewConnectivityResponse.model_validate_json((fixture_dir/"global-multiview-connectivity-response-071.json").read_text())
    validation=validate_global_multiview_connectivity_response(request,response)
    assert validation["rejected"]==[]
    assert [len(validation["accepted"][x]) for x in ["identity_candidates","identity_cues","property_correspondences","perceptual_relations","continuities","perceptual_ambiguities"]]==[0,0,3,8,2,0]
    after,report=ingest_global_multiview_connectivity_response(before,request,response)
    assert len(report["new_information"]["property_correspondences"])==3
    assert len(report["new_information"]["perceptual_relations"])==8
    assert report["new_information"]["continuities"]==[]
    assert len(report["already_known_information"]["continuities"])==2
    reloaded=MultiViewWorkspace.model_validate_json(after.model_dump_json())
    after_metrics,after_graph=_metrics_072(reloaded)
    assert after_metrics["property_correspondences"]==4
    assert after_metrics["perceptual_relations"]==11
    assert after_metrics["continuities"]==2
    assert len(reloaded.pass_1.identities)+len(reloaded.pass_2.identities)==4
    assert all(x.status is not IdentityStatus.SAME_PHYSICAL_OBJECT for x in [*reloaded.pass_1.identities,*reloaded.pass_2.identities])
    print("BEFORE_072="+json.dumps(before_metrics,sort_keys=True))
    print("AFTER_072="+json.dumps(after_metrics,sort_keys=True))
    print("DELTAS_072="+json.dumps({k:after_metrics[k]-before_metrics[k] for k in before_metrics},sort_keys=True))
    print("COMPONENTS_BEFORE_072="+json.dumps(before_graph.components,sort_keys=True))
    print("COMPONENTS_AFTER_072="+json.dumps(after_graph.components,sort_keys=True))
    print("INGEST_072="+json.dumps(report,default=lambda x:x.model_dump(mode="json") if hasattr(x,"model_dump") else str(x),sort_keys=True))


def test_072_rejects_invalid_individual_item_without_rejecting_batch():
    before=_real_workspace_post_069(); _,graph=_metrics_072(before)
    request=build_global_multiview_connectivity_request(before,graph)
    valid=GlobalMultiviewConnectivityResponse(request_id=request.request_id,status="CONNECTIVITY_EVIDENCE_AVAILABLE")
    bad=valid.model_copy(update={"perceptual_relations":[{
      "subject_ref":"obs_p1_front_wall","relation_token":"CONNECTED_TO","object_ref":"obs_p2_side_wall",
      "epistemic_level":"OBSERVED","provenance":[{"observation_ref":"obs_p1_front_wall","photo_index":1,"roi":[0.03,0.28,0.97,0.72]}]}]})
    bad=GlobalMultiviewConnectivityResponse.model_validate(bad.model_dump())
    result=validate_global_multiview_connectivity_response(request,bad)
    assert len(result["rejected"])==1
    assert result["accepted"]["perceptual_relations"]==[]


def test_072_photo_level_perceptual_graph_spans_all_five_views_without_identity_promotion():
    fixture_dir=Path(__file__).parents[1]/"fixtures"/"vision"
    before=_real_workspace_post_069(); _,g0=_metrics_072(before)
    request=build_global_multiview_connectivity_request(before,g0)
    response=GlobalMultiviewConnectivityResponse.model_validate_json((fixture_dir/"global-multiview-connectivity-response-071.json").read_text())
    after,_=ingest_global_multiview_connectivity_response(before,request,response)
    reloaded=MultiViewWorkspace.model_validate_json(after.model_dump_json())
    _,graph=_metrics_072(reloaded)
    photo_by_node={f"observation:{x.id}":x.photo_index for x in [*reloaded.pass_1.observations,*reloaded.pass_2.observations]}
    edges=set()
    for constraint in graph.constraints:
        photos=sorted({photo_by_node[x] for x in constraint.node_refs if x in photo_by_node})
        for a in photos:
            for b in photos:
                if a<b: edges.add((a,b))
    reached={1}
    changed=True
    while changed:
        changed=False
        for a,b in edges:
            if a in reached and b not in reached: reached.add(b); changed=True
            if b in reached and a not in reached: reached.add(a); changed=True
    assert reached=={1,2,3,4,5}
    assert (1,2) in edges and (1,5) in edges
    assert len(graph.insufficiently_connected_components)==2
    weak_obs={n for comp in graph.insufficiently_connected_components for n in comp}
    assert weak_obs=={"observation:obs_p3_tree","observation:obs_p5_near_window","observation:obs_p5_side_wall"}
    print("PHOTO_EDGES_072="+json.dumps(sorted(edges)))
    print("PHOTO_REACH_072="+json.dumps(sorted(reached)))
    print("WEAK_COMPONENTS_072="+json.dumps(graph.insufficiently_connected_components,sort_keys=True))


def _real_workspace_post_071_for_073():
    fixture_dir=Path(__file__).parents[1]/"fixtures"/"vision"
    before=_real_workspace_post_069(); graph=build_multiview_world_constraint_graph(before)
    request=build_global_multiview_connectivity_request(before,graph)
    response=GlobalMultiviewConnectivityResponse.model_validate_json((fixture_dir/"global-multiview-connectivity-response-071.json").read_text())
    after,_=ingest_global_multiview_connectivity_response(before,request,response)
    return MultiViewWorkspace.model_validate_json(after.model_dump_json())


def test_073_property_values_are_preserved_at_first_responsible_ingestion():
    fixture_dir=Path(__file__).parents[1]/"fixtures"/"vision"
    response=RichVisualBootstrapResponse.model_validate_json((fixture_dir/"visual-bootstrap-response-062.json").read_text())
    workspace=ingest_rich_visual_bootstrap_response(response)
    observations={x.id:x for x in workspace.pass_1.observations}
    assert observations["obs_p1_front_wall"].observable_property_values=={"light_render":True,"multiple_openings":True}
    assert observations["obs_p1_front_wall"].observable_properties=={"light_render","multiple_openings"}
    assert observations["obs_p1_front_wall"].proposed_category=="large pale wall surface"
    assert observations["obs_p1_front_wall"].certainty.category is CertaintyLevel.PLAUSIBLE


def test_073_world_hypothesis_is_deterministic_disposable_and_preserves_open_branches(capsys):
    workspace=_real_workspace_post_071_for_073()
    graph=build_multiview_world_constraint_graph(workspace)
    h1=build_world_hypothesis(workspace,graph)
    reloaded=MultiViewWorkspace.model_validate_json(workspace.model_dump_json())
    h2=build_world_hypothesis(reloaded,build_multiview_world_constraint_graph(reloaded))
    assert h1==h2
    assert "world_hypothesis" not in MultiViewWorkspace.model_fields
    assert len(h1.organizations)==2
    assert {tuple(sorted(x.branch_assumptions.items())) for x in h1.organizations}=={
      (("identity-uncertainty-idc_sidewall_p2_p4","same_physical_object"),),
      (("identity-uncertainty-idc_sidewall_p2_p4","incompatible"),)}
    assert h1.identity_candidate_refs==["idc_box_p2_p3","idc_sidewall_p2_p4","idc_stair_p2_p4","idc_upperwindow_p2_p4"]
    assert h1.open_uncertainty_refs==["identity-uncertainty-idc_sidewall_p2_p4"]
    assert h1.property_values_available is True
    expected_unattached=["obs_p3_tree","obs_p5_near_window","obs_p5_side_wall"]
    assert all(x.unattached_observation_refs==expected_unattached for x in h1.organizations)
    assert all(len(x.main_world_observation_refs)==19 for x in h1.organizations)
    assert len(h1.semantic_proposals)==22
    assert all(x.epistemic_level=="CANDIDATE" for x in h1.semantic_proposals)
    levels={a.epistemic_level for a in h1.organizations[0].assertions}
    assert {"OBSERVED","CUE","COMPARABLE_VISUAL_PROPERTY","CANDIDATE","AMBIGUOUS","EXHAUSTED"}.issubset(levels)
    assert all(a.epistemic_level!="OBSERVED" for a in h1.organizations[0].assertions if a.evidence_type=="IDENTITY_CANDIDATE")
    html=render_world_hypothesis_html(h1)
    assert "MONDE CENTRAL" in html and "Organisations concurrentes" in html and "Aucune géométrie 3D" in html
    print("WORLD_HYPOTHESIS_073="+h1.model_dump_json())
    print("HTML_073_B64="+__import__("base64").b64encode(html.encode()).decode())


def test_073_architectural_organization_readiness_is_supported_by_explicit_structure(capsys):
    workspace=_real_workspace_post_071_for_073(); graph=build_multiview_world_constraint_graph(workspace); h=build_world_hypothesis(workspace,graph)
    relations={(x.subject_ref,x.relation_token,x.object_ref) for x in workspace.rich_relation_evidence}
    categories={x.observation_ref:x.proposed_category for x in h.semantic_proposals}
    # Mechanical readiness: all views span the evidence network, a large attached core exists,
    # and explicit observed containment/front relations organize proposed surface/opening/platform semantics.
    photos=set(h.photo_indexes)
    core=set(h.organizations[0].main_world_observation_refs)
    surface_refs={k for k,v in categories.items() if "surface" in v}
    opening_refs={k for k,v in categories.items() if "opening" in v}
    explicit_surface_opening=any(s in opening_refs and o in surface_refs and r=="VISIBLE_WITHIN" for s,r,o in relations)
    explicit_platform_surface=any(categories.get(s,"").startswith("raised platform") and o in surface_refs and r=="VISUALLY_IN_FRONT_OF" for s,r,o in relations)
    ready=(photos=={1,2,3,4,5} and len(core)>=15 and explicit_surface_opening and explicit_platform_surface and not graph.contradictions)
    assert ready
    print("ARCHITECTURAL_ORGANIZATION_073=READY")
    print("ARCHITECTURAL_MECHANICS_073="+json.dumps({"photos":sorted(photos),"main_world_observations":len(core),"unattached":h.organizations[0].unattached_observation_refs,"explicit_surface_opening":explicit_surface_opening,"explicit_platform_surface":explicit_platform_surface,"contradictions":len(graph.contradictions)},sort_keys=True))
