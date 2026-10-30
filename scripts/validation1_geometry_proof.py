"""VALIDATION-1: single bounded, honest 10-part geometry test. Never rebuild source house.

Uses pinned official LDraw mirror and existing geometry-engine predicates.
Mesh COLLISION with nominal aligned connectors is not silently certified as
solid-free; missing connector metadata is NOT replaced by conjecture.
"""
from __future__ import annotations
import argparse, json, hashlib
from pathlib import Path
from collections import deque
from itertools import combinations
from lego_geometry_engine import LDrawLibrary, Relation, check_collision, find_connections, instantiate, transform_from_ldraw, assess_pair, first_mesh_crossing

ROOT=Path(__file__).resolve().parents[1]
DIR=ROOT/"missions/VALIDATION1"
SOURCE=ROOT/"frontend/data/guided004-maison4-356-brickhouse.json"

def dump(name,payload):
    (DIR/name).write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def bbox(p):
    w,d=p["width_studs"],p["length_studs"]
    if p["rotation_quarter_turns"]%2:w,d=d,w
    return (p["x_studs"],p["y_studs"],p["z_plates"],
            p["x_studs"]+w,p["y_studs"]+d,p["z_plates"]+p["height_plates"])

def contacts(a,b):
    if a[2]!=b[5]:return 0
    return max(0,min(a[3],b[3])-max(a[0],b[0]))*max(0,min(a[4],b[4])-max(a[1],b[1]))

def inside(a,b):
    return all(min(a[i+3],b[i+3])>max(a[i],b[i]) for i in range(3))

