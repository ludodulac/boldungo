"""Structured pre-Survey workspace for auditable multi-view photo reasoning.

This is deliberately not ArchitecturalSurvey and contains no free-form chain of
thought.  It records only reviewable claims derived from pixels before factual
Survey fusion or geometric reconstruction.
"""
from __future__ import annotations

from enum import Enum
from typing import ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

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
    "Legacy/default inquiry_state='not_enquirable' MUST carry no open_alternatives.",
    "inquiry_state='open_alternatives' requires at least two unique explicit alternatives: exactly 'same_physical_object' and 'incompatible'.",
    "A CERTAIN same_physical_object or CERTAIN incompatible candidate MUST NOT simultaneously declare open alternatives.",
)


class IdentityInquiryState(str, Enum):
    """Whether an identity candidate itself licenses an autonomous inquiry."""

    NOT_ENQUIRABLE = "not_enquirable"
    OPEN_ALTERNATIVES = "open_alternatives"


class IdentityCandidate(BaseModel):
    model_config = {"extra": "forbid"}
    id: str = Field(min_length=1)
    observation_ids: list[str] = Field(min_length=2)
    status: IdentityStatus
    corroborating_photo_indexes: list[int] = Field(default_factory=list)
    conflicting_photo_indexes: list[int] = Field(default_factory=list)
    certainty: CertaintyLevel = CertaintyLevel.UNKNOWN
    inquiry_state: IdentityInquiryState = IdentityInquiryState.NOT_ENQUIRABLE
    open_alternatives: list[IdentityStatus] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_identity(self) -> "IdentityCandidate":
        if len(self.observation_ids) != len(set(self.observation_ids)):
            raise ValueError("identity observation IDs must be unique")
        if self.status is IdentityStatus.SAME_PHYSICAL_OBJECT and self.certainty not in {
            CertaintyLevel.CERTAIN,
            CertaintyLevel.PLAUSIBLE,
        }:
            raise ValueError("same physical object identity needs explicit support")

        if self.inquiry_state is IdentityInquiryState.NOT_ENQUIRABLE:
            if self.open_alternatives:
                raise ValueError("non-enquirable identity cannot carry open alternatives")
            return self

        if self.status in {IdentityStatus.SAME_PHYSICAL_OBJECT, IdentityStatus.INCOMPATIBLE} and self.certainty is CertaintyLevel.CERTAIN:
            raise ValueError("acquired identity state cannot simultaneously declare open alternatives")
        if len(self.open_alternatives) < 2 or len(self.open_alternatives) != len(set(self.open_alternatives)):
            raise ValueError("enquirable identity requires at least two unique explicit alternatives")
        allowed = {IdentityStatus.SAME_PHYSICAL_OBJECT, IdentityStatus.INCOMPATIBLE}
        if set(self.open_alternatives) != allowed:
            raise ValueError("identity inquiry alternatives must explicitly be same_physical_object and incompatible")
        return self


class RelationInquiryState(str, Enum):
    """Whether an explicit relation competition licenses autonomous inquiry."""

    NOT_ENQUIRABLE = "not_enquirable"
    OPEN_ALTERNATIVES = "open_alternatives"


class RelationAlternative(BaseModel):
    """One explicitly supplied relation for the candidate's exact subject/object pair."""

    relation: str = Field(min_length=1)
    source_observation_ids: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_provenance(self) -> "RelationAlternative":
        if len(self.source_observation_ids) != len(set(self.source_observation_ids)):
            raise ValueError("relation alternative provenance IDs must be unique")
        return self


class RelationInvestigationRecord(BaseModel):
    """Persisted memory of one exact relation-producer investigation; not architectural truth."""
    model_config = ConfigDict(extra="forbid")
    subject_ref: str = Field(min_length=1)
    object_ref: str = Field(min_length=1)
    source_observation_ids: list[str] = Field(min_length=2)
    outcome: Literal["no_reliable_alternatives", "insufficient_visual_evidence"]
    investigation_id: str | None = Field(default=None, min_length=1)
    producer_request_id: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def validate_record(self) -> "RelationInvestigationRecord":
        if len(self.source_observation_ids) != len(set(self.source_observation_ids)):
            raise ValueError("relation investigation source IDs must be unique")
        return self


class ArchitecturalRelationCandidate(BaseModel):
    id: str = Field(min_length=1)
    subject_ref: str = Field(min_length=1)
    object_ref: str = Field(min_length=1)
    relation: str | None = Field(default=None, min_length=1)
    status: ClaimStatus = ClaimStatus.INFERRED
    certainty: CertaintyLevel = CertaintyLevel.UNKNOWN
    supporting_photo_indexes: list[int] = Field(default_factory=list)
    source_observation_ids_by_element: dict[str, list[str]] = Field(default_factory=dict)
    visual_evidence_source_ids: list[str] = Field(default_factory=list)
    investigations: list[RelationInvestigationRecord] = Field(default_factory=list)
    batch_investigation_id: str | None = Field(default=None, min_length=1)
    inquiry_state: RelationInquiryState = RelationInquiryState.NOT_ENQUIRABLE
    open_alternatives: list[RelationAlternative] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_relation_inquiry(self) -> "ArchitecturalRelationCandidate":
        if self.inquiry_state is RelationInquiryState.NOT_ENQUIRABLE:
            if self.open_alternatives:
                raise ValueError("non-enquirable relation cannot carry open alternatives")
            return self
        if self.relation is None:
            raise ValueError("enquirable relation candidate requires an imported relation token")
        if len(self.open_alternatives) < 2:
            raise ValueError("enquirable relation requires at least two explicit alternatives")
        names = [item.relation for item in self.open_alternatives]
        if len(names) != len(set(names)):
            raise ValueError("relation alternatives must be distinct")
        return self


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
    """Unresolved structured competition with explicit source/provenance."""

    id: str = Field(min_length=1)
    subject_ref: str | None = Field(default=None, min_length=1)
    property_name: str = Field(min_length=1)
    source_observation_ids: list[str] = Field(min_length=1)
    resolved_state: str | None = None
    source_ref: str | None = Field(default=None, min_length=1)
    source_kind: str = Field(default="observation", min_length=1)
    open_alternatives: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_uncertainty_source(self) -> "StructuredUncertainty":
        if self.source_kind == "observation" and self.subject_ref is None:
            raise ValueError("observation uncertainty requires subject_ref")
        if self.source_kind == "identity_candidate":
            if self.source_ref is None:
                raise ValueError("identity uncertainty requires source_ref")
            if len(self.open_alternatives) < 2:
                raise ValueError("identity uncertainty requires explicit open alternatives")
        return self


def detect_identity_uncertainties(
    identities: list[IdentityCandidate],
    observations: list[LocalObservation],
) -> list[StructuredUncertainty]:
    """Lift only explicitly enquirable identity competitions; infer nothing."""

    observation_ids = {item.id for item in observations}
    result: list[StructuredUncertainty] = []
    for candidate in identities:
        if candidate.inquiry_state is not IdentityInquiryState.OPEN_ALTERNATIVES:
            continue
        if not set(candidate.observation_ids).issubset(observation_ids):
            continue
        result.append(
            StructuredUncertainty(
                id=f"identity-uncertainty-{candidate.id}",
                property_name="identity",
                source_observation_ids=list(candidate.observation_ids),
                source_ref=candidate.id,
                source_kind="identity_candidate",
                open_alternatives=[item.value for item in candidate.open_alternatives],
            )
        )
    return result


def detect_relation_uncertainties(
    relations: list[ArchitecturalRelationCandidate],
    observations: list[LocalObservation],
) -> list[StructuredUncertainty]:
    """Lift only explicit relation competitions; certainty alone never creates one."""

    observation_ids = {item.id for item in observations}
    result: list[StructuredUncertainty] = []
    for candidate in relations:
        if candidate.inquiry_state is not RelationInquiryState.OPEN_ALTERNATIVES:
            continue
        provenance = {
            source_id
            for alternative in candidate.open_alternatives
            for source_id in alternative.source_observation_ids
        }
        if not provenance or not provenance.issubset(observation_ids):
            continue
        result.append(
            StructuredUncertainty(
                id=f"relation-uncertainty-{candidate.id}",
                subject_ref=candidate.subject_ref,
                property_name="relation",
                source_observation_ids=sorted(provenance),
                source_ref=candidate.id,
                source_kind="relation_candidate",
                open_alternatives=[item.relation for item in candidate.open_alternatives],
            )
        )
    return result


def detect_continuity_uncertainties(
    observations: list[LocalObservation],
    *,
    inquiries: list["VisualInquiry"] | None = None,
    hypotheses: list[OpenHypothesis] | None = None,
) -> list[StructuredUncertainty]:
    """Detect open continuity uncertainty while preserving historical observations.

    Persisted inquiries are acquired knowledge.  A resolved inquiry suppresses
    redetection only when its structured hypothesis/test provenance proves that
    it resolves the same subject and uncertainty/property family.
    """

    grouped: dict[str, list[LocalObservation]] = {}
    for observation in observations:
        grouped.setdefault(observation.id, []).append(observation)

    inquiries = inquiries or []
    hypotheses = hypotheses or []
    hypothesis_by_id = {item.id: item for item in hypotheses}

    def coherently_resolved(uncertainty: StructuredUncertainty) -> bool:
        for inquiry in inquiries:
            if inquiry.state is not InquiryState.RESOLVED:
                continue
            if not inquiry.resolved_hypothesis_id or not inquiry.resolution_test_id:
                continue
            resolved = hypothesis_by_id.get(inquiry.resolved_hypothesis_id)
            if resolved is None or resolved.claim is None:
                continue
            if resolved.source_uncertainty_id != uncertainty.id:
                continue
            if resolved.claim.subject_ref != uncertainty.subject_ref:
                continue
            property_spec = (
                INQUIRY_PROPERTY_REGISTRY.get("continuation")
                if uncertainty.property_name == "continuity"
                else None
            )
            if property_spec is None or resolved.claim.relation not in property_spec.competing_hypothesis_states:
                continue
            test = next(
                (item for item in inquiry.tests if item.id == inquiry.resolution_test_id),
                None,
            )
            if test is None or test.evidence_sought != property_spec.id:
                continue
            result = next(
                (
                    item for item in inquiry.test_results
                    if item.test_id == inquiry.resolution_test_id and item.discriminating
                ),
                None,
            )
            if result is None:
                continue
            resolved_predictions = [
                item.id for item in inquiry.predictions
                if item.hypothesis_id == resolved.id
            ]
            if len(resolved_predictions) != 1:
                continue
            if resolved_predictions[0] not in result.compatible_prediction_ids:
                continue
            return True
        return False

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
        uncertainty = StructuredUncertainty(
            id=f"uncertainty-{subject_ref}-continuity",
            subject_ref=subject_ref,
            property_name="continuity",
            source_observation_ids=source_ids,
        )
        if coherently_resolved(uncertainty):
            continue
        uncertainties.append(uncertainty)
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


