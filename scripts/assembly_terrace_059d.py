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


def ordered_finishes(scope, fixed, mobile):
    """Retest every remaining official terrace placement, posts before top rails.

    Hidden cross bonds are scheduled before deck boards when they are not
    already part of the fixed support or hand-held module.
    """
    existing={p["placement_id"] for p in [*fixed,*mobile]}
    remaining=[p for p in scope if p["placement_id"] not in existing]
    def priority(p):
        pid=p["placement_id"]
        if "hidden-cross-bond" in pid or "hidden-cross-plate" in pid:
            return (0,pid)
        if ":board:" in pid:
            return (1,pid)
        if "rail-post:" in pid:
            return (2,pid)
        if "rail-top" in pid:
            return (4,pid)
        return (3,pid)
    remaining.sort(key=priority)
    installed=[*fixed,*mobile]
    steps=[]
    for i,p in enumerate(remaining,1):
        result=check(p,installed)
        valid=[]
        for q in installed:
            c=connection(p,q)
            if c["status"]=="VALID":
                valid.append(c)
        steps.append({"number":i,"piece":p["placement_id"],
                      "position":[p["x_studs"],p["y_studs"],p["z_plates"]],
                      "direction":"vertical -Z",
                      "installed":[q["placement_id"] for q in installed],
                      "valid_connections":valid,
                      "collision":result,"verdict":result["verdict"]})
        if result["verdict"] == "GEOMETRY_PASS":
            installed.append(p)
        else:
            # A failed operation cannot become a fictitious installed obstacle.
            # Stop here; downstream operations depend on an uninstalled piece.
            for j,q in enumerate(remaining[i:],i+1):
                steps.append({"number":j,"piece":q["placement_id"],
                              "position":[q["x_studs"],q["y_studs"],q["z_plates"]],
                              "direction":"NOT_TESTED","installed":[x["placement_id"] for x in installed],
                              "valid_connections":[],"collision":None,"verdict":"NOT_TESTED",
                              "reason":"earlier insertion BLOCKED or UNKNOWN"})
            break
    return steps


