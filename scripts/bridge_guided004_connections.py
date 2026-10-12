"""Re-tile compatible 1x1 bricks into genuine longer LEGO bricks.

This pass changes only the partition of occupied orthogonal voxels, never
the source scene or occupied volume. It refuses to combine window glass,
openings, distinct materials, heights or semantic colors.
"""
from __future__ import annotations

from collections import defaultdict
from brickhouse.bricks.catalog import standard_orthogonal_definitions

CATALOG = standard_orthogonal_definitions()
ELIGIBLE = {"brick", "masonry", "concrete", "timber"}
LENGTHS = (8, 6, 4, 3, 2)


def bridge_compatible_bricks(model):
    groups = defaultdict(list)
    retained = []
    for part in model.parts:
        if (part.part_id == "BRICK_1X1" and part.category in ELIGIBLE
                and part.opening_id is None and CATALOG[part.part_id].height_plates == 3):
            key = (part.category, part.component, part.facade,
                   part.semantic_color, part.z_plates)
            groups[key].append(part)
        else:
            retained.append(part)
    before = len(model.parts)
    merged_groups = 0
    removed = 0
    for _, members in sorted(groups.items(), key=lambda pair: repr(pair[0])):
        by_xy = {(p.x_studs, p.y_studs): p for p in members}
        if len(by_xy) != len(members):
            raise AssertionError("DUPLICATE_1X1_FOOTPRINT")
        while by_xy:
            x, y = min(by_xy)
            candidates = []
            for length in LENGTHS:
                for axis in ("x", "y"):
                    coords = [((x + offset, y) if axis == "x" else (x, y + offset))
                              for offset in range(length)]
                    if all(c in by_xy for c in coords):
                        candidates.append((length, axis, coords))
            if candidates:
                # Prefer longer elements, then deterministic axis ordering.
                length, axis, coords = max(candidates, key=lambda item: (item[0], item[1] == "x"))
                original = by_xy[x, y]
                # Catalog BRICK_1XN default footprint is 1 x N.
                rotation = 1 if axis == "x" else 0
                definition = CATALOG[f"BRICK_1X{length}"]
                w, l = definition.footprint(rotation)
                if (w, l) != ((length, 1) if axis == "x" else (1, length)):
                    raise AssertionError("CATALOG_FOOTPRINT_MISMATCH")
                replacement = original.model_copy(update={
                    "part_id": f"BRICK_1X{length}",
                    "rotation_quarter_turns": rotation,
                    "width_studs": w, "length_studs": l, "height_plates": 3,
                })
                retained.append(replacement)
                for coord in coords:
                    del by_xy[coord]
                removed += length - 1
                merged_groups += 1
            else:
                retained.append(by_xy.pop((x, y)))

    # Pair parallel one-wide boards into actual 2-wide catalog pieces.
    # No material is added beneath the deck or in architectural voids.
    paired = []
    remaining = {}
    for part in retained:
        definition = CATALOG.get(part.part_id)
        if (definition is None or part.category not in ELIGIBLE or
                part.opening_id is not None or not part.part_id.startswith("BRICK_1X")):
            paired.append(part)
            continue
        length = definition.length_studs
        if f"BRICK_2X{length}" not in CATALOG:
            paired.append(part)
            continue
        provenance = tuple(part.placement_id.split(":")[:2])
        # Keep each staircase tread as a distinct real subassembly.
        if part.placement_id.startswith("scene-stair:") and ":tread:" in part.placement_id:
            provenance = tuple(part.placement_id.split(":")[:3])
        key = (provenance, part.category, part.component, part.facade,
               part.semantic_color, part.z_plates, part.part_id,
               part.rotation_quarter_turns % 2, part.x_studs, part.y_studs)
        if key in remaining:
            raise AssertionError("DUPLICATE_BOARD_COORDINATE")
        remaining[key] = part
    paired_count = 0
    while remaining:
        key = min(remaining, key=repr)
        part = remaining.pop(key)
        rotation = part.rotation_quarter_turns % 2
        adjacent = (part.x_studs + (1 if rotation == 0 else 0),
                    part.y_studs + (0 if rotation == 0 else 1))
        partner = remaining.pop((*key[:-2], *adjacent), None)
        if partner is None:
            paired.append(part)
            continue
        length = CATALOG[part.part_id].length_studs
        definition = CATALOG[f"BRICK_2X{length}"]
        w, l = definition.footprint(rotation)
        paired.append(part.model_copy(update={
            "part_id": definition.id, "width_studs": w, "length_studs": l,
            "height_plates": definition.height_plates,
        }))
        paired_count += 1
    retained = paired

    # Extend existing one-wide bricks using contiguous 1x1 end pieces.
    # This is an exact re-partition of the same studs, not a new support.
    singles = {}
    for item in retained:
        if item.part_id == "BRICK_1X1" and item.category in ELIGIBLE and item.opening_id is None:
            k = (item.category, item.component, item.facade, item.semantic_color,
                 item.z_plates, item.x_studs, item.y_studs)
            singles[k] = item
    extended = []
    extended_count = 0
    for item in retained:
        if item.part_id == "BRICK_1X1" and item in singles.values():
            continue
        definition = CATALOG.get(item.part_id)
        if (definition is None or item.category not in ELIGIBLE or
                item.opening_id is not None or not item.part_id.startswith("BRICK_1X")):
            extended.append(item)
            continue
        length = definition.length_studs
        if f"BRICK_1X{length + 1}" not in CATALOG:
            extended.append(item)
            continue
        rotation = item.rotation_quarter_turns % 2
        x = item.x_studs + (length if rotation else 0)
        y = item.y_studs + (0 if rotation else length)
        key = (item.category, item.component, item.facade, item.semantic_color,
               item.z_plates, x, y)
        single = singles.pop(key, None)
        if single is None:
            extended.append(item)
            continue
        replacement = CATALOG[f"BRICK_1X{length + 1}"]
        w, l = replacement.footprint(rotation)
        extended.append(item.model_copy(update={
            "part_id": replacement.id, "width_studs": w, "length_studs": l,
            "height_plates": replacement.height_plates,
        }))
        extended_count += 1
    extended.extend(singles.values())
    retained = extended
    fixed = type(model).model_validate(model.model_copy(update={"parts": retained}).model_dump(mode="json"))
    return fixed, {"before_parts": before, "after_parts": len(fixed.parts),
                   "one_by_one_bricks_removed_by_merging": removed,
                   "new_multistud_bricks": merged_groups,
                   "paired_parallel_bricks": paired_count,
                   "extended_with_existing_single_bricks": extended_count,
                   "occupied_volume_preserved_by_partition": True}
