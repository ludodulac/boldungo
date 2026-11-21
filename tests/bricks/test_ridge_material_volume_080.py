"""080: geometric material occupancy must not be inferred from triangle crossings."""
from pathlib import Path

import pytest
from lego_geometry_engine.core import AABB, PartDefinition, instantiate

from brickhouse.bricks.ridge_material_volume_080 import (
    decide_physical_interference,
    inspect_shared_interior,
    inspect_solid_shell,
)
from scripts.probe_ridge_material_volume_080 import analyze_ridge_material_080


def _instance(name, triangles):
    vertices = [v for face in triangles for v in face]
    lo = tuple(min(v[i] for v in vertices) for i in range(3))
    hi = tuple(max(v[i] for v in vertices) for i in range(3))
    return instantiate(PartDefinition(name, tuple(triangles), AABB(lo, hi)), name)


def _cube(name, x0=0., x1=1., y0=0., y1=1., z0=0., z1=1.):
    """Known closed, outward oriented, non-LEGO synthetic material solid."""
    a, b, c, d = ((x0,y0,z0), (x1,y0,z0), (x1,y1,z0), (x0,y1,z0))
    e, f, g, h = ((x0,y0,z1), (x1,y0,z1), (x1,y1,z1), (x0,y1,z1))
    return _instance(name, [
        (a,c,b), (a,d,c),   # bottom -z
        (e,f,g), (e,g,h),   # top +z
        (a,e,h), (a,h,d),   # left -x
        (b,c,g), (b,g,f),   # right +x
        (a,b,f), (a,f,e),   # near -y
        (d,h,g), (d,g,c),   # far +y
    ])


def test_closed_box_triangulation_is_safe_for_volume_parity_gate():
    report = inspect_solid_shell(_cube("solid"))
    assert report["triangles"] == 12
    assert report["open_boundary_edges"] == 0
    assert report["nonmanifold_edges"] == 0
    assert report["inconsistent_winding_edges"] == 0
    assert report["degenerate_faces"] == 0
    assert report["watertight_oriented_shell_gate"] == "VALID"
    assert report["volume_from_shell_provable"] is True


def test_true_shared_volume_witness_remains_unapproved_lego_connector():
    a = _cube("a", 0., 1.)
    b = _cube("b", .5, 1.5)
    report = inspect_shared_interior(a, b)
    assert report["shared_material_sample"] == "BOTH_CLOSED_MESH_INTERIORS_CONTAIN_POINT"
    assert report["interior_witness_ldu"]
    assert report["volume_proven"] is True
    assert report["geometric_collision_review"] == "REVIEW_REQUIRED"
    result, why = decide_physical_interference(report)
    assert result == "UNKNOWN"
    assert "CONNECTOR_PROVENANCE" in why
    assert report["physical_certification"] == "NOT_CERTIFIED"


def test_touching_closed_cubes_have_no_positive_common_volume():
    a, b = _cube("a", 0., 1.), _cube("b", 1., 2.)
    review = inspect_shared_interior(a, b)
    assert review["shared_material_sample"] == "NO_POSITIVE_COMMON_BBOX_VOLUME"
    assert review["interior_witness_ldu"] is None
    assert decide_physical_interference(review)[0] == "UNKNOWN"


def test_triangle_soup_has_no_provable_interior_even_if_aabb_is_overlapping():
    sheet = _instance("sheet", [
        ((0., 0., 0.), (1., 0., 0.), (0., 1., 0.)),
    ])
    solid = _cube("solid", 0., 1., 0., 1., -.5, .5)
    report = inspect_shared_interior(sheet, solid)
    assert report["first_shell"]["open_boundary_edges"] == 3
    assert report["first_shell"]["volume_from_shell_provable"] is False
    assert report["shared_material_sample"] == "UNKNOWN_UNCLOSED_OR_UNORIENTED_LDRAW_SURFACE"
    assert report["samples_checked"] == 0
    assert decide_physical_interference(report)[0] == "UNKNOWN"


def test_inconsistent_face_winding_invalidates_solid_parity_gate():
    closed = _cube("box")
    faces = list(closed.triangles)
    faces[0] = faces[0][::-1]
    result = inspect_solid_shell(_instance("bad-winding", faces))
    assert result["watertight_oriented_shell_gate"] == "UNKNOWN"
    assert result["inconsistent_winding_edges"] > 0


def test_partial_or_disjoint_lattice_can_never_claim_valid_clutch():
    a = _cube("a", 0., 1.)
    b = _cube("b", 2., 3.)
    report = inspect_shared_interior(a, b)
    assert report["interior_witness_ldu"] is None
    assert decide_physical_interference(report)[0] == "UNKNOWN"


def test_bounded_sample_validation():
    solid = _cube("x")
    for n in (0, 8, 2.4, -2):
        with pytest.raises(ValueError):
            inspect_shared_interior(solid, solid, points_per_axis=n)


def test_original_ldraw_test_fixture_fails_closed_without_recomputing_079():
    p = Path("lego_geometry_engine/tests/fixtures/ldraw")
    r = analyze_ridge_material_080(p)
    assert r["diagnostic_executed"] is False
    assert r["relocalized_triangles"] is False
    assert r["model_mutated"] is False
    assert r["physical_certification"] == "NOT_CERTIFIED"
    assert r["blocking_reasons"]
    assert r["required_parts"]["3005"]["loaded"] is True
    assert r["required_parts"]["30363"]["loaded"] is False
