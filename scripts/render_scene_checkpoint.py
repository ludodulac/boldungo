#!/usr/bin/env python3
"""Render a deterministic PNG checkpoint through Boldungo's real Scene viewer.

Thin adapter only. Experimental preview flags may replace viewer rendering language
without mutating the ArchitecturalScene JSON.
"""
from __future__ import annotations
import argparse,json,shutil,socketserver,tempfile,threading
from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler
from pathlib import Path
from playwright.sync_api import sync_playwright
VIEWPORT={"width":1280,"height":900}; PRESETS=("front","south-left","rear-oblique","perspective")
LEGACY_RENDER_STAIRS="""function renderStairs() {
  for (const stair of currentScene.stairs ?? []) {
    const start = stair.start, end = stair.end;
    const width = Number(stair.width);
    if (!start || !end || ![Number(start.x), Number(start.y), Number(start.z), Number(end.x), Number(end.y), Number(end.z), width].every(Number.isFinite)) continue;
    const from = new THREE.Vector3(Number(start.x), Number(start.z), Number(start.y));
    const to = new THREE.Vector3(Number(end.x), Number(end.z), Number(end.y));
    const delta = to.clone().sub(from);
    const length = delta.length();
    if (!(length > 0)) continue;
    const thickness = 0.16;
    const geometry = new THREE.BoxGeometry(width, thickness, length);
    const mesh = new THREE.Mesh(geometry, exteriorMaterial(stair.material));
    addEdges(mesh);
    mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), delta.clone().normalize());
    mesh.position.copy(from).add(to).multiplyScalar(0.5);
    mesh.userData.architecturalObjectId = stair.id;
    group.add(mesh);
  }
}
"""
STEPPED_RENDER_STAIRS="""function renderStairs() {
  for (const stair of currentScene.stairs ?? []) {
    const start=stair.start,end=stair.end,width=Number(stair.width);
    if(!start||!end||![Number(start.x),Number(start.y),Number(start.z),Number(end.x),Number(end.y),Number(end.z),width].every(Number.isFinite)) continue;
    const a=new THREE.Vector3(Number(start.x),Number(start.z),Number(start.y)),b=new THREE.Vector3(Number(end.x),Number(end.z),Number(end.y));
    const lower=a.y<=b.y?a.clone():b.clone(),upper=a.y<=b.y?b.clone():a.clone(),horizontal=new THREE.Vector3(upper.x-lower.x,0,upper.z-lower.z),run=horizontal.length(),rise=upper.y-lower.y;
    if(!(run>0)||!(rise>=0)) continue; const count=Math.max(3,Math.min(16,Math.round(Math.max(run/.28,rise/.18)))),dir=horizontal.clone().normalize(),depth=run/count,yaw=Math.atan2(dir.x,dir.z),baseY=lower.y-.04;
    for(let i=0;i<count;i++){const f0=i/count,f1=(i+1)/count,topY=lower.y+rise*f1,h=Math.max(.08,topY-baseY),center=lower.clone().addScaledVector(horizontal,(f0+f1)/2),mesh=new THREE.Mesh(new THREE.BoxGeometry(width,h,depth),exteriorMaterial(stair.material)); addEdges(mesh); mesh.rotation.y=yaw; mesh.position.set(center.x,baseY+h/2,center.z); mesh.userData.architecturalObjectId=stair.id; group.add(mesh);}
  }
}
"""
LEGACY_RENDER_TERRAIN_START="function renderTerrain() {"
QUALITATIVE_TERRAIN_PREFIX="""function renderQualitativeTerrainPreview() {
  // Viewer-only sensitivity proxy. It deliberately stays outside `group`, so the
  // architectural bounding box and therefore every camera preset remain invariant.
  const host=currentScene.volumes?.[0]; if(!host) return;
  const w=metric(host.width),d=metric(host.depth),p=host.position??{x:0,y:0,z:0};
  if(![w,d,Number(p.x),Number(p.y),Number(p.z)].every(Number.isFinite)) return;
  const mat=new THREE.MeshStandardMaterial({color:0x58604f,roughness:.95,side:THREE.DoubleSide});
  const x0=Number(p.x)-5,x1=Number(p.x)+w+5,y0=Number(p.y)-3,y1=Number(p.y)+d+4,t0=Number(p.y)+d*.42,t1=Number(p.y)+d*.78,low=Number(p.z)-.72,high=Number(p.z)+.10;
  const verts=new Float32Array([x0,low,y0,x1,low,y0,x1,low,t0,x0,low,y0,x1,low,t0,x0,low,t0,x0,low,t0,x1,low,t0,x1,high,t1,x0,low,t0,x1,high,t1,x0,high,t1,x0,high,t1,x1,high,t1,x1,high,y1,x0,high,t1,x1,high,y1,x0,high,y1]);
  const geometry=new THREE.BufferGeometry(); geometry.setAttribute('position',new THREE.BufferAttribute(verts,3)); geometry.computeVertexNormals();
  const mesh=new THREE.Mesh(geometry,mat); addEdges(mesh); mesh.userData.renderingConvention='qualitative terrain proxy; no metric claim';
  const terrainPreviewGroup=new THREE.Group(); terrainPreviewGroup.scale.z=-1; terrainPreviewGroup.add(mesh); scene.add(terrainPreviewGroup);
}
function renderTerrain() { renderQualitativeTerrainPreview();
"""
def _browser_path():
    p=next((shutil.which(n) for n in ("google-chrome","google-chrome-stable","chromium","chromium-browser") if shutil.which(n)),None)
    if not p: raise RuntimeError("No Chromium/Chrome binary available")
    return p
