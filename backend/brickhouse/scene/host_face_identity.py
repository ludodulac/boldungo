"""Host-face identity guard for secondary architectural structures.

This module encodes the evidence ordering established by BOLDÜNGO-062:
multi-view landmarks establish face identity first; proximity to a corner or
shared spatial sector never promotes a different host face by itself.
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from brickhouse.building.models import Facade


class HostFaceEvidence(BaseModel):
    """Minimal evidence contract for placing a secondary structure on a host face."""

    landmark_supported_face: Facade | None = None
    near_corner_faces: tuple[Facade, Facade] | None = None
    demonstrated_corner_crossing: bool = False
    landmark_ids: list[str] = Field(default_factory=list)


def resolve_host_face(evidence: HostFaceEvidence) -> Facade | None:
    """Return only the face established by landmark identity.

    Corner proximity is deliberately non-decisive. Unknown landmark identity
    remains unknown rather than being replaced by a convenient adjacent face.
    """

    return evidence.landmark_supported_face


def validate_host_face_candidate(
    candidate: Facade,
    evidence: HostFaceEvidence,
) -> None:
    """Reject a host-face guess unsupported by face identity.

    A different candidate can only survive when an explicit corner crossing has
    been demonstrated. This prevents SAME_SPATIAL_SECTOR from becoming SAME_FACE.
    """

    supported = resolve_host_face(evidence)
    if supported is None:
        raise ValueError(
            "host face is UNKNOWN: landmark identity must be established before placement"
        )
    if candidate == supported:
        return
    if not evidence.demonstrated_corner_crossing:
        raise ValueError(
            f"host face {candidate.value!r} contradicts landmark-supported face "
            f"{supported.value!r}; corner proximity is not host-face evidence"
        )
