"""034+060S: LDraw 30363 top-stud geometry; underside stays unverified."""
import hashlib
import json
from pathlib import Path

import pytest

from brickhouse.bricks.geometry_adapter import CANONICAL_LDRAW_PARTS, _slope_transform
from brickhouse.bricks.lego30363_mechanics_034 import (
    _30363_BBOX_ONLY,
    Placement,
    top_studs,
    contact_30363_top_to_standard_bottom,
    contact_standard_top_to_30363_bottom,
    contact_adjacent_slopes,
)
from brickhouse.bricks.brick_model import BrickModelPart


def test_a_30363_above_standard_support_not_falsely_certified():
    slope = Placement(8, 12, 93, roof_side="negative")
    assert contact_standard_top_to_30363_bottom({(8, 12, 93)}, slope) == "UNKNOWN_UNDERSIDE"
    assert contact_standard_top_to_30363_bottom({(80, 12, 93)}, slope) == "NO_CONTACT"


def test_b_adjacent_30363_studs_exposed_but_clutch_unverified():
    lower = Placement(8, 12, 93, roof_side="negative")
    assert top_studs(lower) == {(11, 12, 96), (11, 13, 96)}
    upper = Placement(8, 12, 96, roof_side="negative")
    assert contact_adjacent_slopes(lower, upper) == "UNKNOWN_UNDERSIDE"
    assert contact_30363_top_to_standard_bottom(
        lower, {(11, 12, 96)}
    ) == "KNOWN_TOP_STUD_CONTACT_BOTTOM_MATING_UNVERIFIED"


def test_c_incompatible_position_rejected():
    lower = Placement(8, 12, 93, roof_side="negative")
    assert contact_adjacent_slopes(
        lower, Placement(20, 12, 96, roof_side="negative")
    ) == "NO_CONTACT"
    assert contact_30363_top_to_standard_bottom(lower, {(8, 12, 95)}) == "NO_CONTACT"


def test_roof_side_must_be_explicit_for_top_studs():
    with pytest.raises(ValueError, match="30363_ROOF_SIDE_REQUIRED"):
        top_studs(Placement(8, 12, 93))


@pytest.mark.parametrize(
    "side,turns,expected",
    [
        ("negative", 0, {(17, 2, 96), (17, 3, 96)}),
        ("negative", 1, {(14, 5, 96), (15, 5, 96)}),
        ("negative", 2, {(14, 2, 96), (14, 3, 96)}),
        ("negative", 3, {(14, 2, 96), (15, 2, 96)}),
        ("positive", 0, {(14, 2, 96), (14, 3, 96)}),
        ("positive", 1, {(14, 2, 96), (15, 2, 96)}),
        ("positive", 2, {(17, 2, 96), (17, 3, 96)}),
        ("positive", 3, {(14, 5, 96), (15, 5, 96)}),
    ],
)
def test_060s_both_sides_and_four_canonical_rotations(side, turns, expected):
    # Independent expected coordinates based on official 30363.dat:
    # local X=-10/+10, Y=0, Z=0; bbox X[-20,20], Z[-70,10].
    assert top_studs(Placement(14, 2, 93, rotation=turns, roof_side=side)) == expected


def test_060s_adapter_matrix_anchors_actual_30363_not_historical_grid():
    roof = BrickModelPart(
        placement_id="roof-000002", part_id="BRICK_SLOPED_18_4X2",
        category="roof_tile", component="roof", roof_side="negative",
        x_studs=14, y_studs=2, z_plates=93, rotation_quarter_turns=0,
    )
    t = _slope_transform(roof, CANONICAL_LDRAW_PARTS[roof.part_id], _30363_BBOX_ONLY)
    assert (t.matrix[0][3], t.matrix[1][3], t.matrix[2][3]) == (350.0, -768.0, 60.0)
    assert t.matrix[0][:3] == (0.0, 0.0, 1.0)
    assert t.matrix[2][:3] == (-1.0, 0.0, 0.0)
    transformed = {t.point((x, 0.0, 0.0)) for x in (-10.0, 10.0)}
    assert transformed == {(350.0, -768.0, 70.0), (350.0, -768.0, 50.0)}
    assert top_studs(Placement(14, 2, 93, roof_side="negative")) == {
        (17, 2, 96), (17, 3, 96)
    }


