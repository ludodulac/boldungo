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


def model_parts() -> tuple[dict, BrickModel, list]:
    module = load(MODULE)
    model = BrickModel.model_validate(module["brick_model"])
    return module, model, model.parts


def test_061_source_modules_are_byte_equivalent_prefix_and_module004_is_new_domain() -> None:
    source = load(SOURCE)
    module = load(MODULE)
    combined = load(COMBINED)

    assert module["metadata"]["mission"] == "BOLDUNGO-063-MODULE004-HOST-FACE-CORRECTION"
    source_parts = source["brick_model"]["parts"]
    combined_parts = combined["brick_model"]["parts"]

    # MODULE001/002/003 are copied as an immutable prefix; only MODULE004 is appended.
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


def test_063_wood_terrace_host_face_identity_is_confirmed() -> None:
    source = load(SOURCE)
    module, _model, parts = model_parts()
    geometry = module["metadata"]["geometry"]
    deck = geometry["deck_footprint"]
    house = module["metadata"]["house_interface"]
    interface = module["metadata"]["module_003_interface"]

    assert deck["status"] == "COARSE_REFINABLE"
    assert deck["x"][1] == source["metadata"]["host_house_left_plane_x"]
    assert deck["y"][1] == source["metadata"]["geometry"]["upper_platform"]["y"][0]
    assert deck["walking_top_z"] == source["metadata"]["level_model"]["future_wood_terrace_interface_z"]
    assert house["host_face"] == "left"
    assert house["relation"] == "DECK_HOUSE_EDGE_ADJACENT_TO_LEFT_HOUSE_PLANE"
    assert house["corner_crossing_required"] is False
    assert interface["shared_host_face"] == "left"
    assert interface["corner_crossing_required"] is False

    floor = parts_with("deck-floor", parts)
    assert floor
    floor_cells = cells(floor)
    floor_z = deck["walking_top_z"] - 1
    for x in range(*deck["x"]):
        for y in range(*deck["y"]):
            assert (x, y, floor_z) in floor_cells
    assert all(z == floor_z for _x, _y, z in floor_cells)

def test_061_wood_terrace_primary_underspace_remains_open() -> None:
    module, _model, parts = model_parts()
    geometry = module["metadata"]["geometry"]
    void = geometry["primary_underspace"]
    deck = geometry["deck_footprint"]
    solid = cells(parts)

    assert void["classification"] == "MAJOR_OPEN_WOOD_TERRACE_UNDERSPACE"
    assert void["open_to_ground"] is True

    # WOOD_TERRACE_PRIMARY_UNDERSPACE_REMAINS_OPEN:
    # the declared interior volume below the deck contains no MODULE004 solids.
    for x in range(*void["x"]):
        for y in range(*void["y"]):
            for z in range(*void["z"]):
                assert (x, y, z) not in solid

    # It is a major under-space, not a narrow accidental slot.
    deck_width = deck["x"][1] - deck["x"][0]
    deck_depth = deck["y"][1] - deck["y"][0]
    void_width = void["x"][1] - void["x"][0]
    void_depth = void["y"][1] - void["y"][0]
    assert void_width / deck_width >= 0.90
    assert void_depth / deck_depth >= 0.80


def test_061_wood_terrace_remains_structurally_distinct_from_masonry_module003() -> None:
    source = load(SOURCE)
    module, _model, module_parts = model_parts()

    module003_raw = [
        raw for raw in source["brick_model"]["parts"]
        if raw["placement_id"].startswith("module-003-")
    ]
    module003 = [
        BrickModel.model_validate({
            "schema_version": "0.1",
            "building_id": source["building_id"],
            "volume_id": "temporary-module003-check",
            "width_studs": source["brick_model"]["width_studs"],
            "depth_studs": source["brick_model"]["depth_studs"],
            "height_plates": source["brick_model"]["height_plates"],
            "parts": module003_raw,
        }).parts
    ][0]

    # WOOD_TERRACE_REMAINS_STRUCTURALLY_DISTINCT_FROM_MASONRY_MODULE003:
    # the two systems may meet at a boundary but occupy no common 3-D cell.
    assert cells(module003).isdisjoint(cells(module_parts))

    interface = module["metadata"]["module_003_interface"]
    assert interface["relation"] == "SAME_LONGITUDINAL_LEFT_FACE_HIGH_LEVEL_NEIGHBORS_REMAIN_DISTINCT"
    assert interface["exact_connection"] == "NOT_OBSERVABLE_NOT_ENCODED"
    assert interface["wood_walking_top_z"] == source["metadata"]["level_model"]["future_wood_terrace_interface_z"]
    assert interface["masonry_walking_top_z"] == source["metadata"]["level_model"]["upper_masonry_platform_z"]


