"""Mission A-2: inspect TWO concrete A1-derived roofs against pinned LDraw DAT.

Retains *negative* collision results and sampled insertion blockers. Uses the
project's LDrawLibrary/check_collision, not a new geometry framework.
"""
from __future__ import annotations

from collections import Counter,defaultdict
from pathlib import Path
import argparse,json

from lego_geometry_engine import (LDrawLibrary, instantiate,
    transform_from_ldraw, check_collision, Relation, Transform)
from experiment_stacked_roofs_a import _ldraw, _audit
from construct_small_roof_a2 import W,L, generate, staged_parts,export

def located(parts,lib):
    lines=_ldraw(parts,W,L,"A2-part-positions").splitlines()
    byid={}
    current=None
    for line in lines:
        if line.startswith("0 // ") and len(line.split())>=4 and line.split()[2] in {p.pid for p in parts if p.role!="base"}:
            current=line.split()[2]
        elif line.startswith("1 ") and current is not None:
            t=line.split()
            if len(t)!=15: raise AssertionError("BAD_LDRAW_TYPE1_FIELD_COUNT")
            definition=lib.load_part(t[-1])
            byid[current]=instantiate(definition,current,
                transform_from_ldraw([float(x) for x in t[2:14]]))
            current=None
    if len(byid)!=len(parts)-1:raise AssertionError("MISSING_REAL_LDRAW_INSTANCE")
    return byid

def shifted(instance,delta_y):
    return instantiate(instance.definition,instance.instance_id+"-moved",
        Transform.translation(0,-delta_y,0).compose(instance.transform))

def bbox_relevant(a,b):
    return a.bbox.relation(b.bbox) is not Relation.SEPARATED

def roof_parent(part,parts):
    if part.role=="slope":
        return next(p for p in parts if p.role=="beam" and p.x==part.x+1
             and p.y==part.y and p.z+p.height==part.z)
    if part.role=="ridge":
        return next(p for p in parts if p.role=="slope" and p.side=="left"
            and p.step==2 and p.y<=part.y<p.y+p.sy if part.ldraw=="3023b") if part.ldraw=="3023b" else next(
            p for p in parts if p.role=="slope" and p.side=="left" and p.step==2)
    raise ValueError(part)

def nominal_connector_cells(parent,child):
    # All these *coordinates* are nominal; true slope underside tubes must be
    # independently checked from s/30363s01.dat.
    if child.role=="slope":
        tube_x=set(range(child.x+1,child.x+4)) if child.side=="left" else set(range(child.x,child.x+3))
        return sorted((x,y) for x in tube_x for y in range(child.y,child.y+child.sy)
                      if (x,y) in parent.top_studs())
    if child.role=="ridge":
        return sorted(parent.top_studs() & child.bottom_cavities())
    return []

def first_intersecting_triangle_pair(a,b):
    """Exact segment/triangle witness from existing collision engine,
    not a volumetric decomposition or material-overlap volume.
    """
    from lego_geometry_engine.core import _tri_intersection_kind
    for ia,ta in enumerate(a.triangles):
        amin=[min(v[c] for v in ta) for c in range(3)]
        amax=[max(v[c] for v in ta) for c in range(3)]
        for ib,tb in enumerate(b.triangles):
            bmin=[min(v[c] for v in tb) for c in range(3)]
            bmax=[max(v[c] for v in tb) for c in range(3)]
            if any(amax[c] < bmin[c]-1e-5 or bmax[c] < amin[c]-1e-5 for c in range(3)):
                continue
            if _tri_intersection_kind(ta,tb) is Relation.COLLISION:
                return {
                    "first_crossing_triangle_index_part_a":ia,
                    "first_crossing_triangle_index_part_b":ib,
                    "triangle_a_world_ldu":[list(v) for v in ta],
                    "triangle_b_world_ldu":[list(v) for v in tb],
                    "axiswise_shared_bbox_world_ldu":{
                        "minimum":[round(max(amin[c],bmin[c]),5) for c in range(3)],
                        "maximum":[round(min(amax[c],bmax[c]),5) for c in range(3)],
                    },
                    "source":"existing _tri_intersection_kind: explicit strict interior edge-to-triangle crossing",
                }
    return {"no_crossing_triangle_found":True,
            "warning":"mesh collision may instead be from containment or non-watertight geometry"}

