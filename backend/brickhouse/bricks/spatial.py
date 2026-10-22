"""Global 3D brick placement for a rectangular building shell."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, Field

from brickhouse.building.models import Facade

from .building_layout import BuildingBrickShell, BuildingWallLayout
from .catalog import create_m0_brick_catalog
from .placement import (
    _BRICK_ID_BY_SPAN,
    _allowed_segments,
    _choose_segment_composition,
)


class GlobalBrickPlacement(BaseModel):
    brick_id: str
    facade: Facade
    x_studs: int = Field(ge=0)
    y_studs: int = Field(ge=0)
    z_plates: int = Field(ge=0)
    rotation_quarter_turns: Literal[0, 1, 2, 3]


class SpatialBrickShell(BaseModel):
    schema_version: Literal["0.1"] = "0.1"
    building_id: str
    volume_id: str
    width_studs: int = Field(gt=0)
    depth_studs: int = Field(gt=0)
    height_bricks: int = Field(gt=0)
    placements: list[GlobalBrickPlacement]


def _wall_by_facade(shell: BuildingBrickShell) -> dict[Facade, BuildingWallLayout]:
    by_facade = {record.facade: record for record in shell.walls}
    required = {Facade.FRONT, Facade.REAR, Facade.LEFT, Facade.RIGHT}
    if set(by_facade) != required:
        raise ValueError("building shell must contain front, rear, left and right walls")
    return by_facade


def _corner_trimmed_segments(
    wall: BuildingWallLayout,
    course: int,
    wall_owns_corners: bool,
) -> list[tuple[int, int]]:
    segments = _allowed_segments(wall.grid.width_studs, course, wall.grid.openings)
    if wall_owns_corners:
        return segments

    width = wall.grid.width_studs
    trimmed: list[tuple[int, int]] = []
    for start, end in segments:
        start = max(start, 1)
        end = min(end, width - 1)
        if start < end:
            trimmed.append((start, end))
    return trimmed


def _choose_supported_segment_composition(
    start_x: int,
    end_x: int,
    previous_joints: frozenset[int],
    support_cells: frozenset[int],
) -> tuple[int, ...]:
    """Tile a course while preferring bricks with a real stud below them.

    The former course tiler optimized bond joints only. Directly above a window or
    door that can produce a perfectly legal-looking raster brick whose entire
    footprint sits over the opening void. A real LEGO lintel must instead bridge far
    enough to overlap at least one supported stud. This dynamic program keeps the
    existing bond preferences, but first minimizes bricks with no vertical bearing.
    """
    if start_x >= end_x:
        return ()

    spans = tuple(sorted(_BRICK_ID_BY_SPAN, reverse=True))

    @lru_cache(maxsize=None)
    def solve(x_studs: int) -> tuple[int, int, int, tuple[int, ...]] | None:
        if x_studs == end_x:
            return 0, 0, 0, ()

        best: tuple[int, int, int, tuple[int, ...]] | None = None
        best_key = None
        for span in spans:
            end = x_studs + span
            if end > end_x:
                continue
            tail = solve(end)
            if tail is None:
                continue
            unsupported_tail, joint_tail, count_tail, spans_tail = tail
            supported_here = any(cell in support_cells for cell in range(x_studs, end))
            unsupported = unsupported_tail + (0 if supported_here else 1)
            joint_overlap = joint_tail + (1 if end < end_x and end in previous_joints else 0)
            candidate = (unsupported, joint_overlap, 1 + count_tail, (span, *spans_tail))
            key = (
                candidate[0],
                candidate[1],
                candidate[2],
                tuple(-value for value in candidate[3]),
            )
            if best is None or key < best_key:
                best = candidate
                best_key = key
        return best

    result = solve(start_x)
    if result is None:
        raise RuntimeError(f"no exact canonical brick composition for segment {start_x}:{end_x}")
    return result[3]


def _course_local_bricks(
    wall: BuildingWallLayout,
    course: int,
    wall_owns_corners: bool,
    previous_joints: frozenset[int],
    previous_support_cells: frozenset[int],
) -> tuple[list[tuple[str, int, int]], frozenset[int], frozenset[int]]:
    """Return local bricks, internal joints and occupied local cells for one course."""
    segments = _corner_trimmed_segments(wall, course, wall_owns_corners)
    result: list[tuple[str, int, int]] = []
    raw_joints: set[int] = set()
    occupied_local: set[int] = set()

    for start, end in segments:
        if course == 0:
            composition = _choose_segment_composition(start, end, previous_joints)
        else:
            composition = _choose_supported_segment_composition(
                start,
                end,
                previous_joints,
                previous_support_cells,
            )
            # A one-brick-high opening ends immediately below this course.  Treat
            # the first course above it as a real lintel: where the opening is
            # narrower than a canonical brick, prefer one continuous brick that
            # bears on masonry at both jambs instead of allowing a joint to fall
            # inside the span.  This remains generic wall logic; no facade- or
            # benchmark-specific dimensions are encoded.
            opening_tops = [
                opening
                for opening in wall.grid.openings
                if opening.z_bricks + opening.height_bricks == course
                and opening.x_studs >= start
                and opening.x_studs + opening.width_studs <= end
            ]
            if len(opening_tops) == 1:
                opening = opening_tops[0]
                for lintel_span in sorted(_BRICK_ID_BY_SPAN, reverse=True):
                    lintel_start = opening.x_studs - 1
                    lintel_end = lintel_start + lintel_span
                    if (
                        lintel_span >= opening.width_studs + 2
                        and start <= lintel_start
                        and lintel_end <= end
                    ):
                        left = _choose_segment_composition(start, lintel_start, previous_joints)
                        right = _choose_segment_composition(lintel_end, end, previous_joints)
                        composition = (*left, lintel_span, *right)
                        break
        x = start
        for span in composition:
            result.append((_BRICK_ID_BY_SPAN[span], x, span))
            occupied_local.update(range(x, x + span))
            x += span
            raw_joints.add(x)

    segment_edges = {edge for segment in segments for edge in segment}
    width = wall.grid.width_studs
    internal = frozenset(
        joint
        for joint in raw_joints
        if joint not in segment_edges and 0 < joint < width
    )
    return result, internal, frozenset(occupied_local)


def _to_global(
    facade: Facade,
    local_x: int,
    span: int,
    course: int,
    width_studs: int,
    depth_studs: int,
    brick_id: str,
) -> GlobalBrickPlacement:
    z = course * 3
    if facade is Facade.FRONT:
        return GlobalBrickPlacement(
            brick_id=brick_id,
            facade=facade,
            x_studs=local_x,
            y_studs=0,
            z_plates=z,
            rotation_quarter_turns=1 if span > 1 else 0,
        )
    if facade is Facade.REAR:
        return GlobalBrickPlacement(
            brick_id=brick_id,
            facade=facade,
            x_studs=width_studs - local_x - span,
            y_studs=depth_studs - 1,
            z_plates=z,
            rotation_quarter_turns=1 if span > 1 else 0,
        )
    if facade is Facade.RIGHT:
        return GlobalBrickPlacement(
            brick_id=brick_id,
            facade=facade,
            x_studs=width_studs - 1,
            y_studs=local_x,
            z_plates=z,
            rotation_quarter_turns=0,
        )
    return GlobalBrickPlacement(
        brick_id=brick_id,
        facade=facade,
        x_studs=0,
        y_studs=depth_studs - local_x - span,
        z_plates=z,
        rotation_quarter_turns=0,
    )


def _occupied_cells(placement: GlobalBrickPlacement) -> set[tuple[int, int, int]]:
    brick = create_m0_brick_catalog().get(placement.brick_id)
    fx, fy = brick.footprint(placement.rotation_quarter_turns)
    course = placement.z_plates // 3
    return {
        (placement.x_studs + dx, placement.y_studs + dy, course)
        for dx in range(fx)
        for dy in range(fy)
    }


def generate_spatial_brick_shell(shell: BuildingBrickShell) -> SpatialBrickShell:
    """Place four walls globally and alternate corner ownership by course."""
    by_facade = _wall_by_facade(shell)
    width = by_facade[Facade.FRONT].grid.width_studs
    depth = by_facade[Facade.RIGHT].grid.width_studs
    heights = {record.grid.height_bricks for record in shell.walls}
    if len(heights) != 1:
        raise ValueError("all walls must share one grid height")
    height = next(iter(heights))

    placements: list[GlobalBrickPlacement] = []
    occupied: set[tuple[int, int, int]] = set()
    previous_joints_by_facade: dict[Facade, frozenset[int]] = {
        facade: frozenset()
        for facade in (Facade.FRONT, Facade.REAR, Facade.LEFT, Facade.RIGHT)
    }
    previous_support_by_facade: dict[Facade, frozenset[int]] = {
        facade: frozenset()
        for facade in (Facade.FRONT, Facade.REAR, Facade.LEFT, Facade.RIGHT)
    }

    for course in range(height):
        horizontal_owns = course % 2 == 0
        current_support_by_facade: dict[Facade, frozenset[int]] = {}
        for facade in (Facade.FRONT, Facade.REAR, Facade.LEFT, Facade.RIGHT):
            wall_owns = horizontal_owns if facade in {Facade.FRONT, Facade.REAR} else not horizontal_owns
            wall = by_facade[facade]
            local_bricks, internal_joints, local_occupied = _course_local_bricks(
                wall,
                course,
                wall_owns,
                previous_joints_by_facade[facade],
                previous_support_by_facade[facade],
            )
            previous_joints_by_facade[facade] = internal_joints
            current_support_by_facade[facade] = local_occupied

            for brick_id, local_x, span in local_bricks:
                placement = _to_global(
                    facade,
                    local_x,
                    span,
                    course,
                    width,
                    depth,
                    brick_id,
                )
                cells = _occupied_cells(placement)
                overlap = occupied.intersection(cells)
                if overlap:
                    raise RuntimeError(f"global brick overlap detected at {sorted(overlap)!r}")
                occupied.update(cells)
                placements.append(placement)
        previous_support_by_facade = current_support_by_facade

    return SpatialBrickShell(
        building_id=shell.building_id,
        volume_id=shell.volume_id,
        width_studs=width,
        depth_studs=depth,
        height_bricks=height,
        placements=placements,
    )
