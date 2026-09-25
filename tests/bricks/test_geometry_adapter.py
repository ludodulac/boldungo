import pytest

from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.catalog import create_m0_brick_catalog, create_standard_plate_catalog
from brickhouse.bricks.geometry_adapter import (
    CANONICAL_LDRAW_PARTS, UnmappedCanonicalPartError, analyze_brick_model_geometry,
    brick_model_part_to_instance, brick_model_part_transform,
)
from brickhouse.bricks.piece_capabilities import create_current_engine_capability_registry
from brickhouse.bricks.windows import VALIDATED_WINDOW_ASSEMBLIES
from brickhouse.building.models import Facade
from lego_geometry_engine import AABB, PartDefinition, Relation, check_collision


def _part(placement_id: str, part_id: str="BRICK_1X1", *, x=0,y=0,z=0,turns=0):
    return BrickModelPart(placement_id=placement_id,part_id=part_id,category="brick",component="wall",x_studs=x,y_studs=y,z_plates=z,rotation_quarter_turns=turns,facade=Facade.FRONT)


def _window_part(placement_id: str, part_id: str, *, x=0,y=0,z=0,turns=0,category="window_frame"):
    return BrickModelPart(placement_id=placement_id,part_id=part_id,category=category,component="facade_detail",x_studs=x,y_studs=y,z_plates=z,rotation_quarter_turns=turns,facade=Facade.FRONT)


def _roof_part(placement_id: str, *, side: str,x=0,y=0,z=0,turns=0,part_id="BRICK_SLOPED_45_2X4"):
    return BrickModelPart(placement_id=placement_id,part_id=part_id,category="roof_tile",component="roof",x_studs=x,y_studs=y,z_plates=z,rotation_quarter_turns=turns,roof_side=side)


def _ridge_part(placement_id: str, part_id="TILE_2X4", *, x=0,y=0,z=0,turns=0):
    return BrickModelPart(placement_id=placement_id,part_id=part_id,category="ridge_tile",component="roof",x_studs=x,y_studs=y,z_plates=z,rotation_quarter_turns=turns,roof_side="ridge")


def _box_definition(part_id,minimum,maximum,description=""):
    x0,y0,z0=minimum; x1,y1,z1=maximum
    p000=(x0,y0,z0);p001=(x0,y0,z1);p010=(x0,y1,z0);p011=(x0,y1,z1);p100=(x1,y0,z0);p101=(x1,y0,z1);p110=(x1,y1,z0);p111=(x1,y1,z1)
    triangles=((p000,p100,p101),(p000,p101,p001),(p010,p011,p111),(p010,p111,p110),(p000,p010,p110),(p000,p110,p100),(p001,p101,p111),(p001,p111,p011),(p000,p001,p011),(p000,p011,p010),(p100,p110,p111),(p100,p111,p101))
    return PartDefinition(part_id,triangles,AABB(minimum,maximum),description)


def _slope_definition(ldraw_id,width,length):
    return _box_definition(f"{ldraw_id}.dat",(-length*10.0,0.0,-(width*20.0-10.0)),(length*10.0,24.0,10.0),f"Slope {width} x {length}")


class FakeLibrary:
    def __init__(self): self.loaded=[]
    def load_part(self,part_id):
        self.loaded.append(part_id)
        for mapping in CANONICAL_LDRAW_PARTS.values():
            if mapping.ldraw_id==part_id:
                if mapping.placement_kind=="slope": return _slope_definition(part_id,mapping.width_studs,mapping.length_studs)
                return _box_definition(
                    f"{part_id}.dat",
                    (-mapping.length_studs*10.0,0.0,-mapping.width_studs*10.0),
                    (mapping.length_studs*10.0,mapping.height_plates*8.0,mapping.width_studs*10.0),
                    f"Part {mapping.width_studs} x {mapping.length_studs}",
                )
        raise FileNotFoundError(part_id)


