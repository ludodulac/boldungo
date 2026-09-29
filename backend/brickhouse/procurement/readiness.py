"""Fail-closed order readiness checks.

A catalog identity alone is not enough to place an order. A supplier-ready line
also needs an explicit physical purchase color. This module keeps that boundary
machine-checkable so an incomplete order file cannot be presented as ready.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from .catalog import PartCrosswalk
from .models import CanonicalOrderPackage


class OrderReadinessBlocker(BaseModel):
    part_id: str = Field(min_length=1)
    semantic_color: str | None = None
    reason: str = Field(min_length=1)


class OrderReadinessReport(BaseModel):
    total_order_lines: int = Field(ge=0)
    part_identity_resolved_lines: int = Field(ge=0)
    purchase_color_resolved_lines: int = Field(ge=0)
    blockers: list[OrderReadinessBlocker]

    @property
    def supplier_ready(self) -> bool:
        return not self.blockers


def assess_order_readiness(
    package: CanonicalOrderPackage,
    crosswalk: PartCrosswalk,
    *,
    purchase_colors: dict[tuple[str, str | None], str] | None = None,
) -> OrderReadinessReport:
    """Assess whether every order line can safely enter a supplier exporter.

    purchase_colors is keyed by the exact canonical BOM line identity:
    (part_id, semantic_color). The value is a canonical physical color key.
    Supplier-specific color IDs are intentionally a later mapping layer.
    """

    mapped = crosswalk.by_engine_id()
    selected_colors = purchase_colors or {}
    blockers: list[OrderReadinessBlocker] = []
    part_ok = 0
    color_ok = 0

    for line in package.order_lines:
        key = (line.part_id, line.semantic_color)
        if line.part_id in mapped:
            part_ok += 1
        else:
            blockers.append(
                OrderReadinessBlocker(
                    part_id=line.part_id,
                    semantic_color=line.semantic_color,
                    reason="missing_verified_part_identity",
                )
            )

        color = selected_colors.get(key)
        if color:
            color_ok += 1
        else:
            blockers.append(
                OrderReadinessBlocker(
                    part_id=line.part_id,
                    semantic_color=line.semantic_color,
                    reason="missing_purchase_color",
                )
            )

    return OrderReadinessReport(
        total_order_lines=len(package.order_lines),
        part_identity_resolved_lines=part_ok,
        purchase_color_resolved_lines=color_ok,
        blockers=blockers,
    )
