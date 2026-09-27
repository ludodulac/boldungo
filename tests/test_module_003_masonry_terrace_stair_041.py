from __future__ import annotations

import json
from pathlib import Path

from brickhouse.bricks.bom import BillOfMaterials
from brickhouse.bricks.brick_model import BrickModel
from brickhouse.bricks.catalog import standard_orthogonal_definitions
from brickhouse.bricks.orthogonal_geometry import orthogonal_bounds, orthogonal_collisions
from brickhouse.bricks.piece_capabilities import (
    PieceCapabilityStage,
    create_current_engine_capability_registry,
    validate_model_part_capabilities,
)
from brickhouse.bricks.support_chain import analyze_standard_brick_support_chain

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "frontend" / "module-001-plus-module-002-roof-export.json"
MODULE = ROOT / "frontend" / "module-003-masonry-terrace-stair-export.json"
COMBINED = ROOT / "frontend" / "module-001-plus-module-002-plus-module-003-export.json"
MASTER = ROOT / "data" / "processed" / "piece_types_master.csv"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_module_003_artifact_counts_levels_and_scope() -> None:
    module = load(MODULE)
    combined = load(COMBINED)
    source = load(SOURCE)

    assert module["metadata"]["module_id"] == "MODULE_003_MASONRY_TERRACE_STAIR"
    assert module["bom"]["total_parts"] == 566
    assert combined["metadata"]["module_003_piece_count"] == 566
    assert combined["metadata"]["module_001_plus_002_piece_count"] == 4794
    assert combined["metadata"]["combined_piece_count"] == 5360
    assert combined["bom"]["total_parts"] == 5360

    levels = module["metadata"]["level_model"]
    assert levels == {
        "ground_low_level_z": 0,
        "intermediate_turn_level_z": 24,
        "upper_masonry_platform_z": 49,
        "future_wood_terrace_interface_z": 45,
    }
    assert module["metadata"]["circulation_path"] == [
        "LOW_Z0",
        "LOWER_RUN_TO_Z24",
        "TURN_LANDING_Z24",
        "UPPER_RUN_TO_Z49",
        "UPPER_PLATFORM_Z49",
    ]

    parts = module["brick_model"]["parts"]
    assert {part["category"] for part in parts} <= {"brick", "plate"}
    assert {part["component"] for part in parts} == {"wall"}
    forbidden = ("timber", "chimney", "antenna", "gutter", "window", "door", "roof")
    assert not any(
        any(word in (part["placement_id"] + " " + part["part_id"]).lower() for word in forbidden)
        for part in parts
    )

    source_parts = source["brick_model"]["parts"]
    combined_source = combined["brick_model"]["parts"][: len(source_parts)]
    for original, translated in zip(source_parts, combined_source):
        expected = dict(original)
        expected["x_studs"] += 21
        assert translated == expected


def test_module_003_bom_is_exact_and_approved() -> None:
    module = load(MODULE)
    expected = {
        "BRICK_1X1": 190,
        "BRICK_1X2": 40,
        "BRICK_1X3": 6,
        "BRICK_1X4": 24,
        "BRICK_1X6": 25,
        "BRICK_1X8": 147,
        "PLATE_1X1": 64,
        "PLATE_1X2": 2,
        "PLATE_1X8": 68,
    }
    actual = {line["part_id"]: line["quantity"] for line in module["bom"]["lines"]}
    assert actual == expected

    registry = create_current_engine_capability_registry(MASTER)
    for part_id in expected:
        assert registry.get(part_id).stage >= PieceCapabilityStage.PLACEMENT_APPROVED


def test_module_003_solids_have_no_collision_and_reach_ground() -> None:
    module = load(MODULE)
    model = BrickModel.model_validate(module["brick_model"])
    bill = BillOfMaterials.model_validate(module["bom"])
    assert bill.total_parts == len(model.parts) == 566
    assert len({part.placement_id for part in model.parts}) == len(model.parts)

    registry = create_current_engine_capability_registry(MASTER)
    validate_model_part_capabilities(model, registry)
    assert orthogonal_collisions(model) == []

    support = analyze_standard_brick_support_chain(model)
    assert support.valid
    assert not support.unsupported_placement_ids


def test_module_003_preserves_large_lower_void() -> None:
    module = load(MODULE)
    model = BrickModel.model_validate(module["brick_model"])

    # Deliberately open covered bay under the platform after the 042 rearward shift:
    # X [16,22), Y [54,71), Z [0,36).
    for part in model.parts:
        bounds = orthogonal_bounds(part)
        assert bounds is not None
        intersects = (
            max(bounds.x0, 16) < min(bounds.x1, 22)
            and max(bounds.y0, 54) < min(bounds.y1, 71)
            and max(bounds.z0, 0) < min(bounds.z1, 36)
        )
        assert not intersects, part.placement_id