class EvidenceRegion(BaseModel):
    """One visual source in an atomic evidence target; region may be genuinely unknown."""

    source_id: str = Field(min_length=1)
    observation_ref: str | None = Field(default=None, min_length=1)
    photo_index: int = Field(ge=1)
    region: NormalizedImageRegion | None = None
    visibility: VisibilityStatus = VisibilityStatus.VISIBLE


class RelationPairProducerStatus(str, Enum):
    PAIR_PROPOSED = "pair_proposed"
    NO_RELIABLE_PAIR = "no_reliable_pair"
    INSUFFICIENT_VISUAL_EVIDENCE = "insufficient_visual_evidence"


class RelationPairProducerSource(BaseModel):
    model_config = ConfigDict(extra="forbid")
    observation_ref: str = Field(min_length=1)
    photo_index: int = Field(ge=1)
    region: NormalizedImageRegion | None = None
    visibility: VisibilityStatus
    proposed_category: str | None = None
    statement: str = Field(min_length=1)


class RelationPairElement(BaseModel):
    model_config = ConfigDict(extra="forbid")
    element_ref: str = Field(min_length=1)
    source_observation_ids: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_sources(self) -> "RelationPairElement":
        if len(self.source_observation_ids) != len(set(self.source_observation_ids)):
            raise ValueError("pair element source observation IDs must be unique")
        return self


class RelationPairProducerResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["0.1"] = "0.1"
    producer_request_id: str = Field(min_length=1)
    status: RelationPairProducerStatus
    sources: list[RelationPairProducerSource] = Field(min_length=2)
    subject: RelationPairElement | None = None
    object: RelationPairElement | None = None
    visual_evidence_source_ids: list[str] | None = None

    @model_validator(mode="after")
    def validate_shape(self) -> "RelationPairProducerResponse":
        refs = [item.observation_ref for item in self.sources]
        if len(refs) != len(set(refs)):
            raise ValueError("pair producer response sources must be unique")
        payload = (self.subject, self.object, self.visual_evidence_source_ids)
        if self.status is RelationPairProducerStatus.PAIR_PROPOSED:
            if any(item is None for item in payload):
                raise ValueError("PAIR_PROPOSED requires subject, object and visual evidence provenance")
            if self.subject.element_ref == self.object.element_ref:
                raise ValueError("relation pair elements must be distinct")
            if not self.visual_evidence_source_ids or len(self.visual_evidence_source_ids) != len(set(self.visual_evidence_source_ids)):
                raise ValueError("PAIR_PROPOSED requires unique non-empty visual evidence provenance")
        elif any(item is not None for item in payload):
            raise ValueError("inconclusive pair producer status cannot carry pair payload")
        return self


class RelationPairProducerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["0.1"] = "0.1"
    producer_request_id: str = Field(min_length=1)
    sources: list[RelationPairProducerSource] = Field(min_length=2)
    identity_candidates: list[IdentityCandidate] = Field(default_factory=list)
    excluded_exact_evidence_sets: list[list[str]] = Field(default_factory=list)
    instruction: str = Field(min_length=1)
    response_schema: dict
    response_invariants: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_request(self) -> "RelationPairProducerRequest":
        refs = [item.observation_ref for item in self.sources]
        if len(refs) != len(set(refs)):
            raise ValueError("pair producer request observation refs must be unique")
        known = set(refs)
        for identity in self.identity_candidates:
            if not set(identity.observation_ids).issubset(known):
                raise ValueError("pair producer identity candidate references unavailable source")
        return self


RELATION_PAIR_PRODUCER_RESPONSE_INVARIANTS = (
    "response.producer_request_id MUST exactly match the request.",
    "response.sources MUST exactly match request.sources including observation_ref, photo_index, ROI, visibility, proposed_category and statement.",
    "PAIR_PROPOSED requires two distinct element_ref values, non-empty source_observation_ids for each element, and non-empty visual_evidence_source_ids.",
    "Every source_observation_id and visual_evidence_source_id MUST reference an observation exposed by the request.",
    "The response proposes only a pair worth relational investigation; it MUST NOT propose, name, infer, negate, invert, or otherwise encode an architectural relation.",
    "Identity candidates are context only. LIKELY_SAME or UNRESOLVED MUST NOT be promoted to SAME_PHYSICAL_OBJECT by the importer.",
    "NO_RELIABLE_PAIR and INSUFFICIENT_VISUAL_EVIDENCE MUST carry no subject, object or visual evidence provenance.",
)


def relation_pair_producer_response_schema() -> dict:
    return RelationPairProducerResponse.model_json_schema()


def build_relation_pair_producer_request(
    producer_request_id: str,
    observations: list[LocalObservation],
    identity_candidates: list[IdentityCandidate],
    excluded_exact_evidence_sets: list[list[str]] | None = None,
) -> RelationPairProducerRequest:
    if len(observations) < 2:
        raise ValueError("relation pair producer requires at least two observations")
    sources = [
        RelationPairProducerSource(
            observation_ref=item.id,
            photo_index=item.photo_index,
            region=item.region,
            visibility=item.visibility,
            proposed_category=item.proposed_category,
            statement=item.statement,
        )
        for item in observations
    ]
    known = {item.id for item in observations}
    identities = [
        item for item in identity_candidates
        if set(item.observation_ids).issubset(known)
    ]
    return RelationPairProducerRequest(
        producer_request_id=producer_request_id,
        sources=sources,
        identity_candidates=identities,
        excluded_exact_evidence_sets=excluded_exact_evidence_sets or [],
        instruction=(
            "Inspect only the supplied observation sources. Determine whether the pixels justify selecting two "
            "distinct physical elements as a pair worth later relational investigation. Do not name, suggest, "
            "infer, negate, invert, or choose any architectural relation. If a pair is justified, return "
            "PAIR_PROPOSED with distinct opaque element_ref values, exact source observation provenance for "
            "each element, and the exact exposed observation IDs providing visual evidence. Existing identity "
            "candidates may be considered only at their stated status; LIKELY_SAME or UNRESOLVED is not established "
            "identity and must not be promoted. Do not propose a pair using exactly an excluded_exact_evidence_set already exhausted by prior investigation; a structurally distinct evidence set remains eligible. Otherwise return NO_RELIABLE_PAIR or INSUFFICIENT_VISUAL_EVIDENCE."
        ),
        response_schema=relation_pair_producer_response_schema(),
        response_invariants=list(RELATION_PAIR_PRODUCER_RESPONSE_INVARIANTS),
    )


def import_relation_pair_producer_response(
    request: RelationPairProducerRequest,
    response: RelationPairProducerResponse,
) -> ArchitecturalRelationCandidate | None:
    if response.producer_request_id != request.producer_request_id:
        raise ValueError("relation pair producer response ID does not match request")
    expected = {item.observation_ref: item for item in request.sources}
    if {item.observation_ref for item in response.sources} != set(expected):
        raise ValueError("relation pair producer source set does not exactly match request")
    for item in response.sources:
        if item != expected[item.observation_ref]:
            raise ValueError("relation pair producer source photo/ROI/visibility/provenance does not exactly match request")
    if response.status is not RelationPairProducerStatus.PAIR_PROPOSED:
        return None
    known = set(expected)
    for element in (response.subject, response.object):
        if not set(element.source_observation_ids).issubset(known):
            raise ValueError("relation pair element references source outside request")
    if not set(response.visual_evidence_source_ids).issubset(known):
        raise ValueError("relation pair visual evidence references source outside request")
    # Pair discovery persists in the existing candidate structure with relation=None until 048 supplies alternatives.
    return ArchitecturalRelationCandidate(
        id=f"relation-pair-{request.producer_request_id}",
        subject_ref=response.subject.element_ref,
        object_ref=response.object.element_ref,
        relation=None,
        status=ClaimStatus.UNKNOWN,
        certainty=CertaintyLevel.UNKNOWN,
        supporting_photo_indexes=sorted({
            expected[source_id].photo_index
            for source_id in response.visual_evidence_source_ids
        }),
        source_observation_ids_by_element={
            response.subject.element_ref: list(response.subject.source_observation_ids),
            response.object.element_ref: list(response.object.source_observation_ids),
        },
        visual_evidence_source_ids=list(response.visual_evidence_source_ids),
        inquiry_state=RelationInquiryState.NOT_ENQUIRABLE,
        open_alternatives=[],
    )


class RelationAlternativeProducerStatus(str, Enum):
    OPEN_ALTERNATIVES = "open_alternatives"
    NO_RELIABLE_ALTERNATIVES = "no_reliable_alternatives"
    INSUFFICIENT_VISUAL_EVIDENCE = "insufficient_visual_evidence"


