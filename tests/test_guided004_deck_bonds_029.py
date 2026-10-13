"""029: measured integration contract for real GUIDED-004 under-deck bonds."""
import json
from pathlib import Path

ROOT = Path("artifacts/lego2-guided-004")
PREFIX = "scene-platform:south-timber-deck-main:hidden-cross-bond-029:"


def test_real_house_contains_eight_catalogue_bonds_with_no_new_collisions():
    model = json.loads((ROOT / "brick-model.json").read_text())
    viewer = json.loads((ROOT / "viewer-export.json").read_text())
    inventory = json.loads((ROOT / "inventory.json").read_text())
    parts = {p["placement_id"]: p for p in model["parts"]}
    bonds = {pid: part for pid, part in parts.items() if pid.startswith(PREFIX)}
    assert len(bonds) == 8
    assert len(parts) == 1879
    assert inventory["total_bricks"] == 1879
    audit = inventory["physical_audit"]
    assert audit["collision_voxel_overlaps"] == 0
    assert audit["connected_components_orthogonal_stud_contact"] <= 12
    assert all(part["part_id"] in ("PLATE_1X3", "PLATE_1X6", "PLATE_1X8") for part in bonds.values())
    assert all(part["z_plates"] == 35 and part["height_plates"] == 1 for part in bonds.values())
    assert set(bonds) <= {p["placement_id"] for p in viewer["brick_model"]["parts"]}
    assert viewer["bom"]["total_parts"] == len(parts)
    all_steps = viewer["assembly_plan"]["steps"]
    seq = {pid: step["sequence"] for step in all_steps for pid in step["placement_ids"]}
    assert set(bonds) <= set(seq)
    for pid in bonds:
        assert "maintenir provisoirement" in next(s["title"] for s in all_steps if pid in s["placement_ids"])
    # All deck boards at the top course are installed after the concealed plates.
    board_steps = [seq[pid] for pid, part in parts.items()
                   if pid.startswith("scene-platform:south-timber-deck") and ":board:" in pid
                   and part["z_plates"] == 36]
    assert max(seq[pid] for pid in bonds) < min(board_steps)
    assert set(inventory["source_openings"]) >= set(inventory["openings_with_parts"])
    assert inventory["mechanical_certification"] == "NOT_CERTIFIED"
    print("GUIDED004_029_INTEGRATION=PASS bonds=8 parts=1879")
