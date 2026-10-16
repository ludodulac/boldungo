"""059I: LDraw nominal clutch-surface calculations for actual GUIDED-004 pieces.

LDraw reference dimensions supplied from official primitives:
stud.dat radius=6; stud4.dat outer tube radius=8;
3007s01.dat inner sidewalls at +/-16 LDU and endwalls +/-76 LDU;
stud rows at +/-10, longitudinal centers -70..70, tubes at -60..60.
These assertions prove nominal clearance, NOT physical grip or continuous
physical grip. Reviewed end-row placements are modeled VALID; strength remains untested.
"""
import json
import math
from pathlib import Path

import pytest
from brickhouse.bricks.brick_model import BrickModelPart
from brickhouse.bricks.connectors import validate_connection

PREFIX = "scene-platform:south-timber-deck-main:"
EXPORT = Path("artifacts/lego2-guided-004/brick-model.json")
STUD_R, TUBE_R, WALL_X, WALL_Y = 6, 8, 16, 76


def surface_metrics(transverse, longitudinal):
    """Signed nominal clearances to sidewall, endwall and nearest tube."""
    side_clearance = WALL_X - (abs(transverse) + STUD_R)
    end_clearance = WALL_Y - (abs(longitudinal) + STUD_R)
    tube_x = 0
    tube_y = min(range(-60, 61, 20), key=lambda y: abs(y - longitudinal))
    tube_clearance = math.hypot(transverse - tube_x, longitudinal - tube_y) - (STUD_R + TUBE_R)
    return side_clearance, end_clearance, tube_clearance, tube_y


def test_059i_actual_three_studs_nominal_surfaces():
    raw = json.loads(EXPORT.read_text(encoding="utf-8"))
    assert len(raw["parts"]) == 1890
    by_id = {p["placement_id"]: BrickModelPart.model_validate(p) for p in raw["parts"]}
    plate = by_id[PREFIX + "hidden-cross-bond-029:06"]
    boards = (by_id[PREFIX + "board:00001"], by_id[PREFIX + "board:00002"])
    assert (plate.part_id, plate.x_studs, plate.y_studs, plate.z_plates, plate.rotation_quarter_turns) == ("PLATE_1X3", 3, 23, 35, 0)
    for board, expected in zip(boards, (2, 1)):
        assert (board.part_id, board.x_studs, board.z_plates, board.rotation_quarter_turns) == ("BRICK_2X8", 3, 36, 0)
        common = [plate.y_studs + .5 + i for i in range(3)
                  if board.y_studs <= plate.y_studs + .5 + i < board.y_studs + 8]
        assert len(common) == expected
        for house_y in common:
            # Test BOTH signs; a quarter-turn value alone does not specify
            # which local LDraw X sign maps to positive house Y.
            index = int(house_y - board.y_studs - .5)
            for sign in (-1, 1):
                long_ldu = sign * (-70 + 20 * index)
                transverse_ldu = sign * 10
                side, end, tube, nearest_tube_y = surface_metrics(transverse_ldu, long_ldu)
                assert side == 0
                assert end >= 0
                assert tube == pytest.approx(math.sqrt(200) - 14)
                assert tube > 0
                print(f"059I SURFACE board={board.placement_id} house_y={house_y} local_x={long_ldu} local_z={transverse_ldu} side_gap={side} end_gap={end} nearest_tube_x={nearest_tube_y} tube_gap={tube:.6f}", flush=True)
        result = validate_connection(plate, board)
        print(f"059I VALIDATOR board={board.placement_id} STATUS={result.status} INTERFACE_COUNT={result.interface_count} REASON={result.reason}", flush=True)
        assert (result.status, result.interface_count) == ("VALID", expected)


@pytest.mark.parametrize("transverse,longitudinal,expected", [
    (11, 70, "sidewall-penetration"),
    (10, 71, "endwall-penetration"),
    (0, 60, "tube-penetration"),
    (10, 70, "nominal-clear"),
])
def test_059i_surface_negative_controls(transverse, longitudinal, expected):
    side, end, tube, _ = surface_metrics(transverse, longitudinal)
    outcome = ("sidewall-penetration" if side < 0 else
               "endwall-penetration" if end < 0 else
               "tube-penetration" if tube < 0 else "nominal-clear")
    assert outcome == expected
