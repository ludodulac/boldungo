"""Conservative planning signals for future autonomous assembly ordering.

This module does not replace AssemblyPlan. It extracts only facts justified by
the current BrickModel: rectangular footprint overlap and direct vertical
support. Ergonomics, insertion paths and global stability are deliberately not
inferred from final placement geometry alone.
"""
from __future__ import annotations
from dataclasses import dataclass
import re
from .brick_model import BrickModel, BrickModelPart

@dataclass(frozen=True)
class PartFootprint:
    placement_id: str
    x0: int
    x1: int
    y0: int
    y1: int
    z0: int
    z1: int

def _dimensions(part: BrickModelPart) -> tuple[int, int, int]:
    match = re.search(r"_(\d+)X(\d+)(?:X(\d+))?(?:_|$)", part.part_id)
    if not match:
        raise ValueError(f"Cannot derive dimensions for {part.part_id!r}")
    width, depth = int(match.group(1)), int(match.group(2))
    if part.rotation_quarter_turns % 2:
        width, depth = depth, width
    if part.category in {"window_frame", "window_pane"}:
        height = int(match.group(3) or 1) * 3
    elif part.category in {"roof_tile", "ridge_tile"}:
        height = 1
    else:
        height = 3
    return width, depth, height

def footprint(part: BrickModelPart) -> PartFootprint:
    width, depth, height = _dimensions(part)
    return PartFootprint(part.placement_id, part.x_studs, part.x_studs + width,
                         part.y_studs, part.y_studs + depth,
                         part.z_plates, part.z_plates + height)

def _overlap_area(a: PartFootprint, b: PartFootprint) -> int:
    return max(0, min(a.x1, b.x1) - max(a.x0, b.x0)) * max(0, min(a.y1, b.y1) - max(a.y0, b.y0))

def direct_support_graph(model: BrickModel) -> dict[str, tuple[str, ...]]:
    """Map each non-roof placement to directly touching supports below it.

    Empty means no support proven in this limited scope, not impossible.
    Sloped roof geometry is intentionally excluded until it has its own
    evidence-backed contact model.
    """
    parts = [p for p in model.parts if p.category not in {"roof_tile", "ridge_tile"}]
    boxes = {p.placement_id: footprint(p) for p in parts}
    result = {}
    for part in parts:
        current = boxes[part.placement_id]
        result[part.placement_id] = tuple(sorted(
            other.placement_id for other in parts
            if other.placement_id != part.placement_id
            and boxes[other.placement_id].z1 == current.z0
            and _overlap_area(boxes[other.placement_id], current) > 0
        ))
    return result

def support_dependencies(model: BrickModel) -> dict[str, tuple[str, ...]]:
    """First safe dependency signal for a later Assembly Planner."""
    return direct_support_graph(model)


@dataclass(frozen=True)
class PlanningCandidate:
    placement_id: str
    z_plates: int
    support_ids: tuple[str, ...]
    support_count: int
    support_area: int
    grounded: bool

def planning_candidates(model: BrickModel, built_ids: set[str]) -> tuple[PlanningCandidate, ...]:
    """Return conservative next-placement candidates.

    A ground-level part is eligible directly. A higher non-roof part is eligible
    only when this analyser can prove at least one direct support and every
    direct support it relies on is already built. This is a prerequisite filter,
    not yet a complete ergonomic or stability score.
    """
    supports = direct_support_graph(model)
    parts = {p.placement_id: p for p in model.parts if p.category not in {"roof_tile", "ridge_tile"}}
    boxes = {pid: footprint(part) for pid, part in parts.items()}
    candidates = []
    for pid, part in parts.items():
        if pid in built_ids:
            continue
        support_ids = supports[pid]
        grounded = part.z_plates == 0
        if not grounded and (not support_ids or not set(support_ids).issubset(built_ids)):
            continue
        support_area = sum(_overlap_area(boxes[pid], boxes[sid]) for sid in support_ids)
        candidates.append(PlanningCandidate(
            placement_id=pid, z_plates=part.z_plates, support_ids=support_ids,
            support_count=len(support_ids), support_area=support_area, grounded=grounded,
        ))
    return tuple(sorted(candidates, key=lambda c: (c.z_plates, -c.support_area, c.placement_id)))


