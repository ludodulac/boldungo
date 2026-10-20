"""Preview (never apply) two-sided ridge bridge candidates for any BrickModel.

Usage:
  python scripts/propose_ridge_bridges_065.py path/to/brick-model.json
  python scripts/propose_ridge_bridges_065.py path/to/viewer-export.json --full

No geometry, inventory or notice is changed.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

from brickhouse.bricks.brick_model import BrickModel
from brickhouse.bricks.ridge_bridge_planner_065 import propose_ridge_bridges


def main():
    parser = argparse.ArgumentParser(description="Advisory, non-mutating ridge bridge preview")
    parser.add_argument("model_json", type=Path)
    parser.add_argument("--max-tiles", type=int, default=2000)
    parser.add_argument("--full", action="store_true",
                        help="Include every proposed tile and unresolved detail")
    args = parser.parse_args()
    raw = json.loads(args.model_json.read_text(encoding="utf-8"))
    model = BrickModel.model_validate(raw.get("brick_model", raw))
    report = propose_ridge_bridges(model, max_tiles=args.max_tiles)
    if not args.full:
        report = {key: value for key, value in report.items()
                  if key not in ("proposed_tiles", "unresolved", "unknown_slope_ids")}
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
