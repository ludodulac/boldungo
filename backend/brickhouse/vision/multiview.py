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


LOCAL_OBSERVATION_RESPONSE_INVARIANTS = (
    "If status='observed', visibility MUST be 'visible'. "
    "Use visibility='occluded' only when the claimed content is not directly observable "
    "because occlusion prevents observing it; partially masked but still directly observed "
    "content remains visibility='visible' and the statement may describe the partial masking.",
)


class LocalObservation(BaseModel):
    model_config = {"extra": "forbid"}
    id: str = Field(min_length=1)
    photo_index: int = Field(ge=1)
    status: ClaimStatus
    visibility: VisibilityStatus
    region: NormalizedImageRegion | None = None
    qualitative_position: str | None = None
    proposed_category: str | None = None
    statement: str = Field(min_length=1)
    certainty: AspectCertainty = Field(default_factory=AspectCertainty)
    observable_properties: set[str] | None = None
    observed_property_states: dict[str, str] | None = None

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


IDENTITY_CANDIDATE_RESPONSE_INVARIANTS = (
    "observation_ids MUST contain unique IDs.",
    "If status='same_physical_object', certainty MUST be 'certain' or 'plausible'.",
)


class IdentityCandidate(BaseModel):
    model_config = {"extra": "forbid"}
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
    source_uncertainty_id: str | None = None


class InquiryPropertySpec(BaseModel):
    id: str = Field(min_length=1)
    perceptual_description: str = Field(min_length=1)
    recognized_states: tuple[str, ...] = Field(min_length=1)
    applicable_unknown_meaning: str = Field(min_length=1)
    epistemic_conditions: tuple[str, ...] = Field(min_length=1)
    competing_hypothesis_states: tuple[str, ...] = Field(min_length=2)

INQUIRY_PROPERTY_REGISTRY = {"continuation": InquiryPropertySpec(
    id="continuation",
    perceptual_description="Whether the same directly observed visual fragment visibly continues beyond the inspected local region or visibly terminates there.",
    recognized_states=("CONTINUES", "TERMINATES"),
    applicable_unknown_meaning="The property is perceptually relevant, but the pixels do not establish either recognized state.",
    epistemic_conditions=("Use only direct pixel evidence.", "Do not infer from architectural plausibility.", "Do not establish a state under occlusion, non-visibility, ambiguity, or insufficient evidence."),
    competing_hypothesis_states=("CONTINUES", "TERMINATES"),
)}

def inquiry_property_registry_payload() -> list[dict]:
    return [INQUIRY_PROPERTY_REGISTRY[key].model_dump(mode="json") for key in sorted(INQUIRY_PROPERTY_REGISTRY)]

class InquiryPropertySpec(BaseModel):
    """Canonical property family currently supported by autonomous inquiry."""

    id: str = Field(min_length=1)
    perceptual_description: str = Field(min_length=1)
    recognized_states: tuple[str, ...] = Field(min_length=1)
    applicable_unknown_meaning: str = Field(min_length=1)
    epistemic_conditions: tuple[str, ...] = Field(min_length=1)
    competing_hypothesis_states: tuple[str, ...] = Field(min_length=1)


INQUIRY_PROPERTY_REGISTRY: dict[str, InquiryPropertySpec] = {
    "continuation": InquiryPropertySpec(
        id="continuation",
        perceptual_description=(
            "Whether a visually relevant fragment or boundary can be seen to continue "
            "through the evidence region or can be seen to terminate there."
        ),
        recognized_states=("CONTINUES", "TERMINATES"),
        applicable_unknown_meaning=(
            "The continuation property is perceptually relevant/observable for this fragment, "
            "but the pixels do not establish whether it CONTINUES or TERMINATES."
        ),
        epistemic_conditions=(
            "Record a state only when the relevant image evidence directly establishes it.",
            "Do not infer termination from occlusion, non-visibility, ambiguity, or missing evidence.",
        ),
        competing_hypothesis_states=("CONTINUES", "TERMINATES"),
    ),
}


def inquiry_property_registry_payload() -> list[dict]:
    """Bootstrap-facing registry generated from the inquiry engine's canonical registry."""
    return [
        INQUIRY_PROPERTY_REGISTRY[key].model_dump(mode="json")
        for key in sorted(INQUIRY_PROPERTY_REGISTRY)
    ]


