"""LEGO2-037: explicit two-part LDraw assembly candidates, not a clutch certificate.

The placement is concrete and reproducible. Collision/insertion are NOT inferred
from ring-axis alignment; they require complete transformed meshes.
"""
from dataclasses import dataclass
from brickhouse.bricks.lego30363_3020_experiment_036 import inspect_30363_on_3020

@dataclass(frozen=True)
class Part:
    lego_id: str
    x: int
    y: int
    z: int
    rotation_y_degrees: int = 0

@dataclass(frozen=True)
class Assembly:
    slope: Part
    plate: Part
    aligned_ring_axes: tuple[int, ...]
    status: str

def candidate(plate_x: int = 10, plate_z: int = -20, plate_y: int = 24) -> Assembly:
    """Positions in LDraw units, y down; 30363 at origin.

    plate_y=24 is an exploratory translation, NOT a solved insertion height.
    """
    alignment = inspect_30363_on_3020(plate_x, plate_z)
    return Assembly(
        Part("30363", 0, 0, 0),
        Part("3020", plate_x, plate_y, plate_z),
        alignment["ring_axes_z_ldu"],
        "AXES_ALIGNED_ONLY" if alignment["axis_alignment"] else "AXES_MISALIGNED",
    )

def ldraw_lines(assembly: Assembly) -> str:
    """A viewable LDraw model; the 3020 reference must resolve in the viewer."""
    return "\n".join([
        "0 LEGO2-037 exploratory 30363 / 3020 geometry; NOT CERTIFIED",
        f"1 16 {assembly.slope.x} {assembly.slope.y} {assembly.slope.z} 1 0 0 0 1 0 0 0 1 30363.dat",
        f"1 4 {assembly.plate.x} {assembly.plate.y} {assembly.plate.z} 1 0 0 0 1 0 0 0 1 3020.dat",
        "0",
    ]) + "\n"

def gate(assembly: Assembly) -> dict:
    """Fail closed until solid collision and insertion have actual evidence."""
    return {
        "axis_alignment": assembly.status,
        "solid_collision": "NOT_COMPUTED",
        "insertion_path": "NOT_COMPUTED",
        "clutch_strength": "NOT_MEASURED",
        "ready_for_guided004": False,
    }