def known_roof_pairs(parts, instances):
    roof=[p for p in parts if p.role in ("slope","ridge")]
    pairs=[]
    for i,a in enumerate(roof):
        for b in roof[i+1:]:
            ia,ib=instances[a.pid],instances[b.pid]
            if not bbox_relevant(ia,ib):
                continue
            rel=check_collision(ia,ib).value
            pairs.append({"a":a.pid,"b":b.pid,"a_part":a.ldraw,"b_part":b.ldraw,
                "relation":rel,
                "collision_witness":first_intersecting_triangle_pair(ia,ib) if rel=="COLLISION" else None,
                "possible_stud_region":
                    (a.role=="ridge" or b.role=="ridge"),"allow_collisions":False})
    return pairs

def official_tube_evidence(root,part,parent):
    """Only the two primitive families actually used by this module.

    Coordinates in stud-grid boundaries, not guessed underside 'studs':
    the 30363's three stud4a cylinders lie BETWEEN its two rows of studs,
    not centered on individual tenon locations.
    """
    if part.role=="slope":
        source=(Path(root)/"parts/s/30363s01.dat").read_text()
        assert "stud4a.dat" in source and "stud4s.dat" in source
        assert all((" -10 " in source," -30 " in source," -50 " in source))
        tube_centres=[(part.x+i,part.y+1) for i in (1,2,3)]
        parent_four_studs={(x+.5,y+.5) for x,y in parent.top_studs()}
        middle=(parent.x+1,parent.y+1)
        established=(middle in tube_centres and len(parent_four_studs)==4
            and parent.z+parent.height==part.z)
        return {"source":"LDraw s/30363s01.dat stud4a/stud4s",
            "tube_centres_at_stud_cell_boundaries":tube_centres,
            "supporting_four_stud_centres":sorted(parent_four_studs),
            "supporting_pair_centre":middle,
            "tube_stud_grid_match":established,
            "contact_plane_y_ldu":-8*part.z}
    if part.ldraw=="3022":
        source=(Path(root)/"parts/3022.dat").read_text()
        assert "stud4.dat" in source and "box5.dat" in source
        middle=(part.x+1,part.y+1)
        return {"source":"LDraw 3022.dat central stud4 support tube",
            "central_tube_boundary":middle,"contact_plane_y_ldu":-8*part.z,
            "top_stud_cells_expected":[(9,2),(9,3),(10,2),(10,3)],
            "tube_stud_grid_match":part.x==9 and part.y==2 and part.z==18}
    if part.ldraw=="3023b":
        source=(Path(root)/"parts/s/3023bs01.dat").read_text()
        assert "stud3.dat" in source
        return {"source":"LDraw s/3023bs01.dat underside central stud3",
            "center_between_opposing_slopes":(part.x+1,part.y+.5),
            "contact_plane_y_ldu":-8*part.z,
            "tube_stud_grid_match":part.x==9 and part.z==18,
            "status":"primitive exists; actual material crossing must be traced"}
    raise ValueError("Unsupported test piece "+part.ldraw)

def sample_insertion(parts,instances):
    """Samples fixed axis -Y movement, no claim of continuous sweep clearance.

    For this official mesh engine, connector interference may appear as
    COLLISION during last 4 LDU, so such collision is explicitly UNKNOWN.
    """
    done=[]
    results=[]
    for p in parts:
        if p.role=="base":
            done.append(p)
            continue
        final=instances[p.pid]
        visited=[]
        for dist in (48,32,24,16,8,4,2,0):
            moving=shifted(final,dist)
            hits=[]
            for q in done:
                if q.role=="base":
                    continue
                fixed=instances[q.pid]
                if not bbox_relevant(moving,fixed):continue
                relation=check_collision(moving,fixed)
                if relation is Relation.COLLISION:
                    hits.append(q.pid)
            visited.append({"height_ldu":dist,"collision_part_ids":sorted(hits)})
        before_engagement=[v for v in visited if v["height_ldu"]>4 and v["collision_part_ids"]]
        at_final=next(v for v in visited if v["height_ldu"]==0)
        results.append({"pid":p.pid,"part":p.ldraw,"role":p.role,"direction":"WORLD_MINUS_Y_TO_FINAL",
            "samples":visited if p.role in ("slope","ridge") else [],
            "blocked_before_last_4_ldu":bool(before_engagement),
            "blocking_earlier_steps":before_engagement,
            "unclassified_final_mesh_collisions":at_final["collision_part_ids"],
            "continuous_insertion_proven":False,
            "connector_clutch_friction_proven":False})
        done.append(p)
    return results

