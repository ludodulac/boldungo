"""Small canonical BrickModel fixture for a geometry-only opening-wall experiment.

This does NOT alter or certify the house's architectural measurements.
"""
from .brick_model import BrickModel
from .physical_wall_export import opening_wall_part_records
from .physical_assembly import generate_geometrically_screened_assembly_plan

def opening_wall_brick_model():
    return BrickModel(
        building_id="engineering-fixture",
        volume_id="opening-wall-12x2",
        width_studs=12,
        depth_studs=2,
        height_plates=15,
        parts=opening_wall_part_records(),
    )

def opening_wall_geometrically_screened_notice():
    """Produce an ordering/geometry-only plan; connectors are NOT checked."""
    model = opening_wall_brick_model()
    plan = generate_geometrically_screened_assembly_plan(model)
    return model, plan


def opening_wall_screened_notice():
    """Legacy fixture alias for GEOMETRY_ONLY, never strict physical validation."""
    return opening_wall_geometrically_screened_notice()
