"""Candidate photo evidence for an accepted ArchitecturalSurvey observation.

This sidecar records newly observed photo support without mutating the accepted
Survey. A candidate may later be reviewed/promoted by a Survey workflow, but it
is never silently inserted into ``SurveyObservation.evidence``.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from brickhouse.building import SourceInfo, SourceKind

from .models import ArchitecturalSurvey


SurveyPhotoEvidenceCandidateStatus = Literal["PROPOSED", "AMBIGUOUS", "REJECTED"]


class SurveyPhotoEvidenceCandidate(BaseModel):
    id: str = Field(min_length=1)
    survey_observation_id: str = Field(min_length=1)
    photo_index: int = Field(ge=1)
    observation: str = Field(min_length=1)
    source: SourceInfo
    status: SurveyPhotoEvidenceCandidateStatus = "PROPOSED"
    diagnostic: str | None = None

    @model_validator(mode="after")
    def validate_source(self) -> "SurveyPhotoEvidenceCandidate":
        if self.source.kind not in {SourceKind.OBSERVED, SourceKind.INFERRED}:
            raise ValueError("Survey photo evidence candidate must be observed or inferred from photo evidence")
        if self.status != "PROPOSED" and not self.diagnostic:
            raise ValueError("ambiguous/rejected Survey evidence candidates require a diagnostic")
        return self


def validate_survey_photo_evidence_candidates(
    survey: ArchitecturalSurvey,
    candidates: list[SurveyPhotoEvidenceCandidate],
) -> None:
    ids = [item.id for item in candidates]
    if len(ids) != len(set(ids)):
        raise ValueError("Survey photo evidence candidate ids must be unique")

    known_photos = {photo.photo_index for photo in survey.photos}
    observations = {observation.id: observation for observation in survey.observations}
    seen_pairs: set[tuple[str, int]] = set()
    for item in candidates:
        if item.photo_index not in known_photos:
            raise ValueError(f"Survey photo evidence candidate {item.id!r} references unknown photo {item.photo_index}")
        observation = observations.get(item.survey_observation_id)
        if observation is None:
            raise ValueError(
                f"Survey photo evidence candidate {item.id!r} references unknown observation {item.survey_observation_id!r}"
            )
        pair = (item.survey_observation_id, item.photo_index)
        if pair in seen_pairs:
            raise ValueError("only one Survey photo evidence candidate may target an observation/photo pair")
        seen_pairs.add(pair)
        accepted_photos = {evidence.photo_index for evidence in observation.evidence}
        if item.photo_index in accepted_photos:
            raise ValueError(
                f"Survey observation {item.survey_observation_id!r} already has accepted evidence on photo {item.photo_index}; "
                "do not duplicate accepted evidence as a candidate"
            )
