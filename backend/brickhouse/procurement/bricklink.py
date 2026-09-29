"""BrickLink Wanted List document generation."""

from __future__ import annotations

from collections import Counter
from xml.etree import ElementTree as ET

from pydantic import BaseModel, Field, model_validator

from .availability import PartColorAvailabilityRegistry
from .catalog import PartCrosswalk
from .colors import ColorCrosswalk, load_color_crosswalk
from .models import CanonicalOrderPackage, OrderLine
from .readiness import assess_order_readiness


class BrickLinkWantedListDocument(BaseModel):
    name: str = Field(min_length=1)
    total_parts: int = Field(gt=0)
    xml: str = Field(min_length=1)


class BrickLinkOrderDocuments(BaseModel):
    schema_version: str = "0.2"
    master: BrickLinkWantedListDocument
    bags: list[BrickLinkWantedListDocument]

    @model_validator(mode="after")
    def validate_totals(self) -> "BrickLinkOrderDocuments":
        if self.master.total_parts != sum(document.total_parts for document in self.bags):
            raise ValueError("BrickLink bag documents do not conserve master quantity")
        return self


def _resolve_lines(
    lines: list[OrderLine],
    *,
    part_crosswalk: PartCrosswalk,
    color_crosswalk: ColorCrosswalk,
    purchase_colors: dict[tuple[str, str | None], str],
) -> Counter[tuple[str, int]]:
    parts = part_crosswalk.by_engine_id()
    colors = color_crosswalk.by_key()
    counter: Counter[tuple[str, int]] = Counter()
    for line in lines:
        part = parts[line.part_id]
        color_key = purchase_colors[(line.part_id, line.semantic_color)]
        color = colors[color_key]
        counter[(part.bricklink_item_no, color.bricklink_color_id)] += line.quantity
    return counter


def _wanted_list_xml(resolved: Counter[tuple[str, int]], *, remarks: str) -> str:
    root = ET.Element("INVENTORY")
    for (item_id, color_id), quantity in sorted(resolved.items()):
        item = ET.SubElement(root, "ITEM")
        ET.SubElement(item, "ITEMTYPE").text = "P"
        ET.SubElement(item, "ITEMID").text = item_id
        ET.SubElement(item, "COLOR").text = str(color_id)
        ET.SubElement(item, "MINQTY").text = str(quantity)
        ET.SubElement(item, "REMARKS").text = remarks
    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="unicode", short_empty_elements=False)


def generate_bricklink_order_documents(
    package: CanonicalOrderPackage,
    part_crosswalk: PartCrosswalk,
    *,
    purchase_colors: dict[tuple[str, str | None], str],
    availability: PartColorAvailabilityRegistry,
    color_crosswalk: ColorCrosswalk | None = None,
) -> BrickLinkOrderDocuments:
    """Generate one complete Wanted List plus one Wanted List per numbered bag."""

    colors = color_crosswalk or load_color_crosswalk()
    readiness = assess_order_readiness(
        package,
        part_crosswalk,
        route="bricklink",
        availability=availability,
        purchase_colors=purchase_colors,
        color_crosswalk=colors,
    )
    if not readiness.supplier_ready:
        details = ", ".join(
            f"{blocker.part_id}:{blocker.reason}" for blocker in readiness.blockers
        )
        raise ValueError("BrickLink export blocked by unresolved procurement lines: " + details)

    master_counter = _resolve_lines(
        package.order_lines,
        part_crosswalk=part_crosswalk,
        color_crosswalk=colors,
        purchase_colors=purchase_colors,
    )
    master = BrickLinkWantedListDocument(
        name="master",
        total_parts=sum(master_counter.values()),
        xml=_wanted_list_xml(master_counter, remarks="Boldungo master order"),
    )

    bags: list[BrickLinkWantedListDocument] = []
    for bag in package.bags:
        counter = _resolve_lines(
            bag.lines,
            part_crosswalk=part_crosswalk,
            color_crosswalk=colors,
            purchase_colors=purchase_colors,
        )
        bags.append(
            BrickLinkWantedListDocument(
                name=f"bag-{bag.bag_number:02d}",
                total_parts=sum(counter.values()),
                xml=_wanted_list_xml(
                    counter,
                    remarks=f"Boldungo bag {bag.bag_number}/{package.total_bags}",
                ),
            )
        )

    return BrickLinkOrderDocuments(master=master, bags=bags)
