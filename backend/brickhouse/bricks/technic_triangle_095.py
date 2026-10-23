"""LEGO2-095 — pin-closed real Technic 5:12:13 A-frame.

The first documented closure is built with official 32278 (15-hole liftarms),
32524 (7-hole center kingpost), and 6558 (3L friction pins). Each vertex
uses holes actually present in the source LDraw definitions, at their REAL
20-LDU spacing, with a real pin traversing precisely three neighbouring
thick beam planes. No fictional stud/hinge contacts.

A closed triangle is *not* a certified beam-to-wall connection. Each house
frame carries a separate wall_anchor verdict and roofing contact verdict.
"""
from __future__ import annotations
from collections import Counter,deque
from math import hypot,sin,cos,radians,atan2
from .triangular_frame_ridge_094 import build_094
from .articulated_roof_093 import rigid,PARTS
from .catalog import standard_orthogonal_definitions
from .roof_studdeck_designer_091 import _cells
from .roof_collision_093 import envelope_intersect,roof_obb

STUD=20.
FRAME_RISE=5
FRAME_HALF=12
FRAME_DIAGONAL=13
PARTS095={
    "32278":("TECHNIC_BEAM_15_HOLES",15,1),
    "32524":("TECHNIC_BEAM_7_HOLES",7,1),
    "6558":("TECHNIC_PIN_3L_FRICTION",3,1),
    "2780":("TECHNIC_PIN_2L_FRICTION",2,1),
    "3700":("TECHNIC_BRICK_1X2_WITH_HOLE",2,1),
    "3004":("BRICK_1X2",2,1),
    "3023b":("PLATE_1X2",2,1),
}
PARTS.update(PARTS095)
D=standard_orthogonal_definitions()
PIN_MATRIX=((1.,0.,0.),(0.,0.,-1.),(0.,1.,0.))
I=((1.,0.,0.),(0.,1.,0.),(0.,0.,1.))


def beam_matrix(direction):
    """LDraw 32278/32524 length LOCAL Z, pin holes along LOCAL X.
    Map the holes to a roof transverse XY frame; local X is world Z.
    """
    dx,dy=direction
    if abs(hypot(dx,dy)-1)>1e-8:
        raise ValueError("NON_UNIT_LIFTARM_DIRECTION")
    return ((0.,dy,dx),(0.,-dx,dy),(1.,0.,0.))


def beam(start,direction,depth,holes,partid,name):
    # Official LDraw 32278: 15 hole centers z=-140..+140.
    # Official LDraw 32524: 7 hole centers z=-60..+60.
    assert (holes,partid) in ((15,"32278"),(7,"32524"))
    h=(holes-1)/2.
    xyz=(start[0]+direction[0]*h*STUD,
         start[1]+direction[1]*h*STUD,depth)
    p=rigid(name,partid,xyz,beam_matrix(direction),"truss095_technic_beam")
    hole_centers=[]
    for i in range(holes):
        c=(round(start[0]+direction[0]*i*STUD,7),
           round(start[1]+direction[1]*i*STUD,7),round(depth,7))
        hole_centers.append(c)
    return p,hole_centers


def pin(name,x,y,z,three=True):
    code="6558" if three else "2780"
    return rigid(name,code,(x,y,z),PIN_MATRIX,"truss095_technic_pin")


