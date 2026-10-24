"""A-2 bounded explicit part counts and two independent pitched rows."""
from collections import Counter

from scripts.construct_small_roof_a2 import generate,staged_parts
from scripts.experiment_stacked_roofs_a import _ldraw

def test_two_explicit_real_ridge_candidates():
    for candidate in ("3023b","3022"):
        parts=staged_parts(generate(candidate))
        assert len({p.pid for p in parts})==len(parts)
        assert sum(p.role=="slope" for p in parts)==4
        assert {p.side for p in parts if p.role=="slope"}=={"left","right"}
        assert {p.step for p in parts if p.role=="slope"}=={1,2}
        assert {p.ldraw for p in parts if p.role=="ridge"}=={candidate}
        assert Counter(p.ldraw for p in parts)["3003"]>=4
        assert parts[0].ldraw=="3811"
        assert parts[-1].role=="ridge"
        assert all(len(x.split())==15 for x in _ldraw(parts,20,20,"A-2").splitlines() if x.startswith("1 "))

def test_alternative_has_one_large_ridge_instead_of_two_small():
    p=generate("3023b"); q=generate("3022")
    assert len(p)==len(q)+1
    assert sum(x.role=="ridge" for x in p)==2
    assert sum(x.role=="ridge" for x in q)==1
