from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"


def test_viewer_supports_generic_same_origin_direct_bundle() -> None:
    source = (FRONTEND / "viewer.js").read_text(encoding="utf-8")
    assert "get('bundle')" in source
    assert "url.origin!==window.location.origin" in source
    assert "loadDirectBundle()" in source
    assert "renderBundle(await r.json(),{persist:false})" in source
    assert "progressiveModule==='001'" not in source
    assert "loadModule001()" not in source


def test_module_001_is_valid_generic_direct_bundle() -> None:
    bundle = json.loads((FRONTEND / "module-001-export.json").read_text(encoding="utf-8"))
    assert bundle["schema_version"] == "0.1"
    assert bundle["building_id"] == "real-house-progressive"
    assert bundle["volume_id"] == "module-001-main-mass"
    model = bundle["brick_model"]
    assert model["volume_id"] == "module-001-main-mass"
    assert len(model["parts"]) == 180
    assert bundle["bom"]["total_parts"] == 180
    assert (model["width_studs"], model["depth_studs"], model["height_plates"]) == (24, 20, 45)
