"""LEGO2-089 — Compile a conservative ROOF assembly dependency graph.

Applies to the ENTIRE 1890-piece GUIDED-004 and the 088 experimental redesign.
Unlike old ridge-only reports, tests every lower roof course, traces a
bottom-up nominal connection path back to the real masonry, and emits an
ordered construction dependency manifest.

This is not a clutch / friction / capacity certificate. A stud in a cavity
is *possible mating geometry*, not evidence of actual reliable attachment.
In particular the optional 30363 rear-cavity -60 LDU position is a
GEOMETRY HYPOTHESIS based on official 30363 wall/tube locations, NOT an
LDraw-reviewed clutch. Keep all physical acceptance gates closed.

No source or experimental BrickModel is mutated. No 075..081 mesh reruns.
"""
from __future__ import annotations

from collections import Counter, defaultdict

from .brick_model import BrickModel
from .catalog import standard_orthogonal_definitions
from .geometry_adapter import (
    CANONICAL_LDRAW_PARTS, LDU_PER_PLATE, LDU_PER_STUD, _slope_transform,
)
from .lego30363_mechanics_034 import _30363_BBOX_ONLY
from .roof_ridge_diagnostics import _studs_documented
from .support_chain import analyze_standard_brick_support_chain


_ALLOWED_CAVITY_Z = frozenset((-60, -20, 0))
# Local Z=-40 crosses the physical underside web and MUST NOT be accepted.
_CAVITY_LOCAL_X = frozenset((-10, 10))


def _underface_30363_stud_candidate(upper, x: int, y: int, z: int) -> str | None:
    """Return type of *nominal* 30363 underside stud-cell accommodation.

    Inverse of the existing canonical LDraw transform, against authentic
    30363 2-wide cavity: interior walls ±16, ends +6/-66, tube axes
    Z=-10/-30/-50 radius 8, stud radius 6, and a Z=-42..-34 cross-web.

    Review 060U documented exact local Z=-20/0 positions for one eave.
    The Z=-60 end-site is geometric inference; never promote as a proven
    clutch interface. -40 is rejected because of the intervening web.
    """
    if (upper.part_id != "BRICK_SLOPED_18_4X2"
            or upper.roof_side not in ("negative", "positive")
            or z != upper.z_plates):
        return None
    t = _slope_transform(
        upper, CANONICAL_LDRAW_PARTS[upper.part_id], _30363_BBOX_ONLY
    ).matrix
    world = ((x + 0.5) * LDU_PER_STUD,
             -z * LDU_PER_PLATE,
             (y + 0.5) * LDU_PER_STUD)
    delta = [world[i] - t[i][3] for i in range(3)]
    lx, ly, lz = [
        sum(t[i][j] * delta[i] for i in range(3))
        for j in range(3)
    ]
    if abs(ly - 24) > 1e-6:
        return None
    if not any(abs(lx - v) < 1e-6 for v in _CAVITY_LOCAL_X):
        return None
    if not any(abs(lz - v) < 1e-6 for v in _ALLOWED_CAVITY_Z):
        return None
    if not (
        16 - abs(lx) - 6 >= -1e-6
        and 6 - lz - 6 >= -1e-6
        and lz + 66 - 6 >= -1e-6
    ):
        return None
    # Tube circle in XZ: outside tube radius 8, stud radius 6.
    # Formula is conservative; no finite physical tolerance assumed.
    from math import hypot
    if min(hypot(lx, lz - tube_z) - 14
           for tube_z in (-10, -30, -50)) <= 1e-6:
        return None
    if -42 <= lz <= -34:
        return None
    return ("GEOMETRY_HYPOTHESIS_REAR_CAVITY"
            if abs(lz + 60) < 1e-6
            else "LDRAW_REVIEWED_FINAL_POSE_060U_GENERALIZED")


def _standard_top_studs(part, definitions):
    definition = definitions.get(part.part_id)
    if definition is None or part.category not in ("brick", "plate"):
        return ()
    width, length = definition.footprint(part.rotation_quarter_turns)
    return tuple((part.x_studs + dx, part.y_studs + dy,
                  part.z_plates + definition.height_plates)
                 for dx in range(width) for dy in range(length))


