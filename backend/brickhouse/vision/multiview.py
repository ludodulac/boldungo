"""Structured pre-Survey workspace for auditable multi-view photo reasoning.

This is deliberately not ArchitecturalSurvey and contains no free-form chain of
thought.  It records only reviewable claims derived from pixels before factual
Survey fusion or geometric reconstruction.
"""
from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from brickhouse.survey.models import NormalizedImageRegion


class ClaimStatus(str, Enum):
    OBSERVED = "observed"
    INFERRED = "inferred"
    UNKNOWN = "unknown"


class VisibilityStatus(str, Enum):
    VISIBLE = "visible"
    ABSENT = "absent"
    NON_VISIBLE = "non_visible"
    OCCLUDED = "occluded"


class IdentityStatus(str, Enum):
    SAME_PHYSICAL_OBJECT = "same_physical_object"
    LIKELY_SAME = "likely_same"
    UNRESOLVED = "unresolved"
    INCOMPATIBLE = "incompatible"


class CertaintyLevel(str, Enum):
    CERTAIN = "certain"
    PLAUSIBLE = "plausible"
    UNPROVEN = "unproven"
    UNKNOWN = "unknown"


class AspectCertainty(BaseModel):
    existence: CertaintyLevel = CertaintyLevel.UNKNOWN
    category: CertaintyLevel = CertaintyLevel.UNKNOWN
    identity: CertaintyLevel = CertaintyLevel.UNKNOWN
    spatial_relation: CertaintyLevel = CertaintyLevel.UNKNOWN
    topology: CertaintyLevel = CertaintyLevel.UNKNOWN
    metric: CertaintyLevel = CertaintyLevel.UNKNOWN


class LocalObservation(BaseModel):
    id: str = Field(min_length=1)
    photo_index: int = Field(ge=1)
    status: ClaimStatus
    visibility: VisibilityStatus
    region: NormalizedImageRegion | None = None
    qualitative_position: str | None = None
    proposed_category: str | None = None
    statement: str = Field(min_length=1)
    certainty: AspectCertainty = Field(default_factory=AspectCertainty)

    @model_validator(mode="after")
    def validate_visibility(self) -> "LocalObservation":
        if self.status is ClaimStatus.OBSERVED and self.visibility is not VisibilityStatus.VISIBLE:
            raise ValueError("observed local claims require visibility='visible'")
        if self.visibility in {VisibilityStatus.NON_VISIBLE, VisibilityStatus.OCCLUDED}:
            if self.certainty.existence is CertaintyLevel.CERTAIN and self.status is ClaimStatus.OBSERVED:
                raise ValueError("non-visible/occluded content cannot be marked observed")
        return self


class ViewAssessment(BaseModel):
    photo_index: int = Field(ge=1)
    subject_hint: str = Field(min_length=1)
    visibility: VisibilityStatus
    statement: str = Field(min_length=1)


class IdentityCandidate(BaseModel):
    id: str = Field(min_length=1)
    observation_ids: list[str] = Field(min_length=2)
    status: IdentityStatus
    corroborating_photo_indexes: list[int] = Field(default_factory=list)
    conflicting_photo_indexes: list[int] = Field(default_factory=list)
    certainty: CertaintyLevel = CertaintyLevel.UNKNOWN

    @model_validator(mode="after")
    def validate_identity(self) -> "IdentityCandidate":
        if len(self.observation_ids) != len(set(self.observation_ids)):
            raise ValueError("identity observation IDs must be unique")
        if self.status is IdentityStatus.SAME_PHYSICAL_OBJECT and self.certainty not in {
            CertaintyLevel.CERTAIN,
            CertaintyLevel.PLAUSIBLE,
        }:
            raise ValueError("same physical object identity needs explicit support")
        if self.status is IdentityStatus.INCOMPATIBLE and self.certainty is CertaintyLevel.CERTAIN:
            return self
        return self


class ArchitecturalRelationCandidate(BaseModel):
    id: str = Field(min_length=1)
    subject_ref: str = Field(min_length=1)
    object_ref: str = Field(min_length=1)
    relation: str = Field(min_length=1)
    status: ClaimStatus = ClaimStatus.INFERRED
    certainty: CertaintyLevel = CertaintyLevel.UNKNOWN
    supporting_photo_indexes: list[int] = Field(default_factory=list)


