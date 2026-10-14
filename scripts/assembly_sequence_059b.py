"""Progressive 059B assembly evidence using existing box/overlap and connector tools.
No fabricated insertion success: unknown geometry and unresolved future dependencies
remain explicitly UNKNOWN. Does not alter GUIDED-004.
"""
import json
import sys
from pathlib import Path
from audit_terrace_048 import box,overlap
from experiment_terrace_057 import select_scope
from prototype_terrace_059b import T1,T2
from brickhouse.bricks.brick_model import BrickModelPart
from brickhouse.bricks.connectors import validate_connection

P="scene-platform:south-timber-deck-main:"
BOARDS=("board:00007","board:00013","board:00019","board:00031")
PLATES=("hidden-cross-bond-029:03","hidden-cross-bond-029:04","hidden-cross-bond-029:08")

def sweep(p):
    b=box(p)
    if b is None:return None
    return (b[0],b[1],b[2],b[3],b[4],b[5]+30)

def check(p,installed):
    swept=sweep(p)
    if swept is None:return {"verdict":"UNKNOWN","blockers":[],"unknown":[]}
    blockers=[q["placement_id"] for q in installed
              if box(q) is not None and overlap(swept,box(q))]
    # Do not interpret all unmodeled roof parts as local obstacles.
    # Unknown geometry is not automatically an intersection either.
    unknown=[q["placement_id"] for q in installed if box(q) is None
             and abs(q.get("x_studs",999)-p["x_studs"])<=10
             and abs(q.get("y_studs",999)-p["y_studs"])<=12
             and abs(q.get("z_plates",999)-p["z_plates"])<=35]
    return {"verdict":"BLOCKED" if blockers else "UNKNOWN" if unknown else "GEOMETRY_PASS",
            "blockers":blockers,"unknown":unknown,
            "sweep":"vertical -Z, rectangular conservative envelope +30 plates"}

def sequence(model,variant):
    full=model["parts"]
    if len(full)!=1890:raise ValueError("not authentic GUIDED-004")
    selected=select_scope(model)
    if len(selected)!=105:raise ValueError("unexpected terrace scope")
    by={p["placement_id"]:p for p in full}
    traverses=[T1] if variant=="B" else [T1,T2]
    boards=[by[P+n] for n in BOARDS]
    plates=[by[P+n] for n in PLATES]
    # Explicitly distinguish present supports from deferred deck/rails/finishes.
    supports=[p for p in selected if "support-solution:timber-post" in p["placement_id"]]
    module=[*plates,*traverses,*boards]
    module_ids={p["placement_id"] for p in module}
    # Fixed supports only at the initial stage; deferred objects must later
    # be evaluated rather than silently treated as absent.
    installed=list(supports)
    steps=[]
    for index,p in enumerate(module,1):
        if p in traverses or p in boards:
            # Subassembly hand-held: check against previously installed
            # subassembly parts, not distant supports until installation.
            fixed=[q for q in installed if q not in supports]
        else:
            fixed=installed
        result=check(p,fixed)
        links=[]
        for q in fixed:
            r=validate_connection(BrickModelPart.model_validate(p),
                                  BrickModelPart.model_validate(q))
            if r.status=="VALID":
                links.append({"other":q["placement_id"],"studs":r.interface_count})
        steps.append({"number":index,"piece":p["placement_id"],
                      "position":[p["x_studs"],p["y_studs"],p["z_plates"]],
                      "direction":"vertical -Z","installed":[q["placement_id"] for q in fixed],
                      "connections":links,"collision":result,"verdict":result["verdict"],
                      "handheld_subassembly":p in traverses or p in boards})
        installed.append(p)
    # Check later-stage guardrails and finishes; no blanket clearance claim.
    deferred=[p for p in selected if p["placement_id"] not in module_ids
              and p["placement_id"] not in {q["placement_id"] for q in supports}]
    late=[]
    for p in deferred:
        result=check(p,installed)
        late.append({"piece":p["placement_id"],"verdict":result["verdict"],
                     "blockers":result["blockers"],"unknown":result["unknown"]})
        installed.append(p)
    first=next((x for x in steps if x["verdict"]!="GEOMETRY_PASS"),None)
    return {"variant":variant,"steps":steps,"later_elements":late,
            "first_unverified_step":first,
            "all_steps_proven":all(x["verdict"]=="GEOMETRY_PASS" for x in steps)
                 and all(x["verdict"]=="GEOMETRY_PASS" for x in late),
            "mechanical_strength":"NOT_CERTIFIED",
            "notes":["Vertical sweep is a conservative geometric test, not a real grasp/motion planner.",
                     "Subassembly placement on supports is NOT proven by these individual sweeps.",
                     "Nonrectangular local geometries remain UNKNOWN."]}

def main(path):
    src=Path(path);raw=src.read_bytes();model=json.loads(raw)
    out=Path("artifacts/lego2-059b");out.mkdir(parents=True,exist_ok=True)
    for variant in ("B","C"):
        report=sequence(model,variant)
        (out/f"sequence-{variant}.json").write_text(json.dumps(report,indent=2))
        print(json.dumps({"variant":variant,"first_unverified":report["first_unverified_step"],
                          "all_steps_proven":report["all_steps_proven"]},indent=2))
    assert src.read_bytes()==raw
if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("Usage: assembly_sequence_059b.py brick-model.json")
    main(sys.argv[1])
