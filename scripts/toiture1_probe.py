"""TOITURE-1: ONE existing B-3 slope 30363 with two original chimney support courses.

Precisely conserves all three LDraw type-1 records, matches a possible
underside cavity from official slope subpart, and analytically tests ALL
vertical insertion positions, not a few sampled waypoints.

No invented physical tolerance. Failure to certify cavity geometry is
NON DÉMONTRÉ rather than an auto-approved stud/cavity connection.
"""
from __future__ import annotations

import argparse,json,math
from pathlib import Path
from lego_geometry_engine import LDrawLibrary,Relation,assess_pair,check_collision,find_connections,instantiate,transform_from_ldraw
from lego_geometry_engine.joint_validation import first_mesh_crossing
from validation2_continuous_insertion import projected_triangle_disk_distance_squared

ROOT=Path(__file__).resolve().parents[1]
DIR=ROOT/"missions"/"TOITURE1"
IDS=["scene-chimney:house-chimney-antenna:00043:solution",
     "scene-chimney:house-chimney-antenna:00052:solution",
     "roof-000338"]
RADIUS=6.0
HEIGHT=4.0
APPROACH=48.0
EPS=1e-5

def dump(name,doc):
    (DIR/name).write_text(json.dumps(doc,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def parse_b3():
    seen={}
    comment=None
    for line in (DIR/"MODULE-B3-ORIGINAL.ldr").read_text().splitlines():
        if line.startswith("0 // "):comment=line[5:].strip()
        elif line.startswith("1 "):
            if comment is None or comment in seen:raise AssertionError("Duplicate/unmarked original row")
            seen[comment]=line.split()
            comment=None
    assert list(seen)==IDS
    assert [seen[i][-1] for i in IDS]==["3622.dat","3622.dat","30363.dat"]
    assert [seen[i][2:5] for i in IDS]==[
        ["950","-840","630"],["950","-864","630"],["970","-888","620"]]
    return seen

def ensure_geometry_sources(ldraw):
    # These source references come directly from the PINNED original LDraw
    # subpart, not 30363-based hidden connector whitelist or assumed dimensions.
    body=(ldraw/"parts/s/30363s01.dat").read_text().lower()
    roof=(ldraw/"parts/30363.dat").read_text().lower()
    stud=(ldraw/"p/stud.dat").read_text().lower()
    slope_sub=[
        "1 16 -10 0 0 0 0 1 0 1 0 -1 0 0 stud.dat",
        "1 16 10 0 0 0 0 1 0 1 0 -1 0 0 stud.dat",
        "0 bfc invertnext",
        "box2-5.dat",
        "box2-7.dat",
    ]
    assert "s\\30363s01.dat" in roof and all(s in body for s in slope_sub)
    assert "6 0 0 0 1 0 0 0 6 4-4edge.dat" in stud
    assert "0 -4 0 6 0 0 0 1 0 0 0 6 4-4edge.dat" in stud
    return {"mirror":"pybricks/ldraw pinned at c43ed06a128a10ed65675166bf42eb6fd608b9b0",
            "real_slope":"30363.dat / s/30363s01.dat",
            "physical_slope_top_studs":[[-10,0,0],[10,0,0]],
            "cavity_lower_face_ldraw_y":24,
            "slope_interior":"Hollow geometry (box2-5 / box2-7) is triangulated and checked in the sweep",
            "stud_radius_ldu":6,"stud_height_ldu":4}

def stud_clearance_sloped(roof,lower):
    """Sufficient continuous certificate: no moving TRIANGLE surface may
    penetrate any stationary cylindrical stud interior at ANY path parameter.
    The projection of every triangle onto XZ is invariant under pure vertical
    translation, and the reachable Y interval is computed algebraically.
    Thus rejecting all overlapping XZ projections proves the whole path for
    the stud cylinders; no point sampling of the translation.
    """
    fixed_studs=[x for x in lower.definition.connectors if x.type=="stud"]
    findings=[]
    for connector in fixed_studs:
        center=lower.transform.point(connector.position)
        threat=None
        touched=0
        for index,triangle in enumerate(roof.triangles):
            # World LDraw Y grows DOWN. At travel distance in [0,48],
            # every moving triangle Y ranges [minY-48,maxY].
            if max(v[1] for v in triangle)<center[1]-HEIGHT-EPS:continue
            if min(v[1] for v in triangle)-APPROACH>center[1]+EPS:continue
            if (min(v[0] for v in triangle)>center[0]+RADIUS or
                max(v[0] for v in triangle)<center[0]-RADIUS or
                min(v[2] for v in triangle)>center[2]+RADIUS or
                max(v[2] for v in triangle)<center[2]-RADIUS):continue
            dist2=projected_triangle_disk_distance_squared(triangle,center[0],center[2])
            touched+=1
            if dist2<(RADIUS-EPS)**2:
                threat={"triangle":index,"projection_distance_ldu":math.sqrt(dist2),
                        "stud_center_ldu":list(center),"moving_triangle_final_xyz_ldu":[list(v) for v in triangle]}
                break
        findings.append({"fixed_stud_center_ldu":list(center),"stud_cylindrical_body_checked":True,
                         "candidate_triangles":touched,"swept_surface_interference":threat,
                         "continuous_sweep_clear":threat is None})
    return findings

def main(ldraw):
    source=parse_b3()
    official=ensure_geometry_sources(ldraw)
    library=LDrawLibrary(ldraw)
    P={}
    for pid in IDS:
        row=source[pid]
        x=list(map(float,row[2:14]))
        part=library.load_part(row[-1])
        assert part.triangles
        P[pid]=instantiate(part,pid,transform_from_ldraw(x),int(row[1]))
    bottom,upper,roof=[P[x] for x in IDS]
    support_rel=check_collision(bottom,upper)
    support_conn=find_connections(bottom,upper)
    support_verdict=assess_pair(bottom,upper,relation=support_rel,connections=support_conn)

    # The slope has no built-in inferred connector because it is nonrectangular.
    # Candidate local underside points are measured from the official lower
    # boundary (y=24) at x±10,z=0; they are NOT inserted into engine globally.
    assert roof.definition.connectors==(), "unexpected slope connector source: review first"
    candidate_local=[(-10.,24.,0.),(10.,24.,0.)]
    underside=[roof.transform.point(v) for v in candidate_local]
    studs=[upper.transform.point(c.position) for c in upper.definition.connectors if c.type=="stud"]
    matched=[list(v) for v in underside if any(math.dist(v,q)<EPS for q in studs)]
    original_conn_count=len(matched)
    roof_rel=check_collision(roof,upper)
    roof_cross=first_mesh_crossing(roof,upper) if roof_rel is Relation.COLLISION else {
        "kind":"NO_RAW_MESH_COLLISION","relation":roof_rel.value}
    lower_rel=check_collision(roof,bottom)
    swept_studs=stud_clearance_sloped(roof,upper)
    threats=[v for v in swept_studs if not v["continuous_sweep_clear"]]
    # Non-stud body exclusion: upper is a box brick with top at Y=-864.
    # Entire roof remains above Y=-864 throughout descent. The only
    # possible overlapping Y-range is the true protruding studs [-868,-864].
    body_top_world=upper.transform.point((0,0,0))[1]
    roof_final_lower=roof.bbox.maximum[1]
    body_separate=roof_final_lower<=body_top_world+EPS
    start_clear=roof_final_lower-APPROACH<upper.bbox.minimum[1]-EPS
    support_start_clear=upper.bbox.maximum[1]-APPROACH<bottom.bbox.minimum[1]-EPS
    matched_roof=(original_conn_count>=1 and roof_rel is Relation.CONTACT
                  and lower_rel is Relation.SEPARATED and body_separate
                  and start_clear and not threats)
    connection="PASS" if matched_roof and support_verdict.verdict=="COMPATIBLE_MATING" else "NON DÉMONTRÉ"
    collision="PASS" if roof_rel is not Relation.COLLISION and lower_rel is not Relation.COLLISION and
                        support_rel is not Relation.COLLISION and not threats else "NON DÉMONTRÉ"
    support="PASS" if connection=="PASS" else "NON DÉMONTRÉ"
    insertion="PASS" if matched_roof and support_start_clear and support_verdict.verdict=="COMPATIBLE_MATING" else "NON DÉMONTRÉ"
    report_conn={
        "stud_cavity_source":official,
        "candidate_underside_centers_from_slope_lower_face":[list(v) for v in underside],
        "chimney_studs_from_official_3622":[list(q) for q in studs],
        "precisely_coincident_mating_centers":matched,
        "original_roof_pair":IDS[2]+" ↔ "+IDS[1],
        "original_roof_pair_nominal_match_count":original_conn_count,
        "roof_30363_not_whitelisted_globally":True,
        "support_pair":IDS[1]+" ↔ "+IDS[0],
        "support_pair_standard_stud_matches":len(support_conn),
        "support_pair_engine_verdict":support_verdict.verdict,
        "status":connection,
        "limitation":"Slope underside candidate centers require explicit clearance from actual full LDraw triangles; a center match alone does NOT demonstrate mating."}
    collision_report={
        "roof_vs_upper_support_mesh":roof_rel.value,
        "roof_vs_lower_support_mesh":lower_rel.value,
        "upper_vs_lower_support_mesh":support_rel.value,
        "roof_upper_strict_mesh_crossing":roof_cross,
        "full_continuous_slope_vs_support_stud_cylinder_sweep":swept_studs,
        "nonstud_body_max_roof_world_y":roof_final_lower,
        "upper_support_nominal_body_top_world_y":body_top_world,
        "roof_body_always_above_nominal_support_body":body_separate,
        "forbidden_intersection_evidence":threats,
        "status":collision}
    insertion_report={
        "motion":"LDraw vertical Y positive down; entire closed interval t in [0,1]; constant orientation",
        "order":IDS,
        "steps":[
            {"part":IDS[0],"start_xyz":[950,-888,630],"target_xyz":[950,-840,630],"approach_ldu":48,"root":"local chimney lower course only; global foundation NOT PROVEN"},
            {"part":IDS[1],"start_xyz":[950,-912,630],"target_xyz":[950,-864,630],"approach_ldu":48,
             "start_clear":support_start_clear,"joint":support_verdict.verdict,
             "rigorous_sweep":"rectangular upright brick stud primitive, as bounded in VALIDATION2"},
            {"part":IDS[2],"start_xyz":[970,-936,620],"target_xyz":[970,-888,620],"approach_ldu":48,
             "start_clear":start_clear,"body_separate_for_all_t":body_separate,
             "stud_sweep_clear_for_all_t":not threats,
             "joint":"PASS" if matched_roof else "NON DÉMONTRÉ"}],
        "continuous_check_not_sampled":True,
        "status":insertion}
    final={"original_roof_id":IDS[2],"original_roof_ref":"30363.dat",
           "original_support_id":IDS[1],"base_support_id":IDS[0],
           "original_roof_connection":"PASS" if connection=="PASS" else "NON DÉMONTRÉ",
           "variant_necessary":"NON" if connection=="PASS" else "NON DÉMONTRÉ",
           "additional_pieces":0,"additional_refs":[],
           "collisions":collision,"local_support_chain":support,
           "support_to_house_foundations":"NON DÉMONTRÉ",
           "insertion":insertion,"visualization":"NON DÉMONTRÉ until Chromium test",
           "whole_roof_408_parts":"NOT_TESTED",
           "overall":"PASS" if connection==collision==support==insertion=="PASS" else "NON DÉMONTRÉ",
           "first_blocker":next(({"stud_center":v["fixed_stud_center_ldu"],
                      "triangle":v["swept_surface_interference"]} for v in threats),None),
           "physical_mechanical_stability":"NON DÉMONTRÉ",
           "source_fidelity":"3 original placement records exact, source PR931 read only",
           "limits":["Slope geometry 18° only; 22° architectural pitch not certified.",
                     "Viewer is simplified visual proxy; proof uses official pinned triangulated LDraw shape.",
                     "No full-house support to foundations, no strength/force/tolerances, no neighboring roof pieces validated."]}
    dump("CONNEXIONS.json",report_conn)
    dump("COLLISIONS.json",collision_report)
    dump("INSERTION.json",insertion_report)
    dump("RESULTAT.json",final)
    print("TOITURE1_MEASURED="+json.dumps({k:final[k] for k in
        ("original_roof_connection","collisions","local_support_chain","insertion","overall","first_blocker")},ensure_ascii=False),flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--ldraw-root",type=Path,required=True)
    main(p.parse_args().ldraw_root)
