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
    with pytest.raises(ValueError, match="PHYSICAL_NOTICE_COVERAGE_MISMATCH"):
        pa.generate_physically_screened_assembly_plan(
            model(part("base", 0, 0), part("upper", 0, 3))
        )

def test_notice_unknown_piece_is_rejected_before_replay(monkeypatch):
    monkeypatch.setattr(pa, "generate_assembly_plan", lambda m: plan(["base", "ghost"]))
    with pytest.raises(ValueError, match="PHYSICAL_NOTICE_COVERAGE_MISMATCH"):
        pa.generate_physically_screened_assembly_plan(model(part("base", 0, 0)))

def test_notice_duplicate_piece_is_rejected_before_replay(monkeypatch):
    monkeypatch.setattr(pa, "generate_assembly_plan", lambda m: plan(["base"], ["base"]))
    with pytest.raises(ValueError, match="DUPLICATE_PHYSICAL_NOTICE_PART"):
        pa.generate_physically_screened_assembly_plan(model(part("base", 0, 0)))


def test_notice_replay_rejects_free_landing_with_blocked_vertical_path(monkeypatch):
    # Final geometry is connected and collision-free; only the notice order
    # makes a straight-down insertion impossible under the installed roof.
    base_left = part("base-left", 0, 0)
    base_right = part("base-right", 2, 0)
    lower_left = part("lower-left", 0, 3)
    roof = part("roof", 1, 6)
    target = part("target", 2, 3)
    items = model(base_left, base_right, lower_left, roof, target)
    bad = plan(["base-left", "base-right"], ["lower-left"], ["roof"], ["target"])
    monkeypatch.setattr(pa, "generate_assembly_plan", lambda m: bad)
    with pytest.raises(ValueError, match="UNBUILDABLE_NOTICE_STEP:.*VERTICAL_INSERTION_BLOCKED"):
        pa.generate_physically_screened_assembly_plan(items)


def test_notice_replay_accepts_vertical_path_before_roof(monkeypatch):
    items = model(part("base-left", 0, 0), part("base-right", 2, 0),
                  part("lower-left", 0, 3), part("roof", 1, 6),
                  part("target", 2, 3))
    good = plan(["base-left", "base-right"], ["lower-left", "target"], ["roof"])
    monkeypatch.setattr(pa, "generate_assembly_plan", lambda m: good)
    assert pa.generate_physically_screened_assembly_plan(items) is good
