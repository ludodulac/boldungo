from brickhouse.scene.architectural_constraints import ArchitecturalConstraint,ConstraintKind,NormalizedRect,evaluate_normalized_constraints
from brickhouse.scene.models import ArchitecturalScene
import json
from pathlib import Path

def test_real_house_v03_prelego_constraints():
    scene=ArchitecturalScene.model_validate_json(Path("frontend/benchmarks/real-house-5/neutral-five-photo-scene-v0.3.json").read_text())
    w=scene.volumes[0].width.value; h=scene.volumes[0].height.value
    rects={}
    for o in scene.openings:
        if o.facade.value=="front":
            rects[o.id]=NormalizedRect(x0=o.offset_horizontal/w,x1=(o.offset_horizontal+o.width)/w,z0=o.offset_vertical/h,z1=(o.offset_vertical+o.height)/h)
    constraints=[
      ArchitecturalConstraint(id="left-bay-upper-middle",kind=ConstraintKind.APPROX_ALIGNED_X,subject_id="front-opening-1",object_id="front-opening-3",tolerance=.03,statement="upper/middle left bay aligned"),
      ArchitecturalConstraint(id="right-bay-upper-middle",kind=ConstraintKind.APPROX_ALIGNED_X,subject_id="front-opening-2",object_id="front-opening-4",tolerance=.03,statement="upper/middle right bay aligned"),
      ArchitecturalConstraint(id="upper-above-middle-left",kind=ConstraintKind.ABOVE,subject_id="front-opening-1",object_id="front-opening-3",tolerance=0,statement="upper above middle"),
      ArchitecturalConstraint(id="middle-above-low-left",kind=ConstraintKind.ABOVE,subject_id="front-opening-3",object_id="front-opening-5",tolerance=0,statement="middle above low")
    ]
    report=evaluate_normalized_constraints(rects,constraints)
    assert not report.violations, report.model_dump()
    assert scene.platforms[1].position.x < 0
    assert scene.stairs[0].start.y==scene.stairs[0].end.y
    assert scene.stairs[1].start.x==scene.stairs[1].end.x
