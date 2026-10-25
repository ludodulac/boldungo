"""R-3 bounded official LDraw mesh verification, not a new geometry engine.

Checks one representative of *each* distinct transformed parent/child pair
in each generated roof, and a handful of adjacent roof pair interfaces.
Repeated classes are counted as nominal repetitions, not exhaustively probed.
An observed COLLISION is kept as a collision; no silent stud exemption.
"""
from __future__ import annotations
from pathlib import Path
from collections import defaultdict
import argparse,json

from lego_geometry_engine import (
    LDrawLibrary, instantiate, transform_from_ldraw, Relation, check_collision)
from generate_roof_recipe_r3 import recipe,ldraw,nominal_audit,_coord

def located(parts,lib,length):
    current=None
    index={p.id for p in parts}
    result={}
    for line in ldraw(parts,length).splitlines():
        if line.startswith("0 // "):
            s=line.split()
            current=s[2] if len(s)>2 and s[2] in index else None
        elif line.startswith("1 ") and current is not None:
            tok=line.split()
            if len(tok)!=15:raise AssertionError("R3_INVALID_TYPE1")
            result[current]=instantiate(lib.load_part(tok[-1]),current,
                       transform_from_ldraw([float(x) for x in tok[2:14]]))
            current=None
    if len(result)!=len(parts):raise AssertionError("R3_REAL_LDRAW_PART_MISSING")
    return result

def key(p,q,length):
    px,py,pz=_coord(p,length)
    qx,qy,qz=_coord(q,length)
    return (p.part,q.part,p.matrix,q.matrix,
            round(px-qx,4),round(py-qy,4),round(pz-qz,4))

def audit(root,length=8):
    parts=recipe(length_studs=length)
    byid={p.id:p for p in parts}
    instances=located(parts,LDrawLibrary(root),length)
    kinds=defaultdict(list)
    for p in parts:
        for pid in p.parents:
            q=byid[pid]
            kinds[key(p,q,length)].append((p.id,q.id))
    analyzed=[]
    for tup,pairs in kinds.items():
        a,b=pairs[0]
        ia,ib=instances[a],instances[b]
        rel=Relation.SEPARATED if ia.bbox.relation(ib.bbox) is Relation.SEPARATED else check_collision(ia,ib)
        analyzed.append({"child":a,"parent":b,"child_ref":tup[0],
                         "parent_ref":tup[1],"mesh_relation":rel.value,
                         "nominal_repetitions":len(pairs),
                         "all_repetitions_mesh_verified":len(pairs)==1,
                         "positive_stud_tube_engagement_demonstrated":False})
        print("R3_REAL_MESH_MATE",a,b,rel.value,"REPEATS",len(pairs))
    # Non-support interfacial checks: one per new class (course adjacency,
    # opposite innermost slope near the ridge, sibling roof segments).
    specials={}
    for p in parts:
        if p.role!="slope":continue
        for q in parts:
            if q.id<=p.id or q.role!="slope":continue
            if abs(p.y-q.y)>8:continue
            if p.x==q.x and p.y==q.y:continue
            typ="opposing" if p.y==q.y and p.z==q.z and p.x!=q.x else (
                "successive_course" if p.y==q.y and p.x!=q.x else "adjacent_bays")
            if typ=="adjacent_bays" and p.y!=0:continue
            marker=(typ,p.part,q.part,abs(p.z-q.z),abs(p.x-q.x),abs(p.y-q.y))
            if marker in specials:continue
            ia,ib=instances[p.id],instances[q.id]
            if ia.bbox.relation(ib.bbox) is Relation.SEPARATED:
                rel=Relation.SEPARATED
            else:
                rel=check_collision(ia,ib)
            specials[marker]={"pair":[p.id,q.id],"class":typ,
                               "relation":rel.value}
            print("R3_NEIGHBOR_MESH",typ,p.id,q.id,rel.value)
    bad=[x for x in analyzed if x["mesh_relation"]=="COLLISION"]
    bad.extend(x for x in specials.values() if x["relation"]=="COLLISION")
    nominal=nominal_audit(parts)
    summary={"total_parts":len(parts),"roof_parts":nominal["roof_parts"],
        "nominal_components":nominal["nominal_components"],
        "nominal_parent_edges":nominal["nominal_parent_edges"],
        "nominal_without_bearing":len(nominal["no_nominal_bearing"]),
        "distinct_parent_mate_transform_classes":len(analyzed),
        "parent_mate_repetitions_nominal":sum(x["nominal_repetitions"] for x in analyzed),
        "parent_mate_classes_contact":sum(x["mesh_relation"]=="CONTACT" for x in analyzed),
        "positive_stud_tube_connections_proven":0,
        "positive_stud_tube_connections_unproven":nominal["nominal_parent_edges"],
        "pieces_without_fully_demonstrated_support_to_foundations":len(parts),
        "components_connected_by_verified_clutch_only":"NOT_ESTABLISHED",
        "forbidden_collision_signals_in_checked_pairs":len(bad),
        "collision_free_full_model":"NOT_ESTABLISHED",
        "all_repeated_instances_checked":False,
        "full_insertion_proven":False,
        "physical_strength_proven":False}
    result={"summary":summary,"parent_mesh_classes":analyzed,
            "roof_neighbor_checks":list(specials.values()),
            "observed_collision_signals":bad,
            "notes":"Actual mesh via existing engine for representative transforms; CONTACT does not prove clutch. Full 3D sweep never run."}
    print("R3_GEOMETRY_SUMMARY",json.dumps(summary,sort_keys=True))
    return result

if __name__=="__main__":
    c=argparse.ArgumentParser()
    c.add_argument("--ldraw-root",type=Path,required=True)
    c.add_argument("--length-studs",type=int,required=True)
    c.add_argument("--output",type=Path,required=True)
    args=c.parse_args()
    report=audit(args.ldraw_root,args.length_studs)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+"\n")
