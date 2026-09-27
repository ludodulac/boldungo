#!/usr/bin/env python3
"""Build MODULE_003_MASONRY_TERRACE_STAIR and the combined M001+M002+M003 bundle.

Mission 041 keeps the photographic topology coarse and explicit:
- one hollow masonry platform/support volume with a preserved lower void,
- a two-run turning circulation path,
- parapets significant to the silhouette,
- a host contact plane and a future timber-deck interface.

The tread raster is prototype quantization, not a claim about real tread count.
"""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "frontend" / "module-001-plus-module-002-roof-export.json"
MODULE_OUT = ROOT / "frontend" / "module-003-masonry-terrace-stair-export.json"
COMBINED_OUT = ROOT / "frontend" / "module-001-plus-module-002-plus-module-003-export.json"

BUILDING_ID = "real-house-progressive"
MODULE_ID = "MODULE_003_MASONRY_TERRACE_STAIR"
MODULE_VOLUME_ID = "module-003-masonry-terrace-stair"
COMBINED_VOLUME_ID = "module-001-plus-module-002-plus-module-003"

SOURCE_SHIFT_X = 21
HOUSE_LEFT_PLANE_X = 24
HOUSE_FRONT_Y = 1
HOUSE_DEPTH = 71
HOUSE_REAR_PLANE_Y = HOUSE_FRONT_Y + HOUSE_DEPTH
MODULE_REARWARD_SHIFT = 10
STAIR_LATERAL_SHIFT = 9

PART_DIMS = {
    "BRICK_1X1": (1, 1, 3),
    "BRICK_1X2": (1, 2, 3),
    "BRICK_1X3": (1, 3, 3),
    "BRICK_1X4": (1, 4, 3),
    "BRICK_1X6": (1, 6, 3),
    "BRICK_1X8": (1, 8, 3),
    "PLATE_1X1": (1, 1, 1),
    "PLATE_1X2": (1, 2, 1),
    "PLATE_1X3": (1, 3, 1),
    "PLATE_1X4": (1, 4, 1),
    "PLATE_1X6": (1, 6, 1),
    "PLATE_1X8": (1, 8, 1),
}

SLOPE_DIMS = {
    "BRICK_SLOPED_45_2X1": (2, 1, 3),
}

parts: list[dict] = []
counter = 0


def _add(part_id: str, x: int, y: int, z: int, rotation: int, subcomponent: str, facade: str = "left") -> None:
    global counter
    counter += 1
    width, length, height = PART_DIMS[part_id]
    parts.append({
        "placement_id": f"module-003-{subcomponent}-{counter:06d}",
        "part_id": part_id,
        "category": "plate" if part_id.startswith("PLATE_") else "brick",
        "component": "wall",
        "x_studs": x,
        "y_studs": y,
        "z_plates": z,
        "rotation_quarter_turns": rotation,
        "facade": facade,
        "roof_side": None,
        "opening_id": None,
        "trim_role": None,
        "semantic_color": None,
        "width_studs": width,
        "length_studs": length,
        "height_plates": height,
    })


def _add_slope_cap(
    part_id: str,
    x: int,
    y: int,
    z: int,
    rotation: int,
    subcomponent: str,
) -> None:
    """Add an approved slope as a local visual cap without moving the stair."""
    global counter
    counter += 1
    width, length, height = SLOPE_DIMS[part_id]
    parts.append({
        "placement_id": f"module-003-{subcomponent}-{counter:06d}",
        "part_id": part_id,
        "category": "roof_tile",
        "component": "roof",
        "x_studs": x,
        "y_studs": y,
        "z_plates": z,
        "rotation_quarter_turns": rotation,
        "facade": None,
        "roof_side": "slope",
        "opening_id": None,
        "trim_role": None,
        "semantic_color": None,
        "width_studs": width,
        "length_studs": length,
        "height_plates": height,
    })


def _tile_line(axis: str, start: int, end: int, fixed: int, z: int, *, plate: bool, subcomponent: str, facade: str = "left") -> None:
    lengths = (8, 6, 4, 3, 2, 1)
    cursor = start
    prefix = "PLATE" if plate else "BRICK"
    while cursor < end:
        remaining = end - cursor
        span = next(value for value in lengths if value <= remaining)
        part_id = f"{prefix}_1X{span}"
        if axis == "y":
            _add(part_id, fixed, cursor, z, 0, subcomponent, facade)
        else:
            _add(part_id, cursor, fixed, z, 1, subcomponent, facade)
        cursor += span


