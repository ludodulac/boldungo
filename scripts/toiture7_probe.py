"""TOITURE-7 — two bounded ORIGINAL-wall under-roof route probes.

DO NOT claim any experimental bricks as retained unless every actual
official-LDraw triangle, stud/cavity edge and conservative continuous
insertion proves PASS. The 75-piece TOITURE-6 retained module is
byte-identical and always preserved; previous 1–6 tests are NOT rerun.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from lego_geometry_engine import (LDrawLibrary,Relation,check_collision,
                                  find_connections,instantiate,transform_from_ldraw)
from lego_geometry_engine.core import CONTACT_EPS
from toiture4_probe import parse,instance,vertical_sufficient,swept_box_safe_others,overlap

ROOT=Path(__file__).resolve().parents[1]
DIR=ROOT/"missions/TOITURE7"
B3=ROOT/"missions/TOITURE3/B3-ORIGINAL-READONLY.ldr"
ORIGINAL75=ROOT/"missions/TOITURE6/MODULE-RETENU-75.ldr"
PREVIOUS75=DIR/"MODULE-RETENU.ldr"
EAST="wall-000719"
ROOF="roof-000223"
MAIN_BEAM="TOITURE3-VARIANT-3006-ROW336-340"
EXCLUDE_ORIGINAL_UPPER_CHIMNEY="scene-chimney:house-chimney-antenna:00052:solution"
EPS=1e-5
ALTERNATIVES=("A","B")

def write(name,obj):
    (DIR/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def src():
    original=parse(B3)
    baseline=parse(ORIGINAL75)
    retained=parse(PREVIOUS75)
    assert len(original)==1904 and len(baseline)==75 and retained==baseline
    assert sum(r[-1]=="30363.dat" for r in original.values())==408
    assert ROOF not in retained
    assert original[ROOF]==["1","1","1270","-768","620","0","0","-1","0","1","0","1","0","0","30363.dat"]
    assert original[EAST]==retained[EAST]
    assert len([id for id,r in retained.items() if r[-1]=="30363.dat"])==5
    return original,retained

def actual_roof_wall(lib,orig):
    roof=instance(lib,ROOF,orig[ROOF])
    wall=instance(lib,EAST,orig[EAST])
    # Official 30363s01 has hollow open underside at y=24, local x ±10.
    cavities=[tuple(roof.transform.point((i,24,0))) for i in (-10,10)]
    studs=[tuple(wall.transform.point(c.position))
           for c in wall.definition.connectors if c.type=="stud"]
    matches=[list(p) for p in cavities if any(math.dist(p,q)<EPS for q in studs)]
    r=check_collision(roof,wall)
    insertion=vertical_sufficient(roof,wall)
    # Real B3 neighbors: stop potential NO-PASS even if own interface PASS.
    neighbors=[]
    for rid,row in orig.items():
        if rid in (ROOF,EAST,EXCLUDE_ORIGINAL_UPPER_CHIMNEY):
            continue
        x,y,z=map(float,row[2:5])
        if not (1140<=x<=1370 and -820<=y<=-710 and 500<=z<=770):
            continue
        p=instance(lib,rid,row)
        if not overlap(roof,p):continue
        rel=check_collision(roof,p)
        if rel is Relation.COLLISION:
            neighbors.append({"id":rid,"ref":row[-1],"relation":"COLLISION"})
    # 10 LDU off-lattice cannot be reported as a 2-stud mating witness.
    testc=[(x,y,z+10) for x,y,z in cavities]
    control_matches=sum(any(math.dist(q,p)<EPS for p in studs) for q in testc)
    local=(len(matches)==2 and r is Relation.CONTACT and
           insertion["status"]=="PASS" and not neighbors and control_matches==0)
    return {"roof_original":ROOF,"wall_original":EAST,"roof_line":' '.join(orig[ROOF]),
            "wall_line":' '.join(orig[EAST]),
            "genuine_part_sources":["30363.dat","3008.dat"],
            "actual_30363_underside_cavities":list(map(list,cavities)),
            "wall_3008_studs_at_top":list(map(list,studs)),
            "exact_anti_stud_to_stud_matches":matches,
            "official_LDraw_mesh_relation":r.value,
            "continuous_vertical_insert":insertion,
            "local_B3_forbidden_neighbors":neighbors,
            "negative_10_LDU_offset_matches":control_matches,
            "roof_wall_interface_status":"PASS" if local else "NON DÉMONTRÉ",
            "adjacent_roof_assembly_with_all_B3":"NON DÉMONTRÉ",
            "does_not_attach_five_retained_roofs":True,
            "status":"PASS" if local else "NON DÉMONTRÉ"}

def potential(a,b):
    return overlap(a,b)

def analyze_variant(name,lib,original,retained):
    case=parse(DIR/("VARIANTE-"+name+".ldr"))
    assert len(case)==81
    for rid,line in retained.items():
        assert case[rid]==line,"Retained TOITURE6 part changed in variant "+rid
    extra=[k for k in case if k not in retained]
    expected=[f"TOITURE7-{name}-3001-{n:02d}" for n in range(1,7)]
    assert extra==expected
    for idx,k in enumerate(extra):
        x,y,z=map(int,case[k][2:5])
        assert case[k][-1]=="3001.dat"
        assert [x,y,z]==[[1000,1060,1120,1180,1200,1240][idx],
                         [-840,-816,-792,-768,-744,-720][idx],
                         620 if name=="A" else 700]
        assert case[k][5:14]==["1","0","0","0","1","0","0","0","1"]
    parts={rid:instance(lib,rid,case[rid]) for rid in extra}
    oldbeam=instance(lib,MAIN_BEAM,retained[MAIN_BEAM])
    eastwall=instance(lib,EAST,retained[EAST])
    chain=[oldbeam,*[parts[k] for k in extra],eastwall]
    # Each new 3001 brick is UNDER the preceding one; all insertion
    # checks use upward insertion relative to previously fixed upper piece.
    edges=[]
    for upper,lower in zip(chain[:-2],chain[1:-1]):
        # Nominal 3001 x-axis bricks are directly under their predecessor.
        count=len(find_connections(lower,upper))
        relation=check_collision(lower,upper)
        sweep=vertical_sufficient(lower,upper,upwards=True)
        ok=(count>0 and relation is Relation.CONTACT and sweep["status"]=="PASS")
        edges.append({"under":lower.instance_id,"above":upper.instance_id,
            "genuine_connectors":count,"official_LDraw_relation":relation.value,
            "continuous_from_below":sweep,"status":"PASS" if ok else "NON DÉMONTRÉ"})
    final=parts[extra[-1]]
    final_con=len(find_connections(final,eastwall))
    final_rel=check_collision(final,eastwall)
    final_sweep=vertical_sufficient(final,eastwall,upwards=True)
    final_ok=(final_con>0 and final_rel is Relation.CONTACT and
              final_sweep["status"]=="PASS")
    edges.append({"under":final.instance_id,"above":EAST,
         "genuine_connectors":final_con,"official_LDraw_relation":final_rel.value,
         "continuous_from_below":final_sweep,
         "status":"PASS" if final_ok else "NON DÉMONTRÉ"})
    # Every new candidate against ALL retained 75 and source B3. Bounded
    # broad-phase uses B3's brick largest nominal half-size <=100 LDU,
    # roof length 80; every potentially intersecting placement is included.
    source_candidates=[]
    retained_ids=set(retained)
    for k,line in original.items():
        if k in retained_ids or k==EXCLUDE_ORIGINAL_UPPER_CHIMNEY:continue
        x,y,z=map(float,line[2:5])
        if 830<=x<=1420 and -940<=y<=-650 and 460<=z<=900:
            source_candidates.append((k,line))
    checked=0
    forbidden=[]
    cache={}
    for k,part in parts.items():
        for id,source in [(rid,retained[rid]) for rid in retained]+source_candidates:
            if id in extra:continue
            if id not in cache:cache[id]=instance(lib,id,source)
            q=cache[id]
            if not potential(part,q):continue
            checked+=1
            rel=check_collision(part,q)
            if rel is Relation.COLLISION:
                forbidden.append({"new":k,"existing":id,"ldraw_ref":source[-1],
                                  "official_mesh_relation":rel.value,
                                  "part_position":list(map(float,part.transform.point((0,0,0)))),
                                  "original_position":list(map(float,source[2:5]))})
        for other in extra:
            if other<=k:continue
            p=parts[other]
            if not potential(part,p):continue
            rel=check_collision(part,p)
            if rel is Relation.COLLISION:
                forbidden.append({"new":k,"existing":other,
                                  "ldraw_ref":"3001.dat","official_mesh_relation":rel.value})
    # Robust install proof cannot certify insertion if a new piece sweeps
    # through any earlier/modeled original piece other than its direct
    # stud/cavity partner. Keep every ambiguity explicit.
    swept=[]
    for i,k in enumerate(extra):
        moving=parts[k]
        allowed={MAIN_BEAM if i==0 else extra[i-1]}
        possible=[]
        # Retained 75 were assembled already; include them as obstacles.
        for rid,line in retained.items():
            if rid in allowed:continue
            if rid not in cache:cache[rid]=instance(lib,rid,line)
            if not swept_box_safe_others(moving,cache[rid],upwards=True):
                possible.append(rid)
        for old_id,line in source_candidates:
            if old_id in allowed:continue
            if old_id not in cache:cache[old_id]=instance(lib,old_id,line)
            if not swept_box_safe_others(moving,cache[old_id],upwards=True):
                possible.append(old_id)
        for other in extra[:i]:
            if other in allowed:continue
            if not swept_box_safe_others(moving,parts[other],upwards=True):
                possible.append(other)
        swept.append({"piece":k,"up_from_below":True,
           "full_48_LDU_continuous_sweep":True,
           "ambiguous_obstacles":possible,
           "status":"PASS" if not possible else "NON DÉMONTRÉ"})
    connectivity=all(e["status"]=="PASS" for e in edges)
    safe=len(forbidden)==0
    insertion=all(e["continuous_from_below"]["status"]=="PASS" for e in edges) and all(
        s["status"]=="PASS" for s in swept)
    valid=connectivity and safe and insertion
    priority=next((f for f in forbidden if f["new"]==extra[-1]),None)
    first=(forbidden[0] if forbidden else
           next((e for e in edges if e["status"]!="PASS"),None) or
           next((s for s in swept if s["status"]!="PASS"),None))
    return {"variant":name,"placement_z":620 if name=="A" else 700,
        "official_part":"3001.dat","candidate_real_lego_bricks":6,
        "no_original_B3_changes":True,
        "from_common_five_roof_beam":MAIN_BEAM,
        "target_second_wall":EAST,
        "stud_cavity_edges":edges,
        "actual_mesh_pairs_screened":checked,
        "forbidden_solid_collisions":forbidden,
        "continuous_insertion_observations":swept,
        "all_required_connectors":"PASS" if connectivity else "NON DÉMONTRÉ",
        "collisions":"PASS" if safe else "FAIL",
        "insertion":"PASS" if insertion else "NON DÉMONTRÉ",
        "fully_connected_second_path":"PASS" if valid else "NON DÉMONTRÉ",
        "first_obstacle":first,"end_piece_collision":priority,
        "retained":valid}

def main(ldraw_root):
    original,retained=src()
    library=LDrawLibrary(ldraw_root)
    assert "0 brick  2 x  4" in (ldraw_root/"parts/3001.dat").read_text().lower()
    assert "0 brick  1 x  8" in (ldraw_root/"parts/3008.dat").read_text().lower()
    assert "0 ~slope brick 18  4 x  2 without top face" in (ldraw_root/"parts/s/30363s01.dat").read_text().lower()
    roof223=actual_roof_wall(library,original)
    alternatives=[analyze_variant(n,library,original,retained) for n in ALTERNATIVES]
    success=next((x for x in alternatives if x["retained"]),None)
    if success:
        # Variant complete and its 75 retained pieces byte-identical. A
        # 81-piece genuine LEGO model could be retained only on true PASS.
        (DIR/"MODULE-RETENU.ldr").write_text(
           (DIR/("VARIANTE-"+success["variant"]+".ldr")).read_text(),encoding="utf-8")
        # A separate viewer with six real 3001 sources is necessary;
        # browser below always checks exact 75 unless dynamic shown.
        raise RuntimeError("SUCCESS_NEEDS_81_PART_VIEWER_BEFORE_CERTIFICATION: do not silently commit a 75 viewer")
    first=next((x["first_obstacle"] for x in alternatives if x["first_obstacle"] is not None),None)
    paths={
       "west_retained_proved_by_TOITURE5": [
         "roof-000338",MAIN_BEAM,
         "TOITURE4-VARIANT-3006-BRIDGE-TO-GABLE",
         "TOITURE4-VARIANT-3622-GABLE-CONNECTOR",
         "gable-000039","gable-000035","gable-000031","gable-000026",
         "wall-000707","wall-000009","TOITURE6-FOUNDATION-3811"],
       "second_original_wall_proved_by_TOITURE6":[
         EAST,"wall-000021","TOITURE6-FOUNDATION-3811"],
       "two_roof_to_different_wall_paths":"NON DÉMONTRÉ",
       "original_roof223_touching_wall719":roof223["status"],
       "why_roof223_is_not_sufficient":"Even if roof223 is supported by wall719, it has NO proven stud/cavity path to the retained five-slope common beam.",
       "bounded_attempts":alternatives
    }
    write("ROOF223-WALL719.json",roof223)
    write("DEUX-CHEMINS.json",paths)
    write("COLLISIONS.json",{
        "original_75_unchanged":True,
        "two_bounded_routes_real_B3_and_75_mesh_probed":True,
        "attempts":[{"route":x["variant"],"forbidden":x["forbidden_solid_collisions"],
           "screened":x["actual_mesh_pairs_screened"],"status":x["collisions"]} for x in alternatives],
        "retained_75_original_TOITURE6_validated_collisions":"PASS, not reaudited",
        "whole_expanded_variant":"FAIL" if any(x["collisions"]=="FAIL" for x in alternatives)
                                  else "NON DÉMONTRÉ",
        "retained_module":"PASS"})
    write("INSERTION.json",{
       "old_retained_75_original_TOITURE6":"PASS, not reaudited",
       "attempts":[{"route":x["variant"],"edges":x["stud_cavity_edges"],
          "sweeps":x["continuous_insertion_observations"],
          "status":x["insertion"]} for x in alternatives],
       "selected_module_additions":0,
       "status":"PASS for unchanged retained 75; NON DÉMONTRÉ for both additions"})
    write("BOM.json",{
       "total_retained_parts":75,"retained_new_parts":0,
       "retained_roof_slopes_30363":5,
       "original_retained_TOITURE6":"missions/TOITURE6/MODULE-RETENU-75.ldr",
       "attempts_each_official_3001":6,
       "experimental_real_bricks_not_in_retained":12,
       "note":"Experiments A/B are separate; no 3001 counts in the retained model."})
    result={
       "retained_parts":75,"new_certified_parts":0,
       "roof_slopes_certified":5,
       "roof223_wall719_local_interface":roof223["status"],
       "roof223_proves_second_path":False,
       "second_roof_support_independent":"NON DÉMONTRÉ",
       "two_local_variants_evaluated":2,
       "variant_results":{x["variant"]:{
         "links":x["all_required_connectors"],"collisions":x["collisions"],
         "insertion":x["insertion"],"first_obstacle":x["first_obstacle"]}
          for x in alternatives},
       "retained_75_collisions":"PASS (reference TOITURE6)",
       "retained_75_insertion":"PASS (reference TOITURE6)",
       "local_3811_foundation":"PASS (reference TOITURE6)",
       "full_house_foundation":"NON DÉMONTRÉ",
       "mechanical_stability":"NON DÉMONTRÉ",
       "mobile_retained_75":"NON DÉMONTRÉ until Chromium actual screenshot",
       "first_obstacle":first,
       "overall":"STOP: preserve 75 actual pieces; neither short under-roof path proved"
    }
    write("RESULTAT.json",result)
    print("TOITURE7_LOCAL="+json.dumps({
        "roof223_wall719":roof223["status"],
        "route_A":{k:alternatives[0][k] for k in
            ("fully_connected_second_path","collisions","insertion","first_obstacle")},
        "route_B":{k:alternatives[1][k] for k in
            ("fully_connected_second_path","collisions","insertion","first_obstacle")},
        "retained":75
    },ensure_ascii=False),flush=True)

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--ldraw-root",type=Path,required=True)
    main(parser.parse_args().ldraw_root)
