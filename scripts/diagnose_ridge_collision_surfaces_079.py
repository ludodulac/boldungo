"""LEGO2-079: localize exactly the 3 mesh intersections from real LDraw 078.

Only mesh-surface crossing *witnesses* and actual normalized LDraw connector
metadata are considered. This DOES NOT distinguish rigid solid wall versus a
permitted deforming clutch from triangles alone, and never marks a full
assembly VALID without documented fit proof.

LDraw is the SAME bounded pinned dependency closure downloaded by 066/078.
All positions and slopes are reused unmodified from 076/077/078.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from lego_geometry_engine import LDrawLibrary, Relation, check_collision, find_connections
from lego_geometry_engine.core import CONTACT_EPS, _tri_intersection_kind

from brickhouse.bricks.geometry_adapter import brick_model_part_to_instance
from brickhouse.bricks.ridge_central_post_076 import assess_central_ridge_post
from brickhouse.bricks.ridge_four_piece_assembly_077 import _virtual_post, _virtual_cover
from brickhouse.bricks.roof_ridge_diagnostics import _studs_documented
from scripts.probe_ridge_full_ldraw_078 import REQUIRED_PARTS, small_ridge_model

COLLISION_PAIRS = (
    ("central_post", "negative_slope"),
    ("central_post", "positive_slope"),
    ("negative_slope", "positive_slope"),
)
MAX_TRIANGLE_CANDIDATES = 600_000
MAX_WITNESSES = 24


def _boxes_overlap(lower_a, upper_a, lower_b, upper_b):
    return not any(
        upper_a[i] < lower_b[i] - CONTACT_EPS
        or upper_b[i] < lower_a[i] - CONTACT_EPS
        for i in range(3)
    )


def _bounds(triangle):
    return (
        tuple(min(v[i] for v in triangle) for i in range(3)),
        tuple(max(v[i] for v in triangle) for i in range(3)),
    )


def localize_crossing_triangles(
    first, second, *, max_candidate_tests=MAX_TRIANGLE_CANDIDATES,
    max_witnesses=MAX_WITNESSES,
):
    """Bounded strict triangle-surface crossing regions in WORLD LDU.

    A narrow region is the overlapping *triangle AABB*, not an exact
    volumetric solid-intersection volume. No physics inference is made.
    """
    if max_candidate_tests < 1 or max_witnesses < 1:
        raise ValueError("positive limits required")
    witness, tested, capped = [], 0, False
    tris_b = [(t, *_bounds(t)) for t in second.triangles]
    for ta in first.triangles:
        alo, ahi = _bounds(ta)
        for tb, blo, bhi in tris_b:
            if not _boxes_overlap(alo, ahi, blo, bhi):
                continue
            if tested >= max_candidate_tests:
                capped = True
                break
            tested += 1
            if _tri_intersection_kind(ta, tb) is not Relation.COLLISION:
                continue
            overlap_low = [max(alo[i], blo[i]) for i in range(3)]
            overlap_high = [min(ahi[i], bhi[i]) for i in range(3)]
            witness.append({
                "aabb_min_ldu": [round(v, 4) for v in overlap_low],
                "aabb_max_ldu": [round(v, 4) for v in overlap_high],
            })
            if len(witness) >= max_witnesses:
                break
        if capped or len(witness) >= max_witnesses:
            break

    if witness:
        lo = [min(w["aabb_min_ldu"][i] for w in witness) for i in range(3)]
        hi = [max(w["aabb_max_ldu"][i] for w in witness) for i in range(3)]
        envelope = {"min_ldu": lo, "max_ldu": hi}
        # World-X is model width, world-Z model depth; LDraw Y is downwards.
        envelope["approx_model_xyz_studs_plates"] = {
            "x_studs": [round(lo[0] / 20, 3), round(hi[0] / 20, 3)],
            "y_studs": [round(lo[2] / 20, 3), round(hi[2] / 20, 3)],
            "height_plates": [round(-hi[1] / 8, 3), round(-lo[1] / 8, 3)],
        }
    else:
        envelope = None
    return {
        "triangles_first": len(first.triangles),
        "triangles_second": len(second.triangles),
        "candidate_triangle_pairs_tested": tested,
        "crossing_witnesses_recorded": len(witness),
        "witness_limit_reached": len(witness) >= max_witnesses,
        "candidate_test_limit_reached": capped,
        "witness_regions": witness,
        "sample_envelope": envelope,
        "exhaustive": not capped and len(witness) < max_witnesses,
    }


def _classify_zone(result, pair_roles, post_top_plane):
    """Only classify HEIGHT of sampled surface crossing, not full provenance."""
    bounds = result["sample_envelope"]
    if bounds is None:
        return "UNKNOWN_NO_STRICT_SURFACE_CROSSING_WITNESS"
    zrange = bounds["approx_model_xyz_studs_plates"]["height_plates"]
    if "central_post" not in pair_roles:
        if zrange[0] >= post_top_plane - 3:
            return "OPPOSING_ROOF_SLOPE_UPPER_SEAM_BAND"
        return "OPPOSING_ROOF_SLOPE_MESH_BODIES"
    # The post brick BODY extends to the mating plane; the projecting stud
    # is ABOVE that plane. A triangle witness below it is not proof of a
    # legitimate anti-stud tube engagement.
    if zrange[1] < post_top_plane - 0.01:
        return "CENTRAL_POST_BODY_SIDE_BELOW_STUD_PLANE"
    if zrange[0] > post_top_plane + 0.01:
        return "CENTRAL_POST_TOP_STUD_BAND"
    return "CENTRAL_POST_AND_SLOPE_CROSSING_NEAR_STUD_PLANE"


def diagnose_three_ridge_collisions(ldraw_root: Path, *, orientations=(0, 1)):
    library = LDrawLibrary(ldraw_root)
    output = {
        "mission": "LEGO2-079",
        "input": "SAME_PINNED_LDRAW_DEPENDENCY_CLOSURE_AS_078",
        "required_parts": {},
        "orientations": [],
        "physical_certification": "NOT_CERTIFIED",
        "model_mutated": False,
        "complete_collision_localization": False,
        "blocking_reasons": [],
        "verdict_meaning": {
            "VALID": "only an independently supported precise local control",
            "INVALID": "only a demonstrated impossible geometric configuration",
            "UNKNOWN": "mesh intersection not attributable to a proven legal clutch or rigid obstruction",
        },
    }
    for name in REQUIRED_PARTS:
        path = ldraw_root / "parts" / f"{name}.dat"
        try:
            part = library.load_part(name)
            output["required_parts"][name] = {
                "file_present": path.is_file(), "mesh_loaded": True,
                "triangles": len(part.triangles),
            }
        except (ValueError, FileNotFoundError) as exc:
            output["required_parts"][name] = {
                "file_present": path.is_file(), "mesh_loaded": False,
                "reason": f"{type(exc).__name__}: {exc}",
            }
            output["blocking_reasons"].append(
                f"REQUIRED_PART_NOT_LOADABLE_{name}: {type(exc).__name__}: {exc}")

    for orientation in orientations:
        model = small_ridge_model(orientation)
        snapshot = model.model_dump_json()
        base = assess_central_ridge_post(model, max_sites=1)
        row = {
            "rotation_quarter_turns": orientation,
            "ridge_tile": "26603" if orientation == 0 else "87079",
            "pairs": [],
            "source_nominal_support": "UNKNOWN",
            "source_post_to_cover_clutch": "UNKNOWN",
            "collision_count": 0,
            "completion": False,
            "physical_certification": "NOT_CERTIFIED",
        }
        if len(base["sites"]) != 1:
            output["blocking_reasons"].append(f"ORIENTATION_{orientation}_NO_SINGLE_SITE")
            output["orientations"].append(row)
            continue
        source = base["sites"][0]
        row["source_nominal_support"] = source["anchor_chain"]["status"]
        row["source_post_to_cover_clutch"] = source["post_to_tile"]
        if (source["status"] != "UNKNOWN_THREE_PART_CLUTCH_NOT_DEMONSTRATED"
                or not source["post_cell"]
                or len(source["slope_ids"]["negative"]) != 1
                or len(source["slope_ids"]["positive"]) != 1):
            output["blocking_reasons"].append(
                f"ORIENTATION_{orientation}_INVALID_076_PRECONDITIONS:{source['status']}")
            output["orientations"].append(row)
            continue
        parts_by_id = {p.placement_id: p for p in model.parts}
        components = {
            "central_post": _virtual_post(source, 0),
            "ridge_cover": _virtual_cover(source, 0),
            "negative_slope": parts_by_id[source["slope_ids"]["negative"][0]],
            "positive_slope": parts_by_id[source["slope_ids"]["positive"][0]],
        }
        try:
            meshes = {name: brick_model_part_to_instance(p, library)
                      for name, p in components.items()}
        except (FileNotFoundError, ValueError) as exc:
            output["blocking_reasons"].append(
                f"ORIENTATION_{orientation}_MISSING_GEOMETRY:{type(exc).__name__}:{exc}")
            output["orientations"].append(row)
            continue

        for first_name, second_name in COLLISION_PAIRS:
            a, b = meshes[first_name], meshes[second_name]
            relation = check_collision(a, b)
            entry = {
                "roles": [first_name, second_name],
                "part_ids": [components[first_name].part_id,
                             components[second_name].part_id],
                "ldraw_mesh_relation": relation.value,
                "status": "UNKNOWN",
                "verdict": "UNKNOWN",
                "reason": "LDRAW_SURFACE_CROSSING_NOT_PHYSICAL_MATING_PROOF",
                "documented_connector_count": len(find_connections(a, b)),
                "documented_stud_cell_overlap": [],
                "witnesses": None,
                "zone": "UNKNOWN_NO_MESH_CROSSING",
                "surface_identity": "UNKNOWN_LDRAW_TRIANGLES_HAVE_NO_STUD_OR_TUBE_FACE_TAGS",
            }
            if relation is Relation.COLLISION:
                row["collision_count"] += 1
                wa = _studs_documented(components[first_name])
                wb = _studs_documented(components[second_name])
                if wa is not None and wb is not None:
                    entry["documented_stud_cell_overlap"] = [
                        list(v) for v in sorted(wa & wb)
                    ]
                crossing = localize_crossing_triangles(a, b)
                entry["witnesses"] = crossing
                entry["zone"] = _classify_zone(
                    crossing, (first_name, second_name),
                    source["post_top_plane"])
                if crossing["crossing_witnesses_recorded"] == 0:
                    entry["reason"] = "MESH_COLLISION_WITHOUT_LOCALIZED_SURFACE_CROSSING"
                elif crossing["candidate_test_limit_reached"]:
                    entry["reason"] = "INCOMPLETE_LOCAL_CROSSING_SEARCH"
                else:
                    # Do NOT silently reclassify a rigid collision as legal
                    # stud insertion from connector guesses or aligned XY.
                    entry["reason"] = "REAL_TRIANGLE_SURFACE_CROSSING_REQUIRES_CONNECTOR_AWARE_REVIEW"
            else:
                entry["reason"] = f"PREVIOUS_COLLISION_NOT_REPRODUCED:{relation.value}"
                output["blocking_reasons"].append(
                    f"ORIENTATION_{orientation}_{first_name}_{second_name}_MISSING_COLLISION")
            row["pairs"].append(entry)
        row["completion"] = (
            len(row["pairs"]) == 3 and row["collision_count"] == 3
            and all(p["witnesses"] is not None
                    and p["witnesses"]["crossing_witnesses_recorded"] > 0
                    and not p["witnesses"]["candidate_test_limit_reached"]
                    for p in row["pairs"])
        )
        if not row["completion"]:
            output["blocking_reasons"].append(
                f"ORIENTATION_{orientation}_NOT_ALL_COLLISIONS_LOCALIZED")
        if model.model_dump_json() != snapshot:
            raise AssertionError("MODEL_MUTATED_DURING_079_DIAGNOSTIC")
        output["orientations"].append(row)

    output["complete_collision_localization"] = (
        all(v["mesh_loaded"] for v in output["required_parts"].values())
        and len(output["orientations"]) == len(orientations)
        and all(v["completion"] for v in output["orientations"])
        and not output["blocking_reasons"]
    )
    return output


def main():
    parser = argparse.ArgumentParser(description="Localize 078 ridge colliding surfaces")
    parser.add_argument("--ldraw-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = diagnose_three_ridge_collisions(args.ldraw_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    for orientation in result["orientations"]:
        print("ROOF_ORIENTATION", orientation["rotation_quarter_turns"],
              "COMPLETE", orientation["completion"])
        for pair in orientation["pairs"]:
            witnesses = pair["witnesses"]
            print("COLLISION_ZONE", "/".join(pair["roles"]),
                  "RELATION", pair["ldraw_mesh_relation"],
                  "REGION", pair["zone"],
                  "VERDICT", pair["verdict"],
                  "WITNESSES",
                  witnesses["crossing_witnesses_recorded"] if witnesses else None,
                  "XYZ_REGION",
                  witnesses["sample_envelope"]["approx_model_xyz_studs_plates"]
                  if witnesses and witnesses["sample_envelope"] else None,
                  "CONNECTOR_METADATA_COUNT", pair["documented_connector_count"],
                  "SHARED_TOP_STUD_CELLS", pair["documented_stud_cell_overlap"])
    print("COLLISION_LOCALIZATION_COMPLETE=", result["complete_collision_localization"])
    print("BLOCKING_REASONS=", result["blocking_reasons"])
    print("PHYSICAL_CERTIFICATION=", result["physical_certification"])
    if not result["complete_collision_localization"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
