"""LEGO2-088: construct roof-ridge proposals ACROSS A WHOLE HOUSE from connector rules.

Unlike 087's detached 3-part demonstrator, this uses ACTUAL source roof
placements, preserves the original BrickModel, and creates a separately named
experimental copy ONLY for non-conflicting 2-sided, top-stud-aligned caps.

Fail-closed. A plan missing documented slope UNDERSIDE-to-structure connectors
cannot become a construction-ready house even if every ridge cap aligns.
No user physical test is requested or claimed. No historical mesh audits rerun.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any

from .brick_model import BrickModel, BrickModelPart
from .catalog import standard_orthogonal_definitions
from .connectors import _box
from .roof import create_m0_roof_catalog
from .roof_ridge_diagnostics import _footprint, _studs_documented


@dataclass(frozen=True)
class _SlopeStudRow:
    part: BrickModelPart
    z: int
    cross_axis: str
    cross: int
    along: tuple[int, int]


def _row(part: BrickModelPart) -> _SlopeStudRow | None:
    if (part.part_id != "BRICK_SLOPED_18_4X2"
            or part.component != "roof"
            or part.roof_side not in ("negative", "positive")):
        return None
    studs = _studs_documented(part)
    if studs is None or len(studs) != 2:
        return None
    z_levels = {z for _, _, z in studs}
    if len(z_levels) != 1:
        return None
    axis = "x" if part.rotation_quarter_turns % 2 == 0 else "y"
    cross_coords = {x if axis == "x" else y for x, y, z in studs}
    along = sorted(y if axis == "x" else x for x, y, z in studs)
    if len(cross_coords) != 1 or len(set(along)) != 2 or along[1] != along[0] + 1:
        return None
    return _SlopeStudRow(part=part, z=next(iter(z_levels)),
                         cross_axis=axis, cross=next(iter(cross_coords)),
                         along=(along[0], along[1]))


def _candidate_cap(a: _SlopeStudRow, b: _SlopeStudRow) -> BrickModelPart | None:
    if a.cross_axis != b.cross_axis or a.z != b.z or a.along != b.along:
        return None
    span = abs(a.cross - b.cross) + 1
    if span not in (2, 3):
        return None
    axis = a.cross_axis
    part_id = "BRICK_2X2" if span == 2 else "BRICK_2X3"
    rotate = 1 if axis == "x" and span == 3 else 0
    x = min(a.cross, b.cross) if axis == "x" else a.along[0]
    y = a.along[0] if axis == "x" else min(a.cross, b.cross)
    return BrickModelPart(
        placement_id=(
            f"EXPERIMENT-088-JOINT-{axis}-{a.z}-{x}-{y}-"
            f"{a.part.placement_id}-{b.part.placement_id}"
        ),
        part_id=part_id, category="brick", component="roof_support",
        x_studs=x, y_studs=y, z_plates=a.z,
        rotation_quarter_turns=rotate,
    )


def _box_overlap(a: tuple[int, ...], b: tuple[int, ...]) -> bool:
    return all(max(a[axis], b[axis]) < min(a[axis + 3], b[axis + 3])
               for axis in range(3))


def construct_rule_based_roof_experiment_088(
    canonical: BrickModel, *, max_roof_pairs: int = 1200,
) -> tuple[dict[str, Any], BrickModel | None]:
    """Evaluate matching 30363 roof rows, install safe-to-PROPOSE cap geometry.

    The resulting BrickModel is explicitly an EXPERIMENT, not construction
    output. Only replace an EXISTING ridge tile when its planar footprint
    is exactly identical; larger or offset covers are blocking, not guessed.
    Roof support, cap mating/force and non-orthogonal clearance still block
    the REAL construction readiness gate.
    """
    if not 1 <= max_roof_pairs <= 1200:
        raise ValueError("max_roof_pairs must be between 1 and 1200")
    source = canonical.model_dump_json()
    roofs = [p for p in canonical.parts if p.component == "roof"]
    slopes = [p for p in roofs if p.roof_side in ("negative", "positive")]
    ridge_tiles = [p for p in roofs if p.roof_side == "ridge"]
    row_by_group: dict[tuple, dict[str, list[_SlopeStudRow]]] = defaultdict(
        lambda: defaultdict(list))
    unreviewed_ids = []
    for slope in slopes:
        record = _row(slope)
        if record is None:
            unreviewed_ids.append(slope.placement_id)
            continue
        row_by_group[(record.z, record.cross_axis, record.along)][slope.roof_side].append(record)

    errors = []
    candidates = []
    accepted: list[dict] = []
    used_slope_ids: set[str] = set()
    claimed_removed_ridges: set[str] = set()
    approved_caps: list[BrickModelPart] = []
    aligned_slope_ids: set[str] = set()
    attempts = 0
    roof_catalog = create_m0_roof_catalog()
    for key, pair in sorted(row_by_group.items()):
        neg, pos = pair.get("negative", []), pair.get("positive", [])
        if not neg or not pos:
            continue
        if len(neg) != 1 or len(pos) != 1:
            errors.append({"key": list(key), "blocker": "AMBIGUOUS_MULTIPLE_SLOPE_ROWS"})
            continue
        a, b = neg[0], pos[0]
        cap = _candidate_cap(a, b)
        if cap is None:
            continue  # distant lower courses are NOT ridge rows
        attempts += 1
        if attempts > max_roof_pairs:
            errors.append({"blocker": "PAIR_BUDGET_REACHED", "limit": max_roof_pairs})
            break
        row = {
            "negative_slope": a.part.placement_id,
            "positive_slope": b.part.placement_id,
            "cap_part_id": cap.part_id,
            "cap_placement_id": cap.placement_id,
            "placement": {
                "x_studs": cap.x_studs, "y_studs": cap.y_studs,
                "z_plates": cap.z_plates,
                "rotation_quarter_turns": cap.rotation_quarter_turns,
            },
            "decision": None, "existing_ridge_to_replace": None,
            "studs_from_each_side": 2,
        }
        definition = standard_orthogonal_definitions()[cap.part_id]
        w, h = definition.footprint(cap.rotation_quarter_turns)
        cap_studs = {(cap.x_studs + x, cap.y_studs + y, cap.z_plates)
                     for x in range(w) for y in range(h)}
        neg_studs = _studs_documented(a.part) or set()
        pos_studs = _studs_documented(b.part) or set()
        if (neg_studs & pos_studs or len(neg_studs & cap_studs) != 2
                or len(pos_studs & cap_studs) != 2
                or a.part.placement_id in used_slope_ids
                or b.part.placement_id in used_slope_ids):
            row["decision"] = "BLOCKED_STUD_DUPLICATION_OR_REUSED_SLOPE"
            candidates.append(row)
            continue

        xy = {(cap.x_studs + x, cap.y_studs + y)
              for x in range(w) for y in range(h)}
        z = cap.z_plates
        # A 2-wide cap has thickness 3 plates. Any already placed, solid,
        # orthogonal part in its space blocks the candidate outright.
        cap_box = _box(cap)
        orthogonal_conflicts = sorted(
            p.placement_id for p in canonical.parts
            if p.component != "roof" and (other := _box(p)) is not None
            and cap_box is not None and _box_overlap(cap_box, other)
        )
        if orthogonal_conflicts:
            row["decision"] = "BLOCKED_EXISTING_SOLID_MATERIAL"
            row["blockers"] = orthogonal_conflicts[:12]
            candidates.append(row)
            continue

        ridge_overlap = []
        for tile in ridge_tiles:
            if tile.z_plates >= z + 3 or tile.z_plates + 1 <= z:
                continue
            cells = _footprint(tile, roof_catalog)
            if cells and cells & xy:
                ridge_overlap.append((tile, cells))
        if (len(ridge_overlap) > 1
                or any(cells != xy or tile.z_plates != z
                       for tile, cells in ridge_overlap)):
            row["decision"] = "BLOCKED_EXISTING_RIDGE_MUST_BE_REDESSIGNED"
            row["blockers"] = [tile.placement_id for tile, _ in ridge_overlap]
            candidates.append(row)
            continue
        replace_id = ridge_overlap[0][0].placement_id if ridge_overlap else None
        if replace_id in claimed_removed_ridges:
            row["decision"] = "BLOCKED_RIDGE_ALREADY_USED"
            candidates.append(row)
            continue
        if any(_box_overlap(cap_box, prev_box) for prev in approved_caps
               if (prev_box := _box(prev)) is not None):
            row["decision"] = "BLOCKED_CAPS_INTERSECT_EACH_OTHER"
            candidates.append(row)
            continue

        # In this test, the cap only shares an axis with these two roof
        # slopes and cannot be certified as load-carrying. NO automatic
        # promotion of undocumented underside or slope-to-wall bonds.
        row["decision"] = "EXPERIMENTAL_CAP_PLACEMENT_ONLY"
        row["existing_ridge_to_replace"] = replace_id
        if replace_id is not None:
            claimed_removed_ridges.add(replace_id)
        used_slope_ids.update((a.part.placement_id, b.part.placement_id))
        aligned_slope_ids.update((a.part.placement_id, b.part.placement_id))
        approved_caps.append(cap)
        accepted.append(row)
        candidates.append(row)

    if accepted:
        # The source's full 1890 placements are never edited in place.
        experiment_parts = [
            p.model_dump(mode="json")
            for p in canonical.parts
            if p.placement_id not in claimed_removed_ridges
        ] + [cap.model_dump(mode="json") for cap in approved_caps]
        experiment = BrickModel.model_validate({
            **canonical.model_dump(mode="json"),
            "building_id": canonical.building_id + "-EXPERIMENTAL-088",
            "parts": experiment_parts,
        })
    else:
        experiment = None

    if canonical.model_dump_json() != source:
        raise AssertionError("CANONICAL_BRICKMODEL_MUTATED")
    attempted_count = len(candidates)
    blockers = Counter(row["decision"] for row in candidates)
    roof_not_integrated = sorted(set(p.placement_id for p in slopes) - aligned_slope_ids)
    result = {
        "canonical_building_id": canonical.building_id,
        "original_part_count": len(canonical.parts),
        "original_roof_slope_count": len(slopes),
        "original_ridge_cover_count": len(ridge_tiles),
        "unreviewed_slope_count": len(unreviewed_ids),
        "unreviewed_slope_ids_sample": sorted(unreviewed_ids)[:15],
        "candidate_pairs_screened": attempts,
        "candidate_caps_proposed": len(accepted),
        "caps_replacing_identical_ridge_tiles": len(claimed_removed_ridges),
        "roof_slope_parts_nominally_joined": len(aligned_slope_ids),
        "roof_slope_parts_not_yet_joined": len(roof_not_integrated),
        "unjoined_roof_slope_ids_sample": roof_not_integrated[:20],
        "decision_counts": dict(sorted(blockers.items())),
        "candidates": candidates,
        "ambiguous_groups": errors[:100],
        "ambiguous_group_count": len(errors),
        "generated_experimental_part_count": len(experiment.parts) if experiment else None,
        "experimental_model_produced": experiment is not None,
        "construction_status": "BLOCKED_NOT_YET_BUILDABLE",
        "first_order_blockers": [
            "NO_DOCUMENTED_30363_UNDERSIDE_TO_HOST_OR_WALL_LOAD_PATH",
            "NO_DOCUMENTED_TWO_30363_TO_BRICK_CAP_CLUTCH",
            "UNVERIFIED_3D_BODY_CLEARANCE_AGAINST_ALL_ROOF_NEIGHBORS",
            "NO_APPROVED_WHOLE_HOUSE_INSERTION_ORDER",
            "NO_DEMONSTRATED_GLOBAL_MECHANICAL_STABILITY",
        ],
        "decision": (
            "EXPERIMENTAL_REDESIGN_CREATED_NOT_APPROVED_FOR_CONSTRUCTION"
            if accepted else "NO_FULL_HOUSE_RIDGE_REDIGN_ACCEPTED"
        ),
        "next_construction_choice": (
            "COMPLETE_DOCUMENTED_ROOF_CONNECTOR_AND_WALL_ANCHOR_DESIGN"
            if accepted else "SWITCH_TO_ANOTHER_DOCUMENTED_ROOF_TECHNIQUE"),
        "canonical_model_unchanged": True,
        "physical_certification": "NOT_CERTIFIED",
    }
    return result, experiment
