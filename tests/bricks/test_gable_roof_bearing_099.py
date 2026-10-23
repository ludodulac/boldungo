"""099 tests: gables cannot be invented and near-contact cannot certify N4."""
from math import radians,sin,cos
from brickhouse.bricks.brick_model import BrickModel,BrickModelPart
from brickhouse.bricks.gable_roof_bearing_099 import build_099,gable_inventory,_underside_at_cross_x

def other_house(with_fake_gable=False,dx=0,dy=0):
    def part(pid,typ,kind,comp,x,y,z,turn=0,facade="front"):
        return BrickModelPart(placement_id=pid,part_id=typ,category=kind,
           component=comp,facade=facade if comp!="roof_support" else None,
           x_studs=x+dx,y_studs=y+dy,z_plates=z,rotation_quarter_turns=turn)
    pieces=[part("ground","TERRAIN","terrain","facade_detail",0,0,0)]
    for key,x in (("west",8),("east",35)):
        pieces.append(part(key,"BRICK_1X8","brick","wall",x,0,90))
        pieces.append(part(key+"-inside","BRICK_1X8","brick","wall",
                           x+(1 if x==8 else -1),0,90))
    for x in (6,35):
        for y in (0,2,4,6):
            pieces.append(part(f"EXPERIMENT-091-DECK-roof-{x}-{y}",
                         "BRICK_2X4","brick","roof_support",x,y,93,1))
    if with_fake_gable:
        pieces.append(part("gable-FLOATING-FRONT","BRICK_1X2","brick","wall",
                           22,2,110,facade="front"))
    return BrickModel(building_id="SECOND-HOUSE-099",volume_id="test",
        width_studs=65,depth_studs=28,height_plates=124,parts=pieces)

def test_second_house_missing_gable_is_not_silently_generated():
    m=other_house()
    before=m.model_dump_json()
    q=build_099(m)
    assert m.model_dump_json()==before
    r=q["report"]
    assert r["facades"]["front"]["gable_piece_count"]==0
    assert r["added_3024_gable_plates"]==0
    assert r["roof_panels_with_two_restrained_fixed_supports"]==0
    assert r["roof_to_wall_two_support_N4_paths"]==0
    assert r["N6"]=="NOT_CERTIFIED"

def test_unfounded_fake_gable_does_not_create_a_support():
    q=build_099(other_house(with_fake_gable=True))
    r=q["report"]
    assert r["facades"]["front"]["gable_piece_count"]==1
    assert r["facades"]["front"]["grounded_gable_piece_count"]==0
    assert r["added_3024_gable_plates"]==0
    assert r["gable_blocker"]=="NO_GROUNDED_FRONT_GABLE"

def test_translated_second_house_cannot_invent_gable_masonry():
    for dx,dy in ((0,0),(7,10),(5,8)):
        r=build_099(other_house(dx=dx,dy=dy))["report"]
        assert not r["real_grounded_gable_detected"]
        assert r["added_3024_gable_plates"]==0

def test_actual_3460_underface_uses_exact_sloped_transform_not_horizontal():
    c,s=cos(radians(22)),sin(radians(22))
    rail={"xyz_ldu":[100.,-800.,50.],
          "rotation":[[c,s,0],[-s,c,0],[0,0,1]]}
    y0,_=_underside_at_cross_x(rail,100.)
    y1,_=_underside_at_cross_x(rail,120.)
    assert abs((y1-y0)+20*s/c)<1e-6

def test_no_certified_load_path_from_vertical_plate_to_inclined_roof():
    r=build_099(other_house())["report"]
    assert not r["pedestal_is_positive_engagement_to_22deg_roof"]
    assert r["remaining_roof_hinge_rotation_upward"]
    assert not r["full_pin_clutch_insertion_verified"]
    assert r["structural_decision"]=="STOP_NO_SECOND_POSITIVELY_LOCKED_GABLE_ROOF_INTERFACE"

def test_independent_second_point_requires_nonzero_lever_arm():
    # Actual GUIDED004 is asserted in workflow; no synthetic gable is used
    # to counterfeit the roof/gable interface.
    q=build_099(other_house(with_fake_gable=True))
    assert q["report"]["pedestal"] is None
    assert q["report"]["roof_panels_with_two_restrained_fixed_supports"]==0
