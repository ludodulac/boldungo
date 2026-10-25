"""BOLDUNGO R-3 — bounded, parametric 45° gabled roof recipe.

The first reusable construction feature rather than a frozen LEGO 31009 model.
Inspired by, *not copied from*, source 31009 / PDF 6038244:
  3832 2x10 support plates — official roof step 2 (page 47);
  3001 2x4 structural bricks — official step 12 (page 54);
  4445 45° 2x8 slopes — official steps 4, 10, 13, 18, 23;
  3023 1x2 plates — official step 6 (page 50), used only as bay join.
  3022 2x2 plates — official step 24 (chimney), experimentally repurposed at ridge.
The 3022 ridge arrangement and flat-bed supports are NEW R-3 ADAPTATIONS.
R-1, R-2, A and GUIDED-004 are neither read nor modified.

There is only one width (8 studs), zero overhang, 45°, and integral
length bays of 8 studs. Invalid combinations are *rejected*, not guessed.

Coordinate conventions: in LDraw, world X is building length, world Z
is building width, world Y is downward. No user-house dimensions.
"""
from __future__ import annotations
from dataclasses import dataclass
from collections import Counter
from pathlib import Path
import argparse,json

SOURCES={
 "LEGO_set":"31009",
 "official_manual":"https://www.lego.com/cdn/product-assets/product.bi.core.pdf/6038244.pdf",
 "original_31009_mapped_steps":{"3832":[2],"3001":[12],
                                   "4445":[4,10,13,18,23],"3023":[6],"3022":[24]},
 "community_R2_model":"missions/R2/31009-ROOF-STEP-PLACEMENTS.tsv",
 "R3_not_official_31009_placement":True,
 "pitch_degrees":45,
 "continuous_assembly_certified":False,
 "physical_strength_certified":False
}
IDENT=(1,0,0,0,1,0,0,0,1)
TURN=(0,0,1,0,1,0,-1,0,0)
FLIP=(-1,0,0,0,1,0,0,0,-1)

@dataclass(frozen=True)
class Brick:
    id:str
    part:str
    role:str
    x:int
    y:int
    z:int
    sx:int
    sy:int
    height:int
    matrix:tuple=IDENT
    source:str="R3_ADAPTATION"
    parents:tuple=()

    def xy(self):
        return set((i,j) for i in range(self.x,self.x+self.sx)
                          for j in range(self.y,self.y+self.sy))

def validate(width_studs,length_studs,pitch_degrees,overhang_studs):
    if isinstance(width_studs,bool) or not isinstance(width_studs,int) or width_studs!=8:
        raise ValueError("R3_WIDTH_ONLY_8_STUDS_TESTED")
    if isinstance(length_studs,bool) or not isinstance(length_studs,int) or not (8<=length_studs<=32) or length_studs%8:
        raise ValueError("R3_LENGTH_MULTIPLE_8_BETWEEN_8_AND_32_ONLY")
    if type(pitch_degrees) not in (int,float) or pitch_degrees!=45:
        raise ValueError("R3_PITCH_45_DEGREES_ONLY")
    if type(overhang_studs) not in (int,float) or overhang_studs!=0:
        raise ValueError("R3_OVERHANG_0_ONLY")

