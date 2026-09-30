#!/usr/bin/env python3
"""Build MODULE005 true negative-space openings in the frozen MODULE001 walls.

Mission 077 applies only corrections authorized by:
075 PHOTO RECOVERY + 076 CURRENT VIOLATION AUDIT.

Exact LEGO coordinates selected from relational constraints remain constructive
approximations. Untargeted openings and MODULE002/003/004 geometry are preserved.
"""
from __future__ import annotations

from copy import deepcopy
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
WALL_BRICK_COURSES = 46

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

# Certified 074 geometry. 077 derives only A and D from this state.
BASE_OPENINGS_074 = {
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

GENERAL_RULES_077 = [
    "PHOTO-CONSTRAINT-PLUS-CURRENT-VIOLATION-BEFORE-CORRECTION",
    "RELATIONAL-RECOVERY-DOES-NOT-IMPLY-EXACT-TARGET",
    "COMMON-BAY-MUST-MOVE-AS-A-SYSTEM",
    "STORY-BAND-CAN-CONSTRAIN-LEVEL-WITHOUT-CERTIFYING-SILL",
    "FAMILY-COMPATIBILITY-DOES-NOT-MEAN-DIMENSION-EQUALITY",
    "TOPOLOGY-CAN-BE-PHOTO-RECOVERED-WHILE-SOLIDITY-REMAINS-UNKNOWN",
    "HUMAN-GROUND-TRUTH-OVERRIDE-MUST-REMAIN-LABELED",
]


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


def _resolve_077(openings_074: dict, source: dict, frame: dict) -> tuple[dict, dict]:
    openings = deepcopy(openings_074)

    # CASE A — preserve the 010/011 bay and move it as one rigid system into
    # the existing MODULE003 upper-platform/interface longitudinal sector.
    module003_y0, module003_y1 = source["metadata"]["geometry"]["upper_platform"]["y"]
    pair_ids = ("OPENING_010", "OPENING_011")
    old_x = {opening_id: openings[opening_id]["x_studs"] for opening_id in pair_ids}
    widths = {opening_id: openings[opening_id]["width_studs"] for opening_id in pair_ids}
    if len(set(old_x.values())) != 1 or len(set(widths.values())) != 1:
        raise RuntimeError("CASE_A bay is no longer rigid/aligned at 074 base")

    pair_width = widths["OPENING_010"]
    admissible_x_min = module003_y0 - frame["side_y0"]
    usable_sector_y1 = min(module003_y1, frame["side_y1"])
    admissible_x_max = usable_sector_y1 - frame["side_y0"] - pair_width
    if admissible_x_min > admissible_x_max:
        raise RuntimeError("CASE_A has no admissible host-wall interval inside MODULE003 sector")

    selected_x = max(old_x["OPENING_010"], admissible_x_min)
    if selected_x > admissible_x_max:
        raise RuntimeError("CASE_A minimal relational translation cannot enter MODULE003 sector")
    delta_x = selected_x - old_x["OPENING_010"]
    for opening_id in pair_ids:
        openings[opening_id]["x_studs"] += delta_x
        openings[opening_id]["case_077"] = {
            "photo_relation": "RECOVERED_VERTICAL_BAY_RELATED_TO_MODULE003_INTERFACE_SECTOR",
            "exact_x": "APPROXIMATED_FROM_RELATIONAL_CONSTRAINT",
            "same_translation_delta_studs": delta_x,
            "bay_identity": "MODULE003_ACCESS_VERTICAL_BAY",
        }

    # CASE D — keep width/height and minimally place OPENING_007 wholly inside
    # the constructive envelope of the recovered FACE_A upper-story openings.
    upper_refs = [openings["OPENING_001"], openings["OPENING_002"]]
    story_band_bottom = min(item["z_bricks"] for item in upper_refs)
    story_band_top = max(item["z_bricks"] + item["height_bricks"] for item in upper_refs)
    seven = openings["OPENING_007"]
    old_z = seven["z_bricks"]
    admissible_z_min = story_band_bottom
    admissible_z_max = story_band_top - seven["height_bricks"]
    if admissible_z_min > admissible_z_max:
        raise RuntimeError("CASE_D current OPENING_007 height cannot fit recovered upper-story envelope")
    selected_z = max(old_z, admissible_z_min)
    if selected_z > admissible_z_max:
        raise RuntimeError("CASE_D minimal shift cannot fit recovered upper-story envelope")
    seven["z_bricks"] = selected_z
    seven["case_077"] = {
        "upper_story_membership": "PHOTO_RECOVERED",
        "exact_z": "APPROXIMATED_FROM_STORY_BAND",
        "admissible_z_bricks": [admissible_z_min, admissible_z_max],
        "selected_z_bricks": selected_z,
        "same_exact_sill_as_face_a_claimed": False,
        "same_exact_head_as_face_a_claimed": False,
        "width_changed": False,
        "height_changed": False,
    }

    correction = {
        "case_a": {
            "implemented": True,
            "pair": list(pair_ids),
            "old_x_studs": old_x,
            "new_x_studs": selected_x,
            "translation_delta_studs": delta_x,
            "module003_interface_world_y": [module003_y0, module003_y1],
            "host_side_world_y": [frame["side_y0"], frame["side_y1"]],
            "admissible_wall_local_x_studs": [admissible_x_min, admissible_x_max],
            "selection_rule": "MINIMAL_RIGID_TRANSLATION_TO_PLACE_FULL_BAY_INSIDE_EXISTING_MODULE003_INTERFACE_SECTOR",
            "photo_relation": "RECOVERED",
            "exact_target_x": "APPROXIMATED",
        },
        "case_d": {
            "implemented": True,
            "opening_id": "OPENING_007",
            "old_z_bricks": old_z,
            "new_z_bricks": selected_z,
            "translation_delta_bricks": selected_z - old_z,
            "upper_story_constructive_envelope_z_bricks": [story_band_bottom, story_band_top],
            "admissible_z_bricks": [admissible_z_min, admissible_z_max],
            "selection_rule": "MINIMAL_VERTICAL_TRANSLATION_WHOLE_OPENING_INSIDE_RECOVERED_UPPER_STORY_ENVELOPE",
            "upper_story_membership": "PHOTO_RECOVERED",
            "exact_target_z": "APPROXIMATED",
            "same_exact_sill_claimed": False,
            "same_exact_head_claimed": False,
            "width_before_after": [BASE_OPENINGS_074["OPENING_007"]["width_studs"], seven["width_studs"]],
            "height_before_after": [BASE_OPENINGS_074["OPENING_007"]["height_bricks"], seven["height_bricks"]],
        },
        "case_e": {
            "engine_capable": False,
            "implemented": False,
            "representation": "ENGINE_LIMITATION_PREVENTS_HONEST_STEP_REPRESENTATION",
            "reason": "Current BrickModel exposes physical part placements, not a non-solid topological transition primitive. A visible step part would require inventing footprint/support/underside geometry that 075 left NOT_OBSERVABLE.",
            "topology": "PHOTO_PARTIALLY_RECOVERED",
            "dimensions": "APPROXIMATED_IF_FUTURE_CAPABILITY_EXISTS",
            "solidity": "NOT_OBSERVABLE",
            "photo_recovered_solid_step": False,
        },
    }
    return openings, correction


def _opening_grids(face_label: str, openings: dict) -> list[WallOpeningGrid]:
    return [
        WallOpeningGrid(
            id=opening_id,
            x_studs=data["x_studs"],
            z_bricks=data["z_bricks"],
            width_studs=data["width_studs"],
            height_bricks=data["height_bricks"],
        )
        for opening_id, data in openings.items()
        if data["face"] == face_label
    ]


def _emit_wall(face_label: str, frame: dict, openings: dict) -> list[dict]:
    facade = FACE_MAPPING[face_label]
    width = 57 if facade == "front" else 69
    layout = generate_wall_layout_with_openings(width, WALL_BRICK_COURSES, _opening_grids(face_label, openings))
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


def _world_opening_cells(frame: dict, openings: dict) -> set[tuple[int, int, int]]:
    blocked: set[tuple[int, int, int]] = set()
    for data in openings.values():
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


def _opening_metadata(openings: dict) -> list[dict]:
    items = []
    for opening_id, data in openings.items():
        facade = FACE_MAPPING[data["face"]]
        item = {
            "opening_id": opening_id,
            "face_label": data["face"],
            "host_facade": facade,
            "type": data["type"],
            "wall_local_grid": {
                "x_studs": data["x_studs"],
                "z_bricks": data["z_bricks"],
                "width_studs": data["width_studs"],
                "height_bricks": data["height_bricks"],
                "status": "CONSTRUCTIVE_APPROXIMATION_077" if "case_077" in data else "PRESERVED_FROM_074",
            },
            "provenance": {
                "base_identity": "PHOTO_CONSTRAINED_070",
                "exact_grid_selection": "CONSTRUCTIVE_APPROXIMATION",
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
            "case_077",
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
    openings, correction_077 = _resolve_077(BASE_OPENINGS_074, source, frame)

    removed = [part for part in source_parts if _target_lower_wall(part)]
    kept = [dict(part) for part in source_parts if not _target_lower_wall(part)]
    rebuilt = (
        _emit_wall("FACE_A", frame, openings)
        + _emit_wall("FACE_B", frame, openings)
        + _emit_wall("FACE_C", frame, openings)
    )

    source_cells = _cells(removed, z_limit=WALL_BRICK_COURSES * 3)
    rebuilt_cells = _cells(rebuilt, z_limit=WALL_BRICK_COURSES * 3)
    blocked = _world_opening_cells(frame, openings)
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
        "mission": "BOLDUNGO-077-MODULE005-PHOTO-RECOVERED-RELATIONAL-CORRECTIONS",
        "recovery_chain": [
            "BOLDUNGO-075-MODULE005-POST074D-BLIND-RELATIONAL-RECOVERY-AUDIT",
            "BOLDUNGO-076-MODULE005-POST075-RECOVERY-TO-CORRECTION-ELIGIBILITY-AUDIT",
        ],
        "structure_type": "NEGATIVE_SPACE_OPENINGS_CUT_IN_EXISTING_MODULE001_WALLS",
        "face_mapping": FACE_MAPPING,
        "opening_count": len(openings),
        "opening_candidate_b10": {"status": "AMBIGUOUS_NOT_CONSTRUCTED", "constructed": False},
        "rejected_openings": REJECTED_OPENINGS,
        "opening_rasters": _opening_metadata(openings),
        "correction_077": correction_077,
        "general_rules_canonized": GENERAL_RULES_077,
        "negative_space": {
            "implementation": "REAL_WALL_MATERIAL_REMOVAL_AND_RETILING",
            "decorative_overlay": False,
            "blocked_wall_cells": len(blocked),
        },
        "opening_surrounds": {"constructed_in_077": False},
        "terrain": {"constructed_in_077": False},
        "preservation": {
            "case_b_changed": False,
            "case_c_changed": False,
            "untargeted_openings_preserved_from_074": [
                "OPENING_001", "OPENING_002", "OPENING_003", "OPENING_004",
                "OPENING_005", "OPENING_006", "OPENING_009", "OPENING_012"
            ],
            "module_002": "BYTE_EQUIVALENT_PART_RECORDS",
            "module_003": "BYTE_EQUIVALENT_PART_RECORDS",
            "module_004": "BYTE_EQUIVALENT_PART_RECORDS",
        },
        "module_005_piece_count": 0,
        "module_005_piece_count_note": "077 changes only MODULE001 negative-space wall retile for A/D. CASE_E is not physically represented because current engine lacks an honest topology-only transition primitive.",
        "module_001_piece_count_before": len(module1_before),
        "module_001_piece_count_after": len(module1_after),
    }

    metadata = {
        **source.get("metadata", {}),
        "module_id": "MODULE_001_PLUS_MODULE_002_PLUS_MODULE_003_PLUS_MODULE_004_PLUS_MODULE_005",
        "mission_module_005": "BOLDUNGO-077-MODULE005-PHOTO-RECOVERED-RELATIONAL-CORRECTIONS",
        "source_bundle_module_001_002_003_004": SOURCE.name,
        "source_piece_count": len(source_parts),
        "combined_piece_count": len(combined_parts),
        "module_005": module5,
    }

    issues = [
        *source.get("fidelity_issues", []),
        {
            "code": "MODULE_005_077_RELATIONAL_TARGETS_APPROXIMATED",
            "severity": "info",
            "object_id": COMBINED_VOLUME_ID,
            "message": "CASE_A exact X and CASE_D exact Z are constructive approximations selected from photo-recovered relational constraints, not observed coordinates.",
        },
        {
            "code": "MODULE_003_004_STEP_ENGINE_LIMITATION",
            "severity": "info",
            "object_id": "MODULE003_MODULE004_INTERFACE",
            "message": "075 recovered local level-transition topology, but current BrickModel lacks a non-solid topology-only transition representation; no physical step is added because underside/support/solidity remain unobserved.",
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
        "opening_count": len(openings),
        "case_a_new_x": correction_077["case_a"]["new_x_studs"],
        "case_a_delta": correction_077["case_a"]["translation_delta_studs"],
        "case_d_new_z": correction_077["case_d"]["new_z_bricks"],
        "case_d_delta": correction_077["case_d"]["translation_delta_bricks"],
        "case_e_implemented": correction_077["case_e"]["implemented"],
        "combined_piece_count": len(combined_parts),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
