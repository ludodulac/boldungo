"""Bounded, non-mutating roof-seam spacing experiment for arbitrary gables.

Probe how moving ONE opposing top-course slope changes local 3-D mesh
interference and whether a transverse ridge tile is still positionable.
This is a *local experiment only*: other slope courses, wall supports,
roof silhouette and every remaining brick require separate checks.

No part from the canonical BrickModel is changed or certified.
"""
from __future__ import annotations

from copy import copy

from lego_geometry_engine import LDrawLibrary

from .brick_model import BrickModelPart
from .ridge_bridge_planner_065 import propose_ridge_bridges
from .ridge_proposal_3d_066 import _pair
from .roof_ridge_diagnostics import _studs_documented
from .roof import create_m0_roof_catalog


def _shifted(part, axis: str, offset: int):
    cloned = copy(part)
    setattr(cloned, "x_studs" if axis == "x" else "y_studs",
            getattr(part, "x_studs" if axis == "x" else "y_studs") + offset)
    # Use a fresh instance ID so geometry transforms cannot be cached across
    # differing experimental coordinates.
    cloned.placement_id = f"EXPERIMENT-{part.placement_id}-{offset:+d}"
    return cloned


def _bridge_for_rows(negative, positive, reference_tile, catalog):
    """Position a tile over two real common longitudinal exposed-stud cells."""
    if negative.rotation_quarter_turns % 2 != positive.rotation_quarter_turns % 2:
        return None, "DIFFERENT_RUN_AXES"
    axis = "x" if negative.rotation_quarter_turns % 2 == 0 else "y"
    n_studs, p_studs = _studs_documented(negative), _studs_documented(positive)
    if n_studs is None or p_studs is None:
        return None, "UNDOCUMENTED_SLOPE_STUDS"
    n_z, p_z = {q[2] for q in n_studs}, {q[2] for q in p_studs}
    if n_z != p_z or len(n_z) != 1:
        return None, "DIFFERENT_STUD_PLANES"

    def cross_along(studs):
        return {(x if axis == "x" else y, y if axis == "x" else x)
                for x, y, _ in studs}
    n_xy, p_xy = cross_along(n_studs), cross_along(p_studs)
    n_cross, p_cross = {v[0] for v in n_xy}, {v[0] for v in p_xy}
    if len(n_cross) != 1 or len(p_cross) != 1:
        return None, "AMBIGUOUS_TOP_STUD_ROWS"
    nc, pc = next(iter(n_cross)), next(iter(p_cross))
    width = abs(nc - pc) + 1
    if not 2 <= width <= 4:
        return None, "NO_SUPPORTED_2_TO_4_WIDE_TILE"
    alongs = sorted({v[1] for v in n_xy} & {v[1] for v in p_xy})
    ref_along = reference_tile["y_studs"] if axis == "x" else reference_tile["x_studs"]
    if ref_along not in alongs or ref_along + 1 not in alongs:
        return None, "TWO_ALONG_STUDS_NOT_ALIGNED"
    part_id = f"TILE_2X{width}"
    try:
        catalog.get(part_id)
    except KeyError:
        return None, "RIDGE_PART_NOT_IN_CATALOG"
    across = min(nc, pc)
    x, y = (across, ref_along) if axis == "x" else (ref_along, across)
    ridge = BrickModelPart(
        placement_id="EXPERIMENTAL-SPACING-RIDGE",
        part_id=part_id, category="ridge_tile", component="roof",
        roof_side="ridge", x_studs=x, y_studs=y,
        z_plates=next(iter(n_z)), rotation_quarter_turns=1 if axis == "x" else 0,
    )
    return ridge, None


