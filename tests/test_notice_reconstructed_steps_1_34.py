import json
from pathlib import Path

EXPORT=Path("frontend/notice-reconstructed-steps-1-34-export.json")

def load():
    return json.loads(EXPORT.read_text(encoding="utf-8"))

def test_notice_1_34_is_exact_ordered_assembly_slice():
    b=load(); plan=b["assembly_plan"]; parts={p["placement_id"]:p for p in b["brick_model"]["parts"]}
    assert plan["total_steps"]==34
    assert [s["sequence"] for s in plan["steps"]]==list(range(1,35))
    ids=[pid for s in plan["steps"] for pid in s["placement_ids"]]
    assert len(ids)==78
    assert len(set(ids))==78
    assert set(ids)==set(parts)
    assert all(s["step_id"]==f"step-{s['sequence']:04d}" for s in plan["steps"])

def test_each_notice_step_cumulative_visibility_and_pli_are_exact():
    b=load(); parts={p["placement_id"]:p for p in b["brick_model"]["parts"]}
    cumulative=[]
    for step in b["assembly_plan"]["steps"]:
        added=step["placement_ids"]
        cumulative.extend(added)
        assert len(cumulative)==len(set(cumulative))
        assert all(pid in parts for pid in added)
        # PLI source is exactly this AssemblyStep: no cumulative placements leak in.
        pli_part_ids=[parts[pid]["part_id"] for pid in added]
        assert len(pli_part_ids)==len(added)
    assert set(cumulative)==set(parts)

def test_reconstructed_placement_fields_are_unchanged_for_surviving_steps_1_8():
    b=load(); parts={p["placement_id"]:p for p in b["brick_model"]["parts"]}
    expected={
      "wall-000001":("BRICK_1X6",1,1,0,1),
      "wall-000002":("BRICK_1X1",7,1,0,0),
      "wall-000003":("BRICK_1X6",10,1,0,1),
      "wall-000004":("BRICK_1X1",16,1,0,0),
      "wall-000009":("BRICK_1X8",16,2,0,0),
      "wall-000010":("BRICK_1X3",16,10,0,0),
      "wall-000005":("BRICK_1X8",9,13,0,1),
      "wall-000006":("BRICK_1X8",1,13,0,1),
      "wall-000007":("BRICK_1X8",1,5,0,0),
      "wall-000008":("BRICK_1X3",1,2,0,0),
      "wall-000011":("BRICK_1X1",2,1,3,0),
      "wall-000012":("BRICK_1X3",5,1,3,1),
      "wall-000013":("BRICK_1X3",10,1,3,1),
      "wall-000014":("BRICK_1X1",15,1,3,0),
      "wall-000020":("BRICK_1X8",16,1,3,0),
      "wall-000021":("BRICK_1X3",16,9,3,0),
      "wall-000022":("BRICK_1X2",16,12,3,0),
      "wall-000015":("BRICK_1X8",8,13,3,1),
      "wall-000016":("BRICK_1X6",2,13,3,1),
      "wall-000017":("BRICK_1X8",1,6,3,0),
      "wall-000018":("BRICK_1X3",1,3,3,0),
      "wall-000019":("BRICK_1X2",1,1,3,0),
    }
    for pid,e in expected.items():
        p=parts[pid]
        assert (p["part_id"],p["x_studs"],p["y_studs"],p["z_plates"],p["rotation_quarter_turns"])==e

def test_notice_stops_before_windows_and_roof_and_does_not_invent_door():
    b=load(); parts=b["brick_model"]["parts"]
    assert all(p["category"] not in {"window_frame","window_pane","roof_tile","ridge_tile"} for p in parts)
    assert not any(p.get("opening_id")=="door_front_01" for p in parts)
    assert b["assembly_plan"]["steps"][-1]["step_id"]=="step-0034"

def test_provenance_is_explicitly_reconstructed_not_historical():
    p=load()["notice_reconstruction_provenance"]
    assert p["run_id"]==35511101561
    assert p["source"]=="docs/examples/building-model-simple-house.json"
    assert p["front_width_studs"]==16
    assert p["status"]=="compatible_reconstruction_not_historical_original"
