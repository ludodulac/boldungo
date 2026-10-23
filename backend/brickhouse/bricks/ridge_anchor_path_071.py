"""LEGO2-071: conservative existing-wall anchor path for proposed ridge posts.

The preexisting wall support-chain graph finds *nominal* stud-plane overlaps,
not verified connectors. This adapter follows only edges independently
documented VALID by connectors.validate_connection, down to global z=0.

Roof supports and glazed frames are not silently promoted to load-bearing
wall chains. Even a fully traced route is NOT a foundation or strength proof.
"""
from __future__ import annotations

from functools import lru_cache

from .connectors import validate_connection
from .support_chain import analyze_standard_brick_support_chain


def trace_documented_wall_anchor(model, host, *, support_report=None) -> dict:
    """Inspect one existing anchor without changing the model.

    A route to model z=0 means only a locally modeled stud connection path.
    No roof underside, ground/foundation, forces or assembly route is proved.
    """
    result = {
        "status": "UNKNOWN_NO_DOCUMENTED_WALL_LOAD_PATH",
        "anchor_id": host.placement_id,
        "route_base_to_anchor": [],
        "connector_status": "UNKNOWN",
        "ground_foundation": "UNKNOWN_NOT_CHECKED",
        "roof_and_lid_interfaces": "UNKNOWN_NOT_CHECKED",
        "mechanical_strength": "UNKNOWN_NOT_MEASURED",
        "physical_certification": "NOT_CERTIFIED",
    }
    if host.component != "wall" or host.category not in ("brick", "plate"):
        result["status"] = "UNKNOWN_HOST_OUTSIDE_WALL_SUPPORT_DOMAIN"
        return result

    report = support_report if support_report is not None else (
        analyze_standard_brick_support_chain(model)
    )
    by_id = {part.placement_id: part for part in model.parts}
    nodes = {node.placement_id: node for node in report.nodes}
    if host.placement_id not in nodes:
        result["status"] = "UNKNOWN_WALL_HOST_NOT_IN_SUPPORT_GRAPH"
        return result

    @lru_cache(maxsize=None)
    def route(part_id):
        node = nodes[part_id]
        # The project's global zero is an architectural datum only, NOT
        # automatically evidence of a mechanically secured foundation.
        if node.z_bottom_plates == 0:
            return (part_id,)
        for lower_id in node.supporters:
            lower = by_id.get(lower_id)
            upper = by_id[part_id]
            if lower is None or validate_connection(lower, upper).status != "VALID":
                continue
            lower_route = route(lower_id)
            if lower_route is not None:
                return (*lower_route, part_id)
        return None

    found = route(host.placement_id)
    if found is None:
        return result
    result.update({
        "status": "DOCUMENTED_NOMINAL_WALL_STUD_PATH_TO_Z0",
        "route_base_to_anchor": list(found),
        "connector_status": "VALID_NOMINAL_INTERFACES_ONLY",
    })
    return result
