from __future__ import annotations

import pytest

from brickhouse.building.models import Facade
from brickhouse.scene.host_face_identity import (
    HostFaceEvidence,
    resolve_host_face,
    validate_host_face_candidate,
)


def test_face_identity_required_before_host_placement_near_rear_corner() -> None:
    """Regression for SAME_SPATIAL_SECTOR != SAME_FACE.

    A secondary structure may sit near the rear corner while landmark tracking
    still identifies the longitudinal LEFT face as its host. Without a
    demonstrated corner crossing, REAR must be rejected.
    """

    evidence = HostFaceEvidence(
        landmark_supported_face=Facade.LEFT,
        near_corner_faces=(Facade.LEFT, Facade.REAR),
        demonstrated_corner_crossing=False,
        landmark_ids=["roof-eave-chain", "module003-stair-platform", "terrace-house-edge"],
    )

    assert resolve_host_face(evidence) is Facade.LEFT
    validate_host_face_candidate(Facade.LEFT, evidence)

    with pytest.raises(ValueError, match="corner proximity is not host-face evidence"):
        validate_host_face_candidate(Facade.REAR, evidence)


def test_host_face_remains_unknown_when_landmarks_do_not_identify_a_face() -> None:
    evidence = HostFaceEvidence(
        landmark_supported_face=None,
        near_corner_faces=(Facade.LEFT, Facade.REAR),
        demonstrated_corner_crossing=False,
    )

    assert resolve_host_face(evidence) is None

    with pytest.raises(ValueError, match="host face is UNKNOWN"):
        validate_host_face_candidate(Facade.REAR, evidence)