def recipe(width_studs=8,length_studs=8,pitch_degrees=45,overhang_studs=0):
    validate(width_studs,length_studs,pitch_degrees,overhang_studs)
    out=[]
    bays=length_studs//8
    for bay in range(bays):
        y0=8*bay
        for end in (0,6):
            yy=y0+end
            out.append(Brick(f"bay{bay}-cross{end}","3832","cross",
                 -1,yy,-1,10,2,1,TURN,
                 "31009_STEP_2_PART_R3_LOCATION"))
    # Direct 1x2 connector plates over both neighboring bays, outside
    # 2x4 wall beds. Each connector spans one stud of each 3832 crossplate.
    for j in range(1,bays):
        yy=8*j
        for xx in (-1,8):
            out.append(Brick(f"join-{yy}-x{xx}","3023","joint",
               xx,yy-1,0,1,2,1,IDENT,
               "31009_STEP_6_PART_R3_NEW_BAY_JOIN",
               (f"bay{j-1}-cross6",f"bay{j}-cross0")))
    # Layer-by-layer studs on plate bearings (no R-1 3003 posts).
    for level in (0,3):
        for bay in range(bays):
            y0=8*bay
            for side,course,xx,maxlevel in (("L",0,0,0),("L",1,2,3),
                                             ("R",1,4,3),("R",0,6,0)):
                if level>maxlevel:continue
                for half in (0,4):
                    yy=y0+half
                    pid=f"bay{bay}-{side}{course}-bed{half}-z{level}"
                    if level==0:
                        parent=f"bay{bay}-cross{0 if half==0 else 6}"
                    else:
                        parent=f"bay{bay}-{side}{course}-bed{half}-z0"
                    out.append(Brick(pid,"3001","wall",xx,yy,level,2,4,3,
                      IDENT,"31009_STEP_12_PART_R3_LOCATION",(parent,)))
    for course in (0,1):
        for bay in range(bays):
            y0=8*bay
            for side,xx,m in (("L",(0,2)[course],IDENT),
                              ("R",(6,4)[course],FLIP)):
                p=(f"bay{bay}-{side}{course}-bed0-z{3 if course else 0}",
                   f"bay{bay}-{side}{course}-bed4-z{3 if course else 0}")
                out.append(Brick(f"bay{bay}-{side}{course}-slope",
                    "4445","slope",xx,y0,3+course*3,2,8,3,m,
                    "31009_STEPS_4_10_13_18_23_PART_R3_MODULAR_POSITION",p))
    for bay in range(bays):
        y0=8*bay
        for j in (0,2,4,6):
            out.append(Brick(f"bay{bay}-ridge{j}","3022","ridge",
                3,y0+j,9,2,2,1,IDENT,
                "31009_STEP_24_CHIMNEY_PART_R3_NEW_RIDGE_LAYOUT",
                (f"bay{bay}-L1-slope",f"bay{bay}-R1-slope")))
    out.sort(key=lambda p: ({"cross":0,"joint":1,"wall":2,"slope":3,"ridge":4}[p.role],p.z,p.y,p.x,p.id))
    ids=[p.id for p in out]
    if len(ids)!=len(set(ids)):raise AssertionError("R3_DUPLICATE_ID")
    index={p.id:p for p in out}
    if any(parent not in index for p in out for parent in p.parents):
        raise AssertionError("R3_MISSING_PARENT")
    return out

def _matrix_string(mat):
    return " ".join(str(k) for k in mat)

def _coord(p,length_studs):
    # Explicit official geometry reference: LDraw 4445 tubes at seven
    # mid-stud centers, x=-60..60; right side rotates about local Y.
    x=20*(p.y+p.sy/2 - length_studs/2)
    z=20*(p.x+p.sx/2-4)
    if p.role=="slope":
        z=20*(p.x+(1.5 if p.matrix==IDENT else .5)-4)
    y=-8*(p.z+p.height)
    return x,y,z

def ldraw(parts,length_studs):
    data=[
      "0 BOLDUNGO R3 GENERIC ROOF 45 DEG — EXPERIMENTAL",
      "0 Name: R3-GENERIC-45.ldr",
      "0 // ORIGINAL ROOF RECIPE; NOT EXACT LEGO 31009 INSTRUCTIONS",
      "0 // This is NOT a GUIDED-004 model, nor certified strength/insertion"]
    # Exports preserve build order with LEGO STEP separators.
    last_role=None
    for p in parts:
        if last_role and last_role!=p.role:data.append("0 STEP")
        last_role=p.role
        data.append(f"0 // {p.id} {p.role} SOURCE {p.source}")
        wx,wy,wz=_coord(p,length_studs)
        f=lambda val:str(int(val)) if val==int(val) else str(val)
        color=1 if p.role=="slope" else 71 if p.role=="wall" else 8 if p.role in ("cross","joint") else 15
        data.append(f"1 {color} {f(wx)} {f(wy)} {f(wz)} {_matrix_string(p.matrix)} {p.part}.dat")
    return "\n".join(data)+"\n"

