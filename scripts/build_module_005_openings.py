#!/usr/bin/env python3
"""Build MODULE005 as true negative-space openings cut into existing MODULE001 walls.

Mission 072 translates the accepted 070 opening identities and 071 relative
geometry onto the frozen MODULE001 wall grid. It does not re-infer architecture.
Exact brick-grid coordinates selected inside accepted relative ranges are
constructive approximations and remain labelled as such.
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
WALL_BRICK_COURSES = 46  # z=0..137; existing Z138/Z139 plate closure remains untouched.

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

# Accepted 071 ranges resolved jointly, not as twelve independent rectangles.
# x_studs is wall-local. z_bricks uses standard three-plate wall courses.
OPENINGS = {
    "OPENING_001": {"face": "FACE_A", "type": "WINDOW", "x_studs": 10, "z_bricks": 32, "width_studs": 9, "height_bricks": 11},
    "OPENING_002": {"face": "FACE_A", "type": "WINDOW", "x_studs": 35, "z_bricks": 32, "width_studs": 11, "height_bricks": 11},
    "OPENING_003": {"face": "FACE_A", "type": "WINDOW", "x_studs": 10, "z_bricks": 18, "width_studs": 9, "height_bricks": 10},
    "OPENING_004": {"face": "FACE_A", "type": "WINDOW", "x_studs": 35, "z_bricks": 18, "width_studs": 11, "height_bricks": 10},
    "OPENING_005": {"face": "FACE_A", "type": "SMALL_LOW_OPENING", "x_studs": 12, "z_bricks": 3, "width_studs": 5, "height_bricks": 9},
    "OPENING_006": {"face": "FACE_A", "type": "LARGE_GLAZED_OPENING", "x_studs": 34, "z_bricks": 2, "width_studs": 13, "height_bricks": 12},
    "OPENING_007": {"face": "FACE_B", "type": "WINDOW", "x_studs": 40, "z_bricks": 28, "width_studs": 9, "height_bricks": 9},
    "OPENING_008": {"face": "FACE_B", "type": "WINDOW", "x_studs": 58, "z_bricks": 28, "width_studs": 8, "height_bricks": 9},
    "OPENING_009": {"face": "FACE_B", "type": "GLASS_BLOCK_OPENING", "x_studs": 44, "z_bricks": 6, "width_studs": 9, "height_bricks": 9},
    "OPENING_010": {"face": "FACE_C", "type": "WINDOW", "x_studs": 40, "z_bricks": 32, "width_studs": 7, "height_bricks": 10},
    "OPENING_011": {
        "face": "FACE_C", "type": "UNKNOWN_OPENING", "x_studs": 40, "z_bricks": 18, "width_studs": 7, "height_bricks": 9,
        "approximation": "CONSTRUCTIVE_APPROXIMATION_DUE_TO_OCCLUSION",
        "unknown_photo_components": ["BOTTOM", "ACTUAL_HEIGHT"],
    },
    "OPENING_012": {
        "face": "FACE_C", "type": "LARGE_GLAZED_OPENING", "x_studs": 9, "z_bricks": 15, "width_studs": 10, "height_bricks": 12,
        "approximation": "CONSTRUCTIVE_APPROXIMATION_DUE_TO_OCCLUSION",
        "visible_occluder_is_certified_sill": False,
        "unknown_photo_components": ["ACTUAL_BOTTOM", "ACTUAL_HEIGHT"],
    },
}

RELATIVE_RANGES = {
    "OPENING_001": {"left": [0.16, 0.20], "right": [0.32, 0.36], "bottom": [0.66, 0.72], "top": [0.90, 0.95]},
    "OPENING_002": {"left": [0.60, 0.64], "right": [0.78, 0.82], "bottom": [0.67, 0.73], "top": [0.91, 0.96]},
    "OPENING_003": {"left": [0.15, 0.19], "right": [0.31, 0.35], "bottom": [0.36, 0.42], "top": [0.56, 0.62]},
    "OPENING_004": {"left": [0.59, 0.63], "right": [0.79, 0.83], "bottom": [0.35, 0.41], "top": [0.57, 0.63]},
    "OPENING_005": {"left": [0.18, 0.22], "right": [0.28, 0.32], "bottom": [0.05, 0.10], "top": [0.22, 0.28]},
    "OPENING_006": {"left": [0.58, 0.62], "right": [0.82, 0.86], "bottom": [0.02, 0.08], "top": [0.25, 0.32]},
    "OPENING_007": {"left": [0.55, 0.65], "right": [0.68, 0.77], "bottom": [0.56, 0.65], "top": [0.75, 0.84]},
    "OPENING_008": {"left": [0.82, 0.90], "right": [0.93, 1.00], "bottom": [0.52, 0.62], "top": [0.70, 0.81]},
    "OPENING_009": {"left": [0.62, 0.70], "right": [0.73, 0.82], "bottom": [0.10, 0.18], "top": [0.25, 0.35]},
    "OPENING_010": {"left": [0.07, 0.12], "right": [0.19, 0.24], "bottom": [0.64, 0.71], "top": [0.85, 0.92]},
    "OPENING_011": {"left": [0.08, 0.14], "right": [0.17, 0.24], "bottom": None, "top": [0.51, 0.62]},
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
    for opening_id, data in OPENINGS.items():
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
            "photo_relative_range": RELATIVE_RANGES[opening_id],
            "wall_local_grid": {
                "x_studs": data["x_studs"],
                "z_bricks": data["z_bricks"],
                "width_studs": data["width_studs"],
                "height_bricks": data["height_bricks"],
                "status": "CONSTRUCTIVE_APPROXIMATION_WITHIN_ACCEPTED_071_CONSTRAINT_NETWORK",
            },
            "provenance": {
                "identity_face_order_type": "PHOTO_CONSTRAINED_070",
                "relative_geometry": "PHOTO_CONSTRAINED_RANGE_071",
                "exact_grid_selection": "CONSTRUCTIVE_APPROXIMATION_072",
            },
        }
        if "approximation" in data:
            item["occlusion_approximation"] = data["approximation"]
            item["unknown_photo_components"] = data["unknown_photo_components"]
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
        "mission": "BOLDUNGO-072-MODULE005-COARSE-LEGO-OPENINGS",
        "structure_type": "NEGATIVE_SPACE_OPENINGS_CUT_IN_EXISTING_MODULE001_WALLS",
        "face_mapping": FACE_MAPPING,
        "opening_count": len(OPENINGS),
        "opening_candidate_b10": {
            "status": "AMBIGUOUS_NOT_CONSTRUCTED",
            "constructed": False,
        },
        "opening_rasters": _opening_metadata(frame),
        "constraint_translation": {
            "policy": "CONSTRAINT_NETWORK_BEFORE_INDEPENDENT_PLACEMENT",
            "face_a_centerlines": {
                "left": ["OPENING_001", "OPENING_003", "OPENING_005"],
                "right": ["OPENING_002", "OPENING_004", "OPENING_006"],
            },
            "face_b_upper_level": ["OPENING_007", "OPENING_008"],
            "face_c_occlusion_approximations": ["OPENING_011", "OPENING_012"],
            "ground_slope_is_not_opening_level": True,
        },
        "negative_space": {
            "implementation": "REAL_WALL_MATERIAL_REMOVAL_AND_RETILING",
            "decorative_overlay": False,
            "blocked_wall_cells": len(blocked),
        },
        "preservation": {
            "module_001_outside_openings": "CELL_OCCUPANCY_IDENTICAL",
            "module_002": "BYTE_EQUIVALENT_PART_RECORDS",
            "module_003": "BYTE_EQUIVALENT_PART_RECORDS",
            "module_004": "BYTE_EQUIVALENT_PART_RECORDS",
        },
        "module_005_piece_count": 0,
        "module_005_piece_count_note": "MODULE005 is negative-space geometry: it removes/resolves MODULE001 wall material and adds no standalone decorative pieces.",
        "module_001_piece_count_before": len(module1_before),
        "module_001_piece_count_after": len(module1_after),
        "replaced_module_001_lower_wall_parts_before": len(removed),
        "replaced_module_001_lower_wall_parts_after": len(rebuilt),
    }

    metadata = {
        **source.get("metadata", {}),
        "module_id": "MODULE_001_PLUS_MODULE_002_PLUS_MODULE_003_PLUS_MODULE_004_PLUS_MODULE_005",
        "mission_module_005": "BOLDUNGO-072-MODULE005-COARSE-LEGO-OPENINGS",
        "source_bundle_module_001_002_003_004": SOURCE.name,
        "source_piece_count": len(source_parts),
        "combined_piece_count": len(combined_parts),
        "module_005": module5,
    }

    issues = [
        *source.get("fidelity_issues", []),
        {
            "code": "MODULE_005_COARSE_OPENING_GRID_APPROXIMATION",
            "severity": "info",
            "object_id": COMBINED_VOLUME_ID,
            "message": "Exact stud/course selections are constructive approximations chosen inside the accepted 071 relative constraint network.",
        },
        {
            "code": "MODULE_005_OPENING_011_OCCLUDED_BOTTOM_UNKNOWN",
            "severity": "info",
            "object_id": "OPENING_011",
            "message": "Bottom and actual height are photographically unresolved; the coarse rectangle is explicitly constructive.",
        },
        {
            "code": "MODULE_005_OPENING_012_OCCLUDED_BOTTOM_UNKNOWN",
            "severity": "info",
            "object_id": "OPENING_012",
            "message": "Terrace/railing occlusion does not certify the visible cutoff as the opening sill; the coarse bottom is constructive.",
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
