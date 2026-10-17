"""Test that screened wall placements export with truthful catalog dimensions."""
from brickhouse.bricks.physical_wall_export import opening_wall_part_records
from brickhouse.bricks.physical_placement_gate import Placement, build_geometrically

def test_export_is_reusable_in_geometric_brickmodel():
    records = opening_wall_part_records()
    assert len(records) == 12
    assert len({r["placement_id"] for r in records}) == 12
    for record in records:
        placement = Placement(record["part_id"], record["x_studs"],
                              record["y_studs"], record["z_plates"],
                              record["rotation_quarter_turns"])
        assert placement.dimensions() == (
            record["width_studs"], record["length_studs"], record["height_plates"]
        )
    assert len(build_geometrically([
        Placement(r["part_id"], r["x_studs"], r["y_studs"],
                  r["z_plates"], r["rotation_quarter_turns"])
        for r in records
    ]).accepted) == 12
