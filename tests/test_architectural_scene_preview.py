from pathlib import Path


def test_scene_preview_keeps_bounded_roof_uncertain() -> None:
    source = Path("frontend/scene-viewer.js").read_text(encoding="utf-8")
    assert "pitch_range_degrees" in source
    assert "range.min_degrees" in source
    assert "range.max_degrees" in source
    assert "Les deux plans transparents montrent les limites, pas un angle choisi." in source
    assert "(range.min_degrees + range.max_degrees) / 2" not in source


def test_scene_preview_does_not_coerce_null_roof_geometry_to_zero() -> None:
    source = Path("frontend/scene-viewer.js").read_text(encoding="utf-8")
    assert "function knownNumber(value)" in source
    assert "value !== null && value !== undefined" in source
    assert "knownNumber(roof.pitch_degrees) && roof.down_slope_direction" in source
    assert "aucun plan de toiture arbitraire n’est dessiné" in source


def test_scene_preview_marks_observed_unmetered_terrain_without_fake_slope() -> None:
    source = Path("frontend/scene-viewer.js").read_text(encoding="utf-8")
    assert "function renderTerrain()" in source
    assert "profile.start_elevation, profile.end_elevation, profile.outward_extent" in source
    assert "terrainGradeStatus = 'observed-unmetered'" in source
    assert "pente observée mais non métrée" in source
    assert "sans inventer d’angle ni d’amplitude" in source
    assert "renderTerrain(); renderRoofs()" in source


def test_blocked_scene_links_to_architectural_preview() -> None:
    source = Path("frontend/scene-required-inputs.js").read_text(encoding="utf-8")
    assert "brickhouse.previewArchitecturalScene" in source
    assert "./scene-viewer.html" in source
    assert "Voir la reconstruction 3D actuelle" in source


def test_scene_preview_page_loads_dedicated_renderer() -> None:
    html = Path("frontend/scene-viewer.html").read_text(encoding="utf-8")
    assert "scene-viewer.js" in html
    assert "Aperçu architectural, pas encore une maquette LEGO" in html


def test_scene_preview_renders_known_exterior_elements() -> None:
    source = Path("frontend/scene-viewer.js").read_text(encoding="utf-8")
    assert "function renderPlatforms()" in source
    assert "function renderStairs()" in source
    assert "currentScene.platforms" in source
    assert "currentScene.stairs" in source
    assert "does not guess which sides receive posts or rails" in source
    assert "Les détails non mesurés ne sont pas inventés." in source


def test_scene_preview_accepts_explicit_scene_url_before_local_storage() -> None:
    source = Path("frontend/scene-viewer.js").read_text(encoding="utf-8")
    explicit = "new URLSearchParams(window.location.search).get('scene')"
    assert explicit in source
    assert "await fetch(explicitSceneUrl)" in source
    assert source.index(explicit) < source.index("localStorage.getItem(key)")
    assert "currentScene = await loadScene()" in source


def test_scene_preview_keeps_historical_local_storage_fallback() -> None:
    source = Path("frontend/scene-viewer.js").read_text(encoding="utf-8")
    for key in (
        "brickhouse.previewArchitecturalScene",
        "brickhouse.pendingSceneValidation",
        "brickhouse.lastSceneSurveyValidation",
    ):
        assert key in source
    assert "if (isArchitecturalScene(candidate)) return candidate" in source
