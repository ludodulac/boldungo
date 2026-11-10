"""Mission 020: bounded diagnostic of real LDraw mesh pairs involving B3 roof 30363.

Read-only. Uses the repository's existing LDrawLibrary, candidate_pairs,
check_collision and find_connections. Mesh intersection is NEVER automatically
called a forbidden solid overlap, even with a matching nominal connector.
"""
from __future__ import annotations

import argparse
from collections import Counter
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


def run(source: Path, root: Path, out: Path, max_pairs: int, max_seconds: int,
        group_index: int | None = None, group_count: int = 8):
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
    # Exact canonical pair identity provides the same order on every runner.
    # Modulo partitioning distributes heavy/easy interfaces evenly, with no overlap.
    candidates.sort(key=lambda pair: tuple(sorted(
        (pair[0].instance_id, pair[1].instance_id)
    )))
    all_candidate_keys = [
        list(sorted((a.instance_id, b.instance_id))) for a, b in candidates
    ]
    if len({tuple(p) for p in all_candidate_keys}) != len(all_candidate_keys):
        raise ValueError("DUPLICATE_BROAD_PHASE_PAIR")
    if group_index is not None:
        if not (group_count == 8 and 0 <= group_index < group_count):
            raise ValueError("INVALID_B3_GROUP")
        selected = [pair for index, pair in enumerate(candidates)
                    if index % group_count == group_index]
    else:
        selected = candidates
    print(f"M023_GROUP={group_index}/{group_count} "
          f"candidate_pairs={len(selected)} global={len(candidates)}",
          flush=True)

    checked = []
    outcomes = Counter()
    tested_per_roof = Counter()
    possible_per_roof = Counter()
    for a, b in candidates:
        for iid in (a.instance_id, b.instance_id):
            if iid in roof_set:
                possible_per_roof[iid] += 1
    limit_reason = None
    for a, b in selected:
        if max_pairs > 0 and len(checked) >= max_pairs:
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
    untested = len(selected) - len(checked)
    roof_fully_examined = (
        sum(tested_per_roof[rid] == possible_per_roof[rid] for rid in roof_ids)
        if not discovery_truncated else 0
    )
    metrics = {
        "source_part_instances": len(records),
        "roof_30363_instances_with_real_mesh_loaded": len(roof_ids),
        "distinct_ldraw_part_families_loaded": len(inventory),
        "spatial_candidate_pairs_discovered": len(candidates),
        "group_expected_pairs": len(selected),
        "group_index": group_index,
        "group_count": group_count,
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
        "group_index": group_index,
        "group_count": group_count,
        # Full canonical manifest is repeated in every group. This permits
        # identifying exact missing pairs even when a different group fails.
        "all_candidate_keys": all_candidate_keys,
        "selected_candidate_keys": [
            all_candidate_keys[index] for index in range(len(candidates))
            if group_index is None or index % group_count == group_index
        ],
        "roof_instance_ids": roof_ids,
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
    if group_index is not None and (untested or discovery_truncated):
        return 2
    return 0 if not outcomes["INDETERMINATE_GEOMETRY_ENGINE_EXCEPTION"] else 2



def aggregate_reports(inputs: Path, out: Path, expected_groups: int = 8):
    """Aggregate ONLY completed group artifacts, proving no missing/duplicate pair.

    The full candidate manifest is included in every individual group artifact:
    even a missing group's exact pair IDs can therefore be enumerated.
    """
    files = sorted(inputs.glob("*/B3-408-ROOF-MESH-AUDIT.json"))
    reports = {}
    problems = []
    for file in files:
        try:
            item = json.loads(file.read_text(encoding="utf-8"))
            group = item["group_index"]
            if not isinstance(group, int) or not 0 <= group < expected_groups:
                raise ValueError(f"invalid group index {group}")
            if group in reports:
                raise ValueError(f"duplicate group {group}")
            reports[group] = item
        except (OSError, ValueError, KeyError, TypeError) as exc:
            problems.append(f"{file}: {type(exc).__name__}: {exc}")

    absent_groups = [i for i in range(expected_groups) if i not in reports]
    representative = next(iter(reports.values()), None)
    expected = (
        [tuple(ids) for ids in representative["all_candidate_keys"]]
        if representative is not None else []
    )
    expected_set = set(expected)
    if not representative:
        problems.append("No readable group artifact: cannot enumerate exact missing pairs")
    elif len(expected) != 1904 or len(expected_set) != len(expected):
        problems.append(
            f"Unexpected broad-phase manifest: {len(expected)} vs 1904, "
            f"{len(expected_set)} unique"
        )
    if expected != sorted(expected):
        problems.append("Manifest is not in canonical sorted pair order")
    if representative and (
        len(representative.get("roof_instance_ids", [])) != 408
        or len(set(representative["roof_instance_ids"])) != 408
    ):
        problems.append("Roof inventory is not exactly 408 unique IDs")

    seen = {}
    duplicates = []
    per_group_counts = {}
    for group, item in sorted(reports.items()):
        manifest = [tuple(ids) for ids in item.get("all_candidate_keys", [])]
        if manifest != expected:
            problems.append(f"Group {group}: candidate manifest differs")
        if item.get("group_count") != expected_groups:
            problems.append(f"Group {group}: expected exactly {expected_groups} groups")
        allocated = set(expected[group::expected_groups])
        declared = {tuple(ids) for ids in item.get("selected_candidate_keys", [])}
        if declared != allocated or len(item.get("selected_candidate_keys", [])) != len(allocated):
            problems.append(f"Group {group}: claimed allocation differs from canonical manifest")
        group_keys = set()
        for pair in item.get("pair_results", []):
            key = tuple(sorted((pair["part_a"], pair["part_b"])))
            if key in seen:
                duplicates.append([*key])
            else:
                seen[key] = pair
            if key in group_keys:
                problems.append(f"Group {group}: duplicate pair inside own report: {key}")
            group_keys.add(key)
            if key not in allocated:
                problems.append(f"Group {group}: pair outside assigned group: {key}")
        expected_local = len(allocated)
        actual_local = len(group_keys)
        per_group_counts[str(group)] = {
            "assigned": expected_local, "tested": actual_local,
            "missing": expected_local - len(allocated & group_keys),
            "status": item.get("status"),
            "limit_reason": item.get("metrics", {}).get("limit_reason"),
        }
        if len(item.get("pair_results", [])) != item.get("metrics", {}).get("mesh_pairs_actually_tested"):
            problems.append(f"Group {group}: result count and metric disagree")
        if actual_local < expected_local:
            problems.append(f"Group {group}: {expected_local - actual_local} assigned pairs not tested")

    extra = sorted(set(seen) - expected_set)
    missing = sorted(expected_set - set(seen))
    if extra:
        problems.append(f"Unexpected extra pairs: {len(extra)}")
    if duplicates:
        problems.append(f"Duplicate pair results: {len(duplicates)}")
    complete = (
        not absent_groups and not missing and not extra and not duplicates
        and not problems and len(seen) == 1904
    )
    results = list(seen.values())
    classification_counts = Counter(p["classification"] for p in results)
    roof_ids = set(representative.get("roof_instance_ids", [])) if representative else set()
    possible = Counter()
    for a, b in expected:
        if a in roof_ids:
            possible[a] += 1
        if b in roof_ids:
            possible[b] += 1
    tested = Counter()
    for a, b in seen:
        if a in roof_ids:
            tested[a] += 1
        if b in roof_ids:
            tested[b] += 1
    fully_examined = sum(tested[x] == possible[x] for x in roof_ids)
    exceptions = classification_counts["INDETERMINATE_GEOMETRY_ENGINE_EXCEPTION"]
    status = ("ANALYSE_GEOMETRIQUE_COMPLETE" if complete and not exceptions
              else "ANALYSE_GEOMETRIQUE_INCOMPLETE")
    intersections = [
        p for p in results if p["classification"] == "MESH_INTERSECTION_REVIEW_REQUIRED"
    ]
    metrics = {
        "groups_completed_with_artifact": len(reports),
        "groups_expected": expected_groups,
        "spatial_candidate_pairs_expected": len(expected),
        "unique_mesh_pairs_tested": len(seen),
        "duplicate_pair_results": len(duplicates),
        "pairs_unexamined": len(missing),
        "roof_instances_total": len(roof_ids),
        "roof_instances_with_all_candidates_tested": fully_examined,
        "mesh_intersections_to_review": len(intersections),
        "contacts_with_nominal_connectors": classification_counts[
            "SURFACE_CONTACT_WITH_NOMINAL_COMPATIBLE_CONNECTORS"
        ],
        "contacts_without_demonstrated_connector": classification_counts[
            "CONTACT_WITHOUT_DEMONSTRATED_CONNECTOR"
        ],
        "mesh_separations": classification_counts["MESH_SEPARATED"],
        "indeterminate": exceptions + classification_counts[
            "MESH_SEPARATED_CONNECTOR_ALIGNMENT_REVIEW_REQUIRED"
        ],
        "forbidden_material_collisions_certified": "NOT_DEMONSTRATED",
        "global_buildability": "NOT_CERTIFIED",
    }
    report = {
        "status": status, "metrics": metrics,
        "absent_groups": absent_groups, "group_counts": per_group_counts,
        "issues": problems,
        "missing_pairs": [list(x) for x in missing],
        "duplicate_pairs": duplicates,
        "unexpected_pairs": [list(x) for x in extra],
        "classification_counts": dict(classification_counts),
        "mesh_intersections": intersections,
        "all_pair_results": results,
        "limitations": [
            "All 1904 spatial candidate pairs is not all possible pair combinations.",
            "A surface intersection is NOT itself a proven forbidden collision.",
            "Nominal connector matching does not certify physical insertion.",
            "Neither stability nor whole-house LEGO constructibility is certified.",
        ],
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "B3-ROOF-GLOBAL-AUDIT.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        "# BOLDÜNGO — Mission 023 — huit groupes de toiture B3",
        "", f"**{status}** — analyse des maillages, pas certification LEGO.",
        "", "| Mesure | Résultat |", "|---|---:|",
    ]
    for key, val in metrics.items():
        lines.append(f"| {key} | {val} |")
    lines.extend(["", "## Répartition par groupe"])
    for group in range(expected_groups):
        if str(group) in per_group_counts:
            lines.append(f"- Groupe {group}: {per_group_counts[str(group)]}")
        else:
            lines.append(f"- Groupe {group}: **ARTEFACT ABSENT**")
    lines.extend(["", "## Paires dont le maillage présente une intersection"])
    for pair in intersections:
        lines.append(
            f"- {pair['part_a']} ({pair['ref_a']} ; {pair['origin_a_ldu']}) / "
            f"{pair['part_b']} ({pair['ref_b']} ; {pair['origin_b_ldu']})"
        )
    if not intersections:
        lines.append("- Aucune dans les paires analysées ; aucun certificat de constructibilité.")
    lines.extend(["", "## Paires manquantes"])
    for a, b in missing:
        lines.append(f"- {a} / {b}")
    if not missing:
        lines.append("- Aucune (si le manifest et les huit groupes sont validés).")
    lines.extend(["", "## Incohérences"])
    lines.extend(f"- {x}" for x in problems)
    if not problems:
        lines.append("- Aucune.")
    lines.extend(["", "## Précautions",
        "Boîtes englobantes : sélection spatiale uniquement.",
        "Un contact sans connecteur reste une connexion NON DÉMONTRÉE.",
        "Toute intersection de maillage doit être étudiée avant d'affirmer une collision interdite.",
        "Insertion et stabilité de la maison : NON CERTIFIÉES.",
    ])
    (out / "RAPPORT-GLOBAL-M023.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print("M023_GLOBAL_SUMMARY_JSON=" + json.dumps(metrics, sort_keys=True), flush=True)
    print(f"M023_GLOBAL_VERDICT={status}", flush=True)
    return 0 if status == "ANALYSE_GEOMETRIQUE_COMPLETE" else 2

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", type=Path, default=MODEL)
    p.add_argument("--ldraw-root", type=Path)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--max-pairs", type=int, default=60,
                   help="0 means no pair cap; wall-time cap still applies")
    p.add_argument("--max-seconds", type=int, default=540)
    p.add_argument("--group-index", type=int,
                   help="0-based index of a deterministic 8-way roof-pair partition")
    p.add_argument("--group-count", type=int, default=8)
    p.add_argument("--aggregate-dir", type=Path,
                   help="Consolidate the eight uploaded reports without recomputing meshes")
    args = p.parse_args()
    if args.aggregate_dir is not None:
        return aggregate_reports(args.aggregate_dir, args.out, args.group_count)
    if args.ldraw_root is None:
        p.error("--ldraw-root required for mesh checks")
    if args.max_pairs < 0 or args.max_seconds < 1:
        p.error("max-pairs >= 0 and max-seconds >= 1 required")
    return run(args.model, args.ldraw_root, args.out, args.max_pairs,
               args.max_seconds, args.group_index, args.group_count)


if __name__ == "__main__":
    raise SystemExit(main())
