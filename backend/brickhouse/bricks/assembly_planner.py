"""Conservative planning signals for future autonomous assembly ordering.

This module does not replace AssemblyPlan. It extracts only facts justified by
the current BrickModel: rectangular footprint overlap and direct vertical
support. Ergonomics, insertion paths and global stability are deliberately not
inferred from final placement geometry alone.
"""
from __future__ import annotations
from dataclasses import dataclass
import re
from .brick_model import BrickModel, BrickModelPart

@dataclass(frozen=True)
class PartFootprint:
    placement_id: str
    x0: int
    x1: int
    y0: int
    y1: int
    z0: int
    z1: int

def _dimensions(part: BrickModelPart) -> tuple[int, int, int]:
    match = re.search(r"_(\d+)X(\d+)(?:X(\d+))?(?:_|$)", part.part_id)
    if not match:
        raise ValueError(f"Cannot derive dimensions for {part.part_id!r}")
    width, depth = int(match.group(1)), int(match.group(2))
    if part.rotation_quarter_turns % 2:
        width, depth = depth, width
    if part.category in {"window_frame", "window_pane"}:
        height = int(match.group(3) or 1) * 3
    elif part.category in {"roof_tile", "ridge_tile"}:
        height = 1
    else:
        height = 3
    return width, depth, height

def footprint(part: BrickModelPart) -> PartFootprint:
    width, depth, height = _dimensions(part)
    return PartFootprint(part.placement_id, part.x_studs, part.x_studs + width,
                         part.y_studs, part.y_studs + depth,
                         part.z_plates, part.z_plates + height)

def _overlap_area(a: PartFootprint, b: PartFootprint) -> int:
    return max(0, min(a.x1, b.x1) - max(a.x0, b.x0)) * max(0, min(a.y1, b.y1) - max(a.y0, b.y0))

def direct_support_graph(model: BrickModel) -> dict[str, tuple[str, ...]]:
    """Map each non-roof placement to directly touching supports below it.

    Empty means no support proven in this limited scope, not impossible.
    Sloped roof geometry is intentionally excluded until it has its own
    evidence-backed contact model.
    """
    parts = [p for p in model.parts if p.category not in {"roof_tile", "ridge_tile"}]
    boxes = {p.placement_id: footprint(p) for p in parts}
    result = {}
    for part in parts:
        current = boxes[part.placement_id]
        result[part.placement_id] = tuple(sorted(
            other.placement_id for other in parts
            if other.placement_id != part.placement_id
            and boxes[other.placement_id].z1 == current.z0
            and _overlap_area(boxes[other.placement_id], current) > 0
        ))
    return result

def support_dependencies(model: BrickModel) -> dict[str, tuple[str, ...]]:
    """First safe dependency signal for a later Assembly Planner."""
    return direct_support_graph(model)