def nominal_mating_alignment(child,parent):
    """STRICT GRID/HEIGHT sanity check, never a substitute for LDraw mesh.

    The deliberate one-stud bad-shift regression must fail even though
    an incidental footprint overlap would still remain.
    """
    if parent.z+parent.height!=child.z:
        return False
    if child.role=="joint" and parent.role=="cross":
        return len(child.xy() & parent.xy())==1  # one end stud from each crossplate
    if child.role=="wall" and parent.role=="cross":
        return len(child.xy() & parent.xy())==4  # 2x2 stud pad at bearing
    if child.role=="wall" and parent.role=="wall":
        return child.xy()==parent.xy()
    if child.role=="slope" and parent.role=="wall":
        return child.x==parent.x and len(child.xy() & parent.xy())==8
    if child.role=="ridge" and parent.role=="slope":
        return child.y>=parent.y and child.y<parent.y+8 and len(child.xy() & parent.xy())==1
    return False

def nominal_audit(parts):
    byid={p.id:p for p in parts}
    adj={p.id:set() for p in parts}
    bad_pairs=[(p.id,pid) for p in parts for pid in p.parents
               if not nominal_mating_alignment(p,byid[pid])]
    for part in parts:
        for parent in part.parents:
            adj[part.id].add(parent);adj[parent].add(part.id)
    components=[];remaining=set(adj)
    while remaining:
        root=next(iter(remaining));stack=[root];found={root}
        while stack:
            for nxt in adj[stack.pop()]-found:
                found.add(nxt);stack.append(nxt)
        components.append(sorted(found));remaining-=found
    roots=[p.id for p in parts if p.role=="cross"]
    visited=set(roots)
    changed=True
    while changed:
        new=visited|{p.id for p in parts if p.parents and all(k in visited for k in p.parents)}
        changed=new!=visited;visited=new
    no_parent=[p.id for p in parts if not p.parents and p.role not in ("cross","joint")]
    return {"parts":len(parts),"roof_parts":sum(p.role in ("slope","ridge") for p in parts),
        "roof_slopes":sum(p.role=="slope" for p in parts),
        "nominal_parent_edges":sum(len(p.parents) for p in parts),
        "nominal_components":len(components),
        "nominal_components_sizes":sorted(map(len,components)),
        "no_nominal_bearing":no_parent,
        "nominal_misaligned_parent_pairs":bad_pairs,
        "not_reaching_nominal_foundation":sorted(set(byid)-visited),
        "static_lego_connector_proven":False,
        "continuous_insertion_proven":False,"physical_strength_proven":False}

def export(output,width_studs=8,length_studs=8,pitch_degrees=45,overhang_studs=0):
    parts=recipe(width_studs,length_studs,pitch_degrees,overhang_studs)
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    nominal=nominal_audit(parts)
    bom=dict(sorted(Counter(p.part for p in parts).items()))
    (output/"ROOF-R3.ldr").write_text(ldraw(parts,length_studs))
    (output/"BOM.json").write_text(json.dumps({"parts":len(parts),"by_part":bom},indent=2)+"\n")
    (output/"ORDER.json").write_text(json.dumps([
       {"number":i+1,"id":p.id,"part":p.part,"role":p.role,
        "parents":list(p.parents),"source":p.source,
        "direction":"vertical approach proposed — continuous path NOT certified"}
       for i,p in enumerate(parts)],indent=2)+"\n")
    (output/"EVIDENCE.json").write_text(json.dumps({
       "source":SOURCES,"parameters":{"width_studs":width_studs,"length_studs":length_studs,
            "pitch_degrees":pitch_degrees,"overhang_studs":overhang_studs},
       "nominal":nominal,"bom":bom,"full_collision_audit":"NOT_EXECUTED",
       "complete_real_support_chains":"NOT_PROVEN",
       "physical_strength_proven":False},indent=2)+"\n")
    print("R3_MODEL",json.dumps({"width":width_studs,"length":length_studs,
        "parts":len(parts),"roof":nominal["roof_parts"],
        "nominal_components":nominal["nominal_components"],
        "nominal_without_bearing":len(nominal["no_nominal_bearing"]),
        "bom":bom},sort_keys=True))
    return parts,nominal

if __name__=="__main__":
    cli=argparse.ArgumentParser()
    cli.add_argument("--width-studs",type=int,required=True)
    cli.add_argument("--length-studs",type=int,required=True)
    cli.add_argument("--pitch-degrees",type=float,required=True)
    cli.add_argument("--overhang-studs",type=float,required=True)
    cli.add_argument("--output",type=Path,required=True)
    a=cli.parse_args()
    export(a.output,a.width_studs,a.length_studs,a.pitch_degrees,a.overhang_studs)
