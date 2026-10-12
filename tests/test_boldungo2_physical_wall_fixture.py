"""Exercise actual Pydantic BrickModel and notice generation end to end."""
from brickhouse.bricks.physical_wall_fixture import (
    opening_wall_brick_model, opening_wall_screened_notice
)

def test_wall_fixture_parses_as_real_brick_model():
    model = opening_wall_brick_model()
    assert model.width_studs == 12
    assert model.depth_studs == 2
    assert model.height_plates == 15
    assert len(model.parts) == 12
    assert all(p.component == "wall" for p in model.parts)

def test_wall_fixture_generates_physically_screened_notice():
    model, plan = opening_wall_screened_notice()
    ids = [pid for step in plan.steps for pid in step.placement_ids]
    assert len(ids) == 12
    assert set(ids) == {p.placement_id for p in model.parts}
    assert plan.total_parts == 12
    assert plan.total_steps > 0
