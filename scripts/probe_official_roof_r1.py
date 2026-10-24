"""R-1 bounded *existing* mesh-engine audit for LEGO 31009-inspired 4445 roof.

Official 31009 book 1 is evidence of LEGO's original assembly steps,
NOT a substitute for full mechanical proof of this adapted geometry.
All uncertain or collision relations are preserved; no auto-reclassification.
"""
from __future__ import annotations
from collections import Counter
import argparse, json
from pathlib import Path

from lego_geometry_engine import (LDrawLibrary, Relation, instantiate,
                                  transform_from_ldraw, check_collision)
from experiment_official_roof_r1 import recipe, ldraw, parent_candidates, audit_nominal

def positions(parts,lib):
    parsed={}
    current=None
    known={p.pid for p in parts}
    for line in ldraw(parts).splitlines():
        if line.startswith("0 // ") and len(line.split())>=3:
            candidate=line.split()[2]
            current=candidate if candidate in known else None
        if line.startswith("1 ") and current is not None:
            tok=line.split()
            if len(tok)!=15:raise ValueError("BAD_OFFICIAL_LDRAW_TYPE1")
            if current=="foundation-3811":
                current=None
                continue
            part=lib.load_part(tok[-1])
            parsed[current]=instantiate(part,current,
                transform_from_ldraw([float(x) for x in tok[2:14]]))
            current=None
    if set(parsed)!=(known-{"foundation-3811"}):
        raise AssertionError("SOME_REAL_PARTS_NOT_INSTANTIATED")
    return parsed

def actual_4445_primitive_alignment(root,parts,inst):
    """Check real stud4a centres vs actual 3007 studs, not invented anti-studs."""
    data=(Path(root)/"parts/4445.dat").read_text()
    refs=[]
    for line in data.splitlines():
        t=line.split()
        if t and t[0]=="1" and t[-1].lower()=="stud4a.dat":
            refs.append([float(x) for x in t[2:14]])
    if len(refs)!=7:
        raise AssertionError("R1_EXPECTED_SEVEN_4445_OPEN_TUBES")
    parents=parent_candidates(parts)[0]
    result=[]
    for slope in (p for p in parts if p.role=="slope"):
        beam=next(p for p in parts if p.pid==parents[slope.pid][0])
        a,b=inst[slope.pid],inst[beam.pid]
        tube_centres=[a.transform.point((t[0],t[1],t[2])) for t in refs]
        # Official 3007.dat 8x2 studs at local X in [-70,70] step 20,
        # and local Z +/-10. Their centres create 7x1 holes at local
        # X in [-60,60], Z=0. Here use full instance matrix from LDraw.
        top_left=[b.transform.point((x,0,-10)) for x in range(-70,71,20)]
        top_right=[b.transform.point((x,0,10)) for x in range(-70,71,20)]
        holes=[((top_left[i][0]+top_left[i+1][0]+top_right[i][0]+top_right[i+1][0])/4,
                (top_left[i][2]+top_left[i+1][2]+top_right[i][2]+top_right[i+1][2])/4)
               for i in range(7)]
        # Right-facing 4445 rotates 180 degrees in plan, so tube indices
        # reverse. Comparison is a SET with tolerance.
        grid_set={(round(x,5),round(z,5)) for x,z in holes}
        tube_set={(round(x,5),round(z,5)) for x,y,z in tube_centres}
        # local stud4a reference centre Y20; its mouth at local y=-4
        # after vertical inversion is Y24 relative to the 4445's origin.
        tip=b.transform.point((0,-4,0))[1]
        mouth=a.transform.point((0,24,-10))[1]
        depth=mouth-tip
        matches=(grid_set==tube_set and abs(depth-4)<.03)
        result.append({"child":slope.pid,"parent":beam.pid,
                       "official_4445_tubes":7,"official_3007_stud_group_holes":7,
                       "all_seven_tube_centres_align_with_3007":grid_set==tube_set,
                       "stud_depth_ldu":round(depth,6),
                       "geometry_alignment_proved":matches,
                       "full_interference_free_insertion_proved":False})
    return result

def run(ldraw_root,output):
    parts=recipe()
    lib=LDrawLibrary(ldraw_root)
    inst=positions(parts,lib)
    ids={p.pid:p for p in parts}
    parents,unsupported,edges=parent_candidates(parts)
    checks=[]
    for p in parts:
        if p.role not in ("slope","ridge"):continue
        for parent in parents[p.pid]:
            ia,ib=inst[p.pid],inst[parent]
            relation=(Relation.SEPARATED if ia.bbox.relation(ib.bbox) is Relation.SEPARATED
                      else check_collision(ia,ib))
            checks.append({"child":p.pid,"parent":parent,
                "child_ldraw":p.ldraw,"parent_ldraw":ids[parent].ldraw,
                "official_real_mesh_relation":relation.value,
                "full_stud_insertion_proven":False,
                "third_party_official_manual_proves_our_variant":False})
    # Verify only the two distinct joins of adjacent 45-degree 4445
    # courses, one on each side; full all-pairs audit is NOT claimed.
    near=[]
    for side in ("left","right"):
        group=sorted((p for p in parts if p.role=="slope" and p.side==side),
                     key=lambda p:p.course)
        if len(group)!=2:raise AssertionError("R1_EXPECT_TWO_COURSES")
        ia,ib=inst[group[0].pid],inst[group[1].pid]
        relation=check_collision(ia,ib) if ia.bbox.relation(ib.bbox) is not Relation.SEPARATED else Relation.SEPARATED
        near.append({"pair":[group[0].pid,group[1].pid],"relation":relation.value})
    align=actual_4445_primitive_alignment(ldraw_root,parts,inst)
    collisions=[d for d in checks+near if d.get("official_real_mesh_relation",d.get("relation"))=="COLLISION"]
    summary={"total_parts":len(parts),"roof_parts":8,
        "nominal_support_edges":edges,"nominal_unsupported":len(unsupported),
        "nominal_components":1 if not unsupported else None,
        "roof_supporting_mesh_pairs_checked":len(checks),
        "adjacent_course_mesh_pairs_checked":len(near),
        "real_4445_to_3007_primitive_mates_aligned":sum(x["geometry_alignment_proved"] for x in align),
        "mesh_collisions_detected_in_checked_pairs":len(collisions),
        "all_model_mesh_pairs_checked":False,
        "roof_assembly_order_in_official_manual":True,
        "our_variant_is_official_lego_build":False,
        "full_insertion_proven":False,
        "physical_strength_proven":False,
        "scope":"roof mate pairs and two adjacent-course pairs only; no exhaustive mesh sweep"}
    result={"summary":summary,"stud_alignment":align,"mesh_mates":checks,
            "adjacent_courses":near,"collisions":collisions}
    output=Path(output)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    for x in align:print("R1_PRIMITIVE_4445_TO_3007",x["child"],
        "centres",x["all_seven_tube_centres_align_with_3007"],
        "depth_ldu",x["stud_depth_ldu"])
    for x in checks:print("R1_MESH_MATE",x["child"],x["parent"],
                          x["official_real_mesh_relation"])
    for x in near:print("R1_ADJACENT_COURSES",x["pair"],x["relation"])
    print("R1_GEOMETRY_SUMMARY",json.dumps(summary,sort_keys=True))
    return result

if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--ldraw-root",required=True,type=Path)
    a.add_argument("--output",required=True,type=Path)
    args=a.parse_args()
    run(args.ldraw_root,args.output)