class Contradiction(BaseModel):
    id: str = Field(min_length=1)
    claim_refs: list[str] = Field(min_length=2)
    statement: str = Field(min_length=1)
    photo_indexes: list[int] = Field(min_length=1)
    resolved: bool = False
    resolution: str | None = None

    @model_validator(mode="after")
    def validate_resolution(self) -> "Contradiction":
        if self.resolved and not self.resolution:
            raise ValueError("resolved contradiction requires a resolution")
        if not self.resolved and self.resolution is not None:
            raise ValueError("unresolved contradiction cannot carry a resolution")
        return self


class HypothesisClaim(BaseModel):
    """Minimal machine-readable relation claim; relation semantics are rule-driven."""

    subject_ref: str = Field(min_length=1)
    relation: str = Field(min_length=1)
    object_ref: str | None = None


class OpenHypothesis(BaseModel):
    id: str = Field(min_length=1)
    subject_refs: list[str] = Field(min_length=1)
    statement: str = Field(min_length=1)
    competing_with: list[str] = Field(default_factory=list)
    certainty: CertaintyLevel = CertaintyLevel.UNPROVEN
    supporting_photo_indexes: list[int] = Field(default_factory=list)
    claim: HypothesisClaim | None = None


class InquiryState(str, Enum):
    OPEN = "open"
    RESOLVED = "resolved"
    IRREDUCIBLE_UNKNOWN = "irreducible_unknown"


class ObservableProperty(BaseModel):
    """Machine-readable observable outcome; absent means no visual consequence is defined."""

    name: str = Field(min_length=1)
    value: str = Field(min_length=1)


class ObservablePrediction(BaseModel):
    """Observable consequence of an existing OpenHypothesis, not an observation."""

    id: str = Field(min_length=1)
    hypothesis_id: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    observable_properties: list[ObservableProperty] = Field(default_factory=list)


class ObservabilityCondition(BaseModel):
    """Conditions required before an expected world outcome is visually testable."""

    region_in_frame: bool = True
    non_occluded: bool = True
    sufficient_visibility: bool = True


def derive_observable_prediction(
    hypothesis: OpenHypothesis,
) -> ObservablePrediction | None:
    """Apply the one generic Experiment-010 continuity rule family."""

    if hypothesis.claim is None:
        return None

    outcomes = {
        "CONTINUES": "visible",
        "TERMINATES": "absent",
    }
    outcome = outcomes.get(hypothesis.claim.relation)
    if outcome is None:
        return None

    condition = ObservabilityCondition()
    return ObservablePrediction(
        id=f"derived-{hypothesis.id}",
        hypothesis_id=hypothesis.id,
        statement=(
            "When the relevant region is in frame, non-occluded, and sufficiently "
            f"visible, compatible continuation is expected to be {outcome}."
        ),
        observable_properties=[
            ObservableProperty(name="continuation", value=outcome),
            ObservableProperty(
                name="observability_required",
                value=(
                    "in_frame+non_occluded+sufficient_visibility"
                    if condition.region_in_frame
                    and condition.non_occluded
                    and condition.sufficient_visibility
                    else "unspecified"
                ),
            ),
        ],
    )


class DiscriminatingProperty(BaseModel):
    """One structured property whose predicted outcomes differ across hypotheses."""

    property_name: str = Field(min_length=1)
    expected_outcomes: dict[str, str] = Field(min_length=2)


class DiscriminatingQuestion(BaseModel):
    """Machine-first question derived from divergent observable predictions."""

    hypothesis_ids: list[str] = Field(min_length=2)
    prediction_ids: list[str] = Field(min_length=2)
    discriminants: list[DiscriminatingProperty] = Field(min_length=1)
    evidence_needed: list[str] = Field(min_length=1)
    human_readable_question: str = Field(min_length=1)