def test_module_003_circulation_is_monotone_and_reaches_platform() -> None:
    module = load(MODULE)
    parts = module["brick_model"]["parts"]

    lower = [
        part for part in parts
        if "stair-lower-tread" in part["placement_id"]
    ]
    upper = [
        part for part in parts
        if "stair-upper-tread" in part["placement_id"]
    ]
    assert [part["z_plates"] + 1 for part in lower] == [3, 6, 9, 12, 16, 20, 24]
    assert [part["z_plates"] + 1 for part in upper] == [
        26, 28, 30, 32, 34, 36, 38, 40, 42, 44, 46, 48, 49
    ]

    landing = [
        part for part in parts
        if "stair-landing-" in part["placement_id"]
        and "support" not in part["placement_id"]
    ]
    assert landing
    assert {part["z_plates"] + 1 for part in landing} == {24}

    platform = [
        part for part in parts if "upper-platform" in part["placement_id"]
    ]
    assert platform
    assert {part["z_plates"] + 1 for part in platform} == {49}


def test_module_003_position_and_interfaces_are_host_relative() -> None:
    module = load(MODULE)
    combined = load(COMBINED)
    geometry = module["metadata"]["geometry"]
    interfaces = module["metadata"]["interfaces"]

    assert geometry["main_masonry_envelope"] == {
        "x": [7, 24], "y": [54, 72], "z": [0, 49]
    }
    assert interfaces["TO_HOUSE"]["plane_x"] == 24
    assert interfaces["TO_GROUND"] == {"z": 0}
    assert interfaces["TO_FUTURE_WOOD_TERRACE"]["walking_level_z"] == 45
    assert interfaces["TO_FUTURE_WOOD_TERRACE"]["plan_span"] == "UNRESOLVED_REFINABLE"

    model = BrickModel.model_validate(combined["brick_model"])
    assert (model.width_studs, model.depth_studs, model.height_plates) == (57, 71, 164)
    assert (model.canvas_width_studs, model.canvas_depth_studs) == (83, 93)
    assert (model.origin_x_studs, model.origin_y_studs) == (24, 1)

    module_parts = combined["brick_model"]["parts"][4794:]
    assert max(part["x_studs"] + (part["length_studs"] if part["rotation_quarter_turns"] % 2 else part["width_studs"]) for part in module_parts) <= 24


def test_module_003_records_viewer_ux_debt_without_viewer_change() -> None:
    module = load(MODULE)
    assert module["metadata"]["viewer_debt"] == "DIRECT_VIEWER_OPENING_UX = NEEDS_FUTURE_FIX"


def test_module_003_042_stair_is_rearward_and_outside_house_footprint() -> None:
    module = load(MODULE)
    combined = load(COMBINED)
    geometry = module["metadata"]["geometry"]

    assert module["metadata"]["rearward_translation_studs"] == 10
    assert module["metadata"]["host_house_rear_plane_y"] == 72
    assert geometry["stair_upper"] == {
        "x": [16, 24], "y": [72, 85], "z": [24, 49]
    }
    assert geometry["stair_lower"] == {
        "x": [9, 16], "y": [85, 93], "z": [0, 24]
    }
    assert geometry["turn_landing"] == {
        "x": [16, 24], "y": [85, 93], "walking_top_z": 24
    }

    # Host footprint in the corrected combined frame:
    # X [24,81), Y [1,72). Every stair placement must remain outside it.
    stair_parts = [
        part for part in combined["brick_model"]["parts"][4794:]
        if "stair-" in part["placement_id"]
    ]
    assert stair_parts
    definitions = standard_orthogonal_definitions()
    for part in stair_parts:
        definition = definitions[part["part_id"]]
        width, length = definition.footprint(part["rotation_quarter_turns"])
        overlaps_house = (
            max(part["x_studs"], 24) < min(part["x_studs"] + width, 81)
            and max(part["y_studs"], 1) < min(part["y_studs"] + length, 72)
        )
        assert not overlaps_house, part["placement_id"]

    upper_treads = [
        part for part in stair_parts
        if "stair-upper-tread" in part["placement_id"]
    ]
    assert min(part["y_studs"] for part in upper_treads) == 72


