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


def _package():
    line = OrderLine(part_id="BRICK_2X4", category="brick", quantity=4)
    return CanonicalOrderPackage(
        building_id="house", volume_id="main", total_parts=4, unique_part_types=1,
        total_bags=1, order_lines=[line],
        bags=[BagOrderManifest(
            bag_number=1, phases=["Structure"], assembly_step_ids=["s1"],
            total_parts=4, lines=[line],
        )],
    )


def _availability(status="catalog_supported"):
    return PartColorAvailabilityRegistry(evidence=[
        PartColorAvailabilityEvidence(
            route="bricklink",
            part_id="BRICK_2X4",
            color_key="light_bluish_gray",
            status=status,
            source="test",
        )
    ])


def test_report_separates_document_readiness_from_live_stock_readiness():
    report = build_procurement_preparation_report(
        _package(),
        load_part_crosswalk(),
        route="bricklink",
        availability=_availability("catalog_supported"),
        appearance=Appearance(
            walls=AppearanceSection(color="light_bluish_gray")
        ),
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


def test_live_available_evidence_makes_both_layers_ready():
    report = build_procurement_preparation_report(
        _package(),
        load_part_crosswalk(),
        route="bricklink",
        availability=_availability("live_available"),
        appearance=Appearance(
            walls=AppearanceSection(color="light_bluish_gray")
        ),
    )

    assert report.document_ready
    assert report.live_order_ready
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
