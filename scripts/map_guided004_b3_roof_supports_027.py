"""M027 — read-only roof support candidate map for real B3 GUIDED004.

Uses pinned genuine LDraw meshes and M026's source-proven 30363 *upper*
studs. AABB proximity or ordinary brick stud position NEVER proves a lower
30363 socket, physical contact, safe insertion, or load-bearing stability.
No collision scan is rerun.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path

from lego_geometry_engine import LDrawLibrary, find_connections, instance_from_dict
from audit_guided004_b3_roof_020 import MODEL, ROOF, placements

NEAR_BELOW_LDU = 32.0
POSSIBLE_GAP_MIN_LDU = -4.0
POSSIBLE_GAP_MAX_LDU = 8.0


def overlaps_xz(a, b, epsilon=0.001):
    # Broad phase only. Positive projected AABB intersection is not a mate.
    return all(
        min(a.maximum[i], b.maximum[i]) - max(a.minimum[i], b.minimum[i]) > epsilon
        for i in (0, 2)
    )


def stud_sites(instance):
    """Top studs whose SOURCE-DEFINED connector axis really points upwards."""
    for connector in instance.definition.connectors:
        if connector.type != "stud":
            continue
        axis = instance.transform.vector(connector.orientation)
        if abs(axis[0]) > 1e-5 or abs(axis[1] + 1.0) > 1e-5 or abs(axis[2]) > 1e-5:
            continue
        yield instance.transform.point(connector.position)


def in_horizontal_bounds(pos, box, epsilon=0.25):
    return (box.minimum[0] - epsilon <= pos[0] <= box.maximum[0] + epsilon
            and box.minimum[2] - epsilon <= pos[2] <= box.maximum[2] + epsilon)


def under_candidacy(roof, support, original):
    """Evidence of potential placement beneath, NOT evidence of a real joint."""
    rb, sb = roof.bbox, support.bbox
    if not overlaps_xz(rb, sb):
        return None

    # In LDraw Y increases DOWNWARD. For an ordinary upright brick a stud
    # connector has its NOMINAL top-mating plane at y=0 relative to its body.
    # We have no underside connector or complete solid shell for 30363.
    sites = [list(pos) for pos in stud_sites(support)
             if in_horizontal_bounds(pos, rb)]
    gaps = [round(site[1] - rb.maximum[1], 4) for site in sites]
    nearest = min(gaps, key=abs) if gaps else None
    if nearest is not None and POSSIBLE_GAP_MIN_LDU <= nearest <= POSSIBLE_GAP_MAX_LDU:
        category = "POSSIBLE_UNPROVEN"
        reason = ("Ordinary support top stud aligned in plan, at nominal vertical "
                  "proximity to slope lower mesh extent; 30363 underside socket unknown")
    elif nearest is not None and -NEAR_BELOW_LDU <= nearest <= NEAR_BELOW_LDU:
        category = "INDETERMINATE_NEAR"
        reason = ("Nearby stud plane but insufficient evidence for a lower "
                  "slope interface; AABB and vertical gap cannot prove contact")
    elif (sb.minimum[1] <= rb.maximum[1] + NEAR_BELOW_LDU and
          sb.maximum[1] >= rb.maximum[1] - NEAR_BELOW_LDU):
        category = "INDETERMINATE_NEAR"
        reason = ("Near projected geometry but no suitable recognized upright "
                  "support stud, or the slope underside is not located")
    else:
        return None
    data = original[support.instance_id]
    return {
        "id": support.instance_id, "ldraw_ref": data["part_id"],
        "origin_ldu": data["origin_ldu"],
        "transform_ldraw": data["transform"],
        "geometry_bbox_ldu": {
            "minimum": list(sb.minimum), "maximum": list(sb.maximum)
        },
        "studs_projected_under_slope_ldu": sites,
        "nearest_stud_plane_to_slope_lowest_mesh_ldu": nearest,
        "candidate_type": category,
        "reason": reason,
        "connection_beneath_30363_proven": False,
    }


def potential_roof_neighbor(roof, other, original):
    rb, sb = roof.bbox, other.bbox
    if not overlaps_xz(rb, sb):
        return None
    # A roof fragment lying deeper in global Y *might* be beneath this
    # fragment. With no 30363 underside socket, such cases are ambiguous.
    dy = sb.maximum[1] - rb.maximum[1]
    if -4.0 <= dy <= NEAR_BELOW_LDU and (
        sb.minimum[1] >= rb.minimum[1] - NEAR_BELOW_LDU
    ):
        return {
            "id": other.instance_id,
            "ldraw_ref": original[other.instance_id]["part_id"],
            "origin_ldu": original[other.instance_id]["origin_ldu"],
            "bbox_vertical_bottom_delta_ldu": round(dy, 4),
            "candidate_type": "INDETERMINATE_SLOPE_BENEATH",
            "reason": "Slope-to-slope projected overlap near lower extent; underside unknown",
            "connection_beneath_30363_proven": False,
        }
    return None


def diagnose(root: Path, out: Path, json_out: Path):
    records, inventory = placements(MODEL)
    original = {r["instance_id"]: r for r in records}
    library = LDrawLibrary(root)
    instances = [instance_from_dict(record, library) for record in records]
    slopes = sorted((p for p in instances if p.definition.part_id == ROOF),
                    key=lambda p: p.instance_id)
    ordinary = sorted((p for p in instances if p.definition.part_id != ROOF),
                      key=lambda p: p.instance_id)
    if len(slopes) != 408 or len(ordinary) != 1496:
        raise ValueError(f"UNEXPECTED_B3_COUNTS:{len(slopes)}:{len(ordinary)}")

    source_studs = {
        (tuple(c.position), c.type)
        for c in slopes[0].definition.connectors
    }
    if source_studs != {
        ((-10.0, 0.0, 0.0), "stud"), ((10.0, 0.0, 0.0), "stud")
    }:
        raise ValueError(f"M026_30363_STUD_SOURCE_NOT_VERIFIED:{source_studs}")
    if any(c.type == "anti_stud" for c in slopes[0].definition.connectors):
        raise ValueError("UNEXPECTED_30363_UNDERSIDE_CONNECTOR")

    rows, top_pairs, sample_candidates = [], [], []
    totals = Counter()
    for roof in slopes:
        rb = roof.bbox
        possible, unknown, roof_neighbors, top_mates = [], [], [], []
        for support in ordinary:
            if not overlaps_xz(rb, support.bbox):
                continue
            candidate = under_candidacy(roof, support, original)
            if candidate is not None:
                (possible if candidate["candidate_type"] == "POSSIBLE_UNPROVEN"
                 else unknown).append(candidate)
            # Independently count upper stud -> ordinary underside matches.
            # No collision clearance or lower support is inferred from these.
            roof_studs = [
                roof.transform.point(c.position)
                for c in roof.definition.connectors if c.type == "stud"
            ]
            if all(abs(stud[1] - support.bbox.maximum[1]) > 40
                   for stud in roof_studs):
                continue
            for conn in find_connections(roof, support):
                datum = {
                    "roof_id": roof.instance_id,
                    "part_above_id": support.instance_id,
                    "part_above_ref": original[support.instance_id]["part_id"],
                    "part_above_origin_ldu": original[support.instance_id]["origin_ldu"],
                    "nominal_stud_world_ldu": list(conn["position"]),
                    "type": conn["type"],
                    "physical_contact_or_clearance_certified": False,
                    "lower_30363_support_proven": False,
                }
                top_mates.append(datum)
                top_pairs.append(datum)
        for other in slopes:
            if roof.instance_id == other.instance_id:
                continue
            candidate = potential_roof_neighbor(roof, other, original)
            if candidate is not None:
                roof_neighbors.append(candidate)
        possible.sort(key=lambda x: (
            abs(x["nearest_stud_plane_to_slope_lowest_mesh_ldu"] or 0),
            x["id"],
        ))
        unknown.sort(key=lambda x: x["id"])
        roof_neighbors.sort(key=lambda x: x["id"])
        top_mates.sort(key=lambda x: (x["part_above_id"], x["nominal_stud_world_ldu"]))

        # No nominal UNDER-30363 connections can yet be demonstrated.
        if possible:
            cat = "B_POSSIBLE_SUPPORT_CONNECTION_UNPROVEN"
        elif unknown or roof_neighbors:
            cat = "D_GEOMETRICALLY_INDETERMINATE"
        else:
            cat = "C_NO_LOWER_SUPPORT_IDENTIFIED"
        totals[cat] += 1
        data = original[roof.instance_id]
        row = {
            "roof_id": roof.instance_id,
            "ldraw_ref": data["part_id"],
            "origin_ldu": data["origin_ldu"],
            "transform_ldraw": data["transform"],
            "bbox_ldu": {"minimum": list(rb.minimum), "maximum": list(rb.maximum)},
            "category": cat,
            "nominal_lower_connections_proven": 0,
            "possible_ordinary_supports": possible,
            "indeterminate_ordinary_neighbors": unknown,
            "indeterminate_slope_neighbors": roof_neighbors,
            "upper_30363_stud_nominal_matches": top_mates,
            "upper_matches_do_not_prove_lower_support": True,
        }
        rows.append(row)
        for support in possible:
            sample_candidates.append((support["ldraw_ref"] != "3004.dat",
                                      abs(support["nearest_stud_plane_to_slope_lowest_mesh_ldu"]),
                                      roof.instance_id, support["id"], row, support))

    if sum(totals.values()) != 408:
        raise AssertionError("Not all 408 slopes uniquely classified")

    selected = None
    if sample_candidates:
        _, _, _, _, r, s = sorted(sample_candidates) [0]
        selected = {
            "roof": {key: r[key] for key in
                     ("roof_id", "ldraw_ref", "origin_ldu", "transform_ldraw")},
            "support": s,
            "selection": "real ordinary-piece candidate with close nominal top-stud plane"
                         " (prefer 3004 if present)",
            "under_30363_connector_and_physical_fit": "NOT_DEMONSTRATED",
        }
    else:
        for r in rows:
            if r["indeterminate_ordinary_neighbors"]:
                s = r["indeterminate_ordinary_neighbors"][0]
                selected = {
                    "roof": {key: r[key] for key in
                             ("roof_id", "ldraw_ref", "origin_ldu", "transform_ldraw")},
                    "support": s,
                    "selection": "nearest unknown ordinary-piece neighbor, not a proven support",
                    "under_30363_connector_and_physical_fit": "NOT_DEMONSTRATED",
                }
                break

    overview = {
        "model": str(MODEL),
        "source_count": len(records),
        "roof_count": len(slopes),
        "other_parts_count": len(ordinary),
        "ldraw_library_revision": "c43ed06a128a10ed65675166bf42eb6fd608b9b0",
        "categories": {
            "A_lower_nominal_connection": 0,
            "B_possible_not_demonstrated":
                totals["B_POSSIBLE_SUPPORT_CONNECTION_UNPROVEN"],
            "C_no_support_identified":
                totals["C_NO_LOWER_SUPPORT_IDENTIFIED"],
            "D_geometric_indeterminate":
                totals["D_GEOMETRICALLY_INDETERMINATE"],
        },
        "slopes_with_upper_nominal_matches":
            len({pair["roof_id"] for pair in top_pairs}),
        "upper_nominal_connector_pairs": len(top_pairs),
        "total_possible_ordinary_roof_support_pairs":
            sum(len(r["possible_ordinary_supports"]) for r in rows),
        "slopes_with_unresolved_roof_below_neighbor":
            sum(bool(r["indeterminate_slope_neighbors"]) for r in rows),
        "exactly_one_category_per_slope": sum(totals.values()) == 408,
        "lower_slope_sockets_proven": 0,
        "physical_collision_scan_repeated": False,
        "model_modified": False,
        "load_bearing_certification": "NOT_CERTIFIED",
    }
    print("M027_REAL_GEOMETRY_LOADED=1904 roof=408", flush=True)
    print("M027_SUMMARY_JSON=" + json.dumps(overview, sort_keys=True), flush=True)
    print("M027_SELECTED_PAIR_JSON=" + json.dumps(selected, sort_keys=True), flush=True)

    result = {
        "summary": overview, "selected_real_pair": selected,
        "per_slope": rows, "upper_nominal_mates": top_pairs,
        "rules": {
            "axis": "world LDraw Y increases DOWN",
            "horizontal_candidate": "positive overlap of genuine mesh X/Z AABB only",
            "B_candidate": ("real ordinary brick upward top stud site projects into roof "
                            "mesh XY? NO: world X/Z footprint, stud Y within [-4,+8] "
                            "LDU of lowest slope mesh Y; an indication only"),
            "D_candidate": ("stud or other roof mesh nearby in space but clearance "
                            "cannot be confirmed; lower 30363 socket unknown"),
            "upper_studs": ("M026 two verified top studs; nominal match to OTHER "
                            "part underside only, never evidence of support below"),
            "forbidden": ("No connector inferred from bbox; no physical fit, "
                          "collision clearance, stability or insertion certified"),
        },
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
    lines = [
        "# BOLDÜNGO — MISSION 027 — CARTOGRAPHIE DES APPUIS DE TOITURE",
        "",
        "**Cartographie géométrique uniquement, aucune certification de construction.**",
        f"Modèle : \`{MODEL}\` — **1 904** pièces réelles, **408** pentes \`30363.dat\`.",
        "Bibliothèque LDraw réelle épinglée : \`pybricks/ldraw@c43ed06a128a10ed65675166bf42eb6fd608b9b0\`.",
        "",
        "## Répartition : chaque pente reçoit exactement UNE catégorie",
        f"- **A — connexion nominale sous la pente démontrée : 0** "
        "(le moteur M026 ne connaît AUCUN logement inférieur 30363).",
        f"- **B — appui inférieur géométriquement possible, non démontré : "
        f"{overview['categories']['B_possible_not_demonstrated']}**.",
        f"- **C — aucune pièce d'appui inférieure identifiée : "
        f"{overview['categories']['C_no_support_identified']}**.",
        f"- **D — géométrie voisine mais appui indéterminé : "
        f"{overview['categories']['D_geometric_indeterminate']}**.",
        f"- **Connexions nominales utilisant les tenons SUPÉRIEURS (distinctes "
        f"des appuis) : {overview['slopes_with_upper_nominal_matches']} pentes, "
        f"{overview['upper_nominal_connector_pairs']} correspondances.**",
        "",
        "Ces catégories ne prouvent ni l'appui physique, ni la fixation, ni "
        "l'absence de collision matérielle.",
        "B signifie seulement : tenon supérieur d'une brique ordinaire existante "
        "proche en projection horizontale et en altitude de la limite inférieure "
        "du maillage de la pente. Aucune face inférieure de 30363 n'est identifiée "
        "comme logement. C signifie 'non identifié par cette méthode', pas "
        "'physiquement absent'. D signifie 'proximité sans information suffisante'.",
        "",
        "## Paire réelle proposée pour la suite",
    ]
    if selected:
        lines.extend([
            f"- Pente : \`{selected['roof']['roof_id']}\` "
            f"({selected['roof']['ldraw_ref']}), origine "
            f"{selected['roof']['origin_ldu']} LDU.",
            f"- Pièce candidate : \`{selected['support']['id']}\` "
            f"({selected['support']['ldraw_ref']}), origine "
            f"{selected['support']['origin_ldu']} LDU.",
            f"- Plan nominal de tenon ordinaire / pente : "
            f"{selected['support'].get('nearest_stud_plane_to_slope_lowest_mesh_ldu')} "
            "LDU d'écart ; **emboîtement sous la pente NON DÉMONTRÉ**.",
        ])
    else:
        lines.append("- Aucune paire de support ordinaire candidate localisée ; "
                     "ne pas inventer de connexion.")

    zone_counts = defaultdict(Counter)
    for r in rows:
        zone_counts[str(r["origin_ldu"][2])][r["category"]] += 1
    lines.extend([
        "",
        "## Zones par position Z LDraw (le long de la toiture)",
        "| Plan Z (LDU) | B possibles | C sans appui identifié | D indéterminés |",
        "|---:|---:|---:|---:|",
    ])
    for zone in sorted(zone_counts, key=lambda s: float(s)):
        count = zone_counts[zone]
        lines.append(
            f"| {zone} | {count['B_POSSIBLE_SUPPORT_CONNECTION_UNPROVEN']} | "
            f"{count['C_NO_LOWER_SUPPORT_IDENTIFIED']} | "
            f"{count['D_GEOMETRICALLY_INDETERMINATE']} |"
        )
    lines.extend([
        "", "## Détail complet des 408 pentes",
        "Les listes complètes de pièces candidates contiennent les **identifiants, "
        "références LEGO, coordonnées LDraw et transformations** dans "
        "\`CARTOGRAPHIE-APPUIS-M027.json\`. Ci-dessous, chaque pente est "
        "classée une seule fois.",
        "",
        "| Pente | Origine LDraw (X,Y,Z) | Cat. | B possibles | D ordinaires | "
        "D pentes | Conn. haut | 1re pièce candidate |",
        "|---|---|:--:|---:|---:|---:|---:|---|",
    ])
    label = {"B_POSSIBLE_SUPPORT_CONNECTION_UNPROVEN": "B",
             "C_NO_LOWER_SUPPORT_IDENTIFIED": "C",
             "D_GEOMETRICALLY_INDETERMINATE": "D"}
    for row in rows:
        candidates = (row["possible_ordinary_supports"]
                      or row["indeterminate_ordinary_neighbors"]
                      or row["indeterminate_slope_neighbors"])
        first = f"{candidates[0]['id']} ({candidates[0]['ldraw_ref']})" if candidates else "—"
        lines.append(
            f"| {row['roof_id']} | {row['origin_ldu']} | "
            f"{label[row['category']]} | "
            f"{len(row['possible_ordinary_supports'])} | "
            f"{len(row['indeterminate_ordinary_neighbors'])} | "
            f"{len(row['indeterminate_slope_neighbors'])} | "
            f"{len(row['upper_30363_stud_nominal_matches'])} | {first} |"
        )
    lines.extend([
        "", "## Limites et précautions",
        "- Contrôle de voisinage et d'alignements nominaux seulement. "
        "Le moteur de collision maillage **n'a pas été relancé**.",
        "- Utilisation du véritable AABB des maillages pour la présélection : "
        "ce n'est **pas** une preuve de contact, support ou absence de collision.",
        "- La pièce 30363 n'a que les deux **tenons supérieurs** validés M026. "
        "Aucun logement inférieur n'est prouvé, aucune famille inventée.",
        "- Les situations C et D sont des priorités d'examen, pas une preuve "
        "de chute des pièces ; B n'est pas physiquement certifié.",
        "- Ni chemin d'insertion, ni force d'emboîtement, ni rigidité ni "
        "stabilité de la toiture ne sont démontrés.",
        "- Aucune pièce du modèle B3 n'a été déplacée ou modifiée.",
    ])
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("M027_REPORT=" + str(out), flush=True)
    print("M027_JSON=" + str(json_out), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ldraw-root", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--json-out", required=True, type=Path)
    args = parser.parse_args()
    diagnose(args.ldraw_root, args.out, args.json_out)


if __name__ == "__main__":
    main()
