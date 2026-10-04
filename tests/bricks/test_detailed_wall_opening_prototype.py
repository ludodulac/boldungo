from brickhouse.bricks.building_layout import generate_building_brick_shell
from brickhouse.bricks.spatial import generate_spatial_brick_shell
from brickhouse.building.models import Appearance, BuildingModel, Facade, Metadata, Opening, OpeningType, Position3D, SourceInfo, SourceKind, Volume, VolumeShape
from brickhouse.geometry import generate_building_geometry


def _shell():
    source = SourceInfo(kind=SourceKind.OBSERVED, confidence=1.0)
    building = BuildingModel(
        schema_version="0.1", id="generic-house", name="Generic house",
        building_type="house", units="m",
        volumes=[Volume(id="main", shape=VolumeShape.RECTANGULAR_PRISM,
                        position=Position3D(x=0,y=0,z=0), width=5, depth=4, height=3, floors=1, source=source)],
        openings=[Opening(id="opening", type=OpeningType.WINDOW, volume_id="main", facade=Facade.FRONT,
                          offset_horizontal=2, offset_vertical=1, width=1, height=1, source=source)],
        roofs=[], appearance=Appearance(), metadata=Metadata(created_from="synthetic"),
    )
    geometry = generate_building_geometry(building)
    return generate_building_brick_shell(geometry, front_width_studs=20)


def _span(part_id):
    return int(part_id.split("X")[-1])


def test_first_course_above_opening_has_a_single_bearing_lintel():
    shell = _shell()
    wall = next(w for w in shell.walls if w.facade is Facade.FRONT)
    opening = wall.grid.openings[0]
    spatial = generate_spatial_brick_shell(shell)
    course = opening.z_bricks + opening.height_bricks
    parts = [p for p in spatial.placements if p.facade is Facade.FRONT and p.z_plates == course * 3]
    bridging = [p for p in parts if p.x_studs < opening.x_studs and p.x_studs + _span(p.brick_id) > opening.x_studs + opening.width_studs]
    assert len(bridging) == 1


def test_opening_void_remains_empty_and_placements_use_catalog_bricks():
    shell = _shell()
    wall = next(w for w in shell.walls if w.facade is Facade.FRONT)
    opening = wall.grid.openings[0]
    spatial = generate_spatial_brick_shell(shell)
    occupied = set()
    for p in spatial.placements:
        if p.facade is not Facade.FRONT:
            continue
        for x in range(p.x_studs, p.x_studs + _span(p.brick_id)):
            occupied.add((x, p.z_plates // 3))
    for course in range(opening.z_bricks, opening.z_bricks + opening.height_bricks):
        for x in range(opening.x_studs, opening.x_studs + opening.width_studs):
            assert (x, course) not in occupied
    assert all(p.brick_id.startswith("BRICK_") for p in spatial.placements)
