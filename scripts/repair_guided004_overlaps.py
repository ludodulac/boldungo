"""Loss-audited overlap repair of orthogonal parts in an existing BrickModel.

This is a post-processing validation pass, NOT a second scene converter.
Non-orthogonal roof pieces remain untouched and are explicitly outside this pass.
"""
from __future__ import annotations

from collections import Counter
from brickhouse.bricks.catalog import standard_orthogonal_definitions

CATALOG = standard_orthogonal_definitions()


def _cells(part):
    definition = CATALOG[part.part_id]
    w, l = definition.footprint(part.rotation_quarter_turns)
    return {(x, y, z)
            for x in range(part.x_studs, part.x_studs + w)
            for y in range(part.y_studs, part.y_studs + l)
            for z in range(part.z_plates, part.z_plates + definition.height_plates)}


def repair_orthogonal_overlaps(model):
    """Keep first occupant of each voxel; split colliding later bricks into 1x1s.

    Preserves the union of occupied orthogonal voxels when course heights align.
    Every removed overlap and changed part is accounted for; does not assert
    stud connectivity, slope collision clearance, or mechanical strength.
    """
    occupied = set()
    result = []
    conflicts = []
    replaced = []
    unrepairable = []
    for part in model.parts:
        if part.part_id not in CATALOG:
            result.append(part)
            continue
        cells = _cells(part)
        overlap = cells & occupied
        if not overlap:
            result.append(part)
            occupied.update(cells)
            continue
        conflicts.append({"placement_id": part.placement_id, "overlap_voxels": len(overlap)})
        remaining = cells - occupied
        definition = CATALOG[part.part_id]
        if definition.height_plates not in (1, 3) or any(
            len({z for xx, yy, z in remaining if (xx, yy) == (x, y)}) not in (0, definition.height_plates)
            for x, y, _ in remaining
        ):
            unrepairable.append(part.placement_id)
            result.append(part)
            occupied.update(cells)
            continue
        unit_id = "BRICK_1X1" if definition.height_plates == 3 else "PLATE_1X1"
        xy = sorted({(x, y) for x, y, z in remaining})
        for index, (x, y) in enumerate(xy):
            result.append(part.model_copy(update={
                "placement_id": f"{part.placement_id}:repair:{index:04d}",
                "part_id": unit_id, "x_studs": x, "y_studs": y,
                "rotation_quarter_turns": 0, "width_studs": 1,
                "length_studs": 1, "height_plates": definition.height_plates,
            }))
        replaced.append({"placement_id": part.placement_id, "replacement_parts": len(xy),
                         "removed_duplicate_voxels": len(overlap)})
        occupied.update(remaining)
    if unrepairable:
        raise ValueError("UNREPAIRABLE_PARTIAL_HEIGHT_OVERLAP:" + repr(unrepairable[:20]))
    fixed = model.model_copy(update={"parts": result})
    fixed = type(model).model_validate(fixed.model_dump(mode="json"))
    checked = set()
    for part in fixed.parts:
        if part.part_id in CATALOG:
            cells = _cells(part)
            if cells & checked:
                raise AssertionError("ORTHOGONAL_OVERLAP_REMAINS:" + part.placement_id)
            checked.update(cells)
    if checked != occupied:
        raise AssertionError("ORTHOGONAL_OCCUPANCY_NOT_PRESERVED")
    return fixed, {"overlap_parts_repaired": len(replaced),
                   "original_overlap_parts": len(conflicts),
                   "original_overlap_voxels": sum(c["overlap_voxels"] for c in conflicts),
                   "replacements": replaced,
                   "before_parts": len(model.parts), "after_parts": len(fixed.parts),
                   "orthogonal_occupied_voxels": len(checked),
                   "roof_parts_outside_orthogonal_gate": sum(p.part_id not in CATALOG for p in fixed.parts)}
