from copy import deepcopy

from brickhouse.procurement.availability import (
    PartColorAvailabilityEvidence,
    PartColorAvailabilityRegistry,
)
from brickhouse.procurement.catalog import load_part_crosswalk
from brickhouse.procurement.colors import load_color_crosswalk
from brickhouse.procurement.models import BagOrderManifest, CanonicalOrderPackage, OrderLine
from brickhouse.procurement.physical import aggregate_physical_requirements
from brickhouse.procurement.readiness import assess_order_readiness


def _package(lines, bags=None):
    if bags is None:
        bags = [
            BagOrderManifest(
                bag_number=1,
                phases=["Structure"],
                assembly_step_ids=["s1"],
                total_parts=sum(line.quantity for line in lines),
                lines=[line.model_copy(deep=True) for line in lines],
            )
        ]
    return CanonicalOrderPackage(
        building_id="house",
        volume_id="main",
        total_parts=sum(line.quantity for line in lines),
        unique_part_types=len(lines),
        total_bags=len(bags),
        order_lines=lines,
        bags=bags,
    )


def _same_part_two_semantics():
    return _package([
        OrderLine(
            part_id="BRICK_2X4",
            category="brick",
            semantic_color="warm stone",
            quantity=60,
        ),
        OrderLine(
            part_id="BRICK_2X4",
            category="brick",
            semantic_color="slightly darker stone",
            quantity=40,
        ),
    ])


def _same_part_colors():
    return {
        ("BRICK_2X4", "warm stone"): "tan",
        ("BRICK_2X4", "slightly darker stone"): "tan",
    }


def _availability(part_id, color_key, quantity):
    return PartColorAvailabilityRegistry(evidence=[
        PartColorAvailabilityEvidence(
            route="bricklink",
            part_id=part_id,
            color_key=color_key,
            status="live_available",
            source="test",
            available_quantity=quantity,
        )
    ])


def _live_report(package, colors, availability):
    return assess_order_readiness(
        package,
        load_part_crosswalk(),
        route="bricklink",
        availability=availability,
        purchase_colors=colors,
        require_live_availability=True,
    )


def test_same_part_color_60_plus_40_is_compared_once_to_stock_70():
    package = _same_part_two_semantics()
    before = package.model_dump(mode="python")

    report = _live_report(
        package,
        _same_part_colors(),
        _availability("BRICK_2X4", "tan", 70),
    )

    assert report.total_order_lines == 2
    assert report.total_physical_requirements == 1
    assert len(report.physical_requirements) == 1
    assert report.physical_requirements[0].required_quantity == 100
    assert report.physical_requirements[0].identity == ("BRICK_2X4", "tan")
    assert report.shortage_total == 30
    assert not report.supplier_ready
    assert [(b.required_quantity, b.available_quantity, b.shortage_quantity) for b in report.blockers] == [
        (100, 70, 30)
    ]
    assert package.model_dump(mode="python") == before


def test_same_part_color_exact_stock_100_is_live_ready():
    report = _live_report(
        _same_part_two_semantics(),
        _same_part_colors(),
        _availability("BRICK_2X4", "tan", 100),
    )

    assert report.physical_requirements[0].required_quantity == 100
    assert report.quantity_covered_lines == 1
    assert report.shortage_total == 0
    assert report.blockers == []
    assert report.supplier_ready


def test_same_part_color_stock_140_keeps_required_100_and_canonical_order_unchanged():
    package = _same_part_two_semantics()
    before_lines = deepcopy(package.order_lines)
    before_bags = deepcopy(package.bags)

    report = _live_report(
        package,
        _same_part_colors(),
        _availability("BRICK_2X4", "tan", 140),
    )

    assert report.physical_requirements[0].required_quantity == 100
    assert report.quantity_covered_lines == 1
    assert report.supplier_ready
    assert [(line.semantic_color, line.quantity) for line in package.order_lines] == [
        ("warm stone", 60),
        ("slightly darker stone", 40),
    ]
    assert package.order_lines == before_lines
    assert package.bags == before_bags
    assert package.total_parts == 100


def test_same_part_different_purchase_colors_are_not_aggregated():
    lines = [
        OrderLine(
            part_id="BRICK_2X4",
            category="brick",
            semantic_color="stone",
            quantity=60,
        ),
        OrderLine(
            part_id="BRICK_2X4",
            category="brick",
            semantic_color="charcoal",
            quantity=40,
        ),
    ]
    package = _package(lines)
    colors = {
        ("BRICK_2X4", "stone"): "tan",
        ("BRICK_2X4", "charcoal"): "black",
    }

    requirements = aggregate_physical_requirements(
        package.order_lines,
        part_crosswalk=load_part_crosswalk(),
        color_crosswalk=load_color_crosswalk(),
        purchase_colors=colors,
    )

    assert [(r.identity, r.required_quantity) for r in requirements] == [
        (("BRICK_2X4", "black"), 40),
        (("BRICK_2X4", "tan"), 60),
    ]


