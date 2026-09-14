#!/usr/bin/env python3
"""One visual gate: P1 vs current viewer vs composed opening viewer, same front camera."""
from __future__ import annotations
import json, shutil, socketserver, tempfile, threading
from functools import partial
from http.server import SimpleHTTPRequestHandler
from pathlib import Path
from playwright.sync_api import sync_playwright
from brickhouse.scene.benchmark_scene_recipe import materialize_scene_recipe

ROOT=Path(__file__).resolve().parents[1]
BENCH=ROOT/'frontend/benchmarks/real-house-5'
OUT=ROOT/'artifacts/real-house-5-composed-window-viewer-gate'
VIEWPORT={'width':1280,'height':900}

def browser_path():
    p=next((shutil.which(n) for n in ('google-chrome','google-chrome-stable','chromium','chromium-browser') if shutil.which(n)),None)
    if not p: raise RuntimeError('No Chromium/Chrome binary available')
    return p

def serve(root):
    h=partial(SimpleHTTPRequestHandler,directory=str(root)); s=socketserver.TCPServer(('127.0.0.1',0),h); t=threading.Thread(target=s.serve_forever,daemon=True); t.start(); return s,t

def render(page, url, scene, target):
    payload=json.dumps(scene,separators=(',',':'))
    page.add_init_script(script=f"localStorage.setItem('brickhouse.previewArchitecturalScene', {json.dumps(payload)});")
    r=page.goto(url,wait_until='networkidle',timeout=30000)
    if not r or not r.ok: raise RuntimeError('viewer HTTP failure')
    page.locator('#viewer').wait_for(state='visible',timeout=10000)
    page.wait_for_function("() => document.querySelector('#message')?.textContent.includes('Aperçu architectural chargé')")
    page.locator('#view-front').click(); page.wait_for_timeout(450)
    page.locator('#viewer').screenshot(path=str(target))


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    shutil.copy2(BENCH/'01-original.jpg',OUT/'01-p1-original.jpg')
    scene=materialize_scene_recipe(BENCH/'scene-candidate-v0.2.json').model_dump(mode='json')
    (OUT/'materialized-scene.json').write_text(json.dumps(scene,indent=2)+'\n',encoding='utf-8')
    ids={f'front-opening-{i}' for i in range(1,5)}
    for o in scene['openings']:
        if o['id'] in ids:
            v=o.get('opening_visual') or {}
            assert v.get('surround_color')=='beige' and v.get('surround_relief')=='projecting'
            assert v.get('glazing_plane')=='recessed' and v.get('leaf_count')==2 and v.get('mullion_count')==1
            assert v.get('glazing')=='dark_reflective' and v.get('frame_color')=='dark_gray_brown'
            assert v.get('frame_material')=='painted_or_dark_joinery'
            assert v.get('pane_count') is None and v.get('pane_layout') is None
    with tempfile.TemporaryDirectory(prefix='boldungo-current-viewer-') as tmp:
        old=Path(tmp); shutil.copytree(ROOT/'frontend',old/'frontend')
        # CURRENT is the exact pre-experiment viewer source from the parent checkpoint.
        current_src=shutil.which('git')
        import subprocess
        src=subprocess.check_output(['git','show','c5fab5dd4b1a202de73f59a0c62276d37fc693cb:frontend/scene-viewer.js'],cwd=ROOT,text=True)
        (old/'frontend/scene-viewer.js').write_text(src,encoding='utf-8')
        s1,t1=serve(old); s2,t2=serve(ROOT)
        try:
            with sync_playwright() as p:
                browser=p.chromium.launch(headless=True,executable_path=browser_path(),args=['--no-sandbox'])
                page=browser.new_page(viewport=VIEWPORT,device_scale_factor=1)
                render(page,f"http://127.0.0.1:{s1.server_address[1]}/frontend/scene-viewer.html",scene,OUT/'02-current-front.png')
                render(page,f"http://127.0.0.1:{s2.server_address[1]}/frontend/scene-viewer.html",scene,OUT/'03-new-front.png')
                browser.close()
        finally:
            for s,t in ((s1,t1),(s2,t2)): s.shutdown(); s.server_close(); t.join(timeout=2)
    print(OUT)
if __name__=='__main__': main()
