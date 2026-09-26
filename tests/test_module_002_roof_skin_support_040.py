from __future__ import annotations

import json
from pathlib import Path

from brickhouse.bricks.bom import BillOfMaterials
from brickhouse.bricks.brick_model import BrickModel
from brickhouse.bricks.geometry_adapter import CANONICAL_LDRAW_PARTS
from brickhouse.bricks.orthogonal_geometry import orthogonal_collisions
from brickhouse.bricks.piece_capabilities import (
    PieceCapabilityStage,
    create_current_engine_capability_registry,
    validate_model_part_capabilities,
)
from brickhouse.bricks.roof_skin_support import (
    SUPPORTED_ROOF_SKIN_ID,
    validate_supported_roof_skin,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "frontend" / "module-001-baseline57-export.json"
MODULE = ROOT / "frontend" / "module-002-roof-export.json"
COMBINED = ROOT / "frontend" / "module-001-plus-module-002-roof-export.json"
MASTER = ROOT / "data" / "processed" / "piece_types_master.csv"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_module_002_roof_skin_support_artifacts_and_counts() -> None:
    source = load(SOURCE)
    module = load(MODULE)
    combined = load(COMBINED)

    counts = module["metadata"]["piece_counts"]
    assert module["metadata"]["module_id"] == "MODULE_002_ROOF"
    assert module["metadata"]["structure_type"] == "ROOF_SKIN_PLUS_SUPPORT"
    assert module["metadata"]["skin_part"] == SUPPORTED_ROOF_SKIN_ID
    assert module["metadata"]["skin_profile_base_z"] == [
        141, 143, 144, 146, 147, 149, 150, 152, 153, 155, 156, 158, 159, 160, 161
    ]
    assert counts == {
        "skin": 2190,
        "support": 663,
        "ridge": 19,
        "module_002": 2872,
    }
    assert module["bom"]["total_parts"] == 2872
    assert combined["bom"]["total_parts"] == 4794
    assert combined["metadata"]["module_001_piece_count"] == 1922
    assert combined["metadata"]["combined_piece_count"] == 4794

    contract = module["metadata"]["architectural_contract"]
    assert contract["roof_type"] == "gable"
    assert contract["ridge_direction"] == "depth"
    assert contract["host_width_studs"] == 57
    assert contract["host_depth_studs"] == 71
    assert contract["roof_span_studs"] == 62
    assert contract["roof_depth_studs"] == 73
    assert contract["wall_to_eave_height_plates"] == 140
    assert contract["skin_eave_base_z"] == 141
    assert contract["ridge_top_z"] == 164
    assert contract["overhang"] == {
        "left_studs": 3,
        "right_studs": 2,
        "front_studs": 1,
        "rear_studs": 1,
    }

    # MODULE 001 stays byte-for-byte semantically unchanged in its own artifact.
    source_parts = source["brick_model"]["parts"]
    combined_host = combined["brick_model"]["parts"][: len(source_parts)]
    assert len(source_parts) == 1922
    for original, translated in zip(source_parts, combined_host):
        expected = dict(original)
        expected["x_studs"] += 3
        expected["y_studs"] += 1
        assert translated == expected


def test_module_002_skin_and_ridge_cover_the_complete_roof() -> None:
    module = load(MODULE)
    parts = module["brick_model"]["parts"]
    skin = [part for part in parts if part["category"] == "roof_tile"]
    ridge = [part for part in parts if part["category"] == "ridge_tile"]

    assert len(skin) == 2190
    assert len(ridge) == 19
    assert {part["part_id"] for part in skin} == {SUPPORTED_ROOF_SKIN_ID}
    assert all(
        (part["width_studs"], part["length_studs"], part["height_plates"]) == (2, 1, 2)
        for part in skin
    )

    expected_y = set(range(73))
    for side, starts in (
        ("negative", range(0, 30, 2)),
        ("positive", range(60, 30, -2)),
    ):
        side_parts = [part for part in skin if part["roof_side"] == side]
        assert {part["x_studs"] for part in side_parts} == set(starts)
        for x in starts:
            line = [part for part in side_parts if part["x_studs"] == x]
            assert {part["y_studs"] for part in line} == expected_y
            assert len(line) == 73

    ridge_cells = set()
    for part in ridge:
        assert part["x_studs"] == 30
        assert part["width_studs"] == 2
        assert part["z_plates"] == 163
        for x in range(30, 32):
            for y in range(part["y_studs"], part["y_studs"] + part["length_studs"]):
                ridge_cells.add((x, y))
    assert ridge_cells == {(x, y) for x in (30, 31) for y in range(73)}
    assert max(part["z_plates"] + part["height_plates"] for part in ridge) == 164


def test_combined_roof_support_has_three_level_connectivity_and_no_orthogonal_collision() -> None:
    source = load(SOURCE)
    combined = load(COMBINED)
    model = BrickModel.model_validate(combined["brick_model"])
    bill = BillOfMaterials.model_validate(combined["bom"])
    assert bill.total_parts == len(model.parts) == 4794
    assert len({part.placement_id for part in model.parts}) == len(model.parts)

    registry = create_current_engine_capability_registry(MASTER)
    # 5404 remains globally KNOWN: its use is approved only by the dedicated
    # supported-roof-skin context, not by silently promoting the master row.
    assert registry.get(SUPPORTED_ROOF_SKIN_ID).stage is PieceCapabilityStage.KNOWN
    validate_model_part_capabilities(model, registry)

    host_ids = {
        part["placement_id"]
        for part in source["brick_model"]["parts"]
    }
    report = validate_supported_roof_skin(model, host_placement_ids=host_ids)
    assert report.skin_to_support_valid
    assert report.support_internal_valid
    assert report.support_to_host_valid
    assert report.ridge_contact_valid
    assert report.collision_valid
    assert not report.unsupported_skin_ids
    assert not report.unsupported_ridge_ids
    assert not report.disconnected_support_ids
    assert not report.skin_envelope_collisions

    # Orthogonal support/wall collision is exact on the stud/plate grid.
    assert orthogonal_collisions(model) == []


def test_module_002_is_scope_clean_and_positioned_on_module_001() -> None:
    module = load(MODULE)
    combined = load(COMBINED)
    model = combined["brick_model"]
    roof_parts = module["brick_model"]["parts"]

    assert (model["width_studs"], model["depth_studs"], model["height_plates"]) == (57, 71, 164)
    assert (model["canvas_width_studs"], model["canvas_depth_studs"]) == (62, 73)
    assert (model["origin_x_studs"], model["origin_y_studs"]) == (3, 1)

    forbidden = ("chimney", "antenna", "gutter", "window", "door", "terrace", "stair")
    assert not any(
        any(word in (part["placement_id"] + " " + part["part_id"]).lower() for word in forbidden)
        for part in roof_parts
    )
    assert {
        part["component"] for part in roof_parts
    } == {"roof", "roof_support"}


def test_supported_5404_mapping_and_viewer_use_real_serialized_height_without_fake_stud() -> None:
    mapping = CANONICAL_LDRAW_PARTS[SUPPORTED_ROOF_SKIN_ID]
    assert mapping.ldraw_id == "5404"
    assert (mapping.width_studs, mapping.length_studs, mapping.height_plates) == (2, 1, 2)
    assert mapping.placement_kind == "slope"

    viewer = (ROOT / "frontend" / "viewer.js").read_text(encoding="utf-8")
    assert "wedgeGeometry(run,span,heightPlates=3)" in viewer
    assert "wedgeGeometry(run,span,world.heightPlates)" in viewer
    assert "p.part_id!=='BRICK_SLOPED_18_2X1X2_3'" in viewer
