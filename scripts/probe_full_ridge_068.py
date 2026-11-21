"""Audit every proposed gable ridge site with real LDraw geometry.

Does NOT modify the model or approve the hypothetical shifted roof.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

from lego_geometry_engine import LDrawLibrary
from brickhouse.bricks.brick_model import BrickModel
from brickhouse.bricks.ridge_full_length_audit_068 import audit_full_ridge


def main():
    parser = argparse.ArgumentParser(description="Non-mutating full-ridge mesh study")
    parser.add_argument("model_json", type=Path)
    parser.add_argument("--ldraw-root", type=Path, required=True)
    parser.add_argument("--max-sites", type=int, default=25)
    parser.add_argument("--shift-studs", type=int, default=3)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not args.ldraw_root.is_dir():
        parser.error("--ldraw-root must be a directory")
    raw = json.loads(args.model_json.read_text(encoding="utf-8"))
    model = BrickModel.model_validate(raw.get("brick_model", raw))
    report = audit_full_ridge(
        model, LDrawLibrary(args.ldraw_root),
        max_sites=args.max_sites, shift_studs=args.shift_studs
    )
    output = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "proposed_sites": report["proposed_sites"],
        "evaluated_sites": report["evaluated_sites"],
        "adjacent_shifted_tile_checks": len(report["adjacent_shifted_tile_checks"]),
        "geometry_counts": report.get("geometry_counts", {}),
        "adjacent_relations": report.get("adjacent_relations", {}),
        "physical_certification": report["physical_certification"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
