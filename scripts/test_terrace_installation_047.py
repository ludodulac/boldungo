"""047 reverse-insertion regression, using the 046 notice geometry."""
import json
import sys
from terrace_notice_046 import bounds, intersect, vertical_blockers, POSTS, TOPS, ids
from terrace_assembly_045 import assemble
from pathlib import Path

def check(path):
    parts=json.loads(Path(path).read_text())["parts"]
    by={p["placement_id"]:p for p in parts}
    assemble(parts)
    a=vertical_blockers(parts,set())
    b=vertical_blockers(parts,POSTS)
    c=vertical_blockers(parts,POSTS|TOPS)
    assert set(a)==POSTS|TOPS,(a,POSTS|TOPS)
    assert set(b)==TOPS,(b,TOPS)
    assert not c,c
    installed=set(ids)
    outside=set(by)-installed-POSTS-TOPS
    for pid in sorted(POSTS)+sorted(TOPS):
        box=bounds(by[pid])
        swept=(*box[:2],box[2],box[3],box[4],max(200,box[5]))
        blockers=[other for other in outside|installed
                  if bounds(by[other]) is not None and intersect(swept,bounds(by[other]))]
        assert not blockers,(pid,blockers)
        installed.add(pid)
    return {"scenario_A":len(a),"scenario_B":len(b),"scenario_C":len(c),"reverse_insertion":"PASS_GEOMETRY_ONLY","physical_clutch":"UNVERIFIED"}

if __name__=="__main__":
    print(json.dumps(check(sys.argv[1]),indent=2))
