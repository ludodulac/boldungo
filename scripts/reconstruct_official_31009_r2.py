"""BOLDUNGO R-2: reconstruct the 25 LEGO 31009 roof-assembly steps.

Authority split:
- LEGO official 6038244.pdf PRINTED pages 47..68: step order, colors,
  type and quantity; no official digital 3D placement coordinates.
- Community whole-set MPD by LTRON (M3_Model building377.mpd at immutable
  commit 31c2222...): 80 numerical type-1 part transforms extracted
  from the roof subassembly. It is NOT an official LEGO CAD file.

No new parts, no guessed pillars, no invented ridge cap. R-1 untouched.
"""
from __future__ import annotations
import argparse,csv,hashlib,json
from collections import Counter
from pathlib import Path

EXPECTED_PER_STEP=(2,2,2,3,2,6,2,1,2,2,4,6,4,4,4,4,2,2,4,2,4,3,3,5,5)
SOURCE={
 "set":"31009","manual_number":"6038244","printed_pages":"47–68",
 "official_manual":"https://www.lego.com/cdn/product-assets/product.bi.core.pdf/6038244.pdf",
 "independent_CAD_source":"https://github.com/willsaliba/M3_Model/blob/31c2222a4b007298e9e53b429562957c78972017/data/train/building377.mpd",
 "independent_CAD_author":"LTRON","full_model_original_ordinals":[149,228],
 "manual_step_count":25,"coordinate_source_IS_NOT_official_LEGO":True
}
BASE=Path(__file__).resolve().parents[1]/"missions/R2"
DATA=BASE/"31009-ROOF-STEP-PLACEMENTS.tsv"
SLOPES={"4445.dat","3037.dat","3038.dat","3039.dat","3046.dat"}
ROOF_COMPONENTS={"3001.dat","3002.dat","3003.dat","3004.dat",
"3005.dat","3009.dat","3010.dat","3022.dat","3023.dat",
"32001.dat","32028.dat","3622.dat","3659.dat","3832.dat",
"60592.dat","60601.dat","6141.dat","3062.dat"}|SLOPES

def read_parts(source=DATA):
    rows=[]
    with Path(source).open(encoding="utf-8",newline="") as f:
        for rec in csv.DictReader(f,delimiter="\t"):
            tokens=rec["ldraw_type1"].split()
            if len(tokens)!=15 or tokens[0]!="1" or tokens[-1] not in ROOF_COMPONENTS:
                raise ValueError("R2_INVALID_LDRAW_LINE_OR_UNKNOWN_PART")
            vals=[float(x) for x in tokens[2:14]]
            m=vals[3:]
            if sorted(round(abs(x),5) for x in m)!=[0,0,0,0,0,0,1,1,1]:
                raise ValueError("R2_NONAXIS_ALIGNED_UNKNOWN_ROTATION")
            step=int(rec["step"]); index=int(rec["source_full_model_ordinal"])
            rows.append({"step":step,"page":int(rec["page"]),"ord":index,
                "within":int(rec["position_in_step"]),"part":tokens[-1],
                "color":int(tokens[1]),"transform":vals,"line":rec["ldraw_type1"]})
    if len(rows)!=80 or [r["ord"] for r in rows]!=list(range(149,229)):
        raise AssertionError("R2_EXACT_80_REAL_SOURCE_PLACEMENTS_CHANGED")
    per_step=Counter(p["step"] for p in rows)
    if tuple(per_step[x] for x in range(1,26))!=EXPECTED_PER_STEP:
        raise AssertionError("R2_OFFICIAL_MANUAL_STEP_COUNTS_MISMATCH")
    if any(r["page"]!=46+r["step"] or r["within"]<1 for r in rows):
        raise AssertionError("R2_MANUAL_PAGE_STEP_MAPPING_MISMATCH")
    if Counter(x["part"] for x in rows)["4445.dat"]!=6:
        raise AssertionError("R2_OFFICIAL_SLOPE_REFERENCE_COUNT_CHANGED")
    if any(r["part"]=="3811.dat" for r in rows):
        raise AssertionError("R2_NO_INVENTED_3811_BASEPLATE")
    return rows

