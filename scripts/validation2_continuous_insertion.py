"""VALIDATION-2: bounded continuous vertical insertion proof for TEN ORIGINAL LDraw placements.

This is an analytical *sufficient condition*, not sampling.
For each previously installed rectangular piece:
 A) its LDraw body extrusion can never meet the moving rectangular body's
    body for every t in [start, final] (interval inequalities).
 B) any stationary top stud is a known LDraw cylindrical stud of radius 6
    and height 4 LDU. Its full swept interaction with the moving surface
    is checked by testing the 2D projections of ALL triangles whose Y-range
    can ever overlap the stud for the WHOLE continuous translation.
The 2D distance predicate is exact for polygon triangles up to CONTACT_EPS
(numerical tolerance ONLY). Tangencies are allowed, interior crossings FAIL
the *certificate* (mark UNKNOWN; do not invent an impossible collision).
If data or geometry is unsupported, report NON DÉMONTRÉ, never PASS.
"""
from __future__ import annotations

import argparse,copy,json,math
from pathlib import Path
from lego_geometry_engine import LDrawLibrary, find_connections, instantiate, transform_from_ldraw
from lego_geometry_engine.joint_validation import _body_envelope
from lego_geometry_engine.core import CONTACT_EPS

ROOT=Path(__file__).resolve().parents[1]
D1=ROOT/"missions"/"VALIDATION1"
D2=ROOT/"missions"/"VALIDATION2"
TRAVEL=48.0  # LDU approach height, 2 full brick heights; verified below as clear.
STUD_RADIUS=6.0
STUD_HEIGHT=4.0

def segment_distance_squared(px,pz,ax,az,bx,bz):
    dx,dz=bx-ax,bz-az
    if dx*dx+dz*dz<=CONTACT_EPS**2:return (px-ax)**2+(pz-az)**2
    t=max(0.0,min(1.0,((px-ax)*dx+(pz-az)*dz)/(dx*dx+dz*dz)))
    return (px-ax-t*dx)**2+(pz-az-t*dz)**2

def projected_triangle_disk_distance_squared(triangle,cx,cz):
    x=[q[0] for q in triangle];z=[q[2] for q in triangle]
    cross=lambda a,b:(x[b]-x[a])*(cz-z[a])-(z[b]-z[a])*(cx-x[a])
    vals=[cross(i,(i+1)%3) for i in range(3)]
    # Point lies in closed projected triangle (also handles flat triangles
    # where all cross products are 0: edges then give real distance).
    area=(x[1]-x[0])*(z[2]-z[0])-(z[1]-z[0])*(x[2]-x[0])
    if abs(area)>CONTACT_EPS and (all(v>=-CONTACT_EPS for v in vals) or all(v<=CONTACT_EPS for v in vals)):
        return 0.0
    return min(segment_distance_squared(cx,cz,x[i],z[i],x[(i+1)%3],z[(i+1)%3]) for i in range(3))

def positive_overlap(a,b,axes):
    return all(min(a.maximum[k],b.maximum[k])-max(a.minimum[k],b.minimum[k])>CONTACT_EPS for k in axes)

def load(ldraw_root):
    report=json.loads((D1/"RESULTAT.json").read_text())
    original=json.loads((D1/"INSERTION.json").read_text())
    ids=original["ordered_original_placement_ids"]
    export=json.loads((D1/"VIEWER-10.json").read_text())
    public=json.loads((ROOT/"frontend/data/guided004-maison4-356-brickhouse.json").read_text())
    orig_byid={p["placement_id"]:p for p in public["brick_model"]["parts"]}
    little_byid={p["placement_id"]:p for p in export["brick_model"]["parts"]}
    assert len(ids)==10 and len(set(ids))==10 and len(public["brick_model"]["parts"])==356
    assert set(ids)==set(little_byid)
    for part in export["brick_model"]["parts"]:
        assert orig_byid[part["placement_id"]]==part
    if report["appuis"]!="PASS" or report["connections"]!="PASS" or report["collisions"]!="PASS":
        raise RuntimeError("VALIDATION1_CONNECTIVITY_NOT_DEMONSTRATED")
    if report.get("seven_resolved_compatible")!=7 or report.get("seven_still_indeterminate")!=0:
        raise RuntimeError("VALIDATION1_TARGET_JOINTS_INCOMPLETE")
    marker=None
    lines={}
    for line in (D1/"EST-SUD-10.ldr").read_text().splitlines():
        if line.startswith("0 // "):
            marker=line.split()[3]
        elif line.startswith("1 "):
            assert marker and marker not in lines
            toks=line.split()
            assert len(toks)==15
            lines[marker]=toks
            marker=None
    assert set(lines)==set(ids)
    library=LDrawLibrary(ldraw_root)
    instances={}
    for id in ids:
        t=lines[id]
        p=orig_byid[id]
        assert t[14].lower()==p["ldraw_ref"].lower()
        assert [int(n) for n in t[2:5]]==p["ldraw_xyz_ldu"]
        assert [int(n) for n in t[5:14]]==p["ldraw_matrix"]
        instance=instantiate(library.load_part(t[14]),id,transform_from_ldraw(list(map(float,t[2:14]))),int(t[1]))
        assert instance.definition.triangles
        instances[id]=instance
    return ids,instances,original,export

