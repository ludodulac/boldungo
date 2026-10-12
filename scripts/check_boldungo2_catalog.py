"""Fail-closed catalog preflight for BOLDUNGO2 house exports.

Run: python scripts/check_boldungo2_catalog.py frontend/data/boldungo2-lego-house-019.json
Exit 1 means NOT buildable. This is only the first gate; a zero-error result
does not certify collisions, insertion or structural strength.
"""
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from brickhouse.bricks.physical_placement_gate import Placement

def audit(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    parts = data["brick_model"]["parts"]
    errors = Counter()
    for part in parts:
        try:
            expected = Placement(
                part["part_id"], part["x_studs"], part["y_studs"],
                part["z_plates"], part.get("rotation_quarter_turns", 0)
            ).dimensions()
        except (ValueError, TypeError, KeyError, AttributeError):
            errors["UNLISTED_PART"] += 1
            continue
        actual = tuple(part.get(key) for key in (
            "width_studs", "length_studs", "height_plates"
        ))
        if actual != expected:
            errors["WRONG_CATALOG_DIMENSIONS"] += 1
        elif not all(
            isinstance(part.get(axis), int) and not isinstance(part.get(axis), bool)
            for axis in ("x_studs", "y_studs", "z_plates")
        ):
            errors["OFF_GRID"] += 1
    return {
        "total": len(parts),
        "catalog_valid": len(parts) - sum(errors.values()),
        "errors": dict(errors),
        "status": "FAIL" if errors else "CATALOG_ONLY_PASS",
        "physical_buildability_certified": False,
    }

def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        raise SystemExit("Usage: check_boldungo2_catalog.py <house.json>")
    report = audit(argv[0])
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if report["errors"] else 0

if __name__ == "__main__":
    sys.exit(main())
