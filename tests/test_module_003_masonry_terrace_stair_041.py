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
    assert module["bom"]["total_parts"] == 721
    assert combined["metadata"]["module_003_piece_count"] == 721
    assert combined["metadata"]["module_001_plus_002_piece_count"] == 4794
    assert combined["metadata"]["combined_piece_count"] == 5515
    assert combined["bom"]["total_parts"] == 5515

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
    assert {part["category"] for part in parts} <= {"brick", "plate", "facade_detail"}
    assert {part["component"] for part in parts} <= {"wall", "facade_detail"}
    slope_caps = [part for part in parts if "parapet-" in part["placement_id"] and "smooth-cap" in part["placement_id"]]
    assert len(slope_caps) == 18
    assert {part["part_id"] for part in slope_caps} == {"BRICK_SLOPED_45_2X1"}
    assert {part["category"] for part in slope_caps} == {"facade_detail"}
    assert {part["component"] for part in slope_caps} == {"facade_detail"}
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
        "BRICK_1X1": 264,
        "BRICK_1X2": 28,
        "BRICK_1X3": 18,
        "BRICK_1X4": 24,
        "BRICK_1X6": 76,
        "BRICK_1X8": 127,
        "BRICK_SLOPED_45_2X1": 18,
        "PLATE_1X1": 94,
        "PLATE_1X2": 2,
        "PLATE_1X6": 2,
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
    assert bill.total_parts == len(model.parts) == 721
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

    # Deliberately open covered bay under the platform after the 047 mapped-opening correction:
    # X [16,23), Y [55,71), Z [0,36). The new x-strong opening opens into this bay.
    for part in model.parts:
        bounds = orthogonal_bounds(part)
        if bounds is None:
            continue
        intersects = (
            max(bounds.x0, 16) < min(bounds.x1, 23)
            and max(bounds.y0, 55) < min(bounds.y1, 71)
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
    house_visible = [
        part for part in module_parts
        if "stair-upper-parapet-house-" in part["placement_id"]
    ]
    core_parts = [
        part for part in module_parts
        if part not in house_visible
    ]
    assert max(
        part["x_studs"] + (
            part["length_studs"] if part["rotation_quarter_turns"] % 2
            else part["width_studs"]
        )
        for part in core_parts
    ) <= 24
    assert house_visible
    assert {part["x_studs"] for part in house_visible} == {24}


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
        if "stair-" in part["placement_id"] and part["category"] in {"brick", "plate"}
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
    assert module["bom"]["total_parts"] == 721
    assert module["metadata"]["prototype_tread_tops"] == {
        "lower": [3, 6, 9, 12, 16, 20, 24],
        "upper": [26, 28, 30, 32, 34, 36, 38, 40, 42, 44, 46, 48, 49],
    }
    assert module["metadata"]["level_model"]["ground_low_level_z"] == 0
    assert module["metadata"]["level_model"]["intermediate_turn_level_z"] == 24
    assert module["metadata"]["level_model"]["upper_masonry_platform_z"] == 49
    assert module["metadata"]["geometry"]["lower_void"] == {
        "x": [16, 23], "y": [55, 71], "z": [0, 36]
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
        "x": [16, 23], "y": [55, 71], "z": [0, 36]
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
        if "-stair-" in part["placement_id"] and part["category"] in {"brick", "plate"}
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
    assert module["bom"]["total_parts"] == 721
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



def test_module_003_044_platform_edge_is_protected_without_blocking_arrival() -> None:
    module = load(MODULE)
    parts = module["brick_model"]["parts"]
    guard = [
        part for part in parts
        if "platform-edge-fall-protection" in part["placement_id"]
    ]
    assert len(guard) == 4
    assert {part["part_id"] for part in guard} == {"BRICK_1X8"}
    assert {part["x_studs"] for part in guard} == {8}
    assert {part["y_studs"] for part in guard} == {71}
    assert {part["z_plates"] for part in guard} == {49, 52, 55, 58}

    definitions = standard_orthogonal_definitions()
    guard_cells = set()
    for part in guard:
        definition = definitions[part["part_id"]]
        width, length = definition.footprint(part["rotation_quarter_turns"])
        for x in range(part["x_studs"], part["x_studs"] + width):
            for y in range(part["y_studs"], part["y_studs"] + length):
                guard_cells.add((x, y))
    assert all((x, 71) in guard_cells for x in range(8, 16))
    assert not any((x, 71) in guard_cells for x in range(16, 23))


def test_module_003_044_false_front_opening_closed_real_rear_opening_preserved() -> None:
    module = load(MODULE)
    model = BrickModel.model_validate(module["brick_model"])
    definitions = standard_orthogonal_definitions()

    front_cells = set()
    rear_cells = set()
    for part in model.parts:
        definition = definitions.get(part.part_id)
        if definition is None or part.category not in {"brick", "plate"}:
            continue
        width, length = definition.footprint(part.rotation_quarter_turns)
        for x in range(part.x_studs, part.x_studs + width):
            for y in range(part.y_studs, part.y_studs + length):
                for z in range(part.z_plates, part.z_plates + definition.height_plates):
                    if y == 54:
                        front_cells.add((x, z))
                    if y == 71:
                        rear_cells.add((x, z))

    assert all((x, z) in front_cells for x in range(8, 23) for z in range(0, 48))
    assert not any((x, z) in rear_cells for x in range(15, 22) for z in range(0, 36))

    lower_void = module["metadata"]["geometry"]["lower_void"]
    assert lower_void == {"x": [16, 23], "y": [55, 71], "z": [0, 36]}
    for part in model.parts:
        bounds = orthogonal_bounds(part)
        if bounds is None:
            continue
        intersects = (
            max(bounds.x0, 16) < min(bounds.x1, 23)
            and max(bounds.y0, 55) < min(bounds.y1, 71)
            and max(bounds.z0, 0) < min(bounds.z1, 36)
        )
        assert not intersects, part.placement_id



def test_module_003_047_stair_parapet_top_envelope_continuous() -> None:
    module = load(MODULE)
    parts = module["brick_model"]["parts"]
    target = module["metadata"]["human_correction_047"]["parapet_target_envelope"]

    caps = [
        part for part in parts
        if "parapet-" in part["placement_id"] and "smooth-cap" in part["placement_id"]
    ]
    assert len(caps) == 18
    assert {part["part_id"] for part in caps} == {"BRICK_SLOPED_45_2X1"}
    assert {part["category"] for part in caps} == {"facade_detail"}
    assert {part["component"] for part in caps} == {"facade_detail"}

    lower_caps = [part for part in caps if "stair-lower-" in part["placement_id"]]
    assert len(lower_caps) == 6
    for rail_y in target["lower"]["rails_y"]:
        rail = sorted(
            (part for part in lower_caps if part["y_studs"] == rail_y),
            key=lambda part: part["x_studs"],
        )
        actual = [
            {
                "from": [part["x_studs"], part["z_plates"]],
                "to": [part["x_studs"] + 2, part["z_plates"] + 3],
            }
            for part in rail
        ]
        assert actual == target["lower"]["segments"]
        for first, second in zip(actual, actual[1:]):
            assert first["to"] == second["from"]
        assert all(
            first["to"][1] > first["from"][1]
            for first in actual
        )

    upper_caps = [part for part in caps if "stair-upper-" in part["placement_id"]]
    assert len(upper_caps) == 12
    for rail_x in target["upper"]["rails_x"]:
        rail = sorted(
            (part for part in upper_caps if part["x_studs"] == rail_x),
            key=lambda part: part["y_studs"],
            reverse=True,
        )
        actual = [
            {
                "from": [part["y_studs"] + 2, part["z_plates"]],
                "to": [part["y_studs"], part["z_plates"] + 3],
            }
            for part in rail
        ]
        assert actual == target["upper"]["segments"]
        for first, second in zip(actual, actual[1:]):
            assert first["to"] == second["from"]
        assert all(
            first["to"][0] < first["from"][0]
            and first["to"][1] > first["from"][1]
            for first in actual
        )

    # The target is exactly representable by the approved slope chain selected
    # for 047, so the geometric envelope error is zero plates.
    assert target["target_error_plates"] == 0

    registry = create_current_engine_capability_registry(MASTER)
    assert registry.get("BRICK_SLOPED_45_2X1").stage >= PieceCapabilityStage.PLACEMENT_APPROVED


def test_module_003_047_visible_parapet_host_wall_coplanar_and_joined() -> None:
    combined = load(COMBINED)
    definitions = standard_orthogonal_definitions()
    source_count = combined["metadata"]["module_001_plus_002_piece_count"]
    source_parts = combined["brick_model"]["parts"][:source_count]
    module_parts = combined["brick_model"]["parts"][source_count:]

    # Derive the visible host wall plane from the actual MODULE001 left facade.
    host_left = [
        part for part in source_parts
        if part["component"] == "wall"
        and part.get("facade") == "left"
        and part["part_id"] in definitions
    ]
    assert host_left

    left_bounds = []
    for part in host_left:
        definition = definitions[part["part_id"]]
        width, length = definition.footprint(part["rotation_quarter_turns"])
        left_bounds.append((
            part["x_studs"],
            part["x_studs"] + width,
            part["y_studs"],
            part["y_studs"] + length,
            part["z_plates"],
            part["z_plates"] + definition.height_plates,
        ))
    host_visible_plane = min(bounds[0] for bounds in left_bounds)

    # The longitudinal host limit must be derived from every structural
    # MODULE001 wall cell that actually occupies that visible plane. This
    # deliberately includes the rear-wall return instead of assuming a
    # historical nominal rear coordinate.
    host_structural = [
        part for part in source_parts
        if part["component"] == "wall"
        and part["category"] in {"brick", "plate"}
        and part["part_id"] in definitions
    ]
    host_cells = set()
    for part in host_structural:
        definition = definitions[part["part_id"]]
        width, length = definition.footprint(part["rotation_quarter_turns"])
        for x in range(part["x_studs"], part["x_studs"] + width):
            for y in range(part["y_studs"], part["y_studs"] + length):
                for z in range(part["z_plates"], part["z_plates"] + definition.height_plates):
                    host_cells.add((x, y, z))

    house_parapet = [
        part for part in module_parts
        if "stair-upper-parapet-house-" in part["placement_id"]
    ]
    assert house_parapet
    parapet_visible_plane = min(part["x_studs"] for part in house_parapet)

    # Semantic coplanarity: derive the host plane from MODULE001, then require
    # the visible parapet skin to occupy that same plane.
    assert parapet_visible_plane == host_visible_plane
    assert {part["x_studs"] for part in house_parapet} == {host_visible_plane}

    parapet_cells = set()
    for part in house_parapet:
        definition = definitions.get(part["part_id"])
        if definition is None:
            continue
        width, length = definition.footprint(part["rotation_quarter_turns"])
        for x in range(part["x_studs"], part["x_studs"] + width):
            for y in range(part["y_studs"], part["y_studs"] + length):
                for z in range(part["z_plates"], part["z_plates"] + definition.height_plates):
                    parapet_cells.add((x, y, z))

    # Semantic longitudinal junction: for every plate in the junction band,
    # discover the last real MODULE001 wall cell on the shared visible plane
    # and require the parapet to start in the immediately adjacent cell.
    derived_host_rear_limits = set()
    for z in range(49, 58):
        host_y = [
            y for x, y, cell_z in host_cells
            if x == host_visible_plane and cell_z == z
        ]
        assert host_y
        last_host_y = max(host_y)
        derived_host_rear_limits.add(last_host_y + 1)
        assert (host_visible_plane, last_host_y + 1, z) in parapet_cells

    # The host limit must be geometrically coherent through the full junction
    # band, but its numeric value is intentionally not hard-coded.
    assert len(derived_host_rear_limits) == 1


def test_module_003_047_human_opening_mapping_is_real_geometry() -> None:
    module = load(MODULE)
    model = BrickModel.model_validate(module["brick_model"])
    definitions = standard_orthogonal_definitions()

    solid = set()
    for part in model.parts:
        definition = definitions.get(part.part_id)
        if definition is None or part.category not in {"brick", "plate"}:
            continue
        width, length = definition.footprint(part.rotation_quarter_turns)
        for x in range(part.x_studs, part.x_studs + width):
            for y in range(part.y_studs, part.y_studs + length):
                for z in range(part.z_plates, part.z_plates + definition.height_plates):
                    solid.add((x, y, z))

    # HUMAN_FALSE_REGION is derived from the actual turn-landing footprint:
    # the front/y-low interior span below the landing must now be solid.
    landing = [
        part for part in model.parts
        if "stair-landing-" in part.placement_id
        and "support" not in part.placement_id
    ]
    landing_bounds = [orthogonal_bounds(part) for part in landing]
    assert all(bounds is not None for bounds in landing_bounds)
    false_y = min(bounds.y0 for bounds in landing_bounds if bounds is not None)
    landing_x0 = min(bounds.x0 for bounds in landing_bounds if bounds is not None)
    landing_x1 = max(bounds.x1 for bounds in landing_bounds if bounds is not None)
    landing_bottom = min(bounds.z0 for bounds in landing_bounds if bounds is not None)
    for x in range(landing_x0 + 1, landing_x1 - 1):
        for z in range(0, landing_bottom):
            assert (x, false_y, z) in solid

    # Discover the real opening from the resulting x-strong main-wall geometry.
    main_wall = [
        part for part in model.parts
        if "main-house-wall-" in part.placement_id
        and part.part_id in definitions
    ]
    assert main_wall
    wall_x = {part.x_studs for part in main_wall}
    assert len(wall_x) == 1
    wall_x = next(iter(wall_x))

    wall_y0 = min(part.y_studs for part in main_wall)
    wall_y1 = max(
        part.y_studs + definitions[part.part_id].footprint(part.rotation_quarter_turns)[1]
        for part in main_wall
    )
    empty_y = [
        y for y in range(wall_y0, wall_y1)
        if all((wall_x, y, z) not in solid for z in range(0, 36))
    ]
    assert empty_y == list(range(57, 65))

    opening = module["metadata"]["human_correction_047"]["opening_mapping"]["human_real_region"]
    assert opening["face"] == "X_STRONG_RIGHT_FACE_OF_MAIN_MASONRY"
    assert opening["visible_plane_x"] == wall_x + 1
    assert opening["y"] == [empty_y[0], empty_y[-1] + 1]

    # The opening communicates with the preserved lower void immediately
    # behind the removed x-strong wall cells.
    for y in empty_y:
        for z in range(0, 36):
            assert (wall_x - 1, y, z) not in solid

    # The old rear opening is still geometrically distinct and is not being
    # used as a substitute for the newly carved x-strong opening.
    rear_y = module["metadata"]["human_correction_047"]["opening_mapping"]["rear_opening_is_distinct"]["y"]
    assert rear_y != false_y
    assert all(
        (x, rear_y, z) not in solid
        for x in range(15, 22)
        for z in range(0, 36)
    )



def test_module_003_047_no_old_parapet_peak_above_target_envelope() -> None:
    module = load(MODULE)
    parts = module["brick_model"]["parts"]
    definitions = standard_orthogonal_definitions()

    assert not any(
        "stair-house-wall-continuity" in part["placement_id"]
        for part in parts
    )
    assert not any(
        "stair-lower-parapet-" in part["placement_id"]
        and "body" not in part["placement_id"]
        and "smooth-cap" not in part["placement_id"]
        for part in parts
    )
    assert not any(
        "stair-upper-parapet-" in part["placement_id"]
        and "body" not in part["placement_id"]
        and "smooth-cap" not in part["placement_id"]
        for part in parts
    )

    body_tops = {}
    for part in parts:
        if "parapet-" not in part["placement_id"] or "body" not in part["placement_id"]:
            continue
        definition = definitions[part["part_id"]]
        width, length = definition.footprint(part["rotation_quarter_turns"])
        top = part["z_plates"] + definition.height_plates
        for x in range(part["x_studs"], part["x_studs"] + width):
            for y in range(part["y_studs"], part["y_studs"] + length):
                body_tops[(x, y)] = max(body_tops.get((x, y), 0), top)

    # Lower cap bases are the maximum permissible body top under each slope.
    for y in (85, 92):
        for x, base in ((9, 24), (11, 27), (13, 30)):
            assert body_tops[(x, y)] == base
            assert body_tops[(x + 1, y)] == base
        assert body_tops[(15, y)] == 33

    # Upper cap bases follow the same rule on both visible rails.
    for x in (16, 24):
        for y, base in ((83, 40), (81, 43), (79, 46), (77, 49), (75, 52), (73, 55)):
            assert body_tops[(x, y)] == base
            assert body_tops[(x, y + 1)] == base
        assert body_tops[(x, 72)] == 58



def test_module_003_047c_opening_support_subsystem_reaches_ground() -> None:
    module = load(MODULE)
    model = BrickModel.model_validate(module["brick_model"])
    report = analyze_standard_brick_support_chain(model)
    by_id = {node.placement_id: node for node in report.nodes}

    local_ids = [
        part.placement_id
        for part in model.parts
        if (
            "main-house-wall-front-jamb" in part.placement_id
            or "main-house-wall-rear-jamb" in part.placement_id
            or "main-house-wall-opening-lintel" in part.placement_id
            or "main-house-wall-upper-closure" in part.placement_id
            or (
                "upper-platform" in part.placement_id
                and part.x_studs == 23
            )
        )
        and part.component == "wall"
        and part.category in {"brick", "plate"}
    ]
    assert local_ids
    assert all(by_id[placement_id].reaches_ground for placement_id in local_ids)

    lintel = [
        by_id[placement_id]
        for placement_id in local_ids
        if "main-house-wall-opening-lintel" in placement_id
    ]
    upper = [
        by_id[placement_id]
        for placement_id in local_ids
        if "main-house-wall-upper-closure" in placement_id
    ]
    platform = [
        by_id[placement_id]
        for placement_id in local_ids
        if "upper-platform" in placement_id
    ]
    assert lintel and upper and platform
    assert all(node.supporters for node in lintel)
    assert all(node.supporters for node in upper)
    assert all(node.supporters for node in platform)

def test_module_003_044_global_geometry_circulation_levels_and_collision_scope() -> None:
    module = load(MODULE)
    model = BrickModel.model_validate(module["brick_model"])
    geometry = module["metadata"]["geometry"]

    assert module["metadata"]["rearward_translation_studs"] == 10
    assert module["metadata"]["stair_lateral_translation_studs"] == 9
    assert geometry["main_masonry_envelope"] == {
        "x": [7, 24], "y": [54, 72], "z": [0, 49]
    }
    assert geometry["upper_platform"] == {
        "x": [7, 24], "y": [54, 72], "walking_top_z": 49
    }
    assert geometry["stair_lower"] == {
        "x": [9, 16], "y": [85, 93], "z": [0, 24]
    }
    assert geometry["turn_landing"] == {
        "x": [16, 24], "y": [85, 93], "walking_top_z": 24
    }
    assert geometry["stair_upper"] == {
        "x": [16, 24], "y": [72, 85], "z": [24, 49]
    }
    assert module["metadata"]["level_model"] == {
        "ground_low_level_z": 0,
        "intermediate_turn_level_z": 24,
        "upper_masonry_platform_z": 49,
        "future_wood_terrace_interface_z": 45,
    }

    lower = [p for p in model.parts if "stair-lower-tread" in p.placement_id]
    upper = [p for p in model.parts if "stair-upper-tread" in p.placement_id]
    assert [p.z_plates + 1 for p in lower] == [3, 6, 9, 12, 16, 20, 24]
    assert [p.z_plates + 1 for p in upper] == [
        26, 28, 30, 32, 34, 36, 38, 40, 42, 44, 46, 48, 49
    ]

    assert orthogonal_collisions(model) == []
    support = analyze_standard_brick_support_chain(model)
    assert support.valid
    assert not support.unsupported_placement_ids
