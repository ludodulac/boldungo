"""Export three non-certified roof-ridge options and a real 30-piece trial BOM.

Usage:
    python scripts/design_ridge_trials_083.py --output artifacts/lego2-083/ridge-trials.json

This is a design/kit proposal, NOT a certified roof or a modified house.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from brickhouse.bricks.ridge_technique_candidates_083 import propose_ridge_techniques_083


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path,
                        default=Path("artifacts/lego2-083/ridge-trials.json"))
    args = parser.parse_args()
    result = propose_ridge_techniques_083()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n",
                           encoding="utf-8")
    print("LEGO2_083_CANDIDATES=", result["candidate_count"])
    print("LEGO2_083_CHOSEN=", result["recommendation"])
    print("LEGO2_083_EXPERIMENTAL_BOM=", result["physical_trial"]["parts"])
    print("LEGO2_083_NOMINAL_JOINTS=", result["physical_trial"]["documented_nominal_frame_joints"])
    print("LEGO2_083_PHYSICAL=", result["physical_certification"])


if __name__ == "__main__":
    main()
