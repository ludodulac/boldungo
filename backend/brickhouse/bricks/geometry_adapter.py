"""Opt-in bridge from BrickHouse canonical placements to the LDraw geometry engine.

Only canonical parts with a verified LDraw identity and placement rule are mapped.
Unknown architectural/detail parts are never guessed.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from lego_geometry_engine import (
    LDrawLibrary,
    PartDefinition,
    PartInstance,
    Transform,
    analyze_assembly,
    instantiate,
)

from .brick_model import BrickModel, BrickModelPart

LDU_PER_STUD = 20.0
LDU_PER_PLATE = 8.0
GEOMETRY_FOOTPRINT_EPS = 1e-4


@dataclass(frozen=True)
class LDrawPartMapping:
    ldraw_id: str
    width_studs: int
    length_studs: int
    height_plates: int = 3
    placement_kind: str = "standard"


CANONICAL_LDRAW_PARTS: Mapping[str, LDrawPartMapping] = {
    "BRICK_1X1": LDrawPartMapping("3005", 1, 1),
    "BRICK_1X2": LDrawPartMapping("3004", 1, 2),
    "BRICK_1X3": LDrawPartMapping("3622", 1, 3),
    "BRICK_1X4": LDrawPartMapping("3010", 1, 4),
    "BRICK_1X6": LDrawPartMapping("3009", 1, 6),
    "BRICK_1X8": LDrawPartMapping("3008", 1, 8),
    "BRICK_2X2": LDrawPartMapping("3003", 2, 2),
    "BRICK_2X3": LDrawPartMapping("3002", 2, 3),
    "BRICK_2X4": LDrawPartMapping("3001", 2, 4),
    "BRICK_2X6": LDrawPartMapping("2456", 2, 6),
    "BRICK_2X8": LDrawPartMapping("3007", 2, 8),
    "BRICK_2X10": LDrawPartMapping("3006", 2, 10),
    # Official LDraw standard rectangular plates. These mappings are part of
    # the placement contract: PLACEMENT_APPROVED pieces must have verified
    # geometry-engine identities.
    "PLATE_1X1": LDrawPartMapping("3024", 1, 1, height_plates=1),
    "PLATE_1X2": LDrawPartMapping("3023b", 1, 2, height_plates=1),
    "PLATE_1X3": LDrawPartMapping("3623", 1, 3, height_plates=1),
    "PLATE_1X4": LDrawPartMapping("3710", 1, 4, height_plates=1),
    "PLATE_1X6": LDrawPartMapping("3666", 1, 6, height_plates=1),
    "PLATE_1X8": LDrawPartMapping("3460", 1, 8, height_plates=1),
    # Validated modern window assemblies. Frames and panes share the same
    # canonical LDraw origin; pane geometry is inset inside that frame origin,
    # so both use the standard BrickModel-to-LDraw placement transform.
    "WINDOW_1X2X2_60592": LDrawPartMapping("60592", 1, 2, height_plates=6),
    "GLASS_FOR_WINDOW_1X2X2_60601": LDrawPartMapping("60601", 1, 2, height_plates=6),
    "WINDOW_1X2X3_60593": LDrawPartMapping("60593", 1, 2, height_plates=9),
    "GLASS_FOR_WINDOW_1X2X3_60602": LDrawPartMapping("60602", 1, 2, height_plates=9),
    "WINDOW_1X4X3_60594": LDrawPartMapping("60594", 1, 4, height_plates=9),
    "GLASS_FOR_WINDOW_1X4X3_60603": LDrawPartMapping("60603", 1, 4, height_plates=9),
    # Flat ridge cover tiles used by the current gable-roof generator.
    "TILE_2X2": LDrawPartMapping("3068b", 2, 2, height_plates=1),
    "TILE_2X3": LDrawPartMapping("26603", 2, 3, height_plates=1),
    "TILE_2X4": LDrawPartMapping("87079", 2, 4, height_plates=1),
    # Official LDraw roof families. All of these slope parts use local X as
    # their longitudinal axis and rise toward local +Z, but their origins are
    # not centered on the footprint, so placement is bbox-anchored below.
    "BRICK_SLOPED_18_4X2": LDrawPartMapping("30363", 4, 2, placement_kind="slope"),
    "BRICK_SLOPED_33_3X6": LDrawPartMapping("3939", 3, 6, placement_kind="slope"),
    "BRICK_SLOPED_33_3X4": LDrawPartMapping("3297", 3, 4, placement_kind="slope"),
    "BRICK_SLOPED_33_3X2": LDrawPartMapping("3298", 3, 2, placement_kind="slope"),
    "BRICK_SLOPED_45_2X4": LDrawPartMapping("3037", 2, 4, placement_kind="slope"),
    "BRICK_SLOPED_45_2X3": LDrawPartMapping("3038", 2, 3, placement_kind="slope"),
    "BRICK_SLOPED_45_2X2": LDrawPartMapping("3039", 2, 2, placement_kind="slope"),
    "BRICK_SLOPED_45_2X1": LDrawPartMapping("3040b", 2, 1, placement_kind="slope"),
}


class UnmappedCanonicalPartError(ValueError):
    pass


@dataclass(frozen=True)
class BrickModelGeometryResult:
    report: object
    mapped_placements: tuple[str, ...]
    unmapped_placements: tuple[str, ...]

    @property
    def complete(self) -> bool:
        return not self.unmapped_placements

    @property
    def valid(self) -> bool:
        return self.complete and bool(getattr(self.report, "valid", False))


def _rotation_matrix(turns: int) -> tuple[tuple[float, float, float], ...]:
    return (
        ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
        ((0.0, 0.0, 1.0), (0.0, 1.0, 0.0), (-1.0, 0.0, 0.0)),
        ((-1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, -1.0)),
        ((0.0, 0.0, -1.0), (0.0, 1.0, 0.0), (1.0, 0.0, 0.0)),
    )[turns % 4]


def _transform_from_rotation(rotation, tx: float, ty: float, tz: float) -> Transform:
    return Transform(((rotation[0][0],rotation[0][1],rotation[0][2],tx),(rotation[1][0],rotation[1][1],rotation[1][2],ty),(rotation[2][0],rotation[2][1],rotation[2][2],tz),(0.0,0.0,0.0,1.0)))


def brick_model_part_transform(part: BrickModelPart, mapping: LDrawPartMapping) -> Transform:
    turns = part.rotation_quarter_turns % 4
    footprint_x = mapping.length_studs if turns % 2 else mapping.width_studs
    footprint_z = mapping.width_studs if turns % 2 else mapping.length_studs
    center_x = (part.x_studs + footprint_x / 2.0) * LDU_PER_STUD
    center_z = (part.y_studs + footprint_z / 2.0) * LDU_PER_STUD
    top_y = -(part.z_plates + mapping.height_plates) * LDU_PER_PLATE
    # Canonical rectangular LDraw parts put length on local X and width on
    # local Z. BrickModel rotation=0 expects width on grid X and length on grid
    # Y, so the base conversion is a -90 degree turn (quarter turn 3).
    physical_turns = (3 + turns) % 4
    return _transform_from_rotation(_rotation_matrix(physical_turns), center_x, top_y, center_z)


def _rotated_bbox(definition: PartDefinition, turns: int) -> tuple[float, float, float, float]:
    transform = _transform_from_rotation(_rotation_matrix(turns), 0.0, 0.0, 0.0)
    minimum, maximum = definition.bbox.minimum, definition.bbox.maximum
    corners = [transform.point((x,y,z)) for x in (minimum[0],maximum[0]) for y in (minimum[1],maximum[1]) for z in (minimum[2],maximum[2])]
    return (min(p[0] for p in corners),max(p[0] for p in corners),min(p[2] for p in corners),max(p[2] for p in corners))


def _slope_transform(part: BrickModelPart, mapping: LDrawPartMapping, definition: PartDefinition) -> Transform:
    if part.roof_side not in {"negative", "positive"}:
        raise UnmappedCanonicalPartError(f"Slope {part.part_id!r} requires roof_side negative/positive at placement {part.placement_id!r}")
    if part.roof_side == "negative":
        physical_turns = (1 - part.rotation_quarter_turns) % 4
    else:
        physical_turns = (3 - part.rotation_quarter_turns) % 4
    min_x,max_x,min_z,max_z = _rotated_bbox(definition,physical_turns)
    footprint_x = mapping.length_studs if part.rotation_quarter_turns % 2 else mapping.width_studs
    footprint_z = mapping.width_studs if part.rotation_quarter_turns % 2 else mapping.length_studs
    expected_x,expected_z = footprint_x*LDU_PER_STUD,footprint_z*LDU_PER_STUD
    actual_x,actual_z = max_x-min_x,max_z-min_z
    if abs(actual_x-expected_x)>GEOMETRY_FOOTPRINT_EPS or abs(actual_z-expected_z)>GEOMETRY_FOOTPRINT_EPS:
        raise ValueError(f"LDraw footprint mismatch for {part.part_id}: expected {expected_x}x{expected_z} LDU, got {actual_x}x{actual_z} LDU")
    tx = part.x_studs*LDU_PER_STUD-min_x
    tz = part.y_studs*LDU_PER_STUD-min_z
    ty = -part.z_plates*LDU_PER_PLATE-definition.bbox.maximum[1]
    return _transform_from_rotation(_rotation_matrix(physical_turns),tx,ty,tz)


def brick_model_part_to_instance(part: BrickModelPart, library: LDrawLibrary) -> PartInstance:
    mapping=CANONICAL_LDRAW_PARTS.get(part.part_id)
    if mapping is None:
        raise UnmappedCanonicalPartError(f"No verified LDraw mapping for canonical part {part.part_id!r} at placement {part.placement_id!r}")
    definition=library.load_part(mapping.ldraw_id)
    transform=_slope_transform(part,mapping,definition) if mapping.placement_kind=="slope" else brick_model_part_transform(part,mapping)
    return instantiate(definition,part.placement_id,transform,color=part.semantic_color)


def brick_model_to_instances(model: BrickModel, library: LDrawLibrary, *, strict: bool=True) -> tuple[list[PartInstance],tuple[str,...]]:
    instances=[]; unmapped=[]
    for part in model.parts:
        try: instances.append(brick_model_part_to_instance(part,library))
        except UnmappedCanonicalPartError:
            if strict: raise
            unmapped.append(part.placement_id)
    return instances,tuple(unmapped)


def analyze_brick_model_geometry(model: BrickModel, library: LDrawLibrary, *, strict: bool=True) -> BrickModelGeometryResult:
    instances,unmapped=brick_model_to_instances(model,library,strict=strict)
    report=analyze_assembly(instances)
    return BrickModelGeometryResult(report=report,mapped_placements=tuple(i.instance_id for i in instances),unmapped_placements=unmapped)
