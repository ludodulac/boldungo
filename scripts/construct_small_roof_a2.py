"""BOLDUNGO A-2: real-part small roof module, limited to TWO ridge candidates.

No GUIDED-004 input. Every piece has a numeric world LDraw transform. This
is a bounded *experiment* and never turns mesh CONTACT into a clutch proof.
"""
from __future__ import annotations

from collections import Counter,defaultdict
from dataclasses import replace
from pathlib import Path
import argparse,json

try:
    from scripts.experiment_stacked_roofs_a import Piece, _ldraw
except ModuleNotFoundError:
    from experiment_stacked_roofs_a import Piece, _ldraw

W,L = 20,20
# Two inner adjacent 30363 courses, j=1 and j=2, from A1. Roof cross section
# covers both sides of a common ridge. The 2x2 pillars and 2x2 bearing bricks
# are explicitly included to bring every course back to the 32x32 baseplate.
def generate(candidate="3023b"):
    if candidate not in ("3023b","3022"):
        raise ValueError("Only two authorized ridge candidates")
    pieces=[Piece("module-base-3811","3811","base",0,0,-1,W,L,1)]
    for step in (1,2):
        for side in ("left","right"):
            x=3*step if side=="left" else W-4-3*step
            bx=x+1
            z=9-3+3*step
            for level in range(0,z,3):
                pieces.append(Piece(f"{side}-j{step}-pier-z{level}","3003","pier",
                                    bx,2,level,2,2))
            pieces.append(Piece(f"{side}-j{step}-bearing","3003","beam",
                                 bx,2,z,2,2))
    for step in (1,2):
        for side in ("left","right"):
            x=3*step if side=="left" else W-4-3*step
            pieces.append(Piece(f"{side}-j{step}-30363","30363","slope",
                       x,2,9+3*step,4,2,3,side,step))
    ridge_z=9+3*2+3
    if candidate=="3023b":
        for y in (2,3):
            pieces.append(Piece(f"ridge-3023b-y{y}","3023b","ridge",9,y,
                                ridge_z,2,1,1))
    else:
        pieces.append(Piece("ridge-3022","3022","ridge",9,2,ridge_z,2,2,1))
    assert len({p.pid for p in pieces})==len(pieces)
    return pieces

def staged_parts(parts):
    """Every support is installed from bottom up, followed by increasing
    slope courses and the ridge; no piece is intentionally passed through
    the finished opposite pan.
    """
    base=[p for p in parts if p.role=="base"]
    posts=sorted((p for p in parts if p.role=="pier"),key=lambda p:(p.z,p.pid))
    beams=sorted((p for p in parts if p.role=="beam"),key=lambda p:(p.z,p.pid))
    slopes=sorted((p for p in parts if p.role=="slope"),key=lambda p:(p.step,p.pid))
    ridge=sorted((p for p in parts if p.role=="ridge"),key=lambda p:p.pid)
    return base+posts+beams+slopes+ridge

def export(outdir):
    outdir=Path(outdir)
    outdir.mkdir(parents=True,exist_ok=True)
    for c in ("3023b","3022"):
        arr=staged_parts(generate(c))
        folder=outdir/c
        folder.mkdir(parents=True,exist_ok=True)
        (folder/"SMALL-ROOF-A2.ldr").write_text(
            _ldraw(arr,W,L,f"BOLDUNGO-A2-NON-CERTIFIE-{c}"))
        bom=dict(sorted(Counter(p.ldraw for p in arr).items()))
        (folder/"BOM.json").write_text(json.dumps({"total":len(arr),"roof":sum(
            p.role in ("slope","ridge") for p in arr),"ldraw":bom},indent=2)+"\n")
        (folder/"ORDER.json").write_text(json.dumps([{"step":i+1,"id":p.pid,
          "ldraw":p.ldraw,"direction":"VERTICAL_FROM_ABOVE__SAMPLED_NOT_CONTINUOUSLY_PROVED",
          "x":p.x,"y":p.y,"z":p.z} for i,p in enumerate(arr)],indent=2)+"\n")
        print("A2_MODULE",c,"TOTAL",len(arr),"ROOF",sum(
            p.role in ("slope","ridge") for p in arr),"BOM",bom)
    return outdir

if __name__=="__main__":
    arg=argparse.ArgumentParser()
    arg.add_argument("--output",type=Path,default=Path("artifacts/lego2-a2-small-module"))
    export(arg.parse_args().output)
