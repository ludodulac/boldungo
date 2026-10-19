"""Run an advisory ridge-connectivity preflight on ANY canonical house export.

Example:
  python scripts/check_roof_ridge_evidence.py path/to/brick-model.json
  python scripts/check_roof_ridge_evidence.py path/to/viewer-export.json --full

This never modifies the source model and never certifies mechanical strength.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from brickhouse.bricks.brick_model import BrickModel
from brickhouse.bricks.roof_ridge_diagnostics import analyze_roof_ridge_evidence


def main() -> None:
    parser = argparse.ArgumentParser(description="Advisory LEGO roof ridge preflight for any BrickModel")
    parser.add_argument("export_json", type=Path, help="BrickModel JSON or viewer bundle JSON")
    parser.add_argument("--full", action="store_true", help="Include per-ridge details and sample pairs")
    args = parser.parse_args()
    data = json.loads(args.export_json.read_text(encoding="utf-8"))
    brick_model = BrickModel.model_validate(data.get("brick_model", data))
    report = analyze_roof_ridge_evidence(brick_model)
    if not args.full:
        report = {key: report[key] for key in (
            "building_id", "roof_pattern", "roof_pieces", "ridge_tiles",
            "slope_tiles", "mono_pitch_tiles", "explicit_roof_supports",
            "ridge_missing_in_gable_candidate", "ridge_alignment_counts",
            "physical_certification",
        )} | {
            "opposing_slope_projected_overlap_candidates":
            report["opposing_slope_same_level_projection"]["candidate_pairs"],
            "mesh_intersection_verdict": "NOT_EVALUATED",
        }
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
