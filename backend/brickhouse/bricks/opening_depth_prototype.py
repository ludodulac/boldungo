"""Prototype a representation-only recessed opening on the LEGO stud grid.

This does not infer architectural wall depth. It moves only an already emitted
window closure one stud inward so the existing one-stud wall thickness can be
read visually as a reveal. The source architecture is unchanged.
"""
from __future__ import annotations

from brickhouse.building.models import Facade
from .brick_model import BrickModel

_INWARD = {
    Facade.FRONT: (0, 1),
    Facade.REAR: (0, -1),
    Facade.LEFT: (1, 0),
    Facade.RIGHT: (-1, 0),
}


def recess_opening_closure_for_prototype(
    model: BrickModel,
    *,
    opening_id: str,
    depth_studs: int = 1,
) -> BrickModel:
    """Return a prototype BrickModel with one known opening closure recessed.

    depth_studs is a LEGO representation choice, not a recovered metric.
    Only real emitted frame/pane placements are translated. Wall masonry,
    architectural dimensions and opening identity remain unchanged.
    """
    if depth_studs != 1:
        raise ValueError("prototype supports exactly one stud of representation depth")

    targets = [
        part for part in model.parts
        if part.opening_id == opening_id and part.category in {"window_frame", "window_pane"}
    ]
    if not targets:
        raise ValueError(f"opening {opening_id!r} has no emitted window closure")
    facades = {part.facade for part in targets}
    if len(facades) != 1 or None in facades:
        raise ValueError("prototype opening closure must belong to exactly one facade")
    facade = next(iter(facades))
    dx, dy = _INWARD[facade]

    shifted = []
    for part in model.parts:
        if part in targets:
            x = part.x_studs + dx
            y = part.y_studs + dy
            if x < 0 or y < 0:
                raise ValueError("prototype recess would leave the model grid")
            part = part.model_copy(update={"x_studs": x, "y_studs": y})
        shifted.append(part)
    return model.model_copy(update={"parts": shifted})
