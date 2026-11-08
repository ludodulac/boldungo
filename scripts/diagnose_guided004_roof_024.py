"""Mission 024: inspect only three real LDraw B3 roof intersection witnesses.

Diagnostic-only. Reuses the existing mesh engine's exact triangle relation;
DO NOT infer physical buildability or forbidden material overlap from an AABB.
"""
from __future__ import annotations

import argparse
import json
from math import sqrt
from pathlib import Path

from audit_guided004_b3_roof_020 import MODEL, placements
from lego_geometry_engine import (
    LDrawLibrary, Relation, check_collision, find_connections, instance_from_dict,
)
from lego_geometry_engine.core import CONTACT_EPS, _tri_intersection_kind

PAIRS = (
    ("A", "roof-000252", "roof-000229"),
    ("B", "roof-000185", "roof-000392"),
    ("C", "roof-000183", "gable-000044"),
)
EXPLANATION = {
    "A": "Pentes de meme orientation, pas longitudinal +60 LDU et +24 LDU vertical ; repetition sur 184 paires du B3. Recouvrement de rangees de pente probable ; connexion/admissibilite non demontrees.",
    "B": "Deux pentes 30363 de rotations opposees, meme altitude, ecart -40 LDU ; repetition 23 fois. Jonction des pans opposes au faitage probable ; raccordement admissible non demontre.",
    "C": "Pente 30363 contre brique de pignon 3010 (1 x 4) ; ecarte +30,+24,+10 LDU. Jonction pignon/couverture a verifier, pas de preuve de correction locale sure.",
}


def triangle_bounds(triangle):
    return (
        [min(p[axis] for p in triangle) for axis in range(3)],
        [max(p[axis] for p in triangle) for axis in range(3)],
    )


def norm_cross(triangle):
    a, b, c = triangle
    u = [b[i] - a[i] for i in range(3)]
    v = [c[i] - a[i] for i in range(3)]
    w = (u[1] * v[2] - u[2] * v[1],
         u[2] * v[0] - u[0] * v[2],
         u[0] * v[1] - u[1] * v[0])
    magnitude = sqrt(sum(q * q for q in w))
    return [round(q / magnitude, 6) for q in w] if magnitude else None


