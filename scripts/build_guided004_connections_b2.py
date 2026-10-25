"""B-2: join the isolated timber-deck board using actual LEGO plates/braces.

Not a new audit engine. Reuses B-1 full-house exporter, old 059L floor
connectivity / vertical AABB insertion tests, 059M known safe 3008/3623
solution, and canonical LDraw adapter. Geometry and seam coordinates are
inferred from the INPUT HOUSE rather than copied from GUIDED-004 constants.

Every B-1 part is immutable and retains its position; four additional
experimental pieces are generated in a new named B-2 model.
"""
from __future__ import annotations

import argparse,hashlib,json
from collections import Counter
from pathlib import Path

from brickhouse.bricks.brick_model import BrickModel,BrickModelPart
from brickhouse.bricks.catalog import standard_orthogonal_definitions
from brickhouse.bricks.geometry_adapter import CANONICAL_LDRAW_PARTS
from lego_geometry_engine import LDrawLibrary

try:
    from scripts.build_guided004_full_house_b1 import build as build_b1,export_ldraw,preview_svg
    from scripts.audit_guided004_physical import audit_physical_model
    from scripts.audit_terrace_059l_full_house_install import components,blocked
    from scripts.export_guided004_059m_reinforced import bounds,overlaps,contact_cells
except ModuleNotFoundError:
    from build_guided004_full_house_b1 import build as build_b1,export_ldraw,preview_svg
    from audit_guided004_physical import audit_physical_model
    from audit_terrace_059l_full_house_install import components,blocked
    from export_guided004_059m_reinforced import bounds,overlaps,contact_cells

SCOPE="B2_EXPERIMENTAL_FLOOR_LINK_NOT_PHYSICALLY_CERTIFIED"

def original_floor(model):
    return [p for p in model.parts
        if p.placement_id.startswith("scene-platform:south-timber-deck-")
        and (":board:" in p.placement_id or ":hidden-" in p.placement_id)]

def _rect_intersection(a,b):
    return (max(0,min(a[3],b[3])-max(a[0],b[0]))
            *max(0,min(a[4],b[4])-max(a[1],b[1])))

def new_part(pid,part_id,x,y,z,rotation):
    d=standard_orthogonal_definitions()[part_id]
    w,l=d.footprint(rotation)
    return BrickModelPart(placement_id=pid,part_id=part_id,
        category="plate" if part_id.startswith("PLATE") else "brick",
        component="roof_support",x_studs=x,y_studs=y,z_plates=z,
        rotation_quarter_turns=rotation,width_studs=w,length_studs=l,
        height_plates=d.height_plates)

def _two_host_plate_clearance(plate,neighbor,orphan):
    """Bounded replica of existing 059M stud-grid & 3002/3622 cavities.

    Nominal 3623 plate studs R=6 LDU. 3002 2x3 underside has sidewall
    +/-16, endwall +/-26, tube axes at local longitudinal +/-10 with R=8.
    3622 1x3 underside has +/-6 sidewall and anti-stud3 R=4.
    This is a local clearance check, not a full mesh/torque proof.
    """
    if (plate.part_id!="PLATE_1X3" or plate.rotation_quarter_turns!=1
         or neighbor.part_id!="BRICK_2X3" or orphan.part_id!="BRICK_1X3"):
        return False,{"reason":"EXPECTED_PLATE_1X3_JOINING_2X3_TO_1X3"}
    if neighbor.z_plates!=orphan.z_plates or plate.z_plates+1!=orphan.z_plates:
        return False,{"reason":"INCORRECT_ENGAGEMENT_PLANE"}
    contacts={p.placement_id:contact_cells(plate,p) for p in (neighbor,orphan)}
    if (len(contacts[neighbor.placement_id])!=2
        or len(contacts[orphan.placement_id])!=1):
        return False,{"reason":"NOT_2_PLUS_1_STUDS","contacts":contacts}
    import math
    margins=[]
    for upper in (neighbor,orphan):
        for x,y in contacts[upper.placement_id]:
            upper_len=bounds(upper)[4]-bounds(upper)[1]
            upper_width=bounds(upper)[3]-bounds(upper)[0]
            longitudinal=(y-upper.y_studs)*20 - (upper_len-1)*10
            end=upper_len*10-4-(abs(longitudinal)+6)
            if upper.part_id=="BRICK_2X3":
                transverse=(x-upper.x_studs)*20-(upper_width-1)*10
                side=upper_width*10-4-(abs(transverse)+6)
                tube=min(math.hypot(transverse,longitudinal-t)-14 for t in (-10,10))
                margins.append({"host":upper.placement_id,"grid":[x,y],
                                "side_gap_ldu":side,"end_gap_ldu":end,
                                "tube_clearance_ldu":tube})
                if side<0 or end<0 or tube<=0:return False,{"margins":margins}
            else:
                side=6-6
                anti_stud=min(abs(longitudinal-t)-(6+4) for t in (-10,10))
                margins.append({"host":upper.placement_id,"grid":[x,y],
                  "side_gap_ldu":side,"end_gap_ldu":end,
                  "anti_stud3_gap_ldu":anti_stud})
                if side<0 or end<0 or anti_stud<0:return False,{"margins":margins}
    return True,{"interface":"stud_into_underside_2X3_and_1X3",
        "checked_stud_cells":3,"margins":margins,
        "clearance_status":"POSITIONS_COMPATIBLE_IN_TARGETED_OFFICIAL_DAT_CROSS_SECTION",
        "full_mesh_clutch_and_insertion":"NOT_PROVEN"}

