"""LEGO2-072: proposed real LEGO 2x3 headpiece on a documented ridge post.

Replace (in an EXPERIMENT ONLY) the uppermost 1x1 post brick from 070/071
with an existing 2x3 brick, centered on the unchanged transverse TILE_2X3.
The lower 1x1 -> 2x3 interface is reviewed by the existing connector gate.
The 2x3 -> ridge TILE interface is NOT reviewed and remains UNKNOWN.
LDraw detects mesh interference; it does not prove underside clutch,
insertion, torsional stiffness or strength. No BrickModel is mutated.
"""
from __future__ import annotations

from collections import Counter

from .brick_model import BrickModelPart
from .catalog import standard_orthogonal_definitions
from .connectors import validate_connection
from .ridge_proposal_3d_066 import _pair
from .ridge_tile_upper_interface_073 import inspect_3002_26603_upper_interface
from .ridge_clutch_verifier_074 import validate_3002_26603_clutch
from .ridge_structural_posts_070 import assess_structural_ridge_posts
from .roof import create_m0_roof_catalog
from .roof_ridge_diagnostics import _footprint


def _make_part(pid, part_id, category, component, x, y, z, turns, side=None):
    return BrickModelPart(
        placement_id=pid, part_id=part_id, category=category,
        component=component, x_studs=x, y_studs=y, z_plates=z,
        rotation_quarter_turns=turns, roof_side=side,
    )


def _nearby_existing(model, cap, *, cap_footprint):
    """Conservative nominal broad phase, not an acceptance criterion."""
    roof_catalog = create_m0_roof_catalog()
    wall_catalog = standard_orthogonal_definitions()
    hits, unknown = [], []
    for p in model.parts:
        if p.component == "roof":
            definition = next((d for d in roof_catalog.parts if d.id == p.part_id), None)
            if definition is None:
                unknown.append(p.placement_id)
                continue
            footprint = _footprint(p, roof_catalog)
            height = definition.height_plates
        elif p.component in ("wall", "roof_support"):
            definition = wall_catalog.get(p.part_id)
            if definition is None:
                unknown.append(p.placement_id)
                continue
            w, d = definition.footprint(p.rotation_quarter_turns)
            footprint = {(p.x_studs + dx, p.y_studs + dy)
                         for dx in range(w) for dy in range(d)}
            height = definition.height_plates
        else:
            # Existing facade details/glazing may overlap: no total clearance
            # certificate can be made from this reduced scan.
            continue
        if footprint & cap_footprint and p.z_plates < cap.z_plates + 3 and (
            p.z_plates + height > cap.z_plates
        ):
            hits.append(p)
    return hits, unknown


