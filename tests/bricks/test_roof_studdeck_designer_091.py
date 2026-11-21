"""091 regression: real stud anti-stud roof alternative, fail-closed load gates."""
import pytest

from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.roof_studdeck_designer_091 import design_standard_stud_roof_091


def wall(pid, x, y, z=0):
    return BrickModelPart(
        placement_id=pid, part_id="BRICK_2X4", category="brick",
        component="wall", facade="front",
        x_studs=x, y_studs=y, z_plates=z, rotation_quarter_turns=1)


def slope(pid, x, y, z, side="negative"):
    return BrickModelPart(
        placement_id=pid, part_id="BRICK_SLOPED_18_4X2",
        category="roof_tile", component="roof",
        roof_side=side, x_studs=x, y_studs=y,
        z_plates=z, rotation_quarter_turns=0)


def model(parts):
    return BrickModel(building_id="OTHER-ROOF-091",
                      volume_id="module", width_studs=50,
                      depth_studs=30, height_plates=20, parts=parts)


def test_alternative_roof_with_masonry_stud_connections_avoids_30363_interfaces():
    original = model([wall("wall-a", 6, 0),
                      slope("a", 6, 0, 3),
                      slope("b", 9, 0, 6)])
    freeze = original.model_dump_json()
    report, built = design_standard_stud_roof_091(original)
    assert original.model_dump_json() == freeze
    assert len(built.parts) == 3
    assert report["replaced_slopes"] == 2
    assert report["deck_bricks"] == 2
    assert report["direct_compression_connected_roof_bricks"] == 2
    assert report["roof_bricks_connected_in_standard_stud_graph"] == 2
    assert report["roof_bricks_not_connected_to_walls"] == []
    assert report["30363_underside_claims"] == 0
    assert all(p.part_id != "BRICK_SLOPED_18_4X2" for p in built.parts)
    assert report["physical_certification"] == "NOT_CERTIFIED"
    assert report["pitch_difference_degrees"] < 0.21


def test_transverse_tie_has_two_wall_connected_anchors_for_two_roots():
    parts = [wall("left", 6, 0), wall("right", 6, 6)]
    parts += [slope(f"tile-{y}", 6, y, 3) for y in range(0, 8, 2)]
    original = model(parts)
    report, built = design_standard_stud_roof_091(original)
    assert report["direct_compression_connected_roof_bricks"] == 2
    assert report["roof_bricks_tied_only_no_compression_certification"] == 2
    assert report["roof_bricks_connected_in_standard_stud_graph"] == 4
    assert len(report["cross_tie_modules"]) == 1
    tie = report["cross_tie_modules"][0]
    assert len(tie["tie_part_ids"]) == 4
    assert tie["span_studs"] == 8
    assert len(tie["grounded_anchor_ids"]) == 2
    assert tie["load_mode"] == "TENSION_AND_BENDING_NOT_RATED"
    assert report["roof_load_capacity_certified"] is False
    assert all(p.part_id in ("BRICK_2X4", "PLATE_1X8", "PLATE_1X6")
               for p in built.parts if p.component == "roof_support")


def test_missing_second_anchor_is_not_a_certified_purlin():
    parts = [wall("left", 6, 0)]
    parts += [slope(f"tile-{y}", 6, y, 3) for y in range(0, 8, 2)]
    report, _ = design_standard_stud_roof_091(model(parts))
    assert report["cross_tie_modules"] == []
    assert report["roof_bricks_not_connected_to_walls"]
    assert report["roof_bricks_tied_only_no_compression_certification"] == 0


def test_wrong_ridge_seam_fails_closed_instead_of_overlapping_bricks():
    source = model([wall("wall", 6, 0),
                    slope("neg", 6, 0, 3, "negative"),
                    slope("pos", 15, 0, 3, "positive")])
    with pytest.raises(ValueError, match="ROOF_RIDGE_OFF_GRID"):
        design_standard_stud_roof_091(source)


def test_catalog_and_design_ids_for_all_proposed_parts():
    original = model([wall("start", 6, 0), slope("s0", 6, 0, 3),
                      slope("s1", 9, 0, 6)])
    report, built = design_standard_stud_roof_091(original)
    from brickhouse.bricks.catalog import standard_orthogonal_definitions
    from brickhouse.bricks.geometry_adapter import CANONICAL_LDRAW_PARTS
    defs = standard_orthogonal_definitions()
    proposed = [x for x in built.parts if x.component == "roof_support"]
    assert proposed
    assert all(x.part_id in defs and x.part_id in CANONICAL_LDRAW_PARTS for x in proposed)
    assert all(item["color"] == "UNSPECIFIED_BY_BRICKMODEL"
               for item in report["bom_added"])
    assert report["original_mutated"] is False


def test_nonstandard_30363_family_is_not_silently_accepted():
    s = slope("wrong", 6, 0, 3)
    changed = s.model_copy(update={"part_id": "BRICK_SLOPED_45_2X2"})
    with pytest.raises(ValueError, match="UNSUPPORTED_OR_TOO_LARGE_ROOF_FAMILY"):
        design_standard_stud_roof_091(model([changed]))
