"""Fail-closed order readiness checks."""

from __future__ import annotations

from pydantic import BaseModel, Field

from .availability import PartColorAvailabilityRegistry, SupplierRoute
from .catalog import PartCrosswalk
from .colors import ColorCrosswalk, load_color_crosswalk
from .models import CanonicalOrderPackage


class OrderReadinessBlocker(BaseModel):
    part_id: str = Field(min_length=1)
    semantic_color: str | None = None
    purchase_color_key: str | None = None
    reason: str = Field(min_length=1)


class OrderReadinessReport(BaseModel):
    route: SupplierRoute
    total_order_lines: int = Field(ge=0)
    part_identity_resolved_lines: int = Field(ge=0)
    purchase_color_resolved_lines: int = Field(ge=0)
    part_color_verified_lines: int = Field(ge=0)
    require_live_availability: bool = False
    blockers: list[OrderReadinessBlocker]

    @property
    def supplier_ready(self) -> bool:
        return not self.blockers


def assess_order_readiness(
    package: CanonicalOrderPackage,
    crosswalk: PartCrosswalk,
    *,
    route: SupplierRoute,
    availability: PartColorAvailabilityRegistry,
    purchase_colors: dict[tuple[str, str | None], str] | None = None,
    color_crosswalk: ColorCrosswalk | None = None,
    require_live_availability: bool = False,
) -> OrderReadinessReport:
    """Assess whether every order line is valid for one specific supplier route."""

    mapped = crosswalk.by_engine_id()
    colors = (color_crosswalk or load_color_crosswalk()).by_key()
    selected_colors = purchase_colors or {}

    blockers: list[OrderReadinessBlocker] = []
    part_ok = 0
    color_ok = 0
    availability_ok = 0

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

        if not availability.supports(
            route,
            line.part_id,
            color_key,
            require_live=require_live_availability,
        ):
            blockers.append(
                OrderReadinessBlocker(
                    part_id=line.part_id,
                    semantic_color=line.semantic_color,
                    purchase_color_key=color_key,
                    reason=(
                        "live_part_color_availability_unverified"
                        if require_live_availability
                        else "part_color_availability_unverified_for_route"
                    ),
                )
            )
            continue

        availability_ok += 1

    return OrderReadinessReport(
        route=route,
        total_order_lines=len(package.order_lines),
        part_identity_resolved_lines=part_ok,
        purchase_color_resolved_lines=color_ok,
        part_color_verified_lines=availability_ok,
        require_live_availability=require_live_availability,
        blockers=blockers,
    )
