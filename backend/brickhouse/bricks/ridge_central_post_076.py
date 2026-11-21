"""LEGO2-076: examine an ANCHORED 1x1 post between unchanged roof slopes.

The wide 3002 head was shown impossible at the ridge stud plane by 075.
This uses 070/071's *original* central 1x1 column, not an additional
wide support. It checks exposed slope-stud occupancy, a vertical nominal
wall/post path, and bounded LDraw mesh contacts against the 26603/87079
cover and both existing 30363 slopes.

Stud positions/contact or a mesh check do NOT certify tile clutch, roof
assembly, insertion, stability, or mechanical load. No model is mutated.
"""
from __future__ import annotations

from collections import Counter

from .brick_model import BrickModelPart
from .connectors import validate_connection
from .ridge_structural_posts_070 import assess_structural_ridge_posts
from .ridge_proposal_3d_066 import _pair
from .roof import create_m0_roof_catalog
from .roof_ridge_diagnostics import _footprint, _studs_documented

# 070 has checked nominal host/post studs and existing masonry obstructions.
# Only these outcomes leave a post eligible for further 076 examination.
_ELIGIBLE_070 = frozenset({
    "UNKNOWN_LDRAW_LIBRARY_REQUIRED",
    "UNKNOWN_INCOMPLETE_LDRAW_GEOMETRY",
    "POSSIBLE_POST_GEOMETRY_CLUTCH_UNKNOWN",
    "UNKNOWN_MESH_BUDGET_EXCEEDED",
})


def _cover(tile, index):
    return BrickModelPart(
        placement_id=f"EXPERIMENT-076-COVER-{index:03d}",
        part_id=tile["part_id"], category="ridge_tile",
        component="roof", roof_side="ridge",
        x_studs=tile["x_studs"], y_studs=tile["y_studs"],
        z_plates=tile["z_plates"],
        rotation_quarter_turns=tile["rotation_quarter_turns"],
    )


def _last_post(part, index):
    return BrickModelPart(
        placement_id=f"EXPERIMENT-076-POST-{index:03d}",
        part_id=part["part_id"], category="brick",
        component="roof_support", x_studs=part["x_studs"],
        y_studs=part["y_studs"], z_plates=part["z_plates"],
        rotation_quarter_turns=0,
    )


