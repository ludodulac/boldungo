"""096: real roof bracket candidates with explicit non-certification."""
from collections import Counter
import math
from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.articulated_roof_093 import rotation
from brickhouse.bricks.roof_technic_transfer_096 import (
    _roof_bracket,_frame_rafter_holes,build_096,
    CANDIDATE_SEARCH_MAX_AXIS_RESIDUAL_LDU,
)


def independent_house(two_wall_studs=False,dx=0,dy=0):
    def part(pid,typ,kind,component,x,y,z,rotation_quarter_turns=0):
        return BrickModelPart(placement_id=pid,part_id=typ,
          category=kind,component=component,facade="front",
          x_studs=x+dx,y_studs=y+dy,z_plates=z,
          rotation_quarter_turns=rotation_quarter_turns)
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
    return BrickModel(building_id="OTHER-PINNED-GABLE-096",volume_id="test",
        width_studs=65,depth_studs=28,height_plates=124,parts=parts)


def test_independent_house_does_not_promote_unanchored_rafters():
    home=independent_house(two_wall_studs=False)
    saved=home.model_dump_json()
    b=build_096(home)
    r=b["report"]
    assert home.model_dump_json()==saved
    assert r["technic_frames"]>=1
    assert r["grounded_two_wall_frames"]==0
    assert r["documented_and_load_rated_roof_to_foundation_paths"]==0
    assert r["physical_certification"]=="NOT_CERTIFIED"
    assert r["roof_pitch_degrees"]==22.
    assert r["new_total"]==r["original_095_total"]+r["additional_real_parts"]


def test_independent_house_with_two_supported_walls_still_fails_closed():
    r=build_096(independent_house(two_wall_studs=True))["report"]
    assert r["grounded_two_wall_frames"]>=1
    assert r["frames_still_without_two_wall_anchors"]>=0
    assert r["physical_certification"]=="NOT_CERTIFIED"
    assert r["n4_load_path_proven"] is False
    assert r["n5_full_mount_sequence_proven"] is False
    assert r["pin_full_body_sweeps_verified"]==0


def test_roof_mounted_real_3700_two_studs_and_hole_world_z():
    rail={"placement_id":"093-negative-baseplate-0-0-16",
          "ldraw_id":"3460","xyz_ldu":[700.,-900.,10.],
          "rotation":rotation("negative",22)}
    frame={"bay":0,"frame":0}
    got,err=_roof_bracket(frame,[rail])
    assert err is None
    assert got["part"]["ldraw_id"]=="3700"
    assert got["stud_cells_local_rail_u"]==[17.5,18.5]
    assert got["rail_underside_offset_ldu"]==8.
    assert got["hole"][2]==10.
    assert got["part"]["rotation"][2][2]==1.


def test_missing_mounting_rail_cannot_be_assumed():
    got,err=_roof_bracket({"frame":1,"bay":8},[])
    assert got is None and err=="REAL_EIGHT_STUD_RAIL_MISSING"


def test_tolerances_not_silently_upgraded_to_n2():
    assert CANDIDATE_SEARCH_MAX_AXIS_RESIDUAL_LDU <=0.1
    r=build_096(independent_house(two_wall_studs=True))["report"]
    for row in r["candidate_details"]:
        if row.get("new_parts") is None and "axis_residual_ldu" in row:
            assert row["axis_exact"] == (row["axis_residual_ldu"] < 0.000001)
            if row["axis_residual_ldu"]>0:
                assert row["status"]=="REAL_PARTS_PLACED_AXIS_RESIDUAL_UNPROVEN"
    assert r["n6_strength_proven"] is False


def test_translated_house_preserves_counts_and_real_piece_ids():
    x=build_096(independent_house(two_wall_studs=True,dx=0,dy=0))
    y=build_096(independent_house(two_wall_studs=True,dx=6,dy=10))
    assert x["report"]["new_total"]==y["report"]["new_total"]
    assert x["report"]["roof_bracket_brace_candidate_chains"]==y["report"]["roof_bracket_brace_candidate_chains"]
    assert all(v["ldraw_id"] in {"3700","32524","2780"} for v in x["added_parts"])


def test_invalid_roof_slope_is_rejected():
    from pytest import raises
    with raises(ValueError,match="22_DEG"):
        build_096(independent_house(),pitch=18.0)
