"""Architectural survey contracts: observation before reconstruction."""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from brickhouse.building import Facade, SourceInfo


class Certainty(str, Enum):
    CERTAIN = "certain"
    PLAUSIBLE = "plausible"
    UNPROVEN = "unproven"


class KnowledgeMode(str, Enum):
    OBSERVED = "observed"
    DEDUCED_MULTIVIEW = "deduced_multiview"
    DEDUCED_ARCHITECTURALLY = "deduced_architecturally"
    HYPOTHESIS = "hypothesis"


class StructureRole(str, Enum):
    VERTICAL_SUPPORT = "vertical_support"
    DIAGONAL_BRACING = "diagonal_bracing"
    GUARDRAIL = "guardrail"


class ObservationKind(str, Enum):
    BUILDING_BOUNDARY = "building_boundary"
    TERRAIN = "terrain"
    MATERIAL = "material"
    WEATHERING = "weathering"
    OPENING = "opening"
    ROOF = "roof"
    CHIMNEY = "chimney"
    EQUIPMENT = "equipment"
    VOLUME = "volume"
    PLATFORM = "platform"
    STAIR = "stair"
    OCCLUSION = "occlusion"
    CONTEXT = "context"
    STRUCTURE = "structure"


class RelationKind(str, Enum):
    """Observed semantic/physical relation between two survey observations.

    Relations are evidence, not architectural assumptions. They let later stages
    preserve facts such as a stair joining a landing without making universal
    rules such as "every raised door needs a platform".
    """

    CONNECTS_TO = "connects_to"
    ADJACENT_TO = "adjacent_to"
    ALIGNED_WITH = "aligned_with"
    SUPPORTS = "supports"
    PART_OF = "part_of"
    SAME_PHYSICAL_OBJECT = "same_physical_object"


class NormalizedImageRegion(BaseModel):
    """Optional evidence box in image coordinates, normalized to 0..1."""

    x0: float = Field(ge=0, le=1)
    y0: float = Field(ge=0, le=1)
    x1: float = Field(ge=0, le=1)
    y1: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def validate_order(self) -> "NormalizedImageRegion":
        if self.x1 <= self.x0 or self.y1 <= self.y0:
            raise ValueError("image region must have positive area")
        return self


class PhotoEvidence(BaseModel):
    photo_index: int = Field(ge=1)
    observation: str = Field(min_length=1)
    region: NormalizedImageRegion | None = None


class CanonicalFrame(BaseModel):
    """Building-centric orientation independent of camera mirroring.

    x increases from the left edge to the right edge when an observer stands
    outside and looks straight at the canonical front facade. y increases from
    front to rear, z from low to high.
    """

    front_facade: Literal["front"] = "front"
    x_direction: Literal["front_view_left_to_right"] = "front_view_left_to_right"
    y_direction: Literal["front_to_rear"] = "front_to_rear"
    z_direction: Literal["bottom_to_top"] = "bottom_to_top"


class PhotoView(BaseModel):
    photo_index: int = Field(ge=1)
    # A targeted detail can be a soffit, roof junction, terrace underside, etc.
    # Such evidence has no honest facade coordinate. Keep legacy facade views as
    # the default, but allow detail photos to explicitly carry no facade.
    capture_role: Literal["facade_view", "targeted_detail"] = "facade_view"
    facade: Facade | None = None
    description: str = Field(min_length=1)
    source: SourceInfo
    image_left_maps_to_facade_offset: Literal["low", "high"] | None = "low"
    user_note: str | None = None

    @model_validator(mode="after")
    def validate_capture_role(self) -> "PhotoView":
        if self.capture_role == "targeted_detail":
            if self.facade is not None or self.image_left_maps_to_facade_offset is not None:
                raise ValueError(
                    "targeted_detail photos must not invent facade coordinates or image offset mapping"
                )
        else:
            if self.facade is None:
                raise ValueError("facade_view photos require facade")
            if self.image_left_maps_to_facade_offset is None:
                raise ValueError("facade_view photos require image_left_maps_to_facade_offset")
        return self


class KnownMeasurement(BaseModel):
    """Exact user-supplied metric anchors that must survive every AI handoff."""

    kind: Literal["front_width"]
    value: float = Field(gt=0)
    units: Literal["m"] = "m"
    source: SourceInfo


class SurfaceAppearance(BaseModel):
    base_material: str = Field(min_length=1)
    nominal_color: str = Field(min_length=1)
    finish: str | None = None
    weathering: list[str] = Field(default_factory=list)
    reproduce_weathering_in_lego: bool = False


