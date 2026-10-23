"""LEGO2-088 full ridge STRIP replacement, not unsafe one-cover-at-a-time."""
import pytest

from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.roof_joint_module_087 import propose_two_slope_bridge_087
from brickhouse.bricks.house_ridge_strip_retile_088 import retile_whole_ridge_088


def _ridge_house(segments, *, rotation=0, gap=0, long_tile_spans=()):
    parts=[]
    for i in range(segments):
        p=propose_two_slope_bridge_087(
            seam_gap_studs=gap,roof_rotation=rotation,
            x_studs=8+(i*2 if rotation else 0),
            y_studs=8+(i*2 if not rotation else 0))
        for part in p.model.parts[:2]:
            parts.append(part.model_copy(update={
                "placement_id":f"S{i}-{part.placement_id}"}))
    sample=propose_two_slope_bridge_087(
        seam_gap_studs=gap,roof_rotation=rotation)
    cap=sample.model.parts[-1]
    cursor=0
    for i,span in enumerate(long_tile_spans):
        assert span in (2,4)
        x=cap.x_studs+(cursor if rotation else 0)
        y=cap.y_studs+(cursor if not rotation else 0)
        parts.append(BrickModelPart(
            placement_id=f"EXISTING-COVER-{i}",
            part_id="TILE_2X4" if span==4 else "TILE_2X2",
            category="ridge_tile",component="roof",roof_side="ridge",
            x_studs=x,y_studs=y,z_plates=cap.z_plates,
            rotation_quarter_turns=rotation))
        cursor+=span
    return BrickModel(building_id="HOUSE-STRIP-088",volume_id="test",
        width_studs=80,depth_studs=80,height_plates=30,parts=parts)


@pytest.mark.parametrize("rotation,gap",[(0,0),(1,0),(0,1),(1,1)])
def test_two_new_caps_replace_one_old_four_long_tile_without_changing_original(rotation,gap):
    old=_ridge_house(2,rotation=rotation,gap=gap,long_tile_spans=(4,))
    source=old.model_dump_json()
    result,copy=retile_whole_ridge_088(old)
    assert result["nominal_candidate_pairs_checked"]==2
    assert result["proposed_cap_count"]==2
    assert result["replaced_old_ridge_tile_count"]==1
    assert result["delta_total"]==1
    assert result["rejected_site_count"]==0
    assert copy is not None and len(copy.parts)==len(old.parts)+1
    assert copy.building_id.endswith("-EXPERIMENTAL-RIDGE-088")
    assert "EXISTING-COVER-0" in {p.placement_id for p in old.parts}
    assert "EXISTING-COVER-0" not in {p.placement_id for p in copy.parts}
    assert result["must_not_issue_final_construction_notice"] is True
    assert result["user_physical_test_requested"] is False
    assert result["physical_certification"]=="NOT_CERTIFIED"
    assert old.model_dump_json()==source


def test_partial_four_long_tile_must_never_be_deleted():
    old=_ridge_house(1,long_tile_spans=(4,))
    before=old.model_dump_json()
    result,copy=retile_whole_ridge_088(old)
    assert copy is None
    assert result["proposed_cap_count"]==0
    assert result["replaced_old_ridge_tile_count"]==0
    assert result["rejected_site_count"]>=1
    assert "BLOCKED_UNCOVERED_OLD_RIDGE_STRIP" in {
        item["reason"] for item in result["rejected_sites"]}
    assert old.model_dump_json()==before


def test_parametric_real_house_sized_ridge_retiles_23_sections_and_12_old_covers():
    old=_ridge_house(23,long_tile_spans=(4,)*11+(2,))
    assert len(old.parts)==58
    result,copy=retile_whole_ridge_088(old)
    assert result["proposed_cap_count"]==23
    assert result["replaced_old_ridge_tile_count"]==12
    assert result["delta_total"]==11
    assert copy is not None and len(copy.parts)==69
    assert sum(p.part_id=="BRICK_2X2" for p in copy.parts)==23
    assert result["physical_certification"]=="NOT_CERTIFIED"


def test_existing_solid_orthogonal_part_prevents_partial_strip_replacement():
    old=_ridge_house(2,long_tile_spans=(4,))
    cap=propose_two_slope_bridge_087().model.parts[-1]
    old.parts.append(BrickModelPart(
        placement_id="SOLID-OBSTRUCTION",
        part_id="BRICK_1X1",category="brick",component="roof_support",
        x_studs=cap.x_studs,y_studs=cap.y_studs,z_plates=cap.z_plates,
        rotation_quarter_turns=0))
    before=old.model_dump_json()
    result,copy=retile_whole_ridge_088(old)
    assert result["proposed_cap_count"]==0
    assert result["replaced_old_ridge_tile_count"]==0
    assert copy is None
    assert old.model_dump_json()==before


def test_no_ridge_uses_nominal_top_studs_but_never_emits_build_ready_claim():
    old=_ridge_house(2)
    result,model=retile_whole_ridge_088(old)
    assert model is not None and result["proposed_cap_count"]==2
    assert result["replaced_old_ridge_tile_count"]==0
    assert result["house_status"]=="EXPERIMENTAL_NOT_READY_FOR_BUILDING"
    assert len(result["cannot_certify_due_to"])>=3
