#!/usr/bin/env python3
"""Build MODULE005 true negative-space openings in the frozen MODULE001 walls.

Mission 074 applies only the accepted blind-recovery corrections from 073 to
the technically green 072 state. Architecture is not re-inferred here.
Photographic constraints remain distinct from exact LEGO grid choices.
"""
from __future__ import annotations

import json
from pathlib import Path

from brickhouse.bricks.bom import generate_bom
from brickhouse.bricks.brick_model import BrickModel
from brickhouse.bricks.placement import WallOpeningGrid, generate_wall_layout_with_openings

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "frontend" / "module-001-plus-module-002-plus-module-003-plus-module-004-export.json"
COMBINED_OUT = ROOT / "frontend" / "module-001-plus-module-002-plus-module-003-plus-module-004-plus-module-005-export.json"

BUILDING_ID = "real-house-progressive"
COMBINED_VOLUME_ID = "module-001-plus-module-002-plus-module-003-plus-module-004-plus-module-005"
WALL_BRICK_COURSES = 46  # z=0..137; existing Z138/Z139 closure remains untouched.

FACE_MAPPING = {
    "FACE_A": "front",
    "FACE_B": "right",
    "FACE_C": "left",
}

PART_DIMS = {
    "BRICK_1X1": (1, 1, 3),
    "BRICK_1X2": (1, 2, 3),
    "BRICK_1X3": (1, 3, 3),
    "BRICK_1X4": (1, 4, 3),
    "BRICK_1X6": (1, 6, 3),
    "BRICK_1X8": (1, 8, 3),
}

# Accepted 070/071 map with only the targeted 073 recovery applied:
# - 006 reaches architectural base,
# - 005 is short and elevated,
# - 008 is rejected from FACE_B and not relocated,
# - 009 sill remains terrain-occlusion-uncertain,
# - 011 extends toward MODULE003 circulation level with uncertain exact sill.
OPENINGS = {
    "OPENING_001": {"face": "FACE_A", "type": "WINDOW", "x_studs": 10, "z_bricks": 32, "width_studs": 9, "height_bricks": 11},
    "OPENING_002": {"face": "FACE_A", "type": "WINDOW", "x_studs": 35, "z_bricks": 32, "width_studs": 11, "height_bricks": 11},
    "OPENING_003": {"face": "FACE_A", "type": "WINDOW", "x_studs": 10, "z_bricks": 18, "width_studs": 9, "height_bricks": 10},
    "OPENING_004": {"face": "FACE_A", "type": "WINDOW", "x_studs": 35, "z_bricks": 18, "width_studs": 11, "height_bricks": 10},
    "OPENING_005": {
        "face": "FACE_A", "type": "SMALL_LOW_OPENING",
        "x_studs": 12, "z_bricks": 8, "width_studs": 5, "height_bricks": 6,
        "height_class": "SHORT",
        "bottom_relation": "ELEVATED_ABOVE_ARCHITECTURAL_BASE",
        "recovery_status": "PHOTO_CONSTRAINED_073",
    },
    "OPENING_006": {
        "face": "FACE_A", "type": "LARGE_GLAZED_OPENING",
        "x_studs": 34, "z_bricks": 0, "width_studs": 13, "height_bricks": 14,
        "bottom_photo_status": "OBSERVED_TO_BASE",
        "recovery_status": "PHOTO_CONSTRAINED_073",
    },
    "OPENING_007": {"face": "FACE_B", "type": "WINDOW", "x_studs": 40, "z_bricks": 28, "width_studs": 9, "height_bricks": 9},
    "OPENING_009": {
        "face": "FACE_B", "type": "GLASS_BLOCK_OPENING",
        "x_studs": 44, "z_bricks": 2, "width_studs": 9, "height_bricks": 13,
        "terrain_occlusion_approximation": "CONSTRUCTIVE_APPROXIMATION_DUE_TO_TERRAIN_OCCLUSION",
        "exact_sill_photo_status": "NOT_OBSERVABLE",
        "visible_terrain_edge_is_certified_sill": False,
        "recovery_status": "PHOTO_CONSTRAINED_073",
    },
    "OPENING_010": {"face": "FACE_C", "type": "WINDOW", "x_studs": 40, "z_bricks": 32, "width_studs": 7, "height_bricks": 10},
    "OPENING_011": {
        "face": "FACE_C",
        "type": "PROBABLE_DOOR_OR_TALL_ACCESS_OPENING",
        "x_studs": 40,
        "z_bricks": 16,
        "width_studs": 7,
        "height_bricks": 11,
        "approximation": "CONSTRUCTIVE_APPROXIMATION_WITH_PHOTO_SUPPORTED_CONTINUITY",
        "exact_sill_photo_status": "NOT_OBSERVABLE",
        "bottom_relation": "TOWARD_MODULE003_CIRCULATION_LEVEL",
        "module003_circulation_level_plates": 49,
        "constructive_bottom_plates": 48,
        "exact_door_geometry_observed": False,
        "unknown_photo_components": ["EXACT_SILL", "EXACT_HEIGHT", "EXACT_DOOR_GEOMETRY"],
        "recovery_status": "PHOTO_SUPPORTED_CONTINUITY_073",
    },
    "OPENING_012": {
        "face": "FACE_C", "type": "LARGE_GLAZED_OPENING", "x_studs": 9, "z_bricks": 15, "width_studs": 10, "height_bricks": 12,
        "approximation": "CONSTRUCTIVE_APPROXIMATION_DUE_TO_OCCLUSION",
        "visible_occluder_is_certified_sill": False,
        "unknown_photo_components": ["ACTUAL_BOTTOM", "ACTUAL_HEIGHT"],
    },
}

