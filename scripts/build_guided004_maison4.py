"""MAISON-4: add all canonical RDC wall pieces for SUD, NORD and OUEST exactly once.
Preserve 239 MAISON-3 LDraw placements. Openings remain symbolic, mechanics not certified.
"""
from __future__ import annotations
import argparse,hashlib,json,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import build_guided004_corner_maison1 as m1
import build_guided004_corner_maison3 as m3
import export_guided004_lego as canonical
from brickhouse.bricks.brick_model import BrickModel
from brickhouse.bricks.geometry_adapter import CANONICAL_LDRAW_PARTS
from brickhouse.scene import ArchitecturalScene
SCENE=ROOT/"frontend/data/boldungo2-guided-004-real-scene.json"
M2=ROOT/"missions/MAISON2/generated"
M3=ROOT/"missions/MAISON3/generated"
OLD_COUNT=239
FACADES=("left","right","back")

def facade_id(value):
    return value.value if hasattr(value, "value") else str(value)

def old_canonical_rows(raw):
    result={};current=None
    for line in raw.splitlines():
        if line.startswith(("0 // CANONICAL-UNCHANGED ","0 // CANONICAL-MAISON2 ","0 // CANONICAL-MAISON3 ")):
            current=line.split()[3]
        elif line.startswith("0 // EXPERIMENTAL-ADDED "):
            current=None
        elif line.startswith("1 "):
            if current is not None:
                if current in result:raise AssertionError("M4_DUPLICATE_OLD_CANONICAL_ID")
                result[current]=line
            current=None
    return result

def ground_openings(scene,nominal_height):
    return {o.id for o in scene.openings
            if facade_id(o.facade) in FACADES and o.offset_vertical<nominal_height and
            o.offset_vertical+o.height>0}

def relevant(p,top,openings):
    if facade_id(p.facade) not in FACADES:return False
    box=m1.gridbox(p)
    if box[2]<0 or box[5]>top:return False
    if p.component=="wall":return True
    return p.component=="facade_detail" and p.opening_id in openings

def schematic(old,adapted,new):
    svg=m1._drawing(old+new,adapted,"BOLDUNGO MAISON-4 - murs EST/SUD/NORD/OUEST RDC GUIDED-004")
    svg=svg.replace('width="1440" height="900" viewBox="0 0 1440 900"',
                    'width="1900" height="900" viewBox="0 0 1900 900"')
    svg=svg.replace("EST = avant (fenêtre au RDC) · SUD = côté gauche · positions GUIDED-004 + plancher expérimental",
                    "EST=front, SUD=left, NORD=right, OUEST=back | Scene GUIDED-004")
    return svg.replace("</svg>",'<text x="22" y="114" font-size="18" font-family="Arial" fill="#9b254c">Ouvertures = PROXYS canoniques ; pas de vitrages reels LEGO ni de certification.</text></svg>')

