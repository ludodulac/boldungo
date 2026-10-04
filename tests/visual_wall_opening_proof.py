from contextlib import contextmanager
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import shutil
import subprocess
import sys
import threading

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = Path("/tmp/wall-opening-proof")
SPATIAL = ROOT / "backend/brickhouse/bricks/spatial.py"
SAMPLE = ROOT / "frontend/sample-export.json"

MODEL = {
  "schema_version":"0.1","id":"wall-opening-proof","name":"Wall opening proof",
  "building_type":"house","units":"m",
  "volumes":[{"id":"main","shape":"rectangular_prism","position":{"x":0,"y":0,"z":0},
              "width":5.0,"depth":1.5,"height":3.0,"floors":1,
              "source":{"kind":"user_provided","confidence":1.0}}],
  "openings":[{"id":"window","type":"window","volume_id":"main","facade":"front",
               "offset_horizontal":2.0,"offset_vertical":0.8,"width":1.0,"height":1.2,
               "source":{"kind":"user_provided","confidence":1.0}}],
  "roofs":[],
  "appearance":{"walls":{"color":"beige"},"roof":{"color":"gray"},"frames":{"color":"white"}},
  "metadata":{"created_from":"synthetic","notes":"Generic matched visual proof for PR #723"}
}

def run(cmd):
    subprocess.run(cmd, cwd=ROOT, check=True)

def generate():
    OUT.mkdir(parents=True, exist_ok=True)
    model=OUT/"model.json"; model.write_text(json.dumps(MODEL), encoding="utf-8")
    after_source=SPATIAL.read_text(encoding="utf-8")
    before_source=subprocess.check_output(
        ["git","show","origin/main:backend/brickhouse/bricks/spatial.py"], cwd=ROOT, text=True
    )
    try:
        SPATIAL.write_text(before_source, encoding="utf-8")
        run(["brickhouse-m0",str(model),str(OUT/"before.json"),"--front-width-studs","20"])
        SPATIAL.write_text(after_source, encoding="utf-8")
        run(["brickhouse-m0",str(model),str(OUT/"after.json"),"--front-width-studs","20"])
    finally:
        SPATIAL.write_text(after_source, encoding="utf-8")
    lines=[]
    for label in ("before","after"):
        data=json.loads((OUT/f"{label}.json").read_text())
        front=[p for p in data["brick_model"]["parts"] if p.get("source_facade")=="front" or p["placement_id"].startswith("wall-")]
        lines.append(f"{label.upper()} total_parts={data['bom']['total_parts']}")
        for p in front:
            if 6 <= p.get("z_plates",0) <= 15:
                lines.append(f"{label} {p['placement_id']} {p['part_id']} x={p['x_studs']} z={p['z_plates']}")
    (OUT/"parts.txt").write_text("\n".join(lines)+"\n")

@contextmanager
def serve():
    class Quiet(SimpleHTTPRequestHandler):
        def log_message(self,*_): pass
    server=ThreadingHTTPServer(("127.0.0.1",0),lambda *a,**k:Quiet(*a,directory=ROOT,**k))
    t=threading.Thread(target=server.serve_forever,daemon=True);t.start()
    try: yield server.server_port
    finally: server.shutdown();t.join();server.server_close()

def browser_binary():
    for name in ("google-chrome","google-chrome-stable","chromium","chromium-browser"):
        p=shutil.which(name)
        if p:return p
    raise RuntimeError("Chromium/Chrome absent")

def capture():
    with serve() as port, sync_playwright() as p:
        browser=p.chromium.launch(headless=True,executable_path=browser_binary(),args=["--no-sandbox"])
        for label in ("before","after"):
            SAMPLE.write_text((OUT/f"{label}.json").read_text())
            context=browser.new_context(viewport={"width":900,"height":700})
            context.add_init_script("localStorage.clear()")
            page=context.new_page()
            page.goto(f"http://127.0.0.1:{port}/frontend/viewer.html?proof={label}",wait_until="networkidle")
            page.locator("#view-front").click()
            page.wait_for_timeout(700)
            page.locator("#viewer").screenshot(path=str(OUT/f"{label}.png"))
            context.close()
        browser.close()

if __name__=="__main__":
    {"generate":generate,"capture":capture}[sys.argv[1]]()
