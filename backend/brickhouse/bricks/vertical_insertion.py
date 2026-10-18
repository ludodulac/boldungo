"""060J: bounded vertical AABB insertion screening for existing BrickModel parts.

Reuses catalog-backed orthogonal_bounds and the positive-volume overlap test,
the same conservative +Z swept-volume concept used in 059B/059L. This is
GEOMETRY_ONLY and NEVER a physical insertion, stability, or clutch certificate.
"""
from __future__ import annotations

from dataclasses import replace
from typing import Sequence

from .brick_model import BrickModelPart
from .orthogonal_geometry import OrthogonalBounds, _overlap, orthogonal_bounds


def _intersects(a: OrthogonalBounds, b: OrthogonalBounds) -> bool:
    """Positive-volume overlap; merely touching the support plane is allowed."""
    return (
        _overlap(a.x0, a.x1, b.x0, b.x1)
        and _overlap(a.y0, a.y1, b.y0, b.y1)
        and _overlap(a.z0, a.z1, b.z0, b.z1)
    )


def _unverified_could_interfere(part: BrickModelPart, swept: OrthogonalBounds) -> bool:
    """Conservative exclusion for a *non-modelled* obstacle.

    Raw width/length/height metadata do not define the solid, in particular for
    sloped surfaces. They can only delimit a possible region, never prove clear
    space *inside* it. If size is unknown, the positive dimensions are unbounded
    (no optimistic assumption of a tiny brick).
    """
    if (part.x_studs >= swept.x1 or part.y_studs >= swept.y1
            or part.z_plates >= swept.z1):
        return False
    w = max(part.width_studs, part.length_studs) if (
        part.width_studs is not None and part.length_studs is not None
    ) else None
    return (
        (w is None or part.x_studs + w > swept.x0)
        and (w is None or part.y_studs + w > swept.y0)
        and (part.height_plates is None
             or part.z_plates + part.height_plates > swept.z0)
    )


def check_vertical_insertion(
    moving: BrickModelPart,
    installed: Sequence[BrickModelPart],
    *,
    rise_plates: int = 30,
    unordered_peers: Sequence[BrickModelPart] = (),
) -> dict:
    """Check ONLY the finite straight-down path from final z+rise to final z.

    'installed' means provably installed *before* the current step.
    'unordered_peers' means other pieces of the *same* notice step: they
    may or may not be installed, so any potentially interfering peer is
    UNKNOWN rather than treating a favorable within-step order as fact.
    """
    if type(rise_plates) is not int or rise_plates < 1:
        raise ValueError("RISE_PLATES_MUST_BE_POSITIVE_INTEGER")
    others = [*installed, *unordered_peers]
    ids = [p.placement_id for p in others]
    if moving.placement_id in ids or len(ids) != len(set(ids)):
        raise ValueError("DUPLICATE_OR_SELF_PLACEMENT")
    initial = [moving.x_studs, moving.y_studs, moving.z_plates + rise_plates]
    final = [moving.x_studs, moving.y_studs, moving.z_plates]
    base = {
        "placement_id": moving.placement_id,
        "initial_position": initial,
        "final_position": final,
        "direction": "VERTICAL_NEGATIVE_Z",
        "rise_plates": rise_plates,
        "scope": "BOUNDED_AABB_SWEEP_ONLY",
        "installed_ids": sorted(p.placement_id for p in installed),
        "unordered_same_step_ids": sorted(p.placement_id for p in unordered_peers),
        "blockers": [],
        "unknown_geometry": [],
        "ambiguous_same_step": [],
        "final_support_contacts": [],
        "physical_certification": "NOT_CERTIFIED",
        "access_from_outside": "NOT_TESTED",
        "stability": "NOT_TESTED",
        "manual_insertion": "NOT_TESTED",
    }
    final_bounds = orthogonal_bounds(moving)
    if final_bounds is None:
        return base | {"verdict": "UNKNOWN", "reason": "UNSUPPORTED_MOBILE_GEOMETRY"}
    swept = replace(final_bounds, z1=final_bounds.z1 + rise_plates)
    base["swept_bounds"] = [
        swept.x0, swept.y0, swept.z0, swept.x1, swept.y1, swept.z1,
    ]

    for part in installed:
        bounds = orthogonal_bounds(part)
        if bounds is None:
            if _unverified_could_interfere(part, swept):
                base["unknown_geometry"].append(part.placement_id)
            continue
        if _intersects(swept, bounds):
            base["blockers"].append(part.placement_id)
        elif (bounds.z1 == final_bounds.z0
              and _overlap(bounds.x0, bounds.x1, final_bounds.x0, final_bounds.x1)
              and _overlap(bounds.y0, bounds.y1, final_bounds.y0, final_bounds.y1)):
            base["final_support_contacts"].append(part.placement_id)

    for part in unordered_peers:
        bounds = orthogonal_bounds(part)
        if ((bounds is None and _unverified_could_interfere(part, swept))
                or (bounds is not None and _intersects(swept, bounds))):
            base["ambiguous_same_step"].append(part.placement_id)

    for key in ("blockers", "unknown_geometry", "ambiguous_same_step",
                "final_support_contacts"):
        base[key].sort()
    if base["blockers"]:
        verdict = "BLOCKED"
        reason = "INSTALLED_SOLID_INTERSECTS_FINITE_SWEEP"
    elif base["unknown_geometry"] or base["ambiguous_same_step"]:
        verdict = "UNKNOWN"
        reason = "UNVERIFIED_GEOMETRY_OR_WITHIN_STEP_ORDER"
    else:
        verdict = "GEOMETRY_CLEAR_ONLY"
        reason = "NO_INTERSECTION_IN_BOUNDED_KNOWN_GEOMETRY"
    return base | {"verdict": verdict, "reason": reason}


