from __future__ import annotations

import json
from pathlib import Path

from brickhouse.survey import ArchitecturalSurvey


FIXTURE = (
    Path(__file__).parents[2]
    / "frontend"
    / "benchmarks"
    / "real-house-5"
    / "accepted-survey-v0.1.json"
)


def _survey() -> ArchitecturalSurvey:
    return ArchitecturalSurvey.model_validate(json.loads(FIXTURE.read_text(encoding="utf-8")))


def test_real_house_5_accepted_orientation_matches_human_confirmed_walkaround() -> None:
    """Guard the accepted capture order; do not invent a corrective reorientation.

    Human confirmation on 2026-09-08 established that the existing accepted
    capture hints are correct: front, right, two complementary left views, then
    the partially observable rear.  Photo 3 approaches the rear through the
    terrace but is still a left-side capture; photo 5 is the rear capture.
    """
    survey = _survey()

    assert survey.known_measurements == []
    canonical = survey.photos[:5]
    supplemental = survey.photos[5:]
    assert [photo.photo_index for photo in canonical] == [1, 2, 3, 4, 5]
    assert [photo.capture_role for photo in canonical] == ["facade_view"] * 5
    assert [photo.facade for photo in canonical] == ["front", "right", "left", "left", "rear"]
    assert supplemental
    assert all(photo.capture_role == "targeted_detail" for photo in supplemental)
    assert all(photo.facade is None for photo in supplemental)
