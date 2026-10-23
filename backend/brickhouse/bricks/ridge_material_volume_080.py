"""LEGO2-080: bounded, fail-closed MATERIAL volume review of ridge collisions.

079 already localized 24 crossing triangle witnesses per pair. This module
does NOT count crossings again. It asks a different question: can the LDraw
triangle soup be interpreted as a watertight, consistently oriented solid,
and if so, do interior points occupy both solids?

Even a shared interior witness is not automatically an INVALID LEGO joint:
interference-fit studs intentionally deform, and slope/1x1 connector domains
are not fully documented. Unknown clutch = UNKNOWN, not a false certificate.
"""
from __future__ import annotations

from collections import Counter
from math import sqrt

from lego_geometry_engine.core import (
    CONTACT_EPS, _ray_triangle_distance,
)


def _vertex(p):
    return tuple(round(float(x), 5) for x in p)


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def inspect_solid_shell(instance) -> dict:
    """Edge-incidence closure and oriented-shell gate, in WORLD LDraw units.

    LDraw flattened primitives may have T junctions, surface seams or open
    rims. The parity point-in-solid test is NOT sound without shell closure.
    """
    count = Counter()
    orientation = Counter()
    degenerate = 0
    signed_six_volume = 0.0
    for triangle in instance.triangles:
        p, q, r = map(_vertex, triangle)
        pq = tuple(q[i] - p[i] for i in range(3))
        pr = tuple(r[i] - p[i] for i in range(3))
        n = _cross(pq, pr)
        if _dot(n, n) < 1e-12:
            degenerate += 1
            continue
        signed_six_volume += _dot(p, _cross(q, r))
        for a, b in ((p, q), (q, r), (r, p)):
            key = (a, b) if a < b else (b, a)
            count[key] += 1
            orientation[key] += (1 if a < b else -1)

    boundary = sum(c == 1 for c in count.values())
    nonmanifold = sum(c > 2 for c in count.values())
    bad_orientation = sum(c == 2 and orientation[key] != 0
                          for key, c in count.items())
    # A non-zero signed volume does not alone prove closed geometry.
    closed = (
        len(instance.triangles) >= 4
        and degenerate == 0 and boundary == 0 and nonmanifold == 0
        and bad_orientation == 0 and abs(signed_six_volume) > 1e-6
    )
    return {
        "triangles": len(instance.triangles),
        "unique_edges": len(count),
        "open_boundary_edges": boundary,
        "nonmanifold_edges": nonmanifold,
        "inconsistent_winding_edges": bad_orientation,
        "degenerate_faces": degenerate,
        "nonzero_oriented_volume": abs(signed_six_volume) > 1e-6,
        "watertight_oriented_shell_gate": "VALID" if closed else "UNKNOWN",
        "volume_from_shell_provable": closed,
        "meaning": (
            "VALID here is ONLY a closed oriented triangle-shell property; "
            "LDraw is not certified as a real material or LEGO clutch model."
        ),
    }


_DIRECTIONS = ((1., 0.3713906763, 0.127831),
               (0.197, 1., 0.317),
               (0.227, 0.419, 1.))


def _inside_on_ray(point, triangles, direction):
    hits = sorted(
        d for tri in triangles
        if (d := _ray_triangle_distance(point, direction, tri)) is not None
    )
    # Same-distance hits can arise from shared edges. A near-tangent ray
    # should not be interpreted as a reliable inside/outside certificate.
    for i in range(1, len(hits)):
        if abs(hits[i] - hits[i-1]) <= CONTACT_EPS:
            return None
    return len(hits) % 2 == 1


def _strict_inside(point, triangles):
    votes = [_inside_on_ray(point, triangles, d) for d in _DIRECTIONS]
    valid = [x for x in votes if x is not None]
    if len(valid) < 2 or any(v != valid[0] for v in valid):
        return None
    return valid[0]


