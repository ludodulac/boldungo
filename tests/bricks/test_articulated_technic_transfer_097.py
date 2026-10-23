"""LEGO2-097 exact three pin joints, face stacking and explicit mobile joint."""
from math import hypot
import pytest
from brickhouse.bricks.articulated_technic_transfer_097 import (
    build_097, circle_elbows, thin_liftarm, check_three_axial_stacks,
    construct_one_exact_joint_chain)
from brickhouse.bricks.brick_model import BrickModel,BrickModelPart

def independent_house(two_wall_studs=False,dx=0,dy=0):
    def part(pid,typ,kind,component,x,y,z,turn=0):
        return BrickModelPart(placement_id=pid,part_id=typ,
            category=kind,component=component,
            facade=None if component=="roof_support" else "front",
            x_studs=x+dx,y_studs=y+dy,z_plates=z,
            rotation_quarter_turns=turn)
    parts=[part("terrain","TERRAIN","terrain","facade_detail",0,0,0)]
    for label,x in (("west",8),("east",35)):
        parts.append(part(label,"BRICK_1X8","brick","wall",x,0,90))
        if two_wall_studs:
            parts.append(part(label+"-inside","BRICK_1X8","brick","wall",
                              x+(1 if x==8 else -1),0,90))
    for x in (6,35):
        for y in (0,2,4,6):
            parts.append(part(f"EXPERIMENT-091-DECK-roof-{x}-{y}",
                         "BRICK_2X4","brick","roof_support",x,y,93,1))
    return BrickModel(building_id="OTHER-GABLE-097",volume_id="test",
           width_studs=65,depth_studs=28,height_plates=124,parts=parts)



def test_circles_reach_any_non_grid_endpoint_without_hole_fudging():
    a=(0.,0.); b=(120.0507923,0.)
    variants=circle_elbows(a,b)
    assert len(variants)==2
    for elbow in variants:
        assert abs(hypot(elbow[0]-a[0],elbow[1]-a[1])-80)<1e-8
        assert abs(hypot(elbow[0]-b[0],elbow[1]-b[1])-80)<1e-8


def test_invalid_spans_fail_before_placing_fictional_link():
    assert circle_elbows((0,0),(200,0))==[]
    with pytest.raises(ValueError,match="FOUR_INTERVALS"):
        thin_liftarm((0,0),(81,0),20,"wrong")


def test_authentic_thin_planes_do_not_overlap_real_studs_or_thick_beam():
    rows=check_three_axial_stacks((0,0,10),(120,0,50),25,35)
    assert len(rows)==3
    assert all(x["faces_touch_exactly"] for x in rows)
    assert all(x["pin_collar_must_occupy_exact_face"] for x in rows)
    with pytest.raises(ValueError):
        check_three_axial_stacks((0,0,10),(120,0,50),30,35)


def test_097_preserves_other_house_even_when_not_supported():
    house=independent_house(two_wall_studs=True)
    before=house.model_dump_json()
    built=build_097(house)
    r=built["report"]
    assert house.model_dump_json()==before
    assert r["geometrically_exact_roof_to_truss_to_wall_connector_chains"]==1
    assert r["new_max_joint_residual_ldu"]<1e-5
    assert r["new_total"]==r["previous_096_parts"]+sum(r["added_real_parts_by_ldraw"].values())-sum(r["removed_real_parts_by_ldraw"].values())
    assert r["added_real_parts_by_ldraw"] in ({"2780":3,"32017":2},{"2780":3,"32017":2,"3700":1})
    assert r["removed_real_parts_by_ldraw"] in ({"2780":2,"32524":1},{})
    assert r["roof_pitch_degrees"]==22
    assert not r["kinematically_stable"]
    assert not r["n4_stability"]
    assert not r["n5_full_insertion"]
    assert r["physical_certification"]=="NOT_CERTIFIED"
    added=built["new_subassembly"]["new_parts"]
    assert sorted(p["ldraw_id"] for p in added) in (["2780"]*3+["32017"]*2,["2780"]*3+["32017"]*2+["3700"])
    ids={p["placement_id"] for p in built["articulated_parts"]}
    assert not any(k in ids for k in built["new_subassembly"]["remove_ids"])
    assert all(k in ids for k in [p["placement_id"] for p in added])


def test_097_second_house_translation_retains_reversible_shape():
    a=build_097(independent_house(two_wall_studs=True,dx=0,dy=0))
    b=build_097(independent_house(two_wall_studs=True,dx=9,dy=7))
    for x in (a,b):
        assert x["report"]["two_walls_grounded_frames"]>=1
        assert x["report"]["mechanically_stable_roof_to_wall_load_paths"]==0
        assert x["report"]["complete_insertion_sweeps_verified"]==0
    assert a["report"]["new_total"]==b["report"]["new_total"]


def test_097_refuses_fake_wall_support():
    without=independent_house(two_wall_studs=False)
    with pytest.raises(ValueError,match="NO_GROUNDED_FRAME"):
        build_097(without)


def test_097_pin_center_axes_and_link_exterior_are_true_LDRAW_poses():
    b=build_097(independent_house(two_wall_studs=True))
    actual=b["new_subassembly"]
    assert len(actual["new_parts"]) in (5,6)
    assert actual["hinge_joint_count"]==3
    assert actual["hole_axis_residual_max_ldu"]<1e-5
    assert actual["kinematics"]=="TWO_LINK_1_DOF_UNBRACED_ELBOW"
    assert not actual["compression_stable"]
    assert not actual["collar_path_free_verified"]
    assert all(x["faces_touch_exactly"] for x in actual["three_axial_stack_evidence"])
    assert {e["axis_exact"] for e in actual["edges"]}=={True}
