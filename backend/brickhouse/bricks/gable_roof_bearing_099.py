"""LEGO2-099: actual grounded gable inventory and one second-bearing attempt.

A pitched roof cannot be *clutched* onto an orthogonal 1x1 plate simply
because the orthogonal plate nearly touches its underside. This module
adds genuine 3024 plates to a proven grounded gable stud, measures the
world-space sloped-plate underside from the actual 093 3460 transform,
and explicitly FAILS N2/N4 if the contact and a lateral/uplift lock are
not actually demonstrated. No fabricated gable or floating beam.
"""
from __future__ import annotations
from collections import Counter
from math import floor, hypot
from .fixed_wall_roof_support_098 import build_wall_tie, STUD, PLATE, D
from .brick_model import BrickModel,BrickModelPart
from .articulated_roof_093 import PIVOT_LOCAL,transform_pt
from .roof_studdeck_designer_091 import _cells,_orthogonal_clearance
from .support_chain import analyze_standard_brick_support_chain

def gable_inventory(source):
    grounded={n.placement_id for n in analyze_standard_brick_support_chain(source).nodes
              if n.reaches_ground}
    facades={}
    for label in ("front","rear","left","right"):
        walls=[p for p in source.parts if p.component=="wall" and p.facade==label]
        gables=[p for p in walls if p.placement_id.startswith("gable-")]
        columns={}
        for p in gables:
            if p.part_id not in D:continue
            for cell in _cells(p):
                datum=p.z_plates+D[p.part_id].height_plates
                if (cell not in columns or columns[cell]["top_plates"]<datum):
                    columns[cell]={"top_plates":datum,"id":p.placement_id,
                       "grounded":p.placement_id in grounded}
        maxz=max((v["top_plates"] for v in columns.values()),default=None)
        facades[label]={"wall_piece_count":len(walls),
                        "gable_piece_count":len(gables),
                        "gable_column_count":len(columns),
                        "max_gable_top_plates":maxz,
                        "grounded_gable_piece_count":sum(p.placement_id in grounded
                                                        for p in gables),
                        "sample_gable_piece_ids":[p.placement_id for p in gables[:6]],
                        "columns":[{"stud_cell":[*xy],**item} for xy,item
                                   in sorted(columns.items())]}
    return facades

def _underside_at_cross_x(rail,world_x):
    """Plane of underside of authentic 3460: y-local positive 8 LDU.
    This is a PLANE ONLY; it is not proof of clutch, mesh or compression.
    """
    R=rail["rotation"];p=rail["xyz_ldu"]
    along=R[0][0]
    if abs(along)<0.2:raise ValueError("099_UNSUPPORTED_3460_PANEL_ORIENTATION")
    px=p[0]+8*R[0][1]
    py=p[1]+8*R[1][1]
    offset=(world_x-px)/along
    return py+offset*R[1][0],offset

def _find_gable_pedestal(source,built,facades,*,max_pl=4):
    """Search front gable only, no second imaginary point."""
    by=facades["front"]
    if not by["gable_piece_count"] or not by["grounded_gable_piece_count"]:
        return None, "NO_GROUNDED_FRONT_GABLE"
    # Only studs on real gable whose own brick is known to reach ground.
    candidates=[c for c in by["columns"] if c["grounded"]]
    # Restrict to a single existing front gable bay. Do not guess y coords:
    # 093 rails have indexed stud locations on the same (x,y) footprint.
    rail=[p for p in built["articulated_parts"] if
          p["placement_id"].startswith("093-negative-baseplate-") and
          p["ldraw_id"]=="3460" and p["kind"]=="rafter_base"]
    if not rail:return None,"NO_TRUE_22DEG_RAIL"
    eave_hinges=[p for p in built["articulated_parts"]
                 if p["placement_id"].startswith("093-negative-basehinge-")
                 and p["kind"]=="hinge_base"]
    if not eave_hinges:
        return None,"NO_REAL_EAVE_HINGE_FOR_INDEPENDENT_SECOND_BEARING"
    eave_x=min(transform_pt(p,PIVOT_LOCAL)[0]/STUD for p in eave_hinges)
    anchored=[]
    for candidate in candidates:
        x,y=candidate["stud_cell"]
        # A post at the EAVE ITSELF gives no second moment arm, even if
        # perfectly touching! Require >=6 studs independent of hinge.
        if not eave_x+6<=x<=eave_x+16:
            continue
        if x%3 not in (0,1,2):raise AssertionError("unreachable")
        center_x=(x+.5)*STUD
        center_z=(y+.5)*STUD
        near=sorted((p for p in rail if abs(p["xyz_ldu"][2]-center_z)<1e-5),
                    key=lambda p:abs(p["xyz_ldu"][0]-center_x))
        for member in near:
            bottom_y,u=_underside_at_cross_x(member,center_x)
            if not -(4*STUD)-1e-6<=u<=4*STUD+1e-6:continue
            gable_top=-candidate["top_plates"]*PLATE
            vertical_space=gable_top-bottom_y
            layers=int(floor((vertical_space+1e-6)/PLATE))
            if not 1<=layers<=max_pl:continue
            top_after=gable_top-layers*PLATE
            gap=round(top_after-bottom_y,7)
            if gap < -0.01 or gap >= PLATE:continue
            # A 22-degree plane varies approximately 8.1 LDU across
            # ONE stud; a nominal center clearance could still put the
            # left edge of a real plate THROUGH the roof. Check BOTH edges.
            edges=[top_after-_underside_at_cross_x(member,edge)[0]
                   for edge in (x*STUD,(x+1)*STUD)]
            if min(edges)<0 or max(edges)>1.6*PLATE:
                continue
            anchored.append((gap,layers,x,y,candidate,member,bottom_y,
                             round(min(edges),7),round(max(edges),7)))
            break
    if not anchored:
        return None,"NO_GABLE_STUD_WITH_CONSERVATIVE_ROOF_UNDERSIDE_CLEARANCE"
    # One module only. Avoid a tiny nearly overconstrained stiff assembly:
    # select nearest positive gap among actual grounded stud locations.
    gap,n,x,y,cell,member,bottom_y,min_edge,max_edge=min(anchored,key=lambda t:(t[0],abs(t[2]-30)))
    plates=[]
    for layer in range(n):
        # LDraw part 3024 PLATE_1X1, top plane at source gable top + layers+1.
        # Unlike 095 replacement bricks, we use the actual integer plates.
        topz=cell["top_plates"]+layer+1
        plates.append(BrickModelPart(placement_id=f"EXPERIMENT-099-GABLE-3024-{x}-{y}-{layer}",
            part_id="PLATE_1X1",category="plate",component="roof_support",
            x_studs=x,y_studs=y,z_plates=cell["top_plates"]+layer,
            width_studs=1,length_studs=1,height_plates=1,
            rotation_quarter_turns=0))
    return {"x":x,"y":y,"eave_pivot_x_studs":eave_x,
         "independent_second_point_lever_arm_studs":round(x-eave_x,3),
         "layer_count":n,"gap_ldu":gap,
         "minimum_roof_plane_to_plate_edge_clearance_ldu":min_edge,
         "maximum_roof_plane_to_plate_edge_clearance_ldu":max_edge,
         "source_gable_brick":cell["id"],"grounded":True,
         "roof_rail_id":member["placement_id"],
         "roof_rail_actual_LDraw_id":"3460",
         "roof_underside_world_y":round(bottom_y,7),
         "top_of_new_plate_world_y":-(cell["top_plates"]+n)*PLATE,
         "modelled_plates":plates,
         "part_id":"3024"},None

