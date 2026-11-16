"""M045 targeted proof: clean LDraw subset; all unsolved pieces explicitly classified."""
from pathlib import Path
from collections import Counter
import json, runpy

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
m39=runpy.run_path(str(ROOT/"missions/039-terrasse/VERIFIER-039.py"))
read,over,studs=(m39[x] for x in ("read","over","studs"))
def collisions(pieces):
    return {tuple(sorted((a["name"],b["name"]))) for i,a in enumerate(pieces) for b in pieces[:i] if over(a,b)}
def run():
    source=read(ROOT/"missions/B3/generated/GUIDED004-B3-1904.ldr")
    old=read(ROOT/"missions/043-terrasse/PROTO-043-TERRASSE-Y-RECALE.ldr")
    oldfull=read(ROOT/"missions/043-terrasse/GUIDED004-B3-EXPERIMENTAL-M043.ldr")
    new=read(HERE/"PROTO-045-TERRASSE-BOIS-NETTOYEE.ldr")
    full=read(HERE/"GUIDED004-B3-EXPERIMENTAL-M045.ldr")
    audit=json.loads((HERE/"AUDIT-045.json").read_text())
    bom=json.loads((HERE/"BOM-045.json").read_text())
    assert (len(source),len(old),len(oldfull),len(new),len(full))==(1904,163,1912,116,1865)
    old_by={p["name"]:p for p in old}
    new_by={p["name"]:p for p in new}
    assert len(new_by)==len(new)
    deleted=set(old_by)-set(new_by)
    assert deleted=={p["name"] for p in audit["deleted"]} and len(deleted)==48
    assert sum(":rail-" in x for x in deleted)==39
    assert sum(x.startswith("EXPERIMENT-B2-DECK") for x in deleted)==4
    assert sum("hidden-cross-" in x for x in deleted)==5
    moved=set()
    for p in new:
        if p["name"] in old_by and p["line"]!=old_by[p["name"]]["line"]:
            moved.add(p["name"])
    assert moved=={p["name"] for p in audit["repositions"]} and len(moved)==29
    assert set(new_by)-set(old_by)=={"M045:post-east:top-brick"}
    for p in new:
        if p["name"].startswith("M039:"):
            assert p["line"]==old_by[p["name"]]["line"]
    # Every original, non-terrrace B3 part retained from M043 is unchanged in the full variant.
    oldnames=set(old_by)
    static=[p for p in oldfull if p["name"] not in oldnames]
    assert [(p["name"],p["line"]) for p in full]==[(p["name"],p["line"]) for p in [*static,*new]]
    assert len(static)==1749
    c0,c1=collisions(oldfull),collisions(full)
    assert not(c1-c0),"NEW FULL HOUSE AABB CLASH: "+repr(sorted(c1-c0)[:5])
    assert len(c0)==audit["collision_AABB"]["M043_full"]
    assert len(c1)==audit["collision_AABB"]["M045_full"]
    assert not any(over(new_by["M045:post-east:top-brick"],p) for p in full if p["name"]!="M045:post-east:top-brick")
    posts=[p for p in new if "support-solution:timber-post" in p["name"] or p["name"]=="M045:post-east:top-brick"]
    boards=[p for p in new if p["name"].startswith("scene-platform:south-timber-") and ":board:" in p["name"]]
    actual=[(p["name"],q["name"]) for p in posts for q in boards if studs(p,q) or studs(q,p)]
    expected={(p["post"],p["board"]) for p in audit["post_to_deck_contacts"]}
    assert set(actual)==expected
    for col in ("east","west","return"):
        assert any("timber-post-"+col in p or col=="east" and p=="M045:post-east:top-brick" for p,q in actual)
    assert Counter(p["part"] for p in new)==Counter(bom["isolated_references"])
    assert Counter(p["part"] for p in full)==Counter(bom["full_references"])
    print("M045 PASS: 48 provisional/free elements removed; 29 support bricks re-seated; 1 connector; 0 new AABB conflicts")
    print("M045 LIMITS: guardrails deferred, 2 return boards/other planks need real underdeck joining; no stability certificate")
if __name__=="__main__":run()
