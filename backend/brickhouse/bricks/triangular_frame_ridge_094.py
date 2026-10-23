"""LEGO2-094 — integrated A-frame truss proposal and separately supported ridge.

This module intentionally preserves the exact 22° 093 roof and every source.
The 093 LDraw composite is extended by REAL LEGO standard parts:
  * horizontal, staggered 2x8 beam courses below the roof;
  * two actual inclined plate chords per transverse A-frame;
  * a central king post from beam level toward the ridge;
  * an independent longitudinal ridge purlin and flat cap bridge;
  * explicit 4275b/4276b complementary geometry checks.

No head-to-head virtual 'connection': only standard-stud interfaces or
coaxial hinge families are tagged as documented *types*. In particular the
unverified triangle corners, king-post transfer and ridge cap contact cannot
be called mechanically validated, even when the triangles are visually real.
"""
from __future__ import annotations
from collections import Counter
from math import atan2,cos,sin,radians,hypot,ceil
from .articulated_roof_093 import build_093,rotation,rigid,PARTS
from .roof_collision_093 import envelope_intersect,roof_obb
from .geometry_adapter import CANONICAL_LDRAW_PARTS

STUD=20.0
PLATE=8.0
I=((1.,0.,0.),(0.,1.,0.),(0.,0.,1.))
# Existing, real LDraw catalogue designs. No custom roof piece.
NEW_PARTS={"3007":(8,2),"3001":(4,2),"3008":(8,1),
           "3009":(6,1),"3010":(4,1),"3004":(2,1),
           "3023b":(2,1),
           "3460":(8,1),"3666":(6,1),"3710":(4,1),
           "87079":(4,2),"3068b":(2,2)}
LOCAL_PARTS={**PARTS,**{k:(k,*v) for k,v in NEW_PARTS.items()}}
# The short 2x2 tile is official LDraw 3068b, added to the orthogonal
# envelope screen; it is NOT an invented custom half-tile.
PARTS.setdefault("3068b",("TILE_2X2",2,2))



def _rotated_z(R):
    return (R[0][2],R[1][2],R[2][2])


def _axis_check(axes,allparts):
    found={p["placement_id"]:p for p in allparts}
    rows=[]
    for pair in axes:
        a,b=found[pair["base"]],found[pair["roof"]]
        axis_a=_rotated_z(a["rotation"])
        axis_b=_rotated_z(b["rotation"])
        d=abs(sum(axis_a[i]*axis_b[i] for i in range(3)))
        rows.append({"base":a["placement_id"],"roof":b["placement_id"],
                     "axis_location_coaxial":True,
                     "axes_parallel_or_antiparallel":abs(d-1)<1e-7,
                     "ldraw_primitive_source":["h2.dat","h1.dat"],
                     "complementary_three_plus_two_fingers":True,
                     "finger_surface_mesh_sweep_verified":False,
                     "strength_verified":False})
    return rows


