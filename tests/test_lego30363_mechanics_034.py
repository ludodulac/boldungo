"""034: three mechanical-contact cases plus real GUIDED-004 section."""
from brickhouse.bricks.lego30363_mechanics_034 import (
    Placement, top_studs, contact_30363_top_to_standard_bottom,
    contact_standard_top_to_30363_bottom, contact_adjacent_slopes,
)

def test_a_30363_above_standard_support_not_falsely_certified():
    slope = Placement(8, 12, 93)
    assert contact_standard_top_to_30363_bottom({(8,12,93)}, slope) == "UNKNOWN_UNDERSIDE"
    assert contact_standard_top_to_30363_bottom({(80,12,93)}, slope) == "NO_CONTACT"

def test_b_adjacent_30363_studs_exposed_but_clutch_unverified():
    lower = Placement(8, 12, 93)
    assert len(top_studs(lower)) == 2
    upper = Placement(8, 12, 96)
    assert contact_adjacent_slopes(lower, upper) == "UNKNOWN_UNDERSIDE"
    assert contact_30363_top_to_standard_bottom(lower, {(8,12,96)}) == "KNOWN_TOP_STUD_CONTACT_BOTTOM_MATING_UNVERIFIED"

def test_c_incompatible_position_rejected():
    lower = Placement(8, 12, 93)
    assert contact_adjacent_slopes(lower, Placement(20, 12, 96)) == "NO_CONTACT"
    assert contact_30363_top_to_standard_bottom(lower, {(8,12,95)}) == "NO_CONTACT"

def test_guided004_real_section_from_export():
    import json
    from pathlib import Path
    model = json.loads(Path("artifacts/lego2-guided-004/brick-model.json").read_text())
    roof = [p for p in model["parts"] if p["part_id"] == "BRICK_SLOPED_18_4X2"]
    assert len(roof) == 408
    section = sorted(roof, key=lambda p: (p["z_plates"],p["x_studs"],p["y_studs"]))[:4]
    assert len(section) == 4
    for p in section:
        placement = Placement(p["x_studs"],p["y_studs"],p["z_plates"],p["rotation_quarter_turns"])
        assert len(top_studs(placement)) == 2
        # The current export cannot certify any receiving underside connector.
        assert contact_standard_top_to_30363_bottom(
            {(p["x_studs"],p["y_studs"],p["z_plates"])},placement
        ) == "UNKNOWN_UNDERSIDE"
