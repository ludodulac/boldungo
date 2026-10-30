"""Targeted real LDraw mesh tests: connectors NEVER excuse an unresolved COLLISION."""
from pathlib import Path
from lego_geometry_engine import LDrawLibrary, Relation, Transform, assess_pair, analyze_assembly, check_collision, find_connections, instantiate
from lego_geometry_engine.joint_validation import _body_envelope

FIXTURE=Path(__file__).parent/"fixtures"/"ldraw"

def parts():
    b=LDrawLibrary(FIXTURE).load_part("3005")
    return b,instantiate(b,"lower"),instantiate(b,"upper",Transform.translation(0,-24,0))

def test_positive_real_stud_cavity_in_contact_without_body_overlap():
    _,lower,upper=parts()
    assert find_connections(lower,upper)
    assert check_collision(lower,upper) is Relation.CONTACT
    outcome=assess_pair(lower,upper)
    assert outcome.verdict=="COMPATIBLE_MATING",outcome
    assert outcome.body_overlap is False
    assert analyze_assembly([lower,upper]).valid is True

def test_negative_misaligned_studs_not_declared_fixed():
    brick,lower,_=parts()
    other=instantiate(brick,"bad-shift",Transform.translation(2,-24,0))
    assert not find_connections(lower,other)
    assert assess_pair(lower,other).verdict != "COMPATIBLE_MATING"
    assert analyze_assembly([lower,other]).valid is False

def test_negative_coincident_bricks_forbidden_volume():
    brick,lower,_=parts()
    duplicate=instantiate(brick,"duplicate")
    out=assess_pair(lower,duplicate)
    assert out.verdict=="FORBIDDEN_COLLISION",out
    assert analyze_assembly([lower,duplicate]).valid is False

def test_negative_simply_touching_without_studs_not_structural_edge():
    brick,lower,_=parts()
    beside=instantiate(brick,"side-touch",Transform.translation(20,0,0))
    assert not find_connections(lower,beside)
    outcome=assess_pair(lower,beside)
    assert outcome.verdict=="NO_MECHANICAL_LINK",outcome
    # Side touch is not nominal support.
    roof=instantiate(brick,"roof",Transform.translation(20,-24,0))
    report=analyze_assembly([lower,beside,roof])
    assert not report.valid, "Two independent grounded components must not be a valid assembly"
    assert len(report.disconnected_components)==2
    assert not any({"lower","side-touch"} <= set(component) for component in report.disconnected_components)

def test_negative_floating_piece_is_not_supported():
    brick,lower,upper=parts()
    floating=instantiate(brick,"floating",Transform.translation(70,-24,0))
    report=analyze_assembly([lower,upper,floating])
    assert "floating" in report.unsupported_parts
    assert report.valid is False

def test_aligned_connectors_do_not_excuse_reported_collision():
    _,lower,upper=parts()
    con=find_connections(lower,upper)
    assert con
    outcome=assess_pair(lower,upper,relation=Relation.COLLISION,connections=con)
    assert outcome.verdict=="INDETERMINATE",outcome
    assert outcome.body_overlap is False

def test_body_penetration_rejected_even_if_connectors_claim_alignment():
    brick,lower,upper=parts()
    penetrating=instantiate(brick,"penetrating",Transform.translation(0,-22,0))
    # Force nominal connector evidence: classifier must still reject a body overlap.
    fake_connectors=find_connections(lower,upper)
    assert fake_connectors
    assert check_collision(lower,penetrating) is Relation.COLLISION
    outcome=assess_pair(lower,penetrating,relation=Relation.COLLISION,connections=fake_connectors)
    assert outcome.verdict=="FORBIDDEN_COLLISION",outcome

def test_synthetic_nonofficial_shapes_not_certified_by_connector_alignment():
    brick,lower,upper=parts()
    unknown=type(brick)(
        "non-canonical-brick.dat",brick.triangles,brick.bbox,brick.description,
        brick.license,brick.connectors
    )
    x=instantiate(unknown,"unknown",Transform.translation(0,-24,0))
    assert find_connections(lower,x)
    assert assess_pair(lower,x).verdict=="INDETERMINATE"