class StructuredUncertainty(BaseModel):
    """Local unresolved property with explicit observation provenance."""

    id: str = Field(min_length=1)
    subject_ref: str = Field(min_length=1)
    property_name: str = Field(min_length=1)
    source_observation_ids: list[str] = Field(min_length=1)
    resolved_state: str | None = None


def detect_continuity_uncertainties(
    observations: list[LocalObservation],
) -> list[StructuredUncertainty]:
    """Detect only relevant-but-unresolved continuity; missing mention is not uncertainty."""

    grouped: dict[str, list[LocalObservation]] = {}
    for observation in observations:
        grouped.setdefault(observation.id, []).append(observation)

    uncertainties: list[StructuredUncertainty] = []
    for subject_ref, subject_observations in grouped.items():
        relevant = [
            item
            for item in subject_observations
            if item.observable_properties is not None
            and INQUIRY_PROPERTY_REGISTRY["continuation"].id in item.observable_properties
        ]
        if not relevant:
            continue

        established_states = {
            item.observed_property_states[INQUIRY_PROPERTY_REGISTRY["continuation"].id]
            for item in relevant
            if item.observed_property_states is not None
            and item.observed_property_states.get(INQUIRY_PROPERTY_REGISTRY["continuation"].id)
            in INQUIRY_PROPERTY_REGISTRY["continuation"].recognized_states
        }
        if established_states:
            continue

        source_ids = sorted({item.id for item in relevant})
        uncertainties.append(
            StructuredUncertainty(
                id=f"uncertainty-{subject_ref}-continuity",
                subject_ref=subject_ref,
                property_name="continuity",
                source_observation_ids=source_ids,
            )
        )
    return uncertainties


def derive_competing_hypotheses(
    uncertainty: StructuredUncertainty,
) -> list[OpenHypothesis]:
    """Derive only alternatives licensed by the one Experiment-014 property family."""

    if uncertainty.resolved_state is not None:
        return []

    property_spec = INQUIRY_PROPERTY_REGISTRY.get("continuation") if uncertainty.property_name == "continuity" else None
    alternatives = property_spec.competing_hypothesis_states if property_spec is not None else None
    if alternatives is None:
        return []

    hypothesis_ids = [
        f"{uncertainty.id}-{relation.lower()}" for relation in alternatives
    ]
    return [
        OpenHypothesis(
            id=hypothesis_id,
            subject_refs=[uncertainty.subject_ref],
            statement=f"Structured alternative: {relation}.",
            competing_with=[
                other_id for other_id in hypothesis_ids if other_id != hypothesis_id
            ],
            claim=HypothesisClaim(
                subject_ref=uncertainty.subject_ref,
                relation=relation,
            ),
            source_uncertainty_id=uncertainty.id,
        )
        for hypothesis_id, relation in zip(hypothesis_ids, alternatives)
    ]


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

    continuation = INQUIRY_PROPERTY_REGISTRY["continuation"]
    outcomes = dict(zip(continuation.competing_hypothesis_states, ("visible", "absent")))
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
            ObservableProperty(name=INQUIRY_PROPERTY_REGISTRY["continuation"].id, value=outcome),
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


class CandidateEvidenceTarget(BaseModel):
    """Existing observation region that is traceably relevant to a discriminant."""

    photo_index: int = Field(ge=1)
    region: NormalizedImageRegion
    source_observation_ids: list[str] = Field(min_length=1)
    discriminant_property: str = Field(min_length=1)
    visibility: VisibilityStatus
    testable: bool
    reason: str = Field(min_length=1)


def derive_candidate_evidence_targets(
    question: DiscriminatingQuestion,
    hypotheses: list[OpenHypothesis],
    observations: list[LocalObservation],
) -> list[CandidateEvidenceTarget]:
    """Find existing, structurally linked ROIs; never invent or rank a region."""

    hypothesis_by_id = {item.id: item for item in hypotheses}
    subject_refs = {
        hypothesis_by_id[hypothesis_id].claim.subject_ref
        for hypothesis_id in question.hypothesis_ids
        if hypothesis_id in hypothesis_by_id
        and hypothesis_by_id[hypothesis_id].claim is not None
    }
    if not subject_refs:
        return []

    discriminants = [item.property_name for item in question.discriminants]
    targets: list[CandidateEvidenceTarget] = []
    for observation in observations:
        if observation.id not in subject_refs or observation.region is None:
            continue
        testable = (
            observation.visibility is VisibilityStatus.VISIBLE
            and observation.status is ClaimStatus.OBSERVED
        )
        for property_name in discriminants:
            targets.append(
                CandidateEvidenceTarget(
                    photo_index=observation.photo_index,
                    region=observation.region,
                    source_observation_ids=[observation.id],
                    discriminant_property=property_name,
                    visibility=observation.visibility,
                    testable=testable,
                    reason=(
                        "Existing ROI is directly referenced by the structured hypothesis subject."
                        if testable
                        else "Structurally linked ROI exists but is not currently visually testable."
                    ),
                )
            )
    return targets


