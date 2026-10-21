"""086: ensure portable mobile 30-piece viewer reflects current executable model."""
import json
from html.parser import HTMLParser
from pathlib import Path

import pytest

from scripts.create_ridge_trial_viewer_086 import (
    TEMPLATE, build_viewer_payload, render_offline_viewer,
)


class _ScriptExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.scripts = {}
        self.current = None
        self.external = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "script":
            if "src" in attrs:
                self.external.append(attrs["src"])
            self.current = attrs.get("id", "_js")
            self.scripts.setdefault(self.current, "")
        if tag == "link" and attrs.get("rel") in ("stylesheet", "preload"):
            if attrs.get("href"):
                self.external.append(attrs["href"])

    def handle_data(self, data):
        if self.current:
            self.scripts[self.current] += data

    def handle_endtag(self, tag):
        if tag == "script":
            self.current = None


def test_payload_has_exact_30_parts_24_frame_steps_and_6_unapproved_roofs():
    data = build_viewer_payload()
    assert data["physical_certification"] == "NOT_CERTIFIED"
    assert data["guided004_modified"] is False
    assert data["view_geometry"] == "SIMPLIFIED_VISUAL_ENVELOPES_NOT_LDRAW_MESHES"
    assert len(data["parts"]) == 30
    assert len(data["steps"]) == 24
    assert len(data["roof_parts"]) == 6
    assert {p["id"] for p in data["parts"]} == set(
        [x["id"] for x in data["steps"]] + data["roof_parts"])
    assert all(p["connector_status"] == "REJECTED_UNDOCUMENTED_ROOF_ATTACHMENT"
               for p in data["parts"] if p["type"] == "roof")
    assert data["roof_attach"] == "REJECTED_UNDOCUMENTED"
    assert {r["ldraw_id"]: r["quantity"] for r in data["bom"]} == {
        "3005": 18, "3008": 6, "30363": 6}


def test_every_step_has_exact_supported_model_coordinates():
    data = build_viewer_payload()
    pieces = {p["id"]: p for p in data["parts"]}
    built = set()
    for item in data["steps"]:
        piece = pieces[item["id"]]
        assert piece["type"] == "frame"
        assert piece["w"] > 0 and piece["d"] > 0 and piece["h"] > 0
        if not item["on_ground"]:
            assert item["supports"], item["id"]
            assert all(parent in built for parent in item["supports"])
        assert item["insertion_screen"] == "GEOMETRY_CLEAR_ONLY"
        built.add(item["id"])
    assert len(built) == 24


def test_all_parts_have_correct_rotated_grid_dimensions():
    data = build_viewer_payload()
    for part in data["parts"]:
        if part["part_id"] == "BRICK_1X1":
            assert (part["w"], part["d"], part["h"]) == (1, 1, 1.2)
        elif part["part_id"] == "BRICK_1X8":
            assert (part["w"], part["d"], part["h"]) == (8, 1, 1.2)
        else:
            assert part["part_id"] == "BRICK_SLOPED_18_4X2"
            assert (part["w"], part["d"], part["h"]) == (2, 4, 1.2)


def test_template_renders_usable_offline_html_without_external_dependencies():
    html = render_offline_viewer(TEMPLATE.read_text(encoding="utf-8"),
                                 build_viewer_payload())
    parser = _ScriptExtractor()
    parser.feed(html)
    assert parser.external == [], "offline HTML must not depend on network imports"
    assert "experiment-data" in parser.scripts
    payload = json.loads(parser.scripts["experiment-data"])
    assert len(payload["parts"]) == 30
    assert len(payload["steps"]) == 24
    assert "__TRIAL_DATA_JSON__" not in html
    assert 'id="step"' in html
    assert 'id="roof"' in html
    assert 'id="viewer"' in html
    assert "NOT_CERTIFIED" in html
    assert "non fixées" in html or "non fixés" in html or "non validées" in html
    assert "Glisser" in html and "Pincer" in html
    assert "application/json" in html
    assert len(parser.scripts.get("_js", "")) > 2000


def test_data_escapes_html_script_breakout():
    html = render_offline_viewer(
        "before __TRIAL_DATA_JSON__ after",
        {"text": "</script><script>alert('unsafe')</script>"})
    assert "</script><script>" not in html
    assert "<\\/script>" in html


def test_template_rejects_multiple_or_missing_payload_slots():
    with pytest.raises(ValueError):
        render_offline_viewer("<html/>", {})
    with pytest.raises(ValueError):
        render_offline_viewer("__TRIAL_DATA_JSON__ __TRIAL_DATA_JSON__", {})
