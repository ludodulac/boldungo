"""Connectivity: a set of supported pieces can still be two separate islands."""
import pytest
from brickhouse.bricks.physical_placement_gate import Placement, build, build_geometrically, verify_connected

def test_two_separate_ground_bricks_fail_final_build():
    with pytest.raises(ValueError, match="DISCONNECTED_ASSEMBLY"):
        build([Placement("BRICK_2X4", 0, 0, 0),
               Placement("BRICK_2X4", 8, 0, 0)])

def test_bridged_ground_bricks_pass_geometric_contact_graph():
    # Gap-free foundations touching at edges are NOT mechanically joined;
    # a top brick overlaps studs on both foundations.
    pieces = [
        Placement("BRICK_2X4", 0, 0, 0, 1),
        Placement("BRICK_2X4", 4, 0, 0, 1),
        Placement("BRICK_2X4", 2, 0, 3, 1),
    ]
    gate = build_geometrically(pieces)
    assert gate.validation_level == "GEOMETRY_ONLY"
    assert gate.connector_validation == "NOT_CHECKED"
    assert len(gate.accepted) == 3

def test_empty_build_is_not_a_valid_assembly():
    with pytest.raises(ValueError, match="EMPTY_ASSEMBLY"):
        verify_connected([])
