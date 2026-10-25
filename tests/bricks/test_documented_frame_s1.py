"""S-1: one bounded, repeatable 20-piece structure and mandatory bad mating."""
import json
from dataclasses import replace
import pytest
from scripts.build_documented_frame_s1 import (
    model,stud_mating,planned_edges,ldraw,ldraw_line,DIM,
    OFFICIAL_MANUAL,PAGES,svg
)

def test_one_20_piece_load_path_from_floor_to_real_plate():
    parts=model()
    assert len(parts)==20
    from collections import Counter
    assert Counter(p.role for p in parts)=={
        "base":1,"column":12,"beam":2,"floor":5}
    assert Counter(p.ref for p in parts)=={
        "91405":1,"3003":12,"3006":2,"3832":5}
    edges=planned_edges(parts)
    assert len(edges)==26
    assert all(stud_mating(upper,lower)["valid"] for upper,lower in edges)
    assert all(stud_mating(a,b)["common_stud_cells"]==4 for a,b in edges)
    byid={p.id:p for p in parts}
    for floor in (p for p in parts if p.role=="floor"):
        for beam in floor.parents:
            sequence=[floor.id,beam]
            p=byid[beam]
            while p.parents:
                p=byid[p.parents[0]]
                sequence.append(p.id)
            assert sequence[-1]=="S1-BASE"
            assert len(sequence)==6

def test_nominal_mating_rejects_deliberate_one_stud_offset():
    parts=model();by={p.id:p for p in parts}
    upper=next(p for p in parts if p.role=="beam")
    lower=by[upper.parents[0]]
    assert stud_mating(upper,lower)["valid"]
    shifted=replace(upper,x=upper.x+1)
    invalid=stud_mating(shifted,lower)
    assert not invalid["valid"]
    assert invalid["common_stud_cells"]==2

def test_nominal_mating_rejects_wrong_plate_height():
    parts=model();by={p.id:p for p in parts}
    upper=next(p for p in parts if p.role=="floor")
    lower=by[upper.parents[0]]
    assert stud_mating(upper,lower)["valid"]
    assert not stud_mating(replace(upper,z=upper.z+1),lower)["valid"]

def test_ldraw_true_type1_matrix_and_color():
    parts=model()
    lines=[s.split() for s in ldraw(parts).splitlines() if s.startswith("1 ")]
    assert len(lines)==20
    assert all(len(tokens)==15 for tokens in lines)
    assert sorted({p[-1] for p in lines})==[
        "3003.dat","3006.dat","3832.dat","91405.dat"]
    assert [p.id for p in parts if p.role=="floor" and p.rot!=(
        0,0,1,0,1,0,-1,0,0)]==[]

def test_nominal_whole_body_not_interpenetrating():
    parts=model()
    def solids(p):return (p.x,p.y,p.z,p.x+p.w,p.y+p.d,p.z+p.h)
    for i,a in enumerate(parts):
        x0,y0,z0,x1,y1,z1=solids(a)
        for b in parts[i+1:]:
            X0,Y0,Z0,X1,Y1,Z1=solids(b)
            assert not (min(x1,X1)>max(x0,X0)
                and min(y1,Y1)>max(y0,Y0)
                and min(z1,Z1)>max(z0,Z0)),(a.id,b.id)

def test_source_experimental_not_copy():
    assert "6038244.pdf" in OFFICIAL_MANUAL
    assert PAGES["horizontal_tie"]=="printed 43-44 / steps 33-34"
    assert "SCHÉMATIQUE" in svg(model())
    assert "NOT a LEGO-official" in ldraw(model())

@pytest.mark.parametrize("role,expected",[
    ("base",(16,16,1)),("column",(2,2,3)),
    ("beam",(10,2,3)),("floor",(2,10,1))
])
def test_four_real_design_footprints(role,expected):
    p=next(p for p in model() if p.role==role)
    assert (p.w,p.d,p.h)==expected
    assert DIM[p.ref]==expected
