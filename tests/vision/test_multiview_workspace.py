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
