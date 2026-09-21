from pathlib import Path

from brickhouse.bricks.assembly_planner import audit_supported_non_roof_plan, plan_supported_non_roof_parts, unresolved_placements
from brickhouse.pipeline import run_m0_pipeline

REFERENCE_HOUSE = Path("docs/examples/building-model-simple-house.json")


def test_reference_house_planner_audit_is_deterministic_and_honest():
    bundle = run_m0_pipeline(REFERENCE_HOUSE, front_width_studs=48)
    first = audit_supported_non_roof_plan(bundle.brick_model)
    second = audit_supported_non_roof_plan(bundle.brick_model)

    assert first == second
    assert first.eligible_count > 0
    assert first.planned_count > 0
    assert first.planned_count + first.unresolved_count == first.eligible_count
    assert first.complete_for_scope is (first.unresolved_count == 0)

    # Keep the real-model audit visible in CI so future planner work is driven
    # by actual coverage rather than invented heuristics.
    # Pin the current reference-house coverage. If geometry or planner logic
    # changes, CI must make that change explicit rather than silently degrading.
    assert first.eligible_count == 691
    assert first.planned_count == 691
    assert first.unresolved_count == 0
    assert first.unresolved_by_reason == ()

    unresolved = unresolved_placements(
        bundle.brick_model, plan_supported_non_roof_parts(bundle.brick_model)
    )
    assert unresolved == ()