def test_060s_canonical_4_by_2_envelope_is_not_legacy_2_by_4():
    roof = Placement(14, 2, 93, roof_side="negative")
    assert contact_standard_top_to_30363_bottom({(17, 3, 93)}, roof) == "UNKNOWN_UNDERSIDE"
    assert contact_standard_top_to_30363_bottom({(14, 5, 93)}, roof) == "NO_CONTACT"
    assert contact_standard_top_to_30363_bottom({(16, 2, 93)}, roof) == "UNKNOWN_UNDERSIDE"
    assert contact_standard_top_to_30363_bottom({(16, 3, 93)}, roof) == "UNKNOWN_UNDERSIDE"


def test_guided004_real_section_from_export():
    model = json.loads(Path("artifacts/lego2-guided-004/brick-model.json").read_text())
    assert len(model["parts"]) == 1890
    roof = [p for p in model["parts"] if p["part_id"] == "BRICK_SLOPED_18_4X2"]
    assert len(roof) == 408
    by_id = {p["placement_id"]: p for p in model["parts"]}
    assert {
        key: by_id["roof-000002"][key]
        for key in (
            "part_id", "x_studs", "y_studs", "z_plates",
            "rotation_quarter_turns", "roof_side", "category",
        )
    } == {
        "part_id": "BRICK_SLOPED_18_4X2",
        "x_studs": 14, "y_studs": 2, "z_plates": 93,
        "rotation_quarter_turns": 0, "roof_side": "negative",
        "category": "roof_tile",
    }
    assert top_studs(Placement(14, 2, 93, roof_side="negative")) == {
        (17, 2, 96), (17, 3, 96)
    }
    section = sorted(
        roof, key=lambda p: (p["z_plates"], p["x_studs"], p["y_studs"])
    )[:4]
    assert len(section) == 4
    for p in section:
        placement = Placement(
            p["x_studs"], p["y_studs"], p["z_plates"],
            p["rotation_quarter_turns"], roof_side=p["roof_side"],
        )
        assert len(top_studs(placement)) == 2
        assert contact_standard_top_to_30363_bottom(
            {(p["x_studs"], p["y_studs"], p["z_plates"])}, placement
        ) == "UNKNOWN_UNDERSIDE"


def test_060s_all_1890_canonical_placement_coordinates_match_060m_export():
    """Baseline: GitHub Actions #39141025551 on immutable LEGO2 060M HEAD.

    Hash ONLY canonical placement facts, not diagnostic 034 evidence whose
    two historical top-stud cells are intentionally being corrected.
    """
    raw = json.loads(Path("artifacts/lego2-guided-004/brick-model.json").read_text())
    keys = (
        "placement_id", "part_id", "category", "component",
        "x_studs", "y_studs", "z_plates", "rotation_quarter_turns",
        "roof_side", "facade", "width_studs", "length_studs", "height_plates",
    )
    placements = sorted(
        ({key: part.get(key) for key in keys} for part in raw["parts"]),
        key=lambda part: part["placement_id"],
    )
    checksum = hashlib.sha256(
        json.dumps(placements, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    assert len(placements) == 1890
    assert checksum == "c45cc07b416b5d4000daf153a974d28079ba6bbc76b4bfbb335a7f32f660607b"


def test_060s_inventory_updates_only_diagnostic_and_keeps_underside_unknown():
    inventory = json.loads(
        Path("artifacts/lego2-guided-004/inventory.json").read_text()
    )
    section = inventory["roof_section_034"]
    by_id = {part["placement_id"]: part for part in section["placements"]}
    assert by_id["roof-000002"]["top_studs_evidenced"] == [
        [17, 2, 96], [17, 3, 96]
    ]
    assert by_id["roof-000002"]["bottom_mating"] == "UNKNOWN_UNDERSIDE"
    assert section["connector_status"] == "TOP_STUDS_VERIFIED_UNDERSIDE_UNVERIFIED"
    assert section["physical_certification"] == "NOT_CERTIFIED"
    assert inventory["mechanical_certification"] == "NOT_CERTIFIED"
