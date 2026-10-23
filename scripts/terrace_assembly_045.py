"""Generate a real GUIDED-004 terrace assembly from exported brick-model.json.
Usage: python scripts/terrace_assembly_045.py artifacts/lego2-guided-004/brick-model.json
No physical clutch or full insertion certification is implied.
"""
import json
import sys
P="scene-platform:south-timber-deck-main:"
ids=[P+"hidden-cross-plate:00007-00013"]+[P+f"board:{n:05d}" for n in (1,7,13)]+[P+"support-solution:timber-post-east:0033:00022"]
def footprint(p):
    w,l,h={"PLATE_1X6":(1,6,1),"BRICK_2X8":(2,8,3),"BRICK_1X1":(1,1,3)}[p["part_id"]]
    if p["rotation_quarter_turns"]%2:w,l=l,w
    return p["x_studs"],p["y_studs"],p["z_plates"],w,l,h
def engagement(a,b):
    x,y,z,w,l,h=footprint(a);X,Y,Z,W,L,H=footprint(b)
    if z+h!=Z:return 0
    return max(0,min(x+w,X+W)-max(x,X))*max(0,min(y+l,Y+L)-max(y,Y))
def assemble(parts):
    by={p["placement_id"]:p for p in parts}
    chosen=[by[i] for i in ids]
    plate,boards,post=chosen[0],chosen[1:4],chosen[4]
    studs=[engagement(plate,b) for b in boards]
    support=engagement(post,boards[0])
    if min(studs)<1 or support!=1:raise AssertionError("045_CONNECTION_REGRESSION")
    return {"parts":chosen,"steps":[{"step":i+1,"placement_id":p["placement_id"],"reference":p["part_id"],"x":p["x_studs"],"y":p["y_studs"],"z":p["z_plates"],"rotation":p["rotation_quarter_turns"]} for i,p in enumerate(chosen)],"plate_board_studs":studs,"post_board_studs":support,"assembly_order":"Plate on jig; press boards sequentially from above; place module on existing post BEFORE surrounding rail posts.","physical_certification":"NOT_CERTIFIED"}
if __name__=="__main__":
    result=assemble(json.load(open(sys.argv[1]))["parts"])
    print(json.dumps(result,indent=2,ensure_ascii=False))
