"""Wobrick/GoBricks-compatible Studio CSV document generation.

Wobrick documents Studio CSV columns including BLItemNo, LdrawId, BLColorId,
LDrawColorId and Qty. This adapter emits exactly those ordering identities while
preserving Boldüngo master and bag quantities.
"""

from __future__ import annotations

import csv
from collections import Counter
from io import StringIO

from pydantic import BaseModel, Field, model_validator

from .availability import PartColorAvailabilityRegistry
from .catalog import PartCrosswalk
from .colors import ColorCrosswalk, load_color_crosswalk
from .models import CanonicalOrderPackage, OrderLine
from .readiness import assess_order_readiness


class WobrickCsvDocument(BaseModel):
    name: str = Field(min_length=1)
    total_parts: int = Field(gt=0)
    csv: str = Field(min_length=1)


class WobrickOrderDocuments(BaseModel):
    schema_version: str = "0.1"
    master: WobrickCsvDocument
    bags: list[WobrickCsvDocument]

    @model_validator(mode="after")
    def validate_totals(self) -> "WobrickOrderDocuments":
        if self.master.total_parts != sum(document.total_parts for document in self.bags):
            raise ValueError("Wobrick bag documents do not conserve master quantity")
        return self


def _resolve_lines(
    lines: list[OrderLine],
    *,
    part_crosswalk: PartCrosswalk,
    color_crosswalk: ColorCrosswalk,
    purchase_colors: dict[tuple[str, str | None], str],
) -> Counter[tuple[str, str, int, int]]:
    parts = part_crosswalk.by_engine_id()
    colors = color_crosswalk.by_key()
    counter: Counter[tuple[str, str, int, int]] = Counter()
    for line in lines:
        part = parts[line.part_id]
        color_key = purchase_colors[(line.part_id, line.semantic_color)]
        color = colors[color_key]
        counter[
            (
                part.bricklink_item_no,
                part.ldraw_id,
                color.bricklink_color_id,
                color.ldraw_color_id,
            )
        ] += line.quantity
    return counter


def _studio_csv(resolved: Counter[tuple[str, str, int, int]]) -> str:
    buffer = StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["BLItemNo", "LdrawId", "BLColorId", "LDrawColorId", "Qty"])
    for (bl_item, ldraw_id, bl_color, ldraw_color), quantity in sorted(resolved.items()):
        writer.writerow([bl_item, ldraw_id, bl_color, ldraw_color, quantity])
    return buffer.getvalue()


def generate_wobrick_order_documents(
    package: CanonicalOrderPackage,
    part_crosswalk: PartCrosswalk,
    *,
    purchase_colors: dict[tuple[str, str | None], str],
    availability: PartColorAvailabilityRegistry,
    color_crosswalk: ColorCrosswalk | None = None,
) -> WobrickOrderDocuments:
    """Generate Wobrick Studio CSV documents only from Wobrick-verified pairs."""

    colors = color_crosswalk or load_color_crosswalk()
    readiness = assess_order_readiness(
        package,
        part_crosswalk,
        route="wobrick",
        availability=availability,
        purchase_colors=purchase_colors,
        color_crosswalk=colors,
    )
    if not readiness.supplier_ready:
        details = ", ".join(
            f"{blocker.part_id}:{blocker.reason}" for blocker in readiness.blockers
        )
        raise ValueError("Wobrick export blocked by unresolved procurement lines: " + details)

    master_counter = _resolve_lines(
        package.order_lines,
        part_crosswalk=part_crosswalk,
        color_crosswalk=colors,
        purchase_colors=purchase_colors,
    )
    master = WobrickCsvDocument(
        name="master",
        total_parts=sum(master_counter.values()),
        csv=_studio_csv(master_counter),
    )

    bags: list[WobrickCsvDocument] = []
    for bag in package.bags:
        counter = _resolve_lines(
            bag.lines,
            part_crosswalk=part_crosswalk,
            color_crosswalk=colors,
            purchase_colors=purchase_colors,
        )
        bags.append(
            WobrickCsvDocument(
                name=f"bag-{bag.bag_number:02d}",
                total_parts=sum(counter.values()),
                csv=_studio_csv(counter),
            )
        )
    return WobrickOrderDocuments(master=master, bags=bags)