def create_deck_reinforcement(b1):
    """Find the orphan board and bridge it to its neighboring board.

    This intentionally accepts only a verified deck topology; other house
    dimensions/arrangements fail closed instead of inventing bridge positions.
    """
    original_bytes=b1.model_dump_json()
    floor=original_floor(b1)
    sizes,isolated=components([p.model_dump(mode="json") for p in floor])
    if len(isolated)!=1 or sizes!=[len(floor)-1,1]:
        raise ValueError("B2_NO_SINGLE_ORPHAN_BOARD_EXPECTED_TOPOLOGY")
    by={p.placement_id:p for p in b1.parts}
    orphan=by[isolated[0]]
    if orphan.part_id!="BRICK_1X3":
        raise ValueError("B2_ORPHAN_BOARD_NOT_1X3")
    o=bounds(orphan)
    alternatives=[]
    for near in floor:
        if near.part_id!="BRICK_2X3" or near.z_plates!=orphan.z_plates:
            continue
        b=bounds(near)
        if b[3]==o[0] and b[1]==o[1] and b[4]==o[4]:
            alternatives.append(near)
    if len(alternatives)!=1:
        raise ValueError("B2_NO_SINGLE_ADJACENT_2X3_SEAM")
    neighbor=alternatives[0]
    nb=bounds(neighbor)
    if nb[3]-nb[0]!=2 or o[3]-o[0]!=1 or o[4]-o[1]<3:
        raise ValueError("B2_SEAM_TOO_NARROW")
    # Width and y position are read directly from the two source boards:
    # one 1x3 plate runs transverse through the 2-stud host + 1-stud orphan.
    xx=nb[0]
    ys=[o[1]+1,o[1]+2]
    upper=[]
    for ix,y in enumerate(ys):
        part=new_part(f"EXPERIMENT-B2-DECK-SEAM-{ix+1}","PLATE_1X3",
                     xx,y,o[2]-1,1)
        ok,report=_two_host_plate_clearance(part,neighbor,orphan)
        if not ok:raise ValueError("B2_INVALID_SEAM_MATE:"+json.dumps(report))
        upper.append(part)
    # Reuse the tested 059M TWO underdeck transverse beams. Their coordinates
    # come from the actual deck board extents and 2x8 standard LEGO footprint.
    main_boards=[p for p in floor if p.placement_id.startswith(
          "scene-platform:south-timber-deck-main:")
          and p.part_id in ("BRICK_2X8","BRICK_1X8") and p.z_plates==orphan.z_plates]
    if not main_boards:raise ValueError("B2_NO_LONG_PLANKS")
    y0=min(p.y_studs for p in main_boards)
    common_length=min(bounds(p)[4]-bounds(p)[1] for p in main_boards)
    if common_length<8:raise ValueError("B2_REQUIRES_AT_LEAST_8_STUD_PLANKS")
    beam_x=o[3]-8
    beams=[]
    for index,frac in enumerate((.25,.625)):
        yy=y0+int(common_length*frac)
        beams.append(new_part(f"EXPERIMENT-B2-DECK-BRACE-{index+1}",
            "BRICK_1X8",beam_x,yy,orphan.z_plates-3,1))
    extra=[*beams,*upper]
    boxes=[(p.placement_id,bounds(p)) for p in b1.parts]
    boxes=[(id,b) for id,b in boxes if b is not None]
    for i,new in enumerate(extra):
        a=bounds(new)
        if any(overlaps(a,b) for _,b in boxes):
            conflicts=[pid for pid,b in boxes if overlaps(a,b)]
            raise ValueError("B2_NEW_PART_INTERPENETRATES_ORIGINAL:"+repr((new.placement_id,conflicts[:4])))
        if any(overlaps(a,bounds(q)) for q in extra[:i]):
            raise ValueError("B2_NEW_PART_INTERPENETRATES_NEW")
    matings={}
    for plate in upper:
        ok,details=_two_host_plate_clearance(plate,neighbor,orphan)
        if not ok:raise AssertionError("B2_TARGETED_STUD_TUBE_MATE_FAILED")
        matings[plate.placement_id]=details
    for beam in beams:
        matched={p.placement_id:len(contact_cells(beam,p)) for p in main_boards
                if contact_cells(beam,p)}
        if len(matched)<4 or sum(matched.values())<6:
            raise ValueError("B2_BEAM_NOT_REJOINING_MULTIPLE_DECK_BOARDS")
        matings[beam.placement_id]={"above_board_studs":matched,
            "stud_grid_aligned":True,
            "underbeam_foundation_and_clutch":"NOT_PROVEN"}
    preview=b1.model_copy(update={"parts":[*b1.parts,*extra]})
    after_sizes,after_isolated=components([p.model_dump(mode="json")
                                        for p in [*floor,*extra]])
    if len(after_sizes)!=1 or after_isolated:
        raise AssertionError("B2_DECK_COMPONENT_NOT_JOINED")
    if original_bytes!=b1.model_dump_json():
        raise AssertionError("B2_SOURCE_MUTATED")
    return preview,extra,{
      "b1_floor_components":sizes,"b2_floor_components":after_sizes,
      "b1_orphan_board":orphan.placement_id,
      "neighbor":neighbor.placement_id,
      "orphan_connected_to_neighbor_by_plate_count":len(upper),
      "nominal_plate_host_interfaces":len(upper)*2,
      "matings":matings,
      "real_clutch_strength":"NOT_CERTIFIED"}

