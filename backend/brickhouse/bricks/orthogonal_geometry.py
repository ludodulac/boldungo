"""Canonical geometry and collision checks for orthogonal stud/tube pieces."""
from __future__ import annotations

from dataclasses import dataclass

from .brick_model import BrickModel, BrickModelPart
from .catalog import standard_orthogonal_definitions


@dataclass(frozen=True)
class OrthogonalBounds:
    placement_id: str
    x0: int
    x1: int
    y0: int
    y1: int
    z0: int
    z1: int


def orthogonal_bounds(part: BrickModelPart) -> OrthogonalBounds | None:
    definition = standard_orthogonal_definitions().get(part.part_id)
    if definition is None or part.category not in {"brick", "plate"}:
        return None
    width, length = definition.footprint(part.rotation_quarter_turns)
    return OrthogonalBounds(
        placement_id=part.placement_id,
        x0=part.x_studs,
        x1=part.x_studs + width,
        y0=part.y_studs,
        y1=part.y_studs + length,
        z0=part.z_plates,
        z1=part.z_plates + definition.height_plates,
    )


def _overlap(a0: int, a1: int, b0: int, b1: int) -> bool:
    return max(a0, b0) < min(a1, b1)


def orthogonal_collisions(model: BrickModel) -> list[tuple[str, str]]:
    bounds = [item for part in model.parts if (item := orthogonal_bounds(part)) is not None]
    collisions: list[tuple[str, str]] = []
    for index, first in enumerate(bounds):
        for second in bounds[index + 1:]:
            if (
                _overlap(first.x0, first.x1, second.x0, second.x1)
                and _overlap(first.y0, first.y1, second.y0, second.y1)
                and _overlap(first.z0, first.z1, second.z0, second.z1)
            ):
                collisions.append(tuple(sorted((first.placement_id, second.placement_id))))
    return sorted(collisions)


def validate_orthogonal_collisions(model: BrickModel) -> None:
    collisions = orthogonal_collisions(model)
    if collisions:
        pairs = ", ".join(f"{a}/{b}" for a, b in collisions)
        raise ValueError(f"BrickModel contains colliding orthogonal placements: {pairs}")
