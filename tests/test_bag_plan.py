from brickhouse.bricks.assembly import AssemblyPlan, AssemblyStep, generate_assembly_plan
from brickhouse.bricks.bags import MAX_PHYSICAL_BAG_PARTS, generate_bag_plan
from brickhouse.bricks.bom import generate_bom
from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from pathlib import Path

import json

from brickhouse.bricks.export import create_export_bundle


def _model() -> BrickModel:
    return BrickModel(
        building_id="bag-test",
        volume_id="v1",
        width_studs=8,
        depth_studs=6,
        height_plates=12,
        parts=[
            BrickModelPart(
                placement_id="wall-front-1",
                part_id="BRICK_1X2",
                category="brick",
                component="wall",
                x_studs=0,
                y_studs=0,
                z_plates=0,
                rotation_quarter_turns=0,
                facade="front",
            ),
            BrickModelPart(
                placement_id="frame-1",
                part_id="WINDOW_1X2X2_60592",
                category="window_frame",
                component="facade_detail",
                x_studs=2,
                y_studs=0,
                z_plates=3,
                rotation_quarter_turns=1,
                facade="front",
            ),
            BrickModelPart(
                placement_id="pane-1",
                part_id="GLASS_FOR_WINDOW_1X2X2_60601",
                category="window_pane",
                component="facade_detail",
                x_studs=2,
                y_studs=0,
                z_plates=3,
                rotation_quarter_turns=1,
                facade="front",
            ),
            BrickModelPart(
                placement_id="detail-1",
                part_id="BRICK_1X1",
                category="facade_detail",
                component="facade_detail",
                x_studs=4,
                y_studs=0,
                z_plates=6,
                rotation_quarter_turns=0,
                facade="front",
            ),
        ],
    )


def _assembly(step_sizes_by_logical_bag: list[list[int]]) -> AssemblyPlan:
    steps = []
    placement_number = 1
    sequence = 1

    for logical_bag, step_sizes in enumerate(step_sizes_by_logical_bag, start=1):
        for step_size in step_sizes:
            placement_ids = [
                f"placement-{placement_number + offset:04d}"
                for offset in range(step_size)
            ]
            placement_number += step_size
            steps.append(AssemblyStep(
                step_id=f"step-{sequence:04d}",
                sequence=sequence,
                component="wall",
                z_plates=sequence,
                title=f"Logical bag {logical_bag} step {sequence}",
                placement_ids=placement_ids,
                phase=f"Phase {logical_bag}",
                bag=logical_bag,
            ))
            sequence += 1

    return AssemblyPlan(
        building_id="physical-bag-test",
        volume_id="v1",
        total_steps=len(steps),
        total_parts=placement_number - 1,
        total_bags=len(step_sizes_by_logical_bag),
        steps=steps,
    )


def _bag_sizes(bag_plan) -> list[int]:
    return [len(bag.placement_ids) for bag in bag_plan.bags]


def test_bag_plan_preserves_current_assembly_grouping_and_order() -> None:
    assembly = generate_assembly_plan(_model())
    bag_plan = generate_bag_plan(assembly)

    assert bag_plan.building_id == assembly.building_id
    assert bag_plan.volume_id == assembly.volume_id
    assert bag_plan.total_bags == assembly.total_bags
    assert bag_plan.total_parts == assembly.total_parts
    assert [bag.bag_number for bag in bag_plan.bags] == list(range(1, bag_plan.total_bags + 1))

    assert [step_id for bag in bag_plan.bags for step_id in bag.assembly_step_ids] == [
        step.step_id for step in assembly.steps
    ]
    assert [placement_id for bag in bag_plan.bags for placement_id in bag.placement_ids] == [
        placement_id for step in assembly.steps for placement_id in step.placement_ids
    ]

    steps_by_id = {step.step_id: step for step in assembly.steps}
    for bag in bag_plan.bags:
        underlying = [steps_by_id[step_id] for step_id in bag.assembly_step_ids]
        assert bag.phases == list(dict.fromkeys(step.phase for step in underlying))


