"""Conservative *candidate* ridge bridges for different LEGO house geometries.

A bridge tile must align with *documented* exposed top-stud cells of both
opposing slopes on its underside plane. This detects missing two-sided ridge
links and proposes an alternative, WITHOUT inserting a brick in the model.

Only straight, orthogonal two-slope ridge runs with documented 30363 exposed
studs are candidate-supported. Other roof geometries remain UNKNOWN. This
does not prove underside clutch, clearance, assembly insertion or strength.
"""
from __future__ import annotations

from collections import Counter, defaultdict

from .roof import create_m0_roof_catalog
from .roof_ridge_diagnostics import _footprint, _studs_documented


def _groups_of_consecutive(numbers):
    """Split a sorted sequence of integer coordinates into contiguous runs."""
    if not numbers:
        return []
    runs, run = [], [numbers[0]]
    for number in numbers[1:]:
        if number != run[-1] + 1:
            runs.append(run)
            run = [number]
        else:
            run.append(number)
    runs.append(run)
    return runs


def propose_ridge_bridges(model, *, stud_provider=None, max_tiles=2000) -> dict:
    """Return non-mutating, geometry-only roof-bridge *proposals*.

    Negative and positive slopes at a common upper-stud plane are grouped
    by the canonical slope rotation: even -> X across ridge, Y along ridge;
    odd -> Y across ridge, X along ridge. This avoids hard-coded house size
    or ridge positions. Distinct ridges at different across-coordinates
    form separate groups.

    Each 2-long candidate tile must match *both sides* at both longitudinal
    columns. No unsupported partial span is ever silently patched.
    """
    if max_tiles < 1:
        raise ValueError("max_tiles must be positive")
    provider = stud_provider or _studs_documented
    catalog = create_m0_roof_catalog()
    roof_parts = [p for p in model.parts if p.component == "roof"]
    slopes = [p for p in roof_parts if p.roof_side in ("negative", "positive")]
    ridges = [p for p in roof_parts if p.roof_side == "ridge"]
    mono = [p for p in roof_parts if p.roof_side == "slope"]
    if not slopes and mono:
        return {
            "building_id": model.building_id, "roof_pattern": "MONO_PITCH",
            "status": "NO_OPPOSING_RIDGE_REQUIRED", "proposed_tiles": [],
            "proposed_count": 0, "replace_ridge_ids": [],
            "physical_certification": "NOT_CERTIFIED",
        }

    # (z, cross-axis, long-coordinate) -> side -> cross-coordinate -> ids
    by_line = defaultdict(lambda: defaultdict(lambda: defaultdict(set)))
    unknown_slopes = []
    for part in slopes:
        cells = provider(part)
        if cells is None:
            unknown_slopes.append(part.placement_id)
            continue
        lateral_axis = "x" if part.rotation_quarter_turns % 2 == 0 else "y"
        for x, y, z in cells:
            cross, along = (x, y) if lateral_axis == "x" else (y, x)
            by_line[(z, lateral_axis, along)][part.roof_side][cross].add(part.placement_id)

    # Paired side studs must be distinct, align on the same stud plane and
    # be reachable by an existing 2-wide ridge tile rotated transversely.
    groups = defaultdict(list)
    unresolved = []
    for (z, axis, along), sides in sorted(by_line.items()):
        negative, positive = sides.get("negative", {}), sides.get("positive", {})
        if not negative or not positive:
            continue  # partial roof courses are not ridge bridge evidence
        if len(negative) != 1 or len(positive) != 1:
            unresolved.append({"z": z, "axis": axis, "along": along,
                               "reason": "MULTIPLE_STUD_LINES_AMBIGUOUS"})
            continue
        neg_cross, pos_cross = next(iter(negative)), next(iter(positive))
        width = abs(neg_cross - pos_cross) + 1
        if width < 2 or width > 4:
            unresolved.append({"z": z, "axis": axis, "along": along,
                               "reason": "NO_SUPPORTED_BRIDGE_WIDTH",
                               "cross_distance_studs": abs(neg_cross - pos_cross)})
            continue
        low = min(neg_cross, pos_cross)
        groups[(z, axis, low, width)].append(along)

    proposed = []
    replaced = set()
    ridge_by_z = defaultdict(list)
    for r in ridges:
        ridge_by_z[r.z_plates].append(r)

    for (z, axis, cross, width), positions in sorted(groups.items()):
        for run in _groups_of_consecutive(sorted(set(positions))):
            # A transverse TILE_2X{width} necessarily spans exactly two
            # longitudinal cells. Odd tails remain unresolved, not bridged.
            for offset in range(0, len(run) - len(run) % 2, 2):
                pair = run[offset:offset + 2]
                if len(proposed) >= max_tiles:
                    unresolved.append({"z": z, "axis": axis, "along": pair[0],
                                       "reason": "MAX_TILES_REACHED"})
                    break
                part_id = f"TILE_2X{width}"
                try:
                    definition = catalog.get(part_id)
                except KeyError:
                    unresolved.append({"z": z, "axis": axis, "along": pair[0],
                                       "reason": "PART_NOT_IN_CATALOG"})
                    continue
                # Axis x: width covers model X after quarter-turn 1, and
                # the tile's 2-stud side follows the long Y direction.
                # Axis y: tile's long side covers model Y without rotation.
                rotation = 1 if axis == "x" else 0
                footprint_x = definition.length_studs if rotation else definition.width_studs
                footprint_y = definition.width_studs if rotation else definition.length_studs
                if (footprint_x, footprint_y) != (
                    (width, 2) if axis == "x" else (2, width)
                ):
                    raise AssertionError("RIDGE_CATALOG_ROTATION_MISMATCH")
                x, y = (cross, pair[0]) if axis == "x" else (pair[0], cross)
                footprint = {(x + dx, y + dy)
                             for dx in range(footprint_x)
                             for dy in range(footprint_y)}
                for r in ridge_by_z[z]:
                    existing_fp = _footprint(r, catalog)
                    if existing_fp is not None and existing_fp & footprint:
                        replaced.add(r.placement_id)
                proposed.append({
                    "part_id": part_id, "category": "ridge_tile",
                    "component": "roof", "roof_side": "ridge",
                    "x_studs": x, "y_studs": y, "z_plates": z,
                    "rotation_quarter_turns": rotation,
                    "nominal_two_sided_stud_alignment": True,
                    "proof": "EXPOSED_STUD_PROJECTION_ONLY",
                })
            if len(run) % 2:
                unresolved.append({"z": z, "axis": axis, "along": run[-1],
                                   "reason": "UNBRIDGED_ODD_LENGTH_TAIL"})

    result_status = (
        "NO_TWO_SIDED_BRIDGE_FOUND" if not proposed
        else "PARTIAL_GEOMETRIC_PROPOSAL" if unresolved or unknown_slopes
        else "GEOMETRIC_PROPOSAL_REQUIRES_PHYSICAL_REVIEW"
    )
    return {
        "building_id": model.building_id,
        "roof_pattern": "TWO_SLOPE_CANDIDATE" if slopes else "NO_TWO_SLOPE_ROOF",
        "status": result_status,
        "proposed_tiles": proposed,
        "proposed_count": len(proposed),
        "replace_ridge_ids": sorted(replaced),
        "net_part_change_if_approved": len(proposed) - len(replaced),
        "unknown_slope_ids": sorted(unknown_slopes)[:25],
        "unknown_slope_count": len(unknown_slopes),
        "unresolved": unresolved[:100],
        "unresolved_count": len(unresolved),
        "existing_ridge_count": len(ridges),
        "model_mutated": False,
        "physical_certification": "NOT_CERTIFIED",
        "limitations": (
            "Exposed studs on both slopes align under proposed transverse "
            "ridge tiles in XY and Z only. Anti-stud clutch, 3-D interference "
            "with all surrounding bricks, assembly direction and mechanical "
            "strength are NOT VERIFIED. Apply no replacements without review."
        ),
    }
