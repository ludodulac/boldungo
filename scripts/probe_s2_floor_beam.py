"""S-2: ONE 3832/3006 geometric investigation, S-1 untouched.

Official LDraw DAT positions and named first-level subprimitives; existing
triangle intersection code only. NEVER whitelist collisions. No new engine.
"""
from __future__ import annotations
import argparse,json,math
from pathlib import Path
from dataclasses import replace

from lego_geometry_engine import LDrawLibrary,Relation,check_collision,find_connections,instantiate,Transform
from lego_geometry_engine.core import _tri_intersection_kind,_point_in_mesh
try:
    from scripts.build_documented_frame_s1 import model,_instance,ldraw_line
except ModuleNotFoundError:
    from build_documented_frame_s1 import model,_instance,ldraw_line

MIRROR_SHA="c43ed06a128a10ed65675166bf42eb6fd608b9b0"

def dat_subfiles(lib,part_ref):
    path=lib._resolve(part_ref+".dat")
    if path is None: raise FileNotFoundError(part_ref)
    out=[]
    for i,ln in enumerate(path.read_text(errors="replace").splitlines(),1):
        fields=ln.split()
        if len(fields)>=15 and fields[0]=="1":
            v=[float(x) for x in fields[2:14]]
            out.append({"line":i,"primitive":fields[14].lower(),"coord":v[:3],
                        "matrix":v[3:]})
    return out

def to_local(p,point):
    # Inputs in S-1 have 3x3 orthonormal LDraw matrices; inverse R^T.
    r=p.rot
    centre=(p.x+p.w/2,p.y+p.d/2)
    t=(20*centre[0],-8*(p.z+p.h),20*centre[1])
    d=[point[i]-t[i] for i in range(3)]
    return [sum(r[3*j+i]*d[j] for j in range(3)) for i in range(3)]

def witness(a,b):
    """First crossing triangle using existing _tri_intersection_kind only."""
    attempts=0
    for i,ta in enumerate(a.triangles):
        a0=[min(p[k] for p in ta) for k in range(3)]
        a1=[max(p[k] for p in ta) for k in range(3)]
        for j,tb in enumerate(b.triangles):
            b0=[min(p[k] for p in tb) for k in range(3)]
            b1=[max(p[k] for p in tb) for k in range(3)]
            if any(a1[k]<b0[k]-1e-4 or b1[k]<a0[k]-1e-4 for k in range(3)):
                continue
            attempts+=1
            if _tri_intersection_kind(ta,tb)==Relation.COLLISION:
                return {"first_triangle_indices":[i,j],
                    "upper_triangle_vertices_ldu":ta,
                    "lower_triangle_vertices_ldu":tb,
                    "upper_local_triangle_ldu":None,
                    "lower_local_triangle_ldu":None,
                    "candidate_overlap_broadphase_count":attempts,
                    "collision_type":"NON_COPLANAR_TRIANGLE_INTERSECTION"}
    return {"triangle_intersection_found":False,"checked_overlap_pairs":attempts,
        "collision_type":"POSSIBLE_MESH_CONTAINMENT_OR_NUMERIC_CASE"}

def source_primitive(lib,inst,tri):
    """Find DAT first-level primitive producing the intersecting triangle.
    No mesh or collision implementation added: reuse private LDraw _expand
    only to attribute offending witness to an original source primitive.
    """
    path=lib._resolve(inst.definition.part_id)
    if not path:return "NOT_FOUND"
    target=tuple(tuple(round(v,3) for v in p) for p in tri)
    targetset=set(target)
    for field in dat_subfiles(lib,path.stem):
        a,b,c,d,e,f,g,h,i=field["matrix"]
        x,y,z=field["coord"]
        local=Transform(((a,b,c,x),(d,e,f,y),(g,h,i,z),(0,0,0,1)))
        sub=lib._resolve(field["primitive"])
        if sub is None:continue
        try:triangles=lib._expand(sub,inst.transform.compose(local),set())
        except Exception:continue
        for one in triangles:
            if set(tuple(round(v,3) for v in p) for p in one)==targetset:
                return {"source_line":field["line"],"primitive":field["primitive"],
                        "source_transform":field["coord"]}
    return "TOP_LEVEL_QUAD_OR_NOT_LOCATED"

def three_d_studs(lib,part,primitive):
    inst=_instance(part,lib)
    ans=[]
    for field in dat_subfiles(lib,part.ref):
        if field["primitive"]==primitive:
            ans.append(inst.transform.point(tuple(field["coord"])))
    return ans

