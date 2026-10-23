"""BOLDUNGO-LEGO2-025: bounded real-house corner prototype, no scene edits.

Uses GUIDED-004's regenerated BrickModel, not an invented wall. Compares
existing partition against course-first catalog tiling of the SAME voxels.
This is a vertical stud-contact preflight, not a clutch/insertion certificate.
"""
import json
from collections import defaultdict
from pathlib import Path

MODEL = Path("artifacts/lego2-guided-004/brick-model.json")
REPORT = Path("artifacts/lego2-guided-004/layer-prototype-025.json")
LENGTHS = (8, 6, 4, 3, 2, 1)
REGION = (16, 27, 2, 11, 0, 15)


def footprint(part):
    name = part["part_id"]
    if not name.startswith("BRICK_1X"):
        return None
    n = int(name.split("X")[-1])
    if n not in LENGTHS:
        return None
    w, l = (n, 1) if part["rotation_quarter_turns"] % 2 else (1, n)
    return {(x, y) for x in range(part["x_studs"], part["x_studs"] + w)
            for y in range(part["y_studs"], part["y_studs"] + l)}


def layer_tiling(z, occupied):
    remaining = set(occupied)
    out = []
    # Alternate corner ownership between adjacent courses; a real L joint.
    axes = ("x", "y") if z // 3 % 2 == 0 else ("y", "x")
    for axis in axes:
        line = ([(x, 2) for x in range(16, 27)] if axis == "x"
                else [(16, y) for y in range(2, 11)])
        seq = [p for p in line if p in remaining]
        while seq:
            run = [seq[0]]
            delta = (1, 0) if axis == "x" else (0, 1)
            for pos in seq[1:]:
                if (pos[0] - run[-1][0], pos[1] - run[-1][1]) != delta:
                    break
                run.append(pos)
            n = next(n for n in LENGTHS if n <= len(run))
            piece = set(run[:n])
            assert piece <= remaining
            out.append((z, piece, "BRICK_1X" + str(n)))
            remaining -= piece
            seq = seq[n:]
    assert not remaining, "Prototype region must be an L corner only"
    return out


def metrics(parts):
    parent = list(range(len(parts)))
    unsupported = 0
    vertical_contacts = 0
    def root(i):
        while parent[i] != i:
            i = parent[i]
        return i
    for i, (z, cells, _) in enumerate(parts):
        if z == 0:
            continue
        supports = [j for j, (lower_z, lower_cells, _) in enumerate(parts)
                    if lower_z == z - 3 and cells & lower_cells]
        if not supports:
            unsupported += 1
        for j in supports:
            parent[root(i)] = root(j)
            vertical_contacts += 1
    return dict(pieces=len(parts), connected_components=len({root(i) for i in range(len(parts))}),
                unsupported=unsupported, vertical_stud_contact_pairs=vertical_contacts)


def test_real_corner_with_adjacent_window_layer_tiling():
    assert MODEL.exists(), "CI must generate the real GUIDED-004 export first"
    data = json.loads(MODEL.read_text(encoding="utf-8"))
    existing, occupied = [], defaultdict(set)
    opening_voxels = set()
    for part in data["parts"]:
        cells = footprint(part)
        if cells is None:
            continue
        cells = {(x, y) for x, y in cells
                 if REGION[0] <= x < REGION[1] and REGION[2] <= y < REGION[3]}
        z = part["z_plates"]
        if not cells or not (REGION[4] <= z < REGION[5]) or z % 3:
            continue
        if part.get("opening_id"):
            opening_voxels.update((x, y, z) for x, y in cells)
        if part["component"] == "wall" and part["category"] == "brick":
            existing.append((z, cells, part["part_id"]))
            occupied[z].update(cells)
    assert len(occupied) == 5 and opening_voxels, "Not a real window-adjacent wall corner"
    direct = [p for z, cells in sorted(occupied.items()) for p in layer_tiling(z, cells)]
    source_voxels = {(x, y, z) for z, cells, _ in existing for x, y in cells}
    direct_voxels = {(x, y, z) for z, cells, _ in direct for x, y in cells}
    assert source_voxels == direct_voxels
    assert not (direct_voxels & opening_voxels)
    assert len(direct_voxels) == sum(len(cells) for _, cells, _ in direct), "Collision"
    before, after = metrics(existing), metrics(direct)
    assert after["connected_components"] <= before["connected_components"]
    assert after["unsupported"] <= before["unsupported"]
    assert after["pieces"] < before["pieces"]
    # Both walls must alternate ownership of the corner stud.
    assert any((16, 2) in cells and len(cells) > 1 and (17, 2) in cells for z, cells, _ in direct if z == 0)
    assert any((16, 2) in cells and len(cells) > 1 and (16, 3) in cells for z, cells, _ in direct if z == 3)
    result = {
        "source": str(MODEL), "zone": "front-left real wall corner near east-rdc-window-left",
        "bounds": REGION, "opening_voxels_protected": len(opening_voxels),
        "occupied_stud_cells_preserved": len(source_voxels),
        "current": before, "layer_first": after,
        "collision_voxels": 0, "catalog": ["BRICK_1X" + str(n) for n in LENGTHS],
        "staggered_corner": True,
        "vertical_insertion": "GEOMETRIC_PREFLIGHT_ONLY",
        "clutch_and_full_assembly": "NOT_CERTIFIED",
        "limitation": "Clipped test region; no full roof, terraces, or chimney proof",
    }
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("LAYER_PROTOTYPE_025=" + json.dumps(result, sort_keys=True))
