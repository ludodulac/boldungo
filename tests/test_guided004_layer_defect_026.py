"""026: Falsifiable layer-first experiment on two disconnected real deck boards.

No scene mutation: exact same occupied voxels. Tests whether retiling a
single-layer deck can create a vertical stud connection (it cannot).
"""
import json
from pathlib import Path

MODEL = Path("artifacts/lego2-guided-004/brick-model.json")
PREFIX = "scene-platform:south-timber-deck-main:board:"
TARGETS = (PREFIX + "00007", PREFIX + "00013")


def _cells(p):
    return {(x, y, z) for x in range(p["x_studs"], p["x_studs"] + p["width_studs"])
            for y in range(p["y_studs"], p["y_studs"] + p["length_studs"])
            for z in range(p["z_plates"], p["z_plates"] + p.get("height_plates", 3))}


def _components(pieces):
    parent = list(range(len(pieces)))
    def root(i):
        while i != parent[i]:
            i = parent[i]
        return i
    edges = 0
    for i, a in enumerate(pieces):
        for j, b in enumerate(pieces[:i]):
            if a["z_plates"] + a["height_plates"] == b["z_plates"] or b["z_plates"] + b["height_plates"] == a["z_plates"]:
                axy = {(x, y) for x, y, _ in _cells(a)}
                bxy = {(x, y) for x, y, _ in _cells(b)}
                if axy & bxy:
                    parent[root(i)] = root(j)
                    edges += 1
    return len({root(i) for i in range(len(pieces))}), edges


def test_real_disconnected_deck_layer_first_cannot_fix_without_new_course():
    data = json.loads(MODEL.read_text(encoding="utf-8"))
    source = [p for p in data["parts"] if p["placement_id"] in TARGETS]
    assert len(source) == 2, "Exact defective GUIDED-004 boards not found"
    assert all(p["part_id"] == "BRICK_2X8" and p["z_plates"] == 36 for p in source)
    old = [dict(p, height_plates=3) for p in source]
    old_cells = [_cells(p) for p in old]
    assert not old_cells[0] & old_cells[1]
    assert max(p["x_studs"] + p["width_studs"] for p in old) == 9
    # Direct layer-first tiling: four catalog 2x4 bricks, each with a
    # transverse joint at y=21. No volume is added and no opening is filled.
    new = []
    for p in old:
        for offset in (0, 4):
            new.append(dict(p, part_id="BRICK_2X4",
                            placement_id=p["placement_id"] + f":layer:{offset}",
                            y_studs=p["y_studs"] + offset, length_studs=4))
    assert set().union(*old_cells) == set().union(*(_cells(p) for p in new))
    assert sum(len(_cells(p)) for p in new) == len(set().union(*old_cells))
    assert _components(old) == (2, 0)
    assert _components(new) == (4, 0)
    # A single 3-plate-high course cannot generate vertical studs by
    # staggering joints in the same z plane. Layer-first is NOT validated.
    report = {
        "zone": "real south-timber-deck-main boards 00007 and 00013",
        "ids": list(TARGETS), "z_plates": 36,
        "old": {"bricks": 2, "components": 2, "unsupported": 2, "collisions": 0},
        "layer_first": {"bricks": 4, "components": 4, "unsupported": 4, "collisions": 0},
        "occupied_volume_preserved": True, "openings_preserved": True,
        "vertical_stud_contacts_old": 0, "vertical_stud_contacts_new": 0,
        "assembly_feasibility": "NO_VERTICAL_CONNECTION",
        "result": "FAIL_TO_RECONNECT",
        "cause": "Both deck boards occupy only z=36..39. No upper course exists to bridge joints; same-height lateral adjacency is not a LEGO stud connection.",
        "recommendation": "Do not apply layer-first to this single-course deck without an architecturally authorized cross-layer connection.",
    }
    out = Path("artifacts/lego2-guided-004/layer-defect-prototype-026.json")
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("LAYER_DEFECT_PROTOTYPE_026=" + json.dumps(report, sort_keys=True))
