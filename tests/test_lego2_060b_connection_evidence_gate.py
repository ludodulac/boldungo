"""060B: physical support must inherit the connector validator's evidence state."""
from types import SimpleNamespace

import pytest

from brickhouse.bricks.brick_model import BrickModelPart
from brickhouse.bricks.catalog import standard_orthogonal_definitions
from brickhouse.bricks.connectors import validate_connection
from brickhouse.bricks.physical_placement_gate import (
    Placement, PhysicalPlacementGate, build, verify_connected,
)
from brickhouse.bricks import physical_assembly as pa


def connector_part(pid, part_id, x=0, y=0, z=0):
    definition = standard_orthogonal_definitions()[part_id]
    dimensions = (
        dict(width_studs=definition.width_studs, length_studs=definition.length_studs,
             height_plates=definition.height_plates)
        if part_id.startswith("PLATE_") else {}
    )
    return BrickModelPart(
        placement_id=pid, part_id=part_id, category=definition.category,
        component="roof_support", x_studs=x, y_studs=y, z_plates=z,
        rotation_quarter_turns=0, **dimensions,
    )


def test_unknown_plate_1x3_under_brick_1x3_is_not_support():
    result = validate_connection(
        connector_part("base", "PLATE_1X3"),
        connector_part("upper", "BRICK_1X3", z=1),
    )
    assert result.status == "UNKNOWN"
    gate = PhysicalPlacementGate()
    gate.add(Placement("PLATE_1X3", 0, 0, 0))
    with pytest.raises(ValueError, match="UNKNOWN_CONNECTOR_SUPPORT:underside-interface-not-documented"):
        gate.add(Placement("BRICK_1X3", 0, 0, 1))
    assert len(gate.accepted) == 1


def test_documented_valid_contact_is_accepted():
    result = validate_connection(
        connector_part("base", "BRICK_2X8"),
        connector_part("upper", "BRICK_1X1", z=3),
    )
    assert result.status == "VALID"
    gate = build([
        Placement("BRICK_2X8", 0, 0, 0),
        Placement("BRICK_1X1", 0, 0, 3),
    ])
    assert len(gate.accepted) == 2


@pytest.mark.parametrize("upper, reason", [
    (Placement("BRICK_1X1", 0, 0, 2), "SOLID_COLLISION"),
    (Placement("BRICK_1X1", 0, 0, 4), "NO_STUD_SUPPORT"),
    (Placement("BRICK_1X1", 3, 0, 3), "NO_STUD_SUPPORT"),
])
def test_invalid_collision_or_missing_plane_stays_rejected(upper, reason):
    result = validate_connection(
        connector_part("base", "BRICK_2X8"),
        connector_part("upper", upper.part_id, x=upper.x, z=upper.z),
    )
    assert result.status == "INVALID"
    gate = PhysicalPlacementGate()
    gate.add(Placement("BRICK_2X8", 0, 0, 0))
    with pytest.raises(ValueError, match=reason):
        gate.add(upper)


def test_unknown_edge_cannot_merge_two_connected_components():
    gate = PhysicalPlacementGate()
    gate.add(Placement("BRICK_2X8", 0, 0, 0))
    gate.add(Placement("BRICK_1X3", 2, 0, 0))
    # VALID on left support, UNKNOWN on right: placement is acceptable,
    # but the unknown edge must not masquerade as a connected support.
    gate.add(Placement("BRICK_2X8", 1, 0, 3))
    with pytest.raises(ValueError, match="DISCONNECTED_ASSEMBLY"):
        verify_connected(gate.accepted)


@pytest.mark.parametrize("placement, reason", [
    (Placement("BRICK_1X1", 0.5, 0, 0), "OFF_GRID"),
    (Placement("BRICK_1X1", 0, 0, 0, rotation=4), "INVALID_ROTATION"),
    (Placement("BRICK_MADE_UP", 0, 0, 0), "PART_NOT_IN_CANONICAL_CATALOG"),
    (Placement("BRICK_1X1", 0, 0, -1), "BELOW_GROUND"),
])
def test_existing_grid_rotation_catalog_checks_remain(placement, reason):
    with pytest.raises(ValueError, match=reason):
        PhysicalPlacementGate().add(placement)


def notice_part(pid, part_id, z, w, l, h):
    return SimpleNamespace(
        placement_id=pid, part_id=part_id,
        x_studs=0, y_studs=0, z_plates=z, rotation_quarter_turns=0,
        width_studs=w, length_studs=l, height_plates=h,
    )


def test_physical_assembly_caller_accepts_documented_valid(monkeypatch):
    base = notice_part("base", "BRICK_2X8", 0, 2, 8, 3)
    upper = notice_part("upper", "BRICK_1X1", 3, 1, 1, 3)
    plan = SimpleNamespace(steps=[
        SimpleNamespace(step_id="step-1", placement_ids=["base"]),
        SimpleNamespace(step_id="step-2", placement_ids=["upper"]),
    ])
    monkeypatch.setattr(pa, "generate_assembly_plan", lambda _: plan)
    result = pa.generate_physically_screened_assembly_plan(
        SimpleNamespace(parts=[base, upper]),
    )
    assert result is plan


def test_physical_assembly_caller_stops_on_unknown_before_notice(monkeypatch):
    base = notice_part("base", "PLATE_1X3", 0, 1, 3, 1)
    upper = notice_part("upper", "BRICK_1X3", 1, 1, 3, 3)
    monkeypatch.setattr(
        pa, "generate_assembly_plan",
        lambda _: pytest.fail("unknown connector passed physical preflight"),
    )
    with pytest.raises(ValueError, match="PHYSICAL_GATE_FAIL:upper:UNKNOWN_CONNECTOR_SUPPORT"):
        pa.generate_physically_screened_assembly_plan(
            SimpleNamespace(parts=[base, upper]),
        )