def assess_central_ridge_post(model, library=None, *, max_sites=8,
                              max_mesh_pairs=60):
    """Assess the exact central 1x1 option; never add or move LEGO parts.

    REVIEW_REQUIRED for a mesh intersection, not mechanical INVALID: the
    mesh engine does not subtract legitimate stud/tube clutch volumes.
    INVALID only for demonstrably duplicated studs / nonmatching planes.
    All physically unproven connections remain UNKNOWN.
    """
    if max_sites < 1 or max_mesh_pairs < 1:
        raise ValueError("limits must be positive")
    # Reuse the ORIGINAL 070/071 post evaluation, including its LDraw scan of
    # every shaft brick against nearby existing roof pieces when available.
    base = assess_structural_ridge_posts(
        model, library=library, max_sites=max_sites,
        max_mesh_pairs=max_mesh_pairs,
    )
    catalog = create_m0_roof_catalog()
    roofs = [p for p in model.parts
             if p.component == "roof" and p.roof_side in ("negative", "positive")]
    studs_by_id = {p.placement_id: _studs_documented(p) for p in roofs}
    checks_left = max_mesh_pairs - base["mesh_pairs_checked"]
    cache, relations = {}, {}
    additional_mesh = 0
    reports = []

    for index, source in enumerate(base["sites"]):
        tile = source["ridge_tile"]
        cap = _cover(tile, index)
        footprint = _footprint(cap, catalog)
        row = {
            "site_index": index,
            "tile_part_id": tile["part_id"],
            "tile_placement": tile,
            "base_070_status": source["status"],
            "post_cell": source.get("post_cell"),
            "post_top_plane": None,
            "post_count": len(source["post_parts"]),
            "anchor_id": source.get("anchor_id"),
            "anchor_chain": source["host_support_path"],
            "post_connector_statuses": source["post_connector_statuses"],
            "post_to_tile": "UNKNOWN_UNREVIEWED_TILE_UNDERSIDE",
            "tile_to_negative_slope": "UNKNOWN_UNVERIFIED_TILE_CLUTCH",
            "tile_to_positive_slope": "UNKNOWN_UNVERIFIED_TILE_CLUTCH",
            "stud_overlap_with_slopes": [],
            "slope_ids": {"negative": [], "positive": []},
            "mesh_checks": list(source.get("mesh_checks", [])),
            "mesh_pairs_required": source.get("mesh_pairs_required", 0),
            "mesh_budget_truncated": False,
            "insertion": "UNKNOWN_NOT_PROVEN",
            "mechanical_strength": "UNKNOWN_NOT_MEASURED",
            "physical_certification": "NOT_CERTIFIED",
            "status": "UNKNOWN_NO_DOCUMENTED_CENTRAL_SUPPORT",
        }
        if (source["status"] not in _ELIGIBLE_070
                or not source["post_parts"]
                or source["host_support_path"]["status"]
                   != "DOCUMENTED_NOMINAL_WALL_STUD_PATH_TO_Z0"
                or any(s != "VALID" for s in source["post_connector_statuses"])):
            if source["status"] == "BLOCKED_MESH_INTERSECTION_REQUIRES_REVIEW":
                row["status"] = "REVIEW_REQUIRED_EXISTING_POST_ROOF_MESH_INTERSECTION"
            reports.append(row)
            continue

        last = _last_post(source["post_parts"][-1], index)
        top = last.z_plates + 3
        post_stud = (last.x_studs, last.y_studs, top)
        row["post_top_plane"] = top
        if last.part_id != "BRICK_1X1" or footprint is None:
            row["status"] = "UNKNOWN_UNREVIEWED_CENTRAL_PART_OR_TILE"
            reports.append(row)
            continue
        if top != cap.z_plates or (last.x_studs, last.y_studs) not in footprint:
            row["status"] = "INVALID_POST_NOT_BELOW_TILE_AT_CONNECTOR_PLANE"
            reports.append(row)
            continue
        # The ordinary connector gate intentionally does not certify the
        # underside of tiles. Even 1x1 nominal XY contact stays UNKNOWN.
        interface = validate_connection(last, cap)
        row["post_to_tile"] = interface.status
        row["post_to_tile_reason"] = interface.reason
        if interface.status == "INVALID":
            row["status"] = "INVALID_POST_TO_TILE_PLACEMENT"
            reports.append(row)
            continue

        plane_cells = {(x, y, cap.z_plates) for x, y in footprint}
        sides = {}
        for side in ("negative", "positive"):
            ids = [p.placement_id for p in roofs
                   if p.roof_side == side and studs_by_id[p.placement_id]
                   and studs_by_id[p.placement_id] & plane_cells]
            row["slope_ids"][side] = sorted(ids)
            if len(ids) == 1:
                sides[side] = next(p for p in roofs if p.placement_id == ids[0])

        if len(sides) != 2:
            row["status"] = "UNKNOWN_INCOMPLETE_OR_AMBIGUOUS_TWO_SLOPE_CONNECTION"
            reports.append(row)
            continue
        overlap = sorted({
            post_stud for p in sides.values()
            if post_stud in (studs_by_id[p.placement_id] or frozenset())
        })
        row["stud_overlap_with_slopes"] = [list(c) for c in overlap]
        if overlap:
            row["status"] = "INVALID_DUPLICATED_TOP_STUD_WITH_ROOF_SLOPE"
            reports.append(row)
            continue

        # 30363 studs are proven present on BOTH sides, at different cells
        # from the post. But 26603's underside has only two tubes and a rim;
        # its clutch on THREE separate parts is not yet documented.
        row["studs_distinct_from_both_slopes"] = True
        row["two_slope_studs_documented"] = True
        if cap.part_id == "TILE_2X3":
            row["post_to_tile"] = "UNKNOWN_SINGLE_1X1_STUD_VS_26603_UNDERSIDE"
        else:
            row["post_to_tile"] = "UNKNOWN_UNREVIEWED_OTHER_TILE_UNDERSIDE"
        row["status"] = "UNKNOWN_THREE_PART_CLUTCH_NOT_DEMONSTRATED"

        if library is not None:
            # The first mesh pairs, between the entire post shaft and roof,
            # and between the post top and cover, were already computed by 070.
            # Only assess the missing COVER-to-both-slopes and slope-to-slope
            # local pairs. No previous shift/ridge audit is restarted.
            a, b = sides["negative"], sides["positive"]
            for first, second in ((cap, a), (cap, b), (a, b)):
                row["mesh_pairs_required"] += 1
                if checks_left <= 0:
                    row["mesh_budget_truncated"] = True
                    continue
                row["mesh_checks"].append(
                    _pair(first, second, library, cache, relations))
                checks_left -= 1
                additional_mesh += 1
            statuses = [c["status"] for c in row["mesh_checks"]]
            if row["mesh_budget_truncated"] or source["status"] == "UNKNOWN_MESH_BUDGET_EXCEEDED":
                row["status"] = "UNKNOWN_INCOMPLETE_LDRAW_BUDGET"
            elif "MESH_INTERSECTION_REVIEW_REQUIRED" in statuses:
                row["status"] = "REVIEW_REQUIRED_LDRAW_MESH_INTERSECTION"
            elif "UNKNOWN_GEOMETRY_UNAVAILABLE" in statuses:
                row["status"] = "UNKNOWN_LDRAW_GEOMETRY_UNAVAILABLE"
            else:
                row["status"] = "UNKNOWN_THREE_PART_CLUTCH_NOT_DEMONSTRATED"
        reports.append(row)
    return {
        "building_id": model.building_id,
        "strategy": "ONE_CENTER_1X1_POST_WITH_TWO_UNCHANGED_SLOPES",
        "sites_checked": len(reports),
        "sites": reports,
        "status_counts": dict(sorted(Counter(row["status"] for row in reports).items())),
        "mesh_pairs_checked": base["mesh_pairs_checked"] + additional_mesh,
        "model_mutated": False,
        "original_part_count": len(model.parts),
        "physical_certification": "NOT_CERTIFIED",
        "limitations": (
            "Distinct LDraw top studs do not prove simultaneous engagement "
            "of a single tile underside on three separate LEGO pieces. "
            "The central 1x1 stud against 26603's two underside tubes/rim, "
            "the cover-to-two-30363 connection, insertion, roof seam "
            "interference and mechanical strength remain UNKNOWN. "
            "No canonical part or existing roof geometry was modified."
        ),
    }
