"""Canonical supplier-independent BrickModel for downstream consumers."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from brickhouse.building.models import Facade, RidgeDirection
from .facade_details import FacadeDetailPlacement, TrimRole
from .roof import SUPPORTED_SLOPE_FAMILIES, SpatialRoof, _footprint, create_m0_roof_catalog
from .spatial import SpatialBrickShell
from .windows import WindowPartPlacement

PartCategory = Literal[
    "brick", "plate", "roof_tile", "ridge_tile", "window_frame", "window_pane",
    "facade_detail", "timber", "concrete", "masonry", "stone", "metal",
    "composite", "terrain",
]
PartComponent = Literal["wall", "roof", "facade_detail"]
EXTERIOR_MATERIAL_CATEGORIES = {
    "timber", "concrete", "masonry", "stone", "metal", "composite",
}


class BrickModelPart(BaseModel):
    placement_id: str
    part_id: str
    category: PartCategory
    component: PartComponent
    x_studs: int = Field(ge=0)
    y_studs: int = Field(ge=0)
    z_plates: int = Field(ge=0)
    rotation_quarter_turns: Literal[0, 1, 2, 3]
    facade: Facade | None = None
    roof_side: Literal["negative", "positive", "ridge", "slope"] | None = None
    opening_id: str | None = None
    trim_role: TrimRole | None = None
    semantic_color: str | None = Field(default=None, min_length=1)
    width_studs: int | None = Field(default=None, gt=0)
    length_studs: int | None = Field(default=None, gt=0)
    height_plates: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_semantic_zone(self):
        if self.component == "wall":
            if self.facade is None or self.roof_side is not None:
                raise ValueError("wall parts require facade and must not define roof_side")
            if self.category not in {"brick", "plate"}:
                raise ValueError("wall parts must use an orthogonal masonry category")
        elif self.component == "roof":
            if self.roof_side is None or self.facade is not None:
                raise ValueError("roof parts require roof_side and must not define facade")
            expected = "ridge_tile" if self.roof_side == "ridge" else "roof_tile"
            if self.category != expected:
                raise ValueError(
                    f"roof part on side {self.roof_side!r} must use category {expected!r}"
                )
        else:
            if self.facade is None or self.roof_side is not None:
                raise ValueError("facade detail parts require facade and must not define roof_side")
            allowed = {
                "brick", "plate", "window_frame", "window_pane", "facade_detail", "terrain",
                *EXTERIOR_MATERIAL_CATEGORIES,
            }
            if self.category not in allowed:
                raise ValueError("facade detail parts must use a facade-compatible category")

        if self.component != "facade_detail" and (self.opening_id is not None or self.trim_role is not None):
            raise ValueError("opening/trim provenance may only be attached to facade detail parts")
        if self.trim_role is not None and self.opening_id is None:
            raise ValueError("trim_role requires opening_id provenance")
        if self.semantic_color is not None and self.component != "facade_detail":
            raise ValueError("semantic_color is currently evidence-backed only for facade detail parts")
        return self


class BrickModel(BaseModel):
    schema_version: Literal["0.1"] = "0.1"
    building_id: str
    volume_id: str
    width_studs: int = Field(gt=0)
    depth_studs: int = Field(gt=0)
    height_plates: int = Field(gt=0)
    canvas_width_studs: int | None = Field(default=None, gt=0)
    canvas_depth_studs: int | None = Field(default=None, gt=0)
    origin_x_studs: int = Field(default=0, ge=0)
    origin_y_studs: int = Field(default=0, ge=0)
    parts: list[BrickModelPart] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_unique_placement_ids(self):
        ids = [part.placement_id for part in self.parts]
        if len(ids) != len(set(ids)):
            raise ValueError("BrickModel placement IDs must be unique")
        return self

    @model_validator(mode="after")
    def normalize_canvas_to_final_model(self):
        """Keep canvas metadata large enough for the final translated representation."""
        required_width = max(
            self.origin_x_studs + self.width_studs,
            max((part.x_studs + 1 for part in self.parts), default=1),
        )
        required_depth = max(
            self.origin_y_studs + self.depth_studs,
            max((part.y_studs + 1 for part in self.parts), default=1),
        )
        if self.canvas_width_studs is None or self.canvas_width_studs < required_width:
            object.__setattr__(self, "canvas_width_studs", required_width)
        if self.canvas_depth_studs is None or self.canvas_depth_studs < required_depth:
            object.__setattr__(self, "canvas_depth_studs", required_depth)
        return self


def _roof_category(part_id: str, side: str) -> Literal["roof_tile", "ridge_tile"]:
    definition = create_m0_roof_catalog().get(part_id)
    expected = "ridge_tile" if side == "ridge" else "roof_tile"
    if definition.category != expected:
        raise ValueError(
            f"roof placement {part_id!r} has category {definition.category!r}, expected {expected!r}"
        )
    return expected


def _roof_family(roof: SpatialRoof):
    catalog = create_m0_roof_catalog()
    ids = {
        catalog.get(placement.part_id).slope_family
        for placement in roof.placements
        if placement.side in {"negative", "positive"}
    }
    ids.discard(None)
    if len(ids) != 1:
        raise ValueError("gable wall generation requires exactly one roof slope family")
    family_id = next(iter(ids))
    return next(family for family in SUPPORTED_SLOPE_FAMILIES if family.id == family_id)


_GABLE_BRICKS = (
    (8, "BRICK_1X8"), (6, "BRICK_1X6"), (4, "BRICK_1X4"),
    (3, "BRICK_1X3"), (2, "BRICK_1X2"), (1, "BRICK_1X1"),
)


def _tile_gable_course(start: int, end: int, reverse: bool):
    remaining = end - start
    spans = []
    while remaining:
        for span, part_id in _GABLE_BRICKS:
            if span <= remaining:
                spans.append((span, part_id))
                remaining -= span
                break
    if reverse:
        spans.reverse()
    cursor = start
    out = []
    for span, part_id in spans:
        out.append((cursor, part_id, span))
        cursor += span
    return out


def _generate_gable_wall_parts(shell: SpatialBrickShell, roof: SpatialRoof):
    family = _roof_family(roof)
    wall_top = shell.height_bricks * 3
    negative = [placement for placement in roof.placements if placement.side == "negative"]
    if not negative:
        return []
    if roof.ridge_direction is RidgeDirection.DEPTH:
        slope_axes = sorted({placement.x_studs for placement in negative})
        span = shell.width_studs
        facades = (Facade.FRONT, Facade.REAR)
    else:
        slope_axes = sorted({placement.y_studs for placement in negative})
        span = shell.depth_studs
        facades = (Facade.LEFT, Facade.RIGHT)

    result = []
    index = 1
    for facade in facades:
        for level in range(len(slope_axes)):
            trim = family.footprint_depth_studs + level * family.course_advance_studs
            start, end = trim, span - trim
            if end <= start:
                continue
            for local, part_id, brick_span in _tile_gable_course(start, end, bool(level % 2)):
                if roof.ridge_direction is RidgeDirection.DEPTH:
                    x = local
                    y = 0 if facade is Facade.FRONT else shell.depth_studs - 1
                else:
                    x = 0 if facade is Facade.LEFT else shell.width_studs - 1
                    y = local
                result.append(
                    BrickModelPart(
                        placement_id=f"gable-{index:06d}", part_id=part_id,
                        category="brick", component="wall", x_studs=x, y_studs=y,
                        z_plates=wall_top + level * family.rise_plates,
                        rotation_quarter_turns=(1 if brick_span > 1 and facade in {Facade.FRONT, Facade.REAR} else 0),
                        facade=facade,
                    )
                )
                index += 1
    return result


def _roof_model_frame(roof: SpatialRoof | None) -> tuple[int, int, int, int]:
    if roof is None or not roof.placements:
        return 0, 0, 0, 0
    cells = set().union(*(_footprint(placement) for placement in roof.placements))
    min_x = min(x for x, _ in cells)
    min_y = min(y for _, y in cells)
    max_x = max(x for x, _ in cells)
    max_y = max(y for _, y in cells)
    x_offset = max(0, -min_x)
    y_offset = max(0, -min_y)
    return x_offset, y_offset, max_x + x_offset + 1, max_y + y_offset + 1


def _model_roof_footprint(part: BrickModelPart) -> set[tuple[int, int]]:
    definition = create_m0_roof_catalog().get(part.part_id)
    footprint_x, footprint_y = (
        (definition.length_studs, definition.width_studs)
        if part.rotation_quarter_turns % 2
        else (definition.width_studs, definition.length_studs)
    )
    return {
        (part.x_studs + dx, part.y_studs + dy)
        for dx in range(footprint_x)
        for dy in range(footprint_y)
    }


def _validate_final_gable_roof_host_contact(model: BrickModel, shell: SpatialBrickShell, roof: SpatialRoof) -> None:
    wall_top = shell.height_bricks * 3
    for side in ("negative", "positive"):
        side_parts = [part for part in model.parts if part.component == "roof" and part.roof_side == side]
        if not side_parts:
            raise ValueError(f"final gable roof side {side!r} has no slope placements")
        eave_z = min(part.z_plates for part in side_parts)
        if eave_z != wall_top:
            raise ValueError(f"final gable roof side {side!r} eave is at {eave_z} plates, expected host wall top {wall_top}")
        eave_cells = set().union(*(_model_roof_footprint(part) for part in side_parts if part.z_plates == eave_z))
        if roof.ridge_direction is RidgeDirection.DEPTH:
            host_axis = model.origin_x_studs if side == "negative" else model.origin_x_studs + shell.width_studs - 1
            touches = any(x == host_axis for x, _ in eave_cells)
        else:
            host_axis = model.origin_y_studs if side == "negative" else model.origin_y_studs + shell.depth_studs - 1
            touches = any(y == host_axis for _, y in eave_cells)
        if not touches:
            raise ValueError(f"final gable roof side {side!r} lost contact with host boundary at stud axis {host_axis} after BrickModel translation")


def generate_brick_model(
    shell: SpatialBrickShell,
    roof: SpatialRoof | None,
    facade_details: list[FacadeDetailPlacement] | None = None,
    window_parts: list[WindowPartPlacement] | None = None,
) -> BrickModel:
    if roof is not None and shell.building_id != roof.building_id:
        raise ValueError("spatial shell and roof must reference the same building")

    x_offset, y_offset, roof_width, roof_depth = _roof_model_frame(roof)
    parts = []
    for index, placement in enumerate(shell.placements, start=1):
        parts.append(BrickModelPart(
            placement_id=f"wall-{index:06d}", part_id=placement.brick_id,
            category="brick", component="wall", x_studs=placement.x_studs + x_offset,
            y_studs=placement.y_studs + y_offset, z_plates=placement.z_plates,
            rotation_quarter_turns=placement.rotation_quarter_turns, facade=placement.facade,
        ))
    if roof is not None:
        parts.extend(
            part.model_copy(update={"x_studs": part.x_studs + x_offset, "y_studs": part.y_studs + y_offset})
            for part in _generate_gable_wall_parts(shell, roof)
        )

    for index, placement in enumerate(facade_details or [], start=1):
        parts.append(BrickModelPart(
            placement_id=f"detail-{index:06d}", part_id=placement.part_id,
            category=placement.category, component="facade_detail",
            x_studs=placement.x_studs + x_offset, y_studs=placement.y_studs + y_offset,
            z_plates=placement.z_plates, rotation_quarter_turns=placement.rotation_quarter_turns,
            facade=placement.facade, opening_id=placement.opening_id,
            trim_role=placement.trim_role, semantic_color=placement.semantic_color,
        ))
    for index, placement in enumerate(window_parts or [], start=1):
        parts.append(BrickModelPart(
            placement_id=f"window-{index:06d}", part_id=placement.part_id,
            category=placement.category, component="facade_detail",
            x_studs=placement.x_studs + x_offset, y_studs=placement.y_studs + y_offset,
            z_plates=placement.z_plates, rotation_quarter_turns=placement.rotation_quarter_turns,
            facade=placement.facade, opening_id=placement.opening_id,
        ))
    if roof is not None:
        for index, placement in enumerate(roof.placements, start=1):
            parts.append(BrickModelPart(
                placement_id=f"roof-{index:06d}", part_id=placement.part_id,
                category=_roof_category(placement.part_id, placement.side), component="roof",
                x_studs=placement.x_studs + x_offset, y_studs=placement.y_studs + y_offset,
                z_plates=placement.z_plates, rotation_quarter_turns=placement.rotation_quarter_turns,
                roof_side=placement.side,
            ))

    wall_top = shell.height_bricks * 3
    roof_top = wall_top
    if roof is not None:
        catalog = create_m0_roof_catalog()
        roof_top = max(
            (placement.z_plates + catalog.get(placement.part_id).height_plates for placement in roof.placements),
            default=wall_top,
        )
    model = BrickModel(
        building_id=shell.building_id, volume_id=shell.volume_id,
        width_studs=shell.width_studs, depth_studs=shell.depth_studs,
        height_plates=max(wall_top, roof_top),
        canvas_width_studs=max(shell.width_studs + x_offset, roof_width),
        canvas_depth_studs=max(shell.depth_studs + y_offset, roof_depth),
        origin_x_studs=x_offset, origin_y_studs=y_offset, parts=parts,
    )
    if roof is not None:
        _validate_final_gable_roof_host_contact(model, shell, roof)
    return model
