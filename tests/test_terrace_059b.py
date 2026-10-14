"""Fixed 059B candidate geometry and conservative experimental status."""
from scripts.prototype_terrace_059b import T1, T2
from scripts.audit_terrace_048 import box, overlap
from brickhouse.bricks.brick_model import BrickModelPart
from brickhouse.bricks.connectors import validate_connection


def test_fixed_candidates_are_distinct_and_do_not_collide():
    assert (T1["part_id"],T1["x_studs"],T1["y_studs"],T1["z_plates"],T1["rotation_quarter_turns"]) == ("BRICK_1X8",6,19,33,1)
    assert (T2["part_id"],T2["x_studs"],T2["y_studs"],T2["z_plates"],T2["rotation_quarter_turns"]) == ("BRICK_1X8",6,22,33,1)
    assert not overlap(box(T1),box(T2))


def test_both_connect_to_four_real_deck_boards():
    # Frozen GUIDED-004 real boards (not fabricated x=5,7,9,11 geometry).
    from tests.test_terrace_structural_056 import terrace_parts
    by={p.placement_id.split("south-timber-deck-main:")[1]:p for p in terrace_parts()}
    expected={"board:00007":1,"board:00013":2,
              "board:00019":2,"board:00031":1}
    for candidate in (T1,T2):
        c=BrickModelPart.model_validate(candidate)
        found={name:validate_connection(c,by[name]).interface_count for name in expected}
        assert found==expected
        assert all(validate_connection(c,by[name]).status=="VALID" for name in expected)
        assert sum(found.values())==6
