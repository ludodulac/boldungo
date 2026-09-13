#!/usr/bin/env python3
"""Expose only photo-supported South-terrace supports for one non-canonical visual gate.

The input already contains the accepted experimental footprint and guardrail. This
adapter does not alter either. It visualizes only support records already carried by
the timber platform; no hidden posts or bracing are invented. No diagonal is added
because the current structured Scene evidence does not localize one safely enough.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path


def _metric(value):
    return float(value.get("value")) if isinstance(value, dict) and "value" in value else float(value)


def add_visible_structure(scene: dict) -> dict:
    result = copy.deepcopy(scene)
    platform = next(p for p in result.get("platforms", []) if p["id"] == "platform-timber-1")
    parts = result.setdefault("partial_wall_segments", [])

    observation = (
        "EXPERIMENT ONLY: P3, corroborated by P4/P5, supports visible timber posts beneath the terrace. "
        "This proxy uses only support records already present in the Scene; exact sections remain low-confidence. "
        "No diagonal/bracing is asserted where the structured evidence does not localize it safely."
    )

    for support in platform.get("supports", []):
        p = support.get("position") or {}
        if any(p.get(axis) is None for axis in ("x", "y", "z")) or support.get("height") is None:
            continue
        width = float(support.get("width", 0.12))
        x, y, z = float(p["x"]), float(p["y"]), float(p["z"])
        height = _metric(support["height"])
        parts.append({
            "id": f"experiment-visible-{support['id']}",
            "start": {"x": x, "y": y - width / 2, "z": z},
            "end": {"x": x, "y": y + width / 2, "z": z},
            "height": {"value": height, "source": {"kind": "inferred", "confidence": 0.2}},
            "thickness": {"value": width, "source": {"kind": "inferred", "confidence": 0.18}},
            "material": "timber",
            "source": {"kind": "inferred", "confidence": 0.2},
            "evidence": [{"photo_index": 3, "observation": observation}],
        })

    result["id"] = f"{scene.get('id', 'scene')}-visible-supports-experiment"
    result["notes"] = (
        result.get("notes", "")
        + " EXPERIMENT ONLY: existing photo-supported timber-platform support records are made visible as low-confidence viewer proxies; no additional hidden support and no unlocalized bracing added; footprint and guardrail unchanged."
    ).strip()
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    scene = json.loads(args.input.read_text(encoding="utf-8"))
    result = add_visible_structure(scene)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
