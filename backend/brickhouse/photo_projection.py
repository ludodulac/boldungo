"""Generic photo/Scene perspective overlay prototype.

Reads normalized image observations, an approximate pinhole camera and an
ArchitecturalScene JSON. It never mutates the Scene. Output is an SVG in the
same image coordinate system as the source photograph.
"""
from __future__ import annotations
import argparse, json, math
from pathlib import Path

def matmul(a,b):
    return [[sum(a[i][k]*b[k][j] for k in range(len(b))) for j in range(len(b[0]))] for i in range(len(a))]

def rodrigues(rv):
    th=math.sqrt(sum(v*v for v in rv))
    if th < 1e-12: return [[1,0,0],[0,1,0],[0,0,1]]
    x,y,z=[v/th for v in rv]; c=math.cos(th); s=math.sin(th); C=1-c
    return [[c+x*x*C,x*y*C-z*s,x*z*C+y*s],[y*x*C+z*s,c+y*y*C,y*z*C-x*s],[z*x*C-y*s,z*y*C+x*s,c+z*z*C]]

def project(p,cam):
    R=rodrigues(cam["rotation_vector"]); t=cam["translation"]
    q=[sum(R[i][j]*p[j] for j in range(3))+t[i] for i in range(3)]
    f=cam["focal_px"]; cx,cy=cam["principal_point_px"]; w,h=cam["image_size"]
    return ((f*q[0]/q[2]+cx)/w,(f*q[1]/q[2]+cy)/h)

def poly(scene,cam):
    v=scene["volumes"][0]; W=v["width"]["value"]; D=v["depth"]["value"]; H=v["height"]["value"]
    out=[]
    def add(id,pts,kind="polyline"): out.append((id,[project(p,cam) for p in pts],kind))
    # Left facade silhouette in this witness coordinate convention.
    add("scene-building-silhouette",[(0,0,0),(0,0,H),(0,D,H),(0,D,0),(0,0,0)])
    for o in scene["openings"]:
        if o["facade"]!="left": continue
        y=o["offset_horizontal"]; z=o["offset_vertical"]; ww=o["width"]; hh=o["height"]
        add("scene-"+o["id"],[(0,y,z),(0,y+ww,z),(0,y+ww,z+hh),(0,y,z+hh),(0,y,z)])
    for p in scene["platforms"]:
        x=p["position"]["x"]; y=p["position"]["y"]; z=p["position"]["z"]; w=p["width"]; d=p["depth"]
        add("scene-"+p["id"],[(0,y,z),(x,y,z),(x,y+d,z),(0,y+d,z)])
    for s in scene["stairs"]:
        add("scene-"+s["id"],[(s["start"]["x"],s["start"]["y"],s["start"]["z"]),(s["end"]["x"],s["end"]["y"],s["end"]["z"])])
    for ch in scene["chimneys"]:
        p=ch["position"]; add("scene-"+ch["id"],[(p["x"],p["y"],p["z"]),(p["x"],p["y"],p["z"]+ch["height"])])
    return out

def svg(scene,obs,cam):
    w,h=cam["image_size"]; photo=Path(obs["image_path"]).name
    lines=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
      f'<image href="{photo}" x="0" y="0" width="{w}" height="{h}" preserveAspectRatio="none"/>',
      '<rect x="8" y="8" width="350" height="74" rx="8" fill="white" fill-opacity=".82"/>',
      '<text x="20" y="34" font-family="sans-serif" font-size="18" fill="#111">PHOTO 4 ↔ projection perspective Scene v0.4</text>',
      '<text x="20" y="61" font-family="sans-serif" font-size="15" fill="#00a6a6">OBSERVÉ = cyan pointillé</text>',
      '<text x="190" y="61" font-family="sans-serif" font-size="15" fill="#d100d1">SCENE = magenta continu</text>']
    def pts(ps): return " ".join(f"{x*w:.1f},{y*h:.1f}" for x,y in ps)
    for p in obs["primitives"]:
        ps=p.get("points")
        if p["kind"]=="BBOX":
            x0,y0,x1,y1=p["bbox"]; ps=[[x0,y0],[x1,y0],[x1,y1],[x0,y1],[x0,y0]]
        if not ps: continue
        lines.append(f'<polyline points="{pts(ps)}" fill="none" stroke="#00d7d7" stroke-width="5" stroke-dasharray="12 9" stroke-linejoin="round"/>')
    for id,ps,_ in poly(scene,cam):
        lines.append(f'<polyline points="{pts(ps)}" fill="none" stroke="#ef00ef" stroke-width="4" stroke-linejoin="round" opacity=".92"/>')
        x,y=ps[0]; lines.append(f'<text x="{x*w+5:.1f}" y="{y*h-5:.1f}" font-family="sans-serif" font-size="13" fill="#ef00ef">{id.replace("scene-","")}</text>')
    lines.append("</svg>")
    return "\n".join(lines)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("scene"); ap.add_argument("constraints"); ap.add_argument("camera"); ap.add_argument("output")
    a=ap.parse_args(); scene=json.loads(Path(a.scene).read_text()); obs=json.loads(Path(a.constraints).read_text()); cam=json.loads(Path(a.camera).read_text())
    Path(a.output).write_text(svg(scene,obs,cam))
if __name__=="__main__": main()
