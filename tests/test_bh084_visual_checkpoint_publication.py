from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGES = ROOT / ".github" / "workflows" / "pages.yml"
VIEWER = ROOT / "frontend" / "viewer.js"


def test_084a_pages_checkpoint_uses_canonical_scene_and_partial_pipeline() -> None:
    workflow = PAGES.read_text(encoding="utf-8")

    assert "frontend/benchmarks/real-house-5/scene-candidate-v0.2.json" in workflow
    assert "from brickhouse.scene.benchmark_scene_recipe import materialize_scene_recipe" in workflow
    assert "from brickhouse.partial_scene_pipeline import run_partial_scene_pipeline" in workflow
    assert "scene = materialize_scene_recipe(recipe)" in workflow
    assert "bundle = run_partial_scene_pipeline(scene, front_width_studs=48)" in workflow
    assert "frontend/real-house-5-visual-checkpoint.json" in workflow
    assert "optimize_scale=True" not in workflow


def test_084a_existing_viewer_supports_direct_bundle_and_construction_mode() -> None:
    viewer = VIEWER.read_text(encoding="utf-8")

    assert "get('bundle')" in viewer
    assert "get('mode')==='construction'" in viewer
    assert "frameCanonicalView('front')" in viewer
    assert "frameCanonicalView('rear')" in viewer
    assert "frameCanonicalView('left')" in viewer
    assert "frameCanonicalView('right')" in viewer
    assert "frameCanonicalView('perspective')" in viewer
    assert "assemblyPrev.addEventListener" in viewer
    assert "assemblyNext.addEventListener" in viewer
    assert "construction-prev" in viewer
    assert "construction-next" in viewer


def test_084a_pages_verifies_deployed_mobile_checkpoint() -> None:
    workflow = PAGES.read_text(encoding="utf-8")

    assert "verify-deployed-visual-checkpoint:" in workflow
    assert "viewer.html?bundle=./real-house-5-visual-checkpoint.json" in workflow
    assert "viewport={'width': 390, 'height': 844}" in workflow
    assert "'#reset-view'" in workflow
    assert "'#view-front'" in workflow
    assert "'#view-right'" in workflow
    assert "'#view-left'" in workflow
    assert "'#view-rear'" in workflow
    assert "OrbitControls drag did not change the rendered view" in workflow
    assert "'#construction-next'" in workflow
    assert "'#construction-prev'" in workflow
