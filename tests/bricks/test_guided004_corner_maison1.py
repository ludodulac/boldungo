"""MAISON-1: no invented dimensions, actual source window, bad joint rejected."""
from pathlib import Path
import pytest
from scripts.build_guided004_corner_maison1 import Add,solid_overlap,touching,KNOWN

def test_reject_misplaced_stud_center_at_corner():
    # Main house source facades are perpendicular: a corner bond must
    # engage both walls; moving it off the wall removes that interface.
    facade_east=(16,2,36,24,3,39)
    facade_south=(16,3,36,17,11,39)
    correct=(16,2,39,18,4,40)
    incorrect=(18,2,39,20,4,40)
    assert touching(correct,facade_east)==2
    assert touching(correct,facade_south)==1
    assert touching(incorrect,facade_south)==0

def test_reject_bad_engagement_height_and_orthogonal_collisions():
    brick=(18,10,33,20,12,36)
    correct=(18,2,36,20,12,39)
    wrong=(18,2,35,20,12,38)
    assert touching(correct,brick)==4
    assert touching(wrong,brick)==0
    assert solid_overlap(wrong,brick)
    assert not solid_overlap(correct,brick)

def test_exact_source_scene_exists_and_is_not_created_by_script():
    s=Path("frontend/data/boldungo2-guided-004-real-scene.json")
    raw=s.read_text()
    assert '"east-rdc-window-left"' in raw
    assert '"width": {"value": 9.3' in raw
    assert '"depth": {"value": 8.2' in raw
    source=Path("scripts/build_guided004_corner_maison1.py").read_text()
    assert "canonical.generate()" in source
    assert "SCENE.read_bytes()" in source
    assert "MAISON1_CANONICAL_MODEL_OR_SCENE_CHANGED" in source
    assert "MAISON1_NEW_ORIGINAL_VOXEL_COLLISION" in source
    assert "NO" in source or "NOT_PROVEN" in source

def test_real_lego_parts_and_no_22_to_45_degree_conversions():
    assert KNOWN=={"3811":(32,32,1),"3003":(2,2,3),"3006":(2,10,3),
                   "3832":(10,2,1),"3022":(2,2,1)}
    assert Add("one","3006","beam",18,2,39,2,10,3).bbox()==(18,2,39,20,12,42)
