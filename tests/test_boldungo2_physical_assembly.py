"""The notice gate must reject invalid geometry AND an impossible step order."""
from types import SimpleNamespace
import pytest
from brickhouse.bricks import physical_assembly as pa

def part(pid, x, z):
    return SimpleNamespace(
        placement_id=pid, part_id="BRICK_2X4", x_studs=x,
        y_studs=0, z_plates=z, rotation_quarter_turns=0,
        width_studs=2, length_studs=4, height_plates=3,
    )

def model(*parts):
    return SimpleNamespace(parts=list(parts))

def plan(*groups):
    return SimpleNamespace(steps=[
        SimpleNamespace(step_id=f"step-{i}", placement_ids=list(group))
        for i, group in enumerate(groups, 1)
    ])

def test_valid_spatial_model_with_wrong_notice_order_is_rejected(monkeypatch):
    monkeypatch.setattr(pa, "generate_assembly_plan", lambda m: plan(["upper"], ["base"]))
    with pytest.raises(ValueError, match="UNBUILDABLE_NOTICE_STEP"):
        pa.generate_physically_screened_assembly_plan(
            model(part("base", 0, 0), part("upper", 0, 3))
        )

def test_valid_spatial_model_with_correct_notice_order_passes(monkeypatch):
    expected = plan(["base"], ["upper"])
    monkeypatch.setattr(pa, "generate_assembly_plan", lambda m: expected)
    assert pa.generate_physically_screened_assembly_plan(
        model(part("base", 0, 0), part("upper", 0, 3))
    ) is expected

def test_fake_part_rejected_before_notice(monkeypatch):
    monkeypatch.setattr(pa, "generate_assembly_plan",
                        lambda m: pytest.fail("notice generated before validation"))
    fake = part("fake", 0, 0)
    fake.part_id = "BRICK_SLOPED_4X36"
    with pytest.raises(ValueError, match="PHYSICAL_GATE_FAIL"):
        pa.generate_physically_screened_assembly_plan(model(fake))

def test_mismatched_dimensions_rejected_before_notice(monkeypatch):
    monkeypatch.setattr(pa, "generate_assembly_plan",
                        lambda m: pytest.fail("notice generated before validation"))
    invalid = part("invalid", 0, 0)
    invalid.length_studs = 2.5
    with pytest.raises(ValueError, match="NONCANONICAL_DIMENSIONS"):
        pa.generate_physically_screened_assembly_plan(model(invalid))

def test_disconnected_ground_islands_rejected_before_notice(monkeypatch):
    monkeypatch.setattr(pa, "generate_assembly_plan",
                        lambda m: pytest.fail("notice generated for disconnected model"))
    with pytest.raises(ValueError, match="DISCONNECTED_ASSEMBLY"):
        pa.generate_physically_screened_assembly_plan(
            model(part("island-a", 0, 0), part("island-b", 8, 0))
        )

def test_notice_missing_piece_is_rejected(monkeypatch):
    monkeypatch.setattr(pa, "generate_assembly_plan", lambda m: plan(["base"]))
    with pytest.raises(ValueError, match="INCOMPLETE_PHYSICAL_NOTICE"):
        pa.generate_physically_screened_assembly_plan(
            model(part("base", 0, 0), part("upper", 0, 3))
        )
