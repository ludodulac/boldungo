"""MAISON-2: ONE adjacent real east facade bay, while keeping all 126 MAISON-1 LDraw placements."""
from __future__ import annotations
import argparse, hashlib, json, sys
from collections import Counter
from itertools import combinations
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import build_guided004_corner_maison1 as m1
import export_guided004_lego as canonical
from brickhouse.bricks.brick_model import BrickModel
from brickhouse.bricks.geometry_adapter import CANONICAL_LDRAW_PARTS
from brickhouse.scene import ArchitecturalScene
from lego_geometry_engine import LDrawLibrary,find_connections,instantiate,transform_from_ldraw
SCENE=ROOT/"frontend/data/boldungo2-guided-004-real-scene.json"
M1=ROOT/"missions/MAISON1/generated"
BAY_STUDS=8

def in_bay(box,seam,end,y,top):
    """Full original bricks intersecting the next 8-stud front-wall bay; never cut bricks."""
    return box[0]<end and box[3]>seam and box[3]<=end and box[1]==y and box[4]==y+1 and 0<=box[2] and box[5]<=top

def verify_maison1(raw,source):
    lines=[s for s in raw.splitlines() if s.startswith("1 ")]
    if len(lines)!=126:raise AssertionError("MAISON2_OLD_COUNT_NOT_126")
    originals={}
    current=None
    for line in raw.splitlines():
        if line.startswith("0 // CANONICAL-UNCHANGED "):current=line.split()[3]
        elif line.startswith("1 ") and current:
            originals[current]=line
            current=None
    if set(originals)!={p.placement_id for p in source}:raise AssertionError("MAISON2_OLD_SOURCE_IDS_CHANGED")
    for p in source:
        if originals[p.placement_id]!=m1._ldraw_canonical(p):
            raise AssertionError("MAISON2_OLD_COORDINATES_CHANGED:"+p.placement_id)
    return lines

def connections(old,added,new,root):
    """Check new supports only. Lateral contacts are NOT stud connections."""
    oldboxes={p.placement_id:m1.gridbox(p) for p in old}
    oldboxes.update({a.name:a.bbox() for a in added})
    newboxes={p.placement_id:m1.gridbox(p) for p in new}
    allboxes={**oldboxes,**newboxes}
    # Do not modify old models, and reject NEW volume overlaps.
    for a,ab in newboxes.items():
        for b,bb in allboxes.items():
            if a!=b and m1.solid_overlap(ab,bb):
                raise AssertionError("MAISON2_NEW_VOLUME_COLLISION:"+a+":"+b)
    ldr={p.placement_id:m1._ldraw_canonical(p) for p in old+new}
    ldr.update({a.name:m1._ldraw_experiment(a) for a in added})
    library=LDrawLibrary(root)
    cache={}
    def obj(k):
        if k not in cache:
            tokens=ldr[k].split()
            cache[k]=instantiate(library.load_part(tokens[-1]),k,
                transform_from_ldraw([float(n) for n in tokens[2:14]]))
        return cache[k]
    edges=[]
    unsupported=[]
    lateral=[]
    for a,ab in newboxes.items():
        supports=[(b,m1.touching(ab,bb)) for b,bb in allboxes.items()
                  if b!=a and m1.touching(ab,bb)>0]
        if not supports:unsupported.append(a)
        for b,cells in supports:
            con=find_connections(obj(a),obj(b))
            edges.append({"upper":a,"lower":b,"overlap_stud_cells":cells,
                         "actual_engine_connector_count":len(con),
                         "engine_recognized":bool(con),
                         "insertion":"NOT_DEMONSTRATED"})
        for b,bb in oldboxes.items():
            if b.startswith("M1-"):continue
            if ab[1]==bb[1] and ab[4]==bb[4] and (ab[0]==bb[3] or ab[3]==bb[0]) and max(ab[2],bb[2])<min(ab[5],bb[5]):
                lateral.append({"new":a,"existing":b,"result":"SIDE_CONTACT_NOT_STUD_BOND"})
    return {"new_collisions":0,"new_support_edges":len(edges),
        "new_support_edges_with_real_connectors":sum(e["engine_recognized"] for e in edges),
        "new_support_edges_detail":edges,
        "new_parts_without_underlying_support":unsupported,
        "side_seam_contacts_non_mechanical":lateral,
        "maison1_old_42_edges_retested":False,
        "maison1_two_baseplate_post_joins":"NOT_PROVEN",
        "mesh_exhaustive":"NOT_DONE",
        "continuous_insertion":"NOT_PROVEN",
        "physical_strength":"NOT_CERTIFIED"}

