import csv
from io import StringIO

import pytest

from brickhouse.procurement.availability import (
    PartColorAvailabilityEvidence,
    PartColorAvailabilityRegistry,
)
from brickhouse.procurement.catalog import load_part_crosswalk
from brickhouse.procurement.models import BagOrderManifest, CanonicalOrderPackage, OrderLine
from brickhouse.procurement.wobrick import generate_wobrick_order_documents


def _rows(text: str):
    return list(csv.DictReader(StringIO(text)))


def _package():
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
                bag_number=2, phases=["Toiture"], assembly_step_ids=["step-2"],
                total_parts=3,
                lines=[
                    OrderLine(part_id="BRICK_2X4", category="brick", quantity=1),
                    OrderLine(part_id="TILE_2X2", category="ridge_tile", quantity=2),
                ],
            ),
        ],
    )


def _availability(route="wobrick"):
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


def test_wobrick_studio_csv_uses_verified_cross_system_ids_and_conserves_bags():
    docs = generate_wobrick_order_documents(
        _package(),
        load_part_crosswalk(),
        purchase_colors={
            ("BRICK_2X4", None): "light_bluish_gray",
            ("TILE_2X2", None): "black",
        },
        availability=_availability(),
    )
    assert docs.master.total_parts == 5
    assert [bag.total_parts for bag in docs.bags] == [2, 3]

    rows = _rows(docs.master.csv)
    assert rows == [
        {
            "BLItemNo": "3001", "LdrawId": "3001",
            "BLColorId": "86", "LDrawColorId": "71", "Qty": "3",
        },
        {
            "BLItemNo": "3068", "LdrawId": "3068b",
            "BLColorId": "11", "LDrawColorId": "0", "Qty": "2",
        },
    ]


def test_wobrick_export_refuses_bricklink_only_availability_evidence():
    with pytest.raises(ValueError, match="unverified_for_route"):
        generate_wobrick_order_documents(
            _package(),
            load_part_crosswalk(),
            purchase_colors={
                ("BRICK_2X4", None): "light_bluish_gray",
                ("TILE_2X2", None): "black",
            },
            availability=_availability("bricklink"),
        )


def test_wobrick_window_glass_uses_ldraw_alias_not_bricklink_number():
    line = OrderLine(part_id="GLASS_FOR_WINDOW_1X4X3_60603", category="window_pane", quantity=2)
    package = CanonicalOrderPackage(
        building_id="house", volume_id="main", total_parts=2, unique_part_types=1,
        total_bags=1, order_lines=[line],
        bags=[BagOrderManifest(
            bag_number=1, phases=["Fenêtres"], assembly_step_ids=["step-1"],
            total_parts=2, lines=[line],
        )],
    )
    availability = PartColorAvailabilityRegistry(evidence=[
        PartColorAvailabilityEvidence(
            route="wobrick", part_id="GLASS_FOR_WINDOW_1X4X3_60603",
            color_key="trans_clear", status="catalog_supported", source="test",
        )
    ])
    docs = generate_wobrick_order_documents(
        package,
        load_part_crosswalk(),
        purchase_colors={("GLASS_FOR_WINDOW_1X4X3_60603", None): "trans_clear"},
        availability=availability,
    )
    row = _rows(docs.master.csv)[0]
    assert row["BLItemNo"] == "60603"
    assert row["LdrawId"] == "86210"
    assert row["BLColorId"] == "12"
    assert row["LDrawColorId"] == "47"
