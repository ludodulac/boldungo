"""R-2 targeted regression: manual LEGO 31009 group counts and model fidelity."""
from collections import Counter
import json
from pathlib import Path
import pytest

from scripts.reconstruct_official_31009_r2 import (
    read_parts,assemble_ldraw,stats,build,make_svg,EXPECTED_PER_STEP,SLOPES
)

def test_80_placements_exactly_match_25_manual_step_inventory(tmp_path):
    p=read_parts()
    assert len(p)==80
    assert p[0]["ord"]==149 and p[-1]["ord"]==228
    assert [len([x for x in p if x["step"]==i]) for i in range(1,26)]==list(EXPECTED_PER_STEP)
    assert len(SLOPES)==5
    assert stats(p)["roof_sloped_parts"]==29
    assert stats(p)["bom_by_design"]["4445"]==6
    assert stats(p)["bom_by_design"]["3037"]==10
    assert stats(p)["bom_by_design"]["3038"]==4
    assert stats(p)["bom_by_design"]["3039"]==5
    assert stats(p)["bom_by_design"]["3046"]==4
    assert "3811" not in stats(p)["bom_by_design"]
    assert stats(p)["bom_by_design"]["3022"]==1  # chimney, NEVER fake ridge
    assert sum(stats(p)["bom_by_design"].values())==80

def test_reproduce_deterministically_with_manual_step_separators(tmp_path):
    ev,bom=build(tmp_path)
    s=(tmp_path/"31009-ROOF-R2-OFFICIAL-STEP-RECONSTRUCTION.ldr").read_text()
    assert s.count("0 STEP")==24
    assert s.count("0 // OFFICIAL LEGO STEP")==25
    assert len([x for x in s.splitlines() if x.startswith("1 ")])==80
    assert [len(x.split()) for x in s.splitlines() if x.startswith("1 ")]==[15]*80
    assert ev["sources"]["coordinate_source_IS_NOT_official_LEGO"] is True
    assert ev["continuous_assembly_experiment_proven"] is False
    assert ev["no_extra_piers_or_3022_ridge"] is True
    order=json.loads((tmp_path/"OFFICIAL-STEPS-ORDER.json").read_text())
    assert len(order)==25 and len(order[-1]["pieces"])==5
    assert sum(len(s["pieces"]) for s in order)==80
    assert len(make_svg(read_parts()))>20000

def test_official_step_4_starts_one_pan_step_10_other():
    p=read_parts()
    assert Counter(x["part"] for x in p if x["step"]==4)=={
       "3039.dat":2,"4445.dat":1}
    assert Counter(x["part"] for x in p if x["step"]==10)=={
       "3037.dat":1,"4445.dat":1}
    assert Counter(x["part"] for x in p if x["step"]==11)=={
       "3037.dat":1,"4445.dat":1,"3002.dat":2}
    assert Counter(x["part"] for x in p if x["step"]==24)=={
       "3003.dat":1,"3004.dat":2,"3022.dat":1,"3062.dat":1}
    assert Counter(x["part"] for x in p if x["step"]==25)=={
       "3046.dat":2,"3038.dat":2,"3037.dat":1}

def test_mutated_source_must_be_rejected(tmp_path):
    s=Path("missions/R2/31009-ROOF-STEP-PLACEMENTS.tsv").read_text()
    bad=tmp_path/"mutated.tsv"
    bad.write_text(s.replace("4445.dat","fakepart.dat",1))
    with pytest.raises(ValueError,match="UNKNOWN_PART"):
        read_parts(bad)
    bad.write_text(s.replace("1\t47\t", "99\t47\t",1))
    with pytest.raises(AssertionError):
        read_parts(bad)
