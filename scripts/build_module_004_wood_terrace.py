#!/usr/bin/env python3
"""Build the first coarse LEGO abstraction of MODULE004: the rear wood terrace.

Mission 061 translates only the accepted surviving model from blind analysis 060:
- elevated rectangular deck adjacent to the rear house facade,
- open primary under-space,
- front and right guard rails,
- visible front and right edge beams,
- one observed front post,
- no invented rear railing or hidden support system.

All dimensions are coarse/refinable constructive choices. The exact house fixing,
hidden support count, diagonal-brace construction and exact MODULE003 connection
remain unresolved rather than being invented.
"""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "frontend" / "module-001-plus-module-002-plus-module-003-export.json"
MODULE_OUT = ROOT / "frontend" / "module-004-wood-terrace-export.json"
COMBINED_OUT = ROOT / "frontend" / "module-001-plus-module-002-plus-module-003-plus-module-004-export.json"

BUILDING_ID = "real-house-progressive"
MODULE_ID = "MODULE_004_WOOD_TERRACE"
MODULE_VOLUME_ID = "module-004-wood-terrace"
COMBINED_VOLUME_ID = "module-001-plus-module-002-plus-module-003-plus-module-004"

# 061 coarse/refinable world coordinates. These are not photographic measurements.
DECK_X0 = 24
DECK_X1 = 56
DECK_Y0 = 72
DECK_Y1 = 88
DECK_BASE_Z = 48
DECK_TOP_Z = 49
BEAM_BASE_Z = 45
FRONT_EDGE_Y = 87
RIGHT_EDGE_X = 55
RAIL_TOP_Z = 61
HOUSE_REAR_PLANE_Y = 72
MODULE003_ADJACENCY_X = 24
OBSERVED_FRONT_POST_X = 40
OBSERVED_FRONT_POST_Y = 87

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

parts: list[dict] = []
counter = 0


def _add(part_id: str, x: int, y: int, z: int, rotation: int, subcomponent: str) -> None:
    global counter
    counter += 1
    width, length, height = PART_DIMS[part_id]
    parts.append({
        "placement_id": f"module-004-{subcomponent}-{counter:06d}",
        "part_id": part_id,
        "category": "timber",
        "component": "facade_detail",
        "x_studs": x,
        "y_studs": y,
        "z_plates": z,
        "rotation_quarter_turns": rotation,
        "facade": "rear",
        "roof_side": None,
        "opening_id": None,
        "trim_role": None,
        "semantic_color": None,
        "width_studs": width,
        "length_studs": length,
        "height_plates": height,
    })


def _tile_line(axis: str, start: int, end: int, fixed: int, z: int, *, plate: bool, subcomponent: str) -> None:
    lengths = (8, 6, 4, 3, 2, 1)
    prefix = "PLATE" if plate else "BRICK"
    cursor = start
    while cursor < end:
        remaining = end - cursor
        span = next(value for value in lengths if value <= remaining)
        part_id = f"{prefix}_1X{span}"
        if axis == "x":
            _add(part_id, cursor, fixed, z, 1, subcomponent)
        else:
            _add(part_id, fixed, cursor, z, 0, subcomponent)
        cursor += span


def _stack_1x1(x: int, y: int, z0: int, z1: int, subcomponent: str) -> None:
    z = z0
    while z + 3 <= z1:
        _add("BRICK_1X1", x, y, z, 0, subcomponent)
        z += 3
    while z < z1:
        _add("PLATE_1X1", x, y, z, 0, subcomponent)
        z += 1


def _build_module_004() -> list[dict]:
    global parts, counter
    parts, counter = [], 0

    # Horizontal deck: one coarse plate skin, not individual real deck boards.
    for y in range(DECK_Y0, DECK_Y1):
        _tile_line(
            "x", DECK_X0, DECK_X1, y, DECK_BASE_Z,
            plate=True,
            subcomponent="deck-platform",
        )

    # Visible front and right edge beams. The right beam stops before the front
    # corner cell so the two beams meet without overlapping.
    _tile_line(
        "x", DECK_X0, DECK_X1, FRONT_EDGE_Y, BEAM_BASE_Z,
        plate=False,
        subcomponent="front-edge-beam",
    )
    _tile_line(
        "y", DECK_Y0, FRONT_EDGE_Y, RIGHT_EDGE_X, BEAM_BASE_Z,
        plate=False,
        subcomponent="right-edge-beam",
    )

    # 060 directly demonstrates at least one front vertical timber support.
    # Its exact metric location is not observable; the coarse proxy is centered
    # on the front edge and is explicitly OBSERVED, not CONSTRUCTIVE_SUPPORT.
    _stack_1x1(
        OBSERVED_FRONT_POST_X,
        OBSERVED_FRONT_POST_Y,
        0,
        BEAM_BASE_Z,
        "observed-front-post",
    )

    # Coarse railing signature only: repeated verticals plus a top rail.
    # The uncertain left termination is intentionally left open for four studs.
    front_posts = (28, 32, 36, 40, 44, 48, 52, 55)
    for x in front_posts:
        _stack_1x1(x, FRONT_EDGE_Y, DECK_TOP_Z, RAIL_TOP_Z, "front-railing-post")

    right_posts_y = (72, 76, 80, 84)
    for y in right_posts_y:
        _stack_1x1(RIGHT_EDGE_X, y, DECK_TOP_Z, RAIL_TOP_Z, "right-railing-post")

    _tile_line(
        "x", 28, DECK_X1, FRONT_EDGE_Y, RAIL_TOP_Z,
        plate=True,
        subcomponent="front-railing-top",
    )
    _tile_line(
        "y", DECK_Y0, FRONT_EDGE_Y, RIGHT_EDGE_X, RAIL_TOP_Z,
        plate=True,
        subcomponent="right-railing-top",
    )

    # Diagonal braces are visible in 060 but deliberately omitted here:
    # the current coarse orthogonal vocabulary has no honest slender diagonal
    # beam primitive. A masonry-like wedge would overstate their volume.
    return parts


