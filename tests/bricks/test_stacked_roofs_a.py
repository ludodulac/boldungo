"""Mission A self-contained tests: no GUIDED-004 source or rewrite."""
import json
import re
from pathlib import Path

import pytest

from scripts.experiment_stacked_roofs_a import construct, _ldraw, _audit

@pytest.mark.parametrize("width,length,pitch,courses", [
    (20, 20, 18, 3),
    (26, 24, 22, 4),
    (26, 28, 22, 5),
])
def test_three_independent_small_houses(width,length,pitch,courses):
    parts, report = construct(width,length,pitch,0,courses)
    assert 20 <= report["width_studs"] <= 30
    assert 20 <= report["length_studs"] <= 30
    assert report["total_parts"] == len(parts)
    assert report["total_parts"] == sum(report["bom_ldraw"].values())
    assert report["roof_parts"] > 0
    assert report["roof_slope_30363"] > 0
    assert report["roof_ridge_3023b"] > 0
    assert report["connected_components_nominal"] == 1
    assert report["unsupported_nominal_count"] == 0
    assert report["orthogonal_body_aabb_collision_count"] == 0
    assert report["supported_roof_to_baseplate_nominal"] == report["roof_parts"]
    assert report["mechanical_strength_or_n6_certified"] is False
    assert report["complete_LDraw_mesh_clearance_proven"] is False
    assert report["stepwise_insertion_checked"] is False
    lines = [line for line in _ldraw(parts,width,length,"test").splitlines()
             if line.startswith("1 ")]
    assert len(lines)==len(parts)
    assert all(len(line.split()) == 15 for line in lines), "LDraw requires 12 transform values"
    assert lines[0].endswith(" 3811.dat")
    assert sum(x.endswith(" 30363.dat") for x in lines) == report["roof_slope_30363"]

@pytest.mark.parametrize("overhang,pitch,width,length", [
    (1,22,20,20),(0,14,20,20),(0,26,20,20),
    (0,22,22,20),(0,22,20,21),(0,22,26,31)])
def test_unsafe_unverified_parameter_rejected(overhang,pitch,width,length):
    with pytest.raises(ValueError):
        construct(width,length,pitch,overhang,4)

def test_two_slope_top_studs_nominally_bridge_ridge():
    parts, report = construct(26,24,22,0,4)
    last = report["roof_courses_each_side"] - 1
    slopes = [p for p in parts if p.role=="slope" and p.step == last]
    left = [p for p in slopes if p.side=="left"]
    right = [p for p in slopes if p.side=="right"]
    ridge = [p for p in parts if p.role=="ridge"]
    for cap in ridge:
        assert any(p.top_studs() & cap.bottom_cavities() for p in left)
        assert any(p.top_studs() & cap.bottom_cavities() for p in right)
    assert report["full_stud_interference_and_insertion_proven"] is False

def test_pitched_step_not_confused_with_smooth_surface():
    _, a = construct(20,20,18,0,3)
    assert abs(a["roof_surface_facet_degrees"] - 18.43494882) < 1e-6
    assert abs(a["course_step_pitch_degrees"] - 21.80140949) < 1e-6
    assert abs(a["requested_pitch_degrees"] - a["course_step_pitch_degrees"]) > 3

def test_generated_l_dr_contains_real_world_slope_orientation():
    parts,_=construct(20,20,22,0,3)
    content=_ldraw(parts,20,20,"matrix-validation")
    lines=[x for x in content.splitlines() if x.startswith("1 ") and x.endswith("30363.dat")]
    assert any(" 1 0 0 0 1 0 0 0 1 30363.dat" in x for x in lines)
    assert any(" -1 0 0 0 1 0 0 0 -1 30363.dat" in x for x in lines)
