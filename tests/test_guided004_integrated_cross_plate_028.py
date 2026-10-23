"""028: certify integration artifacts, not a standalone placement mock."""
import json
from pathlib import Path

ROOT = Path("artifacts/lego2-guided-004")
PLATE = "scene-platform:south-timber-deck-main:hidden-cross-plate:00007-00013"
BOARDS = ["scene-platform:south-timber-deck-main:board:" + n for n in ("00001", "00007", "00013")]
POST = "scene-platform:south-timber-deck-main:support-solution:timber-post-east:0033:00022"


def test_real_export_has_cross_plate_bom_notice_and_support_path():
    model = json.loads((ROOT / "brick-model.json").read_text())
    viewer = json.loads((ROOT / "viewer-export.json").read_text())
    inventory = json.loads((ROOT / "inventory.json").read_text())
    parts = {p["placement_id"]: p for p in model["parts"]}
    assert all(pid in parts for pid in [PLATE, *BOARDS, POST])
    plate = parts[PLATE]
    assert (plate["part_id"], plate["category"]) == ("PLATE_1X6", "plate")
    assert (plate["x_studs"], plate["y_studs"], plate["z_plates"]) == (3, 20, 35)
    assert (plate["width_studs"], plate["length_studs"], plate["height_plates"]) == (6, 1, 1)
    assert inventory["references"]["PLATE_1X6"] >= 1
    assert inventory["physical_audit"]["collision_voxel_overlaps"] == 0
    assert PLATE in {p["placement_id"] for p in viewer["brick_model"]["parts"]}
    assert any(line["part_id"] == "PLATE_1X6" for line in viewer["bom"]["lines"])
    steps = viewer["assembly_plan"]["steps"]
    plate_steps = [step for step in steps if PLATE in step["placement_ids"]]
    assert len(plate_steps) == 1 and "maintenir provisoirement" in plate_steps[0]["title"]
    board_steps = [step for step in steps if set(BOARDS) <= set(step["placement_ids"])]
    assert len(board_steps) == 1 and "emboîter" in board_steps[0]["title"]
    assert plate_steps[0]["sequence"] < board_steps[0]["sequence"]
    assert any(POST in step["placement_ids"] and step["sequence"] < plate_steps[0]["sequence"] for step in steps)
    def box(p):
        return (p["x_studs"], p["y_studs"], p["z_plates"],
                p["x_studs"] + p.get("width_studs", 1),
                p["y_studs"] + p.get("length_studs", 1),
                p["z_plates"] + p.get("height_plates", 3))
    def connects(lower, upper):
        a, b = box(lower), box(upper)
        return a[5] == b[2] and a[0] < b[3] and b[0] < a[3] and a[1] < b[4] and b[1] < a[4]
    assert all(connects(plate, parts[pid]) for pid in BOARDS)
    assert connects(parts[POST], parts[BOARDS[0]])
    # The plate itself is retained by its studs above; this is a connection
    # path to a post, not a fabricated direct support below the plate.
    assert plate["placement_id"] in inventory["physical_audit"]["unsupported_placement_ids"]
    print("GUIDED004_028_INTEGRATION=PASS model inventory notice viewer support-path")