def make_connection_svg(model,extra,output):
    """Local *schematic* view, derived from exact placements, highlights repair."""
    hosts=[p for p in original_floor(model) if "south-timber-deck-main:" in p.placement_id
           and ":board:" in p.placement_id]
    parts=hosts+extra
    points=[]
    for p in parts:
        b=bounds(p)
        if b is None:continue
        x,y,z,X,Y,Z=b
        def pt(x,y,z):return ((x-y)*13.0,(x+y)*5.4-z*7.2)
        q=[pt(x,y,z),pt(X,y,z),pt(X,Y,z),pt(x,Y,z),
           pt(x,y,Z),pt(X,y,Z),pt(X,Y,Z),pt(x,Y,Z)]
        points.extend(q)
    minx=min(x for x,y in points);miny=min(y for x,y in points)
    lines=['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="650" viewBox="0 0 1000 650">',
          '<rect width="1000" height="650" fill="#f6faff"/>',
          '<text x="24" y="37" font-family="sans-serif" font-size="24">B-2 — Raccordement de la terrasse (4 vraies pièces LEGO)</text>',
          '<text x="24" y="66" font-family="sans-serif" font-size="15">Orange = pièces expérimentales de liaison ; bleu = planches existantes.</text>']
    for p in sorted(parts,key=lambda q:q.x_studs+q.y_studs+q.z_plates*.02):
        b=bounds(p);x,y,z,X,Y,Z=b
        def pt(x,y,z):return (90+(x-y)*13-minx,120+(x+y)*5.4-z*7.2-miny)
        q=[pt(x,y,z),pt(X,y,z),pt(X,Y,z),pt(x,Y,z),
           pt(x,y,Z),pt(X,y,Z),pt(X,Y,Z),pt(x,Y,Z)]
        sides=[(1,2,6,5),(2,3,7,6),(4,5,6,7)]
        color=("#f28b27" if p in extra else "#7896c7")
        for face in sides:
            lines.append('<polygon points="'+" ".join(f"{q[i][0]:.1f},{q[i][1]:.1f}" for i in face)+
                         f'" fill="{color}" stroke="#334d62" stroke-width=".65" fill-opacity=".85"/>')
    lines+=['<rect x="15" y="591" width="970" height="45" fill="#fff0d2" rx="9"/>',
            '<text x="25" y="612" font-size="14" font-family="sans-serif">Représentation schématique de volumes, pas un rendu exact LDraw. Emboîtements et résistances non certifiés.</text>',
            '<text x="25" y="631" font-size="13" font-family="sans-serif">Les 2 plaques de couture lient la planche auparavant isolée aux deux rangs voisins.</text>',
            '</svg>']
    output.write_text("\n".join(lines)+"\n",encoding="utf8")

