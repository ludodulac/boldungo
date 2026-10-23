"""Build 098 actual wall-connected crossbeam + unchanged 22° roof; audit DAT axes.

The full 098 house DOES NOT inherit Technic assemblies that are not
demonstrated as load-bearing. A separate diagnostic 096 model corrects
the original physically wrong Technic transforms on ALL 095/096 beams,
3L pins and 2L pins (including 096-F6) without mutating older variants.
"""
from __future__ import annotations
import argparse,hashlib,json
from collections import Counter
from pathlib import Path
from brickhouse.bricks.brick_model import BrickModel
from brickhouse.bricks.geometry_adapter import CANONICAL_LDRAW_PARTS
from brickhouse.bricks.fixed_wall_roof_support_098 import build_wall_tie
from brickhouse.bricks.technic_official_axes_098 import correct_legacy_096_overlay
from brickhouse.bricks.roof_technic_transfer_096 import build_096
from brickhouse.bricks.technic_triangle_095 import PARTS095
from brickhouse.bricks.triangular_frame_ridge_094 import LOCAL_PARTS
from construct_guided004_hinged_roof_093 import PARTS,save_ldraw,draw_views
PARTS.update(LOCAL_PARTS)
PARTS.update(PARTS095)
PARTS.update({"3020":("PLATE_2X4",4,2),"2456":("BRICK_2X6",6,2),
              "3003":("BRICK_2X2",2,2)})

def ldraw_bom(f,overlay):
    counts=Counter(x["ldraw_id"] for x in overlay)
    for p in f.parts:
        mapping=CANONICAL_LDRAW_PARTS.get(p.part_id)
        if mapping is not None and mapping.placement_kind=="standard":
            counts[mapping.ldraw_id]+=1
    return dict(sorted(counts.items()))

