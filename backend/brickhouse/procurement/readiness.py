"""Fail-closed order readiness checks.

A catalog identity alone is not enough to place an order. A supplier-ready line
also needs an explicit physical purchase color and a verified part/color
availability assertion for the target procurement route.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from .catalog import PartCrosswalk
from .colors import ColorCrosswalk, load_color_crosswalk
from .models import CanonicalOrderPackage


class OrderReadinessBlocker(BaseModel):
    part_id: str = Field(min_length=1)
    semantic_color: str | None = None
    purchase_color_key: str | None = None
    reason: str = Field(min_length=1)


class OrderReadinessReport(BaseModel):
    total_order_lines: int = Field(ge=0)
    part_identity_resolved_lines: int = Field(ge=0)
    purchase_color_resolved_lines: int = Field(ge=0)
    part_color_verified_lines: int = Field(ge=0)
    blockers: list[OrderReadinessBlocker]

    @property
    def supplier_ready(self) -> bool:
        return not self.blockers


def assess_order_readiness(
    package: CanonicalOrderPackage,
    crosswalk: PartCrosswalk,
    *,
    purchase_colors: dict[tuple[str, str | None], str] | None = None,
    color_crosswalk: ColorCrosswalk | None = None,
    verified_part_colors: set[tuple[str, str]] | None = None,
) -> OrderReadinessReport:
    """Assess whether every order line can safely enter a supplier exporter.

    purchase_colors is keyed by the exact canonical BOM line identity:
    (part_id, semantic_color). Its value is a canonical physical color key.

    verified_part_colors contains (part_id, canonical_color_key) pairs whose
    physical/catalog availability has been checked for the intended route.
    This explicit input prevents a known color from being mistaken for proof
    that every part is actually obtainable in that color.
    """

    mapped = crosswalk.by_engine_id()
    colors = (color_crosswalk or load_color_crosswalk()).by_key()
    selected_colors = purchase_colors or {}
    verified = verified_part_colors or set()

    blockers: list[OrderReadinessBlocker] = []
    part_ok = 0
    color_ok = 0
    availability_ok = 0

    for line in package.order_lines:
        key = (line.part_id, line.semantic_color)
        part_mapped = line.part_id in mapped
        if part_mapped:
            part_ok += 1
        else:
            blockers.append(
                OrderReadinessBlocker(
                    part_id=line.part_id,
                    semantic_color=line.semantic_color,
                    reason="missing_verified_part_identity",
                )
            )

        color_key = selected_colors.get(key)
        if not color_key:
            blockers.append(
                OrderReadinessBlocker(
                    part_id=line.part_id,
                    semantic_color=line.semantic_color,
                    reason="missing_purchase_color",
                )
            )
            continue

        if color_key not in colors:
            blockers.append(
                OrderReadinessBlocker(
                    part_id=line.part_id,
                    semantic_color=line.semantic_color,
                    purchase_color_key=color_key,
                    reason="unknown_purchase_color",
                )
            )
            continue

        color_ok += 1

        if (line.part_id, color_key) not in verified:
            blockers.append(
                OrderReadinessBlocker(
                    part_id=line.part_id,
                    semantic_color=line.semantic_color,
                    purchase_color_key=color_key,
                    reason="part_color_availability_unverified",
                )
            )
            continue

        availability_ok += 1

    return OrderReadinessReport(
        total_order_lines=len(package.order_lines),
        part_identity_resolved_lines=part_ok,
        purchase_color_resolved_lines=color_ok,
        part_color_verified_lines=availability_ok,
        blockers=blockers,
    )
