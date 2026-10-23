"""LEGO2-056 frozen 56-placement fixture from real GUIDED-004 export.

Source: workflow 38542203291, artifact 11882274004, brick-model.json.
Coordinates and rotations are unmodified. Compact codes B/P map to existing catalog.
"""
from brickhouse.bricks.brick_model import BrickModelPart
from brickhouse.bricks.catalog import standard_orthogonal_definitions
from scripts.audit_terrace_048 import connector_graph_diagnostic
from scripts.experiment_terrace_057 import legacy_057_diagnostic

ROWS = """
board:00001|B2X8|3,17,36,0
board:00002|B2X8|3,25,36,0
board:00003|B2X3|3,33,36,0
board:00007|B2X8|5,17,36,0
board:00008|B2X8|5,25,36,0
board:00009|B2X3|5,33,36,0
board:00013|B2X8|7,17,36,0
board:00014|B2X8|7,25,36,0
board:00015|B2X3|7,33,36,0
board:00019|B2X8|9,17,36,0
board:00020|B2X8|9,25,36,0
board:00021|B2X3|9,33,36,0
board:00026|B2X8|11,25,36,0
board:00027|B2X3|11,33,36,0
board:00031|B1X8|13,17,36,0
board:00032|B1X8|13,25,36,0
board:00033|B1X3|13,33,36,0
hidden-cross-bond-029:01|P1X8|4,25,35,1
hidden-cross-bond-029:02|P1X8|4,33,35,1
hidden-cross-bond-029:03|P1X6|8,36,35,1
hidden-cross-bond-029:04|P1X8|6,17,35,1
hidden-cross-bond-029:05|P1X8|6,26,35,1
hidden-cross-bond-029:06|P1X3|3,23,35,0
hidden-cross-bond-029:07|P1X3|3,31,35,0
hidden-cross-bond-029:08|P1X3|7,34,35,0
hidden-cross-plate:00007-00013|P1X6|3,20,35,1
support-solution:timber-post-east:0033:00022|B1X1|4,18,33,0
support-solution:timber-post-west:0033:00034|B1X1|4,34,33,0
x_max:rail-post:00065|B1X1|13,20,39,0
x_max:rail-post:00069|B1X1|13,23,39,0
x_max:rail-post:00073|B1X1|13,26,39,0
x_max:rail-post:00077|B1X1|13,29,39,0
x_max:rail-post:00081|B1X1|13,32,39,0
x_max:rail-top-solution:00001|B1X8|13,17,42,0
x_max:rail-top-solution:00002|B1X8|13,25,42,0
x_max:rail-top-solution:00003|B1X3|13,33,42,0
x_min:rail-post:00035|B1X1|3,17,39,0
x_min:rail-post:00039|B1X1|3,20,39,0
x_min:rail-post:00043|B1X1|3,23,39,0
x_min:rail-post:00047|B1X1|3,26,39,0
x_min:rail-post:00051|B1X1|3,29,39,0
x_min:rail-post:00055|B1X1|3,32,39,0
x_min:rail-post:00059|B1X1|3,35,39,0
x_min:rail-top-solution:00004|B1X8|3,17,42,0
x_min:rail-top-solution:00005|B1X8|3,25,42,0
x_min:rail-top-solution:00006|B1X3|3,33,42,0
y_max:rail-post:00101|B1X1|6,35,39,0
y_max:rail-post:00105|B1X1|9,35,39,0
y_max:rail-post:00109|B1X2|12,35,39,1
y_max:rail-top-solution:00007|B1X8|4,35,42,1
y_max:rail-top-solution:00008|B1X1|12,35,42,0
y_min:rail-post:00089|B1X1|6,17,39,0
y_min:rail-post:00093|B1X1|9,17,39,0
y_min:rail-post:00097|B1X2|12,17,39,1
y_min:rail-top-solution:00009|B1X8|4,17,42,1
y_min:rail-top-solution:00010|B1X1|12,17,42,0
"""

def terrace_parts():
    prefix="scene-platform:south-timber-deck-main:"
    definitions=standard_orthogonal_definitions()
    parts=[]
    for line in ROWS.strip().splitlines():
        short,code,coords=line.split("|")
        part_id=("BRICK_" if code[0]=="B" else "PLATE_")+code[1:]
        x,y,z,rotation=map(int,coords.split(","))
        definition=definitions[part_id]
        dimensions=({"width_studs":definition.width_studs,
                     "length_studs":definition.length_studs,
                     "height_plates":definition.height_plates}
                    if code[0]=="P" else {})
        parts.append(BrickModelPart(placement_id=prefix+short,part_id=part_id,
            category="plate" if code[0]=="P" else "timber",
            component="facade_detail",facade="left",
            x_studs=x,y_studs=y,z_plates=z,rotation_quarter_turns=rotation,
            **dimensions))
    return parts

def test_real_56_structural_diagnostic():
    parts=terrace_parts()
    assert len(parts)==56
    result=legacy_057_diagnostic(parts)
    assert len(result["valid_edges"])==32
    assert sum(e["contacts"] for e in result["valid_edges"])==35
    assert len(result["unknown_edges"])==36
    assert sum(e["contacts"] for e in result["unknown_edges"])==50
    assert sorted(map(len,result["components"]),reverse=True)==[13,5,5,4,3]+[1]*26
    assert len(result["articulations"])==7
    assert len(result["bridges"])==10
    assert len(result["single_contact_edges"])==29
    assert len(result["identified_supports"])==2
    assert len(result["without_path_to_identified_support"])==42
    assert result["pieces"]-len(result["without_path_to_identified_support"])==14
    assert any(x.endswith("hidden-cross-bond-029:03") for x in result["isolated"])

def test_material_timber_does_not_hide_catalog_connector():
    from brickhouse.bricks.connectors import validate_connection
    parts=terrace_parts()
    by={p.placement_id.split("south-timber-deck-main:")[1]:p for p in parts}
    r=validate_connection(by["board:00001"],by["support-solution:timber-post-east:0033:00022"])
    assert (r.status,r.interface_count)==("VALID",1)
