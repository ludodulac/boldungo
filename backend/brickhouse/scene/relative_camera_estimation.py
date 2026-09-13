"""Bounded calibrated two-view camera estimation for explicit architectural tracks.

This is intentionally not self-calibration or SfM. Intrinsics must be explicitly
supplied. Legacy normalized scalar focal length remains supported for existing
square/synthetic callers. Real image callers may instead provide pixel-space
``fx/fy/cx/cy`` plus image dimensions, which avoids treating x/width and y/height
as an isotropic coordinate space.
"""
from __future__ import annotations

from math import acos, ceil, degrees
from typing import Literal

import numpy as np
from pydantic import BaseModel, Field, model_validator

from brickhouse.building import SourceInfo, SourceKind
from brickhouse.survey import ArchitecturalSurvey

from .relative_multiview import (
    RelativeCameraHypothesis,
    RelativeLandmarkTrack,
    RelativePoint3D,
    RelativeVector3D,
)

RelativeCameraEstimationStatus = Literal["RESOLVED_RELATIVE", "UNRESOLVED"]
_EPS = 1e-12


class CalibratedPhotoIntrinsics(BaseModel):
    """Explicit fixed pinhole intrinsics.

    Two mutually exclusive representations are supported:
    - legacy: ``focal_length`` and normalized principal point, appropriate for
      square/synthetic normalized image coordinates;
    - pixel: image dimensions plus ``focal_x_px/focal_y_px`` and principal point
      in pixels. Pixel mode is the required honest representation for real
      non-square images at the camera-estimation boundary.
    """

    id: str = Field(min_length=1)
    photo_index: int = Field(ge=1)
    focal_length: float | None = Field(default=None, gt=0)
    principal_x: float = Field(default=0.5, ge=0, le=1)
    principal_y: float = Field(default=0.5, ge=0, le=1)
    image_width_px: int | None = Field(default=None, ge=2)
    image_height_px: int | None = Field(default=None, ge=2)
    focal_x_px: float | None = Field(default=None, gt=0)
    focal_y_px: float | None = Field(default=None, gt=0)
    principal_x_px: float | None = None
    principal_y_px: float | None = None
    source: SourceInfo
    statement: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_intrinsics(self) -> "CalibratedPhotoIntrinsics":
        if self.source.kind not in {SourceKind.OBSERVED, SourceKind.USER_PROVIDED, SourceKind.INFERRED}:
            raise ValueError("calibrated photo intrinsics must have traceable observed, user_provided or inferred provenance")
        pixel_values = (
            self.image_width_px,
            self.image_height_px,
            self.focal_x_px,
            self.focal_y_px,
            self.principal_x_px,
            self.principal_y_px,
        )
        has_any_pixel = any(value is not None for value in pixel_values)
        has_all_pixel = all(value is not None for value in pixel_values)
        if has_any_pixel and not has_all_pixel:
            raise ValueError("pixel-space intrinsics require image_width_px, image_height_px, fx, fy, cx and cy together")
        if has_all_pixel and self.focal_length is not None:
            raise ValueError("choose either legacy normalized focal_length or explicit pixel-space intrinsics, not both")
        if not has_all_pixel and self.focal_length is None:
            raise ValueError("calibrated intrinsics require either legacy focal_length or complete pixel-space intrinsics")
        if has_all_pixel:
            assert self.image_width_px is not None and self.image_height_px is not None
            assert self.principal_x_px is not None and self.principal_y_px is not None
            if not 0 <= self.principal_x_px <= self.image_width_px - 1:
                raise ValueError("principal_x_px lies outside the image")
            if not 0 <= self.principal_y_px <= self.image_height_px - 1:
                raise ValueError("principal_y_px lies outside the image")
        return self

    @property
    def pixel_mode(self) -> bool:
        return self.image_width_px is not None

    def normalized_axes(self) -> tuple[float, float, float, float]:
        """Return fx, fy, cx, cy in the existing independent normalized axes."""
        if not self.pixel_mode:
            assert self.focal_length is not None
            return self.focal_length, self.focal_length, self.principal_x, self.principal_y
        assert self.image_width_px is not None and self.image_height_px is not None
        assert self.focal_x_px is not None and self.focal_y_px is not None
        assert self.principal_x_px is not None and self.principal_y_px is not None
        return (
            self.focal_x_px / self.image_width_px,
            self.focal_y_px / self.image_height_px,
            self.principal_x_px / self.image_width_px,
            self.principal_y_px / self.image_height_px,
        )


class RelativeCameraEstimationResult(BaseModel):
    status: RelativeCameraEstimationStatus
    cameras: list[RelativeCameraHypothesis] = Field(default_factory=list)
    supporting_landmark_ids: list[str] = Field(default_factory=list)
    epipolar_rms: float | None = Field(default=None, ge=0)
    positive_depth_fraction: float | None = Field(default=None, ge=0, le=1)
    median_parallax_degrees: float | None = Field(default=None, ge=0)
    diagnostic: str

    @model_validator(mode="after")
    def validate_status(self) -> "RelativeCameraEstimationResult":
        if self.status == "RESOLVED_RELATIVE":
            if len(self.cameras) != 2:
                raise ValueError("resolved relative camera estimation requires exactly two cameras")
            if self.epipolar_rms is None or self.positive_depth_fraction is None or self.median_parallax_degrees is None:
                raise ValueError("resolved relative camera estimation requires validation metrics")
        elif self.cameras:
            raise ValueError("unresolved relative camera estimation must not expose camera hypotheses")
        return self