class DiscriminationPotential(str, Enum):
    NONE = "none"
    TESTABLE = "testable"
    DISCRIMINATING = "discriminating"


class ApplicabilityState(str, Enum):
    APPLICABLE = "applicable"
    NOT_APPLICABLE = "not_applicable"
    UNKNOWN = "unknown"


class DiscriminationAssessment(BaseModel):
    """Qualitative, explainable assessment; no pseudo-probabilistic score."""

    target: CandidateEvidenceTarget
    potential: DiscriminationPotential
    discriminant_applicability: ApplicabilityState
    expected_outcomes_distinct: bool
    reason: str = Field(min_length=1)


class EvidenceTargetSelection(BaseModel):
    """Best qualitative tier; ties are preserved rather than broken arbitrarily."""

    best_candidates: list[CandidateEvidenceTarget] = Field(default_factory=list)
    tied: bool = False
    reason: str = Field(min_length=1)


def derive_discriminant_applicability(
    target: CandidateEvidenceTarget,
    observations: list[LocalObservation],
) -> ApplicabilityState:
    """Derive applicability only from target provenance and structured observation properties."""

    linked = [
        item
        for item in observations
        if item.id in target.source_observation_ids
        and item.photo_index == target.photo_index
        and item.region == target.region
    ]
    if not linked:
        return ApplicabilityState.NOT_APPLICABLE

    states: list[ApplicabilityState] = []
    for observation in linked:
        if observation.region != target.region or observation.photo_index != target.photo_index:
            states.append(ApplicabilityState.NOT_APPLICABLE)
        elif observation.observable_properties is None:
            states.append(ApplicabilityState.UNKNOWN)
        elif target.discriminant_property in observation.observable_properties:
            states.append(ApplicabilityState.APPLICABLE)
        else:
            states.append(ApplicabilityState.NOT_APPLICABLE)

    if ApplicabilityState.APPLICABLE in states:
        return ApplicabilityState.APPLICABLE
    if ApplicabilityState.UNKNOWN in states:
        return ApplicabilityState.UNKNOWN
    return ApplicabilityState.NOT_APPLICABLE


def assess_discrimination_targets(
    question: DiscriminatingQuestion,
    candidates: list[CandidateEvidenceTarget],
    observations: list[LocalObservation],
) -> list[DiscriminationAssessment]:
    """Assess targets using applicability derived from structured observations."""

    question_properties = {item.property_name: item for item in question.discriminants}
    assessments: list[DiscriminationAssessment] = []
    for target in candidates:
        discriminant = question_properties.get(target.discriminant_property)
        applicability = derive_discriminant_applicability(target, observations)
        distinct = (
            discriminant is not None
            and len(set(discriminant.expected_outcomes.values())) > 1
        )
        if not target.testable:
            potential = DiscriminationPotential.NONE
            reason = "Target is structurally linked but not visually testable."
        elif applicability is ApplicabilityState.UNKNOWN:
            potential = DiscriminationPotential.TESTABLE
            reason = "Target is testable but discriminant applicability is structurally unknown."
        elif applicability is not ApplicabilityState.APPLICABLE or not distinct:
            potential = DiscriminationPotential.TESTABLE
            reason = "Target is visible/testable but cannot expose distinct outcomes for this discriminant."
        else:
            potential = DiscriminationPotential.DISCRIMINATING
            reason = "Target is testable and structurally exposes the discriminant with distinct outcomes."
        assessments.append(
            DiscriminationAssessment(
                target=target,
                potential=potential,
                discriminant_applicability=applicability,
                expected_outcomes_distinct=distinct,
                reason=reason,
            )
        )
    return assessments