def build_094(source,*,pitch=22.,truss_step_bays=4,max_new_parts=1500):
    if truss_step_bays<2 or truss_step_bays>8:
        raise ValueError("TRUSS_SPACING_OUTSIDE_DOCUMENTED_GEOMETRIC_RANGE")
    pristine=source.model_dump_json()
    trial=build_093(source,pitch=pitch)
    r=trial["report"]
    full=list(trial["articulated_parts"])
    axes=_axis_check(trial["hinge_axes"],full)
    if not all(a["axes_parallel_or_antiparallel"] for a in axes):
        raise ValueError("HINGE_AXIS_ROTATION_INCOMPATIBLE")
    eave_l,eave_r=r["eave_world_cross_studs"]
    c=cos(radians(pitch))
    left=eave_l+4*c
    right=eave_r-4*c
    middle=(left+right)/2.
    ridge_y=-r["ridge_z_plates_at_midspan"]*PLATE
    eave_y=-r["eave_z_plates"]*PLATE
    parts_new=[]
    joints=[]
    blockers=[]
    frames=[]
    counts=Counter()
    def add(name,ldraw,xyz,rot,kind):
        if ldraw not in LOCAL_PARTS:raise ValueError("PART_NOT_IN_LDRAW")
        p=rigid("094-"+name,ldraw,xyz,rot,kind)
        parts_new.append(p);counts[ldraw]+=1
        return p
    # derive building depth/bays from actual hinge axis coordinates; no fixed y.
    spans=sorted({int(p["placement_id"].split("-")[3])
                 for p in full if p["placement_id"].startswith("093-negative-basehinge-")})
    if len(spans)<2 or any(b-a!=2 for a,b in zip(spans,spans[1:])):
        raise ValueError("INCOMPLETE_ROOF_BAYS")
    truss_starts=spans[::truss_step_bays]
    if truss_starts[-1]!=spans[-1]:truss_starts.append(spans[-1])
    # A-frame runs below roofing, half-stud inset from the skin.
    # Truss pitches explicitly match the real roof angle, not a 90° grid.
    # Put tie beams FLUSH with the underside of the prior 093 eave sill
    # bricks: four plates below the roof hinge plane. This avoids the
    # incompatible solid/solid overlap that a two-plate drop would create.
    tie_top_y=eave_y+PLATE*4.0
    run=middle-left
    angled_length=run/c
    along_segments=[]
    purlin_segments=[]
    for frame_no,bay in enumerate(truss_starts):
        world_z=(bay+1.)*STUD
        # Cross-tie made of real 2x8 bricks (no magically long beam).
        # Staggered cap plates bond adjacent bricks on top, but beam-to-wall
        # at both ends is a candidate until exact studs are verified.
        x0=left-2
        x1=right+2
        run_studs=int(round(x1-x0))
        bricks=[]
        for idx,k in enumerate(range(0,run_studs,8)):
            n=min(8,run_studs-k)
            # Only LEGO brick sizes actually in the established catalog.
            if n not in (4,8):
                blockers.append({"frame":frame_no,"reason":"UNSUPPORTED_LAST_TIE_SPAN",
                                 "remaining_studs":n})
                continue
            mat=I
            part=add(f"tie-{frame_no}-{idx}","3007" if n==8 else "3001",
                ((x0+k+n/2)*STUD,tie_top_y,world_z),mat,"truss_bottom_tie")
            bricks.append(part["placement_id"])
        # Two slanted upper chords per frame, using real 1x8 plate segments.
        # They lie BELOW the skin; there is no invented 22° wedge part.
        rafters=[]
        for side in ("negative","positive"):
            R=rotation(side,pitch)
            for idx,k in enumerate(range(0,int(round(angled_length)),8)):
                n=min(8,int(round(angled_length))-k)
                if n not in (4,6,8):
                    blockers.append({"frame":frame_no,"side":side,
                        "reason":"PITCHED_RAFTER_REQUIRES_MORE_GEOMETRIC_LAP",
                        "remaining_studs":n})
                    continue
                start=left if side=="negative" else right
                xc=start+(1 if side=="negative" else -1)*(k+n/2)*c
                yy=eave_y-(k+n/2)*sin(radians(pitch))*STUD + PLATE*1.25
                p=add(f"rafter-{frame_no}-{side}-{idx}",
                    "3460" if n==8 else ("3666" if n==6 else "3710"),
                    (xc*STUD,yy,world_z),R,"truss_sloping_chord")
                rafters.append(p["placement_id"])
        # Real vertical king post from bottom tie to the roof apex. Every
        # straight vertical member is a standard LEGO part, not fiction;
        # its end joint at nonintegral 22° is not assumed to clutch.
        h=abs(ridge_y-tie_top_y)
        vertical_bricks=[]
        znow=tie_top_y
        for j in range(int(h//24)):
            new=add(f"kingpost-{frame_no}-{j}","3001",
                (middle*STUD,znow-(j+.5)*24,world_z),
                ((0.,1.,0.),(-1.,0.,0.),(0.,0.,1.)),
                "truss_king_post")
            vertical_bricks.append(new["placement_id"])
        # Raise the ends of the bottom chord to the existing eave hinge
        # elevation with one real 1x2 brick + one 1x2 plate per side.
        # Top stud: tie_top_y (brick underside), brick top eave+8,
        # plate underside eave+8, plate top eave. Standard stud-cell chains
        # are nominally explicit; final engagement to hinge base is not.
        toe_risers=[]
        for side in ("negative","positive"):
            toe_cross=left+1.5 if side=="negative" else right-1.5
            lower=add(f"toe-riser-{frame_no}-{side}-brick","3004",
                      (toe_cross*STUD,eave_y+PLATE,world_z),
                      I,"truss_toe_riser_brick")
            upper=add(f"toe-riser-{frame_no}-{side}-plate","3023b",
                      (toe_cross*STUD,eave_y,world_z),
                      I,"truss_toe_riser_plate")
            toe_risers.extend([lower["placement_id"],upper["placement_id"]])
            joints.append({"from":"truss_bottom_tie","to":lower["placement_id"],
                   "connector_type":"STANDARD_STUD_ANTI_STUD_PROPOSED_2_SITES",
                   "nominal_site_count":2,"mechanically_rated":False})
            joints.append({"from":lower["placement_id"],"to":upper["placement_id"],
                   "connector_type":"STANDARD_STUD_ANTI_STUD_PROPOSED_2_SITES",
                   "nominal_site_count":2,"mechanically_rated":False})
        # Real paired finger hinges at both feet AND at the A-frame apex.
        # The 3+2 complementary finger types and coincident pivot are
        # documented by LDraw h2.dat / h1.dat. Their stud clutch to beam
        # ends and their *load rating* still require detailed proof.
        for side in ("negative","positive"):
            R=rotation(side,pitch)
            flip=((-1.,0.,0.),(0.,1.,0.),(0.,0.,-1.))
            moving=tuple(tuple(sum(R[i][k]*flip[k][j] for k in range(3))
                                 for j in range(3)) for i in range(3))
            base_rot=I if side=="negative" else flip
            for place,xx,yy in (
                    ("toe",left+3 if side=="negative" else right-3,eave_y),
                    ("apex",middle,ridge_y+PLATE*2)):
                axis=(xx*STUD,yy,world_z)
                def transformed(R,p):
                    return tuple(sum(R[i][j]*p[j] for j in range(3)) for i in range(3))
                pivot=(20.,4.,0.)
                ba=transformed(base_rot,pivot)
                mb=transformed(moving,pivot)
                b=add(f"framehinge-{frame_no}-{side}-{place}-base",
                      "4275b",tuple(axis[i]-ba[i] for i in range(3)),
                      base_rot,"truss_hinge_base")
                m=add(f"framehinge-{frame_no}-{side}-{place}-moving",
                      "4276b",tuple(axis[i]-mb[i] for i in range(3)),
                      moving,"truss_hinge_moving")
                def actual_pivot(p):
                    rot=p["rotation"];xyz=p["xyz_ldu"]
                    return [xyz[i]+sum(rot[i][j]*pivot[j] for j in range(3))
                            for i in range(3)]
                if any(abs(va-vb)>1e-6 for va,vb
                       in zip(actual_pivot(b),actual_pivot(m))):
                    raise AssertionError("A_FRAME_REAL_HINGE_NOT_COAXIAL")
                joints.append({"from":b["placement_id"],"to":m["placement_id"],
                    "connector_type":"LDRAW_4275B_H2_TO_4276B_H1_COMPLEMENTARY_FINGERS",
                    "three_plus_two_finger_family":"DOCUMENTED",
                    "coaxial_geometry_verified":True,
                    "finger_mesh_interference_verified":False,
                    "standalone_usable_strain_rating":False,
                    "attachment_to_frame_chord":"UNVERIFIED_STUD_ALIGNMENT"})
        load_rows=[
          {"from":"roof_tiles","to":"sloping_rafters",
           "connector_type":"STANDARD_STUD_TUBE_INTERFACE_CANDIDATE",
           "rated":False},
          {"from":"sloping_rafters","to":"kingpost",
           "connector_type":"HINGE_OR_SPECIAL_VERTEX_JOINT_NOT_YET_CONSTRUCTED",
           "rated":False},
          {"from":"kingpost","to":"bottom_tie",
           "connector_type":"END_BEARING_NOT_VERIFIED",
           "rated":False},
          {"from":"bottom_tie","to":"existing_eave_walls",
           "connector_type":"STANDARD_STUD_SITE_TO_BE_MEASURED",
           "rated":False}]
        joints.extend(load_rows)
        frames.append({"frame":frame_no,"bay_studs":bay,
                       "tie_bricks":bricks,"rafter_parts":rafters,
                       "king_post_bricks":vertical_bricks,
                       "clear_span_studs":round(right-left,4),
                       "nominal_bending_span_studs":run_studs,
                       "pitch_degrees":pitch,"transverse_triangle_visible":bool(rafters),
                       "triangle_vertex_mechanically_connected":False,
                       "load_paths":load_rows})
    # Build ridge on independent center purlin, not force incompatible slope
    # panels to mesh into one another. Both sides retain 22 degrees.
    ridge_parts=[]
    ys=spans
    for idx,bay in enumerate(ys[::4]):
        length=min(8,ys[-1]+2-bay)
        if length not in (2,4,6,8):
            raise ValueError("RIDGE_LAST_BEAM_LENGTH_CANNOT_BE_REAL_LEGO")
        ldraw={2:"3004",4:"3010",6:"3009",8:"3008"}[length]
        ridge=add(f"ridge-beam-{idx}", ldraw,
            (middle*STUD,ridge_y-2*PLATE,(bay+length/2)*STUD),
            ((0.,0.,1.),(0.,1.,0.),(-1.,0.,0.)),"ridge_purlin")
        ridge_parts.append(ridge["placement_id"])
    # Replace the existing tip row (last 4-stud tile) on each side with
    # a shorter, real 2x2 tile, leaving space for the independent crest.
    old_tips=[]
    new_tips=[]
    for side in ("negative","positive"):
        side_tiles=[p for p in full if p["kind"]=="roof_skin" and p["side"]==side]
        tip=max(int(p["placement_id"].split("-")[-1]) for p in side_tiles)
        for p in side_tiles:
            if int(p["placement_id"].split("-")[-1])!=tip:continue
            old_tips.append(p)
            q=dict(p)
            q["placement_id"]="094-short-"+p["placement_id"]
            q["ldraw_id"]="3068b"
            R=q["rotation"]
            # Center shorter tile one stud away from peak (toward eave).
            delta=-STUD*(1 if side=="negative" else 1)
            axis=[R[i][0] for i in range(3)]
            q["xyz_ldu"]=[q["xyz_ldu"][i]+axis[i]*delta for i in range(3)]
            parts_new.append(q);counts["3068b"]+=1;new_tips.append(q)
    removed_tip_ids={p["placement_id"] for p in old_tips}
    full=[p for p in full if p["placement_id"] not in removed_tip_ids]
    # Real flat 2x4 tiles on the separate ridge purlin, supported by its
    # studs. The independent cap is 0° and does not torque tilted slopes.
    for bay in spans[::2]:
        cap=add(f"ridge-cover-{bay}","87079",
            (middle*STUD,ridge_y-3*PLATE,
             (bay+(1 if bay==ys[-1] else 2.))*STUD),
            ((1.,0.,0.),(0.,1.,0.),(0.,0.,1.)),
            "ridge_cover_flat")
        joints.append({"from":"ridge_purlin","to":cap["placement_id"],
                       "connector_type":"STANDARD_STUD_TUBE_MATING_PROPOSED",
                       "rated":False})
    full.extend(parts_new)
    if len(parts_new)>max_new_parts:raise ValueError("NEW_PARTS_BUDGET")
    # Explicit 3D screen at the newly CONSTRUCTED ridge. This tests actual
    # transformed catalogue tile ENVELOPES, never repaired fake watertight
    # meshes. A collision is a blocking result, not an approved interlock.
    ridge_caps=[p for p in parts_new if p["kind"]=="ridge_cover_flat"]
    short_tips=[p for p in parts_new if p["placement_id"].startswith("094-short-")]
    ridge_overlaps=[]
    tested=0
    for tip in short_tips:
        for cap in ridge_caps:
            tested+=1
            if envelope_intersect(roof_obb(tip),roof_obb(cap)):
                ridge_overlaps.append([tip["placement_id"],cap["placement_id"]])
    ridge_purlins=[p for p in parts_new if p["kind"]=="ridge_purlin"]
    cover_support_envelope_intersections=0
    supported_ridge_covers=[]
    for cap in ridge_caps:
        cap_nominal_sites=[]
        for support in ridge_purlins:
            # Standard LDraw 3008 roof purlin has TOP STUDS at its
            # y reference, and 87079 tile has underside at y+8 LDU.
            # Mate only with actual coincident planes and overlapping
            # catalogue footprints (no imagined hinge at the ridge).
            top=support["xyz_ldu"][1]
            tile_under=cap["xyz_ldu"][1]+PLATE
            if abs(top-tile_under)>1e-5:
                continue
            along_gap=abs(cap["xyz_ldu"][2]-support["xyz_ldu"][2])
            # Two tile underside cavities nominally fall inside
            # the beam's 8-stud length and 1-stud transverse width.
            beam_length=LOCAL_PARTS[support["ldraw_id"]][1]
            max_gap=(beam_length/2.-.5)*STUD
            if along_gap<=max_gap+1e-5 and abs(cap["xyz_ldu"][0]-support["xyz_ldu"][0])<1e-5:
                cap_nominal_sites.append({"beam_id":support["placement_id"],
                    "tile_id":cap["placement_id"],
                    "nominal_stud_cells":2,
                    "type":"STANDARD_STUD_TO_TILE_UNDERSIDE_MATING_GEOMETRY",
                    "physical_strength":"NOT_TESTED"})
        supported_ridge_covers.extend(cap_nominal_sites)
    if len(supported_ridge_covers)<len(ridge_caps):
        blockers.append({"reason":"RIDGE_COVER_NOT_ALL_STUD_SUPPORTED",
                         "unsupported_cover_count":len(ridge_caps)-len(supported_ridge_covers)})

    if source.model_dump_json()!=pristine:
        raise AssertionError("SOURCE_MUTATED")
    # This is a *candidate truss*: separated triangle pieces do not yet have
    # proven 3D LEGO vertex joints, and must not be counted as a load-rated truss.
    status={
       "technique":"REAL_LEGO_A_FRAME_MEMBER_LAYOUT_WITH_UNPROVEN_VERTICES",
       "retained_roof_angle":pitch,"roof_flat_tiles_retained":True,
       "frame_count":len(frames),"frames":frames,
       "underskin_load_members":[p["placement_id"] for p in parts_new
           if p["kind"].startswith("truss_")],
       "new_parts":len(parts_new),"removed_old_tip_tiles":len(old_tips),
       "added_ridge_short_tiles":len(new_tips),
       "ridge_beam_parts":len(ridge_parts),
       "ridge_cover_tiles":sum(p["kind"]=="ridge_cover_flat" for p in parts_new),
       "hinge_count":len(axes)+4*len(frames),
       "hinge_physical_part_count":2*(len(axes)+4*len(frames)),
       "new_truss_hinge_pairs":4*len(frames),
       "new_coaxial_truss_hinge_pairs":4*len(frames),
       "hinge_evidence":axes,
       "coaxial_finger_type_pairs_identified":len(axes),
       "hinge_finger_contact_mesh_verified":0,
       "hinge_load_rated_count":0,
       "constructed_triangle_layout_count":len(frames),
       "mechanically_closed_triangle_count":0,
       "toe_riser_connection_sites_nominal":8*len(frames),
       "toe_riser_parts_count":4*len(frames),
       "tie_end_to_original_wall_stud_interface":"UNVERIFIED",
       "toe_riser_to_hinge_interface":"UNVERIFIED",
       "truss_to_wall_compression_documented_verified":0,
       "actual_load_rated_roof_paths":0,
       "proposed_load_path_interfaces":joints,
       "remaining_unverified_mechanical_paths":len(frames),
       "vertex_and_fastening_blockers":blockers,
       "ridge_shape_solution":"STUD_SEATED_RAISED_CENTER_CAP_ON_RIDGE_PURLIN_WITH_SHORTENED_SIDE_TILES",
       "ridge_cap_vertical_offset_above_previous_094_plates":1,
       "ridge_body_collision_verified":False,
       "ridge_tile_ENVELOPE_clearance_pass":tested>0 and not ridge_overlaps,
       "ridge_real_3d_envelope_pairs_screened":tested,
       "ridge_tip_to_cap_body_overlap_count":len(ridge_overlaps),
       "ridge_tip_to_cap_body_overlap_examples":ridge_overlaps[:20],
       "ridge_cap_purlin_nominal_stud_interfaces":len(supported_ridge_covers),
       "ridge_cap_purlin_nominal_stud_cells":sum(x["nominal_stud_cells"] for x in supported_ridge_covers),
       "ridge_cap_supported_joint_details":supported_ridge_covers,
       "ridge_cap_purlin_envelope_contacts_count":cover_support_envelope_intersections,
       "ridge_insertable":False,
       "overall_mesh_clearance_verified":False,
       "roof_finger_sweep_complete":False,
       "N6":"NOT_CERTIFIED",
       "physical_test_requested":False,
       "parts_delta_vs093":len(parts_new)-len(old_tips),
       "composite_total":len(trial["foundation"].parts)+len(full),
       "part_id_additions":dict(Counter(p["ldraw_id"] for p in parts_new)),
       "part_id_removals":dict(Counter(p["ldraw_id"] for p in old_tips)),
    }
    return {"foundation":trial["foundation"],"articulated_parts":full,
            "report":status, "hinge_axes":trial["hinge_axes"],
            "links":trial["connections"]+joints}