def plate_06_options(scope, by, base_mobile, base_fixed):
    """Compare 029:06 in the hand-held module vs preinstalled fixed support."""
    plate=by[P+"hidden-cross-bond-029:06"]
    reports={}
    for option in ("A","B"):
        moving=[*base_mobile,plate] if option=="A" else list(base_mobile)
        fixed=[*base_fixed,plate] if option=="B" else list(base_fixed)
        precheck=check(plate,base_fixed) if option=="B" else None
        internal=links(moving)
        connected=reachable(moving,internal,{moving[0]["placement_id"]})
        dock=rigid_module_install(moving,fixed)
        anchors=[e for e in links([*moving,*fixed])
                 if e["status"]=="VALID" and
                 ((e["a"] in {p["placement_id"] for p in moving}) !=
                  (e["b"] in {p["placement_id"] for p in moving}))]
        reports[option]={
            "plate_06":plate["placement_id"],
            "plate_preinstallation":precheck,
            "module_valid_connected":len(connected)==len(moving),
            "plate_internal_valid_links":[e for e in internal
                                          if plate["placement_id"] in (e["a"],e["b"])
                                          and e["status"]=="VALID"],
            "rigid_install":dock,
            "valid_docking_interfaces":anchors,
            "candidate_proven":(len(connected)==len(moving)
                and dock["verdict"]=="GEOMETRY_PASS"
                and (option=="A" or precheck["verdict"]=="GEOMETRY_PASS"))
        }
    return reports


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
    # 059E solution B: preinstall plate 029:06, then lower the unchanged module.
    plate06=by[P+"hidden-cross-bond-029:06"]
    plate06_check=check(plate06,fixed)
    plate06_connections=[connection(plate06,q) for q in fixed]
    plate06_valid=[c for c in plate06_connections if c["status"]=="VALID"]
    plate06_unknown=[c for c in plate06_connections if c["status"]=="UNKNOWN"]
    plate06_supported=bool(plate06_valid)
    # If no VALID support exists, an operator-held plate is only a hypothesis:
    # a free insertion path is not sufficient to mark it installed.
    plate06_preinstalled=(plate06_check["verdict"]=="GEOMETRY_PASS"
                           and plate06_supported)
    docking_fixed=[*fixed,plate06] if plate06_preinstalled else list(fixed)
    dock=rigid_module_install(mobile,docking_fixed) if plate06_preinstalled else {
        "verdict":"NOT_TESTED","reason":"plate 029:06 not demonstrably supported before docking"}
    plate_options = plate_06_options(scope, by, mobile, fixed)
    plate_contacts = [connection(by[P + CROSS], by[P + n]) for n in BOARDS]
    post_contacts = [connection(by[P + "board:00001"], p) for p in posts]
    # Retest the same remaining scope with hidden plates and guardrail posts
    # scheduled before the elements that would cover them.
    later = ordered_finishes(scope, docking_fixed, mobile) if plate06_preinstalled else []
    blocked = next((x for x in later if x["verdict"] == "BLOCKED"), None)
    unknown = next((x for x in later if x["verdict"] == "UNKNOWN"), None)
    # Keep the original 60-operation perimeter: plate06 once, plus 59 deferred.\n    remaining_count=len([p for p in scope if p["placement_id"] not in {q["placement_id"] for q in [*fixed,*mobile]}])\n    if not plate06_preinstalled:\n        later=[{"number":i+2,"piece":p["placement_id"],"verdict":"NOT_TESTED",\n                "reason":"preinstallation of 029:06 not proven"} for i,p in enumerate(\n                p for p in scope if p["placement_id"] not in {q["placement_id"] for q in [*fixed,*mobile,plate06]})]\n    preinstall_step={"number":1,"piece":plate06["placement_id"],\n        "position":[plate06["x_studs"],plate06["y_studs"],plate06["z_plates"]],\n        "direction":"vertical -Z",\n        "installed":[p["placement_id"] for p in fixed],\n        "valid_connections":plate06_valid,"unknown_connections":plate06_unknown,\n        "collision":plate06_check,\n        "verdict":plate06_check["verdict"] if plate06_supported else "UNKNOWN",\n        "holding":"VALID fixed support" if plate06_supported else "NO VALID SUPPORT; hand-held assistance NOT PROVEN"}\n    for i,step in enumerate(later,2):\n        step["number"]=i\n    operations=[preinstall_step,*later]\n    assert len(operations)==remaining_count,(len(operations),remaining_count)\n    counts = {status:sum(x["verdict"]==status for x in operations)
              for status in ("GEOMETRY_PASS","BLOCKED","UNKNOWN","NOT_TESTED")}
    all_connected = len(connected) == len(mobile)
    docking_verified = (plate06_preinstalled and all_connected and bool(anchored) and
                        dock["verdict"] == "GEOMETRY_PASS")
    # Full buildability requires all later steps and hidden-plate dependencies.
    buildable = (plate06_preinstalled and docking_verified and\n                 all(x["verdict"] == "GEOMETRY_PASS" for x in operations))
    return {
        "variant": variant, "mobile": mobile, "fixed_ids": [p["placement_id"] for p in fixed],
        "internal_connections": internal, "internal_valid_connected": all_connected,
        "unreachable_module_parts": sorted(ids - connected),
        "plate_board_contacts": plate_contacts,
        "east_post_board_contacts": post_contacts,
        "docking_interfaces": cross, "valid_anchors": valid_anchors,
        "anchors_reaching_existing_posts": anchored,
        "fixed_valid_links": fixed_links,
        "rigid_module_install": dock,\n        "plate06_preinstallation":preinstall_step,\n        "plate06_preinstalled":plate06_preinstalled,\n        "operations":operations,\n        "operations_total":len(operations),
        "plate_06_options":plate_options,
        "later_terrace": later,
        "later_counts": counts,
        "later_order_rule": "hidden plates, remaining boards, rail posts, other finishes, rail tops",
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
                          "later_counts": report["later_counts"],\n                          "plate06_preinstalled":report["plate06_preinstalled"],\n                          "operations_total":report["operations_total"],
                          "plate_06_options":{k:{"precheck":v["plate_preinstallation"],
                              "connected":v["module_valid_connected"],
                              "rigid":v["rigid_install"]["verdict"],
                              "candidate_proven":v["candidate_proven"]}
                              for k,v in report["plate_06_options"].items()},
                          "buildable": report["complete_assembly_demonstrated"]}, indent=2))
    assert path.read_bytes() == before


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: assembly_terrace_059d.py brick-model.json")
    main(sys.argv[1])