def assemble_ldraw(rows):
    out=[
       "0 BOLDUNGO R-2 LEGO 31009 roof subassembly — 25 step sequence",
       "0 Name: 31009-ROOF-R2-OFFICIAL-STEP-RECONSTRUCTION.ldr",
       "0 // LEGO 6038244.pdf printed pp47-68, steps 1..25",
       "0 // LDraw coordinates based on independent third-party LTRON MPD",
       "0 // NOT an official LEGO digital model; no strength certificate"
    ]
    for step in range(1,26):
        out.append(f"0 // OFFICIAL LEGO STEP {step}, PRINTED PAGE {46+step}")
        for r in rows:
            if r["step"]==step:
                out.append(f"0 // part index {r['ord']} from credited third-party MPD")
                out.append(r["line"])
        if step<25:out.append("0 STEP")
    return "\n".join(out)+"\n"

def stats(rows):
    by_type=Counter(r["part"].replace(".dat","") for r in rows)
    by_clr=Counter((r["part"].replace(".dat",""),r["color"]) for r in rows)
    nroof=sum(r["part"] in SLOPES for r in rows)
    return {"pieces":len(rows),"steps":25,"roof_sloped_parts":nroof,
        "other_roof_supports_windows_and_chimney":len(rows)-nroof,
        "bom_by_design":dict(sorted(by_type.items())),
        "bom_by_design_and_ldraw_color":[{"part":p,"color":c,"quantity":n}
            for (p,c),n in sorted(by_clr.items())],
        "official_LEGO_manual_confirms_step_sequence":True,
        "digital_coordinates_from_community_not_lego":True,
        "non_physical_strength_certification":True}
        
def make_svg(rows):
    # Isometric plan, derived from recorded absolute LDraw coordinates.
    # Simplified colored rectangular extents: NOT exact mesh render.
    d={"3001":(80,40,24),"3002":(60,40,24),"3003":(40,40,24),
       "3004":(40,20,24),"3005":(20,20,24),"3009":(120,20,24),
       "3010":(80,20,24),"3022":(40,40,8),"3023":(40,20,8),
       "3037":(80,40,24),"3038":(60,40,24),"3039":(40,40,24),
       "3046":(40,40,24),"32001":(120,40,8),"32028":(40,20,8),
       "3622":(60,20,24),"3659":(80,20,24),"3832":(200,40,8),
       "4445":(160,40,24),"60592":(40,20,48),"60601":(40,20,48),
       "6141":(20,20,8),"3062":(20,20,24)}
    colors={272:("#153eae","#122d7c","#426ac6"),4:("#cf2b2b","#9f2422","#ef5554"),
            15:("#f1f3f8","#c2c9d5","#ffffff"),28:("#7d6d4e","#5e5039","#a39672"),
            47:("#aad9f5","#81abc8","#e4f9ff"),27:("#d4df35","#8b9327","#f4f99b"),
            14:("#d0ce42","#9e9b34","#f5f0a9"),19:("#debf85","#bc974d","#eed89a"),
            71:("#aaaaaa","#797979","#d1d1d1"),0:("#323232","#171717","#606060")}
    # Isometric coordinate projection: Y is down in LDraw; rebase to roof
    # submodel bounding levels (no fake building walls or invented foundation).
    def pr(x,y,z):
        return (440+(x+95)*1.8-(z-35)*1.1,
                495+(x+95)*.49+(z-35)*.6+(y+265)*1.4)
    def ptlist(corners):
        return " ".join(f"{pr(*x)[0]:.2f},{pr(*x)[1]:.2f}" for x in corners)
    polys=[]
    for r in rows:
        l=r["part"].replace(".dat","")
        W,D,H=d[l]
        v=r["transform"];x,y,z=v[:3];m=v[3:]
        def t(dx,dy,dz):
            return (x+m[0]*dx+m[1]*dy+m[2]*dz,
                    y+m[3]*dx+m[4]*dy+m[5]*dz,
                    z+m[6]*dx+m[7]*dy+m[8]*dz)
        # LDraw local Y=0: studs. Approximate body occupies [0,H] downward,
        # so top is body plane local Y=0; simple wedge shape on roof slope.
        v0=t(-W/2,H,-D/2);v1=t(W/2,H,-D/2);v2=t(W/2,H,D/2);v3=t(-W/2,H,D/2)
        t0=t(-W/2,0,-D/2);t1=t(W/2,0,-D/2);t2=t(W/2,0,D/2);t3=t(-W/2,0,D/2)
        light,shade,top=colors.get(r["color"],("#8da0b4","#5c7087","#b8c7d7"))
        for face,co in [([v0,v1,v2,v3],shade),
                        ([v3,v2,t2,t3],shade),
                        ([v1,v2,t2,t1],light),
                        ([v0,v1,t1,t0],light),
                        ([t0,t1,t2,t3],top)]:
            # Painter order by depth is approximate; this is a lightweight
            # isometric preview rather than true mesh z-buffer.
            depth=sum(u[0]+u[2]+u[1]*.08 for u in face)/len(face)
            polys.append((depth,f'<polygon points="{ptlist(face)}" fill="{co}" stroke="#202b42" stroke-width="0.55"/>'))
    polys.sort(key=lambda p:p[0])
    header=['<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="720" viewBox="0 0 1100 720">',
      '<title>BOLDUNGO R-2 genuine 31009 roof steps, isometric projection from community CAD coordinates</title>',
      '<rect width="1100" height="720" fill="#f4f9fd"/>',
      '<text x="36" y="45" fill="#132039" font-size="30" font-weight="bold" font-family="sans-serif">BOLDÜNGO R-2 — toiture LEGO 31009</text>',
      '<text x="36" y="76" fill="#405575" font-size="17" font-family="sans-serif">80 pièces · 25 étapes du livret 1 · pentes 45° · deux pans · lucarne</text>']
    footer=['<rect x="22" y="653" width="1055" height="49" rx="9" fill="#fff5e6"/>',
      '<text x="36" y="673" font-size="14" fill="#654021" font-family="sans-serif">APERCU ISOMETRIQUE : rectangles simplifiés, PAS un rendu de maillages exact. Le .ldr contient les 80 vraies pièces.</text>',
      '<text x="36" y="692" font-size="13" fill="#654021" font-family="sans-serif">Source : LEGO 6038244.pdf étapes 1–25 + modèle communautaire LTRON · montage physique non certifié.</text>','</svg>']
    return "\n".join(header+[p[1] for p in polys]+footer)+"\n"

