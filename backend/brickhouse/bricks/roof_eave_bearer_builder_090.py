"""LEGO2-090: design catalogue-based, interlocked eave-bearing wall courses.

This is a *construction proposal*, not a permission to assemble a roof.
The beam is a standard 2x4 brick that replaces the conflicting ends of two
orthogonal wall courses. Existing wall pieces are retiled rather than overlapped.
The root 30363 engagement remains an explicitly UNVERIFIED cavity proposal.
No changes to the canonical model or the preceding 088 experiment.
"""
from __future__ import annotations

from collections import Counter
from .brick_model import BrickModel, BrickModelPart
from .catalog import standard_orthogonal_definitions
from .roof_connectivity_compiler_089 import (
    compile_roof_connections_089, _underface_30363_stud_candidate,
)
from .support_chain import analyze_standard_brick_support_chain

_DEFS = standard_orthogonal_definitions()
_SPANS = (8, 6, 4, 3, 2, 1)


def _cells(part):
    d = _DEFS[part.part_id]
    w, h = d.footprint(part.rotation_quarter_turns)
    return {(x, y) for x in range(part.x_studs, part.x_studs + w)
            for y in range(part.y_studs, part.y_studs + h)}


def _retile(original, excluded, tag):
    """Tile the remainder of a single 1-wide wall course without new geometry."""
    cells = _cells(original) - excluded
    if not cells:
        return []
    if original.part_id not in _DEFS:
        raise ValueError("UNKNOWN_ORIGINAL_WALL_PART")
    if len({x for x, _ in cells}) == 1:
        axis = "y"
        fixed = next(iter(cells))[0]
        points = sorted(y for _, y in cells)
        rot = 0
    elif len({y for _, y in cells}) == 1:
        axis = "x"
        fixed = next(iter(cells))[1]
        points = sorted(x for x, _ in cells)
        rot = 1
    else:
        raise ValueError("UNSUPPORTED_WALL_RETILING_GEOMETRY")
    pieces = []
    remaining = set(points)
    serial = 0
    while remaining:
        first = min(remaining)
        run = 0
        while first + run in remaining:
            run += 1
        span = next(v for v in _SPANS if v <= run)
        part_id = f"BRICK_1X{span}"
        if part_id not in _DEFS:
            raise AssertionError(part_id)
        part = BrickModelPart(
            placement_id=f"EXPERIMENT-090-REPLACE-{tag}-{serial}",
            part_id=part_id, category="brick", component="wall",
            x_studs=first if axis == "x" else fixed,
            y_studs=fixed if axis == "x" else first,
            z_plates=original.z_plates, rotation_quarter_turns=rot,
            facade=original.facade,
        )
        assert _cells(part) <= cells
        pieces.append(part)
        remaining -= {first + i for i in range(span)}
        serial += 1
    assert set().union(*(_cells(p) for p in pieces)) == cells
    return pieces


def _beam_for_end_root(root, all_roofs):
    """Return a standard 2x4 cross-course for an outer eave corner.

    Other roof configurations are denied rather than heuristically extending
    a cantilever through unsupported internal space.
    """
    if root.part_id != "BRICK_SLOPED_18_4X2" or root.rotation_quarter_turns % 2:
        return None
    if root.z_plates != min(p.z_plates for p in all_roofs):
        return None
    ymin = min(p.y_studs for p in all_roofs)
    ymax = max(p.y_studs for p in all_roofs)
    if root.y_studs == ymin:
        y = root.y_studs
    elif root.y_studs == ymax:
        y = root.y_studs - 2
    else:
        return None
    if root.roof_side == "negative":
        x = root.x_studs + 2
    elif root.roof_side == "positive":
        x = root.x_studs - 1
    else:
        return None
    if min(x, y) < 0 or root.z_plates < 3:
        return None
    return BrickModelPart(
        placement_id=f"EXPERIMENT-090-EAVE-{root.placement_id}",
        part_id="BRICK_2X4", category="brick", component="wall",
        x_studs=x, y_studs=y, z_plates=root.z_plates - 3,
        rotation_quarter_turns=0,
        facade="front" if root.y_studs == ymin else "rear",
    )