def derive_discriminating_question(
    predictions: list[ObservablePrediction],
) -> DiscriminatingQuestion | None:
    """Derive visual discriminants from structured outcomes, never prediction prose."""

    by_hypothesis: dict[str, ObservablePrediction] = {}
    for prediction in predictions:
        if prediction.hypothesis_id in by_hypothesis:
            raise ValueError("provide exactly one prediction per competing hypothesis")
        by_hypothesis[prediction.hypothesis_id] = prediction
    if len(by_hypothesis) < 2:
        raise ValueError("at least two competing hypothesis predictions are required")

    property_maps = {
        hypothesis_id: {item.name: item.value for item in prediction.observable_properties}
        for hypothesis_id, prediction in by_hypothesis.items()
    }
    common_properties = set.intersection(*(set(items) for items in property_maps.values()))
    discriminants: list[DiscriminatingProperty] = []
    for property_name in sorted(common_properties):
        outcomes = {
            hypothesis_id: property_maps[hypothesis_id][property_name]
            for hypothesis_id in by_hypothesis
        }
        if len(set(outcomes.values())) > 1:
            discriminants.append(
                DiscriminatingProperty(
                    property_name=property_name,
                    expected_outcomes=outcomes,
                )
            )

    if not discriminants:
        return None

    names = [item.property_name for item in discriminants]
    return DiscriminatingQuestion(
        hypothesis_ids=list(by_hypothesis),
        prediction_ids=[item.id for item in by_hypothesis.values()],
        discriminants=discriminants,
        evidence_needed=names,
        human_readable_question=(
            "What observable outcome is present for " + ", ".join(names) + "?"
        ),
    )


class DiscriminatingTest(BaseModel):
    """One photo region where competing predictions are expected to differ."""

    id: str = Field(min_length=1)
    photo_index: int = Field(ge=1)
    region: NormalizedImageRegion
    prediction_ids: list[str] = Field(min_length=2)
    evidence_sought: str = Field(min_length=1)


class InquiryTestResult(BaseModel):
    """Recorded inspection result; absence is evidence only under safe visibility."""

    test_id: str = Field(min_length=1)
    inspected: bool
    region_in_frame: bool
    visibility: VisibilityStatus
    sufficient_visibility: bool
    statement: str = Field(min_length=1)
    compatible_prediction_ids: list[str] = Field(default_factory=list)
    discriminating: bool = False

    @model_validator(mode="after")
    def validate_discriminating_absence(self) -> "InquiryTestResult":
        if self.discriminating and (
            not self.inspected or not self.region_in_frame or not self.sufficient_visibility
        ):
            raise ValueError(
                "discriminating evidence requires an inspected, in-frame, sufficiently visible ROI"
            )
        if self.discriminating and self.visibility in {
            VisibilityStatus.OCCLUDED,
            VisibilityStatus.NON_VISIBLE,
        }:
            raise ValueError("occluded/non-visible ROI cannot provide discriminating evidence")
        return self


class VisualInquiry(BaseModel):
    """Minimal executable inquiry attached to the existing pre-Survey workspace."""

    id: str = Field(min_length=1)
    question: str = Field(min_length=1)
    hypothesis_ids: list[str] = Field(min_length=2)
    predictions: list[ObservablePrediction] = Field(min_length=2)
    tests: list[DiscriminatingTest] = Field(min_length=1)
    test_results: list[InquiryTestResult] = Field(default_factory=list)
    state: InquiryState = InquiryState.OPEN
    viable_hypothesis_ids: list[str] = Field(default_factory=list)
    resolved_hypothesis_id: str | None = None
    resolution_test_id: str | None = None
    information_missing: str | None = None
    stop_reason: str | None = None

    @model_validator(mode="after")
    def validate_contract(self) -> "VisualInquiry":
        hypothesis_ids = set(self.hypothesis_ids)
        if len(hypothesis_ids) != len(self.hypothesis_ids):
            raise ValueError("inquiry hypothesis IDs must be unique")
        if not self.viable_hypothesis_ids:
            self.viable_hypothesis_ids = list(self.hypothesis_ids)
        if not set(self.viable_hypothesis_ids).issubset(hypothesis_ids):
            raise ValueError("viable hypotheses must belong to the inquiry")
        prediction_ids = {item.id for item in self.predictions}
        if len(prediction_ids) != len(self.predictions):
            raise ValueError("prediction IDs must be unique")
        if any(item.hypothesis_id not in hypothesis_ids for item in self.predictions):
            raise ValueError("prediction references hypothesis outside inquiry")
        for test in self.tests:
            if not set(test.prediction_ids).issubset(prediction_ids):
                raise ValueError("test references prediction outside inquiry")
        test_ids = {item.id for item in self.tests}
        for result in self.test_results:
            if result.test_id not in test_ids:
                raise ValueError("test result references unknown inquiry test")
            if not set(result.compatible_prediction_ids).issubset(prediction_ids):
                raise ValueError("test result references unknown prediction")
        if self.state is InquiryState.RESOLVED:
            if self.resolved_hypothesis_id not in hypothesis_ids or not self.resolution_test_id:
                raise ValueError("resolved inquiry requires a surviving hypothesis and resolution test")
            resolution_results = [
                item for item in self.test_results
                if item.test_id == self.resolution_test_id and item.discriminating
            ]
            if not resolution_results:
                raise ValueError("resolved inquiry requires a tested discriminating result")
        if self.state is InquiryState.IRREDUCIBLE_UNKNOWN:
            if len(self.viable_hypothesis_ids) < 2 or not self.information_missing or not self.stop_reason:
                raise ValueError(
                    "irreducible unknown must preserve alternatives, missing information and stop reason"
                )
        return self


