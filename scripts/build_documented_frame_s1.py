"""S-1: ONE experimental 20-part load-path module inspired by LEGO 31009.

Not a reconstruction of an actual set: the official LEGO instruction 6038244
documents base -> stacked wall -> horizontal cap (Book 1, pp 5,14,25,43–44;
steps 2,9,19,33–34). This module adapts those traditional methods to 4
columns + 2 transverse beams + 5 floor plates.

One source of geometry, one model, one bounded official LDraw audit.
No new geometry engine; no roof, GUIDED-004 or canonical pipeline mutation.

Grid: X/Z are LEGO studs, level is *plates* (positive up).
LDraw Y points DOWN; all geometry transforms are true official part IDs.
"""
from __future__ import annotations

from collections import Counter,defaultdict
from dataclasses import dataclass,asdict
import argparse,json,math
from pathlib import Path
from lego_geometry_engine import LDrawLibrary,Relation,check_collision,find_connections,instantiate,transform_from_ldraw

OFFICIAL_MANUAL="https://www.lego.com/cdn/product-assets/product.bi.core.pdf/6038244.pdf"
PAGES={"base":"printed 5 / LEGO step 2",
       "stack":"printed 14 step 9; printed 25 step 19",
       "horizontal_tie":"printed 43-44 / steps 33-34"}
# Bricks, plates and their orientations are genuine official LDraw IDs.
# 91405 plate 16x16 is an EXPERIMENTAL substitution for the original 31009
# 3811 baseplate 32x32; 3006/3832 are documented LEGO parts, but their
# placement as floor beams/deck is S-1 experimental, NOT an official step.
DIM={"91405":(16,16,1),"3003":(2,2,3),"3006":(10,2,3),"3832":(2,10,1)}
ROT=(0,0,1,0,1,0,-1,0,0)
ID=(1,0,0,0,1,0,0,0,1)

@dataclass(frozen=True)
class Placement:
    id:str;ref:str;role:str;x:int;y:int;z:int;w:int;d:int;h:int
    rot:tuple=ID;parents:tuple=();color:int=7

    def footprint(self):
        return {(i,j) for i in range(self.x,self.x+self.w)
                      for j in range(self.y,self.y+self.d)}

def model():
    out=[Placement("S1-BASE","91405","base",-8,-8,-1,16,16,1,color=2)]
    for course in range(3):
        for xx in (-5,3):
            for yy in (-5,3):
                name=f"S1-COLUMN-X{xx}-Y{yy}-LEVEL{course}"
                parent="S1-BASE" if course==0 else f"S1-COLUMN-X{xx}-Y{yy}-LEVEL{course-1}"
                out.append(Placement(name,"3003","column",xx,yy,3*course,2,2,3,
                                     parents=(parent,),color=7))
    for yy in (-5,3):
        out.append(Placement(f"S1-BEAM-Y{yy}","3006","beam",-5,yy,9,10,2,3,
                   parents=tuple(f"S1-COLUMN-X{xx}-Y{yy}-LEVEL2" for xx in (-5,3)),color=4))
    for xx in (-5,-3,-1,1,3):
        out.append(Placement(f"S1-FLOOR-X{xx}","3832","floor",xx,-5,12,2,10,1,rot=ROT,
                   parents=("S1-BEAM-Y-5","S1-BEAM-Y3"),color=15))
    if len(out)!=20: raise AssertionError("S1_EXPECTED_20_PARTS")
    return out

def stud_mating(upper,lower):
    """Strict 2D stud grid and vertical boundary test, NOT a mesh clutch proof."""
    overlap=upper.footprint() & lower.footprint()
    # Four actual stud positions must carry every interface in this
    # bounded design; a part shifted by one stud overlaps only 2 studs
    # and MUST NOT be reported as valid.
    if upper.z != lower.z+lower.h or len(overlap)!=4:
        return {"valid":False,"common_stud_cells":len(overlap),
                "reason":"LEVEL_OR_ALL_FOUR_STUD_CENTRES_MISMATCH"}
    return {"valid":True,"common_stud_cells":len(overlap),
            "stud_centres_studs":sorted(map(list,overlap)),
            "nominal_engagement_interface":"upper underside receives lower studs",
            "actual_tube_depth":"NOT_DEMONSTRATED_BY_GRID_ONLY"}

