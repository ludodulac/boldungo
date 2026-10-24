"""Bounded official LDraw mesh spot-check of existing Mission A assemblies.

Uses the existing lego_geometry_engine and the already version-pinned LDraw
closure downloader. A mesh COLLISION at a stud/tube interface is NOT
automatically an invalid LEGO clutch; this is a diagnostic, not approval.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from lego_geometry_engine import (LDrawLibrary, instantiate,
    transform_from_ldraw, check_collision, Relation)
from experiment_stacked_roofs_a import construct, _ldraw


def _instantiate_samples(parts, width, length, library):
    lines = _ldraw(parts,width,length,"official-mesh-probe").splitlines()
    placed = {}
    pending = None
    for line in lines:
        if line.startswith("0 // ") and line.count(" ") >= 3:
            pending = line.split()[2]
        if line.startswith("1 ") and pending is not None:
            tokens = line.split()
            assert tokens[-1].endswith(".dat") and len(tokens) == 15
            placed[pending] = (tokens[-1][:-4],list(map(float,tokens[2:14])))
            pending = None
    return placed


def audit_one_case(ldraw_root, width, length, pitch, wall_courses):
    parts,meta=construct(width,length,pitch,0,wall_courses)
    library=LDrawLibrary(ldraw_root)
    placed=_instantiate_samples(parts,width,length,library)
    def pfind(**kwargs):
        return next(p for p in parts if all(getattr(p,k)==v for k,v in kwargs.items()))
    left0=pfind(role="slope",side="left",step=0,y=2)
    left1=pfind(role="slope",side="left",step=1,y=2)
    last=meta["roof_courses_each_side"]-1
    leftlast=pfind(role="slope",side="left",step=last,y=2)
    rightlast=pfind(role="slope",side="right",step=last,y=2)
    cap=pfind(role="ridge",y=2)
    beam=next(p for p in parts if p.role=="beam"
              and p.x==left0.x+1 and p.y<=2<p.y+p.sy
              and p.z+p.height==left0.z)
    gable=pfind(role="gablewall",z=meta["wall_courses"]*3,y=0,
                x=4)
    front=pfind(role="slope",side="left",step=0,y=0)
    checks=[("slope_to_beam",left0,beam),
        ("one_course_to_next",left0,left1),
        ("opposing_ridge_slopes",leftlast,rightlast),
        ("left_slope_to_ridge_plate",leftlast,cap),
        ("right_slope_to_ridge_plate",rightlast,cap),
        ("front_eave_against_gable",front,gable)]
    cache={}
    def instance(p):
        if p.pid not in cache:
            dat,transform=placed[p.pid]
            cache[p.pid]=instantiate(library.load_part(dat),p.pid,
                 transform_from_ldraw(transform))
        return cache[p.pid]
    rows=[]
    for relationship, a,b in checks:
        ia,ib=instance(a),instance(b)
        bbox_valid={}
        for p, inst in ((a,ia),(b,ib)):
            expected=(20*(p.y-length/2),20*(p.y+p.sy-length/2),
                      20*(p.x-width/2),20*(p.x+p.sx-width/2))
            actual=(inst.bbox.minimum[0],inst.bbox.maximum[0],
                    inst.bbox.minimum[2],inst.bbox.maximum[2])
            bbox_valid[p.pid]=all(abs(x-y)<0.00001
                                   for x,y in zip(expected,actual))
        relation=check_collision(ia,ib)
        rows.append({"type":relationship,"part_a":a.pid,"part_b":b.pid,
             "part_a_ldraw":a.ldraw,"part_b_ldraw":b.ldraw,
             "mesh_relation":relation.value,
             "aabb_footprint_exact":bbox_valid,
             "full_mesh_computed":True,
             "stud_interference_excluded_from_collision":False,
             "insertion_path_tested":False})
    return {"case":f"{width}x{length}","official_ldraw_mirror_pin":
       "c43ed06a128a10ed65675166bf42eb6fd608b9b0",
       "pairs":rows,
       "pair_count":len(rows),
       "all_selected_mesh_pairs_loaded":all(r["full_mesh_computed"] for r in rows),
       "all_sample_footprints_verified":
          all(all(r["aabb_footprint_exact"].values()) for r in rows),
       "all_house_pairs_checked":False,"physical_certification":"NOT_CERTIFIED"}


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--ldraw-root",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    result=audit_one_case(args.ldraw_root,20,20,22,3)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+"\n")
    for r in result["pairs"]:
        print("MISSION_A_MESH_PAIR",r["type"],r["mesh_relation"],
              "FOOTPRINT",all(r["aabb_footprint_exact"].values()))
    print("MISSION_A_MESH_SAMPLED",result["pair_count"],
          "ALL_FOOTPRINTS",result["all_sample_footprints_verified"],
          "N6",result["physical_certification"])
    if not result["all_sample_footprints_verified"]:
        raise SystemExit("WRONG_ACTUAL_LDRAW_FOOTPRINTS")