def inspect_shared_interior(first, second, *,
                            points_per_axis=5) -> dict:
    """Sample material occupancy WITHOUT counting triangles crossing again.

    A bounded lattice, not a continuous volumetric intersection proof.
    Crucially, it refuses parity on a NON-WATERTIGHT LDraw soup.
    """
    if not isinstance(points_per_axis, int) or not 1 <= points_per_axis <= 7:
        raise ValueError("points_per_axis must be in 1..7")
    a, b = inspect_solid_shell(first), inspect_solid_shell(second)
    answer = {
        "first_shell": a,
        "second_shell": b,
        "status": "UNKNOWN",
        "shared_material_sample": "UNKNOWN_UNTESTED",
        "samples_checked": 0,
        "interior_witness_ldu": None,
        "volume_proven": False,
        "geometric_collision_review": "REVIEW_REQUIRED",
        "connector_material_identity": "UNKNOWN_NO_FACE_TO_PRIMITIVE_PROVENANCE",
        "physical_clutch": "UNKNOWN_NOT_DOCUMENTED_FOR_ALL_THREE_PARTS",
        "physical_certification": "NOT_CERTIFIED",
        "model_mutated": False,
    }
    if not a["volume_from_shell_provable"] or not b["volume_from_shell_provable"]:
        answer["shared_material_sample"] = "UNKNOWN_UNCLOSED_OR_UNORIENTED_LDRAW_SURFACE"
        answer["reason"] = (
            "At least one official LDraw mesh is not a demonstrably closed "
            "consistently oriented shell; surface crossings cannot be "
            "interpreted as two rigid material volumes via ray parity."
        )
        return answer
    lo = [max(first.bbox.minimum[i], second.bbox.minimum[i]) for i in range(3)]
    hi = [min(first.bbox.maximum[i], second.bbox.maximum[i]) for i in range(3)]
    if any(hi[i] - lo[i] <= CONTACT_EPS for i in range(3)):
        answer["shared_material_sample"] = "NO_POSITIVE_COMMON_BBOX_VOLUME"
        answer["reason"] = "Bounding boxes do not share positive volume."
        return answer

    for ix in range(1, points_per_axis+1):
        for iy in range(1, points_per_axis+1):
            for iz in range(1, points_per_axis+1):
                p = tuple(
                    lo[i] + (hi[i] - lo[i]) * k / (points_per_axis+1)
                    for i, k in enumerate((ix, iy, iz))
                )
                answer["samples_checked"] += 1
                inside_a = _strict_inside(p, first.triangles)
                inside_b = _strict_inside(p, second.triangles)
                if inside_a is True and inside_b is True:
                    answer["interior_witness_ldu"] = [round(v, 4) for v in p]
                    answer["shared_material_sample"] = "BOTH_CLOSED_MESH_INTERIORS_CONTAIN_POINT"
                    answer["volume_proven"] = True  # only geometrical inside
                    answer["reason"] = (
                        "Closed triangulated interiors overlap at a sampled "
                        "point. Physical Lego clutch/tolerance and whether "
                        "those surfaces are solid walls are NOT established."
                    )
                    return answer
    answer["shared_material_sample"] = "NO_INTERIOR_POINT_ON_BOUNDED_LATTICE"
    answer["reason"] = (
        "Finite lattice found no point inside both shells. This does not "
        "prove absence of physical material overlap or mating."
    )
    return answer


def decide_physical_interference(volume_report, *,
                                 connector_provenance_available=False):
    """INVALID only with actual certified rigid-body / non-clutch evidence.

    LDraw mesh and inferred 3005 connectors are NOT this evidence. The
    caller may not assert unknown primitive labels are a rigid obstruction.
    """
    if volume_report["shared_material_sample"] == "BOTH_CLOSED_MESH_INTERIORS_CONTAIN_POINT":
        if connector_provenance_available:
            # Even with a source-identified face, friction tolerances are
            # unknown: report material conflict, not an impossible LEGO mate.
            return ("UNKNOWN", "POSITIVE_VOLUME_SAMPLE_BUT_FIT_TOLERANCES_UNKNOWN")
        return ("UNKNOWN", "MATERIAL_INTERIOR_WITNESS_BUT_CONNECTOR_PROVENANCE_UNKNOWN")
    if volume_report["shared_material_sample"] == "UNKNOWN_UNCLOSED_OR_UNORIENTED_LDRAW_SURFACE":
        return ("UNKNOWN", "OPEN_LDRAW_SHELL_PREVENTS_MATERIAL_OCCUPANCY_PROOF")
    return ("UNKNOWN", "FINITE_VOLUME_SAMPLE_CANNOT_CERTIFY_INTERFERENCE_OR_CLUTCH")