REJECTED_OPENINGS = {
    "OPENING_008": {
        "previous_face": "FACE_B",
        "status": "REJECTED_AS_FACE_B_OPENING",
        "constructed": False,
        "relocated": False,
        "source": "BOLDUNGO-073-MODULE005-HUMAN-FAIL-BLIND-RECOVERY",
    },
}

RELATIVE_RANGES = {
    "OPENING_001": {"left": [0.16, 0.20], "right": [0.32, 0.36], "bottom": [0.66, 0.72], "top": [0.90, 0.95]},
    "OPENING_002": {"left": [0.60, 0.64], "right": [0.78, 0.82], "bottom": [0.67, 0.73], "top": [0.91, 0.96]},
    "OPENING_003": {"left": [0.15, 0.19], "right": [0.31, 0.35], "bottom": [0.36, 0.42], "top": [0.56, 0.62]},
    "OPENING_004": {"left": [0.59, 0.63], "right": [0.79, 0.83], "bottom": [0.35, 0.41], "top": [0.57, 0.63]},
    "OPENING_005": {"status": "SUPERSEDED_BY_073_SHORT_ELEVATED_RECOVERY", "top_relation": "APPROX_COMPARABLE_TO_OPENING_006"},
    "OPENING_006": {"bottom": "OBSERVED_TO_BASE_073", "top": "PRESERVE_072_COARSE_HEAD_LEVEL"},
    "OPENING_007": {"left": [0.55, 0.65], "right": [0.68, 0.77], "bottom": [0.56, 0.65], "top": [0.75, 0.84]},
    "OPENING_009": {"bottom": "NOT_OBSERVABLE_DUE_TO_RISING_TERRAIN_073", "visible_portion": "TRUNCATED_BY_RISING_TERRAIN"},
    "OPENING_010": {"left": [0.07, 0.12], "right": [0.19, 0.24], "bottom": [0.64, 0.71], "top": [0.85, 0.92]},
    "OPENING_011": {"bottom": "PROBABLY_TO_CIRCULATION_LEVEL_073", "continuity": "SUPPORTED_PROBABLE", "exact_sill": "NOT_OBSERVABLE"},
    "OPENING_012": {"left": [0.59, 0.65], "right": [0.77, 0.84], "bottom": [0.27, 0.42], "top": [0.52, 0.62]},
}


def _module1(part: dict) -> bool:
    return part["placement_id"].startswith("module-001-b57-")


def _actual_dims(part: dict) -> tuple[int, int, int]:
    width = part.get("width_studs")
    length = part.get("length_studs")
    height = part.get("height_plates")
    if width is None or length is None or height is None:
        width, length, height = PART_DIMS[part["part_id"]]
    if part["rotation_quarter_turns"] % 2:
        width, length = length, width
    return int(width), int(length), int(height)


def _cells(parts: list[dict], *, z_limit: int | None = None) -> set[tuple[int, int, int]]:
    occupied: set[tuple[int, int, int]] = set()
    for part in parts:
        width, length, height = _actual_dims(part)
        z_end = part["z_plates"] + height
        if z_limit is not None:
            z_end = min(z_end, z_limit)
        for x in range(part["x_studs"], part["x_studs"] + width):
            for y in range(part["y_studs"], part["y_studs"] + length):
                for z in range(part["z_plates"], z_end):
                    if z_limit is None or z < z_limit:
                        occupied.add((x, y, z))
    return occupied


