#!/usr/bin/env python3
"""Prepare one reversible P1-guided upper-front composition experiment.

The four openings are adjusted together as one facade rhythm. Values are weak
perceptual proxies only, never promoted measurements.
"""
from __future__ import annotations

import argparse, copy, json
from pathlib import Path


def prepare(scene: dict) -> dict:
    out = copy.deepcopy(scene)
    openings = {o.get("id"): o for o in out.get("openings", [])}

    # One coherent composition: unequal left/right weights, non-identical row
    # alignment, and less generic repeated pier widths. Vertical geometry stays
    # untouched; surrounds and every non-front element remain untouched.
    proposal = {
        "front-opening-1": {"offset_horizontal": 0.72, "width": 1.18},
        "front-opening-2": {"offset_horizontal": 4.55, "width": 1.52},
        "front-opening-3": {"offset_horizontal": 0.92, "width": 1.42},
        "front-opening-4": {"offset_horizontal": 4.35, "width": 1.28},
    }
    for oid, change in proposal.items():
        opening = openings[oid]
        opening.update(change)
        opening["source"] = {"kind": "inferred", "confidence": 0.20}
        opening.setdefault("evidence", []).append({
            "photo_index": 1,
            "observation": "P1 weak perceptual constraint: the four upper/front openings read as one asymmetric facade composition with unequal opening widths, lateral margins and row alignment; exact metric rectangles remain unresolved."
        })

    out.setdefault("notes", "")
    out["notes"] += " EXPERIMENT ONLY: four upper/front openings adjusted together as one weak P1 perceptual rhythm; lower register hypothesis preserved; no surrounds, volume, roof, terrace, supports, stair, terrain, other facade, or LEGO changed."
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("input", type=Path)
    p.add_argument("output", type=Path)
    a = p.parse_args()
    result = prepare(json.loads(a.input.read_text(encoding="utf-8")))
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(a.output)


if __name__ == "__main__":
    main()
