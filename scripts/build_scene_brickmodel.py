#!/usr/bin/env python3
"""Build one full BrickHouse export from a materialized ArchitecturalScene."""
from __future__ import annotations

import argparse
from pathlib import Path

from brickhouse.bricks.export import export_bundle_json
from brickhouse.pipeline import DEFAULT_FRONT_WIDTH_STUDS, run_m0_pipeline_scene
from brickhouse.scene.models import ArchitecturalScene


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("scene", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--front-width-studs", type=int, default=DEFAULT_FRONT_WIDTH_STUDS)
    args = parser.parse_args()

    scene = ArchitecturalScene.model_validate_json(args.scene.read_text(encoding="utf-8"))
    bundle = run_m0_pipeline_scene(scene, front_width_studs=args.front_width_studs)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(export_bundle_json(bundle) + "\n", encoding="utf-8")
    print(
        f"Generated {args.output}: {bundle.bom.total_parts} parts, "
        f"{bundle.bom.unique_part_types} canonical types"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
