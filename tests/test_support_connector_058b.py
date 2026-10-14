"""LEGO2-058B: evidence-limited 1x1 post to 2-wide deck brick.

LDraw: official 3002.dat -> 3002s01.dat and 2456.dat show
underside stud4 tubes, sidewalls, and conventional top stud arrays.
VALID is interface compatibility only, never mechanical strength.
"""
from brickhouse.bricks.brick_model import BrickModelPart
from brickhouse.bricks.connectors import validate_connection


def piece(pid, kind, x, y, z, rotation=0, **extra):
    return BrickModelPart(
        placement_id=pid, part_id=kind, category="timber",
        component="facade_detail", facade="left", x_studs=x, y_studs=y,
        z_plates=z, rotation_quarter_turns=rotation, **extra
    )


def test_west_actual_one_stud_connection():
    post = piece("support-solution:timber-post-west:0033:00034", "BRICK_1X1", 4, 34, 33)
    board = piece("board:00003", "BRICK_2X3", 3, 33, 36)
    result = validate_connection(post, board)
    assert (result.status, result.interface_count) == ("VALID", 1)
    assert validate_connection(board, post) == result


def test_return_west_one_stud_connection():
    post = piece("return-support", "BRICK_1X1", 8, 40, 33)
    board = piece("return-board", "BRICK_2X6", 7, 39, 36)
    assert (validate_connection(post, board).status,
            validate_connection(post, board).interface_count) == ("VALID", 1)


def test_east_existing_valid():
    post = piece("support-east", "BRICK_1X1", 4, 18, 33)
    board = piece("board:00001", "BRICK_2X8", 3, 17, 36)
    assert validate_connection(post, board).status == "VALID"


def test_no_contact_and_outside_footprint():
    for kind in ("BRICK_2X3", "BRICK_2X6"):
        post = piece("post", "BRICK_1X1", 4, 34, 33)
        assert validate_connection(post, piece("away", kind, 30, 33, 36)).status == "INVALID"
        assert validate_connection(post, piece("offset", kind, 5, 34, 36)).status == "INVALID"


def test_vertical_misalignment_and_collision():
    post = piece("post", "BRICK_1X1", 4, 34, 33)
    for kind in ("BRICK_2X3", "BRICK_2X6"):
        assert validate_connection(post, piece("gap", kind, 3, 33, 37)).status == "INVALID"
        assert validate_connection(post, piece("collision", kind, 3, 33, 35)).status == "INVALID"


def test_unsupported_rotation_and_inconsistent_dimensions():
    post = piece("post", "BRICK_1X1", 4, 34, 33)
    for kind in ("BRICK_2X3", "BRICK_2X6"):
        wrong = piece("wrong", kind, 3, 33, 36, rotation=1, width_studs=99, length_studs=99)
        assert validate_connection(post, wrong).status == "UNKNOWN"


def test_other_lower_families_not_automatically_promoted():
    for kind in ("BRICK_2X3", "BRICK_2X6"):
        lower = piece("lower", "BRICK_1X2", 4, 34, 33)
        upper = piece("upper", kind, 3, 33, 36)
        assert validate_connection(lower, upper).status == "UNKNOWN"


def test_undocumented_upper_family_remains_unknown():
    post = piece("post", "BRICK_1X1", 4, 34, 33)
    upper = piece("upper", "BRICK_1X3", 4, 34, 36)
    assert validate_connection(post, upper).status == "UNKNOWN"

def test_rotation_changes_actual_stud_footprint():
    post = piece("post", "BRICK_1X1", 4, 35, 33)
    unrotated = piece("upper-a", "BRICK_2X3", 3, 33, 36, rotation=0)
    rotated = piece("upper-b", "BRICK_2X3", 3, 33, 36, rotation=1)
    assert validate_connection(post, unrotated).status == "VALID"
    assert validate_connection(post, rotated).status == "INVALID"
