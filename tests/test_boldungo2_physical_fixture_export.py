"""Contract tests for a downloadable BOM + screened assembly plan."""
from collections import Counter
from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "physical_fixture_export", ROOT / "scripts" / "export_boldungo2_physical_fixture.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

def test_package_bom_matches_actual_brick_model():
    package = module.create_package()
    parts = package["brick_model"]["parts"]
    bom = package["bill_of_materials"]
    assert len(parts) == 12
    assert bom["total_parts"] == len(parts)
    assert bom["parts_by_id"] == dict(sorted(Counter(p["part_id"] for p in parts).items()))
    assert bom["parts_by_id"]["BRICK_2X10"] == 1
    assert package["validation_level"] == "GEOMETRY_ONLY"
    assert package["connector_validation"] == "NOT_CHECKED"
    assert package["physical_certification"] is False
    assert package["physical_strength_certified"] is False
    assert package["insertability_certified"] is False
    assert package["architectural_fidelity_certified"] is False

def test_export_plan_references_every_piece_exactly_once():
    package = module.create_package()
    actual = [p["placement_id"] for p in package["brick_model"]["parts"]]
    scheduled = [
        pid for step in package["assembly_plan"]["steps"]
        for pid in step["placement_ids"]
    ]
    assert sorted(scheduled) == sorted(actual)
    assert len(scheduled) == len(set(scheduled))
