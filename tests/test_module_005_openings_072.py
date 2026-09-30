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


def grid(opening_id: str) -> dict:
    return rasters()[opening_id]["wall_local_grid"]


def test_module005_keeps_11_constructed_openings() -> None:
    assert module5()["opening_count"] == 11
    assert set(rasters()) == {
        "OPENING_001", "OPENING_002", "OPENING_003", "OPENING_004",
        "OPENING_005", "OPENING_006", "OPENING_007", "OPENING_009",
        "OPENING_010", "OPENING_011", "OPENING_012",
    }


def test_case_a_common_bay_moves_as_one_rigid_system() -> None:
    data = module5()["correction_077"]["case_a"]
    ten = grid("OPENING_010")
    eleven = grid("OPENING_011")
    assert data["implemented"] is True
    assert data["old_x_studs"] == {"OPENING_010": 40, "OPENING_011": 40}
    assert data["translation_delta_studs"] == 12
    assert ten["x_studs"] == eleven["x_studs"] == data["new_x_studs"] == 52
    assert ten["width_studs"] == eleven["width_studs"] == 7
    assert data["exact_target_x"] == "APPROXIMATED"


def test_case_a_new_bay_is_inside_module003_interface_sector() -> None:
    data = module5()["correction_077"]["case_a"]
    side_y0, side_y1 = data["host_side_world_y"]
    sector_y0, sector_y1 = data["module003_interface_world_y"]
    opening_x = data["new_x_studs"]
    width = grid("OPENING_010")["width_studs"]
    world_start = side_y0 + opening_x
    world_end = world_start + width
    assert data["admissible_wall_local_x_studs"][0] <= opening_x <= data["admissible_wall_local_x_studs"][1]
    assert world_start >= sector_y0
    assert world_end <= min(sector_y1, side_y1)
    assert data["selection_rule"].startswith("MINIMAL_RIGID_TRANSLATION")


def test_case_a_vertical_geometry_is_preserved() -> None:
    assert (grid("OPENING_010")["z_bricks"], grid("OPENING_010")["height_bricks"]) == (32, 10)
    assert (grid("OPENING_011")["z_bricks"], grid("OPENING_011")["height_bricks"]) == (16, 11)


def test_case_d_opening_007_moves_into_upper_story_without_dimension_change() -> None:
    data = module5()["correction_077"]["case_d"]
    seven = grid("OPENING_007")
    assert data["implemented"] is True
    assert data["old_z_bricks"] == 28
    assert data["new_z_bricks"] == seven["z_bricks"] == 32
    assert data["admissible_z_bricks"] == [32, 34]
    assert data["upper_story_membership"] == "PHOTO_RECOVERED"
    assert data["exact_target_z"] == "APPROXIMATED"
    assert seven["width_studs"] == 9
    assert seven["height_bricks"] == 9
    assert data["width_before_after"] == [9, 9]
    assert data["height_before_after"] == [9, 9]
    assert data["same_exact_sill_claimed"] is False
    assert data["same_exact_head_claimed"] is False


def test_case_b_and_case_c_geometry_unchanged_from_074() -> None:
    expected = {
        "OPENING_001": (10, 32, 9, 11),
        "OPENING_002": (35, 32, 11, 11),
        "OPENING_003": (10, 18, 9, 10),
        "OPENING_004": (35, 18, 11, 10),
        "OPENING_005": (12, 8, 5, 6),
        "OPENING_006": (34, 0, 13, 14),
        "OPENING_009": (44, 2, 9, 13),
        "OPENING_012": (9, 15, 10, 12),
    }
    for opening_id, values in expected.items():
        item = grid(opening_id)
        assert (item["x_studs"], item["z_bricks"], item["width_studs"], item["height_bricks"]) == values
    assert module5()["preservation"]["case_b_changed"] is False
    assert module5()["preservation"]["case_c_changed"] is False


def test_case_e_engine_limitation_is_explicit_and_no_solidity_is_claimed() -> None:
    data = module5()["correction_077"]["case_e"]
    assert data["engine_capable"] is False
    assert data["implemented"] is False
    assert data["representation"] == "ENGINE_LIMITATION_PREVENTS_HONEST_STEP_REPRESENTATION"
    assert data["topology"] == "PHOTO_PARTIALLY_RECOVERED"
    assert data["solidity"] == "NOT_OBSERVABLE"
    assert data["photo_recovered_solid_step"] is False
    assert module5()["module_005_piece_count"] == 0


def test_general_076_rules_are_canonized_in_077_evidence_metadata() -> None:
    assert set(module5()["general_rules_canonized"]) == {
        "PHOTO-CONSTRAINT-PLUS-CURRENT-VIOLATION-BEFORE-CORRECTION",
        "RELATIONAL-RECOVERY-DOES-NOT-IMPLY-EXACT-TARGET",
        "COMMON-BAY-MUST-MOVE-AS-A-SYSTEM",
        "STORY-BAND-CAN-CONSTRAIN-LEVEL-WITHOUT-CERTIFYING-SILL",
        "FAMILY-COMPATIBILITY-DOES-NOT-MEAN-DIMENSION-EQUALITY",
        "TOPOLOGY-CAN-BE-PHOTO-RECOVERED-WHILE-SOLIDITY-REMAINS-UNKNOWN",
        "HUMAN-GROUND-TRUTH-OVERRIDE-MUST-REMAIN-LABELED",
    }


def test_openings_remain_negative_space_not_decorative_overlays() -> None:
    output = load(OUTPUT)
    data = output["metadata"]["module_005"]
    assert data["negative_space"]["implementation"] == "REAL_WALL_MATERIAL_REMOVAL_AND_RETILING"
    assert data["negative_space"]["decorative_overlay"] is False
    assert data["opening_surrounds"]["constructed_in_077"] is False
    assert data["terrain"]["constructed_in_077"] is False

    parts = output["brick_model"]["parts"]
    occupied = _cells([part for part in parts if _module1(part) and part["z_plates"] < 138])
    frame = {"front_x0": 24, "front_y": 1, "left_x": 24, "right_x": 80, "side_y0": 2}
    for item in rasters().values():
        g = item["wall_local_grid"]
        z0 = g["z_bricks"] * 3
        z1 = (g["z_bricks"] + g["height_bricks"]) * 3
        if item["host_facade"] == "front":
            xs = range(frame["front_x0"] + g["x_studs"], frame["front_x0"] + g["x_studs"] + g["width_studs"])
            ys = [frame["front_y"]]
        else:
            xs = [frame[f"{item['host_facade']}_x"]]
            ys = range(frame["side_y0"] + g["x_studs"], frame["side_y0"] + g["x_studs"] + g["width_studs"])
        assert all((x, y, z) not in occupied for x in xs for y in ys for z in range(z0, z1))


def test_module002_003_004_geometry_unchanged() -> None:
    source = load(SOURCE)
    output = load(OUTPUT)
    source_other = [part for part in source["brick_model"]["parts"] if not _module1(part)]
    output_other = [part for part in output["brick_model"]["parts"] if not _module1(part)]
    assert output_other == source_other


def test_module001_changes_only_as_required_by_current_opening_voids() -> None:
    source = load(SOURCE)
    output = load(OUTPUT)
    before = _cells([part for part in source["brick_model"]["parts"] if _module1(part)])
    after = _cells([part for part in output["brick_model"]["parts"] if _module1(part)])
    assert after - before == set()
    assert before - after
    assert len(before - after) == output["metadata"]["module_005"]["negative_space"]["blocked_wall_cells"]
