"""099 full GUIDED-004 gable inspection and actual first supported-stud pedestal."""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from collections import Counter
from brickhouse.bricks.brick_model import BrickModel
from brickhouse.bricks.geometry_adapter import CANONICAL_LDRAW_PARTS
from brickhouse.bricks.gable_roof_bearing_099 import build_099
from brickhouse.bricks.triangular_frame_ridge_094 import LOCAL_PARTS
from construct_guided004_hinged_roof_093 import PARTS,save_ldraw,draw_views
PARTS.update(LOCAL_PARTS)
PARTS.update({"3020":("PLATE_2X4",4,2),"2456":("BRICK_2X6",6,2),
              "3003":("BRICK_2X2",2,2),"3024":("PLATE_1X1",1,1)})
def bom(f,overlay):
    counts=Counter(p["ldraw_id"] for p in overlay)
    for p in f.parts:
        d=CANONICAL_LDRAW_PARTS.get(p.part_id)
        if d is not None and d.placement_kind=="standard":
            counts[d.ldraw_id]+=1
    return dict(sorted(counts.items()))
def main(source:Path,output:Path):
    raw=source.read_bytes();sha=hashlib.sha256(raw).hexdigest()
    m=BrickModel.model_validate_json(raw)
    if len(m.parts)!=1936:raise ValueError("REQUIRES_REAL_091_GUIDED004_1936")
    out=build_099(m)
    report=out["report"];f=out["foundation"];assembly=out["articulated_parts"]
    if source.read_bytes()!=raw:raise AssertionError("SOURCE_CHANGED")
    output.mkdir(parents=True,exist_ok=True)
    (output/"BRICKMODEL-099-FOUNDATION-GABLE.json").write_text(
        f.model_dump_json(indent=2)+"\n",encoding="utf8")
    stats=save_ldraw(f,assembly,output/"BOLDUNGO-099-GABLE-AND-22DEG-ROOF.ldr")
    if stats["ldraw_mapped_brick_model_part_count"]+stats["articulated_ldraw_placed_parts"]!=report["full_house_parts"]:
        raise AssertionError("MISSING_REAL_099_LDRAW_PLACEMENTS")
    counts=bom(f,assembly)
    if sum(counts.values())!=report["full_house_parts"]:
        raise AssertionError("WRONG_LDRAW_BOM")
    (output/"BOM-099-EXACT.json").write_text(json.dumps({
        "parts":report["full_house_parts"],"ldraw_counts":counts,
        "added_real_3024":report["added_3024_gable_plates"],
        "source_sha256":sha,"purchase_list_approved":False,
        "colors":"UNSPECIFIED"},ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    viewcount=draw_views(f,assembly,output/"views")
    for svg in (output/"views").glob("*.svg"):
        svg.write_text(svg.read_text(encoding="utf8")
                       .replace("BOLDUNGO 093","BOLDUNGO 099"),encoding="utf8")
    # The true LDraw sub-assembly includes a grounded gable source brick,
    # exact placed plates and nearby sloping panel rail. Ground-connected
    # parent wall paths are documented in the full-house report.
    pedestal=report["pedestal"]
    focus=[]
    if pedestal:
        focus=[p for p in f.parts if p.placement_id==pedestal["source_gable_brick"]
               or p.placement_id.startswith("EXPERIMENT-099-GABLE-")]
        focusids={pedestal["roof_rail_id"]}
        area=pedestal["roof_rail_id"].split("-")
        bay=area[3]
        focusids.update({f"093-negative-basehinge-{bay}-0",
                        f"093-negative-roofhinge-{bay}-0"})
    else:focusids=set()
    mini=BrickModel.model_validate({**f.model_dump(mode="json"),
        "building_id":"BOLDUNGO-099-GABLE-SECOND-BEARING-SUBASSEMBLY",
        "parts":[p.model_dump(mode="json") for p in focus]})
    mini_overlay=[p for p in assembly if p["placement_id"] in focusids]
    mini_stats=save_ldraw(mini,mini_overlay,
                     output/"SOUS-ASSEMBLAGE-099-PIGNON-ET-TOIT.ldr")
    summary={**report,"source_091_sha256":sha,"view_count":viewcount,
             "model_ldraw_count":report["full_house_parts"],
             "subassembly_piece_count":mini_stats["ldraw_mapped_brick_model_part_count"]+
                                       mini_stats["articulated_ldraw_placed_parts"],
             "final_artifact_not_stable":True}
    (output/"GRAPHE-ET-INVENTAIRE-099.json").write_text(
        json.dumps(summary,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    txt="""# BOLDÜNGO — 099 : montage réel du premier appui de pignon, ARRÊT

1. Construire les quatre façades selon les positions du vrai modèle.
2. Construire le pignon EXISTANT en briques standards à sa hauteur
   d'origine. Les pièces des autres variantes ne doivent pas être modifiées.
3. Construire les deux appuis 098 sur les tenons de la maçonnerie fondée.
4. Sur une vraie brique du pignon avant reliée à la fondation, assembler
   les plaques 3024 identifiées dans GRAPHE-ET-INVENTAIRE-099.json,
   successivement et VERTICALEMENT par leurs tenons.
5. La hauteur est calculée en utilisant la VRAIE face inférieure du
   rail incliné 3460 LDraw à 22°, et non des points approximatifs.
6. ATTENTION : le rail est incliné et les 3024 restent HORIZONTALES.
   Un écart de hauteur au centre NE DÉMONTRE PAS une interface de tenon
   ou un appui portant exactement au bon endroit. Ne pas forcer
   la rencontre des pièces, et ne pas déclarer ce point stable.
7. Installer le panneau uniquement pour INSPECTION du modèle LDraw ;
   son verrouillage en rotation et soulèvement N4/N5 manque toujours.
8. Arrêt structurel : tant qu'une paire de vrais connecteurs LEGO
   anti-pivot (ou un berceau rigidifié) n'est pas construite,
   zéro panneau avec deux appuis positivement verrouillés.

Ordre des étapes 1-4 plausiblement faisable sur les tenons standards ;
passage 5-8 : position modélisée, insertion et résistance NON PROUVÉES.
Aucune résistance chiffrée, aucun essai physique demandé à Ludovic.
"""
    (output/"NOTICE-099-MONTAGE-PARTIEL-ET-ARRET.md").write_text(txt,encoding="utf8")
    print("LEGO2_099_GABLE_FRONT",report["facades"]["front"]["gable_piece_count"])
    print("LEGO2_099_GABLE_REAR",report["facades"]["rear"]["gable_piece_count"])
    print("LEGO2_099_GROUNDED_FRONT",report["facades"]["front"]["grounded_gable_piece_count"])
    print("LEGO2_099_GROUNDED_REAR",report["facades"]["rear"]["grounded_gable_piece_count"])
    print("LEGO2_099_ADDED_REAL_PLATES",report["added_3024_gable_plates"])
    print("LEGO2_099_GAP_LDU",pedestal["gap_ldu"] if pedestal else "NO_GROUNDED_CONTACT")
    print("LEGO2_099_PARTS",report["full_house_parts"])
    print("LEGO2_099_FIXED_TWO_SUPPORT_ROOF_PANELS",report["roof_panels_with_two_restrained_fixed_supports"])
    print("LEGO2_099_FULL_LOAD_PATHS",report["roof_to_wall_two_support_N4_paths"])
    print("LEGO2_099_VIEWS",viewcount)
    print("LEGO2_099_N6",report["N6"])
    return summary
if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--source",required=True,type=Path)
    parser.add_argument("--output",required=True,type=Path)
    options=parser.parse_args()
    main(options.source,options.output)
