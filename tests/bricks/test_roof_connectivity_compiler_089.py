"""LEGO2-089: roof connector dependencies, not simulated physical strength."""
from pathlib import Path
import pytest

from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.roof_connectivity_compiler_089 import (
    _underface_30363_stud_candidate,
    compile_roof_connections_089,
)
from brickhouse.bricks.roof_joint_module_087 import propose_two_slope_bridge_087


def wall(pid, x, y, z=0, rotation=1):
    return BrickModelPart(
        placement_id=pid, part_id="BRICK_1X8",
        category="brick", component="wall", facade="front",
        x_studs=x, y_studs=y, z_plates=z,
        rotation_quarter_turns=rotation,
    )


def slope(pid, x, y, z, side="negative"):
    return BrickModelPart(
        placement_id=pid, part_id="BRICK_SLOPED_18_4X2",
        category="roof_tile", component="roof", roof_side=side,
        x_studs=x, y_studs=y, z_plates=z,
        rotation_quarter_turns=0,
    )


def house(parts):
    return BrickModel(
        building_id="89-TEST-SHELL",volume_id="test-volume",
        width_studs=40,depth_studs=40,height_plates=40,parts=parts,
    )


def test_nominal_30363_to_wall_and_two_more_roof_courses_compile_in_order():
    bottom=wall("ground",16,2)
    a=slope("a",14,2,3)
    b=slope("b",17,2,6)
    c=slope("c",20,2,9)
    model=house([bottom,a,b,c])
    before=model.model_dump_json()
    report=compile_roof_connections_089(model)
    assert report["roof_slope_parts"]==3
    assert report["roof_slope_grounded_nominal"]==3
    assert report["roof_slope_still_without_grounded_nominal_path"]==0
    assert report["nominal_slope_order_after_wall_assembly"]==["a","b","c"]
    assert all(row["status"]=="NOMINAL_TWO_STUD_PATH_TO_WALL_ONLY"
               for row in report["nominal_roof_stud_rows"])
    assert report["nominal_roof_stud_rows"][0]["grounded_lower_ids"]==["ground"]
    assert report["nominal_roof_stud_rows"][1]["grounded_lower_ids"]==["a"]
    assert report["nominal_roof_stud_rows"][2]["grounded_lower_ids"]==["b"]
    assert report["steps_mechanically_certified"]==0
    assert report["design_gate"].startswith("HOUSE_CONSTRUCTION_DENIED")
    assert report["physical_certification"]=="NOT_CERTIFIED"
    assert model.model_dump_json()==before


def test_current_real_eave_reviewed_sites_not_promoted_to_clutch():
    a=slope("roof-000002",14,2,93)
    assert _underface_30363_stud_candidate(a,16,2,93)=="LDRAW_REVIEWED_FINAL_POSE_060U_GENERALIZED"
    assert _underface_30363_stud_candidate(a,17,2,93)=="LDRAW_REVIEWED_FINAL_POSE_060U_GENERALIZED"
    assert _underface_30363_stud_candidate(a,14,2,93)=="GEOMETRY_HYPOTHESIS_REAR_CAVITY"
    assert _underface_30363_stud_candidate(a,15,2,93) is None


def test_unanchored_slope_rejected_even_if_nominally_stacked_on_it():
    a=slope("a",14,2,3)
    b=slope("b",17,2,6)
    report=compile_roof_connections_089(house([a,b]))
    assert report["roof_slope_grounded_nominal"]==0
    by_id={x["placement_id"]:x for x in report["nominal_roof_stud_rows"]}
    assert by_id["a"]["status"]=="NO_DOCUMENTED_LOWER_STUD_SITE"
    assert by_id["b"]["status"]=="LOWER_STUDS_PRESENT_NO_GROUNDED_PATH"
    assert by_id["b"]["candidate_lower_ids"]==["a"]


def test_single_stud_cannot_pass_support_threshold():
    a=wall("ground",16,2)
    b=slope("a",14,2,3)
    # Shift one wide wall? Here 1x8 overlaps x16 and 17 two sites.
    # Instead use one true 1x1 wall stud at x16,y2.
    single=BrickModelPart(
        placement_id="only_one",part_id="BRICK_1X1",
        category="brick",component="wall",facade="front",
        x_studs=16,y_studs=2,z_plates=0,rotation_quarter_turns=0)
    r=compile_roof_connections_089(house([single,b]))
    assert r["nominal_roof_stud_rows"][0]["status"]=="ONE_STUD_NOT_A_STABLE_PATH"
    assert r["roof_slope_grounded_nominal"]==0


def test_lower_wall_floating_at_non_ground_z_cannot_claim_grounded_path():
    floating=wall("floating",16,2,z=3)
    a=slope("a",14,2,6)
    r=compile_roof_connections_089(house([floating,a]))
    assert r["grounded_masonry_wall_ids"]==0
    assert r["roof_slope_grounded_nominal"]==0


def test_no_stud_top_contact_if_30363_upside_insertion_plane_wrong():
    a=slope("a",14,2,3)
    assert _underface_30363_stud_candidate(a,16,2,6) is None
    assert _underface_30363_stud_candidate(a,14,4,3) is None
    assert _underface_30363_stud_candidate(a,14,2,2) is None


def test_candidate_087_cap_does_not_become_an_approved_loaded_roof():
    c=propose_two_slope_bridge_087()
    r=compile_roof_connections_089(c.model)
    assert r["roof_slope_grounded_nominal"]==0
    assert len(r["ridge_caps"])==1
    cap=r["ridge_caps"][0]
    assert cap["status"]=="CAP_STUD_ALIGNMENT_ONLY_NO_COMPLETE_GROUND_PATH"
    assert all(len(v)==2 for v in cap["stud_cells_by_side"].values())
    assert r["physical_certification"]=="NOT_CERTIFIED"


def test_budget_rejects_unbounded_models_and_empty_budget():
    m=house([slope("a",14,2,3),slope("b",17,2,6)])
    with pytest.raises(ValueError,match="bounded"):
        compile_roof_connections_089(m,max_roof_slopes=1)
    with pytest.raises(ValueError):
        compile_roof_connections_089(m,max_roof_slopes=0)


def test_translation_invariant_30363_underside_connection():
    src=slope("a",14,2,93)
    target=slope("b",114,22,153)
    old=_underface_30363_stud_candidate(src,16,2,93)
    new=_underface_30363_stud_candidate(target,116,22,153)
    assert old==new=="LDRAW_REVIEWED_FINAL_POSE_060U_GENERALIZED"


def test_real_guided004_experimental_if_present_is_not_mutated():
    p=Path("artifacts/lego2-088-guided004-EXPERIMENTAL/GUIDED-004-EXPERIMENTAL-NOT-CERTIFIED.json")
    if not p.is_file():
        pytest.skip("real experimental GUIDED-004 not in this checkout")
    model=BrickModel.model_validate_json(p.read_text(encoding="utf-8"))
    assert len(model.parts)==1901
    before=model.model_dump_json()
    report=compile_roof_connections_089(model)
    assert report["roof_slope_parts"]==408
    assert report["roof_slope_grounded_nominal"]<=408
    assert len(report["ridge_caps"])==23
    assert report["source_model_mutated"] is False
    assert model.model_dump_json()==before
