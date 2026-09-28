#!/usr/bin/env python3
"""Build MODULE_003_MASONRY_TERRACE_STAIR and the combined M001+M002+M003 bundle.

Mission 051 rebuilds MODULE003 from the validated architectural decomposition:
- two-run turning circulation,
- a first-class major architectural void open to ground,
- upper platform/ceiling carried by explicit masonry boundary walls,
- parapets and the HUMAN-PASS 044 platform-edge protection,
- house and future timber-terrace interfaces kept separately refinable.

The tread raster and local metrics remain prototype quantization, not metric truth.
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


def _add_visible_orthogonal(
    part_id: str,
    x: int,
    y: int,
    z: int,
    rotation: int,
    subcomponent: str,
    facade: str = "left",
) -> None:
    """Add an approved orthogonal piece used only for the visible parapet skin."""
    global counter
    counter += 1
    width, length, height = PART_DIMS[part_id]
    parts.append({
        "placement_id": f"module-003-{subcomponent}-{counter:06d}",
        "part_id": part_id,
        "category": "plate" if part_id.startswith("PLATE_") else "brick",
        "component": "facade_detail",
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


def _add_visible_slope(
    part_id: str,
    x: int,
    y: int,
    z: int,
    rotation: int,
    subcomponent: str,
    facade: str = "left",
) -> None:
    """Add an approved slope rendered with the masonry/facade material."""
    global counter
    counter += 1
    width, length, height = SLOPE_DIMS[part_id]
    parts.append({
        "placement_id": f"module-003-{subcomponent}-{counter:06d}",
        "part_id": part_id,
        "category": "facade_detail",
        "component": "facade_detail",
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


def _stack_1x1(
    x: int,
    y: int,
    z_start: int,
    z_end: int,
    subcomponent: str,
    *,
    visible_only: bool = False,
) -> None:
    """Fill one parapet cell up to an exact plate height."""
    z = z_start
    add = _add_visible_orthogonal if visible_only else _add
    while z + 3 <= z_end:
        add("BRICK_1X1", x, y, z, 0, subcomponent)
        z += 3
    while z < z_end:
        add("PLATE_1X1", x, y, z, 0, subcomponent)
        z += 1


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

    # 051 FORM-BEFORE-PIECES rebuild.
    #
    # The upper masonry system is no longer a rectangular solid with local
    # openings cut into it. It is represented as two longitudinal masonry
    # boundary walls carrying a horizontal upper platform. The full-height
    # space on the x-strong side of the inner boundary wall is intentionally
    # left empty from ground to the underside of the platform: this is VOID_01.
    #
    # Local coordinates below are translated rearward by the frozen +10 Y
    # human-approved placement at the end of the build.
    _wall_line("y", 44, 62, 7, 48, "upper-system-outer-support-wall")
    _wall_line("y", 44, 62, 15, 48, "void-01-boundary-support-wall")

    # Upper platform / ceiling of VOID_01. Two 1x8 plates per row span X7..23.
    # Each row is structurally supported by one of the two boundary walls.
    # The old X23 vertical wall strip and local opening/lintel construction are
    # deliberately absent: the negative space is the architectural primitive.
    for y in range(44, 62):
        _add("PLATE_1X8", 7, y, 48, 1, "upper-platform")
        _add("PLATE_1X8", 15, y, 48, 1, "upper-platform")

    # Outer platform parapet retained because it belongs to the established
    # silhouette and does not contradict the first-class void.
    for z in range(49, 61, 3):
        _tile_line(
            "y", 44, 62, 7, z,
            plate=False,
            subcomponent="platform-parapet-outer",
        )

    # HUMAN-PASS 044: preserve the exposed-edge protection exactly in its
    # architectural role. The stair-arrival zone X16+ stays open.
    for z in range(49, 61, 3):
        _tile_line(
            "x", 8, 16, 61, z,
            plate=False,
            subcomponent="platform-edge-fall-protection",
            facade="rear",
        )

    # STAIR_RUN_01: coarse lower run from ground toward turn level Z24.
    lower_levels = [3, 6, 9, 12, 16, 20, 24]
    for x, top in enumerate(lower_levels):
        _add("PLATE_1X8", x, 75, top - 1, 0, "stair-lower-tread")

    # TURN_LANDING: horizontal turning surface at Z24. Only the two side
    # support walls are structural; the space beneath the landing is not
    # artificially filled as part of the old 047 patch logic.
    for y in range(75, 83):
        _add("PLATE_1X8", 7, y, 23, 1, "stair-landing")
    for x in (7, 14):
        _wall_line("y", 75, 83, x, 23, "stair-landing-support")

    # Preserve the landing protection with entry from STAIR_RUN_01 and exit
    # toward STAIR_RUN_02 unobstructed.
    for z in (24, 27, 30):
        _tile_line(
            "x", 7, 15, 82, z,
            plate=False,
            subcomponent="stair-first-landing-rail",
        )
        _tile_line(
            "y", 76, 82, 14, z,
            plate=False,
            subcomponent="stair-first-landing-rail",
        )

    # STAIR_RUN_02: distinct second run, changing direction at the landing and
    # rising toward the house / upper arrival level Z49.
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

    # Coarse parapet envelopes retained from the latest constructive refinement.
    # Their form remains refinable, but they preserve continuous ascent rather
    # than reintroducing the old crenellated silhouette.
    lower_body_tops = (24, 24, 27, 27, 30, 30, 33)
    for x, tread_top, body_top in zip(range(0, 7), lower_levels, lower_body_tops):
        for y in (75, 82):
            _stack_1x1(
                x, y, tread_top, body_top,
                "stair-lower-parapet-body",
            )
    for y in (75, 82):
        for x, z in ((0, 24), (2, 27), (4, 30)):
            _add_visible_slope(
                "BRICK_SLOPED_45_2X1", x, y, z, 0,
                "stair-lower-parapet-smooth-cap",
            )

    upper_body_tops = (40, 40, 43, 43, 46, 46, 49, 49, 52, 52, 55, 55, 58)
    for y, tread_top, body_top in zip(upper_y, upper_levels, upper_body_tops):
        _stack_1x1(
            7, y, tread_top, body_top,
            "stair-upper-parapet-outer-body",
        )
        _stack_1x1(
            15, y, tread_top, body_top,
            "stair-upper-parapet-house-body",
            visible_only=True,
        )

    for x, role in (
        (7, "stair-upper-parapet-outer-smooth-cap"),
        (15, "stair-upper-parapet-house-smooth-cap"),
    ):
        for y, z in ((73, 40), (71, 43), (69, 46), (67, 49), (65, 52), (63, 55)):
            _add_visible_slope(
                "BRICK_SLOPED_45_2X1", x, y, z, 1, role,
            )

    # Minimal constructive bridges keep circulation continuous without claiming
    # exact photographic tread dimensions.
    _add("PLATE_1X2", 6, 76, 24, 1, "stair-turn-bridge")
    _add("PLATE_1X2", 8, 61, 49, 0, "stair-platform-bridge")

    # Preserve the human-approved rearward placement of the MODULE003 system.
    for part in parts:
        part["y_studs"] += MODULE_REARWARD_SHIFT

    # Preserve the human-approved lateral stair placement against the house.
    # Only stair/landing circulation elements receive this local translation.
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
        "mission": "BOLDUNGO-MODULE-003-VOLUMETRIC-REBUILD-051",
        "source_evidence": "docs/evidence/module-003-masonry-terrace-stair-041.json",
        "structure_type": "WALLS_PLUS_PLATFORM_AROUND_MAJOR_VOID_AND_TWO_RUN_STAIR",
        "host_house_left_plane_x": HOUSE_LEFT_PLANE_X,
        "host_house_rear_plane_y": HOUSE_REAR_PLANE_Y,
        "rearward_translation_studs": MODULE_REARWARD_SHIFT,
        "stair_lateral_translation_studs": STAIR_LATERAL_SHIFT,
        "subsystem_confidence": {
            "ENVELOPE": "HIGH",
            "MAJOR_VOID": "HIGH",
            "CIRCULATION": "HIGH",
            "INTERFACES": "MEDIUM",
            "METRICS": "LOW",
        },
        "normalized_decomposition": {
            "STAIR_RUN_01": {
                "relation": "GROUND_TO_TURN_LANDING",
                "orientation": "+X",
                "level": [0, 24],
                "metrics": "COARSE_REFINABLE",
            },
            "TURN_LANDING": {
                "relation": "CONNECTS_RUN_01_TO_RUN_02_WITH_DIRECTION_CHANGE",
                "level": 24,
                "metrics": "COARSE_REFINABLE",
            },
            "STAIR_RUN_02": {
                "relation": "TURN_LANDING_TO_HOUSE_LEVEL",
                "orientation": "-Y",
                "level": [24, 49],
                "metrics": "COARSE_REFINABLE",
            },
            "UPPER_ARRIVAL": {
                "relation": "RUN_02_TO_HOUSE_LEVEL_AND_UPPER_PLATFORM",
                "level": 49,
            },
            "PARAPETS": {
                "relation": "BOUND_STAIR_AND_PROTECT_EXPOSED_PLATFORM_EDGE",
                "detail": "REFINABLE",
            },
            "VOID_01": {
                "relation": "FIRST_CLASS_MAJOR_NEGATIVE_SPACE_UNDER_UPPER_PLATFORM",
                "open_to_ground": True,
                "upper_boundary_z": 48,
                "depth_status": "COARSE_CONFIRMED_EXACT_METRIC_REFINABLE",
            },
            "VOID_BOUNDARIES": {
                "x_low": "MASONRY_SUPPORT_WALL_AT_X15",
                "x_high": "OPEN",
                "y_low": "OPEN",
                "y_high": "OPEN_BELOW_UPPER_ARRIVAL_ZONE",
                "z_low": "GROUND_Z0",
                "z_high": "UPPER_PLATFORM_UNDERSIDE_Z48",
            },
            "UPPER_SOLIDS": {
                "relation": "TWO_MASONRY_BOUNDARY_WALLS_PLUS_HORIZONTAL_PLATFORM",
                "not_a_solid_block": True,
            },
            "HOUSE_INTERFACE": {
                "relation": "RUN_02_REACHES_HOUSE_LEVEL",
                "detail": "FINAL_LEGO_CONNECTION_DEFERRED",
            },
            "TIMBER_TERRACE_INTERFACE": {
                "relation": "ADJACENT_FUTURE_HIGH_LEVEL_SYSTEM",
                "detail": "PLAN_SPAN_UNRESOLVED_REFINABLE",
            },
        },
        "preserved_human_constraints": {
            "general_stair_recognition": "PRESERVED",
            "rearward_position": {
                "status": "PRESERVED",
                "translation_y_studs": MODULE_REARWARD_SHIFT,
            },
            "stair_house_proximity": {
                "status": "PRESERVED",
                "translation_x_studs": STAIR_LATERAL_SHIFT,
            },
            "platform_edge_protection_044": {
                "status": "HUMAN_PASS_PRESERVED",
                "rear_edge_x": [8, 16],
                "y": 71,
                "z": [49, 61],
                "stair_arrival_open_x": [16, 23],
            },
            "global_levels": "PRESERVED",
        },
        "level_model": {
            "ground_low_level_z": 0,
            "intermediate_turn_level_z": 24,
            "upper_masonry_platform_z": 49,
            "future_wood_terrace_interface_z": 45,
        },
        "geometry": {
            "upper_system_envelope": {"x": [7, 23], "y": [54, 72], "z": [0, 49]},
            "upper_platform": {"x": [7, 23], "y": [54, 72], "walking_top_z": 49},
            "void_01": {
                "x": [16, 23],
                "y": [55, 71],
                "z": [0, 48],
                "open_to_ground": True,
                "upper_boundary_z": 48,
                "classification": "MAJOR_ARCHITECTURAL_VOID",
            },
            "stair_run_01": {"x": [9, 16], "y": [85, 93], "z": [0, 24]},
            "turn_landing": {"x": [16, 24], "y": [85, 93], "walking_top_z": 24},
            "stair_run_02": {"x": [16, 24], "y": [72, 85], "z": [24, 49]},
            "upper_arrival": {"house_plane_x": 24, "walking_top_z": 49},
        },
        "interfaces": {
            "TO_HOUSE": {
                "plane_x": 24,
                "z_top": 49,
                "final_lego_connection": "DEFERRED",
            },
            "TO_GROUND": {"z": 0},
            "TO_FUTURE_WOOD_TERRACE": {
                "walking_level_z": 45,
                "relation": "ADJACENT_HIGH_LEVEL_INTERFACE",
                "plan_span": "UNRESOLVED_REFINABLE",
            },
        },
        "circulation_path": [
            "GROUND_Z0",
            "STAIR_RUN_01_TO_Z24",
            "TURN_LANDING_Z24",
            "DIRECTION_CHANGE",
            "STAIR_RUN_02_TO_Z49",
            "HOUSE_LEVEL_Z49",
        ],
        "prototype_tread_tops": {
            "run_01": [3, 6, 9, 12, 16, 20, 24],
            "run_02": [26, 28, 30, 32, 34, 36, 38, 40, 42, 44, 46, 48, 49],
        },
        "piece_counts": {
            "module_003": len(module_parts),
            "by_part_id": dict(sorted(piece_counts.items())),
        },
        "viewer_debt": "DIRECT_VIEWER_OPENING_UX = NEEDS_FUTURE_FIX",
    }

    issues = [
        {
            "code": "MODULE_003_051_METRICS_REFINABLE",
            "severity": "info",
            "object_id": MODULE_VOLUME_ID,
            "message": "051 rebuilds MODULE003 from the validated two-run circulation and first-class major void. Envelope and major-void topology are high confidence; local metrics and fine interfaces remain refinable.",
        },
        {
            "code": "VOID_01_DEPTH_METRIC_REFINABLE",
            "severity": "info",
            "object_id": MODULE_VOLUME_ID,
            "message": "VOID_01 is architecturally established as a large ground-open negative space with an upper boundary. Its exact metric depth remains refinable.",
        },
        {
            "code": "WOOD_TERRACE_INTERFACE_PLAN_UNRESOLVED",
            "severity": "info",
            "object_id": MODULE_VOLUME_ID,
            "message": "The future timber terrace is not built in MODULE003; only the high-level interface remains reserved.",
        },
        {
            "code": "DIRECT_VIEWER_OPENING_UX_NEEDS_FUTURE_FIX",
            "severity": "info",
            "object_id": COMBINED_VOLUME_ID,
            "message": "Known viewer-opening UX debt is recorded but intentionally not addressed in mission 051.",
        },
    ]

    module_model = {
        "schema_version": "0.1",
        "building_id": BUILDING_ID,
        "volume_id": MODULE_VOLUME_ID,
        "width_studs": 25,
        "depth_studs": 39,
        "height_plates": 61,
        "canvas_width_studs": 25,
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
        "void_01": [16, 23, 55, 71, 0, 48],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
