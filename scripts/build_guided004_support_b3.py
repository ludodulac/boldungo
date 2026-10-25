"""BOLDUNGO B-3 / last B mission — bridge timber deck to concrete terrace post.

No new geometric engine; 2-for-1 replacement in isolated B-2 model.
At most one single-support-column contact is made:
  board -> timber post -> NEW transverse 1x4 -> concrete support column ->
  concrete support base at local z=0.
Does NOT claim LEGO foundation/baseplate/main-house-wall connection or
mechanical strength/insertion path without separately established evidence.

Selected by model geometry: search for two distinct adjacent post columns,
a common plate-elevation mating plane, and a sole replaceable 1x1 post at
that plane. No GUIDED-specific dimensions or IDs hardcoded.
"""
from __future__ import annotations
import argparse,hashlib,json
from collections import Counter
from pathlib import Path

from brickhouse.bricks.brick_model import BrickModel
from brickhouse.bricks.catalog import standard_orthogonal_definitions
from brickhouse.bricks.connectors import validate_connection
from brickhouse.bricks.geometry_adapter import brick_model_part_to_instance, CANONICAL_LDRAW_PARTS
from lego_geometry_engine import LDrawLibrary,Relation,check_collision,find_connections

try:
    from scripts.build_guided004_connections_b2 import produce as produce_b2,new_part
    from scripts.build_guided004_full_house_b1 import export_ldraw,preview_svg
    from scripts.export_guided004_059m_reinforced import bounds,overlaps,contact_cells
    from scripts.audit_guided004_physical import audit_physical_model
except ModuleNotFoundError:
    from build_guided004_connections_b2 import produce as produce_b2,new_part
    from build_guided004_full_house_b1 import export_ldraw,preview_svg
    from export_guided004_059m_reinforced import bounds,overlaps,contact_cells
    from audit_guided004_physical import audit_physical_model

def _columns(base):
    p={part.placement_id:part for part in base.parts}
    timber=[q for q in p.values() if "support-solution:timber-post" in q.placement_id
            and q.part_id=="BRICK_1X1"]
    concrete=[q for q in p.values() if "support-solution:concrete-support" in q.placement_id
              and q.part_id=="BRICK_2X2"]
    if not timber or not concrete: raise ValueError("B3_MISSING_TIMBER_OR_CONCRETE_PILLAR")
    return p,timber,concrete