def build_099(source,pitch=22):
    original=source.model_dump_json()
    base=build_wall_tie(source,pitch=pitch)
    facades=gable_inventory(source)
    pedestal,blocker=_find_gable_pedestal(source,base,facades)
    placed=[]
    if pedestal:
        placed=pedestal["modelled_plates"]
        _orthogonal_clearance(base["foundation"].parts,placed)
    f=BrickModel.model_validate({**base["foundation"].model_dump(mode="json"),
          "building_id":base["foundation"].building_id+"-099-GABLE-RETAINING-ATTEMPT",
          "parts":[p.model_dump(mode="json")
                   for p in list(base["foundation"].parts)+placed]})
    if source.model_dump_json()!=original:raise AssertionError("SOURCE_HISTORY_MUTATED")
    graph=list(base["graph"])
    if pedestal:
        chain=[pedestal["source_gable_brick"]]+[
            q.placement_id for q in pedestal["modelled_plates"]]
        for left,right in zip(chain,chain[1:]):
            graph.append({"from":left,"to":right,
              "interface":"REAL_STANDARD_3024_STUD_TO_ANTISTUD",
              "cell":[pedestal["x"],pedestal["y"]],
              "positive_stud_mating_documented":True,
              "source_wall_grounded":True})
        graph.append({"from":chain[-1],"to":pedestal["roof_rail_id"],
              "interface":"UNCONNECTED_GAP_NOT_A_LEGO_JOINT",
              "world_center_gap_ldu":pedestal["gap_ldu"],
              "positive_stud_mating_documented":False,
              "upward_hinge_rotation_unrestrained":True,
              "graph_edge_is_only_unconnected_inspection_candidate":True})
    detail=({k:v for k,v in pedestal.items() if k!="modelled_plates"}
            if pedestal else None)
    report={
        "fixed_architecture_from":"098_INDEPENDENT_OF_097",
        "full_house_parts":len(f.parts)+len(base["articulated_parts"]),
        "added_3024_gable_plates":len(placed),
        "real_grounded_gable_detected":sum(
             int(v["grounded_gable_piece_count"]>0) for v in facades.values()),
        "facades":facades,"pedestal":detail,
        "gable_blocker":blocker,
        "roof_gap_is_NOT_a_true_edge":True,
        "graph_edges":graph,
        "roof_pitch":pitch,"historic_canonical_modified":False,
        "roof_panels_with_two_restrained_fixed_supports":0,
        "roof_to_wall_two_support_N4_paths":0,
        "remaining_roof_hinge_rotation_upward":True,
        "pedestal_is_positive_engagement_to_22deg_roof":False,
        "gable_stud_stack_N2":bool(placed),
        "gable_to_roof_N2":False,
        "roof_underface_gap_unverified_by_mesh":True,
        "full_pin_clutch_insertion_verified":False,
        "N6":"NOT_CERTIFIED",
        "structural_decision":"STOP_NO_SECOND_POSITIVELY_LOCKED_GABLE_ROOF_INTERFACE",
        "real_098_wall_supports":base["report"]["wall_sides"]}
    return {"foundation":f,"articulated_parts":base["articulated_parts"],
        "gable_subassembly":placed,"report":report,"base":base}
