"""Mission 020: bounded diagnostic of real LDraw mesh pairs involving B3 roof 30363.

Read-only. Uses the repository's existing LDrawLibrary, candidate_pairs,
check_collision and find_connections. Mesh intersection is NEVER automatically
called a forbidden solid overlap, even with a matching nominal connector.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import time

from lego_geometry_engine import (
    LDrawLibrary, Relation, check_collision, find_connections, instance_from_dict,
)
from lego_geometry_engine.spatial import candidate_pairs

MODEL = Path("missions/B3/generated/GUIDED004-B3-1904.ldr")
ROOF = "30363.dat"


def placements(path: Path):
    records = []
    identifier = None
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.startswith("0 // "):
            identifier = line[5:].strip()
        elif line.startswith("1 "):
            fields = line.split()
            if len(fields) != 15 or not identifier:
                raise ValueError(f"INVALID_LDRAW_RECORD:line={line_number}")
            records.append(dict(
                instance_id=identifier, part_id=fields[14].lower(), color=int(fields[1]),
                transform=[float(v) for v in fields[2:14]],
                origin_ldu=[float(v) for v in fields[2:5]],
            ))
            identifier = None
    count = Counter(part["part_id"] for part in records)
    if len(records) != 1904 or count[ROOF] != 408:
        raise ValueError(f"WRONG_B3_INVENTORY:{len(records)}:{count[ROOF]}")
    if len({part["instance_id"] for part in records}) != len(records):
        raise ValueError("DUPLICATE_LDRAW_INSTANCE_IDENTIFIERS")
    return records, count


def check_pair(a, b, original):
    # These are real mesh surfaces; a 3D bounding box alone never proves collision.
    relation = check_collision(a, b)
    connectors = find_connections(a, b)
    if relation is Relation.COLLISION:
        category = "MESH_INTERSECTION_REVIEW_REQUIRED"
    elif relation is Relation.CONTACT and connectors:
        category = "SURFACE_CONTACT_WITH_NOMINAL_COMPATIBLE_CONNECTORS"
    elif relation is Relation.CONTACT:
        category = "CONTACT_WITHOUT_DEMONSTRATED_CONNECTOR"
    elif connectors:
        category = "MESH_SEPARATED_CONNECTOR_ALIGNMENT_REVIEW_REQUIRED"
    else:
        category = "MESH_SEPARATED"
    return {
        "part_a": a.instance_id,
        "part_b": b.instance_id,
        "ref_a": original[a.instance_id]["part_id"],
        "ref_b": original[b.instance_id]["part_id"],
        "origin_a_ldu": original[a.instance_id]["origin_ldu"],
        "origin_b_ldu": original[b.instance_id]["origin_ldu"],
        "mesh_relation": relation.value,
        "nominal_connector_matches": len(connectors),
        "classification": category,
        "forbidden_material_collision_proven": False,
    }


def write_report(out_dir: Path, result):
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "B3-408-ROOF-MESH-AUDIT.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    m = result["metrics"]
    lines = [
        "# BOLDÜNGO B3 — Mission 020 — toiture LDraw réelle",
        "",
        f"**Verdict : {result['status']}**. Aucun modèle, pièce ou position modifié.",
        f"Source : \`{MODEL}\` ; bibliothèque : pybricks/ldraw épinglée à c43ed06a128a10ed65675166bf42eb6fd608b9b0.",
        "",
        "| Mesure | Valeur |", "|---|---:|",
    ]
    for key, value in m.items():
        lines.append(f"| {key} | {value} |")
    lines.extend([
        "",
        "Les intersections de maillages **nécessitent une expertise** : un emboîtement",
        "LEGO peut présenter une interférence nominale. Les alignements de connecteurs",
        "ne prouvent pas qu'une intersection de matière soit autorisée.",
        "Ni insertion, ni stabilité, ni connectibilité globale ne sont certifiées.",
        "",
        "## Paires nécessitant un examen",
    ])
    requiring = [p for p in result["pair_results"] if
                 p["classification"] not in {"MESH_SEPARATED",
                 "SURFACE_CONTACT_WITH_NOMINAL_COMPATIBLE_CONNECTORS"}]
    for p in requiring[:40]:
        lines.append(
            f"- \`{p['part_a']}\` ({p['ref_a']} {p['origin_a_ldu']}) / "
            f"\`{p['part_b']}\` ({p['ref_b']} {p['origin_b_ldu']}) : "
            f"**{p['classification']}** ({p['mesh_relation']})."
        )
    if not requiring:
        lines.append("- Aucun dans les paires testées (ceci ne certifie pas les paires restantes).")
    if len(requiring) > 40:
        lines.append(f"- {len(requiring)-40} autres en JSON.")
    (out_dir / "RAPPORT-MISSION-020.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def run(source: Path, root: Path, out: Path, max_pairs: int, max_seconds: int):
    start = time.monotonic()
    records, inventory = placements(source)
    roof_ids = [r["instance_id"] for r in records if r["part_id"] == ROOF]
    roof_set = set(roof_ids)
    original = {r["instance_id"]: r for r in records}
    library = LDrawLibrary(root)
    # The genuine 30363 polygon mesh MUST load before any global pass.
    slope = library.load_part(ROOF)
    if not slope.triangles:
        raise RuntimeError("30363_MESH_EMPTY")
    print(f"M020_FIRST_30363_MESH_LOADED triangles={len(slope.triangles)}", flush=True)
    # Load all source-referenced genuine meshes, no approximated part definitions.
    instances = [instance_from_dict(rec, library) for rec in records]
    print(f"M020_REAL_GEOMETRIES_LOADED instances={len(instances)} roof={len(roof_ids)}", flush=True)
    first = roof_ids[0]
    candidates = []
    discovery_truncated = False
    for a, b in candidate_pairs(instances):
        if a.instance_id not in roof_set and b.instance_id not in roof_set:
            continue
        candidates.append((a, b))
        if len(candidates) >= 250000:
            discovery_truncated = True
            break
    print(f"M020_SPATIAL_PAIRS={len(candidates)} truncated={discovery_truncated}", flush=True)
    # Check one real neighboring interface of the FIRST roof piece before all others.
    candidates.sort(key=lambda pair: (
        0 if first in (pair[0].instance_id, pair[1].instance_id) else 1,
        pair[0].instance_id, pair[1].instance_id,
    ))
    if candidates and first in (candidates[0][0].instance_id,
                                candidates[0][1].instance_id):
        print("M020_FIRST_ROOF_NEIGHBOR_FOUND", flush=True)
    elif not discovery_truncated:
        print("M020_FIRST_ROOF_NO_SPATIALLY_POSSIBLE_NEIGHBOR", flush=True)

    checked = []
    outcomes = Counter()
    tested_per_roof = Counter()
    possible_per_roof = Counter()
    for a, b in candidates:
        for iid in (a.instance_id, b.instance_id):
            if iid in roof_set:
                possible_per_roof[iid] += 1
    limit_reason = None
    for a, b in candidates:
        if len(checked) >= max_pairs:
            limit_reason = "MAX_MESH_PAIRS"
            break
        if time.monotonic() - start >= max_seconds:
            limit_reason = "MAX_WALL_TIME"
            break
        try:
            pair_result = check_pair(a, b, original)
        except Exception as exc:
            pair_result = {
                "part_a": a.instance_id, "part_b": b.instance_id,
                "ref_a": original[a.instance_id]["part_id"],
                "ref_b": original[b.instance_id]["part_id"],
                "origin_a_ldu": original[a.instance_id]["origin_ldu"],
                "origin_b_ldu": original[b.instance_id]["origin_ldu"],
                "classification": "INDETERMINATE_GEOMETRY_ENGINE_EXCEPTION",
                "mesh_relation": "INDETERMINATE",
                "nominal_connector_matches": 0,
                "reason": f"{type(exc).__name__}:{exc}",
                "forbidden_material_collision_proven": False,
            }
        checked.append(pair_result)
        outcomes[pair_result["classification"]] += 1
        for iid in (a.instance_id, b.instance_id):
            if iid in roof_set:
                tested_per_roof[iid] += 1
        if len(checked) <= 3 or len(checked) % 10 == 0:
            print(f"M020_PAIR_TESTED={len(checked)} class={pair_result['classification']}", flush=True)
    if discovery_truncated:
        limit_reason = "BROAD_PHASE_CANDIDATES_CAPPED"
    untested = len(candidates) - len(checked)
    roof_fully_examined = (
        sum(tested_per_roof[rid] == possible_per_roof[rid] for rid in roof_ids)
        if not discovery_truncated else 0
    )
    metrics = {
        "source_part_instances": len(records),
        "roof_30363_instances_with_real_mesh_loaded": len(roof_ids),
        "distinct_ldraw_part_families_loaded": len(inventory),
        "spatial_candidate_pairs_discovered": len(candidates),
        "mesh_pairs_actually_tested": len(checked),
        "roof_instances_in_at_least_one_tested_pair": len(tested_per_roof),
        "roof_instances_with_all_spatial_candidates_tested": roof_fully_examined,
        "candidate_pairs_not_mesh_tested": untested,
        "mesh_intersections_to_review": outcomes["MESH_INTERSECTION_REVIEW_REQUIRED"],
        "surface_contacts_with_nominal_connectors": outcomes["SURFACE_CONTACT_WITH_NOMINAL_COMPATIBLE_CONNECTORS"],
        "surface_contacts_without_proved_connection": outcomes["CONTACT_WITHOUT_DEMONSTRATED_CONNECTOR"],
        "mesh_separations": outcomes["MESH_SEPARATED"],
        "other_indeterminate": outcomes["INDETERMINATE_GEOMETRY_ENGINE_EXCEPTION"] +
                               outcomes["MESH_SEPARATED_CONNECTOR_ALIGNMENT_REVIEW_REQUIRED"],
        "forbidden_material_collisions_certified": "NOT_DEMONSTRATED",
        "global_buildability": "NOT_CERTIFIED",
        "broad_phase_complete": not discovery_truncated,
        "limit_reason": limit_reason or "NONE",
    }
    status = "BOUNDED_INCOMPLETE" if (untested or discovery_truncated) else "ALL_CANDIDATE_MESH_PAIRS_SAMPLED"
    report = {
        "status": status,
        "model": str(source),
        "pinned_ldraw_revision": "c43ed06a128a10ed65675166bf42eb6fd608b9b0",
        "metrics": metrics,
        "first_roof_instance": first,
        "outcomes": dict(outcomes),
        "pair_results": checked,
        "limitations": [
            "One snapshot of genuine LDraw surface meshes; not physical insertion or strength.",
            "AABB used for pair discovery only; never a material-collision proof.",
            "Collision-valued mesh results require manual classification of LEGO interference.",
            "Missing/unexamined candidate pairs are NOT known to be collision-free.",
        ],
    }
    write_report(out, report)
    print("M020_SUMMARY_JSON=" + json.dumps(metrics, sort_keys=True), flush=True)
    print(f"M020_REPORT={out / 'RAPPORT-MISSION-020.md'}", flush=True)
    return 0 if not outcomes["INDETERMINATE_GEOMETRY_ENGINE_EXCEPTION"] else 2


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", type=Path, default=MODEL)
    p.add_argument("--ldraw-root", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--max-pairs", type=int, default=60)
    p.add_argument("--max-seconds", type=int, default=540)
    args = p.parse_args()
    if args.max_pairs < 1 or args.max_seconds < 1:
        p.error("positive limits required")
    return run(args.model, args.ldraw_root, args.out, args.max_pairs, args.max_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
