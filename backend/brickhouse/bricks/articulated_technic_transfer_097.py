"""097 — EXACT articulated double-link 32017, not a fitted rigid 32524.

Two genuine half-thickness Technic beams (32017.dat, 5 holes, 4M
hole-to-hole each) connect one roof brick 3700 to an existing pinned 32278
rafter. A third 2780 forms an elbow whose point comes from the intersection
of two circles of radius 80 LDU. All 3 joint axes coincide without invoking
a factory tolerance for 096's 0.0507923 LDU discrepancy.

IMPORTANT: a free elbow is a mobile linkage, NOT a moment-resisting or
compression-stable truss. N2 interface layout is explicit, but no N4/N6 load
capacity and no complete swept assembly proof are inferred.
"""
from __future__ import annotations
from collections import Counter
from math import hypot,sqrt,isclose
from .roof_technic_transfer_096 import build_096, _roof_bracket, _frame_rafter_holes
from .technic_triangle_095 import beam_matrix,pin,screen_technic_roof_clearance
from .articulated_roof_093 import rigid

LINK_ID="32017"
LINK_HOLE_STEP=20.
LINK_HOLES=5
LINK_RADIUS=80.
# LDraw part 32017 has thickness 10 LDU, half of 32524's 20.
THIN_HALF=5.
PIN_NOMINAL_RADIUS=6.
NO_IMPLIED_TOLERANCE=1e-5

def circle_elbows(a,b,radius=LINK_RADIUS):
    dx,dy=b[0]-a[0],b[1]-a[1]
    d=hypot(dx,dy)
    if d>=2*radius or d<1e-9:
        return []
    h=sqrt(radius*radius-(d/2)**2)
    mx,my=(a[0]+b[0])/2,(a[1]+b[1])/2
    return [(mx+s*(-dy/d)*h,my+s*(dx/d)*h) for s in (1,-1)]

def thin_liftarm(a,b,z,name):
    dx,dy=b[0]-a[0],b[1]-a[1]
    distance=hypot(dx,dy)
    if abs(distance-LINK_RADIUS)>1e-5:
        raise ValueError("REAL_32017_IS_FIVE_HOLES_FOUR_INTERVALS")
    ux,uy=dx/distance,dy/distance
    center=(a[0]+dx/2,a[1]+dy/2,z)
    part=rigid(name,LINK_ID,center,beam_matrix((ux,uy)),
               "truss097_real_technic_thin_beam")
    holes=[(round(a[0]+i*ux*20.,7),
            round(a[1]+i*uy*20.,7),z) for i in range(5)]
    return part,holes

def check_three_axial_stacks(bracket,rafter,link1,link2):
    # Existing roof 3700 and existing 095 rafter: thick 20-LDU sections.
    # 32017: real thin 10-LDU beam. Adjacent, never same-depth at a joint.
    z0=bracket[2]
    z3=rafter[2]
    if abs(z3-z0-40.)>1e-5:
        raise ValueError("SANDWICH_DATUM_NOT_FOUR_STUD_HALVES")
    if abs(link1-z0-15)>1e-5 or abs(link2-link1-10)>1e-5:
        raise ValueError("THIN_BEAMS_NOT_STACKED_IN_ADJACENT_HALVES")
    sections=[
        [("3700",z0,10.),("32017-A",link1,5.)],
        [("32017-A",link1,5.),("32017-B",link2,5.)],
        [("32017-B",link2,5.),("32278",z3,10.)]]
    result=[]
    for i,stack in enumerate(sections):
        p,q=stack
        clearance=q[1]-q[2]-(p[1]+p[2])
        if abs(clearance)>1e-6:
            raise AssertionError("BEAMS_NOT_FACE_ADJACENT_NO_REAL_PIN")
        result.append({"joint":i,"faces_touch_exactly":True,
                       "plane_gap_ldu":round(clearance,7),
                       "cross_section_ldu":[2*p[2],2*q[2]],
                       "through_pin":"2780",
                       "pin_collar_must_occupy_exact_face":True,
                       "pin_sweep_not_certified":True})
    return result

def _nearby_frame_technics(frame_no,parts):
    return [p for p in parts if p["placement_id"].startswith(f"095-F{frame_no}-")
            and p["ldraw_id"] in ("32278","32524")]

