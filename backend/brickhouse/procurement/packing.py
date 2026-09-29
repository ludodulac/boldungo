"""Human-readable kit preparation documents."""

from __future__ import annotations

import csv
from collections import Counter
from io import StringIO
from typing import TypeAlias

from pydantic import BaseModel, Field, model_validator

from .availability import PartColorAvailabilityRegistry, SupplierRoute
from .catalog import PartCrosswalk
from .colors import ColorCrosswalk, load_color_crosswalk
from .models import CanonicalOrderPackage, OrderLine
from .readiness import assess_order_readiness


PhysicalKey: TypeAlias = tuple[str, str, str, int, str]


class BagPackingSheet(BaseModel):
    bag_number: int = Field(gt=0)
    label: str = Field(min_length=1)
    total_parts: int = Field(gt=0)
    csv: str = Field(min_length=1)


class KitPackingDocumentSet(BaseModel):
    schema_version: str = "0.2"
    route: SupplierRoute
    building_id: str
    volume_id: str
    total_parts: int = Field(gt=0)
    total_bags: int = Field(gt=0)
    master_picking_csv: str = Field(min_length=1)
    bag_sheets: list[BagPackingSheet] = Field(min_length=1)
    reconciliation_csv: str = Field(min_length=1)
    labels_text: str = Field(min_length=1)
    reconciliation_clear: bool

    @model_validator(mode="after")
    def validate_bags(self) -> "KitPackingDocumentSet":
        numbers = [sheet.bag_number for sheet in self.bag_sheets]
        if numbers != list(range(1, self.total_bags + 1)):
            raise ValueError("packing sheet bag numbers must be contiguous from 1")
        if self.total_parts != sum(sheet.total_parts for sheet in self.bag_sheets):
            raise ValueError("packing sheet totals do not conserve master part count")
        if not self.reconciliation_clear:
            raise ValueError("a generated kit document set must reconcile exactly")
        return self


def _physical_counter(
    lines: list[OrderLine],
    *,
    part_crosswalk: PartCrosswalk,
    color_crosswalk: ColorCrosswalk,
    purchase_colors: dict[tuple[str, str | None], str],
) -> Counter[PhysicalKey]:
    parts = part_crosswalk.by_engine_id()
    colors = color_crosswalk.by_key()
    counter: Counter[PhysicalKey] = Counter()
    for line in lines:
        part = parts[line.part_id]
        color_key = purchase_colors[(line.part_id, line.semantic_color)]
        color = colors[color_key]
        key: PhysicalKey = (
            line.part_id,
            part.bricklink_item_no,
            color_key,
            color.bricklink_color_id,
            color.bricklink_name,
        )
        counter[key] += line.quantity
    return counter


def _picking_csv(counter: Counter[PhysicalKey]) -> str:
    buffer = StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow([
        "boldungo_part_id", "bricklink_item_no", "purchase_color",
        "bricklink_color_id", "bricklink_color_name", "quantity",
    ])
    for key, quantity in sorted(counter.items(), key=lambda item: item[0]):
        part_id, bricklink_item_no, color_key, color_id, color_name = key
        writer.writerow([part_id, bricklink_item_no, color_key, color_id, color_name, quantity])
    return buffer.getvalue()


def _reconciliation_csv(
    master: Counter[PhysicalKey],
    packed: Counter[PhysicalKey],
) -> tuple[str, bool]:
    buffer = StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow([
        "boldungo_part_id", "bricklink_item_no", "purchase_color",
        "bricklink_color_id", "required_quantity", "packed_quantity", "difference",
    ])
    clear = True
    for key in sorted(set(master) | set(packed)):
        part_id, bricklink_item_no, color_key, color_id, _color_name = key
        required = master.get(key, 0)
        packed_quantity = packed.get(key, 0)
        difference = packed_quantity - required
        clear = clear and difference == 0
        writer.writerow([
            part_id, bricklink_item_no, color_key, color_id,
            required, packed_quantity, difference,
        ])
    return buffer.getvalue(), clear


def generate_kit_packing_documents(
    package: CanonicalOrderPackage,
    part_crosswalk: PartCrosswalk,
    *,
    route: SupplierRoute,
    purchase_colors: dict[tuple[str, str | None], str],
    availability: PartColorAvailabilityRegistry,
    color_crosswalk: ColorCrosswalk | None = None,
) -> KitPackingDocumentSet:
    """Render exact master/bag picking documents for one verified supplier route."""

    colors = color_crosswalk or load_color_crosswalk()
    readiness = assess_order_readiness(
        package,
        part_crosswalk,
        route=route,
        availability=availability,
        purchase_colors=purchase_colors,
        color_crosswalk=colors,
    )
    if not readiness.supplier_ready:
        details = ", ".join(
            f"{blocker.part_id}:{blocker.reason}" for blocker in readiness.blockers
        )
        raise ValueError("kit packing documents blocked by unresolved lines: " + details)

    master = _physical_counter(
        package.order_lines,
        part_crosswalk=part_crosswalk,
        color_crosswalk=colors,
        purchase_colors=purchase_colors,
    )
    packed: Counter[PhysicalKey] = Counter()
    sheets: list[BagPackingSheet] = []
    labels: list[str] = []

    for bag in package.bags:
        counter = _physical_counter(
            bag.lines,
            part_crosswalk=part_crosswalk,
            color_crosswalk=colors,
            purchase_colors=purchase_colors,
        )
        packed.update(counter)
        total = sum(counter.values())
        phases = " / ".join(bag.phases)
        label = (
            f"BOLDÜNGO — {package.building_id} — "
            f"Sac {bag.bag_number}/{package.total_bags} — "
            f"{total} pièces — {phases}"
        )
        sheets.append(BagPackingSheet(
            bag_number=bag.bag_number,
            label=label,
            total_parts=total,
            csv=_picking_csv(counter),
        ))
        labels.append(label)

    reconciliation_csv, clear = _reconciliation_csv(master, packed)
    if not clear:
        raise ValueError("kit bag reconciliation differs from the master physical order")

    return KitPackingDocumentSet(
        route=route,
        building_id=package.building_id,
        volume_id=package.volume_id,
        total_parts=sum(master.values()),
        total_bags=package.total_bags,
        master_picking_csv=_picking_csv(master),
        bag_sheets=sheets,
        reconciliation_csv=reconciliation_csv,
        labels_text="\n".join(labels),
        reconciliation_clear=True,
    )
