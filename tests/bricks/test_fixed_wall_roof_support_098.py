"""098 authentic LDraw axis and fixed wall-to-wall LEGO support regression."""
import pytest
from brickhouse.bricks.brick_model import BrickModel,BrickModelPart
from brickhouse.bricks.fixed_wall_roof_support_098 import (
  build_wall_tie,select_sill_pairs,interlocking_runs)
from brickhouse.bricks.technic_official_axes_098 import (
 OFFICIAL_TYPE1,part_local_axis,physical_axes,type1_matrix,transform,
 corrected_technic_part,real_pin_rotation,real_beam_rotation,
 correct_legacy_096_overlay,actual_world_axis)
from brickhouse.bricks.technic_triangle_095 import beam_matrix,PIN_MATRIX
from brickhouse.bricks.roof_technic_transfer_096 import build_096
from brickhouse.bricks.triangular_frame_ridge_094 import build_094


def independent_house(two_walls=True,dx=0,dy=0):
    def part(pid,typ,kind,component,x,y,z,turn=0):
        return BrickModelPart(placement_id=pid,part_id=typ,category=kind,
         component=component,facade=None if component=="roof_support" else "front",
         x_studs=x+dx,y_studs=y+dy,z_plates=z,rotation_quarter_turns=turn)
    parts=[part("terrain","TERRAIN","terrain","facade_detail",0,0,0)]
    for name,x in (("west",8),("east",35)):
        parts.append(part(name,"BRICK_1X8","brick","wall",x,0,90))
        if two_walls:
            parts.append(part(name+"-inside","BRICK_1X8","brick","wall",
                              x+(1 if x==8 else -1),0,90))
    for x in (6,35):
        for y in (0,2,4,6):
            parts.append(part(f"EXPERIMENT-091-DECK-roof-{x}-{y}",
                         "BRICK_2X4","brick","roof_support",x,y,93,1))
    return BrickModel(building_id="ACTUAL_SECOND_HOUSE_098",volume_id="test",
        width_studs=65,depth_studs=28,height_plates=124,parts=parts)

def test_official_5_independent_DAT_sources_each_y_resolved_correctly():
    expected={"32278":(0.,1.,0.),"32524":(0.,-1.,0.),
              "32017":(0.,1.,0.),"2780":(1.,0.,0.),"6558":(1.,0.,0.)}
    assert physical_axes()==expected
    for code,part in OFFICIAL_TYPE1.items():
        assert part["url"].endswith("/"+code+".dat")
        assert len(type1_matrix(part["reference"]))==3
        assert len(part_local_axis(code))==3

def test_pins_OLD_097_identity_as_local_z_FAILS_TRUE_AXIS():
    for code in ("2780","6558"):
        assert transform(((1.,0.,0.),(0.,1.,0.),(0.,0.,1.)),part_local_axis(code))!=(0.,0.,1.)
        assert transform(real_pin_rotation(),part_local_axis(code))==(0.,0.,1.)

def test_historic_095_pin_matrix_cannot_engage_actual_holes():
    assert transform(PIN_MATRIX,part_local_axis("2780"))!=(0.,0.,1.)
    assert transform(PIN_MATRIX,part_local_axis("6558"))!=(0.,0.,1.)

def test_historic_095_beam_matrix_cannot_engage_actual_holes():
    old=beam_matrix((12/13,-5/13))
    assert transform(old,part_local_axis("32278"))!=(0.,0.,1.)
    assert transform(real_beam_rotation((12/13,-5/13)),part_local_axis("32278"))==(0.,0.,1.)

def test_all_real_technic_parts_have_correct_new_rotations_and_preserved_center():
    from brickhouse.bricks.articulated_roof_093 import rigid
    for code in OFFICIAL_TYPE1:
        p=rigid("part-"+code,code,(100.,-700.,50.),
                beam_matrix((12/13,-5/13)) if code not in ("2780","6558")
                else PIN_MATRIX,"test")
        q,changed=corrected_technic_part(p)
        assert changed is True
        assert q["xyz_ldu"]==p["xyz_ldu"]
        axis=actual_world_axis(q)
        assert axis[0]==0. and axis[1]==0. and abs(axis[2])==1.

