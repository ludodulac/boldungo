"""MAISON-1: ONE true GUIDED-004 east/front + south/left ground-floor corner.

Preserves ALL selected real canonical facade placements and an existing
east-rdc-window-left opening proxy at its true grid coordinates.
Adds one isolated EXPERIMENTAL LEGO baseplate, two interior posts, two S3-like
beams, five floor panels and ONE corner-joining 2x2 plate. Never writes the
canonical Scene/model; project-specific coordinates derive from the existing
1900-era canonical exporter + Scene, never encoded as generation constants.

Important: user-visible "window" remains canonical BRICK_1X1 pseudo-glazing,
NOT LEGO-manufactured window/actual transparent assembly. Floor is a documented
S-3-style construction ADAPTATION, not a Scene assertion of an interior slab.
"""
from __future__ import annotations
import argparse,hashlib,json,sys,math
from pathlib import Path
from collections import Counter
from dataclasses import dataclass,asdict
from itertools import combinations

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from lego_geometry_engine import LDrawLibrary,Relation,check_collision,find_connections,instantiate,transform_from_ldraw
from brickhouse.bricks.brick_model import BrickModel
from brickhouse.bricks.geometry_adapter import CANONICAL_LDRAW_PARTS,brick_model_part_transform
from brickhouse.scene import ArchitecturalScene
import export_guided004_lego as canonical

SCENE=ROOT/"frontend/data/boldungo2-guided-004-real-scene.json"
ID=(1,0,0,0,1,0,0,0,1)
TURN=(0,0,1,0,1,0,-1,0,0)
KNOWN={"3811":(32,32,1),"3003":(2,2,3),"3006":(2,10,3),
       "3832":(10,2,1),"3022":(2,2,1)}

@dataclass(frozen=True)
class Add:
    name:str
    ref:str
    role:str
    x:int
    y:int
    z:int
    w:int
    d:int
    h:int
    matrix:tuple=ID
    color:int=7

    def bbox(self):return (self.x,self.y,self.z,self.x+self.w,self.y+self.d,self.z+self.h)

def gridbox(p):
    m=CANONICAL_LDRAW_PARTS[p.part_id]
    w=m.length_studs if p.rotation_quarter_turns%2 else m.width_studs
    d=m.width_studs if p.rotation_quarter_turns%2 else m.length_studs
    return (p.x_studs,p.y_studs,p.z_plates,
            p.x_studs+w,p.y_studs+d,p.z_plates+m.height_plates)

def solid_overlap(a,b):
    return all(min(a[i+3],b[i+3])>max(a[i],b[i]) for i in range(3))

def touching(upper,lower):
    if upper[2]!=lower[5]:return 0
    return max(0,min(upper[3],lower[3])-max(upper[0],lower[0]))*max(0,min(upper[4],lower[4])-max(upper[1],lower[1]))

