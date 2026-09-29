"""Product-facing procurement choices for "Commander mes pièces".

This module hides supplier file formats and procurement internals behind two
simple route options. It derives readiness from the existing procurement
diagnostics and delegates actual dossier generation to SupplierHandoffPackage.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from brickhouse.building.models import Appearance

from .availability import PartColorAvailabilityRegistry
from .catalog import PartCrosswalk
from .colors import ColorCrosswalk, load_color_crosswalk
from .diagnostics import ProcurementPreparationReport, build_procurement_preparation_report
from .models import CanonicalOrderPackage
from .supplier_package import (
    ExportableRoute,
    SupplierHandoffPackage,
    generate_supplier_handoff_package,
)


BlockerLayer = Literal["document", "live"]


class UserOrderBlocker(BaseModel):
    layer: BlockerLayer
    code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    part_id: str | None = None
    purchase_color_key: str | None = None
    shortage_quantity: int | None = Field(default=None, ge=0)


class UserOrderRouteOption(BaseModel):
    route: ExportableRoute
    label: str = Field(min_length=1)
    document_ready: bool
    live_order_ready: bool
    total_parts: int = Field(gt=0)
    total_bags: int = Field(gt=0)
    blockers: list[UserOrderBlocker]


class UserOrderOptions(BaseModel):
    schema_version: str = "0.1"
    building_id: str = Field(min_length=1)
    total_parts: int = Field(gt=0)
    total_bags: int = Field(gt=0)
    options: list[UserOrderRouteOption] = Field(min_length=2, max_length=2)

    @model_validator(mode="after")
    def validate_routes_and_totals(self) -> "UserOrderOptions":
        routes = [option.route for option in self.options]
        if routes != ["bricklink", "wobrick"]:
            raise ValueError("user order options must expose bricklink then wobrick")
        for option in self.options:
            if option.total_parts != self.total_parts:
                raise ValueError("route option total_parts must match canonical package")
            if option.total_bags != self.total_bags:
                raise ValueError("route option total_bags must match canonical package")
        return self

    def for_route(self, route: ExportableRoute) -> UserOrderRouteOption:
        return next(option for option in self.options if option.route == route)


_LABELS: dict[ExportableRoute, str] = {
    "bricklink": "Commander en LEGO via BrickLink",
    "wobrick": "Commander en briques compatibles",
}


def _document_message(code: str, part_id: str, color: str | None) -> str:
    if code == "missing_architectural_color":
        return f"Couleur physique à résoudre pour {part_id}."
    if code == "noncanonical_architectural_color":
        return f"Couleur physique « {color or '?'} » à résoudre pour {part_id}."
    if code == "missing_verified_part_identity":
        return f"Référence pièce à résoudre pour {part_id}."
    if code == "missing_purchase_color":
        return f"Couleur physique à résoudre pour {part_id}."
    if code == "unknown_purchase_color":
        return f"Couleur physique non reconnue pour {part_id}: {color or '?'}."
    if code == "part_color_availability_unverified_for_route":
        return f"Référence/couleur fournisseur à vérifier pour {part_id} / {color or '?'}."
    return f"Commande à finaliser pour {part_id}: {code}."


def _live_message(report_blocker) -> str:
    part_id = report_blocker.part_id
    color = report_blocker.purchase_color_key or "?"
    if report_blocker.reason == "live_part_color_availability_unverified":
        return f"Stock live non vérifié pour {part_id} / {color}."
    if report_blocker.reason == "available_quantity_unknown":
        return f"Quantité disponible inconnue pour {part_id} / {color}."
    if report_blocker.reason == "live_quantity_observation_time_missing":
        return f"Date d’observation du stock manquante pour {part_id} / {color}."
    if report_blocker.reason == "insufficient_available_quantity":
        return (
            f"Stock insuffisant pour {part_id} / {color}: "
            f"manque {report_blocker.shortage_quantity} pièce(s)."
        )
    return f"Stock à vérifier pour {part_id} / {color}: {report_blocker.reason}."


def _user_blockers(report: ProcurementPreparationReport) -> list[UserOrderBlocker]:
    blockers: list[UserOrderBlocker] = []
    seen: set[tuple[str, str | None, str | None, str]] = set()

    def add(item: UserOrderBlocker) -> None:
        key = (item.code, item.part_id, item.purchase_color_key, item.layer)
        if key not in seen:
            seen.add(key)
            blockers.append(item)

    for line in report.colors.lines:
        if line.status == "resolved_exact_catalog_key":
            continue
        add(
            UserOrderBlocker(
                layer="document",
                code=line.status,
                message=_document_message(line.status, line.part_id, line.source_color),
                part_id=line.part_id,
                purchase_color_key=line.purchase_color_key,
            )
        )

    for blocker in report.catalog_readiness.blockers:
        add(
            UserOrderBlocker(
                layer="document",
                code=blocker.reason,
                message=_document_message(
                    blocker.reason,
                    blocker.part_id,
                    blocker.purchase_color_key or blocker.semantic_color,
                ),
                part_id=blocker.part_id,
                purchase_color_key=blocker.purchase_color_key,
            )
        )

    live_reasons = {
        "live_part_color_availability_unverified",
        "available_quantity_unknown",
        "live_quantity_observation_time_missing",
        "insufficient_available_quantity",
    }
    for blocker in report.live_readiness.blockers:
        if blocker.reason not in live_reasons:
            continue
        add(
            UserOrderBlocker(
                layer="live",
                code=blocker.reason,
                message=_live_message(blocker),
                part_id=blocker.part_id,
                purchase_color_key=blocker.purchase_color_key,
                shortage_quantity=blocker.shortage_quantity or None,
            )
        )

    return blockers


def build_user_order_options(
    package: CanonicalOrderPackage,
    part_crosswalk: PartCrosswalk,
    *,
    availability: PartColorAvailabilityRegistry,
    appearance: Appearance | None,
    color_crosswalk: ColorCrosswalk | None = None,
) -> UserOrderOptions:
    """Build the product-facing BrickLink and Wobrick choices from existing diagnostics."""

    colors = color_crosswalk or load_color_crosswalk()
    options: list[UserOrderRouteOption] = []

    for route in ("bricklink", "wobrick"):
        report = build_procurement_preparation_report(
            package,
            part_crosswalk,
            route=route,
            availability=availability,
            appearance=appearance,
            color_crosswalk=colors,
        )
        options.append(
            UserOrderRouteOption(
                route=route,
                label=_LABELS[route],
                document_ready=report.document_ready,
                live_order_ready=report.live_order_ready,
                total_parts=package.total_parts,
                total_bags=package.total_bags,
                blockers=_user_blockers(report),
            )
        )

    return UserOrderOptions(
        building_id=package.building_id,
        total_parts=package.total_parts,
        total_bags=package.total_bags,
        options=options,
    )


def generate_handoff_from_user_order_option(
    option: UserOrderRouteOption,
    package: CanonicalOrderPackage,
    part_crosswalk: PartCrosswalk,
    *,
    availability: PartColorAvailabilityRegistry,
    appearance: Appearance | None,
    color_crosswalk: ColorCrosswalk | None = None,
) -> SupplierHandoffPackage:
    """Generate the existing supplier dossier for one document-ready product option."""

    if not option.document_ready:
        raise ValueError("user order option is not document-ready")

    if option.total_parts != package.total_parts or option.total_bags != package.total_bags:
        raise ValueError("user order option no longer matches the canonical package")

    colors = color_crosswalk or load_color_crosswalk()
    report = build_procurement_preparation_report(
        package,
        part_crosswalk,
        route=option.route,
        availability=availability,
        appearance=appearance,
        color_crosswalk=colors,
    )
    if not report.document_ready:
        raise ValueError("supplier dossier generation blocked by current document readiness")

    return generate_supplier_handoff_package(
        package,
        part_crosswalk,
        route=option.route,
        purchase_colors=report.colors.purchase_colors(),
        availability=availability,
        color_crosswalk=colors,
    )
