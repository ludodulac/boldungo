"""LEGO2-083: bounded, reproducible ridge technique candidates and 30-part kit.

DESIGN before collision audits: reuse 082's connector-first gate. The preferred
trial has a DOCUMENTED NOMINAL orthogonal frame, with six 30363 cover pieces
left explicitly unapproved until the user attempts a physical fit.

Three genuinely different structural approaches are represented as separate
experimental BrickModels. None modifies the canonical house or supplies
a false physical-strength / complete-roof certification.
"""
from __future__ import annotations

from collections import Counter

from .brick_model import BrickModel, BrickModelPart
from .connector_first_design_082 import screen_connector_first_candidate

LDRAW_IDENTITIES = {
    "BRICK_1X1": "3005",
    "BRICK_1X8": "3008",
    "BRICK_2X3": "3002",
    "PLATE_1X6": "3666",
    "TILE_2X3": "26603",
    "BRICK_SLOPED_18_4X2": "30363",
}


def _std(name: str, part: str, x: int, y: int, z: int, turn=0) -> BrickModelPart:
    return BrickModelPart(
        placement_id=name, part_id=part, category="plate" if part.startswith("PLATE_") else "brick",
        component="roof_support", x_studs=x, y_studs=y, z_plates=z,
        rotation_quarter_turns=turn,
        **({"width_studs": 1, "length_studs": 6, "height_plates": 1}
           if part == "PLATE_1X6" else {}),
    )


def _roof(name: str, part: str, side: str, x: int, y: int,
          z: int, turn=0) -> BrickModelPart:
    return BrickModelPart(
        placement_id=name, part_id=part,
        category="ridge_tile" if side == "ridge" else "roof_tile",
        component="roof", roof_side=side,
        x_studs=x, y_studs=y, z_plates=z, rotation_quarter_turns=turn,
    )


def _house(name: str, pieces: list[BrickModelPart]) -> BrickModel:
    return BrickModel(building_id=name, volume_id="laboratory",
                      width_studs=16, depth_studs=16, height_plates=48,
                      parts=pieces)


def _central_post_cap() -> tuple[BrickModel, list[tuple[str, str]], list[str]]:
    """Old small-post and two 30363 roof faces: unsupported triple clutch."""
    parts = [
        _std("A-post", "BRICK_1X1", 4, 3, 0),
        _roof("A-left", "BRICK_SLOPED_18_4X2", "negative", 1, 2, 0),
        _roof("A-right", "BRICK_SLOPED_18_4X2", "positive", 4, 2, 0),
        _roof("A-cap", "TILE_2X3", "ridge", 3, 2, 3),
    ]
    joints = [("A-post", "A-cap"), ("A-left", "A-cap"), ("A-right", "A-cap")]
    return _house("EXP-083-A-centre-cap", parts), joints, [
        "26603 rim/tube clutch on THREE parts not evidenced",
        "existing four-piece LDraw intersections not resolved",
    ]


def _orthogonal_transverse_spine() -> tuple[BrickModel, list[tuple[str, str]], list[str], list[str]]:
    """30 pieces: 24-part supported nominal skeleton + 6 loose test roof slopes.

    Frame geometry: four piers of four 3005 bricks; two Y transverse beams
    over the piers; three X longitudinal beams; two raised center studs and
    one top spine beam. The six 30363 are *loose components to try last*;
    no roof-face-to-spine clutch is claimed or used for any certified edge.
    """
    pieces: list[BrickModelPart] = []
    joints: list[tuple[str, str]] = []
    for x in (0, 4):
        for y in (0, 6):
            previous = None
            for level in range(4):
                pid = f"B-pier-x{x}-y{y}-z{level}"
                pieces.append(_std(pid, "BRICK_1X1", x, y, level * 3))
                if previous is not None:
                    joints.append((previous, pid))
                previous = pid

    for x in (0, 4):
        pid = f"B-cross-x{x}"
        pieces.append(_std(pid, "BRICK_1X8", x, 0, 12, 0))
        for y in (0, 6):
            joints.append((f"B-pier-x{x}-y{y}-z3", pid))

    for y in (0, 3, 6):
        pid = f"B-long-y{y}"
        pieces.append(_std(pid, "BRICK_1X8", 0, y, 15, 1))
        for x in (0, 4):
            joints.append((f"B-cross-x{x}", pid))

    for x in (0, 4):
        pid = f"B-raised-ridge-x{x}"
        pieces.append(_std(pid, "BRICK_1X1", x, 3, 18))
        joints.append(("B-long-y3", pid))

    pieces.append(_std("B-ridge-spine", "BRICK_1X8", 0, 3, 21, 1))
    for x in (0, 4):
        joints.append((f"B-raised-ridge-x{x}", "B-ridge-spine"))

    skeleton_ids = [p.placement_id for p in pieces]
    # Proposed cladding only: neither physical placement nor mechanical
    # attachment is approved. The user can separately test each contact.
    for side, y in (("negative", 0), ("positive", 4)):
        for x in (0, 2, 4):
            pid = f"B-test-roof-{side}-x{x}"
            pieces.append(_roof(pid, "BRICK_SLOPED_18_4X2", side, x, y, 18, 1))
            joints.append((f"B-long-y{0 if side == 'negative' else 6}", pid))
    loose_ids = [p.placement_id for p in pieces if p.placement_id not in skeleton_ids]
    assert len(skeleton_ids) == 24 and len(loose_ids) == 6
    assert len(pieces) == 30
    return _house("EXP-083-B-transverse-spine", pieces), joints, skeleton_ids, loose_ids


