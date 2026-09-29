"""User-facing procurement preparation diagnostics.

Unlike a supplier handoff, this report is allowed to exist while procurement is
blocked. Its purpose is to explain exactly what remains unresolved instead of
collapsing all failures into a generic "cannot order" state.
"""

from __future__ import annotations

import csv
from io import StringIO

from pydantic import BaseModel, Field

from brickhouse.building.models import Appearance

from .availability import PartColorAvailabilityRegistry, SupplierRoute
from .catalog import PartCrosswalk
from .color_resolution import (
    PurchaseColorResolutionReport,
    resolve_purchase_colors_from_appearance,
)
from .colors import ColorCrosswalk, load_color_crosswalk
from .models import CanonicalOrderPackage
from .readiness import OrderReadinessBlocker, OrderReadinessReport, assess_order_readiness


class ProcurementPreparationReport(BaseModel):
    schema_version: str = "0.1"
    route: SupplierRoute
    total_parts: int = Field(gt=0)
    total_order_lines: int = Field(gt=0)
    colors: PurchaseColorResolutionReport
    catalog_readiness: OrderReadinessReport
    live_readiness: OrderReadinessReport

    @property
    def document_ready(self) -> bool:
        return self.colors.complete and self.catalog_readiness.supplier_ready

    @property
    def live_order_ready(self) -> bool:
        return self.document_ready and self.live_readiness.supplier_ready


def build_procurement_preparation_report(
    package: CanonicalOrderPackage,
    part_crosswalk: PartCrosswalk,
    *,
    route: SupplierRoute,
    availability: PartColorAvailabilityRegistry,
    appearance: Appearance | None,
    color_crosswalk: ColorCrosswalk | None = None,
) -> ProcurementPreparationReport:
    """Explain color, catalog, live-stock, and quantity readiness separately."""

    colors = color_crosswalk or load_color_crosswalk()
    color_report = resolve_purchase_colors_from_appearance(
        package,
        appearance,
        color_crosswalk=colors,
    )
    selected = color_report.purchase_colors()

    catalog = assess_order_readiness(
        package,
        part_crosswalk,
        route=route,
        availability=availability,
        purchase_colors=selected,
        color_crosswalk=colors,
        require_live_availability=False,
    )
    live = assess_order_readiness(
        package,
        part_crosswalk,
        route=route,
        availability=availability,
        purchase_colors=selected,
        color_crosswalk=colors,
        require_live_availability=True,
    )
    return ProcurementPreparationReport(
        route=route,
        total_parts=package.total_parts,
        total_order_lines=len(package.order_lines),
        colors=color_report,
        catalog_readiness=catalog,
        live_readiness=live,
    )


def _blocker_key(blocker: OrderReadinessBlocker) -> tuple[str, str, str]:
    return (
        blocker.part_id,
        blocker.purchase_color_key or "",
        blocker.reason,
    )


def procurement_preparation_csv(report: ProcurementPreparationReport) -> str:
    """Render one auditable CSV combining all unresolved preparation layers."""

    rows: list[tuple[str, str, str, str, str]] = []

    for line in report.colors.lines:
        if line.status != "resolved_exact_catalog_key":
            rows.append(
                (
                    "color",
                    line.part_id,
                    line.source_color or "",
                    line.purchase_color_key or "",
                    line.status,
                )
            )

    for blocker in sorted(report.catalog_readiness.blockers, key=_blocker_key):
        rows.append(
            (
                "catalog",
                blocker.part_id,
                blocker.semantic_color or "",
                blocker.purchase_color_key or "",
                blocker.reason,
            )
        )

    live_reasons = {
        "live_part_color_availability_unverified",
        "available_quantity_unknown",
        "insufficient_available_quantity",
    }
    live_only = {
        _blocker_key(item): item
        for item in report.live_readiness.blockers
        if item.reason in live_reasons
    }
    for blocker in sorted(live_only.values(), key=_blocker_key):
        detail = blocker.semantic_color or ""
        if blocker.reason == "insufficient_available_quantity":
            detail = (
                f"required={blocker.required_quantity};"
                f"available={blocker.available_quantity};"
                f"shortage={blocker.shortage_quantity}"
            )
        elif blocker.reason == "available_quantity_unknown":
            detail = f"required={blocker.required_quantity};available=unknown"
        rows.append(
            (
                "live_stock",
                blocker.part_id,
                detail,
                blocker.purchase_color_key or "",
                blocker.reason,
            )
        )

    buffer = StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["layer", "part_id", "source_or_semantic_color", "purchase_color", "reason"])
    writer.writerows(rows)
    return buffer.getvalue()


def procurement_preparation_summary(report: ProcurementPreparationReport) -> str:
    """Concise machine-readable summary for UI/status files."""

    return (
        f"ROUTE={report.route}\n"
        f"TOTAL_PARTS={report.total_parts}\n"
        f"TOTAL_ORDER_LINES={report.total_order_lines}\n"
        f"COLOR_RESOLVED={report.colors.resolved_lines}\n"
        f"COLOR_UNRESOLVED={report.colors.unresolved_lines}\n"
        f"CATALOG_BLOCKERS={len(report.catalog_readiness.blockers)}\n"
        f"LIVE_BLOCKERS={len(report.live_readiness.blockers)}\n"
        f"QUANTITY_COVERED_LINES={report.live_readiness.quantity_covered_lines}\n"
        f"SHORTAGE_TOTAL={report.live_readiness.shortage_total}\n"
        f"DOCUMENT_READY={'YES' if report.document_ready else 'NO'}\n"
        f"LIVE_ORDER_READY={'YES' if report.live_order_ready else 'NO'}\n"
    )