def find_candidate(base):
    by,timber,concrete=_columns(base)
    candidates=[]
    reasons=Counter()
    examples=[]
    # Merge one existing 2x2 concrete post course and one parallel 1x1
    # timber post course AT THE SAME LEVEL into a LEGO 2x4, leaving the
    # surrounding courses, scene, roof, boards and architecture untouched.
    for c in concrete:
        cbox=bounds(c)
        for old in timber:
            obox=bounds(old)
            if obox[2]!=cbox[2]:
                continue
            reasons["matching_plane"]+=1
            if not any(other.placement_id!=old.placement_id
                       and other.part_id=="BRICK_1X1" and
                       bounds(other)[2]==obox[5]
                       and bounds(other)[:2]==obox[:2] for other in timber):
                continue
            gapx=max(0,cbox[0]-obox[3],obox[0]-cbox[3])
            gapy=max(0,cbox[1]-obox[4],obox[1]-cbox[4])
            if gapx!=0 or gapy>2:continue
            reasons["adjacent_posts"]+=1
            if len(examples)<3: examples.append({"old":old.placement_id,"concrete":c.placement_id,"old_box":obox,"concrete_box":cbox})
            # 2x4 fills exactly the 2x2 concrete footprint and bridges
            # the one-stud gap to the 1x1 timber footprint.
            candidate=new_part("EXPERIMENT-B3-CONCRETE-TO-TIMBER-BRIDGE",
                    "BRICK_2X4",cbox[0],cbox[1],obox[2],0)
            nb=bounds(candidate)
            # Both original post segments must be contained, and a
            # timber column must continue BELOW and ABOVE.
            if not all(nb[k]<=o[k] and o[k+3]<=nb[k+3] for k in (0,1) for o in (cbox,obox)):
                reasons["not_in_2x4_span"]+=1
                continue
            underneath=[t for t in timber if t.placement_id!=old.placement_id
                        and bounds(t)[5]==nb[2] and contact_cells(t,candidate)]
            upper=[t for t in timber if t.placement_id!=old.placement_id
                   and bounds(t)[2]==nb[5] and contact_cells(candidate,t)]
            con_lower=[q for q in concrete if q.placement_id!=c.placement_id
                       and bounds(q)[5]==nb[2] and bounds(q)[:2]==cbox[:2]]
            if not underneath or not upper or not con_lower:
                reasons["no_under_over"]+=1
                continue
            reasons["upper_and_lower"]+=1
            conflicted=[q.placement_id for q in base.parts
                if q.placement_id not in (old.placement_id,c.placement_id)
                and bounds(q) is not None and overlaps(nb,bounds(q))]
            if conflicted:
                reasons["collision"]+=1
                if len(examples)<6:examples.append({"new_box":nb,"colliders":conflicted[:7]})
                continue
            candidates.append((old,c,candidate,underneath,upper,con_lower))
    if not candidates:raise ValueError("B3_NO_SAFE_CONCRETE_TIMBER_COLUMN_BRIDGE")
    # Favor shortest span with min empty middle and stable deterministic ID.
    def rank(v):
        old,c,bridge,under,up,con_lower=v
        b=bounds(bridge);a=bounds(c)
        return (-a[2],abs(b[1]-a[1]),b[0],b[1],old.placement_id)
    candidates.sort(key=rank)
    return candidates[0]

def replace_one(base):
    old,concrete,bridge,under,upper,con_lower=find_candidate(base)
    original={p.placement_id:p.model_dump(mode="json") for p in base.parts}
    after=base.model_copy(update={"parts":[p for p in base.parts
           if p.placement_id not in (old.placement_id,concrete.placement_id)]+[bridge]})
    changed={p.placement_id:p.model_dump(mode="json") for p in after.parts}
    if set(original)-set(changed)!={old.placement_id,concrete.placement_id}:
        raise AssertionError("B3_WRONG_DELETIONS")
    if set(changed)-set(original)!={bridge.placement_id}:
        raise AssertionError("B3_WRONG_ADDITIONS")
    if any(changed[k]!=v for k,v in original.items() if k not in (old.placement_id,concrete.placement_id)):
        raise AssertionError("B3_OTHER_ORIGINAL_PART_MOVED")
    return after,{"removed":[old.placement_id,concrete.placement_id],"added":bridge.placement_id,
            "former_post":old,"new_bridge":bridge,"concrete":concrete,
            "lower_timber_supports":under,"upper_timber_supports":upper,
            "concrete_lower_support":con_lower[0]}

def _mesh_edge(lib,a,b):
    aa=brick_model_part_to_instance(a,lib)
    bb=brick_model_part_to_instance(b,lib)
    relation=(Relation.SEPARATED if aa.bbox.relation(bb.bbox)==Relation.SEPARATED
              else check_collision(aa,bb))
    connects=find_connections(aa,bb)
    return {"from":a.placement_id,"to":b.placement_id,
        "from_ref":CANONICAL_LDRAW_PARTS[a.part_id].ldraw_id,
        "to_ref":CANONICAL_LDRAW_PARTS[b.part_id].ldraw_id,
        "mesh_relation":relation.value,
        "explicit_stud_cavity_connector_count":len(connects),
        "connector_positions_ldu":[x["position"] for x in connects],
        "geometry_supported":bool(connects) and relation!=Relation.COLLISION,
        "continuous_insertion_verified":False,
        "physical_strength_certified":False}

