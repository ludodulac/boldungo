"""LEGO2-088: replace an ENTIRE ridge-cover strip, not a tile at a time.

Real GUIDED-004 has 23 two-sided 30363 stud pairs obstructed by twelve existing
2x4/2x2 ridge tiles. Replacing one wide tile at a time is impossible: a wide
tile spans multiple two-stud rows. Solve this as a complete, conservative
coverage problem, using ONLY the already screened 088 candidates.

This creates a separately named, non-certified experimental house, never a
new canonical model, physical installation instruction or strength claim.
"""
from __future__ import annotations

from collections import Counter
from .brick_model import BrickModel, BrickModelPart
from .catalog import standard_orthogonal_definitions
from .connectors import _box
from .house_roof_rule_builder_088 import (
    _box_overlap, construct_rule_based_roof_experiment_088,
)
from .roof import create_m0_roof_catalog
from .roof_ridge_diagnostics import _footprint, _studs_documented


def _cells(part: BrickModelPart):
    definition = standard_orthogonal_definitions()[part.part_id]
    w, d = definition.footprint(part.rotation_quarter_turns)
    return {(part.x_studs + x, part.y_studs + y)
            for x in range(w) for y in range(d)}


def _reconstruct_candidate(row):
    p = row["placement"]
    return BrickModelPart(
        placement_id=row["cap_placement_id"],
        part_id=row["cap_part_id"],
        category="brick",
        component="roof_support",
        x_studs=p["x_studs"],
        y_studs=p["y_studs"],
        z_plates=p["z_plates"],
        rotation_quarter_turns=p["rotation_quarter_turns"],
    )


