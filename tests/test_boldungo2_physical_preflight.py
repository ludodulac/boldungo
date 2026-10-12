"""Regression tests for BOLDUNGO2 fail-closed physical preflight."""
import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("physical", Path(__file__).resolve().parents[1] / "scripts" / "audit_boldungo2_physical.py")
physical = importlib.util.module_from_spec(spec)
spec.loader.exec_module(physical)

def brick(pid, x=0, y=0, z=0, name="BRICK_2X2", w=2, l=2, h=3):
    return dict(placement_id=pid, part_id=name, x_studs=x, y_studs=y, z_plates=z,
                width_studs=w, length_studs=l, height_plates=h)

def check(parts):
    return physical.audit({"brick_model": {"parts": parts}})

class PhysicalPreflightTests(unittest.TestCase):
    def test_collision_refused(self):
        result = check([brick("a"), brick("b", x=1)])
        self.assertGreater(result["counts"].get("SOLID_AABB_OVERLAP", 0), 0)
        self.assertFalse(result["certified_buildable"])

    def test_adjacent_bricks_not_collision(self):
        result = check([brick("a"), brick("b", x=2)])
        self.assertEqual(result["counts"].get("SOLID_AABB_OVERLAP", 0), 0)
        self.assertFalse(result["certified_buildable"])  # connector proof missing

    def test_fake_catalog_id_refused(self):
        result = check([brick("a", name="BRICK_SLOPED_4X36")])
        self.assertEqual(result["counts"]["UNVERIFIED_PART_ID"], 1)

    def test_wrong_dimensions_refused(self):
        result = check([brick("a", name="BRICK_1X1")])
        self.assertEqual(result["counts"]["CATALOG_DIMENSION_MISMATCH"], 1)

    def test_off_grid_refused(self):
        result = check([brick("a", x=0.3)])
        self.assertEqual(result["counts"]["OFF_INTEGER_GRID"], 1)

    def test_no_floating_certification(self):
        result = check([brick("a", z=30)])
        self.assertFalse(result["certified_buildable"])
        self.assertEqual(result["counts"]["CONNECTOR_VALIDATION_NOT_IMPLEMENTED"], 1)

if __name__ == "__main__":
    unittest.main()
