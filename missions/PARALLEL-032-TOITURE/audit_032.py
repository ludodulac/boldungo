"""Mission 032 nominal-pair census, runnable offline: python3 audit_032.py.
Requires only Python 3 and the unmodified B3 .ldr; no third-party shadow files copied.
Reads the M031-verified F grid and conservative ordinary stud grids; does NOT
validate mesh collision, insertion, or mechanical load."""
from collections import Counter, defaultdict
from pathlib import Path
import json
D={"3005":(1,1),"3004":(1,2),"3622":(1,3),"3010":(1,4),
"3009":(1,6),"3008":(1,8),"3003":(2,2),"3002":(2,3),
"3001":(2,4),"2456":(2,6),"3007":(2,8),"3006":(2,10),
"3023b":(1,2),"3623":(1,3),"3710":(1,4),"3666":(1,6),"3460":(1,8)}
MODEL=Path(__file__).resolve().parents[1]/"B3/generated/GUIDED004-B3-1904.ldr"
def read():
    objects=[];iid=""
    for line in MODEL.read_text(encoding="utf8").splitlines():
        if line.startswith("0 // "):iid=line[5:].strip()
        if line.startswith("1 "):
            a=line.split()
            objects.append(dict(iid=iid,ref=a[14].lower().removesuffix(".dat"),
                origin=tuple(map(int,a[2:5])),rot=tuple(map(int,a[5:14]))))
    return objects
def point(o,p,vector=False):
    return tuple((0 if vector else o["origin"][i])+
        sum(o["rot"][3*i+j]*p[j] for j in range(3)) for i in range(3))
def audit():
    objects=read()
    assert len(objects)==1904
    male=defaultdict(list)
    for o in objects:
        part=o["ref"]
        if part=="30363":sites=[(-10,0,0),(10,0,0)]
        else:
            w,n=D[part]
            sites=[((2*x-n+1)*10,0,(2*z-w+1)*10)
                   for x in range(n) for z in range(w)]
        for p in sites:
            male[point(o,p)].append((o["iid"],part,point(o,(0,-1,0),True)))
    slopes=[o for o in objects if o["ref"]=="30363"]
    assert len(slopes)==408 and len({o["iid"] for o in slopes})==408
    total=roofroof=ordinary=0;with_brick=set();miss=[]
    for o in slopes:
        n=0;normal=point(o,(0,1,0),True)
        for z in (0,-20,-40,-60):
            for x in (-10,10):
                for iid,part,axis in male[point(o,(x,24,z))]:
                    if iid==o["iid"] or sum(axis[i]*normal[i] for i in range(3))>=-0.95:
                        continue
                    n+=1;total+=1
                    if part=="30363":roofroof+=1
                    else:ordinary+=1;with_brick.add(o["iid"])
        if n==0:miss.append(o["iid"])
    assert (total,roofroof,ordinary,len(with_brick),len(miss))==(832,720,112,60,4)
    assert miss==["roof-000001","roof-000023","roof-000208","roof-000230"]
    return dict(parts=len(objects),slopes=len(slopes),nominal_pairs=total,
        roof_roof=roofroof,roof_regular=ordinary,
        slopes_touching_regular=len(with_brick),no_nominal_match=miss,
        material_clearance="NOT_TESTED",stability="NOT_CERTIFIED")
if __name__=="__main__": print(json.dumps(audit(),indent=2))