def _serve(root):
    h=partial(SimpleHTTPRequestHandler,directory=str(root)); s=socketserver.TCPServer(("127.0.0.1",0),h); t=threading.Thread(target=s.serve_forever,daemon=True); t.start(); return s,t
@contextmanager
def _viewer_root(repo_root,stepped_stairs,qualitative_terrain):
    if not stepped_stairs and not qualitative_terrain: yield repo_root; return
    with tempfile.TemporaryDirectory(prefix="boldungo-scene-viewer-") as tmp:
        root=Path(tmp); shutil.copytree(repo_root/"frontend",root/"frontend"); f=root/"frontend"/"scene-viewer.js"; src=f.read_text(encoding="utf-8")
        if stepped_stairs:
            if LEGACY_RENDER_STAIRS not in src: raise RuntimeError("Expected renderStairs not found")
            src=src.replace(LEGACY_RENDER_STAIRS,STEPPED_RENDER_STAIRS,1)
        if qualitative_terrain:
            if LEGACY_RENDER_TERRAIN_START not in src: raise RuntimeError("Expected renderTerrain not found")
            src=src.replace(LEGACY_RENDER_TERRAIN_START,QUALITATIVE_TERRAIN_PREFIX,1)
        f.write_text(src,encoding="utf-8"); yield root
def _apply_preset(page,preset):
    if preset=="front": page.locator("#view-front").click()
    elif preset=="perspective": page.locator("#reset-view").click()
    elif preset in ("south-left","rear-oblique"):
        page.locator("#view-left" if preset=="south-left" else "#view-rear").click(); box=page.locator("#viewer").bounding_box(); x=box["x"]+box["width"]*.5; y=box["y"]+box["height"]*.5; page.mouse.move(x,y); page.mouse.down(); dx=-box["width"]*.12 if preset=="south-left" else box["width"]*.14; page.mouse.move(x+dx,y-box["height"]*.04,steps=12); page.mouse.up()
    else: raise ValueError(preset)
def render_scene_checkpoint(scene_path,preset,output_path,repo_root,zoom_out=0,stepped_stairs=False,qualitative_terrain=False):
    data=json.loads(scene_path.read_text(encoding="utf-8"));
    with _viewer_root(repo_root,stepped_stairs,qualitative_terrain) as root:
        server,thread=_serve(root)
        try:
            with sync_playwright() as p:
                browser=p.chromium.launch(headless=True,executable_path=_browser_path(),args=["--no-sandbox"]); page=browser.new_page(viewport=VIEWPORT,device_scale_factor=1); errors=[]; page.on("pageerror",lambda e:errors.append(str(e))); payload=json.dumps(data,separators=(",",":")); page.add_init_script(script=f"localStorage.setItem('brickhouse.previewArchitecturalScene', {json.dumps(payload)});"); r=page.goto(f"http://127.0.0.1:{server.server_address[1]}/frontend/scene-viewer.html",wait_until="networkidle",timeout=30000)
                if not r or not r.ok: raise RuntimeError("scene-viewer HTTP failure")
                page.locator("#viewer").wait_for(state="visible",timeout=10000); page.wait_for_function("() => document.querySelector('#message')?.textContent.includes('Aperçu architectural chargé')"); _apply_preset(page,preset); page.wait_for_timeout(350)
                if zoom_out: box=page.locator("#viewer").bounding_box(); page.mouse.move(box["x"]+box["width"]*.5,box["y"]+box["height"]*.5); page.mouse.wheel(0,zoom_out); page.wait_for_timeout(350)
                if errors: raise RuntimeError(str(errors))
                output_path.parent.mkdir(parents=True,exist_ok=True); page.locator("#viewer").screenshot(path=str(output_path)); browser.close()
        finally: server.shutdown(); server.server_close(); thread.join(timeout=2)
def main():
    a=argparse.ArgumentParser(); a.add_argument("scene",type=Path); a.add_argument("camera_preset",choices=PRESETS); a.add_argument("output",type=Path); a.add_argument("--repo-root",type=Path,default=Path(__file__).resolve().parents[1]); a.add_argument("--zoom-out",type=float,default=0); a.add_argument("--stepped-stairs",action="store_true"); a.add_argument("--qualitative-terrain",action="store_true"); x=a.parse_args(); render_scene_checkpoint(x.scene,x.camera_preset,x.output,x.repo_root.resolve(),x.zoom_out,x.stepped_stairs,x.qualitative_terrain); print(x.output)
if __name__=="__main__": main()
