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


def test_module005_has_11_constructed_openings() -> None:
    opening = rasters()
    assert module5()["opening_count"] == 11
    assert set(opening) == {
        "OPENING_001", "OPENING_002", "OPENING_003", "OPENING_004",
        "OPENING_005", "OPENING_006", "OPENING_007", "OPENING_009",
        "OPENING_010", "OPENING_011", "OPENING_012",
    }


def test_ambiguous_b10_is_not_constructed() -> None:
    data = module5()
    assert data["opening_candidate_b10"]["status"] == "AMBIGUOUS_NOT_CONSTRUCTED"
    assert data["opening_candidate_b10"]["constructed"] is False
    assert "OPENING_CANDIDATE_B10" not in rasters()


def test_opening_006_reaches_architectural_base() -> None:
    opening = rasters()["OPENING_006"]
    grid = opening["wall_local_grid"]
    assert grid["z_bricks"] == 0
    assert opening["bottom_photo_status"] == "OBSERVED_TO_BASE"


def test_opening_005_is_short_and_elevated_above_base() -> None:
    opening = rasters()
    five = opening["OPENING_005"]
    five_grid = five["wall_local_grid"]
    three_grid = opening["OPENING_003"]["wall_local_grid"]
    assert five["height_class"] == "SHORT"
    assert five["bottom_relation"] == "ELEVATED_ABOVE_ARCHITECTURAL_BASE"
    assert five_grid["z_bricks"] > 0
    assert five_grid["height_bricks"] < three_grid["height_bricks"]
    assert 2 * five_grid["x_studs"] + five_grid["width_studs"] == 29


def test_face_b_has_one_certain_upper_opening() -> None:
    data = module5()["constraint_translation"]
    assert data["face_b_certain_upper_openings"] == ["OPENING_007"]
    assert data["face_b_certain_low_openings"] == ["OPENING_009"]


def test_rejected_opening_008_is_not_constructed_on_face_b() -> None:
    data = module5()
    rejected = data["rejected_openings"]["OPENING_008"]
    assert rejected["status"] == "REJECTED_AS_FACE_B_OPENING"
    assert rejected["constructed"] is False
    assert rejected["relocated"] is False
    assert "OPENING_008" not in rasters()


def test_opening_009_terrain_occlusion_does_not_certify_sill() -> None:
    opening = rasters()["OPENING_009"]
    assert opening["terrain_occlusion_approximation"] == "CONSTRUCTIVE_APPROXIMATION_DUE_TO_TERRAIN_OCCLUSION"
    assert opening["exact_sill_photo_status"] == "NOT_OBSERVABLE"
    assert opening["visible_terrain_edge_is_certified_sill"] is False


def test_opening_011_extends_toward_circulation_level() -> None:
    opening = rasters()["OPENING_011"]
    grid = opening["wall_local_grid"]
    bottom_plates = grid["z_bricks"] * 3
    assert opening["type"] == "PROBABLE_DOOR_OR_TALL_ACCESS_OPENING"
    assert opening["bottom_relation"] == "TOWARD_MODULE003_CIRCULATION_LEVEL"
    assert opening["approximation"] == "CONSTRUCTIVE_APPROXIMATION_WITH_PHOTO_SUPPORTED_CONTINUITY"
    assert abs(bottom_plates - opening["module003_circulation_level_plates"]) <= 1


def test_opening_011_exact_sill_remains_uncertain() -> None:
    opening = rasters()["OPENING_011"]
    assert opening["exact_sill_photo_status"] == "NOT_OBSERVABLE"
    assert opening["exact_door_geometry_observed"] is False
    assert "EXACT_SILL" in opening["unknown_photo_components"]


def test_untargeted_opening_rasters_are_unchanged_from_072() -> None:
    opening = rasters()
    expected = {
        "OPENING_001": (10, 32, 9, 11),
        "OPENING_002": (35, 32, 11, 11),
        "OPENING_003": (10, 18, 9, 10),
        "OPENING_004": (35, 18, 11, 10),
        "OPENING_007": (40, 28, 9, 9),
        "OPENING_010": (40, 32, 7, 10),
        "OPENING_012": (9, 15, 10, 12),
    }
    for opening_id, values in expected.items():
        grid = opening[opening_id]["wall_local_grid"]
        assert (grid["x_studs"], grid["z_bricks"], grid["width_studs"], grid["height_bricks"]) == values


def test_openings_are_negative_space_not_decorative_overlays() -> None:
    output = load(OUTPUT)
    data = output["metadata"]["module_005"]
    assert data["negative_space"]["implementation"] == "REAL_WALL_MATERIAL_REMOVAL_AND_RETILING"
    assert data["negative_space"]["decorative_overlay"] is False
    assert data["opening_surrounds"]["constructed_in_074"] is False
    assert data["terrain"]["constructed_in_074"] is False
    assert data["module_005_piece_count"] == 0

    parts = output["brick_model"]["parts"]
    frame = {
        "front_x0": 24,
        "front_y": 1,
        "left_x": 24,
        "right_x": 80,
        "side_y0": 2,
    }
    occupied = _cells([part for part in parts if _module1(part) and part["z_plates"] < 138])
    for item in rasters().values():
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


def test_module001_outside_current_opening_voids_preserved() -> None:
    source = load(SOURCE)
    output = load(OUTPUT)
    before = _cells([part for part in source["brick_model"]["parts"] if _module1(part)])
    after = _cells([part for part in output["brick_model"]["parts"] if _module1(part)])
    removed = before - after
    added = after - before
    assert added == set()
    assert removed
    assert len(removed) == output["metadata"]["module_005"]["negative_space"]["blocked_wall_cells"]
