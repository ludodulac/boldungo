from pathlib import Path
from brickhouse.scene import ArchitecturalScene

ROOT=Path(__file__).resolve().parents[2]
SCENE=ROOT/"frontend/benchmarks/real-house-5/five-photo-scene-candidate-v0.4.json"

def test_geometry_fidelity_constraints_survive_scene():
    s=ArchitecturalScene.model_validate_json(SCENE.read_text())
    assert s.roofs[0].type.value=="gable"
    assert len(s.stairs)==2
    assert s.stairs[0].end==s.stairs[1].start
    assert s.stairs[0].start.y==s.stairs[0].end.y
    assert s.stairs[1].start.x==s.stairs[1].end.x
    assert any(x.id=="deck-facade-end" for x in s.boundary_constraints)
    assert any(
        x.object_id=="chimney-house-1"
        and x.left_right=="left_of_front_centerline"
        and x.front_back=="rear_portion"
        for x in s.roof_plan_positions
    )
    deck=next(p for p in s.platforms if p.id=="platform-timber-1")
    landing=next(p for p in s.platforms if p.id=="platform-massive-1")
    assert abs((deck.position.y+deck.depth)-landing.position.y)<1e-9
    assert s.terrain and any(
        p.facade.value=="right"
        and p.end_elevation is not None
        and p.start_elevation is not None
        and p.end_elevation>p.start_elevation
        for p in s.terrain.profiles
    )
    assert not any(v.id=="lower_exterior_volume" for v in s.volumes)