def planned_edges(parts):
    by={p.id:p for p in parts}
    return [(p,by[pid]) for p in parts for pid in p.parents]

def ldraw_line(p):
    if (p.w,p.d,p.h)!=DIM[p.ref]:
        # for a rotated plate DIM already describes WORLD stud dimensions
        raise AssertionError("S1_PART_DIMENSION_NOT_VALIDATED")
    wx=(p.x+p.w/2)*20
    wz=(p.y+p.d/2)*20
    wy=-8*(p.z+p.h)
    return f"1 {p.color} {wx:g} {wy:g} {wz:g} "+" ".join(map(str,p.rot))+f" {p.ref}.dat"

def ldraw(parts):
    seq=["0 FILE BOLDUNGO-S1-SUPPORT-FRAME.ldr",
       "0 BOLDUNGO S-1 — EXPERIMENTAL LOAD BEARING FRAME / 20 REAL PARTS",
       "0 // Original guide: LEGO 31009 manual 6038244 pp 5,14,25,43–44.",
       "0 // This configuration is NOT a LEGO-official exact construction.",
       "0 // No roof, GUIDED-004, tested physical stability or insertion certification."]
    last_stage=""
    for p in parts:
        stage=("BASE" if p.role=="base" else f"COLUMN_LEVEL_{p.z}" if p.role=="column"
               else "TWO_CROSS_BEAMS" if p.role=="beam" else "DECK_PLATES")
        if stage!=last_stage:
            if last_stage: seq.append("0 STEP")
            seq.append(f"0 // ASSEMBLY PHASE {stage}")
            last_stage=stage
        seq.extend([f"0 // {p.id} parent={','.join(p.parents) if p.parents else 'GROUND'}",
                    ldraw_line(p)])
    seq.append("0 NOFILE")
    return "\n".join(seq)+"\n"

def _instance(part,library):
    row=ldraw_line(part).split()
    return instantiate(library.load_part(row[-1]),part.id,
        transform_from_ldraw([float(v) for v in row[2:14]]))

