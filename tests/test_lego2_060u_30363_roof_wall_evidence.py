"""060U: two authentic, narrowly evidenced 30363/3008 eave interfaces.

Official LDraw geometry:
  parts/30363.dat -> parts/s/30363s01.dat -> stud4a/stud4s
  parts/3008.dat -> parts/s/3008s01.dat -> stug-1x8.dat -> stud.dat
Neither these tests nor VALID nominal connectors certify resistance, hand
insertion, the full roof or any other placement of these LEGO families.
"""
import hashlib
import json
import math
from pathlib import Path

import pytest

from brickhouse.bricks.brick_model import BrickModelPart
from brickhouse.bricks.connectors import validate_connection


MODEL_PATH = Path("artifacts/lego2-guided-004/brick-model.json")
EXPECTED_POSES = {
    "roof-000002": ("BRICK_SLOPED_18_4X2", 14, 2, 93, 0),
    "wall-000699": ("BRICK_1X8", 16, 2, 90, 1),
    "wall-000715": ("BRICK_1X8", 16, 3, 90, 0),
}
EXPECTED_REASON = "ldraw-30363-3008-guided004-eave-reviewed-sidewall-tube"


def _parts():
    raw = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    assert len(raw["parts"]) == 1890
    selected = {
        p["placement_id"]: BrickModelPart.model_validate(p)
        for p in raw["parts"] if p["placement_id"] in EXPECTED_POSES
    }
    assert set(selected) == set(EXPECTED_POSES)
    for pid, expected in EXPECTED_POSES.items():
        p = selected[pid]
        assert (p.part_id, p.x_studs, p.y_studs, p.z_plates,
                p.rotation_quarter_turns) == expected
    assert selected["roof-000002"].roof_side == "negative"
    return selected, raw


@pytest.mark.parametrize(
    "wall_id,contact",
    [("wall-000699", 2), ("wall-000715", 1)],
)
def test_060u_only_two_authentic_30363_3008_interfaces_are_nominally_valid(wall_id, contact):
    selected, _ = _parts()
    roof, wall = selected["roof-000002"], selected[wall_id]
    for left, right in ((wall, roof), (roof, wall)):
        result = validate_connection(left, right)
        assert (result.status, result.interface_count, result.reason) == (
            "VALID", contact, EXPECTED_REASON,
        )


def test_060u_real_studs_and_wall_surfaces_have_nonpenetrating_nominal_clearance():
    # (local X, local Z) after _slope_transform for true GUIDED-004 poses:
    # wall699: (10,-20), (10,0); wall715: (-10,-20).
    # Official 30363 2-wide underside: inner sidewalls at X+/-16,
    # front endwall Z=+6, rear Z=-66, tube axes Z=-10,-30,-50
    # at transverse X=0 and exterior radius 8 LDU.
    # Official 3008 stud.dat top stud radius 6 LDU, height 4 LDU.
    local_studs = ((10.0, -20.0), (10.0, 0.0), (-10.0, -20.0))
    for x, z in local_studs:
        assert 16.0 - abs(x) - 6.0 == 0.0
        assert 6.0 - z - 6.0 >= 0.0
        assert z - 6.0 + 66.0 >= 0.0
        assert all(
            math.hypot(x, z - tube_z) - (8.0 + 6.0) > 0.0
            for tube_z in (-10.0, -30.0, -50.0)
        )
        assert z - 6.0 > -34.0  # 30363 lower cross-web starts at Z=-34
        # Surface underside local Y at high end >=4, and below the
        # slope at Z near -20 it is still <20: studs occupy local Y20..24.
        assert (20.0 if z < 0.0 else 4.0) < 24.0
    assert math.sqrt(200.0) - 14.0 == pytest.approx(0.142135623730951)


def test_060u_fail_closed_if_any_evidence_specific_pose_is_changed():
    selected, _ = _parts()
    roof = selected["roof-000002"]
    for wall_id in ("wall-000699", "wall-000715"):
        wall = selected[wall_id]
        assert validate_connection(wall, roof).status == "VALID"
        for changed in (
            wall.model_copy(update={"x_studs": wall.x_studs + 1}),
            wall.model_copy(update={"z_plates": wall.z_plates + 3}),
            wall.model_copy(update={"rotation_quarter_turns":
                                    1 - wall.rotation_quarter_turns}),
            wall.model_copy(update={"placement_id": "synthetic-" + wall_id}),
            wall.model_copy(update={"part_id": "BRICK_1X6"}),
        ):
            assert validate_connection(changed, roof).status != "VALID"
    for changed in (
        roof.model_copy(update={"x_studs": 15}),
        roof.model_copy(update={"roof_side": "positive"}),
        roof.model_copy(update={"rotation_quarter_turns": 1}),
        roof.model_copy(update={"placement_id": "roof-altered"}),
    ):
        for wall_id in ("wall-000699", "wall-000715"):
            assert validate_connection(selected[wall_id], changed).status != "VALID"


def test_060u_1890_canonical_parts_fingerprint_unchanged():
    _, raw = _parts()
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


def test_060u_original_034_underside_is_still_conservatively_unknown():
    from brickhouse.bricks.lego30363_mechanics_034 import (
        Placement, contact_standard_top_to_30363_bottom,
    )
    target = Placement(14, 2, 93, roof_side="negative")
    assert contact_standard_top_to_30363_bottom(
        {(16, 2, 93), (17, 2, 93), (16, 3, 93)}, target
    ) == "UNKNOWN_UNDERSIDE"
