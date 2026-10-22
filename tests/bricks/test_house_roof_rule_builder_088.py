"""LEGO2-088: full-house ridge proposals are construction gated, not photo ops."""
import pytest

from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.roof_joint_module_087 import propose_two_slope_bridge_087
from brickhouse.bricks.house_roof_rule_builder_088 import construct_rule_based_roof_experiment_088


def _house(*, turns=0, gaps=0, sections=1, with_ridge=False, partial=False):
    pieces=[]
    for i in range(sections):
        pair=propose_two_slope_bridge_087(
            seam_gap_studs=gaps, roof_rotation=turns,
            x_studs=8+(i*2 if turns else 0),
            y_studs=8+(i*2 if not turns else 0))
        for part in pair.model.parts[:2]:
            pieces.append(part.model_copy(update={
                "placement_id": f"S{i}-{part.placement_id}"}))
        if with_ridge:
            # An existing 1-plate tile at precisely the same footprint
            # must be removed from EXPERIMENTAL COPY before replacing.
            cap=pair.model.parts[-1]
            pieces.append(BrickModelPart(
                placement_id=f"S{i}-existing-ridge",
                part_id="TILE_2X2" if gaps==0 else "TILE_2X3",
                category="ridge_tile",component="roof",roof_side="ridge",
                x_studs=cap.x_studs,y_studs=cap.y_studs,
                z_plates=cap.z_plates,
                rotation_quarter_turns=cap.rotation_quarter_turns))
    if partial:
        pieces.pop()
    return BrickModel(
        building_id="TEST-088-HOUSE",volume_id="test",
        width_studs=80,depth_studs=80,height_plates=50,
        parts=pieces)


@pytest.mark.parametrize("turns,gaps,expect_id",[
    (0,0,"BRICK_2X2"),(1,0,"BRICK_2X2"),
    (0,1,"BRICK_2X3"),(1,1,"BRICK_2X3"),
])
def test_four_documented_alignment_layouts_from_actual_house_roof(turns,gaps,expect_id):
    source=_house(turns=turns,gaps=gaps)
    before=source.model_dump_json()
    result,new=construct_rule_based_roof_experiment_088(source)
    assert result["candidate_caps_proposed"]==1
    assert result["roof_slope_parts_nominally_joined"]==2
    assert result["roof_slope_parts_not_yet_joined"]==0
    assert new is not None
    assert len(new.parts)==3
    assert len(source.parts)==2
    assert new.parts[-1].part_id==expect_id
    assert new.building_id.endswith("-EXPERIMENTAL-088")
    assert result["canonical_model_unchanged"] is True
    assert source.model_dump_json()==before
    assert result["construction_status"]=="BLOCKED_NOT_YET_BUILDABLE"
    assert result["physical_certification"]=="NOT_CERTIFIED"
    assert "NO_DOCUMENTED_30363_UNDERSIDE_TO_HOST_OR_WALL_LOAD_PATH" in result["first_order_blockers"]


@pytest.mark.parametrize("turns", [0,1])
def test_replaces_existing_identical_ridge_tile_only_in_experimental_copy(turns):
    original=_house(turns=turns,with_ridge=True)
    before=original.model_dump_json()
    result,new=construct_rule_based_roof_experiment_088(original)
    assert result["caps_replacing_identical_ridge_tiles"]==1
    assert result["candidate_caps_proposed"]==1
    assert len(new.parts)==len(original.parts)==3
    assert all(p.part_id!="TILE_2X2" for p in new.parts)
    assert any(p.part_id=="TILE_2X2" for p in original.parts)
    assert original.model_dump_json()==before


def test_many_roof_sections_synthesize_distinct_placement_ids_and_counts():
    original=_house(sections=3)
    result,new=construct_rule_based_roof_experiment_088(original)
    assert result["candidate_caps_proposed"]==3
    assert result["roof_slope_parts_nominally_joined"]==6
    assert new and len(new.parts)==9
    assert len({p.placement_id for p in new.parts})==9
    assert result["generated_experimental_part_count"]==9


def test_nonidentical_cover_blocks_replacement_instead_of_changing_real_house():
    original=_house(with_ridge=True)
    tile=original.parts[-1]
    tile.x_studs += 1
    before=original.model_dump_json()
    result,new=construct_rule_based_roof_experiment_088(original)
    assert new is None
    assert result["candidate_caps_proposed"]==0
    assert result["decision_counts"] == {"BLOCKED_EXISTING_RIDGE_MUST_BE_REDESSIGNED":1}
    assert original.model_dump_json()==before


def test_existing_orthogonal_solid_blocks_duplicate_material():
    house=_house()
    cap=propose_two_slope_bridge_087().model.parts[-1]
    house.parts.append(BrickModelPart(
        placement_id="obstruction",
        part_id="BRICK_1X1",category="brick",component="roof_support",
        x_studs=cap.x_studs,y_studs=cap.y_studs,z_plates=cap.z_plates,
        rotation_quarter_turns=0))
    result,new=construct_rule_based_roof_experiment_088(house)
    assert result["decision_counts"]["BLOCKED_EXISTING_SOLID_MATERIAL"]==1
    assert new is None


def test_distant_roof_course_cannot_be_misclassified_as_joinable_ridge():
    candidate=propose_two_slope_bridge_087()
    source=BrickModel.model_validate({
        "building_id":"TEST-FAR", "volume_id":"test",
        "width_studs":80, "depth_studs":80, "height_plates":60,
        "parts":[candidate.model.parts[0].model_dump(mode="json"), {
            **candidate.model.parts[1].model_dump(mode="json"),
            "x_studs":candidate.model.parts[1].x_studs+9}]})
    result,new=construct_rule_based_roof_experiment_088(source)
    assert result["candidate_caps_proposed"]==0
    assert new is None
    assert result["roof_slope_parts_not_yet_joined"]==2
    assert result["next_construction_choice"]=="SWITCH_TO_ANOTHER_DOCUMENTED_ROOF_TECHNIQUE"


def test_invalid_pair_budget_is_fail_closed():
    house=_house()
    for limit in (0,-1,1201):
        with pytest.raises(ValueError):
            construct_rule_based_roof_experiment_088(house,max_roof_pairs=limit)


def test_building_with_only_one_slope_has_no_invented_second_side():
    p=propose_two_slope_bridge_087().model.parts[0]
    house=BrickModel(building_id="ONE-SLOPE",volume_id="test",
                     width_studs=24,depth_studs=24,height_plates=12,
                     parts=[p])
    result,model=construct_rule_based_roof_experiment_088(house)
    assert model is None
    assert result["candidate_caps_proposed"]==0
    assert result["construction_status"]=="BLOCKED_NOT_YET_BUILDABLE"
