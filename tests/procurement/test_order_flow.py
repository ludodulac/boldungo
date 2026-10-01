from io import BytesIO
from zipfile import ZipFile

import pytest

from brickhouse.bricks.assembly import generate_assembly_plan
from brickhouse.bricks.bom import generate_bom
from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.export import create_export_bundle
from brickhouse.building.models import Appearance, AppearanceSection, Facade
from brickhouse.procurement.availability import (
    PartColorAvailabilityEvidence,
    PartColorAvailabilityRegistry,
)
from brickhouse.procurement.catalog import load_part_crosswalk
from brickhouse.procurement.manifest import generate_canonical_order_package_from_bundle
from brickhouse.procurement.order_flow import (
    get_order_options,
    prepare_order,
    prepare_order_zip,
)


def _model() -> BrickModel:
    return BrickModel(
        building_id="order-flow-house",
        volume_id="main",
        width_studs=8,
        depth_studs=6,
        height_plates=12,
        parts=[
            BrickModelPart(
                placement_id="wall-1",
                part_id="BRICK_1X4",
                category="brick",
                component="wall",
                x_studs=0,
                y_studs=0,
                z_plates=0,
                rotation_quarter_turns=1,
                facade=Facade.FRONT,
            ),
            BrickModelPart(
                placement_id="detail-1",
                part_id="BRICK_1X1",
                category="brick",
                component="facade_detail",
                x_studs=4,
                y_studs=0,
                z_plates=3,
                rotation_quarter_turns=0,
                facade=Facade.FRONT,
            ),
            BrickModelPart(
                placement_id="roof-1",
                part_id="BRICK_SLOPED_45_2X4",
                category="roof_tile",
                component="roof",
                x_studs=0,
                y_studs=1,
                z_plates=9,
                rotation_quarter_turns=0,
                roof_side="negative",
            ),
        ],
    )


def _appearance(wall_color="tan") -> Appearance:
    return Appearance(
        walls=AppearanceSection(color=wall_color),
        roof=AppearanceSection(color="black"),
    )


def _finished_bundle(wall_color="tan"):
    model = _model()
    bom = generate_bom(model)
    assembly = generate_assembly_plan(model)
    bundle = create_export_bundle(
        model,
        bom,
        assembly_plan=assembly,
        appearance=_appearance(wall_color),
    )
    assert bundle.instruction_plan is not None
    assert bundle.bag_plan is not None
    assert bundle.bag_plan.total_bags == 3
    return bundle


def _catalog_availability() -> PartColorAvailabilityRegistry:
    evidence = []
    for route in ("bricklink", "wobrick"):
        for part_id, color_key in (
            ("BRICK_1X4", "tan"),
            ("BRICK_1X1", "tan"),
            ("BRICK_SLOPED_45_2X4", "black"),
        ):
            evidence.append(
                PartColorAvailabilityEvidence(
                    route=route,
                    part_id=part_id,
                    color_key=color_key,
                    status="catalog_supported",
                    source=f"fixture:{route}-catalog",
                )
            )
    return PartColorAvailabilityRegistry(evidence=evidence)


def test_finished_bundle_feeds_existing_canonical_order_package():
    bundle = _finished_bundle()

    package = generate_canonical_order_package_from_bundle(bundle)
    options = get_order_options(
        bundle,
        load_part_crosswalk(),
        availability=_catalog_availability(),
    )

    assert package.total_parts == bundle.bom.total_parts == len(bundle.brick_model.parts)
    assert package.total_bags == bundle.bag_plan.total_bags == 3
    assert options.total_parts == package.total_parts
    assert options.total_bags == package.total_bags


def test_bundle_totals_are_preserved_into_options_handoff_and_zip():
    bundle = _finished_bundle()
    availability = _catalog_availability()
    crosswalk = load_part_crosswalk()

    options = get_order_options(bundle, crosswalk, availability=availability)
    handoff = prepare_order(
        bundle,
        "bricklink",
        crosswalk,
        availability=availability,
    )
    zip_bytes = prepare_order_zip(
        bundle,
        "bricklink",
        crosswalk,
        availability=availability,
    )

    assert options.total_parts == bundle.bom.total_parts == 3
    assert handoff.total_parts == bundle.bom.total_parts == 3
    assert options.total_bags == bundle.bag_plan.total_bags == 3
    assert handoff.total_bags == bundle.bag_plan.total_bags == 3
    assert isinstance(zip_bytes, bytes)
    assert zip_bytes.startswith(b"PK")


