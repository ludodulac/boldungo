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
    for candidate in (T1,T2):
        y=candidate["y_studs"]
        upper=[
            BrickModelPart(placement_id=f"board:{i}",part_id="BRICK_2X8",
                category="timber",component="facade_detail",facade="left",
                x_studs=x,y_studs=17 if y==19 else 17,z_plates=36,
                rotation_quarter_turns=0)
            for i,x in enumerate((3,5,7,9))
        ]
        c=BrickModelPart.model_validate(candidate)
        assert sum(validate_connection(c,b).status=="VALID" for b in upper)==4
        assert all(validate_connection(c,b).interface_count==1 for b in upper)
