"""Contracts for photo-derived architectural proposals."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from brickhouse.building.models import BuildingModel
from .compatibility import M0Compatibility


class ClarificationQuestion(BaseModel):
    id: str
    question: str
    reason: str
    importance: Literal["required", "recommended"]


class ProportionEvidence(BaseModel):
    """One explicit piece of evidence used to recover real architectural proportions."""
    facade: Literal["front", "rear", "left", "right", "global"]
    observation: str
    method: Literal[
        "perspective_corrected_ratio",
        "cross_view_consistency",
        "known_scale_anchor",
        "architectural_alignment",
        "uncertain",
    ]
    confidence: float = Field(ge=0.0, le=1.0)


class VisionLandmarkPoint(BaseModel):
    """Provider-proposed location of one named physical landmark in one photo.

    Coordinates remain in the existing independent 0..1 image convention. They
    are only 2D proposals; camera code converts them into an isotropic calibrated
    space later and must not treat these values as calibrated image coordinates.
    """

    photo_index: int = Field(ge=1)
    x: float = Field(ge=0.0, le=1.0)
    y: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    ambiguous: bool = False
    statement: str = Field(min_length=1)
    provenance: Literal["vision_provider"] = "vision_provider"


class VisionLandmarkProposal(BaseModel):
    """Small semantic cross-view landmark proposal produced by the vision layer.

    The provider may explicitly propose physical identity, but this object is not
    an ArchitecturalLandmarkTrack. Provenance and local geometry must validate it
    before the BH-237 bridge can accept it.
    """

    physical_landmark_id: str = Field(min_length=1)
    description: str = Field(min_length=1)
    survey_observation_id: str | None = None
    related_object_hint: str | None = None
    identity_status: Literal["PROPOSED", "AMBIGUOUS", "REJECTED"] = "PROPOSED"
    confidence: float = Field(ge=0.0, le=1.0)
    observations: list[VisionLandmarkPoint] = Field(min_length=2)
    diagnostic: str | None = None

    @model_validator(mode="after")
    def validate_cross_view_proposal(self) -> "VisionLandmarkProposal":
        photos = [item.photo_index for item in self.observations]
        if len(photos) != len(set(photos)):
            raise ValueError("vision landmark proposal may contain at most one point per photo")
        if self.identity_status != "PROPOSED" and not self.diagnostic:
            raise ValueError("ambiguous/rejected landmark proposals require a diagnostic")
        if self.identity_status == "PROPOSED" and any(item.ambiguous for item in self.observations):
            raise ValueError("a proposed physical identity cannot contain an observation already marked ambiguous")
        return self


class VisionSurveyEvidenceCandidate(BaseModel):
    """Provider proposal that an accepted Survey object is visible in another view.

    This is deliberately not Survey evidence. It must remain a candidate sidecar
    until a Survey-aware validator accepts or rejects its provenance.
    """

    id: str = Field(min_length=1)
    survey_observation_id: str = Field(min_length=1)
    photo_index: int = Field(ge=1)
    observation: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    status: Literal["PROPOSED", "AMBIGUOUS", "REJECTED"] = "PROPOSED"
    diagnostic: str | None = None
    provenance: Literal["vision_provider"] = "vision_provider"

    @model_validator(mode="after")
    def validate_candidate(self) -> "VisionSurveyEvidenceCandidate":
        if self.status != "PROPOSED" and not self.diagnostic:
            raise ValueError("ambiguous/rejected evidence candidates require a diagnostic")
        return self


class PhotoAnalysisResult(BaseModel):
    # 0.2 adds compatibility metadata; 0.3 adds explicit proportion/scale evidence;
    # 0.4 adds a bounded landmark/evidence proposal sidecar. Older payloads remain readable.
    schema_version: Literal["0.1", "0.2", "0.3", "0.4"] = "0.4"
    building: BuildingModel
    questions: list[ClarificationQuestion] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    needs_confirmation: bool
    m0_compatibility: M0Compatibility | None = None
    scale_basis: str | None = None
    proportion_evidence: list[ProportionEvidence] = Field(default_factory=list)
    landmark_proposals: list[VisionLandmarkProposal] = Field(default_factory=list)
    survey_evidence_candidates: list[VisionSurveyEvidenceCandidate] = Field(default_factory=list)