def audit(parts,lib):
    by={p.id:p for p in parts}
    edge_report=[]
    cache={}
    # For EVERY intended parent link: real official mesh connector positions.
    for upper,lower in planned_edges(parts):
        nominal=stud_mating(upper,lower)
        a=cache.setdefault(upper.id,_instance(upper,lib))
        b=cache.setdefault(lower.id,_instance(lower,lib))
        connectors=find_connections(a,b)
        cls=f"{upper.ref}_to_{lower.ref}"
        edge_report.append({
          "upper":upper.id,"lower":lower.id,"class":cls,
          "nominal":nominal,
          "real_official_LDraw_engine_connector_count":len(connectors),
          "matched_connector_positions_ldu":[list(c["position"]) for c in connectors],
          "connector_alignment_engine":bool(connectors),
          "stud_tube_mating_depth":"NOT_INDEPENDENTLY_MEASURED",
          "continuous_insertion":"NOT_DEMONSTRATED",
          "strength":"NOT_CERTIFIED"})
    # One mesh intersection representative of EACH distinct type of intended
    # joint, not a 190-pair exhaustive model verification.
    sample={}
    for up,lo in planned_edges(parts):
        key=f"{up.ref}_to_{lo.ref}"
        if key not in sample:
            a,b=cache[up.id],cache[lo.id]
            rel=Relation.SEPARATED if a.bbox.relation(b.bbox)==Relation.SEPARATED else check_collision(a,b)
            sample[key]={"upper":up.id,"lower":lo.id,
                         "representative_official_mesh_relation":rel.value}
            print("S1_MESH_MATE",key,rel.value)
    for edge in edge_report:
        edge["sampled_class_relation"]=sample[edge["class"]]["representative_official_mesh_relation"]
        edge["geometrically_confirmed_in_representative_class"]=(
          edge["nominal"]["valid"] and edge["connector_alignment_engine"] and
          edge["sampled_class_relation"]=="CONTACT")
        edge["full_link_mesh_examined"]=(
            edge["upper"]==sample[edge["class"]]["upper"])
    def path_to_base(part):
        if part.role=="base":return [part.id]
        seq=[part.id];p=part
        while p.parents:
            p=by[p.parents[0]];seq.append(p.id)
        return seq
    roofless_paths={p.id:path_to_base(p) for p in parts if p.role=="floor"}
    proven_edges=sum(e["geometrically_confirmed_in_representative_class"] for e in edge_report)
    full_edges=sum(e["connector_alignment_engine"] for e in edge_report)
    blockers=[e for e in edge_report if not e["geometrically_confirmed_in_representative_class"]]
    summary={"pieces":len(parts),"roles":dict(Counter(p.role for p in parts)),
       "edges_planned":len(edge_report),
       "nominal_wrong_pairs":sum(not e["nominal"]["valid"] for e in edge_report),
       "connector_aligned_edges":full_edges,
       "sampled_mesh_class_count":len(sample),
       "connector_plus_sample_contact_edges":proven_edges,
       "not_confirmed_under_bounded_rule":len(blockers),
       "sampled_mesh_collision_classes":[k for k,v in sample.items()
                    if v["representative_official_mesh_relation"]=="COLLISION"],
       "complete_global_collision_count":"UNKNOWN_NOT_EXHAUSTIVE",
       "all_floor_to_base_connector_aligned":full_edges==len(edge_report),
       "entire_chain_of_mesh_contact_verified":len(blockers)==0 and
                    len(sample)==len(edge_report),
       "insertion_proven":False,"strength_certified":False,
       "physical_static_load_capacity":"UNKNOWN"}
    print("S1_SUMMARY",json.dumps(summary,sort_keys=True))
    return {"summary":summary,"sample_by_interface_class":sample,
      "individual_parent_edges":edge_report,"five_floor_paths":roofless_paths,
      "limits":"Only one representative pair per mesh-transform class; no full insertion, no independent cavity depth, no load test."}

def svg(parts):
    # Projection is VOLUMETRIC SCHEMATIC — exact positions/footprints, not
    # full official LDraw triangle render.
    poly=[]
    colors={"base":("#346a45","#46925a","#68b379"),
            "column":("#7b8493","#a5b2c3","#d1dbe7"),
            "beam":("#8f4741","#bd6259","#e98e80"),
            "floor":("#234f91","#5480be","#85aadf")}
    def projection(x,y,z):return (590+(x-y)*27,625+(x+y)*10-z*29)
    def coords(points):return " ".join(f"{projection(*p)[0]:.1f},{projection(*p)[1]:.1f}" for p in points)
    for p in parts:
        x,y,z=p.x,p.y,p.z;X=x+p.w;Y=y+p.d;H=z+p.h
        corners=[(x,y,z),(X,y,z),(X,Y,z),(x,Y,z),
                 (x,y,H),(X,y,H),(X,Y,H),(x,Y,H)]
        a,b,c=colors[p.role]
        for idx,col in [([1,2,6,5],a),([2,3,7,6],b),([4,5,6,7],c)]:
            pts=[corners[i] for i in idx]
            poly.append((sum(q[0]+q[1]+q[2]*.025 for q in pts)/4,
                '<polygon points="'+coords(pts)+'" fill="'+col+'" stroke="#233448" stroke-width="1"/>'))
    poly.sort(key=lambda z:z[0])
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 850" width="1200" height="850">'
        '<rect width="1200" height="850" fill="#f3f8ff"/>'
        '<text x="35" y="48" font-size="30" font-family="Arial" fill="#203a59">BOLDÜNGO S-1 — Ossature porteuse LEGO</text>'
        '<text x="35" y="78" font-size="18" font-family="Arial" fill="#3f648a">20 pièces · base 16×16 · 4 poteaux · 2 poutres · 5 plaques de plancher</text>'
        +'<g>'+ "\n".join(x[1] for x in poly)+'</g>'
        '<rect x="15" y="784" width="1170" height="54" rx="8" fill="#fff0d6"/>'
        '<text x="27" y="807" font-family="Arial" font-size="16" fill="#84572b">Vue isométrique SCHÉMATIQUE des volumes, PAS un rendu des maillages LDraw officiels.</text>'
        '<text x="27" y="826" font-family="Arial" font-size="15" fill="#84572b">Les vraies références, positions et orientations LEGO figurent dans S1-OSSATURE.ldr.</text>'
        '</svg>\n')

