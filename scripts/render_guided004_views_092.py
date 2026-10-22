"""Render SVG control views FROM real BrickModel orthogonal placements only.

These are deterministic orthographic/axonometric box-envelope previews, not
LDraw mesh views or photographs. Architectural nonrectangular façade details
are excluded rather than invented. Their absence is marked in the output.
"""
from __future__ import annotations
import argparse,json,math
from pathlib import Path

# Exact dimensions for the standard brick/plate catalogue; nothing fictional.
from brickhouse.bricks.catalog import standard_orthogonal_definitions
from brickhouse.bricks.brick_model import BrickModel

D=standard_orthogonal_definitions()
KINDS={
    "roof_surface":"#97adc3","roof_ridge":"#53677a",
    "roof_frame":"#bf784c","roof_deck":"#556372",
    "wall":"#c8cacb","detail":"#97aaa5",
}
def box(p):
    d=D.get(p.part_id)
    if d is None:return None
    w,h=d.footprint(p.rotation_quarter_turns)
    return (p.x_studs,p.y_studs,p.z_plates*.4,
            p.x_studs+w,p.y_studs+h,
            (p.z_plates+d.height_plates)*.4)
def category(p):
    pid=p.placement_id
    if pid.startswith("EXPERIMENT-092-SKIN"):return "roof_surface"
    if pid.startswith("EXPERIMENT-092-TRANSVERSE") or pid.startswith("EXPERIMENT-092-GIRDER"):
        return "roof_frame"
    if pid.startswith("EXPERIMENT-091-RIDGE"):return "roof_ridge"
    if pid.startswith("EXPERIMENT-091-DECK"):return "roof_deck"
    if p.component=="wall":return "wall"
    return "detail"
def project(view,x,y,z):
    if view=="perspective":return ((x-y)*.866,(x+y)*.5-z)
    if view=="front":return (x,-z+.20*y)
    if view=="rear":return (-x,-z-.20*y)
    if view=="north":return (y,-z+.20*x)
    if view=="south":return (-y,-z-.20*x)
    if view=="roof":return (x,y)
    raise ValueError(view)
def polygons(view,b):
    x,y,z,X,Y,Z=b
    v=[(x,y,z),(X,y,z),(X,Y,z),(x,Y,z),
       (x,y,Z),(X,y,Z),(X,Y,Z),(x,Y,Z)]
    faceids=([3,2,6,7],[1,2,6,5],[4,5,6,7])
    if view=="front":faceids=([0,1,5,4],)
    if view=="rear":faceids=([2,3,7,6],)
    if view=="north":faceids=([1,2,6,5],)
    if view=="south":faceids=([3,0,4,7],)
    if view=="roof":faceids=([4,5,6,7],)
    return [[project(view,*v[i]) for i in ids] for ids in faceids]
def render(model,view,path):
    # Use ONLY physical (x,y,z) from real BrickModel placements.
    parts=[]
    for p in model.parts:
        b=box(p)
        if b and p.component in ("wall","facade_detail","roof_support","roof"):
            parts.append((p,b))
    def depth(o):
        _,(x,y,z,X,Y,Z)=o
        return ((x+y) if view=="perspective" else
                y if view=="front" else -y if view=="rear" else
                x if view=="north" else -x if view=="south" else -Z)
    parts.sort(key=depth)
    polygons_by_part=[(p,polygons(view,b)) for p,b in parts]
    allpts=[pt for _,polyset in polygons_by_part for poly in polyset for pt in poly]
    left=min(x for x,y in allpts);right=max(x for x,y in allpts)
    top=min(y for x,y in allpts);bottom=max(y for x,y in allpts)
    W,H=1200,850
    sc=min((W-100)/max(1,right-left),(H-120)/max(1,bottom-top))
    def coord(pt):
        x,y=pt
        return "%.1f,%.1f"%(50+(x-left)*sc,75+(y-top)*sc)
    arr=[
        '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="850" viewBox="0 0 1200 850">',
        '<rect width="1200" height="850" fill="#f5f7fa"/>',
        '<text x="45" y="39" font-size="25" font-family="Arial" fill="#202c3c">BOLDÜNGO — 092 — '+view.upper()+'</text>',
        '<text x="45" y="67" font-size="14" font-family="Arial" fill="#7b3940">Vue technique à partir des pièces du vrai BrickModel. Enveloppes cubiques ; détails non orthogonaux omis.</text>'
    ]
    for p,polys in polygons_by_part:
        color=KINDS[category(p)]
        for i,poly in enumerate(polys):
            fc=color
            arr.append('<polygon points="'+(" ".join(coord(pt) for pt in poly))+
                       '" fill="'+fc+'" fill-opacity=".91" stroke="#2b3746" stroke-width=".30"/>')
    arr += ['<text x="45" y="835" font-family="Arial" font-size="13" fill="#7b3940">NOT_CERTIFIED — ni visibilité occultée, ni résistance, ni insertion physiquement vérifiées.</text>',
            "</svg>"]
    path.write_text("\n".join(arr),encoding="utf-8")
def main(source,previous,out):
    model=BrickModel.model_validate_json(source.read_bytes())
    model091=BrickModel.model_validate_json(previous.read_bytes())
    out.mkdir(parents=True,exist_ok=True)
    for view in ("perspective","front","rear","north","south","roof"):
        render(model,view,out/("092-"+view+".svg"))
    render(model091,"perspective",out/"091-perspective-comparaison.svg")
    print("LEGO2_092_VIEWS",len(list(out.glob("*.svg"))))

if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--source",type=Path,required=True)
    a.add_argument("--previous",type=Path,required=True)
    a.add_argument("--output",type=Path,required=True)
    args=a.parse_args();main(args.source,args.previous,args.output)
