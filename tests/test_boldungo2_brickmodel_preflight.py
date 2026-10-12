"""Real BrickModel JSON preflight: positive fixture and negative failure cases."""
import json
import pytest

from brickhouse.bricks.physical_wall_fixture import opening_wall_brick_model
from scripts.preflight_boldungo2_brickmodel import check_model_data


def test_actual_brickmodel_fixture_passes_limited_preflight():
    result = check_model_data(opening_wall_brick_model().model_dump(mode="json"))
    assert result["status"] == "ORTHOGONAL_PREFLIGHT_PASS"
    assert result["model_parts"] == result["notice_parts"] == 12
    assert result["physical_certification"] is False
    assert result["insertion"] == "NOT_TESTED"
    assert result["stability"] == "NOT_TESTED"


def test_preflight_rejects_non_catalog_part():
    data = opening_wall_brick_model().model_dump(mode="json")
    data["parts"][0]["part_id"] = "FICTIONAL_BRICK"
    with pytest.raises(ValueError, match="PHYSICAL_GATE_FAIL"):
        check_model_data(data)


def test_preflight_rejects_overlapping_part():
    data = opening_wall_brick_model().model_dump(mode="json")
    data["parts"][1]["x_studs"] = data["parts"][0]["x_studs"]
    with pytest.raises(ValueError, match="SOLID_COLLISION"):
        check_model_data(data)


def test_preflight_rejects_missing_stud_support():
    data = opening_wall_brick_model().model_dump(mode="json")
    top = next(p for p in data["parts"] if p["z_plates"] == 12)
    top["z_plates"] = 18
    with pytest.raises(ValueError, match="NO_STUD_SUPPORT"):
        check_model_data(data)


def test_preflight_rejects_invalid_json_contract():
    data = opening_wall_brick_model().model_dump(mode="json")
    data["parts"][0]["rotation_quarter_turns"] = 7
    with pytest.raises(ValueError):
        check_model_data(data)
