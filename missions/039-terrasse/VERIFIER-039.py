"""BOLDUNGO M039 — targeted reproducible, non-certifying geometry checks."""
from collections import Counter
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
D={"3005.dat":(1,1,3),"3004.dat":(1,2,3),"3622.dat":(1,3,3),"3010.dat":(1,4,3),"3009.dat":(1,6,3),"3008.dat":(1,8,3),"3003.dat":(2,2,3),"3002.dat":(2,3,3),"3001.dat":(2,4,3),"2456.dat":(2,6,3),"3007.dat":(2,8,3),"3006.dat":(2,10,3),"3460.dat":(1,8,1),"3623.dat":(1,3,1),"3023b.dat":(1,2,1),"3666.dat":(1,6,1),"3710.dat":(1,4,1),"3700.dat":(2,1,3)}
def read(path):
    parts=[];name=""
    for line in path.read_text(encoding="utf8").splitlines():
        if line.startswith("0 // "):name=line[5:].removeprefix("SOURCE-B3 ")
        if not line.startswith("1 "):continue
        t=line.split(); m=tuple(map(float,t[5:14]))
        p=dict(name=name,line=line,part=t[-1],x=float(t[2]),y=float(t[3]),z=float(t[4]),m=m)
        if p["part"] in D:
            w,l,h=D[p["part"]];width,length=(w,l) if m[0]==1 else (l,w)
            x,y,z=p["x"],p["y"],p["z"]
            p["box"]=(x-width*10,x+width*10,y,y+8*h,z-length*10,z+length*10)
        parts.append(p)
    return parts
def over(p,q):
    if "box" not in p or "box" not in q:return False
    a,b=p["box"],q["box"]
    return a[0]<b[1] and b[0]<a[1] and a[2]<b[3] and b[2]<a[3] and a[4]<b[5] and b[4]<a[5]
def studs(lower,upper):
    if "box" not in lower or "box" not in upper:return 0
    a,b=lower["box"],upper["box"]
    if a[2]!=b[3]:return 0
    common=lambda i,j:len(set(range(round(a[i]+10),round(a[j]),20))&set(range(round(b[i]+10),round(b[j]),20)))
    return common(0,1)*common(4,5)
def xyz(p,loc):
    m=p["m"]
    return tuple(p[k]+sum(m[3*i+j]*loc[j] for j in range(3)) for i,k in enumerate(("x","y","z")))
def run():
    source=read(ROOT/"missions/B3/generated/GUIDED004-B3-1904.ldr")
    model=read(HERE/"PROTO-039-TERRASSE-Y-TECHNIC.ldr")
    assert len(source)==1904 and len(model)==164
    assert "M035:Y:arm:left:3" in (ROOT/"missions/035-terrasse/PROTO-035-GUIDED004-Y.ldr").read_text(encoding="utf8")
    moved=lambda p:p["name"].startswith(("scene-platform:south-timber-","EXPERIMENT-B2-DECK"))
    dropped=lambda p:moved(p) and "support-solution:timber-post" in p["name"] and p["y"]<=-264
    refWood=[p for p in source if moved(p) and not dropped(p)]
    refConcrete=[p for p in source if p["name"].startswith("scene-platform:south-concrete-platform")]
    static=[p for p in source if not moved(p) and p["name"]!="EXPERIMENT-B3-CONCRETE-TO-TIMBER-BRIDGE"]
    extracted=[p for p in model if not p["name"].startswith("M039:")]
    added=[p for p in model if p["name"].startswith("M039:")]
    by={p["name"]:p for p in model}
    assert (len(refWood),len(refConcrete),len(extracted),len(added))==(102,46,148,16)
    assert len(by)==len(model)
    for p in refConcrete:assert by[p["name"]]["line"]==p["line"]
    for p in refWood:
        q=by[p["name"]]
        assert p["x"]==q["x"] and p["z"]==q["z"] and p["part"]==q["part"] and p["m"]==q["m"] and q["y"]==p["y"]+48
    topConcrete=min(p["y"] for p in refConcrete if ":deck:" in p["name"])
    topOrigWood=min(p["y"] for p in source if "south-timber-deck-main:board:" in p["name"])
    topNewWood=min(p["y"] for p in extracted if "south-timber-deck-main:board:" in p["name"])
    assert (topConcrete,topOrigWood,topNewWood)==(-288,-312,-264)
    audit=json.loads((HERE/"AUDIT-039.json").read_text(encoding="utf8"))
    collisions={(p["name"],q["name"]) for p in extracted if moved(p) for q in static if over(p,q)}
    assert len(collisions)==12 and collisions==set(tuple(q) for q in audit["collisions"]["pairs"])
    orth=[p for p in added if "box" in p]
    for i,p in enumerate(orth):
        for q in [*static,*extracted]:assert not over(p,q),(p["name"],q["name"])
        for q in orth[:i]:assert not over(p,q),(p["name"],q["name"])
    chains=[(p["name"],q["name"]) for i,p in enumerate(orth) for q in orth[:i] if studs(p,q) or studs(q,p)]
    assert len(chains)==8
    top=[(p["name"],q["name"]) for p in orth if p["name"] in ("M039:left:3700","M039:right:3700") for q in extracted if studs(p,q)]
    assert len(top)==7 and set(top)=={(q[0],q[1]) for q in audit["board_contacts_GEOMETRIC_AMBIGUOUS"]}
    for name,expected in (("M039:left:32524",((120,-230,550),(180,-150,550))),
                          ("M039:right:32524",((240,-230,590),(180,-150,590)))):
        p=by[name]
        for z,target in zip((-60,40),expected):
            assert all(abs(a-b)<1e-7 for a,b in zip(xyz(p,(0,0,z)),target))
        assert tuple(p["m"][i] for i in (1,4,7))==(0.,0.,1.)
    for name in ("M039:left:6558","M039:right:6558","M039:fork:6558"):
        assert tuple(by[name]["m"][i] for i in (0,3,6))==(0.,0.,1.)
    official=(ROOT/"backend/brickhouse/bricks/technic_official_axes_098.py").read_text(encoding="utf8")
    assert "PIN_PART_LOCAL_AXIS=(1.,0.,0.)" in official
    assert "BEAM_PART_LOCAL_AXIS=(0.,1.,0.)" in official
    bom=json.loads((HERE/"BOM-039.json").read_text(encoding="utf8"))
    assert Counter(p["part"] for p in model)==Counter(bom["all"])
    print("M039 targeted PASS: source 1904; variant 164; 8 solid-stud joints; 2 inclined beams; 3 coaxial pin sites; 7 ambiguous plank overlaps")
    print("M039 STOP: 12 cross-collisions of corrected timber vs unchanged B3; no stable build claim")
if __name__=="__main__":run()