def _sequential_plate_seam() -> tuple[BrickModel, list[tuple[str, str]], list[str]]:
    """A seam plate joined to a host, slopes added in a later operation."""
    parts = [
        _std("C-base", "BRICK_1X1", 4, 4, 0),
        _std("C-plate", "PLATE_1X6", 4, 3, 3, 0),
        _roof("C-left", "BRICK_SLOPED_18_4X2", "negative", 1, 2, 4),
        _roof("C-right", "BRICK_SLOPED_18_4X2", "positive", 4, 2, 4),
    ]
    joints = [("C-base", "C-plate"), ("C-plate", "C-left"),
              ("C-plate", "C-right")]
    return _house("EXP-083-C-plate-seam", parts), joints, [
        "30363 underside to plate has no approved connector evidence",
        "panel insertion is not proven",
    ]


def propose_ridge_techniques_083() -> dict:
    """Compare all three options using the SAME 082 strict design contract."""
    a_model, a_joints, a_limits = _central_post_cap()
    b_model, b_joints, frame_ids, loose_ids = _orthogonal_transverse_spine()
    c_model, c_joints, c_limits = _sequential_plate_seam()
    reports = []
    models = (
        ("A_CENTRAL_COVER", a_model, a_joints, a_limits),
        ("B_TRANSVERSE_BRACED_SPINE", b_model, b_joints, [
            "30363 cladding attachment and slopes' own mutual seams NOT approved",
            "roof silhouette, LDraw body clearance and physical load capacity unproven",
        ]),
        ("C_SEQUENTIAL_PLATE_SEAM", c_model, c_joints, c_limits),
    )
    for technique, model, joints, known_limits in models:
        before = model.model_dump_json()
        overall = screen_connector_first_candidate(model.parts, joints)
        frame_gate = None
        if technique == "B_TRANSVERSE_BRACED_SPINE":
            subset = [p for p in model.parts if p.placement_id in frame_ids]
            frame_joints = [j for j in joints if j[0] in frame_ids and j[1] in frame_ids]
            frame_gate = screen_connector_first_candidate(subset, frame_joints)
        if before != model.model_dump_json():
            raise AssertionError("candidate screening mutated experimental BrickModel")

        reports.append({
            "technique": technique,
            "building_id": model.building_id,
            "count": len(model.parts),
            "connector_gate": overall["decision"],
            "documented_nominal_connections": overall["documented_nominal_connections"],
            "blocked_connections": overall["blocked_connections"],
            "duplicate_top_studs": overall["duplicated_top_studs"],
            "nominal_frame_gate": frame_gate["decision"] if frame_gate else None,
            "nominal_frame_documented_joints": (
                frame_gate["documented_nominal_connections"] if frame_gate else 0),
            "load_path_hypothesis": (
                "piers -> transverse beams -> longitudinal beams -> spine -> unknown cladding"
                if frame_gate else "not proven; blocked interface"),
            "insertion_order": (
                ["piers bottom up", "two transverse beams", "three longitudinal beams",
                 "two ridge raisers", "upper spine",
                 "trial each loose slope separately only after inspecting fit"]
                if frame_gate else ["unsupported joint: do not assemble as a design"]),
            "limits": known_limits,
            "decision": (
                "NOMINAL_FRAME_ONLY__ROOF_CONNECTION_PHYSICAL_TRIAL_REQUIRED"
                if frame_gate and frame_gate["decision"] == "ELIGIBLE_FOR_FURTHER_DESIGN_CHECKS"
                else "REJECTED_FOR_UNDOCUMENTED_JOINTS"
            ),
            "physical_certification": "NOT_CERTIFIED",
        })
    report_b = next(r for r in reports if r["technique"] == "B_TRANSVERSE_BRACED_SPINE")
    if report_b["nominal_frame_gate"] != "ELIGIBLE_FOR_FURTHER_DESIGN_CHECKS":
        raise AssertionError("no reviewed frame; physical experiment must not be issued")
    kit = Counter(p.part_id for p in b_model.parts)
    return {
        "purpose": "SELECT_ONE_BOUNDED_30_PIECE_RIDGE_TRIAL_NOT_A_CERTIFIED_ROOF",
        "candidate_count": 3,
        "candidates": reports,
        "recommendation": "B_TRANSVERSE_BRACED_SPINE",
        "recommendation_scope": "24-piece connector-screened frame ONLY; six slopes are UNCONNECTED EXPERIMENTAL TEST PARTS",
        "physical_trial": {
            "building_id": b_model.building_id,
            "total_pieces": len(b_model.parts),
            "parts": [
                {"engine_id": k, "ldraw_reference": LDRAW_IDENTITIES[k], "quantity": v}
                for k, v in sorted(kit.items())],
            "frame_pieces": len(frame_ids),
            "loose_slope_test_pieces": len(loose_ids),
            "parts_by_placement_id": [
                p.model_dump(mode="json") for p in b_model.parts],
            "documented_nominal_frame_joints": report_b["nominal_frame_documented_joints"],
            "trial_sequence": report_b["insertion_order"],
            "physical_success_condition": (
                "User physically assembles spine frame, then individually tries "
                "both roof-side slope groups without force, confirms positive "
                "engagement, a feasible install/remove sequence, no destructive "
                "interference, and sends explicit observations/photos. "
                "Passing frame assembly alone does NOT pass ridge trial."),
            "stop_conditions": [
                "loose slope does not mate with a documented connector",
                "parts need bending, force or non-LEGO adhesive",
                "seam does not connect both roof sides",
                "structure tips or has no stable supports",
            ],
        },
        "guided004_mutated": False,
        "physical_certification": "NOT_CERTIFIED",
    }
