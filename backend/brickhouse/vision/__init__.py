"""Photo-analysis boundary for BrickHouse."""
from .models import ClarificationQuestion, PhotoAnalysisResult
from .multiview import (
    ArchitecturalRelationCandidate,
    AspectCertainty,
    CertaintyLevel,
    ClaimStatus,
    Contradiction,
    IdentityCandidate,
    IdentityStatus,
    LocalObservation,
    MultiViewPass,
    MultiViewWorkspace,
    OpenHypothesis,
    ViewAssessment,
    VisibilityStatus,
)
from .openai_provider import analyze_building_photos

__all__ = [
    "ArchitecturalRelationCandidate",
    "AspectCertainty",
    "CertaintyLevel",
    "ClaimStatus",
    "ClarificationQuestion",
    "Contradiction",
    "IdentityCandidate",
    "IdentityStatus",
    "LocalObservation",
    "MultiViewPass",
    "MultiViewWorkspace",
    "OpenHypothesis",
    "PhotoAnalysisResult",
    "ViewAssessment",
    "VisibilityStatus",
    "analyze_building_photos",
]
