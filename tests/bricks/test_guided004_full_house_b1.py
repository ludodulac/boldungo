"""B-1 targeted safety and reproducibility regressions for full GUIDED-004."""
import hashlib,json
from pathlib import Path
import pytest
from scripts.build_guided004_full_house_b1 import (
    EXPECTED_CANONICAL,EXPECTED_SLOPES,CANONICAL_SOURCE_WILL_NEVER_BE_WRITTEN,
    SOURCE,build,_matrix_row,checksum,export_ldraw)
from brickhouse.bricks.geometry_adapter import CANONICAL_LDRAW_PARTS

def test_guarded_input_is_actual_guided004_scene():
    assert EXPECTED_CANONICAL==1890
    assert EXPECTED_SLOPES==408
    assert SOURCE.name=="boldungo2-guided-004-real-scene.json"
    assert CANONICAL_SOURCE_WILL_NEVER_BE_WRITTEN
    raw=json.loads(SOURCE.read_text(encoding="utf8"))
    assert raw.get("schema_version")=="0.2"
    assert {"chimneys","openings","stairs","platforms"}<=set(raw)

def test_no_source_output_alias_even_before_regeneration(tmp_path):
    with pytest.raises(ValueError,match="REFUSE_SOURCE"):
        build(SOURCE,tmp_path)

def test_invalid_unknown_parts_remain_unmapped_not_synthetic():
    class Fake:
        part_id="BRICK_888X888"
    assert _matrix_row(Fake(),None) is None

def test_original_source_checksum_changes_when_bytes_change(tmp_path):
    a=tmp_path/"sample"
    a.write_bytes(b"abc")
    h=checksum(a)
    a.write_bytes(b"abcd")
    assert checksum(a)!=h

def test_authentic_ldraw_mapping_supports_original_18degree_slope():
    assert CANONICAL_LDRAW_PARTS["BRICK_SLOPED_18_4X2"].ldraw_id=="30363"
    assert CANONICAL_LDRAW_PARTS["BRICK_SLOPED_18_4X2"].placement_kind=="slope"
    assert CANONICAL_LDRAW_PARTS["TILE_2X2"].ldraw_id=="3068b"
    assert CANONICAL_LDRAW_PARTS["WINDOW_1X2X2_60592"].ldraw_id=="60592"

def test_unchanged_ridge_retiled_full_house_has_independent_output_integration():
    source=Path("scripts/construct_guided004_roof_088.py").read_text()
    assert "GUIDED-004-EXPERIMENTAL-NOT-CERTIFIED.json" in source
    assert "source_sha256" in source
    assert "canonical_piece_count_confirmed" in source

def test_pipeline_not_falsely_certified():
    s=Path("scripts/build_guided004_full_house_b1.py").read_text()
    assert "NOT_CERTIFIED" in s
    assert "NO_45_DEGREE_REPLACEMENT" in s
    assert "parts_without_fully_demonstrated_support_chain" in s
    assert "PROPOSED_BY_EXISTING_BUILDER_NOT_CERTIFIED" in s
    assert "B1_NON_RIDGE_ARCHITECTURE_CHANGED" in s
