"""Bounded bridge from vision landmark proposals to BH-237 explicit tracks.

The vision provider may propose semantic physical identity. This module never
creates identity by feature similarity. It validates Survey provenance, performs
only a small deterministic local corner repeatability check around each proposed
point, and either refines or rejects the provider proposal.
"""
from __future__ import annotations

from math import hypot
from typing import Literal

import numpy as np
from pydantic import BaseModel, Field

from brickhouse.building import SourceInfo, SourceKind
from brickhouse.survey import ArchitecturalSurvey
from brickhouse.survey.evidence_candidates import (
    SurveyPhotoEvidenceCandidate,
    validate_survey_photo_evidence_candidates,
)
from brickhouse.vision.models import (
    VisionLandmarkProposal,
    VisionSurveyEvidenceCandidate,
)

from .photo_landmarks import ArchitecturalLandmarkObservation, ArchitecturalLandmarkTrack
from .photo_rectification import NormalizedImagePoint


LocalLandmarkStatus = Literal["ACCEPTED", "REJECTED"]
ProposalBridgeStatus = Literal[
    "ACCEPTED",
    "REJECTED_IDENTITY",
    "REJECTED_PROVENANCE",
    "REJECTED_LOCALIZATION",
]


class LocalLandmarkValidation(BaseModel):
    status: LocalLandmarkStatus
    proposed_point: NormalizedImagePoint
    refined_point: NormalizedImagePoint | None = None
    repeat_count: int = Field(ge=0)
    dispersion_px: float | None = Field(default=None, ge=0)
    shift_px: float | None = Field(default=None, ge=0)
    corner_strength: float | None = Field(default=None, ge=0)
    diagnostic: str


class VisionLandmarkProposalDecision(BaseModel):
    physical_landmark_id: str
    status: ProposalBridgeStatus
    provider_confidence: float = Field(ge=0, le=1)
    stable_photo_indexes: list[int] = Field(default_factory=list)
    provenance_photo_indexes: list[int] = Field(default_factory=list)
    diagnostic: str


class VisionLandmarkBridgeReport(BaseModel):
    candidate_count: int = Field(ge=0)
    identity_cross_view_defendable: int = Field(ge=0)
    localization_stable: int = Field(ge=0)
    provenance_valid_or_candidate: int = Field(ge=0)
    tracks_accepted: int = Field(ge=0)
    decisions: list[VisionLandmarkProposalDecision] = Field(default_factory=list)
    tracks: list[ArchitecturalLandmarkTrack] = Field(default_factory=list)


def convert_vision_evidence_candidates(
    survey: ArchitecturalSurvey,
    candidates: list[VisionSurveyEvidenceCandidate],
) -> list[SurveyPhotoEvidenceCandidate]:
    """Convert only explicit provider proposals; accepted Survey remains immutable."""
    result = [
        SurveyPhotoEvidenceCandidate(
            id=item.id,
            survey_observation_id=item.survey_observation_id,
            photo_index=item.photo_index,
            observation=item.observation,
            source=SourceInfo(kind=SourceKind.INFERRED, confidence=item.confidence),
            status=item.status,
            diagnostic=item.diagnostic,
        )
        for item in candidates
    ]
    validate_survey_photo_evidence_candidates(survey, result)
    return result


def _box_sum3(array: np.ndarray) -> np.ndarray:
    padded = np.pad(array, 1, mode="edge")
    total = np.zeros_like(array, dtype=float)
    for dy in range(3):
        for dx in range(3):
            total += padded[dy:dy + array.shape[0], dx:dx + array.shape[1]]
    return total


def _shi_tomasi_response(image: np.ndarray) -> np.ndarray:
    plane = np.asarray(image, dtype=float)
    if plane.ndim != 2:
        raise ValueError("local landmark validation requires one grayscale image plane")
    if min(plane.shape) < 16:
        raise ValueError("image plane is too small for local landmark validation")
    finite = np.isfinite(plane)
    if not finite.all():
        raise ValueError("image plane contains non-finite values")
    scale = float(plane.max() - plane.min())
    if scale > 1.0:
        plane = (plane - plane.min()) / max(scale, 1e-12)
    gy, gx = np.gradient(plane)
    sxx = _box_sum3(gx * gx)
    syy = _box_sum3(gy * gy)
    sxy = _box_sum3(gx * gy)
    trace = sxx + syy
    discriminant = np.maximum(0.0, (sxx - syy) ** 2 + 4.0 * sxy * sxy)
    return 0.5 * (trace - np.sqrt(discriminant))


