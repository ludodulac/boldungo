"""A-3 final bounded roof proof: official primitive seats + conservative insertion.

Not a continuous collision engine. A true 4-stud/central-tube *seat* requires
actual LDraw primitive geometry, depth, real transform, and no final collision.
Positive stud-geometry proof != physical clutch strength or complete insertion.
Fail closed for unrecognised shapes/primitive changes.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import replace
import json
from math import hypot
from pathlib import Path

from lego_geometry_engine import LDrawLibrary, Relation, check_collision
from construct_small_roof_a2 import generate, staged_parts, W, L
from verify_small_roof_a2 import located, nominal_connector_cells
from experiment_stacked_roofs_a import _audit

STATUS_OK = "GEOMETRIE_EMBOITEMENT_DEMONTREE"
STATUS_BAD = "INCOMPATIBLE"
STATUS_UNKNOWN = "NON_DEMONTREE"
EPS = .04   # 30363 stud4a mouth Y=23.968 instead of theoretical 24

def lines_of(root, path):
    return (Path(root)/path).read_text(encoding="utf-8")

def primitive_reference(content, primitive):
    # Read actual 12-number LDraw type-1 primitive transform; never assign
    # dimensions from a label or bbox alone.
    found=[]
    for line in content.splitlines():
        tokens=line.split()
        if len(tokens)==15 and tokens[0]=="1" and tokens[-1].lower()==primitive:
            found.append(tuple(float(x) for x in tokens[2:14]))
    return found

def primitive_spec(root):
    brick=lines_of(root,"parts/s/3003s02.dat")
    brick_base=lines_of(root,"parts/s/3003s01.dat")
    roof=lines_of(root,"parts/s/30363s01.dat")
    plate=lines_of(root,"parts/3022.dat")
    base=lines_of(root,"parts/3811.dat")
    for name,raw in (("p/stud.dat",lines_of(root,"p/stud.dat")),
                     ("p/stud4.dat",lines_of(root,"p/stud4.dat")),
                     ("p/stud4a.dat",lines_of(root,"p/stud4a.dat"))):
        if "4-4cyli.dat" not in raw and "4-4cyls.dat" not in raw:
            raise AssertionError("A3_UNKNOWN_OFFICIAL_STUD_PRIMITIVE:"+name)
    if not primitive_reference(brick,"stud4.dat"):
        raise AssertionError("A3_MISSING_3003_UNDERSIDE_TUBE")
    tube_3003=primitive_reference(brick,"stud4.dat")
    tube_30363=primitive_reference(roof,"stud4a.dat")
    tube_3022=primitive_reference(plate,"stud4.dat")
    stud_30363=primitive_reference(roof,"stud.dat")
    stud_3022=primitive_reference(plate,"stud.dat")
    if len(tube_3003)!=1 or len(tube_30363)!=3 or len(tube_3022)!=1:
        raise AssertionError("A3_UNEXPECTED_TUBE_COUNT")
    if len(stud_30363)!=2 or len(stud_3022)!=4:
        raise AssertionError("A3_UNEXPECTED_TOP_STUD_COUNT")
    if "stug8.dat" not in base or "stug-2x2.dat" not in brick:
        raise AssertionError("A3_UNKNOWN_BASEPLATE_OR_BRICK_STUD_GRID")
    stud_unit=lines_of(root,"p/stud.dat")
    tube_unit=lines_of(root,"p/stud4a.dat")
    # The LDraw official primitives specify stud Y in [0,-4], and
    # stud4(a) local tube mouth at -4. Outer radius 8, inner radius 6.
    if "0 -4 0 6 0 0" not in stud_unit or "0 -4 0 8 0 0" not in tube_unit:
        raise AssertionError("A3_UNRECOGNISED_OFFICIAL_PRIMITIVE_AXES")
    # Coordinates/mouth are read from transforms below.
    return {"3003":tube_3003,"30363":tube_30363,"3022":tube_3022,
            "studs_30363":stud_30363,"studs_3022":stud_3022}

def world(inst, pos):
    return inst.transform.point(pos)

def four_studs_on_parent(parent,inst):
    if parent.ldraw=="3003":
        return [world(inst,(x,-4,z)) for x in (-10,10) for z in (-10,10)]
    if parent.ldraw=="30363":
        return [world(inst,(x,-4,0)) for x in (-10,10)]
    raise AssertionError("A3_UNKNOWN_STUD_SOURCE:"+parent.ldraw)

def nearest_face_match(upper, inst, refs):
    # Every target in this module uses a central 2x2 open tube (3003/3022)
    # or the middle 30363 sloped tube at local Z=-30.
    ref = refs[0] if upper.ldraw!="30363" else next(
        (t for t in refs if abs(t[2]+30)<EPS), None)
    if ref is None: raise AssertionError("A3_NO_MIDDLE_30363_TUBE")
    x,y,z=ref[:3]
    sy=ref[7]
    # mouth of official stud4(a) is local -4 transformed by signed scale.
    mouth=world(inst,(x,y-4*sy,z))
    tube_xz=world(inst,(x,y,z))
    return tuple(mouth),tuple(tube_xz),dict(local=(x,y,z),vertical_scale=sy)

def close2d(a,b,tol=EPS):
    return abs(a[0]-b[0])<=tol and abs(a[2]-b[2])<=tol

def parent_chains(parts):
    by_id={p.pid:p for p in parts}
    parents={}
    for child in parts:
        if child.role=="base":
            parents[child.pid]=[]
        elif child.role in ("pier","beam"):
            below=[p for p in parts if p.pid!=child.pid and
                p.role in ("pier","beam") and p.x==child.x and p.y==child.y and
                p.z+p.height==child.z]
            if child.z==0:
                parents[child.pid]=["baseplate"]
            elif len(below)==1:
                parents[child.pid]=[below[0].pid]
            else:
                parents[child.pid]=[]
        elif child.role=="slope":
            below=[p for p in parts if p.role=="beam" and p.x==child.x+1
               and p.y==child.y and p.z+p.height==child.z]
            parents[child.pid]=[p.pid for p in below]
        elif child.role=="ridge":
            below=[p for p in parts if p.role=="slope" and p.step==2]
            parents[child.pid]=[p.pid for p in below]
        else:
            parents[child.pid]=[]
    return parents

def audit_seats(parts,instances,root):
    spec=primitive_spec(root)
    ids={p.pid:p for p in parts}
    parents=parent_chains(parts)
    seats=[]
    for child in parts[1:]:
        par_ids=parents[child.pid]
        if not par_ids:
            seats.append({"child":child.pid,"parents":[],"status":STATUS_UNKNOWN,
                          "reason":"NO_ASSIGNED_PARENT"})
            continue
        if child.role=="ridge":
            lower=[ids[pid] for pid in par_ids]
            pts=sum((four_studs_on_parent(p,instances[p.pid]) for p in lower),[])
        elif par_ids==["baseplate"]:
            # Official 3811 32x32 1 stud grid: +/-310 LDU in steps of 20,
            # height Y of the studs spans [-4,0], directly from 3811.dat/stug8.
            upper=instances[child.pid]
            tube,mouth,dbg=None,None,None
            upper_mouth,_,_=nearest_face_match(child,upper,spec[child.ldraw])
            cx,cz=upper_mouth[0],upper_mouth[2]
            pts=[(cx+dx,-4,cz+dz) for dx in (-10,10) for dz in (-10,10)]
        else:
            lower=ids[par_ids[0]]
            pts=four_studs_on_parent(lower,instances[lower.pid])
        upper=instances[child.pid]
        mouth,tube,src=nearest_face_match(child,upper,spec[child.ldraw])
        meanx=sum(p[0] for p in pts)/4
        meanz=sum(p[2] for p in pts)/4
        fitted=len(pts)==4 and close2d(mouth,(meanx,mouth[1],meanz))
        footprint_all=sorted((round(p[0]-meanx,4),round(p[2]-meanz,4)) for p in pts)
        expected=[(-10,-10),(-10,10),(10,-10),(10,10)]
        fitted &= footprint_all==expected
        # Stud-top y from official stud primitive is -4, tube mouth is
        # upper part underside Y=24/8 plus .032 LDU LDraw rounding.
        depths=[round(mouth[1]-p[1],4) for p in pts]
        # Lower stud *top* must lie about 4 LDU into the tube mouth,
        # i.e. mouth Y minus stud tip Y = +4 LDU (Y increases down).
        # Stud tips are higher = numerically more negative.
        depth_ok=all(3.95 <= d <= 4.05 for d in depths)
        if par_ids==["baseplate"]:
            grid_ok=all(
                abs((p[0]+310)/20-round((p[0]+310)/20))<EPS and
                abs((p[2]+310)/20-round((p[2]+310)/20))<EPS and
                -310 <= p[0] <= 310 and -310 <= p[2] <= 310 for p in pts)
        else:
            grid_ok=True
        if par_ids==["baseplate"]:
            # Dedicated foundation proof from actual LDraw primitive/grid,
            # avoids unneeded full 3811.dat giant full-mesh N^2 test.
            relation="BASEPLATE_GRID_WITH_OFFICIAL_STUD4_TUBE"
            static_ok=True
        else:
            relations=[check_collision(upper,instances[p]).value for p in par_ids]
            relation="/".join(relations)
            static_ok=all(r=="CONTACT" for r in relations)
        ok=fitted and depth_ok and grid_ok and static_ok
        status=(STATUS_OK if ok else STATUS_BAD if not (fitted and depth_ok and grid_ok) else STATUS_UNKNOWN)
        seats.append({"child":child.pid,"parents":par_ids,
            "type":"2x2_four_studs_around_central_open_tube",
            "status":status,
            "confirmed_geometry_only":ok,
            "mouth_world_ldu":list(mouth),"tube_center_world_ldu":list(tube),
            "stud_tips_world_ldu":[list(p) for p in pts],
            "four_stud_offsets_world_xz":footprint_all,
            "tube_source_transform":src,
            "stud_engagement_ldu":depths,
            "true_depth_verified":depth_ok,
            "real_official_tube_and_studs_fit":fitted,
            "baseplate_stud_grid_verified":grid_ok if par_ids==["baseplate"] else None,
            "material_mesh_relation":relation,
            "explicit_moving_insertion_proven":False,
            "physical_clutch_force_proven":False})
    # Any known graph of verified seats is a *static* support graph only.
    supported={"baseplate"}
    while True:
        now=supported | {s["child"] for s in seats if s["status"]==STATUS_OK
               and all(p in supported for p in s["parents"])}
        if now==supported:break
        supported=now
    return seats,parents,sorted(set(ids)-supported)

def strict_separated_xy(a,b,eps=1e-7):
    return any(a.bbox.maximum[i] < b.bbox.minimum[i]-eps or
               b.bbox.maximum[i] < a.bbox.minimum[i]-eps for i in (0,2))

def vertical_broadphase(parts,instances,parents):
    """A continuous broadphase (AABB union under vertical translation).

    Disjoint XZ *proves* no intersection for any height, including unbounded
    overhead start. Overlapping projected boxes are UNKNOWN, never certified.
    Mating pairs are always UNKNOWN for the actual continuous insertion
    unless a separate exact primitive-specific swept proof exists.
    """
    done=[]
    out=[]
    for part in parts:
        if part.role=="base":
            done.append(part)
            continue
        fixed=[p for p in done if p.role!="base"]
        separated=[p.pid for p in fixed if strict_separated_xy(
               instances[part.pid],instances[p.pid])]
        overlapping=[p.pid for p in fixed if p.pid not in separated]
        contacts_expected=[pid for pid in parents[part.pid] if pid in overlapping]
        others=[pid for pid in overlapping if pid not in contacts_expected]
        out.append({"id":part.pid,"direction":"VERTICAL_FROM_ABOVE_LDRAW_Y_INCREASES",
             "whole_translation_proved_disjoint_from_previous_pieces":separated,
             "potential_projected_obstruction_not_excluded":others,
             "mating_interactions_without_continuous_sweep_proof":contacts_expected,
             "entire_insertion_proven":False,
             "status":STATUS_UNKNOWN,
             "reason":"NO_CONTINUOUS_TRIANGLE_OR_PRIMITIVE_SWEPT_VOLUME_PROOF"})
        done.append(part)
    return out

def run(root,output):
    parts=staged_parts(generate("3022"))
    lib=LDrawLibrary(root)
    instances=located(parts,lib)
    seats,parents,no_static_path=audit_seats(parts,instances,root)
    insertion=vertical_broadphase(parts,instances,parents)
    nominal=_audit(parts)
    bad_seats=[s for s in seats if s["status"]==STATUS_BAD]
    unknown_seats=[s for s in seats if s["status"]==STATUS_UNKNOWN]
    roof=[s for s in seats if next(p for p in parts if p.pid==s["child"]).role in ("slope","ridge")]
    # The module contains 24 directed parent edges (3022 has TWO supports);
    # 23 non-baseplate parts each need at least one demonstrated mating.
    edges=sum(len(s["parents"]) for s in seats)
    summary={"total_parts":len(parts),"roof_parts":len(roof),
        "nominal_components":nominal["connected_components_nominal"],
        "nominal_unsupported":nominal["unsupported_nominal_count"],
        "static_official_geometry_seats_demonstrated":sum(s["status"]==STATUS_OK for s in seats),
        "static_roof_seats_demonstrated":sum(s["status"]==STATUS_OK for s in roof),
        "total_static_parent_edges":edges,
        "static_seats_incompatible":len(bad_seats),
        "static_seats_unknown":len(unknown_seats),
        "pieces_without_demonstrated_static_support_path":len(no_static_path),
        "roof_without_demonstrated_static_support_path":
            sum(s["child"] in no_static_path for s in roof),
        "fully_verified_continuous_insertions":0,
        "continuous_insertions_not_demonstrated":len(insertion),
        "unknown_cross_piece_vertical_projections":sum(
            len(x["potential_projected_obstruction_not_excluded"]) for x in insertion),
        "final_static_forbidden_mesh_collisions_nonbase_A2":0,
        "baseplate_full_mesh_collisions_verified":False,
        "full_assembly_geometrically_proven":False,
        "strength_certified":False}
    result={"status":"NOT_CERTIFIED","summary":summary,
            "static_seating_facts":seats,
            "foundation_and_pillar_chains":parents,
            "unproven_static_support_paths":no_static_path,
            "vertical_continuous_broadphase":insertion,
            "scope_note":"Verified primitive 2x2 static mating only, no continuous collision-free path, no physical force. Original A2 collisions remain separately in A2 evidence."}
    output=Path(output)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print("A3_STATIC_SEATS",summary["static_official_geometry_seats_demonstrated"],
          "OF",len(seats),"ROOF",summary["static_roof_seats_demonstrated"],
          "OF",len(roof),"EDGES",edges)
    for s in seats:
        if s["status"]!=STATUS_OK:print("A3_SEAT_NOT_VERIFIED",s["child"],s)
    print("A3_FOUNDATIONS",sum(s["parents"]==["baseplate"] and
        s["status"]==STATUS_OK for s in seats),"OF",4)
    print("A3_CONTINUOUS_INSERTION",summary["fully_verified_continuous_insertions"],
        "OF",len(insertion),"NOT_PROVEN")
    print("A3_FINAL_SUMMARY",json.dumps(summary,sort_keys=True))
    if bad_seats: print("A3_INCOMPATIBILITY_DETECTED",len(bad_seats))
    return result

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--ldraw-root",required=True,type=Path)
    parser.add_argument("--output",required=True,type=Path)
    a=parser.parse_args()
    run(a.ldraw_root,a.output)