def select_discrimination_targets(
    assessments: list[DiscriminationAssessment],
) -> EvidenceTargetSelection:
    """Select all top discriminating candidates; never break a semantic tie by order."""

    best = [
        item.target
        for item in assessments
        if item.potential is DiscriminationPotential.DISCRIMINATING
    ]
    if not best:
        return EvidenceTargetSelection(
            reason="No candidate can currently expose a discriminating outcome."
        )
    canonical = sorted(
        best,
        key=lambda item: (
            item.photo_index,
            item.region.x0,
            item.region.y0,
            item.region.x1,
            item.region.y1,
            tuple(item.source_observation_ids),
            item.discriminant_property,
        ),
    )
    return EvidenceTargetSelection(
        best_candidates=canonical,
        tied=len(canonical) > 1,
        reason=(
            "Multiple candidates have equal best discrimination potential."
            if len(canonical) > 1
            else "One candidate has uniquely best discrimination potential."
        ),
    )


class DiscriminatingTest(BaseModel):
    """One photo region where competing predictions are expected to differ."""

    id: str = Field(min_length=1)
    photo_index: int = Field(ge=1)
    region: NormalizedImageRegion
    prediction_ids: list[str] = Field(min_length=2)
    evidence_sought: str = Field(min_length=1)
    source_observation_ids: list[str] = Field(default_factory=list)


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


class BootstrapPhotoRef(BaseModel):
    photo_index: int = Field(ge=1)
    filename: str = Field(min_length=1)


class VisualBootstrapRequest(BaseModel):
    schema_version: str = "0.3"
    bootstrap_id: str = Field(min_length=1)
    photos: list[BootstrapPhotoRef] = Field(min_length=1)
    instruction: str = Field(min_length=1)
    information_to_record: list[str] = Field(min_length=1)
    epistemic_rules: list[str] = Field(min_length=1)
    output_filename: str = "visual-bootstrap-response.json"
    response_schema: dict
    response_invariants: list[str]
    inquiry_property_registry: list[dict]
    response_example: dict | None = None


VISUAL_BOOTSTRAP_RESPONSE_INVARIANTS = (
    "Observation IDs MUST be unique within observations.",
    "Every observation.photo_index MUST be <= photo_count.",
    "Every identity_candidates[].observation_ids entry MUST reference an existing observations[].id.",
)


class VisualBootstrapResponse(BaseModel):
    model_config = {"extra": "forbid"}
    schema_version: str = "0.1"
    bootstrap_id: str = Field(min_length=1)
    photo_count: int = Field(ge=1)
    observations: list[LocalObservation] = Field(default_factory=list)
    identity_candidates: list[IdentityCandidate] = Field(default_factory=list)
    observer_comment: str | None = None

    @model_validator(mode="after")
    def validate_bootstrap(self) -> "VisualBootstrapResponse":
        ids = {item.id for item in self.observations}
        if len(ids) != len(self.observations):
            raise ValueError("bootstrap observation IDs must be unique")
        for item in self.observations:
            if item.photo_index > self.photo_count:
                raise ValueError("bootstrap observation references unavailable photo")
        for identity in self.identity_candidates:
            unknown = set(identity.observation_ids) - ids
            if unknown:
                raise ValueError(
                    f"bootstrap identity references unknown observations: {sorted(unknown)}"
                )
        return self


NORMALIZED_IMAGE_REGION_RESPONSE_INVARIANTS = (
    "For every non-null region, x1 MUST be greater than x0 and y1 MUST be greater than y0 (positive area).",
)

IMPORT_VISUAL_BOOTSTRAP_RESPONSE_INVARIANTS = (
    "response.bootstrap_id MUST equal request.bootstrap_id.",
    "response.photo_count MUST equal the number of request.photos.",
    "Every response observation.photo_index MUST be one of the photo_index values present in request.photos.",
)


def visual_bootstrap_response_invariants() -> list[str]:
    """Human-readable counterparts of non-schema validators used by bootstrap validation/import."""
    return [
        *LOCAL_OBSERVATION_RESPONSE_INVARIANTS,
        *IDENTITY_CANDIDATE_RESPONSE_INVARIANTS,
        *NORMALIZED_IMAGE_REGION_RESPONSE_INVARIANTS,
        *VISUAL_BOOTSTRAP_RESPONSE_INVARIANTS,
        *IMPORT_VISUAL_BOOTSTRAP_RESPONSE_INVARIANTS,
    ]


