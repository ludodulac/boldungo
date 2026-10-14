"""Regression tests for catalog-backed connector validation."""
from brickhouse.bricks.brick_model import BrickModelPart
from brickhouse.bricks.connectors import validate_connection

def part(pid,part_id,x=0,y=0,z=0,rot=0):
    return BrickModelPart(placement_id=pid,part_id=part_id,
        category="plate" if part_id.startswith("PLATE_") else "brick",
        component="roof_support",x_studs=x,y_studs=y,z_plates=z,
        rotation_quarter_turns=rot)

def test_stacked_bricks():
    r=validate_connection(part("a","BRICK_2X8"),part("b","BRICK_1X1",z=3))
    assert (r.status,r.interface_count)==("UNKNOWN",1)

def test_disjoint():
    assert validate_connection(part("a","BRICK_2X8"),part("b","BRICK_1X1",x=10,z=3)).status=="INVALID"

def test_plate_under_brick():
    r=validate_connection(part("a","PLATE_1X6"),part("b","BRICK_2X8",z=1))
    assert (r.status,r.interface_count)==("UNKNOWN",1)

def test_plate_over_brick():
    r=validate_connection(part("a","BRICK_2X8"),part("b","PLATE_1X6",z=3))
    assert (r.status,r.interface_count)==("UNKNOWN",1)

def test_rotations():
    r=validate_connection(part("a","BRICK_2X8",rot=1),part("b","BRICK_1X8",z=3,rot=1))
    assert (r.status,r.interface_count)==("UNKNOWN",8)

def test_wrong_height():
    assert validate_connection(part("a","BRICK_1X1"),part("b","BRICK_1X1",z=4)).status=="INVALID"

def test_collision():
    assert validate_connection(part("a","BRICK_2X8"),part("b","BRICK_1X1",z=2)).reason=="solid-volume-collision"

def test_unknown():
    assert validate_connection(part("a","BRICK_SLOPED_18_4X2"),part("b","BRICK_1X1",z=3)).status=="UNKNOWN"

def test_symmetry():
    a=part("a","PLATE_1X6");b=part("b","BRICK_2X8",z=1)
    assert validate_connection(a,b)==validate_connection(b,a)

# Exact unmodified GUIDED-004 placements from the 1,890-part export.
# These fixtures deliberately retain the catalog dimensions and rotations.
def test_guided004_terrace_real_placements():
    plate=part("scene-platform:south-timber-deck-main:hidden-cross-plate:00007-00013","PLATE_1X6",3,20,35,1)
    boards=[part("scene-platform:south-timber-deck-main:board:"+n,"BRICK_2X8",x,17,36)
            for n,x in (("00001",3),("00007",5),("00013",7))]
    post=part("scene-platform:south-timber-deck-main:support-solution:timber-post-east:0033:00022","BRICK_1X1",4,18,33)
    # 2 + 2 + 2 plate/board grid positions and 1 post/board position.
    contacts=[validate_connection(plate,b) for b in boards]
    support=validate_connection(post,boards[0])
    assert [r.interface_count for r in contacts]==[2,2,2]
    assert support.interface_count==1
    assert sum(r.interface_count for r in [*contacts,support])==7
    assert all(r.status=="UNKNOWN" for r in [*contacts,support])
    assert all(r.reason=="stud-grid-aligned-but-underside-connector-geometry-unverified"
               for r in [*contacts,support])
