from brickhouse.procurement.availability import (
    PartColorAvailabilityEvidence,
    PartColorAvailabilityRegistry,
)
from brickhouse.procurement.catalog import load_part_crosswalk
from brickhouse.procurement.models import BagOrderManifest, CanonicalOrderPackage, OrderLine
from brickhouse.procurement.readiness import assess_order_readiness


PURCHASE_COLORS = {("BRICK_2X4", "tan"): "tan"}


def _package(required=100):
    line = OrderLine(
        part_id="BRICK_2X4",
        category="brick",
        semantic_color="tan",
        quantity=required,
    )
    return CanonicalOrderPackage(
        building_id="house",
        volume_id="main",
        total_parts=required,
        unique_part_types=1,
        total_bags=1,
        order_lines=[line],
        bags=[
            BagOrderManifest(
                bag_number=1,
                phases=["Structure"],
                assembly_step_ids=["s1"],
                total_parts=required,
                lines=[line.model_copy(deep=True)],
            )
        ],
    )


def _report(route, evidence, required=100):
    return assess_order_readiness(
        _package(required),
        load_part_crosswalk(),
        route=route,
        availability=PartColorAvailabilityRegistry(evidence=[evidence]),
        purchase_colors=PURCHASE_COLORS,
        require_live_availability=True,
    )


def test_catalog_quantity_never_counts_as_live_quantity_evidence():
    report = _report(
        "bricklink",
        PartColorAvailabilityEvidence(
            route="bricklink",
            part_id="BRICK_2X4",
            color_key="tan",
            status="catalog_supported",
            source="fixture:catalog",
            available_quantity=200,
            observed_at="2026-09-29T12:00:00Z",
        ),
    )

    assert not report.supplier_ready
    assert report.quantity_covered_lines == 0
    assert [b.reason for b in report.blockers] == [
        "live_part_color_availability_unverified"
    ]


def test_live_quantity_without_observed_at_is_not_ready():
    report = _report(
        "bricklink",
        PartColorAvailabilityEvidence(
            route="bricklink",
            part_id="BRICK_2X4",
            color_key="tan",
            status="live_available",
            source="fixture:bricklink-stock",
            available_quantity=200,
            observed_at=None,
        ),
    )

    assert not report.supplier_ready
    assert report.quantity_covered_lines == 0
    assert [b.reason for b in report.blockers] == [
        "live_quantity_observation_time_missing"
    ]


def test_wobrick_live_quantity_with_source_and_timestamp_is_covered():
    report = _report(
        "wobrick",
        PartColorAvailabilityEvidence(
            route="wobrick",
            part_id="BRICK_2X4",
            color_key="tan",
            status="live_available",
            source="fixture:wobrick-stock",
            available_quantity=120,
            observed_at="2026-09-29T12:00:00Z",
        ),
    )

    assert report.supplier_ready
    assert report.quantity_covered_lines == 1
    assert report.shortage_total == 0


def test_live_quantity_evidence_cannot_cross_supplier_routes():
    report = _report(
        "wobrick",
        PartColorAvailabilityEvidence(
            route="bricklink",
            part_id="BRICK_2X4",
            color_key="tan",
            status="live_available",
            source="fixture:bricklink-stock",
            available_quantity=500,
            observed_at="2026-09-29T12:00:00Z",
        ),
    )

    assert not report.supplier_ready
    assert report.quantity_covered_lines == 0
    assert [b.reason for b in report.blockers] == [
        "live_part_color_availability_unverified"
    ]


def test_live_quantity_evidence_cannot_cross_colors():
    report = _report(
        "wobrick",
        PartColorAvailabilityEvidence(
            route="wobrick",
            part_id="BRICK_2X4",
            color_key="black",
            status="live_available",
            source="fixture:wobrick-stock",
            available_quantity=500,
            observed_at="2026-09-29T12:00:00Z",
        ),
    )

    assert not report.supplier_ready
    assert report.quantity_covered_lines == 0
    assert [b.reason for b in report.blockers] == [
        "live_part_color_availability_unverified"
    ]


def test_live_quantity_evidence_cannot_cross_parts():
    report = _report(
        "wobrick",
        PartColorAvailabilityEvidence(
            route="wobrick",
            part_id="BRICK_1X2",
            color_key="tan",
            status="live_available",
            source="fixture:wobrick-stock",
            available_quantity=500,
            observed_at="2026-09-29T12:00:00Z",
        ),
    )

    assert not report.supplier_ready
    assert report.quantity_covered_lines == 0
    assert [b.reason for b in report.blockers] == [
        "live_part_color_availability_unverified"
    ]


def test_historical_timestamp_is_representable_without_arbitrary_ttl_rejection():
    report = _report(
        "wobrick",
        PartColorAvailabilityEvidence(
            route="wobrick",
            part_id="BRICK_2X4",
            color_key="tan",
            status="live_available",
            source="fixture:historical-wobrick-stock",
            available_quantity=120,
            observed_at="2020-01-02T03:04:05Z",
        ),
    )

    assert report.supplier_ready
    assert report.quantity_covered_lines == 1
    assert report.blockers == []
