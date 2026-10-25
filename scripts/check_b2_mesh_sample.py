"""B-2: exactly one old 088 ridge interface and the repaired deck seam.

Actual pinned public official LDraw solid meshes, using the ALREADY EXISTING
geometry engine. This is a BOUNDED sample, NOT an exhaustive house audit and
never turns CONTACT into certified stud/tube clutch or insertion.
"""
from __future__ import annotations
import argparse,json,re
from pathlib import Path
from lego_geometry_engine import LDrawLibrary,Relation,check_collision,find_connections
from brickhouse.bricks.brick_model import BrickModel
from brickhouse.bricks.geometry_adapter import brick_model_part_to_instance

def sample(path,library_root):
    m=BrickModel.model_validate_json(Path(path).read_bytes())
    parts={p.placement_id:p for p in m.parts}
    root=LDrawLibrary(library_root)
    placements={}
    def lookup(k):
        if k not in placements:
            placements[k]=brick_model_part_to_instance(parts[k],root)
        return placements[k]
    seam=next(p for p in m.parts if p.placement_id.startswith("EXPERIMENT-B2-DECK-SEAM-"))
    # derive neighbor from real b2 footprint, not any GUIDED-004 coordinates
    bx=seam.x_studs;by=seam.y_studs;bz=seam.z_plates+1
    neighbor=next(p for p in m.parts if p.part_id=="BRICK_2X3"
        and p.component=="facade_detail" and p.z_plates==bz
        and p.x_studs==bx and p.y_studs<=by<p.y_studs+3)
    orphan=next(p for p in m.parts if p.part_id=="BRICK_1X3"
        and p.component=="facade_detail" and p.z_plates==bz
        and p.x_studs==bx+2 and p.y_studs<=by<p.y_studs+3)
    ridge=next(p for p in m.parts if p.placement_id.startswith("EXPERIMENT-088-JOINT-"))
    roof_ids=re.findall(r"roof-\d+",ridge.placement_id)
    if len(roof_ids)!=2 or not all(k in parts for k in roof_ids):
        raise ValueError("B2_RIDGE_SAMPLE_NO_EXACT_PAIR")
    samples=[("deck_2x3_plate",seam.placement_id,neighbor.placement_id),
       ("deck_1x3_plate",seam.placement_id,orphan.placement_id),
       ("ridge_30363_left",ridge.placement_id,roof_ids[0]),
       ("ridge_30363_right",ridge.placement_id,roof_ids[1])]
    observed=[]
    for kind,a,b in samples:
        ia,ib=lookup(a),lookup(b)
        rel=Relation.SEPARATED if ia.bbox.relation(ib.bbox)==Relation.SEPARATED else check_collision(ia,ib)
        connections=find_connections(ia,ib)
        row={"interface":kind,"parts":[a,b],
             "actual_official_LDraw_mesh_relation":rel.value,
             "explicit_compatible_connectors_from_current_engine":len(connections),
             "if_COLLISION_it_is_not_silently_reclassified":True,
             "positive_clutch_and_continuous_insertion":"NOT_DEMONSTRATED"}
        observed.append(row)
        print("B2_MESH_PAIR",kind,rel.value,"EXPLICIT_CONNECTORS",len(connections))
    result={"checked_distinct_pairs":len(observed),
        "checked_actual_pinned_official_mesh":True,
        "sampled_not_exhaustive":True,
        "pairs":observed,
        "interference_signals_in_sample":sum(q["actual_official_LDraw_mesh_relation"]=="COLLISION" for q in observed),
        "separated_pairs_in_sample":sum(q["actual_official_LDraw_mesh_relation"]=="SEPARATED" for q in observed),
        "roof_fully_verified":"NO",
        "connector_clutch_proven":"NO",
        "all_real_insertions_proven":"NO",
        "full_house_mesh_collision_count":"UNKNOWN"}
    print("B2_MESH_SUMMARY",json.dumps({k:v for k,v in result.items() if k!="pairs"},sort_keys=True))
    return result

if __name__=="__main__":
    cli=argparse.ArgumentParser()
    cli.add_argument("--model",type=Path,required=True)
    cli.add_argument("--ldraw-root",type=Path,required=True)
    cli.add_argument("--output",type=Path,required=True)
    a=cli.parse_args()
    report=sample(a.model,a.ldraw_root)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
