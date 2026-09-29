#!/usr/bin/env python3
"""Build MODULE004 after the 064 blind topology audit.

Mission 065 preserves the validated LEFT host face and Z45 level while
correcting only the recovered local topology:
- the terrace reaches the host-wall architectural limit opposite MODULE003,
- the long outer edge remains the main free edge,
- the terminal railing return is rebound to WALL-LIMIT-END,
- the observed main post remains on the outer edge but moves into the
  WALL-LIMIT sector,
- exact terminal angle and exact post metric remain unobserved,
- no hidden support is invented,
- MODULE001/002/003 remain immutable.
"""
from __future__ import annotations

import json
from pathlib import Path

from brickhouse.bricks.bom import generate_bom
from brickhouse.bricks.brick_model import BrickModel

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "frontend" / "module-001-plus-module-002-plus-module-003-export.json"
MODULE_OUT = ROOT / "frontend" / "module-004-wood-terrace-export.json"
COMBINED_OUT = ROOT / "frontend" / "module-001-plus-module-002-plus-module-003-plus-module-004-export.json"

BUILDING_ID = "real-house-progressive"
MODULE_ID = "MODULE_004_WOOD_TERRACE"
MODULE_VOLUME_ID = "module-004-wood-terrace"
COMBINED_VOLUME_ID = "module-001-plus-module-002-plus-module-003-plus-module-004"

COARSE_OUTWARD_DEPTH_STUDS = 18
RAILING_HEIGHT_PLATES = 12
# 064 proves only the relative WALL-LIMIT sector. Rebinding the previous coarse
# 17-stud end-distance to the correct end is a constructive approximation, not
# a photo measurement.
POST_WALL_LIMIT_OFFSET_STUDS = 17

PART_DIMS = {
    "BRICK_1X1": (1, 1, 3),
    "BRICK_1X8": (1, 8, 3),
    "PLATE_1X1": (1, 1, 1),
    "PLATE_1X8": (1, 8, 1),
}

parts: list[dict] = []
counter = 0


def _add(
    part_id: str,
    x: int,
    y: int,
    z: int,
    rotation: int,
    subcomponent: str,
    *,
    facade: str = "left",
) -> None:
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
        "facade": facade,
        "roof_side": None,
        "opening_id": None,
        "trim_role": None,
        "semantic_color": None,
        "width_studs": width,
        "length_studs": length,
        "height_plates": height,
    })


def _tile_x(part_id: str, x0: int, x1: int, y: int, z: int, subcomponent: str) -> None:
    x = x0
    while x < x1:
        remaining = x1 - x
        if remaining >= 8:
            _add(part_id.replace("1X1", "1X8"), x, y, z, 1, subcomponent)
            x += 8
        else:
            _add(part_id, x, y, z, 0, subcomponent)
            x += 1


def _tile_y(part_id: str, y0: int, y1: int, x: int, z: int, subcomponent: str) -> None:
    y = y0
    while y < y1:
        remaining = y1 - y
        if remaining >= 8:
            _add(part_id.replace("1X1", "1X8"), x, y, z, 0, subcomponent)
            y += 8
        else:
            _add(part_id, x, y, z, 0, subcomponent)
            y += 1


def _stack_post(x: int, y: int, z0: int, z1: int, subcomponent: str) -> None:
    z = z0
    while z + 3 <= z1:
        _add("BRICK_1X1", x, y, z, 0, subcomponent)
        z += 3
    while z < z1:
        _add("PLATE_1X1", x, y, z, 0, subcomponent)
        z += 1


