"""LEGO2-084: exact 24-step frame replay before inviting a 30-piece physical trial.

Do not confuse a valid NOMINAL support plane and AABB approach with stable,
clutch-approved LEGO construction. The six 30363 are deliberately listed as
HOLD_FOR_PHYSICAL_MATING_TEST; they are NOT part of the approved assembly plan.
No canonical GUIDED-004 placement is read or mutated.
"""
from __future__ import annotations

from .connector_first_design_082 import screen_connector_first_candidate
from .connectors import validate_connection
from .ridge_technique_candidates_083 import _orthogonal_transverse_spine
from .vertical_insertion import check_vertical_access_from_above


def review_ridge_trial_assembly_084(*, frame_order=None, disable_connector_check=False):
    """Replay each orthogonal frame brick from above with prior connectors.

    frame_order is an experimental *ordering* parameter for rejecting invalid
    proposed manuals. All geometry is taken from the same bounded 083 model.
    """
    model, required, frame_ids, loose_ids = _orthogonal_transverse_spine()
    by_id = {p.placement_id: p for p in model.parts}
    order = list(frame_ids if frame_order is None else frame_order)
    if len(order) != len(frame_ids) or set(order) != set(frame_ids):
        raise ValueError("frame order must contain exactly 24 unique known frame ids")
    frame_parts = [by_id[pid] for pid in frame_ids]
    frame_joints = [pair for pair in required if all(pid in frame_ids for pid in pair)]
    filter_result = screen_connector_first_candidate(frame_parts, frame_joints)

    previous = []
    installed_ids = set()
    reachable = set()
    steps = []
    reasons = []
    all_frame_clear = True
    for number, pid in enumerate(order, start=1):
        part = by_id[pid]
        candidates = [(lo, hi) for lo, hi in frame_joints
                      if hi == pid and lo in installed_ids]
        accepted = []
        for lo, hi in candidates:
            connection = validate_connection(by_id[lo], by_id[hi])
            if connection.status == "VALID" and lo in reachable:
                accepted.append({"from": lo, "to": hi,
                                 "connector": connection.status,
                                 "reason": connection.reason,
                                 "interface_count": connection.interface_count})
        is_ground = part.z_plates == 0
        supported = is_ground or bool(accepted)
        approach = check_vertical_access_from_above(part, previous)
        clear = approach["verdict"] == "GEOMETRY_CLEAR_ONLY"
        status = ("READY_FOR_PHYSICAL_STEP_TEST" if supported and clear
                  else "REJECTED_MISSING_PRIOR_DOCUMENTED_SUPPORT"
                  if not supported
                  else "REJECTED_INSERTION_ENVELOPE_" + approach["verdict"])
        if status != "READY_FOR_PHYSICAL_STEP_TEST":
            reasons.append({"step": number, "part": pid, "reason": status})
        if supported:
            reachable.add(pid)
        if not clear:
            all_frame_clear = False
        steps.append({
            "step": number,
            "placement_id": pid,
            "part_id": part.part_id,
            "position": {"x_studs": part.x_studs,
                         "y_studs": part.y_studs, "z_plates": part.z_plates,
                         "rotation_quarter_turns": part.rotation_quarter_turns},
            "on_structural_ground_datum": is_ground,
            "documented_prior_supports": accepted,
            "insertion_screen": approach["verdict"],
            "insertion_evidence": approach["scope"],
            "status": status,
        })
        previous.append(part)
        installed_ids.add(pid)

    trial = {
        "building_id": model.building_id,
        "total_kit_parts": len(model.parts),
        "frame_parts": len(frame_ids),
        "frame_nominal_joint_count": len(frame_joints),
        "frame_connector_gate": filter_result["decision"],
        "step_count": len(steps),
        "steps": steps,
        "structural_datum": 0,
        "nominal_chain_to_datum_count": len(reachable),
        "frame_top_approaches_clear": all_frame_clear,
        "frame_trial_status": (
            "READY_FOR_USER_FRAME_ASSEMBLY_TRIAL"
            if not reasons and filter_result["decision"] == "ELIGIBLE_FOR_FURTHER_DESIGN_CHECKS"
            else "REJECTED_BEFORE_FRAME_TRIAL"),
        "frame_rejection_reasons": reasons,
        "roof_pieces": [{
            "placement_id": pid,
            "part_id": by_id[pid].part_id,
            "x_studs": by_id[pid].x_studs,
            "y_studs": by_id[pid].y_studs,
            "z_plates": by_id[pid].z_plates,
            "rotation_quarter_turns": by_id[pid].rotation_quarter_turns,
            "status": "HOLD_FOR_PHYSICAL_MATING_TEST_NOT_APPROVED_FOR_INSTALLATION",
        } for pid in loose_ids],
        "roof_attach_status": "REJECTED_UNDOCUMENTED_SLOPE_TO_FRAME_CONNECTION",
        "physical_observation_questions": [
            "Do the 24 frame parts engage naturally with no excessive force?",
            "Does the frame stand without being held, on a level LEGO-compatible base?",
            "Can each of the six slopes attach positively without forcing or bending?",
            "Do BOTH slopes actually join to a COMMON structurally supported ridge?",
            "Can all installed pieces be removed without damage?",
        ],
        "abort_conditions": [
            "any step bends, strains or requires forcing a piece",
            "any required frame part cannot be attached or holds only by balance",
            "a slope has no matching connector or collides with its neighbor",
            "the frame falls or its base is not stable",
        ],
        "physical_certification": "NOT_CERTIFIED",
        "model_mutated": False,
        "limitations": (
            "Nominal stud/tube graph and AABB top-down approach only. "
            "No proof of friction/clutch, independent stability, gravitational "
            "loads, rigid structure or continuous physical insertion. "
            "Six slopes are intentionally HELD, not approved attachments."
        ),
    }
    return trial
