"""M025: trace B3's four ridge triangle witnesses to their LDraw primitives.

Diagnostic only. The existing LEGO2-080 material-volume gate is authoritative
for whether a mesh permits parity-based interior sampling. No geometry or
connector inference is changed. The B3 model remains strictly read-only.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from brickhouse.bricks.ridge_material_volume_080 import (
    decide_physical_interference, inspect_shared_interior, inspect_solid_shell,
)
from lego_geometry_engine import (
    LDrawLibrary, Relation, check_collision, find_connections, instance_from_dict,
)
from lego_geometry_engine.core import _tri_intersection_kind
from audit_guided004_b3_roof_020 import MODEL, placements

A_ID = "roof-000185"
B_ID = "roof-000392"
WITNESSES_M024 = ((0, 601), (0, 698), (1, 601), (2, 601))


def _relpath(root: Path, path: Path):
    return path.relative_to(root).as_posix()


def source_face_provenance(library: LDrawLibrary, filename: str):
    """Trace _expand's *face order*, not new physical geometry.

    Recurse only through type-1 source references, and annotate each
    type-3/type-4 face with its originating LDraw line and primitive chain.
    The engine's _expand retains this ordering (quads give two triangles).
    """
    root = library.root.resolve()
    top = library._resolve(filename)
    if top is None:
        raise FileNotFoundError("Unresolved LDraw source: " + filename)
    def walk(path, chain, seen):
        resolved = path.resolve()
        if resolved in seen:
            raise ValueError("Recursive provenance reference: " + str(resolved))
        next_seen = seen | {resolved}
        relative = _relpath(root, resolved)
        rows = []
        for number, raw in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            f = raw.strip().split()
            if not f:
                continue
            if f[0] == "1" and len(f) >= 15:
                child_ref = " ".join(f[14:])
                child = library._resolve(child_ref)
                if child is None:
                    raise FileNotFoundError(f"Missing primitive {child_ref!r} in {relative}:{number}")
                rows.extend(walk(child, chain + [{"file": relative, "line": number,
                                                "reference": child_ref}], next_seen))
            elif f[0] == "3" and len(f) >= 11:
                rows.append({"source_file": relative, "source_line": number, "ldraw_face_type": 3,
                             "hierarchy": chain, "source_record": raw.strip()})
            elif f[0] == "4" and len(f) >= 14:
                for segment in (0, 1):
                    rows.append({"source_file": relative, "source_line": number,
                                 "ldraw_face_type": 4, "quad_triangle": segment,
                                 "hierarchy": chain, "source_record": raw.strip()})
        return rows
    return walk(top, [], set())


def other_ridge_instances(records):
    """Verify actual relative transform, rather than translation alone."""
    roofs = [r for r in records if r["part_id"] == "30363.dat"]
    by_origin = {tuple(rec["origin_ldu"]): rec for rec in roofs}
    a_rotation = [0., 0., 1., 0., 1., 0., -1., 0., 0.]
    b_rotation = [0., 0., -1., 0., 1., 0., 1., 0., 0.]
    matches = []
    for a in roofs:
        x, y, z = a["origin_ldu"]
        b = by_origin.get((x-40, y, z))
        if b is None:
            continue
        # In LDraw's 12-element records, the first three values are the
        # translation and the remaining nine are the 3x3 orientation matrix.
        if a["transform"][3:] == a_rotation and b["transform"][3:] == b_rotation:
            matches.append({"a": a["instance_id"], "b": b["instance_id"],
                            "translation_difference_ldu": [-40, 0, 0],
                            "orientation_a": a_rotation, "orientation_b": b_rotation})
    return sorted(matches, key=lambda p: (p["a"], p["b"]))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--ldraw-root", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--json-out", required=True, type=Path)
    args = p.parse_args()

    records, count = placements(MODEL)
    original = {r["instance_id"]: r for r in records}
    a_data, b_data = original[A_ID], original[B_ID]
    assert a_data["part_id"] == b_data["part_id"] == "30363.dat"
    assert a_data["origin_ldu"] == [830., -960., 20.]
    assert b_data["origin_ldu"] == [790., -960., 20.]

    library = LDrawLibrary(args.ldraw_root)
    a, b = (instance_from_dict(original[id], library) for id in (A_ID, B_ID))
    expected = source_face_provenance(library, "30363.dat")
    if len(expected) != len(a.triangles) or len(a.triangles) != len(b.triangles):
        raise ValueError(f"PROVENANCE_FACE_COUNT_MISMATCH:{len(expected)}:"
                         f"{len(a.triangles)}:{len(b.triangles)}")
    confirmed = []
    for i, j in WITNESSES_M024:
        relation = _tri_intersection_kind(a.triangles[i], b.triangles[j])
        if relation is not Relation.COLLISION:
            raise ValueError(f"M024_WITNESS_NOT_REPRODUCED:{i}:{j}:{relation.value}")
        confirmed.append({
            "triangle_a_index": i, "triangle_b_index": j,
            "triangle_a_world_vertices_ldu": a.triangles[i],
            "triangle_b_world_vertices_ldu": b.triangles[j],
            "a_ldraw_source": expected[i], "b_ldraw_source": expected[j],
            "mesh_relation": relation.value,
        })
    print(f"M025_PROVENANCE_OK faces={len(expected)} four_witnesses={len(confirmed)}", flush=True)
    for w in confirmed:
        print(f"M025_FACE a={w['triangle_a_index']} from="
              f"{w['a_ldraw_source']['source_file']}:{w['a_ldraw_source']['source_line']} "
              f"b={w['triangle_b_index']} from="
              f"{w['b_ldraw_source']['source_file']}:{w['b_ldraw_source']['source_line']}", flush=True)

    shell_a, shell_b = inspect_solid_shell(a), inspect_solid_shell(b)
    volume = inspect_shared_interior(a, b, points_per_axis=5)
    if shell_a != volume["first_shell"] or shell_b != volume["second_shell"]:
        raise AssertionError("Volume gate shell mismatch")
    status, reason = decide_physical_interference(volume, connector_provenance_available=False)
    relation = check_collision(a, b).value
    connectors = find_connections(a, b)
    transforms = other_ridge_instances(records)

    result = {
        "mission": "025", "model": str(MODEL),
        "ldraw_revision": "c43ed06a128a10ed65675166bf42eb6fd608b9b0",
        "part_a": a_data, "part_b": b_data,
        "description": a.definition.description,
        "triangles_per_part": len(a.triangles),
        "whole_mesh_relation": relation,
        "four_original_surface_intersection_witnesses": confirmed,
        "surfaces_from_original_LDraw_files": [
            "30363.dat", "parts/s/30363s01.dat",
        ],
        "shell_a": shell_a, "shell_b": shell_b,
        "shared_interior_review": volume,
        "material_interference_decision_080": [status, reason],
        "ldraw_nominal_connector_matches": len(connectors),
        "23_repeated_ridge_pair_transform_check": {
            "count": len(transforms),
            "identical_relative_rotations_and_offsets": len(transforms) == 23,
            "pairs": transforms,
            "scope": "Geometric transform equivalence only; physical equivalence not proven",
        },
        "physical_verdict": "C — INDETERMINE",
        "no_material_model_changes": True,
        "limits": [
            "Source primitive labels show provenance, not automatically an identified rigid material.",
            "Closed consistently oriented mesh required before interior parity sampling.",
            "No connectors are invented for slope 30363; nominal engagement unverified.",
            "Triangle crossings alone do not prove forbidden body interference or admissible clutch.",
        ],
    }
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    face_rows = []
    for t in confirmed:
        for which in ("a", "b"):
            s = t[f"{which}_ldraw_source"]
            row = (f"- Témoins A#{t['triangle_a_index']} / B#{t['triangle_b_index']}, "
                   f"pièce {which.upper()} : face d'origine \`{s['source_file']}:{s['source_line']}\`, "
                   f"primitive/ligne \`{s['source_record']}\`, "
                   f"chaîne \`{json.dumps(s['hierarchy'], ensure_ascii=False)}\`.")
            face_rows.append(row)
    lines = [
        "# BOLDÜNGO — MISSION 025 : VERIFICATION MATERIELLE DU FAITAGE",
        "",
        "**Verdict C — INDETERMINE.** Maillages réels, sans modification LEGO.",
        "",
        "## Éléments contrôlés",
        f"- Référence B3 : \`{MODEL}\` ; {len(records)} pièces dont {count['30363.dat']} pentes.",
        f"- \`{A_ID}\` \`30363.dat\` : {a_data['origin_ldu']} LDU ; matrice {a_data['transform'][3:]}.",
        f"- \`{B_ID}\` \`30363.dat\` : {b_data['origin_ldu']} LDU ; matrice {b_data['transform'][3:]}.",
        f"- Référence LDraw épinglée : {result['ldraw_revision']}.",
        f"- Maillage : {len(a.triangles)} triangles par pente ; croisement des surfaces : {relation}.",
        f"- 4 témoins M024 reproduits avec la fonction existante \`_tri_intersection_kind\`.",
        "",
        "## Provenance exacte des surfaces dans la bibliothèque LDraw",
        *face_rows,
        "",
        "La provenance indique les fichiers et primitives exacts, mais ne qualifie",
        "pas en elle-même la portion de matière comme corps rigide, tenon ou logement.",
        "",
        "## Test des volumes (moteur 080 existant)",
        f"- Pièce A : {shell_a['watertight_oriented_shell_gate']} ; arêtes ouvertes "
        f"{shell_a['open_boundary_edges']}, non-manifold {shell_a['nonmanifold_edges']}, "
        f"orientations inconsistantes {shell_a['inconsistent_winding_edges']}, "
        f"faces dégénérées {shell_a['degenerate_faces']}.",
        f"- Pièce B : {shell_b['watertight_oriented_shell_gate']} ; arêtes ouvertes "
        f"{shell_b['open_boundary_edges']}, non-manifold {shell_b['nonmanifold_edges']}, "
        f"orientations inconsistantes {shell_b['inconsistent_winding_edges']}, "
        f"faces dégénérées {shell_b['degenerate_faces']}.",
        f"- Échantillonnage partagé : {volume['shared_material_sample']} ; "
        f"points contrôlés : {volume['samples_checked']} ; "
        f"témoin intérieur : {volume['interior_witness_ldu']}.",
        f"- Décision de sécurité du moteur 080 : {status} — {reason}.",
        f"- Connecteurs 30363 détectés entre pièces : {len(connectors)} ; "
        "aucun emboîtement admissible documenté ici.",
        "",
        "## Extension prudente aux 23 cas",
        f"- Paires présentant exactement les mêmes matrices d'orientation et "
        f"le même décalage relatif : {len(transforms)}/23.",
        "- Transformations relatives identiques ≠ garantie de corps matériel "
        "compatible, de contact LEGO ou de stabilité dans le contexte de la toiture.",
        "",
        "## Conclusion",
        "- **C — INDETERMINE** : aucun certificat de pénétration interdite de deux "
        "corps solides ; aucun emboîtement LEGO admissible démontré.",
        "- Correction de principe **non justifiée** par ces seuls témoignages : "
        "ne pas déplacer une pente ni combler le faîtage.",
        "- Inspecter un modèle de matière/manufacture et connexions documenté "
        "avant toute correction physique. Les propriétés d'insertion, la force "
        "d'emboîtement et la stabilité ne sont pas prouvées.",
        "",
        "Données numériques exhaustives : artefact \`PREUVES-FAITAGE-M025.json\`.",
    ]
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"M025_SHELL_A={shell_a['watertight_oriented_shell_gate']} "
          f"open={shell_a['open_boundary_edges']} nonmanifold={shell_a['nonmanifold_edges']}", flush=True)
    print(f"M025_SHELL_B={shell_b['watertight_oriented_shell_gate']} "
          f"open={shell_b['open_boundary_edges']} nonmanifold={shell_b['nonmanifold_edges']}", flush=True)
    print(f"M025_SHARED_MATERIAL={volume['shared_material_sample']} checked={volume['samples_checked']}", flush=True)
    print(f"M025_23_RELATIVE_TRANSFORMS_IDENTICAL={len(transforms) == 23}", flush=True)
    print("M025_PHYSICAL_VERDICT=C_INDETERMINE", flush=True)
    print(f"M025_REPORT={args.out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
