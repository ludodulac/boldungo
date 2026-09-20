"""Contracts for photo-derived architectural proposals."""
from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field

from brickhouse.building.models import BuildingModel
from .compatibility import M0Compatibility
from .multiview import MultiViewWorkspace


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


class PhotoAnalysisResult(BaseModel):
    # 0.2 adds compatibility metadata; 0.3 adds explicit proportion/scale evidence.
    # Older provider/stored payloads remain readable and are enriched by live analysis.
    schema_version: Literal["0.1", "0.2", "0.3", "0.4"] = "0.4"
    building: BuildingModel
    questions: list[ClarificationQuestion] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    needs_confirmation: bool
    m0_compatibility: M0Compatibility | None = None
    scale_basis: str | None = None
    proportion_evidence: list[ProportionEvidence] = Field(default_factory=list)
    # Transitional compatibility: consumers still receive BuildingModel, while
    # the auditable pre-Survey multiview workspace is now preserved alongside it.
    multiview_workspace: MultiViewWorkspace | None = None
