"""Measured orthogonal stud-contact audit of the *regenerated* GUIDED-004 BrickModel.

Side contact is NOT counted as LEGO connection. Sloped pieces require a
surface model unavailable in the current roof catalog and stay unverified.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from brickhouse.bricks.catalog import standard_orthogonal_definitions
from brickhouse.bricks.roof import create_m0_roof_catalog

ORTHOGONAL = standard_orthogonal_definitions()
ROOF = create_m0_roof_catalog()


def audit_physical_model(model):
    parts = model.parts
    indexed = []
    tops = defaultdict(list)
    unsupported = []
    unsupported_by_group = Counter()
    invalid = []
    unverified = []
    roof_checked_catalog = 0
    for i, part in enumerate(parts):
        definition = ORTHOGONAL.get(part.part_id)
        if definition is None:
            try:
                roof = ROOF.get(part.part_id)
            except KeyError:
                invalid.append(part.placement_id)
                continue
            if part.component != "roof" or part.category != roof.category:
                invalid.append(part.placement_id)
                continue
            roof_checked_catalog += 1
            # Roof catalog provides nominal dimensions and course overlap,
            # but not actual sloped solid mesh or underside connector positions.
            unverified.append(part.placement_id)
            continue
        w, l = definition.footprint(part.rotation_quarter_turns)
        h = definition.height_plates
        if any((actual is not None and actual != expected) for actual, expected in (
            (part.width_studs, w), (part.length_studs, l), (part.height_plates, h)
        )):
            invalid.append(part.placement_id)
        box = (i, part.x_studs, part.y_studs, part.z_plates,
               part.x_studs + w, part.y_studs + l, part.z_plates + h)
        indexed.append(box)
        tops[box[6]].append(box)

    parent = list(range(len(parts)))
    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    def join(i, j):
        parent[root(i)] = root(j)

    collision_pairs = 0
    occupied = {}
    for i, x, y, z, x2, y2, z2 in indexed:
        for xx in range(x, x2):
            for yy in range(y, y2):
                for zz in range(z, z2):
                    key = (xx, yy, zz)
                    if key in occupied and occupied[key] != i:
                        collision_pairs += 1
                    occupied[key] = i
        if z == 0:
            continue
        supports = [other[0] for other in tops[z]
                    if other[0] != i and x < other[4] and other[1] < x2
                    and y < other[5] and other[2] < y2]
        if not supports:
            unsupported.append(parts[i].placement_id)
            prefix = parts[i].placement_id.split(":")[0]
            unsupported_by_group[prefix] += 1
        for j in supports:
            join(i, j)

    groups = defaultdict(list)
    for i, *_ in indexed:
        groups[root(i)].append(i)
    component_map = []
    box_by_index = {box[0]: box for box in indexed}
    unsupported_set = set(unsupported)
    for members in groups.values():
        boxes = [box_by_index[i] for i in members]
        component_map.append({
            "id": min(parts[i].placement_id for i in members),
            "pieces": len(members),
            "bounds": [min(b[1] for b in boxes), min(b[2] for b in boxes),
                       min(b[3] for b in boxes), max(b[4] for b in boxes),
                       max(b[5] for b in boxes), max(b[6] for b in boxes)],
            "structures": dict(Counter(parts[i].placement_id.split(":")[0] for i in members)),
            "unsupported": [parts[i].placement_id for i in members
                            if parts[i].placement_id in unsupported_set],
        })
    component_map.sort(key=lambda c: (-c["pieces"], c["id"]))
    return {
        "total_bricks": len(parts),
        "orthogonal_parts_checked": len(indexed),
        "collision_voxel_overlaps": collision_pairs,
        "unsupported_parts": len(unsupported),
        "unsupported_by_group": dict(sorted(unsupported_by_group.items())),
        "unsupported_placement_ids": unsupported,
        "connected_components_orthogonal_stud_contact": len(groups),
        "component_sizes_descending": sorted((len(g) for g in groups.values()), reverse=True),
        "component_map": component_map,
        "roof_parts_catalog_recognized": roof_checked_catalog,
        "roof_parts_unverified": len(unverified),
        "roof_unverified_ids": unverified,
        "invalid_catalog_or_metadata_parts": invalid,
        "physical_certification": "NOT_CERTIFIED" if (
            collision_pairs or unsupported or len(groups) != 1 or unverified or invalid
        ) else "ORTHOGONAL_PREFLIGHT_ONLY",
        "limitations": [
            "No full sloped-solid geometry or underside connection map in roof catalog",
            "Stud overlap does not prove mechanical clutch strength or vertical insertion",
            "Ground contact alone does not join disconnected LEGO islands",
            "Rectangular collision count is voxel overlap count, not distinct part pairs",
        ],
    }
