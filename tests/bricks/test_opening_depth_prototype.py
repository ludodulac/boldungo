from brickhouse.bricks.opening_depth_prototype import recess_opening_closure_for_prototype
from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.building.models import Facade


def _part(pid, category, x, y, *, opening="o1"):
    return BrickModelPart(
        placement_id=pid, part_id="BRICK_1X1" if category=="brick" else "WINDOW_1X2X2_60592",
        category=category, component="wall" if category=="brick" else "facade_detail",
        x_studs=x, y_studs=y, z_plates=0, rotation_quarter_turns=0,
        facade=Facade.FRONT, opening_id=None if category=="brick" else opening,
    )


def test_recess_moves_only_existing_closure_one_stud_inward():
    wall=_part("wall","brick",0,0)
    frame=_part("frame","window_frame",2,0)
    model=BrickModel(building_id="b",volume_id="v",width_studs=8,depth_studs=5,height_plates=9,parts=[wall,frame])
    out=recess_opening_closure_for_prototype(model,opening_id="o1")
    assert (out.parts[0].x_studs,out.parts[0].y_studs)==(0,0)
    assert (out.parts[1].x_studs,out.parts[1].y_studs)==(2,1)
    assert model.parts[1].y_studs==0


def test_recess_is_explicitly_bounded_to_one_stud_not_metric_inference():
    frame=_part("frame","window_frame",2,0)
    model=BrickModel(building_id="b",volume_id="v",width_studs=8,depth_studs=5,height_plates=9,parts=[frame])
    try:
        recess_opening_closure_for_prototype(model,opening_id="o1",depth_studs=2)
    except ValueError as exc:
        assert "exactly one stud" in str(exc)
    else:
        raise AssertionError("prototype must not accept arbitrary inferred depth")
