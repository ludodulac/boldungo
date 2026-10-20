"""LEGO2-073: source-backed nominal interface for LEGO 3002 below 26603.

The official LDraw geometry contains six 3002 top studs (s/3002s01.dat)
and two underside open tubes in 26603 (s/26603s01.dat, stug4-1x2.dat).
This is a geometry-only SCREEN, not a physical assembly certification.

See docs/lego2-073-3002-26603-interface.md for the exact source geometry.
Do not use this diagnostic to promote a tile to an approved connector.
"""
from __future__ import annotations

from math import hypot

from .catalog import standard_orthogonal_definitions
from .connectors import validate_connection
from .geometry_adapter import CANONICAL_LDRAW_PARTS
from .roof import create_m0_roof_catalog
from .roof_ridge_diagnostics import _footprint

# Official LDraw stud.dat diameter=12 LDU, stud4.dat tube OD=16 LDU.
_STUD_RADIUS_LDU = 6
_TUBE_OUTER_RADIUS_LDU = 8
_LDU_PER_STUD = 20


def inspect_3002_26603_upper_interface(head, cover) -> dict:
    """Review the exact 2x3 stud/tube layout at a proposed head-to-tile plane.

    The *ordinary* validate_connection intentionally knows no TILE_2X3
    underside. A geometry match is NOT returned as VALID and says nothing
    about clutch strength, insertion, loads, or surrounding roof collisions.
    """
    raw = validate_connection(head, cover)
    result = {
        "head_id": head.placement_id,
        "cover_id": cover.placement_id,
        "status": "UNKNOWN_UNREVIEWED_PART_FAMILY",
        "orthogonal_connector_gate": raw.status,
        "upper_clutch": "UNKNOWN_NOT_PHYSICALLY_VALIDATED",
        "insertion_path": "UNKNOWN_NOT_TESTED",
        "mechanical_strength": "UNKNOWN_NOT_MEASURED",
        "physical_certification": "NOT_CERTIFIED",
        "geometry_sources": ["3002.dat", "s/3002s01.dat", "26603.dat",
                             "s/26603s01.dat", "stug4-1x2.dat", "stud4.dat"],
    }
    if (head.part_id, cover.part_id) != ("BRICK_2X3", "TILE_2X3"):
        return result
    if (CANONICAL_LDRAW_PARTS[head.part_id].ldraw_id != "3002"
            or CANONICAL_LDRAW_PARTS[cover.part_id].ldraw_id != "26603"):
        return result
    if head.rotation_quarter_turns != cover.rotation_quarter_turns:
        result["status"] = "UNKNOWN_UNREVIEWED_RELATIVE_ROTATION"
        return result
    if head.z_plates + 3 != cover.z_plates:
        result["status"] = "REJECTED_UNMATCHED_VERTICAL_CONNECTOR_PLANE"
        return result

    # Reuse the catalog; do NOT derive bounds from the 2x3 name or from
    # a nominal tile-to-brick contact alone.
    definition = standard_orthogonal_definitions()[head.part_id]
    w, d = definition.footprint(head.rotation_quarter_turns)
    top_studs = {(head.x_studs + x, head.y_studs + y)
                 for x in range(w) for y in range(d)}
    cover_fp = _footprint(cover, create_m0_roof_catalog())
    if top_studs != cover_fp:
        result["status"] = "REJECTED_UNMATCHED_2X3_FOOTPRINT"
        return result

    # Official 26603s01: two stud4 open tubes at local X +/-10 LDU,
    # local Z=0. Standard adapter maps local X to model longitudinal axis;
    # the tile's two transverse rows span the same footprint as 3002.
    # Tube centers in canonical stud coordinates are integer boundaries
    # surrounded by four top-stud centers, not 6 independent tube joints.
    if cover.rotation_quarter_turns % 2:
        tubes = [(cover.x_studs + u, cover.y_studs + 1)
                 for u in (1, 2)]
    else:
        tubes = [(cover.x_studs + 1, cover.y_studs + u)
                 for u in (1, 2)]
    surrounding = []
    for tx, ty in tubes:
        corners = {(tx + dx, ty + dy)
                   for dx in (-1, 0) for dy in (-1, 0)}
        if not corners <= top_studs:
            result["status"] = "REJECTED_TUBE_WITHOUT_FOUR_SURROUNDING_STUDS"
            return result
        surrounding.append(sorted(corners))

    # Each nearest stud centre sits diagonally 10 LDU from each tube axis
    # on BOTH orthogonal axes. Nominal outer-surface clearance > 0.
    distance = hypot(_LDU_PER_STUD / 2, _LDU_PER_STUD / 2)
    nearest_clearance = distance - _STUD_RADIUS_LDU - _TUBE_OUTER_RADIUS_LDU
    if nearest_clearance < -1e-7:
        result["status"] = "REJECTED_NOMINAL_TUBE_STUD_OVERLAP"
        return result
    result.update({
        "status": "NOMINAL_LDRAW_STUD_AND_TUBE_LAYOUT_ONLY",
        "stud_plane_plates": cover.z_plates,
        "six_head_stud_cells": [list(v) for v in sorted(top_studs)],
        "two_underside_tube_axes_studs": [list(v) for v in tubes],
        "tube_surrounding_stud_cells": [
            [list(v) for v in cells] for cells in surrounding
        ],
        "tube_outer_stud_clearance_ldu": round(nearest_clearance, 6),
        "six_studs_under_tile_footprint": True,
        "top_stud_to_bottom_cavity": "NOMINAL_GEOMETRY_ONLY",
        "perimeter_clutch_strength": "UNKNOWN_NOT_MEASURED",
        "limitations": (
            "The 26603 has an underside rim and two tubes between six 3002 "
            "studs. This is a *modeled* alignment and partial surface-gap "
            "check, not a connector VALID verdict. The tile has NO top studs; "
            "it cannot automatically join the two sloped roof sides ABOVE. "
            "Complete LDraw interference, vertical insertion, real manufacturing "
            "fit and load transfer remain unverified."
        ),
    })
    return result
