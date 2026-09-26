#!/usr/bin/env python3
"""Build MODULE_002_ROOF and the combined MODULE_001 + MODULE_002 viewer bundle.

Mission 040 deliberately models the visible 5404 covering as ROOF_SKIN and a
separate sparse orthogonal stud/tube frame as ROOF_SUPPORT.  MODULE 001 is read
as an immutable input and translated only in the combined canvas to make room
for roof overhang.
"""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "frontend" / "module-001-baseline57-export.json"
MODULE_OUT = ROOT / "frontend" / "module-002-roof-export.json"
COMBINED_OUT = ROOT / "frontend" / "module-001-plus-module-002-roof-export.json"

BUILDING_ID = "real-house-progressive"
MODULE_ID = "MODULE_002_ROOF"
COMBINED_VOLUME_ID = "module-001-plus-module-002-roof"
MODULE_VOLUME_ID = "module-002-roof"
ORIGIN_X = 3
ORIGIN_Y = 1
ROOF_WIDTH = 62
ROOF_DEPTH = 73
BODY_WIDTH = 57
BODY_DEPTH = 71
EAVE_DATUM = 140
SKIN_EAVE_BASE = 141
RIDGE_BASE = 163
RIDGE_TOP = 164
SKIN_PROFILE = (141, 143, 144, 146, 147, 149, 150, 152, 153, 155, 156, 158, 159, 160, 161)
SKIN_ID = "BRICK_SLOPED_18_2X1X2_3"

PLATE_DIMS = {
    "PLATE_1X1": (1, 1, 1),
    "PLATE_1X2": (1, 2, 1),
    "PLATE_1X3": (1, 3, 1),
    "PLATE_1X4": (1, 4, 1),
    "PLATE_1X6": (1, 6, 1),
    "PLATE_1X8": (1, 8, 1),
}
BRICK_DIMS = {"BRICK_1X1": (1, 1, 3)}

parts: list[dict] = []
support_counter = 0
skin_counter = 0
ridge_counter = 0


def _common(pid: str, part_id: str, category: str, component: str, x: int, y: int, z: int,
            rotation: int, *, roof_side=None, width=None, length=None, height=None) -> dict:
    return {
        "placement_id": pid,
        "part_id": part_id,
        "category": category,
        "component": component,
        "x_studs": x,
        "y_studs": y,
        "z_plates": z,
        "rotation_quarter_turns": rotation,
        "facade": None,
        "roof_side": roof_side,
        "opening_id": None,
        "trim_role": None,
        "semantic_color": None,
        "width_studs": width,
        "length_studs": length,
        "height_plates": height,
    }


def add_support(part_id: str, x: int, y: int, z: int, rotation: int = 0) -> None:
    global support_counter
    support_counter += 1
    dims = PLATE_DIMS.get(part_id) or BRICK_DIMS[part_id]
    parts.append(_common(
        f"module-002-support-{support_counter:06d}", part_id,
        "plate" if part_id.startswith("PLATE_") else "brick",
        "roof_support", x, y, z, rotation,
        width=dims[0], length=dims[1], height=dims[2],
    ))


def add_skin(side: str, x: int, y: int, z: int) -> None:
    global skin_counter
    skin_counter += 1
    parts.append(_common(
        f"module-002-skin-{skin_counter:06d}", SKIN_ID, "roof_tile", "roof",
        x, y, z, 0, roof_side=side, width=2, length=1, height=2,
    ))


def add_ridge(part_id: str, x: int, y: int, span: int) -> None:
    global ridge_counter
    ridge_counter += 1
    parts.append(_common(
        f"module-002-ridge-{ridge_counter:06d}", part_id, "ridge_tile", "roof",
        x, y, RIDGE_BASE, 0, roof_side="ridge", width=2, length=span, height=1,
    ))


def source_dims(part: dict) -> tuple[int, int, int]:
    width = part.get("width_studs")
    length = part.get("length_studs")
    height = part.get("height_plates")
    if width is None or length is None:
        tokens = part["part_id"].split("_")[-1].split("X")
        width, length = int(tokens[0]), int(tokens[1])
    if height is None:
        height = 3 if part["category"] == "brick" else 1
    if part["rotation_quarter_turns"] % 2:
        width, length = length, width
    return int(width), int(length), int(height)


