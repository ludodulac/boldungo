"""Reproducible GUIDED-004 expanded terrace audit; prints blockers, writes LDraw."""
import json, re, sys
from pathlib import Path
def box(p):
    m=re.fullmatch(r"(BRICK|PLATE)_(\d+)X(\d+)",p["part_id"])
    if not m:return None
    w,l=int(m[2]),int(m[3])
    if p["rotation_quarter_turns"]%2:w,l=l,w
    x,y,z=p["x_studs"],p["y_studs"],p["z_plates"]
    return x,y,z,x+w,y+l,z+(1 if m[1]=="PLATE" else 3)
def overlap(a,b):
    return all(a[i]<b[i+3] and b[i]<a[i+3] for i in range(3))
def stud(a,b):
    A,B=box(a),box(b)
    return max(0,min(A[3],B[3])-max(A[0],B[0]))*max(0,min(A[4],B[4])-max(A[1],B[1])) if A[5]==B[2] else 0
def audit(model, old_notice, output):
    parts=json.loads(Path(model).read_text())["parts"]
    prefix="scene-platform:south-timber-deck-main:"
    chosen=[p for p in parts if p["placement_id"].startswith(prefix) and p["z_plates"]>=33]
    assert len(chosen)==56
    by={p["placement_id"]:p for p in parts}
    old=[line for line in Path(old_notice).read_text().splitlines() if line.startswith("1 ")]
    assert len(old)==11
    codes={"BRICK_1X1":"3005.dat","BRICK_1X2":"3004.dat","BRICK_1X3":"3622.dat","BRICK_1X8":"3008.dat","BRICK_2X3":"3002.dat","BRICK_2X8":"3007.dat","PLATE_1X3":"3623.dat","PLATE_1X6":"3666.dat","PLATE_1X8":"3460.dat"}
    def line(p):
        x,y,z,X,Y,Z=box(p)
        rotations=((1,0,0,0,1,0,0,0,1),(0,0,-1,0,1,0,1,0,0),(-1,0,0,0,1,0,0,0,-1),(0,0,1,0,1,0,-1,0,0))
        return f"1 7 {(x+X)*10:g} {-Z*8:g} {(y+Y)*10:g} "+ " ".join(map(str,rotations[p["rotation_quarter_turns"]%4]))+" "+codes[p["part_id"]]
    original_ids=[prefix+"support-solution:timber-post-east:0033:00022",prefix+"hidden-cross-plate:00007-00013"]+[prefix+f"board:{n:05}" for n in (1,7,13)]+[prefix+f"x_min:rail-post:{n:05}" for n in (35,39,43)]+[prefix+"y_min:rail-post:00089",prefix+"x_min:rail-top-solution:00004",prefix+"y_min:rail-top-solution:00009"]
    mismatches=[pid for pid,oldline in zip(original_ids,old) if line(by[pid])!=oldline]
    assert not mismatches,mismatches
    assert not any(overlap(box(a),box(b)) for i,a in enumerate(chosen) for b in chosen[i+1:])
    selected={p["placement_id"] for p in chosen}
    external=[p for p in parts if p["placement_id"] not in selected and box(p)]
    assert not any(overlap(box(a),box(b)) for a in chosen for b in external)
    links=[(a["placement_id"],b["placement_id"]) for a in chosen for b in chosen if a is not b and stud(a,b)]
    neighbors={pid:set() for pid in selected}
    for a,b in links:neighbors[a].add(b);neighbors[b].add(a)
    components=[]
    remaining=set(selected)
    while remaining:
        start=remaining.pop();seen={start};todo=[start]
        while todo:
            for nxt in neighbors[todo.pop()] & remaining:
                remaining.remove(nxt);seen.add(nxt);todo.append(nxt)
        components.append(sorted(seen))
    ordered=sorted(chosen,key=lambda p:(0 if p["z_plates"]==33 else 1 if p["z_plates"]==35 else 2 if p["z_plates"]==36 else 3 if p["z_plates"]==39 else 4,p["placement_id"]))
    lines=["0 GUIDED004 terrace 048 - geometry only; NOT PHYSICALLY CERTIFIED"]
    for p in ordered:lines.extend(["0 STEP","0 !NOTE "+p["placement_id"],line(p)])
    Path(output).write_text("\n".join(lines)+"\n")
    blockers=[]
    for p in chosen:
        if p["z_plates"] not in (35,36):continue
        a=box(p);swept=(a[0],a[1],a[2],a[3],a[4],200)
        for q in external:
            if overlap(swept,box(q)):blockers.append([p["placement_id"],q["placement_id"]])
    return {"pieces":len(chosen),"steps":len(ordered),"geometric_links":len(links),"component_sizes":sorted(map(len,components),reverse=True),"isolated": [c[0] for c in components if len(c)==1],"module_drop_blockers":blockers,"ldraw_047_verified_lines":len(old),"visual_validation":"NOT_DONE","physical_certification":"NOT_CERTIFIED"}
if __name__=="__main__":
    print(json.dumps(audit(sys.argv[1],sys.argv[2],sys.argv[3]),indent=2))
