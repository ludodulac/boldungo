from brickhouse.building.models import Appearance, AppearanceSection
from brickhouse.procurement.availability import (
    PartColorAvailabilityEvidence,
    PartColorAvailabilityRegistry,
)
from brickhouse.procurement.catalog import load_part_crosswalk
from brickhouse.procurement.diagnostics import (
    build_procurement_preparation_report,
    procurement_preparation_csv,
    procurement_preparation_summary,
)
from brickhouse.procurement.models import BagOrderManifest, CanonicalOrderPackage, OrderLine


def _package(quantity=4):
    line = OrderLine(part_id="BRICK_2X4", category="brick", quantity=quantity)
    return CanonicalOrderPackage(
        building_id="house", volume_id="main", total_parts=quantity, unique_part_types=1,
        total_bags=1, order_lines=[line],
        bags=[BagOrderManifest(
            bag_number=1, phases=["Structure"], assembly_step_ids=["s1"],
            total_parts=quantity, lines=[line],
        )],
    )


def _multiline_package():
    brick = OrderLine(
        part_id="BRICK_2X4",
        category="brick",
        semantic_color="light_bluish_gray",
        quantity=100,
    )
    tile = OrderLine(
        part_id="TILE_2X2",
        category="ridge_tile",
        semantic_color="black",
        quantity=30,
    )
    return CanonicalOrderPackage(
        building_id="house", volume_id="main", total_parts=130, unique_part_types=2,
        total_bags=1, order_lines=[brick, tile],
        bags=[BagOrderManifest(
            bag_number=1, phases=["Structure"], assembly_step_ids=["s1"],
            total_parts=130, lines=[brick, tile],
        )],
    )


def _availability(status="catalog_supported", available_quantity=None):
    return PartColorAvailabilityRegistry(evidence=[
        PartColorAvailabilityEvidence(
            route="bricklink",
            part_id="BRICK_2X4",
            color_key="light_bluish_gray",
            status=status,
            source="test",
            available_quantity=available_quantity,
        )
    ])


def _multi_availability(bricks, tiles):
    return PartColorAvailabilityRegistry(evidence=[
        PartColorAvailabilityEvidence(
            route="bricklink",
            part_id="BRICK_2X4",
            color_key="light_bluish_gray",
            status="live_available",
            source="test",
            available_quantity=bricks,
        ),
        PartColorAvailabilityEvidence(
            route="bricklink",
            part_id="TILE_2X2",
            color_key="black",
            status="live_available",
            source="test",
            available_quantity=tiles,
        ),
    ])


def _wall_appearance():
    return Appearance(
        walls=AppearanceSection(color="light_bluish_gray")
    )


def test_report_separates_document_readiness_from_live_stock_readiness():
    report = build_procurement_preparation_report(
        _package(),
        load_part_crosswalk(),
        route="bricklink",
        availability=_availability("catalog_supported"),
        appearance=_wall_appearance(),
    )

    assert report.colors.complete
    assert report.document_ready
    assert not report.live_order_ready
    assert report.catalog_readiness.blockers == []
    assert [b.reason for b in report.live_readiness.blockers] == [
        "live_part_color_availability_unverified"
    ]
    summary = procurement_preparation_summary(report)
    assert "DOCUMENT_READY=YES" in summary
    assert "LIVE_ORDER_READY=NO" in summary


def test_live_available_with_unknown_quantity_is_not_live_order_ready():
    report = build_procurement_preparation_report(
        _package(100),
        load_part_crosswalk(),
        route="bricklink",
        availability=_availability("live_available", available_quantity=None),
        appearance=_wall_appearance(),
    )

    assert report.document_ready
    assert not report.live_order_ready
    assert report.live_readiness.part_color_verified_lines == 1
    assert report.live_readiness.quantity_covered_lines == 0
    assert report.live_readiness.shortage_total == 0
    blocker = report.live_readiness.blockers[0]
    assert blocker.reason == "available_quantity_unknown"
    assert blocker.required_quantity == 100
    assert blocker.available_quantity is None