class OpeningVisualDescription(BaseModel):
    frame_color: str | None = None
    frame_material: str | None = None
    leaf_count: int | None = Field(default=None, ge=1, le=8)
    pane_count: int | None = Field(default=None, ge=1, le=32)
    pane_layout: str | None = None
    mullion_count: int | None = Field(default=None, ge=0, le=16)
    glazing: str | None = None
    sill: str | None = None
    surround_material: str | None = None
    surround_color: str | None = None
    shutter_count: int | None = Field(default=None, ge=0, le=8)
    shutter_style: str | None = None
    shutter_color: str | None = None
    shutter_state: str | None = None
    notes: str | None = None


class SurveyObservation(BaseModel):
    id: str
    kind: ObservationKind
    facade: Facade | None = None
    certainty: Certainty
    knowledge_mode: KnowledgeMode | None = None
    qualitative_position: str | None = None
    structure_role: StructureRole | None = None
    statement: str = Field(min_length=1)
    evidence: list[PhotoEvidence] = Field(min_length=1)
    attributes: dict[str, Any] = Field(default_factory=dict)
    # Object existence and one of its properties are different claims. A roof
    # may certainly exist while its type/pitch is only plausible; an opening may
    # certainly exist while door-vs-window remains uncertain. This append-only,
    # backwards-compatible map makes that distinction machine-readable.
    attribute_certainty: dict[str, Certainty] = Field(default_factory=dict)
    attribute_knowledge_mode: dict[str, KnowledgeMode] = Field(default_factory=dict)
    appearance: SurfaceAppearance | None = None
    opening_visual: OpeningVisualDescription | None = None

    @model_validator(mode="after")
    def validate_attribute_certainty(self) -> "SurveyObservation":
        unknown = set(self.attribute_certainty) - set(self.attributes)
        if unknown:
            names = ", ".join(sorted(unknown))
            raise ValueError(
                f"attribute_certainty references missing attributes: {names}"
            )
        unknown_modes = set(self.attribute_knowledge_mode) - set(self.attributes)
        if unknown_modes:
            names = ", ".join(sorted(unknown_modes))
            raise ValueError(
                f"attribute_knowledge_mode references missing attributes: {names}"
            )
        if self.kind is ObservationKind.STRUCTURE and self.structure_role is None:
            raise ValueError("structure observations require structure_role")
        if self.kind is not ObservationKind.STRUCTURE and self.structure_role is not None:
            raise ValueError("structure_role may only be set on structure observations")
        return self

    def certainty_for_attribute(self, name: str) -> Certainty:
        """Return property certainty, preserving legacy Surveys when unmapped."""
        return self.attribute_certainty.get(name, self.certainty)


class SurveyRelation(BaseModel):
    id: str
    kind: RelationKind
    subject_id: str
    object_id: str
    certainty: Certainty
    knowledge_mode: KnowledgeMode | None = None
    statement: str = Field(min_length=1)
    evidence: list[PhotoEvidence] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_distinct_objects(self) -> "SurveyRelation":
        if self.subject_id == self.object_id:
            raise ValueError("survey relation subject_id and object_id must differ")
        return self


class RepresentationPolicy(BaseModel):
    """What understanding should survive, separately from LEGO fidelity."""

    preserve_nominal_materials: bool = True
    preserve_opening_composition: bool = True
    preserve_architectural_details: bool = True
    reproduce_weathering: bool = False
    reproduce_temporary_objects: bool = False


_REPRESENTATION_POLICY_FIELDS = {
    "preserve_nominal_materials",
    "preserve_opening_composition",
    "preserve_architectural_details",
    "reproduce_weathering",
    "reproduce_temporary_objects",
}
_LEGACY_QUALITATIVE_RANKS = {"low": 1, "high": 2}
_CONSERVATIVE_OBSERVATION_KIND_ALIASES = {
    "secondary_volume": ObservationKind.VOLUME.value,
}


