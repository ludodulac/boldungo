"""Orthogonal wall with a real opening, made of canonical rectangular bricks.

This is a validated-placement fixture, not a reconstruction of the house.
The opening is 4 studs wide and 2 brick courses high.
"""
from .physical_placement_gate import Placement, build

def wall_with_opening():
    parts = []
    for course in range(5):
        z = course * 3
        if course in (1, 2):
            # Opening x=4..7, left and right piers.
            parts.extend([
                Placement("BRICK_2X4", 0, 0, z, 1),
                Placement("BRICK_2X4", 8, 0, z, 1),
            ])
        elif course == 3:
            # Lintel is bridged by continuous bricks across the aperture;
            # each one has at least one stud supported by a pier.
            parts.extend([
                Placement("BRICK_2X4", 0, 0, z, 1),
                Placement("BRICK_2X4", 4, 0, z, 1),
                Placement("BRICK_2X4", 8, 0, z, 1),
            ])
        else:
            parts.extend([
                Placement("BRICK_2X4", 0, 0, z, 1),
                Placement("BRICK_2X4", 4, 0, z, 1),
                Placement("BRICK_2X4", 8, 0, z, 1),
            ])
    return parts

def validate_wall_with_opening():
    return build(wall_with_opening())