def visual_bootstrap_response_schema() -> dict:
    """Single source of truth: schema generated from the exact importer model."""
    return VisualBootstrapResponse.model_json_schema()


def build_visual_bootstrap_request(
    bootstrap_id: str,
    photo_filenames: list[str],
) -> VisualBootstrapRequest:
    return VisualBootstrapRequest(
        bootstrap_id=bootstrap_id,
        photos=[
            BootstrapPhotoRef(photo_index=index, filename=filename)
            for index, filename in enumerate(photo_filenames, start=1)
        ],
        instruction=(
            "Inspect the supplied photos and return only visual-bootstrap-response.json. "
            "Record local, traceable visual observations with approximate normalized image "
            "ROIs where possible. State observable properties separately from observed "
            "property states. Do not reconstruct the whole building, infer hidden geometry, "
            "or use architectural plausibility as visual evidence. Similar-looking fragments "
            "across photos remain identity candidates unless their physical identity is "
            "explicitly supported. Do not add fields that are not present in the response "
            "schema. Do not invent enum values. Return a JSON document that validates exactly "
            "against response_schema. N'ajoutez aucun champ absent du schema de reponse, "
            "n'inventez aucune valeur d'enum et retournez un JSON valide exactement contre "
            "response_schema."
        ),
        information_to_record=[
            "local visual fragments or subjects",
            "approximate normalized image regions",
            "visibility",
            "observable properties",
            "observed property states only when visually established",
            "directly supported local visual relations in statements",
            "cross-view identity candidates with explicit support level",
            "For each inquiry_property_registry property: add its canonical id to observable_properties only when pixels make it perceptually relevant. If pixels establish a recognized state, record it under the same id in observed_property_states. If relevant but no state is established, keep the id without a corresponding state. If not relevant, omit it. Absence never means false. Never select a property merely because the engine supports it.",
        ],
        epistemic_rules=[
            "non_visible != absent",
            "occluded != absent",
            "ambiguous != false",
            "not_mentioned != not_relevant",
            "image_roi != world_metric",
            "resemblance != same_physical_object",
            "architectural_plausibility != observation",
        ],
        response_schema=visual_bootstrap_response_schema(),
        response_invariants=visual_bootstrap_response_invariants(),
        inquiry_property_registry=inquiry_property_registry_payload(),
        response_example={
            "schema_version": "0.1",
            "bootstrap_id": "synthetic-example",
            "photo_count": 1,
            "observations": [{
                "id": "fragment-example",
                "photo_index": 1,
                "status": "observed",
                "visibility": "visible",
                "region": {"x0": 0.1, "y0": 0.1, "x1": 0.2, "y1": 0.2},
                "qualitative_position": None,
                "proposed_category": None,
                "statement": "Synthetic visible fragment.",
                "certainty": {
                    "existence": "certain", "category": "unknown",
                    "identity": "unknown", "spatial_relation": "unknown",
                    "topology": "unknown", "metric": "unknown"
                },
                "observable_properties": ["shape"],
                "observed_property_states": None
            }],
            "identity_candidates": [],
            "observer_comment": "Syntax-only synthetic example."
        },
    )


def import_visual_bootstrap_response(
    request: VisualBootstrapRequest,
    response: VisualBootstrapResponse,
) -> "MultiViewWorkspace":
    if response.bootstrap_id != request.bootstrap_id:
        raise ValueError("bootstrap response ID does not match request")
    if response.photo_count != len(request.photos):
        raise ValueError("bootstrap response photo count does not match request")
    expected_indexes = {item.photo_index for item in request.photos}
    if any(item.photo_index not in expected_indexes for item in response.observations):
        raise ValueError("bootstrap observation references unexpected photo")
    return MultiViewWorkspace(
        photo_count=response.photo_count,
        pass_1=MultiViewPass(
            pass_number=1,
            observations=response.observations,
            identities=response.identity_candidates,
        ),
        pass_2=MultiViewPass(pass_number=2),
    )


class VisualEvidenceStatus(str, Enum):
    OBSERVED = "observed"
    NOT_OBSERVED = "not_observed"
    OCCLUDED = "occluded"
    NON_VISIBLE = "non_visible"
    AMBIGUOUS = "ambiguous"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class VisualInquiryRequest(BaseModel):
    schema_version: str = "0.1"
    request_id: str = Field(min_length=1)
    inquiry_id: str = Field(min_length=1)
    instruction: str = Field(min_length=1)
    subject_ref: str = Field(min_length=1)
    property_name: str = Field(min_length=1)
    question: DiscriminatingQuestion
    predictions: list[ObservablePrediction] = Field(min_length=2)
    target: CandidateEvidenceTarget
    test_id: str = Field(min_length=1)
    observability_requirements: list[str] = Field(min_length=1)


