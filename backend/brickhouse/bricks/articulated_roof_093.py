"""Mission 093: real LDraw articulated roof candidate, NOT a virtual smooth surface.

A BrickModel with integer grid/quarter turns cannot represent 22-degree panels.
This generator retains the exact original masonry as a BrickModel *and* adds
real LDraw 4275b/4276b hinge plates, standard plates and official flat tiles
with explicit rigid transforms, a real LDraw assembly, and measured blockers.

Hinge part/finger identities and local pivot (+20,+4,0) are taken from
official LDraw 4275b.dat/4276b.dat. The pivot/finger clearance, wall mating,
sweep, ridge closure, strength and load capacity remain NOT CERTIFIED.
"""
from __future__ import annotations
from collections import Counter,defaultdict
from math import atan,cos,sin,radians,degrees,isclose
from .brick_model import BrickModel,BrickModelPart
from .catalog import standard_orthogonal_definitions
from .roof_studdeck_designer_091 import _cells,_orthogonal_clearance
from .support_chain import analyze_standard_brick_support_chain

PARTS={
 "4275b": ("HINGE_PLATE_1X2_3_FINGERS",2,1),
 "4276b": ("HINGE_PLATE_1X2_2_FINGERS",2,1),
 "3460":("PLATE_1X8",8,1),
 "3710":("PLATE_1X4",4,1),
 "3666":("PLATE_1X6",6,1),
 "3023b":("PLATE_1X2",2,1),
 "87079":("TILE_2X4",4,2),
 "3008":("BRICK_1X8",8,1),
 "3001":("BRICK_2X4",4,2),
}
DEF=standard_orthogonal_definitions()
LDU_STUD=20.
LDU_PLATE=8.
PIVOT_LOCAL=(20.,4.,0.)
# Deliberately 28 studs in total, hinged four studs inboard from the eave.
PANEL_LENGTH=28
PANEL_HINGE_U=4


def rotation(side,angle):
    c,s=cos(radians(angle)),sin(radians(angle))
    if side=="negative":
        # local length X points upslope (world +X,-Y)
        return ((c,s,0.),(-s,c,0.),(0.,0.,1.))
    # local length X points upslope (world -X,-Y), right-handed.
    return ((-c,-s,0.),(-s,c,0.),(0.,0.,-1.))


def mul(R,v):
    return tuple(sum(R[i][j]*v[j] for j in range(3)) for i in range(3))


def rigid(pid,ldraw,center,R,kind,side=None,meta=None):
    return {"placement_id":pid,"ldraw_id":ldraw,"kind":kind,
            "side":side,"xyz_ldu":[round(x,7) for x in center],
            "rotation":[[round(v,9) for v in row] for row in R],
            "interface_evidence":meta or "STANDARD_STUD_TO_ANTI_STUD_TYPE"}


def transform_pt(inst,p):
    R=inst["rotation"];center=inst["xyz_ldu"]
    return [center[i]+sum(R[i][j]*p[j] for j in range(3)) for i in range(3)]


def _house_parameters(model,design_angle):
    if not 1<=design_angle<=35:
        raise ValueError("INCLINE_OUTSIDE_HINGE_PROPOSAL_SCOPE")
    deck=[p for p in model.parts if p.placement_id.startswith("EXPERIMENT-091-DECK-")]
    if not deck or any(p.rotation_quarter_turns not in (0,1) for p in deck):
        raise ValueError("REQUIRES_EXPERIMENTAL_091_REGULAR_TWO_PAN_ROOF")
    axes={p.rotation_quarter_turns for p in deck if p.part_id=="BRICK_2X4"}
    if axes!={1}:
        # The design supports a second building of any length and shifted
        # coordinates, but its pitched cross axis must be X. No silent twist.
        raise ValueError("092_ORIGINAL_ROOF_AXIS_NOT_X")
    zbase=min(p.z_plates for p in deck)
    eaves=[p for p in deck if p.z_plates==zbase and p.part_id=="BRICK_2X4"]
    xs=sorted({p.x_studs for p in eaves})
    if len(xs)!=2:
        raise ValueError("MISSING_TWO_REAL_EAVES")
    left,right=xs[0]+4,xs[1]-1
    if right<=left+20:
        raise ValueError("UNDERSPAN_OR_INVALID_GABLE")
    ys=sorted({p.y_studs for p in eaves})
    if any(b-a!=2 for a,b in zip(ys,ys[1:])):
        raise ValueError("MISSING_ROOF_BAYS")
    if len(ys)<2 or len(ys)>90:
        raise ValueError("ROOF_BAY_BUDGET")
    return deck,zbase,left,right,ys