def select_fragment(model,scene):
    # Semantic selection: east/front facade lower left observed window, and
    # south/left facade, not hand-measured corner numbers.
    front=[p for p in model.parts if p.component=="wall" and p.facade=="front"]
    side=[p for p in model.parts if p.component=="wall" and p.facade=="left"]
    if not front or not side:raise ValueError("MAISON1_TWO_ORIGINAL_WALLS_MISSING")
    opening=next((o for o in scene.openings if o.id=="east-rdc-window-left"),None)
    if opening is None or opening.facade.value!="front":
        raise ValueError("MAISON1_SOURCE_FRONT_WINDOW_MISSING")
    visual=[p for p in model.parts if p.opening_id==opening.id]
    if not visual:raise ValueError("MAISON1_EXISTING_ORIGINAL_OPENING_PROXY_MISSING")
    x0=min(p.x_studs for p in front if p.z_plates==0)
    y0=min(p.y_studs for p in front if p.z_plates==0)
    # Derive cut *from opening bounding rectangle*, with only one 8-stud
    # standard-brick bay beyond the window, not custom house dimensions.
    vbox=[gridbox(p) for p in visual]
    win_min=min(b[0] for b in vbox)
    win_max=max(b[3] for b in vbox)
    front_end=win_max+8
    # South return cropped to two standard 8-stud sections.
    side_end=y0+2*8+4
    height_step=model.height_plates//scene.volumes[0].floors
    # nearest 3-plate wall course not exceeding first floor. The
    # S3-like beams add 3plates + a plate, so reserve 4plates.
    top_course=(height_step-4)//3*3
    if top_course<12:raise ValueError("MAISON1_SOURCE_TOO_LOW")
    top_z=top_course+3
    selected=[]
    for p in model.parts:
        if p.component not in ("wall","facade_detail") or p.facade not in ("front","left"):
            continue
        a=gridbox(p)
        if a[5]>top_z:continue
        if p.facade=="front" and a[0]>=x0 and a[3]<=front_end and a[1]==y0:
            selected.append(p)
        elif p.facade=="left" and a[0]<=x0 and a[3]>=x0 and a[1]>=y0 and a[4]<=side_end:
            selected.append(p)
    # This is the FIRST level; south upper-storey door proxy begins at z36,
    # though it is not a ground-floor architectural opening. Preserve only
    # the actual RDC east window in the selected facade-detail placeholders.
    selected=[p for p in selected if p.component=="wall" or p.opening_id==opening.id]
    ids={p.placement_id for p in selected}
    if len(ids)!=len(selected):raise AssertionError("DUPLICATE_ORIGINAL")
    if not {p.placement_id for p in visual}<=ids:
        raise ValueError("MAISON1_CUT_TRUNCATED_REAL_WINDOW")
    if len([p for p in selected if p.component=="wall" and p.facade=="front"])<10 or len([p for p in selected if p.component=="wall" and p.facade=="left"])<10:
        raise ValueError("MAISON1_FRAGMENT_NOT_TWO_FACADE_SECTIONS")
    return selected,{"east_front_x0":x0,"south_side_y0":y0,
       "front_end":front_end,"side_end":side_end,
       "top_wall_course_z":top_course,"wall_top_z":top_z,
       "scene_first_level_nominal_m":scene.volumes[0].height.value/scene.volumes[0].floors,
       "window_id":opening.id,
       "window_scene_offset_m":opening.offset_horizontal,
       "window_scene_width_m":opening.width,
       "real_original_opening_proxy_count":len(visual),
       "front_facing_east":True,"left_facing_south":True}

def adapted_supports(selected,geometry):
    x0,y0=geometry["east_front_x0"],geometry["south_side_y0"]
    ztop=geometry["wall_top_z"]
    partboxes=[(p.placement_id,gridbox(p)) for p in selected]
    # Two longitudinal beams have their first two studs fixed to front wall.
    # Rear ends rest on TWO internal columns; all new part coordinates
    # originate from observed front-wall bearing course & genuine 3006 size.
    upper=[p for p in selected if p.component=="wall" and p.facade=="front"
           and gridbox(p)[5]==ztop]
    candidates=[]
    for p in upper:
        b=gridbox(p)
        for x in range(b[0],b[3]-1):
            if x>=x0+2 and x<=geometry["front_end"]-10:
                candidates.append(x)
    candidates=sorted(set(candidates))
    if len(candidates)<2:raise ValueError("MAISON1_INSUFFICIENT_EAST_FACADE_BEARING")
    xleft=candidates[0]
    xright=xleft+8
    if xright not in candidates:raise ValueError("MAISON1_MISSING_EAST_FACADE_SECOND_BEARING")
    # Rear posts are two studs wide, immediately below beam far end;
    # no overlap with facade bricks. The support is an explicit S3-type
    # EXPERIMENT, not an architectural observation.
    yrear=y0+8
    add=[Add("M1-EXPERIMENTAL-BASE-3811","3811","base",x0,y0,-1,32,32,1,color=2)]
    for i,xx in enumerate((xleft,xright)):
        for z in range(0,ztop,3):
            add.append(Add(f"M1-POST-{i}-COURSE-{z//3}","3003","post",
                           xx,yrear,z,2,2,3,color=7))
        add.append(Add(f"M1-BEAM-{i}","3006","beam",xx,y0,ztop,2,10,3,
                       matrix=TURN,color=4))
    for idx,yy in enumerate(range(y0,y0+10,2)):
        add.append(Add(f"M1-UPPER-FLOOR-{idx}","3832","floor",
                       xleft,yy,ztop+3,10,2,1,matrix=ID,color=15))
    # Exact two-face *L*-junction : two-by-two plate bridges top front
    # & side wall studs without moving either facade.
    cx,cy=x0,y0
    add.append(Add("M1-TRUE-CORNER-BOND","3022","corner_bond",cx,cy,
                   ztop,2,2,1,color=19))
    if not all((a.w,a.d,a.h)==KNOWN[a.ref] for a in add):
        raise AssertionError("MAISON1_LDRAW_WRONG_SHAPE")
    collisions=[]
    objects=[(a.name,a.bbox()) for a in add]+partboxes
    for (p,b),(q,c) in combinations(objects,2):
        if solid_overlap(b,c):collisions.append((p,q))
    if collisions:
        raise ValueError("MAISON1_NEW_ORIGINAL_VOXEL_COLLISION:"+repr(collisions[:8]))
    return add,{"post_count":2,"floor_panels":5,"beam_count":2,
                "new_post_course_count":ztop//3,
                "front_beam_attaches_to_real_east_bricks":2,
                "corner_bond_bridges_both_original_façades":True,
                "new_parts_added":len(add),"floor_top_z":ztop+4,
                "left_floor_support_x":xleft,"right_floor_support_x":xright,
                "new_body_voxel_collisions":len(collisions)}

