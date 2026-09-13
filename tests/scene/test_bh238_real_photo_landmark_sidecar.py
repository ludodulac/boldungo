import numpy as np

from brickhouse.building import SourceInfo, SourceKind
from brickhouse.scene.photo_landmarks import build_relative_landmark_tracks
from brickhouse.scene.relative_camera_estimation import CalibratedPhotoIntrinsics, estimate_relative_camera_pair
from brickhouse.scene.vision_landmark_bridge import bridge_vision_landmarks, convert_vision_evidence_candidates
from brickhouse.survey import ArchitecturalSurvey
from brickhouse.vision.models import VisionLandmarkProposal, VisionSurveyEvidenceCandidate


POINTS = [
    (-1.0, -0.8, 4.0), (-0.5, 0.7, 5.0), (0.2, -0.5, 6.0), (0.8, 0.9, 5.5),
    (1.2, -0.2, 7.0), (-0.8, 0.3, 8.0), (0.5, 0.4, 4.5), (1.0, -0.7, 6.5),
    (-0.2, 1.0, 7.5), (1.4, 0.2, 8.5), (0.1, -0.9, 5.8), (0.9, 0.6, 7.2),
]


def _survey() -> ArchitecturalSurvey:
    return ArchitecturalSurvey.model_validate({
        "id": "bh238-generic-survey",
        "name": "BH-238 generic landmark survey",
        "photos": [
            {"photo_index": 1, "facade": "front", "description": "View A", "source": {"kind": "observed", "confidence": 1.0}},
            {"photo_index": 2, "facade": "front", "description": "View B", "source": {"kind": "observed", "confidence": 1.0}},
        ],
        "observations": [{
            "id": "opening-1",
            "kind": "opening",
            "facade": "front",
            "certainty": "certain",
            "statement": "One physical opening is accepted from view A.",
            "evidence": [{"photo_index": 1, "observation": "Opening clearly visible in view A."}],
        }],
    })


def _corner_plane(height=120, width=100, x=50, y=60):
    image = np.zeros((height, width), dtype=float)
    image[y:, x:] = 1.0
    return image


def _proposal(x=0.505, y=0.505):
    return VisionLandmarkProposal.model_validate({
        "physical_landmark_id": "opening-1-top-left",
        "description": "Exact top-left physical corner of opening-1",
        "survey_observation_id": "opening-1",
        "identity_status": "PROPOSED",
        "confidence": 0.93,
        "observations": [
            {"photo_index": 1, "x": x, "y": y, "confidence": 0.95, "statement": "Same exact opening corner in view A."},
            {"photo_index": 2, "x": x, "y": y, "confidence": 0.92, "statement": "Same exact opening corner in view B."},
        ],
    })


def test_provider_candidate_evidence_stays_separate_and_can_support_validated_track():
    survey = _survey()
    before = survey.model_dump(mode="json")
    vision_candidate = VisionSurveyEvidenceCandidate(
        id="candidate-opening-1-photo-2",
        survey_observation_id="opening-1",
        photo_index=2,
        observation="The already identified opening-1 is directly visible in view B.",
        confidence=0.91,
    )
    candidates = convert_vision_evidence_candidates(survey, [vision_candidate])
    report = bridge_vision_landmarks(
        survey,
        [_proposal()],
        {1: _corner_plane(), 2: _corner_plane()},
        evidence_candidates=candidates,
    )

    assert report.candidate_count == 1
    assert report.identity_cross_view_defendable == 1
    assert report.provenance_valid_or_candidate == 1
    assert report.localization_stable == 1
    assert report.tracks_accepted == 1
    assert survey.model_dump(mode="json") == before
    assert {item.photo_index for item in survey.observations[0].evidence} == {1}

    relative = build_relative_landmark_tracks(
        survey,
        report.tracks,
        evidence_candidates=candidates,
    )
    assert len(relative) == 1
    assert {item.photo_index for item in relative[0].observations} == {1, 2}


def test_local_validator_rejects_edge_like_or_ambiguous_location_without_creating_identity():
    survey = _survey()
    candidate = convert_vision_evidence_candidates(survey, [VisionSurveyEvidenceCandidate(
        id="candidate-opening-1-photo-2",
        survey_observation_id="opening-1",
        photo_index=2,
        observation="Candidate additional visibility.",
        confidence=0.9,
    )])
    edge = np.zeros((120, 100), dtype=float)
    edge[:, 50:] = 1.0
    report = bridge_vision_landmarks(
        survey,
        [_proposal()],
        {1: edge, 2: edge},
        evidence_candidates=candidate,
    )
    assert report.identity_cross_view_defendable == 1
    assert report.localization_stable == 0
    assert report.tracks_accepted == 0
    assert report.decisions[0].status == "REJECTED_LOCALIZATION"


