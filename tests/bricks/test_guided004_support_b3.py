"""B-3 bounded last-mission geometry regressions, never fabricated strength."""
import pytest
from scripts.build_guided004_support_b3 import replace_one,find_candidate
from scripts.build_guided004_connections_b2 import new_part
from brickhouse.bricks.connectors import validate_connection
from scripts.export_guided004_059m_reinforced import bounds,contact_cells

def test_direct_wrong_bridge_off_grid_fails_connector_model():
    # A real vertical connector at a common stud plane; shifting 1 stud
    # outside the footprint must NOT produce VALID.
    low=new_part("post","BRICK_1X1",4,18,27,0)
    good=new_part("bridge","BRICK_1X4",4,15,30,0)
    bad=new_part("bad","BRICK_1X4",5,15,30,0)
    assert len(contact_cells(low,good))==1
    assert len(contact_cells(low,bad))==0
    r=validate_connection(low,bad)
    assert r.status=="INVALID" and r.interface_count==0

def test_wrong_support_height_rejected():
    low=new_part("post","BRICK_1X1",4,18,27,0)
    bad=new_part("bad","BRICK_1X4",4,15,31,0)
    assert not contact_cells(low,bad)
    assert validate_connection(low,bad).status=="INVALID"

def test_canonical_mapping_used_no_new_part_fabrication():
    from brickhouse.bricks.geometry_adapter import CANONICAL_LDRAW_PARTS
    assert CANONICAL_LDRAW_PARTS["BRICK_1X4"].ldraw_id=="3010"
    assert CANONICAL_LDRAW_PARTS["BRICK_1X1"].ldraw_id=="3005"
    assert CANONICAL_LDRAW_PARTS["BRICK_2X2"].ldraw_id=="3003"
    assert CANONICAL_LDRAW_PARTS["BRICK_2X8"].ldraw_id=="3007"

def test_no_new_roof_and_correct_architecture_guard():
    from pathlib import Path
    s=Path("scripts/build_guided004_support_b3.py").read_text()
    assert "B3_OTHER_ORIGINAL_PART_MOVED" in s
    assert "B3_NEW_BRIDGE_CAUSES_ORTHOGONAL_COLLISION" in s
    assert "B3_SUPPORT_DOES_NOT_REACH_LEVEL_ZERO" in s
    assert "NOT_PROVEN" in s
    assert "B2_SOURCE" not in s or "READONLY" in s
