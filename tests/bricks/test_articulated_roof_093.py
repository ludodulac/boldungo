"""093: actual LDraw rigid transform hinge roof and independent-house regression."""
from math import isclose
from brickhouse.bricks.brick_model import BrickModel,BrickModelPart
from brickhouse.bricks.articulated_roof_093 import (
    build_093,rotation,transform_pt,PIVOT_LOCAL)


def scene():
    return BrickModelPart(
        placement_id="scene-terrain",part_id="TERRAIN",category="terrain",
        component="facade_detail",facade="front",x_studs=0,y_studs=0,
        z_plates=0,rotation_quarter_turns=0)

def w(pid,x):
    return BrickModelPart(
        placement_id=pid,part_id="BRICK_1X8",category="brick",
        component="wall",facade="front",
        x_studs=x,y_studs=0,z_plates=90,rotation_quarter_turns=0)

def roof(pid,x,y,z=93):
    return BrickModelPart(placement_id="EXPERIMENT-091-DECK-"+pid,
       part_id="BRICK_2X4",category="brick",component="roof_support",
       x_studs=x,y_studs=y,z_plates=z,rotation_quarter_turns=1)

def second_house(dx=0,dy=0):
    parts=[scene(),w("left-wall",8),w("right-wall",35)]
    for x in (6,35):
        for y in (0,2,4,6):
            parts.append(roof(f"roof-{x}-{y}",x,y))
    house=BrickModel(building_id="INDEPENDENT-HOUSE",
       volume_id="other",width_studs=43,depth_studs=15,
       height_plates=125,parts=parts)
    if dx or dy:
        translated=[]
        for p in house.parts:
            translated.append(p.model_copy(update={
               "x_studs":p.x_studs+dx,
               "y_studs":p.y_studs+dy}))
        house=BrickModel.model_validate({**house.model_dump(mode="json"),
               "parts":[p.model_dump(mode="json") for p in translated]})
    return house


def test_4275b_4276b_actual_pivot_and_true_pitch():
    original=second_house()
    frozen=original.model_dump_json()
    obj=build_093(original,pitch=22.)
    assert original.model_dump_json()==frozen
    assert obj["report"]["physical_certification"]=="NOT_CERTIFIED"
    assert obj["report"]["slope_error_degrees"]==0
    hinges=obj["hinge_axes"]
    assert len(hinges)==16
    assert all(x["part_pair_real"]==["4275b","4276b"] for x in hinges)
    pos={p["placement_id"]:p for p in obj["articulated_parts"]}
    for h in hinges:
        a=transform_pt(pos[h["base"]],PIVOT_LOCAL)
        b=transform_pt(pos[h["roof"]],PIVOT_LOCAL)
        assert all(abs(x-y)<1e-5 for x,y in zip(a,b))
        assert h["finger_engagement"]=="UNVERIFIED_IN_MESH_AND_SWEEP"


def test_panel_is_inclined_and_covered_by_real_flat_tiles():
    obj=build_093(second_house())
    arts=obj["articulated_parts"]
    tile=[p for p in arts if p["kind"]=="roof_skin"]
    assert tile and all(p["ldraw_id"]=="87079" for p in tile)
    assert {p["side"] for p in tile}=={"negative","positive"}
    neg=[p for p in tile if p["side"]=="negative" and "-0-0" in p["placement_id"]]
    assert neg
    a=neg[0]["rotation"]
    assert a[1][0]<-0.3 # roof visibly climbs toward the ridge
    assert obj["report"]["roof_smooth_surface"] is True
    assert obj["report"]["roof_exterior_flat_plane_count"]==2
    assert obj["report"]["roof_091_and_092_microsteps_not_reused"] is True


def test_grounded_crossed_brick_sills_before_hinges():
    obj=build_093(second_house())
    report=obj["report"]
    assert report["new_structural_eave_sill_parts"]>0
    assert not report["unsupported_hinge_bearings"]
    assert all(p.part_id.startswith(("BRICK_","PLATE_"))
      for p in obj["foundation"].parts
      if p.placement_id.startswith("EXPERIMENT-093"))
    assert len(obj["foundation"].parts) > len(second_house().parts)-8


def test_translate_coordinates_and_smaller_span_no_fixed_house_ids():
    p=build_093(second_house(dx=9,dy=12),pitch=22)
    assert p["report"]["panel_length_studs"] in (16,20)
    assert p["report"]["coaxial_hinge_axis_pairs"]==16
    assert p["report"]["physical_certification"]=="NOT_CERTIFIED"


def test_unknown_pitch_must_fail_closed():
    import pytest
    with pytest.raises(ValueError,match="INCLINE_OUTSIDE"):
        build_093(second_house(),pitch=62.)


def test_staggered_skin_stud_part_types_and_exact_counts():
    o=build_093(second_house())
    counts=o["report"]["real_design_ids"]
    assert counts["4275b"]==16
    assert counts["4276b"]==16
    assert counts["87079"]>0
    assert counts["3460"]>0
    assert o["report"]["hinge_finger_engagement_proven"]==0
    assert o["report"]["roof_to_walls_load_rated_paths"]==0
    assert o["report"]["human_visual_approval"] is False
