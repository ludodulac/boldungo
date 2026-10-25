"""Bounded R-1 tests: real LDraw part IDs and independently reproducible BOM."""
from collections import Counter
from dataclasses import replace
import json
from pathlib import Path
import pytest

from scripts.experiment_official_roof_r1 import (
    SOURCE, recipe, ldraw, audit_nominal, parent_candidates, build
)

@pytest.mark.parametrize("length,total,slopes,ridges",[
    (8,41,4,4), (16,81,8,8)
])
def test_generic_8_stud_roof_bays(length,total,slopes,ridges,tmp_path):
    parts=recipe(length_studs=length)
    info=audit_nominal(parts)
    assert len(parts)==total
    assert info["total_parts"]==total
    assert info["slope_parts"]==slopes
    assert info["ridge_parts"]==ridges
    assert info["roof_parts"]==slopes+ridges
    assert info["bom_ldraw"]["4445"]==slopes
    assert info["bom_ldraw"]["3022"]==ridges
    assert info["bom_ldraw"]["3007"]==4*(length//8)
    assert info["bom_ldraw"]["3003"]==28*(length//8)
    assert info["bom_ldraw"]["3811"]==1
    assert sum(info["bom_ldraw"].values())==total
    assert info["nominal_unsupported"]==[]
    assert info["nominal_components"]==1
    assert info["physical_stability_proven"] is False
    assert info["all_real_connectors_proven"] is False

    parents,miss,edges=parent_candidates(parts)
    assert edges==48*(length//8)
    assert all(len(parents[p.pid])==2 for p in parts if p.role in ("ridge","beam"))
    assert all(len(parents[p.pid])==1 for p in parts if p.role in ("slope","pier"))
    assert sum(p.role=="slope" and p.side=="left" for p in parts)==slopes//2
    assert sum(p.role=="slope" and p.side=="right" for p in parts)==slopes//2

    model=ldraw(parts)
    lines=[x.split() for x in model.splitlines() if x.startswith("1 ")]
    assert len(lines)==total
    assert all(len(x)==15 and x[-1].endswith(".dat") for x in lines)
    assert sum(x[-1]=="4445.dat" for x in lines)==slopes
    assert all(x[5:14]==["1","0","0","0","1","0","0","0","1"]
               for x in lines if x[-1]=="3811.dat")
    arr,result=build(tmp_path/"R1",length_studs=length)
    assert (tmp_path/"R1"/"R1-31009-EXPERIMENT.ldr").read_text()==model
    assert len(json.loads((tmp_path/"R1"/"ORDER.json").read_text()))==total


def test_staggered_roof_courses_both_panels_have_purlins():
    parts=recipe()
    slopes=[p for p in parts if p.role=="slope"]
    assert {p.course for p in slopes}=={0,1}
    assert {p.side for p in slopes}=={"left","right"}
    assert {p.z for p in slopes}=={12,15}
    assert {p.gx for p in slopes}=={12,14,16,18}
    assert all(p.sy==8 and p.sx==2 for p in slopes)
    assert {p.gx for p in parts if p.role=="ridge"}=={15}


@pytest.mark.parametrize("length,z",[(7,0),(12,0),(24,0),(8,3)])
def test_fail_closed_unsupported_sizes(length,z):
    with pytest.raises(ValueError):
        recipe(length_studs=length,foundation_z=z)

def test_manual_provenance_is_clearly_not_an_official_replica():
    assert SOURCE["set"]=="31009"
    assert SOURCE["official_instructions"].endswith("/6038244.pdf")
    assert SOURCE["not_official_assembly_replica"] is True
    assert SOURCE["ldraw_pin"].startswith("c43ed06")

def test_intentionally_misaligned_slope_has_no_nominal_bearing():
    parts=recipe()
    target=next(p for p in parts if p.role=="slope" and p.side=="left" and p.course==1)
    damaged=[replace(p,gx=p.gx+1) if p.pid==target.pid else p for p in parts]
    parents,unsupported,edges=parent_candidates(damaged)
    assert parents[target.pid]==[]
    assert target.pid in unsupported
    assert edges<48
    # The other side still has a path: do not confuse graph reachability
    # through another member with proof of this particular missing bearing.
