"""Fail-closed physical preflight for an existing BrickModel JSON file.

Usage: python scripts/preflight_boldungo2_brickmodel.py path/to/model.json
Exit 0 means ORTHOGONAL_PREFLIGHT_PASS only; never physical certification.
Does not modify source files or create a purchase BOM.
"""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from brickhouse.bricks.brick_model import BrickModel
from brickhouse.bricks.physical_assembly import generate_physically_screened_assembly_plan


def check_model_data(data):
    model = BrickModel.model_validate(data)
    plan = generate_physically_screened_assembly_plan(model)
    return {
        "status": "ORTHOGONAL_PREFLIGHT_PASS",
        "physical_certification": False,
        "model_parts": len(model.parts),
        "notice_parts": plan.total_parts,
        "notice_steps": plan.total_steps,
        "collision": "PASS_RECTANGULAR_AABB_ONLY",
        "catalog": "PASS_INTERNAL_ORTHOGONAL_SUBSET_ONLY",
        "connections": "PASS_VERTICAL_GRID_CONTACT_GRAPH_ONLY",
        "support": "PASS_AT_LEAST_ONE_STUD_CONTACT_ONLY",
        "insertion": "NOT_TESTED",
        "stability": "NOT_TESTED",
        "architecture": "NOT_TESTED",
        "supplier_stock": "NOT_TESTED",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("model_json", type=Path)
    args = parser.parse_args()
    try:
        payload = json.loads(args.model_json.read_text(encoding="utf-8"))
        result = check_model_data(payload)
    except (ValueError, TypeError, KeyError, OSError) as exc:
        print(json.dumps({
            "status": "ORTHOGONAL_PREFLIGHT_FAIL",
            "physical_certification": False,
            "reason": str(exc),
        }, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
