#!/usr/bin/env python3
"""Prepare one reversible front lower-register composition experiment.

Only front-opening-5 and front-opening-6 are changed. Values are weak perceptual
proxies derived from P1 proportions, not promoted metric measurements.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path


def prepare(scene: dict) -> dict:
    out = copy.deepcopy(scene)
    openings = {opening.get("id"): opening for opening in out.get("openings", [])}
    small = openings["front-opening-5"]
    glazed = openings["front-opening-6"]

    # Strengthen P1's characteristic lower-register asymmetry while preserving
    # the already acquired semantics and all vertical relationships.
    small.update({"offset_horizontal": 0.85, "width": 0.82})
    glazed.update({"offset_horizontal": 4.25, "width": 2.15})

    for opening, statement in (
        (small, "P1 weak perceptual constraint: lower-left opening reads distinctly smaller and farther left than the glazed lower-right opening; exact metric rectangle unresolved."),
        (glazed, "P1 weak perceptual constraint: glazed lower-right opening carries substantially more visual weight and sits distinctly to the right; exact metric rectangle unresolved."),
    ):
        opening["source"] = {"kind": "inferred", "confidence": 0.22}
        opening.setdefault("evidence", []).append({"photo_index": 1, "observation": statement})

    out.setdefault("notes", "")
    out["notes"] += " EXPERIMENT ONLY: front lower-register horizontal composition adjusted as a weak P1 perceptual hypothesis; no upper opening, surround, volume, roof, terrace, stair, or LEGO geometry changed."
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    scene = json.loads(args.input.read_text(encoding="utf-8"))
    result = prepare(scene)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