def test_module_003_042_rearward_translation_preserves_topology_levels_and_void() -> None:
    module = load(MODULE)
    assert module["bom"]["total_parts"] == 566
    assert module["metadata"]["prototype_tread_tops"] == {
        "lower": [3, 6, 9, 12, 16, 20, 24],
        "upper": [26, 28, 30, 32, 34, 36, 38, 40, 42, 44, 46, 48, 49],
    }
    assert module["metadata"]["level_model"]["ground_low_level_z"] == 0
    assert module["metadata"]["level_model"]["intermediate_turn_level_z"] == 24
    assert module["metadata"]["level_model"]["upper_masonry_platform_z"] == 49
    assert module["metadata"]["geometry"]["lower_void"] == {
        "x": [16, 22], "y": [54, 71], "z": [0, 36]
    }


def test_module_003_043_platform_and_rearward_position_are_frozen() -> None:
    module = load(MODULE)
    geometry = module["metadata"]["geometry"]

    assert module["metadata"]["rearward_translation_studs"] == 10
    assert module["metadata"]["stair_lateral_translation_studs"] == 9
    assert geometry["main_masonry_envelope"] == {
        "x": [7, 24], "y": [54, 72], "z": [0, 49]
    }
    assert geometry["upper_platform"] == {
        "x": [7, 24], "y": [54, 72], "walking_top_z": 49
    }
    assert geometry["lower_void"] == {
        "x": [16, 22], "y": [54, 71], "z": [0, 36]
    }


def test_module_003_043_stair_moves_to_house_wall_without_entering_house() -> None:
    module = load(MODULE)
    combined = load(COMBINED)
    geometry = module["metadata"]["geometry"]

    assert geometry["stair_upper"] == {
        "x": [16, 24], "y": [72, 85], "z": [24, 49]
    }
    assert geometry["turn_landing"] == {
        "x": [16, 24], "y": [85, 93], "walking_top_z": 24
    }
    assert geometry["stair_lower"] == {
        "x": [9, 16], "y": [85, 93], "z": [0, 24]
    }

    stair_parts = [
        part for part in combined["brick_model"]["parts"][4794:]
        if "-stair-" in part["placement_id"]
    ]
    definitions = standard_orthogonal_definitions()
    for part in stair_parts:
        definition = definitions[part["part_id"]]
        width, length = definition.footprint(part["rotation_quarter_turns"])
        overlaps_house = (
            max(part["x_studs"], 24) < min(part["x_studs"] + width, 81)
            and max(part["y_studs"], 1) < min(part["y_studs"] + length, 72)
        )
        assert not overlaps_house, part["placement_id"]

    upper_treads = [
        part for part in stair_parts
        if "stair-upper-tread" in part["placement_id"]
    ]
    assert max(
        part["x_studs"] + standard_orthogonal_definitions()[part["part_id"]].footprint(part["rotation_quarter_turns"])[0]
        for part in upper_treads
    ) == 24


def test_module_003_043_obstructing_rail_removed_and_first_landing_railed() -> None:
    module = load(MODULE)
    parts = module["brick_model"]["parts"]

    assert module["metadata"]["obstructing_rail_removed"] == "platform-parapet-rear"
    assert not any("platform-parapet-rear" in part["placement_id"] for part in parts)

    rails = [
        part for part in parts
        if "stair-first-landing-rail" in part["placement_id"]
    ]
    assert len(rails) == 6
    assert {part["z_plates"] for part in rails} == {24, 27, 30}

    definitions = standard_orthogonal_definitions()
    occupied = set()
    for part in rails:
        definition = definitions[part["part_id"]]
        width, length = definition.footprint(part["rotation_quarter_turns"])
        for x in range(part["x_studs"], part["x_studs"] + width):
            for y in range(part["y_studs"], part["y_studs"] + length):
                occupied.add((x, y))

    # West entry from lower run and north exit to upper run stay open.
    assert not any(x == 16 and 85 <= y < 92 for x, y in occupied)
    assert not any(y == 85 and 16 <= x < 24 for x, y in occupied)

    # Protection exists on south and east edges.
    assert all((x, 92) in occupied for x in range(16, 24))
    assert all((23, y) in occupied for y in range(86, 92))


def test_module_003_043_circulation_and_collision_scope() -> None:
    module = load(MODULE)
    model = BrickModel.model_validate(module["brick_model"])
    assert module["bom"]["total_parts"] == 566
    assert orthogonal_collisions(model) == []

    support = analyze_standard_brick_support_chain(model)
    assert support.valid
    assert not support.unsupported_placement_ids

    lower = [p for p in model.parts if "stair-lower-tread" in p.placement_id]
    upper = [p for p in model.parts if "stair-upper-tread" in p.placement_id]
    assert [p.z_plates + 1 for p in lower] == [3, 6, 9, 12, 16, 20, 24]
    assert [p.z_plates + 1 for p in upper] == [
        26, 28, 30, 32, 34, 36, 38, 40, 42, 44, 46, 48, 49
    ]