def audit_notice_vertical_insertion(
    model, notice, target_ids: Sequence[str], *, rise_plates: int = 30,
    from_above: bool = False, clearance_plates: int = 1,
) -> dict[str, dict]:
    """Replay actual completed notice *steps* without guessing intra-step order.

    A part from a later step is never treated as already installed. All parts
    from earlier steps are obstacles, not just the selected module or facade.
    """
    by_id = {p.placement_id: p for p in model.parts}
    if len(by_id) != len(model.parts):
        raise ValueError("DUPLICATE_MODEL_PLACEMENT")
    steps = sorted(notice.steps, key=lambda s: s.sequence)
    if len({s.sequence for s in steps}) != len(steps):
        raise ValueError("DUPLICATE_NOTICE_STEP")
    indexed = {}
    for step in steps:
        for pid in step.placement_ids:
            if pid not in by_id or pid in indexed:
                raise ValueError("INVALID_NOTICE_COVERAGE")
            indexed[pid] = step
    if set(indexed) != set(by_id):
        raise ValueError("INVALID_NOTICE_COVERAGE")
    if len(set(target_ids)) != len(target_ids) or any(pid not in indexed for pid in target_ids):
        raise ValueError("INVALID_TARGET_IDS")

    installed = []
    results = {}
    for step in steps:
        group = [by_id[pid] for pid in step.placement_ids]
        for part in group:
            if part.placement_id in target_ids:
                peers = [p for p in group if p.placement_id != part.placement_id]
                if from_above:
                    result = check_vertical_access_from_above(
                        part, installed, unordered_peers=peers,
                        clearance_plates=clearance_plates,
                    )
                else:
                    result = check_vertical_insertion(
                        part, installed, rise_plates=rise_plates,
                        unordered_peers=peers,
                    )
                results[part.placement_id] = result | {
                    "step_id": step.step_id,
                    "step_sequence": step.sequence,
                }
        installed.extend(group)
    return {pid: results[pid] for pid in target_ids}