def complete_technic_frame(*,index,bay,xcenter,eave_y,ridge_y,
                            anchor_points,with_wall_anchors=True):
    """One genuine closed A, two 5/12/13 right triangles joined at the post.

    All five liftarms sit in three adjacent pin planes: -20,0,+20 LDU.
    A 3L pin traverses 60 LDU to engage all three thick liftarms.
    Frames are centered 20 LDU between 093 roof-module seams.
    """
    mid=xcenter*STUD
    foot_y=eave_y-44.0 # leaves 22° roof free above the frame
    apex_y=foot_y-FRAME_RISE*STUD
    z=(bay+1.5)*STUD
    names=lambda tail:f"095-F{index}-{tail}"
    parts=[];holemap={};links=[];checks=[];blocked=[]
    def add_beam(alias,start,d,depth,holes,ldraw):
        p,centers=beam(start,d,z+depth,holes,ldraw,names(alias))
        parts.append(p);holemap[p["placement_id"]]=centers
        return p["placement_id"]
    A=(mid-FRAME_HALF*STUD,foot_y)
    B=(mid+FRAME_HALF*STUD,foot_y)
    C=(mid,foot_y)
    TOP=(mid,apex_y)
    tl=add_beam("tie-left",A,(1.,0.),-20,15,"32278")
    tr=add_beam("tie-right",B,(-1.,0.),20,15,"32278")
    rl=add_beam("rafter-left",A,(FRAME_HALF/FRAME_DIAGONAL,
                             -FRAME_RISE/FRAME_DIAGONAL),20,15,"32278")
    rr=add_beam("rafter-right",B,(-FRAME_HALF/FRAME_DIAGONAL,
                             -FRAME_RISE/FRAME_DIAGONAL),-20,15,"32278")
    post=add_beam("kingpost",C,(0.,-1.),0,7,"32524")
    vertices=[
      ("LEFT_FOOT",A,[(tl,0),(rl,0)]),
      ("RIGHT_FOOT",B,[(tr,0),(rr,0)]),
      ("APEX",TOP,[(rl,13),(rr,13),(post,5)]),
      ("CENTER_TIE",C,[(tl,12),(tr,12),(post,0)])]
    def add_joint(label,pt,members):
        picked=[holemap[p][i] for p,i in members]
        if any(abs(v[0]-pt[0])>1e-5 or abs(v[1]-pt[1])>1e-5
               for v in picked):
            raise AssertionError("TECHNIC_HOLES_NOT_COAXIAL")
        depth=sorted(set(v[2] for v in picked))
        expected=sorted(set([z-20.,z+20.] if len(members)==2
                            else [z-20.,z,z+20.]))
        if depth!=expected:
            raise AssertionError("TECHNIC_PIN_THREE_LAYER_LAYOUT_INVALID")
        p=pin(names("pin-"+label),pt[0],pt[1],z,True)
        parts.append(p)
        for bid,hole_no in members:
            links.append({"from":bid,"to":p["placement_id"],
                          "hole_index":hole_no,
                          "interface":"ACTUAL_LDRAW_32278_32524_HOLE_TO_REAL_6558_3L_PIN",
                          "documented_type":True,
                          "exact_hole_axis_verified":True,
                          "friction_strength_unverified":True})
        checks.append({"vertex":label,"pin":p["placement_id"],
                       "beam_ids":[q for q,_ in members],
                       "hole_centers_ldu":picked,"pin_axis":"WORLD_Z",
                       "all_holes_coaxial":True,
                       "pin_6558_spans_3L":True})
    for label,pt,members in vertices:add_joint(label,pt,members)
    # This creates TWO actual closed cycles, not the old 094 drawn vertices.
    # One shares the bottom-center joint and kingpost with the other.
    adj={}
    for check in checks:
        ids=check["beam_ids"]
        for a in ids:
            adj.setdefault(a,set()).update(set(ids)-{a})
    def closure(edges):
        return all(b in adj.get(a,set()) for a,b in edges)
    left_closed=closure([(tl,rl),(rl,post),(post,tl)])
    right_closed=closure([(tr,rr),(rr,post),(post,tr)])
    if not(left_closed and right_closed):
        raise AssertionError("TRIANGLE_PIN_GRAPH_NOT_CLOSED")
    # Existing 093 roof geometry is preserved. Extensions are placed under
    # the same upper floor; whether they actually bear on walls is SEPARATE.
    anchoring=[]
    for side,foot in (("negative",A),("positive",B)):
        anchor_x=anchor_points[side]*STUD
        diff=(foot[0]-anchor_x)/STUD
        length=abs(diff)
        if abs(length-round(length))>1e-6 or not 1<=length<=14:
            blocked.append({"side":side,"reason":"NO_INTEGER_TECHNIC_WALL_REACH",
                            "span_studs":length})
            continue
        direction=(1.,0.) if diff>0 else (-1.,0.)
        ext=add_beam("extension-"+side,(anchor_x,foot_y),direction,0,15,"32278")
        if abs(holemap[ext][int(round(length))][0]-foot[0])>1e-5:
            raise AssertionError("TECHNIC_EXTENSION_MISALIGNED")
        # Actual pin into the already closed foot vertex would need to pass
        # its existing 6558. It is the SAME hole: no second pin may occupy it.
        # Therefore add the extension BEAM to the existing 3L foot pin joint,
        # whose middle layer (z) was deliberately left free.
        foot_joint="LEFT_FOOT" if side=="negative" else "RIGHT_FOOT"
        links.append({"from":ext,"to":names("pin-"+foot_joint),
                      "hole_index":int(round(length)),
                      "interface":"ACTUAL_LDRAW_32278_HOLE_TO_EXISTING_6558_PIN_MIDDLE",
                      "documented_type":True,"exact_hole_axis_verified":True,
                      "friction_strength_unverified":True})
        anchor_entry={"side":side,"beam_id":ext,"wall_hole_world":
                      [anchor_x,foot_y,z],"stud_mount_status":"UNVERIFIED"}
        # A future stud-anchored 3700 support may be inserted at the
        # target coordinate; source 093 already has roof eave masonry.
        # Do NOT manufacture a wall pin when an exact brick hole and
        # insertion are not demonstrated.
        anchoring.append(anchor_entry)
    return {"frame":index,"bay":bay,"parts":parts,"links":links,
            "vertices":checks,"full_triangle_documented_type":True,
            "closed_right_triangles":2,
            "support_span_studs":round(FRAME_HALF*2,4),
            "tie_to_wall_extensions":anchoring,
            "grounded_wall_pin_count":0,
            "roof_supported_via_verified_interfaces":False,
            "roof_surface_pitch_degrees":22.,
            "roof_truss_pitch_degrees":round(atan2(5,12)*180/3.141592653589793,5),
            "remaining_blockers":blocked+[
                "TECHNIC_EXTENSIONS_NOT_YET_PINNED_TO_GROUNDED_WALL_BRICKS",
                "TRUSS_TO_ROOF_PURLIN_CONNECTION_NOT_VERIFIED",
                "COMPLETE_LDRAW_3D_SWEEP_AND_LOAD_NOT_CERTIFIED",
            ]}


