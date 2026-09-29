from __future__ import annotations

import pytest

from brickhouse.bricks.bags import BagGroup, BagPlan
from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.building.models import Facade
from brickhouse.procurement.manifest import generate_canonical_order_package


def _model() -> BrickModel:
    return BrickModel(
        building_id="house",
        volume_id="main",
        width_studs=8,
        depth_studs=6,
        height_plates=6,
        parts=[
            BrickModelPart(
                placement_id="p1",
                part_id="BRICK_1X2",
                category="brick",
                component="wall",
                x_studs=0,
                y_studs=0,
                z_plates=0,
                rotation_quarter_turns=0,
                facade=Facade.FRONT,
            ),
            BrickModelPart(
                placement_id="p2",
                part_id="BRICK_1X2",
                category="brick",
                component="wall",
                x_studs=2,
                y_studs=0,
                z_plates=0,
                rotation_quarter_turns=0,
                facade=Facade.FRONT,
            ),
            BrickModelPart(
                placement_id="p3",
                part_id="BRICK_1X1",
                category="brick",
                component="wall",
                x_studs=4,
                y_studs=0,
                z_plates=3,
                rotation_quarter_turns=0,
                facade=Facade.FRONT,
            ),
        ],
    )


def _bag_plan(last_placement: str = "p3") -> BagPlan:
    return BagPlan(
        building_id="house",
        volume_id="main",
        total_bags=2,
        total_parts=3,
        bags=[
            BagGroup(
                bag_number=1,
                phases=["Structure"],
                assembly_step_ids=["step-1"],
                placement_ids=["p1", "p2"],
            ),
            BagGroup(
                bag_number=2,
                phases=["Structure"],
                assembly_step_ids=["step-2"],
                placement_ids=[last_placement],
            ),
        ],
    )


def test_order_package_conserves_global_bom_and_numbered_bags():
    package = generate_canonical_order_package(_model(), _bag_plan())

    assert package.supplier_state == "canonical_only"
    assert package.total_parts == 3
    assert package.total_bags == 2
    assert [(line.part_id, line.quantity) for line in package.order_lines] == [
        ("BRICK_1X1", 1),
        ("BRICK_1X2", 2),
    ]
    assert [(line.part_id, line.quantity) for line in package.bags[0].lines] == [
        ("BRICK_1X2", 2),
    ]
    assert [(line.part_id, line.quantity) for line in package.bags[1].lines] == [
        ("BRICK_1X1", 1),
    ]
    assert sum(bag.total_parts for bag in package.bags) == package.total_parts


def test_order_package_refuses_missing_or_unknown_bag_placement_even_when_counts_match():
    with pytest.raises(ValueError, match="conserve BrickModel placements exactly"):
        generate_canonical_order_package(_model(), _bag_plan(last_placement="unknown"))


def test_order_package_refuses_different_building_volume():
    wrong = _bag_plan().model_copy(update={"volume_id": "other"})
    with pytest.raises(ValueError, match="same building volume"):
        generate_canonical_order_package(_model(), wrong)
