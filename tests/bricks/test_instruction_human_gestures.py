import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from brickhouse.bricks.assembly import AssemblyPlan, AssemblyStep
from brickhouse.bricks.instructions import (
    BoundedInstructionSplitPolicy,
    DirectInstructionPolicy,
    InstructionPlan,
    InstructionStep,
    generate_instruction_plan,
    validate_instruction_plan_against_assembly,
)


def _assembly_step(step_id: str, sequence: int, ids: list[str]) -> AssemblyStep:
    return AssemblyStep(
        step_id=step_id,
        sequence=sequence,
        component="wall",
        z_plates=0,
        title=step_id,
        placement_ids=ids,
        phase="Structure",
        bag=1,
        instruction_kind="placement",
        focus="normal",
        view="front",
    )


def _assembly(*groups: list[str]) -> AssemblyPlan:
    steps = [_assembly_step(f"step-{i:04d}", i, ids) for i, ids in enumerate(groups, start=1)]
    return AssemblyPlan(
        building_id="test",
        volume_id="main",
        total_steps=len(steps),
        total_parts=sum(len(ids) for ids in groups),
        total_bags=1,
        steps=steps,
    )


def _instruction(source: str, sequence: int, ids: list[str], *, reason="direct_projection") -> InstructionStep:
    return InstructionStep(
        step_id=f"instruction-{sequence:04d}",
        sequence=sequence,
        title="gesture",
        source_assembly_step_id=source,
        added_placement_ids=ids,
        phase="Structure",
        instruction_kind="placement",
        focus="normal",
        view="front",
        boundary_reason=reason,
    )


def test_direct_projection_preserves_existing_semantics():
    assembly = _assembly(["a", "b"], ["c"])
    plan = generate_instruction_plan(assembly, policy=DirectInstructionPolicy())

    assert plan.schema_version == "0.2"
    assert plan.total_steps == 2
    assert [step.step_id for step in plan.steps] == ["step-0001", "step-0002"]
    assert [step.source_assembly_step_id for step in plan.steps] == ["step-0001", "step-0002"]
    assert [step.added_placement_ids for step in plan.steps] == [["a", "b"], ["c"]]
    assert all(step.boundary_reason == "direct_projection" for step in plan.steps)
    assert plan.steps[0].placement_ids == ["a", "b"]  # in-memory 0.1 compatibility


def test_bounded_policy_can_split_one_assembly_step_into_many_human_gestures():
    assembly = _assembly(["a", "b", "c", "d"])
    plan = generate_instruction_plan(
        assembly,
        policy=BoundedInstructionSplitPolicy(max_added_placements=3),
    )

    assert plan.total_steps == 2
    assert [step.added_placement_ids for step in plan.steps] == [["a", "b"], ["c", "d"]]
    assert [step.source_assembly_step_id for step in plan.steps] == ["step-0001", "step-0001"]
    assert all(step.boundary_reason == "pedagogical_split" for step in plan.steps)


def test_split_conserves_exact_order_per_source_and_globally():
    assembly = _assembly(["a", "b", "c", "d"], ["e", "f"])
    plan = generate_instruction_plan(assembly, policy=BoundedInstructionSplitPolicy(3))

    assert [pid for step in plan.steps for pid in step.added_placement_ids] == ["a", "b", "c", "d", "e", "f"]
    validate_instruction_plan_against_assembly(plan, assembly)


def test_instruction_plan_rejects_global_duplicate():
    with pytest.raises(ValidationError, match="placement ids must be unique"):
        InstructionPlan(
            building_id="test", volume_id="main", total_steps=2, total_parts=2,
            steps=[_instruction("step-0001", 1, ["a"]), _instruction("step-0001", 2, ["a"])],
        )


def test_unknown_brickmodel_placement_is_rejected():
    assembly = _assembly(["a", "unknown"])
    model = SimpleNamespace(parts=[SimpleNamespace(placement_id="a"), SimpleNamespace(placement_id="b")])

    with pytest.raises(ValueError, match="unknown=.*unknown.*missing=.*b"):
        generate_instruction_plan(assembly, model)


def test_omission_against_source_assembly_step_is_rejected():
    assembly = _assembly(["a", "b"])
    plan = InstructionPlan(
        building_id="test", volume_id="main", total_steps=1, total_parts=1,
        steps=[_instruction("step-0001", 1, ["a"])],
    )
    with pytest.raises(ValueError, match="exact ordered placements"):
        validate_instruction_plan_against_assembly(plan, assembly)


def test_reordering_against_source_assembly_step_is_rejected():
    assembly = _assembly(["a", "b"])
    plan = InstructionPlan(
        building_id="test", volume_id="main", total_steps=1, total_parts=2,
        steps=[_instruction("step-0001", 1, ["b", "a"])],
    )
    with pytest.raises(ValueError, match="exact ordered placements"):
        validate_instruction_plan_against_assembly(plan, assembly)


def test_before_added_after_are_derived_without_serialized_state():
    plan = generate_instruction_plan(
        _assembly(["a", "b", "c", "d"]),
        policy=BoundedInstructionSplitPolicy(3),
    )
    assert plan.before_placement_ids(1) == []
    assert plan.steps[0].added_placement_ids == ["a", "b"]
    assert plan.after_placement_ids(1) == ["a", "b"]
    assert plan.before_placement_ids(2) == ["a", "b"]
    assert plan.steps[1].added_placement_ids == ["c", "d"]
    assert plan.after_placement_ids(2) == ["a", "b", "c", "d"]
    dumped = plan.model_dump()
    assert "before_placement_ids" not in dumped["steps"][0]
    assert "after_placement_ids" not in dumped["steps"][0]


def test_final_state_is_identical_to_assembly_plan():
    assembly = _assembly(["a", "b", "c", "d"], ["e", "f", "g"])
    plan = generate_instruction_plan(assembly, policy=BoundedInstructionSplitPolicy(3))
    expected = [pid for step in assembly.steps for pid in step.placement_ids]
    assert plan.after_placement_ids(plan.total_steps) == expected


def test_generation_is_deterministic():
    assembly = _assembly(["a", "b", "c", "d"], ["e", "f", "g"])
    policy = BoundedInstructionSplitPolicy(3)
    first = generate_instruction_plan(assembly, policy=policy).model_dump()
    second = generate_instruction_plan(assembly, policy=policy).model_dump()
    assert first == second


def test_real_notice_steps_1_8_fixture_remains_lossless_without_id_hardcoding():
    fixture = Path(__file__).parents[1] / "fixtures" / "notice_reference_steps_1_8.json"
    assembly = AssemblyPlan.model_validate(json.loads(fixture.read_text()))

    direct = generate_instruction_plan(assembly)
    bounded = generate_instruction_plan(assembly, policy=BoundedInstructionSplitPolicy(3))

    assert direct.total_steps == assembly.total_steps == 8
    assert bounded.total_steps == 10
    assert bounded.total_parts == assembly.total_parts == 22
    assert [pid for step in bounded.steps for pid in step.added_placement_ids] == [
        pid for step in assembly.steps for pid in step.placement_ids
    ]
    split_sources = [
        source.step_id
        for source in assembly.steps
        if sum(step.source_assembly_step_id == source.step_id for step in bounded.steps) > 1
    ]
    assert split_sources == [assembly.steps[0].step_id, assembly.steps[4].step_id]
