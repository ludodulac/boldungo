"""TOITURE-5: exact 31-course original B-3 wall column, from roof wall to y=-24.

Only 30 NEW wall-to-wall joints are measured; TOITURE-4 roof/gable graph is
retained verbatim as a proven prerequisite. The entire wall is one original
B-3 column: no adjustments, no copies, no new brick. No foundation y=0 in B-3.

Real LDraw 3008 triangles, exact stud positions, continuous 48 LDU
vertical insertion envelopes and full stud-cylinder sweep, NEVER discrete
sampled waypoints. Refuse unjustified PASS. Check neighboring B-3 walls
for positive-volume obstructions, without reauditing the roof.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from lego_geometry_engine import LDrawLibrary, Relation, check_collision, find_connections
from lego_geometry_engine.core import CONTACT_EPS
from toiture4_probe import (parse, instance, vertical_sufficient,
                            swept_box_safe_others, overlap, WALL, ORDER as ROOF4_ORDER)

ROOT=Path(__file__).resolve().parents[1]
DIR=ROOT/"missions/TOITURE5"
B3=ROOT/"missions/TOITURE3/B3-ORIGINAL-READONLY.ldr"
FOOT="wall-000009"
ROOF="wall-000707"
FOUNDATION_STATUS="NON DÉMONTRÉ"
EXTRA_ROOFS=[f"roof-{i:06d}" for i in (*range(313,318),*range(359,364))]

def write(name,obj):
    (DIR/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def selected_chain(b3):
    order=[]
    for y in range(-24,-745,-24):
        pick=[(pid,row) for pid,row in b3.items()
              if pid.startswith("wall-") and row[-1]=="3008.dat"
              and float(row[3])==y and float(row[4])==870
              and float(row[2]) in (860,880)]
        if len(pick)!=1:raise AssertionError("Missing/ambiguous original wall course at "+str(y))
        order.append(pick[0][0])
    assert len(order)==31 and order[0]==FOOT and order[-1]==ROOF
    return order

def main(root):
    b3=parse(B3)
    assert len(b3)==1904 and sum(r[-1]=="30363.dat" for r in b3.values())==408
    previous=json.loads((ROOT/"missions/TOITURE4/RESULTAT.json").read_text())
    assert previous["status"]=="PASS_LOCAL_WALL_LINK"
    assert previous["roof_count_preserved"]==5
    original=parse(ROOT/"missions/TOITURE4/MODULE-VARIANTE-PIGNON.ldr")
    current=parse(DIR/"MODULE-TOIT-AU-PIED.ldr")
    levels=selected_chain(b3)
    assert len(current)==43 and len(original)==13
    assert set(current)==set(levels).union(set(original))
    for pid in levels:assert current[pid]==b3[pid],"B-3 original wall placement altered: "+pid
    for pid in original:assert current[pid]==original[pid],"TOITURE4 local piece altered: "+pid
    assert not any(int(row[3])==0 for row in b3.values()), "Existing y=0 found: re-evaluate foundation"
    assert all(int(b3[pid][3])+24==int(b3[levels[i-1]][3]) for i,pid in enumerate(levels) if i)
    # This is a single 31-brick wall column, not thirty invented prototypes.
    lib=LDrawLibrary(root)
    instances={id:instance(lib,id,b3[id]) for id in levels}
    assert all(len(p.definition.connectors)==16 for p in instances.values())
    official=(root/"parts/3008.dat").read_text().lower()
    assert "0 brick  1 x  8" in official
    edges=[]
    problems=[]
    previous_parts=[]
    steps=[]
    for i,pid in enumerate(levels):
        part=instances[pid]
        if i==0:
            steps.append({"sequence":1,"id":pid,"root":"existing B3 wall at y=-24",
                          "approach":"original bottom course is local anchor; no LEGO foundation",
                          "status":"PASS_AS_LOCAL_ROOT"})
        else:
            lower=instances[levels[i-1]]
            matched=find_connections(lower,part)
            rel=check_collision(lower,part)
            motion=vertical_sufficient(part,lower)
            # Compare exact full sweep with every EARLIER INSTALLED other than
            # the intended mating support. A positive projected AABB overlap
            # would require further geometry, and is NOT auto-certified.
            interfering=[p.instance_id for p in previous_parts[:-1]
                         if not swept_box_safe_others(part,p)]
            valid=(len(matched)>=1 and rel is Relation.CONTACT and
                   motion["status"]=="PASS" and not interfering)
            row={"lower":lower.instance_id,"upper":pid,
                 "lower_xyz_ldu":list(map(int,b3[lower.instance_id][2:5])),
                 "upper_xyz_ldu":list(map(int,b3[pid][2:5])),
                 "recognized_connector_count":len(matched),
                 "actual_LDraw_mesh_relation":rel.value,
                 "verified_continuous_insertion":motion,
                 "nonmating_prior_piece_sweep_obstacles":interfering,
                 "status":"PASS" if valid else "NON DÉMONTRÉ"}
            edges.append(row)
            if not valid:problems.append(row)
            x,y,z=map(float,b3[pid][2:5])
            steps.append({"sequence":i+1,"id":pid,
              "start_ldraw_xyz":[x,y-48,z],"end_ldraw_xyz":[x,y,z],
              "motion":"XYZ(t)=(x,y-48+48*t,z) for all t ∈ [0,1], fixed rotation",
              "mating_below":lower.instance_id,
              "all_earlier_nonmating_parts_considered":len(previous_parts)-1,
              "full_continuous_stud_sweep":motion,
              "status":"PASS" if valid else "NON DÉMONTRÉ"})
        previous_parts.append(part)
    assert len(edges)==30 and len(steps)==31
    wall_ok=not problems
    # Current full B3 environment. Unlike the B3 roof local proof, the wall
    # course is part of the original B3 walls and its adjacent neighbors may
    # share coplanar SIDE FACES; these are not positive-volume collisions.
    # Still check every overlapping b-box with genuine official meshes.
    other_ids=set(levels)
    candidates=[]
    for pid,row in b3.items():
        if pid in other_ids:continue
        x,y,z=map(float,row[2:5])
        if 670<=x<=1060 and -780<=y<=0 and 830<=z<=910:
            candidates.append((pid,row))
    excluded_solid=[]
    actual_pairs=0
    for pid,row in candidates:
        ext=instance(lib,pid,row)
        for wall_id in levels:
            own=instances[wall_id]
            # AABB positive overlap only; shared exact side plane is legal.
            if not overlap(ext,own):continue
            actual_pairs+=1
            relation=check_collision(own,ext)
            if relation is Relation.COLLISION:
                excluded_solid.append({"wall":wall_id,"other_original_B3":pid,
                                       "source_part":row[-1],"mesh_relation":relation.value})
    # Foundation cannot be inferred from touching the model's coordinate
    # ground; no original B3 piece begins at y=0 and no baseplate is present.
    base_candidates=[{"id":id,"ref":line[-1],"at_y":line[3]} for id,line in b3.items()
          if line[-1].lower() in {"3811.dat","3811","3857.dat","4186.dat","4186.dat"} or int(line[3])==0]
    assert not base_candidates, "Unexpected foundation candidates; inspect manually"
    # Existing TOITURE4 roof graph was proved unchanged. Glue the original
    # wall-000707 endpoint to its first proven gable-000026.
    graph={r["upper"]:r["lower"] for r in edges if r["status"]=="PASS"}
    prior_conn=json.loads((ROOT/"missions/TOITURE4/CONNEXIONS.json").read_text())
    old_edges=prior_conn["wall_link_edges"]
    assert old_edges[0]["base"]=="wall-000707"
    assert len(old_edges)==7 and all(e["status"]=="PASS" for e in old_edges)
    for e in old_edges:graph[e["attached"]]=e["base"]
    for roof in ["roof-000336","roof-000337","roof-000338","roof-000339","roof-000340"]:
        graph[roof]="TOITURE3-VARIANT-3006-ROW336-340"
    paths={}
    for roof in ["roof-000336","roof-000337","roof-000338","roof-000339","roof-000340"]:
        n=roof
        path=[n]
        for _ in range(60):
            if n==FOOT:break
            if n not in graph:break
            n=graph[n];path.append(n)
        paths[roof]=path
        if n!=FOOT:wall_ok=False
    # No independent wall-to-roof connection to a SECOND separate wall in
    # the retained graph. Other B3 wall/gable candidates are not automatically
    # supports merely because coordinates are near one another.
    second={"status":"NON DÉMONTRÉ","candidate_other_wall":"wall-000706",
            "candidate_other_gable":"gable-000036",
            "reason":"Original TOITURE4 graph has only one wall endpoint (wall-000707). No second actual connector/continuous insertion and load path demonstrated.",
            "physical_stability":"NON DÉMONTRÉ"}
    # The ten other target roof 30363 slopes (original immutable coords)
    # cannot be silently added to the existing 3006. They occupy different
    # X/Y roof rows and require independent stud/cavity and structural checks.
    prev_roofs=["roof-000336","roof-000337","roof-000338","roof-000339","roof-000340"]
    extra=[]
    beam_orig=json.loads((ROOT/"missions/TOITURE4/PROVENANCE.json").read_text())["reuse_toiture3_common_beam"]["original_experiment_line"].split()
    by=float(beam_orig[3])
    for pid in EXTRA_ROOFS:
        row=b3[pid];y=float(row[3])
        # Standard 30363 local underside y+24, 3006 beam stud y=-864
        # = same mating-plane ONLY if y+24==-864.
        planned_cavity_y=y+24
        same_mating_y=abs(planned_cavity_y-by)<CONTACT_EPS
        extra.append({"id":pid,"ref":row[-1],
          "original_xyz":list(map(float,row[2:5])),
          "lower_cavity_candidate_y":planned_cavity_y,
          "existing_shared_3006_mating_y":by,
          "same_shared_beam_mating_plane":same_mating_y,
          "status":"NOT_INTEGRATED — independent load-bearing support unproved"})
    assert len(extra)==10
    # Wall top and original gables remain unchanged, so no TOITURE4
    # geometries are rerun here. The new wall-stud checks are the ONLY
    # new roof-to-foot chain interfaces.
    result={
      "original_wall_chain_31_bricks":31,"new_wall_interfaces_measured":30,
      "roof_preserved":5,"additional_roof_integrated":0,
      "continuity_to_wall_foot":"PASS" if wall_ok else "FAIL",
      "wall_foot_id":FOOT,"wall_top_id":ROOF,
      "foundation_LEGO_identified":"NON",
      "foundation_connection":"NON DÉMONTRÉ",
      "second_independent_support":second["status"],
      "collisions":"PASS" if not excluded_solid else "FAIL",
      "insertion":"PASS" if wall_ok else "NON DÉMONTRÉ",
      "stability_physical":"NON DÉMONTRÉ",
      "visualization":"NON DÉMONTRÉ — browser check pending",
      "first_blocker":(problems[0] if problems else excluded_solid[0] if excluded_solid else
         "Aucune fondation LEGO à y=0 ; deuxième appui indépendant non démontré"),
      "B3_original_1904_preserved":True,"TOITURE4_13_preserved":True,
      "new_physical_bricks":0,
      "structure_to_ground":"wall foot at y=-24 ends body at y=0; not a fixed LEGO foundation",
      "extension_15":"5/15 integrated; remaining 10 not certified",
      "environment":{"nearby_B3_bricks_considered":len(candidates),
                     "potential_material_overlap_mesh_checked":actual_pairs,
                     "forbidden":excluded_solid},
      "scope":"Full 31-level B3 west/back wall column + unchanged prior TOITURE4 roof/gable. No true baseplate or second load path. Viewer uses schematic geometry."
    }
    write("CHAIN-PROOF.json",{"continuous_graph_to_original_foot":paths,
         "original_wall_levels_bottom_to_top":levels,
         "new_30_stud_cavity_edges":edges,
         "checked_count":len(edges),"passing_count":sum(e["status"]=="PASS" for e in edges),
         "first_failure":problems[0] if problems else None,
         "foundation_placement_candidates":base_candidates,
         "status":result["continuity_to_wall_foot"]})
    write("COLLISIONS.json",{"only_new_original_wall_column":True,
         "prior_roof4_collisions":"PASS retained, unchanged",
         "candidate_source_B3_neighbors":len(candidates),
         "source_B3_original_wall_mesh_pairs_checked":actual_pairs,
         "forbidden_neighbors":excluded_solid,"status":result["collisions"]})
    previous_assembly=json.loads((ROOT/"missions/TOITURE4/INSERTION.json").read_text())
    write("INSERTION.json",{"order":levels+previous_assembly["order"][1:],
         "wall_new_steps":steps,"top_12_unchanged_steps":previous_assembly["steps"][1:],
         "new_wall_30_continuous_stud_sweep_proven":wall_ok,
         "relative_translation":"XYZ(t)=(final_x,final_y-48+48*t,final_z), t∈[0,1]; never sampled waypoints",
         "previous_roof4_insertion":"PASS retained unchanged",
         "status":result["insertion"]})
    write("EXTENSION.json",{"tested_source_roofs":15,
         "retained_roof_ids":prev_roofs,"new_roof_candidates":extra,
         "new_integrated":0,"second_support":second,
         "notes":"Row 313..317 cavity y=-840, row 359..363 cavity y=-888, while shared beam top y=-864. Candidate rows need independently verified LEGO supports, not arbitrary contact."})
    write("RESULTAT.json",result)
    print("TOITURE5_MEASURED="+json.dumps({
      k:result[k] for k in ("continuity_to_wall_foot","foundation_LEGO_identified",
        "foundation_connection","second_independent_support","roof_preserved",
        "additional_roof_integrated","collisions","insertion","first_blocker")},ensure_ascii=False),flush=True)

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--ldraw-root",type=Path,required=True)
    main(parser.parse_args().ldraw_root)
