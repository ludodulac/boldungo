import json
from pathlib import Path

from brickhouse.bricks.assembly import AssemblyPlan, AssemblyStep
from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.bom import generate_bom
from brickhouse.bricks.export import BrickExportBundle, create_export_bundle, export_bundle_json
from brickhouse.bricks.instruction_spatial import SpatialCoherenceInstructionPolicy
from brickhouse.bricks.instructions import (
    BoundedInstructionSplitPolicy,
    DirectInstructionPolicy,
    generate_instruction_plan,
)


def _step(ids: list[str]) -> AssemblyStep:
    return AssemblyStep(
        step_id="synthetic", sequence=1, component="wall", z_plates=0,
        title="synthetic", placement_ids=ids, phase="Structure", bag=1,
        instruction_kind="placement", focus="normal", view="front",
    )


def _part(pid: str, x: int, y: int = 0, part_id: str = "BRICK_1X1", rotation: int = 0) -> BrickModelPart:
    return BrickModelPart(
        placement_id=pid, part_id=part_id, category="brick", component="wall",
        x_studs=x, y_studs=y, z_plates=0, rotation_quarter_turns=rotation,
        facade="front",
    )


def _model(parts: list[BrickModelPart]) -> BrickModel:
    return BrickModel(
        building_id="test", volume_id="main", width_studs=40, depth_studs=20,
        height_plates=3, parts=parts,
    )


def test_compact_group_remains_one_gesture():
    ids = ["a", "b", "c"]
    policy = SpatialCoherenceInstructionPolicy(_model([_part("a", 0), _part("b", 1), _part("c", 2)]))
    assert policy.groups_for(_step(ids)) == [ids]
    diagnostic = policy.diagnose(_step(ids))
    assert diagnostic.consecutive_gaps_studs == (0, 0)
    assert diagnostic.directional_relations == ((1, 0), (1, 0))


def test_exactly_two_distant_placements_split_into_two_gestures():
    ids = ["a", "b"]
    policy = SpatialCoherenceInstructionPolicy(_model([_part("a", 0), _part("b", 3)]))
    diagnostic = policy.diagnose(_step(ids))
    assert diagnostic.consecutive_gaps_studs == (2,)
    assert diagnostic.directional_relations == ((1, 0),)
    assert diagnostic.split_after_indices == (1,)
    assert policy.groups_for(_step(ids)) == [["a"], ["b"]]


def test_two_compact_groups_with_clear_gap_split_without_reordering():
    ids = ["a", "b", "c", "d"]
    policy = SpatialCoherenceInstructionPolicy(_model([
        _part("a", 0), _part("b", 1), _part("c", 5), _part("d", 6),
    ]))
    diagnostic = policy.diagnose(_step(ids))
    assert diagnostic.consecutive_gaps_studs == (0, 3, 0)
    assert diagnostic.split_after_indices == (2,)
    assert policy.groups_for(_step(ids)) == [["a", "b"], ["c", "d"]]


def test_continuous_chain_remains_one_gesture():
    ids = ["a", "b", "c", "d"]
    policy = SpatialCoherenceInstructionPolicy(_model([
        _part("a", 0), _part("b", 1), _part("c", 2), _part("d", 3),
    ]))
    assert policy.groups_for(_step(ids)) == [ids]


def test_spatial_alternation_is_not_reordered_or_clustered():
    ids = ["a", "b", "c", "d"]
    policy = SpatialCoherenceInstructionPolicy(_model([
        _part("a", 0), _part("b", 10), _part("c", 0), _part("d", 10),
    ]))
    diagnostic = policy.diagnose(_step(ids))
    assert diagnostic.consecutive_gaps_studs == (9, 9, 9)
    assert diagnostic.directional_relations == ((1, 0), (-1, 0), (1, 0))
    assert diagnostic.split_after_indices == ()
    assert policy.groups_for(_step(ids)) == [ids]


def test_different_part_sizes_use_rotated_footprints_not_origins_only():
    ids = ["long", "touching", "far"]
    policy = SpatialCoherenceInstructionPolicy(_model([
        _part("long", 0, part_id="BRICK_1X6", rotation=1),
        _part("touching", 6),
        _part("far", 10),
    ]))
    diagnostic = policy.diagnose(_step(ids))
    assert diagnostic.consecutive_gaps_studs == (0, 3)
    assert diagnostic.directional_relations == ((1, 0), (1, 0))
    assert diagnostic.split_after_indices == (2,)


