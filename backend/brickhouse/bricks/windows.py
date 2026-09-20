"""Validated real LEGO window assemblies for BrickHouse.

BrickHouse prefers explicit frame+pane assemblies over masonry drawn inside a
window opening. Window composition is architectural evidence: a larger opening
must not be tiled with several frames merely because that makes it constructible.
Only explicit style/topology evidence or an architectural solution selected from
that evidence may create subdivisions.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field

from brickhouse.building.models import BuildingModel, Facade, OpeningType, WindowStyle
from .building_layout import BuildingBrickShell


@dataclass(frozen=True)
class WindowAssemblyDefinition:
    id: str
    frame_part_id: str
    pane_part_id: str
    width_studs: int
    height_bricks: int


VALIDATED_WINDOW_ASSEMBLIES: tuple[WindowAssemblyDefinition, ...] = (
    WindowAssemblyDefinition("window-1x2x2-60592-60601", "WINDOW_1X2X2_60592", "GLASS_FOR_WINDOW_1X2X2_60601", 2, 2),
    WindowAssemblyDefinition("window-1x2x3-60593-60602", "WINDOW_1X2X3_60593", "GLASS_FOR_WINDOW_1X2X3_60602", 2, 3),
    WindowAssemblyDefinition("window-1x4x3-60594-60603", "WINDOW_1X4X3_60594", "GLASS_FOR_WINDOW_1X4X3_60603", 4, 3),
)


class WindowPartPlacement(BaseModel):
    part_id: str
    category: Literal["window_frame", "window_pane"]
    facade: Facade
    x_studs: int = Field(ge=0)
    y_studs: int = Field(ge=0)
    z_plates: int = Field(ge=0)
    rotation_quarter_turns: Literal[0, 1, 2, 3] = 0
    opening_id: str | None = None
    prototype_recess_studs: int = Field(default=0, ge=0, le=1)


class WindowRepresentationStatus(BaseModel):
    """End-to-end status of one architectural window in the derived LEGO shell."""

    opening_id: str
    facade: Facade
    represented: bool
    representation: Literal["validated_assembly", "joinery_free_glazing", "void_only"]


def _to_global(facade: Facade, local_x: int, opening_width: int, z_bricks: int, width_studs: int, depth_studs: int) -> tuple[int, int, int, Literal[0, 1, 2, 3]]:
    z = z_bricks * 3
    if facade is Facade.FRONT:
        return local_x, 0, z, 1
    if facade is Facade.REAR:
        return width_studs - local_x - opening_width, depth_studs - 1, z, 1
    if facade is Facade.RIGHT:
        return width_studs - 1, local_x, z, 0
    return 0, depth_studs - local_x - opening_width, z, 0


def choose_window_assembly(width_studs: int, height_bricks: int) -> WindowAssemblyDefinition | None:
    return next((assembly for assembly in VALIDATED_WINDOW_ASSEMBLIES if assembly.width_studs == width_studs and assembly.height_bricks == height_bricks), None)


def _assembly(width: int, height: int) -> WindowAssemblyDefinition | None:
    return choose_window_assembly(width, height)


def choose_window_layout(style: WindowStyle, width_studs: int, height_bricks: int) -> tuple[tuple[WindowAssemblyDefinition, int, int], ...]:
    """Fit validated LEGO frames without inventing architectural joinery."""
    if style is WindowStyle.BAY:
        return ()
    if style is WindowStyle.SIMPLE:
        assembly = _assembly(width_studs, height_bricks)
        return ((assembly, 0, 0),) if assembly is not None else ()
    if style is WindowStyle.TRADITIONAL_TALL:
        assembly = _assembly(2, 3) if width_studs == 2 and height_bricks == 3 else None
        return ((assembly, 0, 0),) if assembly is not None else ()
    if style is WindowStyle.PAIRED:
        if width_studs != 4 or height_bricks not in {2, 3}:
            return ()
        assembly = _assembly(2, height_bricks)
        return ((assembly, 0, 0), (assembly, 2, 0)) if assembly is not None else ()
    if style is WindowStyle.FOUR_PANE:
        if width_studs != 4 or height_bricks not in {4, 6}:
            return ()
        pane_height = height_bricks // 2
        assembly = _assembly(2, pane_height)
        if assembly is None:
            return ()
        return ((assembly, 0, 0), (assembly, 2, 0), (assembly, 0, pane_height), (assembly, 2, pane_height))
    return ()


def _selected_layout(composition: str, assembly_id: str, width_studs: int, height_bricks: int) -> tuple[tuple[WindowAssemblyDefinition, int, int], ...]:
    assembly = next((item for item in VALIDATED_WINDOW_ASSEMBLIES if item.id == assembly_id), None)
    if assembly is None:
        raise ValueError(f"unknown selected window assembly {assembly_id!r}")
    if composition == "single":
        layout = ((assembly, 0, 0),)
    elif composition == "paired":
        layout = ((assembly, 0, 0), (assembly, assembly.width_studs, 0))
    elif composition == "four_pane":
        layout = (
            (assembly, 0, 0),
            (assembly, assembly.width_studs, 0),
            (assembly, 0, assembly.height_bricks),
            (assembly, assembly.width_studs, assembly.height_bricks),
        )
    else:
        raise ValueError(f"unsupported selected window composition {composition!r}")
    outer_width = max(x + item.width_studs for item, x, _ in layout)
    outer_height = max(z + item.height_bricks for item, _, z in layout)
    if outer_width != width_studs or outer_height != height_bricks:
        raise ValueError("selected window solution does not match anchored opening raster")
    return layout


def _recess_xy(facade: Facade, x: int, y: int, recess: int) -> tuple[int, int]:
    if facade is Facade.FRONT: return x, y + recess
    if facade is Facade.REAR: return x, y - recess
    if facade is Facade.RIGHT: return x - recess, y
    return x + recess, y


def _emit_pair(placements: list[WindowPartPlacement], assembly: WindowAssemblyDefinition, facade: Facade, local_x: int, z_bricks: int, front: int, depth: int, *, opening_id: str | None = None, recess: int = 0) -> None:
    x, y, z, rotation = _to_global(facade, local_x, assembly.width_studs, z_bricks, front, depth)
    x, y = _recess_xy(facade, x, y, recess)
    placements.extend((
        WindowPartPlacement(part_id=assembly.frame_part_id, category="window_frame", facade=facade, x_studs=x, y_studs=y, z_plates=z, rotation_quarter_turns=rotation, opening_id=opening_id, prototype_recess_studs=recess),
        WindowPartPlacement(part_id=assembly.pane_part_id, category="window_pane", facade=facade, x_studs=x, y_studs=y, z_plates=z, rotation_quarter_turns=rotation, opening_id=opening_id, prototype_recess_studs=recess),
    ))


def _emit_joinery_free_glazing(placements: list[WindowPartPlacement], *, facade: Facade, local_x: int, z_bricks: int, width_studs: int, height_bricks: int, front: int, depth: int, opening_id: str | None = None, recess: int = 0) -> None:
    for dx in range(width_studs):
        for dz in range(height_bricks):
            x, y, z, rotation = _to_global(facade, local_x + dx, 1, z_bricks + dz, front, depth)
            x, y = _recess_xy(facade, x, y, recess)
            placements.append(WindowPartPlacement(part_id="BRICK_1X1", category="window_pane", facade=facade, x_studs=x, y_studs=y, z_plates=z, rotation_quarter_turns=rotation, opening_id=opening_id, prototype_recess_studs=recess))


def generate_window_assemblies_with_status(
    building: BuildingModel,
    shell: BuildingBrickShell,
    *,
    selected_solutions: dict[str, tuple[str, str]] | None = None,
    prototype_recess_studs: int = 0,
) -> tuple[list[WindowPartPlacement], set[str], list[WindowRepresentationStatus]]:
    """Generate windows and report whether every architectural void is represented."""
    openings = {opening.id: opening for opening in building.openings}
    walls = {wall.facade: wall for wall in shell.walls}
    front = walls[Facade.FRONT].grid.width_studs
    depth = walls[Facade.RIGHT].grid.width_studs
    placements: list[WindowPartPlacement] = []
    fitted: set[str] = set()
    statuses: list[WindowRepresentationStatus] = []
    selected = selected_solutions or {}
    if prototype_recess_studs not in {0, 1}:
        raise ValueError("prototype LEGO recess is limited to zero or one stud")

    for facade in (Facade.FRONT, Facade.REAR, Facade.LEFT, Facade.RIGHT):
        for raster in walls[facade].grid.openings:
            opening = openings.get(raster.id)
            if not opening or opening.volume_id != shell.volume_id or opening.type is not OpeningType.WINDOW:
                continue
            selected_solution = selected.get(raster.id)
            if selected_solution is not None:
                composition, assembly_id = selected_solution
                layout = _selected_layout(composition, assembly_id, raster.width_studs, raster.height_bricks)
            else:
                style = opening.window_style or WindowStyle.SIMPLE
                layout = choose_window_layout(style, raster.width_studs, raster.height_bricks)
            if layout:
                for assembly, x_offset, z_offset in layout:
                    _emit_pair(placements, assembly, facade, raster.x_studs + x_offset, raster.z_bricks + z_offset, front, depth, opening_id=raster.id, recess=prototype_recess_studs)
                fitted.add(raster.id)
                statuses.append(WindowRepresentationStatus(opening_id=raster.id, facade=facade, represented=True, representation="validated_assembly"))
                continue
            style = opening.window_style or WindowStyle.SIMPLE
            if style in {WindowStyle.SIMPLE, WindowStyle.TRADITIONAL_TALL}:
                _emit_joinery_free_glazing(placements, facade=facade, local_x=raster.x_studs, z_bricks=raster.z_bricks, width_studs=raster.width_studs, height_bricks=raster.height_bricks, front=front, depth=depth, opening_id=raster.id, recess=prototype_recess_studs)
                fitted.add(raster.id)
                statuses.append(WindowRepresentationStatus(opening_id=raster.id, facade=facade, represented=True, representation="joinery_free_glazing"))
                continue
            statuses.append(WindowRepresentationStatus(opening_id=raster.id, facade=facade, represented=False, representation="void_only"))
    return placements, fitted, statuses


def generate_window_assemblies(
    building: BuildingModel,
    shell: BuildingBrickShell,
    *,
    selected_solutions: dict[str, tuple[str, str]] | None = None,
) -> tuple[list[WindowPartPlacement], set[str]]:
    """Compatibility wrapper around the status-aware architectural generator."""
    placements, fitted, _ = generate_window_assemblies_with_status(
        building, shell, selected_solutions=selected_solutions
    )
    return placements, fitted
