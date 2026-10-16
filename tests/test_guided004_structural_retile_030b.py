"""030B real GUIDED-004 structural retile, not an isolated prototype."""
import json
from pathlib import Path

ROOT = Path("artifacts/lego2-guided-004")
PREFIX = "guided004-030b:"


def test_real_export_contains_all_three_volume_preserving_cross_joint_repairs():
    model = json.loads((ROOT / "brick-model.json").read_text())
    inventory = json.loads((ROOT / "inventory.json").read_text())
    viewer = json.loads((ROOT / "viewer-export.json").read_text())
    parts = model["parts"]
    new = [p for p in parts if p["placement_id"].startswith(PREFIX)]
    assert len(new) == 7
    assert len(parts) == 1890
    assert inventory["total_bricks"] == 1890
    audit = inventory["physical_audit"]
    assert audit["collision_voxel_overlaps"] == 0
    assert audit["connected_components_orthogonal_stud_contact"] <= 6
    assert audit["unsupported_parts"] <= 19
    assert audit["roof_parts_unverified"] == 420
    assert {p["placement_id"] for p in new} <= {
        p["placement_id"] for p in viewer["brick_model"]["parts"]
    }
    steps = viewer["assembly_plan"]["steps"]
    covered = {pid for step in steps for pid in step["placement_ids"]}
    assert {p["placement_id"] for p in new} <= covered
    assert viewer["bom"]["total_parts"] == len(parts)
    assert len(inventory["source_openings"]) >= len(inventory["openings_with_parts"])
    assert inventory["mechanical_certification"] == "NOT_CERTIFIED"
    print("GUIDED004_030B_REAL_EXPORT=PASS")