def translate_module_001(source: dict) -> list[dict]:
    out = []
    for raw in source["brick_model"]["parts"]:
        part = dict(raw)
        part["x_studs"] += ORIGIN_X
        part["y_studs"] += ORIGIN_Y
        out.append(part)
    return out


def host_top(translated: list[dict], x: int, y: int) -> int | None:
    result = None
    for part in translated:
        width, length, height = source_dims(part)
        if (
            part["x_studs"] <= x < part["x_studs"] + width
            and part["y_studs"] <= y < part["y_studs"] + length
        ):
            top = part["z_plates"] + height
            result = top if result is None else max(result, top)
    return result


def add_longitudinal_rail(x: int, bottom_z: int) -> None:
    # 73 studs = 8*8 + 6 + 3.  The lower 1x2 seam bridges make the
    # butt-jointed top plates one connected stud/tube beam.
    segments = [(0, "PLATE_1X8", 8), (8, "PLATE_1X8", 8), (16, "PLATE_1X8", 8),
                (24, "PLATE_1X8", 8), (32, "PLATE_1X8", 8), (40, "PLATE_1X8", 8),
                (48, "PLATE_1X8", 8), (56, "PLATE_1X8", 8),
                (64, "PLATE_1X6", 6), (70, "PLATE_1X3", 3)]
    for y, part_id, _ in segments:
        add_support(part_id, x, y, bottom_z)
    for seam in (8, 16, 24, 32, 40, 48, 56, 64, 70):
        add_support("PLATE_1X2", x, seam - 1, bottom_z - 1)


def add_inner_right_rail() -> None:
    """Rail under the innermost right skin course, interrupted at both gables.

    At y=1/71 the existing masonry reaches the skin base itself, so putting a
    rail below it would penetrate MODULE 001.  Those two skin elements are
    supported directly by the pignons; the open-volume rail sections on either
    side remain tied to the adjacent x=35 rail.
    """
    add_support("PLATE_1X1", 33, 0, 160)
    segments = [
        (2, "PLATE_1X8"), (10, "PLATE_1X8"), (18, "PLATE_1X8"),
        (26, "PLATE_1X8"), (34, "PLATE_1X8"), (42, "PLATE_1X8"),
        (50, "PLATE_1X8"), (58, "PLATE_1X6"), (64, "PLATE_1X4"),
        (68, "PLATE_1X3"),
    ]
    for y, part_id in segments:
        add_support(part_id, 33, y, 160)
    for seam in (10, 18, 26, 34, 42, 50, 58, 64, 68):
        add_support("PLATE_1X2", 33, seam - 1, 159)
    add_support("PLATE_1X1", 33, 72, 160)


def add_vertical_stack(x: int, y: int, bottom_z: int, top_z: int) -> None:
    if top_z < bottom_z:
        raise ValueError(f"negative support stack at {(x, y)}: {bottom_z}>{top_z}")
    z = bottom_z
    while z + 3 <= top_z:
        add_support("BRICK_1X1", x, y, z)
        z += 3
    while z < top_z:
        add_support("PLATE_1X1", x, y, z)
        z += 1


def add_direct_gable_anchors(translated: list[dict], x: int, rail_bottom: int) -> None:
    for y in (ORIGIN_Y, ORIGIN_Y + BODY_DEPTH - 1):
        top = host_top(translated, x, y)
        if top is None:
            raise ValueError(f"no MODULE 001 gable host below roof rail at {(x, y)}")
        add_vertical_stack(x, y, top, rail_bottom)


def add_eave_cantilever_anchors() -> None:
    # Each outer rail starts one plate above the Z140 wall datum.  A two-level
    # plate cantilever reaches the overhang without embedding material in M001.
    for y in (2, 68):
        add_support("PLATE_1X2", 0, y, 139, rotation=1)   # x=0..1
        add_support("PLATE_1X3", 1, y, 140, rotation=1)  # x=1..3, host at x=3
        add_support("PLATE_1X2", 60, y, 139, rotation=1) # x=60..61
        add_support("PLATE_1X2", 59, y, 140, rotation=1) # x=59..60, host at x=59


