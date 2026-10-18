"""060J: finite straight-down insertion, never physical/handheld certification."""
import json
from pathlib import Path

import pytest

from brickhouse.bricks.brick_model import BrickModelPart, BrickModel
from brickhouse.bricks.assembly import AssemblyPlan
from brickhouse.bricks.connectors import validate_connection
from brickhouse.bricks.vertical_insertion import (
    check_vertical_insertion, audit_notice_vertical_insertion,
)

MODULE = ("wall-000012", "wall-000034", "wall-000060", "wall-000081")
STEPS = ("step-0003", "step-0007", "step-0011", "step-0015")
SOURCE = Path("artifacts/lego2-guided-004/viewer-export.json")


def brick(pid, part_id="BRICK_1X6", x=0, y=0, z=0, rotation=0):
    return BrickModelPart(
        placement_id=pid, part_id=part_id, category="brick", component="wall",
        facade="rear", x_studs=x, y_studs=y, z_plates=z,
        rotation_quarter_turns=rotation,
    )


def test_a_clear_finite_descent_reports_only_geometry():
    p = brick("mobile", z=3)
    x = check_vertical_insertion(p, [], rise_plates=30)
    assert x["verdict"] == "GEOMETRY_CLEAR_ONLY"
    assert x["initial_position"] == [0, 0, 33]
    assert x["final_position"] == [0, 0, 3]
    assert x["swept_bounds"] == [0, 0, 3, 1, 6, 36]
    assert x["direction"] == "VERTICAL_NEGATIVE_Z"
    assert x["access_from_outside"] == "NOT_TESTED"
    assert x["manual_insertion"] == "NOT_TESTED"
    assert x["physical_certification"] == "NOT_CERTIFIED"


def test_b_installed_overhead_piece_blocks_swept_volume():
    p = brick("moving", z=3)
    already = brick("overhead", z=12)
    r = check_vertical_insertion(p, [already])
    assert r["verdict"] == "BLOCKED"
    assert r["blockers"] == ["overhead"]
    assert r["installed_ids"] == ["overhead"]


def test_c_final_contact_with_support_is_not_collision():
    lower = brick("foundation", part_id="BRICK_1X8", z=0)
    upper = brick("upper", part_id="BRICK_1X6", z=3)
    assert validate_connection(lower, upper).status == "VALID"
    result = check_vertical_insertion(upper, [lower])
    assert result["verdict"] == "GEOMETRY_CLEAR_ONLY"
    assert result["blockers"] == []
    assert result["final_support_contacts"] == ["foundation"]


def test_d_unknown_geometry_near_sweep_does_not_falsely_clear():
    unknown = BrickModelPart.model_construct(
        placement_id="sloped-unverified", part_id="BRICK_SLOPED_18_4X2",
        category="roof_tile", component="roof", roof_side="slope",
        x_studs=0, y_studs=0, z_plates=9, rotation_quarter_turns=0,
        width_studs=2, length_studs=4, height_plates=3,
    )
    result = check_vertical_insertion(brick("moving", z=3), [unknown])
    assert result["verdict"] == "UNKNOWN"
    assert result["unknown_geometry"] == ["sloped-unverified"]
    assert result["blockers"] == []


def test_d_distant_unsupported_geometry_is_not_automatically_blocking():
    unknown = BrickModelPart.model_construct(
        placement_id="far-unverified", part_id="BRICK_SLOPED_18_4X2",
        category="roof_tile", component="roof", roof_side="slope",
        x_studs=100, y_studs=100, z_plates=9, rotation_quarter_turns=1,
        width_studs=2, length_studs=4, height_plates=3,
    )
    result = check_vertical_insertion(brick("moving", z=3), [unknown])
    assert result["verdict"] == "GEOMETRY_CLEAR_ONLY"
    assert result["unknown_geometry"] == []