def _ldraw_experiment(part):
    mx=(part.x+part.w/2)*20
    mz=(part.y+part.d/2)*20
    my=-(part.z+part.h)*8
    return f"1 {part.color} {mx:g} {my:g} {mz:g} "+" ".join(map(str,part.matrix))+f" {part.ref}.dat"

def _ldraw_canonical(part):
    mapping=CANONICAL_LDRAW_PARTS[part.part_id]
    transform=brick_model_part_transform(part,mapping).matrix
    loc=[transform[0][3],transform[1][3],transform[2][3]]
    rot=[transform[i][j] for i in range(3) for j in range(3)]
    f=lambda v:str(int(v)) if abs(v-round(v))<1e-8 else f"{v:.7f}"
    color=47 if part.category=="window_pane" else 19
    return f"1 {color} "+" ".join(f(v) for v in (*loc,*rot))+f" {mapping.ldraw_id}.dat"

def export(selected,add):
    text=["0 FILE GUIDED004-MAISON1-EST-SUD-RDC.ldr",
        "0 MAISON-1: Actual canonical GUIDED-004 front-east and left-south window corner.",
        "0 East window panes are ORIGINAL BRICK_1X1 visual PROXIES, NOT certified real window pieces.",
        "0 Experimental structure: LEGO baseplate, two interior posts, 2 beams, 5 floor panels, one corner plate.",
        "0 DO NOT silently call this an official LEGO model or physical construction certification."]
    for p in sorted(selected,key=lambda q:(q.z_plates,q.x_studs,q.y_studs)):
        text.extend([f"0 // CANONICAL-UNCHANGED {p.placement_id} facade={p.facade}",
                     _ldraw_canonical(p)])
    for a in add:
        text.extend([f"0 // EXPERIMENTAL-ADDED {a.name} role={a.role}",_ldraw_experiment(a)])
    return "\n".join(text+["0 NOFILE"])+"\n"