def test_three_bundle_bags_are_preserved_in_supplier_handoff():
    bundle = _finished_bundle()
    availability = _catalog_availability()
    handoff = prepare_order(
        bundle,
        "bricklink",
        load_part_crosswalk(),
        availability=availability,
    )
    files = handoff.file_map()

    assert handoff.total_bags == 3
    assert "bags/BAG_01_PICKING.csv" in files
    assert "bags/BAG_02_PICKING.csv" in files
    assert "bags/BAG_03_PICKING.csv" in files
    assert "bags/BAG_01_BRICKLINK.xml" in files
    assert "bags/BAG_02_BRICKLINK.xml" in files
    assert "bags/BAG_03_BRICKLINK.xml" in files


def test_bricklink_ready_option_produces_existing_handoff():
    bundle = _finished_bundle()
    availability = _catalog_availability()
    crosswalk = load_part_crosswalk()

    option = get_order_options(
        bundle,
        crosswalk,
        availability=availability,
    ).for_route("bricklink")
    handoff = prepare_order(
        bundle,
        "bricklink",
        crosswalk,
        availability=availability,
    )

    assert option.document_ready
    assert not option.live_order_ready
    assert handoff.route == "bricklink"
    assert "05_ORDER_BRICKLINK_MASTER.xml" in handoff.file_map()


def test_wobrick_ready_option_produces_existing_handoff():
    bundle = _finished_bundle()
    availability = _catalog_availability()
    crosswalk = load_part_crosswalk()

    option = get_order_options(
        bundle,
        crosswalk,
        availability=availability,
    ).for_route("wobrick")
    handoff = prepare_order(
        bundle,
        "wobrick",
        crosswalk,
        availability=availability,
    )

    assert option.document_ready
    assert not option.live_order_ready
    assert handoff.route == "wobrick"
    files = handoff.file_map()
    assert "05_ORDER_WOBRICK_MASTER.csv" in files
    assert "bags/BAG_03_WOBRICK.csv" in files


def test_blocked_route_cannot_generate_incomplete_zip():
    bundle = _finished_bundle(wall_color="off_white")
    availability = _catalog_availability()
    crosswalk = load_part_crosswalk()

    option = get_order_options(
        bundle,
        crosswalk,
        availability=availability,
    ).for_route("bricklink")
    assert not option.document_ready

    with pytest.raises(ValueError, match="not document-ready"):
        prepare_order_zip(
            bundle,
            "bricklink",
            crosswalk,
            availability=availability,
        )


def test_bundle_without_bag_plan_blocks_procurement_boundary():
    model = _model()
    bundle = create_export_bundle(
        model,
        generate_bom(model),
        appearance=_appearance(),
    )
    assert bundle.bag_plan is None

    with pytest.raises(ValueError, match="no BagPlan"):
        get_order_options(
            bundle,
            load_part_crosswalk(),
            availability=_catalog_availability(),
        )


def test_order_flow_does_not_mutate_finished_bundle_artifacts():
    bundle = _finished_bundle()
    before = bundle.model_copy(deep=True)
    availability = _catalog_availability()
    crosswalk = load_part_crosswalk()

    options = get_order_options(bundle, crosswalk, availability=availability)
    handoff = prepare_order(bundle, "wobrick", crosswalk, availability=availability)
    zip_bytes = prepare_order_zip(bundle, "wobrick", crosswalk, availability=availability)

    assert options.total_parts == 3
    assert handoff.total_bags == 3
    with ZipFile(BytesIO(zip_bytes)) as archive:
        assert "05_ORDER_WOBRICK_MASTER.csv" in archive.namelist()

    assert bundle.brick_model == before.brick_model
    assert bundle.bom == before.bom
    assert bundle.assembly_plan == before.assembly_plan
    assert bundle.bag_plan == before.bag_plan
