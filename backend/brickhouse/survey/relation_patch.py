"""Add-only architectural relation patches for an existing Survey.

The external specialist never returns an ArchitecturalSurvey candidate.  It may
only propose new ``SurveyRelation`` objects bound to the exact Survey content it
received.  Application deep-copies the base Survey and appends only validated
relations; every other Survey field is structurally outside the patch contract.
"""
from __future__ import annotations

import hashlib
import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .models import ArchitecturalSurvey, RelationKind, SurveyRelation
from .validation import validate_survey_semantics


_RELATION_FIELDS = {
    "id",
    "kind",
    "subject_id",
    "object_id",
    "certainty",
    "statement",
    "evidence",
}
_EVIDENCE_FIELDS = {"photo_index", "observation", "region"}
_REGION_FIELDS = {"x0", "y0", "x1", "y1"}
_SYMMETRIC_RELATION_KINDS = {
    RelationKind.CONNECTS_TO,
    RelationKind.ADJACENT_TO,
    RelationKind.ALIGNED_WITH,
    RelationKind.SAME_PHYSICAL_OBJECT,
}


def survey_content_fingerprint(survey: ArchitecturalSurvey) -> str:
    """Return a deterministic SHA-256 over the complete canonical Survey JSON.

    Canonicalization uses Pydantic JSON-mode data, UTF-8 JSON, sorted object keys,
    compact separators and no ASCII escaping.  List order is preserved because it
    is part of the Survey document received by the specialist.
    """
    payload = json.dumps(
        survey.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


class SurveyRelationPatch(BaseModel):
    """Minimal v0.1 output contract for the architectural-relations specialist."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["0.1"] = "0.1"
    kind: Literal["survey_relation_patch"] = "survey_relation_patch"
    survey_id: str = Field(min_length=1)
    base_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    patch_id: str = Field(min_length=1)
    mission: Literal["architectural_relations"] = "architectural_relations"
    add_relations: list[SurveyRelation]

    @model_validator(mode="before")
    @classmethod
    def forbid_content_outside_contract(cls, value):
        if not isinstance(value, dict):
            return value
        relations = value.get("add_relations")
        if not isinstance(relations, list):
            return value

        for relation_index, relation in enumerate(relations):
            if not isinstance(relation, dict):
                continue
            unknown = set(relation) - _RELATION_FIELDS
            if unknown:
                names = ", ".join(sorted(unknown))
                raise ValueError(
                    f"add_relations[{relation_index}] contains fields outside SurveyRelation: {names}"
                )

            evidence_items = relation.get("evidence")
            if not isinstance(evidence_items, list):
                continue
            for evidence_index, evidence in enumerate(evidence_items):
                if not isinstance(evidence, dict):
                    continue
                unknown_evidence = set(evidence) - _EVIDENCE_FIELDS
                if unknown_evidence:
                    names = ", ".join(sorted(unknown_evidence))
                    raise ValueError(
                        "add_relations"
                        f"[{relation_index}].evidence[{evidence_index}] contains fields outside PhotoEvidence: {names}"
                    )
                region = evidence.get("region")
                if isinstance(region, dict):
                    unknown_region = set(region) - _REGION_FIELDS
                    if unknown_region:
                        names = ", ".join(sorted(unknown_region))
                        raise ValueError(
                            "add_relations"
                            f"[{relation_index}].evidence[{evidence_index}].region contains fields outside NormalizedImageRegion: {names}"
                        )
        return value

    @model_validator(mode="after")
    def validate_unique_relation_ids(self) -> "SurveyRelationPatch":
        ids = [relation.id for relation in self.add_relations]
        if len(ids) != len(set(ids)):
            raise ValueError("relation patch add_relations ids must be unique")
        return self


class SurveyRelationPatchApplication(BaseModel):
    source_survey_id: str
    base_fingerprint: str
    patch_id: str
    candidate: ArchitecturalSurvey
    added_relations: list[SurveyRelation]


def _relation_identity(relation: SurveyRelation):
    if relation.kind in _SYMMETRIC_RELATION_KINDS:
        endpoints = tuple(sorted((relation.subject_id, relation.object_id)))
    else:
        endpoints = (relation.subject_id, relation.object_id)
    return relation.kind, endpoints


def apply_survey_relation_patch(
    base: ArchitecturalSurvey,
    patch: SurveyRelationPatch,
) -> SurveyRelationPatchApplication:
    """Validate and append only relations, preserving every other base fact."""
    if patch.survey_id != base.id:
        raise ValueError("relation patch survey_id does not match base Survey")

    fingerprint = survey_content_fingerprint(base)
    if patch.base_fingerprint != fingerprint:
        raise ValueError("relation patch base_fingerprint does not match base Survey content")

    known_observations = {observation.id for observation in base.observations}
    known_photos = {photo.photo_index for photo in base.photos}
    existing_ids = {relation.id for relation in base.relations}
    existing_relations = {_relation_identity(relation) for relation in base.relations}
    patch_relation_identities = set()

    for relation in patch.add_relations:
        if relation.id in existing_ids:
            raise ValueError(f"relation patch id collides with existing relation {relation.id!r}")
        if relation.subject_id not in known_observations or relation.object_id not in known_observations:
            raise ValueError(
                f"relation patch {relation.id!r} references an observation absent from the base Survey"
            )
        for evidence in relation.evidence:
            if evidence.photo_index not in known_photos:
                raise ValueError(
                    f"relation patch {relation.id!r} references unknown photo {evidence.photo_index}"
                )

        identity = _relation_identity(relation)
        if identity in existing_relations:
            raise ValueError(
                f"relation patch {relation.id!r} duplicates an existing Survey relation"
            )
        if identity in patch_relation_identities:
            raise ValueError(
                f"relation patch {relation.id!r} duplicates another relation in the same patch"
            )
        patch_relation_identities.add(identity)

    candidate = base.model_copy(deep=True)
    candidate.relations.extend(relation.model_copy(deep=True) for relation in patch.add_relations)

    # Re-parse to run normal ArchitecturalSurvey validation on the enriched result.
    candidate = ArchitecturalSurvey.model_validate(candidate.model_dump(mode="json"))
    semantic_issues = validate_survey_semantics(candidate)
    if semantic_issues:
        first = semantic_issues[0]
        raise ValueError(
            f"relation patch candidate violates Survey semantics: {first.code}: {first.message}"
        )

    # Explicit preservation guard: only the appended relation suffix may differ.
    if candidate.photos != base.photos:
        raise ValueError("relation patch preservation failure: photos changed")
    if candidate.observations != base.observations:
        raise ValueError("relation patch preservation failure: observations changed")
    if candidate.canonical_frame != base.canonical_frame:
        raise ValueError("relation patch preservation failure: canonical_frame changed")
    if candidate.known_measurements != base.known_measurements:
        raise ValueError("relation patch preservation failure: known_measurements changed")
    if candidate.representation_policy != base.representation_policy:
        raise ValueError("relation patch preservation failure: representation_policy changed")
    if candidate.name != base.name or candidate.notes != base.notes:
        raise ValueError("relation patch preservation failure: Survey metadata changed")

    base_relation_count = len(base.relations)
    if candidate.relations[:base_relation_count] != base.relations:
        raise ValueError("relation patch preservation failure: existing relations changed")
    if candidate.relations[base_relation_count:] != patch.add_relations:
        raise ValueError("relation patch preservation failure: appended relations differ from patch")

    return SurveyRelationPatchApplication(
        source_survey_id=base.id,
        base_fingerprint=fingerprint,
        patch_id=patch.patch_id,
        candidate=candidate,
        added_relations=[relation.model_copy(deep=True) for relation in patch.add_relations],
    )