def add_inner_right_bridge() -> None:
    # The innermost right 5404 course sits one plate below the masonry apex at
    # its footprint.  Connect its rail sideways to the adjacent supported rail
    # in the open roof volume instead of penetrating the gable.
    for y in (0, 2, 68, 72):
        add_support("PLATE_1X3", 33, y, 158, rotation=1) # x=33..35
        if y != 68:
            # At y=68 the inner rail's seam bridge already occupies Z159.
            add_support("PLATE_1X1", 33, y, 159)


def build_roof(translated: list[dict]) -> list[dict]:
    left_support_x = (0, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 28)
    right_support_x = (61, 59, 57, 55, 53, 51, 49, 47, 45, 43, 41, 39, 37, 35, 33)

    for side in ("negative", "positive"):
        for course, base_z in enumerate(SKIN_PROFILE):
            start_x = 2 * course if side == "negative" else 60 - 2 * course
            for y in range(ROOF_DEPTH):
                add_skin(side, start_x, y, base_z)

    for course, base_z in enumerate(SKIN_PROFILE):
        add_longitudinal_rail(left_support_x[course], base_z - 1)
        if course == len(SKIN_PROFILE) - 1:
            add_inner_right_rail()
        else:
            add_longitudinal_rail(right_support_x[course], base_z - 1)

    add_eave_cantilever_anchors()

    for course, base_z in enumerate(SKIN_PROFILE[1:], start=1):
        add_direct_gable_anchors(translated, left_support_x[course], base_z - 1)
        if course != len(SKIN_PROFILE) - 1:
            add_direct_gable_anchors(translated, right_support_x[course], base_z - 1)

    add_inner_right_bridge()

    # Two one-stud rails under the approved two-stud flat ridge.
    add_longitudinal_rail(30, RIDGE_BASE - 1)
    add_longitudinal_rail(31, RIDGE_BASE - 1)

    y = 0
    for part_id, span in (
        *[("TILE_2X4", 4)] * 17,
        ("TILE_2X3", 3),
        ("TILE_2X2", 2),
    ):
        add_ridge(part_id, 30, y, span)
        y += span
    if y != ROOF_DEPTH:
        raise AssertionError(f"ridge tiling ended at {y}, expected {ROOF_DEPTH}")
    return parts


def bom(building_id: str, volume_id: str, model_parts: list[dict]) -> dict:
    counts = Counter((p["part_id"], p["category"], p.get("semantic_color")) for p in model_parts)
    lines = [
        {"part_id": pid, "category": category, "semantic_color": color, "quantity": qty}
        for (pid, category, color), qty in sorted(counts.items(), key=lambda item: (item[0][1], item[0][0], item[0][2] or ""))
    ]
    return {
        "schema_version": "0.1",
        "building_id": building_id,
        "volume_id": volume_id,
        "total_parts": len(model_parts),
        "unique_part_types": len(lines),
        "lines": lines,
    }


def bundle(volume_id: str, model: dict, *, metadata: dict, issues: list[dict]) -> dict:
    return {
        "schema_version": "0.1",
        "building_id": BUILDING_ID,
        "volume_id": volume_id,
        "metadata": metadata,
        "appearance": None,
        "brick_model": model,
        "bom": bom(BUILDING_ID, volume_id, model["parts"]),
        "assembly_plan": None,
        "instruction_plan": None,
        "bag_plan": None,
        "fidelity_issues": issues,
        "capability_summary": None,
    }