def _wall_line(axis: str, start: int, end: int, fixed: int, height: int, subcomponent: str, facade: str = "left") -> None:
    z = 0
    while z + 3 <= height:
        _tile_line(axis, start, end, fixed, z, plate=False, subcomponent=subcomponent, facade=facade)
        z += 3
    while z < height:
        _tile_line(axis, start, end, fixed, z, plate=True, subcomponent=subcomponent, facade=facade)
        z += 1


def _tile_qualifying(axis: str, coords: list[int], fixed: int, z: int, *, plate: bool, subcomponent: str) -> None:
    if not coords:
        return
    coords = sorted(coords)
    runs: list[tuple[int, int]] = []
    start = previous = coords[0]
    for value in coords[1:]:
        if value == previous + 1:
            previous = value
            continue
        runs.append((start, previous + 1))
        start = previous = value
    runs.append((start, previous + 1))
    for run_start, run_end in runs:
        _tile_line(axis, run_start, run_end, fixed, z, plate=plate, subcomponent=subcomponent)


def _add_stepped_stringer(axis: str, coords: list[int], support_heights: list[int], fixeds: tuple[int, int], subcomponent: str) -> None:
    maximum = max(support_heights)
    for fixed in fixeds:
        for z in range(0, maximum, 3):
            eligible = [coord for coord, height in zip(coords, support_heights) if height >= z + 3]
            _tile_qualifying(axis, eligible, fixed, z, plate=False, subcomponent=subcomponent)
        for coord, height in zip(coords, support_heights):
            base = (height // 3) * 3
            for z in range(base, height):
                if axis == "x":
                    _add("PLATE_1X1", coord, fixed, z, 0, subcomponent)
                else:
                    _add("PLATE_1X1", fixed, coord, z, 0, subcomponent)


def _build_module_003() -> list[dict]:
    global parts, counter
    parts, counter = [], 0

    # Hollow masonry support volume: three longitudinal support walls plus
    # a rear wall with a deliberately preserved lower opening.
    _wall_line("y", 44, 62, 7, 48, "main-outer-wall")
    _wall_line("y", 44, 62, 23, 48, "main-house-wall")
    _wall_line("y", 44, 61, 15, 48, "main-internal-support")

    # 044 human-detail correction: photographs P4/P5 support the large rear
    # opening, not a second through-opening on the opposite/front lower face.
    # Close that false face while keeping the covered lower bay hollow behind it.
    for z in range(0, 48, 3):
        _tile_line(
            "x", 8, 15, 44, z, plate=False,
            subcomponent="lower-false-opening-closure", facade="front",
        )
        _tile_line(
            "x", 16, 23, 44, z, plate=False,
            subcomponent="lower-false-opening-closure", facade="front",
        )

    for z in range(0, 36, 3):
        _add("BRICK_1X6", 8, 61, z, 1, "rear-wall-left", "rear")
        _add("BRICK_1X1", 14, 61, z, 0, "rear-wall-left", "rear")
        _add("BRICK_1X1", 22, 61, z, 0, "rear-wall-right-pier", "rear")

    # Lintel across the lower opening. The right 1x8 reaches the right pier,
    # so every lintel course remains physically supported.
    for z in range(36, 48, 3):
        _add("BRICK_1X6", 8, 61, z, 1, "rear-lintel", "rear")
        _add("BRICK_1X1", 14, 61, z, 0, "rear-lintel", "rear")
        _add("BRICK_1X8", 15, 61, z, 1, "rear-lintel", "rear")

    # Upper walking platform at top Z49.
    for y in range(44, 62):
        _add("PLATE_1X8", 7, y, 48, 1, "upper-platform")
        _add("PLATE_1X8", 15, y, 48, 1, "upper-platform")
        _add("PLATE_1X1", 23, y, 48, 0, "upper-platform")

    # Significant masonry parapets only. 043 keeps the validated outer
    # parapet but opens the former rear parapet at the stair/platform arrival.
    for z in range(49, 61, 3):
        _tile_line("y", 44, 62, 7, z, plate=False, subcomponent="platform-parapet-outer")

    # 044: protect the exposed rear platform edge outside the stair arrival.
    # X16..22 stays open for circulation; the X8..15 guard joins the existing
    # outer parapet at X7 without restoring the obstructing 043 parapet.
    for z in range(49, 61, 3):
        _tile_line(
            "x", 8, 16, 61, z, plate=False,
            subcomponent="platform-edge-fall-protection", facade="rear",
        )

    # Lower run: coarse seven-tread raster, low courtyard -> turn level Z24.
    lower_levels = [3, 6, 9, 12, 16, 20, 24]
    for x, top in enumerate(lower_levels):
        _add("PLATE_1X8", x, 75, top - 1, 0, "stair-lower-tread")

    # Turning landing at Z24, supported by two sparse edge walls.
    for y in range(75, 83):
        _add("PLATE_1X8", 7, y, 23, 1, "stair-landing")
    for x in (7, 14):
        _wall_line("y", 75, 83, x, 23, "stair-landing-support")

    # 043: add simple L-shaped protection to the first/turn landing while
    # leaving its west entry from the lower run and north exit to the upper
    # run completely open. Three brick courses match the coarse stair rails.
    for z in (24, 27, 30):
        _tile_line("x", 7, 15, 82, z, plate=False, subcomponent="stair-first-landing-rail")
        _tile_line("y", 76, 82, 14, z, plate=False, subcomponent="stair-first-landing-rail")

    # Upper run: 13-tread coarse raster, turn level Z24 -> platform Z49.
    upper_levels = [26, 28, 30, 32, 34, 36, 38, 40, 42, 44, 46, 48, 49]
    upper_y = list(range(74, 61, -1))
    for y, top in zip(upper_y, upper_levels):
        _add("PLATE_1X8", 7, y, top - 1, 1, "stair-upper-tread")

    _add_stepped_stringer(
        "x", list(range(0, 7)), [value - 1 for value in lower_levels],
        (75, 82), "stair-lower-stringer",
    )
    _add_stepped_stringer(
        "y", upper_y, [value - 1 for value in upper_levels],
        (7, 14), "stair-upper-stringer",
    )

    # Coarse solid parapets following both runs.
    for x, top in zip(range(0, 7), lower_levels):
        for y in (75, 82):
            for z in (top, top + 3, top + 6):
                _add("BRICK_1X1", x, y, z, 0, "stair-lower-parapet")
    for y, top in zip(upper_y, upper_levels):
        for x in (7, 14):
            for z in (top, top + 3, top + 6):
                _add("BRICK_1X1", x, y, z, 0, "stair-upper-parapet")

    # 044 silhouette refinement. Approved 45-degree slope pieces act only as
    # cap courses over the existing masonry parapets. Treads, stringers, run
    # envelopes and Z levels are untouched.
    lower_cap_z = (12, 15, 18, 21, 25, 29)
    for y in (75, 82):
        for x, z in zip(range(0, 6), lower_cap_z):
            _add_slope_cap(
                "BRICK_SLOPED_45_2X1", x, y, z, 0,
                "stair-lower-parapet-smooth-cap",
            )

    # The upper run rises more gently in the coarse raster. Six two-stud cap
    # segments preserve the run while reducing the crenellated top silhouette.
    upper_cap_y = (72, 70, 68, 66, 64, 62)
    upper_cap_z = (35, 39, 43, 47, 51, 55)
    for x in (7, 14):
        for y, z in zip(upper_cap_y, upper_cap_z):
            _add_slope_cap(
                "BRICK_SLOPED_45_2X1", x, y, z, 3,
                "stair-upper-parapet-smooth-cap",
            )

    # 044 wall/parapet continuity. After the frozen +10 Y / +9 X transforms,
    # this becomes X23/Y71: outer face X24 is flush with the host wall plane,
    # directly preceding the existing house-side upper parapet at X23/Y72.
    for z in (49, 52, 55):
        _add("BRICK_1X1", 14, 61, z, 0, "stair-house-wall-continuity")

    # Minimal stud/tube bridges joining the lower run to the turn and the upper
    # run to the masonry platform. They are not architectural tread claims.
    _add("PLATE_1X2", 6, 76, 24, 1, "stair-turn-bridge")
    _add("PLATE_1X2", 8, 61, 49, 0, "stair-platform-bridge")

    # 042 human-gate correction: preserve the complete 041 topology and move
    # MODULE 003 rearward as one rigid local assembly. The +10-stud shift is
    # the smallest integer translation that moves the nearest upper-run cell
    # from Y62 to the host rear plane Y72, eliminating shared house-depth
    # projection without changing any X/Z geometry, tread raster or void.
    for part in parts:
        part["y_studs"] += MODULE_REARWARD_SHIFT

    # 043 human-gate refinement: the masonry platform stays frozen. Move only
    # the stair/landing circulation toward the house wall. The upper run was
    # X7..15 with the house wall at X24, so +9 studs is the minimum integer
    # translation that makes its outer edge meet X24 without crossing it.
    for part in parts:
        if "-stair-" in part["placement_id"]:
            part["x_studs"] += STAIR_LATERAL_SHIFT

    return parts


def _bom(volume_id: str, model_parts: list[dict]) -> dict:
    counts = Counter((part["part_id"], part["category"]) for part in model_parts)
    lines = [
        {"part_id": part_id, "category": category, "semantic_color": None, "quantity": quantity}
        for (part_id, category), quantity in sorted(counts.items())
    ]
    return {
        "schema_version": "0.1",
        "building_id": BUILDING_ID,
        "volume_id": volume_id,
        "total_parts": len(model_parts),
        "unique_part_types": len(lines),
        "lines": lines,
    }


def _bundle(volume_id: str, model: dict, metadata: dict, issues: list[dict]) -> dict:
    return {
        "schema_version": "0.1",
        "building_id": BUILDING_ID,
        "volume_id": volume_id,
        "metadata": metadata,
        "appearance": None,
        "brick_model": model,
        "bom": _bom(volume_id, model["parts"]),
        "assembly_plan": None,
        "instruction_plan": None,
        "bag_plan": None,
        "fidelity_issues": issues,
        "capability_summary": None,
    }


def main() -> None:
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    module_parts = _build_module_003()

    piece_counts = Counter(part["part_id"] for part in module_parts)
    subcomponent_counts = Counter(
        part["placement_id"].split("-")[3] for part in module_parts
    )

    metadata = {
        "module_id": MODULE_ID,
        "mission": "BOLDUNGO-MODULE-003-HUMAN-DETAIL-REFINEMENT-044",
        "source_evidence": "docs/evidence/module-003-masonry-terrace-stair-041.json",
        "structure_type": "HOLLOW_MASONRY_PLATFORM_PLUS_TURNING_STAIR",
        "host_house_left_plane_x": HOUSE_LEFT_PLANE_X,
        "host_house_rear_plane_y": HOUSE_REAR_PLANE_Y,
        "rearward_translation_studs": MODULE_REARWARD_SHIFT,
        "stair_lateral_translation_studs": STAIR_LATERAL_SHIFT,
        "obstructing_rail_removed": "platform-parapet-rear",
        "first_landing_rails": "L_SHAPED_ENTRY_EXIT_OPEN",
        "human_detail_refinement_044": {
            "platform_edge_fall_protection": {
                "rear_edge_x": [8, 16],
                "y": 71,
                "z": [49, 61],
                "stair_arrival_open_x": [16, 23],
            },
            "lower_openings": {
                "false_front_opening_closed": {
                    "x": [8, 23], "y": 54, "z": [0, 48]
                },
                "real_rear_opening_preserved": {
                    "x": [15, 22], "y": 71, "z": [0, 36]
                },
            },
            "stair_parapet_top": "APPROVED_45_DEGREE_SLOPE_CAP_PROXY",
            "house_side_parapet_continuity": {
                "x": 23, "y": 71, "z": [49, 58], "host_wall_plane_x": 24
            },
        },
        "level_model": {
            "ground_low_level_z": 0,
            "intermediate_turn_level_z": 24,
            "upper_masonry_platform_z": 49,
            "future_wood_terrace_interface_z": 45,
        },
        "geometry": {
            "main_masonry_envelope": {"x": [7, 24], "y": [54, 72], "z": [0, 49]},
            "upper_platform": {"x": [7, 24], "y": [54, 72], "walking_top_z": 49},
            "lower_void": {"x": [16, 22], "y": [55, 71], "z": [0, 36]},
            "stair_lower": {"x": [9, 16], "y": [85, 93], "z": [0, 24]},
            "turn_landing": {"x": [16, 24], "y": [85, 93], "walking_top_z": 24},
            "stair_upper": {"x": [16, 24], "y": [72, 85], "z": [24, 49]},
        },
        "interfaces": {
            "TO_HOUSE": {"plane_x": 24, "y": [54, 72], "z_top": 49, "final_lego_connection": "DEFERRED"},
            "TO_GROUND": {"z": 0},
            "TO_FUTURE_WOOD_TERRACE": {
                "walking_level_z": 45,
                "relation": "ONE_STEP_BELOW_MASONRY_PLATFORM",
                "plan_span": "UNRESOLVED_REFINABLE",
            },
        },
        "circulation_path": [
            "LOW_Z0",
            "LOWER_RUN_TO_Z24",
            "TURN_LANDING_Z24",
            "UPPER_RUN_TO_Z49",
            "UPPER_PLATFORM_Z49",
        ],
        "prototype_tread_tops": {
            "lower": [3, 6, 9, 12, 16, 20, 24],
            "upper": [26, 28, 30, 32, 34, 36, 38, 40, 42, 44, 46, 48, 49],
        },
        "piece_counts": {
            "module_003": len(module_parts),
            "by_part_id": dict(sorted(piece_counts.items())),
        },
        "viewer_debt": "DIRECT_VIEWER_OPENING_UX = NEEDS_FUTURE_FIX",
    }

    issues = [
        {
            "code": "MODULE_003_LOCAL_METRICS_REFINABLE",
            "severity": "info",
            "object_id": MODULE_VOLUME_ID,
            "message": "041 topology, 042 rearward position and 043 stair placement are preserved; 044 only closes the false lower opening, preserves the photographed rear opening, protects the exposed platform edge, smooths the stair-parapet silhouette with approved slope caps, and joins the house-side parapet to the wall plane.",
        },
        {
            "code": "WOOD_TERRACE_INTERFACE_PLAN_UNRESOLVED",
            "severity": "info",
            "object_id": MODULE_VOLUME_ID,
            "message": "The future timber terrace is not built in MODULE 003; only its lower walking-level interface is reserved.",
        },
        {
            "code": "DIRECT_VIEWER_OPENING_UX_NEEDS_FUTURE_FIX",
            "severity": "info",
            "object_id": COMBINED_VOLUME_ID,
            "message": "Known human-gate viewer opening UX debt is recorded but intentionally not addressed in mission 041.",
        },
    ]

    module_model = {
        "schema_version": "0.1",
        "building_id": BUILDING_ID,
        "volume_id": MODULE_VOLUME_ID,
        "width_studs": 24,
        "depth_studs": 39,
        "height_plates": 61,
        "canvas_width_studs": 24,
        "canvas_depth_studs": 93,
        "origin_x_studs": 0,
        "origin_y_studs": 54,
        "parts": module_parts,
    }
    module_bundle = _bundle(MODULE_VOLUME_ID, module_model, metadata, issues[:2])

    shifted_source_parts = []
    for raw in source["brick_model"]["parts"]:
        part = dict(raw)
        part["x_studs"] += SOURCE_SHIFT_X
        shifted_source_parts.append(part)

    combined_parts = shifted_source_parts + module_parts
    combined_metadata = {
        **metadata,
        "module_id": "MODULE_001_PLUS_MODULE_002_PLUS_MODULE_003",
        "source_bundle": SOURCE.name,
        "source_bundle_translation": {"x_studs": SOURCE_SHIFT_X, "y_studs": 0, "z_plates": 0},
        "module_001_plus_002_piece_count": len(shifted_source_parts),
        "module_003_piece_count": len(module_parts),
        "combined_piece_count": len(combined_parts),
    }
    combined_model = {
        "schema_version": "0.1",
        "building_id": BUILDING_ID,
        "volume_id": COMBINED_VOLUME_ID,
        "width_studs": source["brick_model"]["width_studs"],
        "depth_studs": source["brick_model"]["depth_studs"],
        "height_plates": max(source["brick_model"]["height_plates"], 61),
        "canvas_width_studs": source["brick_model"]["canvas_width_studs"] + SOURCE_SHIFT_X,
        "canvas_depth_studs": 93,
        "origin_x_studs": source["brick_model"]["origin_x_studs"] + SOURCE_SHIFT_X,
        "origin_y_studs": source["brick_model"]["origin_y_studs"],
        "parts": combined_parts,
    }
    combined_bundle = _bundle(
        COMBINED_VOLUME_ID,
        combined_model,
        combined_metadata,
        [*source.get("fidelity_issues", []), *issues],
    )

    MODULE_OUT.write_text(json.dumps(module_bundle, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    COMBINED_OUT.write_text(json.dumps(combined_bundle, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(json.dumps({
        "module_003_piece_count": len(module_parts),
        "combined_piece_count": len(combined_parts),
        "upper_platform_z": 49,
        "intermediate_turn_z": 24,
        "lower_void": [16, 22, 55, 71, 0, 36],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
