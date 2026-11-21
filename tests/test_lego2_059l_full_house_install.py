"""059L: real GUIDED-004, FULL house clearance, NOT mechanical certification."""
import json
from pathlib import Path
import pytest
from scripts.audit_terrace_059l_full_house_install import study

EXPORT=Path('artifacts/lego2-guided-004/brick-model.json')

@pytest.mark.parametrize('variant,naive_count',[('B',83),('C',86)])
def test_059l_full_house_insertion_order(variant,naive_count):
    model=json.loads(EXPORT.read_text(encoding='utf-8'))
    original=json.dumps(model,sort_keys=True)
    r=study(model,variant)
    assert r['original_parts']==1890
    assert r['naive_full_house_blockers']==naive_count
    assert r['staged_floor_blockers']==[]
    assert r['later_stages']==47
    assert r['later_blockers']==[]
    assert r['floor_geometric_components']==[29,1]
    assert r['combined_floor_and_rail_components']==[69]
    assert r['board33_nominal_bridge']=={
        'board33_to_railpost':1,'board27_to_railpost':1}
    assert len(r['floor_lower_host_contacts'])==6
    assert r['nearby_unmodeled_parts']==[]
    assert r['connection_strength']=='NOT_CERTIFIED'
    assert r['physical_buildability']=='NOT_CERTIFIED'
    assert json.dumps(model,sort_keys=True)==original
