"""LEGO2-070: non-mutating proposal for an anchored ridge-cap support post.

Existing 065 transverse ridge cover is kept as a *proposal*, never installed.
This experiment tries a documented stack of ordinary 1x1 LEGO bricks below
its interior cell, on an actual existing wall or roof-support stud column.
Neither the ridge cover/roof-slope clutch nor carrying capacity is proven.

Only known catalog pieces are proposed. Geometry uses 066's real LDraw probe
when a library is supplied; missing meshes and incomplete insertion remain
UNKNOWN. Never modify the canonical 1,890-piece house.
"""
from __future__ import annotations

from collections import Counter

from .brick_model import BrickModelPart
from .catalog import standard_orthogonal_definitions
from .connectors import validate_connection
from .ridge_bridge_planner_065 import propose_ridge_bridges
from .ridge_proposal_3d_066 import _pair
from .roof import create_m0_roof_catalog
from .roof_ridge_diagnostics import _footprint


def _host_cells(part, definition):
    width, length = definition.footprint(part.rotation_quarter_turns)
    return ((part.x_studs + x, part.y_studs + y)
            for x in range(width) for y in range(length))


def _interior_cells(tile, definition):
    """Only the inner transverse columns: not on either roof stud edge."""
    width, length = definition.width_studs, definition.length_studs
    if tile["rotation_quarter_turns"] % 2:
        width, length = length, width
    axis = "x" if tile["rotation_quarter_turns"] % 2 else "y"
    across = width if axis == "x" else length
    if across < 3:
        return []
    cells = []
    for cross in range(1, across - 1):
        for along in range(length if axis == "x" else width):
            x = tile["x_studs"] + (cross if axis == "x" else along)
            y = tile["y_studs"] + (along if axis == "x" else cross)
            cells.append((x, y))
    return cells


def _post(pid, x, y, z, part_id):
    return BrickModelPart(
        placement_id=pid, part_id=part_id, category="brick",
        component="roof_support", x_studs=x, y_studs=y, z_plates=z,
        rotation_quarter_turns=0,
    )


