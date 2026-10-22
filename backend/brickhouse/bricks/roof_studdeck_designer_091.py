"""LEGO2-091: whole-house replacement roof on documented standard stud/anti-stud interfaces.

Design decision: 30363 underside cavities do not yet have an evidenced
connector/insertion contract. REPLACE them in a separate experimental
BrickModel rather than promoting hypothetical interfaces. The alternative is
a stepped, interlocking brick deck (rise 3 plates every 3 studs) with
paired, two-layer transverse *tie* strips over isolated interior courses.
Ties make an assembly connector graph, not a load-rated suspension truss.
No N4/N5/N6 proof; do NOT print a certified build instruction or buy list.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from math import atan, degrees
from .brick_model import BrickModel, BrickModelPart
from .catalog import standard_orthogonal_definitions
from .geometry_adapter import CANONICAL_LDRAW_PARTS
from .support_chain import analyze_standard_brick_support_chain

_DEFS = standard_orthogonal_definitions()
_LEVEL = 3
_SLOPE = "BRICK_SLOPED_18_4X2"
_SUPPORTED_TIES = {4, 6, 8}


def _cells(p):
    d = _DEFS[p.part_id]
    w, h = d.footprint(p.rotation_quarter_turns)
    return {(x, y) for x in range(p.x_studs, p.x_studs + w)
            for y in range(p.y_studs, p.y_studs + h)}


def _new(pid, part, x, y, z, rotation=0):
    definition = _DEFS[part]
    kw = dict(placement_id=pid, part_id=part,
              category=definition.category, component="roof_support",
              x_studs=x, y_studs=y, z_plates=z,
              rotation_quarter_turns=rotation)
    if definition.category == "plate":
        kw.update(width_studs=definition.width_studs,
                  length_studs=definition.length_studs,
                  height_plates=definition.height_plates)
    return BrickModelPart(**kw)


def _coord(part, axis):
    return part.x_studs if axis == "x" else part.y_studs


def _location(axis, cross, along):
    return (cross, along) if axis == "x" else (along, cross)


def _entry(pair):
    x, y, z = pair
    return [x, y, z]


def _vertical_connectors(lower, upper):
    """Nominal mating of standard exposed studs to standard underside cells."""
    if lower.part_id not in _DEFS or upper.part_id not in _DEFS:
        return set()
    return {(x, y, upper.z_plates) for x, y in _cells(lower) & _cells(upper)
            if lower.z_plates + _DEFS[lower.part_id].height_plates
            == upper.z_plates}


def _orthogonal_clearance(existing, added):
    """Reject new solids overlapping existing orthogonal masonry or each other.

    Pre-existing decorative overlaps are outside this mission's scope and are
    never re-certified by this constrained new-build screen.
    """
    volume = {}
    for p in added:
        if p.part_id not in _DEFS:
            raise ValueError("NEW_ROOF_PART_NOT_IN_STANDARD_CATALOG")
        d = _DEFS[p.part_id]
        for z in range(p.z_plates, p.z_plates + d.height_plates):
            for x, y in _cells(p):
                k = (x, y, z)
                prev = volume.get(k)
                if prev is not None:
                    raise ValueError(f"NEW_ROOF_BODY_COLLISION:{prev}:{p.placement_id}:{k}")
                volume[k] = p.placement_id
    for p in existing:
        if p.component not in ("wall", "roof_support") or p.part_id not in _DEFS:
            continue
        d = _DEFS[p.part_id]
        for z in range(p.z_plates, p.z_plates + d.height_plates):
            for x, y in _cells(p):
                k = (x, y, z)
                if k in volume:
                    raise ValueError(f"EXISTING_ORTHOGONAL_BODY_COLLISION:{p.placement_id}:{volume[k]}:{k}")


def design_standard_stud_roof_091(source: BrickModel, *, max_roof_parts=2500):
    """Build a complete alternative roof and conservative per-interface manifest.

    The source's 30363 slope body is NEVER used to claim a connector. For a
    two-sided gable, a trimmed 2x2 top negative course and a 1x4 plate seam
    replace an overlapping apex. A gap in two interior tiles can be tied
    ABOVE the roof deck to two genuinely grounded neighbors (4-stud gap
    bounded by supported ends), but this is a tension path, not compression.
    """
    frozen = source.model_dump_json()
    old = [p for p in source.parts if p.component == "roof" and
           p.roof_side in ("negative", "positive")]
    if not old or len(old) > max_roof_parts or any(
        p.part_id != _SLOPE for p in old
    ):
        raise ValueError("UNSUPPORTED_OR_TOO_LARGE_ROOF_FAMILY")
    if any(p.rotation_quarter_turns not in (0, 1) for p in old):
        raise ValueError("ROOF_ROTATION_UNSUPPORTED")
    axes = {"x" if p.rotation_quarter_turns == 0 else "y" for p in old}
    if len(axes) != 1:
        raise ValueError("MIXED_ORIENTATION_REQUIRES_OTHER_MODULE")
    axis = axes.pop()
    along_axis = "y" if axis == "x" else "x"
    old_by_id = {p.placement_id: p for p in old}
    obsolete_caps = [p for p in source.parts
                     if p.component == "roof_support" and
                     p.placement_id.startswith("EXPERIMENT-088-JOINT-")]
    all_removed = {p.placement_id for p in [*old, *obsolete_caps]}
    tops = {s: [p for p in old if p.roof_side == s and
                p.z_plates == max(q.z_plates for q in old if q.roof_side == s)]
            for s in ("negative", "positive") if any(p.roof_side == s for p in old)}
    seams = []
    reduced = {}
    if len(tops) == 2:
        neg, pos = tops["negative"], tops["positive"]
        neg_at = {_coord(p, along_axis): p for p in neg}
        pos_at = {_coord(p, along_axis): p for p in pos}
        if (len(neg_at) != len(neg) or len(pos_at) != len(pos) or
                set(neg_at) != set(pos_at)):
            raise ValueError("INCOMPLETE_TWO_SIDED_RIDGE_ROWS")
        for a, b in ((neg_at[k], pos_at[k]) for k in sorted(neg_at)):
            if (a.z_plates != b.z_plates or
                    _coord(b, axis) != _coord(a, axis) + 1):
                raise ValueError("ROOF_RIDGE_OFF_GRID_FOR_STANDARD_STUD_BRIDGE")
            # 2-wide top on the negative side; 4-wide positive top.
            # Four projected underside plate cells each cover TWO studs from
            # each opposing side, avoiding the previous 30363 body overlap.
            reduced[a.placement_id] = _coord(b, axis) - 2
            seam_cross = _coord(b, axis) - 2
            along = _coord(a, along_axis)
            for offset in (0, 1):
                x, y = _location(axis, seam_cross, along + offset)
                seams.append(_new(f"EXPERIMENT-091-RIDGE-{a.placement_id}-{offset}",
                                  "PLATE_1X4", x, y, a.z_plates + 3,
                                  1 if axis == "x" else 0))
    deck = []
    for original in old:
        if original.placement_id in reduced:
            cross = reduced[original.placement_id]
            along = _coord(original, along_axis)
            x, y = _location(axis, cross, along)
            pid, rot = "BRICK_2X2", 0
        else:
            x, y = original.x_studs, original.y_studs
            pid, rot = "BRICK_2X4", 1 - original.rotation_quarter_turns
        deck.append(_new("EXPERIMENT-091-DECK-" + original.placement_id,
                         pid, x, y, original.z_plates, rot))
    new_by_source = dict(zip((p.placement_id for p in old), deck))
    base = [p for p in source.parts if p.placement_id not in all_removed]
    grounded_wall_nodes = analyze_standard_brick_support_chain(source).nodes
    grounded_wall = {n.placement_id for n in grounded_wall_nodes if n.reaches_ground}
    wall = [p for p in base if p.component == "wall" and
            p.placement_id in grounded_wall and p.part_id in _DEFS]
    ordered = sorted(deck, key=lambda p: (p.z_plates, p.placement_id))

    def propagate(seed):
        reachable = set(seed)
        links = {}
        for p in ordered:
            links[p.placement_id] = {}
            for lower in [*wall, *ordered]:
                if (lower.placement_id == p.placement_id or
                        lower.z_plates >= p.z_plates):
                    continue
                sites = _vertical_connectors(lower, p)
                if sites:
                    links[p.placement_id][lower.placement_id] = sites
            grounded = set().union(*(v for pid, v in links[p.placement_id].items()
                                      if pid in reachable)) if links[p.placement_id] else set()
            if len(grounded) >= 2:
                reachable.add(p.placement_id)
        return reachable, links

    # Construction of links is based on standard studs, not spatial proximity.
    anchored, links = propagate({p.placement_id for p in wall})
    initial_unsupported = [p for p in ordered if p.placement_id not in anchored]
    disconnected = defaultdict(list)
    for p in initial_unsupported:
        key = (p.z_plates, _coord(p, axis), p.rotation_quarter_turns,
               old_by_id[p.placement_id.removeprefix("EXPERIMENT-091-DECK-")].roof_side)
        disconnected[key].append(p)
    tie_lower = []
    tie_upper = []
    tie_designs = []
    blocked = []
    tied_ids = set()
    for key, group in sorted(disconnected.items()):
        # A successful tie at an earlier/lower course can restore the entire
        # upper chain. Never add redundant plates to already supported rows.
        anchored, _ = propagate({p.placement_id for p in wall} | tied_ids)
        if all(p.placement_id in anchored for p in group):
            continue
        z, cross, rotation, side = key
        alongs = sorted(_coord(p, along_axis) for p in group)
        same_course = sorted((p for p in ordered if p.z_plates == z and
                              _coord(p, axis) == cross and
                              old_by_id[p.placement_id.removeprefix("EXPERIMENT-091-DECK-")].roof_side == side),
                             key=lambda p: _coord(p, along_axis))
        all_at = {_coord(p, along_axis): p for p in same_course}
        # Only an uninterrupted set of tiles between two supported anchors.
        preceding = all_at.get(alongs[0] - 2)
        following = all_at.get(alongs[-1] + 2)
        covered = list(range(alongs[0], alongs[-1] + 1, 2))
        span = (alongs[-1] - alongs[0]) + 6
        if (not preceding or not following or
            preceding.placement_id not in anchored or
            following.placement_id not in anchored or
            set(alongs) != set(covered) or
            span not in _SUPPORTED_TIES):
            blocked.append({"roof_ids": [p.placement_id for p in group],
                            "reason": "NO_BOTH_SIDES_GROUNDED_SUPPORT_OR_BRIDGE_TOO_LONG"})
            continue
        # Multiple strips in parallel at two intermediate footprint columns:
        # both anchor at the two surrounding, wall-connected roof bricks.
        tie_start = _coord(preceding, along_axis)
        tie_xsec = [cross + 1, cross + 2]  # not over the next rising course
        proposed = []
        for idx, cross_cell in enumerate(tie_xsec):
            x, y = _location(axis, cross_cell, tie_start)
            lower = _new(f"EXPERIMENT-091-TIE-{z}-{cross}-{tie_start}-{idx}",
                         f"PLATE_1X{span}", x, y, z + 3,
                         0 if axis == "x" else 1)
            x2, y2 = _location(axis, cross_cell, tie_start + 1)
            upper = _new(f"EXPERIMENT-091-TIE-REINFORCE-{z}-{cross}-{tie_start}-{idx}",
                         f"PLATE_1X{span-2}", x2, y2, z + 4,
                         0 if axis == "x" else 1)
            matches = {p.placement_id: _vertical_connectors(p, lower)
                       for p in same_course}
            if (len(matches.get(preceding.placement_id, ())) < 2 or
                    len(matches.get(following.placement_id, ())) < 2 or
                    any(len(matches.get(p.placement_id, ())) < 2 for p in group) or
                    len(_vertical_connectors(lower, upper)) < span - 2):
                proposed = []
                break
            proposed.append((lower, upper, matches))
        if len(proposed) != 2:
            blocked.append({"roof_ids": [p.placement_id for p in group],
                            "reason": "NO_DOCUMENTED_STUD_PAIRS_FOR_TIE"})
            continue
        for lower, upper, _ in proposed:
            tie_lower.append(lower)
            tie_upper.append(upper)
        tied_ids.update(p.placement_id for p in group)
        tie_designs.append({
            "roof_ids": [p.placement_id for p in group],
            "grounded_anchor_ids": [preceding.placement_id, following.placement_id],
            "tie_part_ids": [p.placement_id for couple in proposed for p in couple[:2]],
            "span_studs": span,
            "interface": "STANDARD_STUD_TO_ANTI_STUD_DOCUMENTED",
            "load_mode": "TENSION_AND_BENDING_NOT_RATED",
            "insertion": "PREASSEMBLE_LOCAL_COURSE_WITH_TIE_THEN_ATTACH_AT_BOTH_ENDS",
            "insertion_clearance_confirmed": False,
        })
    new = [*deck, *tie_lower, *tie_upper, *seams]
    _orthogonal_clearance(base, new)
    deck_ids = {p.placement_id for p in deck}
    # The tied roots have a standard connection to a spanning plate; unlike
    # compression to a wall, their hanging/tension capacity is NOT established.
    connected, links = propagate({p.placement_id for p in wall} | tied_ids)
    ties_proven = []
    for tie in tie_lower:
        for part in deck:
            points = _vertical_connectors(part, tie)
            if points:
                ties_proven.append({"lower": part.placement_id,
                                    "upper": tie.placement_id,
                                    "stud_cells": [_entry(c) for c in sorted(points)],
                                    "interface": "STANDARD_STUD_ANTI_STUD"})
    upper_links = []
    for low in tie_lower:
        for high in tie_upper:
            points = _vertical_connectors(low, high)
            if points:
                upper_links.append({"lower": low.placement_id, "upper": high.placement_id,
                                    "stud_cells": [_entry(c) for c in sorted(points)],
                                    "interface": "STANDARD_STUD_ANTI_STUD"})
    ridge_links = []
    for cap in seams:
        for part in deck:
            points = _vertical_connectors(part, cap)
            if points:
                ridge_links.append({"lower": part.placement_id, "upper": cap.placement_id,
                                    "stud_cells": [_entry(c) for c in sorted(points)],
                                    "interface": "STANDARD_STUD_ANTI_STUD"})
    for cap in seams:
        matched = [v for v in ridge_links if v["upper"] == cap.placement_id]
        if len(matched) != 2 or any(len(v["stud_cells"]) != 2 for v in matched):
            raise ValueError("RIVER_RIDGE_BRIDGE_NOT_TWO_SIDED")
    normal_links = [
        {"lower": low, "upper": upper,
         "stud_cells": [_entry(c) for c in sorted(sites)],
         "interface": "STANDARD_STUD_ANTI_STUD"}
        for upper, sources in links.items()
        for low, sites in sources.items()
        if len(sites) >= 2
    ]
    # Count connector cells and pairs distinctly and explicitly.
    all_links = normal_links + ties_proven + upper_links + ridge_links
    if source.model_dump_json() != frozen:
        raise AssertionError("ORIGINAL_090_MODEL_MUTATED")
    candidate = BrickModel.model_validate({
        **source.model_dump(mode="json"),
        "building_id": source.building_id + "-EXPERIMENTAL-STUDDED-ROOF-091",
        "parts": [p.model_dump(mode="json") for p in [*base, *new]]
    })
    assert len(candidate.parts) == len(base) + len(new)
    def bill(parts):
        pairs = Counter((p.part_id, p.semantic_color or "UNSPECIFIED_BY_BRICKMODEL") for p in parts)
        return [{"part_id": part, "ldraw": CANONICAL_LDRAW_PARTS[part].ldraw_id,
                 "color": color, "quantity": n}
                for (part, color), n in sorted(pairs.items())]
    pitch = degrees(atan((3 * 8) / (3 * 20)))
    report = {
        "design": "WHOLE_HOUSE_STANDARD_STUD_STEPPED_ROOF_WITH_TWO_LAYER_TIE",
        "reason": "30363_UNDERSIDE_INSERTION_AND_CLUTCH_NOT_DOCUMENTED",
        "source_parts": len(source.parts), "experiment_parts": len(candidate.parts),
        "replaced_slopes": len(old),
        "removed_prior_caps": len(obsolete_caps),
        "deck_bricks": len(deck), "ridge_plate_count": len(seams),
        "cross_tie_modules": tie_designs, "blocked_tie_attempts": blocked,
        "roof_positions_old_to_new": {
            p.placement_id: new_by_source[p.placement_id].model_dump(mode="json")
            for p in old
        },
        "parts_added": [p.model_dump(mode="json") for p in new],
        "parts_removed": [p.model_dump(mode="json") for p in [*old, *obsolete_caps]],
        "bom_added": bill(new), "bom_removed": bill([*old, *obsolete_caps]),
        "direct_compression_connected_roof_bricks": len(anchored & deck_ids),
        "roof_bricks_tied_only_no_compression_certification": len(tied_ids),
        "roof_bricks_connected_in_standard_stud_graph": len(connected & deck_ids),
        "roof_bricks_not_connected_to_walls": sorted(deck_ids - connected),
        "stud_interface_pairs_documented_type": len(all_links),
        "stud_interface_cells_documented_type": sum(len(x["stud_cells"]) for x in all_links),
        "standard_interfaces": all_links,
        "30363_underside_claims": 0, "geometric_30363_assumptions_promoted": 0,
        "roof_load_capacity_certified": False,
        "tension_plate_assembly_strength_certified": False,
        "whole_house_insertion_certified": False,
        "full_3d_nonorthogonal_collision_screen": "NOT_VERIFIED",
        "orthogonal_body_collision_check": "PASS",
        "structural_connection_scope": "STANDARD_STUD_TUBE_GEOMETRY_WITH_LOAD_LIMIT_UNPROVEN",
        "roof_rise_plates": 3, "roof_course_advance_studs": 3,
        "stepped_deck_pitch_degrees": round(pitch, 5),
        "architectural_reference_pitch_degrees": 22.0,
        "pitch_difference_degrees": round(abs(pitch - 22.0), 5),
        "visual_appearance": "STAIR_STEPPED_NOT_SMOOTH_ROOF_REQUIRES_REVIEW",
        "assembly": {
            "walls": "PRESERVE_090_LOAD_BEARING_WALLS",
            "deck": "INSTALL_GROUNDED_COURSES_FROM_EAVES_UPWARD",
            "interior_tie": "PREASSEMBLE_TWO_UNSUPPORTED_BRICKS_AND_FOUR_STRIP_MODULE_WITH_SUPPORTED_NEIGHBORS",
            "ridge": "ONLY_AFTER_BOTH_GABLE_SIDES_SEATED",
            "stop": "NO_BUILD_RELEASE_WITHOUT_TIE_STIFFNESS_INSERTION_AND_VISUAL_REVIEW",
        },
        "original_mutated": False, "physical_certification": "NOT_CERTIFIED",
        "user_physical_test_requested": False,
    }
    return report, candidate
