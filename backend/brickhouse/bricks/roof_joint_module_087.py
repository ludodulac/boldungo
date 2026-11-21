"""LEGO2-087: DESIGN an actual two-sided top-stud ridge bridge, not an audit.

Choose a 2x2 LEGO bridge (3003) over TWO opposing 30363 exposed top-stud
pairs. If the sides need extra clearance, a 1-stud seam uses a 2x3 bridge
(3002). Both roof slopes mechanically attach to a COMMON central piece
*only if* the physical clutch trial succeeds. They are separate experiments,
not changes to GUIDED-004 or a load-bearing roofing certificate.

Nominal coordinates follow the official-LDraw-reviewed 034 top-stud transform,
not eyeballed bounding boxes or fabricated underside connections.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .brick_model import BrickModel, BrickModelPart
from .roof_ridge_diagnostics import _studs_documented
from .catalog import standard_orthogonal_definitions

BridgeStatus = Literal[
    "NOMINAL_TWO_SIDED_STUD_ALIGNMENT_PHYSICAL_CLUTCH_UNTESTED",
    "REJECTED_STUD_OVERLAP",
    "REJECTED_STUD_PLANE_OR_FOOTPRINT",
    "REJECTED_UNSUPPORTED_GEOMETRY",
]


@dataclass(frozen=True)
class RidgeBridgeCandidate:
    model: BrickModel
    status: BridgeStatus
    seam_gap_studs: int
    roof_rotation: int
    documented_slope_top_studs: dict[str, tuple[tuple[int, int, int], ...]]
    bridge_receiver_cells: tuple[tuple[int, int, int], ...]
    nominal_engagement_studs: dict[str, tuple[tuple[int, int, int], ...]]

    def report(self) -> dict:
        return {
            "building_id": self.model.building_id,
            "technique": "TWO_OPPOSING_30363_TOP_STUD_ROWS_WITH_COMMON_2_WIDE_CAP",
            "roof_rotation": self.roof_rotation,
            "seam_gap_studs": self.seam_gap_studs,
            "part_count": len(self.model.parts),
            "bill_of_materials": (
                {"30363": 2,
                 "3003" if self.seam_gap_studs == 0 else "3002": 1}),
            "positive_side_roof_studs": {
                key: [list(v) for v in cells]
                for key, cells in self.documented_slope_top_studs.items()
            },
            "cap_underside_footprint_cells": [
                list(cell) for cell in self.bridge_receiver_cells],
            "joint_mating_proposals": {
                key: [list(v) for v in cells]
                for key, cells in self.nominal_engagement_studs.items()
            },
            "joint_plan": [
                {"lower_id": "LEFT_30363", "upper_id": "CENTRAL_CAP",
                 "proposed_interface": "EXPOSED_TWO_30363_STUDS_IN_3003_OR_3002_UNDERSIDE",
                 "physical_clutch": "NOT_TESTED"},
                {"lower_id": "RIGHT_30363", "upper_id": "CENTRAL_CAP",
                 "proposed_interface": "EXPOSED_TWO_30363_STUDS_IN_3003_OR_3002_UNDERSIDE",
                 "physical_clutch": "NOT_TESTED"},
            ],
            "nominal_geometry_status": self.status,
            "insertion": "TWO_SLOPES_FIRST__BRIDGE_STRAIGHT_DOWN__PHYSICAL_TRIAL_REQUIRED",
            "load_path": "NOT_PROVEN_TO_SUPPORTING_WALLS",
            "slope_underface_attachment": "NOT_PROVEN",
            "stability": "NOT_TESTED",
            "physical_certification": "NOT_CERTIFIED",
            "canonical_model_changed": False,
        }


def propose_two_slope_bridge_087(*, seam_gap_studs: int = 0,
                                 roof_rotation: int = 0,
                                 x_studs: int = 8, y_studs: int = 8,
                                 z_plates: int = 0) -> RidgeBridgeCandidate:
    """Propose precisely 3 existing LEGO parts in either roofing orientation.

    Nominal stud plane must cover all FOUR exposed 30363 top studs, two from
    each source slope, with ZERO duplicate stud material. Connection remains
    a physical hypothesis, not a VALID clutch evidence verdict.
    """
    if seam_gap_studs not in (0, 1):
        raise ValueError("only zero and one-stud seam gaps are supported")
    if roof_rotation not in (0, 1):
        raise ValueError("only the two documented roof orientations are supported")
    if min(x_studs, y_studs, z_plates) < 0:
        raise ValueError("experiment coordinates must be nonnegative")
    extra = 4 + seam_gap_studs
    pos_x = x_studs + (extra if roof_rotation == 0 else 0)
    pos_y = y_studs + (extra if roof_rotation == 1 else 0)
    parts = [
        BrickModelPart(
            placement_id="LEFT_30363", part_id="BRICK_SLOPED_18_4X2",
            category="roof_tile", component="roof", roof_side="negative",
            x_studs=x_studs, y_studs=y_studs, z_plates=z_plates,
            rotation_quarter_turns=roof_rotation,
        ),
        BrickModelPart(
            placement_id="RIGHT_30363", part_id="BRICK_SLOPED_18_4X2",
            category="roof_tile", component="roof", roof_side="positive",
            x_studs=pos_x, y_studs=pos_y, z_plates=z_plates,
            rotation_quarter_turns=roof_rotation,
        ),
    ]
    cap_id = "BRICK_2X2" if seam_gap_studs == 0 else "BRICK_2X3"
    cap_turn = 0 if seam_gap_studs == 0 else (1 if roof_rotation == 0 else 0)
    cap_x = x_studs + (3 if roof_rotation == 0 else 0)
    cap_y = y_studs + (3 if roof_rotation == 1 else 0)
    cap = BrickModelPart(
        placement_id="CENTRAL_CAP", part_id=cap_id,
        category="brick", component="roof_support",
        x_studs=cap_x, y_studs=cap_y, z_plates=z_plates + 3,
        rotation_quarter_turns=cap_turn,
    )
    parts.append(cap)
    model = BrickModel(
        building_id=f"EXPERIMENTAL-087-ROT{roof_rotation}-GAP{seam_gap_studs}",
        volume_id="roof-ridge-lab", width_studs=max(pos_x + 4, cap_x + 4),
        depth_studs=max(pos_y + 4, cap_y + 4),
        height_plates=z_plates + 10, parts=parts,
    )
    left, right = parts[:2]
    slots = {p.roof_side: tuple(sorted(_studs_documented(p) or ()))
             for p in (left, right)}
    cap_definition = standard_orthogonal_definitions()[cap_id]
    width, depth = cap_definition.footprint(cap.rotation_quarter_turns)
    receiver = tuple(sorted((cap.x_studs + dx, cap.y_studs + dy, cap.z_plates)
                            for dx in range(width) for dy in range(depth)))
    occupied = set(slots["negative"]) & set(slots["positive"])
    matches = {side: tuple(sorted(set(studs) & set(receiver)))
               for side, studs in slots.items()}
    if occupied:
        status: BridgeStatus = "REJECTED_STUD_OVERLAP"
    elif any(len(v) != 2 for v in slots.values()):
        status = "REJECTED_UNSUPPORTED_GEOMETRY"
    elif any(len(v) != 2 for v in matches.values()) or any(
            stud[2] != cap.z_plates for v in matches.values() for stud in v):
        status = "REJECTED_STUD_PLANE_OR_FOOTPRINT"
    else:
        status = "NOMINAL_TWO_SIDED_STUD_ALIGNMENT_PHYSICAL_CLUTCH_UNTESTED"
    return RidgeBridgeCandidate(
        model=model, status=status, seam_gap_studs=seam_gap_studs,
        roof_rotation=roof_rotation, documented_slope_top_studs=slots,
        bridge_receiver_cells=receiver, nominal_engagement_studs=matches,
    )


def screen_two_slope_ldraw_087(candidate: RidgeBridgeCandidate, library) -> dict:
    """Bounded 3-pair real-mesh review of a SYNTHESIZED pose, not old 080 audit.

    The slope-slope relation is decisive for *this new candidate*: reject an
    intersection between separate solid roof pieces. A cap-stud overlap can
    be an ordinary LEGO connector and remains a physical fit question.
    """
    from .ridge_proposal_3d_066 import _pair
    left, right, cap = candidate.model.parts
    cache = {}
    pairs = {
        "LEFT_TO_RIGHT": _pair(left, right, library, cache),
        "LEFT_TO_CAP": _pair(left, cap, library, cache),
        "RIGHT_TO_CAP": _pair(right, cap, library, cache),
    }
    seam = pairs["LEFT_TO_RIGHT"]["status"]
    if candidate.status != "NOMINAL_TWO_SIDED_STUD_ALIGNMENT_PHYSICAL_CLUTCH_UNTESTED":
        decision = "REJECTED_CONNECTOR_LAYOUT"
    elif seam == "MESH_INTERSECTION_REVIEW_REQUIRED":
        decision = "REJECTED_SLOPE_BODY_INTERSECTION"
    elif seam == "UNKNOWN_GEOMETRY_UNAVAILABLE":
        decision = "BLOCKED_MISSING_LDRAW_EVIDENCE"
    else:
        decision = "PROPOSE_PHYSICAL_THREE_PIECE_JOIN_TEST_NOT_CERTIFIED"
    return {
        "building_id": candidate.model.building_id,
        "pair_checks": pairs,
        "slope_to_slope": seam,
        "cap_joint_physical_clutch": "NOT_TESTED",
        "decision": decision,
        "physical_certification": "NOT_CERTIFIED",
    }


def choose_bounded_two_slope_trial_087(library=None) -> dict:
    """Try the 0-gap variant, then the 1-gap fallback, both orientations.

    No unbounded geometric search, no variant count beyond the four variants.
    An inconclusive/blocked candidate MUST not be recommended for purchase.
    """
    options = []
    for gap in (0, 1):
        for rotation in (0, 1):
            candidate = propose_two_slope_bridge_087(
                seam_gap_studs=gap, roof_rotation=rotation)
            row = candidate.report()
            if library is not None:
                row["ldraw"] = screen_two_slope_ldraw_087(candidate, library)
            options.append(row)
    available = [
        row for row in options
        if (row["nominal_geometry_status"]
            == "NOMINAL_TWO_SIDED_STUD_ALIGNMENT_PHYSICAL_CLUTCH_UNTESTED"
            and (library is None or row["ldraw"]["decision"]
                 == "PROPOSE_PHYSICAL_THREE_PIECE_JOIN_TEST_NOT_CERTIFIED"))
    ]
    recommended = next((r for r in available if r["roof_rotation"] == 0), None)
    return {
        "candidates_tested": len(options),
        "candidates": options,
        "recommended_experiment_id": recommended["building_id"] if recommended else None,
        "recommendation": (
            "THREE_PIECE_HAND_ASSEMBLY_ONLY__NO_FULL_ROOF_APPROVAL"
            if recommended else "NO_CANDIDATE_PASSED_SCOPED_GATES"
        ),
        "user_test": (
            "Hold the two opposite 30363 slopes next to each other. "
            "Try pressing the 3003 (or 3002 with a 1-stud seam) STRAIGHT "
            "DOWN onto the two upper stud pairs, without forcing. "
            "Verify both sides actually engage the SAME cap and can be "
            "removed without strain. Failure means reject this layout."
        ),
        "no_purchase_certification": True,
        "physical_certification": "NOT_CERTIFIED",
        "canonical_model_changed": False,
    }
