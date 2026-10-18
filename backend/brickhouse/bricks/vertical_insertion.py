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
                result = check_vertical_insertion(
                    part, installed, rise_plates=rise_plates,
                    unordered_peers=[p for p in group if p.placement_id != part.placement_id],
                )
                results[part.placement_id] = result | {
                    "step_id": step.step_id,
                    "step_sequence": step.sequence,
                }
        installed.extend(group)
    return {pid: results[pid] for pid in target_ids}
