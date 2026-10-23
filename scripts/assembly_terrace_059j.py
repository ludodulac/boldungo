"""059J: genuine 1890-piece GUIDED-004, 029:06 in hand-held mobile module.

The sequence demonstrates *modeled* nominal connectors and conservative
vertical AABB clearances; it does not certify human assembly, gripping,
joint strength, hidden preinstalled supports, or other nonrectangular geometry.
The official model is read-only. B=T1, C=T1+T2 remain experimental.
"""
import json
import sys
from pathlib import Path

from assembly_terrace_059d import (
    BOARDS, CROSS, HIDDEN, connection, links, ordered_finishes, reachable,
)
from assembly_sequence_059b import P, rigid_module_install
from experiment_terrace_057 import select_scope
from prototype_terrace_059b import T1, T2

STATUS = ("GEOMETRY_PASS", "BLOCKED", "UNKNOWN", "NOT_TESTED")


def analyze(model, variant):
    if variant not in ("B", "C"):
        raise ValueError(variant)
    if len(model["parts"]) != 1890:
        raise ValueError("not the canonical 1890-piece GUIDED-004 export")
    scope = select_scope(model)
    if len(scope) != 105:
        raise ValueError("terrace perimeter changed")
    by = {p["placement_id"]: p for p in model["parts"]}
    board1 = by[P + "board:00001"]
    board2 = by[P + "board:00002"]
    plate = by[P + "hidden-cross-bond-029:06"]
    posts = [p for p in scope if "support-solution:timber-post" in p["placement_id"]]
    fixed = [*posts, *(by[P + name] for name in HIDDEN)]
    mobile = [board1, plate,
              *(by[P + name] for name in BOARDS if name != "board:00001"),
              by[P + CROSS], T1]
    if variant == "C":
        mobile.append(T2)
    module_ids = {p["placement_id"] for p in mobile}
    fixed_ids = {p["placement_id"] for p in fixed}
    official_mobile = module_ids & {p["placement_id"] for p in scope}
    assert not (official_mobile & fixed_ids)
    assert len(fixed) == 39 and len(official_mobile) == 7
    assert board2["placement_id"] not in module_ids | fixed_ids

    # Plate is fitted underneath board1 while the module is held in hand;
    # a plate that floats without its two-stud attachment is NEVER installed.
    plate_board1 = connection(plate, board1)
    plate_board2 = connection(plate, board2)
    internal = links(mobile)
    connected = reachable(mobile, internal, {board1["placement_id"]})
    internal_connected = len(connected) == len(mobile)
    fixed_reached = reachable(
        fixed, links(fixed), {p["placement_id"] for p in posts}
    )
    all_links = links([*mobile, *fixed])
    anchor_edges = [e for e in all_links
                    if e["status"] == "VALID"
                    and ((e["a"] in module_ids) != (e["b"] in module_ids))]
    anchored_edges = [e for e in anchor_edges
                      if (e["a"] if e["a"] in fixed_ids else e["b"])
                      in fixed_reached]
    can_attempt = (plate_board1["status"] == "VALID"
                   and plate_board1["stud_contacts"] == 2
                   and plate_board2["status"] == "VALID"
                   and plate_board2["stud_contacts"] == 1
                   and internal_connected
                   and bool(anchored_edges))
    rigid = rigid_module_install(mobile, fixed) if can_attempt else {
        "verdict": "NOT_TESTED",
        "reason": "missing 029:06 contact, module connectivity or post anchor",
    }
    if can_attempt and rigid["verdict"] == "GEOMETRY_PASS":
        later = ordered_finishes(scope, fixed, mobile)
    else:
        excluded = fixed_ids | official_mobile
        later = [{"piece":p["placement_id"], "verdict":"NOT_TESTED",
                  "reason":"unproven module assembly or docking"} for p in scope
                 if p["placement_id"] not in excluded]
    # Scope = 105 originals; fixed 39; seven canonical mobile (T1/T2
    # experimental and NOT counted in GUIDED-004). Remaining = 59.
    assert len(later) == 59
    counts = {s:sum(step["verdict"] == s for step in later) for s in STATUS}
    board2_step = next(x for x in later
                       if x["piece"] == board2["placement_id"])
    unconnected_stages = [s["piece"] for s in later
                          if s["verdict"] == "GEOMETRY_PASS"
                          and not s.get("valid_connections")]
    geometric_pass = (can_attempt and rigid["verdict"] == "GEOMETRY_PASS"
                      and counts["GEOMETRY_PASS"] == 59
                      and board2_step["verdict"] == "GEOMETRY_PASS"
                      and any(e["status"] == "VALID"
                              and plate["placement_id"] in (e["a"], e["b"])
                              for e in board2_step.get("valid_connections", [])))
    return {
        "variant":variant,
        "official_parts":1890,
        "terrace_original_scope":105,
        "fixed_count":len(fixed),
        "handheld_module_size":len(mobile),
        "official_module_pieces":len(official_mobile),
        "module_parts":[p["placement_id"] for p in mobile],
        "plate_attached_to_board1":plate_board1,
        "plate_receives_board2":plate_board2,
        "module_internal_valid_connected":internal_connected,
        "unreachable_module_parts":sorted(module_ids - connected),
        "module_valid_docking_anchors":anchored_edges,
        "fixed_hidden_parts_without_post_path":sorted(
            fixed_ids - fixed_reached
        ),
        "rigid_module_install":rigid,
        "later_counts":counts,
        "later_steps":later,
        "board2_step":board2_step,
        "first_nonpass":next((s for s in later
                              if s["verdict"] != "GEOMETRY_PASS"), None),
        "later_pieces_without_documented_valid_holding":unconnected_stages,
        "staged_rectangular_geometry_demonstrated":bool(geometric_pass),
        "physical_buildability":"NOT_CERTIFIED",
        "limitations":[
            "LDraw nominal compatibility does not certify clutch strength",
            "Hand-held subassembly internal insertion chronology not fully simulated",
            "Each swept AABB only models vertical -Z clearance, not arbitrary motion",
            "Already fixed hidden support plate stability not guaranteed",
            "The three post/deck single-stud anchors are mechanically unverified",
            "Unknown and non-rectangular obstacles require separate review",
        ],
    }


def main(path):
    source = Path(path)
    before = source.read_bytes()
    model = json.loads(before)
    destination = Path("artifacts/lego2-059b")
    destination.mkdir(parents=True, exist_ok=True)
    ok = True
    for variant in ("B", "C"):
        report = analyze(model, variant)
        (destination / f"059j-staged-terrace-{variant}.json").write_text(
            json.dumps(report, indent=2), encoding="utf-8"
        )
        print(json.dumps({
            "variant":variant,
            "plate_board1":report["plate_attached_to_board1"],
            "plate_board2":report["plate_receives_board2"],
            "module_connected":report["module_internal_valid_connected"],
            "post_anchors":len(report["module_valid_docking_anchors"]),
            "rigid":report["rigid_module_install"]["verdict"],
            "later_counts":report["later_counts"],
            "board2_verdict":report["board2_step"]["verdict"],
            "later_without_valid_holding":len(
                report["later_pieces_without_documented_valid_holding"]
            ),
            "geometric_scope_proven":
                report["staged_rectangular_geometry_demonstrated"],
            "physical_buildability":report["physical_buildability"],
        }, indent=2))
        ok &= report["staged_rectangular_geometry_demonstrated"]
    assert source.read_bytes() == before
    return 0 if ok else 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: assembly_terrace_059j.py brick-model.json")
    raise SystemExit(main(sys.argv[1]))
