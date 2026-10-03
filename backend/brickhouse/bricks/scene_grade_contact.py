"""Render only evidence-backed local grade contacts when a full grade is unresolved.

ArchitecturalScene remains authoritative. This module reuses the exact wall-opening
raster used by the deterministic LEGO shell, then places a one-stud-deep strip of
approved standard plates outside the wall. It never extrapolates an unresolved
facade grade into a slope.
"""
from __future__ import annotations

from dataclasses import dataclass

from brickhouse.building.models import Facade
from brickhouse.geometry import generate_building_geometry
from brickhouse.scene.models import ArchitecturalScene
from brickhouse.scene.topology_projection import project_scene_to_building

from .brick_model import BrickModel, BrickModelPart
from .building_layout import generate_building_brick_shell
from .catalog import create_standard_plate_catalog
from .export import BrickExportFidelityIssue
from .opening_plan_anchors import apply_opening_representation_plan
from .opening_representation_plan import build_opening_representation_plan


_PLATE_SPANS = (
    (8, "PLATE_1X8"),
    (6, "PLATE_1X6"),
    (4, "PLATE_1X4"),
    (3, "PLATE_1X3"),
    (2, "PLATE_1X2"),
    (1, "PLATE_1X1"),
)
_LOCAL_OUTWARD_DEPTH_STUDS = 1
_PLACEMENT_PREFIX = "scene-grade-contact:"


@dataclass(frozen=True)
class LocalGradeContactRaster:
    opening_id: str
    facade: Facade
    wall_x_studs: int
    wall_y_origin_studs: int
    wall_base_z_plates: int
    opening_start_studs: int
    opening_width_studs: int
    opening_bottom_z_plates: int
    sidewalk_x_studs: int
    sidewalk_y_start_studs: int
    sidewalk_top_z_plates: int


def _matching_unresolved_grade_profile(scene: ArchitecturalScene, facade: Facade):
    if scene.terrain is None:
        return None
    for profile in scene.terrain.profiles:
        if profile.facade is not facade:
            continue
        if profile.start_elevation is None or profile.end_elevation is None:
            return profile
    return None


def _zero_clearance_right_openings(scene: ArchitecturalScene):
    main_id = scene.volumes[0].id
    return [
        opening
        for opening in scene.openings
        if (
            opening.volume_id == main_id
            and opening.facade is Facade.RIGHT
            and opening.local_grade_clearance == 0
            and _matching_unresolved_grade_profile(scene, opening.facade) is not None
        )
    ]


def _right_opening_raster(
    scene: ArchitecturalScene,
    opening_id: str,
    *,
    front_width_studs: int,
):
    projection = project_scene_to_building(scene)
    if projection.building is None:
        raise ValueError("local grade contact requires a projectable primary building envelope")

    building = projection.building
    geometry = generate_building_geometry(building)
    shell = generate_building_brick_shell(geometry, front_width_studs)
    plan = build_opening_representation_plan(building, shell)
    applied = apply_opening_representation_plan(building, shell, plan)
    wall = next(record for record in applied.shell.walls if record.facade is Facade.RIGHT)
    try:
        return next(item for item in wall.grid.openings if item.id == opening_id)
    except StopIteration as exc:
        raise ValueError(
            f"right-facade opening {opening_id!r} is absent from the final LEGO wall raster"
        ) from exc


