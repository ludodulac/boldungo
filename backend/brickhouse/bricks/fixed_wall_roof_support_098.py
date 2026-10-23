"""BOLDÜNGO 098: fixed stud-lapped wall-to-wall eave tie, not free Technic elbow.

First improve a real fixed *bearing* under the 093 eave hinges, then
separately prove (or FAIL to prove) a second bearing locking the 22° panel.
The transverse beam uses true 2x8 LEGO 3007 bricks on two verified grounded
walls, with 2x4 LEGO 3020 plates physically lapping all internal seams.
It replaces, in THIS variant only, one row of original 093 eave-sill masonry.
No collision with original sill rows is silently accepted.

The beam is fixed to its two eave wall supports; panel rotation about 4275b/
4276b remains FREE. It is dishonest to call it a complete N4 roof load path.
"""
from __future__ import annotations
from collections import Counter
from .triangular_frame_ridge_094 import build_094
from .technic_triangle_095 import I
from .articulated_roof_093 import rigid
from .roof_studdeck_designer_091 import _cells
from .support_chain import analyze_standard_brick_support_chain
from .catalog import standard_orthogonal_definitions
from .brick_model import BrickModel

D=standard_orthogonal_definitions()
STUD=20.
PLATE=8.
BRICKS={8:"3007",6:"2456",4:"3001",2:"3003"}
LAP="3020"


def grounded_masonry_under_sill(source,sill,grounded,bay):
    """Wall cells at the actual sill underside, not visual proximity."""
    two_y={(x,y) for x in range(sill.x_studs,sill.x_studs+2)
                   for y in (bay,bay+1)}
    candidates=[p for p in source.parts
       if p.placement_id in grounded and p.component=="wall" and p.part_id in D
       and p.z_plates+D[p.part_id].height_plates==sill.z_plates
       and _cells(p)&two_y]
    hits=sorted(set().union(*(_cells(p)&two_y for p in candidates))
                if candidates else [])
    if len(hits)<2:
        return None
    return {"wall_ids":[p.placement_id for p in candidates],
            "stud_cells":[list(h) for h in hits]}


def select_sill_pairs(source,foundation):
    grounded={n.placement_id for n in analyze_standard_brick_support_chain(source).nodes
             if n.reaches_ground}
    sills=[p for p in foundation.parts if
           p.placement_id.startswith("EXPERIMENT-093-EAVE-SILL-")]
    sides={"negative":sorted([p for p in sills if "-negative-" in p.placement_id],
                              key=lambda p:p.y_studs),
           "positive":sorted([p for p in sills if "-positive-" in p.placement_id],
                              key=lambda p:p.y_studs)}
    for item in sides.values():
        if not item:raise ValueError("098_REQUIRES_REAL_093_WALL_CROWNS")
    left=sides["negative"][0];right=sides["positive"][0]
    if left.z_plates!=right.z_plates or left.x_studs+2>=right.x_studs:
        raise ValueError("098_WALL_SUPPORT_GEOMETRY_INVALID")
    for a in range(max(left.y_studs,right.y_studs),
                   min(left.y_studs+D[left.part_id].footprint(0)[1],
                       right.y_studs+D[right.part_id].footprint(0)[1])-1):
        if a%2:continue
        candidates={}
        for side,rows in sides.items():
            sill=next((p for p in rows if
                      p.y_studs<=a and
                      a+2<=p.y_studs+D[p.part_id].footprint(0)[1]),None)
            if sill is None:break
            proof=grounded_masonry_under_sill(source,sill,grounded,a)
            if proof is None:break
            candidates[side]=(sill,proof)
        if len(candidates)==2:
            return a,candidates
    raise ValueError("NO_TWO_REAL_GROUNDED_WALLS_BELOW_SAME_EAVE_BAY")


