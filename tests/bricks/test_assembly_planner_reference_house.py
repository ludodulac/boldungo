from pathlib import Path

from brickhouse.bricks.assembly_planner import audit_supported_non_roof_plan, plan_supported_non_roof_parts, unresolved_placements, validate_planner_result, planner_metrics, evaluate_planner_quality, group_planner_steps, build_autonomous_instruction_steps
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


def test_reference_house_planner_order_respects_direct_support_dependencies():
    bundle = run_m0_pipeline(REFERENCE_HOUSE, front_width_studs=48)
    result = plan_supported_non_roof_parts(bundle.brick_model)
    sequence = {step.placement_id: step.sequence for step in result.steps}
    from brickhouse.bricks.assembly_planner import direct_support_graph

    for placement_id, support_ids in direct_support_graph(bundle.brick_model).items():
        if placement_id not in sequence:
            continue
        for support_id in support_ids:
            assert support_id in sequence
            assert sequence[support_id] < sequence[placement_id]


def test_reference_house_planner_replays_without_contract_violations():
    bundle = run_m0_pipeline(REFERENCE_HOUSE, front_width_studs=48)
    result = plan_supported_non_roof_parts(bundle.brick_model)
    assert validate_planner_result(bundle.brick_model, result) == ()


def test_reference_house_planner_has_measurable_human_continuity():
    bundle = run_m0_pipeline(REFERENCE_HOUSE, front_width_studs=48)
    result = plan_supported_non_roof_parts(bundle.brick_model)
    metrics = planner_metrics(bundle.brick_model, result)
    assert metrics.step_count == 691
    assert metrics.spatial_travel >= 0
    assert metrics.facade_switches >= 0
    assert metrics.max_spatial_jump >= 0


def test_reference_house_quality_report_is_valid_and_complete_for_current_scope():
    bundle = run_m0_pipeline(REFERENCE_HOUSE, front_width_studs=48)
    result = plan_supported_non_roof_parts(bundle.brick_model)
    report = evaluate_planner_quality(bundle.brick_model, result)
    assert report.valid is True
    assert report.issues == ()
    assert report.unresolved_count == 0
    assert report.metrics.step_count == 691


def test_reference_house_grouped_notice_preserves_all_autonomous_placements():
    bundle = run_m0_pipeline(REFERENCE_HOUSE, front_width_studs=48)
    result = plan_supported_non_roof_parts(bundle.brick_model)
    groups = group_planner_steps(bundle.brick_model, result, max_parts=8)
    flattened = [pid for group in groups for pid in group.placement_ids]
    assert flattened == [step.placement_id for step in result.steps]
    assert len(flattened) == 691
    assert groups
    assert all(1 <= len(group.placement_ids) <= 8 for group in groups)


def test_reference_house_autonomous_instruction_projection_is_lossless():
    bundle = run_m0_pipeline(REFERENCE_HOUSE, front_width_studs=48)
    result = plan_supported_non_roof_parts(bundle.brick_model)
    instructions = build_autonomous_instruction_steps(bundle.brick_model, result, max_parts=8)
    flattened = [pid for step in instructions for pid in step.placement_ids]
    assert flattened == [step.placement_id for step in result.steps]
    assert len(flattened) == 691
    assert all(sum(count for _, count in step.part_counts) == len(step.placement_ids) for step in instructions)
