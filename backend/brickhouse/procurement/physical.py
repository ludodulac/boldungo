"""Shared physical procurement aggregation.

Canonical order lines keep semantic/provenance distinctions. This module provides
only the downstream physical view used when one supplier stock quantity must be
compared once against the total requirement for the same part and purchase color.
"""

from __future__ import annotations

from collections import Counter

from pydantic import BaseModel, Field

from .catalog import PartCrosswalk
from .colors import ColorCrosswalk
from .models import OrderLine


class PhysicalRequirement(BaseModel):
    part_id: str = Field(min_length=1)
    supplier_part_ref: str = Field(min_length=1)
    purchase_color_key: str = Field(min_length=1)
    supplier_color_id: int = Field(ge=0)
    supplier_color_name: str = Field(min_length=1)
    required_quantity: int = Field(gt=0)

    @property
    def identity(self) -> tuple[str, str]:
        return (self.part_id, self.purchase_color_key)


def aggregate_physical_requirements(
    lines: list[OrderLine],
    *,
    part_crosswalk: PartCrosswalk,
    color_crosswalk: ColorCrosswalk,
    purchase_colors: dict[tuple[str, str | None], str],
) -> list[PhysicalRequirement]:
    """Aggregate canonical lines by resolved physical part + purchase color."""

    parts = part_crosswalk.by_engine_id()
    colors = color_crosswalk.by_key()
    counts: Counter[tuple[str, str]] = Counter()

    for line in lines:
        color_key = purchase_colors[(line.part_id, line.semantic_color)]
        counts[(line.part_id, color_key)] += line.quantity

    requirements: list[PhysicalRequirement] = []
    for (part_id, color_key), required_quantity in sorted(counts.items()):
        part = parts[part_id]
        color = colors[color_key]
        requirements.append(
            PhysicalRequirement(
                part_id=part_id,
                supplier_part_ref=part.bricklink_item_no,
                purchase_color_key=color_key,
                supplier_color_id=color.bricklink_color_id,
                supplier_color_name=color.bricklink_name,
                required_quantity=required_quantity,
            )
        )
    return requirements
