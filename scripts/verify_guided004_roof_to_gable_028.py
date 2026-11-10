"""Mission 028: source-traced real slope/brick interface, exactly one B3 pair.

Not a mating or solidity engine. Reuse LDrawLibrary/find_connections and
check_collision for REAL meshes. No fictional lower-slope connectors.
"""
from __future__ import annotations

import argparse
import json
from math import hypot
from pathlib import Path

from lego_geometry_engine import LDrawLibrary, Relation, check_collision, find_connections, instance_from_dict
from lego_geometry_engine.core import CONTACT_EPS, _tri_intersection_kind
from audit_guided004_b3_roof_020 import MODEL, placements

ROOF_ID = "roof-000048"
SUPPORT_ID = "gable-000006"
REVISION = "c43ed06a128a10ed65675166bf42eb6fd608b9b0"


def reference_records(path, primitive_name):
    """Enumerate explicit *type-1* uses of one documented LDraw primitive."""
    result = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        f = line.strip().split()
        if f and f[0] == "1" and len(f) == 15 and f[-1].lower().replace("\\", "/") == primitive_name:
            result.append({
                "line": number, "file": path.name,
                "primitive": primitive_name,
                "position_ldu": [float(x) for x in f[2:5]],
                "orientation": [float(x) for x in f[5:14]],
                "source_record": line.strip(),
            })
    return result


def relative_local(world, instance):
    """Invert only the two audited orthonormal B3 rotations."""
    m = instance.transform.matrix
    d = [world[i] - m[i][3] for i in range(3)]
    return [sum(m[row][axis] * d[row] for row in range(3)) for axis in range(3)]


def intersection_witnesses(a, b, cap=8):
    """Use the existing engine's triangle intersection routine, one pair only."""
    meshes_b = []
    for index, t in enumerate(b.triangles):
        lo = [min(v[k] for v in t) for k in range(3)]
        hi = [max(v[k] for v in t) for k in range(3)]
        meshes_b.append((index, t, lo, hi))
    examples = []
    for i, tri_a in enumerate(a.triangles):
        lo_a = [min(v[k] for v in tri_a) for k in range(3)]
        hi_a = [max(v[k] for v in tri_a) for k in range(3)]
        for j, tri_b, lo_b, hi_b in meshes_b:
            if any(hi_a[k] < lo_b[k] - CONTACT_EPS or hi_b[k] < lo_a[k] - CONTACT_EPS
                   for k in range(3)):
                continue
            if _tri_intersection_kind(tri_a, tri_b) is Relation.COLLISION:
                examples.append({"roof_triangle_index": i, "brick_triangle_index": j,
                                 "roof_triangle_world_ldu": tri_a,
                                 "brick_triangle_world_ldu": tri_b})
                if len(examples) >= cap:
                    return examples
    return examples


