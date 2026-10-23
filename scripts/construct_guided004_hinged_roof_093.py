"""Build, export and visualize the actual articulated LDraw roof over GUIDED-004.

The primary BrickModel is preserved without falsifying its integer-grid
schema. The resulting *composite* is the foundation BrickModel + a rigid
LDraw part-transform overlay (.ldr and JSON). All visuals derive only from
that composite's actual transforms. Unsupported meshes remain unsupported.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib,json,math
from pathlib import Path

from brickhouse.bricks.brick_model import BrickModel
from brickhouse.bricks.geometry_adapter import (
  CANONICAL_LDRAW_PARTS,brick_model_part_transform)
from brickhouse.bricks.articulated_roof_093 import build_093, PARTS
from brickhouse.bricks.roof_collision_093 import inspect_093_envelopes
from brickhouse.bricks.catalog import standard_orthogonal_definitions

DEFS=standard_orthogonal_definitions()

def ldraw_row(ldraw,xyz,rot,color=16):
    return ("1 %d "%color + " ".join(f"{v:.7f}" for v in (
        xyz[0],xyz[1],xyz[2],
        rot[0][0],rot[0][1],rot[0][2],
        rot[1][0],rot[1][1],rot[1][2],
        rot[2][0],rot[2][1],rot[2][2])) + " "+ldraw+".dat")

def save_ldraw(model,assembly,path):
    lines=["0 FILE BOLDUNGO_GUIDED004_EXPERIMENTAL_093.ldr",
      "0 LEGO2-093: physical LDraw parts with rigid 22 degree transforms",
      "0 !CATEGORY Model",
      "0 !KEYWORDS NOT_CERTIFIED hinge interface and structural loads not verified",
      "0 Step 1 - model's mapped orthogonal masonry + details"]
    omitted=[]
    mapped=0
    for p in model.parts:
        mapping=CANONICAL_LDRAW_PARTS.get(p.part_id)
        if mapping is None or mapping.placement_kind!="standard":
            omitted.append(p.placement_id)
            continue
        m=brick_model_part_transform(p,mapping).matrix
        lines.append(ldraw_row(mapping.ldraw_id,(m[0][3],m[1][3],m[2][3]),
              [row[:3] for row in m[:3]]))
        mapped+=1
    lines+=["0 STEP","0 Step 2 - real 4275b and 4276b hinge pairs, rails, panel, tiles"]
    for p in assembly:
        lines.append(ldraw_row(p["ldraw_id"],p["xyz_ldu"],p["rotation"]))
    lines+=["0 NOFILE"]
    path.write_text("\n".join(lines)+"\n",encoding="utf8")
    return {"source_brick_model_part_count":len(model.parts),
            "ldraw_mapped_brick_model_part_count":mapped,
            "unmapped_architectural_details_count":len(omitted),
            "unmapped_placement_ids":omitted,
            "articulated_ldraw_placed_parts":len(assembly),
            "full_view_has_all_facade_details":len(omitted)==0}

def part_bbox_transformed(p):
    """Corners of real catalogue part lengths, rotated by its rigid LDraw matrix."""
    length,width=PARTS[p["ldraw_id"]][1:]
    # LDraw plate and tile top at y=0, underface at y=8. Hinge fingers
    # deliberately excluded: visual envelopes do NOT certify hinge clearance.
    points=[]
    for x in (-length*10,length*10):
        for y in (0,8):
            for z in (-width*10,width*10):
                v=[p["xyz_ldu"][i]+sum(p["rotation"][i][j]*q
                      for j,q in enumerate((x,y,z))) for i in range(3)]
                points.append(v)
    return points

def project(view,p):
    x,y,z=p
    if view=="perspective":return (0.82*x-0.45*z,0.27*x+0.52*z+1.3*y)
    if view=="front":return (x,y)
    if view=="rear":return (-x,y)
    if view=="north":return (z,y)
    if view=="south":return (-z,y)
    if view=="roof":return (x,z)
    if view=="frame":return (0.82*x-0.45*z,0.27*x+0.52*z+1.3*y)
    raise ValueError(view)

def draw_views(foundation,assembly,out):
    # Real transformed corners; make SVG projections WITHOUT inventing a plane.
    out.mkdir(parents=True,exist_ok=True)
    struct=[]
    for p in foundation.parts:
        mapping=CANONICAL_LDRAW_PARTS.get(p.part_id)
        if (mapping is None or mapping.placement_kind!="standard" or
               p.component not in ("wall","roof_support","facade_detail")):
            continue
        d=DEFS.get(p.part_id)
        if not d:continue
        mat=brick_model_part_transform(p,mapping).matrix
        ww,hh=d.footprint(p.rotation_quarter_turns)
        # Coordinate BBox in LDraw: x horizontal and z building depth.
        arr=[[x,y,z] for x in [p.x_studs*20,(p.x_studs+ww)*20]
               for y in [-p.z_plates*8,-(p.z_plates+d.height_plates)*8]
               for z in [p.y_studs*20,(p.y_studs+hh)*20]]
        struct.append({"id":p.placement_id,"class":p.component,"corners":arr,
                       "color":"#c2c6ce" if p.component=="wall" else "#a78365"})
    panel=[]
    for p in assembly:
        kinds={"roof_skin":"#75899f",
               "rafter_base":"#c38b62","rafter_lap":"#ba7850",
               "hinge_base":"#c9723f","hinge_roof":"#d5a56c",
               "purlin_upper":"#886548","purlin_lap":"#755039",
               "truss_bottom_tie":"#7d5b35","truss_sloping_chord":"#995a26",
               "truss_king_post":"#d18832","ridge_purlin":"#714e2d",
               "ridge_cover_flat":"#617e94"}
        panel.append({"id":p["placement_id"],"class":p["kind"],
                      "corners":part_bbox_transformed(p),
                      "color":kinds.get(p["kind"],"#828899")})
    for view in ("perspective","front","rear","north","south","roof","frame"):
        # Hide ONLY tile skin for exposed structure view.
        show=struct+[p for p in panel if view!="frame" or p["class"]!="roof_skin"]
        projected=[(p,[project(view,x) for x in p["corners"]]) for p in show]
        extrema=[v for item,pts in projected for v in pts]
        minx=min(p[0] for p in extrema);maxx=max(p[0] for p in extrema)
        miny=min(p[1] for p in extrema);maxy=max(p[1] for p in extrema)
        scale=min(1140/max(maxx-minx,1),725/max(maxy-miny,1))
        def xy(t):
            return (45+(t[0]-minx)*scale,75+(t[1]-miny)*scale)
        data=['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="850">',
         '<rect width="1200" height="850" fill="#f1f5f8"/>',
         '<text x="30" y="33" font-size="24" font-family="Arial">BOLDUNGO 093 — '+view.upper()+'</text>',
         '<text x="30" y="54" font-size="13" font-family="Arial">Vraies transformations LDraw; enveloppes des pièces, pas des maillages; N6 NON CERTIFIÉ.</text>']
        def rank(row):
            q=row[1][0]
            return (q[0]+q[1]) if view in ("perspective","frame") else q[1]
        # This is a technical projections that does not perform true hidden
        # surface elimination; rectangles mark transformed physical extents.
        for p,pts in sorted(projected,key=rank):
            # Vertices are paired [(xmin,ymin,zmin)..]; show body envelopes.
            # Projected convex hull is based on ACTUAL transformed 3D points.
            q=[xy(v) for v in pts]
            hull=convex_hull(q)
            if not hull:continue
            points=" ".join(f"{x:.2f},{y:.2f}" for x,y in hull)
            data.append(f'<polygon points="{points}" fill="{p["color"]}" fill-opacity=".31" stroke="{p["color"]}" stroke-width=".4"/>')
        data+=['<text x="25" y="827" font-size="14" font-family="Arial">Attention : collision charnière, insertion et stabilité restent des contrôles non clos.</text>',
               "</svg>"]
        (out/(view+".svg")).write_text("\n".join(data)+"\n",encoding="utf8")
    return 7

def convex_hull(points):
    pts=sorted(set((round(x,2),round(y,2)) for x,y in points))
    if len(pts)<=1:return pts
    def area(o,a,b):return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    low=[];up=[]
    for p in pts:
        while len(low)>=2 and area(low[-2],low[-1],p)<=0:low.pop()
        low.append(p)
    for p in reversed(pts):
        while len(up)>=2 and area(up[-2],up[-1],p)<=0:up.pop()
        up.append(p)
    return low[:-1]+up[:-1]

def run(source,output,pitch=22.):
    source_hash=hashlib.sha256(source.read_bytes()).hexdigest()
    model=BrickModel.model_validate_json(source.read_bytes())
    if len(model.parts)<5:
        raise ValueError("HOUSE_TOO_SMALL")
    a=build_093(model,pitch=pitch)
    output.mkdir(parents=True,exist_ok=True)
    foundation=a["foundation"]
    (output/"BRICKMODEL-093-UNCHANGED-MASONRY-PLUS-EAVE-SILLS.json").write_text(
          foundation.model_dump_json(indent=2)+"\n",encoding="utf8")
    ldraw=save_ldraw(foundation,a["articulated_parts"],output/"REAL-HINGED-ROOF-093.ldr")
    nviews=draw_views(foundation,a["articulated_parts"],output/"views")
    base_report=a["report"]
    pc=math.cos(math.radians(pitch))
    pivots={
      "negative":base_report["eave_world_cross_studs"][0]+4*pc,
      "positive":base_report["eave_world_cross_studs"][1]-4*pc
    }
    collision=inspect_093_envelopes(foundation,a["articulated_parts"],
                     pitch,pivots,base_report["eave_z_plates"])
    (output/"ENVELOPE-AND-SAMPLED-SWEEP-093.json").write_text(
      json.dumps(collision,indent=2)+"\n",encoding="utf8")
    rep={**a["report"],**ldraw,
      "collision_and_insertion_screen":collision,
      "source_sha256":source_hash,"views_count":nviews,
      "model_schema":"COMPOSITE_BRICKMODEL_PLUS_REAL_LDRAW_RIGID_TRANSFORMS",
      "all_4275b_4276b_pivot_pairs_verified_coaxial":True,
      "upper_frame_type":"SLOPED_RAFTER_RAILS_AND_EAVE_BEARING_SILLS",
      "true_TRIANGULATED_LOAD_RATED_TRUSS":False,
      "roof_panel_to_wall_bearing_certification":"DENIED"}
    (output/"ASSEMBLY-093-EXACT-PLACEMENTS-AND-CONNECTORS.json").write_text(
      json.dumps({"report":rep,"articulated_parts":a["articulated_parts"],
                   "hinge_axes":a["hinge_axes"],
                   "connections":a["connections"]},indent=2)+"\n",encoding="utf8")
    bom=Counter(p["ldraw_id"] for p in a["articulated_parts"])
    new_sills=[p for p in foundation.parts if p.placement_id.startswith("EXPERIMENT-093-EAVE-")]
    removed_deck=[p for p in model.parts if p.placement_id.startswith("EXPERIMENT-091-")]
    sill_counts=Counter(p.part_id for p in new_sills)
    removed_counts=Counter(p.part_id for p in removed_deck)
    b={"articulated_roof":[{"ldraw_id":k,"quantity":v,"color":"UNSPECIFIED"}
         for k,v in sorted(bom.items())],
       "structural_eave_sill_parts_count":rep["new_structural_eave_sill_parts"],
       "new_structural_eave_sill_bom":[{"part_id":pid,
            "ldraw_id":CANONICAL_LDRAW_PARTS[pid].ldraw_id,
            "quantity":n,"color":"UNSPECIFIED"}
             for pid,n in sorted(sill_counts.items())],
       "prior_091_parts_removed":rep["source_091_removed_count"],
       "removed_091_bom":[{"part_id":pid,
            "ldraw_id":CANONICAL_LDRAW_PARTS[pid].ldraw_id,
            "quantity":n,"color":"UNSPECIFIED"}
             for pid,n in sorted(removed_counts.items())],
       "new_total":rep["composite_total_part_count"],
       "prior_091_total":len(model.parts),
       "all_positions_in":"ASSEMBLY-093-EXACT-PLACEMENTS-AND-CONNECTORS.json and BRICKMODEL-093-UNCHANGED-MASONRY-PLUS-EAVE-SILLS.json",
       "colors_ready_for_purchase":False}
    (output/"BOM-093.json").write_text(json.dumps(b,indent=2)+"\n",encoding="utf8")
    plan=[
      "# LEGO2-093 — vraie couverture inclinée, construction candidate seulement",
      "Statut NOT_CERTIFIED. Aucune notice définitive, aucun achat.",
      f"Pièces composées : {rep['composite_total_part_count']} (091: {len(model.parts)}).",
      f"Angle réel de modules articulés : {rep['actual_panel_pitch_degrees']}°.",
      f"Entraxes de charnières vérifiés géométriquement : {rep['coaxial_hinge_axis_pairs']}.",
      f"Raccords de crête : {rep['ridge_status']} (écart nominal {rep['ridge_nominal_gap_studs']} tenons).",
      f"Charnières sans point de fondation nominal : {len(rep['unsupported_hinge_bearings'])}.",
      "La toiture est construite avec de vraies plaques/tiles/hinges LDraw,",
      "mais les pertes de compatibilité mécanique, la charge, l'engagement",
      "des doigts et les collisions maillées ne sont PAS démontrés.",
      "Étape 1 — Murs réels conservés. Étape 2 — assises croisées de briques",
      "et plaques 2-wide sur la tête des murs. Étape 3 — charnières 4275b.",
      "Étape 4 — préassemblage panneau incliné en deux rails et plaques croisées,",
      "avec tuiles 87079. Étape 5 — charnière 4276b, poser les pans à 22°.",
      "STOP : étudier un vrai faîtage compatible, insertion charnières et une",
      "ferme portante triangulée, avant approbation physique N6.",
    ]
    (output/"ORDRE-MONTAGE-093-NON-CERTIFIE.md").write_text(
          "\n".join(plan)+"\n",encoding="utf8")
    print("LEGO2_093_COMPONENTS",rep["composite_total_part_count"])
    print("LEGO2_093_HINGE_PAIRS",rep["coaxial_hinge_axis_pairs"])
    print("LEGO2_093_UNSUPPORTED_BEARINGS",len(rep["unsupported_hinge_bearings"]))
    print("LEGO2_093_RIDGE",rep["ridge_status"])
    print("LEGO2_093_WALL_ENVELOPE_COLLISIONS",collision["tile_vs_orthogonal_wall_envelope_intersections_count"])
    print("LEGO2_093_RIDGE_ENVELOPE_COLLISIONS",collision["ridge_opposing_tip_tile_envelope_intersections_count"])
    print("LEGO2_093_SWEEP_ENVELOPE_COLLISIONS",collision["sampled_sweep_envelope_intersections_count"])
    print("LEGO2_093_MESH_INSERTION",rep["insertion_swept_mesh_screen"])
    print("LEGO2_093_VIEWS",nviews)
    print("LEGO2_093_PHYSICAL_STATUS",rep["physical_certification"])
    return rep

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--source",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--pitch",type=float,default=22.)
    args=ap.parse_args()
    run(args.source,args.output,args.pitch)
