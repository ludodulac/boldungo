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
