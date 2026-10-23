"""LEGO2-077: one 1x1 + one ridge tile + BOTH 30363 slopes, simultaneously.

Uses the exact 076 central-post sites and original model roof placements.
Every one of six pairs in the four-piece virtual assembly is inspected by
the existing LDraw pair engine, if the part geometry is available.

A separate bounded virtual sequence samples a cover lowered over *fixed*
roof slopes and an already-anchored central post. It cannot prove a continuous
assembly path, insertion of the roof slopes, clutch, or strength. NOT_CERTIFIED.
"""
from __future__ import annotations

from collections import Counter
from itertools import combinations

from .brick_model import BrickModelPart
from .ridge_central_post_076 import assess_central_ridge_post
from .ridge_proposal_3d_066 import _pair
from .roof_ridge_diagnostics import _studs_documented

_PAIR_STATUSES = frozenset({
    "MESH_SEPARATED",
    "MESH_CONTACT_REVIEW_REQUIRED",
    "MESH_INTERSECTION_REVIEW_REQUIRED",
    "UNKNOWN_GEOMETRY_UNAVAILABLE",
})
_DEFAULT_LIFTS = (3, 2, 1, 0)


def _virtual_post(row, index):
    x, y = row["post_cell"]
    return BrickModelPart(
        placement_id=f"EXPERIMENT-077-POST-{index:03d}",
        part_id="BRICK_1X1", category="brick", component="roof_support",
        x_studs=x, y_studs=y, z_plates=row["post_top_plane"] - 3,
        rotation_quarter_turns=0,
    )


def _virtual_cover(row, index):
    tile = row["tile_placement"]
    return BrickModelPart(
        placement_id=f"EXPERIMENT-077-COVER-{index:03d}",
        part_id=tile["part_id"], category="ridge_tile",
        component="roof", roof_side="ridge",
        x_studs=tile["x_studs"], y_studs=tile["y_studs"],
        z_plates=tile["z_plates"],
        rotation_quarter_turns=tile["rotation_quarter_turns"],
    )


