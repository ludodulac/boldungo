"""Photo-analysis boundary for BrickHouse.

Keep package import lightweight: deterministic consumers such as
`brickhouse.vision.compatibility` must not require an optional vision provider.
"""
from __future__ import annotations

from .models import ClarificationQuestion, PhotoAnalysisResult

__all__ = ["ClarificationQuestion", "PhotoAnalysisResult", "analyze_building_photos"]


def analyze_building_photos(*args, **kwargs):
    """Load the OpenAI-backed provider only when photo analysis is requested."""
    from .openai_provider import analyze_building_photos as _analyze_building_photos

    return _analyze_building_photos(*args, **kwargs)
