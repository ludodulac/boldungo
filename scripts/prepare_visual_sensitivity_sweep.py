#!/usr/bin/env python3
"""Prepare non-canonical Scene variants for the real-house visual sensitivity sweep."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path


def _metric_value(value):
    return value.get("value") if isinstance(value, dict) and "value" in value else value


def _set_metric(container: dict, key: str, value: float) -> None:
    current = container.get(key)
    if isinstance(current, dict) and "value" in current:
        current["value"] = value
    else:
        container[key] = value


def _scale_height(scene: dict, target_height: float) -> dict:
    result = copy.deepcopy(scene)
    volume = next(v for v in result["volumes"] if v["id"] == "volume_main")
    current_height = float(_metric_value(volume["height"]))
    scale = target_height / current_height
    _set_metric(volume, "height", target_height)

    for opening in result.get("openings", []):
        opening["offset_vertical"] = float(opening["offset_vertical"]) * scale
        opening["height"] = float(opening["height"]) * scale

    for platform in result.get("platforms", []):
        if platform.get("position") and platform["position"].get("z") is not None:
            platform["position"]["z"] = float(platform["position"]["z"]) * scale
        for support in platform.get("supports", []):
            if support.get("position") and support["position"].get("z") is not None:
                support["position"]["z"] = float(support["position"]["z"]) * scale
            if support.get("height") is not None:
                support["height"] = float(support["height"]) * scale

    for stair in result.get("stairs", []):
        for endpoint in ("start", "end"):
            if stair.get(endpoint) and stair[endpoint].get("z") is not None:
                stair[endpoint]["z"] = float(stair[endpoint]["z"]) * scale

    for chimney in result.get("chimneys", []):
        if chimney.get("position") and chimney["position"].get("z") is not None:
            chimney["position"]["z"] = float(chimney["position"]["z"]) * scale
        if chimney.get("height") is not None:
            chimney["height"] = float(chimney["height"]) * scale

    for wall in result.get("partial_wall_segments", []):
        for endpoint in ("start", "end"):
            if wall.get(endpoint) and wall[endpoint].get("z") is not None:
                wall[endpoint]["z"] = float(wall[endpoint]["z"]) * scale
        if wall.get("height") is not None:
            _set_metric(wall, "height", float(_metric_value(wall["height"])) * scale)

    result["id"] = f"{scene.get('id', 'scene')}-height-{target_height:g}-experiment"
    result["notes"] = (result.get("notes", "") + f" EXPERIMENT ONLY: coherent vertical sensitivity scale {scale:.4f}; target height {target_height:g} m is not promoted truth.").strip()
    return result


def _terrace_extent(scene: dict, y_min: float) -> dict:
    result = copy.deepcopy(scene)
    platform = next(p for p in result.get("platforms", []) if p["id"] == "platform-timber-1")
    rear_y = 9.0
    platform["position"]["y"] = y_min
    platform["depth"] = rear_y - y_min
    supports = platform.get("supports", [])
    if supports:
        front = min(supports, key=lambda s: float(s["position"]["y"]))
        front["position"]["y"] = y_min + 0.25
    fraction = (rear_y - y_min) / 9.0
    result["id"] = f"{scene.get('id', 'scene')}-terrace-{round(fraction * 100)}-experiment"
    result["notes"] = (result.get("notes", "") + f" EXPERIMENT ONLY: timber terrace longitudinal sensitivity proxy {fraction:.3f}; hidden contour remains unresolved.").strip()
    return result


def _visible_full_depth_terrace(scene: dict) -> dict:
    """One reversible footprint test: make the P3-visible timber deck read as a platform.

    Only the exposed outer projection is widened. The masonry-side hidden junction
    remains represented by the existing separate fragment/clearance geometry.
    """
    result = copy.deepcopy(scene)
    platform = next(p for p in result.get("platforms", []) if p["id"] == "platform-timber-1")
    platform["position"]["x"] = -2.8
    platform["width"] = 2.8
    source = platform.setdefault("source", {})
    source["kind"] = "inferred"
    source["confidence"] = min(float(source.get("confidence", 0.25)), 0.25)
    platform.setdefault("evidence", []).append({
        "photo_index": 3,
        "observation": "EXPERIMENT ONLY: P3 shows sustained full outward projection on the visible timber terrace; exact hidden junction behind the masonry access complex remains unresolved."
    })
    result["id"] = f"{scene.get('id', 'scene')}-visible-full-depth-terrace-experiment"
    result["notes"] = (result.get("notes", "") + " EXPERIMENT ONLY: reversible low-confidence footprint test. The P3-visible timber platform keeps sustained outward projection; no hidden continuity behind the masonry access complex is asserted.").strip()
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("current", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    current = json.loads(args.current.read_text(encoding="utf-8"))
    args.output_dir.mkdir(parents=True, exist_ok=True)

    for height in (6.5, 6.0, 5.6):
        path = args.output_dir / f"height-{height:g}.json"
        path.write_text(json.dumps(_scale_height(current, height), indent=2) + "\n", encoding="utf-8")

    for label, y_min in (("50", 4.5), ("62", 3.4)):
        path = args.output_dir / f"terrace-{label}.json"
        path.write_text(json.dumps(_terrace_extent(current, y_min), indent=2) + "\n", encoding="utf-8")

    combined = _terrace_extent(_scale_height(current, 6.5), 3.4)
    combined["id"] = f"{current.get('id', 'scene')}-combined-height-6.5-terrace-62-experiment"
    combined["notes"] = (combined.get("notes", "") + " COMBINED VISUAL TEST ONLY: selected 6.5 m height family plus 62% terrace family; neither value is promoted truth.").strip()
    (args.output_dir / "combined-6.5-62.json").write_text(
        json.dumps(combined, indent=2) + "\n", encoding="utf-8"
    )

    corrected = _visible_full_depth_terrace(combined)
    (args.output_dir / "combined-6.5-62-terrace-footprint.json").write_text(
        json.dumps(corrected, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
