from brickhouse.bricks.piece_capabilities import create_current_engine_capability_registry
from brickhouse.procurement.availability import (
    PartColorAvailabilityEvidence,
    PartColorAvailabilityRegistry,
)
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
        building_id="house", volume_id="main", total_parts=2, unique_part_types=1,
        total_bags=1, order_lines=[line],
        bags=[BagOrderManifest(
            bag_number=1, phases=["Structure"], assembly_step_ids=["step-1"],
            total_parts=2, lines=[line],
        )],
    )


def _availability(route="bricklink", status="catalog_supported"):
    return PartColorAvailabilityRegistry(evidence=[
        PartColorAvailabilityEvidence(
            route=route, part_id="BRICK_2X4", color_key="light_bluish_gray",
            status=status, source="test",
        )
    ])


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


def test_crosswalk_contains_verified_bricklink_and_ldraw_special_cases():
    by_id = load_part_crosswalk().by_engine_id()
    assert by_id["BRICK_SLOPED_18_4X2"].bricklink_item_no == "30363"
    assert by_id["BRICK_SLOPED_18_4X2"].ldraw_id == "30363"
    assert by_id["PLATE_1X2"].bricklink_item_no == "3023"
    assert by_id["PLATE_1X2"].ldraw_id == "3023b"
    assert by_id["BRICK_SLOPED_45_2X1"].bricklink_item_no == "3040"
    assert by_id["BRICK_SLOPED_45_2X1"].ldraw_id == "3040b"
    assert by_id["TILE_2X2"].bricklink_item_no == "3068"
    assert by_id["TILE_2X2"].ldraw_id == "3068b"
    assert by_id["GLASS_FOR_WINDOW_1X4X3_60603"].bricklink_item_no == "60603"
    assert by_id["GLASS_FOR_WINDOW_1X4X3_60603"].ldraw_id == "86210"


def test_core_color_crosswalk_contains_bricklink_ldraw_and_gobricks_ids():
    colors = load_color_crosswalk().by_key()
    assert (colors["white"].bricklink_color_id, colors["white"].ldraw_color_id, colors["white"].gobricks_color_no) == (1, 15, "090")
    assert (colors["light_bluish_gray"].bricklink_color_id, colors["light_bluish_gray"].ldraw_color_id, colors["light_bluish_gray"].gobricks_color_no) == (86, 71, "071")
    assert (colors["dark_bluish_gray"].bricklink_color_id, colors["dark_bluish_gray"].ldraw_color_id) == (85, 72)
    assert (colors["reddish_brown"].bricklink_color_id, colors["reddish_brown"].ldraw_color_id) == (88, 70)
    assert (colors["trans_clear"].bricklink_color_id, colors["trans_clear"].ldraw_color_id) == (12, 47)


def test_order_is_not_supplier_ready_until_purchase_color_is_explicit():
    report = assess_order_readiness(
        _package(), load_part_crosswalk(), route="bricklink",
        availability=PartColorAvailabilityRegistry(evidence=[]),
    )
    assert not report.supplier_ready
    assert [b.reason for b in report.blockers] == ["missing_purchase_color"]


def test_bricklink_evidence_does_not_authorize_wobrick_route():
    report = assess_order_readiness(
        _package(), load_part_crosswalk(), route="wobrick",
        availability=_availability("bricklink"),
        purchase_colors={("BRICK_2X4", None): "light_bluish_gray"},
    )
    assert not report.supplier_ready
    assert [b.reason for b in report.blockers] == ["part_color_availability_unverified_for_route"]


def test_catalog_supported_pair_is_enough_for_document_generation_readiness():
    report = assess_order_readiness(
        _package(), load_part_crosswalk(), route="bricklink",
        availability=_availability(),
        purchase_colors={("BRICK_2X4", None): "light_bluish_gray"},
    )
    assert report.part_color_verified_lines == 1
    assert report.supplier_ready


def test_live_readiness_requires_live_evidence():
    report = assess_order_readiness(
        _package(), load_part_crosswalk(), route="bricklink",
        availability=_availability(status="catalog_supported"),
        purchase_colors={("BRICK_2X4", None): "light_bluish_gray"},
        require_live_availability=True,
    )
    assert not report.supplier_ready
    assert [b.reason for b in report.blockers] == ["live_part_color_availability_unverified"]


def test_unknown_color_key_blocks_before_availability():
    report = assess_order_readiness(
        _package(), load_part_crosswalk(), route="bricklink",
        availability=PartColorAvailabilityRegistry(evidence=[]),
        purchase_colors={("BRICK_2X4", None): "not_a_real_catalog_color"},
    )
    assert not report.supplier_ready
    assert [b.reason for b in report.blockers] == ["unknown_purchase_color"]


def test_unknown_part_blocks_readiness_even_with_route_evidence():
    crosswalk = PartCrosswalk(entries=[
        PartCrosswalkEntry(
            engine_id="BRICK_2X4", bricklink_item_no="3001", ldraw_id="3001",
            rebrickable_part_num="3001",
            mapping_status="verified_catalog_identity",
            equivalence_policy="bricklink_catalog_item",
            verification_source="test", ldraw_verification_source="test",
        )
    ])
    registry = PartColorAvailabilityRegistry(evidence=[
        PartColorAvailabilityEvidence(
            route="bricklink", part_id="UNKNOWN_PART", color_key="light_bluish_gray",
            status="catalog_supported", source="test",
        )
    ])
    report = assess_order_readiness(
        _package("UNKNOWN_PART"), crosswalk, route="bricklink",
        availability=registry,
        purchase_colors={("UNKNOWN_PART", None): "light_bluish_gray"},
    )
    assert not report.supplier_ready
    assert [b.reason for b in report.blockers] == ["missing_verified_part_identity"]
