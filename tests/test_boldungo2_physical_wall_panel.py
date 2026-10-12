"""Regression tests for catalog-only staggered wall panel."""
import pytest
from brickhouse.bricks.physical_wall_panel import panel_courses, validate_panel
from brickhouse.bricks.physical_placement_gate import PhysicalPlacementGate, Placement

def test_five_course_panel_has_17_catalog_bricks():
    gate = validate_panel(5)
    assert len(gate.accepted) == 17
    assert all(part.dimensions()[1] == 2 for part in gate.accepted)
    assert sorted({part.z for part in gate.accepted}) == [0, 3, 6, 9, 12]

def test_each_course_spans_twelve_studs_without_gaps():
    for z in (0, 3, 6, 9, 12):
        covered = set()
        for part in panel_courses(5):
            if part.z == z:
                width, _, _ = part.dimensions()
                covered.update(range(part.x, part.x + width))
        assert covered == set(range(12))

def test_panel_cannot_be_assembled_top_down():
    gate = PhysicalPlacementGate()
    with pytest.raises(ValueError, match="NO_STUD_SUPPORT"):
        gate.add(panel_courses(5)[-1])

def test_panel_rejects_duplicate_brick():
    parts = panel_courses(5)
    parts.insert(1, parts[0])
    gate = PhysicalPlacementGate()
    gate.add(parts[0])
    with pytest.raises(ValueError, match="SOLID_COLLISION"):
        gate.add(parts[1])
