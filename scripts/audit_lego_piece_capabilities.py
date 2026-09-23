#!/usr/bin/env python3
"""Read-only audit of Boldungo LEGO piece capability layers.

Default behavior prints a JSON report to stdout. --write writes only the audit
artifact; it never edits engine/catalog/planner code.
"""
from __future__ import annotations
import argparse, csv, json, re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW_PARTS = ROOT / "data/raw/parts.csv"
RAW_ELEMENTS = ROOT / "data/raw/elements.csv"
MASTER = ROOT / "data/processed/piece_types_master.csv"
CAPABILITIES = ROOT / "backend/brickhouse/bricks/piece_capabilities.py"
GEOMETRY = ROOT / "backend/brickhouse/bricks/geometry_adapter.py"
OUTPUT = ROOT / "docs/audits/lego-piece-capability-inventory.json"

def rows(path):
    with path.open(encoding="utf-8", newline="") as h:
        return list(csv.DictReader(h))

def mapping_ids():
    text = GEOMETRY.read_text(encoding="utf-8")
    return dict(re.findall(r'^\s*"([^"]+)":\s*LDrawPartMapping\("([^"]+)"', text, re.M))

def approved_ids():
    # Import the actual registry: no duplicated allow-list in this audit script.
    import sys
    sys.path.insert(0, str(ROOT / "backend"))
    from brickhouse.bricks.piece_capabilities import create_current_engine_capability_registry
    registry = create_current_engine_capability_registry(MASTER)
    return sorted(registry.approved_ids()), {p.engine_id: p for p in registry.pieces}

def family(engine_id):
    if engine_id.startswith("BRICK_SLOPED_"): return "slopes"
    if engine_id.startswith("BRICK_"): return "bricks"
    if engine_id.startswith("TILE_"): return "tiles"
    if engine_id.startswith("WINDOW_"): return "windows"
    if engine_id.startswith("GLASS_"): return "window_glazing"
    return "unknown"