def _target_lower_wall(part: dict) -> bool:
    return (
        _module1(part)
        and part.get("component") == "wall"
        and part.get("facade") in {"front", "left", "right"}
        and part["z_plates"] < WALL_BRICK_COURSES * 3
    )


def _infer_host_frame(parts: list[dict]) -> dict:
    targets = [part for part in parts if _target_lower_wall(part)]
    at_ground = [part for part in targets if part["z_plates"] == 0]

    front = [part for part in at_ground if part["facade"] == "front"]
    left = [part for part in at_ground if part["facade"] == "left"]
    right = [part for part in at_ground if part["facade"] == "right"]
    if not front or not left or not right:
        raise RuntimeError("MODULE001 target facade wall geometry is incomplete")

    front_cells = _cells(front, z_limit=1)
    left_cells = _cells(left, z_limit=1)
    right_cells = _cells(right, z_limit=1)

    frame = {
        "front_x0": min(x for x, _y, _z in front_cells),
        "front_x1": max(x for x, _y, _z in front_cells) + 1,
        "front_y": min(y for _x, y, _z in front_cells),
        "left_x": min(x for x, _y, _z in left_cells),
        "right_x": max(x for x, _y, _z in right_cells),
        "side_y0": min(y for _x, y, _z in left_cells),
        "side_y1": max(y for _x, y, _z in left_cells) + 1,
    }
    if frame["front_x1"] - frame["front_x0"] != 57:
        raise RuntimeError(f"unexpected MODULE001 front width: {frame}")
    if frame["side_y1"] - frame["side_y0"] != 69:
        raise RuntimeError(f"unexpected MODULE001 side-wall width: {frame}")
    if frame["left_x"] == frame["right_x"]:
        raise RuntimeError(f"MODULE001 left/right planes collapsed: {frame}")
    return frame


def _opening_grids(face_label: str) -> list[WallOpeningGrid]:
    return [
        WallOpeningGrid(
            id=opening_id,
            x_studs=data["x_studs"],
            z_bricks=data["z_bricks"],
            width_studs=data["width_studs"],
            height_bricks=data["height_bricks"],
        )
        for opening_id, data in OPENINGS.items()
        if data["face"] == face_label
    ]


def _emit_wall(face_label: str, frame: dict) -> list[dict]:
    facade = FACE_MAPPING[face_label]
    width = 57 if facade == "front" else 69
    layout = generate_wall_layout_with_openings(width, WALL_BRICK_COURSES, _opening_grids(face_label))
    out: list[dict] = []

    for index, placement in enumerate(layout.placements, start=1):
        base_width, base_length, height = PART_DIMS[placement.brick_id]
        if facade == "front":
            x = frame["front_x0"] + placement.x_studs
            y = frame["front_y"]
            rotation = placement.rotation_quarter_turns
        else:
            x = frame[f"{facade}_x"]
            y = frame["side_y0"] + placement.x_studs
            rotation = 0

        out.append({
            "placement_id": f"module-001-b57-m005-{facade}-{index:06d}",
            "part_id": placement.brick_id,
            "category": "brick",
            "component": "wall",
            "x_studs": x,
            "y_studs": y,
            "z_plates": placement.z_plates,
            "rotation_quarter_turns": rotation,
            "facade": facade,
            "roof_side": None,
            "opening_id": None,
            "trim_role": None,
            "semantic_color": None,
            "width_studs": base_width,
            "length_studs": base_length,
            "height_plates": height,
        })
    return out


def _world_opening_cells(frame: dict) -> set[tuple[int, int, int]]:
    blocked: set[tuple[int, int, int]] = set()
    for data in OPENINGS.values():
        facade = FACE_MAPPING[data["face"]]
        z0 = data["z_bricks"] * 3
        z1 = (data["z_bricks"] + data["height_bricks"]) * 3
        if facade == "front":
            xs = range(frame["front_x0"] + data["x_studs"], frame["front_x0"] + data["x_studs"] + data["width_studs"])
            ys = range(frame["front_y"], frame["front_y"] + 1)
        else:
            xs = range(frame[f"{facade}_x"], frame[f"{facade}_x"] + 1)
            ys = range(frame["side_y0"] + data["x_studs"], frame["side_y0"] + data["x_studs"] + data["width_studs"])
        for x in xs:
            for y in ys:
                for z in range(z0, z1):
                    blocked.add((x, y, z))
    return blocked


