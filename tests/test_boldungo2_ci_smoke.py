"""Dedicated CI smoke test: physical fixture can be screened without certification."""
from brickhouse.bricks.physical_wall_fixture import opening_wall_screened_notice

def test_fixture_screening_smoke():
    model, plan = opening_wall_screened_notice()
    assert plan.total_parts == len(model.parts) == 12
    assert plan.total_steps >= 1