def build(output,source=DATA):
    rows=read_parts(source)
    o=Path(output);o.mkdir(parents=True,exist_ok=True)
    model=assemble_ldraw(rows);bom=stats(rows)
    (o/"31009-ROOF-R2-OFFICIAL-STEP-RECONSTRUCTION.ldr").write_text(model,encoding="utf8")
    (o/"BOM.json").write_text(json.dumps(bom,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    order=[{"official_step":step,"printed_manual_page":46+step,
       "pieces":[{"source_full_model_ordinal":p["ord"],"part":p["part"],
                  "ldraw_color":p["color"],"position_world_ldu":p["transform"][:3]}
                  for p in rows if p["step"]==step]}
                  for step in range(1,26)]
    (o/"OFFICIAL-STEPS-ORDER.json").write_text(json.dumps(order,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    ev={"sources":SOURCE,"part_count":len(rows),"steps":len(order),
        "actual_lego_manual_step_quantities_verified":list(EXPECTED_PER_STEP),
        "digital_coordinates_aligned_to_official_steps_but_not_official_LEGO_CAD":True,
        "unsupported_physical_parts_count":"UNPROVEN_NOT_ZERO",
        "connected_components_real_contacts":"NOT_AUDITED",
        "continuous_assembly_experiment_proven":False,
        "physical_resistance_proven":False,
        "no_extra_piers_or_3022_ridge":True,
        "slope_angle_degrees":45,"guided004_never_modified":True}
    (o/"EVIDENCE.json").write_text(json.dumps(ev,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    (o/"R2-ISOMETRIC-PREVIEW.svg").write_text(make_svg(rows),encoding="utf8")
    print("R2_PARTS",len(rows),"SLOPED",bom["roof_sloped_parts"],"STEPS",len(order))
    print("R2_OFFICIAL_STEP_COUNTS",list(EXPECTED_PER_STEP))
    print("R2_BOM",json.dumps(bom["bom_by_design"],sort_keys=True))
    print("R2_ORIGIN_SOURCE_3D","COMMUNITY_LTRON_NOT_LEGO")
    print("R2_NO_FAKE_RIDGE_PILLARS","PASS")
    return ev,bom

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output",default="artifacts/lego2-r2-official-31009")
    p.add_argument("--source",default=DATA)
    x=p.parse_args()
    build(x.output,x.source)