def prove_local_chain(after,context,ldrawroot):
    by={p.placement_id:p for p in after.parts}
    bridge=context["new_bridge"]
    under=context["lower_timber_supports"][0]
    upper=context["upper_timber_supports"][0]
    concrete=context["concrete_lower_support"]
    # Existing terrace concrete support extends downward through exactly
    # aligned LEGO bricks until it reaches the local modeled ground datum.
    downward=[concrete]
    while bounds(downward[-1])[2]>0:
        top=bounds(downward[-1])[2]
        matches=[p for p in after.parts if p.part_id==concrete.part_id
                 and p.placement_id!=downward[-1].placement_id
                 and bounds(p) is not None and bounds(p)[5]==top
                 and bounds(p)[:2]==bounds(concrete)[:2]]
        if len(matches)!=1:break
        downward.append(matches[0])
    timber_column=[upper]
    while True:
        last=timber_column[-1]
        next_parts=[p for p in after.parts
            if p.part_id=="BRICK_1X1" and bounds(p) is not None
            and bounds(p)[:2]==bounds(upper)[:2]
            and bounds(p)[2]==bounds(last)[5]]
        if len(next_parts)!=1:break
        timber_column.append(next_parts[0])
    floor=[p for p in after.parts if ":south-timber-deck-main:board:" in p.placement_id
           and bounds(p) is not None and contact_cells(timber_column[-1],p)]
    if not floor:raise AssertionError("B3_NO_DECK_BOARD_AT_TOP_POST")
    path=[floor[0],*list(reversed(timber_column)),bridge,concrete,*downward[1:]]
    # Strictly contiguous, no repeated parts; physical source is a concrete
    # terrace support rather than a load path into the primary house walls.
    if len(set(p.placement_id for p in path))!=len(path):
        raise AssertionError("B3_CHAIN_DUPLICATE")
    if bounds(path[-1])[2]!=0:raise AssertionError("B3_SUPPORT_DOES_NOT_REACH_LEVEL_ZERO")
    lib=LDrawLibrary(ldrawroot)
    edges=[_mesh_edge(lib,a,b) for a,b in zip(path,path[1:])]
    branch_under=_mesh_edge(lib,under,bridge)
    output={"path_ids":[p.placement_id for p in path],
       "path_part_refs":[CANONICAL_LDRAW_PARTS[p.part_id].ldraw_id for p in path],
       "path_edges":edges,
       "additional_timber_branch":branch_under,
       "edges_positive_stud_cavity":sum(e["geometry_supported"] for e in edges),
       "edges_total":len(edges),
       "last_established_edge":next((i-1 for i,e in enumerate(edges) if not e["geometry_supported"]),len(edges)-1),
       "first_unproven_edge":next((i for i,e in enumerate(edges) if not e["geometry_supported"]),None),
       "reaches_modeled_z0":bounds(path[-1])[2]==0,
       "reaches_main_house_wall_or_LEGO_baseplate":"NOT_PROVEN",
       "true_stability_and_load_transmission":"NOT_CERTIFIED",
       "continuous_insertions":"NOT_PROVEN"}
    print("B3_CHAIN",json.dumps({k:output[k] for k in ("edges_positive_stud_cavity","edges_total","first_unproven_edge","reaches_modeled_z0")}))
    for edge in edges: print("B3_MESH_LINK",edge["from"],"->",edge["to"],edge["mesh_relation"],edge["explicit_stud_cavity_connector_count"])
    return output

