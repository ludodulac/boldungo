from __future__ import annotations

import json
from pathlib import Path

from brickhouse.bricks.bom import BillOfMaterials
from brickhouse.bricks.brick_model import BrickModel
from brickhouse.bricks.catalog import standard_orthogonal_definitions
from brickhouse.bricks.piece_capabilities import (
    PieceCapabilityStage,
    create_current_engine_capability_registry,
    validate_model_part_capabilities,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "frontend" / "module-001-plus-module-002-plus-module-003-export.json"
MODULE = ROOT / "frontend" / "module-004-wood-terrace-export.json"
COMBINED = ROOT / "frontend" / "module-001-plus-module-002-plus-module-003-plus-module-004-export.json"
MASTER = ROOT / "data" / "processed" / "piece_types_master.csv"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def bounds(part) -> tuple[int, int, int, int, int, int]:
    definitions = standard_orthogonal_definitions()
    definition = definitions.get(part.part_id)
    if definition is not None:
        width, length = definition.footprint(part.rotation_quarter_turns)
        height = definition.height_plates
    else:
        width = part.width_studs
        length = part.length_studs
        height = part.height_plates
        assert width is not None and length is not None and height is not None
        if part.rotation_quarter_turns % 2:
            width, length = length, width
    return (
        part.x_studs,
        part.x_studs + int(width),
        part.y_studs,
        part.y_studs + int(length),
        part.z_plates,
        part.z_plates + int(height),
    )


def part_cells(part) -> set[tuple[int, int, int]]:
    x0, x1, y0, y1, z0, z1 = bounds(part)
    return {
        (x, y, z)
        for x in range(x0, x1)
        for y in range(y0, y1)
        for z in range(z0, z1)
    }


def cells(parts) -> set[tuple[int, int, int]]:
    result: set[tuple[int, int, int]] = set()
    for part in parts:
        result.update(part_cells(part))
    return result


def parts_with(fragment: str, parts) -> list:
    return [part for part in parts if fragment in part.placement_id]


def primary_underspace_blockers(parts, void) -> list[str]:
    allowed_fragments = (
        "long-outer-rim-beam",
        "wall-limit-terminal-rim",
        "observed-main-post",
    )
    interior = {
        (x, y, z)
        for x in range(*void["x"])
        for y in range(*void["y"])
        for z in range(*void["z"])
    }
    blockers = []
    for part in parts:
        if any(fragment in part.placement_id for fragment in allowed_fragments):
            continue
        if part_cells(part).intersection(interior):
            blockers.append(part.placement_id)
    return blockers


def model_parts() -> tuple[dict, BrickModel, list]:
    module = load(MODULE)
    model = BrickModel.model_validate(module["brick_model"])
    return module, model, model.parts


def test_065_source_modules_are_immutable_prefix_and_module004_is_new_domain() -> None:
    source = load(SOURCE)
    module = load(MODULE)
    combined = load(COMBINED)

    assert module["metadata"]["mission"] == "BOLDUNGO-065-MODULE004-TOPOLOGY-CORRECTION"
    source_parts = source["brick_model"]["parts"]
    combined_parts = combined["brick_model"]["parts"]

    assert combined_parts[: len(source_parts)] == source_parts
    assert combined["metadata"]["source_piece_count"] == len(source_parts)
    assert combined["metadata"]["module_004_piece_count"] == module["bom"]["total_parts"]
    assert combined["metadata"]["combined_piece_count"] == len(combined_parts)

    new_parts = combined_parts[len(source_parts):]
    assert new_parts == module["brick_model"]["parts"]
    assert new_parts
    assert all(part["placement_id"].startswith("module-004-") for part in new_parts)
    assert all(part["category"] == "timber" for part in new_parts)
    assert all(part["component"] == "facade_detail" for part in new_parts)


def test_065_wood_terrace_reaches_wall_limit_end_on_confirmed_left_face() -> None:
    source = load(SOURCE)
    module, _model, parts = model_parts()
    geometry = module["metadata"]["geometry"]
    deck = geometry["deck_footprint"]

    wall_limit = source["brick_model"]["origin_y_studs"]
    module003_end = source["metadata"]["geometry"]["upper_platform"]["y"][0]

    assert deck["x"][1] == source["metadata"]["host_house_left_plane_x"]
    assert deck["y"] == [wall_limit, module003_end]
    assert deck["walking_top_z"] == source["metadata"]["level_model"]["future_wood_terrace_interface_z"]
    assert deck["metric_status"] == "CONSTRUCTIVE_APPROXIMATION"

    ends = geometry["longitudinal_ends"]
    assert ends["WALL-LIMIT-END"]["y"] == wall_limit
    assert ends["MODULE003-END"]["y"] == module003_end

    floor = parts_with("deck-floor", parts)
    floor_cells = cells(floor)
    floor_z = deck["walking_top_z"] - 1
    for x in range(*deck["x"]):
        for y in range(*deck["y"]):
            assert (x, y, floor_z) in floor_cells


def test_065_primary_underspace_remains_open() -> None:
    module, _model, parts = model_parts()
    void = module["metadata"]["geometry"]["primary_underspace"]

    assert void["classification"] == "MAJOR_OPEN_WOOD_TERRACE_UNDERSPACE"
    assert void["open_to_ground"] is True
    assert primary_underspace_blockers(parts, void) == []


def test_065_primary_underspace_gate_rejects_interior_partition() -> None:
    module, _model, parts = model_parts()
    void = module["metadata"]["geometry"]["primary_underspace"]
    prototype = parts[0]
    partition = prototype.model_copy(update={
        "placement_id": "module-004-interior-partition-negative-regression",
        "part_id": "BRICK_1X8",
        "x_studs": void["x"][0],
        "y_studs": void["y"][0],
        "z_plates": 0,
        "rotation_quarter_turns": 0,
        "facade": "left",
        "width_studs": 1,
        "length_studs": 8,
        "height_plates": 3,
    })

    assert partition.placement_id in primary_underspace_blockers([*parts, partition], void)


def test_065_wood_terrace_remains_structurally_distinct_from_module003() -> None:
    source = load(SOURCE)
    module, _model, module_parts = model_parts()

    module003_raw = [
        raw for raw in source["brick_model"]["parts"]
        if raw["placement_id"].startswith("module-003-")
    ]
    module003 = BrickModel.model_validate({
        "schema_version": "0.1",
        "building_id": source["building_id"],
        "volume_id": "temporary-module003-check",
        "width_studs": source["brick_model"]["width_studs"],
        "depth_studs": source["brick_model"]["depth_studs"],
        "height_plates": source["brick_model"]["height_plates"],
        "parts": module003_raw,
    }).parts

    assert cells(module003).isdisjoint(cells(module_parts))
    interface = module["metadata"]["module_003_interface"]
    assert interface["end_identity"] == "MODULE003-END"
    assert interface["exact_connection"] == "NOT_OBSERVABLE_NOT_ENCODED"


def test_065_terminal_railing_is_at_wall_limit_end_not_module003_end() -> None:
    module, _model, parts = model_parts()
    geometry = module["metadata"]["geometry"]
    deck = geometry["deck_footprint"]
    outer_x = geometry["long_outer_edge"]["x"]
    wall_limit_y = geometry["longitudinal_ends"]["WALL-LIMIT-END"]["y"]
    module003_y = geometry["longitudinal_ends"]["MODULE003-END"]["y"]
    top_z = geometry["railing"]["top_z"]

    long_top = parts_with("railing-long-outer-top", parts)
    terminal_top = parts_with("railing-wall-limit-terminal-top", parts)
    terminal_vertical = parts_with("railing-wall-limit-terminal-vertical", parts)

    assert long_top and terminal_top and terminal_vertical
    assert not parts_with("railing-module003-terminal", parts)

    long_cells = cells(long_top)
    terminal_cells = cells(terminal_top)

    for y in range(*deck["y"]):
        for z in range(top_z - 3, top_z):
            assert (outer_x, y, z) in long_cells

    for x in range(deck["x"][0] + 1, deck["x"][1]):
        for z in range(top_z - 3, top_z):
            assert (x, wall_limit_y, z) in terminal_cells

    assert all(part.y_studs == wall_limit_y for part in terminal_vertical)
    assert geometry["railing"]["terminal_return_end"] == "WALL-LIMIT-END"
    assert geometry["railing"]["module003_end_terminal_return"] is False
    assert module003_y != wall_limit_y


def test_065_observed_post_is_on_outer_edge_in_wall_limit_sector() -> None:
    module, _model, parts = model_parts()
    geometry = module["metadata"]["geometry"]
    post_meta = geometry["observed_main_post"]
    post = parts_with("observed-main-post", parts)

    assert post
    assert post_meta["edge_identity"] == "LONG_OUTER_EDGE"
    assert post_meta["relative_sector"] == "WALL-LIMIT_SECTOR"
    assert post_meta["metric_status"] == "CONSTRUCTIVE_APPROXIMATION"
    assert post_meta["x"] == geometry["long_outer_edge"]["x"]

    wall_y = geometry["longitudinal_ends"]["WALL-LIMIT-END"]["y"]
    module003_y = geometry["longitudinal_ends"]["MODULE003-END"]["y"]
    assert post_meta["y"] - wall_y < module003_y - post_meta["y"]

    post_cells = cells(post)
    beam_z = post_meta["z"][1]
    for z in range(0, beam_z):
        assert (post_meta["x"], post_meta["y"], z) in post_cells

    assert module["metadata"]["constructive_supports"]["added"] == []
    assert module["metadata"]["constructive_supports"]["hidden_supports"] == "UNKNOWN_NOT_INVENTED"


def test_065_unknown_terminal_angle_is_not_promoted_to_observed_right_angle() -> None:
    module, _model, _parts = model_parts()
    terminal = module["metadata"]["geometry"]["terminal_edge"]

    assert terminal["topology_status"] == "SUPPORTED"
    assert terminal["angle_observability"] == "UNKNOWN"
    assert terminal["implementation"] == "ORTHOGONAL_COARSE_CONSTRUCTIVE_APPROXIMATION_ONLY"
    assert terminal["observed_right_angle"] is False


def test_065_footprint_rectangle_requires_closed_edge_evidence() -> None:
    module, _model, _parts = model_parts()
    evidence = module["metadata"]["geometry"]["footprint_evidence"]

    assert evidence["wall_limit_terminal_closure"] == "SUPPORTED_TOPOLOGY"
    assert evidence["terminal_angle_observability"] == "UNKNOWN"
    assert evidence["rectangularity_observability"] == "AMBIGUOUS"
    assert evidence["photographic_rectangle_claim"] is False
    assert evidence["constructive_implementation_shape"] == "RECTANGULAR_ORTHOGONAL_APPROXIMATION"


def test_065_module004_is_collision_free_and_uses_approved_orthogonal_primitives() -> None:
    source = load(SOURCE)
    module, model, parts = model_parts()
    bill = BillOfMaterials.model_validate(module["bom"])

    assert bill.total_parts == len(parts)
    assert len({part.placement_id for part in parts}) == len(parts)

    registry = create_current_engine_capability_registry(MASTER)
    validate_model_part_capabilities(model, registry)
    for line in bill.lines:
        assert registry.get(line.part_id).stage >= PieceCapabilityStage.PLACEMENT_APPROVED

    occupied: set[tuple[int, int, int]] = set()
    for part in parts:
        current = part_cells(part)
        assert occupied.isdisjoint(current), part.placement_id
        occupied.update(current)

    source_model = BrickModel.model_validate(source["brick_model"])
    assert occupied.isdisjoint(cells(source_model.parts))