def _unresolved(ids: list[str], diagnostic: str, *, epipolar_rms: float | None = None) -> RelativeCameraEstimationResult:
    return RelativeCameraEstimationResult(status="UNRESOLVED", supporting_landmark_ids=ids, epipolar_rms=epipolar_rms, diagnostic=diagnostic)


def _normalized_camera_point(item, intrinsics: CalibratedPhotoIntrinsics) -> np.ndarray:
    fx, fy, cx, cy = intrinsics.normalized_axes()
    return np.array([(item.point.x - cx) / fx, (cy - item.point.y) / fy, 1.0], dtype=float)


def _triangulate(p1: np.ndarray, p2: np.ndarray, rotation: np.ndarray, translation: np.ndarray) -> np.ndarray | None:
    projection_1 = np.column_stack((np.eye(3), np.zeros(3)))
    projection_2 = np.column_stack((rotation, translation))
    matrix = np.vstack((
        p1[0] * projection_1[2] - projection_1[0], p1[1] * projection_1[2] - projection_1[1],
        p2[0] * projection_2[2] - projection_2[0], p2[1] * projection_2[2] - projection_2[1],
    ))
    _, _, vh = np.linalg.svd(matrix)
    homogeneous = vh[-1]
    return None if abs(homogeneous[3]) <= _EPS else homogeneous[:3] / homogeneous[3]


def _candidate_geometry(points_1, points_2, rotation, translation) -> tuple[int, list[float]]:
    center_2 = -(rotation.T @ translation)
    positive = 0
    parallaxes: list[float] = []
    for first, second in zip(points_1, points_2, strict=True):
        point = _triangulate(first, second, rotation, translation)
        if point is None:
            continue
        point_2 = rotation @ point + translation
        if point[2] <= _EPS or point_2[2] <= _EPS:
            continue
        positive += 1
        ray_1 = point / np.linalg.norm(point)
        ray_2 = (point - center_2) / np.linalg.norm(point - center_2)
        parallaxes.append(degrees(acos(float(np.clip(np.dot(ray_1, ray_2), -1.0, 1.0)))))
    return positive, parallaxes


def _camera_from_pose(photo_index, intrinsics, rotation, translation, confidence) -> RelativeCameraHypothesis | None:
    fx, fy, cx, cy = intrinsics.normalized_axes()
    # BH-236 camera hypotheses still expose one scalar focal length. A non-square
    # real camera can only be handed off when both normalized axes are isotropic.
    # Otherwise BH-237 must remain UNRESOLVED rather than publish a false camera.
    if abs(fx - fy) > 1e-9:
        return None
    center = -(rotation.T @ translation)
    return RelativeCameraHypothesis(
        id=f"relative-camera-photo-{photo_index}", photo_index=photo_index,
        origin=RelativePoint3D(x=float(center[0]), y=float(center[1]), z=float(center[2])),
        right=RelativeVector3D(x=float(rotation[0, 0]), y=float(rotation[0, 1]), z=float(rotation[0, 2])),
        up=RelativeVector3D(x=float(rotation[1, 0]), y=float(rotation[1, 1]), z=float(rotation[1, 2])),
        forward=RelativeVector3D(x=float(rotation[2, 0]), y=float(rotation[2, 1]), z=float(rotation[2, 2])),
        focal_length=fx, principal_x=cx, principal_y=cy,
        source=SourceInfo(kind=SourceKind.INFERRED, confidence=confidence),
        statement="Deterministic calibrated two-view relative pose from explicit architectural landmark tracks.",
    )