class RelationAlternativeProducerSource(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_id: str = Field(min_length=1)
    observation_ref: str = Field(min_length=1)
    photo_index: int = Field(ge=1)
    region: NormalizedImageRegion | None = None
    visibility: VisibilityStatus


class RelationAlternativeProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")
    relation_token: str = Field(min_length=1)
    source_observation_ids: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_proposal_provenance(self) -> "RelationAlternativeProposal":
        if len(self.source_observation_ids) != len(set(self.source_observation_ids)):
            raise ValueError("relation proposal provenance IDs must be unique")
        return self


class RelationAlternativeProducerResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["0.1"] = "0.1"
    producer_request_id: str = Field(min_length=1)
    subject_ref: str = Field(min_length=1)
    object_ref: str = Field(min_length=1)
    status: RelationAlternativeProducerStatus
    sources: list[RelationAlternativeProducerSource] = Field(min_length=2)
    alternatives: list[RelationAlternativeProposal] | None = None
    relation_descriptions: dict[str, str] | None = None

    @model_validator(mode="after")
    def validate_shape(self) -> "RelationAlternativeProducerResponse":
        source_ids = [item.source_id for item in self.sources]
        refs = [item.observation_ref for item in self.sources]
        if len(source_ids) != len(set(source_ids)) or len(refs) != len(set(refs)):
            raise ValueError("relation producer response sources must be unique")
        if self.status is RelationAlternativeProducerStatus.OPEN_ALTERNATIVES:
            if self.alternatives is None or len(self.alternatives) < 2:
                raise ValueError("open relation competition requires at least two alternatives")
            tokens = [item.relation_token for item in self.alternatives]
            if len(tokens) != len(set(tokens)):
                raise ValueError("open relation alternatives must be distinct")
            if self.relation_descriptions is None or set(self.relation_descriptions) != set(tokens):
                raise ValueError("relation descriptions must exactly cover proposed tokens")
        elif self.alternatives is not None or self.relation_descriptions is not None:
            raise ValueError("inconclusive relation producer status cannot carry alternatives")
        return self


class RelationAlternativeProducerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["0.1"] = "0.1"
    producer_request_id: str = Field(min_length=1)
    subject_ref: str = Field(min_length=1)
    object_ref: str = Field(min_length=1)
    sources: list[RelationAlternativeProducerSource] = Field(min_length=2)
    allowed_relation_tokens: list[str] = Field(min_length=2)
    instruction: str = Field(min_length=1)
    response_schema: dict
    response_invariants: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_request(self) -> "RelationAlternativeProducerRequest":
        source_ids = [item.source_id for item in self.sources]
        refs = [item.observation_ref for item in self.sources]
        if len(source_ids) != len(set(source_ids)) or len(refs) != len(set(refs)):
            raise ValueError("relation producer request sources must be unique")
        if len(self.allowed_relation_tokens) != len(set(self.allowed_relation_tokens)):
            raise ValueError("allowed relation tokens must be unique")
        return self


RELATION_ALTERNATIVE_PRODUCER_RESPONSE_INVARIANTS = (
    "producer_request_id, subject_ref and object_ref MUST exactly match the request.",
    "response.sources MUST exactly match request.sources including source_id, observation_ref, photo_index, region and visibility.",
    "OPEN_ALTERNATIVES requires at least two distinct alternatives; inconclusive statuses MUST carry no alternatives or descriptions.",
    "Every relation_token MUST come from request.allowed_relation_tokens; tokens are opaque machine identifiers and relation_descriptions are documentation only.",
    "Every alternative.source_observation_ids MUST be non-empty and contain only observation_ref values present in request.sources.",
    "No implicit negation, inverse, converse, or additional relation may be created by the importer.",
)


def relation_alternative_producer_response_schema() -> dict:
    return RelationAlternativeProducerResponse.model_json_schema()


def build_relation_alternative_producer_request(
    producer_request_id: str,
    subject_ref: str,
    object_ref: str,
    observations: list[LocalObservation],
) -> RelationAlternativeProducerRequest:
    if len(observations) < 2:
        raise ValueError("relation alternative producer requires at least two source observations")
    sources = [
        RelationAlternativeProducerSource(
            source_id=f"relation-source-{index + 1}",
            observation_ref=item.id,
            photo_index=item.photo_index,
            region=item.region,
            visibility=item.visibility,
        )
        for index, item in enumerate(observations)
    ]
    return RelationAlternativeProducerRequest(
        producer_request_id=producer_request_id,
        subject_ref=subject_ref,
        object_ref=object_ref,
        sources=sources,
        allowed_relation_tokens=["relation_alpha", "relation_beta", "relation_gamma", "relation_delta"],
        instruction=(
            "Inspect only the supplied sources and decide whether their pixels justify a genuine explicit "
            "competition between relations for exactly this subject_ref/object_ref pair. If yes, return "
            "OPEN_ALTERNATIVES with at least two distinct opaque relation tokens selected only from the "
            "allowed list, plus non-executable descriptions and exact source observation provenance. "
            "Do not infer a negation, inverse, converse, or alternative from uncertainty or plausibility. "
            "If no reliable competition is supported, return NO_RELIABLE_ALTERNATIVES; if the supplied "
            "pixels are insufficient, return INSUFFICIENT_VISUAL_EVIDENCE."
        ),
        response_schema=relation_alternative_producer_response_schema(),
        response_invariants=list(RELATION_ALTERNATIVE_PRODUCER_RESPONSE_INVARIANTS),
    )


def import_relation_alternative_producer_response(
    request: RelationAlternativeProducerRequest,
    response: RelationAlternativeProducerResponse,
) -> ArchitecturalRelationCandidate | None:
    if response.producer_request_id != request.producer_request_id:
        raise ValueError("relation producer response ID does not match request")
    if response.subject_ref != request.subject_ref or response.object_ref != request.object_ref:
        raise ValueError("relation producer subject/object does not exactly match request")
    expected_sources = {item.source_id: item for item in request.sources}
    if {item.source_id for item in response.sources} != set(expected_sources):
        raise ValueError("relation producer response source set does not exactly match request")
    for item in response.sources:
        if item != expected_sources[item.source_id]:
            raise ValueError("relation producer source photo/ROI/visibility/provenance does not exactly match request")
    if response.status is not RelationAlternativeProducerStatus.OPEN_ALTERNATIVES:
        return None
    known_observations = {item.observation_ref for item in request.sources}
    alternatives: list[RelationAlternative] = []
    for proposal in response.alternatives:
        if proposal.relation_token not in request.allowed_relation_tokens:
            raise ValueError("relation token is not allowed by request")
        if not set(proposal.source_observation_ids).issubset(known_observations):
            raise ValueError("relation alternative references unknown source observation")
        alternatives.append(
            RelationAlternative(
                relation=proposal.relation_token,
                source_observation_ids=list(proposal.source_observation_ids),
            )
        )
    return ArchitecturalRelationCandidate(
        id=f"relation-candidate-{request.producer_request_id}",
        subject_ref=request.subject_ref,
        object_ref=request.object_ref,
        relation=alternatives[0].relation,
        status=ClaimStatus.INFERRED,
        certainty=CertaintyLevel.UNKNOWN,
        inquiry_state=RelationInquiryState.OPEN_ALTERNATIVES,
        open_alternatives=alternatives,
    )


def record_relation_investigation(
    candidate: ArchitecturalRelationCandidate,
    request: RelationAlternativeProducerRequest,
    response: RelationAlternativeProducerResponse,
    *,
    investigation_id: str | None = None,
) -> ArchitecturalRelationCandidate:
    """Persist only exhaustion of this exact pair+evidence investigation; infer no relation."""
    imported = import_relation_alternative_producer_response(request, response)
    if imported is not None:
        return imported
    source_ids = [item.observation_ref for item in request.sources]
    record = RelationInvestigationRecord(
        subject_ref=request.subject_ref,
        object_ref=request.object_ref,
        source_observation_ids=source_ids,
        outcome=response.status.value,
        investigation_id=investigation_id,
        producer_request_id=request.producer_request_id,
    )
    existing = list(candidate.investigations)
    if record not in existing:
        existing.append(record)
    return candidate.model_copy(update={"investigations": existing})


def exhausted_relation_pair_evidence_sets(
    relations: list[ArchitecturalRelationCandidate],
) -> list[list[str]]:
    """Evidence sets already exhausted by a relation producer, for pair discovery anti-loop context."""
    result: list[list[str]] = []
    for candidate in relations:
        for record in candidate.investigations:
            ids = sorted(record.source_observation_ids)
            if ids not in result:
                result.append(ids)
    return result


class RelationLoopNextAction(str, Enum):
    RELATION_ALTERNATIVE_REQUEST = "relation_alternative_request"
    RELATION_PAIR_REQUEST = "relation_pair_request"


def build_next_relation_loop_request(
    producer_request_id: str,
    workspace: "MultiViewWorkspace",
    candidate: ArchitecturalRelationCandidate | None = None,
) -> RelationAlternativeProducerRequest | RelationPairProducerRequest:
    """Route persisted relation-loop state to the next existing producer without architectural policy."""
    observations = [*workspace.pass_1.observations, *workspace.pass_2.observations]
    by_id = {item.id: item for item in observations}
    if candidate is not None and candidate.relation is None and not candidate.investigations:
        source_ids: list[str] = []
        for ids in candidate.source_observation_ids_by_element.values():
            for source_id in ids:
                if source_id not in source_ids:
                    source_ids.append(source_id)
        for source_id in candidate.visual_evidence_source_ids:
            if source_id not in source_ids:
                source_ids.append(source_id)
        if len(source_ids) < 2 or any(source_id not in by_id for source_id in source_ids):
            raise ValueError("relation candidate lacks sufficient known provenance for alternative producer")
        return build_relation_alternative_producer_request(
            producer_request_id,
            candidate.subject_ref,
            candidate.object_ref,
            [by_id[source_id] for source_id in source_ids],
        )
    identities = [*workspace.pass_1.identities, *workspace.pass_2.identities]
    relations = [*workspace.pass_1.relations, *workspace.pass_2.relations]
    return build_relation_pair_producer_request(
        producer_request_id,
        observations,
        identities,
        exhausted_relation_pair_evidence_sets(relations),
    )


class VisualInquiryBatchItem(BaseModel):
    """One independent, already-validated visual producer request."""
    model_config = ConfigDict(extra="forbid")
    investigation_id: str = Field(min_length=1)
    protocol: Literal["relation_pair", "relation_alternative"]
    request: RelationPairProducerRequest | RelationAlternativeProducerRequest


class VisualInquiryBatchRequest(BaseModel):
    """Transport envelope only: investigations remain independent contracts."""
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["0.1"] = "0.1"
    batch_request_id: str = Field(min_length=1)
    investigations: list[VisualInquiryBatchItem] = Field(min_length=2, max_length=5)
    batch_invariants: list[str] = Field(default_factory=lambda: ["Each result answers exactly one investigation_id.", "PAIR_PROPOSED visual_evidence_source_ids must be unique across relation_pair results in this batch."])

    @model_validator(mode="after")
    def validate_investigations(self) -> "VisualInquiryBatchRequest":
        ids=[item.investigation_id for item in self.investigations]
        if len(ids)!=len(set(ids)):
            raise ValueError("batch investigation_id values must be unique")
        for item in self.investigations:
            expected = "relation_pair" if isinstance(item.request, RelationPairProducerRequest) else "relation_alternative"
            if item.protocol != expected:
                raise ValueError("batch protocol must match embedded request contract")
        return self


class VisualInquiryBatchResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    investigation_id: str = Field(min_length=1)
    protocol: Literal["relation_pair", "relation_alternative"]
    response: RelationPairProducerResponse | RelationAlternativeProducerResponse


class VisualInquiryBatchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["0.1"] = "0.1"
    batch_request_id: str = Field(min_length=1)
    results: list[VisualInquiryBatchResult] = Field(min_length=1, max_length=5)

    @model_validator(mode="after")
    def validate_results(self) -> "VisualInquiryBatchResponse":
        ids=[item.investigation_id for item in self.results]
        if len(ids)!=len(set(ids)):
            raise ValueError("batch result investigation_id values must be unique")
        return self


def import_visual_inquiry_batch_response(
    request: VisualInquiryBatchRequest,
    response: VisualInquiryBatchResponse,
) -> list[ArchitecturalRelationCandidate | None]:
    """Validate and import every result only against its own embedded request."""
    if response.batch_request_id != request.batch_request_id:
        raise ValueError("batch_request_id mismatch")
    expected={item.investigation_id:item for item in request.investigations}
    if set(item.investigation_id for item in response.results) != set(expected):
        raise ValueError("batch results must match investigations exactly")
    imported=[]
    seen_pair_evidence: set[tuple[str, ...]] = set()
    for result in response.results:
        item=expected[result.investigation_id]
        if result.protocol != item.protocol:
            raise ValueError("batch result protocol mismatch")
        if item.protocol=="relation_pair":
            if not isinstance(result.response, RelationPairProducerResponse):
                raise ValueError("wrong response contract for relation_pair")
            imported_pair=import_relation_pair_producer_response(item.request,result.response)
            if imported_pair is not None:
                evidence=tuple(sorted(imported_pair.visual_evidence_source_ids))
                if evidence in seen_pair_evidence:
                    raise ValueError("duplicate relation-pair evidence set inside batch")
                seen_pair_evidence.add(evidence)
            if imported_pair is not None:
                imported_pair = imported_pair.model_copy(update={"batch_investigation_id": result.investigation_id})
            imported.append(imported_pair)
        else:
            if not isinstance(result.response, RelationAlternativeProducerResponse):
                raise ValueError("wrong response contract for relation_alternative")
            imported.append(import_relation_alternative_producer_response(item.request,result.response))
    return imported


def record_relation_alternative_batch_response(
    request: VisualInquiryBatchRequest,
    response: VisualInquiryBatchResponse,
    candidates: list[ArchitecturalRelationCandidate],
) -> list[ArchitecturalRelationCandidate]:
    """Apply each relation-alternative result only to its exact persisted pair and preserve exhaustion memory."""
    if response.batch_request_id != request.batch_request_id:
        raise ValueError("batch_request_id mismatch")
    expected = {item.investigation_id: item for item in request.investigations}
    if set(item.investigation_id for item in response.results) != set(expected):
        raise ValueError("batch results must match investigations exactly")
    by_pair = {(item.subject_ref, item.object_ref): item for item in candidates}
    updated = dict(by_pair)
    for result in response.results:
        item = expected[result.investigation_id]
        if item.protocol != "relation_alternative" or result.protocol != "relation_alternative":
            raise ValueError("relation-alternative batch recorder accepts only relation_alternative investigations")
        if not isinstance(item.request, RelationAlternativeProducerRequest) or not isinstance(result.response, RelationAlternativeProducerResponse):
            raise ValueError("wrong relation-alternative batch contract")
        pair = (item.request.subject_ref, item.request.object_ref)
        candidate = updated.get(pair)
        if candidate is None:
            raise ValueError("batch relation-alternative result has no persisted pair candidate")
        imported = import_relation_alternative_producer_response(item.request, result.response)
        if imported is not None:
            imported = imported.model_copy(update={
                "id": candidate.id,
                "batch_investigation_id": candidate.batch_investigation_id,
                "source_observation_ids_by_element": candidate.source_observation_ids_by_element,
                "visual_evidence_source_ids": candidate.visual_evidence_source_ids,
                "investigations": candidate.investigations,
            })
            updated[pair] = imported
        else:
            updated[pair] = record_relation_investigation(
                candidate, item.request, result.response, investigation_id=result.investigation_id
            )
    return [updated[(item.subject_ref, item.object_ref)] for item in candidates]


def build_relation_pair_batch_request(
    batch_request_id: str,
    workspace: "MultiViewWorkspace",
    *,
    max_investigations: int = 5,
) -> VisualInquiryBatchRequest:
    """Create independent pair-discovery investigations from generic persisted state."""
    if not 2 <= max_investigations <= 5:
        raise ValueError("batch size must be between 2 and 5")
    observations=[*workspace.pass_1.observations,*workspace.pass_2.observations]
    identities=[*workspace.pass_1.identities,*workspace.pass_2.identities]
    relations=[*workspace.pass_1.relations,*workspace.pass_2.relations]
    exhausted=exhausted_relation_pair_evidence_sets(relations)
    items=[]
    # Independent opaque request ids; observer remains responsible for selecting each pair.
    # To avoid artificial duplicates inside the salve, each later request also excludes
    # the exact evidence set selected by earlier returned results only on a future batch.
    for index in range(max_investigations):
        req=build_relation_pair_producer_request(
            f"{batch_request_id}-pair-{index+1}", observations, identities, exhausted
        )
        items.append(VisualInquiryBatchItem(
            investigation_id=f"{batch_request_id}-investigation-{index+1}",
            protocol="relation_pair", request=req
        ))
    return VisualInquiryBatchRequest(batch_request_id=batch_request_id,investigations=items)


def build_relation_alternative_batch_request(
    batch_request_id: str,
    workspace: "MultiViewWorkspace",
    candidates: list[ArchitecturalRelationCandidate],
) -> VisualInquiryBatchRequest:
    """Batch independent next-step relation-alternative requests selected by the existing router."""
    if not 2 <= len(candidates) <= 5:
        raise ValueError("relation-alternative batch requires between 2 and 5 candidates")
    items: list[VisualInquiryBatchItem] = []
    seen_candidate_ids: set[str] = set()
    for index, candidate in enumerate(candidates, start=1):
        if candidate.id in seen_candidate_ids:
            raise ValueError("relation-alternative batch candidates must be unique")
        seen_candidate_ids.add(candidate.id)
        request = build_next_relation_loop_request(
            f"{batch_request_id}-alternative-{index}", workspace, candidate
        )
        if not isinstance(request, RelationAlternativeProducerRequest):
            raise ValueError("candidate is not ready for relation-alternative routing")
        items.append(VisualInquiryBatchItem(
            investigation_id=f"{batch_request_id}-investigation-{index}",
            protocol="relation_alternative",
            request=request,
        ))
    return VisualInquiryBatchRequest(batch_request_id=batch_request_id, investigations=items)


class ReasoningDependency(BaseModel):
    """Explicit reasoning edge only; it carries no architectural priority by itself."""
    model_config = ConfigDict(extra="forbid")
    upstream_ref: str = Field(min_length=1)
    downstream_ref: str = Field(min_length=1)
    downstream_kind: Literal["uncertainty", "hypothesis", "topology", "future_world_representation"]


class InvestigationImpactAssessment(BaseModel):
    """Qualitative impact derived from an open uncertainty, testability, exhaustion and explicit dependencies."""
    model_config = ConfigDict(extra="forbid")
    uncertainty_id: str = Field(min_length=1)
    investigation_available: bool
    addresses_open_uncertainty: bool
    discriminating_testable: bool
    can_modify_shared_state: bool
    exhausted_or_redundant: bool
    downstream_refs: list[str] = Field(default_factory=list)
    blocked: bool


def assess_investigation_impact(
    uncertainty: StructuredUncertainty,
    *,
    discriminating_testable: bool,
    exhausted_or_redundant: bool,
    dependencies: list[ReasoningDependency],
) -> InvestigationImpactAssessment:
    """No score: state-changing impact exists only through explicit downstream dependency edges."""
    downstream = sorted({edge.downstream_ref for edge in dependencies if edge.upstream_ref == uncertainty.id})
    open_uncertainty = uncertainty.resolved_state is None and len(uncertainty.open_alternatives) >= 2
    available = open_uncertainty and not exhausted_or_redundant
    can_modify = available and discriminating_testable and bool(downstream)
    return InvestigationImpactAssessment(
        uncertainty_id=uncertainty.id,
        investigation_available=available,
        addresses_open_uncertainty=open_uncertainty,
        discriminating_testable=discriminating_testable,
        can_modify_shared_state=can_modify,
        exhausted_or_redundant=exhausted_or_redundant,
        downstream_refs=downstream,
        blocked=open_uncertainty and (exhausted_or_redundant or not discriminating_testable or not downstream),
    )


def select_impactful_investigations(
    assessments: list[InvestigationImpactAssessment],
) -> list[InvestigationImpactAssessment]:
    """Keep every non-dominated state-changing investigation; incomparable/equal impacts remain tied."""
    eligible = [item for item in assessments if item.can_modify_shared_state and not item.exhausted_or_redundant]
    result: list[InvestigationImpactAssessment] = []
    for item in eligible:
        item_refs = set(item.downstream_refs)
        dominated = any(item_refs < set(other.downstream_refs) for other in eligible)
        if not dominated:
            result.append(item)
    return result


class IdentityDiscriminant(BaseModel):
    """Explicit perceptual contract supplied for one identity candidate; never inferred."""

    id: str = Field(min_length=1)
    identity_candidate_id: str = Field(min_length=1)
    property_name: str = Field(min_length=1)
    source_ids_by_observation: dict[str, str] = Field(min_length=2)
    outcomes_by_alternative: dict[str, list[str]] = Field(min_length=2)
    required_source_ids: list[str] = Field(min_length=1)
    property_description: str | None = Field(default=None, min_length=1)
    outcome_descriptions: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_identity_discriminant(self) -> "IdentityDiscriminant":
        source_ids = list(self.source_ids_by_observation.values())
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("identity discriminant source IDs must be unique")
        if len(self.required_source_ids) != len(set(self.required_source_ids)):
            raise ValueError("identity discriminant required source IDs must be unique")
        if not set(self.required_source_ids).issubset(source_ids):
            raise ValueError("identity discriminant requires unknown source ID")
        if any(not outcomes for outcomes in self.outcomes_by_alternative.values()):
            raise ValueError("every identity alternative requires at least one outcome")
        all_outcomes = [outcome for outcomes in self.outcomes_by_alternative.values() for outcome in outcomes]
        if len(all_outcomes) != len(set(all_outcomes)):
            raise ValueError("each perceptual outcome must map to exactly one identity alternative")
        if self.outcome_descriptions and set(self.outcome_descriptions) != set(all_outcomes):
            raise ValueError("identity discriminant outcome descriptions must exactly cover outcomes")
        return self


class IdentityDiscriminantProducerStatus(str, Enum):
    DISCRIMINANT_PROPOSED = "discriminant_proposed"
    NO_RELIABLE_DISCRIMINANT = "no_reliable_discriminant"
    INSUFFICIENT_VISUAL_EVIDENCE = "insufficient_visual_evidence"


class IdentityDiscriminantProducerSource(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_id: str = Field(min_length=1)
    observation_ref: str = Field(min_length=1)
    photo_index: int = Field(ge=1)
    region: NormalizedImageRegion | None = None


class IdentityDiscriminantProducerResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["0.1"] = "0.1"
    request_id: str = Field(min_length=1)
    identity_candidate_id: str = Field(min_length=1)
    status: IdentityDiscriminantProducerStatus
    property_name: str | None = Field(default=None, min_length=1)
    property_description: str | None = Field(default=None, min_length=1)
    source_ids_by_observation: dict[str, str] | None = None
    outcomes_by_alternative: dict[str, list[str]] | None = None
    outcome_descriptions: dict[str, str] | None = None
    required_source_ids: list[str] | None = None

    @model_validator(mode="after")
    def validate_producer_shape(self) -> "IdentityDiscriminantProducerResponse":
        payload = (
            self.property_name, self.property_description, self.source_ids_by_observation,
            self.outcomes_by_alternative, self.outcome_descriptions, self.required_source_ids,
        )
        if self.status is IdentityDiscriminantProducerStatus.DISCRIMINANT_PROPOSED:
            if any(item is None for item in payload):
                raise ValueError("proposed discriminant requires complete structured payload")
        elif any(item is not None for item in payload):
            raise ValueError("inconclusive producer status cannot carry discriminant payload")
        return self


IDENTITY_DISCRIMINANT_PRODUCER_RESPONSE_INVARIANTS = (
    "response.request_id and identity_candidate_id MUST exactly match the request.",
    "DISCRIMINANT_PROPOSED requires the complete discriminant payload; NO_RELIABLE_DISCRIMINANT and INSUFFICIENT_VISUAL_EVIDENCE require every discriminant payload field to be null/absent.",
    "property_name MUST be one of request.allowed_property_names. It is an opaque machine token; property_description documents the actually observed perceptual phenomenon and MUST NOT be parsed or executed.",
    "Every outcome token MUST be one of request.allowed_outcomes. outcome_descriptions document observable outcomes and MUST NOT be parsed or executed.",
    "source_ids_by_observation MUST exactly equal the observation_ref→source_id mapping supplied by the request; no source may be invented, omitted, renamed, or duplicated.",
    "required_source_ids MUST be unique and a subset of the request source IDs.",
    "outcomes_by_alternative keys MUST exactly equal request.open_alternatives; every alternative MUST have at least one outcome; every outcome MUST map to exactly one alternative.",
    "outcome_descriptions keys MUST exactly equal all outcome tokens used by outcomes_by_alternative.",
    "General resemblance, assumed category, color alone, material alone, image proximity, architectural plausibility, statement, proposed_category, ID names, corroborating_photo_indexes alone, or conflicting_photo_indexes alone MUST NOT by themselves constitute a reliable identity discriminant.",
    "A proposed discriminant must describe a perceptual property/relation whose allowed observable outcomes have explicitly different consequences for the open alternatives. The engine does not infer those consequences from prose.",
)


def identity_discriminant_producer_response_schema() -> dict:
    return IdentityDiscriminantProducerResponse.model_json_schema()


def identity_discriminant_producer_response_invariants() -> list[str]:
    return list(IDENTITY_DISCRIMINANT_PRODUCER_RESPONSE_INVARIANTS)


class IdentityDiscriminantProducerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["0.1"] = "0.1"
    request_id: str = Field(min_length=1)
    identity_candidate_id: str = Field(min_length=1)
    instruction: str = Field(min_length=1)
    observation_ids: list[str] = Field(min_length=2)
    sources: list[IdentityDiscriminantProducerSource] = Field(min_length=2)
    open_alternatives: list[str] = Field(min_length=2)
    allowed_property_names: list[str] = Field(min_length=1)
    allowed_outcomes: list[str] = Field(min_length=2)
    response_schema: dict
    response_invariants: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_producer_request(self) -> "IdentityDiscriminantProducerRequest":
        if len(self.observation_ids) != len(set(self.observation_ids)):
            raise ValueError("producer observation IDs must be unique")
        source_ids = [item.source_id for item in self.sources]
        refs = [item.observation_ref for item in self.sources]
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("producer source IDs must be unique")
        if len(refs) != len(set(refs)) or set(refs) != set(self.observation_ids):
            raise ValueError("producer sources must exactly cover observations")
        if len(self.allowed_property_names) != len(set(self.allowed_property_names)):
            raise ValueError("allowed property tokens must be unique")
        if len(self.allowed_outcomes) != len(set(self.allowed_outcomes)):
            raise ValueError("allowed outcome tokens must be unique")
        return self


def build_identity_discriminant_producer_request(
    candidate: IdentityCandidate,
    observations: list[LocalObservation],
) -> IdentityDiscriminantProducerRequest | None:
    if candidate.inquiry_state is not IdentityInquiryState.OPEN_ALTERNATIVES:
        return None
    observation_by_id = {item.id: item for item in observations}
    if not set(candidate.observation_ids).issubset(observation_by_id):
        raise ValueError("identity candidate references unknown observation")
    sources = [
        IdentityDiscriminantProducerSource(
            source_id=f"identity-source-{index + 1}",
            observation_ref=observation_id,
            photo_index=observation_by_id[observation_id].photo_index,
            region=observation_by_id[observation_id].region,
        )
        for index, observation_id in enumerate(candidate.observation_ids)
    ]
    return IdentityDiscriminantProducerRequest(
        request_id=f"identity-discriminant-request-{candidate.id}",
        identity_candidate_id=candidate.id,
        instruction=(
            "Inspect only the supplied visual sources. Do NOT decide whether they are the same physical object. "
            "Decide only whether the pixels support a precise perceptual discriminant whose observable outcomes "
            "would differ across the already-open alternatives. If no such reliable discriminant exists, return "
            "NO_RELIABLE_DISCRIMINANT; if the pixels cannot support the inquiry, return INSUFFICIENT_VISUAL_EVIDENCE. "
            "For a proposal, choose one opaque property token and opaque outcome tokens only from the allowed lists, "
            "and document their perceptual meaning in the non-executable description fields. Do not infer from general "
            "resemblance, category, color alone, material alone, image proximity, architectural plausibility, statements, "
            "proposed categories, IDs, or support/conflict photo indexes."
        ),
        observation_ids=list(candidate.observation_ids),
        sources=sources,
        open_alternatives=[item.value for item in candidate.open_alternatives],
        allowed_property_names=["perceptual_discriminant_1", "perceptual_discriminant_2", "perceptual_discriminant_3"],
        allowed_outcomes=["outcome_alpha", "outcome_beta", "outcome_gamma", "outcome_delta"],
        response_schema=identity_discriminant_producer_response_schema(),
        response_invariants=identity_discriminant_producer_response_invariants(),
    )


def import_identity_discriminant_producer_response(
    request: IdentityDiscriminantProducerRequest,
    response: IdentityDiscriminantProducerResponse,
) -> IdentityDiscriminant | None:
    if response.request_id != request.request_id or response.identity_candidate_id != request.identity_candidate_id:
        raise ValueError("identity discriminant producer response does not match request")
    if response.status is not IdentityDiscriminantProducerStatus.DISCRIMINANT_PROPOSED:
        return None
    if response.property_name not in request.allowed_property_names:
        raise ValueError("identity discriminant property token is not allowed")
    expected_sources = {item.observation_ref: item.source_id for item in request.sources}
    if response.source_ids_by_observation != expected_sources:
        raise ValueError("identity discriminant source mapping does not exactly match request")
    source_ids = list(response.source_ids_by_observation.values())
    if len(source_ids) != len(set(source_ids)):
        raise ValueError("identity discriminant source IDs must be unique")
    if len(response.required_source_ids) != len(set(response.required_source_ids)):
        raise ValueError("identity discriminant required source IDs must be unique")
    if not set(response.required_source_ids).issubset(source_ids):
        raise ValueError("identity discriminant requires unknown source ID")
    if set(response.outcomes_by_alternative) != set(request.open_alternatives):
        raise ValueError("identity discriminant alternatives do not exactly match request")
    used = [outcome for outcomes in response.outcomes_by_alternative.values() for outcome in outcomes]
    if any(outcome not in request.allowed_outcomes for outcome in used):
        raise ValueError("identity discriminant outcome token is not allowed")
    if any(not outcomes for outcomes in response.outcomes_by_alternative.values()):
        raise ValueError("every identity alternative requires at least one outcome")
    if len(used) != len(set(used)):
        raise ValueError("each perceptual outcome must map to exactly one identity alternative")
    if set(response.outcome_descriptions) != set(used):
        raise ValueError("outcome descriptions must exactly cover used outcome tokens")
    return IdentityDiscriminant(
        id=f"identity-discriminant-{request.identity_candidate_id}",
        identity_candidate_id=request.identity_candidate_id,
        property_name=response.property_name,
        source_ids_by_observation=dict(response.source_ids_by_observation),
        outcomes_by_alternative={key: list(value) for key, value in response.outcomes_by_alternative.items()},
        required_source_ids=list(response.required_source_ids),
        property_description=response.property_description,
        outcome_descriptions=dict(response.outcome_descriptions),
    )


class IdentityInquiryArtifacts(BaseModel):
    """Identity-specific input adapter feeding the existing generic inquiry pipeline."""

    hypotheses: list[OpenHypothesis]
    predictions: list[ObservablePrediction]
    question: DiscriminatingQuestion
    target: CandidateEvidenceTarget
    assessment: DiscriminationAssessment
    selection: EvidenceTargetSelection
    inquiry: "VisualInquiry"


class CandidateEvidenceTarget(BaseModel):
    """One atomic target, optionally composed of several visual sources."""

    # Legacy mono-source representation remains readable for 008-032.
    photo_index: int | None = Field(default=None, ge=1)
    region: NormalizedImageRegion | None = None
    source_observation_ids: list[str] = Field(min_length=1)
    discriminant_property: str = Field(min_length=1)
    visibility: VisibilityStatus = VisibilityStatus.VISIBLE
    testable: bool
    reason: str = Field(min_length=1)
    evidence_regions: list[EvidenceRegion] = Field(default_factory=list)
    requires_exhaustive_sources: bool = True
    composite_sufficiency: CompositeSufficiencyContract | None = None

    @model_validator(mode="after")
    def validate_evidence_shape(self) -> "CandidateEvidenceTarget":
        if self.evidence_regions:
            source_ids = [item.source_id for item in self.evidence_regions]
            if len(source_ids) != len(set(source_ids)):
                raise ValueError("composite evidence source IDs must be unique")
            if self.photo_index is not None or self.region is not None:
                raise ValueError("composite target cannot also carry legacy photo/region")
            if self.composite_sufficiency is not None and not set(self.composite_sufficiency.required_source_ids).issubset(source_ids):
                raise ValueError("composite target sufficiency references unknown source ID")
            refs = [item.observation_ref for item in self.evidence_regions if item.observation_ref]
            if set(refs) != set(self.source_observation_ids):
                raise ValueError("composite evidence provenance must match source observations")
        elif self.photo_index is None or self.region is None:
            raise ValueError("legacy target requires photo_index and region")
        return self


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
    def target_key(item: CandidateEvidenceTarget) -> tuple:
        if item.evidence_regions:
            sources = tuple(sorted(
                (
                    source.source_id,
                    source.photo_index,
                    None if source.region is None else (
                        source.region.x0, source.region.y0, source.region.x1, source.region.y1
                    ),
                )
                for source in item.evidence_regions
            ))
            return (1, sources, tuple(sorted(item.source_observation_ids)), item.discriminant_property)
        return (
            0,
            item.photo_index,
            item.region.x0,
            item.region.y0,
            item.region.x1,
            item.region.y1,
            tuple(item.source_observation_ids),
            item.discriminant_property,
        )

    canonical = sorted(best, key=target_key)
    return EvidenceTargetSelection(
        best_candidates=canonical,
        tied=len(canonical) > 1,
        reason=(
            "Multiple candidates have equal best discrimination potential."
            if len(canonical) > 1
            else "One candidate has uniquely best discrimination potential."
        ),
    )


class CompositeSufficiencyContract(BaseModel):
    """Minimal declarative rule: these exact source IDs must be usable."""

    required_source_ids: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_required_sources(self) -> "CompositeSufficiencyContract":
        if len(self.required_source_ids) != len(set(self.required_source_ids)):
            raise ValueError("composite sufficiency source IDs must be unique")
        return self


class DiscriminatingTest(BaseModel):
    """One atomic test; composite evidence is never exploded into independent tests."""

    id: str = Field(min_length=1)
    photo_index: int | None = Field(default=None, ge=1)
    region: NormalizedImageRegion | None = None
    prediction_ids: list[str] = Field(min_length=2)
    evidence_sought: str = Field(min_length=1)
    source_observation_ids: list[str] = Field(default_factory=list)
    evidence_regions: list[EvidenceRegion] = Field(default_factory=list)
    composite_sufficiency: CompositeSufficiencyContract | None = None

    @model_validator(mode="after")
    def validate_test_evidence_shape(self) -> "DiscriminatingTest":
        if self.evidence_regions:
            source_ids = [item.source_id for item in self.evidence_regions]
            if len(source_ids) != len(set(source_ids)):
                raise ValueError("composite test source IDs must be unique")
            if self.photo_index is not None or self.region is not None:
                raise ValueError("composite test cannot also carry legacy photo/region")
            if self.composite_sufficiency is not None:
                known = set(source_ids)
                required = self.composite_sufficiency.required_source_ids
                if not set(required).issubset(known):
                    raise ValueError("composite sufficiency references unknown source ID")
        elif self.photo_index is None or self.region is None:
            raise ValueError("legacy test requires photo_index and region")
        return self


class InquiryTestResult(BaseModel):
    """Recorded inspection result; composite results remain atomic and fail closed."""

    test_id: str = Field(min_length=1)
    inspected: bool
    region_in_frame: bool
    visibility: VisibilityStatus
    sufficient_visibility: bool
    statement: str = Field(min_length=1)
    compatible_prediction_ids: list[str] = Field(default_factory=list)
    discriminating: bool = False
    composite_sources: list[EvidenceRegion] = Field(default_factory=list)
    composite_source_statuses: dict[str, str] = Field(default_factory=dict)
    composite_outcome: str | None = None

    @model_validator(mode="after")
    def validate_discriminating_absence(self) -> "InquiryTestResult":
        if self.discriminating and (
            not self.inspected or not self.region_in_frame or not self.sufficient_visibility
        ):
            raise ValueError(
                "discriminating evidence requires an inspected, in-frame, sufficiently visible ROI"
            )
        if (
            self.discriminating
            and not self.composite_sources
            and self.visibility in {VisibilityStatus.OCCLUDED, VisibilityStatus.NON_VISIBLE}
        ):
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


def build_identity_enquiry_bootstrap_request(
    bootstrap_id: str,
    photo_filenames: list[str],
) -> VisualBootstrapRequest:
    """Fresh bootstrap request that may create 035-enquirable candidates; no historical enrichment."""

    base = build_visual_bootstrap_request(bootstrap_id, photo_filenames)
    return base.model_copy(update={
        "schema_version": "0.4",
        "instruction": (
            base.instruction
            + " For cross-view identity candidates, do not decide identity from resemblance. "
              "When pixels justify a genuine unresolved identity competition, you MAY emit inquiry_state='open_alternatives' "
              "with exactly the alternatives 'same_physical_object' and 'incompatible'. If that explicit competition is not "
              "justified, retain the legacy/default non-enquirable form. Do not invent a discriminant in this bootstrap response; "
              "a subsequent machine request will ask for one only for explicitly enquirable candidates."
        ),
        "information_to_record": [
            *base.information_to_record,
            "Identity inquiry readiness: only a genuinely unresolved cross-view identity competition may use inquiry_state='open_alternatives' with exactly ['same_physical_object','incompatible']; otherwise use the non-enquirable legacy/default form.",
        ],
        "epistemic_rules": [
            *base.epistemic_rules,
            "likely_same != open_alternatives",
            "unresolved != automatically_enquirable",
            "corroborating_photo_indexes != identity_discriminant",
            "conflicting_photo_indexes != identity_discriminant",
        ],
    })


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
    schema_version: str = "0.2"
    request_id: str = Field(min_length=1)
    inquiry_id: str = Field(min_length=1)
    instruction: str = Field(min_length=1)
    subject_ref: str = Field(min_length=1)
    property_name: str = Field(min_length=1)
    question: DiscriminatingQuestion
    predictions: list[ObservablePrediction] = Field(min_length=2)
    target: CandidateEvidenceTarget
    test_id: str = Field(min_length=1)
    composite_sufficiency: CompositeSufficiencyContract | None = None
    observability_requirements: list[str] = Field(min_length=1)
    response_schema: dict
    response_invariants: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_exchange_version(self) -> "VisualInquiryRequest":
        expected = "0.3" if self.target.evidence_regions else "0.2"
        if self.schema_version != expected:
            raise ValueError(f"request schema_version must be {expected} for this evidence shape")
        return self


class CompositeSourceResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_id: str = Field(min_length=1)
    observation_ref: str | None = Field(default=None, min_length=1)
    photo_index: int = Field(ge=1)
    region: NormalizedImageRegion | None = None
    status: VisualEvidenceStatus
    local_value: str | None = None
    certainty: CertaintyLevel = CertaintyLevel.UNKNOWN


class VisualEvidenceResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    RESPONSE_INVARIANTS: ClassVar[tuple[str, ...]] = (
        "Legacy: if status is 'observed' or 'not_observed', observed_value MUST be present; if status is 'occluded', 'non_visible', 'ambiguous', or 'insufficient_evidence', observed_value MUST be null/absent and MUST NOT be used as visible/absent evidence.",
        "Legacy: response.photo_index, response.region and response.source_observation_ids MUST exactly match the mono-source request target.",
        "Legacy mono-source responses preserve the 030 contract; composite responses use schema_version 0.3 and MUST NOT carry legacy mono-source evidence fields.",
        "Composite source_results are matched by source_id, not list position; source_id values MUST be unique.",
        "Each composite source_result MUST exactly match its requested observation_ref, photo_index and region; null requested region MUST remain null.",
        "No unknown composite source is allowed. If request.target.requires_exhaustive_sources is true, every requested source MUST occur exactly once.",
        "A decisive composite_status ('observed' or 'not_observed') MUST carry composite_outcome; every inconclusive composite_status MUST carry no composite_outcome.",
        "composite_outcome MUST be one of the structured outcomes allowed by request.question for request.property_name.",
        "Local source status/value never manufactures composite_outcome. Occluded/non-visible/missing sources never imply a negative outcome.",
        "Composite evidence has no executable sufficiency rule in schema 0.3; imported composite results MUST remain non-discriminating and fail closed.",
        "response.request_id, inquiry_id, test_id and property_name MUST exactly match the request.",
    )
    schema_version: str = "0.1"
    request_id: str = Field(min_length=1)
    inquiry_id: str = Field(min_length=1)
    test_id: str = Field(min_length=1)
    property_name: str = Field(min_length=1)

    # Historical 030 mono-source shape.
    photo_index: int | None = Field(default=None, ge=1)
    region: NormalizedImageRegion | None = None
    status: VisualEvidenceStatus | None = None
    observed_value: str | None = None
    certainty: CertaintyLevel = CertaintyLevel.UNKNOWN
    source_observation_ids: list[str] | None = None

    # 038 composite shape.  The global outcome is intentionally separate from local results.
    source_results: list[CompositeSourceResult] = Field(default_factory=list)
    composite_status: VisualEvidenceStatus | None = None
    composite_outcome: str | None = None
    comment: str | None = None

    @model_validator(mode="after")
    def validate_structured_result(self) -> "VisualEvidenceResponse":
        composite = bool(self.source_results) or self.composite_status is not None or self.composite_outcome is not None
        legacy = self.photo_index is not None or self.region is not None or self.status is not None or self.source_observation_ids is not None
        if composite:
            if legacy:
                raise ValueError("composite response cannot also carry legacy mono-source evidence fields")
            if self.schema_version != "0.3":
                raise ValueError("composite response requires schema_version 0.3")
            if not self.source_results or self.composite_status is None:
                raise ValueError("composite response requires source_results and composite_status")
            ids = [item.source_id for item in self.source_results]
            if len(ids) != len(set(ids)):
                raise ValueError("composite response source IDs must be unique")
            decisive = self.composite_status in {VisualEvidenceStatus.OBSERVED, VisualEvidenceStatus.NOT_OBSERVED}
            if decisive != (self.composite_outcome is not None):
                raise ValueError("composite outcome presence must match decisive composite status")
            if self.observed_value is not None:
                raise ValueError("composite response cannot carry legacy observed_value")
        else:
            if self.photo_index is None or self.region is None or self.status is None or not self.source_observation_ids:
                raise ValueError("legacy response requires photo_index, region, status and source_observation_ids")
            decisive = self.status in {VisualEvidenceStatus.OBSERVED, VisualEvidenceStatus.NOT_OBSERVED}
            if decisive and self.observed_value is None:
                raise ValueError("decisive visual evidence requires a structured observed_value")
            if not decisive and self.observed_value is not None:
                raise ValueError("inconclusive visual evidence cannot carry an observed_value")
        return self


def visual_evidence_response_schema() -> dict:
    """Exact machine schema exposed to an external visual observer."""
    return VisualEvidenceResponse.model_json_schema()


def visual_evidence_response_invariants() -> list[str]:
    """Machine contract owned by the exact response model/import protocol."""
    return list(VisualEvidenceResponse.RESPONSE_INVARIANTS)


def exclude_already_investigated_targets(
    uncertainty: StructuredUncertainty,
    assessments: list[DiscriminationAssessment],
    inquiries: list["VisualInquiry"],
) -> list[DiscriminationAssessment]:
    """Remove only structurally identical evidence targets already inspected.

    The uncertainty remains open.  Existing inquiry test_results are the sole
    investigation memory; no parallel truth/history store is introduced.
    """

    def same_target(test: DiscriminatingTest, target: CandidateEvidenceTarget) -> bool:
        if test.evidence_sought != target.discriminant_property:
            return False
        if set(test.source_observation_ids) != set(target.source_observation_ids):
            return False
        if target.evidence_regions:
            if not test.evidence_regions:
                return False
            left = {
                item.source_id: (
                    item.observation_ref, item.photo_index, item.region
                )
                for item in target.evidence_regions
            }
            right = {
                item.source_id: (
                    item.observation_ref, item.photo_index, item.region
                )
                for item in test.evidence_regions
            }
            return left == right
        return (
            not test.evidence_regions
            and test.photo_index == target.photo_index
            and test.region == target.region
        )

    exhausted: list[DiscriminatingTest] = []
    for inquiry in inquiries:
        if inquiry.id != f"inquiry-{uncertainty.id}":
            continue
        inspected_ids = {item.test_id for item in inquiry.test_results if item.inspected}
        exhausted.extend(item for item in inquiry.tests if item.id in inspected_ids)

    return [
        assessment
        for assessment in assessments
        if not any(same_target(test, assessment.target) for test in exhausted)
    ]


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
    if target.evidence_regions:
        # Transport is now lossless through the persisted inquiry.  Without an explicit
        # composite sufficiency rule, however, execution must remain fail-closed.
        test = DiscriminatingTest(
            id=f"test-{uncertainty.id}-composite-{target.discriminant_property}-{source_token}",
            prediction_ids=list(question.prediction_ids),
            evidence_sought=target.discriminant_property,
            source_observation_ids=list(target.source_observation_ids),
            evidence_regions=list(target.evidence_regions),
            composite_sufficiency=target.composite_sufficiency,
        )
    else:
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


def build_identity_discriminant_inquiry(
    candidate: IdentityCandidate,
    uncertainty: StructuredUncertainty,
    discriminant: IdentityDiscriminant | None,
    observations: list[LocalObservation],
) -> IdentityInquiryArtifacts | None:
    """Consume an explicitly supplied identity discriminant; infer no identity semantics."""

    if discriminant is None:
        return None
    if uncertainty.source_kind != "identity_candidate" or uncertainty.source_ref != candidate.id:
        raise ValueError("identity uncertainty does not belong to candidate")
    if discriminant.identity_candidate_id != candidate.id:
        raise ValueError("identity discriminant belongs to another candidate")
    if set(discriminant.source_ids_by_observation) != set(candidate.observation_ids):
        raise ValueError("identity discriminant must reference exactly candidate observations")
    observation_by_id = {item.id: item for item in observations}
    if not set(candidate.observation_ids).issubset(observation_by_id):
        raise ValueError("identity discriminant references unknown observation")

    alternatives = [item.value for item in candidate.open_alternatives]
    if set(discriminant.outcomes_by_alternative) != set(alternatives):
        raise ValueError("identity discriminant must map every and only open alternative")
    # The current generic question model has one expected outcome per hypothesis.
    # Multiple outcomes per alternative are valid contractually but cannot be represented
    # by this vertical slice, so fail closed rather than inventing a policy.
    if any(len(items) != 1 for items in discriminant.outcomes_by_alternative.values()):
        return None
    mapped = {alt: values[0] for alt, values in discriminant.outcomes_by_alternative.items()}
    if len(set(mapped.values())) < 2:
        return None

    hypothesis_ids = [f"{uncertainty.id}-{index}" for index, _ in enumerate(alternatives)]
    hypotheses = [
        OpenHypothesis(
            id=hypothesis_id,
            subject_refs=[candidate.id],
            statement="Structured identity alternative supplied by explicit inquiry contract.",
            competing_with=[other for other in hypothesis_ids if other != hypothesis_id],
            claim=HypothesisClaim(subject_ref=candidate.id, relation=alternative),
            source_uncertainty_id=uncertainty.id,
        )
        for hypothesis_id, alternative in zip(hypothesis_ids, alternatives)
    ]
    predictions = [
        ObservablePrediction(
            id=f"derived-{hypothesis.id}",
            hypothesis_id=hypothesis.id,
            statement="Opaque perceptual outcome supplied by explicit identity discriminant.",
            observable_properties=[
                ObservableProperty(name=discriminant.property_name, value=mapped[hypothesis.claim.relation])
            ],
        )
        for hypothesis in hypotheses
    ]
    question = derive_discriminating_question(predictions)
    if question is None:
        return None

    evidence_regions = [
        EvidenceRegion(
            source_id=discriminant.source_ids_by_observation[observation_id],
            observation_ref=observation_id,
            photo_index=observation_by_id[observation_id].photo_index,
            region=observation_by_id[observation_id].region,
            visibility=observation_by_id[observation_id].visibility,
        )
        for observation_id in candidate.observation_ids
    ]
    target = CandidateEvidenceTarget(
        source_observation_ids=list(candidate.observation_ids),
        discriminant_property=discriminant.property_name,
        visibility=VisibilityStatus.VISIBLE,
        testable=all(
            observation_by_id[item].status is ClaimStatus.OBSERVED
            and observation_by_id[item].visibility is VisibilityStatus.VISIBLE
            for item in candidate.observation_ids
        ),
        reason="Explicit identity discriminant supplies this atomic multiview evidence target.",
        evidence_regions=evidence_regions,
        requires_exhaustive_sources=False,
        composite_sufficiency=CompositeSufficiencyContract(
            required_source_ids=list(discriminant.required_source_ids)
        ),
    )
    assessment = DiscriminationAssessment(
        target=target,
        potential=(
            DiscriminationPotential.DISCRIMINATING
            if target.testable else DiscriminationPotential.NONE
        ),
        discriminant_applicability=(
            ApplicabilityState.APPLICABLE if target.testable else ApplicabilityState.UNKNOWN
        ),
        expected_outcomes_distinct=True,
        reason="Applicability is explicitly licensed by the supplied structured discriminant.",
    )
    selection = select_discrimination_targets([assessment])
    inquiry = build_executable_visual_inquiry(
        uncertainty, hypotheses, predictions, question, [assessment], selection
    )
    if inquiry is None:
        return None
    return IdentityInquiryArtifacts(
        hypotheses=hypotheses,
        predictions=predictions,
        question=question,
        target=target,
        assessment=assessment,
        selection=selection,
        inquiry=inquiry,
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

    def same_composite_sources(test: DiscriminatingTest) -> bool:
        if not target.evidence_regions or not test.evidence_regions:
            return False
        left = {item.source_id: item for item in target.evidence_regions}
        right = {item.source_id: item for item in test.evidence_regions}
        return left == right and test.source_observation_ids == target.source_observation_ids

    test = next(
        (
            item for item in inquiry.tests
            if item.evidence_sought == target.discriminant_property
            and (
                same_composite_sources(item)
                if target.evidence_regions
                else (
                    not item.evidence_regions
                    and item.photo_index == target.photo_index
                    and item.region == target.region
                    and (not item.source_observation_ids or item.source_observation_ids == target.source_observation_ids)
                )
            )
        ),
        None,
    )
    if test is None:
        raise ValueError("candidate target must correspond to an inquiry test")

    composite = bool(target.evidence_regions)
    return VisualInquiryRequest(
        schema_version="0.3" if composite else "0.2",
        request_id=f"request-{inquiry.id}-{test.id}",
        inquiry_id=inquiry.id,
        instruction=(
            "Inspect jointly all referenced evidence sources and return one atomic VisualEvidenceResponse. "
            "Report each source locally, and report the composite outcome separately. Never derive the "
            "composite outcome by concatenating local states; if the joint evidence is insufficient, "
            "return an inconclusive composite status."
            if composite else
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
        composite_sufficiency=test.composite_sufficiency,
        observability_requirements=[
            "source_identity_and_provenance_exact",
            "report_each_inspected_source_without_inventing_roi",
            "composite_outcome_separate_from_local_source_results",
        ] if composite else [
            "region_in_frame",
            "non_occluded",
            "sufficient_visibility",
        ],
        response_schema=visual_evidence_response_schema(),
        response_invariants=visual_evidence_response_invariants(),
    )



def import_visual_evidence_response(
    request: VisualInquiryRequest,
    response: VisualEvidenceResponse,
) -> InquiryTestResult:
    if (
        response.request_id != request.request_id
        or response.inquiry_id != request.inquiry_id
        or response.test_id != request.test_id
        or response.property_name != request.property_name
    ):
        raise ValueError("visual evidence response provenance does not match request")

    if request.target.evidence_regions:
        if response.schema_version != "0.3" or not response.source_results:
            raise ValueError("composite request requires a composite response")
        expected = {item.source_id: item for item in request.target.evidence_regions}
        actual = {item.source_id: item for item in response.source_results}
        if len(actual) != len(response.source_results):
            raise ValueError("duplicate composite response source")
        if not set(actual).issubset(expected):
            raise ValueError("unexpected composite response source")
        if request.target.requires_exhaustive_sources and set(actual) != set(expected):
            raise ValueError("composite response is missing required evidence sources")
        for source_id, result in actual.items():
            wanted = expected[source_id]
            if (
                result.observation_ref != wanted.observation_ref
                or result.photo_index != wanted.photo_index
                or result.region != wanted.region
            ):
                raise ValueError("composite source provenance does not match request")
        outcomes = {
            value
            for discriminant in request.question.discriminants
            if discriminant.property_name == request.property_name
            for value in discriminant.expected_outcomes.values()
        }
        if response.composite_outcome is not None and response.composite_outcome not in outcomes:
            raise ValueError("composite_outcome is not an allowed structured outcome")

        # Sufficiency belongs to this exact test. Old 038 composites carry no contract
        # and therefore remain fail-closed. A source is usable only when its local status is
        # decisive visual evidence; inconclusive statuses are never converted to absence.
        contract = request.composite_sufficiency
        required = set(contract.required_source_ids) if contract is not None else set()
        usable = {
            item.source_id
            for item in response.source_results
            if item.status in {VisualEvidenceStatus.OBSERVED, VisualEvidenceStatus.NOT_OBSERVED}
        }
        sufficient = contract is not None and required.issubset(usable)
        compatible = list(request.question.prediction_ids)
        discriminating = False
        if sufficient and response.composite_outcome is not None:
            expected_by_hypothesis = {
                hypothesis_id: value
                for discriminant in request.question.discriminants
                if discriminant.property_name == request.property_name
                for hypothesis_id, value in discriminant.expected_outcomes.items()
            }
            compatible = [
                prediction_id
                for prediction_id in request.question.prediction_ids
                if expected_by_hypothesis.get(
                    next(item.hypothesis_id for item in request.predictions if item.id == prediction_id)
                ) == response.composite_outcome
            ]
            if not compatible:
                raise ValueError("structured composite_outcome matches no expected outcome")
            discriminating = len(compatible) < len(request.question.prediction_ids)

        sources = [
            EvidenceRegion(
                source_id=item.source_id,
                observation_ref=item.observation_ref,
                photo_index=item.photo_index,
                region=item.region,
                visibility=(
                    VisibilityStatus.OCCLUDED if item.status is VisualEvidenceStatus.OCCLUDED
                    else VisibilityStatus.NON_VISIBLE if item.status is VisualEvidenceStatus.NON_VISIBLE
                    else VisibilityStatus.VISIBLE
                ),
            )
            for item in response.source_results
        ]
        return InquiryTestResult(
            test_id=request.test_id,
            inspected=True,
            region_in_frame=all(item.status is not VisualEvidenceStatus.NON_VISIBLE for item in response.source_results),
            visibility=(
                VisibilityStatus.OCCLUDED if any(item.status is VisualEvidenceStatus.OCCLUDED for item in response.source_results)
                else VisibilityStatus.NON_VISIBLE if any(item.status is VisualEvidenceStatus.NON_VISIBLE for item in response.source_results)
                else VisibilityStatus.VISIBLE
            ),
            sufficient_visibility=sufficient,
            statement=response.comment or (
                "Structured composite external visual evidence imported with sufficient required sources."
                if sufficient else
                "Structured composite external visual evidence imported; required-source sufficiency not established."
            ),
            compatible_prediction_ids=compatible,
            discriminating=discriminating,
            composite_sources=sources,
            composite_source_statuses={item.source_id: item.status.value for item in response.source_results},
            composite_outcome=response.composite_outcome,
        )

    # Historical 030 mono-source importer semantics remain unchanged.
    if (
        response.photo_index != request.target.photo_index
        or response.region != request.target.region
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
        if outcomes.get(next(item.hypothesis_id for item in request.predictions if item.id == prediction_id))
        == response.observed_value
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
    identity_discriminants: list[IdentityDiscriminant] = Field(default_factory=list)
    reasoning_dependencies: list[ReasoningDependency] = Field(default_factory=list)

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
            for relation in phase.relations:
                for alternative in relation.open_alternatives:
                    unknown = set(alternative.source_observation_ids) - known_ids
                    if unknown:
                        raise ValueError(
                            f"relation alternative provenance references unknown observations: {sorted(unknown)}"
                        )
            for item in phase.observations:
                if item.photo_index > self.photo_count:
                    raise ValueError("observation references photo outside supplied input")
            for assessment in phase.view_assessments:
                if assessment.photo_index > self.photo_count:
                    raise ValueError("view assessment references photo outside supplied input")
        identities = {item.id: item for item in self.pass_1.identities + self.pass_2.identities}
        discriminant_ids = [item.id for item in self.identity_discriminants]
        if len(discriminant_ids) != len(set(discriminant_ids)):
            raise ValueError("workspace identity discriminant IDs must be unique")
        for discriminant in self.identity_discriminants:
            candidate = identities.get(discriminant.identity_candidate_id)
            if candidate is None:
                raise ValueError("identity discriminant references unknown identity candidate")
            if set(discriminant.source_ids_by_observation) != set(candidate.observation_ids):
                raise ValueError("identity discriminant observations must exactly match identity candidate")

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
                if test.evidence_regions:
                    if any(source.photo_index > self.photo_count for source in test.evidence_regions):
                        raise ValueError("inquiry test evidence references photo outside supplied input")
                elif test.photo_index is not None and test.photo_index > self.photo_count:
                    raise ValueError("inquiry test references photo outside supplied input")
        return self
