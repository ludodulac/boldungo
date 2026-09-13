#!/usr/bin/env python3
"""Add one non-canonical, low-confidence visible railing hypothesis for the South terrace gate.

The footprint is left untouched. Geometry is limited to the two platform edges already
marked open_railing by the real-house Scene evidence (P3/P4). Dimensions and post rhythm
are rendering approximations only, not promoted architectural measurements.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path


def _segment(segment_id: str, start: dict, end: dict, height: float, note: str) -> dict:
    return {
        "id": segment_id,
        "start": start,
        "end": end,
        "height": {"value": height, "source": {"kind": "inferred", "confidence": 0.2}},
        "thickness": {"value": 0.05, "source": {"kind": "inferred", "confidence": 0.15}},
        "material": "timber",
        "source": {"kind": "inferred", "confidence": 0.2},
        "evidence": [{"photo_index": 3, "observation": note}],
    }


def add_visible_guardrail(scene: dict) -> dict:
    result = copy.deepcopy(scene)
    platform = next(p for p in result.get("platforms", []) if p["id"] == "platform-timber-1")
    p = platform["position"]
    x0, y0, z0 = float(p["x"]), float(p["y"]), float(p["z"])
    x1 = x0 + float(platform["width"])
    y1 = y0 + float(platform["depth"])
    deck_top = z0 + float(platform["thickness"])

    # Only edges already supported as open railing by P3/P4 are represented.
    # Thin partial-wall planes are an experimental Scene-viewer proxy for rails/posts;
    # they are not canonical wall semantics and are never sent to LEGO in this gate.
    parts = result.setdefault("partial_wall_segments", [])
    observation = (
        "EXPERIMENT ONLY: P3/P4 show an open timber guardrail on this visible terrace edge. "
        "Exact rail height, section and spacing are unmeasured; the regular rhythm is a low-confidence visual proxy."
    )

    # Outer longitudinal edge (x_min): two open horizontal rails.
    for index, rail_z in enumerate((deck_top + 0.38, deck_top + 0.78), start=1):
        parts.append(_segment(
            f"experiment-south-terrace-xmin-rail-{index}",
            {"x": x0, "y": y0, "z": rail_z},
            {"x": x0, "y": y1, "z": rail_z},
            0.06,
            observation,
        ))
    # Sparse repeated uprights, including both visible ends.
    for index, fraction in enumerate((0.0, 0.25, 0.5, 0.75, 1.0), start=1):
        y = y0 + (y1 - y0) * fraction
        parts.append(_segment(
            f"experiment-south-terrace-xmin-post-{index}",
            {"x": x0, "y": y - 0.025, "z": deck_top},
            {"x": x0, "y": y + 0.025, "z": deck_top},
            0.86,
            observation,
        ))

    # Rear transverse edge (y_max), also already marked open_railing in the Scene.
    for index, rail_z in enumerate((deck_top + 0.38, deck_top + 0.78), start=1):
        parts.append(_segment(
            f"experiment-south-terrace-ymax-rail-{index}",
            {"x": x0, "y": y1, "z": rail_z},
            {"x": x1, "y": y1, "z": rail_z},
            0.06,
            observation,
        ))
    for index, fraction in enumerate((0.0, 0.5, 1.0), start=1):
        x = x0 + (x1 - x0) * fraction
        parts.append(_segment(
            f"experiment-south-terrace-ymax-post-{index}",
            {"x": x - 0.025, "y": y1, "z": deck_top},
            {"x": x + 0.025, "y": y1, "z": deck_top},
            0.86,
            observation,
        ))

    result["id"] = f"{scene.get('id', 'scene')}-visible-guardrail-experiment"
    result["notes"] = (
        result.get("notes", "")
        + " EXPERIMENT ONLY: low-confidence open-railing proxy on P3/P4-observed x_min and y_max timber-deck edges; footprint, supports, masonry landing, L stair and openings unchanged; no hidden edge continuity asserted."
    ).strip()
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    scene = json.loads(args.input.read_text(encoding="utf-8"))
    result = add_visible_guardrail(scene)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
