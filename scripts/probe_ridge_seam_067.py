"""Run a small what-if 3-D roof apex experiment on any BrickModel.

This NEVER alters the actual roof or inserts any suggested tiles.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

from lego_geometry_engine import LDrawLibrary
from brickhouse.bricks.brick_model import BrickModel
from brickhouse.bricks.ridge_seam_offsets_067 import probe_ridge_seam_offsets


def main():
    parser = argparse.ArgumentParser(description="Non-mutating LDraw ridge seam offset study")
    parser.add_argument("brick_model_json", type=Path)
    parser.add_argument("--ldraw-root", type=Path, required=True)
    parser.add_argument("--max-offset", type=int, default=4)
    parser.add_argument("--proposal-index", type=int, default=0)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not args.ldraw_root.is_dir():
        parser.error("--ldraw-root must be an existing directory")
    data = json.loads(args.brick_model_json.read_text(encoding="utf-8"))
    model = BrickModel.model_validate(data.get("brick_model", data))
    report = probe_ridge_seam_offsets(
        model, LDrawLibrary(args.ldraw_root),
        proposal_index=args.proposal_index, max_offset=args.max_offset,
    )
    output = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
