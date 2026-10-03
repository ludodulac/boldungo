from copy import deepcopy
from pathlib import Path

from brickhouse.bricks.piece_capabilities import (
    create_current_engine_capability_registry,
    validate_model_part_capabilities,
)
from brickhouse.bricks.scene_grade_contact import resolve_local_grade_contact_raster
from brickhouse.partial_scene_pipeline import run_partial_scene_pipeline
from brickhouse.pipeline import run_m0_pipeline_scene
from brickhouse.scene.benchmark_scene_recipe import materialize_scene_recipe


ROOT = Path(__file__).resolve().parents[2]
BENCHMARK = ROOT / "frontend" / "benchmarks" / "real-house-5"
RECIPE = BENCHMARK / "scene-candidate-v0.2.json"
CONTACT_ID = "right-opening-2"
GLASS_BLOCK_ID = "right-opening-3"
FRONT_WIDTH_STUDS = 48


def _scene():
    return materialize_scene_recipe(RECIPE)


def _terrain_parts(bundle):
    return [part for part in bundle.brick_model.parts if part.category == "terrain"]


def _contact_parts(bundle):
    return [
        part
        for part in _terrain_parts(bundle)
        if part.placement_id.startswith("scene-grade-contact:")
    ]


def _right_opening(scene, opening_id):
    return next(opening for opening in scene.openings if opening.id == opening_id)


def _rectangles(scene):
    return {
        opening.id: (
            opening.offset_horizontal,
            opening.offset_vertical,
            opening.width,
            opening.height,
        )
        for opening in scene.openings
    }


def _assert_local_contact(bundle, scene):
    parts = _contact_parts(bundle)
    assert parts
    assert all(part.opening_id == CONTACT_ID for part in parts)
    assert all(part.facade.value == "right" for part in parts)
    assert all(part.category == "terrain" for part in parts)
    assert all(part.component == "facade_detail" for part in parts)
    assert all(part.part_id.startswith("PLATE_1X") for part in parts)

    contact = resolve_local_grade_contact_raster(
        bundle.brick_model,
        scene,
        CONTACT_ID,
        front_width_studs=FRONT_WIDTH_STUDS,
    )

    # The one-plate sidewalk representation ends exactly at the LEGO opening sill.
    assert {part.z_plates + part.height_plates for part in parts} == {
        contact.opening_bottom_z_plates
    }
    assert contact.sidewalk_top_z_plates == contact.opening_bottom_z_plates

    # RIGHT wall occupies its exterior X plane; sidewalk begins at the next stud.
    right_wall = [
        part
        for part in bundle.brick_model.parts
        if part.component == "wall" and part.facade is not None and part.facade.value == "right"
    ]
    outer_wall_x = max(part.x_studs for part in right_wall)
    assert {part.x_studs for part in parts} == {outer_wall_x + 1}
    assert contact.sidewalk_x_studs == outer_wall_x + 1

    # Exact local horizontal span: no extension beyond the LEGO opening raster.
    occupied_y = set()
    for part in parts:
        assert part.width_studs == 1
        assert part.height_plates == 1
        occupied_y.update(range(part.y_studs, part.y_studs + part.length_studs))
    expected_y = set(
        range(
            contact.sidewalk_y_start_studs,
            contact.sidewalk_y_start_studs + contact.opening_width_studs,
        )
    )
    assert occupied_y == expected_y

    # No full unresolved slope is fabricated and no terrain is attached to glass blocks.
    assert not any(
        part.placement_id.startswith("scene-terrain:")
        for part in bundle.brick_model.parts
    )
    assert not any(part.opening_id == GLASS_BLOCK_ID for part in _terrain_parts(bundle))

    issue = next(
        item
        for item in bundle.fidelity_issues
        if item.code == "lego_grade_profile_partial_contact_only"
        and item.object_id == CONTACT_ID
    )
    assert "complete LEGO slope is deliberately omitted" in issue.message


def test_canonical_scene_truth_is_preserved_before_and_after_both_pipelines():
    scene = _scene()
    before = deepcopy(scene.model_dump(mode="json"))
    before_rectangles = _rectangles(scene)

    contact = _right_opening(scene, CONTACT_ID)
    glass = _right_opening(scene, GLASS_BLOCK_ID)
    profile = next(item for item in scene.terrain.profiles if item.facade.value == "right")

    assert contact.local_grade_clearance == 0
    assert glass.opening_visual.glazing == "glass_block"
    assert glass.opening_visual.pane_layout == "square_grid"
    assert profile.start_elevation is None
    assert profile.end_elevation is None
    assert profile.outward_extent is None

    run_m0_pipeline_scene(scene, front_width_studs=FRONT_WIDTH_STUDS)
    run_partial_scene_pipeline(scene, front_width_studs=FRONT_WIDTH_STUDS)

    assert scene.model_dump(mode="json") == before
    assert _rectangles(scene) == before_rectangles
    glass_after = _right_opening(scene, GLASS_BLOCK_ID)
    assert glass_after.opening_visual.glazing == "glass_block"
    assert glass_after.opening_visual.pane_layout == "square_grid"


def test_full_scene_pipeline_builds_only_the_proven_local_sidewalk_contact():
    scene = _scene()
    bundle = run_m0_pipeline_scene(scene, front_width_studs=FRONT_WIDTH_STUDS)

    _assert_local_contact(bundle, scene)

    terrain_parts = _terrain_parts(bundle)
    terrain_quantity = sum(
        line.quantity for line in bundle.bom.lines if line.category == "terrain"
    )
    assert terrain_quantity == len(terrain_parts) == len(_contact_parts(bundle))

    terrain_ids = {part.placement_id for part in terrain_parts}
    assembly_terrain_ids = {
        placement_id
        for step in bundle.assembly_plan.steps
        if step.phase == "Terrain"
        for placement_id in step.placement_ids
    }
    assert terrain_ids
    assert terrain_ids == assembly_terrain_ids

    validate_model_part_capabilities(
        bundle.brick_model,
        create_current_engine_capability_registry(),
    )


def test_partial_real_house_pipeline_uses_original_scene_for_local_grade_contact():
    scene = _scene()
    bundle = run_partial_scene_pipeline(scene, front_width_studs=FRONT_WIDTH_STUDS)

    _assert_local_contact(bundle, scene)

    terrain_parts = _terrain_parts(bundle)
    terrain_quantity = sum(
        line.quantity for line in bundle.bom.lines if line.category == "terrain"
    )
    assert terrain_quantity == len(terrain_parts) == len(_contact_parts(bundle))

    terrain_ids = {part.placement_id for part in terrain_parts}
    assembly_terrain_ids = {
        placement_id
        for step in bundle.assembly_plan.steps
        if step.phase == "Terrain"
        for placement_id in step.placement_ids
    }
    assert terrain_ids == assembly_terrain_ids

    validate_model_part_capabilities(
        bundle.brick_model,
        create_current_engine_capability_registry(),
    )