def interlocking_runs(start,end):
    """Two-stud-compatible genuine LEGO bricks, fail on unfillable runs."""
    run=end-start
    if run<16 or run%2:raise ValueError("NO_MODULAR_TWO_WALL_TIE_SPAN")
    lengths=[]
    while run:
        n=next((x for x in (8,6,4,2) if x<=run),None)
        if n is None:raise ValueError("NO_AUTHENTIC_BRICK_SIZE_FITS")
        lengths.append(n);run-=n
    return lengths


def build_wall_tie(source, *, pitch=22.0, max_span_studs=40):
    pristine=source.model_dump_json()
    if abs(pitch-22)>1e-9:
        raise ValueError("098_ONLY_DOCUMENTED_22_DEG_REFERENCE")
    base=build_094(source,pitch=pitch)
    foundation=base["foundation"]
    eave_bay,sides=select_sill_pairs(source,foundation)
    l=sides["negative"][0];r=sides["positive"][0]
    x0=l.x_studs;xend=r.x_studs+2
    length=xend-x0
    if length>max_span_studs:
        raise ValueError("SPAN_TOO_LONG_WITHOUT_REAL_MIDSPAN_WALL")
    runs=interlocking_runs(x0,xend)
    zplate=l.z_plates
    pieces=[]; connections=[];old_sills=set()
    for side,(sill,proof) in sides.items():
        old_sills.add(sill.placement_id)
        h=D[sill.part_id].footprint(0)[1]
        for y in range(sill.y_studs,sill.y_studs+h):
            if y in (eave_bay,eave_bay+1):continue
            brick=rigid(f"098-{side}-retile-y{y}","3004",
                ((sill.x_studs+1)*STUD,-zplate*PLATE,(y+.5)*STUD),
                I,"roof098_real_wall_sill_retile")
            pieces.append(brick)
    current=x0
    transverse=[]
    for k,n in enumerate(runs):
        part=rigid(f"098-fixed-crossbeam-{k}",BRICKS[n],
                   ((current+n/2)*STUD,-zplate*PLATE,
                    (eave_bay+1)*STUD),I,"roof098_fixed_transverse_beam")
        pieces.append(part)
        transverse.append((current,current+n,part))
        current+=n
    seams=[]
    for i,(_,joint,beam) in enumerate(transverse[:-1]):
        # A real 2×4 plate centered on the stud row -2,-1,+0,+1.
        # It studs into both touching 2x8 bricks in two parallel rows.
        if joint-x0<4 or xend-joint<4:
            raise ValueError("LAP_OVERLAPS_OLD_EAVE_CAP")
        plate=rigid(f"098-beam-lap-{i}",LAP,
                     (joint*STUD,-(zplate+3)*PLATE,
                      (eave_bay+1)*STUD),
                     I,"roof098_studded_joint_lap")
        pieces.append(plate)
        seams.append(plate["placement_id"])
        for nbr in (transverse[i][2],transverse[i+1][2]):
            connections.append({"from":plate["placement_id"],
                                "to":nbr["placement_id"],
                                "interface":"REAL_2X4_PLATE_3020_TOP_STUDS_OF_TWO_3007",
                                "documented_stud_cells":4,
                                "interface_geometry":"INTEGER_GRID_EXACT",
                                "load_capacity_verified":False})
    # The original 093 eave-cap plates remain at precisely their old positions;
    # verify that the replacement end bricks carry the actual stud cells
    # under each one (not merely that a cap is nearby).
    caps=[p for p in foundation.parts
          if p.placement_id.startswith("EXPERIMENT-093-EAVE-CAP-")
          and p.z_plates==zplate+3]
    end_records=[]
    for side,(sill,proof) in sides.items():
        first=transverse[0][2] if side=="negative" else transverse[-1][2]
        needed={(x,y) for x in range(sill.x_studs,sill.x_studs+2)
                          for y in (eave_bay,eave_bay+1)}
        actual=[p for p in caps if
                "-"+side+"-" in p.placement_id and _cells(p)&needed]
        upper=set().union(*(_cells(p)&needed for p in actual)) if actual else set()
        if upper!=needed:
            raise ValueError("MISSING_REAL_EAVE_CAP_STUD_OVERLAP")
        end_records.append({"side":side,"replacement_beam":first["placement_id"],
              "wall_ids":proof["wall_ids"],"bottom_stud_cells":proof["stud_cells"],
              "roof_hinge_cap_ids":[p.placement_id for p in actual],
              "cap_supported_cells":[list(c) for c in sorted(upper)]})
        for wall in proof["wall_ids"]:
            connections.append({"from":wall,"to":first["placement_id"],
             "interface":"ORIGINAL_WALL_STUD_TO_REAL_CROSSBEAM_BRICK_3007",
             "documented_stud_cells":len(proof["stud_cells"]),
             "interface_geometry":"EXACT_MASONRY_GRID"})
        for cap in actual:
            connections.append({"from":first["placement_id"],
            "to":cap.placement_id,
            "interface":"REAL_CROSSBEAM_TOP_STUD_TO_EXISTING_EAVE_093_CAP_1X",
            "interface_geometry":"EXACT_MASONRY_GRID"})
    # Unlike 094 the old candidate A-frame is discarded: no free
    # articulated trusses masquerading as fixed wall supports.
    oldframeprefix=("094-tie-","094-rafter-","094-kingpost-",
                    "094-toe-riser-","094-framehinge-")
    kept=[p for p in base["articulated_parts"]
          if not p["placement_id"].startswith(oldframeprefix)]
    oldcount=len(base["articulated_parts"])-len(kept)
    # Keep historic 093 foundation caps and all architecture except
    # the replaced whole old sill brick pair (new rows exactly tile it).
    f=BrickModel.model_validate({**foundation.model_dump(mode="json"),
        "building_id":foundation.building_id+"-098-FIXED-WALL-CROSSBEAM",
        "parts":[p.model_dump(mode="json") for p in foundation.parts
                 if p.placement_id not in old_sills]})
    if source.model_dump_json()!=pristine:
        raise AssertionError("SOURCE_ARCHIVE_MODIFIED")
    overlay=kept+pieces
    ids=[p["placement_id"] for p in overlay]
    if len(set(ids))!=len(ids):
        raise AssertionError("ID_COLLISION_098")
    report={
        "source_parts":len(source.parts),
        "full_house_composite_parts":len(f.parts)+len(overlay),
        "pitch_degrees":pitch,"two_real_slopes_preserved":True,
        "original_094_frame_candidates_removed":oldcount,
        "historic_093_sill_bricks_removed":sorted(old_sills),
        "new_parts":len(pieces),
        "new_bom":dict(sorted(Counter(p["ldraw_id"] for p in pieces).items())),
        "fixed_crossbeam_segment_parts":len(transverse),
        "real_brick_course_lap_count":len(seams),
        "wall_to_wall_fixed_beam_chains":1,
        "roof_panels_with_secondary_nonhinge_bearing_proven":0,
        "roof_to_wall_complete_stable_paths_proven":0,
        "eave_module_hinged_wall_bearing_nominal":1,
        "span_studs":length,"unbraced_span_studs":length-4,
        "overlong_span_rejected_at_studs":max_span_studs,
        "bay":eave_bay,"wall_sides":end_records,
        "roof_hinge_pitch_fixity":"ROTATION_ABOUT_EAVE_HINGE_NOT_RESTRAINED",
        "wall_studs_and_lap_connections":connections,
        "stud_site_geometry_checked":True,
        "hinge_finger_engagement_and_insertion_verified":False,
        "complete_pin_insertions_verified":0,
        "beam_bending_stiffness_verified":False,
        "midspan_deflection_verified":False,
        "roof_lateral_sliding_prevention_verified":False,
        "ridge_purlin_ground_path_proven":False,
        "physical_strength":"NOT_CERTIFIED",
        "architecture_decision":"FIXED_TRANSVERSE_WALL_TIE_BUILT_BUT_SECOND_ROOF_BEARING_ABSENT"}
    return {"foundation":f,"articulated_parts":overlay,
            "fixed_parts":pieces,"fixed_beam_ids":[t[2]["placement_id"] for t in transverse],
            "graph":connections,"report":report}
