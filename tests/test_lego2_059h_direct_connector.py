"""059H: execute the actual BrickHouse connector on the regenerated GUIDED-004 export.

This is a characterization test, NOT evidence of LDraw clutch compatibility.
The CI workflow generates artifacts/lego2-guided-004/brick-model.json before pytest.
"""
import inspect
import json
from pathlib import Path

import pytest

from brickhouse.bricks.brick_model import BrickModelPart
from brickhouse.bricks.connectors import validate_connection


PREFIX = "scene-platform:south-timber-deck-main:"
EXPORT = Path("artifacts/lego2-guided-004/brick-model.json")


def test_059h_real_connector_and_negative_controls():
    assert EXPORT.is_file(), f"Regenerate authentic GUIDED-004 first: {EXPORT}"
    raw = json.loads(EXPORT.read_text(encoding="utf-8"))
    assert len(raw["parts"]) == 1890
    by_id = {p["placement_id"]: p for p in raw["parts"]}
    ids = [
        PREFIX + "hidden-cross-bond-029:06",
        PREFIX + "board:00001",
        PREFIX + "board:00002",
    ]
    assert all(key in by_id for key in ids)
    plate, board1, board2 = (BrickModelPart.model_validate(by_id[key]) for key in ids)
    source = Path(inspect.getfile(validate_connection)).resolve()
    assert source.as_posix().endswith("/backend/brickhouse/bricks/connectors.py"), source
    assert (plate.part_id, plate.x_studs, plate.y_studs, plate.z_plates, plate.rotation_quarter_turns) == ("PLATE_1X3", 3, 23, 35, 0)
    assert (board1.part_id, board1.x_studs, board1.y_studs, board1.z_plates, board1.rotation_quarter_turns) == ("BRICK_2X8", 3, 17, 36, 0)
    assert (board2.part_id, board2.x_studs, board2.y_studs, board2.z_plates, board2.rotation_quarter_turns) == ("BRICK_2X8", 3, 25, 36, 0)

    print(f"059H ORIGINAL_MODULE={source}", flush=True)
    for board, expected in ((board1, 2), (board2, 1)):
        result = validate_connection(plate, board)
        print(f"059H PAIR={plate.placement_id} -> {board.placement_id} STATUS={result.status} INTERFACE_COUNT={result.interface_count} REASON={result.reason}", flush=True)
        # This narrow, nominally documented connection does NOT certify mechanical strength.
        assert (result.status, result.interface_count, result.reason) == (
            "VALID", expected, "ldraw-3623-3007-reviewed-edge-stud-sidewall"
        )

    def mutated(part, **kwargs):
        return part.model_copy(update=kwargs)

    controls = [
        ("horizontal-offset", plate, mutated(board1, x_studs=20), "INVALID", "no-overlapping-stud-columns"),
        ("incorrect-height", plate, mutated(board1, z_plates=38), "INVALID", "no-vertical-connector-plane"),
        ("solid-collision", plate, mutated(board1, z_plates=35), "INVALID", "solid-volume-collision"),
        ("undocumented-family", mutated(plate, part_id="PLATE_1X4", length_studs=4), board1, "UNKNOWN", "underside-interface-not-documented-for-part"),
    ]
    for label, a, b, status, reason in controls:
        result = validate_connection(a, b)
        print(f"059H NEGATIVE={label} STATUS={result.status} REASON={result.reason}", flush=True)
        assert (result.status, result.reason) == (status, reason)