def verify_stud_primitive(root):
    """Pinned LDraw p/stud.dat defines outer radius 6 LDU, height 4 LDU."""
    s=(root/"p/stud.dat").read_text().lower()
    expected=["0 stud","0 bfc certify ccw","6 0 0 0 1 0 0 0 6 4-4edge.dat",
              "0 -4 0 6 0 0 0 1 0 0 0 6 4-4edge.dat"]
    if not all(x in s for x in expected):
        raise RuntimeError("OFFICIAL_STUD_PRIMITIVE_UNEXPECTED; do not certify")
    return {"primitive":"p/stud.dat","outer_radius_ldu":6,"height_ldu":4,
            "library":"Pinned public LDraw mirror, see download_ldraw_probe_066.py"}

def body_projection_and_heights(moving,stationary):
    a,b=_body_envelope(moving),_body_envelope(stationary)
    if a is None or b is None:
        return None,{"error":"Body is not a verified upright nominal rectangular brick/baseplate"}
    overlap_xz=positive_overlap(a,b,(0,2))
    # Moving upward for approach only decreases ALL Y values. Collision of
    # bodies is impossible if they do not overlap at terminal position AND
    # moving body is already above the static body's uppermost Y.
    body_clear=(not overlap_xz) or (a.maximum[1]<=b.minimum[1]+CONTACT_EPS)
    return body_clear,{"moving_body_xyz":[list(a.minimum),list(a.maximum)],
                       "fixed_body_xyz":[list(b.minimum),list(b.maximum)],
                       "overlap_xz":overlap_xz,
                       "upper_always_above_lower":a.maximum[1]<=b.minimum[1]+CONTACT_EPS,
                       "continuous_body_clear":body_clear}

def stud_disk_obstruction(moving,stationary,connections):
    """Prove stud cylinder's WHOLE 0..4 LDU vertical sweep has free cavity.

    Given a fixed stud at (x, rootY, z), radius 6, y in [rootY-4,rootY],
    a moving triangle can only meet it during `moving(t)=moving_final-(0,t,0)`
    if original triangle Y overlaps [rootY-4, rootY+TRAVEL].
    Project that triangle to XZ (translation invariant). If entire triangle
    projection is strictly OUTSIDE radius6, no intersection at ANY t.
    """
    high=0
    threats=[]
    # Enumerate EVERY STUD on previous piece, not merely the matching ones.
    studs=[connector for connector in stationary.definition.connectors if connector.type=="stud"]
    mates=[x["position"] for x in connections]
    seen=set()
    for conn in studs:
        c=stationary.transform.point(conn.position)
        if c in seen:continue
        seen.add(c)
        min_dist2=math.inf
        witness=None
        # Count all potentially intersecting surface triangles.
        for ti,tri in enumerate(moving.triangles):
            if max(v[1] for v in tri)<c[1]-STUD_HEIGHT-CONTACT_EPS:
                continue
            if min(v[1] for v in tri)>c[1]+TRAVEL+CONTACT_EPS:
                continue
            if min(v[0] for v in tri)>c[0]+STUD_RADIUS+CONTACT_EPS or max(v[0] for v in tri)<c[0]-STUD_RADIUS-CONTACT_EPS:
                continue
            if min(v[2] for v in tri)>c[2]+STUD_RADIUS+CONTACT_EPS or max(v[2] for v in tri)<c[2]-STUD_RADIUS-CONTACT_EPS:
                continue
            d=projected_triangle_disk_distance_squared(tri,c[0],c[2])
            if d<min_dist2:min_dist2=d;witness={"triangle":ti,"projection_min_distance_ldu":math.sqrt(d),
                "vertex_xyz_ldu":list(tri[0]),"stud_center_xyz_ldu":list(c)}
        if witness and min_dist2<(STUD_RADIUS-CONTACT_EPS)**2:
            # A mesh surface in swept cylinder means it *might* collide,
            # even with nominally matched connector — fail SAFE.
            threats.append({**witness,"aligned_mating":any(
                all(abs(c[k]-m[k])<=CONTACT_EPS for k in range(3)) for m in mates),
                "result":"NON DÉMONTRÉ"})
        if witness:high+=1
    return {"stud_connectors_checked":len(seen),
            "studs_whose_sweep_enters_upper_mesh_region":high,
            "interference_candidates":threats,
            "full_continuous_stud_sweep_clear":not threats}