def construct_one_exact_joint_chain(previous,frame_no=0):
    """Replace ONLY one 096 rigid near-miss. Preserve second test candidate."""
    records=previous["report"]["candidate_details"]
    trial=next((x for x in records if x["frame"]==frame_no),None)
    new_roof_3700 = None
    if trial is None or "roof_hole_world" not in trial:
        # Alternate houses need not inherit a 096 near-miss. Design first.
        frames=previous["previous_095"]["report"]["triangles"]
        frame=next((f for f in frames if f["frame"]==frame_no),None)
        if frame is None or frame["grounded_wall_pin_count"]!=2:
            raise ValueError("NO_GROUNDED_FRAME_WITH_ROOF_STUD_CONNECTION")
        bracket,reason=_roof_bracket(frame,previous["articulated_parts"])
        if reason:
            raise ValueError("NO_ACTUAL_ROOF_RAIL_FOR_STUD_BRACKET")
        hole=bracket["hole"]
        holes=_frame_rafter_holes(frame)
        viable=[(abs(hypot(hole[0]-pt[0],hole[1]-pt[1])-120.),
                 k,pt) for k,pt in enumerate(holes)
                if 1<k<13 and hypot(hole[0]-pt[0],hole[1]-pt[1])<2*LINK_RADIUS]
        if not viable:
            raise ValueError("NO_TWO_REAL_THIN_LINKS_CAN_REACH")
        _,k,pt=min(viable)
        trial={"frame":frame_no,"bay":frame["bay"],
               "roof_hole_world":hole,"rafter_hole_world":pt,
               "rafter_hole_index":k,
               "axis_residual_ldu":round(abs(hypot(hole[0]-pt[0],hole[1]-pt[1])-120.),7)}
        new_roof_3700=bracket["part"]
    elif trial["axis_residual_ldu"] <= 1e-7:
        raise ValueError("NO_NONZERO_RESIDUAL_TO_REPLACE")
    A=tuple(trial["roof_hole_world"])
    B=tuple(trial["rafter_hole_world"])
    elbows=circle_elbows(A,B)
    if not elbows:raise ValueError("REAL_THIN_2LINK_SPAN_OUT_OF_RANGE")
    old=previous["articulated_parts"]
    legacy=[
        f"096-F{frame_no}-brace-7-hole",
        f"096-F{frame_no}-pin-at-roof-2780",
        f"096-F{frame_no}-pin-at-rafter-2780"]
    found={p["placement_id"]:p for p in old}
    removed=legacy if all(i in found for i in legacy) else []
    if removed and found[legacy[0]]["ldraw_id"]!="32524":
        raise AssertionError("WRONG_096_BRACE_FAMILY")
    if new_roof_3700 is not None and new_roof_3700["placement_id"] in found:
        raise AssertionError("DOUBLE_REAL_ROOF_BRACKET")
    z0=A[2]; z3=B[2]
    l1=z0+15; l2=l1+10
    layers=check_three_axial_stacks(A,B,l1,l2)
    # Lower/inside elbow minimizes crossing the external roof plane.
    E=max(elbows,key=lambda p:p[1])
    pa,h1=thin_liftarm(A,E,l1,f"097-F{frame_no}-roof-to-elbow-32017")
    pb,h2=thin_liftarm(E,B,l2,f"097-F{frame_no}-elbow-to-frame-32017")
    if hypot(h1[-1][0]-h2[0][0],h1[-1][1]-h2[0][1])>NO_IMPLIED_TOLERANCE:
        raise AssertionError("ELBOW_NOT_EXACTLY_COAXIAL")
    ids=[f"097-F{frame_no}-roof-pin-2780",
         f"097-F{frame_no}-elbow-pin-2780",
         f"097-F{frame_no}-frame-pin-2780"]
    joints=[pin(ids[0],A[0],A[1],z0+10,False),
            pin(ids[1],E[0],E[1],z0+20,False),
            pin(ids[2],B[0],B[1],z0+30,False)]
    added=([new_roof_3700] if new_roof_3700 else [])+[pa,pb,*joints]
    bridge=[f"096-F{frame_no}-roof-3700",pa["placement_id"],
            joints[0]["placement_id"],joints[1]["placement_id"],
            pb["placement_id"],joints[2]["placement_id"],
            f"095-F{frame_no}-rafter-left"]
    # N2 graph: real joint families and centers; N5 only planned at this stage.
    edges=([
      {"from":f"093-negative-baseplate-{trial['bay']}-0-16",
       "to":new_roof_3700["placement_id"],
       "interface":"STANDARD_TWO_STUD_TO_3460_ANTISTUD",
       "axis_exact":True}] if new_roof_3700 else [])+[
       {"from":f"096-F{frame_no}-roof-3700","to":ids[0],
        "interface":"REAL_3700_HOLE_TO_2780","axis_exact":True},
       {"from":ids[0],"to":pa["placement_id"],
        "interface":"REAL_2780_TO_32017_HOLE0","axis_exact":True},
       {"from":pa["placement_id"],"to":ids[1],
        "interface":"REAL_32017_HOLE4_TO_2780","axis_exact":True},
       {"from":ids[1],"to":pb["placement_id"],
        "interface":"REAL_2780_TO_32017_HOLE0","axis_exact":True},
       {"from":pb["placement_id"],"to":ids[2],
        "interface":"REAL_32017_HOLE4_TO_2780","axis_exact":True},
       {"from":ids[2],"to":f"095-F{frame_no}-rafter-left",
        "interface":f"REAL_2780_TO_32278_HOLE{trial['rafter_hole_index']}",
        "axis_exact":True}]
    # True 2L pin collar sits between the actual adjoining part faces.
    assert all(v["faces_touch_exactly"] for v in layers)
    err=max(hypot(h1[0][0]-A[0],h1[0][1]-A[1]),
            hypot(h2[-1][0]-B[0],h2[-1][1]-B[1]),
            hypot(h1[-1][0]-h2[0][0],h1[-1][1]-h2[0][1]))
    if err>NO_IMPLIED_TOLERANCE:
        raise AssertionError("DOUBLE_LINK_HAS_NONZERO_FINAL_PIN_RESIDUAL")
    return {"frame":frame_no,"bay":trial["bay"],"part_ids":bridge,
            "new_parts":added,"remove_ids":removed,"edges":edges,
            "roof_hole":A,"frame_hole":B,"elbow_hole_xy":E,
            "hinge_joint_count":3,"hole_axis_residual_max_ldu":round(err,8),
            "legacy_096_replaced":bool(removed),
            "three_axial_stack_evidence":layers,
            "roof_angle_deg":22.0,"truss_angle_deg":previous["report"]["technic_truss_pitch_degrees"],
            "kinematics":"TWO_LINK_1_DOF_UNBRACED_ELBOW",
            "compression_stable":False,"pin_full_sweep_verified":False,
            "collar_path_free_verified":False,
            "load_path_graph_N2":True,"loaded_support_path_N4":False}

