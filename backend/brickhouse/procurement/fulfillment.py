"""Supplier fulfillment confirmation and exact-quantity validation.

The outgoing order proves what Boldüngo requests. This module separately proves
what a supplier says it can actually fulfill. A kit is never marked confirmed
complete from an order document alone.
"""

from __future__ import annotations

import csv
from collections import Counter
from io import StringIO
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from .catalog import PartCrosswalk
from .models import CanonicalOrderPackage


FulfillmentStatus = Literal[
    "pending",
    "exact_confirmed",
    "unavailable",
    "substitution_proposed",
]


class SupplierConfirmationLine(BaseModel):
    part_id: str = Field(min_length=1)
    supplier_part_ref: str = Field(min_length=1)
    purchase_color_key: str = Field(min_length=1)
    required_quantity: int = Field(gt=0)
    confirmed_quantity: int = Field(ge=0)
    status: FulfillmentStatus
    notes: str | None = None


class FulfillmentBlocker(BaseModel):
    part_id: str = Field(min_length=1)
    purchase_color_key: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    required_quantity: int = Field(gt=0)
    confirmed_quantity: int = Field(ge=0)


class FulfillmentReport(BaseModel):
    schema_version: str = "0.1"
    total_required_parts: int = Field(gt=0)
    exact_confirmed_parts: int = Field(ge=0)
    blockers: list[FulfillmentBlocker]

    @property
    def complete(self) -> bool:
        return not self.blockers and self.exact_confirmed_parts == self.total_required_parts


def _expected_physical_lines(
    package: CanonicalOrderPackage,
    part_crosswalk: PartCrosswalk,
    purchase_colors: dict[tuple[str, str | None], str],
) -> dict[tuple[str, str], tuple[str, int]]:
    parts = part_crosswalk.by_engine_id()
    counts: Counter[tuple[str, str]] = Counter()
    for line in package.order_lines:
        color_key = purchase_colors[(line.part_id, line.semantic_color)]
        counts[(line.part_id, color_key)] += line.quantity
    return {
        key: (parts[key[0]].bricklink_item_no, quantity)
        for key, quantity in counts.items()
    }


def supplier_confirmation_template_csv(
    package: CanonicalOrderPackage,
    part_crosswalk: PartCrosswalk,
    *,
    purchase_colors: dict[tuple[str, str | None], str],
) -> str:
    """Create a pre-filled confirmation sheet; supplier fields start pending."""

    expected = _expected_physical_lines(package, part_crosswalk, purchase_colors)
    buffer = StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow([
        "boldungo_part_id",
        "supplier_part_ref",
        "purchase_color",
        "required_quantity",
        "confirmed_quantity",
        "status",
        "notes",
    ])
    for (part_id, color_key), (supplier_ref, required) in sorted(expected.items()):
        writer.writerow([
            part_id,
            supplier_ref,
            color_key,
            required,
            "",
            "pending",
            "",
        ])
    return buffer.getvalue()


def parse_supplier_confirmation_csv(text: str) -> list[SupplierConfirmationLine]:
    """Parse the supplier-returned sheet without treating blanks as confirmation."""

    rows = list(csv.DictReader(StringIO(text)))
    lines: list[SupplierConfirmationLine] = []
    for row in rows:
        raw_confirmed = (row.get("confirmed_quantity") or "").strip()
        lines.append(
            SupplierConfirmationLine(
                part_id=(row.get("boldungo_part_id") or "").strip(),
                supplier_part_ref=(row.get("supplier_part_ref") or "").strip(),
                purchase_color_key=(row.get("purchase_color") or "").strip(),
                required_quantity=int(row.get("required_quantity") or 0),
                confirmed_quantity=int(raw_confirmed) if raw_confirmed else 0,
                status=(row.get("status") or "pending").strip(),
                notes=(row.get("notes") or "").strip() or None,
            )
        )
    return lines


def validate_supplier_confirmation(
    package: CanonicalOrderPackage,
    part_crosswalk: PartCrosswalk,
    *,
    purchase_colors: dict[tuple[str, str | None], str],
    confirmation_lines: list[SupplierConfirmationLine],
) -> FulfillmentReport:
    """Require exact reference/color/quantity confirmation for every physical line."""

    expected = _expected_physical_lines(package, part_crosswalk, purchase_colors)
    supplied: dict[tuple[str, str], SupplierConfirmationLine] = {}
    blockers: list[FulfillmentBlocker] = []
    exact_total = 0

    for line in confirmation_lines:
        key = (line.part_id, line.purchase_color_key)
        if key in supplied:
            raise ValueError(f"duplicate supplier confirmation line for {key!r}")
        supplied[key] = line

    for key, (supplier_ref, required) in sorted(expected.items()):
        part_id, color_key = key
        line = supplied.get(key)
        if line is None:
            blockers.append(FulfillmentBlocker(
                part_id=part_id,
                purchase_color_key=color_key,
                reason="missing_supplier_confirmation",
                required_quantity=required,
                confirmed_quantity=0,
            ))
            continue

        if line.supplier_part_ref != supplier_ref:
            blockers.append(FulfillmentBlocker(
                part_id=part_id,
                purchase_color_key=color_key,
                reason="supplier_part_reference_changed",
                required_quantity=required,
                confirmed_quantity=line.confirmed_quantity,
            ))
            continue

        if line.required_quantity != required:
            blockers.append(FulfillmentBlocker(
                part_id=part_id,
                purchase_color_key=color_key,
                reason="required_quantity_changed",
                required_quantity=required,
                confirmed_quantity=line.confirmed_quantity,
            ))
            continue

        if line.status == "substitution_proposed":
            blockers.append(FulfillmentBlocker(
                part_id=part_id,
                purchase_color_key=color_key,
                reason="substitution_requires_explicit_approval",
                required_quantity=required,
                confirmed_quantity=line.confirmed_quantity,
            ))
            continue

        if line.status != "exact_confirmed":
            blockers.append(FulfillmentBlocker(
                part_id=part_id,
                purchase_color_key=color_key,
                reason=(
                    "supplier_reports_unavailable"
                    if line.status == "unavailable"
                    else "supplier_confirmation_pending"
                ),
                required_quantity=required,
                confirmed_quantity=line.confirmed_quantity,
            ))
            continue

        if line.confirmed_quantity != required:
            blockers.append(FulfillmentBlocker(
                part_id=part_id,
                purchase_color_key=color_key,
                reason="confirmed_quantity_not_exact",
                required_quantity=required,
                confirmed_quantity=line.confirmed_quantity,
            ))
            continue

        exact_total += required

    for key, line in sorted(supplied.items()):
        if key not in expected:
            blockers.append(FulfillmentBlocker(
                part_id=line.part_id,
                purchase_color_key=line.purchase_color_key,
                reason="unexpected_supplier_line",
                required_quantity=1,
                confirmed_quantity=line.confirmed_quantity,
            ))

    return FulfillmentReport(
        total_required_parts=package.total_parts,
        exact_confirmed_parts=exact_total,
        blockers=blockers,
    )
