"""Mission 095: regenerate the actual GUIDED-004 composite and closed Technic loops.

The 094 tentative trusses are replaced in this NEW experimental variant only.
Real LDraw 32278/32524/6558 are placed at their documented hole positions;
gaps to historical walls and roof are a separate, FAIL-CLOSED proof category.
"""
from __future__ import annotations
import argparse,hashlib,json
from collections import Counter
from pathlib import Path
from brickhouse.bricks.brick_model import BrickModel
from brickhouse.bricks.technic_triangle_095 import build_095,PARTS095
from brickhouse.bricks.triangular_frame_ridge_094 import LOCAL_PARTS
from construct_guided004_hinged_roof_093 import PARTS,save_ldraw,draw_views
PARTS.update(LOCAL_PARTS)
PARTS.update(PARTS095)


def main(src:Path,output:Path):
    sha=hashlib.sha256(src.read_bytes()).hexdigest()
    m=BrickModel.model_validate_json(src.read_bytes())
    if len(m.parts)!=1936: raise ValueError("WRONG_REAL_GUIDED004_091_SOURCE")
    built=build_095(m)
    if hashlib.sha256(src.read_bytes()).hexdigest()!=sha:
        raise AssertionError("SOURCE_VARIANT_CHANGED")
    r=built["report"]
    output.mkdir(parents=True,exist_ok=True)
    foundation=built["foundation"]
    assembly=built["articulated_parts"]
    (output/"BRICKMODEL-095-UNCHANGED-093-WALLS.json").write_text(
        foundation.model_dump_json(indent=2)+"\n",encoding="utf8")
    l=save_ldraw(foundation,assembly,output/"BOLDUNGO-095-REAL-TECHNIC-TRIANGLES.ldr")
    if l["ldraw_mapped_brick_model_part_count"]+l["articulated_ldraw_placed_parts"]!=r["new_total"]:
        raise AssertionError("95_LDRAW_COUNT_MISMATCH")
    nviews=draw_views(foundation,assembly,output/"views")
    for v in (output/"views").glob("*.svg"):
        v.write_text(v.read_text(encoding="utf8").replace("BOLDUNGO 093","BOLDUNGO 095"),
                     encoding="utf8")
    proof={**r,"source091_sha256":sha,"model_LDraw_counts":l,
           "views_produced":nviews,
           "mechanical_strength_certified":False,
           "all_historical_source_variants_unmodified":True,
           "new_LDraw_type1_line_count":r["new_total"],
           "first_frame_closed_by_pins":r["new_assembly_documented_triangle_count"]>=1,
           "construction_gate":"HOLD_WALL_BRACKET_ROOF_TRANSFER_COLLISION_SWEEP"}
    (output/"TECHNIC-095-COMPLETE-EVIDENCE.json").write_text(
        json.dumps(proof,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    new=Counter(p["ldraw_id"] for m in r["triangles"] for p in m["parts"])
    removed=r["removed_bom"]
    bom={"new_total":r["new_total"],"old_total_094":r["old_total"],
         "net_delta":r["net_delta"],
         "added_exact_ldraw_quantities":dict(sorted(new.items())),
         "removed_exact_ldraw_quantities":removed,
         "all_added_positions_in":"TECHNIC-095-COMPLETE-EVIDENCE.json",
         "colors":"UNSPECIFIED_BY_SOURCE_MODEL",
         "order_ready":False,
         "no_original_file_modified":True}
    (output/"BOM-095-EXACT.json").write_text(
        json.dumps(bom,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    steps=[
      "# BOLDÜNGO 095 — montage candidat, fermer d'abord un triangle",
      "",
      "N2 : cinq vraies poutres (4×32278, 1×32524) et quatre 6558.",
      "Ne PAS considérer la résistance N4/N6 certifiée.",
      "",
      "1. Poser l'entrait gauche 32278 dans son plan extérieur.",
      "2. Poser l'entrait droit 32278 dans l'autre plan.",
      "3. Poser le poinçon central 32524 entre eux ; aligner ses trous.",
      "4. Introduire une broche 6558 au point central inférieur,",
      "   en traversant les trois trous colinéaires.",
      "5. Poser les arbalétriers 32278, de part et d'autre du poinçon,",
      "   suivant le triangle de trous 5-12-13.",
      "6. Introduire une 6558 à chacun des deux pieds, en passant dans",
      "   l'entrait et l'arbalétrier concernés (les trois plans sont prévus).",
      "7. Joindre les arbalétriers au trou supérieur no 5 du poinçon",
      "   par une 6558 : les DEUX cycles triangulaires sont alors fermés.",
      "8. Ajouter les deux extensions Technic 32278 aux mêmes broches",
      "   de pieds : ne pas tenter d'insérer une deuxième broche au même trou.",
      "9. ARRET : insertion du module dans le corps entier de la maison,",
      "   jonctions 3700/Studs aux murs et supports de couverture non prouvés.",
      "10. Ne poser ni la toiture ni les panneaux de zinc sur cette ferme",
      "   comme si la capacité des appuis était établie.",
      "",
      "Documentation des pièces: missions/095/CATALOGUE-PIECES-REELLES.md.",
    ]
    (output/"NOTICE-095-TRIANGLE-AVEC-BLOCAGES.md").write_text("\n".join(steps)+"\n",encoding="utf8")
    print("LEGO2_095_COMPLETE_HOUSE",r["new_total"])
    print("LEGO2_095_PIN_CLOSED_A_FRAMES",r["new_assembly_documented_triangle_count"])
    print("LEGO2_095_WALL_GROUNDED_TRUSSES",r["wall_grounded_truss_count"])
    print("LEGO2_095_ROOF_LOAD_PATH_RATED",r["truss_to_roof_load_rated_paths"])
    print("LEGO2_095_SPECIALIZED_COMPONENTS_ADDED",len(new),sum(new.values()))
    print("LEGO2_095_VISUALS",nviews)
    print("LEGO2_095_PHYSICAL_CERTIFICATION",r["physical_strength_certification"])
    return proof

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--source",required=True,type=Path)
    ap.add_argument("--output",required=True,type=Path)
    a=ap.parse_args();main(a.source,a.output)