def compile_roof_connections_089(model: BrickModel, *, max_roof_slopes=2500) -> dict:
    """Build a future-installation dependency DAG, not a false build permit.

    For 30363, two distinct reviewed/hypothetical underside stud sites must
    link to existing GROUNDED lower parts for a provisional load-path.
    Data is orientation/translation invariant, not specific to this house.
    """
    if max_roof_slopes < 1:
        raise ValueError("max_roof_slopes must be positive")
    source = model.model_dump_json()
    roofs = sorted(
        [p for p in model.parts if p.component == "roof"
         and p.roof_side in ("negative", "positive")],
        key=lambda p: (p.z_plates, p.placement_id),
    )
    if len(roofs) > max_roof_slopes:
        raise ValueError("roof slope count exceeds bounded connector budget")

    by_id = {p.placement_id: p for p in model.parts}
    standard = standard_orthogonal_definitions()
    wall_report = analyze_standard_brick_support_chain(model)
    grounded_wall_ids = {node.placement_id for node in wall_report.nodes
                         if node.reaches_ground and node.placement_id in by_id
                         and by_id[node.placement_id].component == "wall"}
    # Every entry is a real exposed top stud, NOT inferred from a bbox.
    tops: dict[tuple[int, int, int], list[tuple[str, str]]] = defaultdict(list)
    for part in model.parts:
        if part.placement_id not in grounded_wall_ids:
            continue
        for site in _standard_top_studs(part, standard):
            tops[site].append((part.placement_id, "WALL_GROUNDED_MASONRY"))

    grounded_roof_ids = set()
    roof_rows = []
    install_after_walls = []
    for roof in roofs:
        connector_evidence: dict[str, set[tuple[int, int, int]]] = defaultdict(set)
        attached_to = defaultdict(set)
        # The underside contact screen only considers real documented
        # top studs of prior wall / lower slope placements.
        for dx in range(4 if roof.rotation_quarter_turns % 2 == 0 else 2):
            for dy in range(2 if roof.rotation_quarter_turns % 2 == 0 else 4):
                x, y = roof.x_studs + dx, roof.y_studs + dy
                site = (x, y, roof.z_plates)
                conclusion = _underface_30363_stud_candidate(roof, *site)
                if conclusion is None:
                    continue
                for lower_pid, provenance in tops.get(site, ()):
                    connector_evidence[conclusion].add(site)
                    attached_to[lower_pid].add((site, provenance, conclusion))
        grounded = set()
        for lower_pid, site_data in attached_to.items():
            if (lower_pid in grounded_wall_ids
                    or lower_pid in grounded_roof_ids):
                grounded.update(item[0] for item in site_data)
        sources = sorted(attached_to)
        status = (
            "NOMINAL_TWO_STUD_PATH_TO_WALL_ONLY"
            if len(grounded) >= 2
            else "ONE_STUD_NOT_A_STABLE_PATH"
            if grounded
            else "LOWER_STUDS_PRESENT_NO_GROUNDED_PATH"
            if sources
            else "NO_DOCUMENTED_LOWER_STUD_SITE"
        )
        if len(grounded) >= 2:
            grounded_roof_ids.add(roof.placement_id)
            install_after_walls.append(roof.placement_id)
        roof_rows.append({
            "placement_id": roof.placement_id,
            "roof_side": roof.roof_side,
            "z_plates": roof.z_plates,
            "status": status,
            "candidate_lower_ids": sources,
            "grounded_lower_ids": sorted(
                pid for pid in sources
                if pid in grounded_wall_ids or pid in grounded_roof_ids),
            "contact_site_count": len(
                set().union(*connector_evidence.values())
                if connector_evidence else set()),
            "grounded_site_count": len(grounded),
            "source_evidence": {
                k: [list(point) for point in sorted(points)]
                for k, points in sorted(connector_evidence.items())
            },
        })
        # Add slope top studs to index even when not ground-connected,
        # so unresolved lower courses remain distinguishable from no contact.
        try:
            real = _studs_documented(roof)
        except ValueError:
            real = None
        for point in real or ():
            tops[point].append((
                roof.placement_id,
                "30363_UPPER_STUDS_LDRAW_REVIEWED",
            ))

    # Final ridge caps: a piece is only a *nominal* two-sided cover when
    # BOTH slope sides have two studs under its footprint at the correct Z.
    caps = []
    for cap in sorted((p for p in model.parts
                       if p.component == "roof_support"
                       and p.part_id in ("BRICK_2X2", "BRICK_2X3")),
                      key=lambda p: p.placement_id):
        cap_sites = _standard_top_studs(cap, standard)
        # This computes the underside cells by footprint, not cap top plane.
        underside = {(x, y, cap.z_plates)
                     for x, y, _ in cap_sites}
        sides: dict[str, set[tuple[int,int,int]]] = defaultdict(set)
        supporters = defaultdict(set)
        for site in underside:
            for lower_pid, _ in tops.get(site, ()):
                lower = by_id.get(lower_pid)
                if (lower is None or lower.component != "roof"
                        or lower.roof_side not in ("negative", "positive")):
                    continue
                sides[lower.roof_side].add(site)
                supporters[lower.roof_side].add(lower_pid)
        cap_status = (
            "NOMINAL_TWO_SIDED_BRIDGE_TO_GROUNDED_SLOPES"
            if all(len(sides[s]) >= 2 for s in ("negative", "positive"))
            and all(supporters[s] <= grounded_roof_ids
                    for s in ("negative", "positive"))
            else "CAP_STUD_ALIGNMENT_ONLY_NO_COMPLETE_GROUND_PATH"
            if all(len(sides[s]) >= 2 for s in ("negative", "positive"))
            else "CAP_NOT_BRIDGING_TWO_FULL_STUD_ROWS"
        )
        caps.append({
            "placement_id": cap.placement_id,
            "part_id": cap.part_id,
            "z_plates": cap.z_plates,
            "status": cap_status,
            "slope_ids": {s: sorted(supporters[s])
                          for s in ("negative", "positive")},
            "stud_cells_by_side": {s: [list(v) for v in sorted(sides[s])]
                                  for s in ("negative", "positive")},
        })
    if model.model_dump_json() != source:
        raise AssertionError("MODEL_CHANGED_WHILE_REVIEWING_DEPENDENCIES")
    counts = dict(sorted(Counter(row["status"] for row in roof_rows).items()))
    cap_counts = dict(sorted(Counter(row["status"] for row in caps).items()))
    return {
        "building_id": model.building_id,
        "parts_total": len(model.parts),
        "roof_slope_parts": len(roofs),
        "roof_slope_grounded_nominal": len(grounded_roof_ids),
        "roof_slope_still_without_grounded_nominal_path": (
            len(roofs) - len(grounded_roof_ids)),
        "grounded_masonry_wall_ids": len(grounded_wall_ids),
        "nominal_roof_stud_rows": roof_rows,
        "nominal_roof_status_counts": counts,
        "ridge_caps": caps,
        "ridge_cap_status_counts": cap_counts,
        "nominal_slope_order_after_wall_assembly": install_after_walls,
        "design_gate": "HOUSE_CONSTRUCTION_DENIED_UNVERIFIED_MATING_AND_STABILITY",
        "missing_engineering_proofs": [
            "30363_UNDERSIDE_STUD_CLUTCH_PHYSICS",
            "30363_REAR_CAVITY_POSITION_EXTENSION_CONFIRMATION",
            "CAP_UNDERSIDE_TO_BOTH_SLOPE_CLUTCH",
            "FULL_ROOF_BODY_CLEARANCE_AND_INSERTION",
            "LOADED_FRAME_STIFFNESS_AND_FOUNDATION",
        ],
        "steps_mechanically_certified": 0,
        "source_model_mutated": False,
        "physical_certification": "NOT_CERTIFIED",
    }
