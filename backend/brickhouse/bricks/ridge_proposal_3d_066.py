"""Non-destructive 3-D LDraw probe for proposed two-sided LEGO roof ridges.

Run after a candidate is selected by the generic 065 planner. Only checks
candidate versus the *actual* roof slopes whose documented top studs lie
under it, plus the two opposite slopes against one another.

Every mesh collision is evidence demanding review, not proof of physically
impossible LEGO engagement: the engine does not model legal clutch volumes
or certify mechanical strength. Tests and probes NEVER change a BrickModel.
"""
from __future__ import annotations

from pathlib import Path
import json

from lego_geometry_engine import LDrawLibrary, Relation, check_collision

from .brick_model import BrickModelPart
from .geometry_adapter import brick_model_part_to_instance
from .ridge_bridge_planner_065 import propose_ridge_bridges
from .roof_ridge_diagnostics import _footprint, _studs_documented
from .roof import create_m0_roof_catalog


def _pair(a, b, library: LDrawLibrary, cache: dict, relation_cache: dict | None = None) -> dict:
    ids = sorted((a.placement_id, b.placement_id))
    result = {"part_a": ids[0], "part_b": ids[1]}
    try:
        for part in (a, b):
            if part.placement_id not in cache:
                cache[part.placement_id] = brick_model_part_to_instance(part, library)
        first, second = cache[a.placement_id], cache[b.placement_id]
        # Identical LDraw meshes with identical world rotations and exactly
        # the same relative translation have identical intersection status
        # under a common rigid translation. This is a strict equivalence,
        # not a guess based on architectural symmetry.
        def rotation(instance):
            return tuple(tuple(round(v, 7) for v in row[:3])
                         for row in instance.transform.matrix[:3])

        delta = tuple(round(second.transform.matrix[i][3] -
                            first.transform.matrix[i][3], 7)
                      for i in range(3))
        equivalence_key = (first.definition.part_id, second.definition.part_id,
                           rotation(first), rotation(second), delta)
        if relation_cache is not None and equivalence_key in relation_cache:
            relation = relation_cache[equivalence_key]
            result["mesh_evidence_method"] = "EXACT_TRANSLATION_EQUIVALENCE"
        else:
            if first.bbox.relation(second.bbox) is Relation.SEPARATED:
                relation = Relation.SEPARATED
            else:
                relation = check_collision(first, second)
            if relation_cache is not None:
                relation_cache[equivalence_key] = relation
            result["mesh_evidence_method"] = "DIRECT_LDRAW_MESH"
        result["mesh_relation"] = relation.value
        result["status"] = {
            Relation.SEPARATED: "MESH_SEPARATED",
            Relation.CONTACT: "MESH_CONTACT_REVIEW_REQUIRED",
            Relation.COLLISION: "MESH_INTERSECTION_REVIEW_REQUIRED",
        }[relation]
    except (FileNotFoundError, ValueError) as exc:
        result.update(status="UNKNOWN_GEOMETRY_UNAVAILABLE",
                      reason=f"{type(exc).__name__}: {exc}")
    return result


def probe_proposed_ridges(model, library: LDrawLibrary, *,
                          max_tiles: int = 1) -> dict:
    """Probe up to max_tiles of 065's proposed ridge pieces using actual meshes.

    This is a sample, not a complete roof collision scan. Only top-stud
    aligned slopes enter the supporting pair check, and every skipped or
    unreviewed candidate remains explicitly unresolved.
    """
    if max_tiles < 1:
        raise ValueError("max_tiles must be >= 1")
    proposal = propose_ridge_bridges(model)
    selected = proposal["proposed_tiles"][:max_tiles]
    slopes = [p for p in model.parts if
              p.component == "roof" and
              p.roof_side in ("negative", "positive")]
    catalog = create_m0_roof_catalog()
    results = []
    cache = {}
    for n, tile in enumerate(selected):
        part = BrickModelPart(placement_id=f"EXPERIMENTAL-RIDGE-{n+1:04d}",
                              **{k: v for k, v in tile.items() if k in {
                                  "part_id", "category", "component", "roof_side",
                                  "x_studs", "y_studs", "z_plates",
                                  "rotation_quarter_turns"}})
        footprint = _footprint(part, catalog)
        supporting = {}
        for slope in slopes:
            if (_studs_documented(slope) or frozenset()).intersection(
                (x, y, part.z_plates) for x, y in footprint
            ):
                supporting.setdefault(slope.roof_side, []).append(slope)
        # Never hide ambiguous multi-slope source sites behind a neat count.
        candidates = sorted(
            [p for side in ("negative", "positive")
             for p in supporting.get(side, [])],
            key=lambda p: p.placement_id,
        )
        checks = [_pair(part, slope, library, cache) for slope in candidates]
        opposite = [
            _pair(a, b, library, cache)
            for a in supporting.get("negative", [])
            for b in supporting.get("positive", [])
        ]
        results.append({
            "tile": {
                "placement_id": part.placement_id, "part_id": part.part_id,
                "x_studs": part.x_studs, "y_studs": part.y_studs,
                "z_plates": part.z_plates,
                "rotation_quarter_turns": part.rotation_quarter_turns,
            },
            "supporting_slope_ids": {
                side: sorted(p.placement_id for p in supporting.get(side, []))
                for side in ("negative", "positive")
            },
            "tile_to_slopes": checks,
            "opposing_slopes": opposite,
            "underside_clutch": "UNKNOWN",
            "physical_certification": "NOT_CERTIFIED",
        })
    return {
        "building_id": model.building_id,
        "proposed_total": proposal["proposed_count"],
        "proposals_checked": len(results),
        "not_checked": proposal["proposed_count"] - len(results),
        "sample": results,
        "model_mutated": False,
        "physical_certification": "NOT_CERTIFIED",
        "scope": (
            "Official LDraw mesh probe for a bounded proposed-ridge sample. "
            "Mesh intersection alone does not demonstrate impossible clutch; "
            "mesh contact does not prove underside mating, insertion or strength. "
            "Opposite slope collision candidates may pre-exist before the bridge."
        ),
    }
