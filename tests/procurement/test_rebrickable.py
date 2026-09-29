from brickhouse.procurement.catalog import load_part_crosswalk
from brickhouse.procurement.colors import load_color_crosswalk
from brickhouse.procurement.models import BagOrderManifest, CanonicalOrderPackage, OrderLine
from brickhouse.procurement.rebrickable import (
    build_bricklink_catalog_availability_from_rebrickable,
)


def _package():
    brick = OrderLine(part_id="BRICK_2X4", category="brick", quantity=3)
    tile = OrderLine(part_id="TILE_2X2", category="ridge_tile", quantity=2)
    return CanonicalOrderPackage(
        building_id="house", volume_id="main", total_parts=5, unique_part_types=2,
        total_bags=1, order_lines=[brick, tile],
        bags=[BagOrderManifest(
            bag_number=1, phases=["Structure"], assembly_step_ids=["s1"],
            total_parts=5, lines=[brick, tile],
        )],
    )


def test_crosswalk_keeps_rebrickable_identity_separate_from_ldraw_and_bricklink():
    parts = load_part_crosswalk().by_engine_id()
    assert parts["BRICK_2X4"].rebrickable_part_num == "3001"
    assert parts["PLATE_1X2"].bricklink_item_no == "3023"
    assert parts["PLATE_1X2"].ldraw_id == "3023b"
    assert parts["PLATE_1X2"].rebrickable_part_num == "3023"
    assert parts["TILE_2X2"].bricklink_item_no == "3068"
    assert parts["TILE_2X2"].ldraw_id == "3068b"
    assert parts["TILE_2X2"].rebrickable_part_num == "3068b"
    assert parts["GLASS_FOR_WINDOW_1X4X3_60603"].ldraw_id == "86210"
    assert parts["GLASS_FOR_WINDOW_1X4X3_60603"].rebrickable_part_num == "60603"


def test_color_crosswalk_has_rebrickable_ids_from_existing_rebrickable_dataset():
    colors = load_color_crosswalk().by_key()
    assert colors["black"].rebrickable_color_id == 0
    assert colors["white"].rebrickable_color_id == 15
    assert colors["light_bluish_gray"].rebrickable_color_id == 71
    assert colors["dark_bluish_gray"].rebrickable_color_id == 72
    assert colors["trans_clear"].rebrickable_color_id == 47


def test_rebrickable_verifier_checks_unique_parts_and_builds_bricklink_catalog_evidence():
    calls = []

    def fake_fetch(url, headers):
        calls.append((url, headers))
        if "/3001/colors/" in url:
            return {"results": [{"color": {"id": 71}}, {"color": {"id": 4}}]}
        if "/3068b/colors/" in url:
            return {"results": [{"color": {"id": 0}}]}
        raise AssertionError(url)

    registry = build_bricklink_catalog_availability_from_rebrickable(
        _package(),
        load_part_crosswalk(),
        purchase_colors={
            ("BRICK_2X4", None): "light_bluish_gray",
            ("TILE_2X2", None): "black",
        },
        api_key="secret-test-key",
        fetch_json=fake_fetch,
        request_delay_seconds=0,
    )

    assert len(calls) == 2
    assert all(call[1]["Authorization"] == "key secret-test-key" for call in calls)
    assert registry.supports("bricklink", "BRICK_2X4", "light_bluish_gray")
    assert registry.supports("bricklink", "TILE_2X2", "black")
    assert not registry.supports("wobrick", "BRICK_2X4", "light_bluish_gray")


def test_rebrickable_verifier_does_not_create_evidence_for_missing_color():
    def fake_fetch(url, headers):
        return {"results": [{"color": {"id": 4}}]}

    registry = build_bricklink_catalog_availability_from_rebrickable(
        _package(),
        load_part_crosswalk(),
        purchase_colors={
            ("BRICK_2X4", None): "light_bluish_gray",
            ("TILE_2X2", None): "black",
        },
        api_key="test",
        fetch_json=fake_fetch,
        request_delay_seconds=0,
    )

    assert registry.evidence == []


def test_rebrickable_api_key_is_required_but_never_part_of_source_url():
    try:
        build_bricklink_catalog_availability_from_rebrickable(
            _package(),
            load_part_crosswalk(),
            purchase_colors={("BRICK_2X4", None): "light_bluish_gray"},
            api_key="",
            request_delay_seconds=0,
        )
    except ValueError as exc:
        assert "API key" in str(exc)
    else:
        raise AssertionError("missing API key should fail")