def validate_new(selected,add,root):
    source={p.placement_id:(gridbox(p),_ldraw_canonical(p)) for p in selected}
    new={a.name:(a.bbox(),_ldraw_experiment(a)) for a in add}
    index={**source,**new}
    bynew={a.name:a for a in add}
    relations=[]
    library=LDrawLibrary(root)
    memo={}
    def getinst(key):
        if key not in memo:
            row=index[key][1].split()
            memo[key]=instantiate(library.load_part(row[-1]),key,
                    transform_from_ldraw([float(x) for x in row[2:14]]))
        return memo[key]
    # All new parts (EXCEPT base): each must have an actual supporting
    # underlying part; every support is recorded, not silently inferred.
    edge_rows=[]
    for a in add:
        if a.role=="base":continue
        parents=[(ident,touching(a.bbox(),box)) for ident,(box,_) in index.items()
                 if ident!=a.name and touching(a.bbox(),box)>0]
        if not parents:raise ValueError("MAISON1_NEW_PART_WITH_NO_STUD_BEARING:"+a.name)
        for ident,count in parents:
            ia,ib=getinst(a.name),getinst(ident)
            connectors=find_connections(ia,ib)
            edge_rows.append({"upper":a.name,"lower":ident,"common_stud_cells":count,
                             "real_LDraw_connector_count":len(connectors),
                             "explicit_connectors":bool(connectors),
                             "mesh_relation":"NOT_INDIVIDUALLY_CHECKED",
                             "insertion":"NOT_DEMONSTRATED"})
    samples={}
    for edge in edge_rows:
        k=(bynew[edge["upper"]].ref,edge["lower"] in new
              and bynew[edge["lower"]].ref
              or CANONICAL_LDRAW_PARTS[next(p for p in selected if p.placement_id==edge["lower"]).part_id].ldraw_id)
        if k in samples:continue
        aa,bb=getinst(edge["upper"]),getinst(edge["lower"])
        rel=Relation.SEPARATED if aa.bbox.relation(bb.bbox)==Relation.SEPARATED else check_collision(aa,bb)
        samples[k]={"upper":edge["upper"],"lower":edge["lower"],"mesh":rel.value}
        print("MAISON1_MESH_CLASS",k,rel.value)
    count_positive=sum(e["explicit_connectors"] for e in edge_rows)
    print("MAISON1_NEW_LINKS",len(edge_rows),"CONNECTORS",count_positive,
          "MESH_CLASS_COUNT",len(samples))
    return {"new_edges":edge_rows,
      "new_edges_total":len(edge_rows),
      "engine_recognized_connector_edges":count_positive,
      "sampled_class_geometry":{str(k):v for k,v in samples.items()},
      "sample_mesh_collision_signals":sum(v["mesh"]=="COLLISION" for v in samples.values()),
      "full_model_mesh_collisions":"NOT_EXHAUSTIVELY_CHECKED",
      "original_canonical_wall_joins_reaudited":False,
      "complete_load_chains":"NOT_CERTIFIED",
      "continuous_insertion":"NOT_PROVEN",
      "physical_strength":"NOT_CERTIFIED"}

def _drawing(parts,add,title,focus=False):
    all_parts=[]
    for p in parts:
        x,y,z,x2,y2,z2=gridbox(p)
        role="window" if p.opening_id else "east" if p.facade=="front" else "south"
        all_parts.append((p.placement_id,(x,y,z,x2,y2,z2),role))
    for a in add:
        all_parts.append((a.name,a.bbox(),a.role))
    col={"east":("#d6bd9c","#e9d5bd","#f3e4d0"),
         "south":("#b49a83","#d6b69e","#e8d6c2"),
         "window":("#6aabce","#8bcee9","#bcefff"),
         "base":("#3a8753","#4fab6e","#8dcaaa"),
         "post":("#6f7a8b","#aab7c6","#c3d4e2"),
         "beam":("#924e47","#be7260","#f3a68e"),
         "floor":("#244c9a","#467bc6","#7da6e6"),
         "corner_bond":("#bf771c","#db9a35","#f4c56c")}
    proj=lambda x,y,z:(720+(x-y)*15,500+(x+y)*5.5-z*11)
    polys=[]
    for ident,box,role in all_parts:
        x,y,z,X,Y,Z=box
        p=[(x,y,z),(X,y,z),(X,Y,z),(x,Y,z),(x,y,Z),(X,y,Z),(X,Y,Z),(x,Y,Z)]
        for face,color in zip(((1,2,6,5),(2,3,7,6),(4,5,6,7)),col[role]):
            coords=[p[q] for q in face]
            dep=sum(r[0]+r[1]+r[2]*.04 for r in coords)/4
            points=" ".join(f"{proj(*r)[0]:.1f},{proj(*r)[1]:.1f}" for r in coords)
            polys.append((dep,f'<polygon points="{points}" fill="{color}" stroke="#243345" stroke-width=".55" opacity="{0.55 if role=="window" else .95}"/>'))
    polys.sort(key=lambda v:v[0])
    s=['<svg xmlns="http://www.w3.org/2000/svg" width="1440" height="900" viewBox="0 0 1440 900">',
       '<rect width="1440" height="900" fill="#f6f9fc"/>',
       f'<text x="22" y="47" font-size="29" font-family="Arial" fill="#17314c">{title}</text>',
       '<text x="22" y="78" font-size="16" font-family="Arial" fill="#41617d">EST = avant (fenêtre au RDC) · SUD = côté gauche · positions GUIDED-004 + plancher expérimental</text>',
       '<g>'+"\n".join(x[1] for x in polys)+'</g>',
       '<rect x="18" y="833" width="1402" height="53" fill="#fff0d6" rx="10"/>',
       '<text x="28" y="855" font-size="15" font-family="Arial">Vue 3D SCHÉMATIQUE des volumes. Vrai LDraw séparé. Fenêtre représentée par proxies canoniques, pas vraie menuiserie LEGO.</text>',
       '<text x="28" y="875" font-size="14" font-family="Arial">La dalle, les poteaux intérieurs et la liaison d’angle sont des ADAPTATIONS ; insertions et solidité NON DÉMONTRÉES.</text>',
       '</svg>']
    return "\n".join(s)+"\n"

