"""LEGO2-098 official-LDraw-derived Technic axis audit.

Directly transcribed type-1 lines from official 32278, 32524, 32017,
2780 and 6558 DAT definitions and the P/confric5 primitive.
IMPORTANT: confric5 longitudinal axis is its LOCAL Y, which is mapped to
PART-LOCAL X in 2780 and 6558. A primitive's Y axis is not a part's Y axis.
These literal official source lines are deliberately assertions, not guessed
catalogue semantics, and have exact upstream URLs beside each sample.
LDraw license/attribution: CC BY 2.0 / CC BY 4.0, authors on source pages.
"""
from __future__ import annotations
from collections import Counter
from math import hypot
from .articulated_roof_093 import rigid

SOURCE="https://raw.githubusercontent.com/pybricks/ldraw/master/"
OFFICIAL_TYPE1={
 "32278":{
   "url":SOURCE+"parts/32278.dat",
   "reference":"1 16 0 0 20 1 0 0 0 1 0 0 0 -1 beamhole.dat",
   "primitive_y_axis":(0.,1.,0.),"primitive":"beamhole.dat"},
 "32524":{
   "url":SOURCE+"parts/32524.dat",
   "reference":"1 16 0 0 20 1 0 0 0 -1 0 0 0 1 beamhole.dat",
   "primitive_y_axis":(0.,1.,0.),"primitive":"beamhole.dat"},
 "32017":{
   "url":SOURCE+"parts/32017.dat",
   "reference":"1 16 0 0 20 -1 0 0 0 1 0 0 0 -1 beamhol2.dat",
   "primitive_y_axis":(0.,1.,0.),"primitive":"beamhol2.dat"},
 "2780":{
   "url":SOURCE+"parts/2780.dat",
   "reference":"1 16 0 0 0 0 1 0 0 0 1 1 0 0 confric5.dat",
   "primitive_y_axis":(0.,1.,0.),"primitive":"confric5.dat"},
 "6558":{
   "url":SOURCE+"parts/6558.dat",
   "reference":"1 16 -10 0 0 0 1 0 0 0 1 1 0 0 confric5.dat",
   "primitive_y_axis":(0.,1.,0.),"primitive":"confric5.dat"}
}

def type1_matrix(line):
    items=line.split()
    if len(items)!=15 or items[0]!="1":
        raise ValueError("INVALID_OFFICIAL_TYPE1_LINE")
    numbers=[float(x) for x in items[5:14]]
    return [numbers[i:i+3] for i in (0,3,6)]

def transform(matrix,axis):
    return tuple(round(sum(matrix[i][j]*axis[j] for j in range(3)),9)
                 for i in range(3))

def unit_column(R,j):
    return tuple(float(R[i][j]) for i in range(3))

def part_local_axis(ldraw_id):
    src=OFFICIAL_TYPE1[ldraw_id]
    return transform(type1_matrix(src["reference"]),src["primitive_y_axis"])

def physical_axes():
    return {k:part_local_axis(k) for k in OFFICIAL_TYPE1}

# True official part local axis: beams -> Y, pins -> X.
PIN_PART_LOCAL_AXIS=(1.,0.,0.)
BEAM_PART_LOCAL_AXIS=(0.,1.,0.)
EXPECTED_WORLD_AXIS=(0.,0.,1.)

def real_pin_rotation():
    """Right-handed map from pin PART local X to world Z."""
    return ((0.,0.,-1.),(0.,1.,0.),(1.,0.,0.))

def real_beam_rotation(direction):
    """Right-handed beam PART local Y to WORLD Z, local Z along XY run."""
    dx,dy=direction
    if abs(hypot(dx,dy)-1.)>1e-7:raise ValueError("BEAM_LENGTH_NOT_UNIT")
    return ((-dy,0.,dx),(dx,0.,dy),(0.,1.,0.))

def corrected_technic_part(p):
    """Reorient real LDraw geometry about each existing hole center."""
    lid=p["ldraw_id"]
    if lid not in OFFICIAL_TYPE1:
        return p,False
    old=p["rotation"]
    if lid in ("2780","6558"):
        desired=real_pin_rotation()
    else:
        direction=(old[0][2],old[1][2])
        desired=real_beam_rotation(direction)
    q={**p,"rotation":[list(row) for row in desired]}
    physical=transform(q["rotation"],part_local_axis(lid))
    if any(abs(physical[i]-EXPECTED_WORLD_AXIS[i])>1e-8 for i in range(3)):
        raise AssertionError(f"REAL_PART_AXIS_NOT_WORLD_Z_{lid}")
    return q,any(abs(q["rotation"][i][j]-old[i][j])>1e-9
                 for i in range(3) for j in range(3))

def correct_legacy_096_overlay(overlay):
    fixed=[];corrected=[];wrong=[]
    for part in overlay:
        if part["ldraw_id"] not in OFFICIAL_TYPE1 or not part["placement_id"].startswith(("095-F","096-F")):
            fixed.append(part)
            continue
        prior=transform(part["rotation"],part_local_axis(part["ldraw_id"]))
        if any(abs(prior[i]-EXPECTED_WORLD_AXIS[i])>1e-8 for i in range(3)):
            wrong.append({"id":part["placement_id"],"ldraw":part["ldraw_id"],
                          "old_axis_world":prior})
        q,did=corrected_technic_part(part)
        fixed.append(q)
        if did:corrected.append(part["placement_id"])
    if not corrected or not any(x.startswith("096-F6-") for x in corrected):
        raise AssertionError("MUST_CORRECT_BOTH_095_AND_096_F6")
    return fixed,{"wrong_before":wrong,"corrected_count":len(corrected),
                  "corrected_ids":corrected,
                  "corrected_by_ldraw":dict(Counter(p["ldraw_id"] for p in fixed
                          if p["placement_id"] in set(corrected))),
                  "contains_uncorrected_096_F6":False,
                  "real_official_local_axes":physical_axes(),
                  "all_reoriented_pin_axis_from_part_local_X":True,
                  "all_reoriented_beam_hole_axis_from_part_local_Y":True,
                  "pin_full_3d_sweep_verified":False,
                  "mechanical_stability_not_implied":True}

def test_transform_matrix_of_LDraw_part(part):
    return transform(part["rotation"],part_local_axis(part["ldraw_id"]))