def assess_ridge_cap_adapters(model, library=None, *, max_sites=8, max_mesh_pairs=80):
    """Probe 3002.dat as a supported headpiece under 26603.dat roof ridge.

    A cap is only *proposed* if the 071 wall-to-z0 path and a documented
    1x1 -> 2x3 connector are present. The top tile clutch is ALWAYS UNKNOWN.
    This uses the 070/071 study without repeating earlier roof-shift audits.
    """
    if max_sites < 1 or max_mesh_pairs < 1:
        raise ValueError("limits must be positive")
    # 070's default library-free path is sufficient to select candidate
    # support columns. Mesh work for THIS one new piece happens below.
    bases = assess_structural_ridge_posts(model, max_sites=max_sites)
    roof_catalog = create_m0_roof_catalog()
    cache, relation_cache = {}, {}
    mesh_count = 0
    rows = []
    for index, site in enumerate(bases["sites"]):
        tile = site["ridge_tile"]
        row = {
            "site_index": index,
            "status": "UNKNOWN_NO_VALID_POST_FOR_CAP",
            "existing_wall_anchor": site.get("anchor_id"),
            "host_support_path": site["host_support_path"]["status"],
            "original_post_count": len(site["post_parts"]),
            "headpiece": None,
            "replaces_experimental_post_top": False,
            "lower_post_to_headpiece": "UNKNOWN",
            "headpiece_to_ridge_tile": "UNKNOWN_UNREVIEWED_TILE_UNDERSIDE",
            "upper_clutch_review": {"status": "UNKNOWN", "reason": "NOT_EVALUATED"},
            "upper_interface_geometry": {"status": "UNKNOWN_NOT_EVALUATED"},
            "roof_slope_connections": "UNKNOWN_UNREVIEWED",
            "insertion_path": "UNKNOWN_NOT_PROVEN",
            "torsional_stability": "UNKNOWN_NOT_MEASURED",
            "mesh_checks": [],
        }
        posts = site["post_parts"]
        # One lower brick plus a replacement top brick is necessary. A cap
        # must never appear atop an unverified wall path.
        if site["host_support_path"]["status"] != "DOCUMENTED_NOMINAL_WALL_STUD_PATH_TO_Z0" or len(posts) < 2:
            if posts and len(posts) < 2:
                row["status"] = "UNKNOWN_NO_ROOM_FOR_HEADPIECE"
            rows.append(row)
            continue
        if tile["part_id"] != "TILE_2X3":
            row["status"] = "UNKNOWN_UNREVIEWED_CAP_DIMENSIONS"
            rows.append(row)
            continue
        # The 2x3 3002 brick (reviewed lower 1x1 edge interface) has the
        # same orientation and footprint as the 2x3 26603 ridge cover.
        head_z = tile["z_plates"] - 3
        lower = posts[-2]
        if lower["z_plates"] + 3 != head_z:
            row["status"] = "UNKNOWN_NONCONTIGUOUS_POST"
            rows.append(row)
            continue
        cap = _make_part(f"EXPERIMENT-072-CAP-{index:03d}",
                         "BRICK_2X3", "brick", "roof_support",
                         tile["x_studs"], tile["y_studs"], head_z,
                         tile["rotation_quarter_turns"])
        lower_part = _make_part(f"EXPERIMENT-072-LOWER-{index:03d}",
                                "BRICK_1X1", "brick", "roof_support",
                                lower["x_studs"], lower["y_studs"],
                                lower["z_plates"], 0)
        ridge = _make_part(f"EXPERIMENT-072-TILE-{index:03d}",
                           tile["part_id"], "ridge_tile", "roof",
                           tile["x_studs"], tile["y_studs"],
                           tile["z_plates"], tile["rotation_quarter_turns"],
                           "ridge")
        definition = standard_orthogonal_definitions()["BRICK_2X3"]
        w, d = definition.footprint(cap.rotation_quarter_turns)
        head_fp = {(cap.x_studs + dx, cap.y_studs + dy)
                   for dx in range(w) for dy in range(d)}
        lid_fp = _footprint(ridge, roof_catalog)
        if head_fp != lid_fp:
            row["status"] = "REJECTED_CAP_COVER_FOOTPRINT_MISMATCH"
            rows.append(row)
            continue
        connection = validate_connection(lower_part, cap)
        row["lower_post_to_headpiece"] = connection.status
        row["connector_reason"] = connection.reason
        if connection.status != "VALID" or connection.interface_count != 1:
            row["status"] = "UNKNOWN_OR_INVALID_HEADPIECE_CONNECTOR"
            rows.append(row)
            continue
        upper = inspect_3002_26603_upper_interface(cap, ridge)
        row["upper_interface_geometry"] = upper
        row["headpiece_to_ridge_tile"] = upper["upper_clutch"]
        # Nominal top-stud geometry must never override collision checks,
        # nor assert a physically tested clutch or tile-to-slope assembly.
        row["headpiece"] = {
            "part_id": cap.part_id, "ldraw_id": "3002",
            "component": "roof_support", "x_studs": cap.x_studs,
            "y_studs": cap.y_studs, "z_plates": cap.z_plates,
            "rotation_quarter_turns": cap.rotation_quarter_turns,
        }
        row["replaces_experimental_post_top"] = True
        # Existing walls/roof bricks aren't removed to make the cap fit.
        nearby, unreviewed = _nearby_existing(model, cap, cap_footprint=head_fp)
        row["upper_clutch_review"] = validate_3002_26603_clutch(
            cap, ridge, library, surrounding=nearby, max_pair_checks=12)
        row["existing_mesh_neighbors"] = sorted(p.placement_id for p in nearby)
        row["unreviewed_existing_parts"] = sorted(unreviewed)[:20]
        pairs = [(cap, ridge)] + [(cap, part) for part in nearby]
        row["mesh_pairs_required"] = len(pairs)
        if library is None:
            row["status"] = "UNKNOWN_LDRAW_LIBRARY_REQUIRED"
        elif mesh_count + len(pairs) > max_mesh_pairs:
            row["status"] = "UNKNOWN_MESH_BUDGET_EXCEEDED"
        else:
            checks = [_pair(a, b, library, cache, relation_cache)
                      for a, b in pairs]
            mesh_count += len(checks)
            row["mesh_checks"] = checks
            if any(c["status"] == "MESH_INTERSECTION_REVIEW_REQUIRED" for c in checks):
                row["status"] = "MESH_INTERSECTION_REVIEW_REQUIRED"
            elif unreviewed or any(c["status"] == "UNKNOWN_GEOMETRY_UNAVAILABLE"
                                   for c in checks):
                row["status"] = "UNKNOWN_UNREVIEWED_OR_MISSING_LDRAW_GEOMETRY"
            else:
                row["status"] = "HEADPIECE_MESH_SCREEN_ONLY_CLUTCH_UNKNOWN"
        rows.append(row)
    return {
        "building_id": model.building_id,
        "strategy": "REPLACE_EXPERIMENTAL_TOP_1X1_WITH_2X3_HEADPIECE",
        "sites_checked": len(rows),
        "status_counts": dict(sorted(Counter(r["status"] for r in rows).items())),
        "sites": rows,
        "mesh_pairs_checked": mesh_count,
        "original_part_count": len(model.parts),
        "model_mutated": False,
        "physical_certification": "NOT_CERTIFIED",
        "limitations": (
            "Reviewed 1x1->2x3 joint only proves nominal geometry, never load. "
            "26603 tube layout checked by 073 and bounded 074 LDraw "
            "insertion samples, but physical clutch "
            "still UNKNOWN. Connection to two roof slopes and preexisting "
            "seam collision, post stability, foundations, full nearby facade "
            "clearance and insertion path remain UNKNOWN. Cap is an experimental "
            "replacement of the post top, not an addition to the canonical house."
        ),
    }
