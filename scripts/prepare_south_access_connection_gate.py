#!/usr/bin/env python3
"""One reversible access-complex correction for the real-house-5 visual gate.

The accepted experimental terrace footprint, guardrail and visible supports are left
untouched. The only change is to the massive landing's outer x edge so the complete
width of the existing upper stair run is actually received by the landing instead of
only its centreline touching it. This is derived from existing Scene geometry, not a
new measurement.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path


def connect_upper_stair_to_landing(scene: dict) -> dict:
    result = copy.deepcopy(scene)
    landing = next(p for p in result.get("platforms", []) if p["id"] == "platform-massive-1")
    upper = next(s for s in result.get("stairs", []) if s["id"] == "stair-exterior-1-run-upper-v1")

    stair_x = float(upper["end"]["x"])
    stair_width = float(upper["width"])
    required_outer_x = stair_x - stair_width / 2.0
    landing_inner_x = float(landing["position"]["x"]) + float(landing["width"])

    # Only enlarge the visible landing outward enough to receive the existing stair.
    # Do not move its inner building contact, y/depth, level, or any other object.
    if required_outer_x < float(landing["position"]["x"]):
        landing["position"]["x"] = required_outer_x
        landing["width"] = landing_inner_x - required_outer_x
        landing["source"] = {"kind": "inferred", "confidence": 0.16}
        landing.setdefault("evidence", []).append({
            "photo_index": 4,
            "observation": (
                "EXPERIMENT ONLY: P4/P5 show the upper L-stair run arriving onto the massive landing. "
                "The landing is widened only enough for the already represented stair width to be fully received; "
                "this is a reversible Scene-coherence approximation, not a measured landing dimension."
            ),
        })

    result["id"] = f"{scene.get('id', 'scene')}-access-connection-experiment"
    result["notes"] = (
        result.get("notes", "")
        + " EXPERIMENT ONLY: massive landing outer edge extended only enough to receive the full existing upper stair width; terrace footprint, guardrail, supports, levels, stair route and openings unchanged."
    ).strip()
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    scene = json.loads(args.input.read_text(encoding="utf-8"))
    result = connect_upper_stair_to_landing(scene)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
