"""059B fixed-candidate A/B/C study; experimental only, no official writes."""
import json
import sys
from pathlib import Path
from audit_terrace_048 import box, overlap, connector_graph_diagnostic
from experiment_terrace_057 import select_scope
from prototype_terrace_059 import score
from brickhouse.bricks.brick_model import BrickModelPart
from brickhouse.bricks.connectors import validate_connection

def traverse(name, y):
    return dict(placement_id="EXPERIMENT:059B:"+name,part_id="BRICK_1X8",
                category="brick",component="roof_support",
                x_studs=6,y_studs=y,z_plates=33,rotation_quarter_turns=1,
                width_studs=1,length_studs=8,height_plates=3)

T1=traverse("T1",19)
T2=traverse("T2",22)

def examine(model):
    full=model["parts"]
    if len(full)!=1890: raise AssertionError("Expected 1890 real parts")
    scope=select_scope(model)
    if len(scope)!=105: raise AssertionError("Expected 105 scoped parts")
    cases={"A":scope,"B":[*scope,T1],"C":[*scope,T1,T2]}
    all_boxes=[(p["placement_id"],box(p)) for p in full]
    all_boxes=[(pid,b) for pid,b in all_boxes if b is not None]
    unmodeled=[p for p in full if box(p) is None]
    results={}
    base_existing=None
    for name,placements in cases.items():
        d=connector_graph_diagnostic(placements)
        metrics=score(placements,d)
        if name=="A":base_existing=metrics["nonpost_reaching_support"]
        new=[p for p in placements if p["placement_id"].startswith("EXPERIMENT:059B:")]
        connections={}
        for p in new:
            obj=BrickModelPart.model_validate(p)
            connections[p["placement_id"]]=[
                {"other":q["placement_id"],"contacts":r.interface_count,"status":r.status}
                for q in scope
                if (r:=validate_connection(obj,BrickModelPart.model_validate(q))).status=="VALID"
            ]
        collisions=[]
        for p in new:
            b=box(p)
            collisions += [{"new":p["placement_id"],"existing":pid}
                           for pid,other in all_boxes if overlap(b,other)]
        if len(new)==2 and overlap(box(new[0]),box(new[1])):
            collisions.append({"new":new[0]["placement_id"],"existing":new[1]["placement_id"]})
        results[name]={
            "placements":new,"metrics":metrics,
            "existing_nonpost_reaching_support_gain":
                metrics["nonpost_reaching_support"]-base_existing-len(new),
            "validated_connections":connections,
            "known_box_collisions":collisions,
            "unmodeled_geometry_count":len(unmodeled),
            "unmodeled_geometry_nearby":[p["placement_id"] for p in unmodeled
                if abs(p["x_studs"]-6)<=9 and 17<=p["y_studs"]<=32 and
                   25<=p["z_plates"]<=42],
            "insertion":{"predeck":"NOT_PROVEN","retrofit":"NOT_PROVEN",
                         "vertical_downward_possible_in_final_assembled_state":False},
            "decision":"NON_DEMONTREE"
        }
    return results

def main(path):
    source=Path(path)
    raw=source.read_bytes()
    results=examine(json.loads(raw))
    out=Path("artifacts/lego2-059b")
    out.mkdir(parents=True,exist_ok=True)
    for name,data in results.items():
        (out/f"variant-{name}.json").write_text(json.dumps(data,indent=2))
    (out/"comparison.json").write_text(json.dumps(results,indent=2))
    if source.read_bytes()!=raw:raise AssertionError("GUIDED-004 changed")
    print(json.dumps({"comparison":results,"official_unchanged":True},indent=2))
    return 0

if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("Usage: prototype_terrace_059b.py brick-model.json")
    raise SystemExit(main(sys.argv[1]))
