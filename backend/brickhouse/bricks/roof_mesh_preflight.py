"""Bounded LDraw-mesh preflight on candidate roof-to-roof interfaces.

For any BrickModel, discover roof pairs by nominal XY footprint overlap.
Inspect at most max_pairs with the existing LDraw geometry engine.
This is a diagnostic: mesh intersections are not automatically impossible
LEGO joints (nominal studs may intersect on legal clutch interfaces), and
mesh separation/contact alone never certifies an assembled, stable roof.

The checker is deliberately bounded to avoid long-running all-pairs audits.
Missing LDraw primitives remain UNKNOWN, not a clean geometry verdict.
"""
from __future__ import annotations

from collections import defaultdict

from lego_geometry_engine import LDrawLibrary, Relation, check_collision

from .geometry_adapter import brick_model_part_to_instance
from .roof_ridge_diagnostics import _footprint
from .roof import create_m0_roof_catalog


def _kind(a, b) -> str:
    sides = {a.roof_side, b.roof_side}
    if sides == {"negative", "positive"}:
        return "OPPOSING_SLOPES"
    if "ridge" in sides and len(sides) > 1:
        return "SLOPE_TO_RIDGE"
    return "ADJACENT_ROOF_PIECES"


def candidate_roof_pairs(model, *, max_candidates: int = 20000):
    """Return prioritized candidate pairs and whether discovery was truncated.

    Nominal 2-D footprint sharing is only a coarse search index;
    even if discovered, a pair is not a proven 3-D contact or collision.
    """
    if max_candidates < 1:
        raise ValueError("max_candidates must be >= 1")
    catalog = create_m0_roof_catalog()
    roof = sorted((p for p in model.parts if p.component == "roof"),
                  key=lambda p: p.placement_id)
    cells = defaultdict(list)
    by_id = {p.placement_id: p for p in roof}
    unsupported_ids = []
    for p in roof:
        fp = _footprint(p, catalog)
        if fp is None:
            unsupported_ids.append(p.placement_id)
            continue
        for cell in fp:
            cells[cell].append(p.placement_id)

    unique = set()
    truncated = False
    for cell in sorted(cells):
        ids = sorted(cells[cell])
        for i, aid in enumerate(ids):
            for bid in ids[i + 1:]:
                pair = (aid, bid)
                if pair in unique:
                    continue
                if len(unique) == max_candidates:
                    truncated = True
                    break
                unique.add(pair)
            if truncated:
                break
        if truncated:
            break

    priority = {"OPPOSING_SLOPES": 0, "SLOPE_TO_RIDGE": 1, "ADJACENT_ROOF_PIECES": 2}
    result = sorted(unique, key=lambda ids: (
        priority[_kind(by_id[ids[0]], by_id[ids[1]])], ids,
    ))
    return ([(by_id[a], by_id[b], _kind(by_id[a], by_id[b]))
             for a, b in result], truncated, unsupported_ids)


def preflight_roof_mesh(model, library: LDrawLibrary, *,
                        max_pairs: int = 3, max_candidates: int = 20000) -> dict:
    """Inspect a bounded sample using real LDraw meshes, never certify clutch."""
    if max_pairs < 1:
        raise ValueError("max_pairs must be >= 1")
    candidates, truncated, unsupported = candidate_roof_pairs(
        model, max_candidates=max_candidates
    )
    checked = []
    cache = {}
    for a, b, kind in candidates[:max_pairs]:
        pair = {"part_a": a.placement_id, "part_b": b.placement_id, "kind": kind}
        try:
            for part in (a, b):
                if part.placement_id not in cache:
                    cache[part.placement_id] = brick_model_part_to_instance(part, library)
            ia, ib = cache[a.placement_id], cache[b.placement_id]
            # Cheap exact transformed mesh bounds first; avoid triangle tests
            # for clearly separated solids.
            if ia.bbox.relation(ib.bbox) is Relation.SEPARATED:
                relation = Relation.SEPARATED
            else:
                relation = check_collision(ia, ib)
            pair["mesh_relation"] = relation.value
            pair["status"] = {
                Relation.COLLISION: "MESH_INTERSECTION_REVIEW_REQUIRED",
                Relation.CONTACT: "MESH_SURFACE_CONTACT_REVIEW_REQUIRED",
                Relation.SEPARATED: "MESH_SEPARATED_IN_THIS_PLACEMENT",
            }[relation]
        except (FileNotFoundError, ValueError) as exc:
            pair["status"] = "UNKNOWN_GEOMETRY_UNAVAILABLE"
            pair["reason"] = f"{type(exc).__name__}: {exc}"
        checked.append(pair)

    return {
        "building_id": model.building_id,
        "roof_candidate_pairs_discovered": len(candidates),
        "discovery_truncated": truncated,
        "unsupported_roof_part_ids": unsupported,
        "pairs_examined": len(checked),
        "examination_truncated": truncated or len(candidates) > len(checked),
        "pairs": checked,
        "physical_certification": "NOT_CERTIFIED",
        "limitations": (
            "XY projection only discovers candidates. Real LDraw meshes are checked "
            "on a bounded sample; nominal connector interference may appear as "
            "mesh intersection. Neither assembly insertion, underside engagement "
            "nor structural stability is certified. Missing meshes are UNKNOWN."
        ),
    }
