"""059I: transformed stud-grid correspondence; NOT a proof of underside clutch."""
import json
from pathlib import Path

from brickhouse.bricks.brick_model import BrickModelPart
from brickhouse.bricks.connectors import validate_connection

PREFIX = "scene-platform:south-timber-deck-main:"
EXPORT = Path("artifacts/lego2-guided-004/brick-model.json")


def test_059i_transformed_longitudinal_stud_centers():
    raw = json.loads(EXPORT.read_text(encoding="utf-8"))
    assert len(raw["parts"]) == 1890
    by = {p["placement_id"]: BrickModelPart.model_validate(p) for p in raw["parts"]}
    plate = by[PREFIX + "hidden-cross-bond-029:06"]
    first = by[PREFIX + "board:00001"]
    second = by[PREFIX + "board:00002"]
    assert (plate.rotation_quarter_turns, first.rotation_quarter_turns, second.rotation_quarter_turns) == (0, 0, 0)

    # Each nominal 20-LDU stud column maps to the center of a grid cell.
    # The sign of the LDraw longitudinal axis depends on the LDraw-to-house
    # coordinate transform; both orientations are reported, not assumed.
    studs = [plate.y_studs + i + 0.5 for i in range(3)]
    def overlap(board):
        return [y for y in studs if board.y_studs <= y < board.y_studs + 8]
    assert overlap(first) == [23.5, 24.5]
    assert overlap(second) == [25.5]
    for board, expected in ((first, 2), (second, 1)):
        for y in overlap(board):
            index = int(y - board.y_studs)
            ldraw_plus_y = -70 + 20 * index
            ldraw_minus_y = 70 - 20 * index
            print(f"059I BOARD={board.placement_id} HOUSE_Y={y} LDraw_axis_positive={ldraw_plus_y} LDraw_axis_reversed={ldraw_minus_y}", flush=True)
        result = validate_connection(plate, board)
        print(f"059I VALIDATOR={result.status} COUNT={result.interface_count} REASON={result.reason}", flush=True)
        assert result.interface_count == expected
        assert result.status == "VALID"
    # This test does not inspect the LDraw underside tube/sidewall primitives.
    # The conservative connector now recognizes only reviewed end-row patterns.
