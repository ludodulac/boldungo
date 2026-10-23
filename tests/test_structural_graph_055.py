"""LEGO2-055 graph tests: VALID edges only, no strength certification."""
from brickhouse.bricks.brick_model import BrickModelPart
from scripts.audit_terrace_048 import connector_graph_diagnostic

def brick(pid,x=0,y=0,z=0,kind="BRICK_1X1"):
    return BrickModelPart(placement_id=pid,part_id=kind,category="brick",
        component="roof_support",x_studs=x,y_studs=y,z_plates=z,
        rotation_quarter_turns=0)

def test_chain_and_articulation():
    d=connector_graph_diagnostic([brick("a"),brick("b",z=3),brick("c",z=6)])
    assert d["articulations"]==["b"]
    assert len(d["bridges"])==2 and len(d["components"])==1

def test_redundant_square():
    d=connector_graph_diagnostic([brick("a",0,0,0),brick("b",1,0,0),
        brick("c",0,0,3,kind="BRICK_1X8"),brick("d",1,0,3,kind="BRICK_1X8")])
    # No horizontal connector edges, and upper parts don't necessarily make a cycle.
    assert all(e["orientation"]=="vertical" for e in d["valid_edges"])

def test_separate_components():
    d=connector_graph_diagnostic([brick("a"),brick("b",x=10)])
    assert len(d["components"])==2 and len(d["isolated"])==2

def test_unknown_not_promoted():
    d=connector_graph_diagnostic([brick("a"),brick("b",z=3,kind="BRICK_1X2")])
    assert not d["valid_edges"] and len(d["unknown_edges"])==1
    assert len(d["components"])==2

def test_guided004_first_module():
    from brickhouse.bricks.catalog import standard_orthogonal_definitions
    definition=standard_orthogonal_definitions()["PLATE_1X6"]
    plate=BrickModelPart(placement_id="hidden-cross-plate:00007-00013",
        part_id="PLATE_1X6",category="plate",component="roof_support",
        x_studs=3,y_studs=20,z_plates=35,rotation_quarter_turns=1,
        width_studs=definition.width_studs,length_studs=definition.length_studs,
        height_plates=definition.height_plates)
    boards=[brick("board:"+n,x,17,36,"BRICK_2X8") for n,x in
            (("00001",3),("00007",5),("00013",7))]
    post=brick("timber-post-east:0033:00022",4,18,33)
    d=connector_graph_diagnostic([plate,*boards,post])
    assert d["pieces"]==5
    assert len(d["valid_edges"])==4
    assert sum(e["contacts"] for e in d["valid_edges"])==7
    assert len(d["components"])==1
    assert d["articulations"]==["board:00001","hidden-cross-plate:00007-00013"]
    assert len(d["bridges"])==4
    assert len(d["single_contact_edges"])==1
