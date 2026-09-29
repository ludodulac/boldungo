from brickhouse.building.models import Appearance, AppearanceSection
from brickhouse.procurement.availability import (
    PartColorAvailabilityEvidence,
    PartColorAvailabilityRegistry,
)
from brickhouse.procurement.catalog import PartCrosswalk, load_part_crosswalk
from brickhouse.procurement.diagnostics import build_procurement_preparation_report
from brickhouse.procurement.models import BagOrderManifest, CanonicalOrderPackage, OrderLine
from brickhouse.procurement.supplier_package import generate_supplier_handoff_package


OBSERVED_AT = "2026-09-29T12:00:00Z"


def _package(quantity=4):
    line = OrderLine(part_id="BRICK_2X4", category="brick", quantity=quantity)
    return CanonicalOrderPackage(
        building_id="house",
        volume_id="main",
        total_parts=quantity,
        unique_part_types=1,
        total_bags=1,
        order_lines=[line],
        bags=[
            BagOrderManifest(
                bag_number=1,
                phases=["Structure"],
                assembly_step_ids=["s1"],
                total_parts=quantity,
                lines=[line.model_copy(deep=True)],
            )
        ],
    )


def _appearance():
    return Appearance(walls=AppearanceSection(color="tan"))


def _empty_availability():
    return PartColorAvailabilityRegistry(evidence=[])


def _crosswalk_without(*, bricklink=False, ldraw=False):
    original = load_part_crosswalk()
    entries = []
    for entry in original.entries:
        if entry.engine_id == "BRICK_2X4":
            update = {}
            if bricklink:
                update["bricklink_item_no"] = None
            if ldraw:
                update["ldraw_id"] = None
            entry = entry.model_copy(update=update)
        entries.append(entry)
    return PartCrosswalk(entries=entries)


def _report(route, *, crosswalk=None, availability=None, quantity=4):
    return build_procurement_preparation_report(
        _package(quantity),
        crosswalk or load_part_crosswalk(),
        route=route,
        availability=availability or _empty_availability(),
        appearance=_appearance(),
    )


def test_bricklink_exportable_without_supplier_stock_evidence():
    report = _report("bricklink")

    assert report.document_ready
    assert not report.live_order_ready
    assert report.catalog_readiness.blockers == []
    assert [blocker.reason for blocker in report.live_readiness.blockers] == [
        "live_part_color_availability_unverified"
    ]

    handoff = generate_supplier_handoff_package(
        _package(),
        load_part_crosswalk(),
        route="bricklink",
        purchase_colors={("BRICK_2X4", None): "tan"},
        availability=_empty_availability(),
    )
    assert "05_ORDER_BRICKLINK_MASTER.xml" in handoff.file_map()


def test_wobrick_exportable_without_supplier_stock_evidence():
    report = _report("wobrick")

    assert report.document_ready
    assert not report.live_order_ready
    assert report.catalog_readiness.blockers == []
    assert [blocker.reason for blocker in report.live_readiness.blockers] == [
        "live_part_color_availability_unverified"
    ]

    handoff = generate_supplier_handoff_package(
        _package(),
        load_part_crosswalk(),
        route="wobrick",
        purchase_colors={("BRICK_2X4", None): "tan"},
        availability=_empty_availability(),
    )
    assert "05_ORDER_WOBRICK_MASTER.csv" in handoff.file_map()


def test_unresolved_color_still_blocks_document_readiness():
    report = build_procurement_preparation_report(
        _package(),
        load_part_crosswalk(),
        route="bricklink",
        availability=_empty_availability(),
        appearance=Appearance(walls=AppearanceSection(color="off_white")),
    )

    assert not report.document_ready
    assert report.colors.unresolved_lines == 1


def test_missing_ldraw_id_blocks_wobrick_document_readiness():
    report = _report("wobrick", crosswalk=_crosswalk_without(ldraw=True))

    assert not report.document_ready
    assert [blocker.reason for blocker in report.catalog_readiness.blockers] == [
        "missing_ldraw_id"
    ]


def test_missing_bricklink_id_blocks_bricklink_document_readiness():
    report = _report("bricklink", crosswalk=_crosswalk_without(bricklink=True))

    assert not report.document_ready
    assert [blocker.reason for blocker in report.catalog_readiness.blockers] == [
        "missing_bricklink_item_no"
    ]


def test_live_shortage_does_not_block_valid_document_or_handoff():
    availability = PartColorAvailabilityRegistry(
        evidence=[
            PartColorAvailabilityEvidence(
                route="bricklink",
                part_id="BRICK_2X4",
                color_key="tan",
                status="live_available",
                source="fixture:bricklink-stock",
                available_quantity=3,
                observed_at=OBSERVED_AT,
            )
        ]
    )
    report = _report("bricklink", availability=availability, quantity=4)

    assert report.document_ready
    assert not report.live_order_ready
    assert report.live_readiness.shortage_total == 1
    assert report.live_readiness.blockers[0].reason == "insufficient_available_quantity"
    assert report.live_readiness.blockers[0].shortage_quantity == 1

    handoff = generate_supplier_handoff_package(
        _package(4),
        load_part_crosswalk(),
        route="bricklink",
        purchase_colors={("BRICK_2X4", None): "tan"},
        availability=availability,
    )
    assert handoff.total_parts == 4


def test_complete_live_stock_keeps_document_ready_and_enables_live_ready():
    availability = PartColorAvailabilityRegistry(
        evidence=[
            PartColorAvailabilityEvidence(
                route="bricklink",
                part_id="BRICK_2X4",
                color_key="tan",
                status="live_available",
                source="fixture:bricklink-stock",
                available_quantity=4,
                observed_at=OBSERVED_AT,
            )
        ]
    )
    report = _report("bricklink", availability=availability, quantity=4)

    assert report.document_ready
    assert report.live_order_ready
    assert report.live_readiness.shortage_total == 0
    assert report.live_readiness.quantity_covered_lines == 1

    handoff = generate_supplier_handoff_package(
        _package(4),
        load_part_crosswalk(),
        route="bricklink",
        purchase_colors={("BRICK_2X4", None): "tan"},
        availability=availability,
    )
    assert handoff.total_parts == 4
