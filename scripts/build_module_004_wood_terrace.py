#!/usr/bin/env python3
"""Build the first coarse LEGO abstraction of MODULE004: the raised wood terrace.

Mission 063 corrects only the host-face identity of the 061 coarse model:
- preserve the complete local MODULE004 geometry and piece topology,
- rotate/reposition it from the contradicted REAR hypothesis to the
  landmark-supported LEFT longitudinal house face,
- keep MODULE003 and MODULE004 on the same longitudinal face without
  asserting their exact mechanical connection,
- preserve the open under-space, supports, railing, dimensions and Z level,
- no modification to MODULE001, MODULE002 or MODULE003.

Exact deck dimensions and fixation mechanics remain COARSE / REFINABLE.
"""
from __future__ import annotations

from collections import Counter
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

# Coarse constructive spans selected only after the relational constraints:
# rear-house adjacency, high-level adjacency to MODULE003, and open under-space.
COARSE_WIDTH_STUDS = 48
COARSE_DEPTH_STUDS = 18
RAILING_HEIGHT_PLATES = 12

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
    facade: str = "rear",
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
    """Tile an exact X span using approved 1x8/1x1 orthogonal primitives."""
    x = x0
    while x < x1:
        remaining = x1 - x
        if remaining >= 8:
            _add(part_id.replace("1X1", "1X8"), x, y, z, 1, subcomponent)
            x += 8
        else:
            _add(part_id, x, y, z, 0, subcomponent)
            x += 1


def _tile_y(part_id: str, y0: int, y1: int, x: int, z: int, subcomponent: str, *, facade: str) -> None:
    """Tile an exact Y span using approved 1x8/1x1 orthogonal primitives."""
    y = y0
    while y < y1:
        remaining = y1 - y
        if remaining >= 8:
            _add(part_id.replace("1X1", "1X8"), x, y, z, 0, subcomponent, facade=facade)
            y += 8
        else:
            _add(part_id, x, y, z, 0, subcomponent, facade=facade)
            y += 1


def _stack_post(x: int, y: int, z0: int, z1: int, subcomponent: str, *, facade: str = "rear") -> None:
    z = z0
    while z + 3 <= z1:
        _add("BRICK_1X1", x, y, z, 0, subcomponent, facade=facade)
        z += 3
    while z < z1:
        _add("PLATE_1X1", x, y, z, 0, subcomponent, facade=facade)
        z += 1


def _placement_dims(part: dict) -> tuple[int, int, int]:
    width, length, height = PART_DIMS[part["part_id"]]
    if part["rotation_quarter_turns"] % 2:
        width, length = length, width
    return width, length, height


def _rotate_061_rear_hypothesis_to_left_host(
    part: dict,
    *,
    old_x0: int,
    old_y0: int,
    host_x: int,
    new_y0: int,
) -> None:
    """Rotate the complete 061 local geometry onto the confirmed LEFT host face.

    The transformation preserves each part ID, subcomponent, Z coordinate and
    local adjacency. Old +X (along the contradicted REAR host) becomes +Y along
    the LEFT facade; old +Y (outward) becomes -X outward from that facade.
    """

    width, length, _height = _placement_dims(part)
    old_y1 = part["y_studs"] + length
    part["x_studs"] = host_x - (old_y1 - old_y0)
    part["y_studs"] = new_y0 + (part["x_studs"] + (old_y1 - old_y0) - host_x)
    # The preceding expression would use the rewritten x; restore the local
    # longitudinal coordinate from the original placement instead.
    # This assignment is intentionally overwritten below from preserved values.