class VisualEvidenceResponse(BaseModel):
    schema_version: str = "0.1"
    request_id: str = Field(min_length=1)
    inquiry_id: str = Field(min_length=1)
    test_id: str = Field(min_length=1)
    photo_index: int = Field(ge=1)
    region: NormalizedImageRegion
    property_name: str = Field(min_length=1)
    status: VisualEvidenceStatus
    observed_value: str | None = None
    certainty: CertaintyLevel = CertaintyLevel.UNKNOWN
    source_observation_ids: list[str] = Field(min_length=1)
    comment: str | None = None

    @model_validator(mode="after")
    def validate_structured_result(self) -> "VisualEvidenceResponse":
        if self.status in {VisualEvidenceStatus.OBSERVED, VisualEvidenceStatus.NOT_OBSERVED}:
            if self.observed_value is None:
                raise ValueError("decisive visual evidence requires a structured observed_value")
        elif self.observed_value is not None:
            raise ValueError("inconclusive visual evidence cannot carry an observed_value")
        return self


def build_executable_visual_inquiry(
    uncertainty: StructuredUncertainty,
    hypotheses: list[OpenHypothesis],
    predictions: list[ObservablePrediction],
    question: DiscriminatingQuestion,
    assessments: list[DiscriminationAssessment],
    selection: EvidenceTargetSelection,
) -> "VisualInquiry" | None:
    """Build one executable inquiry from already-derived structured artifacts only."""

    if len(selection.best_candidates) != 1 or selection.tied:
        return None
    target = selection.best_candidates[0]
    matching_assessments = [
        item for item in assessments
        if item.target == target
        and item.potential is DiscriminationPotential.DISCRIMINATING
    ]
    if len(matching_assessments) != 1:
        return None
    if not target.source_observation_ids:
        return None

    hypothesis_by_id = {item.id: item for item in hypotheses}
    prediction_by_id = {item.id: item for item in predictions}
    if len(hypothesis_by_id) != len(hypotheses) or len(prediction_by_id) != len(predictions):
        return None
    if set(question.hypothesis_ids) != set(hypothesis_by_id):
        return None
    if set(question.prediction_ids) != set(prediction_by_id):
        return None
    if any(
        prediction_by_id[prediction_id].hypothesis_id not in hypothesis_by_id
        for prediction_id in question.prediction_ids
    ):
        return None
    prediction_ids_by_hypothesis = {
        hypothesis_id: [
            prediction_id for prediction_id in question.prediction_ids
            if prediction_by_id[prediction_id].hypothesis_id == hypothesis_id
        ]
        for hypothesis_id in question.hypothesis_ids
    }
    if any(len(ids) != 1 for ids in prediction_ids_by_hypothesis.values()):
        return None
    if any(
        hypothesis_by_id[hypothesis_id].source_uncertainty_id != uncertainty.id
        for hypothesis_id in question.hypothesis_ids
    ):
        return None

    discriminants = [
        item for item in question.discriminants
        if item.property_name == target.discriminant_property
    ]
    if len(discriminants) != 1:
        return None
    discriminant = discriminants[0]
    if set(discriminant.expected_outcomes) != set(question.hypothesis_ids):
        return None
    structured_outcomes = {
        hypothesis_id: next(
            (
                prop.value
                for prop in prediction_by_id[
                    prediction_ids_by_hypothesis[hypothesis_id][0]
                ].observable_properties
                if prop.name == target.discriminant_property
            ),
            None,
        )
        for hypothesis_id in question.hypothesis_ids
    }
    if structured_outcomes != discriminant.expected_outcomes:
        return None

    source_token = "-".join(sorted(target.source_observation_ids))
    test = DiscriminatingTest(
        id=f"test-{uncertainty.id}-{target.photo_index}-{target.discriminant_property}-{source_token}",
        photo_index=target.photo_index,
        region=target.region,
        prediction_ids=list(question.prediction_ids),
        evidence_sought=target.discriminant_property,
        source_observation_ids=list(target.source_observation_ids),
    )
    return VisualInquiry(
        id=f"inquiry-{uncertainty.id}",
        question=question.human_readable_question,
        hypothesis_ids=list(question.hypothesis_ids),
        predictions=[prediction_by_id[item] for item in question.prediction_ids],
        tests=[test],
    )


