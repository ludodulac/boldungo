"""059N integrated staging test on actual 1894 preview and frozen 1890 baseline."""
import json
from pathlib import Path
from brickhouse.bricks.export import BrickExportBundle
from scripts.generate_terrace_059n_staged_notice import run,build,ordering,ORIGINAL
from scripts.export_guided004_059m_reinforced import produce

def test_059n_reproducible_1894_staged_notice(tmp_path):
    canon=(ORIGINAL/"brick-model.json").read_bytes()
    # CI prepares the canonical GUIDED-004, but intentionally does not run
    # the separate experimental 059M preview before pytest. Recreate that
    # exact preview here so the test is self-contained and reproducible.
    preview_dir=tmp_path/"preview"
    produce(dest=preview_dir)
    bundle=BrickExportBundle.model_validate_json(
        (preview_dir/"viewer-export-reinforced.json").read_text(encoding="utf-8"))
    boards,hidden,patches,beams,after=ordering(bundle.brick_model)
    assert (len(boards),len(hidden),len(patches),len(beams),len(after))==(21,9,2,2,47)
    plan,_=build(bundle)
    assert plan.total_parts==1894
    assembled=[pid for st in plan.steps for pid in st.placement_ids]
    assert len(assembled)==len(set(assembled))==1894
    assert plan.steps[0].phase=="Structure"
    staged,report=run(preview=preview_dir,output=tmp_path/"staged")
    assert report["original_parts"]==1890
    assert report["reinforced_parts"]==1894
    assert report["floor_preassembled_parts"]==34
    assert report["deferred_placements"]==47
    assert len(report["deferred_ids"])==47
    assert report["physical_clutch"]=="NOT_CERTIFIED"
    assert staged.assembly_plan.total_parts==staged.instruction_plan.total_parts==staged.bag_plan.total_parts==1894
    assert staged.bom.total_parts==1894
    assert (ORIGINAL/"brick-model.json").read_bytes()==canon
    j=BrickExportBundle.model_validate_json(
        (tmp_path/"staged"/"viewer-export-staged-1894.json").read_text(encoding="utf-8"))
    assert j.assembly_plan.total_parts==1894
    assert (tmp_path/"staged"/"staged-terrace-guide.md").is_file()
    assert len(j.assembly_plan.steps)==report["staged_instruction_steps"]
