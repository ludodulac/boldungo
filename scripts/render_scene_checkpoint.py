#!/usr/bin/env python3
"""Render a deterministic PNG checkpoint through Boldungo's real Scene viewer.

Thin adapter only. Experimental preview flags may replace viewer rendering language
without mutating the ArchitecturalScene JSON.
"""
from __future__ import annotations

import argparse
import json
import shutil
import socketserver
import tempfile
import threading
from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler
from pathlib import Path

from playwright.sync_api import sync_playwright

VIEWPORT = {"width": 1280, "height": 900}
PRESETS = ("front", "south-left", "rear-oblique", "perspective")

LEGACY_RENDER_STAIRS = """function renderStairs() {
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

STEPPED_RENDER_STAIRS = """function renderStairs() {
  for (const stair of currentScene.stairs ?? []) {
    const start = stair.start, end = stair.end;
    const width = Number(stair.width);
    if (!start || !end || ![Number(start.x), Number(start.y), Number(start.z), Number(end.x), Number(end.y), Number(end.z), width].every(Number.isFinite)) continue;
    const rawFrom = new THREE.Vector3(Number(start.x), Number(start.z), Number(start.y));
    const rawTo = new THREE.Vector3(Number(end.x), Number(end.z), Number(end.y));
    const lower = rawFrom.y <= rawTo.y ? rawFrom.clone() : rawTo.clone();
    const upper = rawFrom.y <= rawTo.y ? rawTo.clone() : rawFrom.clone();
    const horizontal = new THREE.Vector3(upper.x - lower.x, 0, upper.z - lower.z);
    const horizontalLength = horizontal.length();
    const rise = upper.y - lower.y;
    if (!(horizontalLength > 0) || !(rise >= 0)) continue;
    const stepCount = Math.max(3, Math.min(16, Math.round(Math.max(horizontalLength / 0.28, rise / 0.18))));
    const direction = horizontal.clone().normalize();
    const treadDepth = horizontalLength / stepCount;
    const yaw = Math.atan2(direction.x, direction.z);
    const baseY = lower.y - 0.04;
    for (let index = 0; index < stepCount; index += 1) {
      const f0 = index / stepCount, f1 = (index + 1) / stepCount;
      const topY = lower.y + rise * f1;
      const boxHeight = Math.max(0.08, topY - baseY);
      const center = lower.clone().addScaledVector(horizontal, (f0 + f1) / 2);
      const mesh = new THREE.Mesh(new THREE.BoxGeometry(width, boxHeight, treadDepth), exteriorMaterial(stair.material));
      addEdges(mesh); mesh.rotation.y = yaw;
      mesh.position.set(center.x, baseY + boxHeight / 2, center.z);
      mesh.userData.architecturalObjectId = stair.id;
      group.add(mesh);
    }
  }
}
"""

LEGACY_RENDER_TERRAIN_START = "function renderTerrain() {"
QUALITATIVE_TERRAIN_PREFIX = """function renderQualitativeTerrainPreview() {
  // Viewer-only sensitivity proxy. The Scene owns only the observed fact that the
  // right/North grade rises front-to-rear; no metric grade is asserted here.
  const host = currentScene.volumes?.[0];
  if (!host) return;
  const w = metric(host.width), d = metric(host.depth);
  const p = host.position ?? {x:0,y:0,z:0};
  if (![w,d,Number(p.x),Number(p.y),Number(p.z)].every(Number.isFinite)) return;
  const mat = new THREE.MeshStandardMaterial({color:0x58604f, roughness:0.95, side:THREE.DoubleSide});
  const x0 = Number(p.x)-5.0, x1 = Number(p.x)+w+5.0;
  const y0 = Number(p.y)-3.0, y1 = Number(p.y)+d+4.0;
  const transition0 = Number(p.y)+d*0.42, transition1 = Number(p.y)+d*0.78;
  const low = Number(p.z)-0.72, high = Number(p.z)+0.10;
  const verts = new Float32Array([
    x0,low,y0, x1,low,y0, x1,low,transition0, x0,low,y0, x1,low,transition0, x0,low,transition0,
    x0,low,transition0, x1,low,transition0, x1,high,transition1, x0,low,transition0, x1,high,transition1, x0,high,transition1,
    x0,high,transition1, x1,high,transition1, x1,high,y1, x0,high,transition1, x1,high,y1, x0,high,y1
  ]);
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(verts,3)); geometry.computeVertexNormals();
  const mesh = new THREE.Mesh(geometry,mat); addEdges(mesh);
  mesh.userData.renderingConvention='qualitative low/high terrain sensitivity proxy; elevations and transition are not measurements';
  group.add(mesh);
}

