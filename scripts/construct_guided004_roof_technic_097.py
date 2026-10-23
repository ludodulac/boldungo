"""097 — real complete and focused LDraw construction exports."""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from collections import Counter
from brickhouse.bricks.brick_model import BrickModel
from brickhouse.bricks.geometry_adapter import CANONICAL_LDRAW_PARTS
from brickhouse.bricks.articulated_technic_transfer_097 import build_097
from brickhouse.bricks.technic_triangle_095 import PARTS095
from brickhouse.bricks.triangular_frame_ridge_094 import LOCAL_PARTS
from construct_guided004_hinged_roof_093 import PARTS,save_ldraw,draw_views

PARTS.update(LOCAL_PARTS)
PARTS.update(PARTS095)
PARTS["32017"]=("TECHNIC_BEAM_5_THIN",5,1)

def exact_bom(f,overlay):
    c=Counter(x["ldraw_id"] for x in overlay)
    for p in f.parts:
        mapping=CANONICAL_LDRAW_PARTS.get(p.part_id)
        if mapping is not None and mapping.placement_kind=="standard":
            c[mapping.ldraw_id]+=1
    return dict(sorted(c.items()))

def export(source:Path,output:Path):
    raw=source.read_bytes(); digest=hashlib.sha256(raw).hexdigest()
    m=BrickModel.model_validate_json(raw)
    if len(m.parts)!=1936:
        raise ValueError("EXPECTED_EXISTING_GUIDED004_091_1936")
    result=build_097(m)
    if source.read_bytes()!=raw:raise AssertionError("SOURCE_CHANGED")
    out=output;out.mkdir(parents=True,exist_ok=True)
    f=result["foundation"]
    a=result["articulated_parts"]
    report=result["report"]
    (out/"BRICKMODEL-097-FOUNDATION.json").write_text(f.model_dump_json(indent=2)+"\n",encoding="utf8")
    modelpath=out/"BOLDUNGO-097-REAL-ARTICULATED-TECHNIC-COMPOSITE.ldr"
    stats=save_ldraw(f,a,modelpath)
    if stats["ldraw_mapped_brick_model_part_count"]+stats["articulated_ldraw_placed_parts"]!=report["new_total"]:
        raise AssertionError("COMPOSITE_097_LDRAW_NOT_EXACT")
    bom=exact_bom(f,a)
    if sum(bom.values())!=report["new_total"]:
        raise AssertionError("097_BOM_TOTAL_BAD")
    (out/"BOM-097-COMPLET-EXACT.json").write_text(json.dumps({
        "total":report["new_total"],"part_by_ldraw":bom,
        "added_from_096":report["added_real_parts_by_ldraw"],
        "removed_from_096":report["removed_real_parts_by_ldraw"],
        "buyable_colors":"UNSPECIFIED","purchase_authorized":False,
        "source_sha256":digest},indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    sub=result["new_subassembly"]
    frameidx=sub["frame"]
    previous=result["previous_096"]["previous_095"]
    old_frame=next(k for k in previous["report"]["triangles"] if k["frame"]==frameidx)
    fids=set()
    for s in old_frame["wall_supports"].values():
        fids.update(s["underlying_grounded_walls"])
    ground=[p for p in f.parts if p.placement_id in fids]
    if not ground:
        raise AssertionError("NO_REAL_GROUNDED_WALL_PIECES_IN_SUBASSEMBLY")
    subfoundation=BrickModel.model_validate({**f.model_dump(mode="json"),
        "building_id":f.building_id+"-097-PARTIAL-SUBASSEMBLY",
        "parts":[p.model_dump(mode="json") for p in ground]})
    wanted=set(p["placement_id"] for p in old_frame["parts"]) - set(sub["remove_ids"])
    wanted.update(p["placement_id"] for p in sub["new_parts"])
    wanted.update(x["placement_id"] for x in a if x["placement_id"].startswith("095-REPLACE-")
                  and x["ldraw_id"]=="3700" and
                  x["xyz_ldu"][2]==(sub["bay"]+.5)*20)
    wanted.add(sub["roof_rail_id"])
    mini=[p for p in a if p["placement_id"] in wanted]
    save_ldraw(subfoundation,mini,out/"SOUS-ASSEMBLAGE-097-FERME0.ldr")
    n=draw_views(f,a,out/"views")
    for page in (out/"views").glob("*.svg"):
        page.write_text(page.read_text(encoding="utf8").replace("BOLDUNGO 093","BOLDUNGO 097"),encoding="utf8")
    proof={**report,"complete_model_source_sha256":digest,
           "actual_ldraw_part_count":report["new_total"],
           "subassembly_ldraw_file":"SOUS-ASSEMBLAGE-097-FERME0.ldr",
           "subassembly_wall_brick_ids":sorted(fids),
           "subassembly_ldraw_piece_count":len(mini)+len(ground),
           "graph":result["graph"],
           "views_generated":n}
    (out/"PREUVES-097-LEGO-CONNEXIONS.json").write_text(
        json.dumps(proof,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    steps="""# BOLDÜNGO 097 — premier sous-assemblage Technic exact, insertion NON achevée

Ne pas confondre une chaîne de TROIS jonctions à axes exacts (N2) avec
une structure stable : l'articulation centrale a encore un degré de liberté.

1. Construire les deux couronnements de mur avec leurs véritables deux
   tenons sous chaque 3700 de la travée 0 (096/095).
2. Préassembler l'entrait et les arbalétriers 5:12:13 de la ferme 095 ;
   présenter les 6558 AVANT les fermetures du module.
3. Positionner le rail de couverture 3460 à 22° comme dans le modèle 093.
4. Accrocher par deux tenons la 3700 096 sous ce rail, sans modifier l'angle.
5. Remplacer seulement le renfort rigide 32524 096 de la travée 0 par
   DEUX vrais liftarms fins 32017 (5 trous), articulés en un coude.
6. Trois vraies broches 2780 en travers des assemblages adjacents :
   3700/32017, 32017/32017, 32017/arbalétrier 32278.
   Introduire d'abord les broches aux extrémités ACCESSIBLES du petit
   sous-assemblage, puis fermer le coude par le côté libre.
7. Stop : sans triangulation ou blocage du coude, cette liaison est MOBILE,
   NON PORTEUSE démontrée. Ajouter une entretoise/contreventement de
   famille prouvée ou changer le support de couverture AVANT de poser
   des charges. La portée des pannes reste à contrôler.
8. L'insertion des 2780, leurs collerettes et les volumes balayés restent
   à valider contre les vrais corps des pièces; un simple calcul d'axe
   et un rendu LDraw ne sont pas une preuve N5.
9. Les cinq fermes sans deux murs restent non fondées dans ce candidat.
   Ne pas commander de pièces ni éditer de notice finale : NOT_CERTIFIED.

Constat : 096 0,0507923 LDU -> 097 axes nominaux coïncidents sans flexion,
mais 0 chemin de charge stabilisé et 0 insertion complète certifiée.
"""
    (out/"NOTICE-097-SOUS-ASSEMBLAGE-ET-BLOCAGES.md").write_text(steps,encoding="utf8")
    print("097_PARTS",report["new_total"])
    print("097_EXACT_CONNECTOR_GRAPHS",report["geometrically_exact_roof_to_truss_to_wall_connector_chains"])
    print("097_MECHANICALLY_STABLE_PATHS",report["mechanically_stable_roof_to_wall_load_paths"])
    print("097_ACTUAL_GROUNDED_FRAMES",report["two_walls_grounded_frames"])
    print("097_JOINT_RESIDUAL",report["new_max_joint_residual_ldu"])
    print("097_PIN_NOMINAL_STACKS",report["new_2780_nominal_pin_stacks"])
    print("097_FULL_INSERTIONS",report["complete_insertion_sweeps_verified"])
    print("097_SUBASSEMBLY_PARTS",proof["subassembly_ldraw_piece_count"])
    print("097_VIEWS",n)
    print("097_PHYSICAL_CERTIFICATION",report["physical_certification"])
    return proof

if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--source",required=True,type=Path)
    a.add_argument("--output",required=True,type=Path)
    opts=a.parse_args()
    export(opts.source,opts.output)
