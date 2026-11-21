"""LEGO2-059 conservative under-deck reinforcement candidate search.

Produces experimental JSON only. No modification of GUIDED-004.
Run: python scripts/prototype_terrace_059.py artifacts/lego2-guided-004/brick-model.json
"""
import json
import sys
from pathlib import Path

from audit_terrace_048 import box, overlap, connector_graph_diagnostic
from experiment_terrace_057 import select_scope
from brickhouse.bricks.brick_model import BrickModelPart
from brickhouse.bricks.connectors import validate_connection

KINDS = ("PLATE_1X6", "PLATE_1X8", "BRICK_1X8", "BRICK_2X8")
PREFIX = "EXPERIMENT:059:"
POST = "support-solution:timber-post"


def score(parts, diag):
    post_ids = {p["placement_id"] for p in parts if POST in p["placement_id"]}
    reachable = set()
    for component in diag["components"]:
        if post_ids.intersection(component):
            reachable.update(component)
    return {
        "pieces": len(parts),
        "valid": len(diag["valid_edges"]),
        "unknown": len(diag["unknown_edges"]),
        "components": len(diag["components"]),
        "isolated": len(diag["isolated"]),
        "nonpost_reaching_support": len(reachable-post_ids),
        "articulations": len(diag["articulations"]),
        "bridges": len(diag["bridges"]),
        "single_stud_edges": len(diag["single_contact_edges"]),
        "post_to_floor_one_stud": sum(
            e["contacts"] == 1 and
            ((POST in e["a"]) != (POST in e["b"]))
            for e in diag["valid_edges"]
        ),
    }


def main(source):
    path = Path(source)
    before = path.read_bytes()
    model = json.loads(before)
    whole = model["parts"]
    selected = select_scope(model)
    if len(whole) != 1890 or len(selected) != 105:
        raise ValueError("Unexpected GUIDED-004 export")
    ids = {p["placement_id"] for p in whole}
    if len(ids) != 1890:
        raise ValueError("Duplicate GUIDED-004 placement IDs")
    boxes = [(p["placement_id"], box(p)) for p in whole]
    boxes = [(pid, b) for pid, b in boxes if b is not None]
    original = connector_graph_diagnostic(selected)
    baseline = score(selected, original)
    parts = [BrickModelPart.model_validate(p) for p in selected]
    # Only standard, catalog-backed horizontal parts, at occupied deck underside
    # elevation. Explicit deterministic coordinates; no invented geometries.
    candidates = []
    for kind in KINDS:
        width, length = map(int, kind.split("_")[1].split("X"))
        height = 1 if kind.startswith("PLATE") else 3
        for rotation in (0, 1):
            w, d = (width, length) if rotation == 0 else (length, width)
            for x in range(2, 15):
                for y in range(16, 46):
                    for z in (32, 33, 34, 35):
                        placement = {
                            "placement_id": f"{PREFIX}{kind}:{x}:{y}:{z}:{rotation}",
                            "part_id": kind,
                            "category": "plate" if height == 1 else "brick",
                            "component": "roof_support",
                            "x_studs": x, "y_studs": y, "z_plates": z,
                            "rotation_quarter_turns": rotation,
                            "width_studs": width, "length_studs": length,
                            "height_plates": height,
                        }
                        b = box(placement)
                        if any(overlap(b, other) for _, other in boxes):
                            continue
                        candidate = BrickModelPart.model_validate(placement)
                        links = []
                        for p in parts:
                            r = validate_connection(candidate, p)
                            if r.status == "VALID":
                                links.append((p.placement_id, r.interface_count))
                        if len(links) < 2:
                            continue
                        # Avoid computing full graph for every geometric candidate.
                        candidates.append((placement, links))
    evaluated = []
    for placement, links in candidates:
        diag = connector_graph_diagnostic([*selected, placement])
        metrics = score([*selected, placement], diag)
        gain = metrics["nonpost_reaching_support"]-baseline["nonpost_reaching_support"]
        if gain > 0:
            evaluated.append({"placement": placement, "connections": links,
                              "metrics": metrics, "gain": gain,
                              "full_model_static_collisions": 0,
                              "insertion_path": "NOT_PROVEN",
                              "mechanical_strength": "NOT_CERTIFIED"})
    evaluated.sort(key=lambda c:(-c["gain"],-len(c["connections"]),
                                 c["placement"]["placement_id"]))
    winner = evaluated[:2]
    out = {
        "mission": "BOLDUNGO-LEGO2-059",
        "source": str(path),
        "source_part_count": len(whole),
        "baseline": baseline,
        "geometrically_connecting_candidates": len(candidates),
        "candidates_with_real_support_path_gain": len(evaluated),
        "prototypes": winner,
        "no_original_part_replaced": True,
        "official_model_unchanged": path.read_bytes() == before,
        "limitations": ["Insertion path not proven", "No physical strength certification",
                        "Other nearby surfaces without catalog boxes not collision-tested"],
    }
    output = Path("artifacts/lego2-059")
    output.mkdir(parents=True, exist_ok=True)
    (output/"prototype-comparison.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))
    if path.read_bytes() != before:
        raise AssertionError("Official GUIDED-004 changed")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: prototype_terrace_059.py brick-model.json")
    raise SystemExit(main(sys.argv[1]))
