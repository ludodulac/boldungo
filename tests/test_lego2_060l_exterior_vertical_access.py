"""060L: full MODEL-TOP approach based on real prior-step geometry.

Reuses 060J vertical_insertion and canonical GUIDED-004 fixture; tests
do not certify manual insertion, real-world access, strength or stability.
"""
import json
from pathlib import Path

import pytest

from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.assembly import AssemblyPlan
from brickhouse.bricks.vertical_insertion import (
    check_vertical_insertion,
    check_vertical_access_from_above,
    audit_notice_vertical_insertion,
    audit_notice_vertical_access_from_above,
)


MODULE = ("wall-000012", "wall-000034", "wall-000060", "wall-000081")
NOTICE_STEPS = ("step-0003", "step-0007", "step-0011", "step-0015")
VIEWER = Path("artifacts/lego2-guided-004/viewer-export.json")


def brick(pid, *, z=0, x=0, y=0, kind="BRICK_1X6"):
    return BrickModelPart(
        placement_id=pid, part_id=kind, category="brick", component="wall",
        facade="rear", x_studs=x, y_studs=y, z_plates=z,
        rotation_quarter_turns=0,
    )


def unknown(pid="unverified", *, x=0, y=0, z=10):
    return BrickModelPart.model_construct(
        placement_id=pid, part_id="BRICK_SLOPED_18_4X2",
        category="roof_tile", component="roof", roof_side="slope",
        x_studs=x, y_studs=y, z_plates=z,
        rotation_quarter_turns=0,
        width_studs=2, length_studs=4, height_plates=None,
    )


def test_a_complete_top_entry_clear_with_explicit_positive_margin():
    moving = brick("moving", z=3)
    other = brick("remote-tall", x=10, z=45)
    r = check_vertical_access_from_above(moving, [other], clearance_plates=2)
    assert r["verdict"] == "GEOMETRY_CLEAR_ONLY"
    assert r["known_installed_max_top_z"] == 48
    assert r["initial_position"] == [0, 0, 50]
    assert r["final_position"] == [0, 0, 3]
    assert r["rise_plates"] == 47
    assert r["positive_margin_plates"] == 2
    assert r["origin_above_known_solids"] is True
    assert r["access_from_outside"] == "MODEL_TOP_APPROACH_GEOMETRY_ONLY"
    assert r["physical_certification"] == "NOT_CERTIFIED"
    assert r["manual_insertion"] == "NOT_TESTED"
    assert r["stability"] == "NOT_TESTED"


def test_b_obstacle_beyond_060j_30_plates_is_not_missed():
    moving = brick("moving", z=3)
    overhead = brick("overhead", z=43)
    old = check_vertical_insertion(moving, [overhead], rise_plates=30)
    new = check_vertical_access_from_above(moving, [overhead])
    assert old["verdict"] == "GEOMETRY_CLEAR_ONLY"
    assert new["initial_position"][2] == 47
    assert new["rise_plates"] == 44
    assert new["verdict"] == "BLOCKED"
    assert new["blockers"] == ["overhead"]


def test_c_lower_roof_of_installed_brick_still_blocks_complete_descent():
    moving = brick("moving", z=3)
    blocked = check_vertical_access_from_above(moving, [brick("overhead", z=12)])
    assert blocked["verdict"] == "BLOCKED"
    assert blocked["blockers"] == ["overhead"]
    assert blocked["access_from_outside"] == "NOT_PROVEN"


def test_d_final_support_face_contact_is_not_solid_collision():
    moving = brick("upper", z=3)
    base = brick("lower", z=0, kind="BRICK_1X8")
    r = check_vertical_access_from_above(moving, [base])
    assert r["verdict"] == "GEOMETRY_CLEAR_ONLY"
    assert r["final_support_contacts"] == ["lower"]
    assert r["blockers"] == []
    assert r["known_installed_max_top_z"] == 3
    assert r["initial_position"] == [0, 0, 4]


def test_e_near_unknown_above_known_envelope_stays_unknown():
    moving = brick("moving", z=3)
    # Its bottom lies ABOVE the derived known-only source; 060J's finite
    # sweep would miss it. 060L must not invent the sloped solid's top.
    other = unknown(z=100)
    r = check_vertical_access_from_above(moving, [other])
    assert r["known_installed_max_top_z"] is None
    assert r["initial_position"][2] == 4
    assert r["verdict"] == "UNKNOWN"
    assert r["unknown_geometry"] == ["unverified"]
    assert r["unverified_upper_corridor_ids"] == ["unverified"]
    assert r["access_from_outside"] == "NOT_PROVEN"


def test_f_distant_unknown_not_automatic_blocker():
    r = check_vertical_access_from_above(
        brick("moving", z=3),
        [unknown(x=200, y=200, z=100)],
    )
    assert r["verdict"] == "GEOMETRY_CLEAR_ONLY"
    assert r["unknown_geometry"] == []