def classify_42(b1,report):
    parts={p.placement_id:p for p in b1.parts}
    out=[]
    for pid in report["unsupported_placement_ids"]:
        p=parts[pid]
        if pid.startswith("EXPERIMENT-088-JOINT-"):
            status="B_OR_D_VERIFIER_30363_UNDERSIDE_HORS_AUDIT_ORTHOGONAL"
        elif pid.startswith("scene-chimney:"):
            status="A_AUCUN_APPUI_VERTICAL_ORTHOGONAL_IMMEDIAT_IDENTIFIE"
        elif p.part_id.startswith("PLATE_") and p.z_plates>0:
            status="B_PLAQUE_SOUS_PLANCHER_POTENTIELLEMENT_CLUTCHEE_PAR_LA_PIECE_SUPERIEURE"
        elif ":board:" in pid:
            status="A_PLANCHE_SANS_APPUI_VERTICAL_DIRECT_REPARABLE_PAR_COUTURE"
        else:
            status="D_APPUI_VERTICAL_INDETERMINE_DANS_AUDIT_LIMITÉ"
        out.append({"placement_id":pid,"part_id":p.part_id,"status":status,
                    "source_audit":"ORTHOGONAL_DIRECT_ONLY"})
    if len(out)!=42:raise AssertionError("B2_EXPECTED_42_B1_IDENTIFIERS_CHANGED")
    return out

