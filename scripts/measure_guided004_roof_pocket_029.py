"""M029 - one B3 30363 underside pocket with a real 3004 stud.

Uses genuine pinned LDraw primitives, the existing LDrawLibrary and mesh
collision checker. Nominal clearance and sampled entry path are NOT proof of
manufactured tolerances, rigid-body volumetric clearance, or clutch strength.
No existing part or placement is changed.
"""
from __future__ import annotations

import argparse
import json
from math import hypot
from pathlib import Path

from lego_geometry_engine import (
    LDrawLibrary, Transform, Relation, check_collision,
    find_connections, instantiate, instance_from_dict,
)
from audit_guided004_b3_roof_020 import MODEL, placements
from verify_guided004_roof_to_gable_028 import (
    ROOF_ID, SUPPORT_ID, REVISION, relative_local, reference_records,
)

SITE = (10.0, 24.0, 0.0)
POSITION = (470.0, -792.0, 50.0)
INSERTION_STEPS = (16, 12, 8, 6, 4, 3, 2, 1, 0)


def checked_record(path, number, expected_prefix):
    lines = path.read_text(encoding="utf-8").splitlines()
    actual = lines[number-1].strip()
    if not actual.startswith(expected_prefix):
        raise ValueError(f"LDRAW_SOURCE_MISMATCH:{path.name}:{number}:{actual}")
    return actual


def get_part(root, rel):
    file = root / rel
    if not file.is_file():
        raise FileNotFoundError(f"MISSING_LDRAW_DEPENDENCY:{rel}")
    return file


def load_witness(root):
    main = get_part(root, "parts/30363.dat")
    sub = get_part(root, "parts/s/30363s01.dat")
    brick = get_part(root, "parts/s/3004s01.dat")
    stud = get_part(root, "p/stud.dat")
    tube = get_part(root, "p/stud4a.dat")
    box = get_part(root, "p/box2-5.dat")

    # Explicit source primitives, not fabricated dimensions or AABB sizes.
    checked_record(main, 16, "1 16 0 0 0 1 0 0 0 1 0 0 0 1")
    t = checked_record(sub, 18, "1 16 0 6.667 -10 1 0 0 0 -4.333")
    f = checked_record(sub, 48, "1 16 0 14 -2 16 0 0 0 -10 0 0 0 8")
    checked_record(sub, 54, "4 16 16 4 6 16 4 -10 16 20 -58 16 24 6")
    checked_record(box, 22, "4 16 1 1 1 -1 1 1 -1 -1 1 1 -1 1")
    checked_record(brick, 23, "1 16 10 0 0 1 0 0 0 1 0 0 0 1 stud.dat")
    checked_record(brick, 24, "1 16 -10 0 0 1 0 0 0 1 0 0 0 1 stud.dat")
    stud_r = checked_record(stud, 19, "1 16 0 0 0 6 0 0 0 -4")
    tube_r = checked_record(tube, 22, "1 16 0 -4 0 8 0 0 0 4")
    stud_data = stud_r.split()
    tube_data = tube_r.split()
    stud_radius = abs(float(stud_data[5]))
    stud_height = abs(float(stud_data[9]))
    tube_radius = abs(float(tube_data[5]))
    tube_center = [float(n) for n in t.split()[2:5]]
    # stud4a defines y from 0 to -4 in its local system;
    # subpart's y scaling -4.333 makes the wall extend from y=6.667 to 23.999.
    tube_y_end = tube_center[1] + 4.0 * abs(float(t.split()[9]))
    face = f.split()
    wall_front_z = float(face[4]) + float(face[13])
    wall_side_x = 16.0
    near_radius = hypot(SITE[0]-tube_center[0], SITE[2]-tube_center[2])
    clearance = {
        "stud_radius_ldu": stud_radius, "stud_height_ldu": stud_height,
        "tube_outer_radius_ldu": tube_radius,
        "tube_center_local_ldu": tube_center,
        "tube_wall_local_y_range_ldu": [tube_center[1], tube_y_end],
        "inner_side_wall_local_x_ldu": wall_side_x,
        "inner_front_wall_local_z_ldu": wall_front_z,
        "stud_local_site_ldu": list(SITE),
        "radial_axis_separation_ldu": near_radius,
        "tube_outer_to_stud_clearance_ldu": round(
            near_radius - tube_radius - stud_radius, 6),
        "side_wall_to_stud_clearance_ldu": round(
            wall_side_x - SITE[0] - stud_radius, 6),
        "front_wall_to_stud_clearance_ldu": round(
            wall_front_z - SITE[2] - stud_radius, 6),
        "source_evidence": {
            "standard_stud_geometry": "p/stud.dat:19",
            "tube_ring_and_outer_wall": "p/stud4a.dat:22",
            "tube_transform": "parts/s/30363s01.dat:18",
            "front_inner_wall": "parts/s/30363s01.dat:48 -> p/box2-5.dat:22",
            "side_inner_wall": "parts/s/30363s01.dat:54",
            "brick_standard_studs": "parts/s/3004s01.dat:23-24",
        },
    }
    return clearance


