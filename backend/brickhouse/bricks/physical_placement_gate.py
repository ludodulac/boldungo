"""Physical placement gate for orthogonal LEGO bricks/plates.

A placement is accepted only when it has catalog geometry, no solid overlap,
and stud/tube support on an already accepted part. The base is an explicit
first part at z=0. This module does not certify clutch strength or slope pieces.
"""
from dataclasses import dataclass

# Subset of the existing catalog.py, deliberately strict (no made-up pieces).
BRICKS = {(1, n) for n in (1, 2, 3, 4, 6, 8)} | {(2, n) for n in (2, 3, 4, 6, 8, 10)}
PLATES = {(1, n) for n in (1, 2, 3, 4, 6, 8)}

@dataclass(frozen=True)
class Placement:
    part_id: str
    x: int
    y: int
    z: int
    rotation: int = 0

    def dimensions(self):
        prefix, raw = self.part_id.split("_", 1)
        w, l = (int(v) for v in raw.split("X"))
        allowed = BRICKS if prefix == "BRICK" else PLATES if prefix == "PLATE" else set()
        if (w, l) not in allowed:
            raise ValueError("PART_NOT_IN_CANONICAL_CATALOG")
        if self.rotation not in (0, 1, 2, 3):
            raise ValueError("INVALID_ROTATION")
        if self.rotation % 2:
            w, l = l, w
        return w, l, 3 if prefix == "BRICK" else 1

class PhysicalPlacementGate:
    def __init__(self):
        self.accepted = []

    def add(self, part):
        if not isinstance(part, Placement):
            raise TypeError("PLACEMENT_REQUIRED")
        if not all(isinstance(v, int) and not isinstance(v, bool) for v in (part.x, part.y, part.z)):
            raise ValueError("OFF_GRID")
        if part.z < 0:
            raise ValueError("BELOW_GROUND")
        w, l, h = part.dimensions()
        for prev in self.accepted:
            pw, pl, ph = prev.dimensions()
            if (part.x < prev.x + pw and prev.x < part.x + w and
                part.y < prev.y + pl and prev.y < part.y + l and
                part.z < prev.z + ph and prev.z < part.z + h):
                raise ValueError("SOLID_COLLISION")
        if self.accepted:
            # Rectangular orthogonal parts: top studs must meet underside tubes
            # on an integer grid. Side contact is NOT an accepted connection.
            if not any(
                prev.z + prev.dimensions()[2] == part.z and
                part.x < prev.x + prev.dimensions()[0] and prev.x < part.x + w and
                part.y < prev.y + prev.dimensions()[1] and prev.y < part.y + l
                for prev in self.accepted
            ):
                raise ValueError("NO_STUD_SUPPORT")
        elif part.z != 0:
            raise ValueError("FIRST_PART_NOT_ON_GROUND")
        self.accepted.append(part)
        return part

def build(parts):
    gate = PhysicalPlacementGate()
    for part in parts:
        gate.add(part)
    return gate
