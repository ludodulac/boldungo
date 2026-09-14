"""Evidence-backed multi-view identity for Survey observations.

A Survey observation may fuse appearances from several photos into one physical
object identity. This module validates only explicit correspondence metadata; it
never infers identity from similarity, facade labels, proximity or projection.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, ValidationError, model_validator

from .models import ArchitecturalSurvey, Certainty
from .validation import SurveyValidationIssue


IdentityStatus = Literal["same_physical_object", "unresolved"]
IdentityCue = Literal[
    "shape_detail",
    "relative_position",
    "structural_continuity",
    "occlusion_continuity",
    "facade_transition",
    "user_statement",
]


class MultiViewIdentityValue(BaseModel):
    status: IdentityStatus
    photo_indexes: list[int] = Field(min_length=2)
    cues: list[IdentityCue] = Field(default_factory=list)
    supporting_relation_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_value(self) -> "MultiViewIdentityValue":
        if len(self.photo_indexes) != len(set(self.photo_indexes)):
            raise ValueError("photo_indexes must be unique")
        if any(index < 1 for index in self.photo_indexes):
            raise ValueError("photo_indexes must contain positive photo indexes")
        if len(self.cues) != len(set(self.cues)):
            raise ValueError("cues must be unique")
        if len(self.supporting_relation_ids) != len(set(self.supporting_relation_ids)):
            raise ValueError("supporting_relation_ids must be unique")
        return self


class MultiViewIdentityFacts(BaseModel):
    observation_id: str
    identity: MultiViewIdentityValue
    certainty: Certainty


class MultiViewIdentityReport(BaseModel):
    facts: list[MultiViewIdentityFacts] = Field(default_factory=list)
    issues: list[SurveyValidationIssue] = Field(default_factory=list)

    model_config = {"arbitrary_types_allowed": True}


def _issue(observation_id: str, code: str, message: str) -> SurveyValidationIssue:
    return SurveyValidationIssue(code=code, observation_id=observation_id, message=message)


def analyze_multiview_identity(survey: ArchitecturalSurvey) -> MultiViewIdentityReport:
    """Validate explicit cross-view correspondence without creating any identity."""

    facts: list[MultiViewIdentityFacts] = []
    issues: list[SurveyValidationIssue] = []
    relations_by_id = {relation.id: relation for relation in survey.relations}

    for observation in sorted(survey.observations, key=lambda item: item.id):
        raw = observation.attributes.get("multiview_identity")
        if raw is None:
            continue
        try:
            identity = MultiViewIdentityValue.model_validate(raw)
        except ValidationError as exc:
            issues.append(_issue(
                observation.id,
                "invalid_multiview_identity",
                f"attributes.multiview_identity is inconsistent: {exc.errors()[0]['msg']}",
            ))
            continue

        evidence_photos = {item.photo_index for item in observation.evidence}
        missing = [index for index in identity.photo_indexes if index not in evidence_photos]
        if missing:
            issues.append(_issue(
                observation.id,
                "multiview_identity_missing_evidence_photo",
                f"multiview identity references photo indexes without observation evidence: {missing}",
            ))

        identity_photos = set(identity.photo_indexes)
        supporting_relations = []
        for relation_id in identity.supporting_relation_ids:
            relation = relations_by_id.get(relation_id)
            if relation is None:
                issues.append(_issue(
                    observation.id,
                    "multiview_identity_support_relation_missing",
                    f"multiview identity references unknown SurveyRelation {relation_id!r}",
                ))
                continue
            relation_observations = {relation.subject_id, relation.object_id}
            relation_photos = {item.photo_index for item in relation.evidence}
            if observation.id not in relation_observations or not (identity_photos & relation_photos):
                issues.append(_issue(
                    observation.id,
                    "multiview_identity_support_relation_not_relevant",
                    (
                        f"SurveyRelation {relation_id!r} does not provide local evidence for "
                        f"observation {observation.id!r} in the identity photo set"
                    ),
                ))
                continue
            supporting_relations.append(relation)

        certainty = observation.certainty_for_attribute("multiview_identity")
        if identity.status == "unresolved" and certainty is Certainty.CERTAIN:
            issues.append(_issue(
                observation.id,
                "unresolved_multiview_identity_cannot_be_certain",
                "multiview_identity status='unresolved' cannot carry certainty='certain'",
            ))
        if (
            identity.status == "same_physical_object"
            and certainty is Certainty.CERTAIN
            and not identity.cues
        ):
            issues.append(_issue(
                observation.id,
                "certain_multiview_identity_missing_discriminating_cue",
                "certain same_physical_object identity requires at least one discriminating evidence cue",
            ))
        if (
            identity.status == "same_physical_object"
            and certainty is Certainty.CERTAIN
            and identity.cues == ["relative_position"]
            and not identity.supporting_relation_ids
        ):
            issues.append(_issue(
                observation.id,
                "certain_multiview_identity_relative_position_requires_relation_evidence",
                (
                    "relative_position text alone cannot make same_physical_object identity certain; "
                    "cite supporting SurveyRelation IDs or keep the identity below certain"
                ),
            ))
        if (
            identity.status == "same_physical_object"
            and certainty is Certainty.CERTAIN
            and supporting_relations
            and any(relation.certainty is not Certainty.CERTAIN for relation in supporting_relations)
        ):
            issues.append(_issue(
                observation.id,
                "certain_multiview_identity_requires_certain_relation_support",
                (
                    "same_physical_object identity cannot be certain when an explicitly cited "
                    "supporting SurveyRelation is below certain"
                ),
            ))

        facts.append(MultiViewIdentityFacts(
            observation_id=observation.id,
            identity=identity,
            certainty=certainty,
        ))

    return MultiViewIdentityReport(facts=facts, issues=issues)


def validate_multiview_identity(survey: ArchitecturalSurvey) -> list[SurveyValidationIssue]:
    return analyze_multiview_identity(survey).issues
