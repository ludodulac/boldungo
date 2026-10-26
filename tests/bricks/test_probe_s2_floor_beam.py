"""S-2: reject invented compatibility; test just ONE existing interface."""
from dataclasses import replace
from pathlib import Path
from scripts.build_documented_frame_s1 import model,stud_mating,ldraw_line
from scripts.probe_s2_floor_beam import to_local

def test_offending_floor_beam_is_exact_one_pair_not_a_new_model():
    parts=model()
    floor=next(p for p in parts if p.role=="floor")
    beam=next(p for p in parts if p.id==floor.parents[0])
    assert (floor.ref,beam.ref)==("3832","3006")
    assert stud_mating(floor,beam)["common_stud_cells"]==4
    assert len(parts)==20
    assert "3832.dat" in ldraw_line(floor)
    assert "3006.dat" in ldraw_line(beam)

def test_deliberately_wrong_vertical_height_fails():
    parts=model()
    plate=next(p for p in parts if p.role=="floor")
    beam=next(p for p in parts if p.id==plate.parents[0])
    assert stud_mating(plate,beam)["valid"]
    bad=replace(plate,z=plate.z-1)
    assert not stud_mating(bad,beam)["valid"]

def test_collision_must_not_be_auto_whitelisted():
    src=Path("scripts/probe_s2_floor_beam.py").read_text()
    assert '"static_interface_verdict":"NON_RESOLU"' in src
    assert 'check_collision(ap,bp)' in src
    assert 'negative_deliberate_4_LDU_vertical_interference_relation' in src
    assert 'repetitions_examined":1' in src

def test_original_s1_lives_unmodified_with_true_20_part_bom():
    from collections import Counter
    assert Counter(p.ref for p in model())=={"91405":1,"3003":12,"3006":2,"3832":5}
