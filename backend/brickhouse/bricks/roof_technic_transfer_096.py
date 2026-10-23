"""LEGO2-096: build real stud-mounted roof/Technic candidate adapters.

The candidate is placed BEFORE it is assessed as a connection. 3700 studs
under a 093 1x8 rail, two authentic 2780 pins, and a 7-hole 32524 brace
are all represented by LDraw transforms. The 5-12-13 frame and the 22 degree
roof are left untouched.  A close but noncoincident pair of pin axes is
NOT a proved connection: precise interference fits and physical load paths
must fail closed, regardless of the drawing's appearance.
"""
from __future__ import annotations

from collections import Counter
from math import hypot
from .articulated_roof_093 import rigid, transform_pt
from .technic_triangle_095 import build_095, beam, pin, STUD, screen_technic_roof_clearance

# 3700: local X = two studs, local Y = stud top to underside;
# actual cross-axial Technic hole at (0,10,0), along local Z.
ROOF_BRACKET_LDRAW = "3700"
BRACE_LDRAW = "32524"
CONNECTOR_LDRAW = "2780"
BRACE_HOLE_INTERVALS = 6
BRACE_HOLE_SPAN_LDU = 120.0
# This *search bound* is NOT a manufacturer's tolerance.
# Any nonzero error must be documented as unresolved and NOT N2 verified.
CANDIDATE_SEARCH_MAX_AXIS_RESIDUAL_LDU = 0.1


def _vadd(p, rotation, local):
    return tuple(round(p[i] + sum(rotation[i][j] * local[j]
                                 for j in range(3)), 7) for i in range(3))


def _frame_rafter_holes(frame):
    """095 left rafter: genuine indexed 20-LDU 5:12:13 hole spacing."""
    vertices = {x["vertex"]: x for x in frame["vertices"]}
    lo = next(v for v in vertices["LEFT_FOOT"]["hole_centers_ldu"]
              if abs(v[2] - (frame["bay"] + 2.5)*STUD) < 1e-6)
    hi = next(v for v in vertices["APEX"]["hole_centers_ldu"]
              if abs(v[2] - lo[2]) < 1e-6)
    return [(round(lo[i]+(hi[i]-lo[i])*k/13., 7) for i in range(3))
            for k in range(14)]


def _roof_bracket(frame, assembly):
    """Two studs of a real 3700 under a genuine 093 segment, not a bbox touch."""
    bay = frame["bay"]
    rail_id = f"093-negative-baseplate-{bay}-0-16"
    rail = next((p for p in assembly if p["placement_id"] == rail_id), None)
    if not rail or rail["ldraw_id"] != "3460":
        return None, "REAL_EIGHT_STUD_RAIL_MISSING"
    # Rail runs u16..24, center u20. Bracket spans u17..19, center u18,
    # wholly inside its documented eight-stud LDraw plate footprint.
    # Underface of plate lies at local Y=8 (stud top of 3700 at Y=0).
    q = rigid(f"096-F{frame['frame']}-roof-3700", ROOF_BRACKET_LDRAW,
              _vadd(rail["xyz_ldu"], rail["rotation"], (-40., 8., 0.)),
              rail["rotation"], "roof096_stud_mounted_technic_bracket",
              side="negative")
    return {"part":q, "rail":rail_id,
            "stud_cells_local_rail_u":[17.5,18.5],
            "rail_underside_offset_ldu":8.,
            "hole":transform_pt(q,(0.,10.,0.)),
            "roof_angle_degrees":22.0},None


