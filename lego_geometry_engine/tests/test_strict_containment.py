"""Bounded conservative fix: boundary parity cannot prove solid confinement."""
from lego_geometry_engine import AABB, PartDefinition, Relation, Transform, check_collision, instantiate
from lego_geometry_engine.core import _point_in_mesh_status, _point_on_mesh_surface
from lego_geometry_engine.joint_validation import assess_pair
from pathlib import Path
from lego_geometry_engine import LDrawLibrary

def cube(size=10):
    h=size
    p=[(-h,-h,-h),(-h,-h,h),(-h,h,-h),(-h,h,h),(h,-h,-h),(h,-h,h),(h,h,-h),(h,h,h)]
    f=((0,4,6),(0,6,2),(1,3,7),(1,7,5),(0,1,5),(0,5,4),
       (2,6,7),(2,7,3),(0,2,3),(0,3,1),(4,5,7),(4,7,6))
    return PartDefinition("cube",tuple(tuple(p[i] for i in f3) for f3 in f),
                          AABB((-h,-h,-h),(h,h,h)))

def test_boundary_is_never_a_strict_interior_witness():
    m=cube().triangles
    assert _point_on_mesh_surface((10,3,0),m)
    assert _point_in_mesh_status((10,3,0),m) is None
    assert _point_in_mesh_status((0,0,0),m) is True
    assert _point_in_mesh_status((30,0,0),m) is False

def test_nested_solids_still_forbidden():
    a=instantiate(cube(10),"outer")
    b=instantiate(cube(2),"inner")
    assert check_collision(a,b) is Relation.COLLISION
    assert assess_pair(a,b).verdict=="FORBIDDEN_COLLISION"

def test_identical_real_mesh_still_forbidden():
    lib=LDrawLibrary(Path(__file__).parent/"fixtures"/"ldraw")
    d=lib.load_part("3005")
    a,b=instantiate(d,"a"),instantiate(d,"b")
    assert check_collision(a,b) is Relation.COLLISION
    assert assess_pair(a,b).verdict=="FORBIDDEN_COLLISION"

def test_bad_height_horizontal_and_unlinked_contact_existing_regression():
    lib=LDrawLibrary(Path(__file__).parent/"fixtures"/"ldraw")
    d=lib.load_part("3005")
    fixed=instantiate(d,"low")
    bad=instantiate(d,"bad",Transform.translation(0,-20,0))
    assert assess_pair(fixed,bad).verdict=="FORBIDDEN_COLLISION"
    shifted=instantiate(d,"shift",Transform.translation(2,-24,0))
    assert assess_pair(fixed,shifted).verdict!="COMPATIBLE_MATING"
    contact=instantiate(d,"side",Transform.translation(20,0,0))
    assert assess_pair(fixed,contact).verdict=="NO_MECHANICAL_LINK"

def test_valid_regular_real_brick_pair_still_compatible():
    lib=LDrawLibrary(Path(__file__).parent/"fixtures"/"ldraw")
    d=lib.load_part("3005")
    a,b=instantiate(d,"low"),instantiate(d,"top",Transform.translation(0,-24,0))
    assert assess_pair(a,b).verdict=="COMPATIBLE_MATING"
