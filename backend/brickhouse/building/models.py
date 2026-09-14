"""Pydantic contracts for BuildingModel v0.1."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, model_validator

EPSILON = 1e-9


class SourceKind(str, Enum):
    OBSERVED = "observed"
    USER_PROVIDED = "user_provided"
    INFERRED = "inferred"
    GENERATED_DEFAULT = "generated_default"


class SourceInfo(BaseModel):
    kind: SourceKind
    confidence: float = Field(ge=0.0, le=1.0)


class Position3D(BaseModel):
    x: float
    y: float
    z: float


class VolumeShape(str, Enum):
    RECTANGULAR_PRISM = "rectangular_prism"


class Volume(BaseModel):
    id: str
    shape: VolumeShape
    position: Position3D
    width: float = Field(gt=0)
    depth: float = Field(gt=0)
    height: float = Field(gt=0)
    floors: int = Field(ge=1, le=3)
    source: SourceInfo


class Facade(str, Enum):
    FRONT = "front"
    REAR = "rear"
    LEFT = "left"
    RIGHT = "right"


class OpeningType(str, Enum):
    WINDOW = "window"
    DOOR = "door"
    GARAGE_DOOR = "garage_door"
    UNKNOWN = "unknown"


class WindowStyle(str, Enum):
    SIMPLE = "simple"
    FOUR_PANE = "four_pane"
    TRADITIONAL_TALL = "traditional_tall"
    PAIRED = "paired"
    BAY = "bay"


class OpeningVisualDescription(BaseModel):
    """Observed opening composition preserved without implying LEGO geometry."""

    frame_color: str | None = None
    frame_material: str | None = None
    leaf_count: int | None = Field(default=None, ge=1, le=8)
    pane_count: int | None = Field(default=None, ge=1, le=32)
    pane_layout: str | None = None
    mullion_count: int | None = Field(default=None, ge=0, le=16)
    glazing: str | None = None
    sill: str | None = None
    sill_color: str | None = None
    surround_material: str | None = None
    surround_color: str | None = None
    surround_relief: Literal["projecting", "flush", "recessed"] | None = None
    glazing_plane: Literal["projecting", "flush", "recessed"] | None = None
    shutter_count: int | None = Field(default=None, ge=0, le=8)
    shutter_style: str | None = None
    shutter_color: str | None = None
    shutter_state: str | None = None
    notes: str | None = None


class Opening(BaseModel):
    id: str
    type: OpeningType
    volume_id: str
    facade: Facade
    offset_horizontal: float = Field(ge=0)
    offset_vertical: float = Field(ge=0)
    width: float = Field(gt=0)
    height: float = Field(gt=0)
    source: SourceInfo
    window_style: WindowStyle | None = None
    has_sill: bool | None = None
    has_decorative_surround: bool | None = None
    opening_visual: OpeningVisualDescription | None = None

    @model_validator(mode="after")
    def validate_window_metadata(self) -> "Opening":
        window_fields = (self.window_style, self.has_sill, self.has_decorative_surround)
        if self.type is not OpeningType.WINDOW and any(value is not None for value in window_fields):
            raise ValueError("window-specific metadata may only be defined on window openings")
        return self


class RoofType(str, Enum):
    FLAT = "flat"
    GABLE = "gable"
    SHED = "shed"


class RidgeDirection(str, Enum):
    WIDTH = "width"
    DEPTH = "depth"


class Roof(BaseModel):
    id: str
    volume_id: str
    type: RoofType
    overhang: float = Field(ge=0)
    ridge_direction: RidgeDirection | None = None
    down_slope_direction: Facade | None = None
    pitch_degrees: float | None = None
    source: SourceInfo

    @model_validator(mode="after")
    def validate_type_specific_fields(self) -> "Roof":
        if self.type is RoofType.GABLE:
            if self.ridge_direction is None:
                raise ValueError("gable roof requires ridge_direction")
            if self.pitch_degrees is None:
                raise ValueError("gable roof requires pitch_degrees")
            if not 0 < self.pitch_degrees < 90:
                raise ValueError("gable roof pitch_degrees must be > 0 and < 90")
            if self.down_slope_direction is not None:
                raise ValueError("gable roof must not define down_slope_direction")
        elif self.type is RoofType.SHED:
            if self.ridge_direction is not None:
                raise ValueError("shed roof must not define ridge_direction")
            if self.down_slope_direction is None:
                raise ValueError("shed roof requires down_slope_direction")
            if self.pitch_degrees is None:
                raise ValueError("shed roof requires pitch_degrees")
            if not 0 < self.pitch_degrees < 90:
                raise ValueError("shed roof pitch_degrees must be > 0 and < 90")
        else:
            if (
                self.ridge_direction is not None
                or self.down_slope_direction is not None
                or self.pitch_degrees is not None
            ):
                raise ValueError("flat roof must not define pitched-roof fields")
        return self


class AppearanceSection(BaseModel):
    color: str


class Appearance(BaseModel):
    walls: AppearanceSection | None = None
    roof: AppearanceSection | None = None
    frames: AppearanceSection | None = None


class Metadata(BaseModel):
    created_from: Literal["synthetic", "photo_analysis", "user_edit"]
    notes: str | None = None


class BuildingModel(BaseModel):
    schema_version: Literal["0.1"]
    id: str
    name: str
    building_type: str
    units: Literal["m"]
    volumes: list[Volume] = Field(min_length=1)
    openings: list[Opening] = Field(default_factory=list)
    roofs: list[Roof] = Field(default_factory=list)
    appearance: Appearance
    metadata: Metadata

    @model_validator(mode="after")
    def validate_cross_object_rules(self) -> "BuildingModel":
        self._validate_ids()
        volumes = {volume.id: volume for volume in self.volumes}
        self._validate_references(volumes)
        self._validate_openings(volumes)
        self._validate_roofs()
        return self

    def _validate_ids(self) -> None:
        all_ids = [obj.id for obj in [*self.volumes, *self.openings, *self.roofs]]
        if len(all_ids) != len(set(all_ids)):
            raise ValueError("object IDs must be globally unique")

    def _validate_references(self, volumes: dict[str, Volume]) -> None:
        for opening in self.openings:
            if opening.volume_id not in volumes:
                raise ValueError(f"opening {opening.id!r} references unknown volume")
        for roof in self.roofs:
            if roof.volume_id not in volumes:
                raise ValueError(f"roof {roof.id!r} references unknown volume")

    def _validate_openings(self, volumes: dict[str, Volume]) -> None:
        for opening in self.openings:
            volume = volumes[opening.volume_id]
            facade_span = volume.width if opening.facade in {Facade.FRONT, Facade.REAR} else volume.depth
            if opening.offset_horizontal + opening.width > facade_span + EPSILON:
                raise ValueError(f"opening {opening.id!r} extends past facade horizontally")
            if opening.offset_vertical + opening.height > volume.height + EPSILON:
                raise ValueError(f"opening {opening.id!r} extends above volume")

        for index, first in enumerate(self.openings):
            for second in self.openings[index + 1 :]:
                if first.volume_id != second.volume_id or first.facade is not second.facade:
                    continue
                if self._openings_overlap(first, second):
                    raise ValueError(f"openings {first.id!r} and {second.id!r} overlap")

    @staticmethod
    def _openings_overlap(first: Opening, second: Opening) -> bool:
        first_right = first.offset_horizontal + first.width
        second_right = second.offset_horizontal + second.width
        first_top = first.offset_vertical + first.height
        second_top = second.offset_vertical + second.height

        horizontal_overlap = (
            first.offset_horizontal < second_right - EPSILON
            and second.offset_horizontal < first_right - EPSILON
        )
        vertical_overlap = (
            first.offset_vertical < second_top - EPSILON
            and second.offset_vertical < first_top - EPSILON
        )
        return horizontal_overlap and vertical_overlap

    def _validate_roofs(self) -> None:
        roof_volume_ids = [roof.volume_id for roof in self.roofs]
        if len(roof_volume_ids) != len(set(roof_volume_ids)):
            raise ValueError("at most one roof may reference a volume in v0.1")
