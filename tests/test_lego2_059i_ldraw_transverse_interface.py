"""059I LDraw coordinate evidence, without asserting unproven clutch VALID.

References (official LDraw):
3623s01.dat: stug-1x3 at origin, top stud centers -20,0,20 along local X;
3007s01.dat: stug-1x8 at local Z +/-10; stug4-1x7 at local X -60..60.
LDraw local long X is mapped to house long Y. The sign is not fixed by
BrickModelPart.rotation_quarter_turns=0 alone.
"""
import json
from pathlib import Path

from brickhouse.bricks.brick_model import BrickModelPart
from brickhouse.bricks.connectors import validate_connection

EXPORT = Path("artifacts/lego2-guided-004/brick-model.json")
PREFIX = "scene-platform:south-timber-deck-main:"


def test_059i_ldraw_underside_stud_and_tube_axes():
    raw = json.loads(EXPORT.read_text(encoding="utf-8"))
    assert len(raw["parts"]) == 1890
    by_id = {p["placement_id"]: BrickModelPart.model_validate(p) for p in raw["parts"]}
    plate = by_id[PREFIX + "hidden-cross-bond-029:06"]
    boards = [by_id[PREFIX + "board:00001"], by_id[PREFIX + "board:00002"]]
    assert (plate.x_studs, plate.y_studs, plate.z_plates) == (3, 23, 35)
    assert all(b.x_studs == 3 and b.z_plates == 36 for b in boards)
    # Plate stud centers: local LDraw X = -20, 0, +20.
    plate_centers = {(plate.x_studs + .5, plate.y_studs + .5 + i) for i in range(3)}
    assert plate_centers == {(3.5, 23.5), (3.5, 24.5), (3.5, 25.5)}
    for board, expected in zip(boards, (2, 1)):
        # The two stud rows on the 2-wide brick are at transverse centers
        # x+0.5 and x+1.5. The seven tube centers lie BETWEEN those rows,
        # at x+1.0, longitudinal positions board.y+1 ... board.y+7.
        stud_rows = {board.x_studs + .5, board.x_studs + 1.5}
        tube_centers = {(board.x_studs + 1, board.y_studs + i) for i in range(1, 8)}
        common = sorted((x, y) for x, y in plate_centers
                        if x in stud_rows and board.y_studs < y < board.y_studs + 8)
        assert len(common) == expected
        assert all(abs(x - (board.x_studs + 1)) == .5 for x, _ in common)
        assert all((x, y) not in tube_centers for x, y in common)
        ldraw_long = [(int((y - board.y_studs - .5) * 20 - 70),
                       int(70 - (y - board.y_studs - .5) * 20)) for _, y in common]
        print(f"059I {board.placement_id} STUD_CENTERS={common} LDRAW_X_NORMAL_REVERSED={ldraw_long} TUBE_CENTERS={sorted(tube_centers)}", flush=True)
        result = validate_connection(plate, board)
        print(f"059I CONNECTOR={result.status} COUNT={result.interface_count} REASON={result.reason}", flush=True)
        assert (result.status, result.interface_count) == ("VALID", expected)
    # Stud-to-tube center mismatch is expected for the one-row partial overlap.
    # Exact stud-to-sidewall clutch clearance remains unverified; do not promote VALID.
