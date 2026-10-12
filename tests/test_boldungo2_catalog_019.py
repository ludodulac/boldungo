"""Ensure legacy visual 019 cannot be mistaken for a validated LEGO build."""
from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "boldungo2_catalog_checker", ROOT / "scripts" / "check_boldungo2_catalog.py"
)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)

def test_visual_house_019_fails_canonical_catalog_gate():
    report = checker.audit(ROOT / "frontend" / "data" / "boldungo2-lego-house-019.json")
    assert report["total"] == 2852
    assert report["errors"]["UNLISTED_PART"] == 2262
    assert report["errors"]["WRONG_CATALOG_DIMENSIONS"] == 582
    assert report["catalog_valid"] == 8
    assert report["status"] == "FAIL"
    assert report["physical_buildability_certified"] is False

def test_cli_returns_failure_for_visual_house_019():
    path = ROOT / "frontend" / "data" / "boldungo2-lego-house-019.json"
    assert checker.main([str(path)]) == 1