def main() -> None:
    global parts, support_counter, skin_counter, ridge_counter
    parts, support_counter, skin_counter, ridge_counter = [], 0, 0, 0
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    translated = translate_module_001(source)
    roof_parts = build_roof(translated)

    roof_metadata = {
        "module_id": MODULE_ID,
        "mission": "BOLDUNGO-MODULE-002-ROOF-SKIN-SUPPORT-PROTOTYPE-040",
        "structure_type": "ROOF_SKIN_PLUS_SUPPORT",
        "skin_part": SKIN_ID,
        "skin_profile_base_z": list(SKIN_PROFILE),
        "architectural_contract": {
            "roof_type": "gable",
            "ridge_direction": "depth",
            "host_width_studs": BODY_WIDTH,
            "host_depth_studs": BODY_DEPTH,
            "roof_span_studs": ROOF_WIDTH,
            "roof_depth_studs": ROOF_DEPTH,
            "wall_to_eave_height_plates": EAVE_DATUM,
            "skin_eave_base_z": SKIN_EAVE_BASE,
            "ridge_top_z": RIDGE_TOP,
            "overhang": {"left_studs": 3, "right_studs": 2, "front_studs": 1, "rear_studs": 1},
        },
        "subcomponents": ["ROOF_SKIN_LEFT", "ROOF_SKIN_RIGHT", "ROOF_RIDGE", "ROOF_SUPPORT"],
        "piece_counts": {
            "skin": skin_counter,
            "support": support_counter,
            "ridge": ridge_counter,
            "module_002": len(roof_parts),
        },
    }
    issues = [
        {
            "code": "ROOF_PROTOTYPE_QUANTIZATION_REFINABLE",
            "severity": "info",
            "object_id": MODULE_VOLUME_ID,
            "message": "Supported 5404 skin starts at Z141 and ridge top is Z164; both remain refinable against the Z140/Z162 architectural datums.",
        },
        {
            "code": "DEPTH_LOW_CONFIDENCE_REFINABLE",
            "severity": "warning",
            "object_id": MODULE_VOLUME_ID,
            "message": "Roof length follows the current 71-stud constructive depth baseline plus one-stud longitudinal overhangs.",
        },
    ]
    roof_model = {
        "schema_version": "0.1",
        "building_id": BUILDING_ID,
        "volume_id": MODULE_VOLUME_ID,
        "width_studs": ROOF_WIDTH,
        "depth_studs": ROOF_DEPTH,
        "height_plates": RIDGE_TOP,
        "canvas_width_studs": ROOF_WIDTH,
        "canvas_depth_studs": ROOF_DEPTH,
        "origin_x_studs": 0,
        "origin_y_studs": 0,
        "parts": roof_parts,
    }
    module_bundle = bundle(MODULE_VOLUME_ID, roof_model, metadata=roof_metadata, issues=issues)

    combined_parts = translated + roof_parts
    combined_model = {
        "schema_version": "0.1",
        "building_id": BUILDING_ID,
        "volume_id": COMBINED_VOLUME_ID,
        "width_studs": BODY_WIDTH,
        "depth_studs": BODY_DEPTH,
        "height_plates": RIDGE_TOP,
        "canvas_width_studs": ROOF_WIDTH,
        "canvas_depth_studs": ROOF_DEPTH,
        "origin_x_studs": ORIGIN_X,
        "origin_y_studs": ORIGIN_Y,
        "parts": combined_parts,
    }
    combined_metadata = {
        **roof_metadata,
        "module_id": "MODULE_001_BASELINE57_PLUS_MODULE_002_ROOF",
        "module_001_source": SOURCE.name,
        "module_001_translation_for_canvas": {"x_studs": ORIGIN_X, "y_studs": ORIGIN_Y, "z_plates": 0},
        "module_001_piece_count": len(translated),
        "combined_piece_count": len(combined_parts),
    }
    combined_bundle = bundle(COMBINED_VOLUME_ID, combined_model, metadata=combined_metadata, issues=[
        *source.get("fidelity_issues", []),
        *issues,
    ])

    MODULE_OUT.write_text(json.dumps(module_bundle, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    COMBINED_OUT.write_text(json.dumps(combined_bundle, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(json.dumps({
        "module_002_piece_count": len(roof_parts),
        "skin_piece_count": skin_counter,
        "support_piece_count": support_counter,
        "ridge_piece_count": ridge_counter,
        "combined_piece_count": len(combined_parts),
        "ridge_top": RIDGE_TOP,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