def scene_plan_svg(scene,info):
    volume=scene.volumes[0]
    # 48 studs span the 9.30m facade, preserving the project's existing
    # scale even when the depth has a different rounding.
    scale=48/volume.width.value
    x0,y0=info["east_front_x0"],info["south_side_y0"]
    left=(info["front_end"]-x0)/scale
    south=(info["side_end"]-y0)/scale
    realx=info["window_scene_offset_m"]
    w=info["window_scene_width_m"]
    S=60
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1100 750" width="1100" height="750">
<rect width="1100" height="750" fill="#f6f8fb"/>
<text x="30" y="45" font-family="Arial" font-size="26">GUIDED-004 — Portion de la vraie Scene (plan du RDC)</text>
<text x="30" y="74" font-family="Arial" font-size="17">Façade EST / avant : {volume.width.value} m (confirmé) · SUD / gauche : {volume.depth.value} m (confirmé)</text>
<rect x="150" y="150" width="{volume.width.value*S:.2f}" height="{volume.depth.value*S:.2f}" fill="#e9e5dd" stroke="#304d68" stroke-width="5"/>
<rect x="150" y="150" width="{left*S:.2f}" height="{south*S:.2f}" fill="#8ed9a8" fill-opacity=".78" stroke="#287b52" stroke-width="3" stroke-dasharray="7 5"/>
<rect x="{150+realx*S:.2f}" y="142" width="{w*S:.2f}" height="16" fill="#288fd4"/>
<text x="150" y="125" font-family="Arial" font-size="18">EST — façade avant (fenêtre bleue)</text>
<text transform="translate(125,350) rotate(-90)" font-family="Arial" font-size="18">SUD — façade gauche</text>
<text x="770" y="190" font-family="Arial" font-size="17">VERT : zone extraite du BrickModel canonique</text>
<text x="770" y="220" font-family="Arial" font-size="16">Fenêtre : {info['window_id']}</text>
<text x="770" y="250" font-family="Arial" font-size="16">Découpe issue du modèle, non dessin inventé.</text>
<text x="30" y="702" font-family="Arial" font-size="15">Vue de situation fidèle à la Scene ; l’intérieur LEGO et la dalle de soutien restent des EXPÉRIMENTATIONS.</text>
</svg>
"""

def run(out,ldrawroot):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    scene_sha=hashlib.sha256(SCENE.read_bytes()).hexdigest()
    scene=ArchitecturalScene.model_validate_json(SCENE.read_bytes())
    oldsource,oldout=canonical.SOURCE,canonical.OUTPUT
    try:
        canonical.SOURCE=SCENE
        canonical.OUTPUT=out/"ISOLATED-CANONICAL-1890"
        inventory=canonical.generate()
    finally:
        canonical.SOURCE,canonical.OUTPUT=oldsource,oldout
    if inventory["total_bricks"]!=1890 or hashlib.sha256(SCENE.read_bytes()).hexdigest()!=scene_sha:
        raise AssertionError("MAISON1_CANONICAL_MODEL_OR_SCENE_CHANGED")
    data=(out/"ISOLATED-CANONICAL-1890"/"brick-model.json").read_bytes()
    full=BrickModel.model_validate_json(data)
    selected,info=select_fragment(full,scene)
    added,adapt=adapted_supports(selected,info)
    file=export(selected,added)
    target=out/"MAISON1-EST-SUD-FRAGMENT.ldr"
    target.write_text(file,encoding="utf8")
    nlines=sum(line.startswith("1 ") for line in file.splitlines())
    if nlines!=len(selected)+len(added):raise AssertionError("MAISON1_LDRAW_INCOMPLETE")
    (out/"MAISON1-VUE-3D-SCHEMATIQUE.svg").write_text(
        _drawing(selected,added,"BOLDÜNGO MAISON-1 — Angle EST–SUD du RDC"),encoding="utf8")
    (out/"MAISON1-LOCALISATION-DANS-SCENE.svg").write_text(scene_plan_svg(scene,info),encoding="utf8")
    b=Counter(CANONICAL_LDRAW_PARTS[p.part_id].ldraw_id for p in selected)+Counter(a.ref for a in added)
    (out/"MAISON1-NOMENCLATURE.json").write_text(json.dumps({
        "total":nlines,"original_canonical_placements_kept":len(selected),
        "adaptations_added":len(added),"by_real_LDraw_part":dict(sorted(b.items())),
        "opening_representation":"CANONICAL_30_BRICK_1X1_SYMBOLIC_PROXY_NOT_GENUINE_GLAZING",
        "no_buying_authorized":True},indent=2,ensure_ascii=False)+"\n")
    (out/"MAISON1-PROVENANCE.json").write_text(json.dumps({
        "source_scene_path":str(SCENE.relative_to(ROOT)), "source_scene_sha256":scene_sha,
        "source_canonical_count":len(full.parts), "original_part_ids":[p.placement_id for p in selected],
        "dimensions_source_scene":{"east_front_m":scene.volumes[0].width.value,
            "south_side_m":scene.volumes[0].depth.value},
        "scale_studs_per_m":full.width_studs/scene.volumes[0].width.value,
        "selected_segment":info,"experimental_supports":adapt,
        "first_floor_level_z_plates":adapt["floor_top_z"],
        "elevation_approx_m":adapt["floor_top_z"]/(full.height_plates/scene.volumes[0].height.value),
        "original_scene_mutated":False,"original_model_mutated":False,
        "accurate_window_glazing_represented":False},indent=2,ensure_ascii=False)+"\n")
    roles_order=("base","post","corner_bond","beam","floor")
    assemble=[{"step":i+1,"part_id":a.name,"ref":a.ref,
       "insertion":"VERTICAL_PROPOSED_NOT_CONTINUOUSLY_PROVEN"}
       for i,a in enumerate(sorted(added,key=lambda x:(roles_order.index(x.role),x.z,x.x,x.y)))]
    (out/"MAISON1-ORDRE-PROPOSE.json").write_text(json.dumps({
       "initial_masonry_original":[p.placement_id for p in sorted(selected,
           key=lambda x:(x.z_plates,x.x_studs,x.y_studs))],
       "original_brick_count":len(selected),"experimental_assembly":assemble,
       "continuous_insertion":"NOT_DEMONSTRATED",
       "load_capacity":"NOT_CERTIFIED"},indent=2,ensure_ascii=False)+"\n")
    evidence=validate_new(selected,added,ldrawroot)
    (out/"MAISON1-CONTROLES-NOUVEAUX-RACCORDS.json").write_text(json.dumps(
       evidence,indent=2,ensure_ascii=False)+"\n")
    results={"parts":nlines,"source_parts":len(selected),"new_parts":len(added),
       "front_wall_count":sum(p.component=="wall" and p.facade=="front" for p in selected),
       "south_wall_count":sum(p.component=="wall" and p.facade=="left" for p in selected),
       "original_window_proxy_count":sum(p.opening_id=="east-rdc-window-left" for p in selected),
       "nominal_terrain_ground_base":"EXPERIMENTAL_3811_NOT_OBSERVED_IN_SCENE",
       "new_orthogonal_body_collisions":adapt["new_body_voxel_collisions"],
       "new_connections":evidence["new_edges_total"],
       "new_connections_with_actual_connector":evidence["engine_recognized_connector_edges"],
       "mesh_sample_collision_signals":evidence["sample_mesh_collision_signals"],
       "complete_assembly":"NOT_PROVEN","mechanical_strength":"NOT_PROVEN"}
    (out/"MAISON1-RESULTATS.json").write_text(json.dumps(results,indent=2,ensure_ascii=False)+"\n")
    print("MAISON1_MODEL",json.dumps(results,sort_keys=True))
    print("MAISON1_REAL_SCENE_FRAGMENT",json.dumps(info,sort_keys=True))
    print("MAISON1_SCENE_ORIGINAL_HASH_PRESERVED",scene_sha)
    return results

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--ldraw-root",type=Path,required=True)
    a=ap.parse_args()
    run(a.output,a.ldraw_root)
