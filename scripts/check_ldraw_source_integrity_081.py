"""LEGO2-081: source-to-import accounting for ONLY official 3005 / 30363.

This counts every type-3 and type-4 face in the pinned official sources
and all transitive references, independently from the importer's _expand.
Never invents closing surfaces or duplicates already-completed collision
checks 060-080. A matching count does NOT guarantee topological closure.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

from lego_geometry_engine import LDrawLibrary
from brickhouse.bricks.ridge_material_volume_080 import inspect_solid_shell
from lego_geometry_engine import instantiate

PARTS = ("3005", "30363")


def tally_ldraw_source(library: LDrawLibrary, part: str) -> dict:
    root = library._resolve(part + ".dat")
    if root is None:
        raise FileNotFoundError(part)
    totals = Counter()
    visited = set()

    def visit(path, stack):
        resolved = path.resolve()
        if resolved in stack:
            raise ValueError(f"Recursive source reference: {path}")
        visited.add(path.relative_to(library.root).as_posix())
        next_stack = stack | {resolved}
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            tokens = line.strip().split()
            if not tokens:
                continue
            if tokens[0] == "0":
                if len(tokens) >= 4 and tokens[1:3] == ["BFC", "CERTIFY"]:
                    if "CW" in tokens[3:]:
                        totals["certify_cw_files"] += 1
                    if "CCW" in tokens[3:]:
                        totals["certify_ccw_files"] += 1
                elif len(tokens) >= 3 and tokens[1:3] == ["BFC", "INVERTNEXT"]:
                    totals["bfc_invertnext_references"] += 1
            elif tokens[0] == "1" and len(tokens) >= 15:
                totals["type1_references"] += 1
                target = library._resolve(" ".join(tokens[14:]))
                if target is None:
                    raise FileNotFoundError(" ".join(tokens[14:]))
                visit(target, next_stack)
            elif tokens[0] == "3" and len(tokens) >= 11:
                totals["source_triangles"] += 1
            elif tokens[0] == "4" and len(tokens) >= 14:
                totals["source_quads"] += 1
            elif tokens[0] == "2":
                totals["line_segments_not_surfaces"] += 1
            elif tokens[0] == "5":
                totals["conditional_edges_not_surfaces"] += 1
    visit(root, set())
    imported = library.load_part(part)
    actual = len(imported.triangles)
    expected = totals["source_triangles"] + 2 * totals["source_quads"]
    shell = inspect_solid_shell(instantiate(imported, f"081-{part}"))
    return {
        "part_id": part,
        "source_files_visited": sorted(visited),
        "source_counts": dict(totals),
        "source_triangle_equivalent": expected,
        "imported_triangle_count": actual,
        "type3_type4_surfaces_accounted_for": actual == expected,
        "imported_shell": shell,
        "material_volume_verdict": "UNKNOWN"
        if not shell["volume_from_shell_provable"] else "GEOMETRIC_VOLUME_GATE_ONLY",
        "physical_certification": "NOT_CERTIFIED",
    }


def check_two_source_parts(ldraw_root: Path) -> dict:
    library = LDrawLibrary(ldraw_root)
    report = {
        "mission": "LEGO2-081",
        "scope": "ONLY_3005_AND_30363_SOURCE_IMPORT",
        "items": {},
        "source_faces_all_accounted_for": False,
        "material_certified": False,
        "physical_certification": "NOT_CERTIFIED",
        "model_mutated": False,
        "blockers": [],
    }
    for part in PARTS:
        try:
            report["items"][part] = tally_ldraw_source(library, part)
        except (ValueError, FileNotFoundError) as exc:
            report["blockers"].append(f"{part}:{type(exc).__name__}:{exc}")
    report["source_faces_all_accounted_for"] = (
        len(report["items"]) == 2
        and not report["blockers"]
        and all(x["type3_type4_surfaces_accounted_for"]
                for x in report["items"].values())
    )
    return report


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--ldraw-root", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    report = check_two_source_parts(args.ldraw_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    for name, part in report["items"].items():
        print("LDRAW_SOURCE_IMPORT", name,
              "SOURCE_TRIANGLE_EQUIVALENT", part["source_triangle_equivalent"],
              "IMPORTED_TRIANGLES", part["imported_triangle_count"],
              "ALL_SOURCE_FACES_PRESENT", part["type3_type4_surfaces_accounted_for"],
              "CW_SUBFILES", part["source_counts"].get("certify_cw_files", 0),
              "INVERTNEXT", part["source_counts"].get("bfc_invertnext_references", 0),
              "OPEN_EDGES", part["imported_shell"]["open_boundary_edges"],
              "WINDING_EDGES", part["imported_shell"]["inconsistent_winding_edges"],
              "VOLUME", part["material_volume_verdict"])
    print("SOURCE_FACET_PARITY=", report["source_faces_all_accounted_for"])
    print("BLOCKERS=", report["blockers"])
    print("PHYSICAL_CERTIFICATION=", report["physical_certification"])
    if not report["source_faces_all_accounted_for"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
