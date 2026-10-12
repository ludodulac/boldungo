"""Fail-closed physical preflight for BOLDUNGO2 preview bundles.

Usage: python scripts/audit_boldungo2_physical.py frontend/data/boldungo2-lego-house-019.json
This is a conservative preflight, NOT a LEGO connector/stability simulator.
"""
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

def audit(bundle):
    parts = bundle["brick_model"]["parts"]
    problems = []
    counts = Counter()
    valid = []
    for p in parts:
        pid = p.get("placement_id", "?")
        name = p.get("part_id", "")
        dims = [p.get("width_studs"), p.get("length_studs"), p.get("height_plates")]
        if not all(isinstance(v, (int, float)) and math.isfinite(v) and v > 0 for v in dims):
            problems.append(("INVALID_DIMENSIONS", pid))
            counts["INVALID_DIMENSIONS"] += 1
            continue
        if not re.fullmatch(r"(BRICK|PLATE)_[1-9][0-9]*X[1-9][0-9]*", name):
            problems.append(("UNVERIFIED_PART_ID", pid))
            counts["UNVERIFIED_PART_ID"] += 1
        else:
            kind, a, b = re.fullmatch(r"(BRICK|PLATE)_([0-9]+)X([0-9]+)", name).groups()
            if sorted([int(a), int(b)]) != sorted(dims[:2]) or (kind == "BRICK" and dims[2] != 3) or (kind == "PLATE" and dims[2] != 1):
                problems.append(("CATALOG_DIMENSION_MISMATCH", pid))
                counts["CATALOG_DIMENSION_MISMATCH"] += 1
        if any(abs(p.get(axis, 0) - round(p.get(axis, 0))) > 1e-6 for axis in ("x_studs", "y_studs", "z_plates")):
            problems.append(("OFF_INTEGER_GRID", pid))
            counts["OFF_INTEGER_GRID"] += 1
        valid.append(p)
    for i, a in enumerate(valid):
        for b in valid[i+1:]:
            overlap = all(min(a[pos]+a[size], b[pos]+b[size])-max(a[pos], b[pos]) > 1e-6 for pos,size in (("x_studs","width_studs"),("y_studs","length_studs"),("z_plates","height_plates")))
            if overlap:
                counts["SOLID_AABB_OVERLAP"] += 1
                if len(problems) < 500:
                    problems.append(("SOLID_AABB_OVERLAP", a["placement_id"], b["placement_id"]))
    # This check cannot prove stud/tube engagement, hinges, support or stability.
    counts["CONNECTOR_VALIDATION_NOT_IMPLEMENTED"] = 1
    return {"status": "FAIL" if counts else "PASS", "certified_buildable": False,
            "part_count": len(parts), "counts": dict(counts), "examples": problems[:100],
            "note": "AABB collisions are conservative for slopes/windows; exact meshes and real connector data are mandatory before certification."}

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: audit_boldungo2_physical.py MODEL.json")
    result = audit(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(1 if result["status"] != "PASS" else 0)
