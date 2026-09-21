from brickhouse.bricks.assembly_planner import direct_support_graph, planning_candidates, score_candidates, plan_supported_non_roof_parts
from brickhouse.bricks.brick_model import BrickModel, BrickModelPart

def part(pid, part_id, x, y, z, rotation=0):
    return BrickModelPart(placement_id=pid, part_id=part_id, category="brick",
        component="wall", x_studs=x, y_studs=y, z_plates=z,
        rotation_quarter_turns=rotation, facade="front")

def model(parts):
    return BrickModel(building_id="b", volume_id="v", width_studs=12,
        depth_studs=12, height_plates=12, parts=parts)

def test_direct_support_requires_vertical_contact_and_footprint_overlap():
    graph = direct_support_graph(model([
        part("base", "BRICK_1X4", 0, 0, 0),
        part("top", "BRICK_1X2", 0, 1, 3),
        part("away", "BRICK_1X2", 8, 0, 3),
    ]))
    assert graph["base"] == ()
    assert graph["top"] == ("base",)
    assert graph["away"] == ()

def test_rotated_footprint_can_supply_support():
    graph = direct_support_graph(model([
        part("base", "BRICK_1X4", 0, 0, 0, rotation=1),
        part("top", "BRICK_1X2", 1, 0, 3, rotation=1),
    ]))
    assert graph["top"] == ("base",)


def test_candidates_start_on_ground_then_unlock_supported_part():
    m = model([
        part("base", "BRICK_1X4", 0, 0, 0),
        part("top", "BRICK_1X2", 0, 1, 3),
        part("unsupported", "BRICK_1X2", 8, 0, 3),
    ])
    assert [c.placement_id for c in planning_candidates(m, set())] == ["base"]
    assert [c.placement_id for c in planning_candidates(m, {"base"})] == ["top"]


def test_scoring_prefers_larger_proven_support_and_keeps_reasons():
    m = model([
        part("wide", "BRICK_1X4", 0, 0, 0),
        part("narrow", "BRICK_1X1", 6, 0, 0),
        part("wide_top", "BRICK_1X4", 0, 0, 3),
        part("narrow_top", "BRICK_1X1", 6, 0, 3),
    ])
    candidates = planning_candidates(m, {"wide", "narrow"})
    scored = score_candidates(candidates)
    assert [item.placement_id for item in scored] == ["wide_top", "narrow_top"]
    assert "direct-support-proven" in scored[0].reasons


def test_planner_builds_supported_stack_and_refuses_unproven_floating_part():
    m = model([
        part("base", "BRICK_1X4", 0, 0, 0),
        part("middle", "BRICK_1X4", 0, 0, 3),
        part("top", "BRICK_1X2", 0, 1, 6),
        part("floating", "BRICK_1X1", 9, 0, 6),
    ])
    result = plan_supported_non_roof_parts(m)
    assert [step.placement_id for step in result.steps] == ["base", "middle", "top"]
    assert result.unresolved_ids == ("floating",)
    assert [step.sequence for step in result.steps] == [1, 2, 3]
