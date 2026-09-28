from __future__ import annotations

import json
from pathlib import Path

from brickhouse.bricks.brick_model import BrickModel

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "frontend" / "module-001-plus-module-002-plus-module-003-export.json"
MODULE = ROOT / "frontend" / "module-004-wood-terrace-export.json"
COMBINED = ROOT / "frontend" / "module-001-plus-module-002-plus-module-003-plus-module-004-export.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def footprint(part: dict) -> tuple[int, int, int, int, int, int]:
    width = part.get("width_studs", 1)
    length = part.get("length_studs", 1)
    if part.get("rotation_quarter_turns", 0) % 2:
        width, length = length, width
    return (
        part["x_studs"],
        part["x_studs"] + width,
        part["y_studs"],
        part["y_studs"] + length,
        part["z_plates"],
        part["z_plates"] + part.get("height_plates", 1),
    )


def cells(parts: list[dict]) -> set[tuple[int, int, int]]:
    out: set[tuple[int, int, int]] = set()
    for part in parts:
        x0, x1, y0, y1, z0, z1 = footprint(part)
        for x in range(x0, x1):
            for y in range(y0, y1):
                for z in range(z0, z1):
                    out.add((x, y, z))
    return out


def parts_with(fragment: str, parts: list[dict]) -> list[dict]:
    return [part for part in parts if fragment in part["placement_id"]]


def test_061_module004_schema_scope_and_source_modules_unchanged() -> None:
    source = load(SOURCE)
    module = load(MODULE)
    combined = load(COMBINED)

    BrickModel.model_validate(module["brick_model"])
    BrickModel.model_validate(combined["brick_model"])

    assert module["metadata"]["mission"] == "BOLDUNGO-061-MODULE004-COARSE-LEGO"
    assert module["metadata"]["metric_status"] == "COARSE_REFINABLE"
    assert module["metadata"]["photo_analysis_source"] == (
        "BOLDUNGO-060-MODULE004-BLIND-WOOD-TERRACE-RECONSTRUCTION"
    )

    source_parts = source["brick_model"]["parts"]
    combined_parts = combined["brick_model"]["parts"]
    assert combined_parts[: len(source_parts)] == source_parts
    assert combined["metadata"]["source_parts_modified"] is False
    assert all(
        part["placement_id"].startswith("module-004-")
        for part in combined_parts[len(source_parts) :]
    )


def test_061_coarse_footprint_level_and_house_interface() -> None:
    module = load(MODULE)
    metadata = module["metadata"]
    parts = module["brick_model"]["parts"]

    assert metadata["geometry"]["footprint"] == {"x": [24, 56], "y": [72, 88]}
    assert metadata["geometry"]["deck_walking_top_z"] == 49
    assert metadata["level_model"]["relation"] == "COARSE_EQUAL_LEVEL_PROXY"
    assert (
        metadata["level_model"]["exact_level_difference_status"]
        == "REFINABLE_NOT_CLAIMED_AS_PHOTOGRAPHIC_METRIC"
    )

    house = metadata["interfaces"]["TO_HOUSE"]
    assert house["rear_plane_y"] == 72
    assert house["relation"] == "SPATIALLY_ADJACENT_ALONG_REAR_EDGE"
    assert house["attachment_mechanism"] == "NOT_OBSERVABLE"
    assert house["rear_railing_added"] is False
    assert min(part["y_studs"] for part in parts) == 72


def test_061_wood_terrace_primary_underspace_remains_open() -> None:
    module = load(MODULE)
    occupied = cells(module["brick_model"]["parts"])

    # WOOD_TERRACE_PRIMARY_UNDERSPACE_REMAINS_OPEN
    # Interior excludes the observed front post/front beam, right beam and
    # house-adjacent rear boundary. It must remain empty below the beam datum.
    for x in range(25, 55):
        for y in range(73, 87):
            for z in range(0, 45):
                assert (x, y, z) not in occupied

    deck = parts_with("deck-platform", module["brick_model"]["parts"])
    assert deck
    deck_cells = cells(deck)
    for x in range(24, 56):
        for y in range(72, 88):
            assert (x, y, 48) in deck_cells