def build(output,ldraw_root):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    original=(M3/"MAISON3-FACADE-EST-RDC.ldr").read_text(encoding="utf8")
    oldrows=[s for s in original.splitlines() if s.startswith("1 ")]
    if len(oldrows)!=OLD_COUNT or original.splitlines()[-1]!="0 NOFILE":
        raise AssertionError("M4_MAISON3_NOT_EXACT_239")
    oldsha=hashlib.sha256(original.encode("utf8")).hexdigest()
    prior=json.loads((M3/"MAISON3-PROVENANCE.json").read_text())
    scenehash=prior["source_scene_sha256"]
    if hashlib.sha256(SCENE.read_bytes()).hexdigest()!=scenehash:
        raise AssertionError("M4_SCENE_SHA_CHANGED")
    scene=ArchitecturalScene.model_validate_json(SCENE.read_bytes())
    if (scene.volumes[0].width.value,scene.volumes[0].depth.value)!=(9.3,8.2):
        raise AssertionError("M4_ARCHITECTURAL_DIMENSIONS_CHANGED")
    top=prior["bounds"]["nominal_rdc_wall_top_plates"]
    if top!=39:raise AssertionError("M4_RDC_TOP_CHANGED")
    prevsource,prevoutput=canonical.SOURCE,canonical.OUTPUT
    try:
        canonical.SOURCE=SCENE
        canonical.OUTPUT=output/"ISOLATED-CANONICAL"
        inv=canonical.generate()
    finally:
        canonical.SOURCE,canonical.OUTPUT=prevsource,prevoutput
    if inv["total_bricks"]!=prior["canonical_brickmodel_count"] or hashlib.sha256(SCENE.read_bytes()).hexdigest()!=scenehash:
        raise AssertionError("M4_CANONICAL_SOURCE_CHANGED")
    model=BrickModel.model_validate_json((output/"ISOLATED-CANONICAL"/"brick-model.json").read_bytes())
    all_by_id={p.placement_id:p for p in model.parts}
    original_canonical=old_canonical_rows(original)
    if len(original_canonical)!=OLD_COUNT-35 or any(
         k not in all_by_id or m1._ldraw_canonical(all_by_id[k])!=row for k,row in original_canonical.items()):
        raise AssertionError("M4_OLD_CANONICAL_ROWS_CHANGED")
    oldparts=[all_by_id[k] for k in original_canonical]
    _,_,oldadaptations=m3.parse_maison2_original((M2/"MAISON2-FRAGMENT-AGRANDI.ldr").read_text())
    if len(oldparts)+len(oldadaptations)!=OLD_COUNT:raise AssertionError("M4_OLD_239_NOT_ACCOUNTED_FOR")
    openingids=ground_openings(scene,scene.volumes[0].height.value/scene.volumes[0].floors)
    relevant_all=[p for p in model.parts if relevant(p,top,openingids)]
    new=sorted((p for p in relevant_all if p.placement_id not in original_canonical),
               key=lambda p:(p.z_plates,FACADES.index(facade_id(p.facade)),p.y_studs,p.x_studs,p.placement_id))
    # An existing or absent canonical face must NOT force fabrication or block a real partial delivery.
    newids={p.placement_id for p in new}
    if len(new)!=len(newids) or {p.placement_id for p in relevant_all}-set(original_canonical)-newids:
        raise AssertionError("M4_GROUND_WALL_SOURCE_COVERAGE_FAILED")
    byface=Counter(facade_id(p.facade) for p in new)
    existing_by_face=Counter(facade_id(p.facade) for p in relevant_all
                             if p.placement_id in original_canonical)
    available_by_face=Counter(facade_id(p.facade) for p in relevant_all)
    all_wall_by_face=Counter(facade_id(p.facade) for p in model.parts
                             if facade_id(p.facade) in FACADES and p.component=="wall")
    crossed_by_face=Counter(facade_id(p.facade) for p in model.parts
                             if facade_id(p.facade) in FACADES and p.component=="wall"
                             and m1.gridbox(p)[2]<top<m1.gridbox(p)[5])
    ground_wall_by_face=Counter(facade_id(p.facade) for p in model.parts
                                if facade_id(p.facade) in FACADES and p.component=="wall"
                                and m1.gridbox(p)[2]<top)
    state={}
    for facade in FACADES:
        available=available_by_face[facade]
        retained=existing_by_face[facade]
        added=byface[facade]
        if available != retained+added:
            raise AssertionError("M4_MISSING_AVAILABLE_CANONICAL_PARTS:"+facade)
        if available==0:
            if all_wall_by_face[facade]==0:
                status="INCOMPLETE_NO_WALL_IN_CANONICAL_SOURCE"
            elif ground_wall_by_face[facade]>0:
                status="INCOMPLETE_RDC_WALL_EXCLUDED_BY_FILTER"
            else:
                status="INCOMPLETE_NO_RDC_WALL_IN_CANONICAL_SOURCE"
        elif crossed_by_face[facade]>0:
            status="INCOMPLETE_CANONICAL_PART_CROSSES_RDC_LIMIT"
        else:
            status="CANONICAL_RDC_PARTS_COVERED"
        state[facade]={
            "status":status,
            "source_all_wall_parts_all_levels":all_wall_by_face[facade],
            "source_rdc_wall_parts_intersecting_level":ground_wall_by_face[facade],
            "source_rdc_boundary_crossers_excluded":crossed_by_face[facade],
            "source_rdc_available_parts_in_selection":available,
            "already_represented_in_maison3":retained,
            "newly_selected":added,
            "total_represented_canonical_rdc":retained+added,
            "complete_architecture_or_mechanical_certificate":False
        }
    (output/"MAISON4-ETAT-FACADES.json").write_text(
        json.dumps(state,indent=2,ensure_ascii=False)+"\n")
    print("MAISON4_PER_FACADE_REAL_CANONICAL_INVENTORY",json.dumps(state,sort_keys=True),flush=True)
    raw=original.splitlines()[:-1]+[
      "0 // MAISON-4: original MAISON-3 239 placements verbatim, plus all remaining RDC wall source parts.",
      "0 // Door/window visual proxies are not real LEGO glazing."]
    for p in new:
        raw+=[f"0 // CANONICAL-MAISON4 {p.placement_id} facade={facade_id(p.facade)} component={p.component} opening={p.opening_id or '-'}",
              m1._ldraw_canonical(p)]
    raw+=["0 NOFILE",""]
    result_text="\n".join(raw)
    ldrawrows=[v for v in result_text.splitlines() if v.startswith("1 ")]
    if ldrawrows[:OLD_COUNT]!=oldrows or len(ldrawrows)!=OLD_COUNT+len(new):
        raise AssertionError("M4_239_ORIGINAL_LDRAW_ROWS_NOT_UNCHANGED")
    (output/"MAISON4-MURS-RDC-COMPLETS.ldr").write_text(result_text,encoding="utf8")
    (output/"MAISON4-VUE-3D-SCHEMATIQUE.svg").write_text(schematic(oldparts,oldadaptations,new),encoding="utf8")
    bom=Counter(json.loads((M3/"MAISON3-NOMENCLATURE.json").read_text())["by_real_LDraw_part"])
    bom.update(CANONICAL_LDRAW_PARTS[p.part_id].ldraw_id for p in new)
    if sum(bom.values())!=len(ldrawrows):raise AssertionError("M4_BOM_COUNT")
    docs={
      "MAISON4-NOMENCLATURE.json":{"total":len(ldrawrows),"maison3_preserved":OLD_COUNT,"new_canonical_parts":len(new),
                                  "by_real_LDraw_part":dict(sorted(bom.items())),"symbolic_openings_not_actual_glazing":True},
      "MAISON4-ORDRE-PROPOSE.json":{"first_239_same_order":True,"additional_low_to_high":[p.placement_id for p in new],
                                  "insertion":"NOT_PROVEN","physical_strength":"NOT_CERTIFIED"},
      "MAISON4-PROVENANCE.json":{"base_maison3_sha":"c31ee8c64b02c6a099954811b3c95f96ef8dda0b",
                               "original_239_LDraw_SHA256":oldsha,"source_scene_sha256":scenehash,
                               "scene_dimensions_m":{"east":9.3,"south":8.2},"RDC_wall_top_plates":top,
                               "canonical_brick_model_count":len(model.parts),
                               "new_scene_placement_ids":[p.placement_id for p in new],
                               "ground_scene_openings":sorted(openingids),
                               "scene_changed":False,"older_models_changed":False}
    }
    for filename,doc in docs.items():
        (output/filename).write_text(json.dumps(doc,indent=2,ensure_ascii=False)+"\n")
    print("MAISON4_MODEL_SVG_BOM_PUBLISHED_IN_JOB",len(ldrawrows),len(new),dict(byface),flush=True)
    checks=m3.fresh_interfaces(oldparts,oldadaptations,new,ldraw_root)
    (output/"MAISON4-CONNEXIONS-COLLISIONS.json").write_text(json.dumps(checks,indent=2,ensure_ascii=False)+"\n")
    crossing=[p.placement_id for p in model.parts if facade_id(p.facade) in FACADES and p.component in ("wall","facade_detail")
              and m1.gridbox(p)[2]<top<m1.gridbox(p)[5]]
    results={"total_placements":len(ldrawrows),"maison3_preserved":OLD_COUNT,
             "new_canonical_parts":len(new),"new_by_facade":{f:byface[f] for f in FACADES},
             "facade_coverage":{f:state[f]["status"] for f in FACADES},
             "new_connections":checks["new_support_edges"],
             "new_connections_recognized":checks["new_support_edges_with_engine_connectors"],
             "new_orthogonal_collisions":checks["new_body_collisions_count"],
             "full_available_RDC_source_parts_included":all(
                 state[f]["source_rdc_available_parts_in_selection"] ==
                 state[f]["total_represented_canonical_rdc"] for f in FACADES),
             "boundary_crossers_not_included":crossing,"mechanics":"NOT_CERTIFIED"}
    limits={"facades_incomplete":[f for f in FACADES if state[f]["status"].startswith("INCOMPLETE")],
            "facade_status_file":"MAISON4-ETAT-FACADES.json",
            "old_unsupported_links":"NOT_RETESTED",
            "old_experimental_floor_height_m":prior["bounds"]["old_experimental_floor_height_m_unvalidated"],
            "doors_windows":"SYMBOLIC_CANONICAL_PROXIES_NOT_REAL_GLAZING",
            "north_grade":"NOT_MEASURED","full_mesh_collisions":"NOT_AUDITED",
            "boundary_crossers_not_included":crossing,"insertion":"NOT_PROVEN",
            "roof_terraces_upper_floors_chimneys":"NOT_ADDED",
            "mechanical_strength":"NOT_CERTIFIED"}
    for filename,doc in (("MAISON4-RESULTATS.json",results),("MAISON4-LIMITES.json",limits)):
        (output/filename).write_text(json.dumps(doc,indent=2,ensure_ascii=False)+"\n")
    print("MAISON4_ONE_BUILD_RESULT",json.dumps(results,sort_keys=True),flush=True)

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",required=True,type=Path)
    ap.add_argument("--ldraw-root",required=True,type=Path)
    a=ap.parse_args()
    build(a.output,a.ldraw_root)
