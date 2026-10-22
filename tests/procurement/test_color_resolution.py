from brickhouse.building.models import Appearance, AppearanceSection
from brickhouse.procurement.color_resolution import (
    color_resolution_csv,
    resolve_purchase_colors_from_appearance,
)
from brickhouse.procurement.models import BagOrderManifest, CanonicalOrderPackage, OrderLine


def _package(lines):
    total = sum(line.quantity for line in lines)
    return CanonicalOrderPackage(
        building_id="house",
        volume_id="main",
        total_parts=total,
        unique_part_types=len(lines),
        total_bags=1,
        order_lines=lines,
        bags=[
            BagOrderManifest(
                bag_number=1,
                phases=["Structure"],
                assembly_step_ids=["s1"],
                total_parts=total,
                lines=lines,
            )
        ],
    )


def test_exact_appearance_keys_resolve_wall_roof_and_frames_without_guessing():
    package = _package([
        OrderLine(part_id="BRICK_2X4", category="brick", quantity=2),
        OrderLine(part_id="BRICK_SLOPED_45_2X2", category="roof_tile", quantity=1),
        OrderLine(part_id="WINDOW_1X2X2_60592", category="window_frame", quantity=1),
    ])
    appearance = Appearance(
        walls=AppearanceSection(color="Light Bluish Gray"),
        roof=AppearanceSection(color="dark-brown"),
        frames=AppearanceSection(color="BLACK"),
    )

    report = resolve_purchase_colors_from_appearance(package, appearance)

    assert report.complete
    assert report.purchase_colors() == {
        ("BRICK_2X4", None): "light_bluish_gray",
        ("BRICK_SLOPED_45_2X2", None): "dark_brown",
        ("WINDOW_1X2X2_60592", None): "black",
    }


def test_off_white_and_dark_gray_are_not_silently_changed_to_catalog_colors():
    package = _package([
        OrderLine(part_id="BRICK_2X4", category="brick", quantity=2),
        OrderLine(part_id="BRICK_SLOPED_45_2X2", category="roof_tile", quantity=1),
    ])
    appearance = Appearance(
        walls=AppearanceSection(color="off_white"),
        roof=AppearanceSection(color="dark_gray"),
    )

    report = resolve_purchase_colors_from_appearance(package, appearance)

    assert not report.complete
    assert report.resolved_lines == 0
    assert report.unresolved_lines == 2
    assert {line.status for line in report.lines} == {
        "noncanonical_architectural_color"
    }
    assert report.purchase_colors() == {}


def test_missing_appearance_blocks_wall_and_window_pane_instead_of_inventing_colors():
    package = _package([
        OrderLine(part_id="BRICK_2X4", category="brick", quantity=1),
        OrderLine(part_id="GLASS_FOR_WINDOW_1X2X2_60601", category="window_pane", quantity=1),
    ])

    report = resolve_purchase_colors_from_appearance(package, None)

    assert report.unresolved_lines == 2
    assert {line.status for line in report.lines} == {"missing_architectural_color"}


def test_semantic_color_has_priority_but_must_itself_be_an_exact_catalog_key():
    package = _package([
        OrderLine(
            part_id="BRICK_1X1",
            category="masonry",
            semantic_color="slightly darker beige",
            quantity=2,
        )
    ])
    appearance = Appearance(walls=AppearanceSection(color="white"))

    report = resolve_purchase_colors_from_appearance(package, appearance)

    assert report.unresolved_lines == 1
    line = report.lines[0]
    assert line.source_kind == "semantic_color"
    assert line.source_color == "slightly darker beige"
    assert line.status == "noncanonical_architectural_color"


def test_resolution_csv_exposes_unresolved_reason_for_human_review():
    package = _package([
        OrderLine(part_id="BRICK_2X4", category="brick", quantity=1)
    ])
    report = resolve_purchase_colors_from_appearance(
        package,
        Appearance(walls=AppearanceSection(color="off_white")),
    )

    text = color_resolution_csv(report)

    assert "off_white" in text
    assert "noncanonical_architectural_color" in text
    assert "purchase_color_key" in text
