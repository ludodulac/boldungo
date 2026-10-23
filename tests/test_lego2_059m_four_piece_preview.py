"""059M: the approved four extras are reproducible, but NOT yet canonical.

The 1890 parts and default export stay bit-for-bit unchanged.
"""
import json
from pathlib import Path

import pytest

from scripts.export_guided004_059m_reinforced import (
    SOURCE, PREFIX, TAG, SPECS, make_preview, nominal_plate_studs, produce,
    staged_audit,
)
from brickhouse.bricks.brick_model import BrickModel
from brickhouse.bricks.export import BrickExportBundle


def test_059m_four_hidden_parts_1894_preview_no_official_mutation(tmp_path):
    canonical_bytes=(SOURCE/"brick-model.json").read_bytes()
    original=BrickModel.model_validate_json(canonical_bytes)
    assert len(original.parts)==1890
    preview, extras, contacts=make_preview(original)
    assert len(preview.parts)==1894
    assert len(extras)==4
    assert [p.placement_id for p in extras]==[TAG+s[0] for s in SPECS]
    assert [p.model_dump() for p in original.parts]==[
        p.model_dump() for p in preview.parts[:1890]]
    assert staged_audit(preview)["floor_nominal_contact_components"]==[34]
    result, evidence=produce(dest=tmp_path)
    assert evidence["total_bricks"]==1894
    assert result.model_dump()==preview.model_dump()
    bundle=BrickExportBundle.model_validate_json(
        (tmp_path/"viewer-export-reinforced.json").read_text(encoding="utf-8"))
    assert bundle.bom.total_parts==1894
    assert bundle.assembly_plan.total_parts==1894
    assert bundle.instruction_plan.total_parts==1894
    assert bundle.bag_plan.total_parts==1894
    assert (SOURCE/"brick-model.json").read_bytes()==canonical_bytes
    assert len(BrickModel.model_validate_json(canonical_bytes).parts)==1890
    assert len(evidence["nominal_ldraw_interfaces"])==6


@pytest.mark.parametrize("plate_name,host_id,expected",[
    ("BOARD33-Y34","board:00027",2),
    ("BOARD33-Y34","board:00033",1),
    ("BOARD33-Y35","board:00027",2),
    ("BOARD33-Y35","board:00033",1),
])
def test_059m_nominal_ldraw_underside_clearances(plate_name,host_id,expected):
    base=BrickModel.model_validate_json(
        (SOURCE/"brick-model.json").read_text(encoding="utf-8"))
    preview, extras, _=make_preview(base)
    ids={p.placement_id:p for p in preview.parts}
    plate=ids[TAG+plate_name]; host=ids[PREFIX+host_id]
    contacts=nominal_plate_studs(plate,host)
    assert len(contacts)==expected
    assert all(c["sidewall_gap"]==0 and c["endwall_gap"]>=0 for c in contacts)
    if host_id=="board:00027":
        assert all(c["tube_gap"]==pytest.approx(2**.5*10-14) for c in contacts)
    else:
        assert all(c["underside_stud3_gap"]==0 for c in contacts)


def test_059m_rejects_unreviewed_canonical_host_change():
    base=BrickModel.model_validate_json(
        (SOURCE/"brick-model.json").read_text(encoding="utf-8"))
    changed=[]
    for p in base.parts:
        changed.append(p.model_copy(update={"x_studs":99})
                       if p.placement_id==PREFIX+"board:00027" else p)
    with pytest.raises(AssertionError):
        make_preview(base.model_copy(update={"parts":changed}))
