"""Physical placement gate regression tests."""
import pytest
from brickhouse.bricks.physical_placement_gate import Placement, PhysicalPlacementGate, build

def test_connected_stack():
    gate = build([Placement("BRICK_2X4", 0, 0, 0), Placement("BRICK_1X2", 0, 0, 3)])
    assert len(gate.accepted) == 2

@pytest.mark.parametrize("part,error", [
    (Placement("BRICK_1X2", 1, 0, 0), "SOLID_COLLISION"),
    (Placement("BRICK_1X2", 4, 0, 3), "NO_STUD_SUPPORT"),
    (Placement("BRICK_1X2", 0, 0, 4), "NO_STUD_SUPPORT"),
    (Placement("BRICK_1X2", 0, 0, 2), "SOLID_COLLISION"),
    (Placement("BRICK_SLOPED_4X36", 0, 0, 3), "PART_NOT_IN_CANONICAL_CATALOG"),
    (Placement("BRICK_3X3", 0, 0, 3), "PART_NOT_IN_CANONICAL_CATALOG"),
])
def test_reject_invalid(part,error):
    gate = PhysicalPlacementGate()
    gate.add(Placement("BRICK_2X4", 0, 0, 0))
    with pytest.raises(ValueError, match=error):
        gate.add(part)
    assert len(gate.accepted) == 1

def test_rotated_plate_supported():
    gate = build([Placement("BRICK_2X4", 0, 0, 0),
                  Placement("PLATE_1X4", 0, 0, 3, rotation=1)])
    assert len(gate.accepted) == 2

def test_first_piece_cannot_float():
    with pytest.raises(ValueError, match="NO_STUD_SUPPORT"):
        build([Placement("BRICK_2X4", 0, 0, 3)])

def test_two_grounded_base_parts_allowed():
    gate = build([Placement("BRICK_2X4", 0, 0, 0), Placement("BRICK_2X4", 2, 0, 0)])
    assert len(gate.accepted) == 2

def test_catalog_includes_real_plate():
    assert build([Placement("PLATE_1X2", 0, 0, 0)]).accepted

def test_catalog_excludes_unlisted_plate():
    with pytest.raises(ValueError, match="PART_NOT_IN_CANONICAL_CATALOG"):
        build([Placement("PLATE_2X4", 0, 0, 0)])

def test_staggered_wall_segment_is_supported():
    gate = build([
        Placement("BRICK_2X4", 0, 0, 0),
        Placement("BRICK_2X4", 2, 0, 0),
        Placement("BRICK_2X4", 1, 0, 3),
        Placement("BRICK_2X4", 1, 0, 6),
    ])
    assert len(gate.accepted) == 4

def test_wall_segment_rejects_overlapping_second_course():
    with pytest.raises(ValueError, match="SOLID_COLLISION"):
        build([
            Placement("BRICK_2X4", 0, 0, 0),
            Placement("BRICK_2X4", 2, 0, 0),
            Placement("BRICK_2X4", 1, 0, 3),
            Placement("BRICK_2X4", 1, 0, 3),
        ])