def build_095(source,*,pitch=22.,max_frames=32):
    pristine=source.model_dump_json()
    previous=build_094(source,pitch=pitch)
    base=previous["report"]
    foundation=previous["foundation"]
    if not base["frame_count"] or base["frame_count"]>max_frames:
        raise ValueError("UNSUPPORTED_FRAME_COUNT")
    # Hinge roof + independently capped ridge remain EXACTLY intact.
    # Delete only unclosed 094 A-frame part candidates. Never edit history.
    keep=[];old=[]
    for p in previous["articulated_parts"]:
        if p["placement_id"].startswith(("094-tie-","094-rafter-",
               "094-kingpost-","094-toe-riser-","094-framehinge-")):
            old.append(p)
        else:keep.append(p)
    hinges=previous["hinge_axes"]
    left=min(a["axis_ldu"][0] for a in hinges if "negative" in a["base"])/STUD
    right=max(a["axis_ldu"][0] for a in hinges if "positive" in a["base"])/STUD
    center=(left+right)/2.
    # Eave height is true 093 sill top, not invented from 094 frame layout.
    eave_cap=[p for p in foundation.parts if
             p.placement_id.startswith("EXPERIMENT-093-EAVE-CAP-") and p.part_id in D]
    if not eave_cap:raise ValueError("MISSING_ORIGINAL_EAVE_MASONRY")
    eave_plate=max(p.z_plates+D[p.part_id].height_plates for p in eave_cap)
    eave_y=-eave_plate*8.0
    ridge_parts=[p for p in keep if p["kind"]=="ridge_cover_flat"]
    ridge_y=min(p["xyz_ldu"][1] for p in ridge_parts) if ridge_parts else eave_y-180
    selected=[];skipped=[]
    for frame in base["frames"]:
        bay=int(frame["bay_studs"])
        # Eave sill actual x-footprint limits include left/right x2 studs.
        anchor_points={"negative":left-1,"positive":right+1}
        candidate=complete_technic_frame(index=frame["frame"],bay=bay,
              xcenter=center,eave_y=eave_y,ridge_y=ridge_y,
              anchor_points=anchor_points)
        if any(p["placement_id"] in {x["placement_id"] for x in keep}
               for p in candidate["parts"]):
            raise AssertionError("PART_ID_COLLISION")
        selected.append(candidate)
    new=[p for m in selected for p in m["parts"]]
    if source.model_dump_json()!=pristine:
        raise AssertionError("HISTORIC_SOURCE_MUTATED")
    closure=sum(m["full_triangle_documented_type"] for m in selected)
    graph=[link for m in selected for link in m["links"]]
    report={
        "source_variant":"EXPERIMENT_094_COMPOSITE_3054",
        "architecture":"GENERIC_PIN_CLOSED_TECHNIC_5_12_13_MODULE",
        "angle_unchanged_degrees":pitch,
        "old_094_trusses_removed_count":len(old),
        "new_technic_parts_added":len(new),
        "old_total":base["composite_total"],
        "new_total":len(foundation.parts)+len(keep)+len(new),
        "net_delta":len(new)-len(old),
        "original_foundation_unchanged":True,
        "new_assembly_documented_triangle_count":closure,
        "new_assembly_two_right_triangles_per_frame":2*closure,
        "new_assembly_unclosed_triangles":len(selected)-closure,
        "wall_grounded_truss_count":sum(m["grounded_wall_pin_count"]==2 for m in selected),
        "truss_to_roof_load_rated_paths":0,
        "adequate_wall_load_paths_verified":0,
        "studless_22deg_roof_preserved":True,
        "remaining_wall_anchoring_and_roof_transfer_blocked":True,
        "every_technic_pin_hole_contact_documented_type":all(
           x["exact_hole_axis_verified"] for x in graph),
        "physical_strength_certification":"NOT_CERTIFIED",
        "insertion_complete":"NOT_PROVEN",
        "new_bom":dict(Counter(p["ldraw_id"] for p in new)),
        "removed_bom":dict(Counter(p["ldraw_id"] for p in old)),
        "frame_bays":[m["bay"] for m in selected],
        "support_span_studs":24,
        "triangles":selected,
    }
    return {"foundation":foundation,"articulated_parts":keep+new,
            "report":report,"real_technic_graph":graph,
            "previous_094":previous}