def test_g_same_step_order_cannot_be_optimistically_chosen():
    moving = brick("moving", z=3)
    peer = brick("unordered-peer", z=43)
    r = check_vertical_access_from_above(moving, [], unordered_peers=[peer])
    assert r["verdict"] == "UNKNOWN"
    assert r["ambiguous_same_step"] == ["unordered-peer"]
    assert r["known_same_step_max_top_z"] == 46
    assert r["initial_position"][2] == 47
    assert r["installed_ids"] == []
    assert r["unordered_same_step_ids"] == ["unordered-peer"]


def test_h_future_notice_piece_excluded_from_current_obstacles():
    class Model:
        parts = [brick("foundation"), brick("target", z=3), brick("future", z=42)]
    class Step:
        def __init__(self, seq, ids):
            self.sequence = seq
            self.step_id = f"step-{seq:04d}"
            self.placement_ids = ids
    class Notice:
        steps = [Step(1, ["foundation"]), Step(2, ["target"]), Step(3, ["future"])]
    result = audit_notice_vertical_access_from_above(
        Model(), Notice(), ["target"]
    )["target"]
    assert result["installed_ids"] == ["foundation"]
    assert result["verdict"] == "GEOMETRY_CLEAR_ONLY"
    assert result["initial_position"] == [0, 0, 4]
    assert "future" not in result["installed_ids"]


@pytest.mark.parametrize("margin", [0, -1, True, 0.5])
def test_margin_must_be_strictly_positive_integer(margin):
    with pytest.raises(ValueError, match="CLEARANCE_PLATES_MUST_BE_POSITIVE_INTEGER"):
        check_vertical_access_from_above(brick("moving"), [], clearance_plates=margin)


def test_unsupported_mobile_cannot_be_declared_clear():
    r = check_vertical_access_from_above(unknown("sloped-moving"), [])
    assert r["verdict"] == "UNKNOWN"
    assert r["origin_definition"] == "NOT_ESTABLISHED_UNSUPPORTED_MOVING_GEOMETRY"
    assert r["access_from_outside"] == "UNKNOWN"


def test_i_four_actual_guided004_parts_and_no_060j_regression():
    assert VIEWER.is_file(), "CI must regenerate authentic GUIDED-004"
    raw = json.loads(VIEWER.read_text(encoding="utf-8"))
    model = BrickModel.model_validate(raw["brick_model"])
    notice = AssemblyPlan.model_validate(raw["assembly_plan"])
    assert len(model.parts) == 1890
    by = {p.placement_id: p for p in model.parts}
    poses = (
        ("BRICK_1X8", 16, 43, 0, 1),
        ("BRICK_1X6", 17, 43, 3, 1),
        ("BRICK_1X8", 16, 43, 6, 1),
        ("BRICK_1X6", 17, 43, 9, 1),
    )
    for pid, pose in zip(MODULE, poses):
        p = by[pid]
        assert (p.part_id, p.x_studs, p.y_studs, p.z_plates,
                p.rotation_quarter_turns) == pose

    bounded = audit_notice_vertical_insertion(model, notice, MODULE)
    exterior = audit_notice_vertical_access_from_above(model, notice, MODULE)
    assert [exterior[pid]["step_id"] for pid in MODULE] == list(NOTICE_STEPS)
    assert [exterior[pid]["step_sequence"] for pid in MODULE] == [3, 7, 11, 15]
    assert [len(exterior[pid]["installed_ids"]) for pid in MODULE] == [11, 34, 59, 81]
    assert [exterior[pid]["known_installed_count"] for pid in MODULE] == [11, 34, 59, 81]
    assert [exterior[pid]["known_same_step_count"] for pid in MODULE] == [5] * 4
    assert [exterior[pid]["known_installed_max_top_z"] for pid in MODULE] == [3, 6, 9, 12]
    assert [exterior[pid]["known_same_step_max_top_z"] for pid in MODULE] == [3, 6, 9, 12]
    assert [exterior[pid]["initial_position"][2] for pid in MODULE] == [4, 7, 10, 13]
    assert [exterior[pid]["final_position"][2] for pid in MODULE] == [0, 3, 6, 9]
    assert [exterior[pid]["rise_plates"] for pid in MODULE] == [4] * 4

    for pid in MODULE:
        old, new = bounded[pid], exterior[pid]
        assert old["verdict"] == new["verdict"] == "GEOMETRY_CLEAR_ONLY"
        assert old["rise_plates"] == 30
        assert new["blockers"] == new["unknown_geometry"] == new["ambiguous_same_step"] == []
        assert len(new["unordered_same_step_ids"]) == 5
        assert new["unverified_upper_corridor_ids"] == []
        assert new["origin_above_known_solids"] is True
        assert new["physical_certification"] == "NOT_CERTIFIED"
        assert new["manual_insertion"] == new["stability"] == "NOT_TESTED"
    assert exterior["wall-000012"]["final_support_contacts"] == []
    assert exterior["wall-000034"]["final_support_contacts"] == ["wall-000012"]
    assert exterior["wall-000060"]["final_support_contacts"] == [
        "wall-000033", "wall-000034", "wall-000035",
    ]
    assert exterior["wall-000081"]["final_support_contacts"] == ["wall-000060"]
