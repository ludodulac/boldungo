from pathlib import Path


VIEWER = Path("frontend/viewer.js")
DOC = Path("docs/VIEWER.md")


def test_viewer_renders_display_only_studs_on_brick_like_parts() -> None:
    js = VIEWER.read_text(encoding="utf-8")

    assert "const studGeometry=new THREE.CylinderGeometry(.30,.30,.15,14)" in js
    assert "studDetailEnabled=!window.matchMedia('(max-width: 760px)').matches" in js
    assert "['brick','plate','facade_detail','window_frame','terrain',...exteriorCategories].includes(p.category)" in js
    assert "const s=new THREE.Mesh(studGeometry,mat(p))" in js


def test_viewer_keeps_category_specific_material_properties() -> None:
    js = VIEWER.read_text(encoding="utf-8")

    assert "k==='window_pane'?.18" in js
    assert "k==='timber'?.58" in js
    assert "k==='metal'?.28" in js
    assert "metalness:k==='metal'?.55:0" in js
    assert "transparent:k==='window_pane'" in js


def test_viewer_docs_no_longer_claim_studs_are_missing() -> None:
    doc = DOC.read_text(encoding="utf-8")

    assert "cylindrical top studs" in doc
    assert "category-specific `MeshStandardMaterial`" in doc
    assert "Studs/tubes" not in doc
