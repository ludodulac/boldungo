"""LEGO2-078: execute 077's 4-piece test with the pinned real LDraw subset.

No network downloader is introduced: CI runs the existing
scripts/download_ldraw_probe_066.py into /tmp, outside git. The final JSON
is written even if the exact four-piece checks reveal a blocker.

No canonical BrickModel is changed and mesh status never certifies clutch.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from lego_geometry_engine import LDrawLibrary
from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.ridge_four_piece_assembly_077 import (
    review_simultaneous_ridge_assembly,
)

REQUIRED_PARTS = ("3005", "26603", "30363", "87079")
REAL_MESH_RELATIONS = {"SEPARATED", "CONTACT", "COLLISION"}


def _part(pid, part_id, category, component, x, y, z, rotation=0, side=None):
    return BrickModelPart(
        placement_id=pid, part_id=part_id, category=category,
        component=component, roof_side=side,
        facade="front" if component == "wall" else None,
        x_studs=x, y_studs=y,
        z_plates=z, rotation_quarter_turns=rotation,
    )


def small_ridge_model(rotation: int, shift: int = 0) -> BrickModel:
    """Two real, geometrically distinct 30363 configurations from 076/077."""
    if rotation == 0:
        roofs = (("negative", 38 + shift, 0),
                 ("positive", 39 + shift, 0))
        x, y, roof_z, wall_z = 40 + shift, 0, 117, 111
    elif rotation == 1:
        roofs = (("negative", 14 + shift, 2),
                 ("positive", 14 + shift, 2))
        x, y, roof_z, wall_z = 14 + shift, 3, 93, 87
    else:
        raise ValueError("Only the already-reviewed two roof orientations")
    parts = [
        _part(side, "BRICK_SLOPED_18_4X2", "roof_tile", "roof",
              ax, ay, roof_z, rotation, side)
        for side, ax, ay in roofs
    ] + [
        _part(f"anchored-{z}", "BRICK_1X1", "brick", "wall",
              x, y, z)
        for z in range(0, wall_z + 1, 3)
    ]
    return BrickModel(
        building_id=f"078-gable-{rotation}-{shift}", volume_id="078",
        width_studs=110, depth_studs=110, height_plates=180,
        parts=parts,
    )


def run_probe(ldraw_root: Path) -> dict:
    report = {
        "mission": "LEGO2-078",
        "ldraw_root_source": "EXISTING_PINNED_LDRAW_MIRROR_CLOSURE_066",
        "required_parts": {},
        "orientations": [],
        "required_four_piece_relations_per_site": 6,
        "physical_certification": "NOT_CERTIFIED",
        "model_mutated": False,
        "complete_real_mesh_check": False,
        "blocking_reasons": [],
    }
    library = LDrawLibrary(ldraw_root)
    for name in REQUIRED_PARTS:
        path = ldraw_root / "parts" / f"{name}.dat"
        value = {"file_present": path.is_file(), "loadable": False}
        if not path.is_file():
            value["error"] = f"MISSING_ROOT_PART:{name}.dat"
            report["blocking_reasons"].append(value["error"])
        else:
            try:
                definition = library.load_part(name)
                value["loadable"] = True
                value["triangle_count"] = len(definition.triangles)
            except (ValueError, FileNotFoundError) as exc:
                value["error"] = f"{type(exc).__name__}:{exc}"
                report["blocking_reasons"].append(
                    f"UNLOADABLE_PART:{name}:{type(exc).__name__}:{exc}")
        report["required_parts"][name] = value
    # Even if one piece fails, report both orientations with UNKNOWN rather
    # than inventing a noncolliding four-piece arrangement.
    for rotation in (0, 1):
        model = small_ridge_model(rotation)
        before = model.model_dump_json()
        evidence = review_simultaneous_ridge_assembly(
            model, library=library, max_sites=1, max_mesh_pairs=32
        )
        if model.model_dump_json() != before:
            raise AssertionError("CANONICAL_MODEL_MUTATED_BY_078_PROBE")
        sites = evidence["sites"]
        item = {
            "roof_orientation_quarter_turns": rotation,
            "roof_cover": "26603" if rotation == 0 else "87079",
            "site_count": len(sites),
            "evidence": evidence,
            "six_mesh_pairs_complete": False,
            "mesh_pair_relations": [],
            "insertion_mesh_pairs_complete": False,
        }
        if not sites:
            report["blocking_reasons"].append(
                f"ORIENTATION_{rotation}_MISSING_RIDGE_SITE")
        else:
            site = sites[0]
            pairs = site["simultaneous_pair_checks"]
            item["mesh_pair_relations"] = [
                {
                    "part_a": pair["part_a"],
                    "part_b": pair["part_b"],
                    "relation": pair.get("mesh_relation"),
                    "status": pair["status"],
                    "reason": pair.get("reason"),
                }
                for pair in pairs
            ]
            item["six_mesh_pairs_complete"] = (
                site["component_count"] == 4
                and len(pairs) == 6
                and all(pair.get("mesh_relation") in REAL_MESH_RELATIONS
                        for pair in pairs)
                and not site["missing_pair_checks"]
            )
            # This is a separate GEOMETRY-only verdict. Full computation
            # is not the same as non-intersecting geometry or LEGO clutch.
            item["collision_pairs"] = [
                {"part_a": pair["part_a"], "part_b": pair["part_b"]}
                for pair in pairs if pair.get("mesh_relation") == "COLLISION"
            ]
            item["mesh_geometry_verdict"] = (
                "UNKNOWN_INCOMPLETE_MESH"
                if not item["six_mesh_pairs_complete"]
                else "REVIEW_REQUIRED_MESH_INTERSECTIONS"
                if item["collision_pairs"]
                else "MESH_SCREEN_NO_INTERSECTIONS_ONLY"
            )
            insertion = site["cover_insertion_samples"]
            item["insertion_mesh_pairs_complete"] = (
                len(insertion) == 4
                and all(len(step["checks"]) == 3 and not step["unchecked"]
                        and all(check.get("mesh_relation")
                                in REAL_MESH_RELATIONS for check in step["checks"])
                        for step in insertion)
            )
            if not item["six_mesh_pairs_complete"]:
                reasons = [
                    p.get("reason", p["status"])
                    for p in pairs if p.get("mesh_relation") not in REAL_MESH_RELATIONS
                ]
                report["blocking_reasons"].append(
                    f"ORIENTATION_{rotation}_MESH_INCOMPLETE:{reasons}")
            if not item["insertion_mesh_pairs_complete"]:
                report["blocking_reasons"].append(
                    f"ORIENTATION_{rotation}_INSERTION_MESH_INCOMPLETE")
        report["orientations"].append(item)
    report["complete_real_mesh_check"] = (
        all(p["loadable"] for p in report["required_parts"].values())
        and all(row["six_mesh_pairs_complete"] and
                row["insertion_mesh_pairs_complete"]
                for row in report["orientations"])
        and not report["blocking_reasons"]
    )
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ldraw-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    # Always write a bounded evidence file for CI review.
    output = run_probe(args.ldraw_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n",
                           encoding="utf-8")
    for row in output["orientations"]:
        print("ROOF_ORIENTATION", row["roof_orientation_quarter_turns"],
              "FULL_MESH_PAIRS", row["six_mesh_pairs_complete"],
              "INSERTION_SAMPLE_COMPLETE", row["insertion_mesh_pairs_complete"],
              "GEOMETRY_VERDICT", row.get("mesh_geometry_verdict", "UNKNOWN"))
        for pair in row["mesh_pair_relations"]:
            print("PAIR", pair["part_a"], pair["part_b"],
                  pair["relation"], pair["status"])
    print("REAL_LDRAW_COMPLETE=", output["complete_real_mesh_check"])
    print("BLOCKERS=", output["blocking_reasons"])
    print("PHYSICAL_CERTIFICATION=", output["physical_certification"])
    if not output["complete_real_mesh_check"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