@dataclass(frozen=True)
class CandidateScore:
    placement_id: str
    score: int
    reasons: tuple[str, ...]

def score_candidates(candidates: tuple[PlanningCandidate, ...], model: BrickModel | None = None, built_ids: set[str] | None = None) -> tuple[CandidateScore, ...]:
    """Rank already-safe candidates using only evidence available in this slice.

    More supported footprint is preferred; lower courses receive a small
    continuity preference. No claim is made yet about fingers, insertion paths,
    global stability or visibility.
    """
    scored = []
    for candidate in candidates:
        score = candidate.support_area * 10 - candidate.z_plates
        reasons_list = [
            "grounded" if candidate.grounded else "direct-support-proven",
            f"support-area={candidate.support_area}",
            f"z={candidate.z_plates}",
        ]
        if model is not None:
            parts = {p.placement_id: p for p in model.parts}
            current = parts[candidate.placement_id]
            # Decorative/detail parts are kept late when an equally safe
            # structural candidate exists. This is a preference, never a
            # substitute for support evidence.
            if current.category == "facade_detail":
                score -= 1000
                reasons_list.append("fragile-detail-late")
        if model is not None and built_ids:
            parts = {p.placement_id: p for p in model.parts}
            current = parts[candidate.placement_id]
            built_parts = [parts[pid] for pid in built_ids if pid in parts]
            if built_parts:
                distance = min(
                    abs(current.x_studs - other.x_studs) + abs(current.y_studs - other.y_studs)
                    for other in built_parts
                )
                score -= distance
                reasons_list.append(f"spatial-distance={distance}")
        reasons = tuple(reasons_list)
        scored.append(CandidateScore(candidate.placement_id, score, reasons))
    return tuple(sorted(scored, key=lambda c: (-c.score, c.placement_id)))


@dataclass(frozen=True)
class PlannerStep:
    sequence: int
    placement_id: str
    score: int
    reasons: tuple[str, ...]

@dataclass(frozen=True)
class PlannerResult:
    steps: tuple[PlannerStep, ...]
    unresolved_ids: tuple[str, ...]
    initial_built_ids: tuple[str, ...] = ()

def plan_supported_non_roof_parts(model: BrickModel, initial_built_ids: set[str] | None = None) -> PlannerResult:
    """Build a deterministic conservative order for the currently proven scope.

    This experimental planner intentionally stops instead of guessing when no
    support-proven candidate remains. The existing AssemblyPlan is not changed.
    """
    eligible_ids = {
        p.placement_id for p in model.parts
        if p.category not in {"roof_tile", "ridge_tile"}
    }
    built: set[str] = set(initial_built_ids or ()) & eligible_ids
    steps: list[PlannerStep] = []
    while built != eligible_ids:
        ranked = score_candidates(planning_candidates(model, built), model, built)
        if not ranked:
            break
        chosen = ranked[0]
        built.add(chosen.placement_id)
        steps.append(PlannerStep(len(steps) + 1, chosen.placement_id, chosen.score, chosen.reasons))
    return PlannerResult(
        steps=tuple(steps),
        unresolved_ids=tuple(sorted(eligible_ids - built)),
        initial_built_ids=tuple(sorted(set(initial_built_ids or ()) & eligible_ids)),
    )


def unresolved_reasons(model: BrickModel, result: PlannerResult) -> dict[str, str]:
    """Explain why this conservative planner stopped on each unresolved part."""
    supports = direct_support_graph(model)
    part_by_id = {p.placement_id: p for p in model.parts}
    built = set(result.initial_built_ids) | {step.placement_id for step in result.steps}
    reasons: dict[str, str] = {}
    for pid in result.unresolved_ids:
        part = part_by_id[pid]
        if part.category in {"roof_tile", "ridge_tile"}:
            reasons[pid] = "roof-slope-contact-not-modelled"
            continue
        support_ids = supports.get(pid, ())
        if not support_ids and part.z_plates > 0:
            reasons[pid] = "no-direct-support-proven"
        elif not set(support_ids).issubset(built):
            reasons[pid] = "support-dependency-unresolved"
        else:
            reasons[pid] = "planner-scope-unresolved"
    return reasons


