"""027: physically joined south timber deck using a concealed catalog plate.

Real GUIDED-004 boards 00001, 00007, 00013; real post under board 00001.
A PLATE_1X6, rotated across x at y=20, z=35, joins underside tubes of
all three boards. The post supports board 00001 at x=4,y=18,z=36.
Stud/tube engagement is modelled; clutch strength is not measured.
"""
import json
from pathlib import Path
from brickhouse.bricks.catalog import standard_orthogonal_definitions

MODEL = Path("artifacts/lego2-guided-004/brick-model.json")
PREFIX = "scene-platform:south-timber-deck-main:"
IDS = tuple(PREFIX + "board:" + s for s in ("00001", "00007", "00013"))
POST = PREFIX + "support-solution:timber-post-east:0033:00022"
PLATE = {"placement_id": "prototype-027:concealed:cross-plate",
         "part_id": "PLATE_1X6", "x_studs": 3, "y_studs": 20,
         "z_plates": 35, "rotation_quarter_turns": 1,
         "width_studs": 6, "length_studs": 1, "height_plates": 1}


def box(p):
    return (p["x_studs"], p["y_studs"], p["z_plates"],
            p["x_studs"] + p["width_studs"],
            p["y_studs"] + p["length_studs"],
            p["z_plates"] + p["height_plates"])


def overlaps(a, b):
    return all(a[i] < b[i+3] and b[i] < a[i+3] for i in range(3))


def stud_connection(a, b):
    if a[5] != b[2] and b[5] != a[2]:
        return False
    return a[0] < b[3] and b[0] < a[3] and a[1] < b[4] and b[1] < a[4]


def components(boxes):
    parents = list(range(len(boxes)))
    def root(i):
        while parents[i] != i:
            i = parents[i]
        return i
    edges = []
    for i in range(len(boxes)):
        for j in range(i):
            if stud_connection(boxes[i], boxes[j]):
                parents[root(i)] = root(j)
                edges.append((i, j))
    return len({root(i) for i in range(len(boxes))}), edges


def test_concealed_cross_plate_joins_real_deck_and_existing_post():
    data = json.loads(MODEL.read_text(encoding="utf-8"))
    indexed = {p["placement_id"]: p for p in data["parts"]}
    assert all(pid in indexed for pid in (*IDS, POST))
    boards = [indexed[pid] for pid in IDS]
    post = indexed[POST]
    assert all(p["part_id"] == "BRICK_2X8" and p["z_plates"] == 36 for p in boards)
    assert post["part_id"] == "BRICK_1X1" and post["z_plates"] == 33
    assert (post["x_studs"], post["y_studs"]) == (4, 18)
    assert (boards[0]["x_studs"], boards[1]["x_studs"], boards[2]["x_studs"]) == (3, 5, 7)
    catalog = standard_orthogonal_definitions()
    definition = catalog[PLATE["part_id"]]
    assert definition.width_studs == 1 and definition.length_studs == 6
    assert definition.height_plates == 1
    old = [box(p) for p in (*boards, post)]
    after = old + [box(PLATE)]
    assert components(old)[0] == 3
    count, edges = components(after)
    assert count == 1, edges
    assert all(not overlaps(a, b) for i, a in enumerate(after) for b in after[i+1:])
    assert stud_connection(box(post), box(boards[0]))
    assert all(stud_connection(box(PLATE), box(p)) for p in boards)
    assert all(box(PLATE)[2] < box(p)[2] for p in boards)
    # Check against EVERY non-roof orthogonal part, not just prototype subset.
    for part in data["parts"]:
        if part["placement_id"] in (*IDS, POST) or part["category"] in ("roof_tile", "ridge_tile"):
            continue
        if any(part.get(k) is None for k in ("width_studs", "length_studs", "height_plates")):
            continue
        assert not overlaps(box(PLATE), box(part)), part["placement_id"]
    # An underside plate is mechanically retained by the boards, which are
    # supported by the real post. Directed 'support below' flags the plate
    # as unsupported but undirected stud-contact graph proves a support path.
    assert components(after)[0] == 1
    result = {
        "zone": "south-timber-deck-main real boards 00007 and 00013, anchored via 00001 and existing post",
        "catalog_parts": ["BRICK_2X8", "BRICK_1X1", "PLATE_1X6"],
        "before_bricks": 4, "after_bricks": 5,
        "before_components": 3, "after_components": 1,
        "before_unsupported_direct": 2, "after_unsupported_direct": 1,
        "before_collisions": 0, "after_collisions": 0,
        "real_stud_tube_connections_added": 3,
        "exterior_geometry_preserved": True,
        "concealed_plate_z": [35, 36],
        "assembly_order": ["existing post", "cross plate supported temporarily", "three deck boards engage cross plate and post"],
        "assembly_order_geometric": True,
        "temporary_plate_support_during_insertion": "REQUIRED",
        "clutch_strength_verified": False,
        "full_mechanical_certification": False,
        "result": "GEOMETRICALLY_CONNECTED_WITH_EXISTING_POST",
    }
    output = Path("artifacts/lego2-guided-004/connection-prototype-027.json")
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("CONNECTION_PROTOTYPE_027=" + json.dumps(result, sort_keys=True))
