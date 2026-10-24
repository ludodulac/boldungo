"""A-3 fail-closed regression: actual official LDraw, including a bad connector.

Executed only AFTER the pinned CI runner downloads its official LDraw closure.
"""
import os
import pytest
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))

from lego_geometry_engine import LDrawLibrary, Transform, instantiate
from construct_small_roof_a2 import staged_parts, generate
from verify_small_roof_a2 import located
from verify_small_roof_a3 import (audit_seats, primitive_spec, STATUS_BAD,
                                   STATUS_OK, STATUS_UNKNOWN,vertical_broadphase,
                                   parent_chains)

def fixture():
    if "A3_LDRAW_ROOT" not in os.environ:
        pytest.skip("A-3 official LDraw geometry tests require pinned CI dependency closure")
    root=Path(os.environ["A3_LDRAW_ROOT"])
    parts=staged_parts(generate("3022"))
    instances=located(parts,LDrawLibrary(root))
    return root,parts,instances

def test_four_roof_seats_and_two_side_ridge_and_all_foundations():
    root,parts,instances=fixture()
    seats,parents,missing=audit_seats(parts,instances,root)
    assert len(parts)==24
    assert len(seats)==23
    assert sum(len(x["parents"]) for x in seats)==24
    assert len(missing)==0
    assert all(x["status"]==STATUS_OK for x in seats)
    assert sum(x["parents"]==["baseplate"] for x in seats)==4
    ridge=next(x for x in seats if x["child"]=="ridge-3022")
    assert len(ridge["parents"])==2
    assert all(3.95<=d<=4.05 for s in seats for d in s["stud_engagement_ldu"])

def test_bad_20_ldu_shift_cannot_pass_as_valid_stud_tube_seat():
    root,parts,instances=fixture()
    slope=next(p for p in parts if p.role=="slope" and p.side=="left" and p.step==2)
    old=instances[slope.pid]
    # Move the real 30363 1 stud sideways (along world Z) but LEAVE its claimed
    # supporter unchanged. Previous 'CONTACT' or graph alone cannot approve it.
    instances[slope.pid]=instantiate(old.definition,slope.pid,
        Transform.translation(0,0,20).compose(old.transform))
    seats,parents,missing=audit_seats(parts,instances,root)
    row=next(s for s in seats if s["child"]==slope.pid)
    assert row["status"]==STATUS_BAD
    assert row["real_official_tube_and_studs_fit"] is False
    assert slope.pid in missing
    assert "ridge-3022" in missing

def test_disjoint_xy_broadphase_is_continuous_only_when_mathematically_disjoint():
    root,parts,instances=fixture()
    seats,parents,missing=audit_seats(parts,instances,root)
    stages=vertical_broadphase(parts,instances,parents,seats)
    assert len(stages)==23
    assert sum(x["entire_insertion_proven"] for x in stages)==18
    assert sum(x["status"]==STATUS_UNKNOWN for x in stages)==5
    assert all(x["entire_insertion_proven"] is False for x in stages
        if next(p for p in parts if p.pid==x["id"]).role in ("slope","ridge"))
    assert any(x["whole_translation_proved_disjoint_from_previous_pieces"] for x in stages)