def main(ldraw):
    prov=json.loads((DIR/"PROVENANCE.json").read_text())
    full=json.loads(SOURCE.read_text())
    little=json.loads((DIR/"VIEWER-10.json").read_text())
    exact=full["brick_model"]["parts"]
    lookup={p["placement_id"]:p for p in exact}
    ids=prov["ids_order"]
    assert len(exact)==356 and len(ids)==10 and len(set(ids))==10
    assert [p["placement_id"] for p in little["brick_model"]["parts"]]==ids
    for part in little["brick_model"]["parts"]:
        assert part==lookup[part["placement_id"]], "ORIGINAL_356_PART_CHANGED: "+part["placement_id"]
    assert little["bom"]["total_parts"]==10
    records={}
    marker=None
    for line in (DIR/"EST-SUD-10.ldr").read_text().splitlines():
        if line.startswith("0 // "):
            marker=line
            continue
        if not line.startswith("1 "):continue
        assert marker is not None
        t=line.split()
        assert len(t)==15
        pid=marker.split()[3]
        assert pid not in records
        records[pid]=t
        marker=None
    assert set(records)==set(ids), "LDraw source selected IDs missing / duplicated"
    selected=[lookup[i] for i in ids]
    instances=[]
    actual_defs={}
    for p in selected:
        t=records[p["placement_id"]]
        raw_values=[float(n) for n in t[2:14]]
        assert [int(n) for n in raw_values[:3]]==p["ldraw_xyz_ldu"]
        assert [int(n) for n in raw_values[3:]]==p["ldraw_matrix"]
        assert t[14].lower()==p["ldraw_ref"].lower()
        assert int(t[1])==p["ldraw_color"]
        definition=LDrawLibrary(ldraw).load_part(t[14])
        # New instance object uses the exact original 12 LDraw transformation values.
        instance=instantiate(definition,p["placement_id"],transform_from_ldraw(raw_values),int(t[1]))
        assert definition.triangles, "OFFICIAL_LDRAW_GEOMETRY_MISSING: "+p["placement_id"]
        instances.append(instance)
        actual_defs[p["placement_id"]]={"ldraw_ref":t[14],"mesh_triangles":len(definition.triangles),
                                         "connectors_inferred":len(definition.connectors),
                                         "description":definition.description,
                                         "geometry_source":"PINNED_LDRAW_MIRROR"}

    boxes={p["placement_id"]:bbox(p) for p in selected}
    nominal_collisions=[]
    edges=[]
    for a,b in combinations(ids,2):
        if inside(boxes[a],boxes[b]):nominal_collisions.append([a,b])
    for up in ids:
        for low in ids:
            if up==low:continue
            n=contacts(boxes[up],boxes[low])
            if n:edges.append({"upper":up,"lower":low,"common_nominal_studs":n})
    assert not nominal_collisions, "SELECTED_GRID_COLLISIONS"
    assert len(edges)==13, "SELECTED_NOMINAL_SUPPORT_GRAPH_CHANGED"
    byid={p.instance_id:p for p in instances}
    mesh_pairs=[]
    for a,b in combinations(ids,2):
        A,B=byid[a],byid[b]
        # Always inspect official matching connectors; broad-phase avoid needless
        # expensive fine-mesh checks for remote pieces.
        con=find_connections(A,B)
        if A.bbox.relation(B.bbox) is Relation.SEPARATED:
            relation="SEPARATED"
        else:
            relation=check_collision(A,B).value
        edge=next((x for x in edges if {x["upper"],x["lower"]}=={a,b}),None)
        nominal_mating=edge is not None
        verdict=assess_pair(A,B,relation=Relation(relation),connections=con)
        classification={
            "COMPATIBLE_MATING":"CONNECTOR_MATCH_MESH_NO_COLLISION",
            "FORBIDDEN_COLLISION":"UNRESOLVED_MESH_COLLISION_NOT_CLEARED",
            "INDETERMINATE":"NOMINAL_STUD_CAVITY_MATING_MESH_INTERFERENCE_NOT_CERTIFIED",
            "NO_MECHANICAL_LINK":"SURFACE_CONTACT_NOT_PROOF_OF_CLUTCH",
        }[verdict.verdict]
        witness=(first_mesh_crossing(A,B) if relation=="COLLISION" and con and nominal_mating else None)
        if relation!="SEPARATED" or con or nominal_mating:
            mesh_pairs.append({"part_a":a,"part_b":b,
                "official_mesh_relation":relation,"connector_matches":len(con),
                "nominal_support_studs":edge["common_nominal_studs"] if edge else 0,
                "classification":classification,"engine_verdict":verdict.verdict,
                "body_aabb_ldu":verdict.body_a,"body_b_aabb_ldu":verdict.body_b,
                "verified_body_overlap":verdict.body_overlap,
                "precise_mesh_surface_crossing":witness,
                "mesh_crossing_is_not_proof_of_solid_material":True})
    for e in edges:
        m=next(q for q in mesh_pairs if {q["part_a"],q["part_b"]}=={e["upper"],e["lower"]})
        e.update({"official_mesh_relation":m["official_mesh_relation"],
                  "official_connector_matches":m["connector_matches"],
                  "joint_status":"PASS_NOMINAL_CONNECTOR" if m["connector_matches"]>0
                         and m["official_mesh_relation"]!="COLLISION" else "NON DÉMONTRÉ"})
    base=ids[0]
    connectors_to_base=[e for e in edges if e["lower"]==base]
    failing_base=[e for e in connectors_to_base if e["official_connector_matches"]==0]
    # Support is only demonstrated by a complete connector-verified path to the
    # base. The baseplate connector metadata may be absent — do not invent it.
    anchored={base}
    while True:
        nxt={e["upper"] for e in edges if e["lower"] in anchored and e["joint_status"]=="PASS_NOMINAL_CONNECTOR"}
        if nxt<=anchored:break
        anchored|=nxt
    unknown_support=[p for p in ids if p not in anchored]
    solid_collision=[p for p in mesh_pairs if p["classification"]=="UNRESOLVED_MESH_COLLISION_NOT_CLEARED"]
    ambiguous_collision=[p for p in mesh_pairs if p["classification"]=="NOMINAL_STUD_CAVITY_MATING_MESH_INTERFERENCE_NOT_CERTIFIED"]
    insertion=[]
    placed=[]
    for pid in ids:
        box=boxes[pid]
        obstructing=[old for old in placed if
                     min(box[3],boxes[old][3])>max(box[0],boxes[old][0])
                     and min(box[4],boxes[old][4])>max(box[1],boxes[old][1])
                     and boxes[old][5]>box[2]]
        supports=[e["lower"] for e in edges if e["upper"]==pid and e["lower"] in placed]
        insertion.append({"piece":pid,"approach":"VERTICAL_FROM_ABOVE",
            "nominal_swept_box_clear":not bool(obstructing),
            "nominal_sweep_obstacles":obstructing,
            "preexisting_nominal_support":supports,
            "full_official_mesh_continuous_insertion":"NON DÉMONTRÉ"})
        placed.append(pid)
    ambiguous_edge=next((e for e in edges if e["joint_status"]!="PASS_NOMINAL_CONNECTOR"),None)
    first_problem=(
        {"piece":failing_base[0]["upper"],"interface":failing_base[0]["lower"],
         "reason":"Base connector not recognized: no demonstrated structural link to the 3811 baseplate."}
        if failing_base else
        {"piece":solid_collision[0]["part_a"],"interface":solid_collision[0]["part_b"],
         "reason":"Mesh intersection without a mating connector: collision not cleared."}
        if solid_collision else
        {"piece":ambiguous_edge["upper"],"interface":ambiguous_edge["lower"],
         "reason":"Aligned nominal connectors found, but official LDraw mesh reports COLLISION; legal stud/cavity engagement versus forbidden solid penetration is NOT resolved."}
        if ambiguous_edge else
        {"piece":ids[0],"interface":None,"reason":"Continuous official-mesh insertion and physical stability are not certified."}
    )
    connection_status=("FAIL" if any(e["official_connector_matches"]==0 for e in edges) else
                       "NON DÉMONTRÉ" if ambiguous_collision else "PASS")
    collisions_status=("FAIL" if solid_collision else
                       "NON DÉMONTRÉ" if ambiguous_collision else "PASS")
    support_status="FAIL" if unknown_support else "PASS"
    insertion_status="NON DÉMONTRÉ" if all(x["nominal_swept_box_clear"] for x in insertion) else "FAIL"
    final={
        "engine_fix":"COLLISION_WITH_CONNECTOR_NO_LONGER_AUTO_CONTACT; surface-only contacts never support",
        "seven_ambiguous_interfaces_located":[p for p in mesh_pairs if p["classification"]=="NOMINAL_STUD_CAVITY_MATING_MESH_INTERFERENCE_NOT_CERTIFIED"],
        "roof_interface":"NON DÉMONTRÉ — module has unresolved intersections, roof follow-up prohibited by mission safety gate",
        "status":"FAIL" if connection_status=="FAIL" or collisions_status=="FAIL" or support_status=="FAIL" else "NON DÉMONTRÉ",
        "selected_count":len(ids),"real_LDraw_refs":len({p["ldraw_ref"] for p in selected}),
        "official_ldraw_geometry_all_loaded":True,
        "connections":connection_status,"collisions":collisions_status,
        "appuis":support_status,"insertion":insertion_status,
        "nominal_vertical_sweep":"PASS" if all(x["nominal_swept_box_clear"] for x in insertion) else "FAIL",
        "visualization":"NON DÉMONTRÉ (browser run separate in same CI campaign)",
        "first_blocker":first_problem,
        "physical_stability":"NON DÉMONTRÉ","real_lego_hands_test":"NOT_DONE",
        "certify_strength":False,"certify_buildable":False,
        "limits":["Official LDraw mesh is not a certified collision/fastening simulator.",
                  "3811 stud/cavity connector grid inferred. Raw mesh intersections are kept indeterminate; actual crossing coordinates recorded, not silently accepted.",
                  "Nominal top-down bounding-box path does not prove full real part insertion."]}
    dump("CONNEXIONS-COLLISIONS.json",{"geometry_loaded":actual_defs,
        "nominal_solid_overlaps":nominal_collisions,"nominal_edges":edges,
        "official_mesh_pairs_examined":mesh_pairs,"unresolved_solid_intersections":solid_collision,
        "undecided_stud_cavity_mesh_overlap":ambiguous_collision,
        "status_connections":connection_status,"status_collisions":collisions_status})
    dump("APPUIS.json",{"base":base,"nominal_supports":edges,
         "base_connectors_recognized":connectors_to_base,
         "rooted_via_recognized_noncolliding_connections":sorted(anchored),
         "not_proven_attached_to_base":unknown_support,"status":support_status})
    dump("INSERTION.json",{"path_type":"STRAIGHT_DOWN_LDRAW_VERTICAL",
         "ordered_original_placement_ids":ids,"per_step":insertion,
         "nominal_sweep_clear":all(x["nominal_swept_box_clear"] for x in insertion),
         "continuous_official_mesh_trajectory":"NON DÉMONTRÉ",
         "physical_insertion":"NON DÉMONTRÉ","status":insertion_status})
    dump("RESULTAT.json",final)
    print("VALIDATION1_MEASURED="+json.dumps({k:final[k] for k in
          ("status","selected_count","real_LDraw_refs","connections","collisions","appuis","insertion","first_blocker")},ensure_ascii=False),
          flush=True)
    # Mission success = reproducible truthful report, not assertion that LEGO is buildable.

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--ldraw-root",type=Path,required=True)
    args=parser.parse_args()
    main(args.ldraw_root)