@dataclass(frozen=True)
class PlannerAudit:
    eligible_count: int
    planned_count: int
    unresolved_count: int
    complete_for_scope: bool
    unresolved_by_reason: tuple[tuple[str, int], ...]

def audit_supported_non_roof_plan(model: BrickModel) -> PlannerAudit:
    """Summarize planner coverage without changing the production AssemblyPlan."""
    result = plan_supported_non_roof_parts(model)
    reasons = unresolved_reasons(model, result)
    counts: dict[str, int] = {}
    for reason in reasons.values():
        counts[reason] = counts.get(reason, 0) + 1
    eligible_count = sum(
        1 for p in model.parts if p.category not in {"roof_tile", "ridge_tile"}
    )
    return PlannerAudit(
        eligible_count=eligible_count,
        planned_count=len(result.steps),
        unresolved_count=len(result.unresolved_ids),
        complete_for_scope=not result.unresolved_ids,
        unresolved_by_reason=tuple(sorted(counts.items())),
    )


@dataclass(frozen=True)
class UnresolvedPlacement:
    placement_id: str
    part_id: str
    category: str
    component: str
    z_plates: int
    reason: str

def unresolved_placements(model: BrickModel, result: PlannerResult) -> tuple[UnresolvedPlacement, ...]:
    """Return concrete unresolved parts so real models can drive the next rule."""
    reasons = unresolved_reasons(model, result)
    parts = {p.placement_id: p for p in model.parts}
    return tuple(
        UnresolvedPlacement(
            placement_id=pid,
            part_id=parts[pid].part_id,
            category=parts[pid].category,
            component=parts[pid].component,
            z_plates=parts[pid].z_plates,
            reason=reasons[pid],
        )
        for pid in result.unresolved_ids
    )


def validate_planner_result(model: BrickModel, result: PlannerResult) -> tuple[str, ...]:
    """Replay planner output and report contract violations without guessing."""
    eligible = {
        p.placement_id for p in model.parts
        if p.category not in {"roof_tile", "ridge_tile"}
    }
    built = set(result.initial_built_ids)
    issues: list[str] = []
    seen: set[str] = set()
    supports = direct_support_graph(model)
    parts = {p.placement_id: p for p in model.parts}
    for step in result.steps:
        pid = step.placement_id
        if pid not in eligible:
            issues.append(f"out-of-scope:{pid}")
            continue
        if pid in seen or pid in result.initial_built_ids:
            issues.append(f"duplicate:{pid}")
            continue
        part = parts[pid]
        required = set(supports[pid])
        if part.z_plates > 0 and (not required or not required.issubset(built)):
            issues.append(f"support-order:{pid}")
        built.add(pid)
        seen.add(pid)
    expected_unresolved = eligible - built
    if expected_unresolved != set(result.unresolved_ids):
        issues.append("unresolved-set-mismatch")
    return tuple(issues)


@dataclass(frozen=True)
class PlannerMetrics:
    step_count: int
    spatial_travel: int
    facade_switches: int
    max_spatial_jump: int

def planner_metrics(model: BrickModel, result: PlannerResult) -> PlannerMetrics:
    """Measure simple human-facing continuity without changing validity."""
    parts = {p.placement_id: p for p in model.parts}
    ordered = [parts[s.placement_id] for s in result.steps if s.placement_id in parts]
    travel = 0
    switches = 0
    max_jump = 0
    for previous, current in zip(ordered, ordered[1:]):
        jump = abs(previous.x_studs-current.x_studs)+abs(previous.y_studs-current.y_studs)
        travel += jump
        max_jump = max(max_jump, jump)
        if previous.facade != current.facade:
            switches += 1
    return PlannerMetrics(len(ordered), travel, switches, max_jump)


@dataclass(frozen=True)
class PlannerQualityReport:
    valid: bool
    issues: tuple[str, ...]
    metrics: PlannerMetrics
    unresolved_count: int

def evaluate_planner_quality(model: BrickModel, result: PlannerResult) -> PlannerQualityReport:
    """One deterministic report for safety first, then human continuity."""
    issues = validate_planner_result(model, result)
    return PlannerQualityReport(
        valid=not issues,
        issues=issues,
        metrics=planner_metrics(model, result),
        unresolved_count=len(result.unresolved_ids),
    )
