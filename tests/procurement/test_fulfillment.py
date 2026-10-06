import csv
from io import StringIO

from brickhouse.procurement.catalog import load_part_crosswalk
from brickhouse.procurement.fulfillment import (
    parse_supplier_confirmation_csv,
    supplier_confirmation_template_csv,
    validate_supplier_confirmation,
)
from brickhouse.procurement.models import BagOrderManifest, CanonicalOrderPackage, OrderLine


def _package():
    brick = OrderLine(part_id="BRICK_2X4", category="brick", quantity=3)
    tile = OrderLine(part_id="TILE_2X2", category="ridge_tile", quantity=2)
    return CanonicalOrderPackage(
        building_id="house", volume_id="main", total_parts=5, unique_part_types=2,
        total_bags=1, order_lines=[brick, tile],
        bags=[BagOrderManifest(
            bag_number=1, phases=["Structure"], assembly_step_ids=["s1"],
            total_parts=5, lines=[brick, tile],
        )],
    )


def _colors():
    return {
        ("BRICK_2X4", None): "light_bluish_gray",
        ("TILE_2X2", None): "black",
    }


def _confirmed_csv():
    template = supplier_confirmation_template_csv(
        _package(), load_part_crosswalk(), purchase_colors=_colors()
    )
    rows = list(csv.DictReader(StringIO(template)))
    for row in rows:
        row["confirmed_quantity"] = row["required_quantity"]
        row["status"] = "exact_confirmed"
    output = StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=rows[0].keys(), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def test_confirmation_template_is_prefilled_but_never_pretends_supplier_confirmed():
    text = supplier_confirmation_template_csv(
        _package(), load_part_crosswalk(), purchase_colors=_colors()
    )
    rows = list(csv.DictReader(StringIO(text)))
    assert len(rows) == 2
    assert {row["status"] for row in rows} == {"pending"}
    assert {row["confirmed_quantity"] for row in rows} == {""}
    assert {row["required_quantity"] for row in rows} == {"3", "2"}


def test_exact_supplier_confirmation_proves_all_parts_confirmed():
    lines = parse_supplier_confirmation_csv(_confirmed_csv())
    report = validate_supplier_confirmation(
        _package(), load_part_crosswalk(),
        purchase_colors=_colors(), confirmation_lines=lines,
    )
    assert report.complete
    assert report.total_required_parts == 5
    assert report.exact_confirmed_parts == 5
    assert report.blockers == []


def test_one_missing_piece_blocks_complete_status():
    lines = parse_supplier_confirmation_csv(_confirmed_csv())
    brick = next(line for line in lines if line.part_id == "BRICK_2X4")
    brick.confirmed_quantity = 2
    report = validate_supplier_confirmation(
        _package(), load_part_crosswalk(),
        purchase_colors=_colors(), confirmation_lines=lines,
    )
    assert not report.complete
    assert report.exact_confirmed_parts == 2
    assert [(b.reason, b.required_quantity, b.confirmed_quantity) for b in report.blockers] == [
        ("confirmed_quantity_not_exact", 3, 2)
    ]


def test_supplier_substitution_is_not_accepted_as_complete():
    lines = parse_supplier_confirmation_csv(_confirmed_csv())
    brick = next(line for line in lines if line.part_id == "BRICK_2X4")
    brick.status = "substitution_proposed"
    report = validate_supplier_confirmation(
        _package(), load_part_crosswalk(),
        purchase_colors=_colors(), confirmation_lines=lines,
    )
    assert not report.complete
    assert [b.reason for b in report.blockers] == [
        "substitution_requires_explicit_approval"
    ]


def test_changed_supplier_reference_is_blocked():
    lines = parse_supplier_confirmation_csv(_confirmed_csv())
    brick = next(line for line in lines if line.part_id == "BRICK_2X4")
    brick.supplier_part_ref = "WRONG"
    report = validate_supplier_confirmation(
        _package(), load_part_crosswalk(),
        purchase_colors=_colors(), confirmation_lines=lines,
    )
    assert not report.complete
    assert [b.reason for b in report.blockers] == [
        "supplier_part_reference_changed"
    ]
