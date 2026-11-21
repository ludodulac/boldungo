"""TOITURE-4: prove a wall/gable connection independent of the chimney.

Only NEW interfaces are tested. TOITURE-3 five-slope module is a pinned PASS
reference. Two REAL new LEGO pieces (3006, 3622) link the TOITURE-3 beam
through gable 000039, 035, 031, 026 to B3 wall 000707.

Pure vertical paths are checked by full-interval analytic bounding envelopes
and official mesh triangle-vs-cylindrical stud sweep.  The lower 3006 bridge
inserts UPWARDS: mathematically equivalent to the stationary upper connector
moving DOWN relative to the bridge. Any unverified swept collision returns
NON DÉMONTRÉ; never dismiss it for connector alignment.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
from lego_geometry_engine import (
    LDrawLibrary,Relation,check_collision,find_connections,instantiate,transform_from_ldraw
)
from lego_geometry_engine.core import CONTACT_EPS
from toiture1_probe import stud_clearance_sloped

ROOT=Path(__file__).resolve().parents[1]
DIR=ROOT/"missions/TOITURE4"
B3=ROOT/"missions/TOITURE3/B3-ORIGINAL-READONLY.ldr"
WALL="wall-000707"
GABLES=["gable-000026","gable-000031","gable-000035","gable-000039"]
CONNECTOR="TOITURE4-VARIANT-3622-GABLE-CONNECTOR"
BRIDGE="TOITURE4-VARIANT-3006-BRIDGE-TO-GABLE"
UPPER="TOITURE3-VARIANT-3006-ROW336-340"
ROOFS=["roof-000336","roof-000337","roof-000338","roof-000339","roof-000340"]
ORDER=[WALL,*GABLES,CONNECTOR,BRIDGE,UPPER,*["roof-000338","roof-000337","roof-000339","roof-000336","roof-000340"]]
NEW={BRIDGE:"1 19 960 -840 760 0 0 -1 0 1 0 1 0 0 3006.dat",
     CONNECTOR:"1 19 970 -864 870 0 0 -1 0 1 0 1 0 0 3622.dat"}
ORIGINAL_UPPER_CHIMNEY="scene-chimney:house-chimney-antenna:00052:solution"
APPROACH=48.0
EPS=1e-5
# Complete B3 source 1904 parsed. A candidate is discovered from a
# conservative 120 LDU wide expansion beyond the module envelope,
# exceeding max original source footprint in its near roof/gable region.
NEIGHBOR_WINDOW=(710,1210,-1100,-650,360,1050)

def write(name,data):
    (DIR/name).write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")

def parse(path):
    result={}
    id=None
    for line in path.read_text().splitlines():
        if line.startswith("0 // "):
            id=line[5:].strip().split()[0]
        elif line.startswith("1 "):
            if not id or id in result:raise AssertionError("Invalid duplicate/unlabeled placement "+str(id))
            result[id]=line.split()
            id=None
    return result

def instance(library,id,line):
    return instantiate(library.load_part(line[-1]),id,transform_from_ldraw(
        [float(x) for x in line[2:14]]),int(line[1]))

def overlap(a,b,axes=(0,1,2)):
    return all(min(a.bbox.maximum[i],b.bbox.maximum[i])-max(a.bbox.minimum[i],b.bbox.minimum[i])>CONTACT_EPS for i in axes)

def source(root):
    b3=parse(B3)
    current=parse(DIR/"MODULE-VARIANTE-PIGNON.ldr")
    assert len(b3)==1904 and sum(line[-1]=="30363.dat" for line in b3.values())==408
    assert len(current)==13 and set(current)==set(ORDER)
    for id in [WALL,*GABLES,*ROOFS]:
        assert current[id]==b3[id], "B3 part unexpectedly edited "+id
    assert current[UPPER]==parse(ROOT/"missions/TOITURE3/MODULE-CONTIGU-5.ldr")[UPPER]
    assert current[CONNECTOR]==NEW[CONNECTOR].split()
    assert current[BRIDGE]==NEW[BRIDGE].split()
    assert current[BRIDGE][-1]=="3006.dat" and current[CONNECTOR][-1]=="3622.dat"
    return b3,current

def strict_official_shapes(root):
    a=(root/"parts/3006.dat").read_text().lower()
    b=(root/"parts/3622.dat").read_text().lower()
    c=(root/"parts/3008.dat").read_text().lower()
    assert "0 brick  2 x 10" in a
    assert "0 brick  1 x  3" in b
    assert "0 brick  1 x  8" in c
    assert "1 16 0 24 0 100 0 0 0 -24 0 0 0 20 box5.dat" in a
    return {"pinned_true_LDraw_3006_3622_3008":True,
            "source":"pybricks/ldraw c43ed06a128a10ed65675166bf42eb6fd608b9b0",
            "nominal_height_brick_ldu":24,"nominal_x_length_3006":200}

def match(a,b):
    return find_connections(a,b)

def vertical_sufficient(moving,stationary,*,upwards=False):
    """Conservative full-sweep check for two fixed upright LEGO pieces.

    Downward case: moving piece body bottom at terminal matches old
    support top (Y increases down). Upward case: moving studs enter
    the stationary piece underside; reverse the relative motion so the
    stationary cavity is descending onto the fixed stud.
    """
    if upwards:
        # A relative coordinate translation makes the moving studs fixed
        # and the stationary cavity move DOWN. Same collision geometry at
        # every t, without samples or new connector assumptions.
        a,b=stationary,moving
        body_end_clear=(
            moving.transform.point((0,0,0))[1] >=
            stationary.transform.point((0,24,0))[1]-EPS)
        start_disjoint=(moving.bbox.minimum[1]+APPROACH >
                        stationary.bbox.maximum[1]+EPS)
    else:
        a,b=moving,stationary
        body_end_clear=(moving.transform.point((0,24,0))[1] <=
                        stationary.transform.point((0,0,0))[1]+EPS)
        start_disjoint=(moving.bbox.maximum[1]-APPROACH <
                        stationary.bbox.minimum[1]-EPS)
    sweeps=stud_clearance_sloped(a,b)
    threats=[x for x in sweeps if not x["continuous_sweep_clear"]]
    return {"direction":"UP from below" if upwards else "DOWN from above",
            "full_continuous_stud_sweep_not_discrete_samples":True,
            "body_planes_separate":body_end_clear,
            "initial_position_outside_neighbor":start_disjoint,
            "studs_checked":len(sweeps),"first_interference":threats[0] if threats else None,
            "status":"PASS" if body_end_clear and start_disjoint and not threats else "NON DÉMONTRÉ"}

def swept_box_safe_others(moving,third_party,*,upwards=False):
    """Sufficient full-interval AABB proof for all NON-MATING neighbors."""
    a,b=moving.bbox,third_party.bbox
    if any(min(a.maximum[k],b.maximum[k])-max(a.minimum[k],b.minimum[k])<=CONTACT_EPS for k in (0,2)):
        return True
    low=min(a.minimum[1],a.minimum[1]+(APPROACH if upwards else -APPROACH))
    high=max(a.maximum[1],a.maximum[1]+(APPROACH if upwards else -APPROACH))
    return high<=b.minimum[1]+CONTACT_EPS or low>=b.maximum[1]-CONTACT_EPS

def main(root):
    b3,rows=source(root)
    official=strict_official_shapes(root)
    prior=json.loads((ROOT/"missions/TOITURE3/RESULTAT.json").read_text())
    assert prior["local_module"]=="PASS" and prior["integrated_30363"]==5
    library=LDrawLibrary(root)
    P={id:instance(library,id,rows[id]) for id in ORDER}
    graph={}
    audited=[]
    chain=[WALL,*GABLES,CONNECTOR,BRIDGE,UPPER]
    # Only new six chain edges; five roof connections are certified in TOITURE3.
    chain_edges=list(zip(chain,chain[1:]))
    for lower,upper in chain_edges:
        a,b=P[lower],P[upper]
        connections=match(a,b)
        relation=check_collision(a,b)
        ups=(upper==BRIDGE)
        swept=vertical_sufficient(b,a,upwards=ups)
        verdict=(len(connections)>0 and relation is Relation.CONTACT and
                 swept["status"]=="PASS")
        row={"base":lower,"attached":upper,"recognized_exact_stud_cavity_count":len(connections),
             "LDraw_real_mesh_relation":relation.value,
             "full_continuous_insert":swept,"status":"PASS" if verdict else "NON DÉMONTRÉ"}
        audited.append(row)
        graph[upper]=lower
    # Below the bridge, the GABLE connector is deliberately installed first.
    # The up-inserting 3006 bridge docks to its underside. The upper original
    # 3006 roof beam then descends onto that bridge. No chimney is required
    # in the chain WALL->GABLE->CONNECTOR->BRIDGE->UPPER->FIVE ROOFS.
    chain_pass=all(x["status"]=="PASS" for x in audited)
    roof_prev=[s for s in
        json.loads((ROOT/"missions/TOITURE3/CONNEXIONS.json").read_text())["roof_to_shared_beam"]]
    roof_pass=len(roof_prev)==5 and all(x["status"]=="PASS" for x in roof_prev)
    graph.update({id:UPPER for id in ROOFS})
    rooted=[id for id in ORDER if id==WALL or
            (id in graph and all(x in graph or x==WALL for x in [graph[id]]))]
    # B3 wall -> gable chain is an existing geometric column, not foundations.
    path={}
    for id in ROOFS:
        n=id;path[id]=[n]
        while n!=WALL and n in graph:
            n=graph[n];path[id].append(n)
        assert n==WALL,"new module must actually reach selected wall"
    # B3 external context: all 1904 positions, prune remote parts by an
    # explicit conservative window. ALL actual candidate mesh intersections
    # use full official LDraw triangles.
    exclude=set(ORDER) & set(b3)
    exclude.add(ORIGINAL_UPPER_CHIMNEY)  # excluded ONLY in experimental variant
    skipped_protected=set()
    candidates=[]
    for id,record in b3.items():
        if id in exclude:continue
        x,y,z=map(float,record[2:5])
        if (NEIGHBOR_WINDOW[0]<=x<=NEIGHBOR_WINDOW[1] and
            NEIGHBOR_WINDOW[2]<=y<=NEIGHBOR_WINDOW[3] and
            NEIGHBOR_WINDOW[4]<=z<=NEIGHBOR_WINDOW[5]):
            candidates.append((id,record))
    outside=[]
    checked=0
    for ext_id,row in candidates:
        ext=instance(library,ext_id,row)
        for owned in ORDER:
            if not overlap(P[owned],ext):continue
            checked+=1
            rel=check_collision(P[owned],ext)
            if rel is Relation.COLLISION:
                outside.append({"new_or_original":owned,"b3_neighbor":ext_id,
                    "reference":row[-1],"mesh_collision":"COLLISION"})
    # Internal non-mating pairs must also be safe; mating pairs cannot
    # excuse solid overlap by connector alignment.
    paired={frozenset((a,b)) for a,b in chain_edges}
    paired.update(frozenset((UPPER,rid)) for rid in ROOFS)
    internal=[]
    for i,a in enumerate(ORDER):
        for b in ORDER[i+1:]:
            if frozenset((a,b)) in paired:continue
            if not overlap(P[a],P[b]):continue
            rel=check_collision(P[a],P[b])
            if rel is Relation.COLLISION:
                internal.append({"a":a,"b":b,"relation":rel.value})
    # Bounded insertion: entire continuous AABB path against *all*
    # previously installed non-mating pieces. This is a SUFFICIENT
    # condition; any interval overlap remains NON DÉMONTRÉ, not FAIL.
    motions=[]
    for i,id in enumerate(ORDER):
        p=P[id]
        upwards=(id==BRIDGE)
        if i==0:
            motions.append({"piece":id,"role":"existing B3 wall is the local assembly root",
                            "start_xyz_ldu":list(map(float,rows[id][2:5])),"status":"PASS",
                            "foundation":"NON DÉMONTRÉ"})
            continue
        parent=graph.get(id)
        old=P[parent] if parent else None
        interference=[]
        for other in ORDER[:i]:
            if other==parent:continue
            if not swept_box_safe_others(p,P[other],upwards=upwards):
                interference.append(other)
        direction=1 if upwards else -1
        final=list(map(float,rows[id][2:5]))
        start=[final[0],final[1]+direction*APPROACH,final[2]]
        entry={"piece":id,"full_path":"p(t)=start+(final-start)*t, t∈[0,1], orientation constant",
               "direction":"UP" if upwards else "DOWN","start_xyz_ldu":start,
               "final_xyz_ldu":final,"parent":parent,
               "checked_all_previous":i,"possible_nonmating_swept_body_obstructions":interference,
               "status":"PASS" if not interference else "NON DÉMONTRÉ"}
        motions.append(entry)
    insertion_pass=chain_pass and roof_pass and all(x["status"]=="PASS" for x in motions)
    good=chain_pass and roof_pass and not outside and not internal and insertion_pass
    first=(next((x for x in audited if x["status"]!="PASS"),None) or
           (outside[0] if outside else None) or (internal[0] if internal else None) or
           next((x for x in motions if x["status"]!="PASS"),None))
    result={
      "roof_count_preserved":5,"original_positions_changed":0,
      "wall_root":WALL,"real_gables_used":GABLES,
      "new_parts":2,"new_part_refs":["3006.dat","3622.dat"],
      "connections":"PASS" if chain_pass and roof_pass else "NON DÉMONTRÉ",
      "collisions":"PASS" if not outside and not internal else "FAIL",
      "supports_to_wall":"PASS" if chain_pass and roof_pass else "NON DÉMONTRÉ",
      "continuous_insertion":"PASS" if insertion_pass else "NON DÉMONTRÉ",
      "stability_mechanical":"NON DÉMONTRÉ",
      "load_to_foundations":"NON DÉMONTRÉ",
      "visualization":"NON DÉMONTRÉ avant Chromium",
      "first_blocker":first,
      "status":"PASS_LOCAL_WALL_LINK" if good else "NON DÉMONTRÉ",
      "structural_warning":"Wall-connected stud/cavity graph is NOT a test of strength or beam deflection, and the wall to foundation path remains unverified.",
      "environment":{"B3_reference_count":1904,
         "window":list(NEIGHBOR_WINDOW),
         "neighbors_checked":len(candidates),
         "mesh_potential_contacts_checked":checked,
         "external_forbidden_collisions":len(outside)}}
    write("CONNEXIONS.json",{"prior_five_roof_interfaces":"TOITURE3 established PASS; not reaudited",
        "wall_link_edges":audited,"roof_to_wall_verified_paths":path,
        "all_five_roof_to_beam_reference_pass":roof_pass,
        "geometry_source":official,"status":result["connections"]})
    write("COLLISIONS.json",{"full_source_B3_record_count":len(b3),
        "neighbor_window":list(NEIGHBOR_WINDOW),
        "original_upper_chimney_excluded_in_variant_only":ORIGINAL_UPPER_CHIMNEY,
        "neighbors_considered":len(candidates),
        "actual_mesh_interactions_checked":checked,
        "forbidden_external_pairs":outside,"forbidden_internal_pairs":internal,
        "status":result["collisions"]})
    write("INSERTION.json",{"order":ORDER,"method":"Whole 48 LDU analytic swept AABB nonmating; stud primitive triangle projection for mating",
        "upward_bridge_relative_motion_equivalence":True,
        "steps":motions,"status":result["continuous_insertion"]})
    write("RESULTAT.json",result)
    print("TOITURE4_MEASURED="+json.dumps({k:result[k] for k in
      ("roof_count_preserved","wall_root","new_parts","connections","collisions",
       "supports_to_wall","continuous_insertion","first_blocker","status","environment")},ensure_ascii=False),flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--ldraw-root",type=Path,required=True)
    main(p.parse_args().ldraw_root)