def design_roof_eave_bearers_090(source: BrickModel):
    """Make a whole-house eave-bracket variant, never mutate source.

    Each candidate must connect to >=3 *distinct* lower stud cells and at
    least two existing grounded wall placements. It must replace EXACTLY the
    intersecting single-width top-wall pieces, retaining their other cells.
    This rule works by roof and wall coordinates, not a fixed house ID.
    """
    before_bytes = source.model_dump_json()
    report = compile_roof_connections_089(source)
    unresolved = {r["placement_id"]: r for r in report["nominal_roof_stud_rows"]
                  if r["status"] == "NO_DOCUMENTED_LOWER_STUD_SITE"}
    roof_parts = [p for p in source.parts if p.component == "roof"
                  and p.roof_side in ("negative", "positive")]
    indexed = {p.placement_id: p for p in source.parts}
    wall_report = analyze_standard_brick_support_chain(source)
    grounded = {n.placement_id for n in wall_report.nodes if n.reaches_ground
                and indexed[n.placement_id].component == "wall"}
    accepted = []
    blockers = []
    removed = set()
    additions = []
    for pid in sorted(unresolved):
        root = indexed[pid]
        beam = _beam_for_end_root(root, roof_parts)
        if beam is None:
            blockers.append({"roof_id": pid, "reason": "REQUIRES_INTERNAL_FRAME_NOT_EAVE_BRACKET"})
            continue
        beam_xy = _cells(beam)
        # The two verified cells must be in the footprint of the new piece.
        sites = [(x, y, root.z_plates) for x, y in sorted(beam_xy)
                 if _underface_30363_stud_candidate(root, x, y, root.z_plates)]
        if len(sites) < 2:
            blockers.append({"roof_id": pid, "reason": "UNSUPPORTED_30363_CAVITY_SITES"})
            continue
        conflicts = [p for p in source.parts if p.component == "wall"
                     and p.category in ("brick", "plate")
                     and p.part_id in _DEFS and
                     beam.z_plates < p.z_plates + _DEFS[p.part_id].height_plates
                     and p.z_plates < beam.z_plates + 3
                     and _cells(p) & beam_xy]
        if (not conflicts or any(p.z_plates != beam.z_plates or
                                 p.category != "brick" or
                                 min(_DEFS[p.part_id].width_studs,
                                     _DEFS[p.part_id].length_studs) != 1
                                 for p in conflicts)
                or any(p.placement_id in removed for p in conflicts)):
            blockers.append({"roof_id": pid, "reason": "UNSAFE_EXISTING_WALL_OVERLAP"})
            continue
        # Reject all orthogonal non-wall collisions in this volume.
        others = [p.placement_id for p in source.parts if
                  p.component != "wall" and p.part_id in _DEFS
                  and p.category in ("brick", "plate")
                  and beam.z_plates < p.z_plates + _DEFS[p.part_id].height_plates
                  and p.z_plates < beam.z_plates + 3
                  and _cells(p) & beam_xy]
        if others:
            blockers.append({"roof_id": pid, "reason": "NON_WALL_ORTHOGONAL_COLLISION",
                             "conflicts": others})
            continue
        # Only load-bearing walls below, at the beam underside datum.
        supports = [(p.placement_id, pos)
                    for p in source.parts if p.placement_id in grounded
                    and p.part_id in _DEFS and p.category in ("brick", "plate")
                    and p.z_plates + _DEFS[p.part_id].height_plates == beam.z_plates
                    for pos in sorted(_cells(p) & beam_xy)]
        support_cells = {pos for _, pos in supports}
        support_ids = {v for v, _ in supports}
        if len(support_cells) < 3 or len(support_ids) < 2:
            blockers.append({"roof_id": pid, "reason": "INSUFFICIENT_INTERLOCKED_WALL_ANCHORS",
                             "lower_stud_count": len(support_cells),
                             "lower_part_count": len(support_ids)})
            continue
        cut = []
        for old in conflicts:
            try:
                cut.extend(_retile(old, beam_xy, old.placement_id))
            except ValueError:
                cut = None
                break
        if cut is None:
            blockers.append({"roof_id": pid, "reason": "WALL_RETILING_FAILED"})
            continue
        new = [beam] + cut
        if len({n.placement_id for n in new}) != len(new):
            raise AssertionError("DUPLICATE_EXPERIMENTAL_IDS")
        removed.update(p.placement_id for p in conflicts)
        additions.extend(new)
        accepted.append({
            "roof_id": pid, "beam_id": beam.placement_id,
            "technique": "CROSS-COURSE_2X4_BRICK_INTERLOCKED_EAVE",
            "beam": beam.model_dump(mode="json"),
            "replaced_wall_ids": sorted(p.placement_id for p in conflicts),
            "retiled_wall_ids": sorted(p.placement_id for p in cut),
            "grounded_lower_ids": sorted(support_ids),
            "grounded_lower_stud_cells": [list(v) for v in sorted(support_cells)],
            "proposed_roof_cavity_cells": [list(v) for v in sites],
            "wall_to_beam_interface": "STANDARD_STUD_TO_ANTI_STUD_CAVITY_DOCUMENTED",
            "beam_to_30363_interface": "GEOMETRY_ONLY_NOT_CLUTCH_CERTIFIED",
            "insertion_plan": "WALL_LOWER_COURSE_THEN_BRACKET_DOWNWARD_THEN_ROOF",
            "roof_insertion_verified": False,
            "load_capacity_verified": False,
        })
    candidate_parts = [p.model_dump(mode="json") for p in source.parts
                       if p.placement_id not in removed]
    candidate_parts += [p.model_dump(mode="json") for p in additions]
    candidate = BrickModel.model_validate({
        **source.model_dump(mode="json"),
        "building_id": source.building_id + "-EXPERIMENTAL-090",
        "parts": candidate_parts,
    })
    if source.model_dump_json() != before_bytes:
        raise AssertionError("SOURCE_MUTATED")
    # These aren't physically proven, so retain the existing nominal compiler's
    # limited meaning. No recategorization as VALID/LOAD_TESTED.
    after = compile_roof_connections_089(candidate)
    corrected = [row["roof_id"] for row in accepted
                 if next(r["status"] for r in after["nominal_roof_stud_rows"]
                         if r["placement_id"] == row["roof_id"])
                 == "NOMINAL_TWO_STUD_PATH_TO_WALL_ONLY"]
    for row in accepted:
        if row["roof_id"] not in corrected:
            raise AssertionError("DESIGNED_BRACKET_FAILED_089_RECHECK")
    before_rows = {r["placement_id"]: r for r in report["nominal_roof_stud_rows"]}
    after_rows = {r["placement_id"]: r for r in after["nominal_roof_stud_rows"]}
    newly_grounded = sorted(pid for pid, old in before_rows.items()
        if old["status"] != "NOMINAL_TWO_STUD_PATH_TO_WALL_ONLY"
        and after_rows[pid]["status"] == "NOMINAL_TWO_STUD_PATH_TO_WALL_ONLY")
    newly_connected_details = [{
        "roof_id": pid,
        "supporter_ids": after_rows[pid]["grounded_lower_ids"],
        "grounded_stud_sites": after_rows[pid]["grounded_site_count"],
        "evidence_types": sorted(after_rows[pid]["source_evidence"]),
        "roof_interface_still_mechanically_unverified": True,
    } for pid in newly_grounded]
    remaining = [{"roof_id": pid, "status": r["status"],
                  "candidate_lower_ids": r["candidate_lower_ids"]}
                 for pid, r in sorted(after_rows.items())
                 if r["status"] != "NOMINAL_TWO_STUD_PATH_TO_WALL_ONLY"]
    before_caps = {r["placement_id"]: r["status"] for r in report["ridge_caps"]}
    new_caps = {r["placement_id"]: r["status"] for r in after["ridge_caps"]}
    caps_newly_grounded = sorted(pid for pid in new_caps
        if new_caps[pid] == "NOMINAL_TWO_SIDED_BRIDGE_TO_GROUNDED_SLOPES"
        and before_caps.get(pid) != new_caps[pid])
    caps_blocked = [r for r in after["ridge_caps"]
                    if r["status"] != "NOMINAL_TWO_SIDED_BRIDGE_TO_GROUNDED_SLOPES"]
    provisional_order = {
        "stage_1": "ORIGINAL_GROUNDED_WALLS_AND_RE-TILED_WALL_TOPS",
        "stage_2_brackets": [r["beam_id"] for r in accepted],
        "stage_3_30363_slope_ids_nominal_order_only":
            after["nominal_slope_order_after_wall_assembly"],
        "stage_4_cap_ids_nominal_only": sorted(
            pid for pid, state in new_caps.items()
            if state == "NOMINAL_TWO_SIDED_BRIDGE_TO_GROUNDED_SLOPES"),
        "gate": "STOP_BEFORE_30363_INSTALLATION_UNTIL_MATING_AND_INSERTION_VERIFIED",
    }
    prior_ids = {p.placement_id for p in source.parts}
    new_ids = {p.placement_id for p in candidate.parts}
    inserted = [p for p in candidate.parts if p.placement_id not in prior_ids]
    removed_parts = [p for p in source.parts if p.placement_id not in new_ids]
    def bom(parts):
        return [{"part_id": key[0], "color": "UNSPECIFIED_BY_BRICKMODEL",
                 "quantity": val} for key, val in sorted(Counter(
                     (p.part_id, "UNSPECIFIED_BY_BRICKMODEL") for p in parts).items())]
    result = {
        "source_building_id": source.building_id,
        "experiment_building_id": candidate.building_id,
        "source_parts": len(source.parts),
        "experimental_parts": len(candidate.parts),
        "roots_initially_missing": sorted(unresolved),
        "accepted_eave_brackets": accepted,
        "bracket_count": len(accepted),
        "root_ids_with_new_nominal_path": corrected,
        "nominal_roof_paths_newly_anchored": len(newly_grounded),
        "newly_anchored_root_count": len([p for p in newly_grounded if p in unresolved]),
        "newly_anchored_descendant_count": len([p for p in newly_grounded if p not in unresolved]),
        "newly_anchored_slope_details": newly_connected_details,
        "roof_paths_still_unreached": remaining,
        "caps_newly_nominally_anchored": caps_newly_grounded,
        "caps_still_blocked_details": caps_blocked,
        "provisional_assembly_sequence": provisional_order,
        "orthogonal_wall_overlap_screen": "PASS_FOR_SELECTED_SAME_COURSE_SOLIDS",
        "nonorthogonal_3d_clearance_and_insertion": "NOT_PROVEN",

        "unresolved_root_designs": blockers,
        "before": {"nominal": report["roof_slope_grounded_nominal"],
                   "unreached": report["roof_slope_still_without_grounded_nominal_path"],
                   "caps": report["ridge_cap_status_counts"]},
        "after": {"nominal": after["roof_slope_grounded_nominal"],
                  "unreached": after["roof_slope_still_without_grounded_nominal_path"],
                  "caps": after["ridge_cap_status_counts"]},
        "parts_added": [p.model_dump(mode="json") for p in inserted],
        "parts_removed": [p.model_dump(mode="json") for p in removed_parts],
        "bom_additions": bom(inserted), "bom_removals": bom(removed_parts),
        "new_orthogonal_documented_wall_interfaces": sum(
            len(r["grounded_lower_stud_cells"]) for r in accepted),
        "roof_cavity_connections_mechanically_proven": 0,
        "physical_certification": "NOT_CERTIFIED",
        "load_capacity_and_roof_insertion": "NOT_DEMONSTRATED",
        "color_purchase_readiness": "BLOCKED_UNSPECIFIED_COLOR",
        "construction_gate": "DENIED_UNVERIFIED_30363_CAVITY_AND_STABILITY",
        "canonical_model_mutated": False,
    }
    return result, candidate