def check_vertical_access_from_above(
    moving: BrickModelPart,
    installed: Sequence[BrickModelPart],
    *,
    clearance_plates: int = 1,
    unordered_peers: Sequence[BrickModelPart] = (),
) -> dict:
    """060L: top-down sweep starting *above* the partial model's known solids.

    Unlike 060J's arbitrary +30 plates, the start is determined by the upper
    face of every known installed orthogonal solid, and also by any same-step
    peer which *could* have been installed, plus a positive plate margin.
    Unmodelled solids are NEVER assigned fictional heights. A potentially
    interfering unknown part above the derived start makes access UNKNOWN.
    Calls the original 060J collision/ordering check; no second geometry engine.
    """
    if type(clearance_plates) is not int or clearance_plates <= 0:
        raise ValueError("CLEARANCE_PLATES_MUST_BE_POSITIVE_INTEGER")
    final_bounds = orthogonal_bounds(moving)
    if final_bounds is None:
        result = check_vertical_insertion(
            moving, installed, rise_plates=clearance_plates,
            unordered_peers=unordered_peers,
        )
        return result | {
            "origin_definition": "NOT_ESTABLISHED_UNSUPPORTED_MOVING_GEOMETRY",
            "known_installed_max_top_z": None,
            "known_same_step_max_top_z": None,
            "positive_margin_plates": clearance_plates,
            "access_from_outside": "UNKNOWN",
        }

    known_installed = [b for p in installed
                       if (b := orthogonal_bounds(p)) is not None]
    known_peers = [b for p in unordered_peers
                   if (b := orthogonal_bounds(p)) is not None]
    installed_ceiling = max((b.z1 for b in known_installed), default=None)
    peers_ceiling = max((b.z1 for b in known_peers), default=None)
    highest_known = max(
        final_bounds.z0, *(b.z1 for b in [*known_installed, *known_peers])
    )
    initial_bottom_z = highest_known + clearance_plates
    result = check_vertical_insertion(
        moving, installed, rise_plates=initial_bottom_z - final_bounds.z0,
        unordered_peers=unordered_peers,
    )
    result.update({
        "origin_definition": "ABOVE_PARTIAL_MODEL_KNOWN_ORTHOGONAL_ENVELOPE",
        "known_installed_max_top_z": installed_ceiling,
        "known_same_step_max_top_z": peers_ceiling,
        "known_installed_count": len(known_installed),
        "known_same_step_count": len(known_peers),
        "positive_margin_plates": clearance_plates,
        "origin_above_known_solids": True,
        "scope": "MODEL_UPPER_SPACE_VERTICAL_AABB_SWEEP_ONLY",
    })

    # In the exterior-from-above mode, an unmodelled obstacle whose *bottom*
    # starts above the calculated initial z still makes the upper corridor
    # unresolved. It is not safe to call such a source externally accessible.
    # Extend the *screening probe*, not the claimed origin, past the obstacle's
    # known bottom; do not invent its missing top height.
    swept_probe = replace(
        final_bounds,
        z1=final_bounds.z1 + result["rise_plates"],
    )
    unknown_above = []
    for group, key in (
        (installed, "unknown_geometry"),
        (unordered_peers, "ambiguous_same_step"),
    ):
        for part in group:
            if orthogonal_bounds(part) is not None:
                continue
            probe = replace(swept_probe, z1=max(swept_probe.z1, part.z_plates + 1))
            if _unverified_could_interfere(part, probe):
                if part.placement_id not in result[key]:
                    result[key].append(part.placement_id)
                unknown_above.append(part.placement_id)
        result[key].sort()

    result["unverified_upper_corridor_ids"] = sorted(set(unknown_above))
    if result["blockers"]:
        result["verdict"] = "BLOCKED"
        result["reason"] = "INSTALLED_SOLID_INTERSECTS_COMPLETE_TOP_SWEEP"
    elif result["unknown_geometry"] or result["ambiguous_same_step"]:
        result["verdict"] = "UNKNOWN"
        result["reason"] = "UNKNOWN_GEOMETRY_OR_UNORDERED_PEER_IN_UPPER_CORRIDOR"
    else:
        result["verdict"] = "GEOMETRY_CLEAR_ONLY"
        result["reason"] = "COMPLETE_MODEL_TOP_VERTICAL_SWEEP_GEOMETRY_ONLY"
    result["access_from_outside"] = (
        "MODEL_TOP_APPROACH_GEOMETRY_ONLY"
        if result["verdict"] == "GEOMETRY_CLEAR_ONLY"
        else "NOT_PROVEN"
    )
    return result


def audit_notice_vertical_access_from_above(
    model, notice, target_ids: Sequence[str], *, clearance_plates: int = 1,
) -> dict[str, dict]:
    """060L: same real notice and same prior-step snapshots as 060J."""
    return audit_notice_vertical_insertion(
        model, notice, target_ids,
        from_above=True, clearance_plates=clearance_plates,
    )
