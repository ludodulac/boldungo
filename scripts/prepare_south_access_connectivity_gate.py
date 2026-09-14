#!/usr/bin/env python3
"""Prepare one non-canonical South-complex morphology gate.

The current best experiment makes the timber deck perceptually important by widening it,
but that rectangle also passes through the already represented masonry landing and the
upper-stair clearance. This gate keeps the same outer bounds, levels and acquired support
positions while decomposing the timber footprint around those existing Scene objects.
No hidden deck continuity, new support, or new metric measurement is introduced.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path


def _edge(treatment: str = "unknown") -> dict:
    return {"treatment": treatment, "access_spans": []}


def deconflict_south_access(scene: dict) -> dict:
    result = copy.deepcopy(scene)
    platforms = result.get("platforms", [])
    timber = next(p for p in platforms if p["id"] == "platform-timber-1")
    outer = next(p for p in platforms if p["id"] == "platform-timber-1-outer-front-fragment")
    massive = next(p for p in platforms if p["id"] == "platform-massive-1")

    x0 = float(timber["position"]["x"])
    y0 = float(timber["position"]["y"])
    z0 = float(timber["position"]["z"])
    x1 = x0 + float(timber["width"])
    y1 = y0 + float(timber["depth"])
    mx0 = float(massive["position"]["x"])
    my0 = float(massive["position"]["y"])
    my1 = my0 + float(massive["depth"])

    # Preserve the existing experimental envelope, but stop the full-width deck at
    # the already represented masonry landing instead of passing timber through it.
    timber["depth"] = my0 - y0
    timber["edges"] = {
        "x_min": _edge("open_railing"),
        "x_max": _edge("wall_attached"),
        "y_min": _edge("unknown"),
        "y_max": _edge("unknown"),
    }
    timber.setdefault("evidence", []).append({
        "photo_index": 3,
        "observation": "EXPERIMENT ONLY: keep the P3-visible full projection up to the existing masonry access envelope; exact hidden junction remains unresolved.",
    })

    # Reuse the already existing outer fragment as the exposed timber strip beside
    # the masonry landing. Its acquired support remains inside this footprint.
    outer["position"]["x"] = x0
    outer["position"]["y"] = my0
    outer["position"]["z"] = z0
    outer["width"] = mx0 - x0
    outer["depth"] = my1 - my0
    outer["edges"] = {
        "x_min": _edge("open_railing"),
        "x_max": _edge("unknown"),
        "y_min": _edge("unknown"),
        "y_max": _edge("unknown"),
    }

    # Beyond the masonry landing, preserve only the pre-existing wall-attached rear
    # band. This keeps the upper-stair corridor empty rather than inventing hidden deck.
    rear_band = {
        "id": "platform-timber-1-rear-wall-band-experiment",
        "host_volume_id": timber.get("host_volume_id"),
        "position": {"x": -1.4, "y": my1, "z": z0},
        "width": 1.4,
        "depth": y1 - my1,
        "thickness": timber["thickness"],
        "supports": [],
        "material": "timber",
        "deck_board_direction": timber.get("deck_board_direction", "unknown"),
        "edges": {
            "x_min": _edge("unknown"),
            "x_max": _edge("wall_attached"),
            "y_min": _edge("unknown"),
            "y_max": _edge("open_railing"),
        },
        "source": {"kind": "inferred", "confidence": 0.12},
        "evidence": [
            {"photo_index": 3, "observation": "EXPERIMENT ONLY: preserves the already represented wall-attached rear timber band while leaving the locally occluded stair corridor empty."},
            {"photo_index": 4, "observation": "Terrace remains visible beyond the masonry access complex; exact hidden outer continuation is not asserted."},
        ],
    }
    platforms.append(rear_band)

    # Guardrail proxies were created before this morphology gate. Trim only the
    # portions that would otherwise float over the deliberately empty stair corridor.
    for wall in result.get("partial_wall_segments", []):
        wid = wall.get("id", "")
        if wid.startswith("experiment-south-terrace-xmin-rail-"):
            wall["end"]["y"] = my1
        elif wid.startswith("experiment-south-terrace-xmin-post-"):
            cy = (float(wall["start"]["y"]) + float(wall["end"]["y"])) / 2
            if cy > my1 + 1e-9:
                wall["source"]["confidence"] = 0.0
                wall["height"]["value"] = 0.0001
        elif wid.startswith("experiment-south-terrace-ymax-rail-"):
            wall["start"]["x"] = -1.4
            wall["end"]["x"] = 0.0
        elif wid.startswith("experiment-south-terrace-ymax-post-"):
            cx = (float(wall["start"]["x"]) + float(wall["end"]["x"])) / 2
            if cx < -1.4 - 1e-9:
                wall["source"]["confidence"] = 0.0
                wall["height"]["value"] = 0.0001

    result["id"] = f"{scene.get('id', 'scene')}-south-access-connectivity-experiment"
    result["notes"] = (
        result.get("notes", "")
        + " EXPERIMENT ONLY: timber footprint is decomposed around the existing masonry landing and upper-stair clearance, using only existing Scene boundaries. Long-deck importance, relative levels, observed supports, covered void and hidden unknowns are preserved."
    ).strip()
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    scene = json.loads(args.input.read_text(encoding="utf-8"))
    result = deconflict_south_access(scene)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
