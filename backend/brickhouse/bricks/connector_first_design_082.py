"""LEGO2-082: connector-FIRST design gate, before placing a candidate assembly.

A stud is not a certified clutch joint. Return REJECTED for unsupported design
interfaces rather than initiating another mesh investigation. This module is
additive, deterministic, house-independent and NEVER edits a BrickModel.

Coordinates are integer LEGO stud cells (x, y) and plate planes (z).
A tube AXIS on a cell boundary is deliberately not represented as an
individual mating stud; this matters for tile 26603's two underside tubes.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

from .brick_model import BrickModelPart
from .catalog import standard_orthogonal_definitions
from .connectors import validate_connection
from .roof import create_m0_roof_catalog
from .roof_ridge_diagnostics import _studs_documented

InterfaceKind = Literal["TOP_STUD", "TUBE_AXIS", "UNDERSIDE_ENVELOPE",
                        "BEARING_PROJECTION", "CLIP"]
Evidence = Literal["LDRAW_REVIEWED", "CATALOG_NOMINAL", "UNVERIFIED_ENVELOPE"]


@dataclass(frozen=True)
class InterfaceSite:
    kind: InterfaceKind
    position: tuple[int, int, int]
    outward_direction: tuple[int, int, int]
    insertion_direction: tuple[int, int, int]
    evidence: Evidence
    source: str


@dataclass(frozen=True)
class PartInterfaceProfile:
    placement_id: str
    part_id: str
    top_studs: tuple[InterfaceSite, ...]
    possible_receivers: tuple[InterfaceSite, ...]
    bearing_projection: tuple[InterfaceSite, ...]
    source_note: str

    @property
    def has_documented_mating_receiver(self) -> bool:
        # A catalogue bbox or a tube axis is NOT a tested clutch.
        return False


def describe_interfaces(part: BrickModelPart) -> PartInterfaceProfile:
    """Extract ONLY supported nominal interfaces from established sources.

    30363 top sites are derived from the existing LDraw-aligned transform.
    26603 tube axes follow the 073 LDraw study and are not certified mates.
    All other undersides are generic envelopes, not fabricated clutch sites.
    CLIP has no known approved implementation and is not advertised.
    """
    std = standard_orthogonal_definitions().get(part.part_id)
    roof = create_m0_roof_catalog()
    sites: list[InterfaceSite] = []
    receivers: list[InterfaceSite] = []
    bearing: list[InterfaceSite] = []
    note = "UNSUPPORTED_PART_ORIENTATION_NO_CONNECTOR_EVIDENCE"
    if std is not None and part.category in ("brick", "plate", "timber"):
        width, length = std.footprint(part.rotation_quarter_turns)
        top = part.z_plates + std.height_plates
        for dx in range(width):
            for dy in range(length):
                x, y = part.x_studs + dx, part.y_studs + dy
                sites.append(InterfaceSite(
                    "TOP_STUD", (x, y, top), (0, 0, 1), (0, 0, -1),
                    "CATALOG_NOMINAL", "catalog.standard_orthogonal_definitions"
                ))
                receivers.append(InterfaceSite(
                    "UNDERSIDE_ENVELOPE", (x, y, part.z_plates),
                    (0, 0, -1), (0, 0, -1),
                    "UNVERIFIED_ENVELOPE", "catalog.footprint_not_an_underside_clutch"
                ))
                bearing.append(InterfaceSite(
                    "BEARING_PROJECTION", (x, y, part.z_plates),
                    (0, 0, -1), (0, 0, -1),
                    "CATALOG_NOMINAL", "catalog.bottom_footprint_not_a_load_test"
                ))
        note = "STANDARD_GRID_STUDS; EXACT_MATE_REQUIRES_EXISTING_CONNECTOR_GATE"
    elif part.part_id == "BRICK_SLOPED_18_4X2":
        documented = _studs_documented(part)
        if documented is not None:
            for point in sorted(documented):
                sites.append(InterfaceSite(
                    "TOP_STUD", point, (0, 0, 1), (0, 0, -1),
                    "LDRAW_REVIEWED", "lego30363_mechanics_034.top_studs"
                ))
            note = "30363_TOP_STUDS_ONLY; SLOPE_UNDERSIDE_UNVERIFIED"
    elif part.part_id == "TILE_2X3" and part.roof_side == "ridge":
        # LDraw 26603s01.dat: two tube axes at grid BOUNDARIES, not
        # six individual stud-to-tube pairings. 073 verifies only a specific
        # 3002/26603 relative pose and still refuses to certify clutch.
        if part.rotation_quarter_turns % 2:
            centers = ((part.x_studs + u, part.y_studs + 1) for u in (1, 2))
        else:
            centers = ((part.x_studs + 1, part.y_studs + u) for u in (1, 2))
        for x, y in centers:
            receivers.append(InterfaceSite(
                "TUBE_AXIS", (x, y, part.z_plates),
                (0, 0, -1), (0, 0, -1),
                "LDRAW_REVIEWED", "ridge_tile_upper_interface_073:26603s01/stug4-1x2"
            ))
        note = "26603_TWO_TUBE_AXES; RIM_CLUTCH_AND_FORCE_UNVERIFIED"
    else:
        # Recognized roof families must NOT inherit rectangular mating rules.
        try:
            definition = roof.get(part.part_id)
        except KeyError:
            definition = None
        if definition is not None:
            note = "ROOF_FAMILY_CONNECTORS_NOT_DOCUMENTED; DESIGN_GATE_BLOCKED"
    return PartInterfaceProfile(
        placement_id=part.placement_id, part_id=part.part_id,
        top_studs=tuple(sites), possible_receivers=tuple(receivers),
        bearing_projection=tuple(bearing), source_note=note,
    )


def screen_connector_first_candidate(
    parts: Sequence[BrickModelPart],
    required_connections: Sequence[tuple[str, str]],
    *,
    max_parts: int = 50,
    max_connections: int = 100,
) -> dict:
    """Reject a design BEFORE integration if nominal joints lack evidence.

    Only a specific existing validate_connection(...) == VALID qualifies a
    required pair. That verdict denotes reviewed NOMINAL geometry only, not
    mechanical clutch. Duplicated exact top-stud cylinders are rejected even
    if a separate two-part test would otherwise look favorable.

    This is not a solid-volume/collision or insertion/path-of-load test.
    Those remain later independent gates for candidate designs only.
    """
    if not (1 <= len(parts) <= max_parts) or len(required_connections) > max_connections:
        raise ValueError("candidate outside bounded 1..max_parts / max_connections budget")
    by_id = {part.placement_id: part for part in parts}
    if len(by_id) != len(parts):
        raise ValueError("duplicate placement ids in experimental candidate")
    profiles = {p.placement_id: describe_interfaces(p) for p in parts}
    occupied: dict[tuple[int, int, int], list[str]] = {}
    for profile in profiles.values():
        for site in profile.top_studs:
            occupied.setdefault(site.position, []).append(profile.placement_id)

    duplicated = [
        {"cell": list(cell), "owners": sorted(owners)}
        for cell, owners in sorted(occupied.items())
        if len(set(owners)) > 1
    ]
    pairs = []
    blocked = []
    for lower_id, upper_id in required_connections:
        if lower_id not in by_id or upper_id not in by_id:
            verdict, detail = "REJECTED_UNKNOWN_PART_ID", "connection references missing placement"
        elif lower_id == upper_id:
            verdict, detail = "REJECTED_SAME_PART", "cannot connect a part to itself"
        else:
            connection = validate_connection(by_id[lower_id], by_id[upper_id])
            verdict = ("DOCUMENTED_NOMINAL_INTERFACE" if connection.status == "VALID"
                       else "REJECTED_INCOMPATIBLE_POSE" if connection.status == "INVALID"
                       else "REJECTED_UNDOCUMENTED_INTERFACE")
            detail = connection.reason
        row = {"lower_id": lower_id, "upper_id": upper_id,
               "design_gate": verdict, "evidence": detail}
        pairs.append(row)
        if verdict != "DOCUMENTED_NOMINAL_INTERFACE":
            blocked.append(row)

    documented_members = {member for item in pairs
                          if item["design_gate"] == "DOCUMENTED_NOMINAL_INTERFACE"
                          for member in (item["lower_id"], item["upper_id"])}
    isolated = sorted(set(by_id) - documented_members)
    return {
        "decision": ("REJECTED_DUPLICATE_STUD_MATERIAL" if duplicated
                     else "REJECTED_UNDOCUMENTED_OR_INCOMPATIBLE_JOINT" if blocked
                     else "REJECTED_NO_REQUIRED_CONNECTIONS" if not pairs
                     else "REJECTED_ISOLATED_PARTS" if isolated
                     else "ELIGIBLE_FOR_FURTHER_DESIGN_CHECKS"),
        "candidate_parts": len(parts),
        "nominal_connections_reviewed": len(pairs),
        "documented_nominal_connections": sum(
            item["design_gate"] == "DOCUMENTED_NOMINAL_INTERFACE" for item in pairs),
        "required_connection_checks": pairs,
        "duplicated_top_studs": duplicated,
        "blocked_connections": blocked,
        "parts_without_documented_nominal_connections": isolated,
        "interface_profiles": {
            key: {"top_stud_count": len(profile.top_studs),
                  "receiver_count": len(profile.possible_receivers),
                  "source": profile.source_note}
            for key, profile in profiles.items()
        },
        "missing_gates": ("NON_CONNECTOR_BODY_CLEARANCE", "CONTINUOUS_INSERTION",
                          "SUPPORTED_LOAD_PATH", "PHYSICAL_CLUTCH_AND_STIFFNESS"),
        "model_mutated": False,
        "physical_certification": "NOT_CERTIFIED",
    }
