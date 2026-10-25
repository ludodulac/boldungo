"""B-2 bounded genuinely additive terrace LEGO stitching tests."""
from pathlib import Path
from dataclasses import replace
import pytest

from brickhouse.bricks.brick_model import BrickModelPart
from scripts.build_guided004_connections_b2 import (
    _two_host_plate_clearance,new_part,SCOPE,original_floor
)

def test_true_plate_1x3_studs_can_enter_2x3_and_1x3_nominal_cavities():
    near=new_part("neighbor","BRICK_2X3",4,7,24,0)
    orphan=new_part("orphan","BRICK_1X3",6,7,24,0)
    plate=new_part("bridge","PLATE_1X3",4,8,23,1)
    good,proof=_two_host_plate_clearance(plate,near,orphan)
    assert good,proof
    assert proof["checked_stud_cells"]==3
    assert len(proof["margins"])==3
    assert proof["full_mesh_clutch_and_insertion"]=="NOT_PROVEN"

def test_negative_real_stud_bridge_shift_one_stud_is_rejected():
    near=new_part("neighbor","BRICK_2X3",4,7,24,0)
    orphan=new_part("orphan","BRICK_1X3",6,7,24,0)
    wrong=new_part("bridge","PLATE_1X3",3,8,23,1)
    good,proof=_two_host_plate_clearance(wrong,near,orphan)
    assert not good
    assert proof["reason"]=="NOT_2_PLUS_1_STUDS"

def test_negative_height_wrong_engagement_plane_rejected():
    near=new_part("neighbor","BRICK_2X3",4,7,24,0)
    orphan=new_part("orphan","BRICK_1X3",6,7,24,0)
    wrong=new_part("bridge","PLATE_1X3",4,8,22,1)
    good,proof=_two_host_plate_clearance(wrong,near,orphan)
    assert not good and proof["reason"]=="INCORRECT_ENGAGEMENT_PLANE"

def test_no_source_specific_dimensions_or_roof_replacements():
    src=Path("scripts/build_guided004_connections_b2.py").read_text()
    assert "from scripts.build_guided004_full_house_b1 import build" in src
    assert "NO_45" not in src or "NOT" in src
    assert "B2_B1_ALL_1901_PLACEMENTS_PRESERVED" in src
    assert "EXPERIMENT-B2-DECK-SEAM-" in src
    assert "B2_ORTHOGONAL_INTERPENETRATION" in src
    assert "408" not in src  # no hardcoded roof slope positions
    assert "1905" in src   # known historical source count guard, not dimensions
    assert "NOT_CERTIFIED" in SCOPE

def test_new_stud_and_plate_references_have_official_ldraw_identity():
    from brickhouse.bricks.geometry_adapter import CANONICAL_LDRAW_PARTS
    assert CANONICAL_LDRAW_PARTS["BRICK_1X8"].ldraw_id=="3008"
    assert CANONICAL_LDRAW_PARTS["PLATE_1X3"].ldraw_id=="3623"
    assert new_part("one","PLATE_1X3",7,4,12,1).width_studs==3
    assert new_part("two","PLATE_1X3",7,4,12,1).length_studs==1
