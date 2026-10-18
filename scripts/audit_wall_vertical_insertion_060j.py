"""Reproduce 060J on the canonical 1890-part GUIDED-004 export (read-only).

Usage: python scripts/audit_wall_vertical_insertion_060j.py
       python scripts/audit_wall_vertical_insertion_060j.py /path/to/viewer-export.json
Prints explicit bounded sweeps. NEVER reports physical insertion certification.
"""
import json
import sys
from pathlib import Path

from brickhouse.bricks.assembly import AssemblyPlan
from brickhouse.bricks.brick_model import BrickModel
from brickhouse.bricks.connectors import validate_connection
from brickhouse.bricks.vertical_insertion import (
    audit_notice_vertical_insertion, check_vertical_insertion,
)

MODULE = ("wall-000012", "wall-000034", "wall-000060", "wall-000081")
DEFAULT = Path("artifacts/lego2-guided-004/viewer-export.json")


def audit(path=DEFAULT):
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    model = BrickModel.model_validate(raw["brick_model"])
    notice = AssemblyPlan.model_validate(raw["assembly_plan"])
    if len(model.parts) != 1890:
        raise ValueError("NOT_AUTHENTIC_GUIDED004_1890")
    by = {p.placement_id: p for p in model.parts}
    expected = (
        ("BRICK_1X8", 16, 43, 0, 1),
        ("BRICK_1X6", 17, 43, 3, 1),
        ("BRICK_1X8", 16, 43, 6, 1),
        ("BRICK_1X6", 17, 43, 9, 1),
    )
    for pid, exp in zip(MODULE, expected):
        p = by[pid]
        if (p.part_id, p.x_studs, p.y_studs, p.z_plates,
                p.rotation_quarter_turns) != exp:
            raise ValueError("GUIDED004_MODULE_DRIFT:" + pid)

    alone = {}
    for n, pid in enumerate(MODULE):
        alone[pid] = check_vertical_insertion(
            by[pid], [by[prev] for prev in MODULE[:n]], rise_plates=30,
        )
    house = audit_notice_vertical_insertion(model, notice, MODULE, rise_plates=30)
    links = [
        {
            "lower": lower, "upper": upper,
            "status": (result := validate_connection(by[lower], by[upper])).status,
            "interface_count": result.interface_count,
        }
        for lower, upper in zip(MODULE, MODULE[1:])
    ]
    return {
        "model": "GUIDED-004", "canonical_parts": len(model.parts),
        "rise_plates": 30, "trajectory": "VERTICAL_NEGATIVE_Z_FINITE",
        "connector_pairs": links,
        "module_isolated": alone,
        "actual_notice": house,
        "physical_buildability": "NOT_CERTIFIED",
        "exterior_access": "NOT_TESTED",
        "stability": "NOT_TESTED",
    }


if __name__ == "__main__":
    if len(sys.argv) > 2:
        raise SystemExit("Usage: audit_wall_vertical_insertion_060j.py [viewer-export.json]")
    print(json.dumps(audit(Path(sys.argv[1]) if len(sys.argv) == 2 else DEFAULT),
                     ensure_ascii=False, indent=2))
