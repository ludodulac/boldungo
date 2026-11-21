"""Reusable roof evidence: real GUIDED-004 plus unrelated roof layouts."""
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from brickhouse.bricks.roof_ridge_diagnostics import analyze_roof_ridge_evidence


def part(pid, part_id, side, x, y, z, rotation=0):
    return SimpleNamespace(
        placement_id=pid, part_id=part_id,
        component="roof", roof_side=side,
        x_studs=x, y_studs=y, z_plates=z,
        rotation_quarter_turns=rotation,
    )


def model(building_id, *parts):
    return SimpleNamespace(building_id=building_id, parts=parts)


def test_different_gable_house_shows_one_sided_ridge_and_projected_overlap():
    m = model("small-gable", part("north", "BRICK_SLOPED_18_4X2", "negative", 38, 0, 117),
              part("south", "BRICK_SLOPED_18_4X2", "positive", 39, 0, 117),
              part("ridge", "TILE_2X4", "ridge", 39, 0, 120))
    result = analyze_roof_ridge_evidence(m)
    assert result["roof_pattern"] == "GABLE_CANDIDATE"
    assert result["ridge_evidence"][0]["sides_with_stud_alignment"] == ["positive"]
    assert result["ridge_evidence"][0]["status"] == "ONE_SIDE_STUD_PROJECTION_ONLY"
    assert result["opposing_slope_same_level_projection"]["candidate_pairs"] == 1
    assert result["opposing_slope_same_level_projection"]["mesh_intersection_verdict"] == "NOT_EVALUATED"
    assert result["physical_certification"] == "NOT_CERTIFIED"


def test_same_rule_works_for_different_house_coordinates_and_rotated_ridge():
    m = model("another-house", part("a", "BRICK_SLOPED_18_4X2", "negative", 48, 20, 120),
              part("b", "BRICK_SLOPED_18_4X2", "positive", 49, 20, 120),
              part("r", "TILE_2X4", "ridge", 49, 20, 123, rotation=1))
    r = analyze_roof_ridge_evidence(m)
    assert r["ridge_alignment_counts"] == {"BOTH_SIDES_STUD_PROJECTION_ONLY": 1}
    assert r["physical_certification"] == "NOT_CERTIFIED"


def test_unreviewed_sloped_family_is_unknown_not_false_pass_or_failure():
    m = model("other-pitch", part("neg", "BRICK_SLOPED_33_3X4", "negative", 10, 2, 12),
              part("pos", "BRICK_SLOPED_33_3X4", "positive", 11, 2, 12),
              part("r", "TILE_2X4", "ridge", 11, 2, 15))
    result = analyze_roof_ridge_evidence(m)
    assert result["ridge_alignment_counts"] == {"UNKNOWN_UNREVIEWED_TOP_CONNECTORS": 1}
    assert result["ridge_evidence"][0]["unknown_sides"] == ["negative", "positive"]


def test_mono_pitch_house_is_not_falsely_flagged_for_absent_ridge():
    m = model("shed", part("roof", "BRICK_SLOPED_45_2X4", "slope", 0, 0, 9))
    r = analyze_roof_ridge_evidence(m)
    assert r["roof_pattern"] == "MONO_PITCH_NO_RIDGE_EXPECTED"
    assert not r["ridge_missing_in_gable_candidate"]
    assert r["ridge_alignment_counts"] == {}


def test_missing_gable_ridge_reported_without_declaring_mechanical_failure():
    m = model("gable-no-ridge", part("a", "BRICK_SLOPED_18_4X2", "negative", 1, 0, 9),
              part("b", "BRICK_SLOPED_18_4X2", "positive", 2, 0, 9))
    r = analyze_roof_ridge_evidence(m)
    assert r["ridge_missing_in_gable_candidate"]
    assert r["physical_certification"] == "NOT_CERTIFIED"


def test_guided004_production_export_is_input_not_a_special_case():
    path = Path("artifacts/lego2-guided-004/brick-model.json")
    if not path.is_file():
        pytest.skip("Regenerated production export not present in this checkout")
    raw = json.loads(path.read_text())
    assert len(raw["parts"]) == 1890
    m = model(raw["building_id"], *(SimpleNamespace(**p) for p in raw["parts"]))
    r = analyze_roof_ridge_evidence(m)
    assert r["ridge_tiles"] == 12
    assert r["slope_tiles"] == 408
    assert r["ridge_alignment_counts"] == {"ONE_SIDE_STUD_PROJECTION_ONLY": 12}
    assert r["opposing_slope_same_level_projection"]["candidate_pairs"] == 23
    assert r["physical_certification"] == "NOT_CERTIFIED"

def test_single_gable_side_does_not_require_a_ridge():
    m = model("incomplete-roof", part("slope", "BRICK_SLOPED_18_4X2", "negative", 0, 0, 9))
    r = analyze_roof_ridge_evidence(m)
    assert r["roof_pattern"] == "OTHER_OR_MIXED_ROOF"
    assert not r["ridge_missing_in_gable_candidate"]
    assert r["physical_certification"] == "NOT_CERTIFIED"
