"""MAISON-3: finish the CURRENT canonical east/front RDC (one operation).

Input is immutable MAISON-2 139-placement LDraw and untouched GUIDED-004 Scene.
Select ALL remaining real front facade wall placements at the canonical grid,
plus any existing lower-right French-door symbolic opening placements.
Only inspect new mechanical interfaces; do not re-audit MAISON-1/2.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_guided004_corner_maison1 as m1
import export_guided004_lego as canonical
from brickhouse.scene import ArchitecturalScene
from brickhouse.bricks.brick_model import BrickModel
from brickhouse.bricks.geometry_adapter import CANONICAL_LDRAW_PARTS
from lego_geometry_engine import LDrawLibrary, find_connections, instantiate, transform_from_ldraw

SCENE = ROOT / "frontend/data/boldungo2-guided-004-real-scene.json"
M2 = ROOT / "missions/MAISON2/generated"
DOOR = "east-rdc-french-door-right"
WINDOW = "east-rdc-window-left"
EXPECTED_M2 = 139


def parse_maison2_original(raw):
    rows = [l for l in raw.splitlines() if l.startswith("1 ")]
    if len(rows) != EXPECTED_M2:
        raise AssertionError("M3_PRESERVED_LDRAW_NOT_139")
    ids, experiments = {}, []
    current = None
    for line in raw.splitlines():
        if line.startswith("0 // CANONICAL-UNCHANGED ") or line.startswith("0 // CANONICAL-MAISON2 "):
            current = ("canonical", line.split()[3], "")
        elif line.startswith("0 // EXPERIMENTAL-ADDED "):
            pieces = line.split()
            current = ("experimental", pieces[3], pieces[4].split("=", 1)[1])
        elif line.startswith("1 "):
            if current is None:
                raise AssertionError("M3_OLD_LDRAW_MISSING_PROVENANCE")
            if current[0] == "canonical":
                ids[current[1]] = line
            else:
                item = line.split()
                part = item[-1].split(".")[0]
                if part not in m1.KNOWN:
                    raise AssertionError("M3_UNKNOWN_OLD_SUPPORT:" + part)
                w, d, h = m1.KNOWN[part]
                x = round(float(item[2]) / 20 - w / 2)
                y = round(float(item[4]) / 20 - d / 2)
                z = round(-float(item[3]) / 8 - h)
                experiments.append(m1.Add(current[1], part, current[2], x, y, z, w, d, h,
                                          color=int(item[1]),
                                          matrix=tuple(int(float(v)) for v in item[5:14])))
            current = None
    if len(ids) != 104 or len(experiments) != 35:
        raise AssertionError("M3_MAISON2_104_PLUS_35_NOT_PRESERVED")
    return rows, ids, experiments


def within_rdc_front(p, x0, xend, front_y, top):
    box = m1.gridbox(p)
    return (
        p.facade == "front" and
        x0 <= box[0] and box[3] <= xend and
        box[1] == front_y and box[4] == front_y + 1 and
        0 <= box[2] and box[5] <= top
    )


def fresh_interfaces(old_source, old_supports, new, root):
    """New vs old/new grid volumes and ONLY the new explicit stud engagements."""
    existing = {p.placement_id: (m1.gridbox(p), m1._ldraw_canonical(p)) for p in old_source}
    existing.update({a.name: (a.bbox(), m1._ldraw_experiment(a)) for a in old_supports})
    additions = {p.placement_id: (m1.gridbox(p), m1._ldraw_canonical(p)) for p in new}
    grid = {**existing, **additions}
    coll = []
    for n, (b, _) in additions.items():
        for k, (c, _) in grid.items():
            if k != n and m1.solid_overlap(b, c) and n < k if k in additions else (k != n and m1.solid_overlap(b, c)):
                coll.append([n, k])
    # Above conditional only records the new/new pair once.
    library = LDrawLibrary(root)
    cache = {}
    def inst(ident):
        if ident not in cache:
            tok = grid[ident][1].split()
            cache[ident] = instantiate(library.load_part(tok[-1]), ident,
                transform_from_ldraw([float(x) for x in tok[2:14]]))
        return cache[ident]
    edges, unsupported, sides = [], [], []
    for ident, (box, _) in additions.items():
        supports = [(name, m1.touching(box, other))
                    for name, (other, _) in grid.items() if name != ident and m1.touching(box, other) > 0]
        if not supports:
            unsupported.append(ident)
        for name, cells in supports:
            conn = find_connections(inst(ident), inst(name))
            edges.append({"upper": ident, "lower": name, "stud_cells": cells,
                          "connector_count": len(conn), "recognized": bool(conn),
                          "vertical_insertion": "NOT_PROVEN"})
        for name, (other, _) in existing.items():
            if name.startswith("M1-"):
                continue
            if (
                (box[1], box[4]) == (other[1], other[4])
                and (box[0] == other[3] or box[3] == other[0])
                and min(box[5], other[5]) > max(box[2], other[2])
            ):
                sides.append({
                    "new": ident,
                    "old": name,
                    "result": "SIDE_CONTACT_NOT_STUD_JOIN"
                })
    return {
        "new_body_collisions_count": len(coll), "new_body_collision_pairs": coll,
        "new_support_edges": len(edges),
        "new_support_edges_with_engine_connectors": sum(v["recognized"] for v in edges),
        "new_support_edges_details": edges,
        "new_without_underlying_stud_bearing": unsupported,
        "lateral_seam_contacts": sides,
        "old_maison1_2_links_not_retested": True,
        "full_mesh_collision_audit": "NOT_PERFORMED",
        "continuous_insertion": "NOT_PROVEN",
        "mechanical_strength": "NOT_CERTIFIED"
    }


def image_m3(source, old_supports, new, scene, x0, y0, studs_per_m):
    """Reuse existing schematic renderer, overlay the observed door as a *guide*, not a brick."""
    svg = m1._drawing(source + new, old_supports,
                      "BOLDÜNGO MAISON-3 - facade EST RDC complete (Scene GUIDED-004)")
    svg = svg.replace('width="1440" height="900" viewBox="0 0 1440 900"',
                      'width="1800" height="900" viewBox="0 0 1800 900"')
    svg = svg.replace("EST = avant (fenêtre au RDC) · SUD = côté gauche",
                      "EST = facade avant, fenetre et porte-fenetre · SUD = cote gauche")
    door = next(o for o in scene.openings if o.id == DOOR)
    x1 = x0 + door.offset_horizontal * studs_per_m
    x2 = x1 + door.width * studs_per_m
    z1 = door.offset_vertical * studs_per_m * 3
    z2 = z1 + door.height * studs_per_m * 3
    # Match the original 3D isometric projection; blueprint marker only.
    project = lambda x, y, z: (720 + (x - y) * 15, 500 + (x + y) * 5.5 - z * 11)
    outline = " ".join(f"{x:.1f},{y:.1f}" for x,y in
                       (project(x1,y0,z1),project(x2,y0,z1),
                        project(x2,y0,z2),project(x1,y0,z2)))
    note = (f'<polygon points="{outline}" fill="none" stroke="#c02b7b" '
            'stroke-width="4" stroke-dasharray="9 7"/>'
            '<text x="22" y="112" font-family="Arial" font-size="18" fill="#92215c">'
            'Contour magenta = emplacement de la porte-fenetre dans la Scene, '
            'PAS un vitrage LEGO ajoute.</text>'
            '<text x="22" y="139" font-family="Arial" font-size="17" fill="#285377">'
            '139 placements MAISON-2 inchanges ; ouverture en briques proxy seulement si deja dans le modele source.</text>')
    return svg.replace("</svg>", note + "\n</svg>")


def run(out, ldraw_root):
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    old_raw = (M2 / "MAISON2-FRAGMENT-AGRANDI.ldr").read_text(encoding="utf8")
    old_sha = hashlib.sha256(old_raw.encode("utf8")).hexdigest()
    old_rows, old_ids, old_supports = parse_maison2_original(old_raw)
    previous = json.loads((M2 / "MAISON2-PROVENANCE.json").read_text())
    if hashlib.sha256(SCENE.read_bytes()).hexdigest() != previous["scene_sha256"]:
        raise AssertionError("M3_SCENE_CANONICAL_HASH_CHANGED")
    scene = ArchitecturalScene.model_validate_json(SCENE.read_bytes())
    if (scene.volumes[0].width.value, scene.volumes[0].depth.value) != (9.3, 8.2):
        raise AssertionError("M3_METRIC_INPUT_CHANGED")
    right_door = next((o for o in scene.openings if o.id == DOOR), None)
    left_window = next((o for o in scene.openings if o.id == WINDOW), None)
    if not right_door or not left_window:
        raise AssertionError("M3_SOURCE_FRONT_RDC_OPENINGS_MISSING")

    # Same canonical exporter as MAISON-2; materialized once in separate output.
    original_source, original_output = canonical.SOURCE, canonical.OUTPUT
    try:
        canonical.SOURCE = SCENE
        canonical.OUTPUT = out / "ISOLATED-CANONICAL-1890"
        inv = canonical.generate()
    finally:
        canonical.SOURCE, canonical.OUTPUT = original_source, original_output
    if inv["total_bricks"] != 1890 or hashlib.sha256(SCENE.read_bytes()).hexdigest() != previous["scene_sha256"]:
        raise AssertionError("M3_CANONICAL_EXPORT_CHANGED")
    model = BrickModel.model_validate_json(
        (out / "ISOLATED-CANONICAL-1890" / "brick-model.json").read_bytes())
    source_by_id = {p.placement_id: p for p in model.parts}
    if any(n not in source_by_id or m1._ldraw_canonical(source_by_id[n]) != line
           for n, line in old_ids.items()):
        raise AssertionError("M3_139_PLACEMENTS_MUST_REMAIN_EXACT")
    old_source = [source_by_id[k] for k in old_ids]
    x0, y0 = previous["bay_old_wall_end_studs"] - 20, 2
    # These are *derived*, not a made-up new house measurement:
    x0 = min(m1.gridbox(p)[0] for p in old_source
             if p.component == "wall" and p.facade == "front")
    y0 = min(m1.gridbox(p)[1] for p in old_source
             if p.component == "wall" and p.facade == "front")
    end = x0 + model.width_studs
    top = (model.height_plates // scene.volumes[0].floors - 4) // 3 * 3 + 3
    if previous["bay_new_wall_end_studs"] != 44 or end <= 44 or top != 39:
        raise AssertionError("M3_SCENE_ENVELOPE_UNEXPECTED")
    candidates = [
        p for p in model.parts
        if (p.component == "wall" or
            (p.component == "facade_detail" and p.opening_id in {WINDOW, DOOR}))
        and within_rdc_front(p, x0, end, y0, top)
    ]
    new = sorted([p for p in candidates if p.placement_id not in old_ids],
                 key=lambda p:(p.z_plates,p.x_studs,p.y_studs,p.placement_id))
    if not new:
        raise AssertionError("M3_REAL_FACADE_EXTENSION_EMPTY")
    if not any(m1.gridbox(p)[0] >= 44 for p in new):
        raise AssertionError("M3_FACADE_DID_NOT_REACH_FINAL_SECTOR")
    present = {p.placement_id for p in old_source + new}
    if {p.placement_id for p in candidates} - present:
        raise AssertionError("M3_CANONICAL_FRONT_RDC_NOT_COMPLETE")

    # DELIVER FIRST: original 139 placements used unchanged, append only canonical.
    old_lines = old_raw.splitlines()
    if old_lines[-1] != "0 NOFILE":
        raise AssertionError("M3_OLD_MODEL_TRAILER")
    appended = []
    for p in new:
        appended += [f"0 // CANONICAL-MAISON3 {p.placement_id} component={p.component} opening={p.opening_id or '-'}",
                     m1._ldraw_canonical(p)]
    final_raw = "\n".join(old_lines[:-1] + [
        "0 // MAISON-3: east/front RDC to the right edge, original Scene coordinates.",
        "0 // Openings, if represented by source BRICK_1X1 proxies, are NOT genuine glazing.",
        "0 // Previous 139 placements preserved in precisely the same order.",
    ] + appended + ["0 NOFILE", ""])
    final_rows = [x for x in final_raw.splitlines() if x.startswith("1 ")]
    if final_rows[:139] != old_rows or len(final_rows) != 139 + len(new):
        raise AssertionError("M3_PREVIOUS_139_ROWS_LOST")
    (out / "MAISON3-FACADE-EST-RDC.ldr").write_text(final_raw)
    (out / "MAISON3-VUE-3D-SCHEMATIQUE.svg").write_text(
        image_m3(old_source, old_supports, new, scene, x0, y0, model.width_studs / 9.3))

    # Diagnostics apply ONLY to the new bricks and their interfaces.
    checks = fresh_interfaces(old_source, old_supports, new, ldraw_root)
    count = Counter(json.loads((M2 / "MAISON2-NOMENCLATURE.json").read_text())["by_real_LDraw_part"])
    count.update(CANONICAL_LDRAW_PARTS[p.part_id].ldraw_id for p in new)
    if sum(count.values()) != len(final_rows):
        raise AssertionError("M3_NOMENCLATURE_TOTAL")
    door_total = [p for p in model.parts if p.opening_id == DOOR
                  and p.facade == "front" and m1.gridbox(p)[2] < top]
    door_added = [p for p in new if p.opening_id == DOOR]
    boundaries = {
        "east_front_m": scene.volumes[0].width.value,
        "south_side_m": scene.volumes[0].depth.value,
        "east_grid_start_studs": x0, "east_grid_end_studs": end,
        "maison2_end_studs": previous["bay_new_wall_end_studs"],
        "nominal_rdc_wall_top_plates": top,
        "nominal_level_m": 2.4,
        "old_experimental_floor_height_m_unvalidated": previous["maison1_floor_height_m_not_approved"],
    }
    source_coverage = {
        "canonical_wall_RDC_source_parts": sum(p.component == "wall" for p in candidates),
        "canonical_wall_RDC_selected_parts": sum(p.component == "wall" for p in old_source + new
                                                  if within_rdc_front(p,x0,end,y0,top)),
        "source_scene_openings": [WINDOW, DOOR],
        "east_window_original_proxy_count": sum(p.opening_id == WINDOW for p in old_source + new),
        "east_french_door_source_proxy_count_below_RDC": len(door_total),
        "east_french_door_proxy_newly_selected": len(door_added),
        "right_door_visual_proxy_status": "CANONICAL_SYMBOL_ONLY" if door_added else "SCENE_ENVELOPE_ONLY_OR_UNREPRESENTED",
        "door_opening_scene_offset_m": right_door.offset_horizontal,
        "door_opening_scene_width_m": right_door.width,
        "door_opening_scene_height_m": right_door.height,
        "genuine_door_or_window_glazing": "NOT_CLAIMED",
    }
    result = {
        "total_placements": len(final_rows),
        "maison2_original_placements_preserved_verbatim": 139,
        "new_canonical_placements": len(new),
        "new_wall_parts": sum(p.component == "wall" for p in new),
        "new_opening_proxy_parts": sum(p.component == "facade_detail" for p in new),
        "new_engine_support_edges": checks["new_support_edges"],
        "new_engine_recognized_edges": checks["new_support_edges_with_engine_connectors"],
        "new_orthogonal_collision_pairs": checks["new_body_collisions_count"],
        "front_RDC_canonical_placements_covered": len(candidates),
        "complete_real_manufactured_door": "NOT_CERTIFIED",
        "full_physical_strength": "NOT_CERTIFIED",
    }
    documents = {
        "MAISON3-NOMENCLATURE.json": {
            "total": len(final_rows), "maison2_preserved": 139, "new_scene_placements": len(new),
            "by_real_LDraw_part": dict(sorted(count.items())), "symbolic_openings_are_not_genuine_glazing": True
        },
        "MAISON3-ORDRE-PROPOSE.json": {
            "keep_maison2_sequence": "EXACTLY_139_UNCHANGED",
            "additional_RDC_parts_lower_to_upper": [p.placement_id for p in new],
            "insertion_paths": "NOT_CONTINUOUSLY_VERIFIED",
            "mechanical_strength": "NOT_CERTIFIED",
        },
        "MAISON3-CONNEXIONS-ET-COLLISIONS.json": checks,
        "MAISON3-PROVENANCE.json": {
            "base_MAISON2_head": "c6ecc5d69c32411700d57e3100ce76d986c1ff1d",
            "maison2_ldraw_sha256": old_sha, "source_scene_sha256": previous["scene_sha256"],
            "canonical_brickmodel_count": len(model.parts), "bounds": boundaries,
            "openings": source_coverage, "new_canonical_ids": [p.placement_id for p in new],
            "source_scene_changed": False, "old_models_changed": False,
        },
        "MAISON3-RESULTATS.json": result,
        "MAISON3-LIMITES.json": {
            "scene_genuine_front_wall": "ALL_CANONICAL_RDC_RELEVANT_BRICKS_INCLUDED",
            "windows_and_french_door": "CANONICAL_SYMBOLS_OR_SCENE_OUTLINES_NOT_GENUINE_LEGO_GLAZING",
            "prior_2_post_baseplate_links": "NOT_PROVEN_AS_MAISON1",
            "prior_maison2_connector_unrecognized": "NOT_RETESTED",
            "old_floor_height_offset_m": round(previous["maison1_floor_height_m_not_approved"]-2.4,4),
            "roof": "NOT_INSTALLED", "terrace": "NOT_INSTALLED",
            "old_levels": "UNCHANGED", "mechanics": "NOT_CERTIFIED",
        }
    }
    for name, obj in documents.items():
        (out / name).write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")
    print("MAISON3_FACADE_EST_RDC_ONE_BUILD", json.dumps(result, sort_keys=True))
    return result


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--ldraw-root", type=Path, required=True)
    args = ap.parse_args()
    run(args.output, args.ldraw_root)
