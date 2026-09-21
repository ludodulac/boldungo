from brickhouse.scene.architectural_constraints import *

def test_alignment_and_order_are_checked_before_metres():
    rects={"upper":NormalizedRect(x0=.1,x1=.3,z0=.65,z1=.85),"lower":NormalizedRect(x0=.11,x1=.31,z0=.25,z1=.45)}
    report=evaluate_normalized_constraints(rects,[ArchitecturalConstraint(id="a",kind="approx_aligned_x",subject_id="upper",object_id="lower",tolerance=.03,statement="same bay"),ArchitecturalConstraint(id="b",kind="above",subject_id="upper",object_id="lower",statement="upper is above lower")])
    assert report.score==1 and not report.violations
    values=normalized_rect_to_metric(rects["upper"],facade_span=10,wall_height=8) 
    assert all(abs(a-b)<1e-9 for a,b in zip(values,(1.0,5.2,2.0,1.6)))

def test_wrong_alignment_is_reported():
    rects={"a":NormalizedRect(x0=.05,x1=.2,z0=.6,z1=.8),"b":NormalizedRect(x0=.65,x1=.8,z0=.2,z1=.4)}
    report=evaluate_normalized_constraints(rects,[ArchitecturalConstraint(id="x",kind="approx_aligned_x",subject_id="a",object_id="b",tolerance=.05,statement="same bay")])
    assert report.score<1 and report.violations[0].constraint_id=="x"