def _build_module_004(source: dict) -> tuple[list[dict], dict]:
    global parts, counter
    parts, counter = [], 0

    source_metadata = source["metadata"]
    house_rear_plane_y = source_metadata["host_house_rear_plane_y"]
    house_left_plane_x = source_metadata["host_house_left_plane_x"]
    walking_top_z = source_metadata["level_model"]["future_wood_terrace_interface_z"]

    # Build the exact 061 local topology in its historical frame first.
    old_x0 = house_left_plane_x
    old_x1 = old_x0 + COARSE_WIDTH_STUDS
    old_y0 = house_rear_plane_y
    old_y1 = old_y0 + COARSE_DEPTH_STUDS

    floor_z = walking_top_z - 1
    beam_z = floor_z - 3
    old_front_y = old_y1 - 1
    old_right_x = old_x1 - 1
    railing_base_z = walking_top_z
    top_rail_z = railing_base_z + RAILING_HEIGHT_PLATES - 3

    for y in range(old_y0, old_y1):
        _tile_x("PLATE_1X1", old_x0, old_x1, y, floor_z, "deck-floor")

    _tile_x("BRICK_1X1", old_x0, old_x1, old_front_y, beam_z, "front-rim-beam")
    _tile_y("BRICK_1X1", old_y0, old_front_y, old_right_x, beam_z, "right-rim-beam", facade="right")

    old_front_post_x = old_x0 + 31
    _stack_post(old_front_post_x, old_front_y, 0, beam_z, "observed-front-post")

    front_post_xs = list(range(old_x0, old_x1 - 1, 4))
    if old_right_x not in front_post_xs:
        front_post_xs.append(old_right_x)
    for x in front_post_xs:
        _stack_post(x, old_front_y, railing_base_z, top_rail_z, "railing-front-vertical")

    right_post_ys = list(range(old_y0, old_front_y, 4))
    for y in right_post_ys:
        _stack_post(old_right_x, y, railing_base_z, top_rail_z, "railing-right-vertical", facade="right")

    _tile_x("BRICK_1X1", old_x0, old_x1, old_front_y, top_rail_z, "railing-front-top")
    _tile_y("BRICK_1X1", old_y0, old_front_y, old_right_x, top_rail_z, "railing-right-top", facade="right")

    # 062: MODULE003 and MODULE004 live on the same longitudinal LEFT face.
    # Use MODULE003's first upper-platform Y boundary as the adjacency boundary,
    # then place the 48-stud terrace span on the other side of that boundary.
    module003_neighbor_y = source_metadata["geometry"]["upper_platform"]["y"][0]
    new_y1 = module003_neighbor_y
    new_y0 = new_y1 - COARSE_WIDTH_STUDS
    host_x = house_left_plane_x

    # Apply one rigid 90-degree host-face transformation to every 061 part.
    for part in parts:
        original_x = part["x_studs"]
        original_y = part["y_studs"]
        width, length, _height = _placement_dims(part)
        original_y1 = original_y + length
        part["x_studs"] = host_x - (original_y1 - old_y0)
        part["y_studs"] = new_y0 + (original_x - old_x0)
        part["rotation_quarter_turns"] = (part["rotation_quarter_turns"] + 1) % 4
        part["facade"] = "left"

    new_x0 = host_x - COARSE_DEPTH_STUDS
    new_x1 = host_x
    outer_edge_x = new_x0
    module003_side_edge_y = new_y1 - 1
    observed_post_x = outer_edge_x
    observed_post_y = new_y0 + (old_front_post_x - old_x0)

    geometry = {
        "deck_footprint": {
            "x": [new_x0, new_x1],
            "y": [new_y0, new_y1],
            "walking_top_z": walking_top_z,
            "status": "COARSE_REFINABLE",
        },
        "primary_underspace": {
            "x": [new_x0 + 1, new_x1 - 1],
            "y": [new_y0 + 1, new_y1 - 1],
            "z": [0, floor_z],
            "open_to_ground": True,
            "classification": "MAJOR_OPEN_WOOD_TERRACE_UNDERSPACE",
        },
        "house_edge": {"x": host_x, "host_face": "left"},
        "front_edge": {
            "x": outer_edge_x,
            "local_identity": "061_FRONT_FREE_EDGE_ROTATED_TO_LEFT_FACE_OUTER_EDGE",
        },
        "right_edge": {
            "y": module003_side_edge_y,
            "local_identity": "061_RIGHT_FREE_EDGE_ROTATED_TO_LONGITUDINAL_END",
        },
        "observed_front_post": {
            "x": observed_post_x,
            "y": observed_post_y,
            "z": [0, beam_z],
        },
        "railing": {
            "base_z": railing_base_z,
            "top_z": top_rail_z + 3,
            "front_edge": True,
            "right_edge": True,
            "house_back_edge": False,
            "left_edge": "PARTIALLY_OCCLUDED_NOT_ASSERTED",
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

    module_model = BrickModel(
        building_id=BUILDING_ID,
        volume_id=MODULE_VOLUME_ID,
        width_studs=COARSE_WIDTH_STUDS,
        depth_studs=COARSE_DEPTH_STUDS,
        height_plates=geometry["railing"]["top_z"],
        canvas_width_studs=geometry["deck_footprint"]["x"][1],
        canvas_depth_studs=geometry["deck_footprint"]["y"][1],
        origin_x_studs=geometry["deck_footprint"]["x"][0],
        origin_y_studs=geometry["deck_footprint"]["y"][0],
        parts=module_parts,
    )

    module_metadata = {
        "module_id": MODULE_ID,
        "mission": "BOLDUNGO-063-MODULE004-HOST-FACE-CORRECTION",
        "source_bundle": SOURCE.name,
        "visual_source": "5_BASE_PHOTOS_ATTACHED_TO_MISSION_061",
        "blind_reasoning_source": "BOLDUNGO-060_ACCEPTED_READY_FOR_COARSE_LEGO",
        "structure_type": "RAISED_RECTANGULAR_WOOD_TERRACE_WITH_OPEN_UNDERSPACE",
        "confidence": {
            "ORIENTATION": "HIGH",
            "RELATIVE_LEVEL": "MEDIUM",
            "ADJACENCY": "HIGH",
            "FOOTPRINT": "COARSE_REFINABLE",
            "METRICS": "LOW_REFINABLE",
        },
        "geometry": geometry,
        "observed_supports": {
            "front_rim_beam": "IMPLEMENTED",
            "right_rim_beam": "IMPLEMENTED",
            "front_vertical_post": "IMPLEMENTED_ONE_OBSERVED_POST",
            "diagonal_braces": "OBSERVED_NOT_IMPLEMENTED_ORTHOGONAL_ENGINE_CANNOT_REPRESENT_DIAGONAL_BEAM_HONESTLY",
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
            "face_identity_status": "CONFIRMED_BY_062_FIVE_BASE_PHOTOS",
            "corner_crossing_required": False,
            "fixation_mechanism": "NOT_OBSERVABLE_NOT_ENCODED",
        },
        "module_003_interface": {
            "relation": "SAME_LONGITUDINAL_LEFT_FACE_HIGH_LEVEL_NEIGHBORS_REMAIN_DISTINCT",
            "shared_host_face": "left",
            "neighbor_boundary_y": source["metadata"]["geometry"]["upper_platform"]["y"][0],
            "corner_crossing_required": False,
            "wood_walking_top_z": geometry["deck_footprint"]["walking_top_z"],
            "masonry_walking_top_z": source["metadata"]["level_model"]["upper_masonry_platform_z"],
            "exact_connection": "NOT_OBSERVABLE_NOT_ENCODED",
        },
        "railing_contract": {
            "front": "COARSE_TOP_RAIL_PLUS_REPEATED_VERTICALS",
            "right": "COARSE_TOP_RAIL_PLUS_REPEATED_VERTICALS",
            "front_right_corner": "PRESERVED",
            "house_edge": "NO_AUTOMATIC_RAILING",
            "left_end": "PARTIALLY_OCCLUDED_NOT_ASSERTED",
        },
        "semantic_requirements": [
            "WOOD_TERRACE_PRIMARY_UNDERSPACE_REMAINS_OPEN",
            "WOOD_TERRACE_REMAINS_STRUCTURALLY_DISTINCT_FROM_MASONRY_MODULE003",
            "WOOD_TERRACE_HOST_FACE_IDENTITY_IS_CONFIRMED",
            "FACE_IDENTITY_REQUIRED_BEFORE_HOST_PLACEMENT",
            "WOOD_TERRACE_RAILING_OCCUPIES_FRONT_AND_RIGHT_FREE_EDGES",
            "NO_UNOBSERVED_BACK_RAILING",
            "NO_HIDDEN_SUPPORT_PROMOTED_TO_OBSERVED",
        ],
    }

    issues = [
        {
            "code": "MODULE_004_COARSE_METRICS_REFINABLE",
            "severity": "info",
            "object_id": MODULE_VOLUME_ID,
            "message": "MODULE004 footprint and exact railing spacing are coarse constructive approximations preserving the observed relations, not photo-measured dimensions.",
        },
        {
            "code": "MODULE_004_HIDDEN_SUPPORTS_UNKNOWN",
            "severity": "info",
            "object_id": MODULE_VOLUME_ID,
            "message": "Only observed support structure is represented. Hidden additional supports remain unknown and are not promoted to photographic truth.",
        },
        {
            "code": "MODULE_004_DIAGONAL_BRACES_DEFERRED",
            "severity": "info",
            "object_id": MODULE_VOLUME_ID,
            "message": "Diagonal braces are visible in the base photos but are not approximated with orthogonal blocks because the current engine lacks an honest diagonal beam primitive.",
        },
        {
            "code": "MODULE_003_MODULE_004_CONNECTION_UNRESOLVED",
            "severity": "info",
            "object_id": COMBINED_VOLUME_ID,
            "message": "MODULE003 and MODULE004 are adjacent high-level systems. Their exact physical connection is not observable and remains unencoded.",
        },
    ]

    module_bundle = _bundle(MODULE_VOLUME_ID, module_model, module_metadata, issues[:3])

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
        "mission_module_004": "BOLDUNGO-063-MODULE004-HOST-FACE-CORRECTION",
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
        "deck_footprint": geometry["deck_footprint"],
        "primary_underspace": geometry["primary_underspace"],
        "observed_front_post": geometry["observed_front_post"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
