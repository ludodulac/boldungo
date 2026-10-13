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


def test_each_concealed_bond_has_stud_contact_path_to_existing_post():
    from brickhouse.bricks.catalog import standard_orthogonal_definitions

    model = json.loads((ROOT / "brick-model.json").read_text())
    definitions = standard_orthogonal_definitions()
    deck = [p for p in model["parts"]
            if p["placement_id"].startswith("scene-platform:south-timber-deck")
            and p["part_id"] in definitions]
    def box(p):
        d = definitions[p["part_id"]]
        w, l = d.footprint(p["rotation_quarter_turns"])
        x, y, z = p["x_studs"], p["y_studs"], p["z_plates"]
        return (x, y, z, x + w, y + l, z + d.height_plates)
    boxes = [box(p) for p in deck]
    parent = list(range(len(deck)))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for i, a in enumerate(boxes):
        for j in range(i + 1, len(deck)):
            b = boxes[j]
            vertical = a[5] == b[2] or b[5] == a[2]
            horizontal = a[0] < b[3] and b[0] < a[3] and a[1] < b[4] and b[1] < a[4]
            if vertical and horizontal:
                parent[find(j)] = find(i)
    post_id = "scene-platform:south-timber-deck-main:support-solution:timber-post-east:0033:00022"
    by_id = {p["placement_id"]: i for i, p in enumerate(deck)}
    root = find(by_id[post_id])
    bonds = [pid for pid in by_id if pid.startswith(PREFIX)]
    assert len(bonds) == 8
    assert all(find(by_id[pid]) == root for pid in bonds)
    assert all(find(by_id[pid]) == root for pid in by_id if ":board:" in pid)
    # This proves a stud-contact graph path, NOT mechanical load resistance.
