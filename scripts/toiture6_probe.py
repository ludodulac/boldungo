"""TOITURE-6: one real 3811 local baseplate + second original B3 wall path.

Conservative official LDraw geometry: no connector-only PASS.  A true foundation
of the entire house / anchoring to ground and force/stability are NOT tested.
Only new joints after certified TOITURE5 are measured.
"""
from __future__ import annotations
import argparse,json,math
from dataclasses import replace
from pathlib import Path
from lego_geometry_engine import (LDrawLibrary,Relation,check_collision,
                                  find_connections,instantiate,transform_from_ldraw)
from lego_geometry_engine.core import CONTACT_EPS
from toiture1_probe import stud_clearance_sloped
from toiture4_probe import parse,instance,vertical_sufficient,swept_box_safe_others,overlap

ROOT=Path(__file__).resolve().parents[1]
DIR=ROOT/"missions/TOITURE6"
B3=ROOT/"missions/TOITURE3/B3-ORIGINAL-READONLY.ldr"
SOURCE=ROOT/"missions/TOITURE5/MODULE-TOIT-AU-PIED.ldr"
BASE="TOITURE6-FOUNDATION-3811"
WEST_FOOT="wall-000009"
EAST_FOOT="wall-000021"
EAST_TOP="wall-000719"
ROOF_BEAM="TOITURE3-VARIANT-3006-ROW336-340"
BRACES=["TOITURE6-BRIDGE-D-3006","TOITURE6-BRIDGE-C-3006",
        "TOITURE6-BRIDGE-B-3006","TOITURE6-BRIDGE-A-3006"]
ROOF_NEW="roof-000315"
EAST_WALL_IDS="wall-000021 wall-000045 wall-000069 wall-000092 wall-000116 wall-000139 wall-000163 wall-000186 wall-000210 wall-000233 wall-000256 wall-000279 wall-000301 wall-000323 wall-000346 wall-000368 wall-000391 wall-000413 wall-000435 wall-000458 wall-000480 wall-000503 wall-000527 wall-000552 wall-000576 wall-000601 wall-000625 wall-000649 wall-000673 wall-000696 wall-000719".split()
EXPECTED={
BASE:"1 2 960 0 760 1 0 0 0 1 0 0 0 1 3811.dat",
BRACES[0]:"1 19 1180 -768 620 1 0 0 0 1 0 0 0 1 3006.dat",
BRACES[1]:"1 19 1180 -792 620 1 0 0 0 1 0 0 0 1 3006.dat",
BRACES[2]:"1 19 1180 -816 620 1 0 0 0 1 0 0 0 1 3006.dat",
BRACES[3]:"1 19 1060 -840 620 1 0 0 0 1 0 0 0 1 3006.dat"}
EPS=1e-5
def write(name,payload):
    (DIR/name).write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def scope():
    original=parse(B3)
    previous=parse(SOURCE)
    fragment=parse(DIR/"MODULE-VARIANTE.ldr")
    assert len(original)==1904 and len(previous)==43 and len(fragment)==80
    assert all(fragment[k]==v for k,v in previous.items()),"TOITURE-5 record mutated"
    assert len(EAST_WALL_IDS)==31 and len(set(EAST_WALL_IDS))==31
    for i,k in enumerate(EAST_WALL_IDS):
        assert fragment[k]==original[k] and original[k][-1] in ("3008.dat","3009.dat")
        assert int(original[k][3])==-24*(i+1)
        assert int(original[k][2])==1270
    assert EAST_WALL_IDS[0]==EAST_FOOT and EAST_WALL_IDS[-1]==EAST_TOP
    assert fragment[ROOF_NEW]==original[ROOF_NEW] and fragment[ROOF_NEW][-1]=="30363.dat"
    for k,line in EXPECTED.items():assert fragment[k]==line.split()
    prior=json.loads((ROOT/"missions/TOITURE5/RESULTAT.json").read_text())
    assert prior["continuity_to_wall_foot"]=="PASS"
    return original,previous,fragment