def test_mapping_covers_standard_bricks_roof_slopes_ridge_tiles_and_windows():
    assert {b.id for b in create_m0_brick_catalog().bricks}.issubset(CANONICAL_LDRAW_PARTS)
    assert {p.id for p in create_standard_plate_catalog().bricks}.issubset(CANONICAL_LDRAW_PARTS)
    expected={
        "PLATE_1X1":"3024","PLATE_1X2":"3023b","PLATE_1X3":"3623",
        "PLATE_1X4":"3710","PLATE_1X6":"3666","PLATE_1X8":"3460",
        "TILE_2X2":"3068b","TILE_2X3":"26603","TILE_2X4":"87079",
        "BRICK_SLOPED_18_4X2":"30363","BRICK_SLOPED_33_3X6":"3939","BRICK_SLOPED_33_3X4":"3297","BRICK_SLOPED_33_3X2":"3298",
        "BRICK_SLOPED_45_2X4":"3037","BRICK_SLOPED_45_2X3":"3038","BRICK_SLOPED_45_2X2":"3039","BRICK_SLOPED_45_2X1":"3040b",
        "WINDOW_1X2X2_60592":"60592","GLASS_FOR_WINDOW_1X2X2_60601":"60601",
        "WINDOW_1X2X3_60593":"60593","GLASS_FOR_WINDOW_1X2X3_60602":"60602",
        "WINDOW_1X4X3_60594":"60594","GLASS_FOR_WINDOW_1X4X3_60603":"60603",
    }
    assert {k:CANONICAL_LDRAW_PARTS[k].ldraw_id for k in expected}==expected
    assert all(CANONICAL_LDRAW_PARTS[key].height_plates==1 for key in ("TILE_2X2","TILE_2X3","TILE_2X4","PLATE_1X1","PLATE_1X2","PLATE_1X3","PLATE_1X4","PLATE_1X6","PLATE_1X8"))
    approved_window_ids={part_id for assembly in VALIDATED_WINDOW_ASSEMBLIES for part_id in (assembly.frame_part_id,assembly.pane_part_id)}
    assert approved_window_ids.issubset(CANONICAL_LDRAW_PARTS)


def test_ldraw_mapping_covers_every_current_placement_approved_part():
    approved=create_current_engine_capability_registry().approved_ids()
    assert approved.issubset(CANONICAL_LDRAW_PARTS), sorted(approved-set(CANONICAL_LDRAW_PARTS))


def test_window_frame_and_pane_share_exact_ldraw_origin_and_nominal_height():
    for assembly in VALIDATED_WINDOW_ASSEMBLIES:
        frame=CANONICAL_LDRAW_PARTS[assembly.frame_part_id]
        pane=CANONICAL_LDRAW_PARTS[assembly.pane_part_id]
        assert (frame.width_studs,frame.length_studs,frame.height_plates)==(1,assembly.width_studs,assembly.height_bricks*3)
        assert (pane.width_studs,pane.length_studs,pane.height_plates)==(1,assembly.width_studs,assembly.height_bricks*3)
        frame_part=_window_part("frame",assembly.frame_part_id,x=5,y=7,z=12,turns=1)
        pane_part=_window_part("pane",assembly.pane_part_id,x=5,y=7,z=12,turns=1,category="window_pane")
        assert brick_model_part_transform(frame_part,frame)==brick_model_part_transform(pane_part,pane)


def test_grid_coordinates_convert_to_ldraw_center_and_negative_y_up():
    part=_part("p","BRICK_1X2",x=2,y=3,z=6);t=brick_model_part_transform(part,CANONICAL_LDRAW_PARTS[part.part_id])
    assert (t.matrix[0][3],t.matrix[1][3],t.matrix[2][3])==(50.0,-72.0,80.0)
    assert t.matrix[0][:3]==(0.0,0.0,-1.0) and t.matrix[2][:3]==(1.0,0.0,0.0)


def test_true_ldraw_1x2_axes_land_on_brickmodel_1x2_footprint():
    instance=brick_model_part_to_instance(_part("p","BRICK_1X2",x=2,y=3),FakeLibrary())
    assert (instance.bbox.minimum[0],instance.bbox.maximum[0])==pytest.approx((40.0,60.0))
    assert (instance.bbox.minimum[2],instance.bbox.maximum[2])==pytest.approx((60.0,100.0))


def test_quarter_turn_places_length_on_grid_x():
    part=_part("p","BRICK_1X4",x=2,y=3,turns=1);t=brick_model_part_transform(part,CANONICAL_LDRAW_PARTS[part.part_id])
    assert (t.matrix[0][3],t.matrix[2][3])==(80.0,70.0)
    assert t.matrix[0][:3]==(1.0,0.0,0.0) and t.matrix[2][:3]==(0.0,0.0,1.0)


