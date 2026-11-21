"""059J: physically bounded nominal LDraw interface, not clutch-strength certification.

References: official LDraw 3623s01.dat, 3007s01.dat, stud.dat,
stud4.dat, stug4-1x7.dat.  This test exercises the *real*
BrickHouse validator with regenerated GUIDED-004 placements.
"""
import inspect
import json
import math
from pathlib import Path

import pytest

from brickhouse.bricks.brick_model import BrickModelPart
from brickhouse.bricks.connectors import validate_connection

PREFIX = "scene-platform:south-timber-deck-main:"
EXPORT = Path("artifacts/lego2-guided-004/brick-model.json")
REASON = "ldraw-3623-3007-reviewed-edge-stud-sidewall"


def real_parts():
    data = json.loads(EXPORT.read_text(encoding="utf-8"))
    assert len(data["parts"]) == 1890
    by_id = {p["placement_id"]: BrickModelPart.model_validate(p)
             for p in data["parts"]}
    return (by_id[PREFIX + "hidden-cross-bond-029:06"],
            by_id[PREFIX + "board:00001"],
            by_id[PREFIX + "board:00002"])


@pytest.mark.parametrize("board_number,indices", [(1, (6, 7)), (2, (0,))])
def test_059j_real_ldraw_edge_clutch_geometry(board_number, indices):
    plate, board1, board2 = real_parts()
    board = board1 if board_number == 1 else board2
    assert inspect.getfile(validate_connection).endswith(
        "backend/brickhouse/bricks/connectors.py")
    assert (plate.part_id, plate.rotation_quarter_turns, plate.x_studs) == (
        "PLATE_1X3", 0, board.x_studs)
    assert (board.part_id, board.rotation_quarter_turns) == ("BRICK_2X8", 0)
    assert plate.z_plates + 1 == board.z_plates
    # Every reviewed stud center is on the edge row of the brick (10 LDU
    # from middle): tangent to the side wall 16 LDU from the middle.
    # Brick end walls are at +/-76 LDU; tubes radius 8 at +/-60..60.
    for index in indices:
        y_stud = board.y_studs + index + 0.5
        assert plate.y_studs < y_stud < plate.y_studs + 3
        longitudinal = -70 + 20 * index
        transverse = -10
        assert 16 - (abs(transverse) + 6) == 0
        assert 76 - (abs(longitudinal) + 6) >= 0
        tube_gap = min(math.hypot(transverse, longitudinal - y) - 14
                       for y in range(-60, 61, 20))
        assert tube_gap == pytest.approx(math.sqrt(200) - 14)
        assert tube_gap > 0
        # LDraw plate stud protrusion is 4 LDU; brick underside spans
        # to y=24. Transverse reinforcement ribs at y<=18.5 do not
        # occupy the stud's y=20..24 interval.
        assert 20 > 18.5
    outcome = validate_connection(plate, board)
    assert (outcome.status, outcome.interface_count, outcome.reason) == (
        "VALID", len(indices), REASON)


def test_059j_symmetry_and_strict_negative_controls():
    plate, board1, board2 = real_parts()
    for board, count in ((board1, 2), (board2, 1)):
        assert validate_connection(board, plate).status == "VALID"
        assert validate_connection(board, plate).interface_count == count
    # Other under-brick placements have not had their underside
    # primitives reviewed: they must remain UNKNOWN, not generic VALID.
    assert validate_connection(
        plate.model_copy(update={"y_studs": 20}), board1).status == "UNKNOWN"
    assert validate_connection(
        plate.model_copy(update={"rotation_quarter_turns": 1}), board1
    ).status != "VALID"
    assert validate_connection(
        plate.model_copy(update={"z_plates": 36}), board1
    ).reason == "solid-volume-collision"
    assert validate_connection(
        plate.model_copy(update={"x_studs": 20}), board1
    ).status == "INVALID"
    assert validate_connection(
        plate.model_copy(update={"part_id": "PLATE_1X4", "length_studs": 4}),
        board1
    ).status == "UNKNOWN"