def review_simultaneous_ridge_assembly(
    model, library=None, *, max_sites=8, max_mesh_pairs=80,
    cover_lift_plates=_DEFAULT_LIFTS,
):
    """Conservative four-piece full-seat plus fixed-slope cover-insertion check.

    Per-site status:
      INVALID: only a demonstrated duplicate stud cylinder / wrong z plane;
      REVIEW_REQUIRED: a LDraw mesh intersection needing connector-aware review;
      UNKNOWN: missing support, uncertain mesh/clutch/fit/assembly evidence.

    VALID is intentionally NOT returned without material/manufacturer evidence.
    """
    lifts = tuple(cover_lift_plates)
    if (max_sites < 1 or max_mesh_pairs < 1
            or not lifts or len(lifts) > 12
            or any(type(v) is not int or v < 0 for v in lifts)
            or tuple(sorted(set(lifts), reverse=True)) != lifts
            or lifts[-1] != 0):
        raise ValueError("positive budgets; descending distinct nonnegative lifts ending at zero")

    bases = assess_central_ridge_post(model, max_sites=max_sites)
    roof_by_id = {p.placement_id: p for p in model.parts
                  if p.component == "roof" and p.roof_side in ("negative", "positive")}
    cache, relation_cache = {}, {}
    checks_done, reports = 0, []
    for index, source in enumerate(bases["sites"]):
        row = {
            "site_index": index,
            "status": "UNKNOWN",
            "reason": "NO_FOUR_PART_CONFIGURATION_WITH_DOCUMENTED_ANCHOR",
            "component_count": 0,
            "components": [],
            "host_anchor_status": source["anchor_chain"]["status"],
            "nominal_wall_post_connectors": list(source["post_connector_statuses"]),
            "base_076_status": source["status"],
            "central_stud_collision": "UNKNOWN_NOT_EVALUATED",
            "post_to_cover_clutch": "UNKNOWN_UNVERIFIED_TILE_UNDERSIDE",
            "negative_slope_to_cover_clutch": "UNKNOWN_UNVERIFIED_30363_TO_TILE",
            "positive_slope_to_cover_clutch": "UNKNOWN_UNVERIFIED_30363_TO_TILE",
            "simultaneous_pair_checks": [],
            "missing_pair_checks": [],
            "cover_insertion_samples": [],
            "insertion_order": [
                "wall_and_lower_central_post_stack",
                "top_central_1x1_post",
                "left_and_right_30363_slopes_at_original_placements",
                "26603_or_87079_cover_lowered_vertically",
            ],
            "post_stack_insertion": "UNKNOWN_NOT_SIMULATED",
            "slope_installation": "UNKNOWN_NOT_SIMULATED",
            "cover_insertion": "UNKNOWN_CONTINUOUS_PATH_UNPROVEN",
            "load_and_stiffness": "UNKNOWN_NOT_MEASURED",
            "physical_certification": "NOT_CERTIFIED",
        }
        if (source["status"] != "UNKNOWN_THREE_PART_CLUTCH_NOT_DEMONSTRATED"
                or source["post_top_plane"] is None
                or source["anchor_chain"]["status"]
                   != "DOCUMENTED_NOMINAL_WALL_STUD_PATH_TO_Z0"
                or not source["post_connector_statuses"]
                or any(s != "VALID" for s in source["post_connector_statuses"])
                or len(source["slope_ids"]["negative"]) != 1
                or len(source["slope_ids"]["positive"]) != 1):
            reports.append(row)
            continue

        neg = roof_by_id[source["slope_ids"]["negative"][0]]
        pos = roof_by_id[source["slope_ids"]["positive"][0]]
        post = _virtual_post(source, index)
        cover = _virtual_cover(source, index)
        row["components"] = [
            {"role": role, "placement_id": p.placement_id,
             "part_id": p.part_id, "x_studs": p.x_studs,
             "y_studs": p.y_studs, "z_plates": p.z_plates,
             "rotation_quarter_turns": p.rotation_quarter_turns}
            for role, p in (("central_post", post), ("ridge_cover", cover),
                            ("negative_slope", neg), ("positive_slope", pos))
        ]
        row["component_count"] = 4
        z = cover.z_plates
        cell = (post.x_studs, post.y_studs, post.z_plates + 3)
        studs_a, studs_b = _studs_documented(neg), _studs_documented(pos)
        if cell[2] != z:
            row.update(status="INVALID", reason="CENTRAL_POST_NOT_AT_RIDGE_CONNECTOR_PLANE",
                       central_stud_collision="INVALID_MISMATCHED_HEIGHT")
            reports.append(row)
            continue
        if studs_a is None or studs_b is None:
            row["reason"] = "MISSING_DOCUMENTED_SLOPE_STUD_CELLS"
            reports.append(row)
            continue
        overlapping = [p.placement_id for p, studs in ((neg, studs_a), (pos, studs_b))
                       if cell in studs]
        if overlapping:
            row.update(status="INVALID", reason="DUPLICATED_POST_AND_SLOPE_STUD",
                       central_stud_collision="INVALID_DUPLICATED_STUD_CYLINDER",
                       overlapping_slope_ids=overlapping)
            reports.append(row)
            continue
        row["central_stud_collision"] = "NO_DUPLICATED_DOCUMENTED_TOP_STUD_CELLS"
        # The tile underside accepts neither the post nor slopes by a
        # validated rule. A single free central cell is NOT clutch evidence.
        row["reason"] = "FOUR_PART_CLUTCH_AND_INSERTION_UNKNOWN"

        if library is None:
            row["reason"] = "LDRAW_LIBRARY_REQUIRED_FOR_SIMULTANEOUS_MESH"
            reports.append(row)
            continue

        assembly = [post, cover, neg, pos]
        by_pair = {}
        # All six simultaneous part-vs-part checks, not only some pairs.
        for first, second in combinations(assembly, 2):
            pair_key = frozenset((first.placement_id, second.placement_id))
            if checks_done >= max_mesh_pairs:
                row["missing_pair_checks"].append({
                    "pair_ids": sorted(pair_key), "reason": "PAIR_BUDGET_EXHAUSTED"})
                continue
            result = _pair(first, second, library, cache, relation_cache)
            row["simultaneous_pair_checks"].append(result)
            by_pair[pair_key] = result
            checks_done += 1

        # No roof slope is EVER moved. Only a virtual cover is lowered along
        # Z while the three other parts remain at exact original positions.
        for lift in lifts:
            sampled_cover = cover.model_copy(update={
                "z_plates": cover.z_plates + lift,
                "placement_id": f"{cover.placement_id}-LIFT-{lift}",
            })
            sample = {"lift_plates": lift, "checks": [], "unchecked": []}
            for fixed in (post, neg, pos):
                # Seated lift=0 reuses the existing full-assembly pair result.
                key = frozenset((cover.placement_id, fixed.placement_id))
                if lift == 0 and key in by_pair:
                    sample["checks"].append(by_pair[key])
                    continue
                if checks_done >= max_mesh_pairs:
                    reason = {"target": fixed.placement_id,
                              "reason": "PAIR_BUDGET_EXHAUSTED"}
                    sample["unchecked"].append(reason)
                    continue
                result = _pair(sampled_cover, fixed, library, cache, relation_cache)
                sample["checks"].append(result)
                checks_done += 1
            row["cover_insertion_samples"].append(sample)

        all_checks = row["simultaneous_pair_checks"] + [
            pair for sample in row["cover_insertion_samples"]
            for pair in sample["checks"]
        ]
        statuses = {p["status"] for p in all_checks}
        if row["missing_pair_checks"] or any(s["unchecked"] for s in row["cover_insertion_samples"]):
            row["reason"] = "INCOMPLETE_SIMULTANEOUS_OR_INSERTION_MESH_BUDGET"
        elif "UNKNOWN_GEOMETRY_UNAVAILABLE" in statuses:
            row["reason"] = "UNAVAILABLE_COMPLETE_OFFICIAL_LDRAW_GEOMETRY"
        elif "MESH_INTERSECTION_REVIEW_REQUIRED" in statuses:
            row.update(status="REVIEW_REQUIRED",
                       reason="FOUR_PART_MESH_INTERSECTION_NEEDS_CONNECTOR_AWARE_REVIEW")
        elif statuses - _PAIR_STATUSES:
            row["reason"] = "UNRECOGNIZED_MESH_RELATION"
        else:
            row["reason"] = "DISCRETE_MESH_SCREEN_ONLY_NO_MECHANICAL_CLUTCH_PROOF"
        reports.append(row)

    return {
        "building_id": model.building_id,
        "approach": "EXACT_ONE_1X1_PLUS_RIDGE_COVER_PLUS_BOTH_UNMOVED_30363",
        "sites_checked": len(reports),
        "sites": reports,
        "status_counts": dict(sorted(Counter(r["status"] for r in reports).items())),
        "mesh_pairs_computed": checks_done,
        "original_part_count": len(model.parts),
        "model_mutated": False,
        "physical_certification": "NOT_CERTIFIED",
        "limitations": (
            "Six pairwise LDraw checks are simultaneous-placement screening; "
            "they are not a complete four-body LEGO connector, tolerance, "
            "elastic-clutch, insertion or strength model. Cover insertion "
            "is sampled at discrete heights only, with both original roof "
            "slopes held fixed. Slope insertion and post-stack erection are "
            "not demonstrated. No automatic VALID mechanical outcome."
        ),
    }
