"""032: auditable classification of unsupported GUIDED-004 pieces.

Connectivity is not clutch strength. Never count roof solids as orthogonal
stud supports and never synthesize a visible chimney bracket.
"""
from __future__ import annotations

def classify_guided004_supports(model, audit):
    ids = set(audit["unsupported_placement_ids"])
    groups = audit["component_map"]
    main = max(groups, key=lambda group: group["pieces"])
    main_id = main["id"]
    owner = {}
    for group in groups:
        for placement in group["unsupported"]:
            owner[placement] = group["id"]
    rows = []
    for pid in sorted(ids):
        group = owner.get(pid)
        if group == main_id:
            classification = "A_CONNECTED_VIA_STUD_PATH"
            reason = "Connected to main orthogonal stud-contact component; clutch strength not certified"
        elif group:
            classification = "C_STABILITY_UNDETERMINED"
            reason = "Connected within isolated chimney island, no demonstrated stud path to house"
        else:
            classification = "C_STABILITY_UNDETERMINED"
            reason = "No verified component assignment"
        rows.append({"placement_id":pid,"class":classification,"component":group,"reason":reason})
    if len(rows) != audit["unsupported_parts"]:
        raise AssertionError("032_UNSUPPORTED_CLASSIFICATION_INCOMPLETE")
    chimney_groups = [g for g in groups if any("scene-chimney" in p for p in g["unsupported"])]
    if len(chimney_groups) != 2:
        raise AssertionError("032_CHIMNEY_ISLAND_COUNT_CHANGED")
    attempts = {
      "west_metal": [
        "Direct vertical stud path: chimney starts z30; wall nearby occupies x16 while chimney starts x19, leaving an open lateral gap",
        "Hidden cross-joint in chimney alone: existing 030b joint connects chimney internally but not the wall",
        "Support via roof: roof has no verified orthogonal stud/underside contact model; roof edits forbidden"
      ],
      "antenna": [
        "Direct vertical stud path: chimney starts z90; no orthogonal wall support beneath its x45..48,y30..33 footprint",
        "Internal cross-joint: existing 030b joints connect antenna chimney internally but not to the main house",
        "Roof-supported interface: requires certified sloped-roof underside/contact and insertion; roof edits forbidden"
      ]
    }
    return {
      "unsupported_direct_count":len(rows),
      "supported_via_connection_path":sum(r["class"].startswith("A_") for r in rows),
      "truly_floating":sum(r["class"].startswith("B_") for r in rows),
      "stability_undetermined":sum(r["class"].startswith("C_") for r in rows),
      "classifications":rows,
      "chimney_metal_connected":False,
      "chimney_antenna_connected":False,
      "chimney_attempts_and_blockers":attempts,
      "mechanical_certification":"NOT_CERTIFIED"
    }