def run(root,outdir):
    lib=LDrawLibrary(root)
    outdir=export(outdir)
    allsummary=[]
    for candidate in ("3023b","3022"):
        parts=staged_parts(generate(candidate))
        graph_nominal=_audit(parts)
        instances=located(parts,lib)
        possible=[]
        for part in parts:
            if part.role not in ("slope","ridge"):continue
            parent=roof_parent(part,parts)
            cells=nominal_connector_cells(parent,part)
            # Official file states 30363s01 local underside tube centers at
            # local Z=-10,-30,-50; this verifies only XY projection, not force.
            pair_rel=check_collision(instances[part.pid],instances[parent.pid]).value
            possible.append({"roof_piece_id":part.pid,"bearing_piece_id":parent.pid,
                "roof_ldraw":part.ldraw,"bearing_ldraw":parent.ldraw,
                "matching_local_30363_tube_projection":bool(cells) if part.role=="slope" else None,
                "nominal_stud_cells":[list(x) for x in cells],
                "official_LDraw_tube_and_stud_geometry":official_tube_evidence(root,part,parent),
                "actual_mesh_pair_relation":pair_rel,
                "geometry_positive_clutch_certified":False,
                "reason":"MATCHED_STUD_PROJECTION_BUT_CLUTCH_AND_INSERTION_NOT_PROVEN"})
        pairs=known_roof_pairs(parts,instances)
        insertion=sample_insertion(parts,instances)
        bad=[x for x in pairs if x["relation"]=="COLLISION"]
        blocked=[x for x in insertion if x["blocked_before_last_4_ldu"]]
        unproven=[x["roof_piece_id"] for x in possible if
              not x["geometry_positive_clutch_certified"]]
        counters={"model_pieces":len(parts),"roof_pieces":sum(p.role in ("slope","ridge") for p in parts),
            "connected_components_nominal":graph_nominal["connected_components_nominal"],
            "parts_without_nominal_support":graph_nominal["unsupported_nominal_count"],
            "orthogonal_boxes_colliding":graph_nominal["orthogonal_body_aabb_collision_count"],
            "other_structural_pieces":sum(p.role in ("pier","beam") for p in parts),
            "stud_projection_candidates":sum(bool(x["nominal_stud_cells"]) for x in possible),
            "roof_pieces_without_demonstrated_positive_connection":len(unproven),
            "nominal_roof_supports_without_confirmed_clutch":unproven,
            "sampled_mesh_roof_pairs":len(pairs),"unclassified_roof_mesh_collisions":len(bad),
            "roof_interfaces_with_real_tube_grid_alignment":sum(x["official_LDraw_tube_and_stud_geometry"]["tube_stud_grid_match"] for x in possible),
            "contact_mesh_bearing_pairs":sum(x["actual_mesh_pair_relation"]=="CONTACT" for x in possible),
            "roof_interfaces_with_contact_and_tube_grid_alignment":sum(x["actual_mesh_pair_relation"]=="CONTACT" and x["official_LDraw_tube_and_stud_geometry"]["tube_stud_grid_match"] for x in possible),
            "all_final_step_mesh_collision_occurrences":sum(len(x["unclassified_final_mesh_collisions"]) for x in insertion),
            "roof_mesh_collisions":bad,"insertions_blocked_before_clutch_zone":len(blocked),
            "blocked_insertions":blocked,"all_insertions_continuously_verified":False,
            "genuine_lego_material_strength_verified":False}
        report={"candidate":candidate,"counts":counters,"roof_connections":possible,
            "selected_actual_mesh_pair_relations":pairs,"insertion_samples":insertion,
            "source_nominal_support_chain":graph_nominal["graph_supporter_counts"],
            "notes":"Only bbox-screened roof pairs, every movement tested at finite sampled 48,32,24,16,8,4,2,0 LDU; no all-pairs insertion/proven continuous path",
            "approval":"NOT_VALIDATED"}
        path=outdir/candidate/"REAL-LDRAW-ROOF-AND-INSERTION.json"
        path.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
        print("A2_CANDIDATE",candidate,json.dumps({k:v for k,v in counters.items()
             if not isinstance(v,list)},sort_keys=True))
        for row in possible: print("A2_ROOF_BEARING",candidate,row["roof_piece_id"],
              "parent",row["bearing_piece_id"],
              "official_tube_match",row["official_LDraw_tube_and_stud_geometry"]["tube_stud_grid_match"],
              "mesh",row["actual_mesh_pair_relation"])
        for row in bad:print("A2_COLLISION",candidate,row["a"],row["b"],row["relation"])
        for row in bad:print("A2_COLLISION_WITNESS",candidate,row["a"],row["b"],json.dumps(row.get("collision_witness")))
        for row in blocked[:6]: print("A2_EARLY_INSERTION_BLOCK",candidate,row["pid"],row["blocking_earlier_steps"][:2])
        allsummary.append({"candidate":candidate,**counters})
    (outdir/"COMPARE-CANDIDATES.json").write_text(json.dumps(allsummary,indent=2)+"\n")
    return allsummary

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--ldraw-root",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    run(args.ldraw_root,args.output)
