"""GUIDED-004 buildability map from the REAL generator export, not scene geometry.

Usage: python scripts/audit_guided004_constructibility_043.py artifacts/lego2-guided-004
Reads the existing physical audit; does NOT certify physical clutch.
"""
import collections
import json
import pathlib
import sys

def analyze(folder):
    folder = pathlib.Path(folder)
    parts = json.loads((folder / "brick-model.json").read_text())["parts"]
    audit = json.loads((folder / "inventory.json").read_text())["physical_audit"]
    def zone(p):
        c, pid = p["category"], p["placement_id"]
        if c in ("roof_tile", "ridge_tile"): return "roof"
        if "chimney" in pid: return "chimneys"
        if "stair" in pid: return "stairs"
        if "platform" in pid or "concrete-timber" in pid or c in ("concrete", "timber", "plate"): return "decks_terraces"
        if c == "window_pane": return "opening_details"
        return "walls_and_masonry"
    groups = collections.defaultdict(list)
    for p in parts: groups[zone(p)].append(p)
    unsupported = set(audit["unsupported_placement_ids"])
    zones = {}
    for name, group in sorted(groups.items()):
        ids = {p["placement_id"] for p in group}
        zones[name] = {
            "pieces": len(group),
            "references": dict(collections.Counter(p["part_id"] for p in group)),
            "unsupported_by_existing_audit": len(ids & unsupported),
            "unsupported_ids": sorted(ids & unsupported),
            "roof_interfaces_unverified": sum(p["category"] in ("roof_tile", "ridge_tile") for p in group),
            "individual_stud_tube_connections": "NOT_COUNTED_BY_EXISTING_AUDIT",
        }
    assert sum(v["pieces"] for v in zones.values()) == len(parts)
    assert sum(v["unsupported_by_existing_audit"] for v in zones.values()) == audit["unsupported_parts"]
    return {
        "total_parts": len(parts),
        "zones": zones,
        "global_collision_voxel_overlaps": audit["collision_voxel_overlaps"],
        "global_orthogonal_parts_checked": audit["orthogonal_parts_checked"],
        "global_orthogonal_connected_components": audit["connected_components_orthogonal_stud_contact"],
        "global_component_sizes": audit["component_sizes_descending"],
        "roof_unverified": audit["roof_parts_unverified"],
        "physical_certification": "NOT_CERTIFIED",
        "warning": "Existing audit counts geometric support/contact, not real-world stability or verified individual stud/tube engagements.",
    }

if __name__ == "__main__":
    print(json.dumps(analyze(sys.argv[1]), indent=2, ensure_ascii=False))
