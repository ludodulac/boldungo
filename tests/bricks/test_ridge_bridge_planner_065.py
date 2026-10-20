"""065: straight gable ridge bridges for arbitrary houses, without mutation."""
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from brickhouse.bricks.ridge_bridge_planner_065 import propose_ridge_bridges


def part(pid, part_id, side, x, y, z, turns=0):
    return SimpleNamespace(placement_id=pid, part_id=part_id, component="roof",
                           roof_side=side, x_studs=x, y_studs=y, z_plates=z,
                           rotation_quarter_turns=turns)


def house(name, *parts):
    return SimpleNamespace(building_id=name, parts=list(parts))


def test_transverse_tile_reaches_both_opposing_real_30363_stud_rows():
    m = house("another-gable",
              part("neg", "BRICK_SLOPED_18_4X2", "negative", 38, 4, 117),
              part("pos", "BRICK_SLOPED_18_4X2", "positive", 39, 4, 117),
              part("old", "TILE_2X4", "ridge", 39, 4, 120))
    result = propose_ridge_bridges(m)
    assert result["status"] == "GEOMETRIC_PROPOSAL_REQUIRES_PHYSICAL_REVIEW"
    assert result["proposed_count"] == 1
    assert result["replace_ridge_ids"] == ["old"]
    tile = result["proposed_tiles"][0]
    assert (tile["part_id"], tile["x_studs"], tile["y_studs"],
            tile["z_plates"], tile["rotation_quarter_turns"]) == (
                "TILE_2X3", 39, 4, 120, 1)
    assert tile["proof"] == "EXPOSED_STUD_PROJECTION_ONLY"
    assert result["model_mutated"] is False
    assert result["physical_certification"] == "NOT_CERTIFIED"
    assert m.parts[2].part_id == "TILE_2X4"


def test_rotated_gable_stud_rows_need_opposite_ridge_orientation():
    # Genuine 30363 stud coordinates for canonical turn1, 060S:
    # negative (14,5),(15,5), positive (14,2),(15,2).
    m = house("ridge-along-x",
              part("neg", "BRICK_SLOPED_18_4X2", "negative", 14, 2, 93, 1),
              part("pos", "BRICK_SLOPED_18_4X2", "positive", 14, 2, 93, 1))
    result = propose_ridge_bridges(m)
    assert result["proposed_count"] == 1
    tile = result["proposed_tiles"][0]
    assert (tile["part_id"], tile["x_studs"], tile["y_studs"],
            tile["z_plates"], tile["rotation_quarter_turns"]) == (
                "TILE_2X4", 14, 2, 96, 0)
    assert result["physical_certification"] == "NOT_CERTIFIED"


def test_unreviewed_slope_family_not_assumed_compatible():
    m = house("roof33",
              part("neg", "BRICK_SLOPED_33_3X4", "negative", 10, 0, 9),
              part("pos", "BRICK_SLOPED_33_3X4", "positive", 11, 0, 9))
    result = propose_ridge_bridges(m)
    assert result["proposed_count"] == 0
    assert result["unknown_slope_count"] == 2
    assert result["status"] == "NO_TWO_SIDED_BRIDGE_FOUND"


def test_shed_roof_requires_no_opposing_ridge_and_creates_no_piece():
    m = house("single-pitch", part("mono", "BRICK_SLOPED_45_2X4",
                                   "slope", 0, 0, 6))
    result = propose_ridge_bridges(m)
    assert result["status"] == "NO_OPPOSING_RIDGE_REQUIRED"
    assert result["proposed_count"] == 0


def test_odd_longitudinal_length_is_explicitly_unresolved():
    m = house("odd", part("a", "UNKNOWN", "negative", 0, 0, 9),
              part("b", "UNKNOWN", "positive", 0, 0, 9))
    def provider(p):
        x = 10 if p.roof_side == "negative" else 8
        return {(x, y, 12) for y in range(3)}
    r = propose_ridge_bridges(m, stud_provider=provider)
    assert r["proposed_count"] == 1
    assert r["unresolved_count"] == 1
    assert r["unresolved"][0]["reason"] == "UNBRIDGED_ODD_LENGTH_TAIL"
    assert r["status"] == "PARTIAL_GEOMETRIC_PROPOSAL"


def test_bridge_proposals_are_bounded_and_non_mutating():
    m = house("limited",
              part("neg", "BRICK_SLOPED_18_4X2", "negative", 38, 0, 117),
              part("pos", "BRICK_SLOPED_18_4X2", "positive", 39, 0, 117),
              part("neg2", "BRICK_SLOPED_18_4X2", "negative", 38, 2, 117),
              part("pos2", "BRICK_SLOPED_18_4X2", "positive", 39, 2, 117))
    result = propose_ridge_bridges(m, max_tiles=1)
    assert result["proposed_count"] == 1
    assert result["unresolved_count"] == 1
    assert result["unresolved"][0]["reason"] == "MAX_TILES_REACHED"
    assert len(m.parts) == 4
    with pytest.raises(ValueError, match="positive"):
        propose_ridge_bridges(m, max_tiles=0)


def test_1890_piece_guided004_proposes_23_not_unverified_canonical_change():
    path = Path("artifacts/lego2-guided-004/brick-model.json")
    if not path.is_file():
        pytest.skip("real GUIDED-004 export not in checkout")
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert len(raw["parts"]) == 1890
    model = house(raw["building_id"],
                  *(SimpleNamespace(**p) for p in raw["parts"]))
    before = [(p.placement_id, p.part_id, p.x_studs, p.y_studs)
              for p in model.parts]
    result = propose_ridge_bridges(model)
    assert result["proposed_count"] == 23
    assert result["existing_ridge_count"] == 12
    assert len(result["replace_ridge_ids"]) == 12
    assert result["net_part_change_if_approved"] == 11
    assert result["unresolved_count"] == 0
    assert result["unknown_slope_count"] == 0
    assert all(t["part_id"] == "TILE_2X3" and
               t["rotation_quarter_turns"] == 1 and
               t["x_studs"] == 39 and t["z_plates"] == 120
               for t in result["proposed_tiles"])
    assert sorted(t["y_studs"] for t in result["proposed_tiles"]) == list(range(0, 46, 2))
    assert result["model_mutated"] is False
    assert result["physical_certification"] == "NOT_CERTIFIED"
    assert before == [(p.placement_id, p.part_id, p.x_studs, p.y_studs)
                      for p in model.parts]


def test_existing_correct_ridge_not_unnecessarily_replaced():
    m = house("already-cross-braced",
              part("neg", "BRICK_SLOPED_18_4X2", "negative", 38, 4, 117),
              part("pos", "BRICK_SLOPED_18_4X2", "positive", 39, 4, 117),
              part("good", "TILE_2X3", "ridge", 39, 4, 120, 1))
    result = propose_ridge_bridges(m)
    assert result["proposed_count"] == 0
    assert result["already_two_sided_aligned_ridge_ids"] == ["good"]
    assert result["replace_ridge_ids"] == []
    assert result["status"] == "EXISTING_TWO_SIDED_STUD_ALIGNMENT_ONLY"
    assert result["physical_certification"] == "NOT_CERTIFIED"
