"""Evidence-limited connector model for LEGO 30363 (GUIDED-004 mission 034).

LDraw 30363.dat references s/30363s01.dat. That subpart contains two
stud.dat primitives at local X=-10,+10, Y=0, Z=0, and stud4a.dat
underside primitives. LDraw units: 20 per stud, Y points down.
The *two exposed top studs* are directly evidenced; underside clutch
compatibility is not specified by the mesh and is deliberately UNKNOWN.

Source:
https://sources.debian.org/src/ldraw-parts/1802%2Bds-1/parts/30363.dat
https://sources.debian.org/src/ldraw-parts/1802%2Bds-1/parts/s/30363s01.dat
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal

PART_ID = "BRICK_SLOPED_18_4X2"
LEGO_ID = "30363"
FOOTPRINT_STUDS = (2, 4)
HEIGHT_PLATES = 3
# 30363s01.dat: two exposed stud.dat at X=+-10, Z=0;
# local Z=0 is the high, square end; low end is Z=-70.
TOP_STUDS = ((0, 0), (1, 0))
UNDERSIDE = "GEOMETRY_PRESENT_CLUTCH_UNVERIFIED"
MESH_COLLISION = "NOT_AVAILABLE_AS_WATERTIGHT_TRIANGULATION"

@dataclass(frozen=True)
class Placement:
    x: int
    y: int
    z: int
    rotation: int = 0

def rotate_cell(x: int, y: int, quarter_turns: int) -> tuple[int, int]:
    q = quarter_turns % 4
    if q == 0: return x, y
    if q == 1: return 3-y, x
    if q == 2: return 1-x, 3-y
    return y, 1-x

def top_studs(p: Placement) -> frozenset[tuple[int,int,int]]:
    return frozenset((p.x + dx, p.y + dy, p.z + HEIGHT_PLATES)
                     for x,y in TOP_STUDS
                     for dx,dy in [rotate_cell(x,y,p.rotation)])

def contact_30363_top_to_standard_bottom(slope: Placement, standard_bottom_cells: set[tuple[int,int,int]]) -> Literal["KNOWN_TOP_STUD_CONTACT_BOTTOM_MATING_UNVERIFIED", "NO_CONTACT"]:
    """LDraw proves slope top studs, not the other part's underside clutch."""
    return ("KNOWN_TOP_STUD_CONTACT_BOTTOM_MATING_UNVERIFIED"
            if top_studs(slope) & standard_bottom_cells else "NO_CONTACT")

def contact_standard_top_to_30363_bottom(standard_top_cells: set[tuple[int,int,int]], slope: Placement) -> Literal["UNKNOWN_UNDERSIDE", "NO_CONTACT"]:
    # The exact receiving connector coordinates are not proven by the mesh.
    width, depth = (2,4) if slope.rotation % 2 == 0 else (4,2)
    envelope = {(slope.x+dx,slope.y+dy,slope.z) for dx in range(width) for dy in range(depth)}
    return "UNKNOWN_UNDERSIDE" if envelope & standard_top_cells else "NO_CONTACT"

def contact_adjacent_slopes(a: Placement, b: Placement) -> Literal["UNKNOWN_UNDERSIDE", "NO_CONTACT"]:
    return contact_standard_top_to_30363_bottom(set(top_studs(a)), b)
