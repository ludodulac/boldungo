"""060C: geometry-only evidence is never a substitute for 060B physical support."""
from types import SimpleNamespace

import pytest

from brickhouse.bricks import physical_assembly as pa
from brickhouse.bricks.physical_placement_gate import (
    Placement, GeometricPlacementGate, PhysicalPlacementGate,
    build, build_geometrically, verify_geometrically_connected,
)
from scripts.preflight_boldungo2_brickmodel import check_model_data
from brickhouse.bricks.physical_wall_fixture import opening_wall_brick_model


def test_same_unknown_pair_passes_only_explicit_geometric_path():
    parts = [Placement("PLATE_1X3", 0, 0, 0),
             Placement("BRICK_1X3", 0, 0, 1)]
    geometry = build_geometrically(parts)
    assert isinstance(geometry, GeometricPlacementGate)
    assert geometry.validation_level == "GEOMETRY_ONLY"
    assert geometry.connector_validation == "NOT_CHECKED"
    assert geometry.physical_certification is False
    assert len(geometry.accepted) == 2
    with pytest.raises(ValueError, match="UNKNOWN_CONNECTOR_SUPPORT"):
        build(parts)


def test_strict_valid_still_accepted():
    result = build([
        Placement("BRICK_2X8", 0, 0, 0),
        Placement("BRICK_1X1", 0, 0, 3),
    ])
    assert isinstance(result, PhysicalPlacementGate)
    assert result.validation_level == "CONNECTOR_EVIDENCE_STRICT"
    assert result.connector_validation == "REQUIRED_VALID"
    assert result.physical_certification is False


@pytest.mark.parametrize("bad,error", [
    (Placement("BRICK_1X3", 0, 0, 0), "SOLID_COLLISION"),
    (Placement("BRICK_1X3", 5, 0, 1), "NO_STUD_SUPPORT"),
    (Placement("BRICK_1X3", 0, 0, 2), "NO_STUD_SUPPORT"),
    (Placement("BRICK_1X3", 0, 0, 0, 4), "INVALID_ROTATION"),
    (Placement("BRICK_1X3", 0.5, 0, 0), "OFF_GRID"),
    (Placement("FICTIONAL", 0, 0, 0), "PART_NOT_IN_CANONICAL_CATALOG"),
])
def test_geometry_never_bypasses_catalog_grid_rotation_collision_or_support(bad, error):
    gate = GeometricPlacementGate()
    gate.add(Placement("PLATE_1X3", 0, 0, 0))
    with pytest.raises(ValueError, match=error):
        gate.add(bad)


def test_geometric_connectivity_still_rejects_unbridged_islands():
    with pytest.raises(ValueError, match="DISCONNECTED_ASSEMBLY"):
        build_geometrically([
            Placement("BRICK_1X1", 0, 0, 0),
            Placement("BRICK_1X1", 3, 0, 0),
        ])
    with pytest.raises(ValueError, match="EMPTY_ASSEMBLY"):
        verify_geometrically_connected([])


def test_geometric_notice_order_checked_without_strict_claim(monkeypatch):
    parts = [
        SimpleNamespace(
            placement_id="base", part_id="PLATE_1X3", x_studs=0,
            y_studs=0, z_plates=0, rotation_quarter_turns=0,
            width_studs=1, length_studs=3, height_plates=1,
        ),
        SimpleNamespace(
            placement_id="upper", part_id="BRICK_1X3", x_studs=0,
            y_studs=0, z_plates=1, rotation_quarter_turns=0,
            width_studs=1, length_studs=3, height_plates=3,
        ),
    ]
    model = SimpleNamespace(parts=parts)
    correct = SimpleNamespace(steps=[
        SimpleNamespace(step_id="1", placement_ids=["base"]),
        SimpleNamespace(step_id="2", placement_ids=["upper"]),
    ])
    monkeypatch.setattr(pa, "generate_assembly_plan", lambda _: correct)
    assert pa.generate_geometrically_screened_assembly_plan(model) is correct
    with pytest.raises(ValueError, match="PHYSICAL_GATE_FAIL:upper:UNKNOWN_CONNECTOR_SUPPORT"):
        pa.generate_physically_screened_assembly_plan(model)

    wrong = SimpleNamespace(steps=[
        SimpleNamespace(step_id="1", placement_ids=["upper"]),
        SimpleNamespace(step_id="2", placement_ids=["base"]),
    ])
    monkeypatch.setattr(pa, "generate_assembly_plan", lambda _: wrong)
    with pytest.raises(ValueError, match="UNBUILDABLE_NOTICE_STEP"):
        pa.generate_geometrically_screened_assembly_plan(model)


def test_preflight_reports_uncertified_geometry_not_connector_proof():
    result = check_model_data(opening_wall_brick_model().model_dump(mode="json"))
    assert result["status"] == "ORTHOGONAL_PREFLIGHT_PASS"
    assert result["validation_level"] == "GEOMETRY_ONLY"
    assert result["connector_validation"] == "NOT_CHECKED"
    assert result["physical_evidence"] == "NOT_CERTIFIED"
    assert result["physical_certification"] is False
    assert result["stability"] == "NOT_TESTED"
    assert result["insertion"] == "NOT_TESTED"
