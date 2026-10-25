"""R-1: generic, notice-inspired two-pitch 45-degree LEGO roof.

This is an independent experiment, NOT a model copied from LEGO 31009 and
NOT a GUIDED-004 converter. Four official 4445 slopes are supported by 3007
beams and 3003 studs; the ridge uses 3022 plates. The LEGO 31009 book 1
(official PDF 6038244) documents a real step-by-step 45-degree gable roof,
but these dimensions and support patterns are our own adaptation.

LDraw geometry: +X is the roof LENGTH, +Z the roof SPAN; +Y points DOWN.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict, deque
from dataclasses import dataclass
import json
from pathlib import Path

SOURCE = {
    "set": "31009",
    "name": "Creator Small Cottage / La petite maison",
    "official_instructions": "https://www.lego.com/cdn/product-assets/product.bi.core.pdf/6038244.pdf",
    "manual": "1/3",
    "printed_pages": [48, 49, 51, 53, 55, 57, 60, 63, 65, 68],
    "official_roof_principle": (
        "brick and plate-bearing substrate, two opposite runs of 45-degree "
        "slope bricks, higher-course slope bricks and ridge-side finish; "
        "see diagram steps 4-25 (printed pages 49-68)."
    ),
    "not_official_assembly_replica": True,
    "ldraw_pin": "c43ed06a128a10ed65675166bf42eb6fd608b9b0",
}

@dataclass(frozen=True)
class P:
    pid: str
    ldraw: str
    role: str
    gx: int
    gy: int
    z: int  # HEIGHT OF BOTTOM, measured in 8-LDU plates
    sx: int
    sy: int
    height: int=3
    side: str=""
    course: int=-1

    def footprint(self):
        return {(x,y) for x in range(self.gx,self.gx+self.sx)
                      for y in range(self.gy,self.gy+self.sy)}
    def studs(self):
        if self.role=="slope":
            ridge_side_x=self.gx+1 if self.side=="left" else self.gx
            return {(ridge_side_x,y) for y in range(self.gy,self.gy+self.sy)}
        return self.footprint()


def recipe(*, length_studs=8, foundation_z=0):
    """Bounded repeatable bay: 8 studs across eave-to-eave, 8/16 long.

    No attempt to derive architectural dimensions. The 2x8 beam/slope module
    repeats end-to-end, which is the reusable dimension, not a user house.
    """
    if length_studs not in (8,16) or foundation_z!=0:
        raise ValueError("R1_ALLOWED_LENGTH_8_OR_16_FOUNDATION_AT_ZERO_ONLY")
    arr=[P("foundation-3811","3811","base",0,0,-1,32,32,1)]
    step=[]
    for bay in range(length_studs//8):
        y0=12+8*bay
        for side in ("left","right"):
            for course in (0,1):
                x0={"left":(12,14),"right":(18,16)}[side][course]
                top_beam_z=9 if course==0 else 12
                for station in (0,6):
                    for level in range(0,top_beam_z,3):
                        arr.append(P(f"{side}-c{course}-b{bay}-pier{station}-z{level}",
                                     "3003","pier",x0,y0+station,level,2,2))
                arr.append(P(f"{side}-c{course}-b{bay}-purlin","3007",
                             "beam",x0,y0,top_beam_z,2,8))
                arr.append(P(f"{side}-c{course}-b{bay}-roof","4445","slope",
                             x0,y0,top_beam_z+3,2,8,3,side,course))
        for off in (0,2,4,6):
            arr.append(P(f"ridge-b{bay}-y{off}","3022","ridge",15,y0+off,18,2,2,1))
    arr.sort(key=lambda p:(-1 if p.role=="base" else {
       "pier":0,"beam":1,"slope":2,"ridge":3}[p.role],
       p.z,p.course,p.gy,p.gx,p.pid))
    if len({p.pid for p in arr})!=len(arr):
        raise AssertionError("DUPLICATE_PART_ID")
    return arr


def parent_candidates(parts):
    """Pure *nominal* adjacency. Real connections require the mesh audit."""
    byid={p.pid:p for p in parts}
    parents={"foundation-3811":[]}
    for p in parts[1:]:
        if p.role=="pier":
            if p.z==0:
                selected=["foundation-3811"]
            else:
                selected=[q.pid for q in parts if q.role=="pier" and
                          q.gx==p.gx and q.gy==p.gy and q.z+q.height==p.z]
        elif p.role=="beam":
            selected=[q.pid for q in parts if q.role=="pier" and
                      q.gx==p.gx and q.gy in (p.gy,p.gy+6) and
                      q.z+q.height==p.z]
        elif p.role=="slope":
            selected=[q.pid for q in parts if q.role=="beam" and
                      q.gx==p.gx and q.gy==p.gy and q.z+q.height==p.z]
        elif p.role=="ridge":
            selected=[q.pid for q in parts if q.role=="slope" and
                      q.course==1 and q.gy<=p.gy and
                      p.gy+p.sy<=q.gy+q.sy and
                      ((q.side=="left" and (15,p.gy) in q.studs()) or
                       (q.side=="right" and (16,p.gy) in q.studs()))]
        else:
            selected=[]
        parents[p.pid]=sorted(selected)
    reachable={"foundation-3811"}
    while True:
        nxt=reachable|{p.pid for p in parts if
            p.pid!="foundation-3811" and any(q in reachable for q in parents[p.pid])}
        if nxt==reachable:break
        reachable=nxt
    edges=sum(len(x) for x in parents.values())
    return parents,sorted(set(byid)-reachable),edges


def ldraw(parts):
    lines=["0 BOLDUNGO R-1 — experimental roof inspired by LEGO 31009",
           "0 Name: R1-31009-EXPERIMENT.ldr",
           "0 // NOT an official LEGO 31009 reconstruction; geometry unvalidated"]
    ident="1 0 0 0 1 0 0 0 1"
    rot=" -1 0 0 0 1 0 0 0 -1"
    for p in parts:
        lines.append(f"0 // {p.pid} {p.role}")
        if p.role=="base":
            lines.append(f"1 2 0 0 0 {ident} 3811.dat")
            continue
        # 3811 spans studs whose centres range -310..+310; 0-based
        # grid centre maps to world coordinate 20*(grid+0.5-16).
        pos_x=20*(p.gy+p.sy/2-16)
        if p.role=="slope":
            pos_z=20*(p.gx+(1.5 if p.side=="left" else .5)-16)
        else:
            pos_z=20*(p.gx+p.sx/2-16)
        pos_y=-8*(p.z+p.height)
        matrix=rot.strip() if p.role=="slope" and p.side=="right" else ident
        color=1 if p.role=="slope" else 8 if p.role=="ridge" else 71
        fmt=lambda v: str(int(v)) if int(v)==v else str(v)
        lines.append(f"1 {color} {fmt(pos_x)} {fmt(pos_y)} {fmt(pos_z)} {matrix} {p.ldraw}.dat")
    return "\n".join(lines)+"\n"


def audit_nominal(parts):
    parents,unsupported,edges=parent_candidates(parts)
    raw=Counter(p.ldraw for p in parts)
    role=Counter(p.role for p in parts)
    return {"total_parts":len(parts),"roof_parts":role["slope"]+role["ridge"],
       "slope_parts":role["slope"],"ridge_parts":role["ridge"],
       "supports_count":role["pier"]+role["beam"],
       "nominal_support_edges":edges,"nominal_unsupported":unsupported,
       "nominal_components":1 if not unsupported else "NOT_ESTABLISHED",
       "bom_ldraw":dict(sorted(raw.items())),
       "physical_stability_proven":False,"complete_real_insertion_proven":False,
       "all_real_connectors_proven":False,
       "nominal_only":True}

def build(output,*,length_studs=8):
    output=Path(output)
    output.mkdir(parents=True,exist_ok=True)
    parts=recipe(length_studs=length_studs)
    report=audit_nominal(parts)
    (output/"R1-31009-EXPERIMENT.ldr").write_text(ldraw(parts),encoding="utf-8")
    (output/"BOM.json").write_text(json.dumps(
        {"total_parts":len(parts),"ldraw":report["bom_ldraw"]},
        indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    (output/"ORDER.json").write_text(json.dumps(
        [{"step":n+1,"id":p.pid,"ldraw":p.ldraw,"role":p.role,
          "insertion":"vertical-down proposed; NOT fully proven"}
          for n,p in enumerate(parts)],indent=2)+"\n",encoding="utf-8")
    (output/"EVIDENCE.json").write_text(json.dumps(
        {"source":SOURCE,"model_parameters":{"length_studs":length_studs,
         "span_studs":8},"audit":report,"parents":parent_candidates(parts)[0]},
         indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("R1_BUILT",json.dumps({"length_studs":length_studs,
        "total_parts":report["total_parts"],"roof_parts":report["roof_parts"],
        "nominal_unsupported_count":len(report["nominal_unsupported"]),
        "nominal_components":report["nominal_components"],"bom":report["bom_ldraw"]},sort_keys=True))
    return parts,report


if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--output",type=Path,default=Path("artifacts/lego2-roof-r1"))
    a.add_argument("--length-studs",type=int,default=8)
    args=a.parse_args()
    build(args.output,length_studs=args.length_studs)