def run(out,ldraw_root):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    original=(M1/"MAISON1-EST-SUD-FRAGMENT.ldr").read_text()
    prov=json.loads((M1/"MAISON1-PROVENANCE.json").read_text())
    bom1=json.loads((M1/"MAISON1-NOMENCLATURE.json").read_text())
    sha=hashlib.sha256(SCENE.read_bytes()).hexdigest()
    if sha!=prov["source_scene_sha256"]:raise AssertionError("MAISON2_SCENE_HASH_CHANGED")
    scene=ArchitecturalScene.model_validate_json(SCENE.read_bytes())
    if (scene.volumes[0].width.value,scene.volumes[0].depth.value)!=(9.3,8.2):
        raise AssertionError("MAISON2_SCENE_METRIC_CHANGED")
    oldsource,oldout=canonical.SOURCE,canonical.OUTPUT
    try:
        canonical.SOURCE=SCENE
        canonical.OUTPUT=out/"ISOLATED-CANONICAL-1890"
        inventory=canonical.generate()
    finally:
        canonical.SOURCE,canonical.OUTPUT=oldsource,oldout
    if inventory["total_bricks"]!=1890 or hashlib.sha256(SCENE.read_bytes()).hexdigest()!=sha:
        raise AssertionError("MAISON2_CANONICAL_MODEL_CHANGED")
    full=BrickModel.model_validate_json((out/"ISOLATED-CANONICAL-1890"/"brick-model.json").read_bytes())
    ids=set(prov["original_part_ids"])
    preserved=[p for p in full.parts if p.placement_id in ids]
    if len(ids)!=91 or len(preserved)!=91:raise AssertionError("MAISON2_91_ORIGINALS_LOST")
    old_lines=verify_maison1(original,preserved)
    info=prov["selected_segment"]
    added,_=m1.adapted_supports(preserved,info)
    if len(added)!=35 or not {m1._ldraw_experiment(a) for a in added}.issubset(set(old_lines)):
        raise AssertionError("MAISON2_35_EXPERIMENTAL_PARTS_CHANGED")
    x0=info["east_front_x0"]
    seam=max(m1.gridbox(p)[3] for p in preserved if p.component=="wall" and p.facade=="front")
    end=min(seam+BAY_STUDS,x0+full.width_studs)
    if end<=info["front_end"]:raise AssertionError("MAISON2_NO_ADJACENT_EXTENSION")
    extension=[p for p in full.parts if p.placement_id not in ids and p.component=="wall" and p.facade=="front"
               and in_bay(m1.gridbox(p),seam,end,info["south_side_y0"],info["wall_top_z"])]
    extension.sort(key=lambda p:(p.z_plates,p.x_studs,p.y_studs,p.placement_id))
    if not extension or len({p.placement_id for p in extension})!=len(extension):
        raise AssertionError("MAISON2_NO_REAL_NEW_BRICKS")
    # Priority 1: tangible LDraw + 3D view, before BOM and targeted connector checks.
    raw=original.splitlines()
    if raw[-1]!="0 NOFILE":raise AssertionError("MAISON2_OLD_LDRAW_TRAILER")
    lines=raw[:-1]+[
        "0 // MAISON-2: EXACT old 126 LDraw placements plus one REAL GUIDED-004 east facade bay.",
        "0 // M1 interior floor discrepancy NOT APPROVED; no new floor or roof."
    ]
    for p in extension:
        lines.extend(["0 // CANONICAL-MAISON2 "+p.placement_id+" facade=front",m1._ldraw_canonical(p)])
    combined="\n".join(lines+["0 NOFILE",""])
    placements=[s for s in combined.splitlines() if s.startswith("1 ")]
    if placements[:126]!=old_lines or len(placements)!=126+len(extension):
        raise AssertionError("MAISON2_M1_126_NOT_PRESERVED")
    (out/"MAISON2-FRAGMENT-AGRANDI.ldr").write_text(combined)
    view=m1._drawing(preserved+extension,added,"BOLDÜNGO MAISON-2 — extension de la vraie façade EST")
    view=view.replace("</svg>",f'<text x="22" y="112" font-family="Arial" font-size="17" fill="#236785">Une travée réelle : x={seam}..{end} tenons. 126 pièces MAISON-1 intactes + {len(extension)} briques canoniques.</text>\n</svg>')
    (out/"MAISON2-VUE-3D-SCHEMATIQUE.svg").write_text(view)
    proof=connections(preserved,added,extension,ldraw_root)
    total=126+len(extension)
    count=Counter(bom1["by_real_LDraw_part"])
    count.update(CANONICAL_LDRAW_PARTS[p.part_id].ldraw_id for p in extension)
    if sum(count.values())!=total:raise AssertionError("MAISON2_BOM_WRONG")
    metadata={"scene_sha256":sha,"canonical_model_count":len(full.parts),
      "source_dimensions_m":{"east":9.3,"south":8.2},
      "maison1_exact_placement_prefix":126,"maison1_ldraw_sha256":hashlib.sha256(original.encode()).hexdigest(),
      "new_source_placement_ids":[p.placement_id for p in extension],
      "bay_old_wall_end_studs":seam,"bay_new_wall_end_studs":end,
      "bay_studs":BAY_STUDS,"studs_per_meter":full.width_studs/9.3,
      "maison1_floor_height_m_not_approved":prov["elevation_approx_m"],
      "nominal_level_m":info["scene_first_level_nominal_m"],
      "scene_mutated":False,"old_model_mutated":False}
    bom={"total":total,"maison1_preserved":126,"actual_canonical_bricks_added":len(extension),
         "by_real_LDraw_part":dict(sorted(count.items())),"new_window_proxies":0,
         "original_30_window_proxies_still_not_certified_glazing":True}
    assembly={"maison1_initial_126":"UNCHANGED","new_source_bottom_up":[p.placement_id for p in extension],
              "insertion":"NOT_DEMONSTRATED","physical_strength":"NOT_CERTIFIED"}
    result={"parts_total":total,"preserved":126,"new_source_bricks":len(extension),
            "bay":[seam,end],"new_connections":proof["new_support_edges"],
            "recognized_new_connections":proof["new_support_edges_with_real_connectors"],
            "unsupported_new_bricks":len(proof["new_parts_without_underlying_support"]),
            "new_collisions":proof["new_collisions"],"mechanics":"NOT_CERTIFIED",
            "floor_difference_m_not_approved":round(prov["elevation_approx_m"]-info["scene_first_level_nominal_m"],4)}
    for file,data in [("MAISON2-PROVENANCE.json",metadata),("MAISON2-NOMENCLATURE.json",bom),
                      ("MAISON2-CONTROLES-CONNEXIONS.json",proof),("MAISON2-ORDRE-PROPOSE.json",assembly),
                      ("MAISON2-RESULTATS.json",result)]:
        (out/file).write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n")
    print("MAISON2_SINGLE_REAL_BAY",json.dumps(result,sort_keys=True))
    return result

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--ldraw-root",type=Path,required=True)
    args=parser.parse_args()
    run(args.output,args.ldraw_root)
