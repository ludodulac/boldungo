"""Fail-closed order readiness checks."""

from __future__ import annotations

from pydantic import BaseModel, Field

from .availability import PartColorAvailabilityRegistry, SupplierRoute
from .catalog import PartCrosswalk
from .colors import ColorCrosswalk, load_color_crosswalk
from .models import CanonicalOrderPackage, OrderLine
from .physical import PhysicalRequirement, aggregate_physical_requirements


class OrderReadinessBlocker(BaseModel):
    part_id: str = Field(min_length=1)
    semantic_color: str | None = None
    purchase_color_key: str | None = None
    reason: str = Field(min_length=1)
    required_quantity: int | None = Field(default=None, gt=0)
    available_quantity: int | None = Field(default=None, ge=0)
    shortage_quantity: int = Field(default=0, ge=0)


class OrderReadinessReport(BaseModel):
    route: SupplierRoute
    total_order_lines: int = Field(ge=0)
    total_physical_requirements: int = Field(ge=0)
    part_identity_resolved_lines: int = Field(ge=0)
    purchase_color_resolved_lines: int = Field(ge=0)
    part_color_verified_lines: int = Field(ge=0)
    quantity_covered_lines: int = Field(ge=0)
    shortage_total: int = Field(ge=0)
    require_live_availability: bool = False
    physical_requirements: list[PhysicalRequirement] = Field(default_factory=list)
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
    """Assess one route after canonical lines are aggregated physically."""

    mapped = crosswalk.by_engine_id()
    color_catalog = color_crosswalk or load_color_crosswalk()
    colors = color_catalog.by_key()
    selected_colors = purchase_colors or {}

    blockers: list[OrderReadinessBlocker] = []
    part_ok = 0
    color_ok = 0
    availability_ok = 0
    quantity_covered = 0
    shortage_total = 0
    valid_lines: list[OrderLine] = []

    for line in package.order_lines:
        key = (line.part_id, line.semantic_color)
        if line.part_id not in mapped:
            blockers.append(
                OrderReadinessBlocker(
                    part_id=line.part_id,
                    semantic_color=line.semantic_color,
                    reason="missing_verified_part_identity",
                )
            )
            continue

        part = mapped[line.part_id]
        if route == "bricklink" and not part.bricklink_item_no:
            blockers.append(
                OrderReadinessBlocker(
                    part_id=line.part_id,
                    semantic_color=line.semantic_color,
                    reason="missing_bricklink_item_no",
                )
            )
            continue
        if route == "wobrick":
            if not part.bricklink_item_no:
                blockers.append(
                    OrderReadinessBlocker(
                        part_id=line.part_id,
                        semantic_color=line.semantic_color,
                        reason="missing_bricklink_item_no",
                    )
                )
                continue
            if not part.ldraw_id:
                blockers.append(
                    OrderReadinessBlocker(
                        part_id=line.part_id,
                        semantic_color=line.semantic_color,
                        reason="missing_ldraw_id",
                    )
                )
                continue

        part_ok += 1

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
        valid_lines.append(line)

    physical_requirements = aggregate_physical_requirements(
        valid_lines,
        part_crosswalk=crosswalk,
        color_crosswalk=color_catalog,
        purchase_colors=selected_colors,
    )

    for requirement in physical_requirements:
        evidence = availability.evidence_for(
            route,
            requirement.part_id,
            requirement.purchase_color_key,
        )

        # Document/export readiness depends only on resolvable export identities,
        # colors and exact quantities. Supplier availability is a separate layer.
        if not require_live_availability:
            if evidence is not None:
                availability_ok += 1
            continue

        if evidence is None or evidence.status != "live_available":
            blockers.append(
                OrderReadinessBlocker(
                    part_id=requirement.part_id,
                    purchase_color_key=requirement.purchase_color_key,
                    reason="live_part_color_availability_unverified",
                    required_quantity=requirement.required_quantity,
                )
            )
            continue

        availability_ok += 1

        if evidence.available_quantity is None:
            blockers.append(
                OrderReadinessBlocker(
                    part_id=requirement.part_id,
                    purchase_color_key=requirement.purchase_color_key,
                    reason="available_quantity_unknown",
                    required_quantity=requirement.required_quantity,
                )
            )
            continue

        if evidence.observed_at is None:
            blockers.append(
                OrderReadinessBlocker(
                    part_id=requirement.part_id,
                    purchase_color_key=requirement.purchase_color_key,
                    reason="live_quantity_observation_time_missing",
                    required_quantity=requirement.required_quantity,
                    available_quantity=evidence.available_quantity,
                )
            )
            continue

        if evidence.available_quantity < requirement.required_quantity:
            shortage = requirement.required_quantity - evidence.available_quantity
            shortage_total += shortage
            blockers.append(
                OrderReadinessBlocker(
                    part_id=requirement.part_id,
                    purchase_color_key=requirement.purchase_color_key,
                    reason="insufficient_available_quantity",
                    required_quantity=requirement.required_quantity,
                    available_quantity=evidence.available_quantity,
                    shortage_quantity=shortage,
                )
            )
            continue

        quantity_covered += 1

    return OrderReadinessReport(
        route=route,
        total_order_lines=len(package.order_lines),
        total_physical_requirements=len(physical_requirements),
        part_identity_resolved_lines=part_ok,
        purchase_color_resolved_lines=color_ok,
        part_color_verified_lines=availability_ok,
        quantity_covered_lines=quantity_covered,
        shortage_total=shortage_total,
        require_live_availability=require_live_availability,
        physical_requirements=physical_requirements,
        blockers=blockers,
    )