def experiment(ldrawroot):
    lib=LDrawLibrary(ldrawroot)
    ps=model()
    plate=next(x for x in ps if x.role=="floor")
    beam=next(x for x in ps if x.id==plate.parents[0])
    ap,bp=_instance(plate,lib),_instance(beam,lib)
    relation=check_collision(ap,bp)
    aligns=find_connections(ap,bp)
    beam_studs=three_d_studs(lib,beam,"stud.dat")
    plate_studs=three_d_studs(lib,plate,"stud.dat")
    tubes=three_d_studs(lib,plate,"stud4.dat")
    # The upper plate's underside cavity axes are aligned vertically with
    # its top actual physical studs, not with the engine's guessed
    # Width=2 => X-axis assumption (LDraw 3832 LONG axis is X).
    xy=lambda x:(round(x[0],4),round(x[2],4))
    axes=sorted(set(map(xy,beam_studs)) & set(map(xy,plate_studs)))
    lower_top_y=bp.transform.point((0,0,0))[1]
    plate_bottom_y=ap.transform.point((0,8,0))[1]
    plate_cavity_ceiling=ap.transform.point((0,4,0))[1]
    stud_top_y=bp.transform.point((0,-4,0))[1]
    # 3832 and 3006 DAT: tube r_outer=8; stud radius=6.
    min_tube_dist=min(math.hypot(a[0]-b[0],a[2]-b[2])
                        for a in tubes for b in beam_studs)
    min_tube_clearance=min_tube_dist-(8+6)
    wit=witness(ap,bp)
    if "upper_triangle_vertices_ldu" in wit:
        wit["upper_local_triangle_ldu"]=[to_local(plate,p) for p in wit["upper_triangle_vertices_ldu"]]
        wit["lower_local_triangle_ldu"]=[to_local(beam,p) for p in wit["lower_triangle_vertices_ldu"]]
        wit["upper_source"]=source_primitive(lib,ap,wit["upper_triangle_vertices_ldu"])
        wit["lower_source"]=source_primitive(lib,bp,wit["lower_triangle_vertices_ldu"])
    # Negative: 4 LDU into beam solid, deliberately wrong plate height.
    # Not the normal insertion (continuous movement NOT studied).
    shifted=instantiate(ap.definition,"ILLEGAL_PLATE_4_LDU_TOO_LOW",
        Transform.translation(0,4,0).compose(ap.transform))
    invalid_relation=check_collision(shifted,bp)
    # Same ALREADY EXISTING triangulated intersection detector on deliberately
    # invalid vertical overlap. If true physical shell interference cannot be
    # detected, do not proclaim our witness test trustworthy.
    wrong_witness=witness(shifted,bp)
    vertex_in_beam=_point_in_mesh(ap.triangles[0][0],bp.triangles)
    vertex_in_plate=_point_in_mesh(bp.triangles[0][0],ap.triangles)
    plate_bbox=ap.bbox;beam_bbox=bp.bbox
    plate_encloses_beam=all(plate_bbox.minimum[i]<=beam_bbox.minimum[i]
                             and beam_bbox.maximum[i]<=plate_bbox.maximum[i]
                             for i in range(3))
    beam_encloses_plate=all(beam_bbox.minimum[i]<=plate_bbox.minimum[i]
                             and plate_bbox.maximum[i]<=beam_bbox.maximum[i]
                             for i in range(3))
    # Verify every original floor/beam mate using actual DAT, not merely the
    # engine's descriptor-derived connectors (3006 and 3832 both have the
    # long dimension along local X, despite the "2 x 10" name).
    all_pairs=[]
    for up in (p for p in ps if p.role=="floor"):
        for pid in up.parents:
            lo=next(p for p in ps if p.id==pid)
            upper_studs=three_d_studs(lib,up,"stud.dat")
            lower_studs=three_d_studs(lib,lo,"stud.dat")
            upper_tubes=three_d_studs(lib,up,"stud4.dat")
            common=sorted(set(map(xy,upper_studs))&set(map(xy,lower_studs)))
            minimum=min(math.hypot(x[0]-y[0],x[2]-y[2])
                         for x in upper_tubes for y in lower_studs)
            same_level=abs(_instance(up,lib).transform.point((0,8,0))[1]-
                           _instance(lo,lib).transform.point((0,0,0))[1])<1e-8
            count=len(common)
            all_pairs.append({"plate":up.id,"beam":lo.id,
                 "genuine_dat_stud_axes_in_common":count,
                 "underside_outer_tube_to_lower_stud_clearance_ldu":round(minimum-14,6),
                 "plate_underside_equals_beam_top_plane":same_level,
                 "positive_static_stud_fit":count==4 and minimum>14 and same_level})
    # Conclusive only for the geometry in this bounded interface:
    # no surface crossings, no fully contained part, actual 4-axis match,
    # positive tube/stud separation, and counterexample shows actual crossing.
    # Geometry engine's original COLLISION remains RAW and unchanged.
    no_cross="triangle_intersection_found" in wit and False or (
        wit.get("triangle_intersection_found") is False)
    negative_real_cross=("first_triangle_indices" in wrong_witness)
    intentional_fit=(relation==Relation.COLLISION and no_cross
         and (vertex_in_beam or vertex_in_plate)
         and not plate_encloses_beam and not beam_encloses_plate
         and len(axes)==4 and min_tube_clearance>0
         and abs(stud_top_y-plate_cavity_ceiling)<1e-8
         and abs(lower_top_y-plate_bottom_y)<1e-8
         and negative_real_cross
         and len(all_pairs)==10 and all(x["positive_static_stud_fit"] for x in all_pairs))
    result={
      "part_upper":plate.id,"part_lower":beam.id,
      "upper_LDraw_row":ldraw_line(plate),"lower_LDraw_row":ldraw_line(beam),
      "upper_part":"3832.dat","lower_part":"3006.dat",
      "upper_official_part_header":"Plate 2 x 10; DAT actual long X axis, rotated to S1 long Z axis",
      "lower_official_part_header":"Brick 2 x 10; DAT actual long X axis",
      "mesh_relation_at_S1_position":relation.value,
      "engine_inferred_connectors":len(aligns),
      "engine_connector_locations":[list(v["position"]) for v in aligns],
      "actual_DAT_beam_stud_centres_count":len(beam_studs),
      "actual_DAT_plate_stud_centres_count":len(plate_studs),
      "actual_DAT_plate_underside_tubes_count":len(tubes),
      "actual_horizontal_stud_to_cavity_axis_matches":len(axes),
      "actual_overlapping_stud_axis_xz_ldu":axes,
      "beam_stud_top_y":stud_top_y,
      "plate_cavity_ceiling_y":plate_cavity_ceiling,
      "plate_bottom_y":plate_bottom_y,"beam_body_top_y":lower_top_y,
      "nominal_stud_insertion_depth_LDU":abs(plate_bottom_y-plate_cavity_ceiling),
      "nominal_tube_outer_radius_LDU":8,
      "nominal_stud_radius_LDU":6,
      "min_tube_stud_diagonal_separation_LDU":min_tube_dist,
      "min_tube_stud_radial_clearance_LDU":min_tube_clearance,
      "witness":wit,
      "negative_deliberate_4_LDU_vertical_interference_relation":invalid_relation.value,
      "negative_wrong_depth_has_actual_triangles_crossing":negative_real_cross,
      "negative_wrong_depth_triangle_witness":wrong_witness,
      "original_mesh_inside_ray_vertex_plate_to_beam":vertex_in_beam,
      "original_mesh_inside_ray_vertex_beam_to_plate":vertex_in_plate,
      "original_body_complete_bbox_containment_either_way":plate_encloses_beam or beam_encloses_plate,
      "original_mesh_collision_comes_from_containment_fallback_not_triangle_crossing":relation==Relation.COLLISION and no_cross,
      "repeated_ten_couplings_actual_official_DAT":all_pairs,
      "all_ten_actual_stud_cavity_alignments_compatible":all(x["positive_static_stud_fit"] for x in all_pairs),
      "counterexample_detected_as_real_interference":negative_real_cross,
      "bounded_static_geometric_verdict":"COMPATIBLE" if intentional_fit else "NON_RESOLU",
      "nominal_normal_collision_has_not_been_silently_ignored":relation==Relation.COLLISION,
      "repetitions_examined":10,
      "triangle_intersection_representative_pairs":1,
      "static_interface_verdict":"COMPATIBLE" if intentional_fit else "NON_RESOLU",
      "insertion_continuous":"NON_DEMONTREE",
      "mechanical_strength":"NON_CERTIFIEE",
      "notes":"Only a genuine overlap of solids in the original geometry can prove incompatible. A mesh intersection in a documented stud-cavity region alone is not a validated physical interference or a permitted exception."
    }
    print("S2_RAW",json.dumps({k:v for k,v in result.items() if k not in ("witness","negative_wrong_depth_triangle_witness","engine_connector_locations","actual_overlapping_stud_axis_xz_ldu","repeated_ten_couplings_actual_official_DAT")},sort_keys=True))
    print("S2_TEN_MATES",json.dumps(all_pairs,sort_keys=True))
    print("S2_BAD_WITNESS",json.dumps(wrong_witness,sort_keys=True))
    print("S2_WITNESS",json.dumps(wit,sort_keys=True))
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--ldraw-root",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    x=p.parse_args()
    res=experiment(x.ldraw_root)
    x.output.parent.mkdir(parents=True,exist_ok=True)
    x.output.write_text(json.dumps(res,indent=2,ensure_ascii=False)+"\n")
