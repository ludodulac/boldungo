from brickhouse.bricks.piece_capabilities import create_current_engine_capability_registry
from brickhouse.procurement.catalog import (
    PartCrosswalk,
    PartCrosswalkEntry,
    audit_crosswalk_coverage,
    load_part_crosswalk,
    require_complete_approved_crosswalk,
)
from brickhouse.procurement.colors import load_color_crosswalk
from brickhouse.procurement.models import BagOrderManifest, CanonicalOrderPackage, OrderLine
from brickhouse.procurement.readiness import assess_order_readiness


def _package(part_id: str = "BRICK_2X4") -> CanonicalOrderPackage:
    line = OrderLine(part_id=part_id, category="brick", quantity=2)
    return CanonicalOrderPackage(
        building_id="house",
        volume_id="main",
        total_parts=2,
        unique_part_types=1,
        total_bags=1,
        order_lines=[line],
        bags=[
            BagOrderManifest(
                bag_number=1,
                phases=["Structure"],
                assembly_step_ids=["step-1"],
                total_parts=2,
                lines=[line],
            )
        ],
    )


def test_verified_crosswalk_covers_every_current_placement_approved_part():
    registry = create_current_engine_capability_registry()
    crosswalk = load_part_crosswalk()

    coverage = audit_crosswalk_coverage(registry, crosswalk)

    assert coverage.approved_part_count == 35
    assert coverage.mapped_part_count == 35
    assert coverage.missing_engine_ids == []
    assert coverage.extra_engine_ids == []
    assert coverage.complete
    require_complete_approved_crosswalk(registry, crosswalk)


def test_crosswalk_contains_known_roof_and_window_catalog_identities():
    by_id = load_part_crosswalk().by_engine_id()

    assert by_id["BRICK_SLOPED_18_4X2"].bricklink_item_no == "30363"
    assert by_id["BRICK_SLOPED_33_3X6"].bricklink_item_no == "3939"
    assert by_id["BRICK_SLOPED_33_3X4"].bricklink_item_no == "3297"
    assert by_id["BRICK_SLOPED_33_3X2"].bricklink_item_no == "3298"
    assert by_id["BRICK_SLOPED_45_2X4"].bricklink_item_no == "3037"
    assert by_id["BRICK_SLOPED_45_2X3"].bricklink_item_no == "3038"
    assert by_id["BRICK_SLOPED_45_2X2"].bricklink_item_no == "3039"
    assert by_id["BRICK_SLOPED_45_2X1"].bricklink_item_no == "3040"
    assert by_id["WINDOW_1X2X2_60592"].bricklink_item_no == "60592"
    assert by_id["GLASS_FOR_WINDOW_1X4X3_60603"].bricklink_item_no == "60603"


def test_core_color_crosswalk_contains_current_architectural_colors():
    colors = load_color_crosswalk().by_key()

    assert colors["white"].bricklink_color_id == 1
    assert colors["light_bluish_gray"].bricklink_color_id == 86
    assert colors["dark_bluish_gray"].bricklink_color_id == 85
    assert colors["tan"].bricklink_color_id == 2
    assert colors["reddish_brown"].bricklink_color_id == 88
    assert colors["trans_clear"].bricklink_color_id == 12


def test_order_is_not_supplier_ready_until_purchase_color_is_explicit():
    report = assess_order_readiness(_package(), load_part_crosswalk())

    assert report.part_identity_resolved_lines == 1
    assert report.purchase_color_resolved_lines == 0
    assert report.part_color_verified_lines == 0
    assert not report.supplier_ready
    assert [blocker.reason for blocker in report.blockers] == ["missing_purchase_color"]


def test_known_color_still_blocks_until_part_color_availability_is_verified():
    report = assess_order_readiness(
        _package(),
        load_part_crosswalk(),
        purchase_colors={("BRICK_2X4", None): "light_bluish_gray"},
    )

    assert report.part_identity_resolved_lines == 1
    assert report.purchase_color_resolved_lines == 1
    assert report.part_color_verified_lines == 0
    assert [blocker.reason for blocker in report.blockers] == [
        "part_color_availability_unverified"
    ]
    assert not report.supplier_ready


def test_order_is_ready_only_when_part_color_pair_is_explicitly_verified():
    report = assess_order_readiness(
        _package(),
        load_part_crosswalk(),
        purchase_colors={("BRICK_2X4", None): "light_bluish_gray"},
        verified_part_colors={("BRICK_2X4", "light_bluish_gray")},
    )

    assert report.part_identity_resolved_lines == 1
    assert report.purchase_color_resolved_lines == 1
    assert report.part_color_verified_lines == 1
    assert report.blockers == []
    assert report.supplier_ready


def test_unknown_color_key_blocks_before_availability():
    report = assess_order_readiness(
        _package(),
        load_part_crosswalk(),
        purchase_colors={("BRICK_2X4", None): "not_a_real_catalog_color"},
        verified_part_colors={("BRICK_2X4", "not_a_real_catalog_color")},
    )

    assert not report.supplier_ready
    assert [blocker.reason for blocker in report.blockers] == [
        "unknown_purchase_color"
    ]


def test_unknown_part_blocks_readiness_even_when_color_and_pair_are_selected():
    crosswalk = PartCrosswalk(
        entries=[
            PartCrosswalkEntry(
                engine_id="BRICK_2X4",
                bricklink_item_no="3001",
                mapping_status="verified_catalog_identity",
                equivalence_policy="bricklink_catalog_item",
                verification_source="test",
            )
        ]
    )
    report = assess_order_readiness(
        _package("UNKNOWN_PART"),
        crosswalk,
        purchase_colors={("UNKNOWN_PART", None): "light_bluish_gray"},
        verified_part_colors={("UNKNOWN_PART", "light_bluish_gray")},
    )

    assert not report.supplier_ready
    assert [blocker.reason for blocker in report.blockers] == [
        "missing_verified_part_identity"
    ]
