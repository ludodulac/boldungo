"""Evidence-based 30363 underside / 3020 top-stud alignment experiment.

Coordinates are LDraw units (20 per stud, 8 per plate); Y increases downward.
The source mesh proves annular geometry, NOT clutch force or insertion clearance.
Sources: Debian ldraw-parts 1802+ds-1 parts/30363.dat and parts/s/30363s01.dat.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class UndersideRing:
    z_ldu: int
    y_ldu: float
    primitive: str
    # LDraw primitive transform row 2 (local vertical direction).
    vertical_scale: float

# Actual type-1 lines in 30363s01.dat; note paired primitives at -30/-50.
RINGS = (
    UndersideRing(-10, 6.667, "stud4a.dat", -4.333),
    UndersideRing(-30, 13.334, "stud4s.dat", 2.667),
    UndersideRing(-30, 13.344, "stud4a.dat", -2.656),
    UndersideRing(-50, 20.0, "stud4s.dat", 2.667),
    UndersideRing(-50, 20.0, "stud4a.dat", -1.0),
)
# 3020 plate has 2 x 4 studs, pitch 20 LDU; stud centre locations
# relative to its own centre (top face at y=0).
PLATE_3020_STUD_CENTRES = tuple(
    (x, z) for x in (-10, 10) for z in (-30, -10, 10, 30)
)

def candidate_ring_alignment(plate_dx=0, plate_dz=0):
    """Match ring axes with 3020 stud axes; no clutch certification."""
    axes = {(plate_dx + x, plate_dz + z) for x, z in PLATE_3020_STUD_CENTRES}
    return tuple(r for r in RINGS if (0, r.z_ldu) in axes)

def inspect_30363_on_3020(plate_dx=10, plate_dz=-20):
    """Report geometric alignment separately from unverified physical insertion.

    30363 has a central underside ring axis x=0. A 3020 shifted by +10
    LDU centres one column of its studs on that axis. z shift -20 aligns
    studs at -50,-30,-10,+10. This is an axis-only candidate.
    """
    matched = candidate_ring_alignment(plate_dx, plate_dz)
    return {
        "slope_part": "30363",
        "support_part": "3020",
        "plate_translation_ldu": (plate_dx, plate_dz),
        "ring_axes_z_ldu": tuple(sorted({r.z_ldu for r in matched})),
        "axis_alignment": bool(matched),
        "dimension_clearance": "UNVERIFIED",
        "solid_collision": "UNVERIFIED",
        "insertion": "UNVERIFIED",
        "clutch": "UNVERIFIED",
        "mechanically_certified": False,
    }