def estimate_relative_camera_pair(
    survey: ArchitecturalSurvey,
    intrinsics: list[CalibratedPhotoIntrinsics],
    tracks: list[RelativeLandmarkTrack],
    *, first_photo_index: int, second_photo_index: int,
    minimum_tracks: int = 8, minimum_parallax_degrees: float = 1.0, maximum_epipolar_rms: float = 0.01,
) -> RelativeCameraEstimationResult:
    if first_photo_index == second_photo_index:
        raise ValueError("relative camera estimation requires two distinct photos")
    if minimum_tracks < 8:
        raise ValueError("calibrated eight-point estimation requires at least eight tracks")
    if minimum_parallax_degrees <= 0 or maximum_epipolar_rms <= 0:
        raise ValueError("camera estimation thresholds must be positive")
    known_photos = {photo.photo_index for photo in survey.photos}
    if first_photo_index not in known_photos or second_photo_index not in known_photos:
        raise ValueError("relative camera estimation references a photo absent from Survey")
    by_photo = {item.photo_index: item for item in intrinsics}
    if len(by_photo) != len(intrinsics):
        raise ValueError("calibrated photo intrinsics must reference unique photos")
    if first_photo_index not in by_photo or second_photo_index not in by_photo:
        return _unresolved([], "Explicit calibrated intrinsics are required for both photos; focal self-calibration is outside BH-237.")
    first_intrinsics, second_intrinsics = by_photo[first_photo_index], by_photo[second_photo_index]

    usable = []
    for track in sorted(tracks, key=lambda item: item.id):
        observations = {item.photo_index: item for item in track.observations}
        if first_photo_index in observations and second_photo_index in observations:
            usable.append((track.id, observations[first_photo_index], observations[second_photo_index]))
    ids = [item[0] for item in usable]
    if len(usable) < minimum_tracks:
        return _unresolved(ids, f"Only {len(usable)} explicit cross-view track(s); require at least {minimum_tracks} for calibrated pose estimation.")

    p1 = [_normalized_camera_point(item[1], first_intrinsics) for item in usable]
    p2 = [_normalized_camera_point(item[2], second_intrinsics) for item in usable]
    xy1, xy2 = np.array([[p[0], p[1]] for p in p1]), np.array([[p[0], p[1]] for p in p2])
    if np.linalg.matrix_rank(xy1 - xy1.mean(axis=0)) < 2 or np.linalg.matrix_rank(xy2 - xy2.mean(axis=0)) < 2:
        return _unresolved(ids, "Landmark image geometry is degenerate: points do not span two image dimensions.")
    design = np.array([[b[0]*a[0], b[0]*a[1], b[0], b[1]*a[0], b[1]*a[1], b[1], a[0], a[1], 1.0] for a, b in zip(p1, p2, strict=True)])
    if np.linalg.matrix_rank(design, tol=1e-10) < 8:
        return _unresolved(ids, "Two-view correspondence system is rank-deficient; relative pose is not identifiable.")
    _, _, vh = np.linalg.svd(design)
    raw = vh[-1].reshape(3, 3)
    u, singular, vt = np.linalg.svd(raw)
    if np.linalg.det(u) < 0: u[:, -1] *= -1
    if np.linalg.det(vt) < 0: vt[-1, :] *= -1
    sigma = float((singular[0] + singular[1]) / 2.0)
    essential = u @ np.diag([sigma, sigma, 0.0]) @ vt
    residuals = [float(b @ essential @ a) for a, b in zip(p1, p2, strict=True)]
    rms = float(np.sqrt(np.mean(np.square(residuals))))
    if not np.isfinite(rms) or rms > maximum_epipolar_rms:
        return _unresolved(ids, "Calibrated correspondences do not support a coherent essential matrix within the reprojection gate.", epipolar_rms=rms)

    u, _, vt = np.linalg.svd(essential)
    if np.linalg.det(u) < 0: u[:, -1] *= -1
    if np.linalg.det(vt) < 0: vt[-1, :] *= -1
    w = np.array([[0., -1., 0.], [1., 0., 0.], [0., 0., 1.]])
    rotations = [u @ w @ vt, u @ w.T @ vt]
    rotations = [r if np.linalg.det(r) > 0 else -r for r in rotations]
    direction = u[:, 2]
    candidates = []
    index = 0
    for rotation in rotations:
        for translation in (direction, -direction):
            positive, parallaxes = _candidate_geometry(p1, p2, rotation, translation)
            median = float(np.median(parallaxes)) if parallaxes else 0.0
            candidates.append((positive, median, -index, rotation, translation)); index += 1
    candidates.sort(key=lambda item: (item[0], item[1], item[2]), reverse=True)
    best, second = candidates[0], candidates[1]
    required_positive = max(minimum_tracks, ceil(0.8 * len(usable)))
    if best[0] < required_positive or best[0] == second[0]:
        return _unresolved(ids, "Cheirality does not identify one relative camera pose strongly enough.", epipolar_rms=rms)
    if best[1] < minimum_parallax_degrees:
        return _unresolved(ids, f"Relative camera parallax is insufficient ({best[1]:.6g} deg).", epipolar_rms=rms)

    confidence = min([first_intrinsics.source.confidence, second_intrinsics.source.confidence] + [obs.source.confidence for _, a, b in usable for obs in (a, b)])
    camera1 = _camera_from_pose(first_photo_index, first_intrinsics, np.eye(3), np.zeros(3), confidence)
    camera2 = _camera_from_pose(second_photo_index, second_intrinsics, best[3], best[4], confidence)
    if camera1 is None or camera2 is None:
        return _unresolved(
            ids,
            "Calibrated pixel intrinsics are coherent, but the current BH-236 camera hypothesis exposes one scalar focal length; non-square-axis handoff remains UNRESOLVED rather than publishing a false camera.",
            epipolar_rms=rms,
        )
    return RelativeCameraEstimationResult(
        status="RESOLVED_RELATIVE", cameras=[camera1, camera2], supporting_landmark_ids=ids,
        epipolar_rms=rms, positive_depth_fraction=best[0] / len(usable), median_parallax_degrees=best[1],
        diagnostic=f"Resolved calibrated relative pose from {len(usable)} explicit tracks; translation scale remains arbitrary and metric scale is intentionally absent.",
    )
