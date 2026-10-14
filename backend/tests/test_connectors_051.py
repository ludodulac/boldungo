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
    assert (r.status,r.interface_count)==("VALID",1)

def test_disjoint():
    assert validate_connection(part("a","BRICK_2X8"),part("b","BRICK_1X1",x=10,z=3)).status=="INVALID"

def test_plate_under_brick():
    r=validate_connection(part("a","PLATE_1X6"),part("b","BRICK_2X8",z=1))
    assert (r.status,r.interface_count)==("VALID",1)

def test_plate_over_brick():
    r=validate_connection(part("a","BRICK_2X8"),part("b","PLATE_1X6",z=3))
    assert (r.status,r.interface_count)==("VALID",1)

def test_rotations():
    r=validate_connection(part("a","BRICK_2X8",rot=1),part("b","BRICK_1X8",z=3,rot=1))
    assert (r.status,r.interface_count)==("VALID",8)

def test_wrong_height():
    assert validate_connection(part("a","BRICK_1X1"),part("b","BRICK_1X1",z=4)).status=="INVALID"

def test_collision():
    assert validate_connection(part("a","BRICK_2X8"),part("b","BRICK_1X1",z=2)).reason=="solid-volume-collision"

def test_unknown():
    assert validate_connection(part("a","BRICK_SLOPED_18_4X2"),part("b","BRICK_1X1",z=3)).status=="UNKNOWN"

def test_symmetry():
    a=part("a","PLATE_1X6");b=part("b","BRICK_2X8",z=1)
    assert validate_connection(a,b)==validate_connection(b,a)