def refine_local_landmark(
    image: np.ndarray,
    proposed_point: NormalizedImagePoint,
    *,
    search_radius_px: int = 8,
    maximum_dispersion_px: float = 3.0,
    maximum_shift_px: float = 12.0,
    minimum_corner_strength: float = 1e-4,
) -> LocalLandmarkValidation:
    """Refine one already-identified point; never discover or match identities."""
    if search_radius_px < 4:
        raise ValueError("local landmark search radius must be at least 4 pixels")
    response = _shi_tomasi_response(image)
    height, width = response.shape
    seed_x = proposed_point.x * (width - 1)
    seed_y = proposed_point.y * (height - 1)
    picks: list[tuple[float, float, float]] = []
    for radius in (search_radius_px - 2, search_radius_px, search_radius_px + 2):
        for offset_x, offset_y in ((0, 0), (-2, 0), (2, 0), (0, -2), (0, 2)):
            cx = seed_x + offset_x
            cy = seed_y + offset_y
            x0 = max(1, int(round(cx - radius)))
            x1 = min(width - 1, int(round(cx + radius + 1)))
            y0 = max(1, int(round(cy - radius)))
            y1 = min(height - 1, int(round(cy + radius + 1)))
            if x1 <= x0 or y1 <= y0:
                continue
            patch = response[y0:y1, x0:x1]
            index = int(np.argmax(patch))
            py, px = np.unravel_index(index, patch.shape)
            picks.append((float(x0 + px), float(y0 + py), float(patch[py, px])))
    if len(picks) < 5:
        return LocalLandmarkValidation(
            status="REJECTED",
            proposed_point=proposed_point,
            repeat_count=len(picks),
            diagnostic="Too few bounded local refinements were available near the proposed point.",
        )

    xs = np.array([item[0] for item in picks], dtype=float)
    ys = np.array([item[1] for item in picks], dtype=float)
    strengths = np.array([item[2] for item in picks], dtype=float)
    median_x = float(np.median(xs))
    median_y = float(np.median(ys))
    radial = np.sqrt((xs - median_x) ** 2 + (ys - median_y) ** 2)
    dispersion = float(np.sqrt(np.mean(radial ** 2)))
    shift = hypot(median_x - seed_x, median_y - seed_y)
    strength = float(np.median(strengths))
    refined = NormalizedImagePoint(
        x=min(1.0, max(0.0, median_x / (width - 1))),
        y=min(1.0, max(0.0, median_y / (height - 1))),
    )
    accepted = (
        dispersion <= maximum_dispersion_px
        and shift <= maximum_shift_px
        and strength >= minimum_corner_strength
    )
    reasons = []
    if dispersion > maximum_dispersion_px:
        reasons.append(f"repeatability dispersion {dispersion:.3g}px exceeds {maximum_dispersion_px:.3g}px")
    if shift > maximum_shift_px:
        reasons.append(f"local refinement shift {shift:.3g}px exceeds {maximum_shift_px:.3g}px")
    if strength < minimum_corner_strength:
        reasons.append("local structure is edge-like/diffuse rather than a stable corner")
    return LocalLandmarkValidation(
        status="ACCEPTED" if accepted else "REJECTED",
        proposed_point=proposed_point,
        refined_point=refined if accepted else None,
        repeat_count=len(picks),
        dispersion_px=dispersion,
        shift_px=shift,
        corner_strength=max(0.0, strength),
        diagnostic=("Stable bounded local corner refinement." if accepted else "; ".join(reasons)),
    )