def test_061_railing_signature_is_preserved_after_host_face_rotation() -> None:
    module, _model, parts = model_parts()
    geometry = module["metadata"]["geometry"]
    deck = geometry["deck_footprint"]
    railing = geometry["railing"]
    outer_x = geometry["front_edge"]["x"]
    end_y = geometry["right_edge"]["y"]
    top_z = railing["top_z"]

    front_top = parts_with("railing-front-top", parts)
    right_top = parts_with("railing-right-top", parts)
    front_vertical = parts_with("railing-front-vertical", parts)
    right_vertical = parts_with("railing-right-vertical", parts)
    assert front_top and right_top and front_vertical and right_vertical

    front_cells = cells(front_top)
    right_cells = cells(right_top)
    for y in range(*deck["y"]):
        for z in range(top_z - 3, top_z):
            assert (outer_x, y, z) in front_cells
    for x in range(deck["x"][0] + 1, deck["x"][1]):
        for z in range(top_z - 3, top_z):
            assert (x, end_y, z) in right_cells

    assert len({part.y_studs for part in front_vertical}) >= 8
    assert len({part.x_studs for part in right_vertical}) >= 4
    assert module["metadata"]["railing_contract"]["house_edge"] == "NO_AUTOMATIC_RAILING"

def test_061_observed_supports_are_explicit_and_hidden_supports_not_invented() -> None:
    module, _model, parts = model_parts()
    geometry = module["metadata"]["geometry"]
    observed = module["metadata"]["observed_supports"]
    constructive = module["metadata"]["constructive_supports"]

    assert observed == {
        "front_rim_beam": "IMPLEMENTED",
        "right_rim_beam": "IMPLEMENTED",
        "front_vertical_post": "IMPLEMENTED_ONE_OBSERVED_POST",
        "diagonal_braces": "OBSERVED_NOT_IMPLEMENTED_ORTHOGONAL_ENGINE_CANNOT_REPRESENT_DIAGONAL_BEAM_HONESTLY",
    }
    assert constructive["added"] == []
    assert constructive["status"] == "NONE_ADDED"
    assert constructive["hidden_supports"] == "UNKNOWN_NOT_INVENTED"

    front_beam = parts_with("front-rim-beam", parts)
    right_beam = parts_with("right-rim-beam", parts)
    post = parts_with("observed-front-post", parts)
    assert front_beam and right_beam and post

    deck = geometry["deck_footprint"]
    front_y = geometry["front_edge"]["y"]
    right_x = geometry["right_edge"]["x"]
    beam_z = min(bounds(part)[4] for part in front_beam)

    front_beam_cells = cells(front_beam)
    for x in range(*deck["x"]):
        assert (x, front_y, beam_z) in front_beam_cells

    right_beam_cells = cells(right_beam)
    for y in range(deck["y"][0], front_y):
        assert (right_x, y, beam_z) in right_beam_cells

    px = geometry["observed_front_post"]["x"]
    py = geometry["observed_front_post"]["y"]
    post_cells = cells(post)
    for z in range(0, beam_z):
        assert (px, py, z) in post_cells


def test_061_module004_is_collision_free_and_uses_approved_orthogonal_primitives() -> None:
    source = load(SOURCE)
    module, model, parts = model_parts()
    bill = BillOfMaterials.model_validate(module["bom"])

    assert bill.total_parts == len(parts)
    assert len({part.placement_id for part in parts}) == len(parts)

    registry = create_current_engine_capability_registry(MASTER)
    validate_model_part_capabilities(model, registry)
    for line in bill.lines:
        assert registry.get(line.part_id).stage >= PieceCapabilityStage.PLACEMENT_APPROVED

    # Scene-native timber is outside the wall collision validator, so audit its
    # actual occupied cells explicitly.
    occupied: set[tuple[int, int, int]] = set()
    for part in parts:
        current = part_cells(part)
        assert occupied.isdisjoint(current), part.placement_id
        occupied.update(current)

    # MODULE004 must not penetrate any pre-existing source geometry.
    source_model = BrickModel.model_validate(source["brick_model"])
    assert occupied.isdisjoint(cells(source_model.parts))
