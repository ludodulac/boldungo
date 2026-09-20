from pathlib import Path
import json, subprocess, sys
from brickhouse.building.validation import load_building_model
from brickhouse.geometry import generate_building_geometry
from brickhouse.bricks.building_layout import generate_building_brick_shell
from brickhouse.bricks.spatial import generate_spatial_brick_shell
from brickhouse.bricks.windows import generate_window_assemblies_with_status
from brickhouse.bricks.facade_details import generate_prototype_window_reveals
from brickhouse.bricks.brick_model import generate_brick_model
from brickhouse.bricks.bom import generate_bom
from brickhouse.bricks.export import create_export_bundle, export_bundle_json

ROOT=Path(__file__).resolve().parents[1]; OUT=Path("/tmp/deep-bay-proof")
MODEL={"schema_version":"0.1","id":"deep-bay-proof","name":"Deep bay proof","building_type":"house","units":"m","volumes":[{"id":"main","shape":"rectangular_prism","position":{"x":0,"y":0,"z":0},"width":5.0,"depth":1.5,"height":3.0,"floors":1,"source":{"kind":"user_provided","confidence":1.0}}],"openings":[{"id":"window","type":"window","volume_id":"main","facade":"front","offset_horizontal":2.0,"offset_vertical":0.8,"width":1.0,"height":1.2,"source":{"kind":"user_provided","confidence":1.0}}],"roofs":[],"appearance":{"walls":{"color":"beige"},"roof":{"color":"gray"},"frames":{"color":"white"}},"metadata":{"created_from":"synthetic","notes":"Generic LEGO representation prototype; one-stud recess is not architectural metric truth"}}
def build(recess):
 OUT.mkdir(parents=True,exist_ok=True); p=OUT/"model.json";p.write_text(json.dumps(MODEL));b=load_building_model(p);g=generate_building_geometry(b);shell=generate_building_brick_shell(g,20);sp=generate_spatial_brick_shell(shell);wins,_,_=generate_window_assemblies_with_status(b,shell,prototype_recess_studs=recess);details=generate_prototype_window_reveals(b,shell) if recess else [];m=generate_brick_model(sp,None,details,wins);bundle=create_export_bundle(m,generate_bom(m),appearance=b.appearance);export_bundle_json(bundle,OUT/("after.json" if recess else "before.json"))
if __name__=="__main__": build(int(sys.argv[1]))
