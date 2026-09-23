import json
from pathlib import Path

from brickhouse.bricks.assembly_planner import plan_supported_non_roof_parts
from brickhouse.bricks.instructions import generate_autonomous_instruction_plan
from brickhouse.pipeline import run_m0_pipeline

PREVIEW = Path("frontend/notice-autonomous-preview-export.json")
REFERENCE_HOUSE = Path("docs/examples/building-model-simple-house.json")


def _preview():
    return json.loads(PREVIEW.read_text(encoding="utf-8"))


def _expected_steps():
    bundle = run_m0_pipeline(REFERENCE_HOUSE, front_width_studs=48)
    result = plan_supported_non_roof_parts(bundle.brick_model)
    instruction = generate_autonomous_instruction_plan(bundle.brick_model, result, max_parts=8)
    return instruction.steps[:5]


def test_autonomous_preview_is_exact_first_five_instruction_steps():
    preview = _preview()
    expected = _expected_steps()
    actual = preview["instruction_plan"]["steps"]
    assert len(actual) == 5
    assert actual == [step.model_dump(mode="json") for step in expected]
    assert preview["assembly_plan"]["steps"] == actual


def test_autonomous_preview_contains_exactly_referenced_placements_in_order():
    preview = _preview()
    expected = _expected_steps()
    expected_ids = [pid for step in expected for pid in step.placement_ids]
    instruction_ids = [pid for step in preview["instruction_plan"]["steps"] for pid in step["placement_ids"]]
    model_ids = [part["placement_id"] for part in preview["brick_model"]["parts"]]
    assert instruction_ids == expected_ids
    assert set(model_ids) == set(expected_ids)
    assert len(model_ids) == len(expected_ids) == len(set(expected_ids))
    assert preview["instruction_plan"]["total_parts"] == len(expected_ids)
    assert preview["bom"]["total_parts"] == len(model_ids)


def test_autonomous_preview_adapter_is_explicit_and_trivial():
    preview = _preview()
    meta = preview["experimental_notice_preview"]
    assert meta["source"] == "generate_autonomous_instruction_plan"
    assert meta["step_limit"] == 5
    assert meta["adapter"] == "instruction_plan_steps_exposed_as_assembly_plan_for_existing_viewer"
    assert preview["assembly_plan"] == preview["instruction_plan"]
