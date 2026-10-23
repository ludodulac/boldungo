"""Evidence-limited connector model for LEGO 30363 (GUIDED-004 mission 034).

060S: exposed top-stud locations use the EXISTING canonical slope placement
transform, not the historical unrotated 2x4 grid. Official LDraw 30363.dat
includes s/30363s01.dat with studs at local (+/-10, 0, 0) LDU.

The exact LDraw X/Z bbox is [-20,+20] x [-70,+10], with max local Y=24
and stud tops at Y=-4. This reference AABB is used ONLY to anchor the
existing geometry_adapter._slope_transform. It is NOT a substitute solid mesh,
a collision check, or an underside clutch certificate.

Sources:
https://library.ldraw.org/library/official/parts/30363.dat
https://github.com/pybricks/ldraw/blob/master/parts/s/30363s01.dat
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from lego_geometry_engine import AABB, PartDefinition

from .brick_model import BrickModelPart
from .geometry_adapter import (
    CANONICAL_LDRAW_PARTS,
    LDU_PER_PLATE,
    LDU_PER_STUD,
    _slope_transform,
)

PART_ID = "BRICK_SLOPED_18_4X2"
LEGO_ID = "30363"
FOOTPRINT_STUDS = (4, 2)  # canonical rotation=0, X by Y
HEIGHT_PLATES = 3
TOP_STUDS_LDRAW = ((-10.0, 0.0, 0.0), (10.0, 0.0, 0.0))
UNDERSIDE = "GEOMETRY_PRESENT_CLUTCH_UNVERIFIED"
MESH_COLLISION = "NOT_AVAILABLE_AS_WATERTIGHT_TRIANGULATION"

# Verified 30363.dat / s/30363s01.dat extent; bbox-only reference, not
# a fabricated connector or watertight mesh. _slope_transform owns the
# rotation, roof-side polarity, origin anchoring, and translation rules.
_30363_BBOX_ONLY = PartDefinition(
    "30363.dat",
    (),
    AABB((-20.0, -4.0, -70.0), (20.0, 24.0, 10.0)),
    "LDraw 30363 reference bbox for existing slope placement transform",
)


@dataclass(frozen=True)
class Placement:
    x: int
    y: int
    z: int
    rotation: int = 0
    roof_side: Literal["negative", "positive"] | None = None


def rotate_cell(x: int, y: int, quarter_turns: int) -> tuple[int, int]:
    """Legacy 2x4 LOCAL grid rotation; NOT a 30363-to-house transform.

    Retained for callers that explicitly use this historical helper.
    Connector positions must instead be obtained using top_studs().
    """
    q = quarter_turns % 4
    if q == 0: return x, y
    if q == 1: return 3-y, x
    if q == 2: return 1-x, 3-y
    return y, 1-x


def _slope_part(p: Placement) -> BrickModelPart:
    if p.roof_side not in ("negative", "positive"):
        raise ValueError("30363_ROOF_SIDE_REQUIRED_FOR_TOP_STUD_TRANSFORM")
    return BrickModelPart(
        placement_id="30363-target",
        part_id=PART_ID,
        category="roof_tile",
        component="roof",
        roof_side=p.roof_side,
        x_studs=p.x,
        y_studs=p.y,
        z_plates=p.z,
        rotation_quarter_turns=p.rotation,
    )


def top_studs(p: Placement) -> frozenset[tuple[int, int, int]]:
    """True LDraw exposed-stud CELLS and top-plane z in canonical coordinates.

    The existing geometry adapter transforms the LDraw stud-base centres.
    A whole stud cell has its centre at (index+0.5)*20 LDU. Reject rather
    than round away a non-grid-aligned result.
    """
    part = _slope_part(p)
    transform = _slope_transform(part, CANONICAL_LDRAW_PARTS[PART_ID], _30363_BBOX_ONLY)
    cells = set()
    for local in TOP_STUDS_LDRAW:
        gx, gy, gz = transform.point(local)
        grid = (gx / LDU_PER_STUD - 0.5,
                gz / LDU_PER_STUD - 0.5,
                -gy / LDU_PER_PLATE)
        integer_cell = tuple(round(value) for value in grid)
        if any(abs(value - rounded) > 1e-6 for value, rounded in zip(grid, integer_cell)):
            raise ValueError("30363_TOP_STUD_OFF_CANONICAL_GRID")
        cells.add(integer_cell)
    return frozenset(cells)


def contact_30363_top_to_standard_bottom(
    slope: Placement, standard_bottom_cells: set[tuple[int, int, int]]
) -> Literal["KNOWN_TOP_STUD_CONTACT_BOTTOM_MATING_UNVERIFIED", "NO_CONTACT"]:
    """LDraw proves slope top studs, not the other part's underside clutch."""
    return ("KNOWN_TOP_STUD_CONTACT_BOTTOM_MATING_UNVERIFIED"
            if top_studs(slope) & standard_bottom_cells else "NO_CONTACT")


def contact_standard_top_to_30363_bottom(
    standard_top_cells: set[tuple[int, int, int]], slope: Placement
) -> Literal["UNKNOWN_UNDERSIDE", "NO_CONTACT"]:
    # Existing conservative rule: bbox screening ONLY, never VALID.
    # The historical (2,4) zero-turn bbox was inconsistent with BrickModel.
    width, depth = (
        FOOTPRINT_STUDS
        if slope.rotation % 2 == 0 else FOOTPRINT_STUDS[::-1]
    )
    envelope = {
        (slope.x + dx, slope.y + dy, slope.z)
        for dx in range(width) for dy in range(depth)
    }
    return "UNKNOWN_UNDERSIDE" if envelope & standard_top_cells else "NO_CONTACT"


def contact_adjacent_slopes(
    a: Placement, b: Placement
) -> Literal["UNKNOWN_UNDERSIDE", "NO_CONTACT"]:
    return contact_standard_top_to_30363_bottom(set(top_studs(a)), b)
