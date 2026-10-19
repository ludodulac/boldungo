"""Advisory, house-independent roof-ridge evidence for canonical BrickModels.

This is deliberately NOT a stability gate. It compares documented exposed top
studs with ridge-tile footprints, and separately lists *projected* overlaps of
opposing slopes. Neither proves underside engagement, mesh clearance, or load.

Supports arbitrary houses and part counts. Unsupported connector geometries
stay UNKNOWN. Mono-pitch roofs are not incorrectly required to have a ridge.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Callable

from .roof import create_m0_roof_catalog


def _footprint(part, catalog):
    try:
        definition = catalog.get(part.part_id)
    except KeyError:
        return None
    width, depth = definition.width_studs, definition.length_studs
    if part.rotation_quarter_turns % 2:
        width, depth = depth, width
    return frozenset(
        (part.x_studs + dx, part.y_studs + dy)
        for dx in range(width) for dy in range(depth)
    )


def _studs_documented(part):
    """Return known 3D *top stud cells* or None for an unreviewed family."""
    if part.part_id != "BRICK_SLOPED_18_4X2" or part.roof_side not in ("negative", "positive"):
        return None
    # Reuse 060S official LDraw-coordinate conversion. Do not duplicate maths.
    from .lego30363_mechanics_034 import Placement, top_studs

    return top_studs(Placement(
        part.x_studs, part.y_studs, part.z_plates,
        part.rotation_quarter_turns, roof_side=part.roof_side,
    ))


def analyze_roof_ridge_evidence(model, *, stud_provider: Callable | None = None) -> dict:
    """Report nominal evidence across houses; never assign VALID to a bond.

    The optional provider returns canonical (x,y,z) stud cells or None when
    geometry has not been reviewed. This makes additional roof families
    extensible without pretending their connectors are interchangeable.
    """
    catalog = create_m0_roof_catalog()
    provider = stud_provider or _studs_documented
    roof = [p for p in model.parts if p.component == "roof"]
    slopes = [p for p in roof if p.roof_side in ("negative", "positive")]
    ridge = [p for p in roof if p.roof_side == "ridge"]
    mono = [p for p in roof if p.roof_side == "slope"]
    if not roof:
        pattern = "NO_ROOF"
    elif mono and not slopes and not ridge:
        pattern = "MONO_PITCH_NO_RIDGE_EXPECTED"
    elif slopes and not mono:
        pattern = "GABLE_CANDIDATE"
    else:
        pattern = "OTHER_OR_MIXED_ROOF"

    # Only currently evidence-backed part families have known exposed studs.
    by_height = defaultdict(list)
    unknown_by_height = defaultdict(list)
    slope_footprints = {}
    for part in slopes:
        footprint = _footprint(part, catalog)
        slope_footprints[part.placement_id] = footprint
        definition = catalog.get(part.part_id) if footprint is not None else None
        if definition is None:
            # Unknown catalogue height: cannot safely infer contact with ridge.
            unknown_by_height[None].append(part)
            continue
        upper_z = part.z_plates + definition.height_plates
        cells = provider(part)
        if cells is None:
            unknown_by_height[upper_z].append(part)
        else:
            for x, y, z in cells:
                by_height[z].append((part.roof_side, x, y, part.placement_id))

    tiles = []
    for tile in sorted(ridge, key=lambda p: p.placement_id):
        fp = _footprint(tile, catalog)
        if fp is None:
            tiles.append({"ridge_id": tile.placement_id, "status": "UNKNOWN_RIDGE_GEOMETRY",
                          "sides_with_stud_alignment": [], "unknown_sides": ["negative", "positive"]})
            continue
        aligned = defaultdict(set)
        for side, x, y, pid in by_height[tile.z_plates]:
            if (x, y) in fp:
                aligned[side].add(pid)
        uncertain = set()
        for part in unknown_by_height[tile.z_plates] + unknown_by_height[None]:
            pfp = slope_footprints[part.placement_id]
            if pfp is None or pfp & fp:
                uncertain.add(part.roof_side)
        sides = sorted(aligned)
        if len(sides) == 2:
            status = "BOTH_SIDES_STUD_PROJECTION_ONLY"
        elif uncertain - set(sides):
            status = "UNKNOWN_UNREVIEWED_TOP_CONNECTORS"
        elif len(sides) == 1:
            status = "ONE_SIDE_STUD_PROJECTION_ONLY"
        else:
            status = "NO_DOCUMENTED_STUD_ALIGNMENT"
        tiles.append({
            "ridge_id": tile.placement_id,
            "status": status,
            "sides_with_stud_alignment": sides,
            "unknown_sides": sorted(uncertain - set(sides)),
        })

    # This is a projection filter, NOT a 3D collision test.
    neg_by_z = defaultdict(list)
    pos_by_z = defaultdict(list)
    for p in slopes:
        (neg_by_z if p.roof_side == "negative" else pos_by_z)[p.z_plates].append(p)
    candidate_count = 0
    examples = []
    for z in sorted(set(neg_by_z) & set(pos_by_z)):
        for left in neg_by_z[z]:
            f_left = slope_footprints[left.placement_id]
            if f_left is None:
                continue
            for right in pos_by_z[z]:
                f_right = slope_footprints[right.placement_id]
                if f_right is None:
                    continue
                overlap = f_left & f_right
                if not overlap:
                    continue
                candidate_count += 1
                if len(examples) < 5:
                    examples.append({"negative_id": left.placement_id,
                                     "positive_id": right.placement_id,
                                     "common_projected_cells": len(overlap), "z_plates": z})

    counts = dict(Counter(tile["status"] for tile in tiles))
    return {
        "building_id": model.building_id,
        "roof_pattern": pattern,
        "roof_pieces": len(roof),
        "ridge_tiles": len(ridge),
        "slope_tiles": len(slopes),
        "mono_pitch_tiles": len(mono),
        "explicit_roof_supports": sum(p.component == "roof_support" for p in model.parts),
        "ridge_missing_in_gable_candidate": pattern == "GABLE_CANDIDATE" and not ridge,
        "ridge_alignment_counts": counts,
        "ridge_evidence": tiles,
        "opposing_slope_same_level_projection": {
            "candidate_pairs": candidate_count,
            "examples": examples,
            "mesh_intersection_verdict": "NOT_EVALUATED",
        },
        "physical_certification": "NOT_CERTIFIED",
        "scope": "Nominal top-stud projection only: underside, clearances, collisions, assembly sequence, and mechanical strength NOT certified.",
    }
