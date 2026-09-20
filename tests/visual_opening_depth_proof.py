from contextlib import contextmanager
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import shutil
import subprocess
import sys
import threading

from playwright.sync_api import sync_playwright

from brickhouse.bricks.export import BrickExportBundle
from brickhouse.bricks.opening_depth_prototype import recess_opening_closure_for_prototype

ROOT=Path(__file__).resolve().parents[1]
OUT=Path("/tmp/opening-depth-proof")
SAMPLE=ROOT/"frontend/sample-export.json"
MODEL={
 "schema_version":"0.1","id":"opening-depth-proof","name":"Opening depth proof",
 "building_type":"house","units":"m",
 "volumes":[{"id":"main","shape":"rectangular_prism","position":{"x":0,"y":0,"z":0},"width":5.0,"depth":1.5,"height":3.0,"floors":1,"source":{"kind":"user_provided","confidence":1.0}}],
 "openings":[{"id":"window","type":"window","volume_id":"main","facade":"front","offset_horizontal":2.0,"offset_vertical":0.8,"width":1.0,"height":1.2,"source":{"kind":"user_provided","confidence":1.0},"window_style":"simple","has_sill":True,"has_decorative_surround":True}],
 "roofs":[],
 "appearance":{"walls":{"color":"beige"},"roof":{"color":"gray"},"frames":{"color":"white"}},
 "metadata":{"created_from":"synthetic","notes":"Generic one-stud representation-depth prototype; not architectural metric truth"}
}

def generate():
 OUT.mkdir(parents=True,exist_ok=True)
 model=OUT/"model.json";model.write_text(json.dumps(MODEL),encoding="utf-8")
 subprocess.run(["brickhouse-m0",str(model),str(OUT/"before.json"),"--front-width-studs","20"],cwd=ROOT,check=True)
 bundle=BrickExportBundle.model_validate_json((OUT/"before.json").read_text())
 recessed=recess_opening_closure_for_prototype(bundle.brick_model,opening_id="window",depth_studs=1)
 after=bundle.model_copy(update={"brick_model":recessed})
 (OUT/"after.json").write_text(after.model_dump_json(indent=2,exclude_none=True))
 before_window=[p for p in bundle.brick_model.parts if p.opening_id=="window" and p.category in {"window_frame","window_pane"}]
 after_window=[p for p in recessed.parts if p.opening_id=="window" and p.category in {"window_frame","window_pane"}]
 lines=["DEPTH_STUDS=1 REPRESENTATION_ONLY"]
 lines += [f"BEFORE {p.placement_id} {p.part_id} ({p.x_studs},{p.y_studs},{p.z_plates})" for p in before_window]
 lines += [f"AFTER {p.placement_id} {p.part_id} ({p.x_studs},{p.y_studs},{p.z_plates})" for p in after_window]
 (OUT/"parts.txt").write_text("\n".join(lines)+"\n")

@contextmanager
def serve():
 class Quiet(SimpleHTTPRequestHandler):
  def log_message(self,*_):pass
 server=ThreadingHTTPServer(("127.0.0.1",0),lambda *a,**k:Quiet(*a,directory=ROOT,**k))
 t=threading.Thread(target=server.serve_forever,daemon=True);t.start()
 try:yield server.server_port
 finally:server.shutdown();t.join();server.server_close()

def browser_binary():
 for name in ("google-chrome","google-chrome-stable","chromium","chromium-browser"):
  p=shutil.which(name)
  if p:return p
 raise RuntimeError("Chromium/Chrome absent")

def capture():
 with serve() as port,sync_playwright() as p:
  browser=p.chromium.launch(headless=True,executable_path=browser_binary(),args=["--no-sandbox"])
  for label in ("before","after"):
   SAMPLE.write_text((OUT/f"{label}.json").read_text())
   context=browser.new_context(viewport={"width":900,"height":700})
   context.add_init_script("localStorage.clear()")
   page=context.new_page()
   page.goto(f"http://127.0.0.1:{port}/frontend/viewer.html?depth={label}",wait_until="networkidle")
   page.locator("#view-front").click();page.wait_for_timeout(500)
   page.locator("#viewer").screenshot(path=str(OUT/f"{label}-front.png"))
   page.locator("#reset-view").click();page.wait_for_timeout(500)
   page.locator("#viewer").screenshot(path=str(OUT/f"{label}-three-quarter.png"))
   context.close()
  browser.close()

if __name__=="__main__":
 {"generate":generate,"capture":capture}[sys.argv[1]]()
