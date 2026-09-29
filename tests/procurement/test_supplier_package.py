from io import BytesIO
from zipfile import ZipFile

import pytest

from brickhouse.procurement.availability import (
    PartColorAvailabilityEvidence,
    PartColorAvailabilityRegistry,
)
from brickhouse.procurement.catalog import load_part_crosswalk
from brickhouse.procurement.models import BagOrderManifest, CanonicalOrderPackage, OrderLine
from brickhouse.procurement.supplier_package import (
    generate_supplier_handoff_package,
    supplier_handoff_zip_bytes,
)


def _package():
    brick = OrderLine(part_id="BRICK_2X4", category="brick", quantity=3)
    tile = OrderLine(part_id="TILE_2X2", category="ridge_tile", quantity=2)
    return CanonicalOrderPackage(
        building_id="house", volume_id="main", total_parts=5, unique_part_types=2,
        total_bags=2, order_lines=[brick, tile],
        bags=[
            BagOrderManifest(
                bag_number=1, phases=["Structure"], assembly_step_ids=["s1"],
                total_parts=2,
                lines=[OrderLine(part_id="BRICK_2X4", category="brick", quantity=2)],
            ),
            BagOrderManifest(
                bag_number=2, phases=["Toiture"], assembly_step_ids=["s2"],
                total_parts=3,
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


def _availability(route):
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


def test_bricklink_handoff_contains_supplier_message_master_bags_and_reconciliation():
    handoff = generate_supplier_handoff_package(
        _package(), load_part_crosswalk(), route="bricklink",
        purchase_colors=_colors(), availability=_availability("bricklink"),
    )
    files = handoff.file_map()
    assert handoff.total_parts == 5
    assert "05_ORDER_BRICKLINK_MASTER.xml" in files
    assert "bags/BAG_01_BRICKLINK.xml" in files
    assert "bags/BAG_02_PICKING.csv" in files
    assert "UNRESOLVED_LINES=0" in files["00_READINESS.txt"]
    assert "AUCUNE substitution" in files["01_SUPPLIER_REQUEST_FR.txt"]
    assert "NO substitution" in files["01_SUPPLIER_REQUEST_EN.txt"]
    assert ",0\n" in files["04_RECONCILIATION.csv"]


def test_wobrick_handoff_contains_studio_csv_instead_of_bricklink_xml():
    handoff = generate_supplier_handoff_package(
        _package(), load_part_crosswalk(), route="wobrick",
        purchase_colors=_colors(), availability=_availability("wobrick"),
    )
    files = handoff.file_map()
    assert "05_ORDER_WOBRICK_MASTER.csv" in files
    assert "bags/BAG_01_WOBRICK.csv" in files
    assert "05_ORDER_BRICKLINK_MASTER.xml" not in files
    assert files["05_ORDER_WOBRICK_MASTER.csv"].startswith(
        "BLItemNo,LdrawId,BLColorId,LDrawColorId,Qty\n"
    )


def test_handoff_zip_is_deterministic_and_contains_exact_named_files():
    handoff = generate_supplier_handoff_package(
        _package(), load_part_crosswalk(), route="bricklink",
        purchase_colors=_colors(), availability=_availability("bricklink"),
    )
    first = supplier_handoff_zip_bytes(handoff)
    second = supplier_handoff_zip_bytes(handoff)
    assert first == second
    with ZipFile(BytesIO(first)) as archive:
        names = archive.namelist()
        assert names == sorted(names)
        assert "01_SUPPLIER_REQUEST_FR.txt" in names
        assert "bags/BAG_02_PICKING.csv" in names
        assert archive.read("00_READINESS.txt").decode("utf-8").startswith(
            "STATUS=READY_FOR_DOCUMENT_HANDOFF"
        )


def test_handoff_refuses_wrong_route_availability():
    with pytest.raises(ValueError, match="unresolved lines"):
        generate_supplier_handoff_package(
            _package(), load_part_crosswalk(), route="wobrick",
            purchase_colors=_colors(), availability=_availability("bricklink"),
        )
