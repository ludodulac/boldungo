"""LEGO2-094: independent-house real LDraw truss/ridge structural proposal."""
from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.triangular_frame_ridge_094 import build_094
from brickhouse.bricks.articulated_roof_093 import transform_pt,PIVOT_LOCAL
import pytest


def other_building(dx=0,dy=0):
    def wall(pid,x):
        return BrickModelPart(placement_id=pid,part_id="BRICK_1X8",
          category="brick",component="wall",facade="front",
          x_studs=x+dx,y_studs=dy,z_plates=90,rotation_quarter_turns=0)
    parts=[wall("support-negative",8),wall("support-positive",35)]
    for x in (6,35):
        for y in (0,2,4,6):
            parts.append(BrickModelPart(
               placement_id=f"EXPERIMENT-091-DECK-roof-{x}-{y}",
               part_id="BRICK_2X4",category="brick",component="roof_support",
               x_studs=x+dx,y_studs=y+dy,z_plates=93,
               rotation_quarter_turns=1))
    return BrickModel(building_id="OTHER-GABLE-094",volume_id="test",
            width_studs=65,depth_studs=28,height_plates=124,parts=parts)


def test_other_house_has_real_new_truss_and_nonfictional_roof_ridge():
    m=other_building()
    before=m.model_dump_json()
    obj=build_094(m)
    assert m.model_dump_json()==before
    report=obj["report"]
    assert report["frame_count"]>=2
    assert report["new_parts"]>0
    assert report["constructed_triangle_layout_count"]>=2
    assert report["mechanically_closed_triangle_count"]==0
    assert report["ridge_beam_parts"]>=1
    assert report["ridge_cover_tiles"]>=1
    assert report["removed_old_tip_tiles"]==len([
         p for p in obj["articulated_parts"] if p["placement_id"].startswith("094-short")])
    assert report["retained_roof_angle"]==22.
    assert report["N6"]=="NOT_CERTIFIED"
    assert report["actual_load_rated_roof_paths"]==0


def test_real_hinge_complementary_family_and_axis_orientation():
    obj=build_094(other_building())
    rows=obj["report"]["hinge_evidence"]
    assert rows and len(rows)==16
    assert all(x["axes_parallel_or_antiparallel"] for x in rows)
    assert all(x["complementary_three_plus_two_fingers"] for x in rows)
    assert all(not x["finger_surface_mesh_sweep_verified"] for x in rows)
    assert obj["report"]["hinge_finger_contact_mesh_verified"]==0


def test_independent_house_translation_preserves_ridge_and_frame_design():
    a=build_094(other_building())
    b=build_094(other_building(dx=9,dy=10))
    assert b["report"]["frame_count"]==a["report"]["frame_count"]
    assert b["report"]["ridge_beam_parts"]==a["report"]["ridge_beam_parts"]
    assert b["report"]["composite_total"]==a["report"]["composite_total"]


def test_catalog_only_and_part_quantity_accounting():
    obj=build_094(other_building())
    report=obj["report"]
    new=report["part_id_additions"]
    removed=report["part_id_removals"]
    assert all(k in {"3007","3001","3008","3460","3666","3710","87079","3068b","4275b","4276b"}
               for k in new)
    assert sum(new.values())==report["new_parts"]
    assert sum(removed.values())==report["removed_old_tip_tiles"]
    assert report["parts_delta_vs093"]==sum(new.values())-sum(removed.values())
    assert report["composite_total"]==(
        len(obj["foundation"].parts)+len(obj["articulated_parts"]))


def test_reject_bad_frame_cadence_instead_of_inventing_part():
    with pytest.raises(ValueError,match="TRUSS_SPACING"):
        build_094(other_building(),truss_step_bays=50)


def test_no_fake_mechanical_closure_on_unproven_vertices():
    r=build_094(other_building())["report"]
    assert r["truss_to_wall_compression_documented_verified"]==0
    assert r["remaining_unverified_mechanical_paths"]==r["frame_count"]
    assert r["overall_mesh_clearance_verified"] is False
    assert r["ridge_insertable"] is False
    assert r["roof_finger_sweep_complete"] is False


def test_real_truss_corner_hinge_pairs_are_coaxial_but_not_load_rated():
    obj=build_094(other_building())
    r=obj["report"]
    assert r["new_truss_hinge_pairs"]==4*r["frame_count"]
    assert r["new_coaxial_truss_hinge_pairs"]==4*r["frame_count"]
    h=[x for x in obj["links"] if
       x.get("connector_type")=="LDRAW_4275B_H2_TO_4276B_H1_COMPLEMENTARY_FINGERS"]
    assert len(h)==4*r["frame_count"]
    assert all(x["coaxial_geometry_verified"] for x in h)
    assert not any(x["standalone_usable_strain_rating"] for x in h)
    assert all(x["attachment_to_frame_chord"]=="UNVERIFIED_STUD_ALIGNMENT"
               for x in h)