class ArchitecturalSurvey(BaseModel):
    schema_version: Literal["0.1", "0.2"] = "0.1"
    id: str
    name: str
    canonical_frame: CanonicalFrame = Field(default_factory=CanonicalFrame)
    photos: list[PhotoView] = Field(min_length=1)
    known_measurements: list[KnownMeasurement] = Field(default_factory=list)
    observations: list[SurveyObservation] = Field(default_factory=list)
    relations: list[SurveyRelation] = Field(default_factory=list)
    representation_policy: RepresentationPolicy = Field(default_factory=RepresentationPolicy)
    notes: str | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_conservative_external_shapes(cls, value):
        """Repair only lossless/conservative external-AI shape drift.

        Some external models have returned ``representation_policy`` as a list
        of field names instead of the required object. Because that list carries
        no boolean values, the only non-fabricating interpretation is the
        backend's safe default policy. A literal ``secondary_volume`` observation
        kind is a narrower wording of the canonical ``volume`` category, so it
        can be normalized without changing the observation statement, evidence,
        attributes, identity, or relations. An opening whose semantic type is
        literally ``opening`` and explicitly unproven means the subtype is
        unknown, so the unsupported placeholder is removed. Legacy low/high
        layout labels are ordinal, not metric, and are normalized to ranks 1/2.
        """
        if not isinstance(value, dict):
            return value
        normalized = dict(value)

        policy = normalized.get("representation_policy")
        if (
            isinstance(policy, list)
            and all(isinstance(item, str) for item in policy)
            and set(policy).issubset(_REPRESENTATION_POLICY_FIELDS)
        ):
            normalized["representation_policy"] = RepresentationPolicy().model_dump()

        observations = normalized.get("observations")
        if isinstance(observations, list):
            repaired_observations = []
            for item in observations:
                if not isinstance(item, dict):
                    repaired_observations.append(item)
                    continue
                repaired = dict(item)
                kind = repaired.get("kind")
                if kind in _CONSERVATIVE_OBSERVATION_KIND_ALIASES:
                    repaired["kind"] = _CONSERVATIVE_OBSERVATION_KIND_ALIASES[kind]
                attributes = repaired.get("attributes")
                certainty_map = repaired.get("attribute_certainty")
                if isinstance(attributes, dict):
                    new_attributes = dict(attributes)
                    if new_attributes.get("semantic_type") == "opening":
                        semantic_certainty = certainty_map.get("semantic_type") if isinstance(certainty_map, dict) else None
                        if semantic_certainty == "unproven":
                            new_attributes.pop("semantic_type", None)
                            if isinstance(certainty_map, dict):
                                new_certainty = dict(certainty_map)
                                new_certainty.pop("semantic_type", None)
                                repaired["attribute_certainty"] = new_certainty
                    for field in ("facade_horizontal_rank", "facade_vertical_rank"):
                        rank = new_attributes.get(field)
                        if isinstance(rank, str) and rank in _LEGACY_QUALITATIVE_RANKS:
                            new_attributes[field] = _LEGACY_QUALITATIVE_RANKS[rank]
                    repaired["attributes"] = new_attributes
                repaired_observations.append(repaired)
            normalized["observations"] = repaired_observations

        return normalized

    @model_validator(mode="after")
    def validate_survey(self) -> "ArchitecturalSurvey":
        photo_indexes = [photo.photo_index for photo in self.photos]
        if len(photo_indexes) != len(set(photo_indexes)):
            raise ValueError("photo indexes must be unique")
        if not any(photo.facade is Facade.FRONT for photo in self.photos):
            raise ValueError("survey requires at least one canonical front photo")
        measurement_kinds = [measurement.kind for measurement in self.known_measurements]
        if len(measurement_kinds) != len(set(measurement_kinds)):
            raise ValueError("survey known measurement kinds must be unique")

        observation_ids = [observation.id for observation in self.observations]
        if len(observation_ids) != len(set(observation_ids)):
            raise ValueError("survey observation IDs must be unique")

        relation_ids = [relation.id for relation in self.relations]
        if len(relation_ids) != len(set(relation_ids)):
            raise ValueError("survey relation IDs must be unique")

        known_photos = set(photo_indexes)
        known_observations = set(observation_ids)
        for observation in self.observations:
            for evidence in observation.evidence:
                if evidence.photo_index not in known_photos:
                    raise ValueError(
                        f"observation {observation.id!r} references unknown photo {evidence.photo_index}"
                    )
        for relation in self.relations:
            if relation.subject_id not in known_observations or relation.object_id not in known_observations:
                raise ValueError(f"relation {relation.id!r} references unknown survey observation")
            for evidence in relation.evidence:
                if evidence.photo_index not in known_photos:
                    raise ValueError(f"relation {relation.id!r} references unknown photo {evidence.photo_index}")
        return self