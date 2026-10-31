from lego_geometry_engine import (
    AABB, LDrawLibrary, PartDefinition, Transform, find_connections, instantiate,
)


def test_rectangular_brick_connectors_follow_ldraw_length_x_width_z(tmp_path):
    library = LDrawLibrary(tmp_path)
    connectors = tuple(
        library._infer_basic_connectors(
            "Brick 1 x 2",
            AABB((-20.0, -4.0, -10.0), (20.0, 24.0, 10.0)),
        )
    )
    studs = [connector for connector in connectors if connector.type == "stud"]
    anti_studs = [connector for connector in connectors if connector.type == "anti_stud"]

    assert {connector.position for connector in studs} == {
        (-10.0, 0.0, 0.0),
        (10.0, 0.0, 0.0),
    }
    assert {connector.position for connector in anti_studs} == {
        (-10.0, 24.0, 0.0),
        (10.0, 24.0, 0.0),
    }


def test_baseplate_3811_has_top_studs_but_not_fake_underside_connectors(tmp_path):
    """3811.dat top face has 32x32 studs, body y=0..4, no anti-stud bottom."""
    library = LDrawLibrary(tmp_path)
    connectors = tuple(
        library._infer_basic_connectors(
            "Baseplate 32 x 32",
            AABB((-320.0, -4.0, -320.0), (320.0, 4.0, 320.0)),
        )
    )
    studs = [c for c in connectors if c.type == "stud"]
    assert len(studs) == 1024
    assert not [c for c in connectors if c.type == "anti_stud"]
    positions = {c.position for c in studs}
    assert (-310.0, 0.0, -310.0) in positions
    assert (310.0, 0.0, 310.0) in positions
    assert all(c.orientation == (0, -1, 0) for c in studs)


def test_original_validation1_wall_3008_aligns_on_3811_grid_only_at_exact_position(tmp_path):
    """Nominal stud mating, not an assertion of no mesh collisions or strength.

    Coordinates and bounding boxes correspond to the two original LDraw placements
    M1-EXPERIMENTAL-BASE-3811 and wall-000001, kept unchanged.
    """
    library = LDrawLibrary(tmp_path)
    plate_bbox = AABB((-320, -4, -320), (320, 4, 320))
    wall_bbox = AABB((-80, -4, -10), (80, 24, 10))
    base = PartDefinition(
        "3811.dat", (), plate_bbox,
        connectors=tuple(library._infer_basic_connectors("Baseplate 32 x 32", plate_bbox)),
    )
    wall = PartDefinition(
        "3008.dat", (), wall_bbox,
        connectors=tuple(library._infer_basic_connectors("Brick 1 x 8", wall_bbox)),
    )
    base_instance = instantiate(base, "M1-EXPERIMENTAL-BASE-3811", Transform.translation(640, 0, 360))
    wall_instance = instantiate(wall, "wall-000001", Transform.translation(400, -24, 50))
    assert len(find_connections(base_instance, wall_instance)) == 8

    # 2 LDraw units out of alignment is too far for nominal stud/cavity tolerance.
    displaced = instantiate(wall, "displaced", Transform.translation(402, -24, 50))
    assert not find_connections(base_instance, displaced)

    # A wall with a solid overlap into the base may still show X/Z alignment,
    # but must NOT pass the connector-plane equality test.
    wrong_height = instantiate(wall, "wrong-height", Transform.translation(400, -22, 50))
    assert not find_connections(base_instance, wrong_height)
