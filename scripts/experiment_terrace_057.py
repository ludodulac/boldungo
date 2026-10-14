"""Reproduce LEGO2-057 A/B/C from an unmodified GUIDED-004 brick-model.json.

Run: python scripts/experiment_terrace_057.py /path/to/brick-model.json
No official model writes; no mechanical-strength inference.
"""
import json
import sys
from pathlib import Path

from audit_terrace_048 import connector_graph_diagnostic, box, overlap
from brickhouse.bricks.brick_model import BrickModelPart

PREFIX = "scene-platform:south-timber-deck-"
EXPECTED = {
    "A": {"pieces":105,"valid":65,"components":47,"support_reachable":48},
    "B": {"pieces":106,"valid":69,"components":44,"support_reachable":48},
    "C": {"pieces":107,"valid":73,"components":42,"support_reachable":48},
}
ADDITIONS = (
    {"placement_id":"EXPERIMENT:P1","part_id":"PLATE_1X6",
     "category":"plate","component":"roof_support",
     "x_studs":4,"y_studs":27,"z_plates":35,"rotation_quarter_turns":1,
     "width_studs":1,"length_studs":6,"height_plates":1},
    {"placement_id":"EXPERIMENT:P2","part_id":"PLATE_1X6",
     "category":"plate","component":"roof_support",
     "x_studs":8,"y_studs":30,"z_plates":35,"rotation_quarter_turns":1,
     "width_studs":1,"length_studs":6,"height_plates":1},
)

def select_scope(model):
    return [p for p in model["parts"] if
            (p["placement_id"].startswith(PREFIX+"main:") and p["z_plates"]>=33)
            or p["placement_id"].startswith(PREFIX+"west-return:")
            or (p["placement_id"].startswith(PREFIX)
                and "support-solution:timber-post" in p["placement_id"])]

def legacy_057_diagnostic(placements):
    """Freeze the 057 evidence baseline, independently of later reviewed families.

    The historical validator returned UNKNOWN for BRICK_2X3/BRICK_2X6
    underside interfaces. This wrapper preserves that historical comparison;
    the production validator itself is never modified.
    """
    import brickhouse.bricks.connectors as connectors
    from brickhouse.bricks.connectors import ConnectionResult
    old = connectors.validate_connection

    def baseline(a, b):
        r = old(a, b)
        if r.status == "VALID":
            from brickhouse.bricks.connectors import _box
            A, B = _box(a), _box(b)
            if A is not None and B is not None:
                upper = b if A[5] == B[2] else a
                if upper.part_id in {"BRICK_2X3", "BRICK_2X6"}:
                    return ConnectionResult("UNKNOWN", r.interface_count,
                                            "057-baseline-underside-not-documented")
        return r

    connectors.validate_connection = baseline
    try:
        return connector_graph_diagnostic(placements)
    finally:
        connectors.validate_connection = old


def experiment(model):
    selected=select_scope(model)
    if len(selected)!=105:
        raise ValueError(f"Expected 105 real placements; got {len(selected)}")
    original_ids={p["placement_id"] for p in selected}
    if len(original_ids)!=105:raise ValueError("duplicate placement IDs")
    result={}
    for name,extra in (("A",()),("B",ADDITIONS[:1]),("C",ADDITIONS)):
        placements=[*selected,*extra]
        diagnostic=legacy_057_diagnostic(placements)
        collisions=[(a["placement_id"],b["placement_id"])
            for i,a in enumerate(placements) for b in placements[i+1:]
            if overlap(box(a),box(b))]
        reachable=diagnostic["pieces"]-len(diagnostic["without_path_to_identified_support"])
        result[name]={
            "pieces":len(placements),
            "valid":len(diagnostic["valid_edges"]),
            "valid_contacts":sum(e["contacts"] for e in diagnostic["valid_edges"]),
            "unknown":len(diagnostic["unknown_edges"]),
            "components":len(diagnostic["components"]),
            "isolated":len(diagnostic["isolated"]),
            "articulations":len(diagnostic["articulations"]),
            "bridges":len(diagnostic["bridges"]),
            "support_reachable":reachable,
            "collisions":len(collisions),
            "new_valid_edges":[e for e in diagnostic["valid_edges"]
                if e["a"].startswith("EXPERIMENT:") or e["b"].startswith("EXPERIMENT:")],
        }
    return result

def main(path):
    source=Path(path)
    before=source.read_bytes()
    result=experiment(json.loads(before))
    if source.read_bytes()!=before:raise AssertionError("official model changed")
    print(json.dumps({"variants":result,"expected_reference":EXPECTED,
                      "matches_reference":{k:all(result[k][m]==v
                        for m,v in EXPECTED[k].items()) for k in EXPECTED}},
                     indent=2))
    return 0 if all(all(result[k][m]==v for m,v in EXPECTED[k].items())
                    for k in EXPECTED) else 1

if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("Usage: experiment_terrace_057.py brick-model.json")
    raise SystemExit(main(sys.argv[1]))