function renderTerrain() {
  renderQualitativeTerrainPreview();
"""


def _browser_path():
    path = next((shutil.which(n) for n in ("google-chrome","google-chrome-stable","chromium","chromium-browser") if shutil.which(n)), None)
    if not path: raise RuntimeError("No Chromium/Chrome binary available")
    return path

def _serve(root):
    handler=partial(SimpleHTTPRequestHandler,directory=str(root)); server=socketserver.TCPServer(("127.0.0.1",0),handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True); thread.start(); return server,thread

@contextmanager
def _viewer_root(repo_root, stepped_stairs, qualitative_terrain):
    if not stepped_stairs and not qualitative_terrain:
        yield repo_root; return
    with tempfile.TemporaryDirectory(prefix="boldungo-scene-viewer-") as tmp:
        root=Path(tmp); shutil.copytree(repo_root/"frontend",root/"frontend")
        viewer_js=root/"frontend"/"scene-viewer.js"; source=viewer_js.read_text(encoding="utf-8")
        if stepped_stairs:
            if LEGACY_RENDER_STAIRS not in source: raise RuntimeError("Expected renderStairs not found")
            source=source.replace(LEGACY_RENDER_STAIRS,STEPPED_RENDER_STAIRS,1)
        if qualitative_terrain:
            if LEGACY_RENDER_TERRAIN_START not in source: raise RuntimeError("Expected renderTerrain not found")
            source=source.replace(LEGACY_RENDER_TERRAIN_START,QUALITATIVE_TERRAIN_PREFIX,1)
        viewer_js.write_text(source,encoding="utf-8"); yield root

def _apply_preset(page,preset):
    if preset=="front": page.locator("#view-front").click()
    elif preset=="perspective": page.locator("#reset-view").click()
    elif preset in ("south-left","rear-oblique"):
        page.locator("#view-left" if preset=="south-left" else "#view-rear").click(); canvas=page.locator("#viewer"); box=canvas.bounding_box()
        if not box: raise RuntimeError("Scene viewer canvas has no bounding box")
        x=box["x"]+box["width"]*.5; y=box["y"]+box["height"]*.5; page.mouse.move(x,y); page.mouse.down()
        dx=-box["width"]*.12 if preset=="south-left" else box["width"]*.14
        page.mouse.move(x+dx,y-box["height"]*.04,steps=12); page.mouse.up()
    else: raise ValueError(preset)

def render_scene_checkpoint(scene_path,preset,output_path,repo_root,zoom_out=0.0,stepped_stairs=False,qualitative_terrain=False):
    scene=json.loads(scene_path.read_text(encoding="utf-8"))
    if scene.get("schema_version")!="0.2" or not isinstance(scene.get("volumes"),list): raise ValueError("Input must be ArchitecturalScene 0.2")
    with _viewer_root(repo_root,stepped_stairs,qualitative_terrain) as served_root:
        server,thread=_serve(served_root)
        try:
            with sync_playwright() as p:
                browser=p.chromium.launch(headless=True,executable_path=_browser_path(),args=["--no-sandbox"]); page=browser.new_page(viewport=VIEWPORT,device_scale_factor=1); errors=[]
                page.on("pageerror",lambda e:errors.append(str(e))); payload=json.dumps(scene,separators=(",",":"))
                page.add_init_script(script=f"localStorage.setItem('brickhouse.previewArchitecturalScene', {json.dumps(payload)});")
                response=page.goto(f"http://127.0.0.1:{server.server_address[1]}/frontend/scene-viewer.html",wait_until="networkidle",timeout=30000)
                if not response or not response.ok: raise RuntimeError("scene-viewer HTTP failure")
                page.locator("#viewer").wait_for(state="visible",timeout=10000); page.wait_for_function("() => document.querySelector('#message')?.textContent.includes('Aperçu architectural chargé')")
                _apply_preset(page,preset); page.wait_for_timeout(350)
                if zoom_out:
                    box=page.locator("#viewer").bounding_box(); page.mouse.move(box["x"]+box["width"]*.5,box["y"]+box["height"]*.5); page.mouse.wheel(0,zoom_out); page.wait_for_timeout(350)
                if errors: raise RuntimeError(f"Scene viewer runtime errors: {errors}")
                output_path.parent.mkdir(parents=True,exist_ok=True); page.locator("#viewer").screenshot(path=str(output_path)); browser.close()
        finally:
            server.shutdown(); server.server_close(); thread.join(timeout=2)

def main():
    parser=argparse.ArgumentParser(); parser.add_argument("scene",type=Path); parser.add_argument("camera_preset",choices=PRESETS); parser.add_argument("output",type=Path); parser.add_argument("--repo-root",type=Path,default=Path(__file__).resolve().parents[1]); parser.add_argument("--zoom-out",type=float,default=0.0); parser.add_argument("--stepped-stairs",action="store_true"); parser.add_argument("--qualitative-terrain",action="store_true")
    args=parser.parse_args(); render_scene_checkpoint(args.scene,args.camera_preset,args.output,args.repo_root.resolve(),args.zoom_out,args.stepped_stairs,args.qualitative_terrain); print(args.output)
if __name__=="__main__": main()
