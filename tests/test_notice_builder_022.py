from pathlib import Path

VIEWER = Path("frontend/viewer.js")


def _thumbnail_source() -> str:
    source = VIEWER.read_text(encoding="utf-8")
    return source.split("function constructionPartPreview", 1)[1].split("function updateConstructionHud", 1)[0]


def test_thumbnail_keeps_existing_3d_mesh_and_box_size() -> None:
    thumb = _thumbnail_source()
    assert "piece=makePartMesh(" in thumb
    assert "thumbCamera=new THREE.PerspectiveCamera(32,96/58" in thumb
    assert "preview.width=96" in thumb
    assert "preview.height=58" in thumb
    assert "thumbRenderer.setSize(96,58,false)" in thumb


def test_thumbnail_auto_frames_short_and_long_bricks_from_real_box() -> None:
    thumb = _thumbnail_source()
    assert "size=box.getSize(new THREE.Vector3())" in thumb
    assert "hFov=2*Math.atan(Math.tan(vFov/2)*thumbCamera.aspect)" in thumb
    assert "distance=Math.max(" in thumb
    assert "fitHeight/(2*Math.tan(vFov/2))" in thumb
    assert "fitWidth/(2*Math.tan(hFov/2))" in thumb
    assert "radius*3.15" not in thumb
    # 1x4 and 1x8 share the same box-fit rule; no part-specific scale hacks.
    assert "BRICK_1X4" not in thumb
    assert "BRICK_1X8" not in thumb


def test_multiple_part_types_still_keep_independent_thumbnails_and_quantities() -> None:
    source = VIEWER.read_text(encoding="utf-8")
    hud = source.split("function updateConstructionHud", 1)[1].split("function showAssemblyStep", 1)[0]
    assert "groups=new Map()" in hud
    assert "const key=part.part_id+'|'+(part.semantic_color??part.category)" in hud
    assert "list.replaceChildren(...[...groups.values()].map(row=>constructionPartPreview(row.part,row.quantity)))" in hud
