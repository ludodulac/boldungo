"""Deterministic facade details that never fake window joinery with wall bricks.

Architectural trim is allowed only outside the glazing void. Observed sills and
decorative surrounds remain separate from frame/pane joinery, and each emitted
placement keeps its architectural role so later LEGO part selection can improve
without changing the evidence model.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from brickhouse.building.models import BuildingModel, Facade, OpeningType
from .building_layout import BuildingBrickShell

TrimRole = Literal["sill", "left_jamb", "right_jamb", "head", "surround_base", "reveal_left", "reveal_right", "reveal_sill", "reveal_head"]
FacadeDetailCategory = Literal["facade_detail", "masonry", "stone"]


class FacadeDetailPlacement(BaseModel):
    part_id: str
    category: FacadeDetailCategory = "facade_detail"
    facade: Facade
    x_studs: int = Field(ge=0)
    y_studs: int = Field(ge=0)
    z_plates: int = Field(ge=0)
    rotation_quarter_turns: Literal[0, 1, 2, 3] = 0
    opening_id: str | None = None
    trim_role: TrimRole | None = None
    semantic_color: str | None = Field(default=None, min_length=1)
    prototype_recess_studs: int = Field(default=0, ge=0, le=1)


_CANONICAL_TRIM_SPANS: tuple[tuple[int, str], ...] = (
    (8, "BRICK_1X8"),
    (6, "BRICK_1X6"),
    (4, "BRICK_1X4"),
    (3, "BRICK_1X3"),
    (2, "BRICK_1X2"),
    (1, "BRICK_1X1"),
)


def _normalized_material(value: str) -> str:
    return "_".join(value.strip().lower().replace("-", "_").split())


def _material_category(value: str | None) -> FacadeDetailCategory:
    """Classify only exact structured material assertions for dedicated fields."""
    if value is None:
        return "facade_detail"

    material = _normalized_material(value)
    explicit_stone = {
        "stone",
        "natural_stone",
        "cut_stone",
        "dressed_stone",
        "masonry_stone",
    }
    explicit_masonry = {
        "masonry",
        "mineral",
        "rendered_masonry",
    }
    if material in explicit_stone:
        return "stone"
    if material in explicit_masonry:
        return "masonry"
    return "facade_detail"


def _surround_category(opening) -> FacadeDetailCategory:
    """Translate only explicit surround material evidence into a LEGO category.

    A descriptor such as ``stone_like`` describes appearance, not geological
    certainty, so it remains the conservative masonry family. Only descriptors
    that explicitly assert stone are classified as stone. Unknown descriptors
    stay generic instead of being guessed from surround color or facade style.
    """
    visual = opening.opening_visual
    if visual is None or visual.surround_material is None:
        return "facade_detail"

    material = _normalized_material(visual.surround_material)
    explicit_stone = {
        "stone",
        "natural_stone",
        "cut_stone",
        "dressed_stone",
        "masonry_stone",
    }
    if material in explicit_stone:
        return "stone"
    if any(token in material for token in ("masonry", "mineral", "stone_like", "rendered")):
        return "masonry"
    return "facade_detail"


def _sill_category(opening) -> FacadeDetailCategory:
    """Translate dedicated sill material evidence without changing sill geometry."""
    visual = opening.opening_visual
    if visual is None:
        return "facade_detail"
    return _material_category(visual.sill)


def _surround_semantic_color(opening) -> str | None:
    """Return explicit observed surround color without mapping it to LEGO IDs."""
    visual = opening.opening_visual
    if visual is None or visual.surround_color is None:
        return None
    value = visual.surround_color.strip()
    return value or None


def _sill_semantic_color(opening) -> str | None:
    """Return only explicit structured sill color evidence."""
    visual = opening.opening_visual
    if visual is None or visual.sill_color is None:
        return None
    value = visual.sill_color.strip()
    return value or None


def _to_global(
    facade: Facade,
    local_x: int,
    course: int,
    width_studs: int,
    depth_studs: int,
) -> tuple[int, int, int]:
    z = course * 3
    if facade is Facade.FRONT:
        return local_x, 0, z
    if facade is Facade.REAR:
        return width_studs - local_x - 1, depth_studs - 1, z
    if facade is Facade.RIGHT:
        return width_studs - 1, local_x, z
    return 0, depth_studs - local_x - 1, z


def _to_global_horizontal_run(
    facade: Facade,
    local_x: int,
    span: int,
    course: int,
    width_studs: int,
    depth_studs: int,
) -> tuple[int, int, int, Literal[0, 1]]:
    """Map one facade-local horizontal run to a canonical 1xN brick anchor.

    The anchor is always the minimum world-grid corner of the brick footprint.
    Rear and left facades reverse their local horizontal axis, so their anchor
    must account for the full span rather than only the first local cell.
    """
    z = course * 3
    if facade is Facade.FRONT:
        return local_x, 0, z, 1
    if facade is Facade.REAR:
        return width_studs - local_x - span, depth_studs - 1, z, 1
    if facade is Facade.RIGHT:
        return width_studs - 1, local_x, z, 0
    return 0, depth_studs - local_x - span, z, 0


def _append_cell(
    placements,
    seen,
    *,
    facade,
    local_x,
    course,
    wall_width,
    wall_height,
    front_width,
    depth,
    opening_id,
    trim_role,
    category: FacadeDetailCategory = "facade_detail",
    semantic_color: str | None = None,
) -> None:
    if not (0 <= local_x < wall_width and 0 <= course < wall_height):
        return
    key = (facade, local_x, course)
    if key in seen:
        return
    seen.add(key)
    x, y, z = _to_global(facade, local_x, course, front_width, depth)
    placements.append(
        FacadeDetailPlacement(
            part_id="BRICK_1X1",
            category=category,
            facade=facade,
            x_studs=x,
            y_studs=y,
            z_plates=z,
            opening_id=opening_id,
            trim_role=trim_role,
            semantic_color=semantic_color,
        )
    )


def _append_horizontal_run(
    placements,
    seen,
    *,
    facade,
    start_local_x,
    end_local_x,
    course,
    wall_width,
    wall_height,
    front_width,
    depth,
    opening_id,
    trim_role,
    category: FacadeDetailCategory = "facade_detail",
    semantic_color: str | None = None,
) -> None:
    """Compact an exact horizontal cell run into longest canonical 1xN bricks."""
    start = max(0, start_local_x)
    end = min(wall_width, end_local_x)
    if start >= end or not (0 <= course < wall_height):
        return

    cursor = start
    while cursor < end:
        remaining = end - cursor
        for span, part_id in _CANONICAL_TRIM_SPANS:
            if span > remaining:
                continue
            cells = [(facade, local_x, course) for local_x in range(cursor, cursor + span)]
            if any(cell in seen for cell in cells):
                span, part_id = 1, "BRICK_1X1"
                cells = [(facade, cursor, course)]
            if cells[0] in seen:
                cursor += 1
                break

            seen.update(cells)
            x, y, z, rotation = _to_global_horizontal_run(
                facade,
                cursor,
                span,
                course,
                front_width,
                depth,
            )
            placements.append(
                FacadeDetailPlacement(
                    part_id=part_id,
                    category=category,
                    facade=facade,
                    x_studs=x,
                    y_studs=y,
                    z_plates=z,
                    rotation_quarter_turns=rotation if span > 1 else 0,
                    opening_id=opening_id,
                    trim_role=trim_role,
                    semantic_color=semantic_color,
                )
            )
            cursor += span
            break


def generate_window_surrounds(
    building: BuildingModel,
    shell: BuildingBrickShell,
    *,
    skip_opening_ids: set[str] | None = None,
) -> list[FacadeDetailPlacement]:
    """Render observed sill/surround masonry strictly outside window voids.

    A decorative surround owns the full ring immediately outside the opening:
    horizontal head/base runs include the two corner cells shared with the jamb
    columns. When a separately observed sill replaces the surround base, the
    sill remains limited to the opening width and its own structured evidence,
    while the surround keeps only the two lower corner cells so its jambs stay
    visually continuous without borrowing sill material/color evidence.

    Horizontal runs use the longest placement-approved canonical 1xN bricks that
    preserve the exact occupied cells. Vertical jambs remain 1x1-per-course
    because the current placement model supports only rotations around the
    vertical axis; using a 1xN brick across courses would invent an unvalidated
    sideways-building technique.
    """
    _ = skip_opening_ids
    openings = {opening.id: opening for opening in building.openings}
    walls = {wall.facade: wall for wall in shell.walls}
    front = walls[Facade.FRONT].grid.width_studs
    depth = walls[Facade.RIGHT].grid.width_studs
    placements: list[FacadeDetailPlacement] = []
    seen: set[tuple[Facade, int, int]] = set()

    def add(facade, raster, local_x, course, role, wall, category="facade_detail", semantic_color=None):
        _append_cell(
            placements,
            seen,
            facade=facade,
            local_x=local_x,
            course=course,
            wall_width=wall.grid.width_studs,
            wall_height=wall.grid.height_bricks,
            front_width=front,
            depth=depth,
            opening_id=raster.id,
            trim_role=role,
            category=category,
            semantic_color=semantic_color,
        )

    def add_run(facade, raster, start, end, course, role, wall, category="facade_detail", semantic_color=None):
        _append_horizontal_run(
            placements,
            seen,
            facade=facade,
            start_local_x=start,
            end_local_x=end,
            course=course,
            wall_width=wall.grid.width_studs,
            wall_height=wall.grid.height_bricks,
            front_width=front,
            depth=depth,
            opening_id=raster.id,
            trim_role=role,
            category=category,
            semantic_color=semantic_color,
        )

    for facade in (Facade.FRONT, Facade.REAR, Facade.LEFT, Facade.RIGHT):
        wall = walls[facade]
        for raster in wall.grid.openings:
            opening = openings.get(raster.id)
            if not opening or opening.type is not OpeningType.WINDOW:
                continue
            if not opening.has_sill and not opening.has_decorative_surround:
                continue
            left = raster.x_studs - 1
            right = raster.x_studs + raster.width_studs
            bottom = raster.z_bricks - 1
            top = raster.z_bricks + raster.height_bricks
            surround_category = _surround_category(opening)
            surround_color = _surround_semantic_color(opening)
            sill_category = _sill_category(opening)
            sill_color = _sill_semantic_color(opening)
            if opening.has_decorative_surround:
                add_run(
                    facade,
                    raster,
                    left,
                    right + 1,
                    top,
                    "head",
                    wall,
                    surround_category,
                    surround_color,
                )
                if not opening.has_sill:
                    add_run(
                        facade,
                        raster,
                        left,
                        right + 1,
                        bottom,
                        "surround_base",
                        wall,
                        surround_category,
                        surround_color,
                    )
                for course in range(raster.z_bricks, raster.z_bricks + raster.height_bricks):
                    add(facade, raster, left, course, "left_jamb", wall, surround_category, surround_color)
                    add(facade, raster, right, course, "right_jamb", wall, surround_category, surround_color)
                if opening.has_sill:
                    add(facade, raster, left, bottom, "left_jamb", wall, surround_category, surround_color)
                    add(facade, raster, right, bottom, "right_jamb", wall, surround_category, surround_color)
            if opening.has_sill:
                add_run(
                    facade,
                    raster,
                    raster.x_studs,
                    raster.x_studs + raster.width_studs,
                    bottom,
                    "sill",
                    wall,
                    sill_category,
                    sill_color,
                )
    return placements


def generate_prototype_window_reveals(building: BuildingModel, shell: BuildingBrickShell, *, recess_studs: int = 1) -> list[FacadeDetailPlacement]:
    """One-stud LEGO representation prototype; never an architectural metric claim."""
    if recess_studs != 1:
        raise ValueError("prototype reveal depth is exactly one LEGO stud")
    walls = {wall.facade: wall for wall in shell.walls}
    front = walls[Facade.FRONT].grid.width_studs
    depth = walls[Facade.RIGHT].grid.width_studs
    openings = {opening.id: opening for opening in building.openings}
    out = []
    def add(facade, local_x, course, role, opening_id):
        x, y, z = _to_global(facade, local_x, course, front, depth)
        rotation = 0 if facade in {Facade.FRONT, Facade.REAR} else 1
        if facade is Facade.REAR: y -= 1
        if facade is Facade.RIGHT: x -= 1
        out.append(FacadeDetailPlacement(part_id="BRICK_1X2", category="facade_detail", facade=facade, x_studs=x, y_studs=y, z_plates=z, rotation_quarter_turns=rotation, opening_id=opening_id, trim_role=role, prototype_recess_studs=1))
    for facade, wall in walls.items():
        for r in wall.grid.openings:
            o = openings.get(r.id)
            if not o or o.type is not OpeningType.WINDOW: continue
            for course in range(r.z_bricks, r.z_bricks + r.height_bricks):
                add(facade, r.x_studs, course, "reveal_left", r.id)
                add(facade, r.x_studs + r.width_studs - 1, course, "reveal_right", r.id)
            for x in range(r.x_studs, r.x_studs + r.width_studs):
                add(facade, x, r.z_bricks, "reveal_sill", r.id)
                add(facade, x, r.z_bricks + r.height_bricks - 1, "reveal_head", r.id)
    return out
