"""R-3 recipe tests: two real independent models, fail-closed dimensions.

These checks do NOT claim physical assembly or complete mesh collision proof.
"""
import json
from collections import Counter
from dataclasses import replace
from pathlib import Path
import pytest

from scripts.generate_roof_recipe_r3 import (
    recipe,export,ldraw,nominal_audit,nominal_mating_alignment,
    validate,SOURCES
)
from scripts.render_roof_r3_preview import svg

@pytest.mark.parametrize("length,pieces,roof,braces",[
    (8,22,8,2),
    (16,46,16,6)
])
def test_two_generatable_lengths_have_two_pans_two_courses_ridge(length,pieces,roof,braces,tmp_path):
    arr=recipe(width_studs=8,length_studs=length,pitch_degrees=45,overhang_studs=0)
    info=nominal_audit(arr)
    assert len(arr)==pieces
    assert info["roof_parts"]==roof
    assert Counter(p.role for p in arr)["cross"]+Counter(p.role for p in arr)["joint"]==braces
    assert info["nominal_components"]==1, info
    assert not info["no_nominal_bearing"]
    assert not info["nominal_misaligned_parent_pairs"]
    assert not info["not_reaching_nominal_foundation"]
    assert all(len(p.parents)==2 for p in arr if p.role in ("slope","ridge"))
    assert {p.part for p in arr}==({"3832","3001","4445","3022"} if length==8 else {"3832","3001","4445","3022","3023"})
    assert sum(p.part=="3001" for p in arr)==12*(length//8)
    assert sum(p.part=="4445" for p in arr)==4*(length//8)
    assert sum(p.part=="3023" for p in arr)==2*(length//8-1)
    assert sum(p.part=="3022" for p in arr)==4*(length//8)
    lines=[x.split() for x in ldraw(arr,length).splitlines() if x.startswith("1 ")]
    assert len(lines)==pieces and all(len(x)==15 for x in lines)
    out=tmp_path/f"R3-{length}"
    export(out,8,length,45,0)
    assert (out/"ROOF-R3.ldr").read_text()==ldraw(arr,length)
    b=json.loads((out/"BOM.json").read_text())
    assert b["parts"]==pieces
    assert sum(b["by_part"].values())==pieces
    assert len(json.loads((out/"ORDER.json").read_text()))==pieces
    view=svg(8,length)
    assert "SCHÉMATIQUE" in view and "<polygon" in view
    assert len(view)>10000

@pytest.mark.parametrize("arg,value,msg",[
    ("width_studs",10,"R3_WIDTH"),
    ("width_studs",12,"R3_WIDTH"),
    ("length_studs",9,"R3_LENGTH"),
    ("length_studs",40,"R3_LENGTH"),
    ("pitch_degrees",22,"R3_PITCH"),
    ("pitch_degrees",18,"R3_PITCH"),
    ("overhang_studs",1,"R3_OVERHANG"),
])
def test_unsupported_parameter_is_explicitly_refused(arg,value,msg):
    kw=dict(width_studs=8,length_studs=8,pitch_degrees=45,overhang_studs=0)
    kw[arg]=value
    with pytest.raises(ValueError,match=msg):
        recipe(**kw)

def test_deliberate_roof_one_stud_bad_shift_fails_grid_alignment():
    parts=recipe()
    sl=next(p for p in parts if p.role=="slope" and p.x==2)
    parent=next(p for p in parts if p.id==sl.parents[0])
    assert nominal_mating_alignment(sl,parent)
    shifted=replace(sl,x=sl.x+1)
    assert not nominal_mating_alignment(shifted,parent)
    with_shift=[shifted if p.id==sl.id else p for p in parts]
    report=nominal_audit(with_shift)
    assert any(a==sl.id for a,b in report["nominal_misaligned_parent_pairs"])

def test_provenance_marks_all_r3_placements_as_experimental():
    parts=recipe()
    assert all("R3" in p.source or "MODULAR" in p.source or "ADAPTATION_BRIDGE" in p.source for p in parts)
    assert SOURCES["R3_not_official_31009_placement"] is True
    assert SOURCES["physical_strength_certified"] is False
    assert SOURCES["original_31009_mapped_steps"]["3001"]==[12]
    assert SOURCES["original_31009_mapped_steps"]["3022"]==[24]
