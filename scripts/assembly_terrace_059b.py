"""Experimental 059B assembly evidence. No official model writes.

Uses existing rectangular collision and connector functions; non-catalog geometry
is UNKNOWN. A verified sweep is geometric only, not a mechanical certification.
"""
import json
import sys
from pathlib import Path
from audit_terrace_048 import box, overlap
from experiment_terrace_057 import select_scope
from prototype_terrace_059b import T1,T2
from brickhouse.bricks.brick_model import BrickModelPart
from brickhouse.bricks.connectors import validate_connection

BOARD_IDS=("board:00007","board:00013","board:00019","board:00031")
WATCH=("hidden-cross-bond-029:03","hidden-cross-bond-029:04","hidden-cross-bond-029:08")
PREFIX="scene-platform:south-timber-deck-main:"

def swept_up(p, z_high=100):
    b=box(p)
    return (b[0],b[1],b[2],b[3],b[4],z_high)

def check_sweep(moving, fixed):
    volume=swept_up(moving)
    blockers=[]
    unknown=[]
    for p in fixed:
        b=box(p)
        if b is None:
            unknown.append(p["placement_id"])
        elif overlap(volume,b):
            blockers.append(p["placement_id"])
    return {"direction":"vertical -Z (from above)",
            "rectangular_blockers":blockers,
            "unmodeled_collision_status":"UNKNOWN" if unknown else "NONE",
            "unmodeled_ids":unknown}

def examine(model):
    full=model["parts"]
    assert len(full)==1890
    scope=select_scope(model)
    assert len(scope)==105
    by={p["placement_id"]:p for p in full}
    boards=[by[PREFIX+name] for name in BOARD_IDS]
    traverses=[T1,T2]
    contacts={}
    for t in traverses:
        c=BrickModelPart.model_validate(t)
        links=[]
        for b in boards:
            r=validate_connection(c,BrickModelPart.model_validate(b))
            if r.status=="VALID":
                links.append({"board":b["placement_id"],"stud_contacts":r.interface_count})
        contacts[t["placement_id"]]=links
        assert [x["stud_contacts"] for x in links]==[1,2,2,1]
    # Assembly jig: traverses positioned but not independently self-supporting.
    # The four deck boards are lowered one by one; the jig is hand-held.
    # All other official pieces are conservatively considered pre-existing.
    excluded={p["placement_id"] for p in boards}
    fixed=[p for p in full if p["placement_id"] not in excluded]
    operations=[]
    for board in boards:
        sweep=check_sweep(board,[*fixed,*traverses])
        operations.append({"piece":board["placement_id"],
                           "final_xyz":[board["x_studs"],board["y_studs"],board["z_plates"]],
                           "movement":"vertical -Z",
                           "sweep":sweep,
                           "note":"hand-held jig; lower board onto T1/T2 before fixing to posts"})
        fixed.append(board)
    # Each hidden plate is explicitly checked, never presumed insertable later.
    plates=[]
    for short in WATCH:
        pid=PREFIX+short
        if pid not in by:
            plates.append({"piece":pid,"status":"NOT_FOUND"})
            continue
        target=by[pid]
        others=[p for p in full if p["placement_id"]!=pid]
        plates.append({"piece":pid,"final_xyz":[target["x_studs"],target["y_studs"],target["z_plates"]],
                       "sweep_after_full_deck":check_sweep(target,[*others,*traverses])})
    # Rigid-body lowering of the finished module: check the union of all
    # component swept boxes against official pieces not included in module.
    module=[*boards,*traverses]
    module_ids={p["placement_id"] for p in boards}
    external=[p for p in full if p["placement_id"] not in module_ids]
    module_sweeps=[{"piece":p["placement_id"],"sweep":check_sweep(p,external)}
                   for p in module]
    return {"source_count":len(full),"contacts":contacts,
            "predeck_handheld_subassembly_operations":operations,
            "existing_hidden_plate_insertion_checks":plates,
            "assembled_module_vertical_insertion":module_sweeps,
            "geometric_assembly_demonstrated":False,
            "decision_B":"NON_DEMONTRE",
            "decision_C":"NON_DEMONTRE",
            "single_stud_post_connections_remain":3,
            "mechanical_strength":"NOT_CERTIFIED"}

def main(source):
    path=Path(source)
    before=path.read_bytes()
    result=examine(json.loads(before))
    dest=Path("artifacts/lego2-059b")
    dest.mkdir(parents=True,exist_ok=True)
    (dest/"assembly-evidence.json").write_text(json.dumps(result,indent=2))
    # Small existing LDraw-compatible experimental step listing.
    # This is a geometric assembly proposal, not a collision-cleared notice.
    codes={"BRICK_1X8":"3008.dat","BRICK_2X8":"3007.dat","BRICK_1X8":"3008.dat"}
    lines=["0 LEGO2-059B experimental handheld subassembly - NOT VERIFIED","0 Name: terrace-059b-subassembly.ldr"]
    model=json.loads(before)
    by={p["placement_id"]:p for p in model["parts"]}
    for p in (T1,T2,*[by[PREFIX+n] for n in BOARD_IDS]):
        b=box(p)
        # LDraw part origin at bounding-box center; quarter-turn transform.
        rot=p["rotation_quarter_turns"]%4
        mat=((1,0,0,0,1,0,0,0,1),(0,0,-1,0,1,0,1,0,0),
             (-1,0,0,0,1,0,0,0,-1),(0,0,1,0,1,0,-1,0,0))[rot]
        lines.extend(["0 STEP","0 !NOTE "+p["placement_id"],
                      f"1 7 {(b[0]+b[3])*10:g} {-b[5]*8:g} {(b[1]+b[4])*10:g} "+
                      " ".join(map(str,mat))+" "+codes[p["part_id"]]])
    (dest/"terrace-059b-subassembly.ldr").write_text("\n".join(lines)+"\n")
    assert path.read_bytes()==before
    print(json.dumps(result,indent=2))
    return 0

if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("Usage: assembly_terrace_059b.py brick-model.json")
    raise SystemExit(main(sys.argv[1]))