def cropped_stud_witness(moving,static):
    """Use actual moving LDraw triangles, official 6 LDU stud primitive,
    and *only* the static stud cylinders whose XZ disk intersects mover.
    Geometry for other studs is disjoint in XZ, exactly, at every t.
    """
    bounds=moving.bbox
    fixed=[c for c in static.definition.connectors
           if c.type=="stud"
           and bounds.minimum[0]-6.00001<=static.transform.point(c.position)[0]<=bounds.maximum[0]+6.00001
           and bounds.minimum[2]-6.00001<=static.transform.point(c.position)[2]<=bounds.maximum[2]+6.00001]
    smaller=replace(static,definition=replace(static.definition,connectors=tuple(fixed)))
    report=stud_clearance_sloped(moving,smaller)
    bad=[x for x in report if not x["continuous_sweep_clear"]]
    return {"source_real_mesh":moving.definition.part_id,
            "studs_total":sum(c.type=="stud" for c in static.definition.connectors),
            "studs_in_exact_swept_projection":len(fixed),
            "full_parametric_stud_sweep":True,"interferences":bad,
            "status":"PASS" if not bad else "NON DÉMONTRÉ"}

def plate_to_wall(plate,foot):
    fixed=plate.transform.point((0,0,0))[1]
    lower=foot.transform.point((0,24,0))[1]
    # Baseplate solid body starts at y=0 and extends down to y=4.
    # Wall body ends at y=0. Only studs can intersect the wall cavities.
    body_nonoverlap=lower<=fixed+EPS
    start_clear=foot.bbox.maximum[1]-48<plate.bbox.minimum[1]-EPS
    nominal=find_connections(plate,foot)
    studs=cropped_stud_witness(foot,plate)
    valid=len(nominal)>=2 and body_nonoverlap and start_clear and studs["status"]=="PASS"
    return {"foot":foot.instance_id,"plate":plate.instance_id,
            "actual_mesh_plate_bbox":list(plate.definition.bbox.minimum+plate.definition.bbox.maximum),
            "body_y_separation":body_nonoverlap,"48_ldu_start_disjoint":start_clear,
            "official_anti_stud_to_stud_matches":len(nominal),
            "real_stud_primitive_vs_real_wall_mesh":studs,
            "status":"PASS" if valid else "NON DÉMONTRÉ"}

def pair(under,above,kind):
    contacts=find_connections(under,above)
    rel=check_collision(under,above)
    sweep=vertical_sufficient(above,under)
    good=bool(contacts) and rel is Relation.CONTACT and sweep["status"]=="PASS"
    return {"from":under.instance_id,"to":above.instance_id,"kind":kind,
            "official_mesh_relation":rel.value,"genuine_connector_count":len(contacts),
            "continuous_insertion":sweep,
            "status":"PASS" if good else "NON DÉMONTRÉ"}

def positive_volume(a,b):
    return all(min(a.bbox.maximum[k],b.bbox.maximum[k])-
               max(a.bbox.minimum[k],b.bbox.minimum[k])>CONTACT_EPS for k in (0,1,2))