def test_ridge_tile_uses_one_plate_height_and_standard_axis_conversion():
    instance=brick_model_part_to_instance(_ridge_part("ridge",x=4,y=6,z=30),FakeLibrary())
    assert (instance.bbox.minimum[0],instance.bbox.maximum[0])==pytest.approx((80.0,120.0))
    assert (instance.bbox.minimum[2],instance.bbox.maximum[2])==pytest.approx((120.0,200.0))
    assert instance.bbox.minimum[1]==pytest.approx(-248.0)
    assert instance.bbox.maximum[1]==pytest.approx(-240.0)


def test_adapter_preserves_placement_id_and_uses_verified_ldraw_id():
    lib=FakeLibrary();instance=brick_model_part_to_instance(_part("wall-000001"),lib)
    assert lib.loaded==["3005"] and instance.instance_id=="wall-000001"


def test_two_canonical_bricks_on_consecutive_courses_contact_without_collision():
    lib=FakeLibrary();lower=brick_model_part_to_instance(_part("lower",z=0),lib);upper=brick_model_part_to_instance(_part("upper",z=3),lib)
    assert check_collision(lower,upper) is Relation.CONTACT


@pytest.mark.parametrize("part_id",["BRICK_SLOPED_18_4X2","BRICK_SLOPED_33_3X6","BRICK_SLOPED_33_3X4","BRICK_SLOPED_33_3X2","BRICK_SLOPED_45_2X4","BRICK_SLOPED_45_2X3","BRICK_SLOPED_45_2X2","BRICK_SLOPED_45_2X1"])
def test_verified_slope_families_align_decentered_ldraw_bbox_to_grid(part_id):
    lib=FakeLibrary();mapping=CANONICAL_LDRAW_PARTS[part_id];instance=brick_model_part_to_instance(_roof_part("roof",side="negative",x=2,y=5,z=12,part_id=part_id),lib)
    assert instance.bbox.minimum[0]==pytest.approx(40.0) and instance.bbox.maximum[0]==pytest.approx((2+mapping.width_studs)*20.0)
    assert instance.bbox.minimum[2]==pytest.approx(100.0) and instance.bbox.maximum[2]==pytest.approx((5+mapping.length_studs)*20.0)
    assert instance.bbox.maximum[1]==pytest.approx(-96.0)
    assert instance.transform.vector((0.0,0.0,1.0))[0]==pytest.approx(1.0)


def test_positive_slope_reverses_rise_without_moving_footprint():
    instance=brick_model_part_to_instance(_roof_part("roof-pos",side="positive",x=7,y=1,z=9),FakeLibrary())
    assert (instance.bbox.minimum[0],instance.bbox.maximum[0])==pytest.approx((140.0,180.0))
    assert (instance.bbox.minimum[2],instance.bbox.maximum[2])==pytest.approx((20.0,100.0))
    assert instance.transform.vector((0.0,0.0,1.0))[0]==pytest.approx(-1.0)


def test_rotated_slope_aligns_when_ridge_runs_along_width_axis():
    instance=brick_model_part_to_instance(_roof_part("roof-rot",side="negative",x=3,y=4,z=6,turns=1),FakeLibrary())
    assert (instance.bbox.minimum[0],instance.bbox.maximum[0])==pytest.approx((60.0,140.0))
    assert (instance.bbox.minimum[2],instance.bbox.maximum[2])==pytest.approx((80.0,120.0))
    assert instance.transform.vector((0.0,0.0,1.0))[2]==pytest.approx(1.0)


def test_strict_mode_rejects_unmapped_parts_instead_of_guessing():
    model=BrickModel(building_id="b",volume_id="v",width_studs=2,depth_studs=2,height_plates=3,parts=[_part("unknown","UNVERIFIED_PART")])
    with pytest.raises(UnmappedCanonicalPartError): analyze_brick_model_geometry(model,FakeLibrary())


def test_partial_mode_is_explicitly_incomplete_and_never_valid():
    model=BrickModel(building_id="b",volume_id="v",width_studs=2,depth_studs=2,height_plates=3,parts=[_part("mapped"),_part("unknown","UNVERIFIED_PART",x=1)])
    result=analyze_brick_model_geometry(model,FakeLibrary(),strict=False)
    assert result.mapped_placements==("mapped",) and result.unmapped_placements==("unknown",)
    assert result.complete is False and result.valid is False