def apply_inquiry_test(
    inquiry: VisualInquiry,
    result: InquiryTestResult,
    *,
    no_more_candidate_evidence: bool = False,
    information_missing: str | None = None,
) -> VisualInquiry:
    """Apply one inspected ROI result without promoting any hypothesis to a fact."""

    updated = inquiry.model_copy(deep=True)
    test = next((item for item in updated.tests if item.id == result.test_id), None)
    if test is None:
        raise ValueError("test result references unknown inquiry test")
    allowed_predictions = set(test.prediction_ids)
    if not set(result.compatible_prediction_ids).issubset(allowed_predictions):
        raise ValueError("test result is not scoped to the tested predictions")
    updated.test_results.append(result)

    if result.discriminating:
        surviving_hypotheses = {
            prediction.hypothesis_id
            for prediction in updated.predictions
            if prediction.id in result.compatible_prediction_ids
        }
        updated.viable_hypothesis_ids = [
            item for item in updated.viable_hypothesis_ids if item in surviving_hypotheses
        ]
        if len(updated.viable_hypothesis_ids) == 1:
            updated.state = InquiryState.RESOLVED
            updated.resolved_hypothesis_id = updated.viable_hypothesis_ids[0]
            updated.resolution_test_id = result.test_id
            updated.stop_reason = "A tested discriminating ROI eliminated all competing hypotheses."
            return VisualInquiry.model_validate(updated.model_dump())

    if no_more_candidate_evidence:
        updated.state = InquiryState.IRREDUCIBLE_UNKNOWN
        updated.information_missing = information_missing or "No accessible discriminating evidence remains."
        updated.stop_reason = "Available candidate evidence cannot distinguish the remaining hypotheses."
    return VisualInquiry.model_validate(updated.model_dump())


class MultiViewPass(BaseModel):
    pass_number: Literal[1, 2]
    observations: list[LocalObservation] = Field(default_factory=list)
    view_assessments: list[ViewAssessment] = Field(default_factory=list)
    identities: list[IdentityCandidate] = Field(default_factory=list)
    relations: list[ArchitecturalRelationCandidate] = Field(default_factory=list)
    contradictions: list[Contradiction] = Field(default_factory=list)
    hypotheses: list[OpenHypothesis] = Field(default_factory=list)


class MultiViewWorkspace(BaseModel):
    schema_version: Literal["0.1"] = "0.1"
    photo_count: int = Field(ge=1)
    pass_1: MultiViewPass
    pass_2: MultiViewPass
    inquiries: list[VisualInquiry] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_workspace(self) -> "MultiViewWorkspace":
        if self.pass_1.pass_number != 1 or self.pass_2.pass_number != 2:
            raise ValueError("workspace requires ordered pass 1 and pass 2")
        known_ids = {item.id for item in self.pass_1.observations} | {
            item.id for item in self.pass_2.observations
        }
        for phase in (self.pass_1, self.pass_2):
            for identity in phase.identities:
                unknown = set(identity.observation_ids) - known_ids
                if unknown:
                    raise ValueError(f"identity references unknown observations: {sorted(unknown)}")
            for item in phase.observations:
                if item.photo_index > self.photo_count:
                    raise ValueError("observation references photo outside supplied input")
            for assessment in phase.view_assessments:
                if assessment.photo_index > self.photo_count:
                    raise ValueError("view assessment references photo outside supplied input")
        hypothesis_ids = {item.id for item in self.pass_1.hypotheses} | {
            item.id for item in self.pass_2.hypotheses
        }
        for inquiry in self.inquiries:
            unknown_hypotheses = set(inquiry.hypothesis_ids) - hypothesis_ids
            if unknown_hypotheses:
                raise ValueError(
                    f"inquiry references unknown hypotheses: {sorted(unknown_hypotheses)}"
                )
            for test in inquiry.tests:
                if test.photo_index > self.photo_count:
                    raise ValueError("inquiry test references photo outside supplied input")
        return self
