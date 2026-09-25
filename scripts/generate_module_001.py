"""Generate the first progressive BOLDÜNGO module: coarse main-house mass only."""
import json
from pathlib import Path
from brickhouse.bricks.bom import generate_bom
from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.catalog import create_m0_brick_catalog
from brickhouse.bricks.export import BrickExportBundle, BrickExportFidelityIssue

X, Y, COURSES = 24, 20, 15
parts=[]
i=1
def add(pid,x,y,z,rot,facade):
    global i
    parts.append(BrickModelPart(placement_id=f"module-001-{i:06d}",part_id=pid,category="brick",component="wall",x_studs=x,y_studs=y,z_plates=z,rotation_quarter_turns=rot,facade=facade))
    i+=1
for course in range(COURSES):
    z=course*3
    for x in (0,8,16):
        add("BRICK_1X8",x,0,z,1,"front")
        add("BRICK_1X8",x,Y-1,z,1,"rear")
    for y,pid in ((1,"BRICK_1X8"),(9,"BRICK_1X6"),(15,"BRICK_1X4")):
        add(pid,0,y,z,0,"left")
        add(pid,X-1,y,z,0,"right")

catalog=create_m0_brick_catalog()
for p in parts:
    catalog.get(p.part_id)
model=BrickModel(building_id="real-house-progressive",volume_id="module-001-main-mass",width_studs=X,depth_studs=Y,height_plates=COURSES*3,parts=parts)
bundle=BrickExportBundle(building_id=model.building_id,volume_id=model.volume_id,brick_model=model,bom=generate_bom(model),fidelity_issues=[BrickExportFidelityIssue(code="PROVISIONAL_SCALE",severity="warning",object_id=model.volume_id,message="MODULE 001 is a deliberately coarse provisional-scale reference mass; openings, roof and adjacent structures are deferred.")])
out=Path(__file__).resolve().parents[1]/"frontend"/"module-001-export.json"
out.write_text(json.dumps(bundle.model_dump(mode="json"),indent=2)+"\n",encoding="utf-8")
print(f"{out}: {len(parts)} M0 parts, {X}x{Y} studs, {COURSES*3} plates")