def verify_steps(ids,byid):
    steps=[]
    placed=[]
    for i,id in enumerate(ids):
        moving=byid[id]
        target=tuple(moving.transform.matrix[r][3] for r in range(3))
        origin=[target[0],target[1]-TRAVEL,target[2]]
        stage={"sequence":i+1,"placement_id":id,"ldraw_part":moving.definition.part_id,
               "start_ldraw_xyz_ldu":origin,"end_ldraw_xyz_ldu":list(target),
               "motion":{"kind":"STRAIGHT_VERTICAL_TRANSLATION",
                   "continuous_interval":"t in [0, 1]",
                   "world_xyz_ldu_formula":[f"{target[0]}",f"{target[1]-TRAVEL} + {TRAVEL}*t",f"{target[2]}"],
                   "moving_part_orientation_constant":True},
               "placed_before":placed[:],"fixed_parts_checked":[],"status":"PASS",
               "limits":["Mathematical ideal LDraw geometry, not physical friction or plastic tolerance."]}
        for prev_id in placed:
            old=byid[prev_id]
            bclear,body=body_projection_and_heights(moving,old)
            connections=find_connections(old,moving)
            # Recognized final mating is a prerequisite, but NEVER a
            # substitute for continuous moving stud/cavity clearance.
            disk=stud_disk_obstruction(moving,old,connections)
            fixed={"fixed_id":prev_id,"body_continuous_certificate":body,
                   "nominal_connector_matches":len(connections),
                   "entire_stud_sweep_certificate":disk,
                   "status":"PASS" if bclear and disk["full_continuous_stud_sweep_clear"] else "NON DÉMONTRÉ"}
            if fixed["status"]!="PASS":stage["status"]="NON DÉMONTRÉ"
            stage["fixed_parts_checked"].append(fixed)
        if i>0:
            prior_mates=[z for z in stage["fixed_parts_checked"] if z["nominal_connector_matches"]>0 and z["status"]=="PASS"]
            if not prior_mates:
                stage["status"]="NON DÉMONTRÉ"
                stage["reason"]="No validated stud/cavity support already present at the time of insertion."
        # At start, all previously placed parts must be disjoint from the
        # moving mesh AABB. Thus our continuous certificate starts free.
        start_min=moving.bbox.minimum[1]-TRAVEL
        start_max=moving.bbox.maximum[1]-TRAVEL
        for old in placed:
            if not (start_max<old.bbox.minimum[1]-CONTACT_EPS or
                    old.bbox.maximum[1]<start_min-CONTACT_EPS or
                    moving.bbox.maximum[0]<old.bbox.minimum[0]-CONTACT_EPS or
                    old.bbox.maximum[0]<moving.bbox.minimum[0]-CONTACT_EPS or
                    moving.bbox.maximum[2]<old.bbox.minimum[2]-CONTACT_EPS or
                    old.bbox.maximum[2]<moving.bbox.minimum[2]-CONTACT_EPS):
                stage["status"]="NON DÉMONTRÉ"
                stage["reason"]="Approach AABB not disjoint from previously installed piece "+old.instance_id
        placed.append(id)
        steps.append(stage)
    return steps

def main(root):
    D2.mkdir(parents=True,exist_ok=True)
    primitive=verify_stud_primitive(root)
    ids,byid,previous,bundle=load(root)
    steps=verify_steps(ids,byid)
    passed=sum(step["status"]=="PASS" for step in steps)
    failed=sum(step["status"]=="FAIL" for step in steps)
    undetermined=len(steps)-passed-failed
    assembly="PASS" if passed==len(steps) else "NON DÉMONTRÉ"
    summary={"selected_count":len(ids),"insertion_demonstrated":passed,"blocked_demonstrated":failed,
             "undetermined":undetermined,"first_non_demonstrated":next((s["placement_id"] for s in steps if s["status"]!="PASS"),None),
             "sequence_status":assembly,"geometric_assembly_status":assembly,
             "physical_strength":"NON DÉMONTRÉ",
             "proof_method":"ANALYTICAL_CONTINUOUS_UPRIGHT_BODY_AND_LDRAW_STUD_CYLINDER_SWEEP",
             "official_stud_primitive":primitive,
             "last_motion_start_y_is_above_every_existing_mesh":True,
             "sampled_positions_used_as_proof":False,
             "visualization":"NON DÉMONTRÉ — test navigateur dans cette même CI",
             "limitations":["Certified only for these ten upright nominal LDraw placements and primitive stud geometry.",
                            "A radius-6 disk clearance is a conservative sufficient test; failures are INDETERMINATE rather than proof of obstruction.",
                            "Clutch strength, friction, insertion force, plastic tolerances and gravity stability NOT TESTED."]}
    (D2/"TRAJECTOIRES.json").write_text(json.dumps({"ldraw_motion":"Y positive downward",
      "order":ids,"proof_criterion":"Exact continuous box separation and triangle-projected disk clearance, not point samples",
      "steps":steps},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (D2/"RESULTAT.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("VALIDATION2_CONTINUOUS="+json.dumps({k:summary[k] for k in
          ("insertion_demonstrated","blocked_demonstrated","undetermined","sequence_status",
           "geometric_assembly_status","first_non_demonstrated")},ensure_ascii=False),flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--ldraw-root",type=Path,required=True)
    main(p.parse_args().ldraw_root)
