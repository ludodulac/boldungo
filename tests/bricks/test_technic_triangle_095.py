"""095: real 5/12/13 pin joints, changed houses, rigid transforms and no fake wall proof."""
import math
import pytest
from brickhouse.bricks.technic_triangle_095 import (
    build_095, complete_technic_frame, beam, beam_matrix,PARTS095)

from brickhouse.bricks.brick_model import BrickModel, BrickModelPart


def other_building(dx=0,dy=0):
    """Independent 094-style second house without test-module imports."""
    def wall(pid,x):
        return BrickModelPart(placement_id=pid,part_id="BRICK_1X8",
            category="brick",component="wall",facade="front",
            x_studs=x+dx,y_studs=dy,z_plates=90,rotation_quarter_turns=0)
    terrain=BrickModelPart(placement_id="terrain",part_id="TERRAIN",
        category="terrain",component="facade_detail",facade="front",
        x_studs=dx,y_studs=dy,z_plates=0,rotation_quarter_turns=0)
    parts=[terrain,wall("left",8),wall("right",35)]
    for x in (6,35):
        for y in (0,2,4,6):
            parts.append(BrickModelPart(
                placement_id=f"EXPERIMENT-091-DECK-roof-{x}-{y}",
                part_id="BRICK_2X4",category="brick",component="roof_support",
                x_studs=x+dx,y_studs=y+dy,z_plates=93,rotation_quarter_turns=1))
    return BrickModel(building_id="OTHER-GABLE-095",volume_id="test",
            width_studs=65,depth_studs=28,height_plates=124,parts=parts)



def test_technics_real_hole_positions_and_rotations():
    p,h=beam((0,0),(12/13,-5/13),20,15,"32278","beam1")
    assert len(h)==15
    assert h[0]==(0.,0.,20)
    assert math.isclose(h[13][0],240,abs_tol=1e-6)
    assert math.isclose(h[13][1],-100,abs_tol=1e-6)
    assert h[14][0]>h[13][0]
    R=p["rotation"]
    assert all(math.isclose(sum(R[i][j]**2 for i in range(3)),1,
                          abs_tol=1e-7) for j in range(3))
    # Hole axis of official 32278 is local X, mapped to world Z.
    assert (R[0][0],R[1][0],R[2][0])==(0,0,1)


def test_first_triangle_has_actual_four_pinned_vertices_and_closed_loops():
    m=complete_technic_frame(index=0,bay=0,xcenter=40,
         eave_y=-776,ridge_y=-953,
         anchor_points={"negative":17,"positive":63})
    assert m["full_triangle_documented_type"] is True
    assert m["closed_right_triangles"]==2
    assert len(m["vertices"])==4
    assert {v["vertex"] for v in m["vertices"]}=={
         "LEFT_FOOT","RIGHT_FOOT","APEX","CENTER_TIE"}
    assert all(v["all_holes_coaxial"] for v in m["vertices"])
    assert all(v["pin_6558_spans_3L"] for v in m["vertices"])
    assert sum(p["ldraw_id"]=="6558" for p in m["parts"])==4
    assert sum(p["ldraw_id"]=="32278" for p in m["parts"])==6
    assert sum(p["ldraw_id"]=="32524" for p in m["parts"])==1
    assert m["grounded_wall_pin_count"]==0
    assert m["roof_supported_via_verified_interfaces"] is False


def test_full_real_other_house_replaces_unclosed_094_skeleton():
    before=other_building()
    frozen=before.model_dump_json()
    trial=build_095(before)
    assert before.model_dump_json()==frozen
    r=trial["report"]
    assert r["new_assembly_documented_triangle_count"]>=1
    assert r["new_assembly_unclosed_triangles"]==0
    assert r["wall_grounded_truss_count"]==0
    assert r["truss_to_roof_load_rated_paths"]==0
    assert r["physical_strength_certification"]=="NOT_CERTIFIED"
    assert r["angle_unchanged_degrees"]==22.
    assert r["old_total"]==len(trial["previous_094"]["foundation"].parts)+len(
        trial["previous_094"]["articulated_parts"])
    assert r["new_total"]==len(trial["foundation"].parts)+len(trial["articulated_parts"])
    assert all(not p["placement_id"].startswith(("094-tie-","094-rafter-",
                  "094-kingpost-","094-framehinge-","094-toe-riser-"))
               for p in trial["articulated_parts"])
    assert not any(p["placement_id"].startswith("EXPERIMENT-092")
                   for p in trial["articulated_parts"])


def test_other_translated_house_and_correct_quantity_delta():
    a=build_095(other_building())
    b=build_095(other_building(dx=9,dy=10))
    assert a["report"]["new_total"]==b["report"]["new_total"]
    assert a["report"]["new_assembly_documented_triangle_count"]==b["report"]["new_assembly_documented_triangle_count"]
    for x in (a,b):
        r=x["report"]
        assert r["new_total"]==r["old_total"]+r["net_delta"]
        assert sum(r["new_bom"].values())==r["new_technic_parts_added"]
        assert sum(r["removed_bom"].values())==r["old_094_trusses_removed_count"]


def test_bad_integer_anchor_span_is_rejected_not_invented():
    m=complete_technic_frame(index=0,bay=0,xcenter=40,
         eave_y=-776,ridge_y=-953,
         anchor_points={"negative":17.3,"positive":63})
    assert any(x["reason"]=="NO_INTEGER_TECHNIC_WALL_REACH"
               for x in m["remaining_blockers"] if isinstance(x,dict))
    assert m["grounded_wall_pin_count"]==0


def test_no_fake_labeled_assembly_as_physically_certified():
    r=build_095(other_building())["report"]
    assert r["every_technic_pin_hole_contact_documented_type"]
    assert r["wall_grounded_truss_count"]==0
    assert r["adequate_wall_load_paths_verified"]==0
    assert r["insertion_complete"]=="NOT_PROVEN"
    assert r["remaining_wall_anchoring_and_roof_transfer_blocked"]
