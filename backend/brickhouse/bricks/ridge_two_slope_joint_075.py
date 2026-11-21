"""LEGO2-075: can ONE ridge cover engage both sloped sides AND its 3002 head?

The 065 planner identifies *exposed* 30363 studs under a transverse cover.
The 072 headpiece places 3002 directly under that same cover, with six studs
on the very same z-plane. Here we check that distinct actual LEGO parts do
not claim the same stud cylinders at identical XYZ coordinates.

This is a bounded, non-mutating design gate; real LDraw mesh relations are
separately reported via 066. It cannot certify the 26603 underside clutch.
"""
from __future__ import annotations

from collections import Counter

from .brick_model import BrickModelPart
from .catalog import standard_orthogonal_definitions
from .ridge_bridge_planner_065 import propose_ridge_bridges
from .ridge_cap_adapter_072 import assess_ridge_cap_adapters
from .ridge_proposal_3d_066 import _pair
from .roof import create_m0_roof_catalog
from .roof_ridge_diagnostics import _footprint, _studs_documented


def _headpiece_studs(head):
    definition = standard_orthogonal_definitions().get(head["part_id"])
    if definition is None:
        return None
    w, d = definition.footprint(head["rotation_quarter_turns"])
    return {
        (head["x_studs"] + x, head["y_studs"] + y, head["z_plates"] + definition.height_plates)
        for x in range(w) for y in range(d)
    }


def _candidate_part(prefix, tile, index):
    return BrickModelPart(
        placement_id=f"EXPERIMENT-075-{prefix}-{index:03d}",
        part_id=tile["part_id"],
        category="ridge_tile",
        component="roof", roof_side="ridge",
        x_studs=tile["x_studs"], y_studs=tile["y_studs"],
        z_plates=tile["z_plates"],
        rotation_quarter_turns=tile["rotation_quarter_turns"],
    )


def _head_part(head, index):
    return BrickModelPart(
        placement_id=f"EXPERIMENT-075-HEAD-{index:03d}",
        part_id=head["part_id"], category="brick",
        component="roof_support",
        x_studs=head["x_studs"], y_studs=head["y_studs"],
        z_plates=head["z_plates"],
        rotation_quarter_turns=head["rotation_quarter_turns"],
    )


