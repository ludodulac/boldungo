"""Regression tests for evidence-limited 30363/3020 connection experiment."""
from brickhouse.bricks.lego30363_3020_experiment_036 import (
    RINGS, candidate_ring_alignment, inspect_30363_on_3020,
)

def test_underside_primitives_and_heights():
    assert [(r.z_ldu, r.primitive) for r in RINGS] == [
        (-10, "stud4a.dat"),
        (-30, "stud4s.dat"), (-30, "stud4a.dat"),
        (-50, "stud4s.dat"), (-50, "stud4a.dat"),
    ]
    assert RINGS[0].y_ldu == 6.667
    assert RINGS[-1].y_ldu == 20.0

def test_candidate_stud_axes_match():
    result = inspect_30363_on_3020()
    assert result["axis_alignment"] is True
    assert result["ring_axes_z_ldu"] == (-50, -30, -10)
    assert result["mechanically_certified"] is False
    assert result["insertion"] == "UNVERIFIED"

def test_misaligned_plate_has_no_ring_contact():
    assert candidate_ring_alignment(0, -20) == ()
    result = inspect_30363_on_3020(0, -20)
    assert result["axis_alignment"] is False
    assert result["mechanically_certified"] is False

def test_axis_alignment_is_not_mechanical_connection():
    assert inspect_30363_on_3020()["clutch"] == "UNVERIFIED"
    assert inspect_30363_on_3020()["solid_collision"] == "UNVERIFIED"