def main(source:Path,output:Path):
    raw=source.read_bytes(); source_sha=hashlib.sha256(raw).hexdigest()
    m=BrickModel.model_validate_json(raw)
    if len(m.parts)!=1936:
        raise ValueError("GUIDED004_EXPECTED_091_EXPERIMENTAL_1936")
    output.mkdir(parents=True,exist_ok=True)
    built=build_wall_tie(m)
    report=built["report"]
    foundation=built["foundation"];assembly=built["articulated_parts"]
    if source.read_bytes()!=raw:
        raise AssertionError("DO_NOT_EDIT_HISTORIC_091_SOURCE")
    (output/"BRICKMODEL-098-FIXED-WALL-FOUNDATION.json").write_text(
          foundation.model_dump_json(indent=2)+"\n",encoding="utf8")
    ld=save_ldraw(foundation,assembly,output/"BOLDUNGO-098-WALL-FIXED-TIE-AND-22DEG-ROOF.ldr")
    if ld["ldraw_mapped_brick_model_part_count"]+ld["articulated_ldraw_placed_parts"]!=report["full_house_composite_parts"]:
        raise AssertionError("LDraw_MISSING_098_GEOMETRY")
    b=ldraw_bom(foundation,assembly)
    if sum(b.values())!=report["full_house_composite_parts"]:
        raise AssertionError("TOTAL_BOM_NOT_REAL_LDRAW")
    (output/"BOM-098-FULL-EXACT.json").write_text(json.dumps({
          "total":report["full_house_composite_parts"],"by_ldraw":b,
          "new_fixed_support_parts":report["new_bom"],
          "roof_pitch_degrees":22.,
          "colors":"UNSPECIFIED","release_for_purchase":False,
          "source_091_sha256":source_sha},indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    # Audit 095, 096 old LDraw matrices independently of the NEW
    # simplified fixed-structure roof. This is not a copied 097 assembly.
    old=build_096(m)
    corrected,axes=correct_legacy_096_overlay(old["articulated_parts"])
    diagnostic=output/"AUDIT-098-CORRECTED-095-096-TECHNIC-AXES.ldr"
    corrected_ld=save_ldraw(old["foundation"],corrected,diagnostic)
    if corrected_ld["ldraw_mapped_brick_model_part_count"]+corrected_ld["articulated_ldraw_placed_parts"]!=2943:
        raise AssertionError("096_AUDIT_ALTERED_REAL_PIECES")
    (output/"AUDIT-098-OFFICIAL-LDRAW-AXES.json").write_text(
        json.dumps(axes,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    views=draw_views(foundation,assembly,output/"views")
    for page in (output/"views").glob("*.svg"):
        page.write_text(page.read_text(encoding="utf8")
                       .replace("BOLDUNGO 093","BOLDUNGO 098"),encoding="utf8")
    # A runnable real subassembly: the fixed crossbeam course, actual walls,
    # authentic 093 sill caps and part of the first tilted roof panel.
    ends=report["wall_sides"]
    wall_ids={w for side in ends for w in side["wall_ids"]}
    cap_ids={w for side in ends for w in side["roof_hinge_cap_ids"]}
    subparts=[p for p in foundation.parts if p.placement_id in (wall_ids|cap_ids)]
    submodel=BrickModel.model_validate({**foundation.model_dump(mode="json"),
       "building_id":"BOLDUNGO-098-GROUNDED-BEAM-SUBASSEMBLY",
       "parts":[p.model_dump(mode="json") for p in subparts]})
    bay=report["bay"]
    mini_assembly=[p for p in assembly if p["placement_id"].startswith("098-") and
                   (p["kind"]!="roof098_real_wall_sill_retile")]
    mini_assembly+= [p for p in assembly if p["placement_id"].startswith(
                         (f"093-negative-basehinge-{bay}-0",
                          f"093-negative-roofhinge-{bay}-0",
                          f"093-negative-baseplate-{bay}-0-0",
                          f"093-negative-interlockedplate-{bay}-0-0",
                          f"093-negative-tile-{bay}-0"))]
    mini_ld=save_ldraw(submodel,mini_assembly,
                       output/"SOUS-ASSEMBLAGE-098-POUTRE-FIXE-ET-CHARNIERE.ldr")
    proof={**report,"source_091_sha256":source_sha,
       "new_098_house_architecture":"REMOVE_UNANCHORED_094_TECHNIC_TRUSSES_ADD_TRUE_WALL_BRICK_TIE",
       "real_096_axes_audit":axes,
       "subassembly_real_part_count":mini_ld["ldraw_mapped_brick_model_part_count"]+
                                      mini_ld["articulated_ldraw_placed_parts"],
       "seven_views_count":views,
       "complete_LDraw_line_count":report["full_house_composite_parts"],
       "mechanical_full_roof_load_paths":0,
       "N2_wall_crossbeam_brick_stud_interfaces":True,
       "N4_roof_pitch_kinematically_locked":False,
       "N5_complete_insertion_verified":False,
       "N6": "NOT_CERTIFIED"}
    (output/"EVIDENCE-098-WALL-TIE-AND-BLOCKERS.json").write_text(
         json.dumps(proof,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    notice="""# BOLDÜNGO — 098 : traversée fixe entre deux murs, étape d'atelier

**AVERTISSEMENT** : la poutre transversale en briques est réellement
bondée sur les murs et maintenue par des plaques anti-déjointement.
MAIS la toiture à 22° pivote toujours librement sur ses charnières 4275b/
4276b : le FAÎTAGE et la seconde portée ne sont pas retenus de façon
démontrée. Ne jamais appeler cela une maison physiquement certifiée.

1. Construire les deux murs en conservant chaque cellule d'assise originale.
2. Refaire uniquement dans la NOUVELLE variante 098 les couronnements des
   deux murs à la travée concernée, avec des vraies 3004 et 3007.
3. Insérer depuis l'intérieur la succession de vraies briques LEGO 3007
   de 2×8, de mur à mur : chaque extrémité reprend au moins deux tenons
   fondés du modèle réel. Laisser toutes les façades et ouvertures intactes.
4. Verrouiller chaque joint entre 3007 avec une vraie plaque 3020 2×4,
   à cheval sur les deux briques, à hauteur des studs existants.
5. Reposer les plaques de couronnement 093 d'origine exactement à leurs
   anciennes coordonnées, sur les studs de la nouvelle poutre aux extrémités.
6. Monter les plaques charnières originales 4275b et leurs 4276b, puis
   reposer les rails et tuiles, en gardant une inclinaison EXACTE de 22°.
7. **STOP STRUCTUREL** : la nouvelle poutre fixe ne prouve ni la stabilité
   de l'angle du toit ni le soutien à la crête. La flexion de la poutre
   et l'insertion finale des charnières sont NON TESTÉES. Il faut une
   seconde assise à la toiture, fixée réellement à cette structure.
8. Ne pas commander les pièces sur la base de cette notice partielle.
   Aucune résistance chiffrée n'est supposée.

Un module eave hinge→mur est documenté à l'origine et consolidé par la
nouvelle poutre. **ZÉRO panneau entièrement stabilisé**. Le graphe de
studs de la poutre et l'audit réel des axes sont dans les preuves JSON.
"""
    (output/"NOTICE-098-SUPPORT-FIXE-ET-STOP.md").write_text(notice,encoding="utf8")
    print("LEGO2_098_FULL_HOUSE",report["full_house_composite_parts"])
    print("LEGO2_098_FIXED_WALL_CROSSBEAMS",report["wall_to_wall_fixed_beam_chains"])
    print("LEGO2_098_BRICK_SEAM_STUD_LAPS",report["real_brick_course_lap_count"])
    print("LEGO2_098_SPAN_STUDS",report["span_studs"])
    print("LEGO2_098_PANELS_WITH_SECOND_FIXED_SUPPORT",report["roof_panels_with_secondary_nonhinge_bearing_proven"])
    print("LEGO2_098_STABLE_COMPLETE_ROOF_PATHS",report["roof_to_wall_complete_stable_paths_proven"])
    print("LEGO2_098_FIX_OLD_REAL_LDRAW_AXES",axes["corrected_count"])
    print("LEGO2_098_OLD_096_F6_CORRECTED",not axes["contains_uncorrected_096_F6"])
    print("LEGO2_098_SEVEN_VIEWS",views)
    print("LEGO2_098_N6",report["physical_strength"])
    return proof

if __name__=="__main__":
    arg=argparse.ArgumentParser()
    arg.add_argument("--source",required=True,type=Path)
    arg.add_argument("--output",required=True,type=Path)
    v=arg.parse_args()
    main(v.source,v.output)
