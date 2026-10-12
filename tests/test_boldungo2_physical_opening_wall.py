"""Regression checks for a wall aperture and its supported lintel."""
from brickhouse.bricks.physical_opening_wall import wall_with_opening, validate_wall_with_opening

def test_wall_with_opening_passes_catalog_support_preflight():
    assert len(validate_wall_with_opening().accepted) == 11

def test_opening_is_clear_on_two_courses():
    parts = wall_with_opening()
    for z in (3, 6):
        for p in parts:
            if p.z == z:
                width, _, _ = p.dimensions()
                assert p.x + width <= 4 or p.x >= 8

def test_lintel_has_supported_bridge_over_aperture():
    parts = wall_with_opening()
    bridge = [p for p in parts if p.z == 9]
    assert len(bridge) == 1
    coverage = set()
    for p in bridge:
        w, _, _ = p.dimensions()
        coverage.update(range(p.x, p.x + w))
    assert coverage == set(range(1, 11))
