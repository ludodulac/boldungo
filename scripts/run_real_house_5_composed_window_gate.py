#!/usr/bin/env python3
"""One visual gate: P1 vs CURRENT vs composed viewer experiment, same front camera."""
from __future__ import annotations
import json, shutil, socketserver, subprocess, tempfile, threading
from functools import partial
from http.server import SimpleHTTPRequestHandler
from pathlib import Path
from playwright.sync_api import sync_playwright
from brickhouse.scene.benchmark_scene_recipe import materialize_scene_recipe

ROOT=Path(__file__).resolve().parents[1]
BENCH=ROOT/'frontend/benchmarks/real-house-5'
OUT=ROOT/'artifacts/real-house-5-composed-window-viewer-gate'
VIEWPORT={'width':1280,'height':900}
CHECKPOINT='c5fab5dd4b1a202de73f59a0c62276d37fc693cb'
OLD_START='function renderOpenings() {'
OLD_END='\nfunction renderPlatforms() {'
NEW_RENDER=r'''function openingViewerColor(value, fallback) {
  if (value === 'beige') return 0xd8c2a4;
  if (value === 'dark_gray_brown') return 0x2d2926;
  return fallback;
}
function renderOpenings() {
  for (const opening of currentScene.openings ?? []) {
    const volume = volumeById(opening.volume_id); if (!volume) continue;
    const width=metric(volume.width),depth=metric(volume.depth),height=metric(volume.height);
    const ow=Number(opening.width),oh=Number(opening.height),ox=Number(opening.offset_horizontal),oz=Number(opening.offset_vertical);
    if (![width,depth,height,ow,oh,ox,oz].every(Number.isFinite)) continue;
    const p=volume.position??{x:0,y:0,z:0}, visual=opening.opening_visual??{}, thickness=.035;
    let x,y,z,axis;
    if(opening.facade==='front'||opening.facade==='rear'){x=Number(p.x)+ox+ow/2;y=Number(p.z)+oz+oh/2;z=Number(p.y)+(opening.facade==='front'?-thickness:depth+thickness);axis='z';}
    else{x=Number(p.x)+(opening.facade==='left'?-thickness:width+thickness);y=Number(p.z)+oz+oh/2;z=Number(p.y)+ox+ow/2;axis='x';}
    const composed=visual.leaf_count===2&&visual.mullion_count===1&&visual.glazing==='dark_reflective'&&visual.surround_color==='beige';
    if(!composed){const g=axis==='z'?new THREE.BoxGeometry(ow,oh,thickness):new THREE.BoxGeometry(thickness,oh,ow);const m=new THREE.Mesh(g,openingMaterial);m.position.set(x,y,z);group.add(m);continue;}
    // Pure viewer conventions: tiny relative offsets/thicknesses, no architectural depth claim.
    const surroundT=Math.min(ow,oh)*.055, relief=.018, recess=.018;
    const surroundMat=new THREE.MeshStandardMaterial({color:openingViewerColor(visual.surround_color,0xd8c2a4),roughness:.72});
    const darkMat=new THREE.MeshStandardMaterial({color:0x15191d,roughness:.16,metalness:.05});
    const frameMat=new THREE.MeshStandardMaterial({color:openingViewerColor(visual.frame_color,0x2d2926),roughness:.45});
    const face=opening.facade==='front'?-1:1;
    const addBox=(bw,bh,bt,bx,by,bz,mat)=>{const g=axis==='z'?new THREE.BoxGeometry(bw,bh,bt):new THREE.BoxGeometry(bt,bh,bw);const m=new THREE.Mesh(g,mat);m.position.set(bx,by,bz);group.add(m);};
    const normal=(d)=>axis==='z'?[0,0,face*d]:[face*d,0,0];
    const at=(dx,dy,dn)=>{const n=normal(dn);return[x+(axis==='z'?dx:0)+n[0],y+dy,z+(axis==='x'?dx:0)+n[2]];};
    // Clear surround as four strips, preserving the opening's exact outer width/height.
    for(const [bw,bh,dx,dy] of [[ow,surroundT,0,(oh-surroundT)/2],[ow,surroundT,0,-(oh-surroundT)/2],[surroundT,oh-2*surroundT,(ow-surroundT)/2,0],[surroundT,oh-2*surroundT,-(ow-surroundT)/2,0]]){const q=at(dx,dy,relief);addBox(bw,bh,thickness,...q,surroundMat);}
    const innerW=Math.max(.01,ow-2*surroundT),innerH=Math.max(.01,oh-2*surroundT),q=at(0,0,-recess);addBox(innerW,innerH,thickness,...q,darkMat);
    // Exactly one vertical mullion from structured mullion_count=1. No panes/transoms inferred.
    const mullionW=Math.min(innerW*.055,.08),mq=at(0,0,-recess+0.006);addBox(mullionW,innerH,thickness*1.25,...mq,frameMat);
  }
}
'''