def test_061_observed_support_provenance_is_not_promoted_to_hidden_truth() -> None:
    module = load(MODULE)
    metadata = module["metadata"]
    parts = module["brick_model"]["parts"]

    observed = parts_with("observed-front-post", parts)
    assert observed
    observed_cells = cells(observed)
    for z in range(0, 45):
        assert (40, 87, z) in observed_cells

    supports = metadata["supports"]
    assert len(supports["observed"]) == 1
    assert supports["observed"][0]["status"] == "OBSERVED_SUPPORT_COARSELY_TRANSLATED"
    assert supports["constructive_supports_added"] == []
    assert not parts_with("constructive-support", parts)

    # Braces are observed in 060 but not faked with a bulky orthogonal/wedge proxy.
    assert supports["diagonal_braces"]["photo_status"] == "OBSERVED"
    assert supports["diagonal_braces"]["lego_status"] == (
        "DEFERRED_NO_HONEST_SLENDER_DIAGONAL_PRIMITIVE"
    )
    assert not parts_with("diagonal", parts)


def test_061_front_and_right_railing_signature_without_house_edge_railing() -> None:
    module = load(MODULE)
    parts = module["brick_model"]["parts"]

    front_posts = parts_with("front-railing-post", parts)
    right_posts = parts_with("right-railing-post", parts)
    front_top = parts_with("front-railing-top", parts)
    right_top = parts_with("right-railing-top", parts)

    assert front_posts and right_posts and front_top and right_top
    assert {part["x_studs"] for part in front_posts} == {28, 32, 36, 40, 44, 48, 52, 55}
    assert {part["y_studs"] for part in right_posts} == {72, 76, 80, 84}

    # Angle front-right is present and the uncertain left termination remains open.
    assert any(part["x_studs"] == 55 and part["y_studs"] == 87 for part in front_posts)
    assert not any(
        "railing" in part["placement_id"]
        and part["y_studs"] == 72
        and part["x_studs"] < 55
        for part in parts
    )
    assert not parts_with("rear-railing", parts)


def test_061_visible_edge_beams_exist() -> None:
    module = load(MODULE)
    parts = module["brick_model"]["parts"]

    front_beam = parts_with("front-edge-beam", parts)
    right_beam = parts_with("right-edge-beam", parts)
    assert front_beam and right_beam

    front_cells = cells(front_beam)
    right_cells = cells(right_beam)
    for x in range(24, 56):
        for z in range(45, 48):
            assert (x, 87, z) in front_cells
    for y in range(72, 87):
        for z in range(45, 48):
            assert (55, y, z) in right_cells


def test_061_wood_terrace_remains_structurally_distinct_from_masonry_module003() -> None:
    source = load(SOURCE)
    module = load(MODULE)

    m3_parts = [
        part for part in source["brick_model"]["parts"]
        if part["placement_id"].startswith("module-003-")
    ]
    m4_parts = module["brick_model"]["parts"]
    assert m3_parts and m4_parts

    # WOOD_TERRACE_REMAINS_STRUCTURALLY_DISTINCT_FROM_MASONRY_MODULE003
    assert cells(m3_parts).isdisjoint(cells(m4_parts))

    interface = module["metadata"]["interfaces"]["TO_MODULE003"]
    assert interface["adjacency_plane_x"] == 24
    assert interface["relation"] == "ADJACENT_HIGH_LEVEL_SYSTEMS_STRUCTURALLY_DISTINCT"
    assert interface["exact_connection"] == "NOT_OBSERVABLE"

    # A face-adjacent high-level contact exists without cell overlap.
    m3 = cells(m3_parts)
    m4 = cells(m4_parts)
    assert any(
        (23, y, z) in m3 and (24, y, z) in m4
        for y in range(72, 88)
        for z in range(45, 62)
    )


def test_061_piece_counts_and_combined_bundle_accounting() -> None:
    source = load(SOURCE)
    module = load(MODULE)
    combined = load(COMBINED)

    assert module["bom"]["total_parts"] == 141
    assert combined["metadata"]["module_004_piece_count"] == 141
    assert combined["metadata"]["module_001_plus_002_plus_003_piece_count"] == source["bom"]["total_parts"]
    assert combined["bom"]["total_parts"] == source["bom"]["total_parts"] + 141
    assert combined["metadata"]["combined_piece_count"] == combined["bom"]["total_parts"]
