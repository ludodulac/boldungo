import json
from copy import deepcopy
from pathlib import Path

import pytest

from brickhouse.scene import OpeningPriorQuery, PhotoGeometryAnnotation, PhotoScaleCueBinding, PlanarPhotoRectification, build_visual_scale_cues_from_photo_geometry, estimate_architectural_scale, france_residential_opening_priors_v01, rectified_plane_reference_annotation, rectify_photo_geometry_annotation
from brickhouse.scene.benchmark_scene_recipe import materialize_scene_recipe
from brickhouse.survey import ArchitecturalSurvey

ROOT = Path(__file__).resolve().parents[2]
BENCHMARK = ROOT / "frontend" / "benchmarks" / "real-house-5"


def _load(name):
    return json.loads((BENCHMARK / name).read_text(encoding="utf-8"))


def _estimate_height():
    survey = ArchitecturalSurvey.model_validate(_load("accepted-survey-v0.1.json"))
    before = deepcopy(survey.model_dump())
    shared = _load("front-width-scale-evidence.json")
    evidence = _load("front-height-scale-evidence.json")
    rectification = PlanarPhotoRectification.model_validate(shared["rectification"])
    source = [PhotoGeometryAnnotation.model_validate(item) for item in shared["annotations"]]
    rectified = [rectify_photo_geometry_annotation(rectification, item) for item in source]
    by_id = {a.id: b for a, b in zip(source, rectified, strict=True)}
    reference = rectified_plane_reference_annotation(rectification, annotation_id="real-house-5-front-wall-height-reference-v1", observation_id="building-boundary-1", statement="Rectified front wall height reference.")
    priors = {}
    bindings = []
    for spec in evidence["cue_specs"]:
        candidates = [p for p in france_residential_opening_priors_v01(OpeningPriorQuery(semantic_type=spec["semantic_type"], leaf_count=spec["leaf_count"])) if p.dimension == "height"]
        prior = next(p for p in candidates if p.id == spec["prior_id"])
        priors[prior.id] = prior
        feature = by_id[spec["annotation_id"]]
        bindings.append(PhotoScaleCueBinding(id=f"{feature.id}:height", feature_annotation_id=feature.id, reference_annotation_id=reference.id, axis="height", cue_family=spec["cue_family"], prior_id=prior.id, reference_extent_coverage="full_target_extent", target_extent_id="volume_main.height"))
    cues = build_visual_scale_cues_from_photo_geometry(survey, [*rectified, reference], bindings)
    estimate = estimate_architectural_scale(cues, list(priors.values()), minimum_independent_families=evidence["policy"]["minimum_independent_families"])
    assert survey.model_dump() == before
    assert survey.known_measurements == []
    return estimate


def test_front_height_generic_scale_estimator_rejects_over_tall_candidate():
    estimate = _estimate_height()
    stored = _load("front-height-scale-estimate.json")
    assert estimate.resolved is True
    assert estimate.value_m == pytest.approx(stored["value_m"], abs=0.001)
    assert estimate.min_m == pytest.approx(stored["min_m"], abs=0.001)
    assert estimate.max_m == pytest.approx(stored["max_m"], abs=0.001)
    assert estimate.supporting_families == stored["supporting_families"]
    assert 8.0 > estimate.max_m


def test_materialized_scene_uses_height_consensus_and_rectified_front_composition():
    scene = materialize_scene_recipe(BENCHMARK / "scene-candidate-v0.2.json")
    main = scene.volumes[0]
    openings = {o.id: o for o in scene.openings}
    assert main.height.value == pytest.approx(6.5243)
    assert main.height.source.kind.value == "inferred"
    assert main.height.source.confidence == pytest.approx(0.2915)
    assert openings["front-opening-1"].offset_vertical == pytest.approx(4.84)
    assert openings["front-opening-2"].offset_vertical == pytest.approx(4.98)
    assert openings["front-opening-6"].offset_vertical == 0.0
    assert all(o.offset_vertical + o.height <= main.height.value + 1e-9 for o in openings.values() if o.volume_id == main.id)
