"""A small, real-catalog, stud-supported wall segment.

This is an engineering proof fixture, NOT a reconstruction of the user's
house or a structural-strength certificate.
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from brickhouse.bricks.physical_placement_gate import Placement, build

def wall_segment():
    # Two adjacent 2x4 base bricks, bridged by a staggered 2x4 brick.
    # Stud overlaps on the second course connect the base pieces.
    return [
        Placement("BRICK_2X4", 0, 0, 0),
        Placement("BRICK_2X4", 2, 0, 0),
        Placement("BRICK_2X4", 1, 0, 3),
        Placement("BRICK_2X4", 1, 0, 6),
    ]

def validate_wall_segment():
    return build(wall_segment())

if __name__ == "__main__":
    gate = validate_wall_segment()
    print(f"WALL_SEGMENT_PREFLIGHT_PASS:{len(gate.accepted)}")