def test_e_later_piece_not_part_of_installed_notice_snapshot():
    earlier = brick("earlier", z=0)
    target = brick("target", z=3)
    later = brick("later", z=12)
    from brickhouse.bricks.assembly import AssemblyStep
    # Fake plan steps only; source placements are test fixtures, not the house.
    class Step:
        def __init__(self, seq, ids):
            self.sequence = seq
            self.step_id = f"step-{seq:04d}"
            self.placement_ids = ids
    class Model:
        parts = [earlier, target, later]
    class Notice:
        steps = [Step(1, ["earlier"]), Step(2, ["target"]), Step(3, ["later"])]
    result = audit_notice_vertical_insertion(Model(), Notice(), ["target"])["target"]
    assert result["verdict"] == "GEOMETRY_CLEAR_ONLY"
    assert result["installed_ids"] == ["earlier"]
    assert "later" not in result["installed_ids"]
    assert result["final_support_contacts"] == ["earlier"]


def test_unordered_peer_with_potential_obstruction_is_unknown_not_clear():
    moving = brick("moving", z=3)
    same_step_other = brick("peer", z=9)
    r = check_vertical_insertion(moving, [], unordered_peers=[same_step_other])
    assert r["verdict"] == "UNKNOWN"
    assert r["ambiguous_same_step"] == ["peer"]
    assert r["blockers"] == []


@pytest.mark.parametrize("rise", [0, -1, 0.1, True])
def test_invalid_rise_fails_explicitly(rise):
    with pytest.raises(ValueError, match="RISE_PLATES_MUST_BE_POSITIVE_INTEGER"):
        check_vertical_insertion(brick("m"), [], rise_plates=rise)


def test_f_real_guided004_four_wall_placements_and_actual_notice_order():
    assert SOURCE.is_file(), "CI must generate authentic GUIDED-004 before pytest"
    full = json.loads(SOURCE.read_text(encoding="utf-8"))
    model = BrickModel.model_validate(full["brick_model"])
    notice = AssemblyPlan.model_validate(full["assembly_plan"])
    assert len(model.parts) == 1890
    by = {p.placement_id: p for p in model.parts}
    expected = [
        ("BRICK_1X8", 16, 43, 0, 1),
        ("BRICK_1X6", 17, 43, 3, 1),
        ("BRICK_1X8", 16, 43, 6, 1),
        ("BRICK_1X6", 17, 43, 9, 1),
    ]
    for pid, (part_id, x, y, z, rot) in zip(MODULE, expected):
        p = by[pid]
        assert (p.part_id, p.x_studs, p.y_studs,
                p.z_plates, p.rotation_quarter_turns) == (part_id, x, y, z, rot)

    for lower, upper in zip(MODULE, MODULE[1:]):
        assert validate_connection(by[lower], by[upper]).status == "VALID"

    isolated = {}
    for i, pid in enumerate(MODULE):
        isolated[pid] = check_vertical_insertion(by[pid], [by[prev] for prev in MODULE[:i]])
        assert isolated[pid]["verdict"] == "GEOMETRY_CLEAR_ONLY"
        assert isolated[pid]["installed_ids"] == sorted(MODULE[:i])

    actual = audit_notice_vertical_insertion(model, notice, MODULE)
    assert [actual[pid]["step_id"] for pid in MODULE] == list(STEPS)
    assert [actual[pid]["step_sequence"] for pid in MODULE] == [3, 7, 11, 15]
    assert [len(actual[pid]["installed_ids"]) for pid in MODULE] == [11, 34, 59, 81]
    for pid in MODULE:
        assert actual[pid]["verdict"] == "GEOMETRY_CLEAR_ONLY"
        assert actual[pid]["blockers"] == []
        assert actual[pid]["unknown_geometry"] == []
        assert actual[pid]["ambiguous_same_step"] == []
        assert len(actual[pid]["unordered_same_step_ids"]) == 5
        assert actual[pid]["physical_certification"] == "NOT_CERTIFIED"
        assert actual[pid]["access_from_outside"] == "NOT_TESTED"
        assert actual[pid]["stability"] == "NOT_TESTED"
    assert actual["wall-000012"]["final_support_contacts"] == []
    assert actual["wall-000034"]["final_support_contacts"] == ["wall-000012"]
    assert actual["wall-000060"]["final_support_contacts"] == [
        "wall-000033", "wall-000034", "wall-000035",
    ]
    assert actual["wall-000081"]["final_support_contacts"] == ["wall-000060"]
