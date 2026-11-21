"""Regression checks for honest physical metrics on the actual regenerated house."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from audit_guided004_physical import audit_physical_model
from repair_guided004_overlaps import repair_orthogonal_overlaps, _cells
from bridge_guided004_connections import bridge_compatible_bricks
from brickhouse.bricks.brick_model import BrickModel, BrickModelPart


def _part(pid, x, z, *, y=0):
    return BrickModelPart(
        placement_id=pid, part_id="BRICK_1X1", category="brick",
        component="wall", facade="front", x_studs=x, y_studs=y,
        z_plates=z, rotation_quarter_turns=0,
    )


def _model(parts):
    return BrickModel(
        building_id="physical-test", volume_id="main", width_studs=8,
        depth_studs=8, height_plates=30, parts=parts,
    )


def test_stud_contact_not_side_contact():
    m = _model([_part("a", 0, 0), _part("b", 1, 0),
                _part("c", 0, 3)])
    result = audit_physical_model(m)
    assert result["connected_components_orthogonal_stud_contact"] == 2
    assert result["unsupported_parts"] == 0
    assert result["physical_certification"] == "NOT_CERTIFIED"


def test_floating_part_is_reported():
    result = audit_physical_model(_model([_part("base", 0, 0), _part("floating", 0, 6)]))
    assert result["unsupported_parts"] == 1
    assert result["unsupported_placement_ids"] == ["floating"]


def test_overlap_repair_preserves_voxel_union_and_reports_support():
    m = _model([_part("a", 0, 0), _part("b", 0, 0)])
    fixed, metrics = repair_orthogonal_overlaps(m)
    assert metrics["original_overlap_parts"] == 1
    assert len(fixed.parts) == 1
    result = audit_physical_model(fixed)
    assert result["collision_voxel_overlaps"] == 0
    assert result["connected_components_orthogonal_stud_contact"] == 1


def test_structural_retiling_reduces_components_without_changing_occupied_volume():
    # The long replacement must bridge two lower bricks by real stud overlap.
    parts = [_part("left", 0, 0), _part("right", 2, 0)]
    parts += [_part(f"upper-{x}", x, 3) for x in range(3)]
    original = _model(parts)
    before = audit_physical_model(original)
    repaired, metrics = bridge_compatible_bricks(original)
    after = audit_physical_model(repaired)
    assert len(repaired.parts) == 3
    assert metrics["one_by_one_bricks_removed_by_merging"] == 2
    assert set().union(*(_cells(p) for p in original.parts)) == set().union(*(_cells(p) for p in repaired.parts))
    assert after["collision_voxel_overlaps"] == 0
    assert after["connected_components_orthogonal_stud_contact"] < before["connected_components_orthogonal_stud_contact"]
    assert after["unsupported_parts"] <= before["unsupported_parts"]


def test_parallel_deck_boards_pair_without_changing_occupied_volume():
    first = _part("scene-platform:deck:board:1", 0, 36)
    second = _part("scene-platform:deck:board:2", 1, 36)
    first = first.model_copy(update={
        "part_id": "BRICK_1X8", "category": "timber",
        "component": "facade_detail", "width_studs": 1, "length_studs": 8,
    })
    second = second.model_copy(update={
        "part_id": "BRICK_1X8", "category": "timber",
        "component": "facade_detail", "width_studs": 1, "length_studs": 8,
    })
    original = _model([first, second])
    fixed, metrics = bridge_compatible_bricks(original)
    assert metrics["paired_parallel_bricks"] == 1
    assert len(fixed.parts) == 1
    assert fixed.parts[0].part_id == "BRICK_2X8"
    assert set().union(*(_cells(p) for p in original.parts)) == set().union(*(_cells(p) for p in fixed.parts))
    assert audit_physical_model(fixed)["collision_voxel_overlaps"] == 0


def test_extend_existing_brick_with_single_preserves_voxels():
    base = _part("long", 0, 3).model_copy(update={
        "part_id": "BRICK_1X2", "width_studs": 1, "length_studs": 2,
    })
    single = _part("single", 0, 3, y=2)
    original = _model([base, single])
    fixed, metrics = bridge_compatible_bricks(original)
    assert metrics["extended_with_existing_single_bricks"] == 1
    assert len(fixed.parts) == 1
    assert fixed.parts[0].part_id == "BRICK_1X3"
    assert set().union(*(_cells(p) for p in original.parts)) == set().union(*(_cells(p) for p in fixed.parts))
    assert audit_physical_model(fixed)["collision_voxel_overlaps"] == 0


def test_stair_tread_pairing_uses_numeric_not_lexicographic_stud_order():
    left = _part("scene-stair:run:tread:00013", 9, 27, y=6).model_copy(update={
        "part_id": "BRICK_1X6", "category": "concrete",
        "component": "facade_detail", "facade": "left",
        "width_studs": 1, "length_studs": 6,
    })
    right = left.model_copy(update={
        "placement_id": "scene-stair:run:tread:00014", "x_studs": 10,
    })
    before = _model([right, left])
    after, metrics = bridge_compatible_bricks(before)
    assert metrics["paired_parallel_bricks"] == 1
    assert len(after.parts) == 1
    assert after.parts[0].part_id == "BRICK_2X6"
    assert set().union(*(_cells(p) for p in before.parts)) == set().union(*(_cells(p) for p in after.parts))


def test_roof_nominal_dimensions_do_not_certify_sloped_mechanics():
    roof = _part("roof-slope", 0, 9).model_copy(update={
        "part_id": "BRICK_SLOPED_18_4X2", "category": "roof_tile",
        "component": "roof", "facade": None, "roof_side": "negative",
        "width_studs": 4, "length_studs": 2,
    })
    measured = audit_physical_model(_model([roof]))
    assert measured["roof_nominal_footprints_checked"] == 1
    assert measured["roof_parts_verified_mechanically"] == 0
    assert measured["roof_parts_unverified"] == 1
    bad = roof.model_copy(update={"width_studs": 9})
    rejected = audit_physical_model(_model([bad]))
    assert rejected["roof_nominal_footprints_invalid"] == ["roof-slope"]
