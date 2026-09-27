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
    assert module["bom"]["total_parts"] == 564
    assert combined["metadata"]["module_003_piece_count"] == 564
    assert combined["metadata"]["module_001_plus_002_piece_count"] == 4794
    assert combined["metadata"]["combined_piece_count"] == 5358
    assert combined["bom"]["total_parts"] == 5358

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
        "BRICK_1X6": 22,
        "BRICK_1X8": 148,
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
    assert bill.total_parts == len(model.parts) == 564
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

    # Deliberately open covered bay under the platform:
    # X [16,22), Y [44,61), Z [0,36).
    for part in model.parts:
        bounds = orthogonal_bounds(part)
        assert bounds is not None
        intersects = (
            max(bounds.x0, 16) < min(bounds.x1, 22)
            and max(bounds.y0, 44) < min(bounds.y1, 61)
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
        "x": [7, 24], "y": [44, 62], "z": [0, 49]
    }
    assert interfaces["TO_HOUSE"]["plane_x"] == 24
    assert interfaces["TO_GROUND"] == {"z": 0}
    assert interfaces["TO_FUTURE_WOOD_TERRACE"]["walking_level_z"] == 45
    assert interfaces["TO_FUTURE_WOOD_TERRACE"]["plan_span"] == "UNRESOLVED_REFINABLE"

    model = BrickModel.model_validate(combined["brick_model"])
    assert (model.width_studs, model.depth_studs, model.height_plates) == (57, 71, 164)
    assert (model.canvas_width_studs, model.canvas_depth_studs) == (83, 83)
    assert (model.origin_x_studs, model.origin_y_studs) == (24, 1)

    module_parts = combined["brick_model"]["parts"][4794:]
    assert max(part["x_studs"] + (part["length_studs"] if part["rotation_quarter_turns"] % 2 else part["width_studs"]) for part in module_parts) <= 24


def test_module_003_records_viewer_ux_debt_without_viewer_change() -> None:
    module = load(MODULE)
    assert module["metadata"]["viewer_debt"] == "DIRECT_VIEWER_OPENING_UX = NEEDS_FUTURE_FIX"
