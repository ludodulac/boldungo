from xml.etree import ElementTree as ET

import pytest

from brickhouse.procurement.bricklink import generate_bricklink_order_documents
from brickhouse.procurement.catalog import load_part_crosswalk
from brickhouse.procurement.models import BagOrderManifest, CanonicalOrderPackage, OrderLine


def _package() -> CanonicalOrderPackage:
    brick = OrderLine(part_id="BRICK_2X4", category="brick", quantity=3)
    tile = OrderLine(part_id="TILE_2X2", category="ridge_tile", quantity=2)
    return CanonicalOrderPackage(
        building_id="house",
        volume_id="main",
        total_parts=5,
        unique_part_types=2,
        total_bags=2,
        order_lines=[brick, tile],
        bags=[
            BagOrderManifest(
                bag_number=1,
                phases=["Structure"],
                assembly_step_ids=["step-1"],
                total_parts=2,
                lines=[
                    OrderLine(part_id="BRICK_2X4", category="brick", quantity=2)
                ],
            ),
            BagOrderManifest(
                bag_number=2,
                phases=["Structure", "Toiture"],
                assembly_step_ids=["step-2", "step-3"],
                total_parts=3,
                lines=[
                    OrderLine(part_id="BRICK_2X4", category="brick", quantity=1),
                    OrderLine(part_id="TILE_2X2", category="ridge_tile", quantity=2),
                ],
            ),
        ],
    )


def _items(xml: str) -> dict[tuple[str, int], int]:
    root = ET.fromstring(xml)
    assert root.tag == "INVENTORY"
    result = {}
    for item in root.findall("ITEM"):
        assert item.findtext("ITEMTYPE") == "P"
        result[(item.findtext("ITEMID"), int(item.findtext("COLOR")))] = int(
            item.findtext("MINQTY")
        )
    return result


def test_bricklink_documents_conserve_master_and_numbered_bags():
    package = _package()
    colors = {
        ("BRICK_2X4", None): "light_bluish_gray",
        ("TILE_2X2", None): "black",
    }
    verified = {
        ("BRICK_2X4", "light_bluish_gray"),
        ("TILE_2X2", "black"),
    }

    documents = generate_bricklink_order_documents(
        package,
        load_part_crosswalk(),
        purchase_colors=colors,
        verified_part_colors=verified,
    )

    assert documents.master.total_parts == 5
    assert [bag.name for bag in documents.bags] == ["bag-01", "bag-02"]
    assert [bag.total_parts for bag in documents.bags] == [2, 3]
    assert _items(documents.master.xml) == {
        ("3001", 86): 3,
        ("3068", 11): 2,
    }
    assert _items(documents.bags[0].xml) == {("3001", 86): 2}
    assert _items(documents.bags[1].xml) == {
        ("3001", 86): 1,
        ("3068", 11): 2,
    }


def test_bricklink_export_refuses_unverified_part_color_pair():
    with pytest.raises(ValueError, match="part_color_availability_unverified"):
        generate_bricklink_order_documents(
            _package(),
            load_part_crosswalk(),
            purchase_colors={
                ("BRICK_2X4", None): "light_bluish_gray",
                ("TILE_2X2", None): "black",
            },
            verified_part_colors=set(),
        )


def test_bricklink_export_aggregates_semantic_lines_that_choose_same_physical_color():
    line_a = OrderLine(
        part_id="BRICK_2X4",
        category="masonry",
        semantic_color="warm stone",
        quantity=2,
    )
    line_b = OrderLine(
        part_id="BRICK_2X4",
        category="masonry",
        semantic_color="slightly darker stone",
        quantity=3,
    )
    package = CanonicalOrderPackage(
        building_id="house",
        volume_id="main",
        total_parts=5,
        unique_part_types=2,
        total_bags=1,
        order_lines=[line_a, line_b],
        bags=[
            BagOrderManifest(
                bag_number=1,
                phases=["Façades"],
                assembly_step_ids=["step-1"],
                total_parts=5,
                lines=[line_a, line_b],
            )
        ],
    )
    purchase_colors = {
        ("BRICK_2X4", "warm stone"): "tan",
        ("BRICK_2X4", "slightly darker stone"): "tan",
    }

    documents = generate_bricklink_order_documents(
        package,
        load_part_crosswalk(),
        purchase_colors=purchase_colors,
        verified_part_colors={("BRICK_2X4", "tan")},
    )

    assert _items(documents.master.xml) == {("3001", 2): 5}


def test_order_package_rejects_same_total_with_wrong_bag_composition():
    with pytest.raises(ValueError, match="bag composition"):
        CanonicalOrderPackage(
            building_id="house",
            volume_id="main",
            total_parts=2,
            unique_part_types=1,
            total_bags=1,
            order_lines=[
                OrderLine(part_id="BRICK_2X4", category="brick", quantity=2)
            ],
            bags=[
                BagOrderManifest(
                    bag_number=1,
                    phases=["Structure"],
                    assembly_step_ids=["step-1"],
                    total_parts=2,
                    lines=[
                        OrderLine(part_id="BRICK_1X1", category="brick", quantity=2)
                    ],
                )
            ],
        )
