"""R-3 phone-friendly isometric *schematic*, never exact LDraw mesh."""
from __future__ import annotations
from pathlib import Path
import argparse,sys
try:
    from generate_roof_recipe_r3 import recipe
except ModuleNotFoundError:
    from scripts.generate_roof_recipe_r3 import recipe

def svg(width,length):
    a=recipe(width_studs=width,length_studs=length)
    fw=1100
    # Project longitudinal Y and span X and height Z into isometric screen.
    # all values are stud units.
    k=19 if length<=8 else 14
    def pt(x,y,z):
        return (540+(y-length/2)*k-(x-4)*k,
                467+(y-length/2)*k*.37+(x-4)*k*.45-z*21)
    def coords(points):
        return " ".join(f"{pt(*p)[0]:.1f},{pt(*p)[1]:.1f}" for p in points)
    colors={"joint":("#a0b4c5","#c5d3df","#e1e9f0"),
            "cross":("#687f99","#96afc5","#d3e2eb"),
            "wall":("#982f34","#d94546","#ed6a61"),
            "slope":("#092c7c","#154db1","#417ade"),
            "ridge":("#9ca4ba","#ccd3e4","#f0f2fb")}
    polys=[]
    for p in a:
        x,y,z=p.x,p.y,p.z
        X,Y=x+p.sx,y+p.sy
        bot=[(x,y,z),(X,y,z),(X,Y,z),(x,Y,z)]
        if p.role=="slope":
            # Visual wedge rises towards shared center; model geometry must be
            # read from official 4445.dat — this top surface is a schematic.
            if p.x<4:
                roof=[(x,y,z+.5),(X,y,z+3),(X,Y,z+3),(x,Y,z+.5)]
            else:
                roof=[(x,y,z+3),(X,y,z+.5),(X,Y,z+.5),(x,Y,z+3)]
        else:
            roof=[(x,y,z+p.height),(X,y,z+p.height),
                  (X,Y,z+p.height),(x,Y,z+p.height)]
        shade,front,top=colors[p.role]
        faces=[([bot[0],bot[1],roof[1],roof[0]],shade),
            ([bot[1],bot[2],roof[2],roof[1]],front),
            ([bot[3],bot[2],roof[2],roof[3]],shade),
            (roof,top)]
        for face,c in faces:
            depth=sum(q[0]+q[1]+q[2]*.03 for q in face)/len(face)
            polys.append((depth,f'<polygon points="{coords(face)}" fill="{c}" stroke="#273850" stroke-width="0.9"/>'))
    polys.sort(key=lambda q:q[0])
    result=[
        '<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="720" viewBox="0 0 1100 720">',
        f'<title>BOLDUNGO R-3 generic LEGO 45° roof {width}x{length} studs</title>',
        '<rect width="1100" height="720" fill="#f5faff"/>',
        f'<text x="38" y="52" font-size="28" font-family="sans-serif" fill="#18324e" font-weight="bold">BOLDÜNGO R-3 — Toit 45° · {width} × {length} tenons</text>',
        f'<text x="38" y="82" font-size="18" font-family="sans-serif" fill="#375975">Recette paramétrique expérimentale · {len(a)} pièces LEGO réelles</text>',
        '<g stroke-linejoin="round">'+ "\n".join(x[1] for x in polys)+'</g>',
        '<rect x="22" y="655" width="1056" height="47" rx="9" fill="#fff1dc"/>',
        '<text x="40" y="674" font-family="sans-serif" font-size="14" fill="#75421a">VUE SCHÉMATIQUE ISOMÉTRIQUE — profils simplifiés ; ce n’est PAS un rendu des triangles LDraw.</text>',
        '<text x="40" y="694" font-family="sans-serif" font-size="13" fill="#75421a">Les références et orientations authentiques sont dans ROOF-R3.ldr. Assemblage physique non certifié.</text>',
        '</svg>'
    ]
    return "\n".join(result)+"\n"

if __name__=="__main__":
    c=argparse.ArgumentParser()
    c.add_argument("--length-studs",type=int,required=True)
    c.add_argument("--width-studs",type=int,required=True)
    c.add_argument("--output",type=Path,required=True)
    ar=c.parse_args()
    ar.output.parent.mkdir(parents=True,exist_ok=True)
    ar.output.write_text(svg(ar.width_studs,ar.length_studs))
    print("R3_ISOMETRIC_SCHEMATIC",ar.output)