def test_directional_relations_cover_axes_turns_single_and_unknown_geometry():
    ids = ["a", "b", "c", "d"]
    policy = SpatialCoherenceInstructionPolicy(_model([
        _part("a", 0, 0), _part("b", 0, 2), _part("c", 2, 2), _part("d", 2, 0),
    ]))
    diagnostic = policy.diagnose(_step(ids))
    assert diagnostic.directional_relations == ((0, 1), (1, 0), (0, -1))

    single = policy.diagnose(_step(["a"]))
    assert single.directional_relations == ()

    unknown = policy.diagnose(_step(["missing"]))
    assert unknown.directional_relations is None
    assert unknown.split_after_indices == ()


def test_geometry_change_can_change_split_but_id_change_cannot():
    step_a = _step(["a", "b", "c", "d"])
    compact_then_far = _model([_part("a", 0), _part("b", 1), _part("c", 5), _part("d", 6)])
    assert SpatialCoherenceInstructionPolicy(compact_then_far).groups_for(step_a) == [["a", "b"], ["c", "d"]]

    renamed_step = _step(["w", "x", "y", "z"])
    renamed_model = _model([_part("w", 0), _part("x", 1), _part("y", 5), _part("z", 6)])
    assert [len(group) for group in SpatialCoherenceInstructionPolicy(renamed_model).groups_for(renamed_step)] == [2, 2]

    moved_model = _model([_part("a", 0), _part("b", 1), _part("c", 2), _part("d", 3)])
    assert SpatialCoherenceInstructionPolicy(moved_model).groups_for(step_a) == [["a", "b", "c", "d"]]


def _notice_reference_model() -> BrickModel:
    rows = [
        ("wall-000001", "BRICK_1X6", 1, 1, 0, 1, "front"),
        ("wall-000002", "BRICK_1X1", 7, 1, 0, 0, "front"),
        ("wall-000003", "BRICK_1X6", 10, 1, 0, 1, "front"),
        ("wall-000004", "BRICK_1X1", 16, 1, 0, 0, "front"),
        ("wall-000009", "BRICK_1X8", 16, 2, 0, 0, "right"),
        ("wall-000010", "BRICK_1X3", 16, 10, 0, 0, "right"),
        ("wall-000005", "BRICK_1X8", 9, 13, 0, 1, "rear"),
        ("wall-000006", "BRICK_1X8", 1, 13, 0, 1, "rear"),
        ("wall-000007", "BRICK_1X8", 1, 5, 0, 0, "left"),
        ("wall-000008", "BRICK_1X3", 1, 2, 0, 0, "left"),
        ("wall-000011", "BRICK_1X1", 2, 1, 3, 0, "front"),
        ("wall-000012", "BRICK_1X3", 5, 1, 3, 1, "front"),
        ("wall-000013", "BRICK_1X3", 10, 1, 3, 1, "front"),
        ("wall-000014", "BRICK_1X1", 15, 1, 3, 0, "front"),
        ("wall-000020", "BRICK_1X8", 16, 1, 3, 0, "right"),
        ("wall-000021", "BRICK_1X3", 16, 9, 3, 0, "right"),
        ("wall-000022", "BRICK_1X2", 16, 12, 3, 0, "right"),
        ("wall-000015", "BRICK_1X8", 8, 13, 3, 1, "rear"),
        ("wall-000016", "BRICK_1X6", 2, 13, 3, 1, "rear"),
        ("wall-000017", "BRICK_1X8", 1, 6, 3, 0, "left"),
        ("wall-000018", "BRICK_1X3", 1, 3, 3, 0, "left"),
        ("wall-000019", "BRICK_1X2", 1, 1, 3, 0, "left"),
    ]
    return BrickModel(
        building_id="building-simple-house", volume_id="main", width_studs=16,
        depth_studs=13, height_plates=6,
        parts=[BrickModelPart(
            placement_id=pid, part_id=part_id, category="brick", component="wall",
            x_studs=x, y_studs=y, z_plates=z, rotation_quarter_turns=rotation,
            facade=facade,
        ) for pid, part_id, x, y, z, rotation, facade in rows],
    )