def test_096_F6_beam_and_pin_have_wrong_old_AXES_and_are_repaired():
    old=build_096(independent_house())
    source_old=old["articulated_parts"]
    fix,report=correct_legacy_096_overlay(source_old)
    assert report["corrected_count"]>0
    assert report["wrong_before"]
    assert report["contains_uncorrected_096_F6"] is False
    assert any(k.startswith("096-F0-brace") for k in report["corrected_ids"])
    for obj in fix:
        if obj["placement_id"].startswith(("095-F","096-F")) and obj["ldraw_id"] in OFFICIAL_TYPE1:
            axis=test_transform_matrix_of_LDraw_part(obj)
            assert axis[0]==0. and axis[1]==0. and abs(axis[2])==1.
    assert len(fix)==len(source_old)

def test_wall_bridge_uses_only_actual_lappable_lengths():
    assert interlocking_runs(8,36)==[8,8,8,4]
    assert interlocking_runs(8,40)==[8,8,8,8]
    with pytest.raises(ValueError,match="NO_MODULAR"):
        interlocking_runs(8,39)

def test_second_house_experiment_fixed_beam_and_wall_not_just_contact():
    m=independent_house();snapshot=m.model_dump_json()
    x=build_wall_tie(m)
    r=x["report"]
    assert m.model_dump_json()==snapshot
    assert r["wall_to_wall_fixed_beam_chains"]==1
    assert r["real_brick_course_lap_count"]>=2
    assert r["span_studs"]>=16
    assert r["eave_module_hinged_wall_bearing_nominal"]==1
    assert r["roof_panels_with_secondary_nonhinge_bearing_proven"]==0
    assert r["roof_to_wall_complete_stable_paths_proven"]==0
    assert r["physical_strength"]=="NOT_CERTIFIED"
    assert r["two_real_slopes_preserved"]
    assert r["full_house_composite_parts"]==len(x["foundation"].parts)+len(x["articulated_parts"])
    assert set(r["new_bom"]).issubset({"3007","3001","3003","2456","3020","3004"})
    assert all(y["wall_ids"] and len(y["bottom_stud_cells"])>=2 for y in r["wall_sides"])
    assert any(c["interface"]=="REAL_2X4_PLATE_3020_TOP_STUDS_OF_TWO_3007"
               for c in x["graph"])

def test_second_house_can_be_translated_and_still_grounded():
    a=build_wall_tie(independent_house(dx=0,dy=0))
    b=build_wall_tie(independent_house(dx=6,dy=8))
    assert a["report"]["span_studs"]==b["report"]["span_studs"]
    assert a["report"]["real_brick_course_lap_count"]==b["report"]["real_brick_course_lap_count"]

def test_second_house_missing_wall_cells_must_fail_closed():
    with pytest.raises(ValueError,match="NO_TWO_REAL_GROUNDED"):
        build_wall_tie(independent_house(two_walls=False))

def test_reject_unbraced_overlong_house():
    with pytest.raises(ValueError,match="SPAN_TOO_LONG"):
        build_wall_tie(independent_house(),max_span_studs=16)

def test_reject_other_pitch_not_silently_built():
    with pytest.raises(ValueError,match="22_DEG"):
        build_wall_tie(independent_house(),pitch=18)

def test_no_094_mobile_trusses_in_fixed_house():
    a=build_wall_tie(independent_house())
    assert not any(p["placement_id"].startswith(("094-tie-","094-rafter-","094-kingpost-",
                                                 "094-toe-riser-","094-framehinge-"))
                   for p in a["articulated_parts"])
    assert sum(1 for p in a["articulated_parts"]
               if p["kind"]=="roof098_fixed_transverse_beam")>=2