def diagnose(root, output, jsonout):
    rows, counts = placements(MODEL)
    by_id = {r["instance_id"]: r for r in rows}
    roof_data, brick_data = by_id[ROOF_ID], by_id[SUPPORT_ID]
    assert (roof_data["part_id"], roof_data["origin_ldu"]) == (
        "30363.dat", [470.0, -816.0, 60.0])
    assert (brick_data["part_id"], brick_data["origin_ldu"]) == (
        "3004.dat", [480.0, -792.0, 50.0])
    source = load_witness(root)
    lib = LDrawLibrary(root)
    roof = instance_from_dict(roof_data, lib)
    brick = instance_from_dict(brick_data, lib)
    stud_def = lib.load_part("stud.dat")
    stud_sites = reference_records(get_part(root, "parts/s/3004s01.dat"), "stud.dat")
    if len(stud_sites) != 2 or len(roof.definition.triangles) != 700:
        raise ValueError("REAL_GEOMETRY_NOT_MATCHING_PINNED_SOURCE")
    stud0 = brick.transform.point((-10, 0, 0))
    stud1 = brick.transform.point((10, 0, 0))
    if tuple(stud0) != POSITION or relative_local(stud0, roof) != list(SITE):
        raise ValueError(f"LOCAL_TO_WORLD_SITE_MISMATCH:{stud0}")
    world_tube = roof.transform.point(source["tube_center_local_ldu"])
    world_wall_x_dir = roof.transform.vector((1, 0, 0))
    world_wall_z_dir = roof.transform.vector((0, 0, 1))

    # Sample a straight motion of the GENUINE cylindrical stud itself.
    # Only a virtual isolated stud primitive moves; the B3 roof/3004 pieces
    # remain at their recorded transforms for all stored output.
    trajectory = []
    for down in INSERTION_STEPS:
        fake_stud_pos = (stud0[0], stud0[1]+down, stud0[2])
        actual_stud = instantiate(
            stud_def, "isolated-original-3004-stud",
            Transform.translation(*fake_stud_pos),
        )
        result = check_collision(roof, actual_stud)
        trajectory.append({
            "virtual_downward_offset_ldu": down,
            "stud_base_world_ldu": list(fake_stud_pos),
            "stud_tip_world_ldu": [fake_stud_pos[0],fake_stud_pos[1]-4,fake_stud_pos[2]],
            "mesh_relation": result.value,
            "surface_mesh_test_only": True,
        })
    mesh_pair = check_collision(roof, brick)
    nominal_matches = find_connections(roof, brick)
    nonnegative = all(source[k] >= -0.001 for k in (
        "tube_outer_to_stud_clearance_ldu",
        "side_wall_to_stud_clearance_ldu",
        "front_wall_to_stud_clearance_ldu",
    ))
    path_no_mesh_interference = all(
        x["mesh_relation"] != Relation.COLLISION.value for x in trajectory)
    # The three-source-surface nominal pocket plus an unblocked sampled
    # vertical approach suffices ONLY for "geometrically compatible".
    # Mechanical retention/clutch, shell closure and tolerance remain UNKNOWN.
    if nonnegative and path_no_mesh_interference and mesh_pair is not Relation.COLLISION:
        verdict = "A_LOGEMENT_GEOMETRIQUEMENT_COMPATIBLE_NOMINAL"
        rationale = ("Documented standard stud radius 6, underside walls and "
                     "tube radius 8 form a nominal pocket with nonnegative "
                     "cross-section margins and no mesh collisions in the "
                     "sampled straight insertion positions.")
    else:
        verdict = "C_DONNEES_INSUFFISANTES"
        rationale = ("Nominal clearance and/or sampled mesh insertion "
                     "produces an unresolved interference signal. Open "
                     "LDraw surface meshes cannot certify rigid solid "
                     "obstruction; do not claim incompatibility.")
    evidence = {
        "mission":"029", "source_model":str(MODEL),
        "source_B3_blob":"288c60fde76918128d8b955f78ebfa9afc2dfe8e",
        "ldraw_mirror_pinned_revision":"c43ed06a128a10ed65675166bf42eb6fd608b9b0",
        "actual_piece_identifiers": [roof_data, brick_data],
        "only_local_site":list(SITE),
        "world_stud_selected":list(stud0),
        "world_second_stud":list(stud1),
        "selected_stud_in_slope_local":relative_local(stud0,roof),
        "real_mesh_triangles": {
            "roof":len(roof.triangles), "brick":len(brick.triangles),
            "isolated_real_stud":len(stud_def.triangles),
        },
        "documented_cross_section":source,
        "tube_axis_world_ldu":list(world_tube),
        "local_x_direction_world":list(world_wall_x_dir),
        "local_z_direction_world":list(world_wall_z_dir),
        "full_pair_mesh_relation":mesh_pair.value,
        "nominal_connector_matches_current_engine":len(nominal_matches),
        "sampled_isolated_real_stud_insertions":trajectory,
        "sampled_vertical_path_no_mesh_collision_signal":path_no_mesh_interference,
        "nominal_cross_section_margins_nonnegative":nonnegative,
        "verdict":verdict,
        "rationale":rationale,
        "clutch_stability_tolerances_certified":False,
        "solid_material_volume_certified":False,
        "insertion_continuity_certified":False,
        "physical_fit_certified":False,
        "model_modified":False,
    }
    jsonout.parent.mkdir(parents=True,exist_ok=True)
    jsonout.write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    output.parent.mkdir(parents=True,exist_ok=True)
    lines=[
        "# BOLDÜNGO — M029 — PREMIER LOGEMENT SOUS LA PENTE",
        "",
        f"**Verdict : {verdict}** — compatibilité géométrique NOMINALE seulement ; "
        "aucune tenue mécanique ou stabilité certifiée.",
        f"Source B3 inchangée : \`{MODEL}\`, 1 904 pièces, 408 pentes.",
        f"Révision LDraw épinglée : \`{REVISION}\`.",
        "",
        "## Paire réelle et site (uniques)",
        f"- \`{ROOF_ID}\` 30363 : origine \`{roof_data['origin_ldu']}\`, "
        f"rotation \`{roof_data['transform'][3:]}\`.",
        f"- \`{SUPPORT_ID}\` 3004 : origine \`{brick_data['origin_ldu']}\`.",
        f"- Tenon candidat : centre monde \`{list(stud0)}\`, "
        f"site pente local \`{list(SITE)}\`. Autre tenon monde : \`{list(stud1)}\`.",
        "",
        "## Surfaces LDraw documentées autour du tenon",
        f"- \`p/stud.dat:19\` : rayon **{source['stud_radius_ldu']} LDU**, "
        f"hauteur **{source['stud_height_ldu']} LDU**.",
        f"- \`parts/s/30363s01.dat:18 → p/stud4a.dat:22\` : "
        f"tube ouvert, rayon extérieur **{source['tube_outer_radius_ldu']} LDU**, "
        f"axe local \`{source['tube_center_local_ldu']}\`, "
        f"longueur verticale documentée jusqu'à "
        f"y≈{source['tube_wall_local_y_range_ldu'][1]} LDU.",
        f"- \`parts/s/30363s01.dat:54\` : plan intérieur latéral "
        f"x=**{source['inner_side_wall_local_x_ldu']} LDU** ; "
        f"\`parts/s/30363s01.dat:48 → p/box2-5.dat:22\` : plan "
        f"intérieur frontal z=**{source['inner_front_wall_local_z_ldu']} LDU**.",
        "",
        "## Mesures de l'espace nominal local (X/Z)",
        f"- Centre tenon / axe tube : **{round(source['radial_axis_separation_ldu'],6)} LDU**.",
        f"- Jeu entre surfaces cylindriques : **{source['tube_outer_to_stud_clearance_ldu']} LDU** "
        "(distance axes − rayon tube 8 − rayon tenon 6).",
        f"- Jeu au plan latéral x=16 : **{source['side_wall_to_stud_clearance_ldu']} LDU**.",
        f"- Jeu au plan frontal z=6 : **{source['front_wall_to_stud_clearance_ldu']} LDU**.",
        "- Ces valeurs décrivent une **poche nominale de retenue à trois voisins** "
        "(2 plans et 1 tube) ; elles ne prouvent pas le serrage réel, le degré "
        "d'élasticité du plastique ou la tolérance de fabrication.",
        "",
        "## Géométrie entière de la paire et insertion hypothétique",
        f"- Maillages authentiques : pente {len(roof.triangles)} triangles, "
        f"brique {len(brick.triangles)} ; \`check_collision\` de la paire : "
        f"**{mesh_pair.value}**.",
        f"- Connecteurs connus \`find_connections\` entre ces pièces : "
        f"**{len(nominal_matches)}** (le logement inférieur n'est pas "
        "enregistré dans le moteur M026).",
        "- Trajectoire verticale hypothétique testée sur le **seul tenon réel "
        "isolé**, sans déplacer la pente ni la brique B3 :",
        "| Décalage positif vers le bas (LDU) | Résultat du maillage réel |",
        "|---:|---|",
    ]
    for point in trajectory:
        lines.append(
            f"| {point['virtual_downward_offset_ldu']} | "
            f"{point['mesh_relation']} |")
    lines.extend([
        "",
        "- La trajectoire est **échantillonnée**, non continue ; des maillages "
        "ouverts ou des tolérances réelles peuvent masquer des interférences. "
        "Ce test **ne simule pas** le déplacement de la brique entière.",
        "",
        "## Verdict, limites et prochaine action",
        f"- **{verdict}** : {rationale}",
        "- Une poche géométrique nominale n'est **PAS** un connecteur LEGO "
        "physiquement certifié. Aucun connecteur \`anti_stud\` ajouté.",
        "- Aucune validation de tenue, insertion complète de la brique, "
        "résistance mécanique ni stabilité globale de la toiture.",
        "- **Action concrète conseillée :** réaliser un assemblage réel de "
        "la référence authentique LEGO 30363 sur une 3004, dans la même "
        "orientation relative, et vérifier si le tenon se loge et tient sans "
        "forcer. Photographier la face inférieure et la liaison, avec la "
        "référence des pièces ; ce sera une preuve complémentaire avant "
        "d'étendre les règles du moteur.",
        "- Si un prototype physique est indisponible, consulter une notice "
        "officielle LEGO montrant précisément cette combinaison 30363/3004 "
        "et son orientation.",
        "- Aucun changement des pièces B3 ni du moteur. Aucun test sur "
        "les autres pentes ni audit global relancé.",
        "",
        "Preuves structurées : \`MESURES-LOGEMENT-M029.json\` dans l'artefact Actions.",
    ])
    output.write_text("\n".join(lines)+"\n",encoding="utf-8")
    print("M029_METRICS_JSON="+json.dumps({
        "site":list(SITE), "stud":list(stud0),
        "stud_radius":source["stud_radius_ldu"],
        "tube_outer_radius":source["tube_outer_radius_ldu"],
        "radial_axis_separation":round(source["radial_axis_separation_ldu"],6),
        "clearance_tube":source["tube_outer_to_stud_clearance_ldu"],
        "clearance_side":source["side_wall_to_stud_clearance_ldu"],
        "clearance_front":source["front_wall_to_stud_clearance_ldu"],
        "pair_mesh":mesh_pair.value,
        "virtual_path":{str(p["virtual_downward_offset_ldu"]):p["mesh_relation"] for p in trajectory},
        "mating_connectors_known":len(nominal_matches),
        "verdict":verdict},sort_keys=True),flush=True)
    print("M029_REPORT="+str(output),flush=True)


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--ldraw-root",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--json-out",type=Path,required=True)
    a=p.parse_args()
    diagnose(a.ldraw_root,a.out,a.json_out)


if __name__=="__main__":
    main()