def bridge_vision_landmarks(
    survey: ArchitecturalSurvey,
    proposals: list[VisionLandmarkProposal],
    image_planes: dict[int, np.ndarray],
    *,
    evidence_candidates: list[SurveyPhotoEvidenceCandidate] | None = None,
    minimum_provider_confidence: float = 0.7,
) -> VisionLandmarkBridgeReport:
    """Validate provider identity/provenance and locally refine into BH-237 tracks."""
    candidates = evidence_candidates or []
    if candidates:
        validate_survey_photo_evidence_candidates(survey, candidates)
    candidate_pairs = {
        (item.survey_observation_id, item.photo_index)
        for item in candidates
        if item.status == "PROPOSED"
    }
    survey_observations = {item.id: item for item in survey.observations}
    decisions: list[VisionLandmarkProposalDecision] = []
    tracks: list[ArchitecturalLandmarkTrack] = []
    identity_count = 0
    stable_count = 0
    provenance_count = 0

    for proposal in proposals:
        if proposal.identity_status != "PROPOSED" or proposal.confidence < minimum_provider_confidence:
            decisions.append(VisionLandmarkProposalDecision(
                physical_landmark_id=proposal.physical_landmark_id,
                status="REJECTED_IDENTITY",
                provider_confidence=proposal.confidence,
                diagnostic=proposal.diagnostic or "Provider did not make a sufficiently confident explicit physical-identity proposal.",
            ))
            continue
        identity_count += 1
        if proposal.survey_observation_id is None or proposal.survey_observation_id not in survey_observations:
            decisions.append(VisionLandmarkProposalDecision(
                physical_landmark_id=proposal.physical_landmark_id,
                status="REJECTED_PROVENANCE",
                provider_confidence=proposal.confidence,
                diagnostic="No valid Survey observation binding is available for this physical landmark.",
            ))
            continue
        survey_observation = survey_observations[proposal.survey_observation_id]
        accepted_evidence = {item.photo_index for item in survey_observation.evidence}
        provenance_photos: list[int] = []
        provenance_ok = True
        for item in proposal.observations:
            if item.photo_index in accepted_evidence or (proposal.survey_observation_id, item.photo_index) in candidate_pairs:
                provenance_photos.append(item.photo_index)
            else:
                provenance_ok = False
        if not provenance_ok:
            decisions.append(VisionLandmarkProposalDecision(
                physical_landmark_id=proposal.physical_landmark_id,
                status="REJECTED_PROVENANCE",
                provider_confidence=proposal.confidence,
                provenance_photo_indexes=sorted(provenance_photos),
                diagnostic="One or more proposed photo occurrences have neither accepted Survey evidence nor an explicit new-evidence candidate.",
            ))
            continue
        provenance_count += 1

        refined_observations: list[ArchitecturalLandmarkObservation] = []
        stable_photos: list[int] = []
        local_failures: list[str] = []
        for item in proposal.observations:
            plane = image_planes.get(item.photo_index)
            if plane is None:
                local_failures.append(f"photo {item.photo_index}: image plane unavailable")
                continue
            validation = refine_local_landmark(
                plane,
                NormalizedImagePoint(x=item.x, y=item.y),
            )
            if validation.status != "ACCEPTED" or validation.refined_point is None:
                local_failures.append(f"photo {item.photo_index}: {validation.diagnostic}")
                continue
            stable_photos.append(item.photo_index)
            refined_observations.append(ArchitecturalLandmarkObservation(
                physical_landmark_id=proposal.physical_landmark_id,
                photo_index=item.photo_index,
                survey_observation_id=proposal.survey_observation_id,
                point=validation.refined_point,
                source=SourceInfo(
                    kind=SourceKind.OBSERVED,
                    confidence=min(proposal.confidence, item.confidence),
                ),
                statement=(
                    f"Vision provider proposed {proposal.description}; bounded local validation refined the location "
                    f"with {validation.dispersion_px:.3g}px repeatability dispersion."
                ),
            ))
        if len(refined_observations) < 2:
            decisions.append(VisionLandmarkProposalDecision(
                physical_landmark_id=proposal.physical_landmark_id,
                status="REJECTED_LOCALIZATION",
                provider_confidence=proposal.confidence,
                stable_photo_indexes=sorted(stable_photos),
                provenance_photo_indexes=sorted(provenance_photos),
                diagnostic="; ".join(local_failures) or "Fewer than two stable local observations survived.",
            ))
            continue
        stable_count += 1
        track = ArchitecturalLandmarkTrack(
            id=f"vision-{proposal.physical_landmark_id}",
            physical_landmark_id=proposal.physical_landmark_id,
            survey_observation_id=proposal.survey_observation_id,
            observations=refined_observations,
            source=SourceInfo(kind=SourceKind.OBSERVED, confidence=proposal.confidence),
            statement=(
                "Explicit provider-proposed physical identity retained only after Survey provenance and bounded local "
                "repeatability validation; no feature matcher created this identity."
            ),
        )
        tracks.append(track)
        decisions.append(VisionLandmarkProposalDecision(
            physical_landmark_id=proposal.physical_landmark_id,
            status="ACCEPTED",
            provider_confidence=proposal.confidence,
            stable_photo_indexes=sorted(stable_photos),
            provenance_photo_indexes=sorted(provenance_photos),
            diagnostic="Physical identity proposal retained with at least two stable, traceable photo occurrences.",
        ))

    return VisionLandmarkBridgeReport(
        candidate_count=len(proposals),
        identity_cross_view_defendable=identity_count,
        localization_stable=stable_count,
        provenance_valid_or_candidate=provenance_count,
        tracks_accepted=len(tracks),
        decisions=decisions,
        tracks=tracks,
    )
