"""Mission 014: production plan dispatch must not silently bypass its existing strict gate."""
from types import SimpleNamespace

import pytest

from brickhouse import pipeline
from brickhouse.bricks import physical_assembly


def make_part(identity, x, z, part_id="BRICK_2X4", width=2, length=4):
    return SimpleNamespace(
        placement_id=identity, part_id=part_id, x_studs=x,
        y_studs=0, z_plates=z, rotation_quarter_turns=0,
        width_studs=width, length_studs=length, height_plates=3,
    )


def test_generator_rejects_interpenetrating_supported_brick_bodies(monkeypatch):
    model = SimpleNamespace(parts=[
        make_part("base", 0, 0), make_part("colliding", 1, 0),
    ])
    monkeypatch.setattr(
        physical_assembly, "generate_assembly_plan",
        lambda m: pytest.fail("Plan emitted before physical collision rejection"),
    )
    with pytest.raises(ValueError, match="PHYSICAL_GATE_FAIL:colliding:SOLID_COLLISION"):
        pipeline._plan_for_supported_orthogonal_parts(model)


def test_generator_allows_correct_orthogonal_stud_connection(monkeypatch):
    model = SimpleNamespace(parts=[
        make_part("base", 0, 0), make_part("upper", 0, 3, "BRICK_1X2", 1, 2),
    ])
    plan = SimpleNamespace(steps=[
        SimpleNamespace(step_id="step-1", placement_ids=["base"]),
        SimpleNamespace(step_id="step-2", placement_ids=["upper"]),
    ])
    monkeypatch.setattr(physical_assembly, "generate_assembly_plan", lambda m: plan)
    assert pipeline._plan_for_supported_orthogonal_parts(model) is plan


def test_unknown_geometry_not_claimed_as_physically_verified(monkeypatch):
    model = SimpleNamespace(parts=[make_part("visual", 0, 0, part_id="SLOPE_UNVERIFIED")])
    marker = object()
    monkeypatch.setattr(pipeline, "generate_assembly_plan", lambda m: marker)
    assert pipeline._plan_for_supported_orthogonal_parts(model) is marker
    # This is the legacy VISUAL-ONLY path, never a physical-gate certificate.


def test_partial_preview_accepts_separate_valid_ground_groups_without_certification(monkeypatch):
    model = SimpleNamespace(parts=[
        make_part("island-a", 0, 0), make_part("island-b", 8, 0),
    ])
    expected = SimpleNamespace(steps=[])
    monkeypatch.setattr(physical_assembly, "generate_assembly_plan", lambda m: expected)
    assert pipeline._plan_for_supported_orthogonal_parts(
        model, allow_disconnected_preview=True
    ) is expected
    with pytest.raises(ValueError, match="PHYSICAL_GATE_FAIL:DISCONNECTED_ASSEMBLY"):
        pipeline._plan_for_supported_orthogonal_parts(model)


def test_partial_preview_still_refuses_real_solid_overlap(monkeypatch):
    model = SimpleNamespace(parts=[
        make_part("base", 0, 0), make_part("collision", 1, 0),
    ])
    monkeypatch.setattr(physical_assembly, "generate_assembly_plan",
                        lambda m: pytest.fail("Preview plan emitted despite collision"))
    with pytest.raises(ValueError, match="PHYSICAL_GATE_FAIL:collision:SOLID_COLLISION"):
        pipeline._plan_for_supported_orthogonal_parts(model, allow_disconnected_preview=True)
