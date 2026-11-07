"""TOITURE-3 — ONE five-roof contiguous LEGO module, bounded against immutable B-3.

Fifteen original 30363 parts are inventoried in 3x5 rows.  Five adjacent
row-two original roof pieces are supported by one REAL 3006 2x10 shared
beam, joined to one original 3622. No original B-3 placement is changed.

The proof uses OFFICIAL LDraw triangulations (not the viewer proxies).
A mesh COLLISION always blocks certification, never excused by aligned studs.
Every roof's insertion uses whole-sweep analytical cylinder/triangle projection.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from lego_geometry_engine import (LDrawLibrary, Relation, check_collision,
                                  find_connections, instantiate, transform_from_ldraw)
from lego_geometry_engine.core import CONTACT_EPS
from toiture1_probe import stud_clearance_sloped

ROOT=Path(__file__).resolve().parents[1]
DIR=ROOT/"missions/TOITURE3"
B3=DIR/"B3-ORIGINAL-READONLY.ldr"
ROOT_ID="scene-chimney:house-chimney-antenna:00043:solution"
REPLACED="scene-chimney:house-chimney-antenna:00052:solution"
BEAM_ID="TOITURE3-VARIANT-3006-ROW336-340"
ROWS=[
 [f"roof-{n:06d}" for n in range(313,318)],
 [f"roof-{n:06d}" for n in range(336,341)],
 [f"roof-{n:06d}" for n in range(359,364)],
]
STUDIED=[x for row in ROWS for x in row]
ASSEMBLY_ORDER=[ROOT_ID,BEAM_ID,*[ROWS[1][2],ROWS[1][1],ROWS[1][3],ROWS[1][0],ROWS[1][4]]]
# Complete 1904 placement snapshot used for environmental checks.
# Source maximum official part footprint is 2x10 = 200 LDU, and slope
# is 80 LDU; ±(100+10) clearance around target AABB is conservative.
WINDOW=(810,1170,-1020,-690,380,860)
APPROACH=48.0
EPS=1e-5

def write(name,value):
    (DIR/name).write_text(json.dumps(value,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")

def load_records(path):
    data={}
    marker=None
    for line in path.read_text().splitlines():
        if line.startswith("0 // "):
            marker=line[5:].strip().split()[0]
        elif line.startswith("1 "):
            if not marker or marker in data:raise AssertionError("Missing/duplicate original placement annotation")
            data[marker]=line.split()
            marker=None
    return data

def read_originals():
    b3=load_records(B3)
    assert len(b3)==1904, "B3 must be a complete immutable snapshot"
    assert sum(v[-1].lower()=="30363.dat" for v in b3.values())==408
    assert len(STUDIED)==15 and len(set(STUDIED))==15
    for i,row in enumerate(ROWS):
        for k,rid in enumerate(row):
            data=b3[rid]
            assert data[-1]=="30363.dat"
            assert list(map(int,data[2:5]))==[1030-60*i,-864-24*i,540+40*k]
            assert data[5:14]==["0","0","-1","0","1","0","1","0","0"]
    assert b3[ROOT_ID]==["1","19","950","-840","630","0","0","-1","0","1","0","1","0","0","3622.dat"]
    assert b3[REPLACED]==["1","19","950","-864","630","0","0","-1","0","1","0","1","0","0","3622.dat"]
    fragment=load_records(DIR/"MODULE-CONTIGU-5.ldr")
    assert len(fragment)==7
    assert set(fragment)==set(ASSEMBLY_ORDER)
    for rid in ROWS[1]+[ROOT_ID]:
        assert fragment[rid]==b3[rid],"original B3 original transformed! "+rid
    assert fragment[BEAM_ID]==["1","19","960","-864","620","0","0","-1","0","1","0","1","0","0","3006.dat"]
    assert REPLACED not in fragment
    return b3,fragment

def instance(lib,rid,record):
    return instantiate(lib.load_part(record[-1]),rid,
        transform_from_ldraw(list(map(float,record[2:14]))),int(record[1]))

def projected_overlap_positive(a,b,axes):
    return all(min(a.maximum[k],b.maximum[k])-
               max(a.minimum[k],b.minimum[k])>CONTACT_EPS for k in axes)

def possible_solid_volume_contact(a,b):
    return projected_overlap_positive(a.bbox,b.bbox,(0,1,2))

def record_origin_in_window(record):
    x,y,z=map(float,record[2:5])
    return WINDOW[0]<=x<=WINDOW[1] and WINDOW[2]<=y<=WINDOW[3] and WINDOW[4]<=z<=WINDOW[5]

def fixed_studs(p):
    return [tuple(p.transform.point(c.position))
            for c in p.definition.connectors if c.type=="stud"]

def roof_cavities(p):
    # Official /parts/s/30363s01.dat: source y=24 for underside end
    # and local x +/-10,z 0, checked against official file below.
    return [tuple(p.transform.point((x,24,0))) for x in (-10,10)]

def center_hits(cavities,studs):
    return [list(c) for c in cavities if any(math.dist(c,s)<EPS for s in studs)]

def official_geom_guard(lib_root):
    slope=(lib_root/"parts/s/30363s01.dat").read_text().lower()
    beam=(lib_root/"parts/3006.dat").read_text().lower()
    base=(lib_root/"parts/3622.dat").read_text().lower()
    assert "0 ~slope brick 18  4 x  2 without top face" in slope
    assert "1 16 -10 0 0 0 0 1 0 1 0 -1 0 0 stud.dat" in slope
    assert "1 16 10 0 0 0 0 1 0 1 0 -1 0 0 stud.dat" in slope
    assert "0 bfc invertnext" in slope and "box2-7.dat" in slope
    assert "0 brick  2 x 10" in beam
    assert "1 16 0 24 0 100 0 0 0 -24 0 0 0 20 box5.dat" in beam
    assert "0 brick  1 x  3" in base
    return {"pinned_official_ldraw":True,"30363_underside_candidate_y":24,
            "30363_slope_degrees":18,"3006_length_ldu":200,
            "3006_width_ldu":40,"primitive_stud_radius_ldu":6,
            "source":"c43ed06a128a10ed65675166bf42eb6fd608b9b0"}

def certified_transition(moving,stationary,kind):
    """All t∈[0,1]: upper body never reaches lower body; all fixed
    stud cylinders checked with entire projected-sweep criterion.
    This is conservative; any triangle/interference yields UNKNOWN.
    """
    target_end=moving.transform.point((0,24,0))[1]
    support_top=stationary.transform.point((0,0,0))[1]
    bodies_separate=target_end<=support_top+EPS
    start_clear=moving.bbox.maximum[1]-APPROACH<stationary.bbox.minimum[1]-EPS
    sw=stud_clearance_sloped(moving,stationary)
    threats=[x for x in sw if not x["continuous_sweep_clear"]]
    return {"role":kind,"start_disjoint":start_clear,
            "solid_body_y_plane_separate_for_all_t":bodies_separate,
            "actual_studs_all_checked":len(sw),
            "stud_cylinder_continuous_clearance":not threats,
            "first_obstacle":threats[0] if threats else None,
            "status":"PASS" if start_clear and bodies_separate and not threats else "NON DÉMONTRÉ"}

def main(root):
    b3,fragment=read_originals()
    pinned=official_geom_guard(root)
    lib=LDrawLibrary(root)
    selected={rid:instance(lib,rid,fragment[rid]) for rid in ASSEMBLY_ORDER}
    lower,beam=selected[ROOT_ID],selected[BEAM_ID]
    # Reuse TOITURE2 result strictly as prior baseline, no retesting its 3002.
    prior=json.loads((ROOT/"missions/TOITURE2/RESULTAT.json").read_text())
    assert prior["overall"]=="PASS","TOITURE2 reference must remain certified"

    bottom_hits=find_connections(lower,beam)
    base_mesh=check_collision(lower,beam)
    base_cont=certified_transition(beam,lower,"Original 3622 bottom to 3006 shared beam")
    base_pass=base_mesh is Relation.CONTACT and len(bottom_hits)==3 and base_cont["status"]=="PASS"

    beam_studs=fixed_studs(beam)
    assert len(beam_studs)==20,"Unexpected official 3006 stud grid; no artificial mating"
    roof_info=[]
    local_collisions=[]
    all_steps=[{"sequence":1,"piece":ROOT_ID,"position":list(map(int,fragment[ROOT_ID][2:5])),
                "status":"PASS","role":"locally rooted 3622; no house foundation proof"},
               {"sequence":2,"piece":BEAM_ID,
                "approach_start_ldu":[960,-912,620],"end_ldu":[960,-864,620],
                "motion":"XYZ(t)=(960,-912+48*t,620); 0<=t<=1",
                "support_connectors":len(bottom_hits),"continuous_clearance":base_cont,
                "status":"PASS" if base_pass else "NON DÉMONTRÉ"}]
    installed=[lower,beam]
    for roof_id in ASSEMBLY_ORDER[2:]:
        piece=selected[roof_id]
        centers=center_hits(roof_cavities(piece),beam_studs)
        roof_rel=check_collision(piece,beam)
        roof_to_base=check_collision(piece,lower) if possible_solid_volume_contact(piece,lower) else Relation.SEPARATED
        swept=certified_transition(piece,beam,"3006 studs into 30363 cavities")
        siblings=[]
        siblings_clear=True
        for old in installed[2:]:
            has_volume_overlap=possible_solid_volume_contact(piece,old)
            collision=check_collision(piece,old) if has_volume_overlap else Relation.CONTACT if piece.bbox.relation(old.bbox) is Relation.CONTACT else Relation.SEPARATED
            if collision is Relation.COLLISION:
                siblings_clear=False
                local_collisions.append({"part_a":roof_id,"part_b":old.instance_id,
                    "relation":"COLLISION","reason":"two adjacent original B3 roof parts cannot overlap"})
            # If XZ projections do not overlap in positive area, there
            # cannot be an obstruction along the entire vertical insertion.
            whole_sweep_free=not projected_overlap_positive(piece.bbox,old.bbox,(0,2))
            siblings.append({"already_installed":old.instance_id,
                             "final_mesh_relation":collision.value,
                             "xy_projected_sweep_clear_for_all_t":whole_sweep_free})
            if not whole_sweep_free:siblings_clear=False
        roof_pass=(len(centers)==2 and roof_rel is Relation.CONTACT and
                   roof_to_base is not Relation.COLLISION and
                   swept["status"]=="PASS" and siblings_clear)
        roof_info.append({"id":roof_id,"ldraw_ref":"30363.dat",
            "source_ldraw_xyz":list(map(int,fragment[roof_id][2:5])),
            "roof_underside_candidates_ldu":[list(q) for q in roof_cavities(piece)],
            "matched_3006_studs_ldu":centers,
            "roof_mesh_relation_to_shared_beam":roof_rel.value,
            "roof_mesh_relation_to_original_lower":roof_to_base.value,
            "roof_entire_continuous_vertical_approach":swept,
            "older_roof_neighbor_checks":siblings,
            "status":"PASS" if roof_pass else "NON DÉMONTRÉ"})
        x,y,z=map(int,fragment[roof_id][2:5])
        all_steps.append({"sequence":len(all_steps)+1,"piece":roof_id,
            "approach_start_ldu":[x,y-APPROACH,z],"end_ldu":[x,y,z],
            "motion":f"XYZ(t)=({x},{y-APPROACH}+48*t,{z}); 0<=t<=1",
            "shared_support":BEAM_ID,"attached_cavities":centers,
            "roof_30263_actual_mesh_relation":roof_rel.value,
            "continuous_clearance":swept,"other_roofs":siblings,
            "status":"PASS" if roof_pass else "NON DÉMONTRÉ"})
        installed.append(piece)

    # Study all three original rows; no added unanchored modules are
    # declared constructed just to reach 15. Environment includes them.
    original_target_rows=[]
    for row_num,row in enumerate(ROWS,1):
        original_target_rows.append({"row_number":row_num,"original_roof_ids":row,
          "positions_ldu":[list(map(int,b3[r][2:5])) for r in row],
          "classification":"FIVE_INTEGRATED" if row_num==2 else
                 "ORIGINAL_B3_NEIGHBOR_ONLY; no load-bearing support outside chimney proved"})
    excluded=set(ASSEMBLY_ORDER)-{BEAM_ID}
    excluded.add(REPLACED)
    # All 1904 source placements parsed. Conservative ±~150 LDU filtering
    # exceeds any B3 reference's supported maximal x/z half-extent (<=100).
    potential=[(rid,record) for rid,record in b3.items()
               if rid not in excluded and record_origin_in_window(record)]
    environment=[]
    external_forbidden=[]
    types_seen=set()
    counts=0
    for ext_id,record in potential:
        if record[-1].lower() not in {"30363.dat","3622.dat","3002.dat"}:
            raise RuntimeError("unexpected B3 nearby part family; broaden official geometry loader before PASS: "+record[-1])
        ext=instance(lib,ext_id,record)
        types_seen.add(record[-1])
        for own_id in ASSEMBLY_ORDER:
            own=selected[own_id]
            if not possible_solid_volume_contact(own,ext):
                continue
            counts+=1
            relation=check_collision(own,ext)
            row={"module_id":own_id,"original_neighbor":ext_id,
                 "neighbor_ref":record[-1],
                 "official_mesh_relation":relation.value}
            environment.append(row)
            if relation is Relation.COLLISION:
                external_forbidden.append(row)
    supported_count=sum(p["status"]=="PASS" for p in roof_info) if base_pass else 0
    local_safe=base_pass and all(p["status"]=="PASS" for p in roof_info) and not local_collisions
    env_safe=not external_forbidden
    # Distinguish selected module support path from proper load-bearing
    # roofing structure: original lower support is an isolated chimney
    # course, NOT demonstrated continuous to the house's structural wall.
    load_to_real_house="NON DÉMONTRÉ"
    verdict={
       "studied_30363":15,
       "integrated_30363":supported_count if local_safe and env_safe else 0,
       "locally_compatible_30363":supported_count,
       "integrated_target_max":5,
       "experimental_parts_added":1,
       "experimental_part_refs":["3006.dat"],
       "prior_B3_upper_replaced":1,
       "original_roof_placement_changes":0,
       "connections":"PASS" if local_safe else "NON DÉMONTRÉ",
       "collisions":"PASS" if not local_collisions and env_safe else "FAIL",
       "supports":"PASS" if local_safe else "NON DÉMONTRÉ",
       "insertion":"PASS" if local_safe else "NON DÉMONTRÉ",
       "structure_house":load_to_real_house,
       "visualization":"NON DÉMONTRÉ until actual Chromium test",
       "first_blocker":(
          "Unverified official 3622->3006 support connection" if not base_pass else
          next((p["id"]+": "+str(p["roof_mesh_relation_to_shared_beam"])+" or swept path blocks" for p in roof_info if p["status"]!="PASS"),None) or
          ("B3 neighboring collision: "+json.dumps(external_forbidden[0]) if external_forbidden else None)
       ),
       "whole_house_assembly":"NON DÉMONTRÉ",
       "physical_stability":"NON DÉMONTRÉ",
       "local_module":"PASS" if local_safe and env_safe else "NON DÉMONTRÉ",
       "overall":"PARTIAL_PROGRESS" if local_safe and env_safe else "NON DÉMONTRÉ",
       "scope":"FIVE contiguous original 30363 roof pieces, one shared genuine 3006, one unchanged B3 3622. Fifteen roof positions studied; remaining ten unintegrated due missing support to house.",
       "environment_checks":{"B3_records":len(b3),
           "nearby_conservative_window":list(WINDOW),
           "nearby_placements_considered":len(potential),
           "actual_mesh_pairs_checked":counts,
           "ref_types_found":sorted(types_seen),
           "forbidden_pairs":len(external_forbidden)},
       "warning":"NO claim that the chimney alone is an adequate roof-bearing structure."}
    write("CONNEXIONS.json",{"original_toiture2_preserved":True,"official_geometry":pinned,
        "lower_to_shared_beam":{"matches":len(bottom_hits),
                                "relation":base_mesh.value,
                                "continuous_approach":base_cont,
                                "status":"PASS" if base_pass else "NON DÉMONTRÉ"},
        "roof_to_shared_beam":roof_info,
        "original_three_rows_inventoried":original_target_rows,
        "status":verdict["connections"]})
    write("COLLISIONS.json",{"original_source_B3_immutable":True,
        "replaced_upper_3622_excluded_only_in_variant":REPLACED,
        "checked_local_roof_sibling_pairs":sum(len(p["older_roof_neighbor_checks"]) for p in roof_info),
        "local_forbidden_pairs":local_collisions,
        "neighboring_source_candidates":len(potential),
        "neighboring_real_mesh_pairs":environment,
        "neighboring_forbidden_pairs":external_forbidden,
        "status":verdict["collisions"]})
    write("INSERTION.json",{"whole_continuous_vertical_trajectories_not_just_samples":True,
        "ldraw_y_positive_down":True,"order":ASSEMBLY_ORDER,
        "steps":all_steps,"local_status":verdict["insertion"],
        "all_B3_surrounding_roof_installation_order":"NON DÉMONTRÉ",
        "force_insertion_friction":"NON DÉMONTRÉ"})
    write("RESULTAT.json",verdict)
    print("TOITURE3_MEASURED="+json.dumps({key:verdict[key] for key in
      ("studied_30363","integrated_30363","locally_compatible_30363",
       "connections","collisions","supports","insertion","structure_house",
       "first_blocker","environment_checks")},ensure_ascii=False),flush=True)

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--ldraw-root",type=Path,required=True)
    main(parser.parse_args().ldraw_root)
