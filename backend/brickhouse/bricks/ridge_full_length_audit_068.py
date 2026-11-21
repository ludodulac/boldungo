"""Non-mutating full-length 3-D roof seam study for any two-slope house.

Checks EVERY candidate along the ridge up to a visible budget. Uses 067's
single-site real LDraw probe and adds seams between *simultaneously shifted*
neighboring positive roof tiles (avoids testing against unmoved neighbors).
Always reports incomplete coverage; no physical LEGO joint is certified.

The default offsets compare existing placement with the empirically interesting
three-stud hypothesis. This does NOT modify actual canonical models.
"""
from __future__ import annotations

from collections import Counter

from lego_geometry_engine import LDrawLibrary

from .ridge_bridge_planner_065 import propose_ridge_bridges
from .ridge_seam_offsets_067 import probe_ridge_seam_offsets, _shifted
from .ridge_proposal_3d_066 import _pair
from .roof import create_m0_roof_catalog, SUPPORTED_SLOPE_FAMILIES


def audit_full_ridge(model, library: LDrawLibrary, *,
                     max_sites: int = 25,
                     shift_studs: int = 3) -> dict:
    if max_sites < 1:
        raise ValueError("max_sites must be >= 1")
    if shift_studs not in (1, 2, 3, 4):
        raise ValueError("shift_studs must be 1..4")

    proposal = propose_ridge_bridges(model)
    planned = proposal["proposed_tiles"]
    if not planned:
        return {
            "building_id": model.building_id, "status": "NO_PROPOSED_RIDGE_SITES",
            "proposed_sites": 0, "evaluated_sites": 0, "not_evaluated_sites": 0,
            "sites": [], "adjacent_shifted_tile_checks": [],
            "model_mutated": False, "physical_certification": "NOT_CERTIFIED",
        }

    all_parts = {p.placement_id: p for p in model.parts}
    rows = []
    geometry_counts = Counter()
    shifted_tiles = []
    exact_geometry_cache = {}
    roof_course_status = Counter()
    catalog = create_m0_roof_catalog()
    for idx in range(min(len(planned), max_sites)):
        experiment = probe_ridge_seam_offsets(
            model, library, proposal_index=idx, max_offset=shift_studs,
            relation_cache=exact_geometry_cache)
        by_offset = {abs(v["positive_roof_shift_studs"]): v
                     for v in experiment["offsets"]}
        baseline, shifted = by_offset.get(0), by_offset.get(shift_studs)
        if baseline is None or shifted is None:
            rows.append({
                "proposal_index": idx, "status": "UNKNOWN_MISSING_OFFSET_RESULT",
                "model_unchanged": True,
            })
            continue

        seam0 = baseline["slopes_mesh"].get("mesh_relation", "UNKNOWN")
        seam1 = shifted["slopes_mesh"].get("mesh_relation", "UNKNOWN")
        tile_relations = [
            item.get("mesh_relation", "UNKNOWN")
            for item in shifted["tile_to_slopes"]
        ]
        previous_relations = [
            item.get("mesh_relation", "UNKNOWN")
            for item in shifted["previous_positive_course"]
        ]
        geometry_counts["baseline:" + seam0] += 1
        geometry_counts["shifted:" + seam1] += 1
        positive_part = all_parts.get(experiment["base_pair"][1])
        previous_ids = experiment["previous_course_ids"]
        course = {"status": "UNKNOWN_PREVIOUS_COURSE_OR_FAMILY"}
        if positive_part is not None and len(previous_ids) == 1:
            previous_part = all_parts.get(previous_ids[0])
            try:
                part_family = catalog.get(positive_part.part_id).slope_family
            except KeyError:
                part_family = None
            family = next((f for f in SUPPORTED_SLOPE_FAMILIES
                           if f.id == part_family), None)
            if previous_part is not None and family is not None:
                axis_field = ("x_studs" if experiment["shift_axis"] == "x"
                              else "y_studs")
                previous_axis = getattr(previous_part, axis_field)
                original_axis = getattr(positive_part, axis_field)
                original_step = abs(previous_axis - original_axis)
                shifted_step = abs(previous_axis - (
                    original_axis + shifted["positive_roof_shift_studs"]))
                proper_rise = (positive_part.z_plates - previous_part.z_plates
                               == family.rise_plates)
                consistent = (shifted_step == family.course_advance_studs
                              and proper_rise)
                course = {
                    "status": ("PRESERVED_NOMINAL_COURSE_ADVANCE" if consistent
                               else "BROKEN_NOMINAL_COURSE_ADVANCE"),
                    "family": family.id,
                    "required_advance_studs": family.course_advance_studs,
                    "original_advance_studs": original_step,
                    "shifted_advance_studs": shifted_step,
                    "required_rise_plates": family.rise_plates,
                    "rise_plates_preserved": proper_rise,
                }
        roof_course_status[course["status"]] += 1
        status = (
            "BROKEN_ROOF_COURSE_GEOMETRY"
            if course["status"] == "BROKEN_NOMINAL_COURSE_ADVANCE"
            else "UNKNOWN" if course["status"] != "PRESERVED_NOMINAL_COURSE_ADVANCE"
            or seam1 == "UNKNOWN" or
            any(value == "UNKNOWN" for value in tile_relations + previous_relations)
            else "INTERSECTION_REVIEW_REQUIRED"
            if seam1 == "COLLISION" or "COLLISION" in tile_relations + previous_relations
            else "LOCAL_MESH_REVIEW_REQUIRED"
        )
        geometry_counts[status] += 1
        rows.append({
            "proposal_index": idx,
            "existing_tile": planned[idx],
            "negative_id": experiment["base_pair"][0],
            "positive_id": experiment["base_pair"][1],
            "baseline_opposing_slopes": seam0,
            "shift_studs": shifted["positive_roof_shift_studs"],
            "shifted_opposing_slopes": seam1,
            "shifted_bridge": shifted["bridge_candidate"],
            "shifted_bridge_to_slopes": tile_relations,
            "shifted_to_previous_course": previous_relations,
            "previous_course_ids": experiment["previous_course_ids"],
            "course_advance_validation": course,
            "status": status,
        })
        # Neighbor checks must model the *entire row shifted together*, not
        # one tile shifted against an unshifted side neighbor.
        positive = all_parts.get(experiment["base_pair"][1])
        if positive is not None:
            shifted_tiles.append(
                (_shifted(positive, experiment["shift_axis"],
                          shifted["positive_roof_shift_studs"]),
                 positive, experiment["shift_axis"]))

    adjacent = []
    cache = {}
    catalog = create_m0_roof_catalog()
    for i, (first, original, axis) in enumerate(shifted_tiles):
        shape = catalog.get(original.part_id)
        footprint_length = (
            shape.length_studs if axis == "x" else shape.width_studs
        )
        along = "y_studs" if axis == "x" else "x_studs"
        next_along = getattr(original, along) + footprint_length
        for following, original_following, following_axis in shifted_tiles[i+1:]:
            if following_axis != axis or first.z_plates != following.z_plates:
                continue
            if getattr(original_following, along) != next_along:
                continue
            if getattr(first, "x_studs" if axis == "x" else "y_studs") != getattr(
                following, "x_studs" if axis == "x" else "y_studs"
            ):
                continue
            relation = _pair(first, following, library, cache, exact_geometry_cache)
            adjacent.append({
                "first_original_id": original.placement_id,
                "second_original_id": original_following.placement_id,
                "mesh_relation": relation.get("mesh_relation", "UNKNOWN"),
                "status": relation["status"],
            })

    truncated = len(planned) > len(rows)
    missing = sum(row["status"] == "UNKNOWN" for row in rows)
    intersections = sum(row["status"] == "INTERSECTION_REVIEW_REQUIRED" for row in rows)
    return {
        "building_id": model.building_id,
        "status": "PARTIAL_SAMPLE" if truncated else "ALL_PROPOSALS_SAMPLED",
        "proposed_sites": len(planned),
        "evaluated_sites": len(rows),
        "not_evaluated_sites": len(planned) - len(rows),
        "shift_studs_hypothesis": shift_studs,
        "unique_mesh_relations_computed": len(exact_geometry_cache),
        "mesh_reuse_method": "EXACT_RELATIVE_LDRAW_TRANSFORM_EQUIVALENCE",
        "geometry_counts": dict(sorted(geometry_counts.items())),
        "nominal_course_geometry_counts": dict(sorted(roof_course_status.items())),
        "sites_with_unknown_geometry": missing,
        "sites_with_review_required_intersection": intersections,
        "sites": rows,
        "adjacent_shifted_tile_checks": adjacent,
        "adjacent_relations": dict(sorted(Counter(
            row["mesh_relation"] for row in adjacent).items())),
        "existing_ridge_pieces": proposal["existing_ridge_count"],
        "hypothetical_bridge_pieces": proposal["proposed_count"],
        "model_mutated": False,
        "physical_certification": "NOT_CERTIFIED",
        "limitations": (
            "Even a collision-free mesh sample is NOT a structurally buildable "
            "ridge. This compares local upper courses with shifted pieces; "
            "underside grip, insertion, global roof silhouette, all wall "
            "supports, and other roof interfaces remain unproven. "
            "Existing ridge placements are not modified. "
            "Only checked sites are represented; budget omissions are visible."
        ),
    }
