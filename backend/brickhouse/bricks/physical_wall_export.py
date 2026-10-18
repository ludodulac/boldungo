"""Convert a geometry-screened wall fixture to the canonical BrickModel schema.

This is a fixture adapter only: it does not change the user's house geometry.
"""
from .physical_opening_wall import wall_with_opening
from .physical_placement_gate import build_geometrically

def opening_wall_part_records():
    parts = wall_with_opening()
    build_geometrically(parts)  # geometry ONLY; no connector evidence verified
    result = []
    for i, part in enumerate(parts, 1):
        w, l, h = part.dimensions()
        result.append({
            "placement_id": f"physical-opening-wall-{i:03d}",
            "part_id": part.part_id,
            "category": "brick",
            "component": "wall",
            "facade": "front",
            "x_studs": part.x,
            "y_studs": part.y,
            "z_plates": part.z,
            "rotation_quarter_turns": part.rotation,
            "width_studs": w,
            "length_studs": l,
            "height_plates": h,
        })
    return result