def _opening_metadata(frame: dict) -> list[dict]:
    items = []
    for opening_id, data in OPENINGS.items():
        facade = FACE_MAPPING[data["face"]]
        item = {
            "opening_id": opening_id,
            "face_label": data["face"],
            "host_facade": facade,
            "type": data["type"],
            "photo_relative_constraint": RELATIVE_RANGES[opening_id],
            "wall_local_grid": {
                "x_studs": data["x_studs"],
                "z_bricks": data["z_bricks"],
                "width_studs": data["width_studs"],
                "height_bricks": data["height_bricks"],
                "status": "CONSTRUCTIVE_APPROXIMATION_074",
            },
            "provenance": {
                "base_identity": "PHOTO_CONSTRAINED_070",
                "base_relative_geometry": "PHOTO_CONSTRAINED_071",
                "targeted_recovery": data.get("recovery_status"),
                "exact_grid_selection": "CONSTRUCTIVE_APPROXIMATION_074",
            },
        }
        for key in (
            "height_class",
            "bottom_relation",
            "bottom_photo_status",
            "terrain_occlusion_approximation",
            "exact_sill_photo_status",
            "visible_terrain_edge_is_certified_sill",
            "approximation",
            "module003_circulation_level_plates",
            "constructive_bottom_plates",
            "exact_door_geometry_observed",
            "unknown_photo_components",
        ):
            if key in data:
                item[key] = data[key]
        if opening_id == "OPENING_012":
            item["visible_occluder_is_certified_sill"] = False
        items.append(item)
    return items