def build_093(model:BrickModel,*,pitch=22.,max_parts=7000):
    old_dump=model.model_dump_json()
    deck,zbase,left,right,ys=_house_parameters(model,pitch)
    panel_length=max(8,min(32,4*round(((right-left)/(2*cos(radians(pitch)))+PANEL_HINGE_U)/4)))
    report_wall=analyze_standard_brick_support_chain(model)
    grounded={n.placement_id for n in report_wall.nodes if n.reaches_ground}
    # Strip ALL 091 roof: preserve masonry + prior 090 eave-wall additions.
    removed=[p for p in model.parts if p.placement_id.startswith("EXPERIMENT-091-")]
    if len([p for p in removed if p.placement_id.startswith("EXPERIMENT-091-DECK-")])!=len(deck):
        raise AssertionError("INCOMPLETE_091_DECK_REMOVAL")
    base=[p for p in model.parts if p.placement_id not in {p.placement_id for p in removed}]
    # Build TWO continuous masonry-bonded eave sills, inside the house,
    # under the hinge pivots, using real catalogue bricks and staggered plates.
    # This raises the roofs by four plates and removes the eave/wall intersection.
    rims=[]
    sill_manifest=[]
    root_wall={p.placement_id for p in base if p.component=="wall"
               and p.placement_id in grounded and p.part_id in DEF}
    for side,cross in (("negative",left-2),("positive",right)):
        for j,along in enumerate(range(ys[0],ys[-1]+2,8)):
            length=min(8,ys[-1]+2-along)
            if length not in (6,8):
                raise ValueError("EAVE_SILL_REQUIRES_MODULAR_END_LENGTH_6_OR_8")
            part_id="BRICK_2X"+str(length)
            brick=BrickModelPart(
                placement_id=f"EXPERIMENT-093-EAVE-SILL-{side}-{j}",
                part_id=part_id,category="brick",component="roof_support",
                x_studs=cross,y_studs=along,z_plates=zbase,
                rotation_quarter_turns=0)
            supports=[p for p in base if p.placement_id in root_wall
                and p.z_plates+DEF[p.part_id].height_plates==zbase
                and _cells(p)&_cells(brick)]
            sites=set().union(*(_cells(p)&_cells(brick) for p in supports)) if supports else set()
            if len(sites)<4:
                raise ValueError("EAVE_SILL_NO_GROUNDED_WALL_BEARING")
            rims.append(brick)
            sill_manifest.append({"part":brick.placement_id,
                "wall_support_ids":[p.placement_id for p in supports],
                "compression_joint_stud_sites":[list(site) for site in sorted(sites)]})
        # These bridge all brick-to-brick butt joints at 8-stud intervals.
        cap_runs=[(ys[0],4)]
        cap_runs +=[(v,8) for v in range(ys[0]+4,ys[-1]+2,8)
                    if v+8<=ys[-1]+2]
        last=cap_runs[-1][0]+cap_runs[-1][1]
        if last<ys[-1]+2:
            cap_runs.append((last,ys[-1]+2-last))
        for dx in (0,1):
            for j,(along,ln) in enumerate(cap_runs):
                if ln not in (2,4,6,8):
                    raise ValueError("EAVE_RIM_SEGMENT_LENGTH_INVALID")
                rims.append(BrickModelPart(
                    placement_id=f"EXPERIMENT-093-EAVE-CAP-{side}-{dx}-{j}",
                    part_id="PLATE_1X"+str(ln),category="plate",
                    component="roof_support",x_studs=cross+dx,y_studs=along,
                    z_plates=zbase+3,rotation_quarter_turns=0,
                    width_studs=1,length_studs=ln,height_plates=1))
    _orthogonal_clearance(base,rims)
    foundation=BrickModel.model_validate({**model.model_dump(mode="json"),
        "building_id":model.building_id+"-EXPERIMENTAL-093-REAL-LDRAW-ANGLED",
        "parts":[p.model_dump(mode="json") for p in [*base,*rims]]})
    # Other architectural components remain unchanged.
    assert model.model_dump_json()==old_dump

    instances=[]
    connections=[]
    unsupported=[]
    hinge_axes=[]
    new_assembly=[]
    def add(pid,num,xyz,R,kind,side=None):
        obj=rigid(pid,num,xyz,R,kind,side)
        instances.append(obj);return obj
    eye=((1.,0.,0.),(0.,1.,0.),(0.,0.,1.))
    flip=((-1.,0.,0.),(0.,1.,0.),(0.,0.,-1.))
    def roof_center(side,pivot,t,u,width,layer):
        R=rotation(side,pitch)
        # u is the roofing panel's stud distance from its outermost edge;
        # roof hinge joint is at u=PANEL_HINGE_U, not at roof edge.
        along=(u-PANEL_HINGE_U)*20.
        # Perpendicular to the true inclined panel face, toward tile top.
        normal=(-R[0][1], -R[1][1],0.) # equals (-sin,-cos) left
        world=[pivot[i]+mul(R,(along,0.,(t+width/2.)*20.*(1 if side=='negative' else -1)))[i]
               for i in range(3)]
        # OFFICIAL 4275b/4276b: hinge pivot y=4, top studs y=0.\n        # Stud top is exactly 4 LDU above the hinge axis, NOT 8.\n        # An 8-LDU plate atop it has its top at axis + 12 LDU.
        return tuple(world[i]+(4+layer*8)*normal[i] for i in range(3))

    # Geometry: LDraw tile/plate local x = length, z = width.
    per_side={}
    wall_stud_site_pairs=0
    for side in ("negative","positive"):
        center=left if side=="negative" else right
        R=rotation(side,pitch)
        # Hinge base part ends at the fulcrum; the other part is turned
        # to face the roof, about the SAME physical hinge axis.
        base_R=eye if side=="negative" else flip
        moving_R=((-R[0][0],R[0][1],0.),(-R[1][0],R[1][1],0.),
                  (0.,0.,-R[2][2]))
        # For negative side the moving plate needs opposite X orientation
        # relative to the roof panel: R * Y_180.
        moving_R=tuple(tuple(sum(R[i][k]*flip[k][j] for k in range(3))
                             for j in range(3)) for i in range(3))
        # The hinge axes MUST be co-located in all three coordinates.
        side_hits=0
        for t in ys:
            pivot=(center*20.,-((zbase+4)*8.+4),0.)
            for off in (0,1):
                axis=(pivot[0],pivot[1],(t+off+.5)*20.)
                base_off=mul(base_R,PIVOT_LOCAL)
                move_off=mul(moving_R,PIVOT_LOCAL)
                base_c=tuple(axis[i]-base_off[i] for i in range(3))
                move_c=tuple(axis[i]-move_off[i] for i in range(3))
                b=add(f"093-{side}-basehinge-{t}-{off}","4275b",base_c,base_R,"hinge_base",side)
                m=add(f"093-{side}-roofhinge-{t}-{off}","4276b",move_c,moving_R,"hinge_roof",side)
                b_axis=transform_pt(b,PIVOT_LOCAL)
                m_axis=transform_pt(m,PIVOT_LOCAL)
                if any(abs(a-b)>1e-5 for a,b in zip(b_axis,m_axis)):
                    raise AssertionError("REAL_HINGE_AXES_NOT_COAXIAL")
                hinge_axes.append({"base":b["placement_id"],"roof":m["placement_id"],
                                   "axis_ldu":b_axis,"pitch":pitch,
                                   "part_pair_real":["4275b","4276b"],
                                   "finger_engagement":"UNVERIFIED_IN_MESH_AND_SWEEP"})
                # Verify a nominal eave bearing from ACTUAL grounded wall
                # bricks on the same roof bay and correct z plane.
                plane=({(center-2,y) for y in range(t,t+2)} if side=="negative"
                       else {(center+1,y) for y in range(t,t+2)})
                support=[p.placement_id for p in rims if
                    p.component=="roof_support" and p.part_id in DEF and
                    p.z_plates+DEF[p.part_id].height_plates==zbase+4 and
                    _cells(p)&plane]
                if support:
                    side_hits+=1;wall_stud_site_pairs+=len(support)
                else:
                    unsupported.append({"side":side,"bay":t,"offset":off,
                                        "blocker":"HINGE_BASE_NO_GROUNDED_WALL_STUD"})
                connections.append({"from":b["placement_id"],"to":m["placement_id"],
                    "type":"4275b_3_FINGERS_TO_4276b_2_FINGERS",
                    "coaxial":True,"finger_interference":"NOT_VERIFIED",
                    "connector_documented_family":True,
                    "strength":"NOT_PROVEN"})
            # Each TWO-STUD-DEEP module contains a rigid connected plate
            # sandwich and exterior smooth 2x4 tiles at the proper angle.
            rails=[]
            for off in (0,1):
                for u in range(0,panel_length,8):
                    L=min(8,panel_length-u)
                    pid=f"093-{side}-baseplate-{t}-{off}-{u}"
                    x=roof_center(side,pivot,t+off,u+L/2.,1,1)
                    rail=add(pid,"3460" if L==8 else "3710",x,R,"rafter_base",side)
                    rails.append(rail)
                    if u==0:
                        connections.append({"from":f"093-{side}-roofhinge-{t}-{off}",
                                            "to":pid,
                                            "type":"DOCUMENTED_STANDARD_STUD_TUBE_ALIGNMENT",
                                            "stud_count":2,"strength":"NOT_PROVEN"})
                # Separate staggered reinforced course; overlaps seams.
                lap_intervals=[(0,4)]
                lap_intervals.extend((u,min(8,panel_length-u)) for u in range(4,panel_length,8))
                for u,L in lap_intervals:
                    pid=f"093-{side}-interlockedplate-{t}-{off}-{u}"
                    x=roof_center(side,pivot,t+off,u+L/2.,1,2)
                    add(pid,"3460" if L==8 else "3710",x,R,"rafter_lap",side)
                    connections.append({"from":"lower_course_rails","to":pid,
                        "type":"STANDARD_STUD_TUBE_MATING_PROPOSED",
                        "stud_count":L,"strength":"NOT_PROVEN"})
            for u in range(0,panel_length,4):
                tile=add(f"093-{side}-tile-{t}-{u}","87079",
                         roof_center(side,pivot,t,u+2.,2,3),
                         R,"roof_skin",side)
                connections.append({"from":"interlocked_2rail_course",
                                    "to":tile["placement_id"],
                                    "type":"STANDARD_STUD_TUBE_MATING_PROPOSED",
                                    "stud_count":8,"strength":"NOT_PROVEN"})
        # Two LONGITUDINAL purlins beneath this side's roof, connecting
        # different 2-stud roof panels into a whole-house framed bay.
        # Each is DOUBLE-LAYERED and staggered across its butt joints.
        # Parts are rotated by the same actual 22-degree panel transform.
        Q=((0.,0.,-1.),(0.,1.,0.),(1.,0.,0.))
        purlin_R=tuple(tuple(sum(R[i][k]*Q[k][j] for k in range(3))
                             for j in range(3)) for i in range(3))
        depth=(ys[-1]+2)-ys[0]
        def segments(origin,limit,first):
            segments=[]
            cur=origin
            head=min(first,limit-cur)
            if head>0:
                segments.append((cur,head))
                cur+=head
            while cur<limit:
                n=min(8,limit-cur)
                segments.append((cur,n))
                cur+=n
            return segments
        def actual_plate(length):
            mapping={8:"3460",6:"3666",4:"3710",2:"3023b"}
            if length not in mapping:
                raise ValueError("UNSUPPORTED_PURLIN_PLATE_LENGTH")
            return mapping[length]
        for cross in (8,16):
            uppers=segments(ys[0],ys[-1]+2,8)
            lowers=segments(ys[0],ys[-1]+2,4)
            for level,layer,runs in (("UPPER",0,uppers),("LAP",-1,lowers)):
                for idx,(start,length) in enumerate(runs):
                    rid=f"093-{side}-PURLIN-{cross}-{level}-{idx}"
                    middle=roof_center(side,pivot,start,cross+.5,length,layer)
                    add(rid,actual_plate(length),middle,purlin_R,
                        "purlin_upper" if layer==0 else "purlin_lap",side)
                    connections.append({
                       "from":"SLOPED_RAILS" if layer==0 else "PURLIN_UPPER_COURSE",
                       "to":rid,
                       "type":"STANDARD_STUD_TO_ANTI_STUD_MATING_PROPOSED",
                       "nominal_under_roof":True,
                       "strength":"BENDING_LOAD_UNPROVEN"})
        per_side[side]={"eave_pivot_studs":center,"bays":len(ys),
                        "nominal_wall_bearing_sites":side_hits,
                        "purlin_rows":2}

    if len(instances)>max_parts:
        raise ValueError("PART_BUDGET_EXCEEDED")
    # Roof plane silhouette and ridge measured from exact rigid transforms.
    half=(right-left)/2.
    rise_at_ridge_studs=half*20.*__import__("math").tan(radians(pitch))/8.
    x_front=left-4*cos(radians(pitch))
    x_back=right+4*cos(radians(pitch))
    roof_tip_l=left+(panel_length-PANEL_HINGE_U)*cos(radians(pitch))
    roof_tip_r=right-(panel_length-PANEL_HINGE_U)*cos(radians(pitch))
    ridge_gap=roof_tip_r-roof_tip_l
    if ridge_gap < -1:
        # Overlapping roof panels across centerline require actual mesh check.
        roof_ridge_status="BLOCKED_POSSIBLE_PANE_INTERSECTION"
    elif ridge_gap > 0.3:
        roof_ridge_status="BLOCKED_GAP_NEEDS_DOCUMENTED_RIDGE_CLOSURE"
    else:
        roof_ridge_status="RIDGE_NEAR_NOMINAL_ALIGNMENT_MESH_PENDING"
    counts=Counter(p["ldraw_id"] for p in instances)
    report={
        "architecture":"SLOPED_TWO_PANEL_HALF_ROOF_REAL_LDRAW_4275B_4276B",
        "source_091_parts":len(model.parts),
        "masonry_and_facade_retained":len(base),
        "new_structural_eave_sill_parts":len(rims),
        "eave_sill_connections":sill_manifest,
        "articulated_instances":len(instances),
        "composite_total_part_count":len(base)+len(rims)+len(instances),
        "source_091_removed_count":len(removed),
        "canonical_1890_unchanged":True,
        "roof_091_and_092_microsteps_not_reused":True,
        "real_design_ids":dict(sorted(counts.items())),
        "sources_hinge_official":["https://library.ldraw.org/parts/8469",
             "https://library.ldraw.org/parts/8472"],
        "slope_aim_degrees":pitch,"actual_panel_pitch_degrees":pitch,
        "pitch_reference_degrees":22.,
        "slope_error_degrees":round(abs(pitch-22),6),
        "eave_world_cross_studs":[x_front,x_back],
        "ridge_world_cross_studs":[roof_tip_l,roof_tip_r],
        "ridge_nominal_gap_studs":round(ridge_gap,5),
        "ridge_status":roof_ridge_status,
        "eave_z_plates":zbase+4,
        "eave_rise_plates_from_historic_roof":4,
        "panel_length_studs":panel_length,
        "ridge_z_plates_at_midspan":round(zbase+4+rise_at_ridge_studs,4),
        "hinge_axis_pairs":len(hinge_axes),
        "coaxial_hinge_axis_pairs":len(hinge_axes),
        "hinge_finger_engagement_proven":0,
        "standard_rail_to_tile_interface_proposals":sum("STUD" in c["type"] for c in connections),
        "roof_to_walls_load_rated_paths":0,
        "wall_bearing_pair_candidates":wall_stud_site_pairs,
        "unsupported_hinge_bearings":unsupported,
        "interior_truss_certified":False,
        "under_roof_purlin_rows_total":4,
        "load_bearing_purlin_stiffness":"NOT_ESTABLISHED",
        "roof_panel_to_foundation_mechanical_status":"UNPROVEN_HINGE_FRICTION_AND_LOAD",
        "roof_surface_studless_finished_tiles":(panel_length//4)*2*len(ys),
        "roof_smooth_surface":True,
        "roof_exterior_flat_plane_count":2,
        "insertion_swept_mesh_screen":"NOT_VERIFIED",
        "3d_nonorthogonal_clash":"NOT_VERIFIED",
        "physical_certification":"NOT_CERTIFIED",
        "human_visual_approval":False,
        "assembly_plan":[
            "RETAIN_ALL_090_GROUNDED_MASONRY_AND_FACADE",
            "ATTACH_HINGE_4275B_BASES_AT_EAVE_ON_APPROVED_WALL_STUDS",
            "PREASSEMBLE_RAILS_WITH_OVERLAPPING_STANDARD_PLATES_AND_TILES",
            "MATE_4276B_2_FINGER_PLATES_WITH_REAL_4275B_3_FINGERS",
            "MOVE_PANELS_TO_22_DEG_ABOUT_COAXIAL_LDRAW_JOINTS",
            "STOP_VALIDATE_HINGE_MESH_SWEEP_RIDGE_GAP_AND_ROOF_LOAD_PATH",
        ]}
    return {"foundation":foundation,"articulated_parts":instances,
            "connections":connections,"hinge_axes":hinge_axes,"report":report}