def _build_module_004(source: dict) -> tuple[list[dict], dict]:
    global parts, counter
    parts, counter = [], 0

    metadata = source["metadata"]
    source_model = source["brick_model"]

    host_x = metadata["host_house_left_plane_x"]
    module003_end_y = metadata["geometry"]["upper_platform"]["y"][0]
    # Use the existing coarse house model's front longitudinal limit as the
    # constructive WALL-LIMIT-END. This is not promoted to a photo measurement.
    wall_limit_end_y = source_model["origin_y_studs"]
    walking_top_z = metadata["level_model"]["future_wood_terrace_interface_z"]

    outer_x = host_x - COARSE_OUTWARD_DEPTH_STUDS
    floor_z = walking_top_z - 1
    beam_z = floor_z - 3
    top_rail_z = walking_top_z + RAILING_HEIGHT_PLATES - 3

    # Deck: the 064 topology says the long terrace reaches WALL-LIMIT-END.
    # The orthogonal terminal closure is only a coarse constructive encoding.
    for y in range(wall_limit_end_y, module003_end_y):
        _tile_x("PLATE_1X1", outer_x, host_x, y, floor_z, "deck-floor")

    # Main visible long outer rim.
    _tile_y(
        "BRICK_1X1",
        wall_limit_end_y,
        module003_end_y,
        outer_x,
        beam_z,
        "long-outer-rim-beam",
    )

    # Coarse terminal closure at WALL-LIMIT-END. The long outer rim owns the
    # outer corner cell, preventing an artificial overlap there.
    _tile_x(
        "BRICK_1X1",
        outer_x + 1,
        host_x,
        wall_limit_end_y,
        beam_z,
        "wall-limit-terminal-rim",
    )

    post_y = min(
        wall_limit_end_y + POST_WALL_LIMIT_OFFSET_STUDS,
        module003_end_y - 1,
    )
    _stack_post(
        outer_x,
        post_y,
        0,
        beam_z,
        "observed-main-post",
    )

    # Long outer railing remains continuous.
    long_outer_post_ys = list(range(wall_limit_end_y, module003_end_y, 4))
    if module003_end_y - 1 not in long_outer_post_ys:
        long_outer_post_ys.append(module003_end_y - 1)
    for y in long_outer_post_ys:
        _stack_post(
            outer_x,
            y,
            walking_top_z,
            top_rail_z,
            "railing-long-outer-vertical",
        )

    # The terminal return is rebound to WALL-LIMIT-END, not MODULE003-END.
    # The outer corner is owned by the long outer railing; the host-wall corner
    # is left without an invented automatic house-edge railing.
    for x in range(outer_x + 4, host_x, 4):
        _stack_post(
            x,
            wall_limit_end_y,
            walking_top_z,
            top_rail_z,
            "railing-wall-limit-terminal-vertical",
        )

    _tile_y(
        "BRICK_1X1",
        wall_limit_end_y,
        module003_end_y,
        outer_x,
        top_rail_z,
        "railing-long-outer-top",
    )
    _tile_x(
        "BRICK_1X1",
        outer_x + 1,
        host_x,
        wall_limit_end_y,
        top_rail_z,
        "railing-wall-limit-terminal-top",
    )

    geometry = {
        "deck_footprint": {
            "x": [outer_x, host_x],
            "y": [wall_limit_end_y, module003_end_y],
            "walking_top_z": walking_top_z,
            "status": "COARSE_REFINABLE",
            "metric_status": "CONSTRUCTIVE_APPROXIMATION",
        },
        "footprint_evidence": {
            "long_outer_edge": "SUPPORTED",
            "wall_limit_terminal_closure": "SUPPORTED_TOPOLOGY",
            "terminal_angle_observability": "UNKNOWN",
            "rectangularity_observability": "AMBIGUOUS",
            "photographic_rectangle_claim": False,
            "constructive_implementation_shape": "RECTANGULAR_ORTHOGONAL_APPROXIMATION",
        },
        "primary_underspace": {
            "x": [outer_x + 1, host_x - 1],
            "y": [wall_limit_end_y + 1, module003_end_y - 1],
            "z": [0, floor_z],
            "open_to_ground": True,
            "classification": "MAJOR_OPEN_WOOD_TERRACE_UNDERSPACE",
        },
        "house_edge": {
            "x": host_x,
            "y": [wall_limit_end_y, module003_end_y],
            "host_face": "left",
        },
        "longitudinal_ends": {
            "MODULE003-END": {
                "y": module003_end_y,
                "identity": "LONGITUDINAL_END_NEIGHBORING_MODULE003",
            },
            "WALL-LIMIT-END": {
                "y": wall_limit_end_y,
                "identity": "OPPOSITE_LONGITUDINAL_END_AT_HOST_WALL_LIMIT_SECTOR",
                "metric_status": "CONSTRUCTIVE_APPROXIMATION_FROM_EXISTING_HOUSE_MODEL",
            },
        },
        "long_outer_edge": {
            "x": outer_x,
            "y": [wall_limit_end_y, module003_end_y],
        },
        "terminal_edge": {
            "end_identity": "WALL-LIMIT-END",
            "y": wall_limit_end_y,
            "x": [outer_x, host_x],
            "topology_status": "SUPPORTED",
            "angle_observability": "UNKNOWN",
            "implementation": "ORTHOGONAL_COARSE_CONSTRUCTIVE_APPROXIMATION_ONLY",
            "observed_right_angle": False,
        },
        "observed_main_post": {
            "x": outer_x,
            "y": post_y,
            "z": [0, beam_z],
            "edge_identity": "LONG_OUTER_EDGE",
            "relative_sector": "WALL-LIMIT_SECTOR",
            "metric_status": "CONSTRUCTIVE_APPROXIMATION",
        },
        "railing": {
            "base_z": walking_top_z,
            "top_z": top_rail_z + 3,
            "long_outer_edge": True,
            "terminal_return_end": "WALL-LIMIT-END",
            "module003_end_terminal_return": False,
            "house_edge": False,
        },
    }
    return parts, geometry