def produce(output,ldrawroot):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    b1output=output/"SOURCE-B1-REGENERATED-ISOLATED"
    build_b1(b1output,ldrawroot)
    b1folder=b1output/"EXPERIMENTAL-1901-FULL-HOUSE"
    before=(b1folder/"BRICKMODEL-EXPERIMENTAL-1901.json").read_bytes()
    b1=BrickModel.model_validate_json(before)
    oldaudit=audit_physical_model(b1)
    classified=classify_42(b1,oldaudit)
    variant,added,mating=create_deck_reinforcement(b1)
    if len(variant.parts)!=1905 or len(added)!=4:raise AssertionError("B2_EXPECTED_1905")
    if (b1folder/"BRICKMODEL-EXPERIMENTAL-1901.json").read_bytes()!=before:
        raise AssertionError("B2_B1_COPY_CHANGED")
    newaudit=audit_physical_model(variant)
    if newaudit["collision_voxel_overlaps"]!=0:raise AssertionError("B2_ORTHOGONAL_INTERPENETRATION")
    out=output/"EXPERIMENTAL-1905-FULL-HOUSE"
    out.mkdir(parents=True,exist_ok=True)
    lib=LDrawLibrary(ldrawroot)
    ld=export_ldraw(variant,lib,out/"GUIDED004-B2-1905-FULL-HOUSE.ldr","GUIDED004_B2_1905")
    if not ld["complete_file"] or ld["ldraw_type1_count"]!=1905:
        raise AssertionError("B2_FULL_HOUSE_UNMAPPED")
    faces=preview_svg(variant,out/"GUIDED004-B2-FULL-HOUSE-ISOMETRIC.svg")
    make_connection_svg(variant,added,out/"B2-CORRECTED-DECK-JOINTS.svg")
    (out/"BRICKMODEL-B2-1905.json").write_text(variant.model_dump_json(indent=2)+"\n",encoding="utf8")
    beforeids={p.placement_id:p.model_dump(mode="json") for p in b1.parts}
    afterids={p.placement_id:p.model_dump(mode="json") for p in variant.parts}
    if any(afterids[k]!=v for k,v in beforeids.items()):
        raise AssertionError("B2_MOVED_OR_REPLACED_B1_PART")
    addedids=sorted(set(afterids)-set(beforeids))
    if set(addedids)!={p.placement_id for p in added}:
        raise AssertionError("B2_UNEXPECTED_DELTA")
    bom={"total":len(variant.parts),
      "by_canonical_part":dict(sorted(Counter(p.part_id for p in variant.parts).items())),
      "by_ldraw_id":dict(sorted(Counter(CANONICAL_LDRAW_PARTS[p.part_id].ldraw_id
                       for p in variant.parts).items())),
      "added_by_part":dict(sorted(Counter(p.part_id for p in added).items())),
      "purchase_authorized":False}
    (out/"BOM-B2.json").write_text(json.dumps(bom,ensure_ascii=False,indent=2)+"\n")
    original_plan=json.loads((b1folder/"ASSEMBLY-ORDER-NOT-CERTIFIED.json").read_text())
    plan={
      "status":"ALL_STAGES_PROPOSED_NOT_CONTINUOUS_INSERTION_CERTIFIED",
      "stage_terrace_preassembly":{
        "before":"installing south timber deck boards",
        "sequence":[p.placement_id for p in added],
        "relationships":"attach 2 1x3 plates UNDER both adjacent boards before placing the module",
        "continuous_insertion":"NOT_PROVEN"},
      "existing_B1_stages_unchanged":original_plan["steps"],
      "all_1905_placement_ids_covered":True,
      "full_house_steps":len(original_plan["steps"])+1}
    oldplanids={pid for step in original_plan["steps"] for pid in step["placement_ids"]}
    assert oldplanids==set(beforeids)
    (out/"ORDER-B2-NOT-CERTIFIED.json").write_text(json.dumps(plan,ensure_ascii=False,indent=2)+"\n")
    data={"from_count":len(b1.parts),"to_count":len(variant.parts),
      "added":len(addedids),"removed":0,"moved":0,
      "added_piece_ids":addedids,
      "original_42":classified,
      "repaired_original_non_orphan_board_count":1,
      "original_42_still_outside_auditor_not_floating_proof":sum(
         p["status"].startswith("B_") or p["status"].startswith("D_") for p in classified),
      "b1_orthogonal_unsupported":oldaudit["unsupported_parts"],
      "b2_orthogonal_unsupported":newaudit["unsupported_parts"],
      "b1_orthogonal_components":oldaudit["connected_components_orthogonal_stud_contact"],
      "b2_orthogonal_components":newaudit["connected_components_orthogonal_stud_contact"],
      "b1_orthogonal_collision_cells":oldaudit["collision_voxel_overlaps"],
      "b2_orthogonal_collision_cells":newaudit["collision_voxel_overlaps"],
      "b1_unverified_slopes":oldaudit["roof_parts_unverified"],
      "b2_unverified_slopes":newaudit["roof_parts_unverified"],
      "floor_repair":mating,
      "positive_clutch_proven":"NO",
      "local_stud_and_cavity_cross_section_compatible":4,
      "entire_house_mechanical_support_unproven":1905,
      "entire_house_mechanically_connected_component_count":"NOT_ESTABLISHED",
      "full_mesh_collision_count":"NOT_AUDITED",
      "old_B1_SHA256":hashlib.sha256(before).hexdigest(),
      "new_B2_SHA256":hashlib.sha256((out/"BRICKMODEL-B2-1905.json").read_bytes()).hexdigest(),
      "old_B1_files_unchanged":(b1folder/"BRICKMODEL-EXPERIMENTAL-1901.json").read_bytes()==before,
      "assembly_step_count_before":len(original_plan["steps"]),
      "assembly_step_count_after":len(original_plan["steps"])+1,
      "preview_faces":faces,
      "mating_clearance_is_not_full_physical_validation":True}
    (out/"BEFORE-AFTER-B1-B2.json").write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n")
    (out/"ALL-42-B1-CLASSIFIED.json").write_text(json.dumps(classified,ensure_ascii=False,indent=2)+"\n")
    print("B2_HOUSE",json.dumps({k:data[k] for k in ("from_count","to_count",
       "added","removed","moved","b1_orthogonal_unsupported",
       "b2_orthogonal_unsupported","b1_orthogonal_components",
       "b2_orthogonal_components","b1_orthogonal_collision_cells",
       "b2_orthogonal_collision_cells","b1_unverified_slopes",
       "b2_unverified_slopes","assembly_step_count_before",
       "assembly_step_count_after")},sort_keys=True))
    print("B2_FLOOR_REJOIN",json.dumps({k:mating[k] for k in
       ("b1_floor_components","b2_floor_components","b1_orphan_board",
        "neighbor","nominal_plate_host_interfaces")},sort_keys=True))
    print("B2_B1_ALL_1901_PLACEMENTS_PRESERVED",True)
    print("B2_ORIGINAL_SCENE_UNTOUCHED",True)
    return data

if __name__=="__main__":
    cli=argparse.ArgumentParser()
    cli.add_argument("--output",type=Path,required=True)
    cli.add_argument("--ldraw-root",type=Path,required=True)
    args=cli.parse_args()
    produce(args.output,args.ldraw_root)
