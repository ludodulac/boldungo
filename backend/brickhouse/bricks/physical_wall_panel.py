"""Catalog-only 12-stud wall panel: staggered masonry, no fictitious parts.

Engineering fixture only. NOT a validated model of the user's house.
"""
from brickhouse.bricks.physical_placement_gate import Placement, build

def panel_courses(height=5):
    if not isinstance(height, int) or height < 1:
        raise ValueError("INVALID_COURSE_COUNT")
    result = []
    for course in range(height):
        z = course * 3
        if course % 2 == 0:
            # Three 4x2 footprints, rotated canonical BRICK_2X4.
            for x in (0, 4, 8):
                result.append(Placement("BRICK_2X4", x, 0, z, 1))
        else:
            # Offset by two studs; 2x2 ends maintain full 12-stud width.
            result.append(Placement("BRICK_2X2", 0, 0, z))
            for x in (2, 6):
                result.append(Placement("BRICK_2X4", x, 0, z, 1))
            result.append(Placement("BRICK_2X2", 10, 0, z))
    return result

def validate_panel(height=5):
    return build(panel_courses(height))

if __name__ == "__main__":
    validated = validate_panel()
    print(f"PANEL_PREFLIGHT_ACCEPTED:{len(validated.accepted)}")