def _join_one_grounded_frame(frame, assembly):
    if frame["grounded_wall_pin_count"] != 2:
        return {"frame":frame["frame"],"bay":frame["bay"],
                "status":"NO_TWO_GROUNDED_WALL_ANCHORS",
                "new_parts":[],"edges":[]}
    roof,reason = _roof_bracket(frame,assembly)
    if reason:
        return {"frame":frame["frame"],"bay":frame["bay"],"status":reason,
                "new_parts":[],"edges":[]}
    hole = roof["hole"]
    indexed = _frame_rafter_holes(frame)
    eligible = []
    for k in range(2,13):  # never displace an already occupied vertex pin
        base = indexed[k]
        length = hypot(hole[0]-base[0],hole[1]-base[1])
        err = abs(length-BRACE_HOLE_SPAN_LDU)
        eligible.append((err,k,length,base))
    err,k,length,rafter_hole = min(eligible)
    if err >= CANDIDATE_SEARCH_MAX_AXIS_RESIDUAL_LDU:
        return {"frame":frame["frame"],"bay":frame["bay"],
                "status":"NO_REAL_7_HOLE_BRACE_SPAN_NEAR_STUD_GRID",
                "best_axis_residual_ldu":round(err,7),
                "new_parts":[],"edges":[]}
    depth = (frame["bay"]+1.5)*STUD  # midway between rail and rafter
    # Rafter-left is an existing actual 32278, positioned at z=depth+20.
    target_rafter=f"095-F{frame['frame']}-rafter-left"
    if not any(p["placement_id"]==target_rafter and p["ldraw_id"]=="32278"
               for p in frame["parts"]):
        raise AssertionError("REAL_095_RAFTER_MISSING")
    direction=((hole[0]-rafter_hole[0])/length,
               (hole[1]-rafter_hole[1])/length)
    brace,centers = beam((rafter_hole[0],rafter_hole[1]),direction,
                         depth,7,BRACE_LDRAW,
                         f"096-F{frame['frame']}-brace-7-hole")
    end=centers[6]
    residual=hypot(hole[0]-end[0],hole[1]-end[1])
    # Pin axis is WORLD Z for both 3700 local-Z under negative roof
    # and 32278/32524 local-X. This test is orientation-based.
    R=roof["part"]["rotation"]
    if any(abs(R[i][2] - (0.,0.,1.)[i])>1e-6 for i in range(3)):
        raise AssertionError("ROOF_3700_PIN_AXIS_NOT_PARALLEL_TO_TECHNIC")
    if abs(hole[2] - (depth-20.))>1e-6:
        raise AssertionError("ROOF_3700_WRONG_PIN_PLANE")
    if abs(rafter_hole[2]-(depth+20.))>1e-6:
        raise AssertionError("FRAME_RAFTER_WRONG_PIN_PLANE")
    lower_pin=pin(f"096-F{frame['frame']}-pin-at-roof-2780",
                  hole[0],hole[1],depth-10.,False)
    upper_pin=pin(f"096-F{frame['frame']}-pin-at-rafter-2780",
                  rafter_hole[0],rafter_hole[1],depth+10.,False)
    exact=residual < 1e-6
    edges=[
      {"from":roof["rail"],"to":roof["part"]["placement_id"],
       "interface":"TWO_REAL_3700_TOP_STUDS_TO_3460_UNDERSIDE",
       "studs":2,"nominal_alignment":True,"clutch_unverified":True},
      {"from":roof["part"]["placement_id"],"to":lower_pin["placement_id"],
       "interface":"REAL_3700_HOLE_TO_2780_PIN",
       "axis_world":"Z","nominal_alignment":True},
      {"from":lower_pin["placement_id"],"to":brace["placement_id"],
       "interface":"2780_PIN_TO_32524_HOLE_6",
       "axis_residual_ldu":round(residual,7),
       "exact_hole_axis_verified":exact},
      {"from":brace["placement_id"],"to":upper_pin["placement_id"],
       "interface":"32524_HOLE_0_TO_2780_PIN",
       "exact_hole_axis_verified":True},
      {"from":upper_pin["placement_id"],"to":target_rafter,
       "interface":f"2780_TO_32278_HOLE_{k}",
       "exact_hole_axis_verified":True},
    ]
    return {"frame":frame["frame"],"bay":frame["bay"],
            "status":("EXACT_PIN_CENTER_CHAIN_CANDIDATE" if exact else
                      "REAL_PARTS_PLACED_AXIS_RESIDUAL_UNPROVEN"),
            "stud_mount":roof,"rafter_hole_index":k,
            "rafter_hole_world":rafter_hole,
            "brace_hole_0_world":centers[0],
            "brace_hole_6_world":end,
            "roof_hole_world":hole,
            "axis_residual_ldu":round(residual,7),
            "axis_exact":exact,
            "pin_2780_spacing_20_ldu":True,
            "pin_6558_full_sweep_verified":False,
            "pin_2780_full_sweep_verified":False,
            "collar_clearance_verified":False,
            "mechanical_strength_established":False,
            "new_parts":[roof["part"],brace,lower_pin,upper_pin],
            "edges":edges}