def probe_ridge_seam_offsets(model, library: LDrawLibrary, *,
                             proposal_index: int = 0,
                             max_offset: int = 4) -> dict:
    """Check at most 5 shifts, with a genuine LDraw mesh per local interface."""
    if not 0 <= max_offset <= 4:
        raise ValueError("max_offset must be between 0 and 4")
    proposals = propose_ridge_bridges(model, max_tiles=max(1, proposal_index + 1))
    tiles = proposals["proposed_tiles"]
    if proposal_index < 0:
        raise ValueError("proposal_index must be non-negative")
    if proposal_index >= len(tiles):
        return {
            "building_id": model.building_id,
            "status": "NO_PROPOSAL_AT_INDEX",
            "offsets": [], "model_mutated": False,
            "physical_certification": "NOT_CERTIFIED",
        }
    tile = tiles[proposal_index]
    axis = "x" if tile["rotation_quarter_turns"] == 1 else "y"
    catalog = create_m0_roof_catalog()
    ridge_at = tile["z_plates"]

    # Only the exact documented top stud rows under the proposed tile.
    required = {
        (x, y, ridge_at)
        for x in range(tile["x_studs"], tile["x_studs"] + (3 if axis == "x" else 2))
        for y in range(tile["y_studs"], tile["y_studs"] + (2 if axis == "x" else 3))
    }
    slope_candidates = {"negative": [], "positive": []}
    for part in model.parts:
        if part.component != "roof" or part.roof_side not in slope_candidates:
            continue
        if (_studs_documented(part) or set()).intersection(required):
            slope_candidates[part.roof_side].append(part)
    if any(len(slope_candidates[side]) != 1 for side in slope_candidates):
        return {
            "building_id": model.building_id, "status": "AMBIGUOUS_LOCAL_SLOPES",
            "candidate_ids": {k: [p.placement_id for p in v]
                              for k, v in slope_candidates.items()},
            "offsets": [], "model_mutated": False,
            "physical_certification": "NOT_CERTIFIED",
        }

    negative, positive = slope_candidates["negative"][0], slope_candidates["positive"][0]
    neg_pos = negative.x_studs if axis == "x" else negative.y_studs
    pos_pos = positive.x_studs if axis == "x" else positive.y_studs
    sign = 1 if pos_pos > neg_pos else -1 if pos_pos < neg_pos else 0
    if not sign:
        return {
            "building_id": model.building_id, "status": "AMBIGUOUS_SHIFT_DIRECTION",
            "offsets": [], "model_mutated": False,
            "physical_certification": "NOT_CERTIFIED",
        }

    checks = []
    # Outer positive slope course, if present, is required context; moving
    # only the highest course can break its existing nominal attachments.
    previous = sorted([
        part for part in model.parts
        if part.component == "roof" and part.roof_side == "positive"
        and part.z_plates < positive.z_plates
        and part.rotation_quarter_turns % 2 == positive.rotation_quarter_turns % 2
        and (_studs_documented(part) or set())
        and ((part.y_studs == positive.y_studs) if axis == "x"
             else (part.x_studs == positive.x_studs))
    ], key=lambda p: (-p.z_plates, p.placement_id))[:1]

    for amount in range(max_offset + 1):
        moving = _shifted(positive, axis, sign * amount)
        cache = {}
        slope_pair = _pair(negative, moving, library, cache)
        ridge, reason = _bridge_for_rows(negative, moving, tile, catalog)
        current = {
            "positive_roof_shift_studs": sign * amount,
            "positive_original_id": positive.placement_id,
            "negative_original_id": negative.placement_id,
            "slopes_mesh": slope_pair,
            "bridge_candidate": None,
            "tile_to_slopes": [],
            "previous_positive_course": [_pair(moving, p, library, cache) for p in previous],
            "physical_certification": "NOT_CERTIFIED",
        }
        if ridge is not None:
            current["bridge_candidate"] = {
                "part_id": ridge.part_id,
                "x_studs": ridge.x_studs,
                "y_studs": ridge.y_studs,
                "z_plates": ridge.z_plates,
                "rotation_quarter_turns": ridge.rotation_quarter_turns,
                "status": "TWO_SIDE_STUD_PROJECTION_ONLY",
            }
            current["tile_to_slopes"] = [
                _pair(ridge, negative, library, cache),
                _pair(ridge, moving, library, cache),
            ]
        else:
            current["bridge_unavailable_reason"] = reason
        checks.append(current)

    return {
        "building_id": model.building_id,
        "status": "LOCAL_EXPERIMENT_ONLY",
        "base_pair": [negative.placement_id, positive.placement_id],
        "shift_axis": axis,
        "previous_course_ids": [p.placement_id for p in previous],
        "offsets": checks,
        "model_mutated": False,
        "physical_certification": "NOT_CERTIFIED",
        "limitations": (
            "Only one uppermost piece and a sample of its adjacent course are "
            "considered. Even collision-free 3-D meshes would not prove actual "
            "LEGO clutch, full-house wall support, all adjacent pieces, roof "
            "silhouette, or the vertical insertion path. Never auto-apply shifts."
        ),
    }