def assess_structural_ridge_posts(model, library=None, *,
                                  max_sites=8, max_post_plates=30,
                                  max_mesh_pairs=80):
    """Explore a short vertical structural route on existing masonry.

    This does NOT design an unsupported spanning beam or assume a floating
    post in the middle of a roof. For each proposed cover, evaluate ONE
    highest real host below an interior cell. A proposed post stack must
    use reviewed nominal connector interfaces; unobstructed orthogonal
    envelopes and actual LDraw meshes are separate checks.

    The existing roof's nominal pitch, wall/eave contacts and part list are
    never modified. The ridge cover's attachment to opposing roof slopes
    and the cover-to-post underside remain UNKNOWN without specific proof.
    """
    if max_sites < 1 or max_post_plates < 3 or max_mesh_pairs < 1:
        raise ValueError("limits must be positive (max_post_plates >= 3)")
    proposals = propose_ridge_bridges(model, max_tiles=max_sites)
    ortho = standard_orthogonal_definitions()
    roof_catalog = create_m0_roof_catalog()
    hosts = []
    unknown_hosts = []
    for part in model.parts:
        if part.component not in ("wall", "roof_support"):
            continue
        definition = ortho.get(part.part_id)
        if definition is None or part.category not in ("brick", "plate"):
            unknown_hosts.append(part.placement_id)
        else:
            hosts.append((part, definition, frozenset(_host_cells(part, definition))))
    results = []
    mesh_checks = 0
    cache, relations = {}, {}
    for index, tile in enumerate(proposals["proposed_tiles"]):
        part_def = roof_catalog.get(tile["part_id"])
        interior = set(_interior_cells(tile, part_def))
        site = {
            "ridge_tile": {k: tile[k] for k in (
                "part_id", "x_studs", "y_studs", "z_plates",
                "rotation_quarter_turns")},
            "status": "NO_EXISTING_ANCHOR_UNDER_RIDGE",
            "post_parts": [], "post_connector_statuses": [],
            "lid_to_slopes": "UNKNOWN_UNVERIFIED_RIDGE_CLUTCH",
            "post_to_lid": "UNKNOWN_RIDGE_TILE_UNDERSIDE",
            "insertion": "UNKNOWN_NOT_PROVEN",
            "structural_strength": "UNKNOWN_NOT_MEASURED",
            "mesh_checks": [],
        }
        if not interior:
            site["status"] = "NO_INTERIOR_CELL_FOR_POST"
            results.append(site)
            continue
        # A post must begin exactly on actual existing masonry. Prefer the
        # shortest valid vertical run, irrespective of house dimensions.
        candidates = []
        for host, definition, cells in hosts:
            top = host.z_plates + definition.height_plates
            if 3 <= tile["z_plates"] - top <= max_post_plates:
                for x, y in sorted(cells & interior):
                    candidates.append((tile["z_plates"] - top, x, y,
                                       host.placement_id, host))
        if not candidates:
            results.append(site)
            continue
        height, x, y, _, host = min(candidates)
        site["anchor_id"] = host.placement_id
        site["post_cell"] = [x, y]
        site["post_height_plates"] = height
        # For this limited 070 candidate every post is made of 1x1 BRICKS;
        # do not silently substitute plates with unreviewed interfaces.
        if height % 3:
            site["status"] = "UNKNOWN_NON_BRICK_HEIGHT_REQUIRES_REDESIGN"
            results.append(site)
            continue
        bottom = tile["z_plates"] - height
        posts = [_post(f"EXPERIMENT-070-{index:03d}-{i:02d}",
                       x, y, bottom + 3 * i, "BRICK_1X1")
                 for i in range(height // 3)]
        statuses = [validate_connection(a, b).status
                    for a, b in zip([host, *posts[:-1]], posts)]
        site["post_parts"] = [{
            "part_id": p.part_id, "x_studs": x, "y_studs": y,
            "z_plates": p.z_plates, "component": "roof_support",
        } for p in posts]
        site["post_connector_statuses"] = statuses
        if any(s != "VALID" for s in statuses):
            site["status"] = "UNKNOWN_OR_INVALID_POST_CONNECTORS"
            results.append(site)
            continue

        # Check the proposed shaft against every other existing masonry part,
        # not just against the selected host. Another wall cannot be erased.
        obstruction = []
        for other, definition, cells in hosts:
            if other.placement_id == host.placement_id or (x, y) not in cells:
                continue
            if other.z_plates < tile["z_plates"] and (
                other.z_plates + definition.height_plates > bottom
            ):
                obstruction.append(other.placement_id)
        if obstruction:
            site["status"] = "BLOCKED_EXISTING_MASONRY"
            site["blocking_host_ids"] = sorted(obstruction)
            results.append(site)
            continue
        if unknown_hosts:
            site["status"] = "UNKNOWN_UNMAPPED_EXISTING_SUPPORTS"
            site["unknown_host_count"] = len(unknown_hosts)
            results.append(site)
            continue

        # Nominal XY/Z screening only selects mesh candidates; the relation
        # itself comes from LDraw. Includes other ridge tiles/roof sides.
        nearby_roof = [
            part for part in model.parts
            if part.component == "roof"
            and (fp := _footprint(part, roof_catalog)) is not None
            and (x, y) in fp
            and part.z_plates <= tile["z_plates"]
            and part.z_plates + roof_catalog.get(part.part_id).height_plates >= bottom
        ]
        mesh_targets = [
            (post, roof_part)
            for post in posts for roof_part in nearby_roof
            if roof_part.z_plates <= post.z_plates + 3
            and post.z_plates <= roof_part.z_plates + roof_catalog.get(roof_part.part_id).height_plates
        ]
        site["mesh_pairs_required"] = len(mesh_targets)
        if library is None:
            site["status"] = "UNKNOWN_LDRAW_LIBRARY_REQUIRED"
        elif mesh_checks + len(mesh_targets) > max_mesh_pairs:
            site["status"] = "UNKNOWN_MESH_BUDGET_EXCEEDED"
        else:
            checks = [_pair(a, b, library, cache, relations)
                      for a, b in mesh_targets]
            mesh_checks += len(checks)
            site["mesh_checks"] = checks
            if any(c["status"] == "MESH_INTERSECTION_REVIEW_REQUIRED" for c in checks):
                site["status"] = "BLOCKED_MESH_INTERSECTION_REQUIRES_REVIEW"
            elif any(c["status"] == "UNKNOWN_GEOMETRY_UNAVAILABLE" for c in checks):
                site["status"] = "UNKNOWN_INCOMPLETE_LDRAW_GEOMETRY"
            else:
                # Even a clear shaft has no checked cover-to-post clutch and
                # DOES NOT solve the pre-existing opposite-slope ridge seam.
                site["status"] = "POSSIBLE_POST_GEOMETRY_CLUTCH_UNKNOWN"
        results.append(site)
    return {
        "building_id": model.building_id,
        "approach": "STUD_ANCHORED_INTERIOR_RIDGE_POST_UNDER_TRANSVERSE_COVER",
        "roof_pattern": proposals["roof_pattern"],
        "candidate_cover_count": proposals["proposed_count"],
        "sites_checked": len(results),
        "unresolved_cover_sites": proposals.get("unresolved_count", 0),
        "statuses": dict(sorted(Counter(s["status"] for s in results).items())),
        "sites": results,
        "mesh_pairs_checked": mesh_checks,
        "model_mutated": False,
        "original_part_count": len(model.parts),
        "physical_certification": "NOT_CERTIFIED",
        "limitations": (
            "No slope was moved. Post-to-cover underside clutch, two-sided "
            "cover-to-slope clutch, baseline slope collision, strength/load "
            "capacity, full roof clearance and insertion sequence remain "
            "unverified. A ridge post does not by itself make a solid roof."
        ),
    }
