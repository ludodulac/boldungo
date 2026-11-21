from brickhouse.bricks.lego30363_3020_assembly_037 import candidate, gate, ldraw_lines

def test_positive_axis_alignment_not_physical_certificate():
    a = candidate()
    assert a.aligned_ring_axes == (-50, -30, -10)
    assert a.status == "AXES_ALIGNED_ONLY"
    assert "30363.dat" in ldraw_lines(a)
    assert "3020.dat" in ldraw_lines(a)
    assert gate(a)["ready_for_guided004"] is False

def test_negative_axis_alignment():
    a = candidate(plate_x=0)
    assert a.aligned_ring_axes == ()
    assert a.status == "AXES_MISALIGNED"
    assert gate(a)["ready_for_guided004"] is False

def test_no_false_collision_or_insertion_pass():
    result = gate(candidate())
    assert result["solid_collision"] == "NOT_COMPUTED"
    assert result["insertion_path"] == "NOT_COMPUTED"
