"""Produce one real Photo-4 overlay: observed constraints vs perspective Scene-v0.4 projection."""
from __future__ import annotations
import json
from pathlib import Path
from PIL import Image,ImageDraw
from brickhouse.scene.photo_projection import ImageConstraint,PerspectiveCamera,project_point,normalized_error

ROOT=Path(__file__).resolve().parents[1]
PHOTO=ROOT/"frontend/benchmarks/real-house-5/04-original.jpg"
SCENE=ROOT/"frontend/benchmarks/real-house-5/five-photo-scene-candidate-v0.4.json"
OBS=ROOT/"frontend/benchmarks/real-house-5/photo-4-image-constraints-v0.1.json"
OUT=ROOT/"photo4-perspective-overlay.png"

def world_primitives(s):
    v=s["volumes"][0]; w=v["width"]["value"]; d=v["depth"]["value"]; h=v["height"]["value"]
    # left facade lies x=0 in this witness; outlines are intentionally projected from Scene geometry.
    p={"volume-main":[[(0,0,0),(0,d,0),(0,d,h),(0,0,h),(0,0,0)]]}
    for o in s["openings"]:
        if o["facade"]!="left": continue
        y=o["offset_horizontal"]; z=o["offset_vertical"]; ow=o["width"]; oh=o["height"]
        p[o["id"]]=[[(0,y,z),(0,y+ow,z),(0,y+ow,z+oh),(0,y,z+oh),(0,y,z)]]
    for plat in s["platforms"]:
        x=plat["position"]["x"]; y=plat["position"]["y"]; z=plat["position"]["z"]; pw=plat["width"]; pd=plat["depth"]
        p[plat["id"]]=[[(x,y,z),(x+pw,y,z),(x+pw,y+pd,z),(x,y+pd,z),(x,y,z)]]
    p["stair-exterior-1"]=[[(q["start"]["x"],q["start"]["y"],q["start"]["z"]),(q["end"]["x"],q["end"]["y"],q["end"]["z"])] for q in s["stairs"]]
    return p

def fit_camera(scene,constraints,initial):
    # Small deterministic grid search: camera is a variable, not assumed known.
    anchors=[c for c in constraints if c.scene_object_id in {"left-upper","left-access","platform-timber-1","platform-massive-1"}]
    best=(1e9,initial)
    for yaw in range(-55,-14,5):
      for pitch in range(0,21,4):
       for scale_i in range(45,101,5):
        cam=initial.model_copy(update={"yaw_degrees":yaw,"pitch_degrees":pitch,"scale":scale_i/1000})
        err=0; n=0
        primitives=world_primitives(scene)
        for c in anchors:
            lines=primitives.get(c.scene_object_id,[])
            if not lines: continue
            pts=[project_point(q,cam) for line in lines for q in line]
            if not pts: continue
            pc=((min(x for x,y in pts)+max(x for x,y in pts))/2,(min(y for x,y in pts)+max(y for x,y in pts))/2)
            oc=(sum(q.x for q in c.points)/len(c.points),sum(q.y for q in c.points)/len(c.points))
            err+=(pc[0]-oc[0])**2+(pc[1]-oc[1])**2;n+=1
        if n and err/n<best[0]: best=(err/n,cam)
    return best[1]

def pix(pt,W,H): return (round(pt[0]*W),round(pt[1]*H))

def main():
    scene=json.loads(SCENE.read_text()); raw=json.loads(OBS.read_text())
    cs=[ImageConstraint.model_validate(x) for x in raw["constraints"]]
    cam=fit_camera(scene,cs,PerspectiveCamera.model_validate(raw["camera_initial"]))
    im=Image.open(PHOTO).convert("RGBA"); W,H=im.size
    overlay=Image.new("RGBA",im.size,(0,0,0,0)); d=ImageDraw.Draw(overlay)
    # OBSERVED = cyan-ish light line; PROJECTED = magenta-ish dark line. Labels make colors nonessential.
    for c in cs:
        pts=[pix((q.x,q.y),W,H) for q in c.points]
        if c.kind.value=="bbox" and len(pts)==2: d.rectangle([pts[0],pts[1]],outline=(20,220,220,235),width=max(3,W//400))
        elif len(pts)>1: d.line(pts,fill=(20,220,220,235),width=max(3,W//400))
        elif pts: d.ellipse([pts[0][0]-6,pts[0][1]-6,pts[0][0]+6,pts[0][1]+6],outline=(20,220,220,235),width=3)
    primitives=world_primitives(scene)
    for oid,lines in primitives.items():
        for line in lines:
            pts=[pix(project_point(q,cam),W,H) for q in line]
            d.line(pts,fill=(230,40,170,220),width=max(3,W//450))
    d.rectangle((10,10,min(W-10,760),90),fill=(255,255,255,205))
    d.text((25,22),"PHOTO 4 — SAME IMAGE SPACE",fill=(0,0,0,255))
    d.text((25,47),"OBSERVED = cyan   |   SCENE v0.4 PROJECTED = magenta",fill=(0,0,0,255))
    d.text((25,70),f"estimated camera yaw={cam.yaw_degrees:.0f} pitch={cam.pitch_degrees:.0f} scale={cam.scale:.3f}",fill=(0,0,0,255))
    Image.alpha_composite(im,overlay).convert("RGB").save(OUT,quality=94)
    report={"camera":cam.model_dump(),"observed_constraints":len(cs),"scene_unchanged":True,"output":OUT.name}
    (ROOT/"photo4-perspective-overlay-report.json").write_text(json.dumps(report,indent=2)+"\n")
if __name__=="__main__": main()
