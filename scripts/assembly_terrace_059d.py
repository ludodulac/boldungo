"""059D: existing anchored board/plate module, conservative reproducible study.

No new candidate search, no official model changes, no unproven mechanical claims.
"""
import json
import sys
from collections import deque
from pathlib import Path

from assembly_sequence_059b import rigid_module_install, check, P
from experiment_terrace_057 import select_scope
from prototype_terrace_059b import T1, T2
from brickhouse.bricks.brick_model import BrickModelPart
from brickhouse.bricks.connectors import validate_connection

BOARDS = ("board:00001", "board:00007", "board:00013", "board:00019", "board:00031")
CROSS = "hidden-cross-plate:00007-00013"
HIDDEN = ("hidden-cross-bond-029:03", "hidden-cross-bond-029:04", "hidden-cross-bond-029:08")


def connection(a, b):
    r = validate_connection(BrickModelPart.model_validate(a), BrickModelPart.model_validate(b))
    return {"a": a["placement_id"], "b": b["placement_id"],
            "status": r.status, "stud_contacts": r.interface_count}


def links(parts):
    result = []
    for i, a in enumerate(parts):
        for b in parts[i + 1:]:
            c = connection(a, b)
            if c["status"] != "INVALID":
                result.append(c)
    return result


def reachable(parts, edges, starts):
    adjacent = {p["placement_id"]: set() for p in parts}
    for e in edges:
        if e["status"] == "VALID":
            adjacent[e["a"]].add(e["b"])
            adjacent[e["b"]].add(e["a"])
    visited = set(starts)
    queue = deque(starts)
    while queue:
        for other in adjacent.get(queue.popleft(), ()):
            if other not in visited:
                visited.add(other)
                queue.append(other)
    return visited


def study(model, variant):
    full = model["parts"]
    assert len(full) == 1890
    scope = select_scope(model)
    assert len(scope) == 105
    by = {p["placement_id"]: p for p in full}
    mobile = [by[P + name] for name in BOARDS]
    mobile.append(by[P + CROSS])
    mobile.append(T1)
    if variant == "C":
        mobile.append(T2)
    ids = {p["placement_id"] for p in mobile}
    posts = [p for p in scope if "support-solution:timber-post" in p["placement_id"]]
    hidden = [by[P + name] for name in HIDDEN]
    fixed = [*posts, *hidden]
    internal = links(mobile)
    connected = reachable(mobile, internal, [mobile[0]["placement_id"]])
    anchor_links = links([*mobile, *fixed])
    cross = [e for e in anchor_links if
             (e["a"] in ids) != (e["b"] in ids)]
    valid_anchors = [e for e in cross if e["status"] == "VALID"]
    fixed_links = links(fixed)
    post_ids = {p["placement_id"] for p in posts}
    fixed_reachable = reachable(fixed, fixed_links, post_ids)
    anchored = [e for e in valid_anchors if
                (e["a"] if e["a"] not in ids else e["b"]) in fixed_reachable]
    dock = rigid_module_install(mobile, fixed)
    plate_contacts = [connection(by[P + CROSS], by[P + n]) for n in BOARDS]
    post_contacts = [connection(by[P + "board:00001"], p) for p in posts]
    # All remaining terrace parts are deferred, not silently omitted.
    installed = [*fixed, *mobile]
    later = []
    for p in scope:
        if p["placement_id"] in {q["placement_id"] for q in installed}:
            continue
        result = check(p, installed)
        later.append({"piece": p["placement_id"], **result})
        installed.append(p)
    blocked = next((x for x in later if x["verdict"] == "BLOCKED"), None)
    unknown = next((x for x in later if x["verdict"] == "UNKNOWN"), None)
    all_connected = len(connected) == len(mobile)
    docking_verified = (all_connected and bool(anchored) and
                        dock["verdict"] == "GEOMETRY_PASS")
    # Full buildability requires all later steps and hidden-plate dependencies.
    buildable = docking_verified and all(x["verdict"] == "GEOMETRY_PASS" for x in later)
    return {
        "variant": variant, "mobile": mobile, "fixed_ids": [p["placement_id"] for p in fixed],
        "internal_connections": internal, "internal_valid_connected": all_connected,
        "unreachable_module_parts": sorted(ids - connected),
        "plate_board_contacts": plate_contacts,
        "east_post_board_contacts": post_contacts,
        "docking_interfaces": cross, "valid_anchors": valid_anchors,
        "anchors_reaching_existing_posts": anchored,
        "fixed_valid_links": fixed_links,
        "rigid_module_install": dock,
        "later_terrace": later,
        "first_blocked_operation": blocked,
        "first_unknown_operation": unknown,
        "docking_geometrically_demonstrated": docking_verified,
        "complete_assembly_demonstrated": buildable,
        "verdict": "ASSEMBLAGE_GEOMETRIQUEMENT_DEMONTRE" if buildable else "NON_DEMONTRE",
        "limitations": ["AABB swept geometry is conservative and not a physical insertion certification",
                        "Noncatalog geometry and UNKNOWN connections are not treated as VALID",
                        "Three direct post/deck single-stud contacts remain mechanically uncertified"]
    }


def main(source):
    path = Path(source)
    before = path.read_bytes()
    model = json.loads(before)
    dest = Path("artifacts/lego2-059b")
    dest.mkdir(parents=True, exist_ok=True)
    for variant in ("B", "C"):
        report = study(model, variant)
        (dest / f"anchored-module-{variant}.json").write_text(json.dumps(report, indent=2))
        print(json.dumps({"variant": variant, "internal_connected": report["internal_valid_connected"],
                          "valid_anchors": len(report["valid_anchors"]),
                          "anchored_to_post": len(report["anchors_reaching_existing_posts"]),
                          "rigid_verdict": report["rigid_module_install"]["verdict"],
                          "first_blocked": report["first_blocked_operation"],
                          "first_unknown": report["first_unknown_operation"],
                          "buildable": report["complete_assembly_demonstrated"]}, indent=2))
    assert path.read_bytes() == before


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: assembly_terrace_059d.py brick-model.json")
    main(sys.argv[1])