def build_097(source,frame_no=0):
    original=source.model_dump_json()
    prev=build_096(source)
    assembled=construct_one_exact_joint_chain(prev,frame_no)
    removed=set(assembled["remove_ids"])
    before=prev["articulated_parts"]
    now=[p for p in before if p["placement_id"] not in removed]+assembled["new_parts"]
    ids=[p["placement_id"] for p in now]
    if len(ids)!=len(set(ids)):raise AssertionError("DUPLICATE_LDRAW_PIECES")
    graph=[x for x in prev["graph"]
           if x.get("from") not in removed and x.get("to") not in removed]
    graph+=assembled["edges"]
    delta=Counter(p["ldraw_id"] for p in assembled["new_parts"])
    sub=Counter(p["ldraw_id"] for p in before if p["placement_id"] in removed)
    screened=screen_technic_roof_clearance(
        [p for p in assembled["new_parts"] if p["ldraw_id"] in ("32278","32524")],
        before)
    if source.model_dump_json()!=original:
        raise AssertionError("ORIGINAL_VARIANT_MUTATED")
    report={
        "previous_096_parts":prev["report"]["new_total"],
        "new_total":len(prev["foundation"].parts)+len(now),
        "removed_actual_ids":assembled["remove_ids"],
        "added_real_parts_by_ldraw":dict(delta),
        "removed_real_parts_by_ldraw":dict(sub),
        "frames":prev["report"]["technic_frames"],
        "two_walls_grounded_frames":prev["report"]["grounded_two_wall_frames"],
        "unanchored_frames":prev["report"]["frames_still_without_two_wall_anchors"],
        "geometrically_exact_roof_to_truss_to_wall_connector_chains":1,
        "mechanically_stable_roof_to_wall_load_paths":0,
        "removed_096_numerical_mismatch_ldu":0.0507923,
        "new_max_joint_residual_ldu":assembled["hole_axis_residual_max_ldu"],
        "new_2780_nominal_pin_stacks":3,
        "complete_insertion_sweeps_verified":0,
        "true_pin_collar_mesh_verified":False,
        "kinematically_stable":False,
        "roof_pitch_degrees":22.,
        "exterior_panels_unmodified":True,
        "collision_screen_new_pieces_limited":screened,
        "n1_real_parts":True,"n2_interface_axis_geometry":True,
        "n3_global_3d_collisions":False,"n4_stability":False,
        "n5_full_insertion":False,"n6_strength":False,
        "physical_certification":"NOT_CERTIFIED",
        "structural_decision":"CHANGE_ARCHITECTURE_OR_BRACE_1DOF_ELBOW_BEFORE_097_MERGE",
        "subassembly":{k:v for k,v in assembled.items() if k!="new_parts"}
    }
    return {"foundation":prev["foundation"],"articulated_parts":now,
            "new_subassembly":assembled,"graph":graph,"report":report,
            "previous_096":prev}