def _bom(volume_id: str, model_parts: list[dict]) -> dict:
    counts = Counter((part["part_id"], part["category"]) for part in model_parts)
    lines = [
        {
            "part_id": part_id,
            "category": category,
            "semantic_color": None,
            "quantity": quantity,
        }
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


def _bundle(volume_id: str, model: dict, metadata: dict, issues: list[dict], appearance=None) -> dict:
    return {
        "schema_version": "0.1",
        "building_id": BUILDING_ID,
        "volume_id": volume_id,
        "metadata": metadata,
        "appearance": appearance,
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
    module_parts = _build_module_004()

    metadata = {
        "module_id": MODULE_ID,
        "mission": "BOLDUNGO-061-MODULE004-COARSE-LEGO",
        "source_evidence": "docs/evidence/module-004-wood-terrace-061.json",
        "structure_type": "ELEVATED_OPEN_WOOD_TERRACE",
        "metric_status": "COARSE_REFINABLE",
        "photo_analysis_source": "BOLDUNGO-060-MODULE004-BLIND-WOOD-TERRACE-RECONSTRUCTION",
        "geometry": {
            "footprint": {"x": [DECK_X0, DECK_X1], "y": [DECK_Y0, DECK_Y1]},
            "deck_walking_top_z": DECK_TOP_Z,
            "front_edge_y": FRONT_EDGE_Y,
            "right_edge_x": RIGHT_EDGE_X,
            "primary_underspace": {
                "x": [DECK_X0 + 1, RIGHT_EDGE_X],
                "y": [DECK_Y0 + 1, FRONT_EDGE_Y],
                "z": [0, BEAM_BASE_Z],
                "status": "MUST_REMAIN_OPEN",
            },
        },
        "interfaces": {
            "TO_HOUSE": {
                "rear_plane_y": HOUSE_REAR_PLANE_Y,
                "relation": "SPATIALLY_ADJACENT_ALONG_REAR_EDGE",
                "attachment_mechanism": "NOT_OBSERVABLE",
                "rear_railing_added": False,
            },
            "TO_MODULE003": {
                "adjacency_plane_x": MODULE003_ADJACENCY_X,
                "relation": "ADJACENT_HIGH_LEVEL_SYSTEMS_STRUCTURALLY_DISTINCT",
                "exact_connection": "NOT_OBSERVABLE",
            },
        },
        "level_model": {
            "module003_upper_level_reference_z": 49,
            "wood_deck_top_z": DECK_TOP_Z,
            "relation": "COARSE_EQUAL_LEVEL_PROXY",
            "exact_level_difference_status": "REFINABLE_NOT_CLAIMED_AS_PHOTOGRAPHIC_METRIC",
        },
        "supports": {
            "observed": [
                {
                    "id": "FRONT_POST_PROXY",
                    "x": OBSERVED_FRONT_POST_X,
                    "y": OBSERVED_FRONT_POST_Y,
                    "z": [0, BEAM_BASE_Z],
                    "status": "OBSERVED_SUPPORT_COARSELY_TRANSLATED",
                }
            ],
            "constructive_supports_added": [],
            "diagonal_braces": {
                "photo_status": "OBSERVED",
                "lego_status": "DEFERRED_NO_HONEST_SLENDER_DIAGONAL_PRIMITIVE",
            },
        },
        "railing": {
            "front": "COARSE_VERTICAL_REPETITION_PLUS_TOP_RAIL",
            "right": "COARSE_VERTICAL_REPETITION_PLUS_TOP_RAIL",
            "rear_house_edge": "NONE",
            "left_termination": "PARTIALLY_OPEN_UNCERTAIN",
        },
        "semantic_requirements": [
            "WOOD_TERRACE_PRIMARY_UNDERSPACE_REMAINS_OPEN",
            "WOOD_TERRACE_REMAINS_STRUCTURALLY_DISTINCT_FROM_MASONRY_MODULE003",
            "HOUSE_EDGE_HAS_NO_AUTOMATIC_RAILING",
            "OBSERVED_SUPPORTS_ARE_NOT_CONFUSED_WITH_CONSTRUCTIVE_SUPPORTS",
            "FRONT_AND_RIGHT_RAILING_SIGNATURE_EXISTS",
            "MODULE001_MODULE002_MODULE003_SOURCE_PARTS_UNCHANGED",
        ],
    }

    issues = [
        {
            "code": "MODULE004_COARSE_METRICS_REFINABLE",
            "severity": "info",
            "object_id": MODULE_VOLUME_ID,
            "message": "Footprint and level are coarse constructive choices preserving the 060 topology; they are not photographic survey measurements.",
        },
        {
            "code": "MODULE004_HIDDEN_SUPPORTS_NOT_OBSERVABLE",
            "severity": "info",
            "object_id": MODULE_VOLUME_ID,
            "message": "Only the observed front post is materialized. No hidden support is promoted from structurally plausible to visually observed.",
        },
        {
            "code": "MODULE004_DIAGONAL_BRACES_DEFERRED",
            "severity": "info",
            "object_id": MODULE_VOLUME_ID,
            "message": "Diagonal bracing is photographically observed but omitted from this coarse orthogonal translation because no honest slender diagonal primitive is used.",
        },
        {
            "code": "MODULE004_HOUSE_ATTACHMENT_MECHANISM_NOT_OBSERVABLE",
            "severity": "info",
            "object_id": MODULE_VOLUME_ID,
            "message": "The deck is spatially adjacent to the rear facade, but no ledger, anchor or embedment mechanism is asserted.",
        },
    ]

    module_model = {
        "schema_version": "0.1",
        "building_id": BUILDING_ID,
        "volume_id": MODULE_VOLUME_ID,
        "width_studs": DECK_X1 - DECK_X0,
        "depth_studs": DECK_Y1 - DECK_Y0,
        "height_plates": RAIL_TOP_Z + 1,
        "canvas_width_studs": DECK_X1,
        "canvas_depth_studs": DECK_Y1,
        "origin_x_studs": DECK_X0,
        "origin_y_studs": DECK_Y0,
        "parts": module_parts,
    }
    module_bundle = _bundle(MODULE_VOLUME_ID, module_model, metadata, issues)

    source_parts = [dict(part) for part in source["brick_model"]["parts"]]
    combined_parts = source_parts + module_parts

    source_model = source["brick_model"]
    max_x = max(
        part["x_studs"] + (
            part.get("length_studs", 1)
            if part.get("rotation_quarter_turns", 0) % 2
            else part.get("width_studs", 1)
        )
        for part in combined_parts
    )
    max_y = max(
        part["y_studs"] + (
            part.get("width_studs", 1)
            if part.get("rotation_quarter_turns", 0) % 2
            else part.get("length_studs", 1)
        )
        for part in combined_parts
    )
    max_z = max(
        part["z_plates"] + part.get("height_plates", 1)
        for part in combined_parts
    )

    combined_metadata = {
        **metadata,
        "module_id": "MODULE_001_PLUS_MODULE_002_PLUS_MODULE_003_PLUS_MODULE_004",
        "source_bundle": SOURCE.name,
        "source_bundle_translation": {"x_studs": 0, "y_studs": 0, "z_plates": 0},
        "module_001_plus_002_plus_003_piece_count": len(source_parts),
        "module_004_piece_count": len(module_parts),
        "combined_piece_count": len(combined_parts),
        "source_parts_modified": False,
    }

    combined_model = {
        "schema_version": "0.1",
        "building_id": BUILDING_ID,
        "volume_id": COMBINED_VOLUME_ID,
        "width_studs": max(source_model["width_studs"], DECK_X1),
        "depth_studs": max(source_model["depth_studs"], DECK_Y1),
        "height_plates": max(source_model["height_plates"], max_z),
        "canvas_width_studs": max(source_model.get("canvas_width_studs") or 0, max_x),
        "canvas_depth_studs": max(source_model.get("canvas_depth_studs") or 0, max_y),
        "origin_x_studs": source_model.get("origin_x_studs", 0),
        "origin_y_studs": source_model.get("origin_y_studs", 0),
        "parts": combined_parts,
    }
    combined_bundle = _bundle(
        COMBINED_VOLUME_ID,
        combined_model,
        combined_metadata,
        [*source.get("fidelity_issues", []), *issues],
        appearance=source.get("appearance"),
    )

    MODULE_OUT.write_text(
        json.dumps(module_bundle, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    COMBINED_OUT.write_text(
        json.dumps(combined_bundle, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(json.dumps({
        "module_004_piece_count": len(module_parts),
        "combined_piece_count": len(combined_parts),
        "footprint": [DECK_X0, DECK_X1, DECK_Y0, DECK_Y1],
        "deck_top_z": DECK_TOP_Z,
        "observed_front_post": [OBSERVED_FRONT_POST_X, OBSERVED_FRONT_POST_Y, 0, BEAM_BASE_Z],
        "constructive_supports_added": 0,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
