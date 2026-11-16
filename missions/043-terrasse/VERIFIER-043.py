"""Targeted M043 geometry gate. Uses existing M039 read/over/studs/xyz, without editing shared engine."""
from __future__ import annotations
from collections import Counter
from pathlib import Path
import json, runpy

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
M039=runpy.run_path(str(ROOT/"missions/039-terrasse/VERIFIER-039.py"))
read,over,studs,xyz=(M039[k] for k in ("read","over","studs","xyz"))
MOVED=lambda p:p["name"].startswith(("scene-platform:south-timber-","EXPERIMENT-B2-DECK"))
def clash_pairs(parts):
    boxes=[p for p in parts if "box" in p]
    return {
        tuple(sorted((p["name"],q["name"])))
        for i,p in enumerate(boxes) for q in boxes[:i] if over(p,q)
    }
def nominal_Y(prototype):
    y=[p for p in prototype if p["name"].startswith("M039:")]
    assert len(y)==16
    by={p["name"]:p for p in prototype}
    chain=[(p["name"],q["name"]) for i,p in enumerate(y) if "box" in p
           for q in y[:i] if "box" in q and (studs(p,q) or studs(q,p))]
    assert len(chain)==8
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
    return chain
def run():
    source=read(ROOT/"missions/B3/generated/GUIDED004-B3-1904.ldr")
    old=read(ROOT/"missions/039-terrasse/PROTO-039-TERRASSE-Y-TECHNIC.ldr")
    new=read(HERE/"PROTO-043-TERRASSE-Y-RECALE.ldr")
    full=read(HERE/"GUIDED004-B3-EXPERIMENTAL-M043.ldr")
    assert (len(source),len(old),len(new),len(full))==(1904,164,163,1912)
    assert len({p["name"] for p in full})==len(full)
    assert len({p["name"] for p in new})==len(new)
    # Original B3 elements that M039 displaced are never silently merged back.
    static=[p for p in source if not MOVED(p) and p["name"]!="EXPERIMENT-B3-CONCRETE-TO-TIMBER-BRIDGE"]
    assert len(static)==1795
    shifted=[p for p in new if MOVED(p)]
    y=[p for p in new if p["name"].startswith("M039:")]
    assert len(shifted)==101 and len(y)==16
    concrete=[p for p in new if p["name"].startswith("scene-platform:south-concrete-platform")]
    assert len(concrete)==46
    expected=[*static,*shifted,*y]
    assert [(p["name"],p["line"]) for p in full]==[(p["name"],p["line"]) for p in expected]
    previous={p["name"]:p for p in old}
    current={p["name"]:p for p in new}
    for p in concrete:
        assert p["line"]==next(q["line"] for q in source if q["name"]==p["name"])
    assert all(previous[p["name"]]["line"]==p["line"] for p in y)
    assert len(nominal_Y(new))==8
    baseline=json.loads((ROOT/"missions/039-terrasse/AUDIT-039.json").read_text(encoding="utf8"))
    logged={tuple(q) for q in baseline["collisions"]["pairs"]}
    before={(p["name"],q["name"]) for p in old if MOVED(p) for q in static if over(p,q)}
    after={(p["name"],q["name"]) for p in shifted for q in static if over(p,q)}
    assert before==logged and len(before)==12
    assert not after,"M043 STILL CLASHES WITH RETAINED HOUSE: "+repr(sorted(after)[:12])
    assert all((p["name"],q["name"]) not in after for p,q in [])
    # No hiding collisions: compare full 3D rectangular AABBs, including those inherited.
    b3_pairs=clash_pairs(source)
    p039_full=[*static,*[p for p in old if MOVED(p) or p["name"].startswith("M039:")]]
    old_pairs=clash_pairs(p039_full)
    new_pairs=clash_pairs(full)
    assert len(b3_pairs)==230 and len(old_pairs)==223 and len(new_pairs)==205
    assert not new_pairs-old_pairs, "NEW AABB CONFLICT IN FULL M043"
    assert not new_pairs-b3_pairs, "M043 INTRODUCED AABB CONFLICT VS B3"
    assert len(old_pairs-new_pairs)==18
    assert len(clash_pairs(old))==78 and len(clash_pairs(new))==70
    assert not clash_pairs(new)-clash_pairs(old)
    old_top=min(p["y"] for p in source if "south-timber-deck-main:board:" in p["name"])
    new_top=min(p["y"] for p in new if "south-timber-deck-main:board:" in p["name"])
    concrete_top=min(p["y"] for p in new if "south-concrete-platform:deck:" in p["name"])
    assert (old_top,concrete_top,new_top)==(-312,-288,-264)
    # Recalepinage garde le retour bois; les 4 lames superposees sont remplacees par 3 bandes jointives.
    west=[p for p in shifted if "south-timber-deck-west-return:board:" in p["name"]]
    assert len(west)==3 and all(p["part"]=="3007.dat" and p["x"]==170 for p in west)
    assert sorted(p["z"] for p in west)==[740,780,820]
    assert "scene-platform:south-timber-deck-west-return:board:00007" not in current
    assert all(not over(p,q) for p in west for q in static)
    audit=json.loads((HERE/"AUDIT-043.json").read_text(encoding="utf8"))
    metrics=audit["after_M043"]
    assert metrics["full_house_M043_AABB_count"]==len(new_pairs)
    assert metrics["reported_initial_12_remaining"]==len(after)==0
    bom=json.loads((HERE/"BOM-043.json").read_text(encoding="utf8"))
    assert Counter(p["part"] for p in full)==Counter(bom["full_house_total"])
    assert Counter(p["part"] for p in new)==Counter(bom["isolated_total"])
    print("M043 PASS: 12/12 M039 clashes resolved, 0 new orthogonal AABB, 16 Y parts with 3 nominal Technic axes")
    print("M043 STOP: 205 inherited full-house AABB pairs remain; beams/pins meshes, insertion, grip, stability unverified")
if __name__=="__main__":run()
