"""B-1: create a REAL full GUIDED-004 experimental house, without editing source.

Reuses 1890-piece canonical exporter and existing 088 complete-ridge overlay:
- regenerate the 1890 original ONLY into a new isolated B1 directory;
- 088 rebuilds a separate 1901-piece *experimental* candidate if possible;
- export every mapped actual LEGO LDraw piece using existing canonical adapter;
- preview all placements as explicitly SCHEMATIC 3D SVG;
- existing audit and assembly plan, no new geometry engine.
No 45-degree swap. No source scene writes. Fail closed on unsupported geometry.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib,json,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import export_guided004_lego as canonical_export
from construct_guided004_roof_088 import construct_to_files
from audit_guided004_physical import audit_physical_model
from brickhouse.bricks.brick_model import BrickModel
from brickhouse.bricks.bom import generate_bom
from brickhouse.bricks.assembly import generate_assembly_plan
from brickhouse.bricks.geometry_adapter import (CANONICAL_LDRAW_PARTS,
    brick_model_part_transform,_slope_transform)
from lego_geometry_engine import LDrawLibrary

SOURCE=ROOT/"frontend/data/boldungo2-guided-004-real-scene.json"
EXPECTED_CANONICAL=1890
EXPECTED_SLOPES=408
CANONICAL_SOURCE_WILL_NEVER_BE_WRITTEN=True

def checksum(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def _matrix_row(part,library):
    mapping=CANONICAL_LDRAW_PARTS.get(part.part_id)
    if mapping is None:
        return None
    if mapping.placement_kind=="slope":
        definition=library.load_part(mapping.ldraw_id)
        xform=_slope_transform(part,mapping,definition)
    else:
        xform=brick_model_part_transform(part,mapping)
    m=xform.matrix
    # All matrices are the exact transformations returned by the EXISTING
    # geometry adapter, including the 30363 sloped-brick bbox anchoring.
    loc=[m[0][3],m[1][3],m[2][3]]
    rot=[m[i][j] for i in range(3) for j in range(3)]
    def fmt(v):return str(int(v)) if abs(v-round(v))<1e-8 else f"{v:.7f}"
    color=(1 if part.component=="roof" and part.roof_side!="ridge"
        else 8 if part.component=="roof" else
        15 if part.category in ("window_frame","window_pane") else
        7 if part.component=="roof_support" else 19)
    return f"1 {color} "+" ".join(fmt(x) for x in (*loc,*rot))+f" {mapping.ldraw_id}.dat"

def export_ldraw(model,library,path,label):
    lines=[f"0 FILE {label}.ldr",
         f"0 BOLDUNGO B1 FULL HOUSE — {label}",
         "0 !CATEGORY Model",
         "0 // Original GUIDED-004 22deg-like stepped 30363 roof preserved",
         "0 // Experimental. Unsupported pieces NEVER silently approximated.",
         "0 // NOT certified constructible; NO load/insertion validation."]
    misses=[]
    mapped=Counter()
    for i,p in enumerate(model.parts):
        row=_matrix_row(p,library)
        if row is None:
            misses.append({"id":p.placement_id,"part":p.part_id,
                           "component":p.component})
            continue
        lines.extend([f"0 // {p.placement_id}",row])
        mapped[p.part_id]+=1
    if misses:
        # Keep the partial file diagnostic, but don't claim it is a complete
        # LDraw translation of the house.
        lines.append(f"0 // UNMAPPED PARTS: {len(misses)}; NOT COMPLETE")
    lines.append("0 NOFILE")
    path.write_text("\n".join(lines)+"\n",encoding="utf8")
    return {"source_count":len(model.parts),
            "ldraw_type1_count":sum(mapped.values()),
            "mapped_by_part":dict(sorted(mapped.items())),
            "unmapped_count":len(misses),"unmapped":misses,
            "complete_file":not misses}

def preview_svg(model,path):
    """One visible whole-house isometric projection of TRUE grid placements.

    Uses BrickModel part footprint/height instead of full LDraw triangles;
    a schematic preview, NOT an exact mesh render. This is only a viewer.
    """
    defs=CANONICAL_LDRAW_PARTS
    shape=[]
    for p in model.parts:
        d=defs.get(p.part_id)
        if d is None:continue
        w=d.length_studs if p.rotation_quarter_turns%2 else d.width_studs
        dep=d.width_studs if p.rotation_quarter_turns%2 else d.length_studs
        x,y,z=p.x_studs,p.y_studs,p.z_plates
        top=z+d.height_plates
        if p.component=="roof" and p.roof_side!="ridge":
            # Technically sloped body, shown only as its nominal envelope.
            # 45deg appearance or invented pitch must not be introduced.
            top=max(top,z+3)
        shade,side,cap=(
            ("#5e6c7b","#8999aa","#b1bdc9") if p.component=="roof"
            else ("#8c6b4b","#b49772","#ded0ae") if p.component=="roof_support"
            else ("#9aafb8","#b9cbd4","#dee9ef") if p.category in ("window_frame","window_pane")
            else ("#8d7665","#c2a48e","#dbc9b9"))
        shape.append((x,y,z,w,dep,top-z,shade,side,cap,p.placement_id))
    def point(x,y,z):
        return ((x-y)*1.25,(x+y)*.44-z*1.05)
    surfaces=[]
    coords=[]
    for x,y,z,w,d,h,shade,side,cap,pid in shape:
        q=[point(x,y,z),point(x+w,y,z),point(x+w,y+d,z),point(x,y+d,z),
           point(x,y,z+h),point(x+w,y,z+h),point(x+w,y+d,z+h),point(x,y+d,z+h)]
        coords.extend(q)
        faces=[([q[1],q[2],q[6],q[5]],side),
               ([q[2],q[3],q[7],q[6]],shade),
               ([q[4],q[5],q[6],q[7]],cap)]
        depth=x+y+z*.05
        surfaces.extend((depth+i*.01,pts,color) for i,(pts,color) in enumerate(faces))
    mini_x=min(x for x,y in coords);mini_y=min(y for x,y in coords)
    max_x=max(x for x,y in coords);max_y=max(y for x,y in coords)
    scale=min(1180/max(1,max_x-mini_x),780/max(1,max_y-mini_y))
    def svgpts(poly):
        return " ".join(f"{50+(x-mini_x)*scale:.2f},{105+(y-mini_y)*scale:.2f}" for x,y in poly)
    # A simple depth painter, no claim of pixel-exact triangle visibility.
    surfaces.sort(key=lambda r:r[0])
    title=f"GUIDED-004 — COPIE EXPÉRIMENTALE COMPLÈTE ({len(model.parts)} pièces)"
    content=['<svg xmlns="http://www.w3.org/2000/svg" width="1320" height="960" viewBox="0 0 1320 960">',
       f'<title>{title}</title>',
       '<rect width="1320" height="960" fill="#f5f7fb"/>',
       f'<text x="40" y="46" font-size="26" fill="#23364e" font-family="sans-serif" font-weight="bold">{title}</text>',
       '<text x="40" y="77" font-size="15" fill="#354b64" font-family="sans-serif">Murs, ouvertures, terrasse, escaliers, cheminée et toiture à progression proche de 22° : positions du vrai BrickModel.</text>']
    content.extend(f'<polygon points="{svgpts(poly)}" fill="{color}" stroke="#485465" stroke-width=".24" fill-opacity=".96"/>' for dep,poly,color in surfaces)
    content+=['<rect x="20" y="894" width="1280" height="50" rx="9" fill="#fff2de"/>',
       '<text x="35" y="916" font-size="15" fill="#674522" font-family="sans-serif">VUE ISOMÉTRIQUE SCHÉMATIQUE DES EMPRISES : PAS un rendu exact des maillages officiels LDraw.</text>',
       '<text x="35" y="938" font-size="14" fill="#674522" font-family="sans-serif">La construction et les insertions du toit ne sont pas certifiées. Le fichier .ldr conserve les pièces LDraw exactes.</text>','</svg>']
    path.write_text("\n".join(content)+"\n",encoding="utf8")
    return len(surfaces)

def _finish(output,src,source_scene_sha,source_sha,exp,decision,library):
    orig=BrickModel.model_validate_json(src.read_bytes())
    if len(orig.parts)!=EXPECTED_CANONICAL:raise ValueError("B1_ORIGINAL_COUNT_NOT_1890")
    if len(exp.parts)!=1901:
        raise ValueError("B1_EXPERIMENTAL_RIDGE_NOT_1901_STOP")
    # The 088 candidate is allowed to change ONLY existing roof/ridge
    # members; walls, windows, terrace, staircase, chimneys must be identical.
    def invariant(p):
        return p.component!="roof" or p.roof_side!="ridge"
    def preserved(m):
        return {p.placement_id:p.model_dump(mode="json") for p in m.parts if invariant(p)}
    original_fixed=preserved(orig);exp_fixed=preserved(exp)
    # 088 adds NEW ridge connector bricks in roof_support. Their existence
    # is the intended experiment and must never be mistaken for a change to
    # the canonical walls, openings, stairs, terrace or chimneys.
    removed=set(original_fixed)-set(exp_fixed)
    added=set(exp_fixed)-set(original_fixed)
    changed={k for k in original_fixed.keys()&exp_fixed.keys()
             if original_fixed[k]!=exp_fixed[k]}
    forbidden_new={k for k in added
             if not (k.startswith("EXPERIMENT-088-JOINT-")
                 and exp_fixed[k]["component"]=="roof_support")}
    if removed or changed or forbidden_new:
        delta={"missing":sorted(removed)[:12],
               "forbidden_additions":sorted(forbidden_new)[:12],
               "changed":sorted(changed)[:12]}
        raise AssertionError("B1_NON_RIDGE_ARCHITECTURE_CHANGED:"+json.dumps(delta))
    print("B1_NONRIDGE_OLD_IDS_UNCHANGED",len(original_fixed),
          "NEW_EXPERIMENTAL_RIDGE_JOINTS",len(added))
    before_roof=Counter(p.part_id for p in orig.parts if p.component=="roof")
    after_roof=Counter(p.part_id for p in exp.parts if p.component=="roof")
    slopes_orig=sum(p.part_id=="BRICK_SLOPED_18_4X2" for p in orig.parts)
    slopes_exp=sum(p.part_id=="BRICK_SLOPED_18_4X2" for p in exp.parts)
    if slopes_orig!=EXPECTED_SLOPES or slopes_exp!=EXPECTED_SLOPES:
        raise AssertionError("B1_CANNOT_CHANGE_408_GABLE_SLOPES")

    out=output/"EXPERIMENTAL-1901-FULL-HOUSE"
    out.mkdir(parents=True,exist_ok=True)
    exact=export_ldraw(exp,library,out/"GUIDED004-B1-FULL-HOUSE-22DEG.ldr","GUIDED004_B1_1901")
    surfaces=preview_svg(exp,out/"GUIDED004-B1-FULL-HOUSE-ISOMETRIC.svg")
    audit=audit_physical_model(exp)
    # The existing canonical AssemblyPlan (rightly) does not know how to
    # schedule EXPERIMENT-088-JOINT roof_support pieces. DO NOT mutate that
    # planner or lie about its completeness: plan all ordinary 1878 pieces
    # with the existing function, append the 23 new joints as an explicitly
    # unproven experimental phase with a separate provenance flag.
    extra_joint_ids=sorted(added)
    core=BrickModel.model_validate({**exp.model_dump(mode="json"),
         "parts":[p.model_dump(mode="json") for p in exp.parts
                  if p.placement_id not in added]})
    assembly=generate_assembly_plan(core)
    core_steps=assembly.model_dump(mode="json")["steps"]
    ordered=[pid for step in assembly.steps for pid in step.placement_ids]
    ordered+=extra_joint_ids
    if len(ordered)!=len(exp.parts) or set(ordered)!={p.placement_id for p in exp.parts}:
        raise AssertionError("B1_ASSEMBLY_ORDER_MISSING_PARTS")
    supplemental_step={
      "step_id":"EXPERIMENTAL-088-RIDGE-CONNECTORS-B1",
      "title":"23 nouveaux connecteurs du faîtage — insertion non démontrée",
      "placement_ids":extra_joint_ids,
      "insertion_status":"NOT_DEMONSTRATED",
      "parent_stud_tube_compatibility":"NOT_CERTIFIED",
      "provenance":"EXPERIMENTAL_088_NEW_PARTS_NOT_IN_EXISTING_ASSEMBLY_PLANNER"}
    bom=generate_bom(exp)
    if bom.total_parts!=len(exp.parts):
        raise AssertionError("B1_GENERATED_BOM_MISMATCH")
    (out/"BOM.json").write_text(json.dumps({
       "total":len(exp.parts),"by_canonical_part":dict(sorted(Counter(p.part_id for p in exp.parts).items())),
       "by_ldraw_id":dict(sorted(Counter(
          CANONICAL_LDRAW_PARTS[p.part_id].ldraw_id
          for p in exp.parts if p.part_id in CANONICAL_LDRAW_PARTS).items())),
       "colors_proven":False,"procurement_approved":False,
       "source_sha256":source_sha},indent=2,ensure_ascii=False)+"\n")
    (out/"ASSEMBLY-ORDER-NOT-CERTIFIED.json").write_text(
        json.dumps({"steps":[*core_steps,supplemental_step],
          "existing_planner_pieces":len(core.parts),
          "additional_088_ridge_connector_pieces":len(extra_joint_ids),
          "all_source_parts_ordered":True,"real_insertion_demonstrated":False,
          "physical_stability_demonstrated":False,
          "status":"PROPOSED_BY_EXISTING_BUILDER_NOT_CERTIFIED"},
          indent=2,ensure_ascii=False)+"\n")
    (out/"BRICKMODEL-EXPERIMENTAL-1901.json").write_text(exp.model_dump_json(indent=2)+"\n")
    (out/"CONNECTIONS-AND-COLLISIONS.json").write_text(json.dumps({
      "audit_scope":"existing rectangular voxel / orthogonal contact only",
      "audit":audit,"roof_slopes_physical_clutch_verified":0,
      "full_1901_connected_components_physical":"NOT_ESTABLISHED",
      "full_1901_collision_pairs_official_mesh":"NOT_CHECKED",
      "full_chain_to_foundations_per_piece":"NOT_ESTABLISHED",
      "parts_without_fully_demonstrated_support_chain":len(exp.parts),
      "roof_continuous_insertions_proven":0,
      "mechanical_strength":"NOT_CERTIFIED"},indent=2,ensure_ascii=False)+"\n")
    comparison={"canonical_count":len(orig.parts),"experimental_count":len(exp.parts),
       "net_delta":len(exp.parts)-len(orig.parts),
       "all_original_nonridge_parts_unchanged":True,"original_nonridge_part_count":len(original_fixed),
       "added_new_ridge_connector_bricks":len(added),
       "canonical_roof_part_bom":dict(sorted(before_roof.items())),
       "experimental_roof_part_bom":dict(sorted(after_roof.items())),
       "slope_30363_original":slopes_orig,"slope_30363_experiment":slopes_exp,
       "roof_pitch":"NO_45_DEGREE_REPLACEMENT; original ~21.8deg course rise/run retained",
       "source_scene_sha256":source_scene_sha,"canonical_export_sha256":source_sha,
       "source_scene_file_unchanged":checksum(SOURCE)==source_scene_sha,
       "original_export_unchanged":checksum(src)==source_sha,
       "ldraw":exact,
       "isometric_schematic_face_count":surfaces,
       "original_088_decision":decision.get("decision"),
       "physical_certification":"DENIED"}
    (out/"COMPARISON-WITH-1890-CANONICAL.json").write_text(json.dumps(comparison,indent=2,ensure_ascii=False)+"\n")
    print("B1_FULL_HOUSE",json.dumps({
       "canonical":len(orig.parts),"experimental":len(exp.parts),
       "mapped_ldraw":exact["ldraw_type1_count"],"unmapped":exact["unmapped_count"],
       "roof_slopes":slopes_exp,"orthogonal_voxel_collision_cells":audit["collision_voxel_overlaps"],
       "orthogonal_connected_components":audit["connected_components_orthogonal_stud_contact"],
       "orthogonal_unsupported":audit["unsupported_parts"],
       "roof_unverified":audit["roof_parts_unverified"],
       "fully_proven_load_paths":0,"no_full_support_proof":len(exp.parts),
       "assembly_steps":len(core_steps)+1,"svg_faces":surfaces},sort_keys=True))
    return comparison

def build(output,ldraw_root,source=SOURCE):
    output=Path(output);source=Path(source)
    if output.resolve()==source.resolve() or source.resolve().is_relative_to(output.resolve()):
        raise ValueError("B1_REFUSE_SOURCE_OVERWRITE_OR_PARENT_OUTPUT")
    input_sha=checksum(source)
    # Force existing canonical exporter to a fresh experiment-specific
    # directory. Do not edit the existing source exporter.
    canonical_export.SOURCE=source
    canonical_export.OUTPUT=output/"READONLY-CANONICAL-1890-REGEN"
    inv=canonical_export.generate()
    src=canonical_export.OUTPUT/"brick-model.json"
    if inv["total_bricks"]!=1890 or checksum(source)!=input_sha:
        raise AssertionError("B1_SOURCE_SCENE_MUTATION_OR_WRONG_COUNT")
    source_sha=checksum(src)
    exp_dir=output/"REUSED-088-RIDGE-CANDIDATE"
    decision=construct_to_files(src,exp_dir)
    exp_path=exp_dir/"GUIDED-004-EXPERIMENTAL-NOT-CERTIFIED.json"
    if not exp_path.is_file():
        raise AssertionError("B1_NO_088_FULL_EXPERIMENTAL_MODEL")
    exp=BrickModel.model_validate_json(exp_path.read_bytes())
    library=LDrawLibrary(ldraw_root)
    report=_finish(output,src,input_sha,source_sha,exp,decision,library)
    assert checksum(src)==source_sha and checksum(source)==input_sha
    print("B1_ALL_SOURCE_BYTES_UNCHANGED","YES")
    return report

if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--output",type=Path,required=True)
    a.add_argument("--ldraw-root",type=Path,required=True)
    opt=a.parse_args()
    build(opt.output,opt.ldraw_root)
