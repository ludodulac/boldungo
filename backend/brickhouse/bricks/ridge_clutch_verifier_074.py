"""LEGO2-074: fail-closed mechanical fit gate for LEGO 3002 / tile 26603.

Checks the particular fully-aligned 2x3-on-2x3 connector proposal.
Reuses 073's exact 6-stud/2-tube locations and 066's LDraw collision engine.
A *discrete* insertion sweep is diagnostic, never proof of continuous
assembly, clutch force or realistic material interference. No automatic VALID.
"""
from __future__ import annotations

from .ridge_proposal_3d_066 import _pair
from .ridge_tile_upper_interface_073 import inspect_3002_26603_upper_interface


def validate_3002_26603_clutch(head, cover, library=None, *, surrounding=(),
                              lift_plates=(3, 2, 1, 0),
                              max_pair_checks=20) -> dict:
    """Return VALID / INVALID / UNKNOWN for the specified full-seat proposal.

    INVALID means a documented contradiction with the *specified* full-seat
    geometry (not that partial LEGO clutch in a different pose is impossible).
    UNKNOWN includes matching nominal geometry whenever real-world clutch,
    continuous insertion and manufacturer tolerances are unverified.

    This function does not mutate either placement, any house, or LDraw data.
    """
    if max_pair_checks < 1 or not lift_plates or len(lift_plates) > 12:
        raise ValueError("positive budget and 1..12 insertion steps required")
    if (any(type(step) is not int or step < 0 for step in lift_plates)
            or tuple(sorted(set(lift_plates), reverse=True)) != tuple(lift_plates)
            or lift_plates[-1] != 0):
        raise ValueError("lift_plates must be distinct descending nonnegative integers ending at 0")

    nominal = inspect_3002_26603_upper_interface(head, cover)
    result = {
        "head_id": head.placement_id,
        "cover_id": cover.placement_id,
        "status": "UNKNOWN",
        "reason": "PHYSICAL_CLUTCH_NOT_VERIFIED",
        "nominal_geometry": nominal["status"],
        "nominal_layout_status": "UNKNOWN",
        "mesh_at_seated_height": "UNKNOWN_NOT_CHECKED",
        "discrete_insertion_checks": [],
        "missing_or_skipped_checks": [],
        "checks_performed": 0,
        "insertion_path": "UNKNOWN_CONTINUOUS_INSERTION",
        "stud_tube_clutch": "UNKNOWN_MANUFACTURING_FIT",
        "load_transfer": "UNKNOWN_NOT_MEASURED",
        "physical_certification": "NOT_CERTIFIED",
        "model_mutated": False,
        "limitations": ("LDraw has nominal surfaces, not deformation/friction. "
                        "Mesh CONTACT/COLLISION cannot alone prove clutch or "
                        "rule out intentional stud-and-tube interference. "
                        "This scan only samples specified lifts and supplied "
                        "surroundings; full roof access remains UNKNOWN."),
    }
    if nominal["status"].startswith("REJECTED_"):
        result.update(status="INVALID",
                      reason="INCOMPATIBLE_FULL_SEAT_PLACEMENT",
                      nominal_layout_status="INVALID")
        return result
    if nominal["status"] != "NOMINAL_LDRAW_STUD_AND_TUBE_LAYOUT_ONLY":
        result["reason"] = "UNREVIEWED_PART_OR_ORIENTATION"
        return result
    result["nominal_layout_status"] = "VALID"
    # VALID above means only *layout*. It must never become the mechanical
    # status unless actual clutch engagement has independent evidence.
    if library is None:
        result["reason"] = "LDRAW_LIBRARY_NOT_PROVIDED"
        return result

    # Work on independent immutable-style Pydantic copies. A 2x3 tile is
    # stepped vertically down onto the six studs; no roof slope is moved.
    neighbors = [p for p in surrounding
                 if p.placement_id not in (head.placement_id, cover.placement_id)]
    if len({p.placement_id for p in neighbors}) != len(neighbors):
        result["reason"] = "AMBIGUOUS_DUPLICATE_SURROUNDING_IDS"
        return result
    cache, relation_cache = {}, {}
    budget = max_pair_checks
    for step in lift_plates:
        moved = cover.model_copy(update={
            "z_plates": cover.z_plates + step,
            "placement_id": f"EXPERIMENT-074-{cover.placement_id}-LIFT-{step}",
        })
        targets = [head, *neighbors]
        row = {"lift_plates": step, "pairs": [], "unchecked": 0}
        for target in targets:
            if budget <= 0:
                row["unchecked"] += 1
                result["missing_or_skipped_checks"].append(
                    {"lift_plates": step, "target": target.placement_id,
                     "reason": "PAIR_BUDGET_EXHAUSTED"})
                continue
            check = _pair(moved, target, library, cache, relation_cache)
            row["pairs"].append(check)
            budget -= 1
            result["checks_performed"] += 1
            if step == 0 and target.placement_id == head.placement_id:
                result["mesh_at_seated_height"] = check["status"]
        result["discrete_insertion_checks"].append(row)

    statuses = [c["status"]
                for row in result["discrete_insertion_checks"]
                for c in row["pairs"]]
    if result["missing_or_skipped_checks"]:
        result["reason"] = "INCOMPLETE_LDRAW_PAIR_BUDGET"
    elif any(s == "UNKNOWN_GEOMETRY_UNAVAILABLE" for s in statuses):
        result["reason"] = "INCOMPLETE_LDRAW_PART_GEOMETRY"
    elif any(s == "MESH_INTERSECTION_REVIEW_REQUIRED" for s in statuses):
        result["reason"] = "MESH_INTERFERENCE_NEEDS_CONNECTOR_AWARE_REVIEW"
    else:
        result["reason"] = "DISCRETE_MESH_SCREEN_DONE_PHYSICAL_CLUTCH_UNPROVEN"
    # Deliberately NO positive mechanical VALID based on a sampled
    # finite LDraw mesh, whether separated, contact or intersection.
    return result
