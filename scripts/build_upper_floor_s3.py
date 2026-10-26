"""S-3: ONE 47-piece experimental LEGO upper storey, reusing S-1 unchanged.

S-1 = base, four columns, two load bearing beams and five lower floor
plates. S-3 extends that EXACT model: two parallel WALL SECTIONS made from
10 2x2 bricks in each of two courses, two upper beams and five upper floor
plates. Nothing is moved or overwritten. No roof or user-house dimensions.

S-2 static floor-on-beam tenon/tube proof is reused by reference; it is
NOT rerun for the 20 original pieces. Only the 40 *new* support links are
checked with the existing genuine LDraw connector engine. Real mesh
representatives are sampled only for newly introduced interface types.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import replace
from pathlib import Path
import argparse,json

from lego_geometry_engine import LDrawLibrary,Relation,check_collision,find_connections

try:
    from scripts import build_documented_frame_s1 as s1
except ImportError:
    import build_documented_frame_s1 as s1

# A bounded S-3 prototype with 10-stud walls. Coordinates are inherited from
# S-1's actual beams / lower floor positions, not any GUIDED-004 dimension.
def build():
    original=s1.model()
    base_floor=sorted((p for p in original if p.role=="floor"),key=lambda p:p.x)
    base_beams=sorted((p for p in original if p.role=="beam"),key=lambda p:p.y)
    if len(base_floor)!=5 or len(base_beams)!=2:
        raise ValueError("S3_EXPECTED_S1_TWO_BEAMS_FIVE_DECK_PLATES")
    floor_z=base_floor[0].z+base_floor[0].h
    if not all(p.z+p.h==floor_z for p in base_floor):
        raise ValueError("S3_NONPLANAR_LOWER_DECK")
    xs=[p.x for p in base_floor]
    ys=[p.y for p in base_beams]
    out=list(original)
    for course in range(2):
        for side,y in enumerate(ys):
            for i,x in enumerate(xs):
                name=f"S3-WALL-{side}-SEG-{i}-COURSE-{course}"
                parent=(base_floor[i].id if course==0
                        else f"S3-WALL-{side}-SEG-{i}-COURSE-0")
                out.append(s1.Placement(name,"3003","wall",x,y,
                     floor_z+3*course,2,2,3,
                     parents=(parent,),color=71))
    beam_z=floor_z+6
    for side,y in enumerate(ys):
        first, last=base_floor[0],base_floor[-1]
        if last.x+last.w-first.x!=10:
            raise ValueError("S3_WALL_LENGTH_NOT_SUPPORTED_3006")
        out.append(s1.Placement(f"S3-UPPER-BEAM-{side}","3006","upper_beam",
             first.x,y,beam_z,10,2,3,parents=tuple(
               f"S3-WALL-{side}-SEG-{i}-COURSE-1" for i in range(5)),color=4))
    deck_z=beam_z+3
    for i,old in enumerate(base_floor):
        out.append(s1.Placement(f"S3-UPPER-FLOOR-{i}","3832","upper_floor",
             old.x,old.y,deck_z,old.w,old.d,old.h,rot=old.rot,
             parents=("S3-UPPER-BEAM-0","S3-UPPER-BEAM-1"),color=15))
    assert len(out)==47
    return out

def new_edges(parts):
    by={p.id:p for p in parts}
    return [(p,by[parent]) for p in parts[20:] for parent in p.parents]

def volume_interior_overlaps(parts):
    findings=[]
    for i,p in enumerate(parts):
        for q in parts[i+1:]:
            if min(p.x+p.w,q.x+q.w)<=max(p.x,q.x):continue
            if min(p.y+p.d,q.y+q.d)<=max(p.y,q.y):continue
            if min(p.z+p.h,q.z+q.h)<=max(p.z,q.z):continue
            findings.append([p.id,q.id])
    return findings

def validate_new_connections(parts,root):
    library=LDrawLibrary(root)
    memo={}
    report=[]
    representatives={}
    for up,down in new_edges(parts):
        nominal=s1.stud_mating(up,down)
        if not nominal["valid"]:raise ValueError("S3_MISALIGNED_NEW_SUPPORT:"+up.id)
        if up.id not in memo:memo[up.id]=s1._instance(up,library)
        if down.id not in memo:memo[down.id]=s1._instance(down,library)
        a,b=memo[up.id],memo[down.id]
        connectors=find_connections(a,b)
        key=up.ref+"_TO_"+down.ref
        if key not in representatives:
            relation=Relation.SEPARATED if a.bbox.relation(b.bbox)==Relation.SEPARATED else check_collision(a,b)
            representatives[key]={"upper":up.id,"lower":down.id,
                                   "actual_official_mesh_relation":relation.value}
            print("S3_MESH_REPRESENTATIVE",key,relation.value)
        row={
          "upper":up.id,"lower":down.id,"class":key,
          "nominal_common_studs":nominal["common_stud_cells"],
          "actual_LDraw_stud_cavity_connectors":len(connectors),
          "actual_LDraw_connector_positions":[list(c["position"]) for c in connectors],
          "representative_mesh_relation":representatives[key]["actual_official_mesh_relation"],
          "actual_this_specific_pair_triangle_mesh_scanned":(
            representatives[key]["upper"]==up.id and
            representatives[key]["lower"]==down.id),
          "insertion_continuous":"NOT_PROVEN",
          "physical_load_strength":"NOT_PROVEN"
        }
        report.append(row)
    summary={
        "total_pieces":len(parts),
        "original_S1_pieces_unchanged":20,
        "new_pieces":len(parts)-20,
        "new_support_edges":len(report),
        "new_edges_with_four_real_stud_centres":sum(
            r["nominal_common_studs"]==4 for r in report),
        "new_edges_with_engine_recognized_connectors":sum(
            r["actual_LDraw_stud_cavity_connectors"]>0 for r in report),
        "mesh_representative_classes":len(representatives),
        "mesh_representative_COLLISION_classes":sum(
            x["actual_official_mesh_relation"]=="COLLISION" for x in representatives.values()),
        "mesh_representatives":representatives,
        "full_47_piece_mesh_collision_scan":"NOT_PERFORMED",
        "new_body_AABB_overlaps":len(volume_interior_overlaps(parts)),
        "full_path_47_piece_continuous_insertions_proven":False,
        "physical_stability_certified":False
    }
    print("S3_SUMMARY",json.dumps({k:v for k,v in summary.items() if k!="mesh_representatives"},sort_keys=True))
    return {"summary":summary,"new_edges":report,
      "S2_proof_reused":"missions/S2/RESULTATS-S2.md; all 10 original floor/beam static interfaces only",
      "limits":"New connector alignment measured on all new pairs, full triangle test only on one representative of each shape-class. No insertion continuity or strength proof."}

def path_to_base(p,by):
    visited=[]
    while True:
        if p.id in visited:raise AssertionError("S3_CYCLIC_PATH")
        visited.append(p.id)
        if not p.parents:return visited
        p=by[p.parents[0]]

def assembly(parts):
    return [
       {"step":i+1,"part_id":p.id,"ldraw_reference":p.ref,
        "role":p.role,"resting_on":list(p.parents),
        "vertical_insertion":"PROPOSED_NOT_CONTINUOUSLY_PROVEN"}
       for i,p in enumerate(parts)
    ]

def generate(out,ldrawroot):
    p=build()
    if [s1.ldraw_line(a) for a in p[:20]]!=[s1.ldraw_line(a) for a in s1.model()]:
        raise AssertionError("S3_ORIGINAL_S1_MUST_REMAIN_BYTE_IDENTICAL")
    overlaps=volume_interior_overlaps(p)
    if overlaps:raise AssertionError("S3_ILLEGAL_NOMINAL_BODY_INTERSECTION "+repr(overlaps[:4]))
    by={q.id:q for q in p}
    links=new_edges(p)
    if len(links)!=40 or not all(s1.stud_mating(a,b)["valid"] for a,b in links):
        raise AssertionError("S3_WRONG_NEW_PARENT_LINKS")
    result=validate_new_connections(p,ldrawroot)
    # Stop rather than fabricate geometry if any new real connector is absent.
    if result["summary"]["new_edges_with_engine_recognized_connectors"]!=40:
        raise ValueError("S3_REAL_CONNECTORS_MISSING")
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    model_lines=["0 FILE BOLDUNGO-S3-ONE-UPPER-STOREY.ldr",
      "0 S-3 experimental extension of original 20-part S-1, neither house nor official set.",
      "0 Original S-1 20 placements unchanged; S-2 floor/beam static proof reused.",
      "0 NO ROOF / NO GUIDED-004 / NO INSERTION OR PHYSICAL LOAD CERTIFICATION."]
    previous=""
    for part in p:
        section=("S1-FRAME" if part.id.startswith("S1-") else
                 "WALL-BOTTOM" if part.role=="wall" and part.z==13 else
                 "WALL-TOP" if part.role=="wall" else
                 "UPPER-BEAMS" if part.role=="upper_beam" else "UPPER-DECK")
        if section!=previous:
            if previous:model_lines.append("0 STEP")
            model_lines.append(f"0 // STAGE {section}")
            previous=section
        model_lines.extend([f"0 // {part.id} LINKS {','.join(part.parents)}",
                            s1.ldraw_line(part)])
    model_lines.append("0 NOFILE")
    (out/"S3-PETIT-ETAGE-47-PIECES.ldr").write_text("\n".join(model_lines)+"\n")
    art=s1.svg([replace(x,role={"wall":"column","upper_beam":"beam",
            "upper_floor":"floor"}.get(x.role,x.role)) for x in p])
    art=art.replace("BOLDÜNGO S-1 — Ossature porteuse LEGO","BOLDÜNGO S-3 — Premier petit étage LEGO")
    art=art.replace("20 pièces · base 16×16 · 4 poteaux · 2 poutres · 5 plaques de plancher",
                    "47 pièces · 2 murs partiels · poutres porteuses · plancher supérieur")
    (out/"S3-VUE-3D-SCHEMATIQUE.svg").write_text(art)
    bom=dict(sorted(Counter(x.ref for x in p).items()))
    (out/"S3-NOMENCLATURE.json").write_text(json.dumps({
        "total":len(p),"original_unchanged":20,"added":27,
        "by_ldraw":bom,
        "added_by_ldraw":dict(sorted(Counter(x.ref for x in p[20:]).items())),
        "no_purchase_order":True},indent=2)+"\n")
    (out/"S3-ORDRE-MONTAGE.json").write_text(json.dumps({
        "steps":assembly(p),
        "total_steps_individual_pieces":len(p),
        "additions_only_new_assembly_steps":len(p)-20,
        "continuous_assembly_proven":False},indent=2)+"\n")
    paths={q.id:path_to_base(q,by) for q in p if q.role=="upper_floor"}
    (out/"S3-CHEMINS-APPUI.json").write_text(json.dumps({
        "base":"S1-BASE","upper_floor_paths":paths,
        "links_nominal":sum(len(x.parents) for x in p),
        "links_new":len(links),
        "not_a_mechanical_load_capacity_certification":True},indent=2)+"\n")
    (out/"S3-CONTROLES-CONNEXIONS.json").write_text(json.dumps(result,indent=2)+"\n")
    print("S3_MODEL",json.dumps({"pieces":len(p),"new":len(p)-20,
      "by_ref":bom,"new_connections":len(links),
      "body_overlap_count":len(overlaps),
      "upper_floor_to_base_nominal_paths":len(paths)},sort_keys=True))
    return result

if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--output",type=Path,required=True)
    a.add_argument("--ldraw-root",type=Path,required=True)
    args=a.parse_args()
    generate(args.output,args.ldraw_root)
