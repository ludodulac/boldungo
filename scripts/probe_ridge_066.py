"""CLI: one local LDraw 3-D ridge experiment, no canonical modifications.

python scripts/probe_ridge_066.py brick-model.json --ldraw-root /tmp/ldraw
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from lego_geometry_engine import LDrawLibrary
from brickhouse.bricks.brick_model import BrickModel
from brickhouse.bricks.ridge_proposal_3d_066 import probe_proposed_ridges


def main() -> None:
    parser = argparse.ArgumentParser(description="Non-destructive 3-D roof ridge probe")
    parser.add_argument("brick_model_json", type=Path)
    parser.add_argument("--ldraw-root", type=Path, required=True)
    parser.add_argument("--max-tiles", type=int, default=1)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not args.ldraw_root.is_dir():
        parser.error("--ldraw-root must exist")
    raw = json.loads(args.brick_model_json.read_text(encoding="utf-8"))
    model = BrickModel.model_validate(raw.get("brick_model", raw))
    report = probe_proposed_ridges(
        model, LDrawLibrary(args.ldraw_root), max_tiles=args.max_tiles
    )
    output = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