def produce(out,libroot):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    ps=model()
    bom=dict(sorted(Counter(p.ref for p in ps).items()))
    graph={p.id:list(p.parents) for p in ps}
    if sum(bom.values())!=20:raise AssertionError("BAD_TOTAL")
    checks= [stud_mating(p,next(q for q in ps if q.id==pa))
             for p in ps for pa in p.parents]
    if len(checks)!=26 or not all(x["valid"] for x in checks):
        raise AssertionError("NOMINAL_BAD_MATE")
    (out/"S1-OSSATURE.ldr").write_text(ldraw(ps),encoding="utf8")
    (out/"NOMENCLATURE.json").write_text(json.dumps({
        "total":20,"by_ldraw_reference":bom,"colors_are_experimental":True,
        "all_parts_LDraw_official":True,"no_purchase_order":True},indent=2)+"\n")
    (out/"MONTAGE.json").write_text(json.dumps({
      "build_order":[{"number":i+1,"id":p.id,"role":p.role,"part":p.ref,
                      "bearing_on":list(p.parents),
                      "direction":"vertical top-down APPROACH SUGGESTED, NOT PROVEN CONTINUOUS"}
                  for i,p in enumerate(ps)],
      "steps":5,"full_continuous_insertion":"NOT_PROVEN",
      "authoritative_official_steps":"NOT_IDENTICAL_TO_31009"},indent=2)+"\n")
    (out/"OSSATURE-VUE-3D-SCHEMATIQUE.svg").write_text(svg(ps),encoding="utf8")
    byid={p.id:p for p in ps}
    def route(p):
        seq=[p.id]
        while p.parents:
            p=byid[p.parents[0]]
            seq.append(p.id)
        return seq
    (out/"CHEMIN-D-APPUI.json").write_text(json.dumps({
      "root":"S1-BASE","parent_links":graph,
      "per_floor_plate_routes":{p.id:route(p) for p in ps if p.role=="floor"},
      "bearing_is_geometric_only":True},indent=2)+"\\n")
    results=audit(ps,LDrawLibrary(libroot))
    (out/"PREUVES-GEOMETRIE.json").write_text(json.dumps(results,indent=2)+"\n")
    (out/"PROVENANCE.json").write_text(json.dumps({
       "official_set":"LEGO Creator 31009 Small Cottage",
       "official_manual":OFFICIAL_MANUAL,
       "manual_steps":PAGES,
       "faithful_reconstruction":False,
       "adaptations":["91405 plate16x16 substituted for official set 3811 baseplate",
           "4 x 3003 column stacks are a new 3-course grid",
           "2 x 3006 transverse beams and 5 x 3832 2x10 deck plates are a new floor arrangement"],
       "follows_design_principle":"baseplate wall stack horizontal bracing illustrated by official LEGO 31009",
       "LDRAW_PARTS_VERSION":"pybricks/ldraw @ c43ed06a128a10ed65675166bf42eb6fd608b9b0",
       "full_insertion":False,"mechanical_strength":False},indent=2)+"\n")
    return results

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--ldraw-root",type=Path,required=True)
    arg=ap.parse_args()
    produce(arg.output,arg.ldraw_root)