def resolve_local_grade_contact_raster(
    model: BrickModel,
    scene: ArchitecturalScene,
    opening_id: str,
    *,
    front_width_studs: int,
) -> LocalGradeContactRaster:
    """Resolve the local sidewalk anchor from the exact final wall-opening raster."""
    opening = next((item for item in scene.openings if item.id == opening_id), None)
    if opening is None:
        raise ValueError(f"opening {opening_id!r} does not exist")
    if opening.facade is not Facade.RIGHT or opening.local_grade_clearance != 0:
        raise ValueError(
            f"opening {opening_id!r} is not a zero-clearance right-facade grade anchor"
        )
    if opening.volume_id != scene.volumes[0].id:
        raise ValueError("083B local grade contact supports only the primary volume right facade")
    if _matching_unresolved_grade_profile(scene, Facade.RIGHT) is None:
        raise ValueError("right-facade unresolved grade profile is required for local-contact mode")

    raster = _right_opening_raster(
        scene,
        opening_id,
        front_width_studs=front_width_studs,
    )
    wall_parts = [
        part
        for part in model.parts
        if part.component == "wall" and part.facade is Facade.RIGHT
    ]
    if not wall_parts:
        raise ValueError("BrickModel has no right-facade wall raster")

    # Wall-depth enrichment may add inward right-facade layers at smaller X.
    # The exterior wall plane is therefore the maximum X, never an invented offset.
    wall_x = max(part.x_studs for part in wall_parts)
    exterior_wall_parts = [part for part in wall_parts if part.x_studs == wall_x]
    wall_y_origin = min(part.y_studs for part in exterior_wall_parts)
    wall_base_z = min(part.z_plates for part in exterior_wall_parts)
    opening_bottom = wall_base_z + raster.z_bricks * 3
    if opening_bottom < 1:
        raise ValueError(
            f"opening {opening_id!r} bottom is at {opening_bottom} plates; "
            "a one-plate local sidewalk cannot be placed below it without negative Z"
        )

    return LocalGradeContactRaster(
        opening_id=opening_id,
        facade=Facade.RIGHT,
        wall_x_studs=wall_x,
        wall_y_origin_studs=wall_y_origin,
        wall_base_z_plates=wall_base_z,
        opening_start_studs=raster.x_studs,
        opening_width_studs=raster.width_studs,
        opening_bottom_z_plates=opening_bottom,
        sidewalk_x_studs=wall_x + _LOCAL_OUTWARD_DEPTH_STUDS,
        sidewalk_y_start_studs=wall_y_origin + raster.x_studs,
        sidewalk_top_z_plates=opening_bottom,
    )


def _tile_local_span(contact: LocalGradeContactRaster) -> list[BrickModelPart]:
    catalog = create_standard_plate_catalog()
    parts: list[BrickModelPart] = []
    cursor = 0
    remaining = contact.opening_width_studs
    index = 1

    while remaining:
        span, part_id = next((item for item in _PLATE_SPANS if item[0] <= remaining))
        definition = catalog.get(part_id)
        parts.append(
            BrickModelPart(
                placement_id=(
                    f"{_PLACEMENT_PREFIX}{contact.facade.value}:"
                    f"{contact.opening_id}:{index:04d}"
                ),
                part_id=part_id,
                category="terrain",
                component="facade_detail",
                x_studs=contact.sidewalk_x_studs,
                y_studs=contact.sidewalk_y_start_studs + cursor,
                z_plates=contact.sidewalk_top_z_plates - definition.height_plates,
                rotation_quarter_turns=0,
                facade=contact.facade,
                opening_id=contact.opening_id,
                width_studs=definition.width_studs,
                length_studs=definition.length_studs,
                height_plates=definition.height_plates,
            )
        )
        cursor += span
        remaining -= span
        index += 1
    return parts


def augment_brick_model_with_scene_grade_contacts(
    model: BrickModel,
    scene: ArchitecturalScene,
    *,
    front_width_studs: int,
) -> BrickModel:
    """Add only zero-clearance local sidewalk anchors; never extrapolate a slope."""
    openings = _zero_clearance_right_openings(scene)
    if not openings:
        return model

    existing = {
        part.opening_id
        for part in model.parts
        if part.placement_id.startswith(_PLACEMENT_PREFIX)
    }
    additions: list[BrickModelPart] = []
    for opening in openings:
        if opening.id in existing:
            continue
        contact = resolve_local_grade_contact_raster(
            model,
            scene,
            opening.id,
            front_width_studs=front_width_studs,
        )
        additions.extend(_tile_local_span(contact))

    if not additions:
        return model
    return model.model_copy(update={"parts": [*model.parts, *additions]})


def grade_contact_fidelity_issues(
    scene: ArchitecturalScene,
) -> list[BrickExportFidelityIssue]:
    """Report that an observed grade direction is only represented at local anchors."""
    issues: list[BrickExportFidelityIssue] = []
    for opening in _zero_clearance_right_openings(scene):
        profile = _matching_unresolved_grade_profile(scene, opening.facade)
        if profile is None:
            continue
        issues.append(
            BrickExportFidelityIssue(
                code="lego_grade_profile_partial_contact_only",
                severity="warning",
                object_id=opening.id,
                message=(
                    f"Local sidewalk contact is represented exactly at opening {opening.id!r} "
                    "because local_grade_clearance=0. The right-facade grade direction is "
                    "observed as rising along the wall, but its metric endpoints remain "
                    "unresolved; the complete LEGO slope is deliberately omitted until a "
                    "second metric grade anchor is available."
                ),
            )
        )
    return issues
