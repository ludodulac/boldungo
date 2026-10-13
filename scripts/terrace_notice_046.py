"""GUIDED-004 terrace module 045: conservative vertical insertion and LDraw steps.

Run: python scripts/terrace_notice_046.py path/to/brick-model.json output.ldr
Requires only Python stdlib; reuses terrace_assembly_045 identities and engagements.
"""
import json
import re
import sys
from pathlib import Path
from terrace_assembly_045 import ids, assemble, engagement

P = "scene-platform:south-timber-deck-main:"
POSTS = {P + f"x_min:rail-post:{n}" for n in ("00035","00039","00043")} | {P + "y_min:rail-post:00089"}
TOPS = {P + "x_min:rail-top-solution:00004", P + "y_min:rail-top-solution:00009"}
CODES = {"PLATE_1X6":"3666.dat", "BRICK_2X8":"3007.dat", "BRICK_1X1":"3005.dat"}

def bounds(p):
    w,l,h=p.get("width_studs"),p.get("length_studs"),p.get("height_plates")
    m=re.fullmatch(r"(BRICK|PLATE|TILE)_(\d+)X(\d+)",p["part_id"])
    if m and (w is None or l is None):
        w,l=map(int,m.groups()[1:])
        if p["rotation_quarter_turns"]%2:w,l=l,w
    if h is None:h=1 if p["part_id"].startswith(("PLATE_","TILE_")) else 3
    if w is None or l is None:return None
    return p["x_studs"],p["y_studs"],p["z_plates"],p["x_studs"]+w,p["y_studs"]+l,p["z_plates"]+h

def intersect(a,b):
    return all(a[i]<b[i+3] and b[i]<a[i+3] for i in range(3))

def vertical_blockers(parts, removed):
    by={p["placement_id"]:p for p in parts}
    module=[by[i] for i in ids[:4]]
    static=[p for p in parts if p["placement_id"] not in set(ids)|removed]
    result=[]
    for p in static:
        b=bounds(p)
        if b is None:continue
        for q in module:
            a=bounds(q)
            swept=(a[0],a[1],a[2],a[3],a[4],max(a[5],200))
            if intersect(swept,b):
                result.append(p["placement_id"])
                break
    return sorted(set(result))

def line(p):
    x,y,z,w,l,h=bounds(p)
    # LDraw: 20 LDU per stud, 8 LDU per plate, Y positive downward.
    # Convert min-corner grid to part center; LDraw local length points along Z.
    # 90-degree rotations swap footprint axes.
    rot=p["rotation_quarter_turns"]%4
    mats=((1,0,0,0,1,0,0,0,1),(0,0,-1,0,1,0,1,0,0),(-1,0,0,0,1,0,0,0,-1),(0,0,1,0,1,0,-1,0,0))
    mx=" ".join(map(str,mats[rot]))
    return f"1 7 {(x+w/2)*20:g} {-z*8:g} {(y+l/2)*20:g} {mx} {CODES[p['part_id']]}"

def main(path, output):
    parts=json.loads(Path(path).read_text())["parts"]
    by={p["placement_id"]:p for p in parts}
    report=assemble(parts)
    module=[by[i] for i in ids[:4]]
    assert all(not intersect(bounds(a),bounds(b)) for i,a in enumerate(module) for b in module[i+1:])
    assert engagement(by[ids[4]],by[ids[1]])==1
    after=vertical_blockers(parts,set())
    before_posts=vertical_blockers(parts,POSTS)
    before_all=vertical_blockers(parts,POSTS|TOPS)
    assert POSTS <= set(after)
    assert TOPS <= set(before_posts)
    assert before_all==[], before_all
    lines=["0 GUIDED004 terrace module 045 / 046","0 !LICENSE CC0-1.0",
           "0 !NOTE Pre-install the BRICK_1X1 support at original location.",
           "0 !NOTE Assemble plate + three boards separately, then lower vertically.",
           "0 !NOTE Install FOUR rail posts and TWO rail top beams AFTER module.",
           "0 !NOTE Geometry-only insertion; physical stability NOT CERTIFIED.",
           "0 STEP", "0 !NOTE Existing support post: "+ids[4],line(by[ids[4]])]
    for n,p in enumerate(module):
        lines+=["0 STEP",f"0 !NOTE Step {n+1}: {p['placement_id']}",line(p)]
    lines+=["0 STEP","0 !NOTE Next: install rail posts "+", ".join(sorted(POSTS)),
            "0 !NOTE Then install rail top beams "+", ".join(sorted(TOPS))]
    Path(output).write_text("\n".join(lines)+"\n")
    print(json.dumps({"parts":5,"module_steps":4,"after_rail_blockers":after,
        "before_four_posts_blockers":before_posts,"before_posts_and_top_beams_blockers":before_all,
        "static_internal_collisions":0,"physical_certification":"NOT_CERTIFIED"},indent=2))

if __name__=="__main__":
    main(sys.argv[1],sys.argv[2])
