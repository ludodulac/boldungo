"""032: verify the 19 support classifications from the actual regenerated house."""
import json
from pathlib import Path

def test_guided004_032_support_classification():
    root = Path("artifacts/lego2-guided-004")
    inventory = json.loads((root/"inventory.json").read_text())
    model = json.loads((root/"brick-model.json").read_text())
    audit = inventory["physical_audit"]
    report = inventory["support_classification_032"]
    assert len(model["parts"]) == inventory["total_bricks"] == 1890
    assert audit["collision_voxel_overlaps"] == 0
    assert audit["connected_components_orthogonal_stud_contact"] == 3
    assert report["unsupported_direct_count"] == audit["unsupported_parts"] == 19
    assert report["supported_via_connection_path"] == 15
    assert report["truly_floating"] == 0
    assert report["stability_undetermined"] == 4
    assert {p["placement_id"] for p in report["classifications"]} == set(audit["unsupported_placement_ids"])
    assert report["chimney_metal_connected"] is False
    assert report["chimney_antenna_connected"] is False
    assert len(report["chimney_attempts_and_blockers"]["west_metal"]) == 3
    assert len(report["chimney_attempts_and_blockers"]["antenna"]) == 3
    assert report["mechanical_certification"] == "NOT_CERTIFIED"