def test_different_parts_same_purchase_color_are_not_aggregated():
    lines = [
        OrderLine(
            part_id="BRICK_2X4",
            category="brick",
            semantic_color="stone large",
            quantity=60,
        ),
        OrderLine(
            part_id="BRICK_1X2",
            category="brick",
            semantic_color="stone small",
            quantity=40,
        ),
    ]
    package = _package(lines)
    colors = {
        ("BRICK_2X4", "stone large"): "tan",
        ("BRICK_1X2", "stone small"): "tan",
    }

    requirements = aggregate_physical_requirements(
        package.order_lines,
        part_crosswalk=load_part_crosswalk(),
        color_crosswalk=load_color_crosswalk(),
        purchase_colors=colors,
    )

    assert {(r.part_id, r.purchase_color_key, r.required_quantity) for r in requirements} == {
        ("BRICK_2X4", "tan", 60),
        ("BRICK_1X2", "tan", 40),
    }


def test_three_canonical_lines_to_same_physical_pair_become_one_requirement_100():
    lines = [
        OrderLine(part_id="BRICK_2X4", category="brick", semantic_color="a", quantity=25),
        OrderLine(part_id="BRICK_2X4", category="brick", semantic_color="b", quantity=35),
        OrderLine(part_id="BRICK_2X4", category="brick", semantic_color="c", quantity=40),
    ]
    package = _package(lines)
    colors = {
        ("BRICK_2X4", "a"): "tan",
        ("BRICK_2X4", "b"): "tan",
        ("BRICK_2X4", "c"): "tan",
    }

    report = _live_report(
        package,
        colors,
        _availability("BRICK_2X4", "tan", 100),
    )

    assert report.total_order_lines == 3
    assert report.total_physical_requirements == 1
    assert report.physical_requirements[0].required_quantity == 100
    assert report.quantity_covered_lines == 1
    assert report.supplier_ready


def test_bags_remain_separate_while_master_physical_requirement_aggregates():
    a = OrderLine(
        part_id="BRICK_2X4",
        category="brick",
        semantic_color="warm stone",
        quantity=30,
    )
    b = OrderLine(
        part_id="BRICK_2X4",
        category="brick",
        semantic_color="slightly darker stone",
        quantity=70,
    )
    package = _package(
        [a.model_copy(update={"quantity": 60}), b.model_copy(update={"quantity": 40})],
        bags=[
            BagOrderManifest(
                bag_number=1,
                phases=["Structure"],
                assembly_step_ids=["s1"],
                total_parts=30,
                lines=[a],
            ),
            BagOrderManifest(
                bag_number=2,
                phases=["Structure"],
                assembly_step_ids=["s2"],
                total_parts=70,
                lines=[b],
            ),
        ],
    )

    # The deliberately different semantic split above is invalid as a canonical
    # conservation example, so construct a valid 30 + 70 package directly.
    package = _package(
        [
            OrderLine(
                part_id="BRICK_2X4",
                category="brick",
                semantic_color="bag one stone",
                quantity=30,
            ),
            OrderLine(
                part_id="BRICK_2X4",
                category="brick",
                semantic_color="bag two stone",
                quantity=70,
            ),
        ],
        bags=[
            BagOrderManifest(
                bag_number=1,
                phases=["Structure"],
                assembly_step_ids=["s1"],
                total_parts=30,
                lines=[
                    OrderLine(
                        part_id="BRICK_2X4",
                        category="brick",
                        semantic_color="bag one stone",
                        quantity=30,
                    )
                ],
            ),
            BagOrderManifest(
                bag_number=2,
                phases=["Structure"],
                assembly_step_ids=["s2"],
                total_parts=70,
                lines=[
                    OrderLine(
                        part_id="BRICK_2X4",
                        category="brick",
                        semantic_color="bag two stone",
                        quantity=70,
                    )
                ],
            ),
        ],
    )
    colors = {
        ("BRICK_2X4", "bag one stone"): "tan",
        ("BRICK_2X4", "bag two stone"): "tan",
    }
    before_bags = deepcopy(package.bags)

    requirements = aggregate_physical_requirements(
        package.order_lines,
        part_crosswalk=load_part_crosswalk(),
        color_crosswalk=load_color_crosswalk(),
        purchase_colors=colors,
    )

    assert requirements[0].required_quantity == 100
    assert [bag.total_parts for bag in package.bags] == [30, 70]
    assert package.bags == before_bags
