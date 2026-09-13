"""Explicit architectural landmark correspondences backed by photo/Survey evidence.

This sidecar does not discover or match landmarks. Physical identity is declared
explicitly by the caller and is validated against immutable Survey evidence before
being adapted to the BH-236 relative reconstruction contract. BH-238 additionally
allows an explicit proposed-photo-evidence sidecar, without mutating accepted Survey.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from brickhouse.building import SourceInfo, SourceKind
from brickhouse.survey import ArchitecturalSurvey
from brickhouse.survey.evidence_candidates import (
    SurveyPhotoEvidenceCandidate,
    validate_survey_photo_evidence_candidates,
)

from .photo_rectification import NormalizedImagePoint
from .photo_scale_cues import PhotoGeometryAnnotation, validate_photo_geometry_annotations
from .relative_multiview import RelativeLandmarkObservation, RelativeLandmarkTrack


ArchitecturalLandmarkStatus = Literal["EXPLICIT_MATCH"]


class ArchitecturalLandmarkObservation(BaseModel):
    """One explicitly identified occurrence of a physical landmark in one photo."""

    physical_landmark_id: str = Field(min_length=1)
    photo_index: int = Field(ge=1)
    survey_observation_id: str = Field(min_length=1)
    point: NormalizedImagePoint
    source: SourceInfo
    statement: str = Field(min_length=1)
    coordinate_space_id: str = Field(default="image", min_length=1)
    geometry_annotation_id: str | None = None

    @model_validator(mode="after")
    def validate_source(self) -> "ArchitecturalLandmarkObservation":
        if self.source.kind not in {SourceKind.OBSERVED, SourceKind.INFERRED}:
            raise ValueError("architectural landmark observation source must be observed or inferred")
        return self


class ArchitecturalLandmarkTrack(BaseModel):
    """Explicit claim that listed 2D observations are the same physical landmark."""

    id: str = Field(min_length=1)
    physical_landmark_id: str = Field(min_length=1)
    survey_observation_id: str = Field(min_length=1)
    observations: list[ArchitecturalLandmarkObservation] = Field(min_length=2)
    status: ArchitecturalLandmarkStatus = "EXPLICIT_MATCH"
    source: SourceInfo
    statement: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_explicit_identity(self) -> "ArchitecturalLandmarkTrack":
        if self.source.kind not in {SourceKind.OBSERVED, SourceKind.USER_PROVIDED}:
            raise ValueError("physical landmark identity must be explicitly observed or user_provided")
        photos = [item.photo_index for item in self.observations]
        if len(photos) != len(set(photos)):
            raise ValueError("an architectural landmark track may contain at most one observation per photo")
        for item in self.observations:
            if item.physical_landmark_id != self.physical_landmark_id:
                raise ValueError("landmark observation physical identity disagrees with its explicit track identity")
            if item.survey_observation_id != self.survey_observation_id:
                raise ValueError("landmark observation Survey identity disagrees with its explicit track binding")
            if item.coordinate_space_id != "image":
                raise ValueError("BH-237 landmark bridge currently accepts original image coordinates only")
        return self


def validate_architectural_landmark_tracks(
    survey: ArchitecturalSurvey,
    tracks: list[ArchitecturalLandmarkTrack],
    *,
    geometry_annotations: list[PhotoGeometryAnnotation] | None = None,
    evidence_candidates: list[SurveyPhotoEvidenceCandidate] | None = None,
) -> None:
    """Validate explicit identity plus accepted or explicitly proposed photo provenance."""
    track_ids = [track.id for track in tracks]
    if len(track_ids) != len(set(track_ids)):
        raise ValueError("architectural landmark track ids must be unique")
    physical_ids = [track.physical_landmark_id for track in tracks]
    if len(physical_ids) != len(set(physical_ids)):
        raise ValueError("physical landmark ids must be unique across explicit tracks")

    known_photos = {photo.photo_index for photo in survey.photos}
    survey_observations = {observation.id: observation for observation in survey.observations}
    annotations = geometry_annotations or []
    if annotations:
        validate_photo_geometry_annotations(survey, annotations)
    annotation_by_id = {annotation.id: annotation for annotation in annotations}

    candidates = evidence_candidates or []
    if candidates:
        validate_survey_photo_evidence_candidates(survey, candidates)
    candidate_pairs = {
        (item.survey_observation_id, item.photo_index)
        for item in candidates
        if item.status == "PROPOSED"
    }

    for track in tracks:
        observation = survey_observations.get(track.survey_observation_id)
        if observation is None:
            raise ValueError(
                f"landmark track {track.id!r} references unknown Survey observation {track.survey_observation_id!r}"
            )
        evidence_photos = {evidence.photo_index for evidence in observation.evidence}
        for item in track.observations:
            if item.photo_index not in known_photos:
                raise ValueError(f"landmark track {track.id!r} references unknown photo {item.photo_index}")
            has_accepted_evidence = item.photo_index in evidence_photos
            has_candidate_evidence = (track.survey_observation_id, item.photo_index) in candidate_pairs
            if not (has_accepted_evidence or has_candidate_evidence):
                raise ValueError(
                    f"landmark track {track.id!r} is not backed by accepted Survey evidence or an explicit "
                    f"candidate for observation {track.survey_observation_id!r} on photo {item.photo_index}"
                )
            if item.geometry_annotation_id is None:
                continue
            annotation = annotation_by_id.get(item.geometry_annotation_id)
            if annotation is None:
                raise ValueError(
                    f"landmark track {track.id!r} references unknown photo geometry annotation "
                    f"{item.geometry_annotation_id!r}"
                )
            if (
                annotation.photo_index != item.photo_index
                or annotation.observation_id != item.survey_observation_id
                or annotation.coordinate_space_id != item.coordinate_space_id
            ):
                raise ValueError(
                    f"landmark track {track.id!r} geometry annotation does not share its photo, Survey identity and coordinate space"
                )
            region = annotation.region
            if not (region.x0 <= item.point.x <= region.x1 and region.y0 <= item.point.y <= region.y1):
                raise ValueError(
                    f"landmark track {track.id!r} point lies outside geometry annotation {annotation.id!r}"
                )


def build_relative_landmark_tracks(
    survey: ArchitecturalSurvey,
    tracks: list[ArchitecturalLandmarkTrack],
    *,
    geometry_annotations: list[PhotoGeometryAnnotation] | None = None,
    evidence_candidates: list[SurveyPhotoEvidenceCandidate] | None = None,
) -> list[RelativeLandmarkTrack]:
    """Adapt only validated explicit correspondences to the BH-236 track contract."""
    validate_architectural_landmark_tracks(
        survey,
        tracks,
        geometry_annotations=geometry_annotations,
        evidence_candidates=evidence_candidates,
    )
    result: list[RelativeLandmarkTrack] = []
    for track in sorted(tracks, key=lambda item: item.physical_landmark_id):
        result.append(
            RelativeLandmarkTrack(
                id=track.physical_landmark_id,
                observations=[
                    RelativeLandmarkObservation(
                        photo_index=item.photo_index,
                        observation_id=item.survey_observation_id,
                        point=item.point,
                        source=item.source,
                        statement=item.statement,
                    )
                    for item in sorted(track.observations, key=lambda value: value.photo_index)
                ],
            )
        )
    return result
