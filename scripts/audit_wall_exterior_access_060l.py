"""060L: reproducible model-top vertical access audit of four true wall parts.

Reads the existing unmodified 1,890-part canonical GUIDED-004 viewer-export;
no new geometry, notice rewrites, physical hand-access or stability claims.

Usage: python scripts/audit_wall_exterior_access_060l.py
       python scripts/audit_wall_exterior_access_060l.py path/to/viewer-export.json
"""
import json
import sys
from pathlib import Path

from brickhouse.bricks.assembly import AssemblyPlan
from brickhouse.bricks.brick_model import BrickModel
from brickhouse.bricks.vertical_insertion import (
    audit_notice_vertical_insertion,
    audit_notice_vertical_access_from_above,
)

MODEL = Path("artifacts/lego2-guided-004/viewer-export.json")
PARTS = ("wall-000012", "wall-000034", "wall-000060", "wall-000081")
STEPS = ("step-0003", "step-0007", "step-0011", "step-0015")
POSES = (
    ("BRICK_1X8", 16, 43, 0, 1),
    ("BRICK_1X6", 17, 43, 3, 1),
    ("BRICK_1X8", 16, 43, 6, 1),
    ("BRICK_1X6", 17, 43, 9, 1),
)


def audit(path=MODEL):
    viewer = json.loads(Path(path).read_text(encoding="utf-8"))
    model = BrickModel.model_validate(viewer["brick_model"])
    notice = AssemblyPlan.model_validate(viewer["assembly_plan"])
    if len(model.parts) != 1890:
        raise ValueError("NOT_GUIDED004_CANONICAL_1890")
    by = {p.placement_id: p for p in model.parts}
    for pid, pose in zip(PARTS, POSES):
        p = by[pid]
        if (p.part_id, p.x_studs, p.y_studs, p.z_plates,
                p.rotation_quarter_turns) != pose:
            raise ValueError("CANONICAL_POSE_DRIFT:" + pid)

    old = audit_notice_vertical_insertion(model, notice, PARTS)
    full = audit_notice_vertical_access_from_above(
        model, notice, PARTS, clearance_plates=1
    )
    rows = []
    for pid, step in zip(PARTS, STEPS):
        old_result = old[pid]
        new_result = full[pid]
        if new_result["step_id"] != step:
            raise ValueError("REAL_NOTICE_STEP_DRIFT:" + pid)
        rows.append({
            "placement_id": pid,
            "notice_step": step,
            "initial_position": new_result["initial_position"],
            "final_position": new_result["final_position"],
            "total_descent_plates": new_result["rise_plates"],
            "known_installed_max_top_z": new_result["known_installed_max_top_z"],
            "same_step_known_max_top_z": new_result["known_same_step_max_top_z"],
            "positive_margin_plates": new_result["positive_margin_plates"],
            "prior_step_obstacles": len(new_result["installed_ids"]),
            "same_step_unordered_peers": len(new_result["unordered_same_step_ids"]),
            "blockers": new_result["blockers"],
            "unknown_geometry": new_result["unknown_geometry"],
            "ambiguous_same_step": new_result["ambiguous_same_step"],
            "bounded_060j_verdict": old_result["verdict"],
            "bounded_060j_rise_plates": old_result["rise_plates"],
            "from_model_top_verdict": new_result["verdict"],
            "model_top_origin": new_result["origin_definition"],
            "access_from_outside": new_result["access_from_outside"],
        })
    return {
        "model": "GUIDED-004",
        "canonical_parts": len(model.parts),
        "approach": "STRAIGHT_DOWN_FROM_MODEL_TOP_ENVELOPE_PLUS_ONE_PLATE",
        "not_verified": ["hand_access", "real_insertability",
                         "clutch_strength", "mechanical_stability"],
        "physical_certification": "NOT_CERTIFIED",
        "rows": rows,
    }


if __name__ == "__main__":
    if len(sys.argv) > 2:
        raise SystemExit("Usage: audit_wall_exterior_access_060l.py [viewer-export.json]")
    print(json.dumps(audit(Path(sys.argv[1]) if len(sys.argv) == 2 else MODEL),
                     indent=2, ensure_ascii=False))