def _two_view_survey_for_camera() -> ArchitecturalSurvey:
    return ArchitecturalSurvey.model_validate({
        "id": "bh238-camera-survey",
        "name": "BH-238 portrait camera survey",
        "photos": [
            {"photo_index": 1, "facade": "front", "description": "Camera A", "source": {"kind": "observed", "confidence": 1.0}},
            {"photo_index": 2, "facade": "front", "description": "Camera B", "source": {"kind": "observed", "confidence": 1.0}},
        ],
        "observations": [{
            "id": "rigid",
            "kind": "volume",
            "facade": "front",
            "certainty": "certain",
            "statement": "Rigid structure visible in both views.",
            "evidence": [
                {"photo_index": 1, "observation": "Rigid structure in A."},
                {"photo_index": 2, "observation": "Rigid structure in B."},
            ],
        }],
    })


def _relative_tracks(width, height, fx, fy, cx, cy):
    from brickhouse.scene.photo_landmarks import ArchitecturalLandmarkObservation, ArchitecturalLandmarkTrack
    tracks = []
    for index, (x, y, z) in enumerate(POINTS):
        physical = f"corner-{index}"
        observations = []
        # Keep the synthetic calibrated baseline modest enough that every landmark
        # remains inside both portrait images. The test is about anisotropic image
        # coordinates at the camera boundary, not about accepting off-image points.
        for photo_index, camera_x in ((1, 0.0), (2, 0.2)):
            px = cx + fx * (x - camera_x) / z
            py = cy - fy * y / z
            observations.append(ArchitecturalLandmarkObservation(
                physical_landmark_id=physical,
                photo_index=photo_index,
                survey_observation_id="rigid",
                point={"x": px / width, "y": py / height},
                source=SourceInfo(kind=SourceKind.OBSERVED, confidence=1.0),
                statement="Synthetic pixel-calibrated architectural point.",
            ))
        tracks.append(ArchitecturalLandmarkTrack(
            id=f"track-{index}",
            physical_landmark_id=physical,
            survey_observation_id="rigid",
            observations=observations,
            source=SourceInfo(kind=SourceKind.OBSERVED, confidence=1.0),
            statement="Explicit physical identity for portrait-camera test.",
        ))
    return tracks


def _pixel_intrinsics(photo_index, width, height, fx, fy, cx, cy):
    return CalibratedPhotoIntrinsics(
        id=f"pixel-{photo_index}",
        photo_index=photo_index,
        image_width_px=width,
        image_height_px=height,
        focal_x_px=fx,
        focal_y_px=fy,
        principal_x_px=cx,
        principal_y_px=cy,
        source=SourceInfo(kind=SourceKind.USER_PROVIDED, confidence=1.0),
        statement="Explicit synthetic pixel intrinsics.",
    )


def test_portrait_non_square_intrinsics_do_not_publish_false_scalar_camera():
    survey = _two_view_survey_for_camera()
    width, height = 691, 1536
    fx = fy = 900.0
    cx, cy = width / 2.0, height / 2.0
    tracks = build_relative_landmark_tracks(survey, _relative_tracks(width, height, fx, fy, cx, cy))
    result = estimate_relative_camera_pair(
        survey,
        [_pixel_intrinsics(1, width, height, fx, fy, cx, cy), _pixel_intrinsics(2, width, height, fx, fy, cx, cy)],
        tracks,
        first_photo_index=1,
        second_photo_index=2,
    )
    assert result.status == "UNRESOLVED"
    assert result.cameras == []
    assert "scalar focal" in result.diagnostic.lower()
    assert result.epipolar_rms is not None


def test_square_pixel_intrinsics_remain_compatible_with_bh237_camera_hypothesis():
    survey = _two_view_survey_for_camera()
    width = height = 1000
    fx = fy = 800.0
    cx = cy = 500.0
    tracks = build_relative_landmark_tracks(survey, _relative_tracks(width, height, fx, fy, cx, cy))
    result = estimate_relative_camera_pair(
        survey,
        [_pixel_intrinsics(1, width, height, fx, fy, cx, cy), _pixel_intrinsics(2, width, height, fx, fy, cx, cy)],
        tracks,
        first_photo_index=1,
        second_photo_index=2,
    )
    assert result.status == "RESOLVED_RELATIVE"
    assert len(result.cameras) == 2