def build_visual_inquiry_request(
    inquiry: "VisualInquiry",
    question: DiscriminatingQuestion,
    hypotheses: list[OpenHypothesis],
    target: CandidateEvidenceTarget,
) -> VisualInquiryRequest:
    hypothesis_by_id = {item.id: item for item in hypotheses}
    subject_refs = {
        hypothesis_by_id[item].claim.subject_ref
        for item in question.hypothesis_ids
        if item in hypothesis_by_id and hypothesis_by_id[item].claim is not None
    }
    if len(subject_refs) != 1:
        raise ValueError("visual exchange requires one structurally identified subject")
    test = next(
        (
            item
            for item in inquiry.tests
            if item.photo_index == target.photo_index
            and item.region == target.region
            and item.evidence_sought == target.discriminant_property
            and (
                not item.source_observation_ids
                or item.source_observation_ids == target.source_observation_ids
            )
        ),
        None,
    )
    if test is None:
        raise ValueError("candidate target must correspond to an inquiry test")
    return VisualInquiryRequest(
        request_id=f"request-{inquiry.id}-{test.id}",
        inquiry_id=inquiry.id,
        instruction=(
            "Inspect only the referenced photo/ROI and return a VisualEvidenceResponse JSON. "
            "Report occluded, non-visible, ambiguous, or insufficient evidence explicitly; "
            "do not infer absence from inability to see."
        ),
        subject_ref=next(iter(subject_refs)),
        property_name=target.discriminant_property,
        question=question,
        predictions=inquiry.predictions,
        target=target,
        test_id=test.id,
        observability_requirements=[
            "region_in_frame",
            "non_occluded",
            "sufficient_visibility",
        ],
    )


def import_visual_evidence_response(
    request: VisualInquiryRequest,
    response: VisualEvidenceResponse,
) -> InquiryTestResult:
    if (
        response.request_id != request.request_id
        or response.inquiry_id != request.inquiry_id
        or response.test_id != request.test_id
        or response.photo_index != request.target.photo_index
        or response.region != request.target.region
        or response.property_name != request.property_name
        or response.source_observation_ids != request.target.source_observation_ids
    ):
        raise ValueError("visual evidence response provenance does not match request")

    inconclusive = response.status in {
        VisualEvidenceStatus.OCCLUDED,
        VisualEvidenceStatus.NON_VISIBLE,
        VisualEvidenceStatus.AMBIGUOUS,
        VisualEvidenceStatus.INSUFFICIENT_EVIDENCE,
    }
    if inconclusive:
        visibility = (
            VisibilityStatus.OCCLUDED
            if response.status is VisualEvidenceStatus.OCCLUDED
            else VisibilityStatus.NON_VISIBLE
            if response.status is VisualEvidenceStatus.NON_VISIBLE
            else VisibilityStatus.VISIBLE
        )
        return InquiryTestResult(
            test_id=request.test_id,
            inspected=True,
            region_in_frame=response.status is not VisualEvidenceStatus.NON_VISIBLE,
            visibility=visibility,
            sufficient_visibility=False,
            statement=response.comment or f"External visual result: {response.status.value}.",
            compatible_prediction_ids=request.question.prediction_ids,
            discriminating=False,
        )

    outcomes = {
        hypothesis_id: value
        for discriminant in request.question.discriminants
        if discriminant.property_name == request.property_name
        for hypothesis_id, value in discriminant.expected_outcomes.items()
    }
    compatible = [
        prediction_id
        for prediction_id in request.question.prediction_ids
        if outcomes.get(
            next(
                item.hypothesis_id
                for item in request.predictions
                if item.id == prediction_id
            )
        ) == response.observed_value
    ]
    if not compatible:
        raise ValueError("structured observed_value matches no expected outcome")
    return InquiryTestResult(
        test_id=request.test_id,
        inspected=True,
        region_in_frame=True,
        visibility=VisibilityStatus.VISIBLE,
        sufficient_visibility=True,
        statement=response.comment or "Structured external visual evidence imported.",
        compatible_prediction_ids=compatible,
        discriminating=len(compatible) == 1,
    )


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
