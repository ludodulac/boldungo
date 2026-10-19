"""Run missions 1+2 on any canonical house, never modify the model.

python scripts/check_house_assembly_064.py my-brick-model.json
python scripts/check_house_assembly_064.py viewer-export.json --ldraw-root /path/to/ldraw
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

from brickhouse.bricks.brick_model import BrickModel
from brickhouse.bricks.connector_audit_064 import audit_orthogonal_connections
from brickhouse.bricks.roof_host_mesh_064 import check_roof_host_mesh
from brickhouse.bricks.roof_mesh_preflight import preflight_roof_mesh
from lego_geometry_engine import LDrawLibrary


def main():
    parser = argparse.ArgumentParser(description="Advisory roof mesh and LEGO connector evidence")
    parser.add_argument("model", type=Path, help="BrickModel or viewer-export JSON")
    parser.add_argument("--ldraw-root", type=Path, help="Complete real LDraw parts library")
    parser.add_argument("--max-mesh-pairs", type=int, default=3)
    parser.add_argument("--max-interfaces", type=int, default=30000)
    args = parser.parse_args()
    if args.ldraw_root and not args.ldraw_root.is_dir():
        parser.error("--ldraw-root must be an existing directory")
    raw = json.loads(args.model.read_text(encoding="utf-8"))
    model = BrickModel.model_validate(raw.get("brick_model", raw))
    library = LDrawLibrary(args.ldraw_root) if args.ldraw_root else None
    report = {
        "building_id": model.building_id,
        "roof_to_roof_collision_evidence": (
            preflight_roof_mesh(model, library, max_pairs=args.max_mesh_pairs)
            if library else {"status": "NOT_RUN_LDRAW_LIBRARY_REQUIRED",
                             "physical_certification": "NOT_CERTIFIED"}
        ),
        "roof_to_wall_collision_evidence": check_roof_host_mesh(
            model, library, max_pairs=args.max_mesh_pairs),
        "nominal_orthogonal_connections": audit_orthogonal_connections(
            model, max_interfaces=args.max_interfaces),
        "physical_certification": "NOT_CERTIFIED",
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
