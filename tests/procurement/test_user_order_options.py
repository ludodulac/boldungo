import pytest

from brickhouse.building.models import Appearance, AppearanceSection
from brickhouse.procurement.availability import (
    PartColorAvailabilityEvidence,
    PartColorAvailabilityRegistry,
)
from brickhouse.procurement.catalog import load_part_crosswalk
from brickhouse.procurement.models import BagOrderManifest, CanonicalOrderPackage, OrderLine
from brickhouse.procurement.user_order import (
    build_user_order_options,
    generate_handoff_from_user_order_option,
)


OBSERVED_AT = "2026-09-29T12:00:00Z"


def _package() -> CanonicalOrderPackage:
    line = OrderLine(part_id="BRICK_2X4", category="brick", quantity=5)
    return CanonicalOrderPackage(
        building_id="house",
        volume_id="main",
        total_parts=5,
        unique_part_types=1,
        total_bags=2,
        order_lines=[line],
        bags=[
            BagOrderManifest(
                bag_number=1,
                phases=["Structure"],
                assembly_step_ids=["s1"],
                total_parts=2,
                lines=[OrderLine(part_id="BRICK_2X4", category="brick", quantity=2)],
            ),
            BagOrderManifest(
                bag_number=2,
                phases=["Structure"],
                assembly_step_ids=["s2"],
                total_parts=3,
                lines=[OrderLine(part_id="BRICK_2X4", category="brick", quantity=3)],
            ),
        ],
    )


def _appearance(color="tan"):
    return Appearance(walls=AppearanceSection(color=color))


def _catalog_availability():
    return PartColorAvailabilityRegistry(
        evidence=[
            PartColorAvailabilityEvidence(
                route="bricklink",
                part_id="BRICK_2X4",
                color_key="tan",
                status="catalog_supported",
                source="fixture:bricklink-catalog",
            ),
            PartColorAvailabilityEvidence(
                route="wobrick",
                part_id="BRICK_2X4",
                color_key="tan",
                status="catalog_supported",
                source="fixture:wobrick-catalog",
            ),
        ]
    )


def _availability_with_bricklink_shortage():
    return PartColorAvailabilityRegistry(
        evidence=[
            PartColorAvailabilityEvidence(
                route="bricklink",
                part_id="BRICK_2X4",
                color_key="tan",
                status="live_available",
                source="fixture:bricklink-stock",
                available_quantity=4,
                observed_at=OBSERVED_AT,
            ),
            PartColorAvailabilityEvidence(
                route="wobrick",
                part_id="BRICK_2X4",
                color_key="tan",
                status="catalog_supported",
                source="fixture:wobrick-catalog",
            ),
        ]
    )


def test_bricklink_document_ready_without_live_stock_can_generate_dossier():
    package = _package()
    availability = _catalog_availability()
    options = build_user_order_options(
        package,
        load_part_crosswalk(),
        availability=availability,
        appearance=_appearance(),
    )
    bricklink = options.for_route("bricklink")

    assert bricklink.label == "Commander en LEGO via BrickLink"
    assert bricklink.document_ready
    assert not bricklink.live_order_ready
    assert bricklink.total_parts == package.total_parts
    assert bricklink.total_bags == package.total_bags

    handoff = generate_handoff_from_user_order_option(
        bricklink,
        package,
        load_part_crosswalk(),
        availability=availability,
        appearance=_appearance(),
    )

    assert handoff.route == "bricklink"
    assert handoff.total_parts == package.total_parts
    assert "05_ORDER_BRICKLINK_MASTER.xml" in handoff.file_map()


def test_wobrick_document_ready_can_generate_existing_handoff_package():
    package = _package()
    availability = _catalog_availability()
    options = build_user_order_options(
        package,
        load_part_crosswalk(),
        availability=availability,
        appearance=_appearance(),
    )
    wobrick = options.for_route("wobrick")

    assert wobrick.label == "Commander en briques compatibles"
    assert wobrick.document_ready
    assert not wobrick.live_order_ready

    handoff = generate_handoff_from_user_order_option(
        wobrick,
        package,
        load_part_crosswalk(),
        availability=availability,
        appearance=_appearance(),
    )

    files = handoff.file_map()
    assert handoff.route == "wobrick"
    assert "05_ORDER_WOBRICK_MASTER.csv" in files
    assert "05_ORDER_BRICKLINK_MASTER.xml" not in files


def test_unresolved_physical_color_blocks_document_generation():
    package = _package()
    availability = _catalog_availability()
    options = build_user_order_options(
        package,
        load_part_crosswalk(),
        availability=availability,
        appearance=_appearance("off_white"),
    )
    bricklink = options.for_route("bricklink")

    assert not bricklink.document_ready
    assert any(
        blocker.layer == "document"
        and blocker.code == "noncanonical_architectural_color"
        for blocker in bricklink.blockers
    )

    with pytest.raises(ValueError, match="not document-ready"):
        generate_handoff_from_user_order_option(
            bricklink,
            package,
            load_part_crosswalk(),
            availability=availability,
            appearance=_appearance("off_white"),
        )


def test_document_ready_is_distinct_from_live_shortage_and_shortage_is_visible():
    package = _package()
    availability = _availability_with_bricklink_shortage()
    options = build_user_order_options(
        package,
        load_part_crosswalk(),
        availability=availability,
        appearance=_appearance(),
    )
    bricklink = options.for_route("bricklink")

    assert bricklink.document_ready
    assert not bricklink.live_order_ready
    shortages = [
        blocker
        for blocker in bricklink.blockers
        if blocker.code == "insufficient_available_quantity"
    ]
    assert len(shortages) == 1
    assert shortages[0].layer == "live"
    assert shortages[0].shortage_quantity == 1
    assert "manque 1 pièce" in shortages[0].message

    handoff = generate_handoff_from_user_order_option(
        bricklink,
        package,
        load_part_crosswalk(),
        availability=availability,
        appearance=_appearance(),
    )
    assert handoff.total_parts == 5


def test_user_order_totals_match_canonical_package_for_both_routes():
    package = _package()
    options = build_user_order_options(
        package,
        load_part_crosswalk(),
        availability=_catalog_availability(),
        appearance=_appearance(),
    )

    assert options.total_parts == package.total_parts
    assert options.total_bags == package.total_bags
    assert [option.route for option in options.options] == ["bricklink", "wobrick"]
    assert all(option.total_parts == package.total_parts for option in options.options)
    assert all(option.total_bags == package.total_bags for option in options.options)