def test_required_100_available_75_reports_shortage_25_and_blocks_live_ready():
    report = build_procurement_preparation_report(
        _package(100),
        load_part_crosswalk(),
        route="bricklink",
        availability=_availability("live_available", available_quantity=75),
        appearance=_wall_appearance(),
    )

    assert report.document_ready
    assert not report.live_order_ready
    assert report.live_readiness.quantity_covered_lines == 0
    assert report.live_readiness.shortage_total == 25
    blocker = report.live_readiness.blockers[0]
    assert blocker.reason == "insufficient_available_quantity"
    assert blocker.required_quantity == 100
    assert blocker.available_quantity == 75
    assert blocker.shortage_quantity == 25
    assert "SHORTAGE_TOTAL=25" in procurement_preparation_summary(report)


def test_required_100_available_100_is_quantity_covered():
    report = build_procurement_preparation_report(
        _package(100),
        load_part_crosswalk(),
        route="bricklink",
        availability=_availability("live_available", available_quantity=100),
        appearance=_wall_appearance(),
    )

    assert report.live_readiness.quantity_covered_lines == 1
    assert report.live_readiness.shortage_total == 0
    assert report.live_readiness.blockers == []
    assert report.live_order_ready


def test_required_100_available_140_is_covered_without_mutating_bom():
    package = _package(100)
    report = build_procurement_preparation_report(
        package,
        load_part_crosswalk(),
        route="bricklink",
        availability=_availability("live_available", available_quantity=140),
        appearance=_wall_appearance(),
    )

    assert report.live_readiness.quantity_covered_lines == 1
    assert report.live_order_ready
    assert package.total_parts == 100
    assert package.order_lines[0].quantity == 100
    assert sum(line.quantity for line in package.order_lines) == 100


def test_multiline_one_piece_short_blocks_global_live_order_ready():
    report = build_procurement_preparation_report(
        _multiline_package(),
        load_part_crosswalk(),
        route="bricklink",
        availability=_multi_availability(bricks=100, tiles=29),
        appearance=None,
    )

    assert report.document_ready
    assert not report.live_order_ready
    assert report.live_readiness.quantity_covered_lines == 1
    assert report.live_readiness.shortage_total == 1
    assert [(b.part_id, b.shortage_quantity) for b in report.live_readiness.blockers] == [
        ("TILE_2X2", 1)
    ]


def test_multiline_all_lines_covered_is_live_order_ready():
    report = build_procurement_preparation_report(
        _multiline_package(),
        load_part_crosswalk(),
        route="bricklink",
        availability=_multi_availability(bricks=100, tiles=40),
        appearance=None,
    )

    assert report.document_ready
    assert report.live_order_ready
    assert report.live_readiness.quantity_covered_lines == 2
    assert report.live_readiness.shortage_total == 0
    assert report.live_readiness.blockers == []


def test_unknown_photo_color_is_explained_instead_of_guessed():
    report = build_procurement_preparation_report(
        _package(),
        load_part_crosswalk(),
        route="bricklink",
        availability=PartColorAvailabilityRegistry(evidence=[]),
        appearance=Appearance(walls=AppearanceSection(color="off_white")),
    )

    assert not report.document_ready
    assert report.colors.unresolved_lines == 1
    csv_text = procurement_preparation_csv(report)
    assert "off_white" in csv_text
    assert "noncanonical_architectural_color" in csv_text
    assert "missing_purchase_color" in csv_text


def test_missing_appearance_produces_explicit_color_blocker():
    report = build_procurement_preparation_report(
        _package(),
        load_part_crosswalk(),
        route="bricklink",
        availability=PartColorAvailabilityRegistry(evidence=[]),
        appearance=None,
    )

    assert not report.document_ready
    assert report.colors.lines[0].status == "missing_architectural_color"
    assert "COLOR_UNRESOLVED=1" in procurement_preparation_summary(report)
