"""031: verify real concrete/timber cross-seam, not a disconnected prototype."""
import json
from pathlib import Path

ROOT = Path("artifacts/lego2-guided-004")
PREFIX = "guided004-031:concrete-timber-cross-joint:"


def test_real_house_cross_seam_volume_and_inventory():
    model = json.loads((ROOT / "brick-model.json").read_text())
    inventory = json.loads((ROOT / "inventory.json").read_text())
    viewer = json.loads((ROOT / "viewer-export.json").read_text())
    parts = model["parts"]
    joints = [p for p in parts if p["placement_id"].startswith(PREFIX)]
    assert len(joints) == 6
    assert len(parts) == inventory["total_bricks"] == viewer["bom"]["total_parts"]
    assert inventory["physical_audit"]["collision_voxel_overlaps"] == 0
    assert inventory["physical_audit"]["connected_components_orthogonal_stud_contact"] <= 4
    assert len(parts) == 1883
    ids = {p["placement_id"] for p in parts}
    assert "scene-platform:south-concrete-platform:y_max:parapet:00427" not in ids
    assert "scene-platform:south-timber-deck-main:board:00025" not in ids
    assert {p["placement_id"] for p in joints} <= {
        p["placement_id"] for p in viewer["brick_model"]["parts"]}
    steps = viewer["assembly_plan"]["steps"]
    covered = {pid for step in steps for pid in step["placement_ids"]}
    assert {p["placement_id"] for p in joints} <= covered
    assert inventory["mechanical_certification"] == "NOT_CERTIFIED"
