from pathlib import Path

import pytest

from brickhouse.bricks.bom import generate_bom
from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.catalog import create_m0_brick_catalog, create_standard_plate_catalog
from brickhouse.bricks.export import create_export_bundle, export_bundle_json
from brickhouse.bricks.orthogonal_geometry import orthogonal_bounds, orthogonal_collisions
from brickhouse.bricks.piece_capabilities import (
    PieceCapabilityStage,
    create_current_engine_capability_registry,
    validate_model_part_capabilities,
)
from brickhouse.bricks.support_chain import analyze_standard_brick_support_chain
from brickhouse.building.models import Facade


MASTER = Path("data/processed/piece_types_master.csv")
PLATES = {
    "PLATE_1X1": (1, 1),
    "PLATE_1X2": (1, 2),
    "PLATE_1X3": (1, 3),
    "PLATE_1X4": (1, 4),
    "PLATE_1X6": (1, 6),
    "PLATE_1X8": (1, 8),
}


def part(pid, part_id, category, z, rotation=0):
    kwargs = {}
    if category == "plate":
        definition = create_standard_plate_catalog().get(part_id)
        kwargs = dict(
            width_studs=definition.width_studs,
            length_studs=definition.length_studs,
            height_plates=definition.height_plates,
        )
    return BrickModelPart(
        placement_id=pid,
        part_id=part_id,
        category=category,
        component="wall",
        x_studs=0,
        y_studs=0,
        z_plates=z,
        rotation_quarter_turns=rotation,
        facade=Facade.FRONT,
        **kwargs,
    )


def stack_3_1_3():
    return BrickModel(
        building_id="orthogonal-capability",
        volume_id="stack",
        width_studs=2,
        depth_studs=2,
        height_plates=7,
        parts=[
            part("brick-bottom", "BRICK_1X2", "brick", 0),
            part("plate-middle", "PLATE_1X2", "plate", 3),
            part("brick-top", "BRICK_1X2", "brick", 4),
        ],
    )


def test_standard_plate_catalog_is_exactly_one_plate_high_and_bricks_stay_three():
    plates = create_standard_plate_catalog()
    assert {item.id: (item.width_studs, item.length_studs) for item in plates.bricks} == PLATES
    assert {item.height_plates for item in plates.bricks} == {1}
    assert {item.category for item in plates.bricks} == {"plate"}
    assert {item.height_plates for item in create_m0_brick_catalog().bricks} == {3}


def test_plate_quarter_turn_uses_generic_orthogonal_footprint():
    p = part("rotated", "PLATE_1X2", "plate", 0, rotation=1)
    bounds = orthogonal_bounds(p)
    assert bounds is not None
    assert (bounds.x1 - bounds.x0, bounds.y1 - bounds.y0, bounds.z1 - bounds.z0) == (2, 1, 1)


def test_3_1_3_stack_has_exact_bounds_no_collision_and_continuous_support():
    model = stack_3_1_3()
    bounds = {p.placement_id: orthogonal_bounds(p) for p in model.parts}
    assert (bounds["brick-bottom"].z0, bounds["brick-bottom"].z1) == (0, 3)
    assert (bounds["plate-middle"].z0, bounds["plate-middle"].z1) == (3, 4)
    assert (bounds["brick-top"].z0, bounds["brick-top"].z1) == (4, 7)
    assert orthogonal_collisions(model) == []

    report = analyze_standard_brick_support_chain(model)
    assert report.valid
    nodes = {node.placement_id: node for node in report.nodes}
    assert nodes["plate-middle"].supporters == ["brick-bottom"]
    assert nodes["brick-top"].supporters == ["plate-middle"]
    assert nodes["brick-top"].reaches_ground is True


def test_plate_inside_brick_vertical_volume_is_a_collision():
    model = stack_3_1_3().model_copy(deep=True)
    model.parts[1].z_plates = 2
    assert orthogonal_collisions(model) == [("brick-bottom", "plate-middle")]


def test_plate_geometry_must_match_canonical_definition():
    with pytest.raises(ValueError, match="canonical definition"):
        BrickModelPart(
            placement_id="bad", part_id="PLATE_1X2", category="plate", component="wall",
            x_studs=0, y_studs=0, z_plates=0, rotation_quarter_turns=0,
            facade=Facade.FRONT, width_studs=1, length_studs=2, height_plates=3,
        )


def test_all_audited_plates_are_placement_approved_only_after_geometry_capability():
    registry = create_current_engine_capability_registry(MASTER)
    for part_id in PLATES:
        capability = registry.get(part_id)
        assert capability.stage is PieceCapabilityStage.PLACEMENT_APPROVED
        assert capability.auto_placeable is True
    validate_model_part_capabilities(stack_3_1_3(), registry)


def test_3_1_3_serialization_bom_and_export_preserve_plate_identity_and_geometry():
    model = stack_3_1_3()
    restored = BrickModel.model_validate_json(model.model_dump_json())
    assert restored == model
    assert restored.height_plates == 7

    bom = generate_bom(model)
    assert bom.total_parts == 3
    assert {(line.part_id, line.category, line.quantity) for line in bom.lines} == {
        ("BRICK_1X2", "brick", 2),
        ("PLATE_1X2", "plate", 1),
    }

    bundle = create_export_bundle(model, bom)
    payload = export_bundle_json(bundle)
    assert '"height_plates": 1' in payload
    assert '"category": "plate"' in payload
    assert bundle.metadata.physical_model.height_mm == pytest.approx(22.4)


def test_viewer_prefers_serialized_geometry_and_keeps_legacy_fallback():
    js = Path("frontend/viewer.js").read_text(encoding="utf-8")
    assert "p.height_plates??1" in js
    assert "p.width_studs??parsed.a" in js
    assert "'brick','plate','facade_detail'" in js
    assert "candidate.z_plates+dims(candidate).heightPlates===part.z_plates" in js
