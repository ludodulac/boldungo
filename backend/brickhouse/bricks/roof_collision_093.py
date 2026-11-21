"""093 conservative OBB collision and limited hinge sweep of real LDraw transforms.

Checks solid rectangular envelopes of actual placed plate/tile catalogue parts
against selected orthogonal load-bearing walls, and the two tip tiles at ridge.
Hinge fingers and true LDraw meshes, full subassembly insertion and strength
are OUT OF SCOPE and cannot be marked CERTIFIED by this geometric screening.
"""
from __future__ import annotations
from itertools import product
from math import sin,cos,radians
from .articulated_roof_093 import PARTS
from .catalog import standard_orthogonal_definitions
DEF=standard_orthogonal_definitions()


def matvec(R,pt):
    return [sum(R[i][j]*pt[j] for j in range(3)) for i in range(3)]


def roof_obb(p):
    length,width=PARTS[p["ldraw_id"]][1:]
    R=p["rotation"];d=matvec(R,(0,4,0))
    center=[p["xyz_ldu"][i]+d[i] for i in range(3)]
    return center,[list(v) for v in zip(*R)],[length*10.,4.,width*10.]


def wall_obb(p):
    d=DEF[p.part_id]
    w,h=d.footprint(p.rotation_quarter_turns)
    p0=(p.x_studs*20.,-(p.z_plates+d.height_plates)*8.,p.y_studs*20.)
    p1=((p.x_studs+w)*20.,-p.z_plates*8.,(p.y_studs+h)*20.)
    return ([(p0[i]+p1[i])/2 for i in range(3)],
             [[1,0,0],[0,1,0],[0,0,1]],
             [(p1[i]-p0[i])/2 for i in range(3)])


def cross(a,b):
    return (a[1]*b[2]-a[2]*b[1],
            a[2]*b[0]-a[0]*b[2],
            a[0]*b[1]-a[1]*b[0])


def dot(a,b):
    return sum(x*y for x,y in zip(a,b))


def envelope_intersect(a,b,epsilon=.01):
    """Separating-axis test of exactly the rotated rectangular ENVELOPES."""
    ac,axesA,ar=a
    bc,axesB,br=b
    delta=[bc[i]-ac[i] for i in range(3)]
    for axis in [*axesA,*axesB,*[cross(x,y) for x in axesA for y in axesB]]:
        norm2=dot(axis,axis)
        if norm2<1e-8:continue
        d=abs(dot(delta,axis))
        r=sum(abs(dot(x,axis))*h for x,h in zip(axesA,ar))
        r+=sum(abs(dot(x,axis))*h for x,h in zip(axesB,br))
        if d>=r-epsilon: return False
    return True


def rotate_about_world_z(p,pivot,delta_degrees):
    """Sample a legal hinge rotation around exact local hinge Z axis."""
    t=radians(delta_degrees)
    R=((cos(t),-sin(t),0.),(sin(t),cos(t),0.),(0.,0.,1.))
    new=dict(p)
    old=p["xyz_ldu"]
    from_pivot=[old[0]-pivot[0],old[1]-pivot[1],old[2]-pivot[2]]
    turn=matvec(R,from_pivot)
    new["xyz_ldu"]=[pivot[i]+turn[i] for i in range(3)]
    new["rotation"]=[[dot(R[i],list(col)) for col in zip(*p["rotation"])]
                     for i in range(3)]
    return new


def inspect_093_envelopes(foundation,instances,angle,eave_side_pivots,zbase):
    tiles=[p for p in instances if p["kind"]=="roof_skin"]
    # Rendered tiles only. The solids are official catalogue pieces but
    # their envelope is conservative; a hit is REQUIRES_LDRAW_MESH_REVIEW.
    near_roof=[p for p in foundation.parts if p.component=="wall"
               and p.part_id in DEF
               and p.z_plates+DEF[p.part_id].height_plates>=zbase-6]
    wallboxes=[(p.placement_id,wall_obb(p)) for p in near_roof]
    direct=[]
    for tile in tiles:
        box=roof_obb(tile)
        for pid,other in wallboxes:
            if envelope_intersect(box,other):
                direct.append((tile["placement_id"],pid))
                if len(direct)>250:break
        if len(direct)>250:break
    grouped={}
    for tile in tiles:
        parts=tile["placement_id"].split("-")
        if not parts[-1].isdigit():continue
        by=(parts[-2],parts[-1])
        grouped.setdefault(by,{})[tile["side"]]=tile
    # Only compare panels covering SAME bay at their final crosswise tip.
    tip=max(int(k[1]) for k in grouped)
    ridge=[]
    for (bay,index),sides in sorted(grouped.items()):
        if int(index)==tip and len(sides)==2:
            if envelope_intersect(roof_obb(sides["negative"]),
                                  roof_obb(sides["positive"])):
                ridge.append(bay)
    swept=[]
    # At eave each outer roof tile follows hinge angular travel. Analyze
    # exact rotated 3D rectangular envelopes at 0,5,...,target angle.
    outer=[p for p in tiles if p["placement_id"].endswith("-0")]
    for tile in outer:
        side=tile["side"]
        pivot=(eave_side_pivots[side]*20.,-((zbase)*8.+4),0.)
        for theta in sorted(set([0.,5.,10.,15.,20.,float(angle)])):
            if theta>angle:continue
            delta=(angle-theta) if side=="negative" else (theta-angle)
            turned=rotate_about_world_z(tile,pivot,delta)
            box=roof_obb(turned)
            for pid,wb in wallboxes:
                if envelope_intersect(box,wb):
                    swept.append({"tile":tile["placement_id"],"wall":pid,
                                  "angle_deg":theta})
                    break
    return {
        "wall_orthogonal_solids_near_roof_examined":len(wallboxes),
        "actual_tile_placement_envelope_tests":len(tiles)*len(wallboxes),
        "tile_vs_orthogonal_wall_envelope_intersections_count":len(direct),
        "tile_vs_wall_sample":direct[:25],
        "ridge_opposing_tip_tile_envelope_intersections_count":len(ridge),
        "ridge_tip_bay_collision_samples":ridge[:20],
        "sampled_angular_sweep_positions_deg":[0,5,10,15,20,angle],
        "sampled_sweep_envelope_intersections_count":len(swept),
        "sampled_sweep_intersections":swept[:20],
        "all_nonorthogonal_scene_geometry_screened":False,
        "all_4275b_4276b_finger_meshes_screened":False,
        "whole_roof_insertion_certified":False,
        "collision_safety_verdict":"NOT_CERTIFIED_UNTIL_FULL_LDRAW_MESH_REVIEW",
    }