def assess_two_slope_ridge_connection(model, library=None, *, max_sites=8,
                                      max_mesh_pairs=40):
    """Reject coincident 3002 studs and both opposing 30363 stud rows.

    Position INVALID is a contradiction for the specific simultaneous,
    fully-seated 3002 + 26603 + 2x30363 plan, not a claim that the LEGO
    parts cannot be assembled in other arrangements.

    An intermediate or differently sized connector is not invented here.
    The original narrow 1x1 post remains a separate UNKNOWN alternative.
    """
    if max_sites < 1 or max_mesh_pairs < 1:
        raise ValueError("limits must be positive")
    proposals = propose_ridge_bridges(model, max_tiles=max_sites)
    caps = assess_ridge_cap_adapters(model, max_sites=max_sites)
    catalog = create_m0_roof_catalog()
    roof_slopes = [p for p in model.parts
                   if p.component == "roof" and p.roof_side in ("negative", "positive")]
    documented_studs = {p.placement_id: _studs_documented(p) for p in roof_slopes}
    roof_by_id = {p.placement_id: p for p in roof_slopes}
    cache, relation_cache = {}, {}
    pair_count = 0
    reports = []
    for idx, proposed in enumerate(proposals["proposed_tiles"]):
        tile_part = _candidate_part("RIDGE", proposed, idx)
        fp = _footprint(tile_part, catalog)
        required_cells = {(x, y, tile_part.z_plates) for x, y in fp}
        sides = {"negative": [], "positive": []}
        for p in roof_slopes:
            studs = documented_studs[p.placement_id]
            if studs is not None and studs & required_cells:
                sides[p.roof_side].append(p.placement_id)

        row = {
            "site_index": idx,
            "ridge_part": proposed["part_id"],
            "ridge_placement": {
                "x_studs": proposed["x_studs"], "y_studs": proposed["y_studs"],
                "z_plates": proposed["z_plates"],
                "rotation_quarter_turns": proposed["rotation_quarter_turns"],
            },
            "slope_ids": {s: sorted(ids) for s, ids in sides.items()},
            "status": "UNKNOWN_TWO_SIDED_JOINT_NOT_PROVEN",
            "two_slope_cover_clutch": "UNKNOWN_UNDOCUMENTED_30363_TO_26603",
            "headpiece_to_cover_clutch": "UNKNOWN_UNDOCUMENTED_3002_TO_26603",
            "roof_support_path": "UNKNOWN",
            "shared_stud_cells_by_side": {"negative": [], "positive": []},
            "mesh_pairs": [],
            "mesh_budget_truncated": False,
            "alternative": "UNKNOWN_NARROW_1X1_POST_TO_TILE_NOT_CERTIFIED",
            "physical_certification": "NOT_CERTIFIED",
        }
        cap = caps["sites"][idx] if idx < len(caps["sites"]) else None
        head = cap.get("headpiece") if cap else None
        row["roof_support_path"] = cap["host_support_path"] if cap else "UNKNOWN"
        if len(sides["negative"]) != 1 or len(sides["positive"]) != 1:
            row["status"] = "UNKNOWN_AMBIGUOUS_OR_MISSING_TWO_SLOPE_STUD_EVIDENCE"
            reports.append(row)
            continue

        neg = roof_by_id[sides["negative"][0]]
        pos = roof_by_id[sides["positive"][0]]
        if head is None:
            row["status"] = "UNKNOWN_NO_SUPPORTED_3002_HEADPIECE"
            reports.append(row)
            continue
        cap_studs = _headpiece_studs(head)
        if cap_studs is None:
            row["status"] = "UNKNOWN_UNSUPPORTED_HEADPIECE_PART"
            reports.append(row)
            continue

        overlap = {}
        for side, slope in (("negative", neg), ("positive", pos)):
            slope_studs = documented_studs[slope.placement_id] or frozenset()
            shared = sorted(cap_studs & slope_studs & required_cells)
            overlap[side] = shared
            row["shared_stud_cells_by_side"][side] = [list(cell) for cell in shared]
        row["headpiece_stud_count"] = len(cap_studs)
        row["two_slope_stud_overlap_count"] = sum(len(v) for v in overlap.values())
        # Two independent brick studs, with both bases at the same plane,
        # cannot physically occupy identical cylinder volumes. This local
        # proposed triple assembly is INVALID even if mesh files are missing.
        if overlap["negative"] or overlap["positive"]:
            row["status"] = "INVALID_DUPLICATED_STUD_OCCUPANCY"
            row["contradiction"] = (
                "3002 top studs and real 30363 upper studs occupy the same "
                "global XY stud cells at the identical Z plane, so the proposed "
                "full-size headpiece cannot co-exist with both unchanged slopes."
            )
        else:
            row["status"] = "UNKNOWN_NO_STUD_DUPLICATION_BUT_CLUTCH_UNPROVEN"

        if library is not None:
            # Only this site's three roof joints and two roof-to-head pairs.
            # LDraw reports CONTACT/COLLISION, not certified LEGO clutch.
            cap_part = _head_part(head, idx)
            pairs = [(cap_part, neg), (cap_part, pos),
                     (tile_part, neg), (tile_part, pos), (neg, pos)]
            for a, b in pairs:
                if pair_count >= max_mesh_pairs:
                    row["mesh_budget_truncated"] = True
                    break
                row["mesh_pairs"].append(_pair(a, b, library, cache, relation_cache))
                pair_count += 1
        reports.append(row)

    return {
        "building_id": model.building_id,
        "proposed_sites": proposals["proposed_count"],
        "sites_checked": len(reports),
        "sites": reports,
        "status_counts": dict(sorted(Counter(r["status"] for r in reports).items())),
        "ldraw_mesh_pairs_checked": pair_count,
        "original_part_count": len(model.parts),
        "model_mutated": False,
        "physical_certification": "NOT_CERTIFIED",
        "limitations": (
            "Even if the 3002 overlaps the 30363 stud rows, this only rejects "
            "this specific overlapping triple assembly. A narrow post, side "
            "adapter or independent truss could avoid shared upper studs but "
            "requires separate supported-part, mesh, clutch and insertion proofs. "
            "Never move slopes or certify the whole house from this evidence."
        ),
    }
