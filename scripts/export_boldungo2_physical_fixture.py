"""Reproducible GEOMETRY-ONLY fixture package: catalog placements, BOM and notice.

This is not the user's house and does not certify strength or insertability.
"""
from collections import Counter
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from brickhouse.bricks.physical_wall_fixture import opening_wall_geometrically_screened_notice

def create_package():
    model, plan = opening_wall_geometrically_screened_notice()
    bom = Counter(p.part_id for p in model.parts)
    return {
        "schema_version": "boldungo2.engineering_fixture.v1",
        "fixture": "opening_wall_12x2",
        "validation_level": "GEOMETRY_ONLY",
        "connector_validation": "NOT_CHECKED",
        "physical_certification": False,
        "physical_strength_certified": False,
        "insertability_certified": False,
        "architectural_fidelity_certified": False,
        "brick_model": model.model_dump(mode="json"),
        "assembly_plan": plan.model_dump(mode="json"),
        "bill_of_materials": {
            "total_parts": len(model.parts),
            "parts_by_id": dict(sorted(bom.items())),
        },
    }

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    data = create_package()
    encoded = json.dumps(data, indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded + "\n", encoding="utf-8")
        print(f"EXPORTED:{args.output}")
    else:
        print(encoded)

if __name__ == "__main__":
    main()
