"""M035: offline structural-boundary gate. No shared engine modification."""
from __future__ import annotations
import json
from pathlib import Path
from collections import Counter

ROOT=Path(__file__).resolve().parents[2]
DIR=Path(__file__).resolve().parent
SOURCE=ROOT/"missions/B3/generated/GUIDED004-B3-1904.ldr"
PROTOTYPE=DIR/"PROTO-035-GUIDED004-Y.ldr"
DIM={
"3005.dat":(1,1,3),"3004.dat":(1,2,3),"3622.dat":(1,3,3),
"3010.dat":(1,4,3),"3009.dat":(1,6,3),"3008.dat":(1,8,3),
"3003.dat":(2,2,3),"3002.dat":(2,3,3),"3001.dat":(2,4,3),
"2456.dat":(2,6,3),"3007.dat":(2,8,3),"3006.dat":(2,10,3),
"3460.dat":(1,8,1),"3623.dat":(1,3,1),"3023b.dat":(1,2,1),
"3666.dat":(1,6,1),"3710.dat":(1,4,1),
}
IDENT=(1,0,0,0,1,0,0,0,1)
TURN=(0,0,-1,0,1,0,1,0,0)
BACK_TURN=(0,0,1,0,1,0,-1,0,0)
def read(path):
    parts=[]; identifier=None
    for ln in path.read_text(encoding="utf8").splitlines():
        if ln.startswith("0 // "):
            identifier=ln[5:].removeprefix("SOURCE-GUIDED004 ")
        elif ln.startswith("1 "):
            s=ln.split()
            matrix=tuple(map(int,s[5:14]))
            assert matrix in (IDENT,TURN,BACK_TURN), (identifier,"NON_ORTHOGONAL_PART")
            item={"id":identifier,"line":ln,"part":s[-1],"x":int(s[2]),"y":int(s[3]),"z":int(s[4]),"matrix":matrix}
            if item["part"] in DIM:
                w,l,h=DIM[item["part"]];wx,wz=(l,w) if matrix==IDENT else (w,l)
                x,y,z=item["x"],item["y"],item["z"]
                item["box"]=(x-10*wx,x+10*wx,y,y+8*h,z-10*wz,z+10*wz)
            parts.append(item)
    return parts
def overlap(a,b):
    A,B=a["box"],b["box"]
    return A[0]<B[1] and B[0]<A[1] and A[2]<B[3] and B[2]<A[3] and A[4]<B[5] and B[4]<A[5]
def stud_contact(a,b):
    A,B=a["box"],b["box"]
    if A[2]!=B[3]: return 0
    dx=min(A[1],B[1])-max(A[0],B[0]);dz=min(A[5],B[5])-max(A[4],B[4])
    return max(0,dx//20)*max(0,dz//20)
def run():
    source=read(SOURCE);proto=read(PROTOTYPE)
    originals=[p for p in source if p["id"].startswith("scene-platform:") or p["id"].startswith(("EXPERIMENT-B2-DECK","EXPERIMENT-B3-CONCRETE"))]
    existing=[p for p in proto if not p["id"].startswith("M035:")]
    new=[p for p in proto if p["id"].startswith("M035:")]
    assert len(source)==1904 and len(originals)==155 and len(new)==16
    assert [(p["id"],p["line"]) for p in originals]==[(p["id"],p["line"]) for p in existing], "SOURCE TERRACE ALTERED"
    assert len({p["id"] for p in proto})==len(proto)
    assert all(p.get("box") for p in new)
    for i,p in enumerate(new):
        for q in source:
            if "box" in q: assert not overlap(p,q),(p["id"],q["id"])
        for q in new[:i]: assert not overlap(p,q),(p["id"],q["id"])
    edges=[]
    for i,p in enumerate(new):
        for j,q in enumerate(new[:i]):
            n=stud_contact(p,q)+stud_contact(q,p)
            if n: edges.append((i,j))
    assert len(edges)==15
    parent=list(range(len(new)))
    def find(i):
        while parent[i]!=i:
            parent[i]=parent[parent[i]];i=parent[i]
        return i
    for i,j in edges: parent[find(i)]=find(j)
    assert len({find(i) for i in range(len(new))})==1,"Y NOT NOMINALLY CONNECTED"
    host=[]
    for p in new:
        for q in originals:
            if p.get("box") and q.get("box") and (stud_contact(p,q) or stud_contact(q,p)):
                host.append(q["id"])
    assert set(host)=={
      "scene-platform:south-timber-deck-main:board:00014",
      "scene-platform:south-timber-deck-main:board:00026"
    },host
    bom=json.loads((DIR/"BOM-035.json").read_text(encoding="utf8"))
    assert Counter(p["part"] for p in proto)==Counter(bom["prototype_references"])
    print("M035 PASS: 1904 originals, 155 extracted, 16 Y parts, 0 new nominal AABB collisions, 15 Y joints, 2 board interfaces")
    print("NO mechanical stability, diagonal fidelity, insertion, or terrain certification.")
if __name__=="__main__":run()
