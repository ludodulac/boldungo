from __future__ import annotations

import json
from pathlib import Path

from brickhouse.bricks.catalog import standard_orthogonal_definitions

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "frontend" / "module-001-plus-module-002-plus-module-003-plus-module-004-export.json"
OUTPUT = ROOT / "frontend" / "module-001-plus-module-002-plus-module-003-plus-module-004-plus-module-005-export.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def module5() -> dict:
    return load(OUTPUT)["metadata"]["module_005"]


def rasters() -> dict[str, dict]:
    return {item["opening_id"]: item for item in module5()["opening_rasters"]}


def _dims(part: dict) -> tuple[int, int, int]:
    definitions = standard_orthogonal_definitions()
    definition = definitions.get(part["part_id"])
    if definition is not None:
        width, length = definition.footprint(part["rotation_quarter_turns"])
        return int(width), int(length), int(definition.height_plates)
    width = int(part["width_studs"])
    length = int(part["length_studs"])
    if part["rotation_quarter_turns"] % 2:
        width, length = length, width
    return width, length, int(part["height_plates"])


def _cells(parts: list[dict]) -> set[tuple[int, int, int]]:
    result = set()
    for part in parts:
        width, length, height = _dims(part)
        for x in range(part["x_studs"], part["x_studs"] + width):
            for y in range(part["y_studs"], part["y_studs"] + length):
                for z in range(part["z_plates"], part["z_plates"] + height):
                    result.add((x, y, z))
    return result


def _module1(part: dict) -> bool:
    return part["placement_id"].startswith("module-001-b57-")


def test_module005_has_12_constructed_openings() -> None:
    data = module5()
    assert data["opening_count"] == 12
    assert len(data["opening_rasters"]) == 12
    assert {item["opening_id"] for item in data["opening_rasters"]} == {
        f"OPENING_{index:03d}" for index in range(1, 13)
    }


def test_ambiguous_b10_is_not_constructed() -> None:
    data = module5()
    assert data["opening_candidate_b10"]["status"] == "AMBIGUOUS_NOT_CONSTRUCTED"
    assert data["opening_candidate_b10"]["constructed"] is False
    assert "OPENING_CANDIDATE_B10" not in rasters()


def test_face_a_has_two_persistent_opening_centerlines() -> None:
    opening = rasters()

    def doubled_center(opening_id: str) -> int:
        grid = opening[opening_id]["wall_local_grid"]
        return 2 * grid["x_studs"] + grid["width_studs"]

    assert {doubled_center(i) for i in ("OPENING_001", "OPENING_003", "OPENING_005")} == {29}
    assert {doubled_center(i) for i in ("OPENING_002", "OPENING_004", "OPENING_006")} == {81}


def test_face_a_low_openings_preserve_different_widths() -> None:
    opening = rasters()
    width = lambda opening_id: opening[opening_id]["wall_local_grid"]["width_studs"]
    assert width("OPENING_005") < width("OPENING_001")
    assert width("OPENING_006") > width("OPENING_002")
    assert width("OPENING_005") != width("OPENING_006")


def test_face_b_upper_openings_share_architectural_level() -> None:
    opening = rasters()
    seven = opening["OPENING_007"]["wall_local_grid"]
    eight = opening["OPENING_008"]["wall_local_grid"]
    assert seven["z_bricks"] == eight["z_bricks"]
    assert seven["height_bricks"] == eight["height_bricks"]


def test_glass_block_opening_009_exists_as_opening_entity() -> None:
    opening = rasters()["OPENING_009"]
    assert opening["type"] == "GLASS_BLOCK_OPENING"
    assert opening["provenance"]["identity_face_order_type"] == "PHOTO_CONSTRAINED_070"


def test_face_c_opening_011_retains_occlusion_approximation_provenance() -> None:
    opening = rasters()["OPENING_011"]
    assert opening["occlusion_approximation"] == "CONSTRUCTIVE_APPROXIMATION_DUE_TO_OCCLUSION"
    assert set(opening["unknown_photo_components"]) == {"BOTTOM", "ACTUAL_HEIGHT"}
    assert opening["photo_relative_range"]["bottom"] is None
    assert opening["provenance"]["exact_grid_selection"] == "CONSTRUCTIVE_APPROXIMATION_072"


def test_face_c_opening_012_does_not_use_visible_occluder_as_certified_sill() -> None:
    opening = rasters()["OPENING_012"]
    assert opening["visible_occluder_is_certified_sill"] is False
    assert opening["occlusion_approximation"] == "CONSTRUCTIVE_APPROXIMATION_DUE_TO_OCCLUSION"
    assert "ACTUAL_BOTTOM" in opening["unknown_photo_components"]


def test_openings_are_negative_space_not_decorative_overlays() -> None:
    output = load(OUTPUT)
    data = output["metadata"]["module_005"]
    assert data["negative_space"]["implementation"] == "REAL_WALL_MATERIAL_REMOVAL_AND_RETILING"
    assert data["negative_space"]["decorative_overlay"] is False
    assert data["module_005_piece_count"] == 0

    parts = output["brick_model"]["parts"]
    opening = rasters()
    frame = {
        "front_x0": 24,
        "front_y": 1,
        "left_x": 24,
        "right_x": 80,
        "side_y0": 2,
    }
    occupied = _cells([part for part in parts if _module1(part) and part["z_plates"] < 138])
    for item in opening.values():
        grid = item["wall_local_grid"]
        z0 = grid["z_bricks"] * 3
        z1 = (grid["z_bricks"] + grid["height_bricks"]) * 3
        if item["host_facade"] == "front":
            xs = range(frame["front_x0"] + grid["x_studs"], frame["front_x0"] + grid["x_studs"] + grid["width_studs"])
            ys = [frame["front_y"]]
        else:
            xs = [frame[f"{item['host_facade']}_x"]]
            ys = range(frame["side_y0"] + grid["x_studs"], frame["side_y0"] + grid["x_studs"] + grid["width_studs"])
        assert all((x, y, z) not in occupied for x in xs for y in ys for z in range(z0, z1))


def test_module002_003_004_geometry_unchanged() -> None:
    source = load(SOURCE)
    output = load(OUTPUT)
    source_other = [part for part in source["brick_model"]["parts"] if not _module1(part)]
    output_other = [part for part in output["brick_model"]["parts"] if not _module1(part)]
    assert output_other == source_other


def test_module001_outside_openings_preserved_as_occupied_geometry() -> None:
    source = load(SOURCE)
    output = load(OUTPUT)
    before = _cells([part for part in source["brick_model"]["parts"] if _module1(part)])
    after = _cells([part for part in output["brick_model"]["parts"] if _module1(part)])
    removed = before - after
    added = after - before
    assert added == set()
    assert removed
    assert len(removed) == output["metadata"]["module_005"]["negative_space"]["blocked_wall_cells"]
