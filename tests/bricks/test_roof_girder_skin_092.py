"""092: whole-roof assembly changes, stud interfaces, collision and noncertification."""
from brickhouse.bricks.brick_model import BrickModel,BrickModelPart
from brickhouse.bricks.roof_studdeck_designer_091 import design_standard_stud_roof_091
from brickhouse.bricks.roof_girder_skin_092 import design_braced_skin_092,_roof_cross_axis
import pytest


def wall(pid,x,y):
    return BrickModelPart(placement_id=pid,part_id="BRICK_2X4",
        category="brick",component="wall",facade="front",
        x_studs=x,y_studs=y,z_plates=0,rotation_quarter_turns=1)

def slope(pid,x,y,z=3):
    return BrickModelPart(placement_id=pid,part_id="BRICK_SLOPED_18_4X2",
        category="roof_tile",component="roof",roof_side="negative",
        x_studs=x,y_studs=y,z_plates=z,rotation_quarter_turns=0)

def build_other_house(dx=0,dy=0):
    originals=[wall("w-front",6+dx,0+dy),
              wall("w-rear",6+dx,6+dy)]
    originals += [slope("roof-"+str(y),6+dx,y+dy) for y in (0,2,4,6)]
    originals += [wall("w-extra",6+dx,12+dy),slope("roof-extra",6+dx,12+dy)]
    model=BrickModel(building_id="OTHER-SHED",
        volume_id="test",width_studs=60,depth_studs=35,height_plates=20,
        parts=originals)
    return design_standard_stud_roof_091(model)[1]


def test_actual_standard_stud_girder_replaces_ties_and_reuses_grounded_edges():
    source=build_other_house()
    before=source.model_dump_json()
    report,trial=design_braced_skin_092(source)
    assert source.model_dump_json()==before
    assert "EXPERIMENT-092-TRANSVERSE-GIRDER" in {
        p.placement_id for p in trial.parts}
    assert report["girder_span_studs"]==8
    assert len(report["girder_supported_end_ids"])>=2
    assert report["girder_load_capacity"].startswith("NO_SPAN")
    assert report["load_rated_connectors"]==0
    assert report["remaining_unproven_tension_dependent_roof_ids_count"]==10
    assert report["physical_certification"]=="NOT_CERTIFIED"


def test_skin_generates_real_standard_plates_with_matching_stud_interfaces():
    report,trial=design_braced_skin_092(build_other_house())
    assert report["skin_improved_deck_bricks"]>=1
    assert report["skin_plate_count"]==4*report["skin_improved_deck_bricks"]
    assert all(p.part_id in {"PLATE_1X1","PLATE_1X2"} for p in trial.parts
               if p.placement_id.startswith("EXPERIMENT-092-SKIN-"))
    assert report["skin_max_riser_plates_exposed"]==1
    assert report["smooth_zinc_equivalence"].startswith("NOT_ACHIEVED")
    assert report["pitch_error_degrees"]<0.21


def test_translation_does_not_hardcode_guided004_coordinates():
    report,trial=design_braced_skin_092(build_other_house(dx=9,dy=11))
    assert report["girder_span_studs"]==8
    assert report["skin_improved_deck_bricks"]>=1
    assert trial.building_id.endswith("-EXPERIMENTAL-092")


def test_wrong_tie_length_fails_closed():
    source=build_other_house()
    mutated=[p.model_copy(update={"part_id":"PLATE_1X6","width_studs":1,"length_studs":6,"height_plates":1})
             if p.placement_id.startswith("EXPERIMENT-091-TIE-")
             and not p.placement_id.startswith("EXPERIMENT-091-TIE-REINFORCE-")
             else p for p in source.parts]
    bad=BrickModel.model_validate({**source.model_dump(mode="json"),
                                  "parts":[p.model_dump(mode="json") for p in mutated]})
    with pytest.raises(ValueError,match="UNMODIFIED_TWO_LAYER"):
        design_braced_skin_092(bad)


def test_bom_is_exact_delta_between_full_experimental_model_variants():
    source=build_other_house()
    report,variant=design_braced_skin_092(source)
    old={p.placement_id:p for p in source.parts}
    new={p.placement_id:p for p in variant.parts}
    additions=[p for pid,p in new.items() if pid not in old]
    deleted=[p for pid,p in old.items() if pid not in new]
    assert len(additions)==len(report["added_parts"])
    assert len(deleted)==len(report["old_tie_parts_removed"])
    assert sum(x["quantity"] for x in report["bom_added"])==len(additions)
    assert sum(x["quantity"] for x in report["bom_removed"])==len(deleted)


def test_nonexistent_or_nonstandard_parts_cannot_enter_design():
    source=build_other_house()
    source.parts[0].part_id="UNDOCUMENTED"
    with pytest.raises(Exception):
        design_braced_skin_092(source)