def build():
    raw = rows(RAW_PARTS); elements = rows(RAW_ELEMENTS); master_rows = rows(MASTER)
    raw_by_id = {r["part_num"]: r for r in raw}
    master = {r["engine_id"]: r for r in master_rows}
    designs = defaultdict(set)
    for e in elements:
        if e.get("design_id"): designs[e["part_num"]].add(e["design_id"])
    approved, registry = approved_ids()
    mappings = mapping_ids()

    items = []
    for eid in approved:
        ldraw = mappings.get(eid)
        m = master.get(eid)
        raw_row = raw_by_id.get(ldraw) if ldraw else None
        p = registry[eid]
        items.append({
            "boldungo_id": eid,
            "part_num": ldraw if raw_row else None,
            "design_ids": sorted(designs.get(ldraw, set())) if raw_row else [],
            "ldraw_id": ldraw,
            "source_category": (m or raw_row or {}).get("category") or (raw_row or {}).get("part_cat_id"),
            "architectural_family": family(eid),
            "layers": {
                "RAW_KNOWN": raw_row is not None,
                "MASTER_SELECTED": m is not None,
                "ENGINE_APPROVED": True,
                "SPECIAL_TECHNIQUE_REQUIRED": False,
            },
            "master_status": m.get("status") if m else None,
            "piece_capability_stage": p.stage.name,
            "geometry_available": ldraw is not None,
            "connectivity_known": True if eid.startswith("BRICK_") and not eid.startswith("BRICK_SLOPED_") else "specialized_or_limited",
            "placement_approved": True,
            "special_technique_required": False,
            "autonomous_selection_available": True,
        })

    dormant = [
      {"family":"plates","raw_reference_count":143,"sources":["data/raw/parts.csv category 14","data/processed/piece_types_master.csv"],"first_blocker":"not promoted as a general autonomous placement palette"},
      {"family":"tiles","raw_reference_count":None,"sources":["data/raw/parts.csv","data/processed/piece_types_master.csv"],"first_blocker":"only TILE_2X2/TILE_2X3/TILE_2X4 are placement-approved, for current specialized use"},
      {"family":"jumpers","raw_reference_count":None,"sources":["data/raw/parts.csv category 9"],"first_blocker":"offset stud connectivity/placement not approved"},
      {"family":"masonry","raw_reference_count":None,"sources":["data/raw/parts.csv category 5"],"first_blocker":"not canonicalized/promoted for placement"},
      {"family":"arches","raw_reference_count":None,"sources":["data/raw/parts.csv category 37"],"first_blocker":"non-rectangular geometry/connectivity not approved"},
      {"family":"doors","raw_reference_count":None,"sources":["data/raw/parts.csv category 16","data/processed/piece_types_master.csv"],"first_blocker":"no current autonomous door assembly/placement approval"},
      {"family":"additional_windows","raw_reference_count":None,"sources":["data/raw/parts.csv category 16","data/processed/piece_types_master.csv"],"first_blocker":"current engine restricts windows to three validated frame/pane assemblies"},
      {"family":"fences_railings","raw_reference_count":138,"sources":["data/raw/parts.csv category 32"],"first_blocker":"scene railing solution reuses standard bricks; fence geometry/connectivity is not approved"},
      {"family":"round","raw_reference_count":None,"sources":["data/raw/parts.csv categories 20,21,67"],"first_blocker":"round connection/footprint vocabulary not promoted"},
      {"family":"cheese_slopes","raw_reference_count":None,"sources":["data/raw/parts.csv category 3"],"first_blocker":"not in current validated roof slope families"},
      {"family":"inverted_slopes","raw_reference_count":None,"sources":["data/raw/parts.csv"],"first_blocker":"inverted support/connectivity not approved"},
      {"family":"wedges","raw_reference_count":455,"sources":["data/raw/parts.csv category 6"],"first_blocker":"angled footprint/connectivity not approved"},
      {"family":"curved_slopes","raw_reference_count":None,"sources":["data/raw/parts.csv categories 3,37,67"],"first_blocker":"curved geometry is known in raw data but not canonicalized for placement"},
      {"family":"brackets_snot","raw_reference_count":None,"sources":["data/raw/parts.csv categories 5,9,34"],"first_blocker":"side-stud/SNOT connector inference is not approved"},
      {"family":"headlight","raw_reference_count":None,"sources":["data/raw/parts.csv"],"first_blocker":"SNOT connector semantics not approved"},
      {"family":"bars_clips","raw_reference_count":None,"sources":["data/raw/parts.csv and category 32"],"first_blocker":"bar/clip connection domain not implemented for autonomous placement"},
      {"family":"hinges","raw_reference_count":240,"sources":["data/raw/parts.csv category 18"],"first_blocker":"hinge articulation/connectivity not approved"},
      {"family":"technic","raw_reference_count":None,"sources":["data/raw/parts.csv categories 8,12,46,51,53,54,55"],"first_blocker":"Technic connector inference/placement is outside current approved domain"},
    ]

    active = sum(r.get("status") == "ACTIVE" for r in master_rows)
    experimental = sum(r.get("status") == "EXPERIMENTAL" for r in master_rows)
    inconsistencies = []
    missing_map = [x for x in approved if x not in mappings]
    if missing_map: inconsistencies.append({"type":"approved_without_ldraw_mapping","ids":missing_map})
    implicit = [r["engine_id"] for r in master_rows if registry[r["engine_id"]].stage.name != "KNOWN" and r["engine_id"] not in approved]
    if implicit: inconsistencies.append({"type":"implicit_master_promotion","ids":implicit})

    return {
      "schema_version":"0.1",
      "audit_kind":"lego_piece_capability_inventory",
      "derivation":{
        "raw_parts":"CSV row count excluding header",
        "master_types":"CSV row count excluding header",
        "master_status":"count status column values",
        "placement_approved":"create_current_engine_capability_registry(...).approved_ids()",
        "ldraw_mappings":"CANONICAL_LDRAW_PARTS keys parsed from geometry_adapter.py",
        "note":"null means not cleanly determined by this audit; no identifier/count is invented."
      },
      "counts":{"raw_parts":len(raw),"master_types":len(master_rows),"master_active":active,"master_experimental":experimental,"placement_approved":len(approved)},
      "placement_approved_ids":approved,
      "approved_pieces":items,
      "dormant_priority_families":dormant,
      "consistency":{
        "all_approved_exist_in_registry":all(x in registry for x in approved),
        "all_approved_have_ldraw_mapping":not missing_map,
        "no_implicit_master_placement_approval":not implicit,
        "inconsistencies":inconsistencies
      }
    }

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--write",action="store_true")
    args=ap.parse_args(); report=build()
    text=json.dumps(report,indent=2,ensure_ascii=False)+"\n"
    if args.write:
        OUTPUT.parent.mkdir(parents=True,exist_ok=True); OUTPUT.write_text(text,encoding="utf-8")
        print(OUTPUT)
    else: print(text,end="")
if __name__=="__main__": main()