def build_096(source, *, pitch=22.):
    snapshot=source.model_dump_json()
    if abs(pitch-22)>1e-9:
        raise ValueError("096_REQUIRES_REAL_22_DEG_ROOF")
    old=build_095(source,pitch=pitch)
    if source.model_dump_json()!=snapshot:
        raise AssertionError("HISTORICAL_SOURCE_091_MUTATED")
    assembly=old["articulated_parts"]
    trials=[_join_one_grounded_frame(t,assembly)
            for t in old["report"]["triangles"]]
    new=[p for row in trials for p in row["new_parts"]]
    all_ids=[p["placement_id"] for p in assembly+new]
    if len(all_ids)!=len(set(all_ids)):
        raise AssertionError("096_DUPLICATED_PLACEMENT_ID")
    # No attempt to add fictional masonry under the five unsupported bays.
    anchored=old["report"]["wall_grounded_truss_count"]
    candidate=sum(bool(t["new_parts"]) for t in trials)
    exact=sum(t.get("axis_exact",False) for t in trials)
    clash=screen_technic_roof_clearance(new,assembly)
    report={
       "source_variant":"095_LDRAW_COMPOSITE",
       "canonical_original_1890_mutated":False,
       "source_091_mutated":False,
       "roof_pitch_degrees":pitch,
       "technic_truss_pitch_degrees":old["report"]["triangles"][0]["roof_truss_pitch_degrees"],
       "original_095_total":old["report"]["new_total"],
       "new_total":old["report"]["new_total"]+len(new),
       "additional_real_parts":len(new),
       "added_bom_ldraw":dict(sorted(Counter(p["ldraw_id"] for p in new).items())),
       "removed_bom_ldraw":{},
       "technic_frames":len(trials),
       "grounded_two_wall_frames":anchored,
       "frames_still_without_two_wall_anchors":len(trials)-anchored,
       "roof_bracket_brace_candidate_chains":candidate,
       "exact_coaxial_complete_chains":exact,
       "documented_and_load_rated_roof_to_foundation_paths":0,
       "all_part_catalog_ids_real":all(p["ldraw_id"] in
                                       (ROOF_BRACKET_LDRAW,BRACE_LDRAW,CONNECTOR_LDRAW)
                                       for p in new),
       "new_brace_body_to_skin_envelope_screen":clash,
       "pin_insertion_axis_and_nominal_lengths_inspected":2*candidate,
       "pin_full_body_sweeps_verified":0,
       "pin_collars_verified":0,
       "collision_mesh_all_parts_verified":False,
       "n1_real_ldraw_part_identities":True,
       "n2_stud_mount_nominal":candidate,
       "n2_brace_pin_exact":exact,
       "n3_swept_clearance_proven":False,
       "n4_load_path_proven":False,
       "n5_full_mount_sequence_proven":False,
       "n6_strength_proven":False,
       "physical_certification":"NOT_CERTIFIED",
       "candidate_details":[{k:v for k,v in x.items() if k!="new_parts"}
                            for x in trials],
       "decisions":[
          "GROUNDLESS_FRAMES_NOT_PROMOTED",
          "REAL_3700_TOP_STUDS_ARE_INSTALLED_UNDER_EXISTING_3460_RAIL",
          "REAL_32524_AND_2780S_ADDED_ONLY_WITH_BOUNDED_AXIS_RESIDUAL",
          "RESIDUAL_GREATER_THAN_ZERO_REMAINS_UNVERIFIED_NOT_N2",
          "NO_WALL_ROOF_N4_OR_PIN_N5_CERTIFICATE"
       ],
    }
    return {"foundation":old["foundation"],
            "articulated_parts":assembly+new,
            "added_parts":new,
            "graph":old["real_technic_graph"]+
                     [edge for t in trials for edge in t["edges"]],
            "report":report,
            "previous_095":old}
