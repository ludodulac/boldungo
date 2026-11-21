"""GUIDED-004 030B: strictly local, volume-preserving LEGO joint retessellation.

Three interfaces: two west-return rail caps, two disconnected west metal
chimney strips, and two disconnected house chimney strips. Uses only
catalogued rectangular bricks. No architecture source or roof changes.
"""
from __future__ import annotations

from .brick_model import BrickModel, BrickModelPart
from .catalog import standard_orthogonal_definitions

_DECK = "scene-platform:south-timber-deck-west-return:"
_WEST = "scene-chimney:west-metal-chimney-volume:"
_HOUSE = "scene-chimney:house-chimney-antenna:"

# Existing exact pieces are replaced, never shifted or silently discarded.
# (placement id, catalog part, x, y, z, quarter turns, inherited material)
_REPLACEMENTS = (
    (
        (_DECK + "x_max:rail-top-solution:00011",
         _DECK + "y_min:rail-top-solution:00016",
         _DECK + "y_max:rail-top-solution:00014"),
        (("BRICK_1X2", 12, 36, 42, 1),
         ("BRICK_1X4", 13, 37, 42, 0),
         ("BRICK_1X2", 12, 41, 42, 1)),
        "west-return-rail",
    ),
    (
        (_WEST + "00025:solution", _WEST + "00027:solution"),
        (("BRICK_1X8", 19, 39, 33, 1),
         ("BRICK_2X8", 19, 40, 33, 1)),
        "west-metal-chimney",
    ),
    (
        (_HOUSE + "00010:solution", _HOUSE + "00016:solution"),
        (("BRICK_1X3", 45, 30, 93, 0),
         ("BRICK_2X3", 46, 30, 93, 0)),
        "house-chimney",
    ),
)


def retile_guided004_structural_interfaces(model: BrickModel) -> BrickModel:
    """Swap joints across courses while preserving each replaced voxel exactly.

    New cross-joints overlap *below-course* studs of previously separate
    strips; the two rail cross-bricks engage the existing x=13 posts.
    Fail closed if geometry, catalogue or occupancy changes upstream.
    """
    catalog = standard_orthogonal_definitions()
    by_id = {part.placement_id: part for part in model.parts}
    if _DECK + "x_max:rail-top-solution:00011" not in by_id:
        return model  # unrelated buildings are unaffected

    def cells(part):
        definition = catalog.get(part.part_id)
        if definition is None:
            raise ValueError("030B_UNRECOGNISED_PART:" + part.part_id)
        w, l = definition.footprint(part.rotation_quarter_turns)
        return {(x, y, z)
                for x in range(part.x_studs, part.x_studs + w)
                for y in range(part.y_studs, part.y_studs + l)
                for z in range(part.z_plates, part.z_plates + definition.height_plates)}

    removed = set()
    added = []
    for old_ids, replacements, label in _REPLACEMENTS:
        if any(pid not in by_id for pid in old_ids):
            raise ValueError("030B_MISSING_ANCHOR:" + label)
        old = [by_id[pid] for pid in old_ids]
        original_volume = set().union(*(cells(part) for part in old))
        new = []
        for index, (reference, x, y, z, rotation) in enumerate(replacements, 1):
            definition = catalog[reference]
            w, l = definition.footprint(rotation)
            new.append(BrickModelPart(
                placement_id=f"guided004-030b:{label}:cross-joint:{index:02d}",
                part_id=reference, category=old[0].category,
                component=old[0].component, facade=old[0].facade,
                x_studs=x, y_studs=y, z_plates=z,
                rotation_quarter_turns=rotation, width_studs=w,
                length_studs=l, height_plates=definition.height_plates,
            ))
        new_cells = [cells(part) for part in new]
        if len(set().union(*new_cells)) != sum(map(len, new_cells)):
            raise ValueError("030B_NEW_PARTS_OVERLAP:" + label)
        if set().union(*new_cells) != original_volume:
            raise ValueError("030B_ARCHITECTURE_CHANGED:" + label)
        removed.update(old_ids)
        added.extend(new)

    # The exact old occupied voxels are retained, so the pre-existing
    # collision-free export remains collision-free; still explicitly gate
    # each new placement against every other rectangular part.
    other_cells = set()
    for part in model.parts:
        if part.placement_id not in removed and part.part_id in catalog:
            other_cells.update(cells(part))
    for part in added:
        if cells(part) & other_cells:
            raise ValueError("030B_COLLISION:" + part.placement_id)
    return model.model_copy(update={
        "parts": [p for p in model.parts if p.placement_id not in removed] + added
    })