def analyze(root: Path, output: Path, jsonout: Path):
    records, counts = placements(MODEL)
    src = {r["instance_id"]: r for r in records}
    ra, sa = src[ROOF_ID], src[SUPPORT_ID]
    if (ra["part_id"], ra["origin_ldu"]) != ("30363.dat", [470., -816., 60.]):
        raise ValueError("ROOF_RECORD_CHANGED")
    if (sa["part_id"], sa["origin_ldu"]) != ("3004.dat", [480., -792., 50.]):
        raise ValueError("SUPPORT_RECORD_CHANGED")
    library = LDrawLibrary(root)
    roof = instance_from_dict(ra, library)
    support = instance_from_dict(sa, library)
    sub30363 = root / "parts" / "s" / "30363s01.dat"
    sub3004 = root / "parts" / "s" / "3004s01.dat"
    if not (sub30363.is_file() and sub3004.is_file()):
        raise FileNotFoundError("MISSING_REAL_LDRAW_SUBPART_30363_OR_3004")
    tube_a = reference_records(sub30363, "stud4a.dat")
    tube_s = reference_records(sub30363, "stud4s.dat")
    roof_top_studs = reference_records(sub30363, "stud.dat")
    brick_studs = reference_records(sub3004, "stud.dat")
    if len(tube_a) != 3 or len(tube_s) != 2 or len(brick_studs) != 2 or len(roof_top_studs) != 2:
        raise ValueError("PINNED_LDRAW_PRIMITIVES_NOT_AS_EXPECTED")
    lib_primitive = root / "p" / "stud4a.dat"
    if not lib_primitive.is_file() or "Stud Tube Open" not in lib_primitive.read_text(encoding="utf-8").splitlines()[0]:
        raise ValueError("UNSUPPORTED_STUD4A_PRIMITIVE")
    stud_source = root / "p" / "stud.dat"
    if not stud_source.is_file() or stud_source.read_text(encoding="utf-8").splitlines()[0].strip() != "0 Stud":
        raise ValueError("UNSUPPORTED_STUD_PRIMITIVE")
    tube_list = []
    for t in tube_a:
        center = roof.transform.point(t["position_ldu"])
        tube_list.append({**t, "world_axis_origin_ldu": list(center),
                          "world_axis_direction": list(roof.transform.vector((0, -1, 0))),
                          "role": "SOURCE_CYLINDRICAL_TUBE_NOT_CERTIFIED_UNDERSIDE_CONNECTOR"})
    angled_list = [
        {**t, "world_axis_origin_ldu": list(roof.transform.point(t["position_ldu"])),
         "role": "SOURCE_SLOPED_TUBE_FRAGMENT_NOT_STANDALONE_MATING_SITE"}
        for t in tube_s
    ]
    support_sites = []
    for stud in brick_studs:
        loc = support.transform.point(stud["position_ldu"])
        local = relative_local(loc, roof)
        candidates = [
            {"tube_subpart_line": t["line"],
             "horizontal_axis_distance_ldu": round(hypot(local[0]-t["position_ldu"][0],
                                                        local[2]-t["position_ldu"][2]), 6),
             "center_y_difference_ldu": round(local[1]-t["position_ldu"][1], 6)}
            for t in tube_a
        ]
        support_sites.append({
            **stud,
            "stud_center_world_ldu": list(loc),
            "stud_tip_world_ldu": list(support.transform.point((
                stud["position_ldu"][0], stud["position_ldu"][1] - 4,
                stud["position_ldu"][2]
            ))),
            "stud_center_in_slope_local_ldu": [round(x, 6) for x in local],
            "nearest_tube_axis_distance_ldu": min(p["horizontal_axis_distance_ldu"]
                                                   for p in candidates),
            "near_tubes": candidates,
            "matches_any_documented_tube_center_exactly": any(
                p["horizontal_axis_distance_ldu"] < 1e-6 for p in candidates
            ),
        })
    matches = find_connections(roof, support)
    collision = check_collision(roof, support)
    witness = intersection_witnesses(roof, support) if collision is Relation.COLLISION else []
    report = {
        "mission": "M028",
        "pinned_ldraw_revision": REVISION,
        "source_model": str(MODEL),
        "total_parts": len(records), "roof_count": counts["30363.dat"],
        "pair": [ra, sa],
        "meshes": {
            "roof_triangles": len(roof.triangles), "brick_triangles": len(support.triangles),
            "roof_bbox_ldu": [list(roof.bbox.minimum), list(roof.bbox.maximum)],
            "brick_bbox_ldu": [list(support.bbox.minimum), list(support.bbox.maximum)],
            "mesh_relation": collision.value,
            "strict_noncoplanar_triangle_witnesses_capped_at_8": witness,
        },
        "primitive_sources": {
            "brick_studs_source": "parts/s/3004s01.dat",
            "slope_underside_tubes_source": "parts/s/30363s01.dat",
            "slope_bottom_tube_open_geometry": "p/stud4a.dat",
            "brick_stud_geometry": "p/stud.dat",
            "slope_tube_axes": tube_list,
            "slope_tube_slope_fragments": angled_list,
            "slope_top_studs": roof_top_studs,
            "brick_studs": support_sites,
        },
        "connector_matches_between_real_pieces": matches,
        "nominal_lower_mate_demonstrated": False,
        "physical_mating_verdict": "C_INDETERMINE",
        "reason": ("One stud (470,-792,50) projects into slope footprint, but "
                   "in slope-local coordinates it is (10,24,0), not on any "
                   "source-defined central underside tube axis (0,z=-10/-30/-50). "
                   "LDraw surfaces define tubes and voids, not a verified "
                   "receiving clutch site at (10,24,0); a stud can potentially "
                   "engage between tubes, so noncoincident centers do NOT exclude "
                   "mating. The other 3004 stud is outside slope footprint. "
                   "Mesh surface intersections alone cannot certify solid interference."),
        "limits": [
            "No underside anti_stud connector invented for 30363.",
            "No load-bearing under-slope fit or insertion path demonstrated.",
            "AABB only used to contextualize geometry, not infer mating.",
            "No other B3 pair, roof or mesh scan executed.",
        ],
        "model_mutated": False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    jsonout.parent.mkdir(parents=True, exist_ok=True)
    jsonout.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n",encoding="utf-8")
    lines = [
        "# BOLDÜNGO — M028 : une jonction réelle sous la pente 30363",
        "",
        "**Verdict C — INDÉTERMINÉ : aucune connexion porteuse démontrée ni exclusion démontrée.**",
        f"Modèle : \`{MODEL}\` ; 1 904 pièces, 408 pentes, aucune transformation.",
        f"Bibliothèque réelle épinglée : \`{REVISION}\`.",
        "",
        "## Pièces et positions",
        f"- \`{ROOF_ID}\` 30363.dat : {ra['origin_ldu']} LDU, orientation {ra['transform'][3:]}",
        f"- \`{SUPPORT_ID}\` 3004.dat : {sa['origin_ldu']} LDU, orientation {sa['transform'][3:]}",
        "",
        "## Primitives réelles tracées",
        f"- Brique 3004 : **2 vrais tenons \`p/stud.dat\`** (via "
        f"\`parts/s/3004s01.dat\`) aux coordonnées mondiales "
        f"{[x['stud_center_world_ldu'] for x in support_sites]}.",
        f"- Pente 30363 : **3 sources \`p/stud4a.dat\`** de tube ouvert "
        f"(via \`parts/s/30363s01.dat\`) ; centres des axes mondiaux "
        f"{[x['world_axis_origin_ldu'] for x in tube_list]}.",
        f"- Pente : {len(angled_list)} fragments inclinés \`stud4s.dat\` "
        "relevés. Tenons sur le dessus **séparés** de ces tubes.",
        "",
        "## Décalages de la jonction actuelle",
    ]
    for t in support_sites:
        lines.append(
            f"- Tenon 3004 \`{t['stud_center_world_ldu']}\` : "
            f"position dans la pente locale \`{t['stud_center_in_slope_local_ldu']}\` ; "
            f"écart horizontal au plus proche axe de tube sous pente : "
            f"**{t['nearest_tube_axis_distance_ldu']} LDU**. "
            f"Écarts aux 3 axes : "
            f"{[v['horizontal_axis_distance_ldu'] for v in t['near_tubes']]} LDU."
        )
    lines.extend([
        "",
        "La présence d'un tube cylindrique ne prouve pas que son centre soit "
        "le point d'engagement d'un tenon extérieur : le tenon peut s'insérer "
        "**entre** tubes et parois. L'écart de centres ne constitue donc "
        "**pas** une exclusion mécanique.",
        "",
        "## Contact, collision et fixation",
        f"- Maillage pente : {len(roof.triangles)} triangles ; brique : "
        f"{len(support.triangles)} triangles.",
        f"- \`check_collision\` de l'**unique paire** : "
        f"**{collision.value}** ; {len(witness)} témoin(s) de croisements "
        "non coplanaires (8 au maximum).",
        f"- \`find_connections\` : {len(matches)} connecteur(s) reconnus "
        "entre ces deux pièces. La bibliothèque M026 ne modélise aucun "
        "logement inférieur utilisable sur 30363.",
        "- Aucun verdict de collision de maillage ne prouve à lui seul une "
        "interférence interdite entre corps rigides, particulièrement pour "
        "les maillages ouverts LDraw.",
        "- **C — INDÉTERMINÉ** : le détail de réception sous la pente (formes "
        "de vide utilisables par tenon, leurs tolérances et insertion) "
        "n'est pas suffisamment documenté/qualifié pour confirmer A ou B.",
        "",
        "## Conséquence pour les futurs appuis",
        "- La catégorie B de M027 reste **appui géométriquement possible**, "
        "pas connexion porteuse validée.",
        "- Un prochain contrôle doit déterminer une surface d'appui/une "
        "cavité compatible spécifique à la position locale (10,24,0), "
        "sans inventer de connecteur d'après l'AABB.",
        "- Aucune pente, pignon, mur, terrasse, photo ou code de collision modifié.",
        "",
        "Preuves chiffrées exhaustives : \`PREUVES-JONCTION-M028.json\` "
        "dans l'artefact GitHub Actions du job.",
    ])
    output.write_text("\n".join(lines)+"\n",encoding="utf-8")
    print("M028_GEOMETRY_LOADED roof="+str(len(roof.triangles))+
          " brick="+str(len(support.triangles)),flush=True)
    print("M028_METRICS_JSON="+json.dumps({
        "studs": [x["stud_center_world_ldu"] for x in support_sites],
        "relative_local_studs": [x["stud_center_in_slope_local_ldu"] for x in support_sites],
        "tube_world_axes": [x["world_axis_origin_ldu"] for x in tube_list],
        "nearest_horizontal_tube_axis_ldu": [
            x["nearest_tube_axis_distance_ldu"] for x in support_sites],
        "mesh_relation": collision.value,
        "strict_surface_witness_count_capped": len(witness),
        "nominal_mates": len(matches), "verdict": report["physical_mating_verdict"],
    },sort_keys=True),flush=True)
    print("M028_REPORT="+str(output),flush=True)
    return 0


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--ldraw-root",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--json-out",required=True,type=Path)
    a=p.parse_args()
    return analyze(a.ldraw_root,a.out,a.json_out)


if __name__=="__main__":
    raise SystemExit(main())
