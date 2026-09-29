import csv
from io import StringIO

import pytest

from brickhouse.procurement.availability import (
    PartColorAvailabilityEvidence,
    PartColorAvailabilityRegistry,
)
from brickhouse.procurement.catalog import load_part_crosswalk
from brickhouse.procurement.models import BagOrderManifest, CanonicalOrderPackage, OrderLine
from brickhouse.procurement.packing import generate_kit_packing_documents


def _rows(text: str) -> list[dict[str, str]]:
    return list(csv.DictReader(StringIO(text)))


def _package() -> CanonicalOrderPackage:
    brick = OrderLine(part_id="BRICK_2X4", category="brick", quantity=3)
    tile = OrderLine(part_id="TILE_2X2", category="ridge_tile", quantity=2)
    return CanonicalOrderPackage(
        building_id="house", volume_id="main", total_parts=5, unique_part_types=2,
        total_bags=2, order_lines=[brick, tile],
        bags=[
            BagOrderManifest(
                bag_number=1, phases=["Structure"], assembly_step_ids=["step-1"],
                total_parts=2,
                lines=[OrderLine(part_id="BRICK_2X4", category="brick", quantity=2)],
            ),
            BagOrderManifest(
                bag_number=2, phases=["Structure", "Toiture"],
                assembly_step_ids=["step-2", "step-3"], total_parts=3,
                lines=[
                    OrderLine(part_id="BRICK_2X4", category="brick", quantity=1),
                    OrderLine(part_id="TILE_2X2", category="ridge_tile", quantity=2),
                ],
            ),
        ],
    )


def _colors():
    return {
        ("BRICK_2X4", None): "light_bluish_gray",
        ("TILE_2X2", None): "black",
    }


def _availability(route="bricklink"):
    return PartColorAvailabilityRegistry(evidence=[
        PartColorAvailabilityEvidence(
            route=route, part_id="BRICK_2X4", color_key="light_bluish_gray",
            status="catalog_supported", source="test",
        ),
        PartColorAvailabilityEvidence(
            route=route, part_id="TILE_2X2", color_key="black",
            status="catalog_supported", source="test",
        ),
    ])


def test_kit_documents_produce_master_bags_labels_and_zero_difference_reconciliation():
    docs = generate_kit_packing_documents(
        _package(),
        load_part_crosswalk(),
        route="bricklink",
        purchase_colors=_colors(),
        availability=_availability(),
    )
    assert docs.route == "bricklink"
    assert docs.total_parts == 5
    assert docs.total_bags == 2
    assert docs.reconciliation_clear
    assert [sheet.total_parts for sheet in docs.bag_sheets] == [2, 3]
    master = {
        (row["bricklink_item_no"], row["bricklink_color_id"]): int(row["quantity"])
        for row in _rows(docs.master_picking_csv)
    }
    assert master == {("3001", "86"): 3, ("3068", "11"): 2}
    assert _rows(docs.bag_sheets[0].csv)[0]["quantity"] == "2"
    reconciliation = _rows(docs.reconciliation_csv)
    assert {row["difference"] for row in reconciliation} == {"0"}
    assert sum(int(row["required_quantity"]) for row in reconciliation) == 5
    assert sum(int(row["packed_quantity"]) for row in reconciliation) == 5
    assert "Sac 1/2" in docs.labels_text
    assert "Sac 2/2" in docs.labels_text


def test_kit_documents_refuse_availability_from_another_route():
    with pytest.raises(ValueError, match="unverified_for_route"):
        generate_kit_packing_documents(
            _package(),
            load_part_crosswalk(),
            route="wobrick",
            purchase_colors=_colors(),
            availability=_availability("bricklink"),
        )