def produce(output,ldrawroot):
    output=Path(output)
    from_b2=output/"REGENERATED-B2-SOURCE-READONLY"
    produce_b2(from_b2,ldrawroot)
    source=from_b2/"EXPERIMENTAL-1905-FULL-HOUSE"/"BRICKMODEL-B2-1905.json"
    src=source.read_bytes()
    initial=BrickModel.model_validate_json(src)
    variant,ctx=replace_one(initial)
    audit0=audit_physical_model(initial)
    audit1=audit_physical_model(variant)
    if audit1["collision_voxel_overlaps"]!=0:
        raise AssertionError("B3_NEW_BRIDGE_CAUSES_ORTHOGONAL_COLLISION")
    path=prove_local_chain(variant,ctx,ldrawroot)
    dst=output/"B3-EXPERIMENTAL-1905"
    dst.mkdir(parents=True,exist_ok=True)
    info=export_ldraw(variant,LDrawLibrary(ldrawroot),
                      dst/"GUIDED004-B3-1905.ldr","GUIDED004_B3_1905")
    if info["unmapped_count"] or info["ldraw_type1_count"]!=len(variant.parts):
        raise AssertionError("B3_LDRAW_MISSING_ORIGIN")
    preview_svg(variant,dst/"B3-FULL-HOUSE-SCHEMATIC.svg")
    (dst/"BRICKMODEL-B3-1905.json").write_text(variant.model_dump_json(indent=2)+"\n")
    (dst/"CHAIN-PROOF-LOCAL.json").write_text(json.dumps(path,indent=2,ensure_ascii=False)+"\n")
    delta={"b2_parts":len(initial.parts),"b3_parts":len(variant.parts),
      "added_ids":[ctx["added"]],"removed_ids":ctx["removed"],
      "moved_ids":[],"floor_original_positions_preserved":True,
      "b2_sha256":hashlib.sha256(src).hexdigest(),
      "b2_bytes_unchanged":source.read_bytes()==src,
      "b2_orthogonal_unsupported":audit0["unsupported_parts"],
      "b3_orthogonal_unsupported":audit1["unsupported_parts"],
      "b2_orthogonal_components":audit0["connected_components_orthogonal_stud_contact"],
      "b3_orthogonal_components":audit1["connected_components_orthogonal_stud_contact"],
      "b2_orthogonal_collisions":audit0["collision_voxel_overlaps"],
      "b3_orthogonal_collisions":audit1["collision_voxel_overlaps"],
      "b2_roof_unverified":audit0["roof_parts_unverified"],
      "b3_roof_unverified":audit1["roof_parts_unverified"],
      "chain_established":path["edges_positive_stud_cavity"]==path["edges_total"],
      "chain_to_z0":path["reaches_modeled_z0"],
      "chain_to_primary_house":"NOT_PROVEN",
      "full_house_mesh_collision_exhaustive":"NOT_TESTED",
      "physical_strength":"NOT_CERTIFIED"}
    (dst/"B2-VS-B3.json").write_text(json.dumps(delta,ensure_ascii=False,indent=2)+"\n")
    bom={"parts":len(variant.parts),
         "by_part":dict(sorted(Counter(p.part_id for p in variant.parts).items())),
         "added":{ctx["new_bridge"].part_id:1},
         "removed":{ctx["former_post"].part_id:1,ctx["concrete"].part_id:1},
         "procurement":False}
    (dst/"BOM-B3.json").write_text(json.dumps(bom,ensure_ascii=False,indent=2)+"\n")
    orig_plan=json.loads((from_b2/"EXPERIMENTAL-1905-FULL-HOUSE"/"ORDER-B2-NOT-CERTIFIED.json").read_text())
    plan={"proposed_stages_before_B3":orig_plan["full_house_steps"],
       "B3_changed_internal_post_stage":{
         "remove_old":ctx["removed"],"replace_with":ctx["added"],
         "prerequisite":"Build concrete and timber columns to replacement elevation; insert horizontal bridge then upper timber post and floor.",
         "full_continuous_insertion":"NOT_PROVEN"},
       "proposed_stages_B3":orig_plan["full_house_steps"],
       "existing_B2_order_is_preserved_except_one_replacement":True,
       "complete_build_certification":"NOT_PROVEN"}
    (dst/"ORDER-B3-PROPOSED.json").write_text(json.dumps(plan,indent=2,ensure_ascii=False)+"\n")
    print("B3_HOUSE",json.dumps(delta,sort_keys=True))
    return delta

if __name__=="__main__":
    cli=argparse.ArgumentParser()
    cli.add_argument("--ldraw-root",type=Path,required=True)
    cli.add_argument("--output",type=Path,required=True)
    a=cli.parse_args()
    produce(a.output,a.ldraw_root)
