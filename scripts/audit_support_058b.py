"""Compare 057 historical connector evidence to 058B without changing GUIDED-004.

Usage: python scripts/audit_support_058b.py artifacts/lego2-guided-004/brick-model.json
"""
import json
import sys
from pathlib import Path

from experiment_terrace_057 import select_scope, legacy_057_diagnostic
from audit_terrace_048 import connector_graph_diagnostic


def measure(placements, diagnostic):
    post_ids = {p["placement_id"] for p in placements
                if "support-solution:timber-post" in p["placement_id"]}
    floor_ids = {p["placement_id"] for p in placements} - post_ids
    reached = set()
    for component in diagnostic["components"]:
        if post_ids.intersection(component):
            reached.update(component)
    edges = diagnostic["valid_edges"]
    post_to_floor = [e for e in edges
                     if (e["a"] in post_ids) != (e["b"] in post_ids)]
    post_edges = [e for e in edges if e["a"] in post_ids and e["b"] in post_ids]
    return {
        "pieces_total": len(placements),
        "post_segments": len(post_ids),
        "floor_and_other_nonpost_pieces": len(floor_ids),
        "valid_edges": len(edges),
        "unknown_edges": len(diagnostic["unknown_edges"]),
        "components": len(diagnostic["components"]),
        "isolated": len(diagnostic["isolated"]),
        "floor_reaching_posts": len(reached & floor_ids),
        "floor_not_reaching_posts": len(floor_ids - reached),
        "post_segments_reaching_posts": len(reached & post_ids),
        "post_to_floor_valid_edges": len(post_to_floor),
        "single_stud_post_to_floor_edges": sum(e["contacts"] == 1 for e in post_to_floor),
        "post_stack_valid_edges": len(post_edges),
        "articulations": len(diagnostic["articulations"]),
        "bridges": len(diagnostic["bridges"]),
        "newly_recognized_post_to_floor": [
            {"a":e["a"],"b":e["b"],"contacts":e["contacts"]}
            for e in post_to_floor
        ],
    }


def main(path):
    source = Path(path)
    raw = source.read_bytes()
    placements = select_scope(json.loads(raw))
    if len(placements) != 105:
        raise ValueError(f"Expected 105 real GUIDED-004 placements, got {len(placements)}")
    if len({p["placement_id"] for p in placements}) != 105:
        raise ValueError("Duplicate IDs in GUIDED-004")
    before = measure(placements, legacy_057_diagnostic(placements))
    after = measure(placements, connector_graph_diagnostic(placements))
    if source.read_bytes() != raw:
        raise AssertionError("Official export changed")
    print(json.dumps({"before":before, "after":after,
                      "floor_path_gain":after["floor_reaching_posts"]-before["floor_reaching_posts"],
                      "new_physical_connections":0},indent=2))
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: audit_support_058b.py brick-model.json")
    raise SystemExit(main(sys.argv[1]))
