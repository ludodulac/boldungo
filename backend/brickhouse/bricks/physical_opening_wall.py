"""Orthogonal wall with a real opening, made of canonical rectangular bricks.

This is a validated-placement fixture, not a reconstruction of the house.
The opening is 4 studs wide and 2 brick courses high.\nA 2x10 lintel spans both piers; this does not certify bending strength.
"""
from .physical_placement_gate import Placement, build

def wall_with_opening():
    parts = []
    for course in range(5):
        z = course * 3
        if course == 0:
            # Offset base: each brick is tied into a pier on the next course.
            parts.extend([
                Placement("BRICK_2X2", 0, 0, z),
                Placement("BRICK_2X4", 2, 0, z, 1),
                Placement("BRICK_2X4", 6, 0, z, 1),
                Placement("BRICK_2X2", 10, 0, z),
            ])
        elif course in (1, 2):
            # Opening x=4..7, left and right piers.
            parts.extend([
                Placement("BRICK_2X4", 0, 0, z, 1),
                Placement("BRICK_2X4", 8, 0, z, 1),
            ])
        elif course == 3:
            # A single real 2x10 beam spans both piers. Its studs overlap
            # the left and right pier, joining them into one component.
            # The 1-stud end recesses are deliberate, not filled by fake parts.
            parts.append(Placement("BRICK_2X10", 1, 0, z, 1))
        else:
            parts.extend([
                Placement("BRICK_2X4", 0, 0, z, 1),
                Placement("BRICK_2X4", 4, 0, z, 1),
                Placement("BRICK_2X4", 8, 0, z, 1),
            ])
    return parts

def validate_wall_with_opening():
    return build(wall_with_opening())
