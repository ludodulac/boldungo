"""LEGO2-080: real occupied-volume gate for 079's EXACT three collisions.

No repeated triangle-crossing scan and no new ridge architecture. The only
task is to distinguish a true shell interior from surfaces with no reliable
inside/outside interpretation, using the same pinned LDraw subset as 078/079.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from lego_geometry_engine import LDrawLibrary

from brickhouse.bricks.geometry_adapter import brick_model_part_to_instance
from brickhouse.bricks.ridge_central_post_076 import assess_central_ridge_post
from brickhouse.bricks.ridge_four_piece_assembly_077 import _virtual_post
from brickhouse.bricks.ridge_material_volume_080 import (
    inspect_shared_interior, decide_physical_interference,
)
from scripts.diagnose_ridge_collision_surfaces_079 import COLLISION_PAIRS
from scripts.probe_ridge_full_ldraw_078 import REQUIRED_PARTS, small_ridge_model


def analyze_ridge_material_080(ldraw_root: Path):
    library = LDrawLibrary(ldraw_root)
    report = {
        "mission": "LEGO2-080",
        "input": "EXACT_THREE_COLLISION_PAIRS_OF_079",
        "relocalized_triangles": False,
        "required_parts": {},
        "orientations": [],
        "status": "UNKNOWN",
        "diagnostic_executed": False,
        "model_mutated": False,
        "physical_certification": "NOT_CERTIFIED",
        "blocking_reasons": [],
    }
    for part_id in REQUIRED_PARTS:
        try:
            definition = library.load_part(part_id)
            report["required_parts"][part_id] = {
                "loaded": True, "triangles": len(definition.triangles)
            }
        except (ValueError, FileNotFoundError) as exc:
            report["required_parts"][part_id] = {
                "loaded": False, "reason": f"{type(exc).__name__}: {exc}"
            }
            report["blocking_reasons"].append(
                f"GEOMETRY_NOT_AVAILABLE:{part_id}:{type(exc).__name__}:{exc}"
            )
    if report["blocking_reasons"]:
        return report

    for rotation in (0, 1):
        model = small_ridge_model(rotation)
        unchanged = model.model_dump_json()
        sources = assess_central_ridge_post(model, max_sites=1)["sites"]
        row = {
            "orientation_quarter_turns": rotation,
            "ridge_cover": "26603" if rotation == 0 else "87079",
            "pair_verdicts": [],
            "complete_diagnostic": False,
        }
        if len(sources) != 1 or sources[0]["status"] != "UNKNOWN_THREE_PART_CLUTCH_NOT_DEMONSTRATED":
            report["blocking_reasons"].append(
                f"ORIENTATION_{rotation}_SOURCE_076_ANCHOR_OR_GEOMETRY_UNKNOWN")
            report["orientations"].append(row)
            continue
        source = sources[0]
        original_slopes = {
            p.placement_id: p for p in model.parts if p.component == "roof"
        }
        parts = {
            "central_post": _virtual_post(source, 0),
            "negative_slope": original_slopes[source["slope_ids"]["negative"][0]],
            "positive_slope": original_slopes[source["slope_ids"]["positive"][0]],
        }
        try:
            meshes = {role: brick_model_part_to_instance(p, library)
                      for role, p in parts.items()}
        except (ValueError, FileNotFoundError) as exc:
            report["blocking_reasons"].append(
                f"ORIENTATION_{rotation}_MISSING_MESH:{type(exc).__name__}:{exc}"
            )
            report["orientations"].append(row)
            continue

        for a, b in COLLISION_PAIRS:
            volume = inspect_shared_interior(meshes[a], meshes[b])
            verdict, reason = decide_physical_interference(
                volume, connector_provenance_available=False)
            row["pair_verdicts"].append({
                "roles": [a, b],
                "source_079": "CONFIRMED_REAL_LDRAW_TRIANGLE_CROSSING",
                "surface_crossing_count_from_079": 24,
                "crossings_recomputed": False,
                "solids": [
                    {"role": a, "part_id": parts[a].part_id},
                    {"role": b, "part_id": parts[b].part_id},
                ],
                "volume_review": volume,
                "documented_connector_from_079": "NONE_FOUND",
                "real_matter_overlap": (
                    "UNKNOWN_MODEL_HAS_NO_CERTIFIED_MATERIAL_SURFACE_PROVENANCE"
                ),
                "verdict": verdict,
                "reason": reason,
                "physical_certification": "NOT_CERTIFIED",
            })
        row["complete_diagnostic"] = len(row["pair_verdicts"]) == 3
        if model.model_dump_json() != unchanged:
            raise AssertionError("MODEL_080_MUTATED_EXISTING_1890_PIECE_CONFIGURATION")
        report["orientations"].append(row)

    report["diagnostic_executed"] = (
        len(report["orientations"]) == 2
        and all(o["complete_diagnostic"] for o in report["orientations"])
        and not report["blocking_reasons"]
    )
    return report


def main():
    cli = argparse.ArgumentParser(description="Material review of 079 ridge collisions only")
    cli.add_argument("--ldraw-root", required=True, type=Path)
    cli.add_argument("--output", required=True, type=Path)
    args = cli.parse_args()
    result = analyze_ridge_material_080(args.ldraw_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    for orientation in result["orientations"]:
        print("ORIENTATION", orientation["orientation_quarter_turns"])
        for pair in orientation["pair_verdicts"]:
            r = pair["volume_review"]
            print("PAIR", "/".join(pair["roles"]),
                  "SHELL_A", r["first_shell"]["watertight_oriented_shell_gate"],
                  "OPEN_EDGES_A", r["first_shell"]["open_boundary_edges"],
                  "NONMANIFOLD_A", r["first_shell"]["nonmanifold_edges"],
                  "SHELL_B", r["second_shell"]["watertight_oriented_shell_gate"],
                  "OPEN_EDGES_B", r["second_shell"]["open_boundary_edges"],
                  "NONMANIFOLD_B", r["second_shell"]["nonmanifold_edges"],
                  "MATERIAL", r["shared_material_sample"],
                  "VERDICT", pair["verdict"],
                  "REASON", pair["reason"])
    print("VOLUME_REVIEW_EXECUTED=", result["diagnostic_executed"])
    print("BLOCKING_REASONS=", result["blocking_reasons"])
    print("PHYSICAL_CERTIFICATION=", result["physical_certification"])
    if not result["diagnostic_executed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