def main(ldraw):
    original,old,frag=scope()
    library=LDrawLibrary(ldraw)
    assert "0 baseplate 32 x 32" in (ldraw/"parts/3811.dat").read_text().lower()
    assert "0 brick  2 x 10" in (ldraw/"parts/3006.dat").read_text().lower()
    assert "0 brick  1 x  8" in (ldraw/"parts/3008.dat").read_text().lower()
    P={}
    # Only new pieces plus original wall endpoints and 31 wall courses are instantiated.
    for k in [BASE,WEST_FOOT,*EAST_WALL_IDS,*BRACES,ROOF_BEAM,ROOF_NEW]:
        P[k]=instance(library,k,frag[k])
    plate=P[BASE]
    assert len(plate.definition.connectors)>=1024 and plate.definition.part_id=="3811.dat"
    foundation_west=plate_to_wall(plate,P[WEST_FOOT])
    foundation_east=plate_to_wall(plate,P[EAST_FOOT])
    base_pass=all(x["status"]=="PASS" for x in (foundation_west,foundation_east))
    # Negative controls: 1/2 stud horizontal shift must break exact lattice;
    # a superimposed duplicate genuine 3811 would be forbidden.
    bad=instantiate(P[WEST_FOOT].definition,"NEGATIVE-HALF-STUD",
        P[WEST_FOOT].transform.compose(type(P[WEST_FOOT].transform).translation(10,0,0)))
    negative={"10_LDU_half_stud_shift_nominal_matches":len(find_connections(plate,bad)),
              "identical_3811_solid_collision":check_collision(plate,plate).value}
    negative_ok=(negative["10_LDU_half_stud_shift_nominal_matches"]==0
                 and negative["identical_3811_solid_collision"]=="COLLISION")
    # Every other B3 part occupying the foundation contact elevation must be
    # assessed for body intersection and nearby stud lattice alignment.
    # This is NOT a claim to a whole-house foundation.
    base_near=[]
    base_bad=[]
    for k,row in original.items():
        if k in (WEST_FOOT,EAST_FOOT):continue
        if abs(float(row[3])+24)>EPS:continue
        x,z=float(row[2]),float(row[4])
        # B3 bricks at xz within baseplate projection + maximal B3 half span
        if not (520<=x<=1400 and 320<=z<=1200):continue
        r=instance(library,k,row)
        if not overlap(r,plate,(0,2)):continue
        body_clear=r.transform.point((0,24,0))[1]<=plate.transform.point((0,0,0))[1]+EPS
        con=len(find_connections(plate,r))
        base_near.append({"id":k,"ref":row[-1],"nominal_con":con,"body_y_separate":body_clear})
        if not body_clear or con<1:base_bad.append(base_near[-1])
    # Second distinct wall (east, x=1270): 30 NEW original joints, not the
    # already-proved original west wall column from TOITURE-5.
    wall_edges=[pair(P[a],P[b],"ORIGINAL_B3_SECOND_WALL_COURSE")
                for a,b in zip(EAST_WALL_IDS,EAST_WALL_IDS[1:])]
    east_ok=all(p["status"]=="PASS" for p in wall_edges)
    # Continuous 48 LDU insertion of wall pieces against all nonmating
    # previously installed members of the *second* column. Positive AABB
    # projected sweep ambiguity never silently passes.
    side_assembly=[]
    for i,k in enumerate(EAST_WALL_IDS):
        if i==0:continue
        nonmating=[p for p in EAST_WALL_IDS[:i-1]
                   if not swept_box_safe_others(P[k],P[p])]
        if nonmating:east_ok=False
        side_assembly.append({"id":k,"step":i+1,"previous_nonmating_obstructions":nonmating,
                              "status":"PASS" if not nonmating else "NON DÉMONTRÉ"})
    # second roof-support pathway: wall719 <- D <- C <- B <- A <- old roof beam
    chain=[EAST_TOP,*BRACES,ROOF_BEAM]
    support_edges=[]
    for i in range(len(chain)-1):
        a,b=chain[i],chain[i+1]
        # Note row 719 is below the D support at y=-768.
        support_edges.append(pair(P[a],P[b],"NEW_SECOND_LOAD_PATH"))
    two_paths=east_ok and all(e["status"]=="PASS" for e in support_edges)
    # Real geometry and neighboring B3 placements, only for newly added
    # 4 braces, and global local foundation contact. Exclude original upper
    # chimney (already excluded only in TOITURE4 experimental variant).
    checked=0
    collisions=[]
    excluded={"scene-chimney:house-chimney-antenna:00052:solution"}
    for new_id in BRACES:
        new=P[new_id]
        for old_id,row in original.items():
            if old_id in excluded:continue
            if old_id==ROOF_NEW:continue  # separately examined as new roof candidate
            if old_id in EAST_WALL_IDS:continue
            x,y,z=map(float,row[2:5])
            if not (820<=x<=1370 and -900<=y<=-700 and 450<=z<=850):continue
            oldpart=instance(library,old_id,row)
            if not positive_volume(new,oldpart):continue
            checked+=1
            rel=check_collision(new,oldpart)
            if rel is Relation.COLLISION:
                collisions.append({"piece":new_id,"original_B3_neighbor":old_id,
                                   "reference":row[-1],"relation":rel.value})
        # All added beams are actual physical solids, and the existing
        # roof common beam/gable support is preserved. Check their mesh
        # intersections, not merely connector centers.
        # Intended pairs are already assessed, but COLLISION always forbids.
    internal=[]
    new_beams=[P[k] for k in BRACES]
    for i,p in enumerate(new_beams):
        for q in new_beams[i+1:]+[P[ROOF_BEAM]]:
            if not positive_volume(p,q):continue
            rel=check_collision(p,q)
            if rel is Relation.COLLISION:internal.append([p.instance_id,q.instance_id])
    # One targeted sixth slope, original B-3 30363, same coordinates.
    roof=P[ROOF_NEW]
    a=P[BRACES[-1]]
    cavities=[tuple(roof.transform.point((q,24,0))) for q in (-10,10)]
    studs=[tuple(a.transform.point(c.position)) for c in a.definition.connectors if c.type=="stud"]
    matched=[list(c) for c in cavities if any(math.dist(c,s)<EPS for s in studs)]
    roof_rel=check_collision(roof,a)
    roof_sweep=vertical_sufficient(roof,a)
    # This extra roof is inserted BEFORE the old five. Test its final
    # local interactions with the original five roofs separately. No old
    # TOITURE3 certification is re-run.
    # Conservative swept AABB for the original row-336 pieces is included
    # to avoid falsely claiming a realizable ordering.
    roof_vs_previous=[]
    oldrooforder=["roof-000338","roof-000337","roof-000339","roof-000336","roof-000340"]
    roof_siblings=[]
    for pid in oldrooforder:
        sibling=instance(library,pid,frag[pid])
        relation=check_collision(roof,sibling) if positive_volume(roof,sibling) else Relation.SEPARATED
        # Later inserting the already-certified original slope into an
        # assembly where roof315 is present may have a swept collision.
        swept=swept_box_safe_others(sibling,roof)
        roof_siblings.append({"later_original_slope":pid,"final_relation":relation.value,
                              "conservative_full_sweep_AABB_separated":swept})
    sixth_pass=(len(matched)==2 and roof_rel is Relation.CONTACT and
                roof_sweep["status"]=="PASS"
                and all(x["final_relation"]!="COLLISION" and
                        x["conservative_full_sweep_AABB_separated"] for x in roof_siblings))
    # A conservative swept overlap from roof 315 may leave sixth roof
    # NOT CERTIFIED; do not grow the claimed roof count just for aesthetics.
    collision_ok=not collisions and not internal and not base_bad
    support_pass=base_pass and two_paths and collision_ok and negative_ok
    first=(None if support_pass else
        next(({"base":k,"reason":v} for k,v in
              [("wall009",foundation_west),("wall021",foundation_east)]
              if v["status"]!="PASS"),None)
        or next((v for v in wall_edges if v["status"]!="PASS"),None)
        or next((v for v in support_edges if v["status"]!="PASS"),None)
        or (collisions[0] if collisions else internal[0] if internal else
            base_bad[0] if base_bad else "NON DÉMONTRÉ"))
    result={
      "pieces_in_experimental_module":80,
      "parts_from_TOITURE5_preserved":43,
      "original_second_wall_pieces":31,
      "new_experimental_pieces":5,
      "new_experimental_refs":{"3811.dat":1,"3006.dat":4},
      "roof_count_preserved":5,
      "sixth_original_roof_candidate":ROOF_NEW,
      "new_roofs_geometrically_certified":1 if sixth_pass and support_pass else 0,
      "total_roofs_certified":6 if sixth_pass and support_pass else 5,
      "baseplate_3811_geometry":"PASS" if base_pass and negative_ok and not base_bad else "NON DÉMONTRÉ",
      "wall000009_on_base":foundation_west["status"],
      "wall000021_on_base":foundation_east["status"],
      "local_foundation":"PASS" if base_pass and negative_ok and not base_bad else "NON DÉMONTRÉ",
      "second_original_wall_chain":f"{sum(x['status']=='PASS' for x in wall_edges)}/30",
      "second_independent_roof_to_wall_path":"PASS" if support_pass else "NON DÉMONTRÉ",
      "two_wall_paths_distinct_above_base":True if two_paths else False,
      "shared_single_local_baseplate":True,
      "full_house_foundation":"NON DÉMONTRÉ",
      "mechanical_stability":"NON DÉMONTRÉ",
      "collisions":"PASS" if collision_ok else "FAIL",
      "insertion":"PASS" if support_pass else "NON DÉMONTRÉ",
      "viewer":"NON DÉMONTRÉ until mobile Chromium proof",
      "roof_sixth_insertion":"PASS" if sixth_pass else "NON DÉMONTRÉ",
      "first_obstacle":first if first is not None else
          ("Sixth roof after/before neighboring slopes: full sweep ambiguity" if not sixth_pass else None),
      "overall":"PASS_TWO_LOCAL_SUPPORTS" if support_pass else "NON DÉMONTRÉ",
      "limitations":["One 3811 baseplate does NOT certify anchoring, whole-house foundation or force capacity",
                     "Two graph paths end in different genuine B3 walls and share one local 3811",
                     "No plastic fit friction, bending, fatigue or buckling test",
                     "Any sixth-slope ambiguity is not claimed as an extra certified roof."]
    }
    write("FONDATION.json",{"placement":EXPECTED[BASE],"source":"Official 3811.dat genuine LDraw",
         "root_west":foundation_west,"root_east":foundation_east,
         "nearby_original_B3_bases_considered":base_near,
         "invalid_neighbor_foundations":base_bad,
         "negative_tests":negative,"negative_tests_pass":negative_ok,
         "local_plate_not_full_house":True,
         "status":result["local_foundation"]})
    write("DEUXIEME-APPUI.json",{"first_original_WEST_wall_foot":WEST_FOOT,
         "first_original_WEST_roof_wall_top":"wall-000707",
         "first_roof_path_from_previous_TOITURE5":"PASS retained unchanged",
         "second_original_EAST_wall_foot":EAST_FOOT,
         "second_original_EAST_wall_top":EAST_TOP,
         "original_east_wall_ids_bottom_to_top":EAST_WALL_IDS,
         "east_new_30_stud_cavity_connections":wall_edges,
         "east_all_nonmating_wall_insertions":side_assembly,
         "new_beam_bridge_edges":support_edges,
         "two_independent_walls":"wall-000707 and wall-000719",
         "common_roof_beam":ROOF_BEAM,
         "same_local_baseplate_not_separate_anchors":True,
         "status":result["second_independent_roof_to_wall_path"]})
    write("COLLISIONS.json",{"B3_original_records":len(original),
         "B3_new_braces_real_mesh_pair_interactions_checked":checked,
         "B3_actual_forbidden":collisions,"new_support_internal_solid_overlap":internal,
         "baseplate_adjacent_footprint":base_near,
         "baseplate_grid_or_body_incompatibility":base_bad,
         "original_5_roofs_previous_TOITURE5":"PASS retained unchanged",
         "roof315_pair_with_bridge":roof_rel.value,
         "roof315_to_existing_roof_rows":roof_siblings,
         "status":result["collisions"]})
    order=json.loads((DIR/"VIEWER-80.json").read_text())["assembly_plan"]["steps"]
    write("INSERTION.json",{"order":[s["placement_ids"][0] for s in order],
         "original_toiture5":"PASS retained unchanged",
         "baseplate_root":"LOCAL FIRST PLACEMENT",
         "foundation_west_48ldu":foundation_west,
         "foundation_east_48ldu":foundation_east,
         "second_wall_30_entire_continuous_insertion":wall_edges,
         "second_support_four_genuine_3006_stud_sweeps":support_edges,
         "new_roof315": {"matched_cavity_centers":matched,
                         "real_mesh_relation":roof_rel.value,
                         "whole_continuous_sweep":roof_sweep,
                         "later_original_roof_siblings":roof_siblings,
                         "status":result["roof_sixth_insertion"]},
         "status":result["insertion"]})
    write("RESULTAT.json",result)
    print("TOITURE6_MEASURED="+json.dumps({k:result[k] for k in
          ("local_foundation","second_original_wall_chain",
           "second_independent_roof_to_wall_path","roof_count_preserved",
           "new_roofs_geometrically_certified","collisions","insertion",
           "roof_sixth_insertion","first_obstacle")},ensure_ascii=False),flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--ldraw-root",type=Path,required=True)
    main(p.parse_args().ldraw_root)
