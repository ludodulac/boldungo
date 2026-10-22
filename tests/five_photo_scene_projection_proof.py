"""Orthographic Scene-vs-photo proof before LEGO materialization."""
from __future__ import annotations
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps

ROOT=Path(__file__).resolve().parents[1]
SCENE=ROOT/"frontend/benchmarks/real-house-5/five-photo-scene-candidate-v0.4.json"
PHOTOS=[ROOT/f"frontend/benchmarks/real-house-5/{i:02d}-original.jpg" for i in range(1,6)]
FACADES=["front","right","left","left","rear"]
OUT=ROOT/"five-photo-scene-projections"

def xy_for(facade,offset,z,span,h,box):
    x0,y0,x1,y1=box
    # Scene facade offsets grow left->right in canonical facade coordinates.
    return (x0+(offset/span)*(x1-x0), y1-(z/h)*(y1-y0))

def draw_projection(scene,facade,size=(600,600)):
    im=Image.new("RGB",size,"white"); d=ImageDraw.Draw(im)
    box=(70,70,540,520); vol=scene["volumes"][0]
    span=vol["width"]["value"] if facade in ("front","rear") else vol["depth"]["value"]
    h=vol["height"]["value"]
    x0,y0,x1,y1=box
    d.rectangle(box,outline="black",width=4)
    roof=scene["roofs"][0]
    if roof["type"]=="gable" and facade in ("front","rear"):
        d.polygon([(x0,y0),(x1,y0),((x0+x1)//2,20)],outline="black")
    for o in scene["openings"]:
        if o["facade"]!=facade: continue
        a=xy_for(facade,o["offset_horizontal"],o["offset_vertical"]+o["height"],span,h,box)
        b=xy_for(facade,o["offset_horizontal"]+o["width"],o["offset_vertical"],span,h,box)
        d.rectangle([a,b],outline="black",width=3)
        d.text((a[0]+3,a[1]+3),o["id"],fill="black")
    if facade=="right" and scene.get("terrain"):
        p=scene["terrain"]["profiles"][0]
        a=xy_for(facade,0,p["start_elevation"],span,h,box); b=xy_for(facade,span,p["end_elevation"],span,h,box)
        d.line([a,b],fill="black",width=5); d.text((a[0]+5,a[1]-22),"GROUND_PROFILE",fill="black")
    if facade=="left":
        for p in scene["platforms"]:
            a=xy_for(facade,p["position"]["y"],p["position"]["z"],span,h,box)
            b=xy_for(facade,p["position"]["y"]+p["depth"],p["position"]["z"],span,h,box)
            d.line([a,b],fill="black",width=8); d.text((a[0],a[1]-20),p["id"],fill="black")
        for s in scene["stairs"]:
            a=xy_for(facade,s["start"]["y"],s["start"]["z"],span,h,box); b=xy_for(facade,s["end"]["y"],s["end"]["z"],span,h,box)
            d.line([a,b],fill="black",width=7)
    if facade=="rear":
        for s in scene["stairs"]:
            # Rear projection uses x and z; proxy geometry outside x<0 remains visible left of wall.
            sx0=x0+(s["start"]["x"]/vol["width"]["value"])*(x1-x0); sy0=y1-(s["start"]["z"]/h)*(y1-y0)
            sx1=x0+(s["end"]["x"]/vol["width"]["value"])*(x1-x0); sy1=y1-(s["end"]["z"]/h)*(y1-y0)
            d.line([(sx0,sy0),(sx1,sy1)],fill="black",width=7)
    # Chimney qualitative projection.
    c=scene["chimneys"][0]
    off=c["position"]["x"] if facade in ("front","rear") else c["position"]["y"]
    cx,cy=xy_for(facade,off,c["position"]["z"],span,h,box)
    d.rectangle([cx-12,cy-65,cx+12,cy],outline="black",width=4); d.text((cx-35,cy-85),"chimney",fill="black")
    d.text((20,570),f"SCENE v0.4 — {facade} — orthographic qualitative projection",fill="black")
    return im

def main():
    scene=json.loads(SCENE.read_text())
    OUT.mkdir(exist_ok=True)
    for i,(photo,facade) in enumerate(zip(PHOTOS,FACADES),1):
        src=Image.open(photo).convert("RGB")
        src=ImageOps.contain(src,(600,600))
        left=Image.new("RGB",(600,600),"white"); left.paste(src,((600-src.width)//2,(600-src.height)//2))
        right=draw_projection(scene,facade)
        pair=Image.new("RGB",(1200,600),"white"); pair.paste(left,(0,0)); pair.paste(right,(600,0))
        ImageDraw.Draw(pair).text((15,15),f"PHOTO SOURCE {i}",fill="black")
        pair.save(OUT/f"photo-{i}-vs-scene.png")
if __name__=="__main__": main()
