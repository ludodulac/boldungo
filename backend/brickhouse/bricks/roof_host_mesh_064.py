"""Roof-to-wall collision evidence for arbitrary canonical houses.

Complement to the 063 roof-to-roof mesh checker. The XY grid only
discovers candidates; real LDraw meshes are tested if supplied.
Never infer clutch strength from mesh proximity or intersections.
"""
from __future__ import annotations
from collections import defaultdict

from lego_geometry_engine import Relation, check_collision
from .catalog import standard_orthogonal_definitions
from .geometry_adapter import brick_model_part_to_instance
from .roof import create_m0_roof_catalog


def roof_host_candidates(model, *, max_candidates=20000):
    if max_candidates < 1:
        raise ValueError("max_candidates must be positive")
    walls = defaultdict(list)
    catalog = standard_orthogonal_definitions()
    unknown_hosts = []
    for part in model.parts:
        if part.component not in ("wall", "roof_support"):
            continue
        definition = catalog.get(part.part_id)
        if definition is None:
            unknown_hosts.append(part.placement_id)
            continue
        w, d = definition.footprint(part.rotation_quarter_turns)
        for x in range(part.x_studs, part.x_studs + w):
            for y in range(part.y_studs, part.y_studs + d):
                walls[x, y].append((part, part.z_plates,
                                    part.z_plates + definition.height_plates))

    pairs = {}
    truncated = False
    roof_catalog = create_m0_roof_catalog()
    for slope in sorted((p for p in model.parts if p.component == "roof"),
                        key=lambda p: p.placement_id):
        try:
            definition = roof_catalog.get(slope.part_id)
        except KeyError:
            continue
        w, d = definition.width_studs, definition.length_studs
        if slope.rotation_quarter_turns % 2:
            w, d = d, w
        z0, z1 = slope.z_plates, slope.z_plates + definition.height_plates
        for x in range(slope.x_studs, slope.x_studs + w):
            for y in range(slope.y_studs, slope.y_studs + d):
                for host, hz0, hz1 in walls.get((x, y), []):
                    if hz1 < z0 or z1 < hz0:
                        continue
                    key = (slope.placement_id, host.placement_id)
                    if key in pairs:
                        continue
                    if len(pairs) >= max_candidates:
                        truncated = True
                        break
                    pairs[key] = (slope, host)
                if truncated:
                    break
            if truncated:
                break
        if truncated:
            break
    return [pairs[key] for key in sorted(pairs)], truncated, sorted(unknown_hosts)


def check_roof_host_mesh(model, library, *, max_pairs=3,
                         max_candidates=20000):
    if max_pairs < 1:
        raise ValueError("max_pairs must be positive")
    pairs, discovery_truncated, unsupported = roof_host_candidates(
        model, max_candidates=max_candidates)
    cache = {}
    results = []
    for slope, host in pairs[:max_pairs]:
        entry = {"roof": slope.placement_id, "host": host.placement_id,
                 "connector_status": "UNKNOWN_UNVERIFIED_ROOF_UNDERSIDE"}
        if library is None:
            entry["status"] = "UNKNOWN_LDRAW_LIBRARY_NOT_PROVIDED"
        else:
            try:
                for part in (slope, host):
                    if part.placement_id not in cache:
                        cache[part.placement_id] = brick_model_part_to_instance(part, library)
                a, b = cache[slope.placement_id], cache[host.placement_id]
                relation = (Relation.SEPARATED
                            if a.bbox.relation(b.bbox) is Relation.SEPARATED
                            else check_collision(a, b))
                entry["mesh_relation"] = relation.value
                entry["status"] = {
                    Relation.COLLISION: "MESH_INTERSECTION_REVIEW_REQUIRED",
                    Relation.CONTACT: "MESH_CONTACT_CLUTCH_UNKNOWN",
                    Relation.SEPARATED: "MESH_SEPARATED_IN_THIS_PLACEMENT",
                }[relation]
            except (FileNotFoundError, ValueError) as exc:
                entry["status"] = "UNKNOWN_GEOMETRY_UNAVAILABLE"
                entry["reason"] = f"{type(exc).__name__}: {exc}"
        results.append(entry)
    return {
        "candidate_pairs": len(pairs),
        "candidate_discovery_truncated": discovery_truncated,
        "pairs_examined": len(results),
        "examination_truncated": discovery_truncated or len(pairs) > len(results),
        "unsupported_host_ids": unsupported[:12],
        "pairs": results,
        "physical_certification": "NOT_CERTIFIED",
    }
