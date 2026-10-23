"""079: strict surface-crossing witnesses, provenance-limited outcomes."""
from pathlib import Path

import pytest
from lego_geometry_engine import LDrawLibrary, Relation
from lego_geometry_engine.core import AABB, PartDefinition, instantiate
from scripts.diagnose_ridge_collision_surfaces_079 import (
    COLLISION_PAIRS, _classify_zone, diagnose_three_ridge_collisions,
    localize_crossing_triangles,
)


def _mesh(pid, triangles):
    points = [v for tri in triangles for v in tri]
    lo = tuple(min(p[i] for p in points) for i in range(3))
    hi = tuple(max(p[i] for p in points) for i in range(3))
    return instantiate(PartDefinition(pid, tuple(triangles), AABB(lo, hi)), pid)


def test_strict_witness_finds_actual_crossing_not_just_overlapping_boxes():
    first = _mesh("first", [
        ((0., 0., 0.), (4., 0., 0.), (0., 4., 0.)),
    ])
    second = _mesh("second", [
        ((1., 1., -1.), (1., 1., 1.), (3., 1., 0.)),
    ])
    result = localize_crossing_triangles(first, second)
    assert result["candidate_triangle_pairs_tested"] == 1
    assert result["crossing_witnesses_recorded"] == 1
    assert result["sample_envelope"] is not None
    assert result["candidate_test_limit_reached"] is False
    assert result["exhaustive"] is True
    assert result["sample_envelope"]["approx_model_xyz_studs_plates"]


def test_surface_contact_is_not_claimed_as_a_solid_penetration():
    first = _mesh("first", [
        ((0., 0., 0.), (4., 0., 0.), (0., 4., 0.)),
    ])
    second = _mesh("second", [
        ((0., 0., 0.), (4., 0., 0.), (0., 4., 0.)),
    ])
    result = localize_crossing_triangles(first, second)
    assert result["crossing_witnesses_recorded"] == 0
    assert result["sample_envelope"] is None


def test_low_scan_limit_never_claims_exhaustive_localization():
    tri = ((0., 0., 0.), (4., 0., 0.), (0., 4., 0.))
    crossed = ((1., 1., -1.), (1., 1., 1.), (3., 1., 0.))
    a = _mesh("a", [tri] * 8)
    b = _mesh("b", [crossed] * 8)
    r = localize_crossing_triangles(a, b, max_candidate_tests=1, max_witnesses=40)
    assert r["candidate_test_limit_reached"]
    assert not r["exhaustive"]
    assert r["candidate_triangle_pairs_tested"] == 1


def test_post_sidewall_vs_top_stud_height_zone_is_scoped_not_strength():
    bounds = {"sample_envelope": {
        "approx_model_xyz_studs_plates": {"height_plates": [116.0, 118.0]}}}
    assert _classify_zone(bounds, ("central_post", "negative_slope"), 120) == (
        "CENTRAL_POST_BODY_SIDE_BELOW_STUD_PLANE")
    bounds["sample_envelope"]["approx_model_xyz_studs_plates"]["height_plates"] = [121, 122]
    assert _classify_zone(bounds, ("central_post", "positive_slope"), 120) == (
        "CENTRAL_POST_TOP_STUD_BAND")
    bounds["sample_envelope"]["approx_model_xyz_studs_plates"]["height_plates"] = [119, 121]
    assert _classify_zone(bounds, ("central_post", "negative_slope"), 120) == (
        "CENTRAL_POST_AND_SLOPE_CROSSING_NEAR_STUD_PLANE")


def test_three_target_pairs_are_exactly_the_prior_three_collisions():
    assert COLLISION_PAIRS == (
        ("central_post", "negative_slope"),
        ("central_post", "positive_slope"),
        ("negative_slope", "positive_slope"),
    )


def test_missing_ldraw_dependency_does_not_invent_fit(tmp_path):
    report = diagnose_three_ridge_collisions(tmp_path)
    assert report["complete_collision_localization"] is False
    assert len(report["orientations"]) == 2
    assert report["physical_certification"] == "NOT_CERTIFIED"
    assert report["model_mutated"] is False
    assert all(p["mesh_loaded"] is False
               for p in report["required_parts"].values())
    assert report["blocking_reasons"]


def test_tiny_fixture_with_only_3005_never_claims_three_proven_collisions():
    fixture = Path("lego_geometry_engine/tests/fixtures/ldraw")
    assert (fixture / "parts" / "3005.dat").is_file()
    report = diagnose_three_ridge_collisions(fixture)
    assert report["complete_collision_localization"] is False
    assert report["required_parts"]["3005"]["mesh_loaded"] is True
    assert report["required_parts"]["30363"]["mesh_loaded"] is False
    assert report["physical_certification"] == "NOT_CERTIFIED"


def test_localizer_rejects_invalid_limits():
    a = _mesh("a", [((0, 0, 0), (1, 0, 0), (0, 1, 0))])
    with pytest.raises(ValueError):
        localize_crossing_triangles(a, a, max_candidate_tests=0)
    with pytest.raises(ValueError):
        localize_crossing_triangles(a, a, max_witnesses=0)
