from pathlib import Path
from brickhouse.scene import ArchitecturalScene
ROOT=Path(__file__).resolve().parents[1]
SCENE=ROOT/"frontend/benchmarks/real-house-5/five-photo-scene-candidate-v0.3.json"

def test_geometry_fidelity_constraints_survive_scene():
    s=ArchitecturalScene.model_validate_json(SCENE.read_text())
    assert s.roofs[0].type.value=="gable"
    assert len(s.stairs)==2
    assert s.stairs[0].end==s.stairs[1].start
    assert any(x.id=="deck-facade-end" for x in s.boundary_constraints)
    assert any(x.object_id=="chimney-house-1" for x in s.roof_plan_positions)
    assert s.terrain and any(p.facade.value=="right" and p.end_elevation>p.start_elevation for p in s.terrain.profiles)
    assert not any(v.id=="lower_exterior_volume" for v in s.volumes)