def retile_whole_ridge_088(
    source: BrickModel, *, max_candidates: int = 1200,
) -> tuple[dict, BrickModel | None]:
    """Re-tile complete covered ridge strips, preserving all unreviewed areas.

    All claimed source tiles must be covered by the union of NEW caps on the
    SAME connection plane, with no overlaps among the caps themselves. No
    fractional demolition of old tiles. Any unreviewed straddling tile
    blocks its entire local group instead of silently becoming a floating
    or missing piece.
    """
    before = source.model_dump_json()
    base, _ = construct_rule_based_roof_experiment_088(
        source, max_roof_pairs=max_candidates)
    original = {p.placement_id: p for p in source.parts}
    ridges = [p for p in source.parts
              if p.component == "roof" and p.roof_side == "ridge"]
    catalogue = create_m0_roof_catalog()
    proposals = []
    denied = []
    for row in base["candidates"]:
        if row["decision"] not in (
            "EXPERIMENTAL_CAP_PLACEMENT_ONLY",
            "BLOCKED_EXISTING_RIDGE_MUST_BE_REDESSIGNED",
        ):
            denied.append({"site": row["cap_placement_id"],
                           "reason": row["decision"]})
            continue
        cap = _reconstruct_candidate(row)
        neg, pos = original[row["negative_slope"]], original[row["positive_slope"]]
        a, b = set(_studs_documented(neg) or ()), set(_studs_documented(pos) or ())
        occupied = {(x, y, cap.z_plates) for x, y in _cells(cap)}
        if (len(a) != 2 or len(b) != 2 or a & b
                or len(a & occupied) != 2 or len(b & occupied) != 2):
            denied.append({"site": cap.placement_id,
                           "reason": "BLOCKED_INCOMPLETE_FOUR_STUD_ALIGNMENT"})
            continue
        assert not any(
            _box_overlap(_box(cap), other)
            for p in source.parts if p.component != "roof"
            if (other := _box(p)) is not None
        ), "base 088 geometric filter must have blocked orthogonal solid overlap"
        proposals.append(cap)

    proposals.sort(key=lambda p: (p.z_plates, p.x_studs, p.y_studs,
                                  p.placement_id))
    accepted = []
    for cap in proposals:
        rect = _box(cap)
        if any(_box_overlap(rect, _box(old)) for old in accepted):
            denied.append({"site": cap.placement_id,
                           "reason": "BLOCKED_OVERLAPPING_NEW_CAPS"})
        else:
            accepted.append(cap)

    # Fixed-point: dropping a rejected cap can expose a partial old tile;
    # then ALL caps touching that tile must be rejected. Terminates as the
    # set monotonically shrinks and is bounded by the proposed cap count.
    for _ in range(len(accepted) + 1):
        cells_by_z: dict[int, set[tuple[int,int]]] = {}
        for cap in accepted:
            cells_by_z.setdefault(cap.z_plates, set()).update(_cells(cap))
        covering_tiles = set()
        unreleasable = set()
        for tile in ridges:
            tile_fp = _footprint(tile, catalogue)
            if tile_fp is None:
                continue
            spans = [
                cap for cap in accepted
                if tile.z_plates < cap.z_plates + 3
                and tile.z_plates + 1 > cap.z_plates
                and tile_fp & _cells(cap)
            ]
            if not spans:
                continue
            if (
                all(cap.z_plates == tile.z_plates for cap in spans)
                and tile_fp <= cells_by_z.get(tile.z_plates, set())
            ):
                covering_tiles.add(tile.placement_id)
            else:
                unreleasable.add(tile.placement_id)
        if not unreleasable:
            break
        reject_caps = {
            cap.placement_id for cap in accepted
            if any(
                tile.placement_id in unreleasable
                and (_footprint(tile, catalogue) or frozenset()) & _cells(cap)
                and tile.z_plates < cap.z_plates + 3
                and tile.z_plates + 1 > cap.z_plates
                for tile in ridges
            )
        }
        if not reject_caps:
            raise AssertionError("unreleasable tile without conflicting cap")
        denied.extend({"site": pid,
                       "reason": "BLOCKED_UNCOVERED_OLD_RIDGE_STRIP"}
                      for pid in sorted(reject_caps))
        accepted = [cap for cap in accepted
                    if cap.placement_id not in reject_caps]
    else:
        raise AssertionError("ridge strip coverage did not converge")

    replaced_tiles = [
        tile.placement_id for tile in ridges
        if any(
            tile.z_plates == cap.z_plates
            and (_footprint(tile, catalogue) or frozenset()) & _cells(cap)
            for cap in accepted
        )
    ]
    # Recheck exact global tile coverage AFTER all rejected caps are removed.
    footprints = {}
    for cap in accepted:
        footprints.setdefault(cap.z_plates, set()).update(_cells(cap))
    for tid in replaced_tiles:
        tile = original[tid]
        if not (_footprint(tile, catalogue) or frozenset()) <= footprints[tile.z_plates]:
            raise AssertionError("partial tile removal forbidden")
    assert not (set(replaced_tiles) & {c.placement_id for c in accepted})
    proposal = None
    if accepted:
        replacement_set = set(replaced_tiles)
        new_parts = [
            p.model_dump(mode="json") for p in source.parts
            if p.placement_id not in replacement_set
        ] + [cap.model_dump(mode="json") for cap in accepted]
        proposal = BrickModel.model_validate({
            **source.model_dump(mode="json"),
            "building_id": source.building_id + "-EXPERIMENTAL-RIDGE-088",
            "parts": new_parts,
        })

    if source.model_dump_json() != before:
        raise AssertionError("SOURCE_MODEL_CHANGED")
    decision = {
        "stage": "WHOLE_RIDGE_STRIP_REPLACEMENT_NOT_PIECE_BY_PIECE",
        "canonical_part_count": len(source.parts),
        "original_sloped_roof_part_count": base["original_roof_slope_count"],
        "nominal_candidate_pairs_checked": base["candidate_pairs_screened"],
        "proposed_cap_count": len(accepted),
        "proposed_cap_placement_ids": sorted(cap.placement_id for cap in accepted),
        "replaced_old_ridge_tile_count": len(replaced_tiles),
        "replaced_old_ridge_tile_ids": sorted(replaced_tiles),
        "rejected_site_count": len(denied),
        "rejected_sites": denied[:100],
        "proposal_count_if_written": len(proposal.parts) if proposal else None,
        "delta_total": len(accepted) - len(replaced_tiles),
        "part_id_delta": (
            dict(Counter(p.part_id for p in proposal.parts)
                 - Counter(p.part_id for p in source.parts))
            if proposal else {}),
        "house_status": "EXPERIMENTAL_NOT_READY_FOR_BUILDING" if proposal
                        else "NO_VIABLE_RIDGE_REPLACEMENT",
        "cannot_certify_due_to": [
            "30363_UNDERSIDE_TO_WALL_OR_FERME_CONNECTOR_NOT_DOCUMENTED",
            "TWO_SLOPES_TO_COMMON_CAP_CLUTCH_NOT_FULLY_DOCUMENTED",
            "NONCONNECTOR_BODY_COLLISION_WITH_NEARBY_ROOF_NOT_CLEARED",
            "WHOLE_HOUSE_INSERTION_AND_STABILITY_NOT_DEMONSTRATED",
        ],
        "must_not_issue_final_construction_notice": True,
        "user_physical_test_requested": False,
        "canonical_intact": True,
        "physical_certification": "NOT_CERTIFIED",
    }
    return decision, proposal