def _bom_dict(model: BrickModel) -> dict:
    return generate_bom(model).model_dump(mode="json")


def _bundle(volume_id: str, model: BrickModel, metadata: dict, issues: list[dict]) -> dict:
    return {
        "schema_version": "0.1",
        "building_id": BUILDING_ID,
        "volume_id": volume_id,
        "metadata": metadata,
        "appearance": None,
        "brick_model": model.model_dump(mode="json"),
        "bom": _bom_dict(model),
        "assembly_plan": None,
        "instruction_plan": None,
        "bag_plan": None,
        "fidelity_issues": issues,
        "capability_summary": None,
    }


def main() -> None:
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    module_parts, geometry = _build_module_004(source)

    deck = geometry["deck_footprint"]
    module_model = BrickModel(
        building_id=BUILDING_ID,
        volume_id=MODULE_VOLUME_ID,
        width_studs=deck["x"][1] - deck["x"][0],
        depth_studs=deck["y"][1] - deck["y"][0],
        height_plates=geometry["railing"]["top_z"],
        canvas_width_studs=deck["x"][1],
        canvas_depth_studs=deck["y"][1],
        origin_x_studs=deck["x"][0],
        origin_y_studs=deck["y"][0],
        parts=module_parts,
    )

    module_metadata = {
        "module_id": MODULE_ID,
        "mission": "BOLDUNGO-065-MODULE004-TOPOLOGY-CORRECTION",
        "visual_source": "5_BASE_PHOTOS_ATTACHED_TO_MISSION_061",
        "topology_source": "BOLDUNGO-064_ACCEPTED_BLIND_FOOTPRINT_AND_EDGE_AUDIT",
        "structure_type": "RAISED_WOOD_TERRACE_WITH_WALL_LIMIT_TERMINAL_CLOSURE",
        "confidence": {
            "HOST_FACE": "HUMAN_VALIDATED",
            "TOPOLOGY": "HIGH",
            "TERMINAL_ANGLE": "UNKNOWN",
            "METRICS": "LOW_REFINABLE",
        },
        "geometry": geometry,
        "observed_supports": {
            "long_outer_rim_beam": "IMPLEMENTED",
            "main_vertical_post": "IMPLEMENTED_ONE_OBSERVED_POST",
            "diagonal_braces": "OBSERVED_NOT_IMPLEMENTED_ORTHOGONAL_ENGINE_CANNOT_REPRESENT_DIAGONAL_BEAM_HONESTLY",
        },
        "constructive_edge_members": {
            "wall_limit_terminal_rim": "CONSTRUCTIVE_APPROXIMATION_OF_SUPPORTED_TERMINAL_CLOSURE",
        },
        "constructive_supports": {
            "added": [],
            "status": "NONE_ADDED",
            "hidden_supports": "UNKNOWN_NOT_INVENTED",
        },
        "house_interface": {
            "host_face": "left",
            "relation": "DECK_HOUSE_EDGE_ADJACENT_TO_LEFT_HOUSE_PLANE",
            "plane_x": source["metadata"]["host_house_left_plane_x"],
            "face_identity_status": "HUMAN_VALIDATED_063",
            "fixation_mechanism": "NOT_OBSERVABLE_NOT_ENCODED",
        },
        "module_003_interface": {
            "relation": "SAME_LONGITUDINAL_LEFT_FACE_HIGH_LEVEL_NEIGHBORS_REMAIN_DISTINCT",
            "shared_host_face": "left",
            "end_identity": "MODULE003-END",
            "corner_crossing_required": False,
            "wood_walking_top_z": deck["walking_top_z"],
            "masonry_walking_top_z": source["metadata"]["level_model"]["upper_masonry_platform_z"],
            "exact_connection": "NOT_OBSERVABLE_NOT_ENCODED",
        },
        "railing_contract": {
            "long_outer_edge": "COARSE_TOP_RAIL_PLUS_REPEATED_VERTICALS",
            "wall_limit_terminal": "COARSE_TOP_RAIL_PLUS_REPEATED_VERTICALS",
            "module003_end_terminal": "ABSENT",
            "house_edge": "NO_AUTOMATIC_RAILING",
        },
        "semantic_requirements": [
            "WOOD_TERRACE_REACHES_WALL_LIMIT_END",
            "TERMINAL_RAILING_IS_AT_WALL_LIMIT_END_NOT_MODULE003_END",
            "OBSERVED_POST_IS_ON_OUTER_EDGE_IN_WALL_LIMIT_SECTOR",
            "UNKNOWN_TERMINAL_ANGLE_IS_NOT_PROMOTED_TO_OBSERVED_RIGHT_ANGLE",
            "FOOTPRINT_RECTANGLE_REQUIRES_CLOSED_EDGE_EVIDENCE",
            "WOOD_TERRACE_HOST_FACE_IDENTITY_IS_CONFIRMED",
            "FACE_IDENTITY_REQUIRED_BEFORE_HOST_PLACEMENT",
            "WOOD_TERRACE_PRIMARY_UNDERSPACE_REMAINS_OPEN",
            "WOOD_TERRACE_REMAINS_STRUCTURALLY_DISTINCT_FROM_MASONRY_MODULE003",
            "NO_HIDDEN_SUPPORT_PROMOTED_TO_OBSERVED",
        ],
    }

    issues = [
        {
            "code": "MODULE_004_COARSE_METRICS_REFINABLE",
            "severity": "info",
            "object_id": MODULE_VOLUME_ID,
            "message": "MODULE004 wall-limit reach and post metric are constructive approximations on the existing coarse house scale, not photo measurements.",
        },
        {
            "code": "MODULE_004_TERMINAL_ANGLE_UNKNOWN",
            "severity": "info",
            "object_id": MODULE_VOLUME_ID,
            "message": "The terminal closure topology is supported, but its exact angle is not observable; the orthogonal LEGO closure is constructive only.",
        },
        {
            "code": "MODULE_004_HIDDEN_SUPPORTS_UNKNOWN",
            "severity": "info",
            "object_id": MODULE_VOLUME_ID,
            "message": "Only the observed main support is represented. Hidden additional supports remain unknown and are not promoted to photographic truth.",
        },
        {
            "code": "MODULE_004_DIAGONAL_BRACES_DEFERRED",
            "severity": "info",
            "object_id": MODULE_VOLUME_ID,
            "message": "Diagonal braces are observed but remain unimplemented because the current orthogonal engine lacks an honest diagonal beam primitive.",
        },
        {
            "code": "MODULE_003_MODULE_004_CONNECTION_UNRESOLVED",
            "severity": "info",
            "object_id": COMBINED_VOLUME_ID,
            "message": "MODULE003 and MODULE004 remain adjacent high-level systems; their exact physical connection is not observable and remains unencoded.",
        },
    ]

    module_bundle = _bundle(MODULE_VOLUME_ID, module_model, module_metadata, issues[:4])

    source_model = source["brick_model"]
    combined_parts = [dict(part) for part in source_model["parts"]] + [dict(part) for part in module_parts]
    combined_model = BrickModel(
        building_id=BUILDING_ID,
        volume_id=COMBINED_VOLUME_ID,
        width_studs=source_model["width_studs"],
        depth_studs=source_model["depth_studs"],
        height_plates=max(source_model["height_plates"], module_model.height_plates),
        canvas_width_studs=max(source_model.get("canvas_width_studs") or 1, module_model.canvas_width_studs or 1),
        canvas_depth_studs=max(source_model.get("canvas_depth_studs") or 1, module_model.canvas_depth_studs or 1),
        origin_x_studs=source_model.get("origin_x_studs", 0),
        origin_y_studs=source_model.get("origin_y_studs", 0),
        parts=combined_parts,
    )

    combined_metadata = {
        **source["metadata"],
        "module_id": "MODULE_001_PLUS_MODULE_002_PLUS_MODULE_003_PLUS_MODULE_004",
        "mission_module_004": "BOLDUNGO-065-MODULE004-TOPOLOGY-CORRECTION",
        "source_bundle_module_001_002_003": SOURCE.name,
        "source_piece_count": len(source_model["parts"]),
        "module_004_piece_count": len(module_parts),
        "combined_piece_count": len(combined_parts),
        "module_004": module_metadata,
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
        "module_004_piece_count": len(module_parts),
        "combined_piece_count": len(combined_parts),
        "deck_footprint": deck,
        "wall_limit_end": geometry["longitudinal_ends"]["WALL-LIMIT-END"],
        "module003_end": geometry["longitudinal_ends"]["MODULE003-END"],
        "observed_main_post": geometry["observed_main_post"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