def main() -> None:
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    source_parts = source["brick_model"]["parts"]
    frame = _infer_host_frame(source_parts)

    removed = [part for part in source_parts if _target_lower_wall(part)]
    kept = [dict(part) for part in source_parts if not _target_lower_wall(part)]
    rebuilt = (
        _emit_wall("FACE_A", frame)
        + _emit_wall("FACE_B", frame)
        + _emit_wall("FACE_C", frame)
    )

    source_cells = _cells(removed, z_limit=WALL_BRICK_COURSES * 3)
    rebuilt_cells = _cells(rebuilt, z_limit=WALL_BRICK_COURSES * 3)
    blocked = _world_opening_cells(frame)
    expected = source_cells - blocked
    if rebuilt_cells != expected:
        missing = len(expected - rebuilt_cells)
        extra = len(rebuilt_cells - expected)
        raise RuntimeError(f"MODULE005 wall occupancy mismatch: missing={missing} extra={extra}")
    if rebuilt_cells.intersection(blocked):
        raise RuntimeError("MODULE005 negative space contains wall material")

    combined_parts = kept + rebuilt
    model_data = dict(source["brick_model"])
    model_data["volume_id"] = COMBINED_VOLUME_ID
    model_data["parts"] = combined_parts
    combined_model = BrickModel.model_validate(model_data)

    module1_before = [part for part in source_parts if _module1(part)]
    module1_after = [part for part in combined_parts if _module1(part)]

    module5 = {
        "module_id": "MODULE_005_OPENINGS",
        "mission": "BOLDUNGO-074-MODULE005-TARGETED-HUMAN-FAIL-RECOVERY",
        "recovery_source": "BOLDUNGO-073-MODULE005-HUMAN-FAIL-BLIND-RECOVERY",
        "structure_type": "NEGATIVE_SPACE_OPENINGS_CUT_IN_EXISTING_MODULE001_WALLS",
        "face_mapping": FACE_MAPPING,
        "opening_count": len(OPENINGS),
        "opening_candidate_b10": {
            "status": "AMBIGUOUS_NOT_CONSTRUCTED",
            "constructed": False,
        },
        "rejected_openings": REJECTED_OPENINGS,
        "opening_rasters": _opening_metadata(frame),
        "constraint_translation": {
            "policy": "TARGETED_073_RECOVERY_ONLY",
            "face_a_centerlines": {
                "left": ["OPENING_001", "OPENING_003", "OPENING_005"],
                "right": ["OPENING_002", "OPENING_004", "OPENING_006"],
            },
            "face_b_certain_upper_openings": ["OPENING_007"],
            "face_b_certain_low_openings": ["OPENING_009"],
            "face_b_rejected": ["OPENING_008"],
            "opening_009_terrain_rule": "TERRAIN_OCCLUSION_DOES_NOT_CERTIFY_SILL",
            "opening_011_continuity": "PHOTO_SUPPORTED_PROBABLE_TO_MODULE003_CIRCULATION_LEVEL",
            "ground_slope_is_not_opening_level": True,
        },
        "negative_space": {
            "implementation": "REAL_WALL_MATERIAL_REMOVAL_AND_RETILING",
            "decorative_overlay": False,
            "blocked_wall_cells": len(blocked),
        },
        "opening_surrounds": {
            "observed": True,
            "different_appearance": True,
            "relief_observed": "AMBIGUOUS",
            "constructed_in_074": False,
            "policy": "STRUCTURAL_VOID_FIRST",
        },
        "terrain": {
            "constructed_in_074": False,
        },
        "preservation": {
            "module_001_outside_targeted_areas": "OCCUPIED_GEOMETRY_PRESERVED",
            "untargeted_opening_rasters": ["OPENING_001", "OPENING_002", "OPENING_003", "OPENING_004", "OPENING_007", "OPENING_010", "OPENING_012"],
            "module_002": "BYTE_EQUIVALENT_PART_RECORDS",
            "module_003": "BYTE_EQUIVALENT_PART_RECORDS",
            "module_004": "BYTE_EQUIVALENT_PART_RECORDS",
        },
        "module_005_piece_count": 0,
        "module_005_piece_count_note": "MODULE005 remains negative-space geometry and adds no decorative surround or terrain parts.",
        "module_001_piece_count_before": len(module1_before),
        "module_001_piece_count_after": len(module1_after),
        "replaced_module_001_lower_wall_parts_before": len(removed),
        "replaced_module_001_lower_wall_parts_after": len(rebuilt),
    }

    metadata = {
        **source.get("metadata", {}),
        "module_id": "MODULE_001_PLUS_MODULE_002_PLUS_MODULE_003_PLUS_MODULE_004_PLUS_MODULE_005",
        "mission_module_005": "BOLDUNGO-074-MODULE005-TARGETED-HUMAN-FAIL-RECOVERY",
        "source_bundle_module_001_002_003_004": SOURCE.name,
        "source_piece_count": len(source_parts),
        "combined_piece_count": len(combined_parts),
        "module_005": module5,
    }

    issues = [
        *source.get("fidelity_issues", []),
        {
            "code": "MODULE_005_TARGETED_RECOVERY_GRID_APPROXIMATION",
            "severity": "info",
            "object_id": COMBINED_VOLUME_ID,
            "message": "074 changes only the four sectors recovered by blind audit 073; exact grid choices remain constructive approximations.",
        },
        {
            "code": "MODULE_005_OPENING_009_TERRAIN_OCCLUDED_SILL",
            "severity": "info",
            "object_id": "OPENING_009",
            "message": "The rising terrain truncates the visible lower portion; exact architectural sill remains unobserved and terrain is not built in 074.",
        },
        {
            "code": "MODULE_005_OPENING_011_EXACT_SILL_UNCERTAIN",
            "severity": "info",
            "object_id": "OPENING_011",
            "message": "Photo fragments support continuity toward circulation level, but exact sill and exact door geometry remain unobserved.",
        },
        {
            "code": "MODULE_005_OPENING_012_OCCLUDED_BOTTOM_UNKNOWN",
            "severity": "info",
            "object_id": "OPENING_012",
            "message": "Terrace/railing occlusion does not certify the visible cutoff as the opening sill; 072 coarse placement is preserved.",
        },
    ]

    output = {
        "schema_version": source["schema_version"],
        "building_id": BUILDING_ID,
        "volume_id": COMBINED_VOLUME_ID,
        "metadata": metadata,
        "appearance": source.get("appearance"),
        "brick_model": combined_model.model_dump(mode="json"),
        "bom": generate_bom(combined_model).model_dump(mode="json"),
        "assembly_plan": source.get("assembly_plan"),
        "instruction_plan": source.get("instruction_plan"),
        "bag_plan": source.get("bag_plan"),
        "fidelity_issues": issues,
        "capability_summary": source.get("capability_summary"),
    }
    COMBINED_OUT.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(json.dumps({
        "combined_piece_count": len(combined_parts),
        "module_005_piece_count": 0,
        "opening_count": len(OPENINGS),
        "module_001_piece_count_before": len(module1_before),
        "module_001_piece_count_after": len(module1_after),
        "removed_wall_parts": len(removed),
        "rebuilt_wall_parts": len(rebuilt),
        "face_mapping": FACE_MAPPING,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