def witness_triangles(a, b, limit=4):
    """Find existing engine's non-coplanar surface intersections, no new engine."""
    samples = []
    other = [(t, *triangle_bounds(t)) for t in b.triangles]
    for index_a, ta in enumerate(a.triangles):
        min_a, max_a = triangle_bounds(ta)
        for index_b, (tb, min_b, max_b) in enumerate(other):
            if any(max_a[i] < min_b[i] - CONTACT_EPS or
                   max_b[i] < min_a[i] - CONTACT_EPS for i in range(3)):
                continue
            if _tri_intersection_kind(ta, tb) is Relation.COLLISION:
                samples.append({
                    "triangle_a_index": index_a,
                    "triangle_b_index": index_b,
                    "triangle_a_world_vertices_ldu": ta,
                    "triangle_b_world_vertices_ldu": tb,
                    "triangle_a_unit_normal": norm_cross(ta),
                    "triangle_b_unit_normal": norm_cross(tb),
                    "evidence": "NON_COPLANAR_TRIANGLE_INTERSECTION",
                })
                if len(samples) == limit:
                    return samples
    return samples


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ldraw-root", type=Path, required=True)
    parser.add_argument("--out", type=Path,
                        default=Path("missions/MAISON_COMPLETE2/DIAGNOSTIC-INTERSECTIONS-M024.md"))
    parser.add_argument("--json-out", type=Path,
                        default=Path("artifacts/lego2-m024/DIAGNOSTIC-TRIANGLES-M024.json"))
    args = parser.parse_args()

    records, inventory = placements(MODEL)
    original = {rec["instance_id"]: rec for rec in records}
    library = LDrawLibrary(args.ldraw_root)
    part_ids = sorted({original[x]["part_id"]
                       for _, a, b in PAIRS for x in (a, b)})
    definitions = {part_id: library.load_part(part_id) for part_id in part_ids}
    for part_id, definition in definitions.items():
        print("M024_MESH_LOADED part=" + part_id
              + " triangles=" + str(len(definition.triangles))
              + " inferred_connectors=" + str(len(definition.connectors)),
              flush=True)

    results = []
    for label, ida, idb in PAIRS:
        a, b = (instance_from_dict(original[p], library) for p in (ida, idb))
        relation = check_collision(a, b)
        connections = find_connections(a, b)
        witnesses = witness_triangles(a, b) if relation is Relation.COLLISION else []
        entry = {
            "case": label,
            "part_a": original[ida],
            "part_b": original[idb],
            "description_a": a.definition.description,
            "description_b": b.definition.description,
            "mesh_triangles_a": len(a.triangles),
            "mesh_triangles_b": len(b.triangles),
            "mesh_relation": relation.value,
            "mesh_aabb_relation_only_for_broad_phase": a.bbox.relation(b.bbox).value,
            "mesh_aabb_a": {"minimum": a.bbox.minimum, "maximum": a.bbox.maximum},
            "mesh_aabb_b": {"minimum": b.bbox.minimum, "maximum": b.bbox.maximum},
            "inferred_connectors_a": len(a.definition.connectors),
            "inferred_connectors_b": len(b.definition.connectors),
            "connector_matches": connections,
            "noncoplanar_triangle_witnesses": witnesses,
            "physical_verdict": "INDETERMINE",
            "rationale": EXPLANATION[label],
            "forbidden_material_collision_proven": False,
            "physically_compatible_joint_proven": False,
        }
        results.append(entry)
        print("M024_CASE=" + label + " pair=" + ida + "/" + idb
              + " mesh=" + relation.value
              + " witnesses=" + str(len(witnesses))
              + " matching_connectors=" + str(len(connections))
              + " PHYSICAL_VERDICT=INDETERMINE", flush=True)

    result = {
        "model": str(MODEL),
        "ldraw_revision": "c43ed06a128a10ed65675166bf42eb6fd608b9b0",
        "model_parts": len(records),
        "model_roof_parts": inventory["30363.dat"],
        "M023_verified": {
            "candidate_pairs_tested": 1904,
            "roof_parts_fully_examined": 408,
            "mesh_intersections": 209,
            "roof_roof": 207, "roof_gable": 2,
            "repeated_roof_offsets": {
                "(60,24,0)": 184,
                "(-40,0,0)": 23,
            },
            "surface_contacts_without_connectors": 1695,
        },
        "cases": results,
        "engine_connector_limitation": (
            "LDraw 30363 description is 'Slope Brick 18 4 x 2'. "
            "Connector inference matches descriptions beginning with 'Brick' or 'Plate' "
            "and canonical rectangular brick faces only. It does not infer slope-specific "
            "stud or underside mating geometry. Zero matches cannot prove no joint exists."
        ),
        "limits": [
            "M024 analyzes only the three supplied representative pairs, not 209 fresh pairs.",
            "Engine detects intersections of mesh triangles; it does not label which "
            "surfaces are permissible LEGO stud/tube engagements.",
            "No proof of admissible mating, forbidden solid body penetration, insertion "
            "path, clutch force or mechanical stability.",
        ],
    }
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md = [
        "# BOLDÜNGO — Mission 024 : diagnostic des intersections de toiture",
        "",
        "Source : `missions/B3/generated/GUIDED004-B3-1904.ldr`, 1 904 pièces, "
        "408 pentes `30363.dat`; maillages réels pybricks/ldraw révision épinglée "
        "`c43ed06a128a10ed65675166bf42eb6fd608b9b0`.",
        "",
        "## Résultat global de la mission 023 (récupéré et vérifié)",
        "1 904/1 904 paires examinées ; 408/408 pièces de toiture couvertes ; "
        "**209 croisements de maillages** : 207 toiture/toiture et 2 toiture/pignon.",
        "Les cas toiture/toiture comprennent 184 décalages (+60,+24,0) et "
        "23 décalages (-40,0,0) LDU.",
        "Les 1 695 autres interactions sont des contacts **sans connexion démontrée**.",
        "Un croisement de maillages ne certifie ni une collision matérielle interdite "
        "ni un emboîtement LEGO admissible.",
        "",
        "## Trois paires représentatives, maillages réels",
    ]
    for entry in results:
        ida, idb = entry["part_a"], entry["part_b"]
        md.extend([
            "",
            "### Cas " + entry["case"] + " — " + ida["instance_id"] + " / " + idb["instance_id"],
            "- Pièce A : `" + ida["instance_id"] + "`, `" + ida["part_id"] + "`, "
            + str(ida["origin_ldu"]) + " LDU ; matrice " + str(ida["transform"][3:]) + ".",
            "- Pièce B : `" + idb["instance_id"] + "`, `" + idb["part_id"] + "`, "
            + str(idb["origin_ldu"]) + " LDU ; matrice " + str(idb["transform"][3:]) + ".",
            "- Maillages : `" + entry["mesh_relation"] + "`; "
            + str(len(entry["noncoplanar_triangle_witnesses"]))
            + " témoins de triangles non coplanaires intersectés ; "
            + str(len(entry["connector_matches"])) + " connecteur(s) reconnu(s).",
            "- Témoins des surfaces : indices de triangles et sommets 3D exacts "
            "dans l'artefact `DIAGNOSTIC-TRIANGLES-M024.json`. "
            + ("Premier témoin : triangles #"
               + str(entry["noncoplanar_triangle_witnesses"][0]["triangle_a_index"])
               + " et #"
               + str(entry["noncoplanar_triangle_witnesses"][0]["triangle_b_index"])
               + "." if entry["noncoplanar_triangle_witnesses"] else
               "Aucun témoin de croisement de triangles obtenu."),
            "- **Verdict physique : INDETERMINE**. "
            + entry["rationale"],
            "- Correction de principe : qualifier d'abord les surfaces corps/tenons/logements "
            "et la trajectoire de pose ; aucune modification ou suppression de pièces autorisée "
            "sur ces seules données.",
        ])
    md.extend([
        "",
        "## Connecteurs et généralisation",
        "- Le catalogue LDraw décrit `30363.dat` comme « Slope Brick 18 4 x 2 » ; "
        "l'inférence actuelle de `LDrawLibrary` repose sur une expression régulière "
        "pour les briques/plaques classiques, sans identification des faces inclinées "
        "et dessous spécifiques. Elle ne reconnaît donc pas automatiquement "
        "les attaches de cette pente.",
        "- Les 184 et 23 répétitions de décalages montrent des **configurations "
        "récurrentes**, mais un cas ne suffit pas à classer toutes les instances "
        "en emboîtements autorisés ou collisions interdites.",
        "- Les deux contacts avec des pignons ne sont représentés ici que par un "
        "seul cas détaillé ; aucune conclusion sur la deuxième jonction.",
        "",
        "## Limites",
        "- Les boîtes englobantes ne servent qu'au filtrage, jamais à prouver un choc.",
        "- Les intersections de triangles doivent être réexaminées en distinguant "
        "les volumes des tenons/logements et les trajets d'insertion.",
        "- **Constructibilité, stabilité et absence de collision interdite : NON DEMONTREES.**",
        "- Aucune modification des 1 904 pièces ou des dimensions architecturales.",
    ])
    args.out.write_text("\n".join(md) + "\n", encoding="utf-8")
    print("M024_REPORT_PATH=" + str(args.out), flush=True)
    print("M024_JSON_PATH=" + str(args.json_out), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