def browser_path():
    p=next((shutil.which(n) for n in ('google-chrome','google-chrome-stable','chromium','chromium-browser') if shutil.which(n)),None)
    if not p: raise RuntimeError('No Chromium/Chrome binary available')
    return p

def serve(root):
    h=partial(SimpleHTTPRequestHandler,directory=str(root)); s=socketserver.TCPServer(('127.0.0.1',0),h); t=threading.Thread(target=s.serve_forever,daemon=True); t.start(); return s,t

def render(page,url,scene,target):
    payload=json.dumps(scene,separators=(',',':')); page.add_init_script(script=f"localStorage.setItem('brickhouse.previewArchitecturalScene', {json.dumps(payload)});")
    r=page.goto(url,wait_until='networkidle',timeout=30000)
    if not r or not r.ok: raise RuntimeError('viewer HTTP failure')
    page.locator('#viewer').wait_for(state='visible',timeout=10000); page.wait_for_function("() => document.querySelector('#message')?.textContent.includes('Aperçu architectural chargé')")
    page.locator('#view-front').click(); page.wait_for_timeout(450); page.locator('#viewer').screenshot(path=str(target))

def main():
    OUT.mkdir(parents=True,exist_ok=True); shutil.copy2(BENCH/'01-original.jpg',OUT/'01-p1-original.jpg')
    scene=materialize_scene_recipe(BENCH/'scene-candidate-v0.2.json').model_dump(mode='json'); (OUT/'materialized-scene.json').write_text(json.dumps(scene,indent=2)+'\n',encoding='utf-8')
    ids={f'front-opening-{i}' for i in range(1,5)}
    for o in scene['openings']:
        if o['id'] in ids:
            v=o.get('opening_visual') or {}
            assert (v.get('surround_color'),v.get('surround_relief'),v.get('glazing_plane'))==('beige','projecting','recessed')
            assert (v.get('leaf_count'),v.get('mullion_count'),v.get('glazing'))==(2,1,'dark_reflective')
            assert (v.get('frame_color'),v.get('frame_material'))==('dark_gray_brown','painted_or_dark_joinery')
            assert v.get('pane_count') is None and v.get('pane_layout') is None
    with tempfile.TemporaryDirectory(prefix='boldungo-window-gate-') as tmp:
        root=Path(tmp); current=root/'current'; new=root/'new'; shutil.copytree(ROOT/'frontend',current/'frontend'); shutil.copytree(ROOT/'frontend',new/'frontend')
        src=subprocess.check_output(['git','show',f'{CHECKPOINT}:frontend/scene-viewer.js'],cwd=ROOT,text=True); (current/'frontend/scene-viewer.js').write_text(src,encoding='utf-8')
        start=src.index(OLD_START); end=src.index(OLD_END,start); experimental=src[:start]+NEW_RENDER+src[end:]; (new/'frontend/scene-viewer.js').write_text(experimental,encoding='utf-8'); (OUT/'viewer-experiment.diff.txt').write_text('Viewer-only replacement of renderOpenings(): composed rendering consumes only existing opening_visual; no Scene mutation.\n',encoding='utf-8')
        s1,t1=serve(current); s2,t2=serve(new)
        try:
            with sync_playwright() as p:
                browser=p.chromium.launch(headless=True,executable_path=browser_path(),args=['--no-sandbox']); page=browser.new_page(viewport=VIEWPORT,device_scale_factor=1)
                render(page,f"http://127.0.0.1:{s1.server_address[1]}/frontend/scene-viewer.html",scene,OUT/'02-current-front.png'); render(page,f"http://127.0.0.1:{s2.server_address[1]}/frontend/scene-viewer.html",scene,OUT/'03-new-front.png'); browser.close()
        finally:
            for s,t in ((s1,t1),(s2,t2)): s.shutdown(); s.server_close(); t.join(timeout=2)
    print(OUT)
if __name__=='__main__': main()