def test_real_notice_steps_1_8_spatial_policy_is_lossless_and_diagnostic():
    fixture = Path(__file__).parents[1] / "fixtures" / "notice_reference_steps_1_8.json"
    assembly = AssemblyPlan.model_validate(json.loads(fixture.read_text()))
    model = _notice_reference_model()
    spatial_policy = SpatialCoherenceInstructionPolicy(model)

    direct = generate_instruction_plan(assembly, model, policy=DirectInstructionPolicy())
    bounded = generate_instruction_plan(assembly, model, policy=BoundedInstructionSplitPolicy(3))
    spatial = generate_instruction_plan(assembly, model, policy=spatial_policy)

    assert (direct.total_steps, bounded.total_steps, spatial.total_steps) == (8, 10, 9)
    assert spatial.total_parts == 22
    assert spatial.after_placement_ids(spatial.total_steps) == [
        pid for source in assembly.steps for pid in source.placement_ids
    ]
    diagnostics = [spatial_policy.diagnose(source) for source in assembly.steps]
    assert [d.consecutive_gaps_studs for d in diagnostics] == [
        (0, 2, 0), (0,), (0,), (0,), (2, 2, 2), (0, 0), (0,), (0, 0),
    ]
    assert [d.split_after_indices for d in diagnostics] == [
        (2,), (), (), (), (), (), (), (),
    ]
    assert diagnostics[4].directional_relations == ((1, 0), (1, 0), (1, 0))
    assert spatial_policy.groups_for(assembly.steps[1]) == [assembly.steps[1].placement_ids]
    assert spatial_policy.groups_for(assembly.steps[4]) == [assembly.steps[4].placement_ids]


def test_spatial_policy_is_deterministic():
    ids = ["a", "b", "c", "d"]
    model = _model([_part("a", 0), _part("b", 1), _part("c", 5), _part("d", 6)])
    policy = SpatialCoherenceInstructionPolicy(model)
    assert policy.groups_for(_step(ids)) == policy.groups_for(_step(ids))


def test_export_bundle_explicit_spatial_policy_preserves_default_and_round_trips():
    fixture = Path(__file__).parents[1] / "fixtures" / "notice_reference_steps_1_8.json"
    assembly = AssemblyPlan.model_validate(json.loads(fixture.read_text()))
    model = _notice_reference_model()

    direct_bundle = create_export_bundle(model, generate_bom(model), assembly)
    notice_bundle = create_export_bundle(
        model,
        generate_bom(model),
        assembly,
        instruction_policy=SpatialCoherenceInstructionPolicy(model),
    )

    assert direct_bundle.instruction_plan is not None
    assert direct_bundle.instruction_plan.total_steps == 8
    assert direct_bundle.instruction_plan.steps[0].added_placement_ids == [
        "wall-000001", "wall-000002", "wall-000003", "wall-000004",
    ]

    assert notice_bundle.assembly_plan is not None
    assert notice_bundle.assembly_plan.total_steps == 8
    assert notice_bundle.instruction_plan is not None
    assert notice_bundle.instruction_plan.total_steps == 9
    assert notice_bundle.instruction_plan.steps[0].source_assembly_step_id == "step-0001"
    assert notice_bundle.instruction_plan.steps[0].added_placement_ids == [
        "wall-000001", "wall-000002",
    ]
    assert notice_bundle.instruction_plan.steps[1].source_assembly_step_id == "step-0001"
    assert notice_bundle.instruction_plan.steps[1].added_placement_ids == [
        "wall-000003", "wall-000004",
    ]
    assert [step.source_assembly_step_id for step in notice_bundle.instruction_plan.steps[2:]] == [
        "step-0002", "step-0003", "step-0004", "step-0005",
        "step-0006", "step-0007", "step-0008",
    ]

    restored = BrickExportBundle.model_validate_json(export_bundle_json(notice_bundle))
    assert restored.instruction_plan is not None
    assert restored.instruction_plan.total_steps == 9
    assert [step.added_placement_ids for step in restored.instruction_plan.steps] == [
        step.added_placement_ids for step in notice_bundle.instruction_plan.steps
    ]
