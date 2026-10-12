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
    fixed = type(model).model_validate(model.model_copy(update={"parts": retained}).model_dump(mode="json"))
    return fixed, {"before_parts": before, "after_parts": len(fixed.parts),
                   "one_by_one_bricks_removed_by_merging": removed,
                   "new_multistud_bricks": merged_groups,
                   "occupied_volume_preserved_by_partition": True}