def test_export_bundle_adds_bag_plan_without_removing_existing_bag_field() -> None:
    model = _model()
    assembly = generate_assembly_plan(model)
    bundle = create_export_bundle(model, generate_bom(model), assembly)

    assert bundle.assembly_plan == assembly
    assert bundle.instruction_plan is not None
    assert all(not hasattr(step, "bag") for step in bundle.instruction_plan.steps)
    assert bundle.bag_plan is not None
    assert bundle.bag_plan.total_bags == assembly.total_bags
    assert bundle.bag_plan.total_parts == len(model.parts)
    assert [step_id for bag in bundle.bag_plan.bags for step_id in bag.assembly_step_ids] == [
        step.step_id for step in assembly.steps
    ]


def test_logical_bag_over_200_is_split_into_contiguous_physical_bags() -> None:
    assembly = _assembly([[100, 100, 50]])

    bag_plan = generate_bag_plan(assembly)

    assert MAX_PHYSICAL_BAG_PARTS == 200
    assert _bag_sizes(bag_plan) == [200, 50]
    assert [bag.assembly_step_ids for bag in bag_plan.bags] == [
        ["step-0001", "step-0002"],
        ["step-0003"],
    ]


def test_assembly_step_is_never_split_between_physical_bags() -> None:
    assembly = _assembly([[120, 90]])

    bag_plan = generate_bag_plan(assembly)

    assert _bag_sizes(bag_plan) == [120, 90]
    assert [bag.assembly_step_ids for bag in bag_plan.bags] == [
        ["step-0001"],
        ["step-0002"],
    ]


def test_logical_bags_are_never_merged_even_when_capacity_remains() -> None:
    assembly = _assembly([[150], [40]])

    bag_plan = generate_bag_plan(assembly)

    assert _bag_sizes(bag_plan) == [150, 40]
    assert [bag.phases for bag in bag_plan.bags] == [["Phase 1"], ["Phase 2"]]
    assert [bag.assembly_step_ids for bag in bag_plan.bags] == [
        ["step-0001"],
        ["step-0002"],
    ]


def test_physical_split_preserves_all_steps_placements_and_total_parts() -> None:
    assembly = _assembly([[80, 80, 80], [50, 60]])

    bag_plan = generate_bag_plan(assembly)

    assert _bag_sizes(bag_plan) == [160, 80, 110]
    assert bag_plan.total_parts == assembly.total_parts
    assert [bag.bag_number for bag in bag_plan.bags] == [1, 2, 3]
    assert [step_id for bag in bag_plan.bags for step_id in bag.assembly_step_ids] == [
        step.step_id for step in assembly.steps
    ]
    assert [placement_id for bag in bag_plan.bags for placement_id in bag.placement_ids] == [
        placement_id
        for step in assembly.steps
        for placement_id in step.placement_ids
    ]


def test_single_step_over_200_stays_intact_in_one_oversize_bag() -> None:
    assembly = _assembly([[201, 10]])

    bag_plan = generate_bag_plan(assembly)

    assert _bag_sizes(bag_plan) == [201, 10]
    assert bag_plan.bags[0].assembly_step_ids == ["step-0001"]
    assert len(bag_plan.bags[0].placement_ids) == 201


def test_real_baseline57_export_splits_into_expected_physical_bags() -> None:
    export_path = (
        Path(__file__).resolve().parents[1]
        / "frontend"
        / "module-001-baseline57-export.json"
    )
    payload = json.loads(export_path.read_text(encoding="utf-8"))
    model = BrickModel.model_validate(payload["brick_model"])

    assembly = generate_assembly_plan(model)
    bag_plan = generate_bag_plan(assembly)

    assert assembly.total_parts == 1922
    assert assembly.total_steps == 236
    assert bag_plan.total_parts == 1922
    assert bag_plan.total_bags == 10
    assert _bag_sizes(bag_plan) == [198, 198, 198, 198, 198, 198, 198, 198, 200, 138]

    assert [step_id for bag in bag_plan.bags for step_id in bag.assembly_step_ids] == [
        step.step_id for step in assembly.steps
    ]
    assert [placement_id for bag in bag_plan.bags for placement_id in bag.placement_ids] == [
        placement_id
        for step in assembly.steps
        for placement_id in step.placement_ids
    ]
