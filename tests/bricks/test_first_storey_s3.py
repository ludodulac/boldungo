"""S-3: only added 27 bricks; S-1 and S-2 are accepted unmodified."""
from collections import Counter
from dataclasses import replace
from scripts import build_documented_frame_s1 as s1
from scripts import build_upper_floor_s3 as s3

def test_first_real_small_storey_with_two_distinct_wall_sections():
    orig=s1.model()
    p=s3.build()
    assert len(orig)==20 and len(p)==47
    assert p[:20]==orig
    new=p[20:]
    assert Counter(q.role for q in new)=={"wall":20,"upper_beam":2,"upper_floor":5}
    assert Counter(q.ref for q in new)=={"3003":20,"3006":2,"3832":5}
    assert {x.y for x in new if x.role=="wall"}=={-5,3}
    assert {x.z for x in new if x.role=="wall"}=={13,16}
    assert {x.z for x in new if x.role=="upper_floor"}=={22}
    assert {x.z for x in new if x.role=="upper_beam"}=={19}
    assert not s3.volume_interior_overlaps(p)

def test_all_40_new_links_have_four_nominal_stud_centres_and_reach_S1_base():
    p=s3.build(); by={q.id:q for q in p}
    edges=s3.new_edges(p)
    assert len(edges)==40
    assert all(s1.stud_mating(a,b)["valid"] for a,b in edges)
    assert all(s1.stud_mating(a,b)["common_stud_cells"]==4 for a,b in edges)
    assert all(s3.path_to_base(q,by)[-1]=="S1-BASE" for q in p if q.role=="upper_floor")
    assert all(len(s3.path_to_base(q,by))==10 for q in p if q.role=="upper_floor")

def test_negative_reject_beam_shifted_one_stud():
    p=s3.build()
    beam=next(x for x in p if x.role=="upper_beam")
    wall=next(x for x in p if x.id==beam.parents[0])
    good=s1.stud_mating(beam,wall)
    bad=s1.stud_mating(replace(beam,x=beam.x+1),wall)
    assert good["valid"] and good["common_stud_cells"]==4
    assert not bad["valid"] and bad["common_stud_cells"]==2

def test_negative_reject_wall_not_on_lower_deck():
    p=s3.build()
    wall=next(x for x in p if x.role=="wall")
    deck=next(x for x in p if x.id==wall.parents[0])
    assert s1.stud_mating(wall,deck)["valid"]
    assert not s1.stud_mating(replace(wall,z=wall.z+1),deck)["valid"]

def test_all_parts_have_real_ldraw_references_and_valid_matrices():
    p=s3.build()
    lines=[s1.ldraw_line(x).split() for x in p]
    assert len(lines)==47 and all(len(a)==15 for a in lines)
    assert set(a[-1] for a in lines)=={
        "91405.dat","3003.dat","3006.dat","3832.dat"}
    assert all(x.ref in s1.DIM for x in p)

def test_four_nominal_phases_match_a_small_house_storey():
    p=s3.build()
    assert Counter(q.role for q in p)=={
        "base":1,"column":12,"beam":2,"floor":5,
        "wall":20,"upper_beam":2,"upper_floor":5}
    assert all(q.parents for q in p[1:])
    assert [s1.ldraw_line(q) for q in p[:20]]==[
        s1.ldraw_line(q) for q in s1.model()]

def test_s2_static_proof_is_reused_without_weakening():
    from pathlib import Path
    s=Path("scripts/build_upper_floor_s3.py").read_text()
    assert "missions/S2/RESULTATS-S2.md" in s
    assert "full_47_piece_mesh_collision_scan" in s
    assert "NOT_PERFORMED" in s
    assert "NOT_PROVEN" in s
