from io import BytesIO
from zipfile import ZipFile

from fastapi.testclient import TestClient

import brickhouse.api as api_module
from brickhouse.api import app
from brickhouse.bricks.assembly import generate_assembly_plan
from brickhouse.bricks.bom import generate_bom
from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.export import create_export_bundle
from brickhouse.building.models import Appearance, AppearanceSection, Facade
from brickhouse.procurement.availability import (
    PartColorAvailabilityEvidence,
    PartColorAvailabilityRegistry,
)


client = TestClient(app)


def _model() -> BrickModel:
    return BrickModel(
        building_id="order-screen-house",
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


def _bundle(wall_color="tan", *, with_bags=True):
    model = _model()
    assembly = generate_assembly_plan(model) if with_bags else None
    return create_export_bundle(
        model,
        generate_bom(model),
        assembly_plan=assembly,
        appearance=Appearance(
            walls=AppearanceSection(color=wall_color),
            roof=AppearanceSection(color="black"),
        ),
    )


def _catalog_evidence() -> PartColorAvailabilityRegistry:
    rows = []
    for route in ("bricklink", "wobrick"):
        for part_id, color_key in (
            ("BRICK_1X4", "tan"),
            ("BRICK_1X1", "tan"),
            ("BRICK_SLOPED_45_2X4", "black"),
        ):
            rows.append(
                PartColorAvailabilityEvidence(
                    route=route,
                    part_id=part_id,
                    color_key=color_key,
                    status="catalog_supported",
                    source=f"fixture:{route}-catalog",
                )
            )
    return PartColorAvailabilityRegistry(evidence=rows)


def _install_catalog_evidence(monkeypatch):
    registry = _catalog_evidence()
    monkeypatch.setattr(
        api_module,
        "_procurement_availability_for_bundle",
        lambda bundle: registry,
    )


def test_order_options_http_uses_backend_totals_and_keeps_live_distinct():
    bundle = _bundle()

    response = client.post(
        "/api/v1/order-options",
        json={"bundle": bundle.model_dump(mode="json")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_parts"] == bundle.bom.total_parts == 3
    assert payload["total_bags"] == bundle.bag_plan.total_bags == 3
    assert [option["route"] for option in payload["options"]] == ["bricklink", "wobrick"]
    assert all(option["document_ready"] is True for option in payload["options"])
    assert all(option["live_order_ready"] is False for option in payload["options"])


def test_bricklink_document_ready_downloads_nonempty_backend_zip_without_stock_evidence():
    bundle = _bundle()

    response = client.post(
        "/api/v1/prepare-order/bricklink",
        json={"bundle": bundle.model_dump(mode="json")},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    assert "boldungo-maison-bricklink.zip" in response.headers["content-disposition"]
    assert response.content.startswith(b"PK")
    with ZipFile(BytesIO(response.content)) as archive:
        names = archive.namelist()
        assert "05_ORDER_BRICKLINK_MASTER.xml" in names
        assert "bags/BAG_01_BRICKLINK.xml" in names
        assert "bags/BAG_02_BRICKLINK.xml" in names
        assert "bags/BAG_03_BRICKLINK.xml" in names


def test_wobrick_document_ready_downloads_nonempty_backend_zip_without_stock_evidence():
    bundle = _bundle()

    response = client.post(
        "/api/v1/prepare-order/wobrick",
        json={"bundle": bundle.model_dump(mode="json")},
    )

    assert response.status_code == 200
    assert "boldungo-maison-compatible.zip" in response.headers["content-disposition"]
    with ZipFile(BytesIO(response.content)) as archive:
        names = archive.namelist()
        assert "05_ORDER_WOBRICK_MASTER.csv" in names
        assert "bags/BAG_01_WOBRICK.csv" in names
        assert "bags/BAG_02_WOBRICK.csv" in names
        assert "bags/BAG_03_WOBRICK.csv" in names


def test_document_ready_without_live_stock_still_downloads():
    bundle = _bundle()
    options = client.post(
        "/api/v1/order-options",
        json={"bundle": bundle.model_dump(mode="json")},
    ).json()

    bricklink = next(option for option in options["options"] if option["route"] == "bricklink")
    assert bricklink["document_ready"] is True
    assert bricklink["live_order_ready"] is False

    response = client.post(
        "/api/v1/prepare-order/bricklink",
        json={"bundle": bundle.model_dump(mode="json")},
    )
    assert response.status_code == 200
    assert len(response.content) > 0


def test_unresolved_color_blocks_zip_and_returns_human_message():
    bundle = _bundle("off_white")

    options_response = client.post(
        "/api/v1/order-options",
        json={"bundle": bundle.model_dump(mode="json")},
    )
    assert options_response.status_code == 200
    bricklink = next(
        option for option in options_response.json()["options"]
        if option["route"] == "bricklink"
    )
    assert bricklink["document_ready"] is False
    messages = [blocker["message"] for blocker in bricklink["blockers"]]
    assert any("Couleur physique" in message for message in messages)

    download = client.post(
        "/api/v1/prepare-order/bricklink",
        json={"bundle": bundle.model_dump(mode="json")},
    )
    assert download.status_code == 409
    assert download.headers["content-type"].startswith("application/json")
    assert "finalisée" in download.json()["detail"]


def test_bundle_without_bag_plan_is_human_blocked_and_no_zip():
    bundle = _bundle(with_bags=False)

    options = client.post(
        "/api/v1/order-options",
        json={"bundle": bundle.model_dump(mode="json")},
    )
    assert options.status_code == 422
    assert "sacs de construction" in options.json()["detail"]
    assert "BagPlan" not in options.json()["detail"]

    download = client.post(
        "/api/v1/prepare-order/bricklink",
        json={"bundle": bundle.model_dump(mode="json")},
    )
    assert download.status_code == 409
    assert not download.content.startswith(b"PK")
